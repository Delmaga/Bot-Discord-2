# cogs/tickets.py
import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta
import asyncio

def load_data():
    os.makedirs("data", exist_ok=True)
    path = "data/tickets_seiko_v4.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"config": {}, "tickets": {}}

def save_data(data):
    with open("data/tickets_seiko_v4.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

class TicketHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.cleanup_old_tickets.start()

    def cog_unload(self):
        self.cleanup_old_tickets.cancel()

    @tasks.loop(hours=1)
    async def cleanup_old_tickets(self):
        now = datetime.now(datetime.timezone.utc)
        to_delete = []
        for ch_id, ticket in self.data["tickets"].items():
            if ticket["state"] == "CLOSED":
                close_time = datetime.fromisoformat(ticket["closed_at"])
                if (now - close_time) > timedelta(hours=24):
                    to_delete.append(ch_id)
        for ch_id in to_delete:
            try:
                channel = self.bot.get_channel(int(ch_id))
                if channel:
                    await channel.delete(reason="[SEÏKO] Nettoyage auto 24h")
                self.data["tickets"].pop(ch_id, None)
                save_data(self.data)
            except:
                pass

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type != discord.InteractionType.component:
            return
        cid = interaction.data.get("custom_id", "")
        if not cid.startswith("ticket_"):
            return

        parts = cid.split("_")
        if len(parts) < 3:
            return

        action, ticket_id = parts[1], parts[2]
        data = load_data()
        if ticket_id not in data["tickets"]:
            await interaction.response.send_message("❌ Ticket introuvable.", ephemeral=True)
            return

        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Réservé au staff.", ephemeral=True)
            return

        ticket = data["tickets"][ticket_id]

        if action == "claim":
            if ticket["state"] != "OPEN":
                await interaction.response.send_message("✅ Déjà pris en charge.", ephemeral=True)
                return
            ticket["state"] = "CLAIMED"
            ticket["claimed_by"] = str(interaction.user.id)
            await interaction.channel.send(f"🔷 **{interaction.user.mention} a pris en charge ce ticket.**")
            await interaction.response.defer()

        elif action == "close":
            ticket["state"] = "CLOSED"
            ticket["closed_at"] = datetime.now(datetime.timezone.utc).isoformat()
            await interaction.channel.edit(name=f"closed-{interaction.channel.name}")
            await interaction.channel.send("🔴 **Ticket fermé. Suppression dans 24h.**")
            await interaction.response.defer()

        elif action == "transcript":
            messages = []
            async for msg in interaction.channel.history(limit=1000, oldest_first=True):
                if msg.type == discord.MessageType.default and not msg.author.bot:
                    messages.append(f"[{msg.created_at.strftime('%Y-%m-%d %H:%M')}] {msg.author}: {msg.content}")
            if messages:
                try:
                    await interaction.user.send(
                        f"📄 **Transcript — Ticket {ticket_id}**\n```txt\n" + "\n".join(messages[:50]) + "\n```"
                    )
                except:
                    pass
            await interaction.response.send_message("✅ Transcript envoyé en MP.", ephemeral=True)

        save_data(data)

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ticket = discord.SlashCommandGroup("ticket", "Gérer les tickets — SEÏKO v4.0")

    @ticket.command(name="create", description="Ouvrir un ticket")
    async def ticket_create(self, ctx, category: discord.Option(str, choices=["Support", "Bug", "Autre"])):
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data["config"]:
            data["config"][guild_id] = {
                "categories": [
                    {"name": "Support", "description": "Besoin d'aide ?", "emoji": "💬"},
                    {"name": "Bug", "description": "Signaler un bug", "emoji": "🐛"}
                ],
                "ping_role": None,
                "footer": "By Seïko • v4.0"
            }
            save_data(data)

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True, manage_channels=True)
        }

        ping_line = ""
        role_id = data["config"][guild_id]["ping_role"]
        if role_id:
            role = ctx.guild.get_role(int(role_id))
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                ping_line = f"{role.mention}"

        channel = await ctx.guild.create_text_channel(
            name=f"ticket-{ctx.author.name}",
            overwrites=overwrites,
            reason=f"Ticket ouvert par {ctx.author}"
        )

        ticket_id = str(channel.id)
        data["tickets"][ticket_id] = {
            "user_id": str(ctx.author.id),
            "category": category,
            "created_at": datetime.now(datetime.timezone.utc).isoformat(),
            "state": "OPEN"
        }
        save_data(data)

        message_lines = [
            "🟦 **TICKET — Seïko**",
            ping_line,
            "───────────────────────────────────────",
            f"📁 Catégorie : {category}",
            f"👤 Utilisateur : {ctx.author.name}",
            f"🕒 Heure : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "───────────────────────────────────────",
            "▶️ En attente de prise en charge...",
            "",
            "Merci de détailler votre demande.",
            "Un membre du staff vous répondra sous 24-48h."
        ]

        await channel.send(content="\n".join(message_lines))
        await ctx.respond(f"✅ Ticket créé : {channel.mention}", ephemeral=False)

    @ticket.command(name="category-add", description="Ajouter une catégorie")
    @commands.has_permissions(administrator=True)
    async def ticket_category_add(self, ctx, nom: str, description: str, emoji: str):
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data["config"]:
            data["config"][guild_id] = {"categories": [], "ping_role": None}
        config = data["config"][guild_id]
        if "categories" not in config:
            config["categories"] = []
        config["categories"].append({"name": nom, "description": description, "emoji": emoji})
        data["config"][guild_id] = config
        save_data(data)
        await ctx.respond(f"✅ Catégorie `{nom}` ajoutée.", ephemeral=False)

    @ticket.command(name="category-del", description="Supprimer une catégorie")
    @commands.has_permissions(administrator=True)
    async def ticket_category_del(self, ctx, nom: str):
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data["config"]:
            return await ctx.respond("❌ Aucune configuration.", ephemeral=False)
        config = data["config"][guild_id]
        if "categories" not in config:
            config["categories"] = []
        before = len(config["categories"])
        config["categories"] = [c for c in config["categories"] if c["name"] != nom]
        if len(config["categories"]) == before:
            return await ctx.respond(f"❌ Catégorie `{nom}` non trouvée.", ephemeral=False)
        data["config"][guild_id] = config
        save_data(data)
        await ctx.respond(f"✅ Catégorie `{nom}` supprimée.", ephemeral=False)

    @ticket.command(name="category-edit", description="Modifier une catégorie")
    @commands.has_permissions(administrator=True)
    async def ticket_category_edit(self, ctx, nom: str, nouveau_nom: str, nouvelle_description: str, nouveaux_emojis: str):
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data["config"]:
            return await ctx.respond("❌ Aucune configuration.", ephemeral=False)
        config = data["config"][guild_id]
        if "categories" not in config:
            config["categories"] = []
        for cat in config["categories"]:
            if cat["name"] == nom:
                cat["name"] = nouveau_nom
                cat["description"] = nouvelle_description
                cat["emoji"] = nouveaux_emojis
                data["config"][guild_id] = config
                save_data(data)
                return await ctx.respond(f"✅ Catégorie mise à jour.", ephemeral=False)
        await ctx.respond(f"❌ Catégorie `{nom}` non trouvée.", ephemeral=False)

    @ticket.command(name="footer", description="Modifier le footer")
    @commands.has_permissions(administrator=True)
    async def ticket_footer(self, ctx, texte: str):
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data["config"]:
            data["config"][guild_id] = {}
        config = data["config"][guild_id]
        config["footer"] = texte
        data["config"][guild_id] = config
        save_data(data)
        await ctx.respond(f"✅ Footer : `{texte}`", ephemeral=False)

    @ticket.command(name="ping", description="Définir le rôle staff")
    @commands.has_permissions(administrator=True)
    async def ticket_ping(self, ctx, role: discord.Role):
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data["config"]:
            data["config"][guild_id] = {}
        data["config"][guild_id]["ping_role"] = role.id
        save_data(data)
        await ctx.respond(f"✅ Rôle de ping : {role.mention}", ephemeral=False)

def setup(bot):
    bot.add_cog(TicketSystem(bot))
    bot.add_cog(TicketHandler(bot))