# cogs/stats.py
import discord
from discord.ext import commands
import asyncio
import random

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="stats", description="📊 Statistiques — Seïko Quantum Display")
    async def stats(self, ctx):
        guild = ctx.guild
        if not guild:
            return await ctx.respond("❌ Commande utilisable uniquement dans un serveur.", ephemeral=False)

        # Données statiques
        total_members = guild.member_count
        humans = sum(1 for m in guild.members if not m.bot)
        bots = total_members - humans
        channels = len(guild.channels)
        roles = len(guild.roles)

        # ✅ Message initial (simulation de chargement)
        msg = await ctx.respond("```\n[░░░░░░░░░░] Connexion au système...\n```", ephemeral=False)
        await asyncio.sleep(0.5)

        # ✅ 3 mises à jour pour simuler la "latence vivante"
        for i in range(3):
            # Génère une latence aléatoire entre 25 et 75 ms
            fake_ping = random.randint(25, 75)

            content = (
                "```\n"
                "\u001b[2;36m |------------------------------------|\u001b[0m\n"
                "\u001b[2;36m |\u001b[0m \u001b[1;33mSYSTÈME DE SURVEILLANCE — SEÏKO\u001b[0m \u001b[2;36m║\u001b[0m\n"
                "\u001b[2;36m |------------------------------------|\u001b[0m\n"
                f"\u001b[2;36m|\u001b[0m 📁 \u001b[1;37mServeur\u001b[0m          \u001b[2;36m║\u001b[0m\n"
                f"\u001b[2;36m|\u001b[0m 👥 Membres : \u001b[1;33m{total_members:,}\u001b[0m     \u001b[2;36m║\u001b[0m\n"
                f"\u001b[2;36m|\u001b[0m 🧑 Humains  : \u001b[1;32m{humans:,}\u001b[0m      \u001b[2;36m║\u001b[0m\n"
                f"\u001b[2;36m|\u001b[0m 🤖 Bots     : \u001b[1;31m{bots:,}\u001b[0m        \u001b[2;36m║\u001b[0m\n"
                f"\u001b[2;36m|\u001b[0m 📚 Salons   : \u001b[1;36m{channels}\u001b[0m         \u001b[2;36m║\u001b[0m\n"
                f"\u001b[2;36m|\u001b[0m 🎭 Rôles    : \u001b[1;35m{roles}\u001b[0m         \u001b[2;36m║\u001b[0m\n"
                "\u001b[2;36m |------------------------------------|\u001b[0m\n"
                f"\u001b[2;36m|\u001b[0m 🤖 \u001b[1;37mBot\u001b[0m               \u001b[2;36m║\u001b[0m\n"
                f"\u001b[2;36m|\u001b[0m 📡 Latence  : \u001b[1;33m{fake_ping} ms\u001b[0m      \u001b[2;36m║\u001b[0m\n"
                f"\u001b[2;36m|\u001b[0m 🕒 Uptime   : \u001b[1;32mEn ligne\u001b[0m       \u001b[2;36m║\u001b[0m\n"
                "\u001b[2;36m |------------------------------------|\u001b[0m\n"
                "```"
            )
            await msg.edit(content=content)
            await asyncio.sleep(0.4)

        # ✅ Dernière mise à jour : latence réelle
        real_ping = round(self.bot.latency * 1000)
        final_content = (
            "```\n"
            "\u001b[2;36m |------------------------------------|\u001b[0m\n"
            "\u001b[2;36m |\u001b[0m \u001b[1;33mSYSTÈME DE SURVEILLANCE — SEÏKO\u001b[0m \u001b[2;36m║\u001b[0m\n"
            "\u001b[2;36m |------------------------------------|\u001b[0m\n"
            f"\u001b[2;36m|\u001b[0m 📁 \u001b[1;37mServeur\u001b[0m          \u001b[2;36m║\u001b[0m\n"
            f"\u001b[2;36m|\u001b[0m 👥 Membres : \u001b[1;33m{total_members:,}\u001b[0m     \u001b[2;36m║\u001b[0m\n"
            f"\u001b[2;36m|\u001b[0m 🧑 Humains  : \u001b[1;32m{humans:,}\u001b[0m      \u001b[2;36m║\u001b[0m\n"
            f"\u001b[2;36m|\u001b[0m 🤖 Bots     : \u001b[1;31m{bots:,}\u001b[0m        \u001b[2;36m║\u001b[0m\n"
            f"\u001b[2;36m|\u001b[0m 📚 Salons   : \u001b[1;36m{channels}\u001b[0m         \u001b[2;36m║\u001b[0m\n"
            f"\u001b[2;36m|\u001b[0m 🎭 Rôles    : \u001b[1;35m{roles}\u001b[0m         \u001b[2;36m║\u001b[0m\n"
            "\u001b[2;36m |-----------------------------------|\u001b[0m\n"
            f"\u001b[2;36m|\u001b[0m 🤖 \u001b[1;37mBot\u001b[0m               \u001b[2;36m║\u001b[0m\n"
            f"\u001b[2;36m|\u001b[0m 📡 Latence  : \u001b[1;33m{real_ping} ms\u001b[0m      \u001b[2;36m║\u001b[0m\n"
            f"\u001b[2;36m|\u001b[0m 🕒 Uptime   : \u001b[1;32mEn ligne\u001b[0m       \u001b[2;36m║\u001b[0m\n"
            "\u001b[2;36m |-----------------------------------|\u001b[0m\n"
            "```"
        )
        await msg.edit(content=final_content)

def setup(bot):
    bot.add_cog(Stats(bot))