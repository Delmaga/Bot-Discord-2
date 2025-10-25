import discord
from discord.ext import commands

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="stats", description="Statistiques du bot")
    async def stats(self, ctx):
        embed = discord.Embed(title="📊 Statistiques", color=0x5865F2)
        embed.add_field(name="Ping", value=f"{round(self.bot.latency * 1000)} ms", inline=False)
        embed.add_field(name="Serveurs", value=str(len(self.bot.guilds)), inline=True)
        if ctx.guild:
            embed.add_field(name="Membres", value=str(ctx.guild.member_count), inline=True)
            embed.add_field(name="Rôles", value=str(len(ctx.guild.roles)), inline=True)
            bots = sum(1 for m in ctx.guild.members if m.bot)
            embed.add_field(name="Bots", value=str(bots), inline=True)
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Stats(bot))