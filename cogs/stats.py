# cogs/stats.py
import discord
from discord.ext import commands
from datetime import datetime

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="stats", description="📊 Statistiques — Console Seïko")
    async def stats(self, ctx):
        guild = ctx.guild
        if not guild:
            return await ctx.respond("❌ Commande utilisable uniquement dans un serveur.", ephemeral=False)

        total_members = guild.member_count
        humans = sum(1 for m in guild.members if not m.bot)
        bots = total_members - humans
        channels = len(guild.channels)
        roles = len(guild.roles)
        ping = round(self.bot.latency * 1000)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = (
            f"[SERVER]    SYSTÈME DE SURVEILLANCE — SEÏKO                              {now}\n"
            f"[SERVER] Membre : {total_members}\n"
            f"[SERVER] Humains : {humans}\n"
            f"[SERVER] Bots : {bots}\n"
            f"[SERVER] Salons : {channels}\n"
            f"[SERVER] Rôles : {roles}\n"
            f"[SERVER] Latence : {ping} ms\n"
            f"[SERVER] Uptime : En ligne"
        )

        await ctx.respond(content, ephemeral=False)

def setup(bot):
    bot.add_cog(Stats(bot))