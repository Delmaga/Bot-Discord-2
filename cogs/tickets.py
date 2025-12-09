# cogs/tickets.py
import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import asyncio

# === UTILITAIRES ===
def load_data():
    os.makedirs("data", exist_ok=True)
    path = "data/tickets_seiko_v3.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"config": {}, "tickets": {}}

def save_data(data):
    with open("data/tickets_seiko_v3.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def format_timestamp(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# === ÉTAT DU TICKET ===
class TicketState:
    def __init__(self, ticket_id, user_id, category, created_at):
        self.ticket_id = ticket_id
        self.user_id = user_id
        self.category = category
        self.created_at = created_at
        self.state = "OPEN"
        self.claimed_by = None
        self.closed_at = None

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "category": self.category,
            "created_at": self.created_at,
            "state": self.state,
            "claimed_by": self.claimed_by,
            "closed_at": self.closed_at
        }

# === VUE DYNAMIQUE ===
class TicketControlView(discord.ui.View):
    def __init__(self, ticket_id):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        # Boutons selon l’état
        state = self.get_ticket_state()
        if state == "OPEN":
            self.add_item(discord.ui.Button(label="🔷 Claim", style=discord.ButtonStyle.primary, custom_id=f"ticket_claim_{self.ticket_id}"))
            self.add_item(discord.ui.Button(label="🔴 Close", style=discord.ButtonStyle.danger, custom_id=f"ticket_close_{self.ticket_id}"))
        elif state == "CLAIMED":
            self.add_item(discord.ui.Button(label="🔴 Close", style=discord.ButtonStyle.danger, custom_id=f"ticket_close_{self.ticket_id}"))
            self.add_item(discord.ui.Button(label="📄 Transcript", style=discord.ButtonStyle.secondary, custom_id=f"ticket_transcript_{self.ticket_id}"))

    def get_ticket_state(self):
        data = load_data()
        if self.ticket_id not in data["tickets"]:
            return "UNKNOWN"
        return data["tickets"][self.ticket_id]["state"]

# === ÉCOUTEUR GLOBAL ===
class TicketHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.cleanup_old_tickets.start()

    def cog_unload(self):
        self.cleanup_old_tickets.cancel()

    @tasks.loop(hours=1)
    async def cleanup_old_tickets(self):
        now = datetime.utcnow()
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

        action, ticket_id = cid.split("_", 2)[1], cid.split("_", 2)[2]
        if ticket_id not in self.data["tickets"]:
            return await interaction.response.send_message("❌ Ticket introuvable.", ephemeral=True)

        ticket = self.data["tickets"][ticket_id]
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ Réservé au staff.", ephemeral=True)

        if action == "claim":
            if ticket["state"] != "OPEN":
                return await interaction.response.send_message("✅ Déjà pris en charge.", ephemeral=True)
            ticket["state"] = "CLAIMED"
            ticket["claimed_by"] = str(interaction.user.id)
            await interaction.channel.send(f"🔷 **{interaction.user.mention} a pris en charge ce ticket.**")
            await interaction.response.defer()

        elif action == "close":
            ticket["state"] = "CLOSED"
            ticket["closed_at"] = datetime.utcnow().isoformat()
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

        # Sauvegarde et mise à jour de la vue
        save_data(self.data)
        new_view = TicketControlView(ticket_id)
        try:
            await interaction.message.edit(view=new_view)
        except:
            pass

# === COMMANDES SLASH ===
class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ticket = discord.SlashCommandGroup("ticket", "Système de tickets SEÏKO v3.0 — The Impossible Ticket")

    @ticket.command(name="create", description="Ouvrir un ticket")
    async def create(self, ctx, category: discord.Option(str, choices=["Support", "Bug", "Autre"])):
        # Configuration par serveur
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data["config"]:
            data["config"][guild_id] = {"ping_role": None}
            save_data(data)

        # Permissions
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True, manage_channels=True)
        }

        # Rôle staff
        ping = ""
        role_id = data["config"][guild_id]["ping_role"]
        if role_id:
            role = ctx.guild.get_role(int(role_id))
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                ping = f"{role.mention}"

        # Création du salon
        channel = await ctx.guild.create_text_channel(
            name=f"ticket-{ctx.author.name}",
            overwrites=overwrites,
            reason=f"Ticket ouvert par {ctx.author}"
        )

        # ID unique
        ticket_id = str(channel.id)
        data["tickets"][ticket_id] = {
            "user_id": str(ctx.author.id),
            "category": category,
            "created_at": datetime.utcnow().isoformat(),
            "state": "OPEN"
        }
        save_data(data)

        # Message structuré SEÏKO v3.0 — sans bordure, mais avec effet de déformation
        lines = [
            "🟦 **TICKET — SEÏKO v3.0**",
            "───────────────────────────────────────",
            f"📁 Catégorie : {category}",
            f"👤 Utilisateur : {ctx.author.name}",
            f"🕒 Heure : {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
            "───────────────────────────────────────",
            "Merci de détailler votre demande.",
            "Un membre du staff vous répondra sous 24-48h."
            "▶️ En attente de prise en charge...",
        ]

        await channel.send(content=ping, content="\n".join(lines))
        await channel.send(view=TicketControlView(ticket_id))

        await ctx.respond(f"✅ Ticket créé : {channel.mention}", ephemeral=False)

    @ticket.command(name="ping", description="Définir le rôle staff")
    @commands.has_permissions(administrator=True)
    async def ping(self, ctx, role: discord.Role):
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data["config"]:
            data["config"][guild_id] = {}
        data["config"][guild_id]["ping_role"] = str(role.id)
        save_data(data)
        await ctx.respond(f"✅ Rôle de ping : {role.mention}", ephemeral=False)

def setup(bot):
    bot.add_cog(TicketSystem(bot))
    bot.add_cog(TicketHandler(bot))