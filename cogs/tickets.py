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

# ========== BOUTONS D'ACTION DANS LE TICKET ==========
class TicketActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Prendre en charge", style=discord.ButtonStyle.primary, emoji="👤")
    async def take_over(self, button, interaction):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Réservé au staff.", ephemeral=True)
            return
        await interaction.channel.send(f"✅ **{interaction.user.mention} prend en charge ce ticket.**")
        await interaction.response.defer()

    @discord.ui.button(label="Transcript", style=discord.ButtonStyle.secondary, emoji="📥")
    async def transcript(self, button, interaction):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Réservé au staff.", ephemeral=True)
            return
        messages = []
        async for msg in interaction.channel.history(limit=1000, oldest_first=True):
            if msg.type == discord.MessageType.default and not msg.author.bot:
                content = msg.content or "[Contenu non textuel]"
                messages.append(f"[{msg.created_at.strftime('%H:%M')}] **{msg.author}** : {content}")
        if not messages:
            return await interaction.response.send_message("📭 Aucun message à transcrire.", ephemeral=True)
        try:
            await interaction.user.send(
                f"**📄 Transcript du ticket : {interaction.channel.name}**\n```txt\n" +
                "\n".join(messages)[:1900] + "\n```"
            )
            await interaction.response.send_message("✅ Transcript envoyé en MP.", ephemeral=True)
        except:
            await interaction.response.send_message("❌ Impossible d'envoyer un MP.", ephemeral=True)

    @discord.ui.button(label="Fermer", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close_ticket(self, button, interaction):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Réservé au staff.", ephemeral=True)
            return
        await interaction.channel.edit(name=f"closed-{interaction.channel.name}")
        await interaction.channel.send("🔒 Ce ticket sera supprimé dans **24 heures**.")
        await interaction.response.defer()
        await asyncio.sleep(24 * 3600)
        try:
            await interaction.channel.delete()
        except:
            pass

# ========== MENU DÉROULANT ==========
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
        super().__init__(placeholder="Veuillez sélectionner une catégorie", options=options)
        self.config = config
        self.target_channel = target_channel

    async def callback(self, interaction: discord.Interaction):
        category_name = self.values[0]
        category = next((c for c in self.config["categories"] if c["name"] == category_name), None)
        if not category:
            await interaction.response.send_message("❌ Catégorie introuvable.", ephemeral=True)
            return

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

        message = f"""🟦 **NOUVEAU TICKET OUVERT**

        **Catégorie** : {category['name']}
        **Utilisateur** : {user.mention}
        **Heure** : <t:{int(datetime.now().timestamp())}:F>

        Merci de détailler votre demande ci-dessous.
        Un membre de l’équipe vous répondra sous **24 à 48 heures**.

        ────────────────────────────────"""
            color=0x36393f  # Gris doux = fond intégré
            
        embed.set_footer(text=f"By {self.config['footer']}")
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        await channel.send(content=ping, embed=embed)
        await channel.send("**🛠️ Actions disponibles :**", view=TicketActionView())

        await interaction.response.send_message(
            f"✅ **{user.mention}, votre ticket a été créé :** {channel.mention}",
            ephemeral=False
        )

class TicketView(discord.ui.View):
    def __init__(self, config, target_channel):
        super().__init__(timeout=300)
        self.add_item(TicketCategorySelect(config, target_channel))

# ========== COG PRINCIPAL ==========
class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = "data/tickets_config.json"
        self.config = load_json(self.config_path, {})

    def get_guild_config(self, guild_id):
        return self.config.get(str(guild_id), {
            "categories": [
                {"name": "Assistance", "description": "Besoin d'aide ?", "emoji": "💬"},
                {"name": "Signaler un bug", "description": "Dysfonctionnement à signaler", "emoji": "🐛"},
                {"name": "Autre demande", "description": "Toute autre requête", "emoji": "📝"}
            ],
            "footer": "By Delmaga",
            "ping_role": None
        })

    def set_guild_config(self, guild_id, data):
        self.config[str(guild_id)] = data
        save_json(self.config_path, self.config)

    ticket = discord.SlashCommandGroup("ticket", "Gérer les tickets")

    @ticket.command(name="create", description="Ouvrir un ticket")
    async def ticket_create(self, ctx):
        config = self.get_guild_config(ctx.guild.id)
        if not config["categories"]:
            await ctx.respond("❌ Aucune catégorie configurée.", ephemeral=False)
            return

        embed = discord.Embed(
            description=(
                "🎫 **CENTRE D’ASSISTANCE**\n\n"
                "Veuillez sélectionner une catégorie ci-dessous pour ouvrir un ticket.\n\n"
                "Un membre de l’équipe vous répondra sous **24 à 48 heures**.\n"
                "Merci de votre patience."
            ),
            color=0x36393f
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text=f"By {config['footer']}")

        view = TicketView(config, ctx.channel)
        await ctx.respond(embed=embed, view=view, ephemeral=False)

    @ticket.command(name="category_add", description="Ajouter une catégorie")
    @commands.has_permissions(administrator=True)
    async def ticket_category_add(self, ctx, nom: str, description: str, emoji: str):
        config = self.get_guild_config(ctx.guild.id)
        config["categories"].append({"name": nom, "description": description, "emoji": emoji})
        self.set_guild_config(ctx.guild.id, config)
        await ctx.respond(f"✅ Catégorie `{nom}` ajoutée.", ephemeral=False)

    @ticket.command(name="ping", description="Définir le rôle à mentionner")
    @commands.has_permissions(administrator=True)
    async def ticket_ping(self, ctx, role: discord.Role):
        config = self.get_guild_config(ctx.guild.id)
        config["ping_role"] = role.id
        self.set_guild_config(ctx.guild.id, config)
        await ctx.respond(f"✅ Rôle de ping : {role.mention}", ephemeral=False)

    @ticket.command(name="footer", description="Modifier le footer")
    @commands.has_permissions(administrator=True)
    async def ticket_footer(self, ctx, texte: str):
        config = self.get_guild_config(ctx.guild.id)
        config["footer"] = texte
        self.set_guild_config(ctx.guild.id, config)
        await ctx.respond(f"✅ Footer : `{texte}`", ephemeral=False)

def setup(bot):
    bot.add_cog(TicketSystem(bot))