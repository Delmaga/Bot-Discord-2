# cogs/stats.py
import discord
from discord.ext import commands
import asyncio
import random

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="stats", description="📊 Statistiques du serveur et du bot")
    async def stats(self, ctx):
        guild = ctx.guild
        if not guild:
            return await ctx.respond("❌ Commande utilisable uniquement dans un serveur.", ephemeral=False)

        total_members = guild.member_count
        humans = sum(1 for m in guild.members if not m.bot)
        bots = total_members - humans
        channels = len(guild.channels)
        roles = len(guild.roles)

        # ✅ Simulation de latence dynamique
        msg = await ctx.respond("```\n[░░░░░░░░░░] Chargement des données...\n```", ephemeral=False)
        await asyncio.sleep(0.4)

        for _ in range(3):
            fake_ping = random.randint(25, 75)
            content = (
                "```\n"
                "┌──────────────────────────────────────┐\n"
                "│       SYSTÈME DE SURVEILLANCE        │\n"
                "│              — SEÏKO —               │\n"
                "├──────────────────────────────────────┤\n"
                f"│ 📁 Serveur                           │\n"
                f"│ 👥 Membres : {total_members:<24} │\n"
                f"│ 🧑 Humains  : {humans:<24} │\n"
                f"│ 🤖 Bots     : {bots:<24} │\n"
                f"│ 📚 Salons   : {channels:<24} │\n"
                f"│ 🎭 Rôles    : {roles:<24} │\n"
                "├──────────────────────────────────────┤\n"
                f"│ 🤖 Bot                               │\n"
                f"│ 📡 Latence  : {fake_ping} ms{' ' * (21 - len(str(fake_ping)))} │\n"
                "│ 🕒 Uptime   : En ligne               │\n"
                "└──────────────────────────────────────┘\n"
                "```"
            )
            await msg.edit(content=content)
            await asyncio.sleep(0.4)

        # ✅ Dernière mise à jour : latence réelle
        real_ping = round(self.bot.latency * 1000)
        final_content = (
            "```\n"
            "┌──────────────────────────────────────┐\n"
            "│       SYSTÈME DE SURVEILLANCE        │\n"
            "│              — SEÏKO —               │\n"
            "├──────────────────────────────────────┤\n"
            f"│ 📁 Serveur                           │\n"
            f"│ 👥 Membres : {total_members:<24} │\n"
            f"│ 🧑 Humains  : {humans:<24} │\n"
            f"│ 🤖 Bots     : {bots:<24} │\n"
            f"│ 📚 Salons   : {channels:<24} │\n"
            f"│ 🎭 Rôles    : {roles:<24} │\n"
            "├──────────────────────────────────────┤\n"
            f"│ 🤖 Bot                               │\n"
            f"│ 📡 Latence  : {real_ping} ms{' ' * (21 - len(str(real_ping)))} │\n"
            "│ 🕒 Uptime   : En ligne               │\n"
            "└──────────────────────────────────────┘\n"
            "```"
        )
        await msg.edit(content=final_content)

def setup(bot):
    bot.add_cog(Stats(bot))