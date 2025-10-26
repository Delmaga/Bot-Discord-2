# cogs/stats.py
import discord
from discord.ext import commands
import datetime

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="stats", description="📊 Statistiques du serveur & du bot")
    async def stats(self, ctx):
        guild = ctx.guild
        if not guild:
            return await ctx.respond("❌ Commande utilisable uniquement dans un serveur.", ephemeral=False)

        # === DONNÉES ===
        total_members = guild.member_count
        humans = sum(1 for m in guild.members if not m.bot)
        bots = total_members - humans
        channels = len(guild.channels)
        roles = len(guild.roles)
        ping = round(self.bot.latency * 1000)

        # === EMBED STYLÉ ===
        embed = discord.Embed(
            title="",
            description="```ansi\n"
                        "[2;34m┌──────────────────────────────┐[0m\n"
                        "[2;34m│ [0m✨ [1;36mSTATISTIQUES DU SERVEUR [0m[2;34m │[0m\n"
                        "[2;34m└──────────────────────────────┘[0m\n"
                        "```",
            color=0x000000  # Noir pour fond sombre
        )

        # Serveur
        embed.add_field(
            name="```ansi\n[2;34m📁 SERVEUR[0m```",
            value="```ansi\n"
                  f"[2;37m👥 Membres : [0m[1;33m{total_members:,}[0m\n"
                  f"[2;37m🧑 Humains  : [0m[1;32m{humans:,}[0m\n"
                  f"[2;37m🤖 Bots     : [0m[1;31m{bots:,}[0m\n"
                  f"[2;37m📚 Salons   : [0m[1;36m{channels}[0m\n"
                  f"[2;37m🎭 Rôles    : [0m[1;35m{roles}[0m\n"
                  "```",
            inline=True
        )

        # Bot
        embed.add_field(
            name="```ansi\n[2;34m🤖 BOT[0m```",
            value="```ansi\n"
                  f"[2;37m📡 Latence  : [0m[1;33m{ping} ms[0m\n"
                  f"[2;37m🕒 Uptime   : [0m[1;32mEn ligne[0m\n"
                  f"[2;37m👾 Version  : [0m[1;36m1.0.0[0m\n"
                  "```",
            inline=True
        )

        # Footer
        embed.set_footer(
            text=f"• BY {ctx.author} •",
            icon_url=ctx.author.display_avatar.url
        )

        # Thumbnail = logo du serveur
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        await ctx.respond(embed=embed, ephemeral=False)

def setup(bot):
    bot.add_cog(Stats(bot))