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

        # === DONNÉES DU SERVEUR ===
        total_members = guild.member_count
        humans = sum(1 for m in guild.members if not m.bot)
        bots = total_members - humans
        channels = len(guild.channels)
        roles = len(guild.roles)

        # === DONNÉES DU BOT ===
        ping = round(self.bot.latency * 1000)

        # === EMBED PREMIUM ===
        embed = discord.Embed(
            title="",
            description=(
                "```ansi\n"
                "[2;34m┌──────────────────────────────┐[0m\n"
                "[2;34m│ [0m✨ [1;36mSTATISTIQUES DU SERVEUR [0m[2;34m │[0m\n"
                "[2;34m└──────────────────────────────┘[0m\n"
                "```"
            ),
            color=0x2b2d31,  # Gris foncé = invisible sur fond Discord
            timestamp=datetime.datetime.now(datetime.UTC)
        )

        # Serveur
        embed.add_field(
            name="📁 **Serveur**",
            value=f"👥 Membres : `{total_members:,}`\n"
                  f"🧑 Humains : `{humans:,}`\n"
                  f"🤖 Bots : `{bots:,}`\n"
                  f"📚 Salons : `{channels}`\n"
                  f"🎭 Rôles : `{roles}`",
            inline=True
        )

        # Bot
        embed.add_field(
            name="🤖 **Bot**",
            value=f"📡 Latence : `{ping} ms`\n"
                  f"🕒 Uptime : En ligne\n"
                  f"👾 Version : `1.0.0`",
            inline=True
        )

        # Ligne de séparation
        embed.add_field(
            name="\u200b",
            value="⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
            inline=False
        )

        # Footer
        embed.set_footer(
            text=f"Demandé par {ctx.author}",
            icon_url=ctx.author.display_avatar.url
        )

        # Thumbnail = logo du serveur
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        await ctx.respond(embed=embed, ephemeral=False)

def setup(bot):
    bot.add_cog(Stats(bot))