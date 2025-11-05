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
        super().__init__(placeholder="Sélectionnez une catégorie", options=options)
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

        full_content = f"{ping}\n{message}" if ping else message
        await channel.send(content=full_content)

        await interaction.response.send_message(
            f"✅ **{user.mention}, votre ticket a été créé :** {channel.mention}",
            ephemeral=False
        )

class TicketView(discord.ui.View):
    def __init__(self, config, target_channel):
        super().__init__(timeout=300)
        self.add_item(TicketCategorySelect(config, target_channel))

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = "data/tickets_config.json"
        self.config = load_json(self.config_path, {})

    def get_guild_config(self, guild_id):
        return self.config.get(str(guild_id), {
            "categories": [
                {"name": "Support", "description": "Besoin d'aide ou d'assistance", "emoji": "💬"},
                {"name": "Bug", "description": "Signaler un dysfonctionnement", "emoji": "🐛"},
                {"name": "Autre", "description": "Toute autre demande", "emoji": "📝"}
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

        message = (
            "🎫 **CENTRE D’ASSISTANCE**\n\n"
            "Bienvenue dans notre centre d’assistance officiel.\n"
            "Veuillez sélectionner une catégorie ci-dessous en fonction de votre besoin :\n\n"
        )

        for cat in config["categories"]:
            message += f" • {cat['emoji']} **{cat['name']}** — {cat['description']}\n"

        message += "\nUn membre de l’équipe vous répondra sous **24 à 48 heures**.\n"
        message += "Merci de votre patience et de votre confiance."

        view = TicketView(config, ctx.channel)
        await ctx.respond(message, view=view, ephemeral=False)

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