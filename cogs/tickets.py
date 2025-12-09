# cogs/tickets.py — SEÏKO v4.0
import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta
import asyncio

# === UTILITAIRES ===
def load_data():
    os.makedirs("data", exist_ok=True)
    path = "data/seiko_tickets_v4.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"config": {}, "tickets": {}}

def save_data(data):
    with open("data/seiko_tickets_v4.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

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
                    await channel.delete(reason="[SEÏKO] Auto-delete 24h")
                self.data["tickets"].pop(ch_id, None)
                save_data(self.data)
            except:
                pass

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type != discord.InteractionType.component:
            return
        cid = interaction.data.get("custom_id", "")
        if not cid.startswith("seiko_ticket_"):
            return

        action, ticket_id = cid.split("_", 3)[2], cid.split("_", 3)[3]
        if ticket_id not in self.data["tickets"]:
            return await interaction.response.send_message("❌ Ticket introuvable.", ephemeral=True)

        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ Staff only.", ephemeral=True)

        ticket = self.data["tickets"][ticket_id]

        if action == "claim" and ticket["state"] == "OPEN":
            ticket["state"] = "CLAIMED"
            ticket["claimed_by"] = str(interaction.user.id)
            await interaction.channel.send(f"👤 **{interaction.user.mention} a pris en charge ce ticket.**")
            await interaction.response.defer()

        elif action == "close":
            ticket["state"] = "CLOSED"
            ticket["closed_at"] = datetime.utcnow().isoformat()
            await interaction.channel.edit(name=f"closed-{interaction.channel.name}")
            await interaction.channel.send("🔒 **Ticket fermé. Suppression dans 24h.**")
            await interaction.response.defer()

        save_data(self.data)

# === COMMANDES SLASH ===
class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_guild_config(self, guild_id):
        data = load_data()
        gid = str(guild_id)
        if gid not in data["config"]:
            data["config"][gid] = {
                "categories": [
                    {"name": "Support", "description": "Besoin d'aide ?", "emoji": "💬"},
                    {"name": "Bug", "description": "Signaler un bug", "emoji": "🐛"}
                ],
                "footer": "By Seïko",
                "ping_role": None
            }
            save_data(data)
        return data["config"][gid]

    @discord.slash_command(name="ticket", description="Ouvrir un ticket")
    async def ticket(self, ctx):
        cfg = self.get_guild_config(ctx.guild.id)
        embed = discord.Embed(
            description=(
                "🎫 **Centre D’Assistance — Seïko**\n\n"
                "Sélectionnez une catégorie ci-dessous.\n\n"
                "Un membre du staff vous répondra sous 24-48h."
            ),
            color=0x36393f
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text=cfg["footer"])

        options = []
        for cat in cfg["categories"]:
            options.append(discord.SelectOption(
                label=cat["name"],
                description=cat["description"],
                emoji=cat["emoji"]
            ))
        
        select = discord.ui.Select(
            placeholder="Sélectionnez une catégorie",
            options=options,
            custom_id=f"seiko_ticket_select_{ctx.guild.id}"
        )

        async def select_callback(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                return await interaction.response.send_message("❌ Ce ticket est réservé à l’initiateur.", ephemeral=True)
            category = interaction.values[0]
            await self.create_ticket(interaction, category, cfg)

        select.callback = select_callback
        view = discord.ui.View(timeout=300)
        view.add_item(select)
        await ctx.respond(embed=embed, view=view, ephemeral=False)

    async def create_ticket(self, interaction, category, cfg):
        guild = interaction.guild
        user = interaction.user

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, manage_channels=True)
        }

        if cfg["ping_role"]:
            role = guild.get_role(cfg["ping_role"])
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(f"ticket-{user.name}", overwrites=overwrites)

        # Message principal
        ping_line = f"<@&{cfg['ping_role']}>" if cfg["ping_role"] else ""
        message = (
            f"🎫 **NOUVEAU TICKET — Seïko **\n\n"
            f"{ping_line}\n"
            f"**Catégorie** : {category}\n"
            f"**Utilisateur** : {user.mention}\n"
            f"**Heure** : <t:{int(datetime.utcnow().timestamp())}:F>\n\n"
            "Merci de détailler votre demande. Un membre du staff vous répondra sous 24-48h."
        )
        await channel.send(content=message)

        # Boutons
        btn_claim = discord.ui.Button(label="Prendre en charge", style=discord.ButtonStyle.primary, custom_id=f"seiko_ticket_claim_{channel.id}")
        btn_close = discord.ui.Button(label="Fermer", style=discord.ButtonStyle.danger, custom_id=f"seiko_ticket_close_{channel.id}")
        view = discord.ui.View(timeout=None)
        view.add_item(btn_claim)
        view.add_item(btn_close)
        await channel.send(view=view)

        # Sauvegarde
        data = load_data()
        data["tickets"][str(channel.id)] = {
            "user_id": str(user.id),
            "category": category,
            "created_at": datetime.utcnow().isoformat(),
            "state": "OPEN"
        }
        save_data(data)

        await interaction.response.send_message(f"✅ Ticket créé : {channel.mention}", ephemeral=False)

    @discord.slash_command(name="ticket_category_add", description="Ajouter une catégorie")
    @commands.has_permissions(administrator=True)
    async def ticket_category_add(self, ctx, nom: str, description: str, emoji: str):
        data = load_data()
        cfg = self.get_guild_config(ctx.guild.id)
        cfg["categories"].append({"name": nom, "description": description, "emoji": emoji})
        data["config"][str(ctx.guild.id)] = cfg
        save_data(data)
        await ctx.respond(f"✅ Catégorie `{nom}` ajoutée.", ephemeral=False)

    @discord.slash_command(name="ticket_category_del", description="Supprimer une catégorie")
    @commands.has_permissions(administrator=True)
    async def ticket_category_del(self, ctx, nom: str):
        data = load_data()
        cfg = self.get_guild_config(ctx.guild.id)
        before = len(cfg["categories"])
        cfg["categories"] = [c for c in cfg["categories"] if c["name"] != nom]
        if len(cfg["categories"]) == before:
            return await ctx.respond(f"❌ Catégorie `{nom}` non trouvée.", ephemeral=False)
        data["config"][str(ctx.guild.id)] = cfg
        save_data(data)
        await ctx.respond(f"✅ Catégorie `{nom}` supprimée.", ephemeral=False)

    @discord.slash_command(name="ticket_ping", description="Définir le rôle staff")
    @commands.has_permissions(administrator=True)
    async def ticket_ping(self, ctx, role: discord.Role):
        data = load_data()
        cfg = self.get_guild_config(ctx.guild.id)
        cfg["ping_role"] = role.id
        data["config"][str(ctx.guild.id)] = cfg
        save_data(data)
        await ctx.respond(f"✅ Rôle de ping : {role.mention}", ephemeral=False)

    @discord.slash_command(name="ticket_footer", description="Modifier le footer")
    @commands.has_permissions(administrator=True)
    async def ticket_footer(self, ctx, texte: str):
        data = load_data()
        cfg = self.get_guild_config(ctx.guild.id)
        cfg["footer"] = texte
        data["config"][str(ctx.guild.id)] = cfg
        save_data(data)
        await ctx.respond(f"✅ Footer : `{texte}`", ephemeral=False)

def setup(bot):
    bot.add_cog(TicketSystem(bot))
    bot.add_cog(TicketHandler(bot))