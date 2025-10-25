import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta
import random

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

class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_id, bot):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id
        self.bot = bot
        self.add_item(discord.ui.Button(label="🎉 Participer", style=discord.ButtonStyle.green, custom_id=f"giveaway_join_{giveaway_id}"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.data["custom_id"].startswith("giveaway_join_"):
            return False
        gid = str(interaction.guild.id)
        giveaways = load_json("data/giveaways.json", {})
        if gid not in giveaways or self.giveaway_id not in giveaways[gid]:
            await interaction.response.send_message("❌ Ce giveaway n'existe plus.", ephemeral=True)
            return False
        giveaway = giveaways[gid][self.giveaway_id]
        if str(interaction.user.id) in giveaway["participants"]:
            await interaction.response.send_message("✅ Vous participez déjà !", ephemeral=True)
            return False
        giveaway["participants"].append(str(interaction.user.id))
        save_json("data/giveaways.json", giveaways)
        await interaction.response.send_message("✅ Participation enregistrée !", ephemeral=True)
        return True

class GiveawaySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_giveaways.start()

    def cog_unload(self):
        self.check_giveaways.cancel()

    @tasks.loop(seconds=30)
    async def check_giveaways(self):
        giveaways = load_json("data/giveaways.json", {})
        now = datetime.utcnow().timestamp()
        updated = False
        for gid, gws in list(giveaways.items()):
            for gwid, gw in list(gws.items()):
                if not gw.get("ended", False) and gw["end_time"] <= now:
                    gw["ended"] = True
                    channel = self.bot.get_channel(int(gw["channel_id"]))
                    if channel:
                        winners = []
                        valid_participants = [uid for uid in gw["participants"] if channel.guild.get_member(int(uid))]
                        if valid_participants and gw["winners"] > 0:
                            selected = random.sample(valid_participants, min(gw["winners"], len(valid_participants)))
                            winners = [f"<@{uid}>" for uid in selected]
                        result = "🎉 **Félicitations** : " + ", ".join(winners) if winners else "❌ Aucun participant."
                        await channel.send(f"**Résultat du giveaway : {gw['title']}**\n{result}")
                    updated = True
        if updated:
            save_json("data/giveaways.json", giveaways)

    giveaway = discord.SlashCommandGroup("giveaway", "Gérer les giveaways")

    @giveaway.command(name="create", description="Créer un giveaway")
    @commands.has_permissions(manage_guild=True)
    async def create(self, ctx, titre: str, description: str, temps: str, gagnants: int, salon: discord.TextChannel = None):
        seconds = 0
        for amount, unit in [("d", 86400), ("h", 3600), ("m", 60), ("s", 1)]:
            if amount in temps:
                parts = temps.split(amount)
                if parts[0].isdigit():
                    seconds += int(parts[0]) * unit
                    temps = amount.join(parts[1:])
        if seconds <= 0:
            return await ctx.respond("❌ Format de temps invalide. Ex: 2h30m", ephemeral=True)
        end_time = datetime.utcnow().timestamp() + seconds
        channel = salon or ctx.channel
        embed = discord.Embed(title=titre, description=description, color=0x5865F2)
        embed.add_field(name="Gagnants", value=str(gagnants))
        embed.add_field(name="Durée", value=f"<t:{int(end_time)}:R>")
        embed.set_footer(text="Cliquez sur 🎉 Participer ci-dessous !")
        view = GiveawayView(str(int(end_time * 1000)), self.bot)
        msg = await channel.send(embed=embed, view=view)
        giveaways = load_json("data/giveaways.json", {})
        gid = str(ctx.guild.id)
        if gid not in giveaways:
            giveaways[gid] = {}
        giveaways[gid][str(int(end_time * 1000))] = {
            "title": titre,
            "description": description,
            "end_time": end_time,
            "winners": gagnants,
            "channel_id": str(channel.id),
            "message_id": str(msg.id),
            "participants": [],
            "ended": False
        }
        save_json("data/giveaways.json", giveaways)
        await ctx.respond("✅ Giveaway lancé !", ephemeral=True)

    @giveaway.command(name="end", description="Terminer un giveaway")
    @commands.has_permissions(manage_guild=True)
    async def end(self, ctx, giveaway_id: str):
        giveaways = load_json("data/giveaways.json", {})
        gid = str(ctx.guild.id)
        if gid not in giveaways or giveaway_id not in giveaways[gid]:
            return await ctx.respond("❌ Giveaway introuvable.", ephemeral=True)
        giveaways[gid][giveaway_id]["end_time"] = datetime.utcnow().timestamp() - 1
        save_json("data/giveaways.json", giveaways)
        await ctx.respond("✅ Giveaway terminé manuellement.", ephemeral=True)

    @giveaway.command(name="list", description="Liste des giveaways")
    @commands.has_permissions(manage_guild=True)
    async def list_giveaways(self, ctx):
        giveaways = load_json("data/giveaways.json", {})
        gid = str(ctx.guild.id)
        if gid not in giveaways or not giveaways[gid]:
            return await ctx.respond("📭 Aucun giveaway.", ephemeral=True)
        lines = []
        for gwid, gw in giveaways[gid].items():
            status = "✅ Terminé" if gw["ended"] else "⏳ Actif"
            lines.append(f"- **{gw['title']}** ({status})")
        await ctx.respond("\n".join(lines[:10]), ephemeral=True)

def setup(bot):
    bot.add_cog(GiveawaySystem(bot))