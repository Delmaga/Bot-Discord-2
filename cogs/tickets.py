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
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = "data/tickets_config.json"
        self.config = load_json(self.config_path, {})

    def get_guild_config(self, guild_id):
        return self.config.get(str(guild_id), {
            "categories": [{"name": "Support", "description": "Besoin d'aide ?", "emoji": "❓"}],
            "footer": "By Delmaga",
            "ping_role": None
        })

    def set_guild_config(self, guild_id, data):
        self.config[str(guild_id)] = data
        save_json(self.config_path, self.config)

    class TicketView(discord.ui.View):
        def __init__(self, bot, config, guild_id):
            super().__init__(timeout=None)
            self.bot = bot
            self.config = config
            self.guild_id = guild_id
            for cat in config["categories"]:
                self.add_item(discord.ui.Button(
                    label=cat["name"],
                    emoji=cat["emoji"],
                    style=discord.ButtonStyle.secondary,
                    custom_id=f"ticket_{cat['name']}"
                ))

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            if not interaction.data.get("custom_id", "").startswith("ticket_"):
                return False
            category_name = interaction.data["custom_id"].replace("ticket_", "")
            category = next((c for c in self.config["categories"] if c["name"] == category_name), None)
            if not category:
                await interaction.response.send_message("❌ Catégorie introuvable.", ephemeral=True)
                return False

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
                    ping = role.mention

            channel = await guild.create_text_channel(f"ticket-{user.name}", overwrites=overwrites)
            embed = discord.Embed(
                title=f"🎫 Nouveau ticket - {guild.name}",
                description=(
                    f"**Catégorie** : {category['name']}\n"
                    f"**Utilisateur** : {user.mention}\n"
                    f"**Heure** : <t:{int(datetime.now().timestamp())}:F>\n\n"
                    "Merci de détailler votre demande. Un membre de l'équipe vous répondra sous 24-48h."
                ),
                color=0x5865F2
            )
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            embed.set_footer(text=f"By {self.config['footer']}")
            await channel.send(content=ping, embed=embed)
            await interaction.response.send_message(f"✅ Votre ticket a été créé : {channel.mention}", ephemeral=True)
            return True

    ticket = discord.SlashCommandGroup("ticket", "Gestion des tickets")

    @ticket.command(name="create", description="Ouvrir un ticket")
    async def create(self, ctx):
        config = self.get_guild_config(ctx.guild.id)
        if not config["categories"]:
            return await ctx.respond("❌ Aucune catégorie disponible.", ephemeral=True)
        embed = discord.Embed(
            title="🎫 Centre d'assistance",
            description="Sélectionnez une catégorie ci-dessous pour ouvrir un ticket.",
            color=0x5865F2
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text=f"By {config['footer']}")
        view = self.TicketView(self.bot, config, ctx.guild.id)
        await ctx.respond(embed=embed, view=view, ephemeral=True)

    @ticket.command(name="category-add", description="Ajouter une catégorie")
    @commands.has_permissions(administrator=True)
    async def category_add(self, ctx, nom: str, description: str, emoji: str):
        config = self.get_guild_config(ctx.guild.id)
        config["categories"].append({"name": nom, "description": description, "emoji": emoji})
        self.set_guild_config(ctx.guild.id, config)
        await ctx.respond(f"✅ Catégorie `{nom}` ajoutée.", ephemeral=True)

    @ticket.command(name="category-del", description="Supprimer une catégorie")
    @commands.has_permissions(administrator=True)
    async def category_del(self, ctx, nom: str):
        config = self.get_guild_config(ctx.guild.id)
        before = len(config["categories"])
        config["categories"] = [c for c in config["categories"] if c["name"] != nom]
        if len(config["categories"]) == before:
            return await ctx.respond(f"❌ Catégorie `{nom}` non trouvée.", ephemeral=True)
        self.set_guild_config(ctx.guild.id, config)
        await ctx.respond(f"✅ Catégorie `{nom}` supprimée.", ephemeral=True)

    @ticket.command(name="footer", description="Modifier le footer")
    @commands.has_permissions(administrator=True)
    async def footer(self, ctx, texte: str):
        config = self.get_guild_config(ctx.guild.id)
        config["footer"] = texte
        self.set_guild_config(ctx.guild.id, config)
        await ctx.respond(f"✅ Footer mis à jour : `{texte}`", ephemeral=True)

    @ticket.command(name="ping", description="Définir le rôle à mentionner")
    @commands.has_permissions(administrator=True)
    async def ping(self, ctx, role: discord.Role):
        config = self.get_guild_config(ctx.guild.id)
        config["ping_role"] = role.id
        self.set_guild_config(ctx.guild.id, config)
        await ctx.respond(f"✅ Rôle de ping : {role.mention}", ephemeral=True)

    @commands.slash_command(name="close", description="Fermer le ticket")
    async def close(self, ctx):
        if not isinstance(ctx.channel, discord.TextChannel) or not ctx.channel.name.startswith("ticket-"):
            return await ctx.respond("❌ Cette commande est réservée aux salons de ticket.", ephemeral=True)
        await ctx.channel.edit(name=f"closed-{ctx.channel.name}")
        await ctx.respond("🔒 Ce ticket sera supprimé dans 24 heures.")
        await asyncio.sleep(24 * 3600)
        try:
            await ctx.channel.delete()
        except:
            pass

def setup(bot):
    bot.add_cog(TicketSystem(bot))