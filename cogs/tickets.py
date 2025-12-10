# cogs/tickets.py
import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta, timezone
import asyncio

def load_data():
    os.makedirs("data", exist_ok=True)
    path = "data/tickets_seiko_v9.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"config": {}, "tickets": {}}

def save_data(data):
    with open("data/tickets_seiko_v9.json", "w", encoding="utf-8") as f:
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
        now = datetime.now(timezone.utc)
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

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="ticket", description="Ouvrir un ticket via menu")
    async def ticket(self, ctx):
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data["config"]:
            data["config"][guild_id] = {
                "categories": [
                    {"name": "Support", "description": "Besoin d'aide ?", "emoji": "💬"},
                    {"name": "Bug", "description": "Signaler un bug", "emoji": "🐛"},
                    {"name": "Autre", "description": "Toute autre demande", "emoji": "📝"}
                ],
                "ping_role": None,
                "transcript_channel": None,
                "footer": "By Seïko"
            }
            save_data(data)

        config = data["config"][guild_id]
        options = []
        for cat in config["categories"]:
            options.append(
                discord.SelectOption(
                    label=cat["name"],
                    description=cat["description"],
                    emoji=cat["emoji"]
                )
            )

        select = discord.ui.Select(
            placeholder="Veuillez sélectionner une catégorie",
            options=options
        )

        async def select_callback(interaction):
            category = interaction.data['values'][0]
            if interaction.user != ctx.author:
                await interaction.response.send_message("❌ Ce ticket est privé.", ephemeral=True)
                return

            guild = interaction.guild
            user = interaction.user

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, manage_channels=True)
            }

            ping_line = ""
            if config["ping_role"]:
                role = guild.get_role(config["ping_role"])
                if role:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                    ping_line = f"{role.mention}"

            channel = await guild.create_text_channel(
                name=f"ticket-{user.name}",
                overwrites=overwrites,
                reason=f"Ticket ouvert par {user}"
            )

            # ✅ BARRE DE PROGRESSION — 2 secondes, dans le salon du ticket
            progress_msg = await channel.send("```\n[░░░░░░░░░░] 0% — Initialisation...\n```")
            for i in range(1, 11):
                await asyncio.sleep(0.2)
                bars = "█" * i + "░" * (10 - i)
                pct = i * 10
                await progress_msg.edit(content=f"```\n[{bars}] {pct}% — Création du ticket en cours...\n```")
            await progress_msg.edit(content="```\n[██████████] 100% — Votre ticket a été parfaitement initialisé !\n```")
            await asyncio.sleep(1)
            await progress_msg.delete()

            ticket_id = str(channel.id)
            data["tickets"][ticket_id] = {
                "user_id": str(user.id),
                "category": category,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "state": "OPEN"
            }
            save_data(data)

            message_lines = [
                "🟦 **TICKET — Seïko**",
                ping_line,
                "───────────────────────────────────────",
                f"📁 Catégorie : **{category}**",
                f"👤 Utilisateur : **{user.name}**",
                f"🕒 Heure : **{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**",
                "───────────────────────────────────────",
                "▶️ En attente de prise en charge...",
                "",
                "Merci de détailler votre demande.",
                "Un membre du staff vous répondra sous 24-48h."
            ]

            await channel.send(content="\n".join(message_lines))

            async def claim_callback(interaction):
                if not interaction.user.guild_permissions.manage_channels:
                    await interaction.response.send_message("❌ Réservé au staff.", ephemeral=True)
                    return
                await interaction.channel.send(f"🔷 **{interaction.user.mention} a pris en charge ce ticket.**")
                await interaction.response.defer()

            async def close_callback(interaction):
                if not interaction.user.guild_permissions.manage_channels:
                    await interaction.response.send_message("❌ Réservé au staff.", ephemeral=True)
                    return
                await interaction.channel.edit(name=f"closed-{channel.name}")
                await interaction.channel.send("🔒 Ce ticket sera supprimé dans **24 heures**.")
                await interaction.response.defer()

                if config["transcript_channel"]:
                    transcript_channel = self.bot.get_channel(int(config["transcript_channel"]))
                    if transcript_channel:
                        messages = []
                        async for msg in interaction.channel.history(limit=1000, oldest_first=True):
                            if msg.type == discord.MessageType.default and not msg.author.bot:
                                messages.append(f"[{msg.created_at.strftime('%Y-%m-%d %H:%M')}] {msg.author}: {msg.content}")
                        if messages:
                            await transcript_channel.send(
                                f"📄 **Transcript — Ticket {ticket_id}**\n```txt\n" + "\n".join(messages[:100]) + "\n```"
                            )

                # ✅ BARRE DE PROGRESSION 24H — AJOUTÉE ICI (SEULE CHOSE AJOUTÉE)
                progress_24h = await interaction.channel.send("```\n[░░░░░░░░░░] 0% — Suppression dans 24h...\n```")
                total_steps = 96  # 24h * 4 (toutes les 15 min)
                for step in range(1, total_steps + 1):
                    await asyncio.sleep(900)  # 15 minutes
                    pct = int((step / total_steps) * 100)
                    filled = "█" * min(step, 10)
                    empty = "░" * max(0, 10 - step)
                    try:
                        await progress_24h.edit(content=f"```\n[{filled}{empty}] {pct}% — Suppression en cours...\n```")
                    except:
                        break
                try:
                    await interaction.channel.delete()
                except:
                    pass

            view = discord.ui.View(timeout=None)
            claim_btn = discord.ui.Button(label="Prendre en charge", style=discord.ButtonStyle.primary, emoji="👤")
            close_btn = discord.ui.Button(label="Fermer", style=discord.ButtonStyle.danger, emoji="🔒")
            claim_btn.callback = claim_callback
            close_btn.callback = close_callback
            view.add_item(claim_btn)
            view.add_item(close_btn)
            await channel.send(view=view)

            await interaction.response.send_message(f"✅ Ticket créé : {channel.mention}", ephemeral=False)

        select.callback = select_callback

        embed = discord.Embed(
            title="🎫 CENTRE D’ASSISTANCE",
            description=(
                "Veuillez sélectionner une catégorie ci-dessous pour ouvrir un ticket.\n\n"
                "Un membre de l’équipe vous répondra sous **24 à 48 heures**.\n"
                "Merci de votre patience."
            ),
            color=0x2b2d31
        )
        embed.set_footer(text=config["footer"])
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)

        view = discord.ui.View(timeout=300)
        view.add_item(select)
        await ctx.respond(embed=embed, view=view, ephemeral=False)

    @discord.slash_command(name="ticket_create", description="Créer un ticket dans un salon spécifique")
    async def ticket_create(self, ctx, salon: discord.TextChannel, category: discord.Option(str, choices=["Support", "Bug", "Autre"])):
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data["config"]:
            data["config"][guild_id] = {"categories": [], "ping_role": None}
        config = data["config"][guild_id]

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True, manage_channels=True)
        }

        ping_line = ""
        if config["ping_role"]:
            role = ctx.guild.get_role(config["ping_role"])
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                ping_line = f"{role.mention}"

        channel = await ctx.guild.create_text_channel(
            name=f"ticket-{ctx.author.name}",
            overwrites=overwrites,
            category=salon.category
        )

        ticket_id = str(channel.id)
        data["tickets"][ticket_id] = {
            "user_id": str(ctx.author.id),
            "category": category,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "state": "OPEN"
        }
        save_data(data)

        message_lines = [
            "🟦 **TICKET — Seïko**",
            ping_line,
            "───────────────────────────────────────",
            f"📁 Catégorie : **{category}**",
            f"👤 Utilisateur : **{ctx.author.name}**",
            f"🕒 Heure : **{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**",
            "───────────────────────────────────────",
            "▶️ En attente de prise en charge...",
            "",
            "Merci de détailler votre demande.",
            "Un membre du staff vous répondra sous 24-48h."
        ]

        await channel.send(content="\n".join(message_lines))
        await ctx.respond(f"✅ Ticket créé : {channel.mention}", ephemeral=False)

    @discord.slash_command(name="ticket_transcript", description="Définir le salon pour les transcripts automatiques")
    @commands.has_permissions(administrator=True)
    async def ticket_transcript(self, ctx, salon: discord.TextChannel):
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data["config"]:
            data["config"][guild_id] = {}
        data["config"][guild_id]["transcript_channel"] = str(salon.id)
        save_data(data)
        await ctx.respond(f"✅ Transcripts automatiques activés dans {salon.mention}.", ephemeral=False)

    @discord.slash_command(name="ticket_category_add", description="Ajouter une catégorie")
    @commands.has_permissions(administrator=True)
    async def ticket_category_add(self, ctx, nom: str, description: str, emoji: str):
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data["config"]:
            data["config"][guild_id] = {"categories": []}
        config = data["config"][guild_id]
        if "categories" not in config:
            config["categories"] = []
        config["categories"].append({"name": nom, "description": description, "emoji": emoji})
        data["config"][guild_id] = config
        save_data(data)
        await ctx.respond(f"✅ Catégorie `{nom}` ajoutée.", ephemeral=False)

    @discord.slash_command(name="ticket_category_del", description="Supprimer une catégorie")
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

    @discord.slash_command(name="ticket_ping", description="Définir le rôle staff")
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