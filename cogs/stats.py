# cogs/stats.py
import discord
from discord.ext import commands
import psutil
import platform
import datetime

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="stats", description="📊 Statistiques du bot et du serveur")
    async def stats(self, ctx):
        # === DONNÉES DU SERVEUR ===
        guild = ctx.guild
        if not guild:
            return await ctx.respond("❌ Commande utilisable uniquement dans un serveur.", ephemeral=False)

        member_count = guild.member_count
        human_count = sum(1 for m in guild.members if not m.bot)
        bot_count = member_count - human_count
        channel_count = len(guild.channels)
        role_count = len(guild.roles)

        # === DONNÉES DU BOT ===
        ping = round(self.bot.latency * 1000)
        uptime = "En ligne"
        python_version = platform.python_version()
        discord_version = discord.__version__

        # === EMBED PRINCIPAL ===
        embed = discord.Embed(
            title="✨ **Statistiques du Serveur & du Bot**",
            color=0x002366,  # Bleu marine profond
            timestamp=datetime.datetime.utcnow()
        )

        file = discord.File("data/border.png", filename="border.png")
        embed.set_image(url="attachment://border.png")
        await ctx.respond(embed=embed, file=file, ephemeral=False)

        # Serveur
        embed.add_field(
            name="📁 **Serveur**",
            value=(
                f"👥 **Membres** : `{member_count:,}`\n"
                f"🧑 **Humains** : `{human_count:,}`\n"
                f"🤖 **Bots** : `{bot_count:,}`\n"
                f"📚 **Salons** : `{channel_count}`\n"
                f"🎭 **Rôles** : `{role_count}`"
            ),
            inline=True
        )

        # Bot
        embed.add_field(
            name="🤖 **Bot**",
            value=(
                f"📡 **Latence** : `{ping} ms`\n"
                f"🕒 **Uptime** : `{uptime}`\n"
                f"🐍 **Python** : `{python_version}`\n"
                f"👾 **discord.py** : `{discord_version}`"
            ),
            inline=True
        )

        # Barre décorative
        embed.add_field(
            name="\u200b",
            value="⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
            inline=False
        )

        # Footer élégant
        embed.set_footer(
            text="Demandé par " + ctx.author.name,
            icon_url=ctx.author.display_avatar.url
        )

        # Thumbnail = logo du serveur
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        # Réponse publique
        await ctx.respond(embed=embed, ephemeral=False)

def setup(bot):
    bot.add_cog(Stats(bot))