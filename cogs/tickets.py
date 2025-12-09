# cogs/tickets.py
import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta, timezone
import asyncio

def load_data():
    os.makedirs("data", exist_ok=True)
    path = "data/tickets_seiko_v8.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"config": {}, "tickets": {}}

def save_data(data):
    with open("data/tickets_seiko_v8.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="ticket", description="Ouvrir un ticket")
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
                "transcript_channel": None
            }
            save_data(data)

        config = data["config"][guild_id]
        options = [discord.SelectOption(label=cat["name"], description=cat["description"], emoji=cat["emoji"]) for cat in config["categories"]]

        select = discord.ui.Select(placeholder="Sélectionnez une catégorie", options=options)

        async def select_callback(interaction):
            category = interaction.data['values'][0]
            if interaction.user != ctx.author:
                await interaction.response.send_message("🔒 Accès restreint.", ephemeral=True)
                return

            # ✅ Chargement 0–100% (éphémère)
            progress_msg = await interaction.response.send_message("```\n[░░░░░░░░░░] 0% — Initialisation...\n```", ephemeral=True)
            for i in range(1, 11):
                await asyncio.sleep(0.1)
                bars = "█" * i + "░" * (10 - i)
                pct = i * 10
                await interaction.edit_original_response(content=f"```\n[{bars}] {pct}% — Création du ticket...\n```")
            await asyncio.sleep(0.2)
            await interaction.edit_original_response(content="```\n[██████████] 100% — Ticket créé !\n```")
            await asyncio.sleep(1)
            await interaction.delete_original_response()

            # ✅ Création du salon
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

            # ✅ Nom = Catégorie-ID
            channel = await guild.create_text_channel(f"{category}-{interaction.channel.id}", overwrites=overwrites)

            ticket_id = str(channel.id)
            data["tickets"][ticket_id] = {
                "user_id": str(user.id),
                "category": category,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "state": "OPEN",
                "channel_id": ticket_id
            }
            save_data(data)

            # ✅ Message dans le ticket (backticks only)
            msg = (
                "```\n"
                "TICKET — SEÏKO v8.0\n"
                "────────────────────\n"
                f"Catégorie : {category}\n"
                f"Utilisateur : {user.name}\n"
                f"Heure : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                "────────────────────\n"
                "En attente de prise en charge...\n"
                "```\n"
                "Merci de détailler votre demande. Réponse sous 24-48h."
            )
            await channel.send(content=ping_line)
            await channel.send(msg)

            # ✅ Bouton Fermer
            async def close_callback(i):
                if not i.user.guild_permissions.manage_channels:
                    await i.response.send_message("❌ Staff only.", ephemeral=True)
                    return

                await i.response.defer()
                await i.channel.edit(name=f"closed-{i.channel.name}")

                # ✅ Transfert du transcript
                transcript_channel_id = config.get("transcript_channel")
                if transcript_channel_id:
                    transcript_ch = self.bot.get_channel(int(transcript_channel_id))
                    if transcript_ch:
                        messages = []
                        async for msg in i.channel.history(limit=1000, oldest_first=True):
                            if msg.type == discord.MessageType.default and not msg.author.bot:
                                messages.append(f"[{msg.created_at.strftime('%H:%M')}] {msg.author}: {msg.content}")
                        if messages:
                            await transcript_ch.send(
                                f"📄 **Transcript — Ticket `{ticket_id}`**\n```txt\n" + "\n".join(messages[:100]) + "\n```"
                            )

                # ✅ Barre de suppression 24h (message public)
                progress = await i.channel.send("```\n[░░░░░░░░░░] 0% — Suppression dans 24h...\n```")
                total_steps = 24 * 4  # toutes les 15 min
                for step in range(1, total_steps + 1):
                    await asyncio.sleep(900)  # 15 min
                    pct = int((step / total_steps) * 100)
                    bars = "█" * (step) + "░" * (total_steps - step)
                    try:
                        await progress.edit(content=f"```\n[{bars[:10]}] {pct}% — Suppression en cours...\n```")
                    except:
                        break
                try:
                    await i.channel.delete()
                except:
                    pass

            view = discord.ui.View(timeout=None)
            close_btn = discord.ui.Button(label="🔴 Fermer", style=discord.ButtonStyle.danger)
            close_btn.callback = close_callback
            view.add_item(close_btn)
            await channel.send(view=view)

            await interaction.followup.send(f"✅ Ticket créé : {channel.mention}", ephemeral=False)

        select.callback = select_callback
        await ctx.respond("Sélectionnez une catégorie :", view=discord.ui.View().add_item(select), ephemeral=False)

    @discord.slash_command(name="ticket_transcript", description="Définir le salon pour les transcripts")
    @commands.has_permissions(administrator=True)
    async def ticket_transcript(self, ctx, salon: discord.TextChannel):
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data["config"]:
            data["config"][guild_id] = {}
        data["config"][guild_id]["transcript_channel"] = str(salon.id)
        save_data(data)
        await ctx.respond(f"✅ Transcripts activés dans {salon.mention}.", ephemeral=False)

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