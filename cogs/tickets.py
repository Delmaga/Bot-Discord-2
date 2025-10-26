import discord
from discord.ext import commands
import json
import os
from datetime import datetime

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
    def __init__(self, bot, config):
        options = []
        for cat in config["categories"]:
            options.append(
                discord.SelectOption(
                    label=cat["name"],
                    description=cat["description"][:100],
                    emoji=cat["emoji"]
                )
            )
        super().__init__(
            placeholder="Choisissez une catégorie...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.bot = bot
        self.config = config

    async def callback(self, interaction: discord.Interaction):
        category_name = self.values[0]
        category = next((c for c in self.config["categories"] if c["name"] == category_name), None)
        if not category:
            return await interaction.response.send_message("❌ Catégorie introuvable.", ephemeral=True)

        guild = interaction.guild
        user = interaction.user

        # Permissions du salon
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, manage_channels=True)
        }

        # Rôle staff
        ping = ""
        if self.config.get("ping_role"):
            role = guild.get_role(self.config["ping_role"])
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                ping = role.mention

        # Créer le salon
        channel = await guild.create_text_channel(f"ticket-{user.name}", overwrites=overwrites)

        # Embed de bienvenue
        embed = discord.Embed(
            title=f"🎫 Ticket - {guild.name}",
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

        # Message public dans le salon d'origine
        await interaction.response.send_message(
            f"✅ {user.mention}, votre ticket a été créé : {channel.mention}",
            ephemeral=False  # ← Visible par tous
        )

class TicketView(discord.ui.View):
    def __init__(self, bot, config):
        super().__init__(timeout=None)
        self.add_item(TicketCategorySelect(bot, config))

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = "data/tickets_config.json"
        self.config = load_json(self.config_path, {})

    def get_guild_config(self, guild_id):
        return self.config.get(str(guild_id), {
            "categories": [
                {"name": "Support", "description": "Besoin d'aide ?", "emoji": "❓"},
                {"name": "Bug", "description": "Signaler un bug", "emoji": "🐛"},
                {"name": "Autre", "description": "Autre demande", "emoji": "📝"}
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
            return await ctx.respond("❌ Aucune catégorie disponible.", ephemeral=False)

        embed = discord.Embed(
            title="🎫 Centre d'assistance",
            description="Sélectionnez une catégorie ci-dessous pour ouvrir un ticket.",
            color=0x5865F2
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text=f"By {config['footer']}")

        view = TicketView(self.bot, config)
        await ctx.respond(embed=embed, view=view, ephemeral=False)  # ← Visible par tous

    # --- Commandes d'administration (visibles par tous) ---
    @discord.slash_command(name="ticket_category_add")
    @commands.has_permissions(administrator=True)
    async def ticket_category_add(self, ctx, nom: str, description: str, emoji: str):
        config = self.get_guild_config(ctx.guild.id)
        config["categories"].append({"name": nom, "description": description, "emoji": emoji})
        self.set_guild_config(ctx.guild.id, config)
        await ctx.respond(f"✅ Catégorie `{nom}` ajoutée.", ephemeral=False)

    @discord.slash_command(name="ticket_footer")
    @commands.has_permissions(administrator=True)
    async def ticket_footer(self, ctx, texte: str):
        config = self.get_guild_config(ctx.guild.id)
        config["footer"] = texte
        self.set_guild_config(ctx.guild.id, config)
        await ctx.respond(f"✅ Footer mis à jour : `{texte}`", ephemeral=False)

    @discord.slash_command(name="ticket_ping")
    @commands.has_permissions(administrator=True)
    async def ticket_ping(self, ctx, role: discord.Role):
        config = self.get_guild_config(ctx.guild.id)
        config["ping_role"] = role.id
        self.set_guild_config(ctx.guild.id, config)
        await ctx.respond(f"✅ Rôle de ping : {role.mention}", ephemeral=False)

    @discord.slash_command(name="close", description="Fermer le ticket")
    async def close(self, ctx):
        if not isinstance(ctx.channel, discord.TextChannel) or not ctx.channel.name.startswith("ticket-"):
            return await ctx.respond("❌ Cette commande est réservée aux salons de ticket.", ephemeral=False)
        await ctx.channel.edit(name=f"closed-{ctx.channel.name}")
        await ctx.respond("🔒 Ce ticket sera supprimé dans 24 heures.", ephemeral=False)
        # Optionnel : ajouter un délai de suppression

def setup(bot):
    bot.add_cog(TicketSystem(bot))