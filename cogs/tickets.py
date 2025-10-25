# cogs/tickets.py
import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import asyncio

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_path = "data/tickets.json"
        self.load_data()
        self.close_old_tickets.start()

    def cog_unload(self):
        self.close_old_tickets.cancel()

    def load_data(self):
        os.makedirs("data", exist_ok=True)
        if os.path.exists(self.data_path):
            with open(self.data_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    self.config = json.loads(content)
                else:
                    self.config = self.default_config()
        else:
            self.config = self.default_config()
            self.save_data()

    def default_config(self):
        return {
            "categories": [
                {"name": "Support", "description": "Besoin d'aide ?", "emoji": "❓"},
                {"name": "Bug", "description": "Signaler un bug", "emoji": "🐛"},
                {"name": "Autre", "description": "Autre demande", "emoji": "📝"}
            ],
            "footer": "By Delmaga",
            "ping_role": None,
            "active_tickets": {}  # {channel_id: {"created_at": timestamp, "author_id": id, "category": "..."}}
        }

    def save_data(self):
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    # ========== VUE AVEC MENU DÉROULANT ==========
    class TicketCategorySelect(discord.ui.Select):
        def __init__(self, bot, config):
            options = []
            for cat in config["categories"]:
                options.append(
                    discord.SelectOption(
                        label=cat["name"],
                        description=cat["description"],
                        emoji=cat["emoji"],
                        value=cat["name"]
                    )
                )
            super().__init__(
                placeholder="Sélectionnez le type de ticket...",
                min_values=1,
                max_values=1,
                options=options
            )
            self.bot = bot
            self.config = config

        async def callback(self, interaction: discord.Interaction):
            guild = interaction.guild
            user = interaction.user
            selected_category = self.values[0]

            # Trouver la catégorie
            category = next((c for c in self.config["categories"] if c["name"] == selected_category), None)
            if not category:
                return await interaction.response.send_message("❌ Catégorie introuvable.", ephemeral=True)

            # Créer salon privé
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    read_message_history=True
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    manage_channels=True
                )
            }

            ping = ""
            if self.config.get("ping_role"):
                role = guild.get_role(self.config["ping_role"])
                if role:
                    overwrites[role] = discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True
                    )
                    ping = role.mention

            channel = await guild.create_text_channel(
                name=f"ticket-{user.name}",
                overwrites=overwrites,
                reason=f"Ticket créé par {user}"
            )

            # Embed de bienvenue
            embed = discord.Embed(
                title=f"🎫 Ticket - {guild.name}",
                description=(
                    f"**Catégorie** : {category['name']}\n"
                    f"**Demandé par** : {user.mention}\n"
                    f"**Heure** : <t:{int(datetime.now().timestamp())}:F>\n\n"
                    "- Soyez précis pour que nous puissions mieux vous répondre\n"
                    "- Vous aurez une réponse entre 24h & 48h."
                ),
                color=0x5865F2
            )
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            embed.set_footer(text=f"By {self.config['footer']}")

            await channel.send(content=ping, embed=embed)

            # Message de confirmation
            await interaction.response.send_message(
                f"✅ Votre ticket a été créé : {channel.mention}",
                ephemeral=True
            )

    class TicketCategoryView(discord.ui.View):
        def __init__(self, bot, config):
            super().__init__(timeout=None)
            self.add_item(TicketSystem.TicketCategorySelect(bot, config))

    # ========== COMMANDES SLASH ==========
    ticket_group = discord.SlashCommandGroup("ticket", "Gérer les tickets")

    @ticket_group.command(name="create", description="Ouvrir un ticket")
    async def ticket_create(self, ctx):
        """Affiche le menu déroulant pour choisir la catégorie"""
        if not self.config["categories"]:
            return await ctx.respond("❌ Aucune catégorie de ticket configurée.", ephemeral=True)

        embed = discord.Embed(
            title="🎫 Créer un ticket",
            description="Veuillez choisir la catégorie ci-dessous.",
            color=0x5865F2
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text=f"By {self.config['footer']}")

        view = self.TicketCategoryView(self.bot, self.config)
        await ctx.respond(embed=embed, view=view, ephemeral=True)

    @ticket_group.command(name="category-add", description="Ajouter une catégorie")
    @commands.has_permissions(administrator=True)
    async def ticket_category_add(self, ctx, nom: str, description: str, emojis: str):
        self.config["categories"].append({
            "name": nom,
            "description": description,
            "emoji": emojis
        })
        self.save_data()
        await ctx.respond(f"✅ Catégorie `{nom}` ajoutée.", ephemeral=True)

    @ticket_group.command(name="category-del", description="Supprimer une catégorie")
    @commands.has_permissions(administrator=True)
    async def ticket_category_del(self, ctx, nom: str):
        before = len(self.config["categories"])
        self.config["categories"] = [c for c in self.config["categories"] if c["name"] != nom]
        if len(self.config["categories"]) == before:
            return await ctx.respond(f"❌ Catégorie `{nom}` non trouvée.", ephemeral=True)
        self.save_data()
        await ctx.respond(f"✅ Catégorie `{nom}` supprimée.", ephemeral=True)

    @ticket_group.command(name="category-list", description="Lister les catégories")
    @commands.has_permissions(administrator=True)
    async def ticket_category_list(self, ctx):
        if not self.config["categories"]:
            return await ctx.respond("📭 Aucune catégorie.", ephemeral=True)
        lines = [f"{c['emoji']} **{c['name']}** — {c['description']}" for c in self.config["categories"]]
        embed = discord.Embed(title="📋 Catégories de tickets", description="\n".join(lines), color=0x5865F2)
        await ctx.respond(embed=embed, ephemeral=True)

    @ticket_group.command(name="edit-category", description="Modifier une catégorie")
    @commands.has_permissions(administrator=True)
    async def ticket_edit_category(self, ctx, nom: str, nouveau_nom: str, nouvelle_description: str, nouveaux_emojis: str):
        for cat in self.config["categories"]:
            if cat["name"] == nom:
                cat["name"] = nouveau_nom
                cat["description"] = nouvelle_description
                cat["emoji"] = nouveaux_emojis
                self.save_data()
                return await ctx.respond(f"✅ Catégorie mise à jour.", ephemeral=True)
        await ctx.respond(f"❌ Catégorie `{nom}` non trouvée.", ephemeral=True)

    @ticket_group.command(name="footer", description="Changer le footer")
    @commands.has_permissions(administrator=True)
    async def ticket_footer(self, ctx, footer: str):
        self.config["footer"] = footer
        self.save_data()
        await ctx.respond(f"✅ Footer mis à jour : `{footer}`", ephemeral=True)

    @ticket_group.command(name="ping", description="Définir le rôle à mentionner")
    @commands.has_permissions(administrator=True)
    async def ticket_ping(self, ctx, role: discord.Role):
        self.config["ping_role"] = role.id
        self.save_data()
        await ctx.respond(f"✅ Rôle de ping : {role.mention}", ephemeral=True)

    # ========== COMMANDE DE FERMETURE ==========
    @commands.slash_command(name="close", description="Fermer un ticket")
    async def close_ticket(self, ctx):
        if not isinstance(ctx.channel, discord.TextChannel):
            return await ctx.respond("❌ Commande réservée aux salons textuels.", ephemeral=True)

        # Renommer le salon
        await ctx.channel.edit(name=f"ticket-close-{ctx.channel.id}")
        await ctx.respond("🔒 Ce ticket sera supprimé dans 24h.")

        # Planifier la suppression
        await asyncio.sleep(24 * 3600)  # 24 heures
        try:
            await ctx.channel.delete(reason="Ticket fermé depuis 24h")
        except:
            pass  # Ignore si déjà supprimé

# ========== SETUP OBLIGATOIRE ==========
def setup(bot):
    bot.add_cog(TicketSystem(bot))