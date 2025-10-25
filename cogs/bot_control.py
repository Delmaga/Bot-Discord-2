import discord
from discord.ext import commands
import os

class BotControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="bot_on", description="Annoncer que le bot est en ligne")
    @commands.slash_command(name="bot_on")
    async def cmd_bot_on(self, ctx, ...):  # ← nom interne différent
        msg = "✅ **Le bot est de nouveau en ligne !**"
        if rajout:
            msg += f"\n> {rajout}"
        await ctx.channel.send(msg)

    @commands.slash_command(name="bot_off", description="Annoncer une maintenance")
    @commands.has_permissions(administrator=True)
    async def bot_off(self, ctx, raison: str, temps: str):
        await ctx.channel.send(f"⚠️ **Maintenance prévue**\nRaison : {raison}\nTemps estimé : {temps}")

    @commands.slash_command(name="bot_redem", description="Annoncer un redémarrage")
    @commands.has_permissions(administrator=True)
    async def bot_redem(self, ctx):
        await ctx.channel.send("🔄 **Redémarrage en cours...**")

    @commands.slash_command(name="bot_ping", description="Voir la latence")
    async def bot_ping(self, ctx):
        await ctx.respond(f"🏓 Pong ! `{round(self.bot.latency * 1000)} ms`")

def setup(bot):
    bot.add_cog(BotControl(bot))