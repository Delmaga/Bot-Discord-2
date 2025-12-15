# cogs/stats.py
import discord
from discord.ext import commands
import datetime

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="stats", description="📊 Statistiques du serveur et du bot")
    async def stats(self, ctx):
        guild = ctx.guild
        if not guild:
            return await ctx.respond("❌ Commande utilisable uniquement dans un serveur.", ephemeral=False)

        # Données
        total_members = guild.member_count
        humans = sum(1 for m in guild.members if not m.bot)
        bots = total_members - humans
        channels = len(guild.channels)
        roles = len(guild.roles)
        ping = round(self.bot.latency * 1000)

        # Titre encadré
        title = "STATISTIQUES DU SERVEUR"
        title_line = f"✨ {title}"
        width = max(len(title_line), 30)  # Largeur minimale
        top = "┌" + "─" * width + "┐"
        middle = "│ " + title_line.ljust(width - 1) + "│"
        bottom = "└" + "─" * width + "┘"

        # Embed
        embed = discord.Embed(
            description=(
                f"```\n{top}\n{middle}\n{bottom}\n```\n"
                f"📁 **Serveur**\n"
                f"👥 Membres : `{total_members:,}`\n"
                f"🧑 Humains : `{humans:,}`\n"
                f"🤖 Bots : `{bots:,}`\n"
                f"📚 Salons : `{channels}`\n"
                f"🎭 Rôles : `{roles}`\n\n"
                f"🤖 **Bot**\n"
                f"📡 Latence : `{ping} ms`\n"
                f"🕒 Uptime : En ligne"
            ),
            color=0x2b2d31  # Fond invisible (gris foncé de Discord)
        )

        # Footer
        embed.set_footer(text=f"Demandé par {ctx.author}", icon_url=ctx.author.display_avatar.url)

        # Thumbnail = logo du serveur
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        await ctx.respond(embed=embed, ephemeral=False)

def setup(bot):
    bot.add_cog(Stats(bot))
    