# cogs/bot_control.py
import discord
from discord.ext import commands

class BotControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="bot_on", description="Annoncer que le bot est en ligne")
    @commands.has_permissions(administrator=True)
    async def cmd_bot_on(self, ctx, rajout: str = ""):
        msg = "✅ **Le bot est de nouveau en ligne !**"
        if rajout:
            msg += f"\n> {rajout}"
        await ctx.channel.send(msg)

    @discord.slash_command(name="bot_off", description="Annoncer une maintenance")
    @commands.has_permissions(administrator=True)
    async def cmd_bot_off(self, ctx, raison: str, temps: str):
        await ctx.channel.send(f"⚠️ **Maintenance prévue**\nRaison : {raison}\nTemps estimé : {temps}")

    @discord.slash_command(name="bot_redem", description="Annoncer un redémarrage")
    @commands.has_permissions(administrator=True)
    async def cmd_bot_redem(self, ctx):
        await ctx.channel.send("🔄 **Redémarrage en cours...**")

    @discord.slash_command(name="bot_ping", description="Voir la latence")
    async def cmd_bot_ping(self, ctx):
        await ctx.respond(f"🏓 Pong ! `{round(self.bot.latency * 1000)} ms`")

def setup(bot):
    bot.add_cog(BotControl(bot))