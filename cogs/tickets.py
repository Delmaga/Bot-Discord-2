# cogs/tickets.py
import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import asyncio

def load_json(path, default):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            return json.loads(content) if content else default
    return default

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ========== BOUTONS D'ACTION (STYLE CINÉMA) ==========
class TicketActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="  Prendre en charge  ", style=discord.ButtonStyle.primary, emoji="👤")
    async def take_over(self, button, interaction):
        if not interaction.user.guild_permissions.manage_channels:
            embed = discord.Embed(
                description="❌ **Accès refusé**\nSeul le staff peut utiliser cette action.",
                color=0xED4245
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        embed = discord.Embed(
            description=f"✅ **{interaction.user.mention} prend en charge ce ticket.**",
            color=0x57F287
        )
        await interaction.channel.send(embed=embed)
        await interaction.response.defer()

    @discord.ui.button(label="  Transcript  ", style=discord.ButtonStyle.secondary, emoji="📥")
    async def transcript(self, button, interaction):
        if not interaction.user.guild_permissions.manage_channels:
            embed = discord.Embed(
                description="❌ **Accès refusé**",
                color=0xED4245
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        messages = []
        async for msg in interaction.channel.history(limit=1000, oldest_first=True):
            if msg.type == discord.MessageType.default and not msg.author.bot:
                content = msg.content or "[Contenu non textuel]"
                messages.append(f"[{msg.created_at.strftime('%H:%M')}] **{msg.author}** : {content}")

        if not messages:
            embed = discord.Embed(description="📭 Aucun message à transcrire.", color=0xFEE75C)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        transcript_text = "\n".join(messages)
        try:
            await interaction.user.send(
                f"```ansi\n"
                f"[2;34m┌──────────────────────────────┐[0m\n"
                f"[2;34m│ [0m📄 [1;36mTRANSCRIPT DU TICKET [0m[2;34m │[0m\n"
                f"[2;34m└──────────────────────────────┘[0m\n"
                f"```"
                f"\n```txt\n{transcript_text[:1900]}\n```"
            )
            embed = discord.Embed(description="✅ Transcript envoyé en MP.", color=0x57F287)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            embed = discord.Embed(description="❌ Vos MP sont fermés.", color=0xED4245)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="  Fermer le ticket  ", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close_ticket(self, button, interaction):
        if not interaction.user.guild_permissions.manage_channels:
            embed = discord.Embed(description="❌ **Accès refusé**", color=0xED4245)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.channel.edit(name=f"closed-{interaction.channel.name}")
        embed = discord.Embed(
            description="🔒 **Ce ticket sera supprimé dans 24 heures.**",
            color=0x2b2d31
        )
        await interaction.channel.send(embed=embed)
        await interaction.response.defer()

        await asyncio.sleep(24 * 3600)
        try:
            await interaction.channel.delete()
        except:
            pass

# ========== MENU DÉROULANT (STYLE PREMIUM) ==========
class TicketCategorySelect(discord.ui.Select):
    def __init__(self, config, target_channel):
        options = [
            discord.SelectOption(
                label=cat["name"],
                description=cat["description"][:100],
                emoji=cat["emoji"]
            )
            for cat in config["categories"]
        ]
        super().__init__(
            placeholder=" Sélectionnez une catégorie ",
            options=options,
            custom_id="ticket_category_select"
        )
        self.config = config
        self.target_channel = target_channel

    async def callback(self, interaction: discord.Interaction):
        category_name = self.values[0]
        category = next((c for c in self.config["categories"] if c["name"] == category_name), None)
        if not category:
            embed = discord.Embed(description="❌ Catégorie introuvable.", color=0xED4245)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        guild = interaction.guild
        user = interaction.user

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, manage_channels=True)
        }

        ping = ""
        if self.config.get("ping_role"):
            role = guild.get_role(self.config["ping_role"])
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                ping = f"🔔 {role.mention}"

        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            overwrites=overwrites,
            category=self.target_channel.category
        )

        # === EMBED CINÉMA ===
        embed = discord.Embed(
            title="",
            description="```ansi\n"
                        "[2;34m┌──────────────────────────────┐[0m\n"
                        "[2;34m│ [0m🎫 [1;36mNOUVEAU TICKET OUVERT [0m[2;34m │[0m\n"
                        "[2;34m└──────────────────────────────┘[0m\n"
                        "```",
            color=0x2b2d31
        )
        embed.add_field(
            name="```ansi\n[2;37m📋 INFORMATIONS[0m```",
            value="```ansi\n"
                  f"[2;37mCatégorie : [0m[1;33m{category['name']}[0m\n"
                  f"[2;37mUtilisateur : [0m{user.mention}\n"
                  f"[2;37mHeure      : [0m<t:{int(datetime.now().timestamp())}:F>\n"
                  "```",
            inline=False
        )
        embed.add_field(
            name="```ansi\n[2;37m📝 INSTRUCTIONS[0m```",
            value="```ansi\n"
                  "[2;37m• Soyez précis dans votre demande\n"
                  "[2;37m• Un membre de l'équipe répondra\n"
                  "[2;37m  sous 24-48h.\n"
                  "```",
            inline=False
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.set_footer(text=f"By {self.config['footer']}")

        await channel.send(content=ping, embed=embed)
        await channel.send("```ansi\n[2;34m🛠️ ACTIONS DISPONIBLES[0m```", view=TicketActionView())

        # Confirmation publique
        confirm_embed = discord.Embed(
            description=f"✅ **{user.mention}, votre ticket a été créé :** {channel.mention}",
            color=0x57F287
        )
        await interaction.response.send_message(embed=confirm_embed, ephemeral=False)

class TicketView(discord.ui.View):
    def __init__(self, config, target_channel):
        super().__init__(timeout=300)
        self.add_item(TicketCategorySelect(config, target_channel))

# ========== COG PRINCIPAL (PAS DE CHANGEMENT FONCTIONNEL) ==========
class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = "data/tickets_config.json"
        self.config = load_json(self.config_path, {})

    def get_guild_config(self, guild_id):
        return self.config.get(str(guild_id), {
            "categories": [
                {"name": "Support", "description": "Besoin d'aide ?", "emoji": "❓"},
                {"name": "Bug", "description": "Signaler un bug", "emoji": "🐛"}
            ],
            "footer": "By Delmaga",
            "ping_role": None
        })

    def set_guild_config(self, guild_id, data):
        self.config[str(guild_id)] = data
        save_json(self.config_path, self.config)

    @discord.slash_command(name="ticket", description="Ouvrir un ticket")
    async def ticket(self, ctx):
        config = self.get_guild_config(ctx.guild.id)
        if not config["categories"]:
            embed = discord.Embed(description="❌ Aucune catégorie configurée.", color=0xED4245)
            return await ctx.respond(embed=embed, ephemeral=False)

        embed = discord.Embed(
            title="",
            description="```ansi\n"
                        "[2;34m┌──────────────────────────────┐[0m\n"
                        "[2;34m│ [0m🎫 [1;36mCENTRE D'ASSISTANCE [0m[2;34m │[0m\n"
                        "[2;34m└──────────────────────────────┘[0m\n"
                        "```",
            color=0x2b2d31
        )
        embed.add_field(
            name="```ansi\n[2;37m📌 INSTRUCTIONS[0m```",
            value="```ansi\n"
                  "[2;37mSélectionnez une catégorie ci-dessous\n"
                  "[2;37mpour ouvrir un ticket.\n"
                  "```",
            inline=False
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text=f"By {config['footer']}")

        view = TicketView(config, ctx.channel)
        await ctx.respond(embed=embed, view=view, ephemeral=False)

    @discord.slash_command(name="ticket_category_add")
    @commands.has_permissions(administrator=True)
    async def ticket_category_add(self, ctx, nom: str, description: str, emoji: str):
        config = self.get_guild_config(ctx.guild.id)
        config["categories"].append({"name": nom, "description": description, "emoji": emoji})
        self.set_guild_config(ctx.guild.id, config)
        embed = discord.Embed(description=f"✅ Catégorie `{nom}` ajoutée.", color=0x57F287)
        await ctx.respond(embed=embed, ephemeral=False)

    @discord.slash_command(name="ticket_ping")
    @commands.has_permissions(administrator=True)
    async def ticket_ping(self, ctx, role: discord.Role):
        config = self.get_guild_config(ctx.guild.id)
        config["ping_role"] = role.id
        self.set_guild_config(ctx.guild.id, config)
        embed = discord.Embed(description=f"✅ Rôle de ping : {role.mention}", color=0x57F287)
        await ctx.respond(embed=embed, ephemeral=False)

    @discord.slash_command(name="ticket_footer")
    @commands.has_permissions(administrator=True)
    async def ticket_footer(self, ctx, texte: str):
        config = self.get_guild_config(ctx.guild.id)
        config["footer"] = texte
        self.set_guild_config(ctx.guild.id, config)
        embed = discord.Embed(description=f"✅ Footer : `{texte}`", color=0x57F287)
        await ctx.respond(embed=embed, ephemeral=False)

def setup(bot):
    bot.add_cog(TicketSystem(bot))