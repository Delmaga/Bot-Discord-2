# cogs/tickets.py
import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta, timezone
import asyncio

def load_data():
    os.makedirs("data", exist_ok=True)
    path = "data/tickets_seiko_v10.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"config": {}, "tickets": {}}

def save_data(data):
    with open("data/tickets_seiko_v10.json", "w", encoding="utf-8") as f:
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
                "footer": "By Seïko",
                "ticket_counter": 1
            }
            save_data(data)

        config = data["config"][guild_id]

        # ✅ Vérifie que "categories" existe
        if "categories" not in config or not config["categories"]:
            config["categories"] = [
                {"name": "Support", "description": "Besoin d'aide ?", "emoji": "💬"},
                {"name": "Bug", "description": "Signaler un bug", "emoji": "🐛"},
                {"name": "Autre", "description": "Toute autre demande", "emoji": "📝"}
            ]
            save_data(data)

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
            placeholder="Sélectionnez une catégorie",
            options=options
        )

        async def select_callback(interaction):
            await interaction.response.defer(ephemeral=False)

            category = interaction.data['values'][0]
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
                    ping_line = f"<@&{role.id}>"

            # ✅ Vérifie et initialise ticket_counter
            if "ticket_counter" not in config:
                config["ticket_counter"] = 1
                save_data(data)

            ticket_number = config["ticket_counter"]
            config["ticket_counter"] = ticket_number + 1
            save_data(data)

            channel = await guild.create_text_channel(
                name=f"{ticket_number}-{category}",
                overwrites=overwrites,
                reason=f"Ticket #{ticket_number} par {user.name}"
            )

            # ✅ BARRE 2S
            progress = await channel.send("```\n[░░░░░░░░░░] 0% — Initialisation...\n```")
            for i in range(1, 11):
                await asyncio.sleep(0.2)
                bars = "█" * i + "░" * (10 - i)
                pct = i * 10
                await progress.edit(content=f"```\n[{bars}] {pct}% — Création...\n```")
            await progress.edit(content="```\n[██████████] 100% — Ticket initialisé !\n```")
            await asyncio.sleep(1)
            await progress.delete()

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
                f"🔢 Ticket N° : **{ticket_number}**",
                f"🕒 Heure : **{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**",
                "───────────────────────────────────────",
                "▶️ En attente de prise en charge...",
                "",
                "Merci de détailler votre demande.",
                "Un membre du staff vous répondra sous 24-48h."
            ]
            await channel.send(content="\n".join(message_lines))

            async def claim_callback(i):
                if not i.user.guild_permissions.manage_channels:
                    await i.response.send_message("❌ Staff only.", ephemeral=True)
                    return
                await i.channel.send(f"🔷 **{i.user.mention} a pris en charge ce ticket.**")
                await i.response.defer()

            async def close_callback(i):
                if not i.user.guild_permissions.manage_channels:
                    await i.response.send_message("❌ Staff only.", ephemeral=True)
                    return
                await i.response.defer()
                await i.channel.edit(name=f"closed-{i.channel.name}")
                await i.channel.send("🔒 Suppression dans 24h.")

                if config["transcript_channel"]:
                    ch = self.bot.get_channel(int(config["transcript_channel"]))
                    if ch:
                        msgs = []
                        async for m in i.channel.history(limit=1000, oldest_first=True):
                            if m.type == discord.MessageType.default and not m.author.bot:
                                msgs.append(f"[{m.created_at.strftime('%H:%M')}] {m.author}: {m.content}")
                        if msgs:
                            await ch.send(f"📄 **Transcript — Ticket {ticket_number}**\n```txt\n" + "\n".join(msgs[:100]) + "\n```")

                # ✅ BARRE 24H
                prog = await i.channel.send("```\n[░░░░░░░░░░] 0% — Suppression...\n```")
                steps = 96
                for s in range(1, steps + 1):
                    await asyncio.sleep(900)
                    pct = int((s / steps) * 100)
                    filled = "█" * min(s, 10)
                    empty = "░" * max(0, 10 - s)
                    try:
                        await prog.edit(content=f"```\n[{filled}{empty}] {pct}% — Suppression...\n```")
                    except:
                        break
                try:
                    await i.channel.delete()
                except:
                    pass

            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="👤 Prendre en charge", style=discord.ButtonStyle.primary))
            view.add_item(discord.ui.Button(label="🔒 Fermer", style=discord.ButtonStyle.danger))

            for item in view.children:
                if item.label == "👤 Prendre en charge":
                    item.callback = claim_callback
                else:
                    item.callback = close_callback

            await channel.send(view=view)
            await interaction.followup.send(f"✅ Ticket **#{ticket_number}** créé : {channel.mention}", ephemeral=False)

        select.callback = select_callback
        embed = discord.Embed(
            title="🎫 **CENTRE D’ASSISTANCE**",
            description="Sélectionnez une catégorie ci-dessous.",
            color=0x2b2d31
        )
        embed.set_footer(text="By Seïko")
        view = discord.ui.View(timeout=None)
        view.add_item(select)
        await ctx.respond(embed=embed, view=view, ephemeral=False)

    @discord.slash_command(name="ticket_create", description="Créer un ticket dans un salon")
    async def ticket_create(self, ctx, salon: discord.TextChannel, category: discord.Option(str, choices=["Support", "Bug", "Autre"])):
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data["config"]:
            data["config"][guild_id] = {
                "categories": [],
                "ping_role": None,
                "ticket_counter": 1
            }
        config = data["config"][guild_id]

        # ✅ Vérifie ticket_counter
        if "ticket_counter" not in config:
            config["ticket_counter"] = 1
            save_data(data)

        ticket_number = config["ticket_counter"]
        config["ticket_counter"] = ticket_number + 1
        save_data(data)

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
                ping_line = f"<@&{role.id}>"

        channel = await ctx.guild.create_text_channel(
            name=f"{ticket_number}-{category}",
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
            f"🔢 Ticket N° : **{ticket_number}**",
            f"🕒 Heure : **{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**",
            "───────────────────────────────────────",
            "▶️ En attente...",
            "",
            "Merci de détailler votre demande."
        ]
        await channel.send(content="\n".join(message_lines))
        await ctx.respond(f"✅ Ticket **#{ticket_number}** : {channel.mention}", ephemeral=False)

    @discord.slash_command(name="ticket_transcript", description="Salon pour les transcripts")
    @commands.has_permissions(administrator=True)
    async def ticket_transcript(self, ctx, salon: discord.TextChannel):
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data["config"]:
            data["config"][guild_id] = {}
        data["config"][guild_id]["transcript_channel"] = str(salon.id)
        save_data(data)
        await ctx.respond(f"✅ Transcripts dans {salon.mention}.", ephemeral=False)

    @discord.slash_command(name="ticket_category_add", description="Ajouter une catégorie")
    @commands.has_permissions(administrator=True)
    async def ticket_category_add(self, ctx, nom: str, description: str, emoji: str):
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data["config"]:
            data["config"][guild_id] = {
                "categories": [],
                "ping_role": None,
                "ticket_counter": 1
            }
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
            return await ctx.respond("❌ Aucune config.", ephemeral=False)
        config = data["config"][guild_id]
        if "categories" not in config:
            config["categories"] = []
        before = len(config["categories"])
        config["categories"] = [c for c in config["categories"] if c["name"] != nom]
        if len(config["categories"]) == before:
            return await ctx.respond(f"❌ Catégorie `{nom}` introuvable.", ephemeral=False)
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