import discord
from discord.ext import commands

class Other(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="say", description="Faire parler le bot")
    @commands.has_permissions(administrator=True)
    async def say(self, ctx, salon: discord.TextChannel, message: str):
        await salon.send(message)
        await ctx.respond("✅ Message envoyé.")

    @commands.slash_command(name="say_dm", description="Envoyer un MP")
    @commands.has_permissions(administrator=True)
    async def say_dm(self, ctx, membre: discord.Member, message: str):
        try:
            await membre.send(message)
            await ctx.respond(f"✅ MP envoyé à {membre.mention}.")
        except:
            await ctx.respond("❌ Impossible d'envoyer le MP.")

    @commands.slash_command(name="help", description="Afficher l'aide")
    async def help(self, ctx):
        embed = discord.Embed(title="📚 Commandes du bot", color=0x5865F2)
        embed.add_field(name="🎫 Tickets", value="/ticket create, /close", inline=False)
        embed.add_field(name="📝 Logs", value="/logs message, modération, ticket", inline=False)
        embed.add_field(name="🔒 Modération", value="/ban, /mute, /warn, /kick", inline=False)
        embed.add_field(name="🎉 Giveaway", value="/giveaway create, end, list", inline=False)
        embed.add_field(name="⭐ Avis", value="/avis, /avis_stat", inline=False)
        embed.add_field(name="👋 Bienvenue", value="/welcome create, test, role", inline=False)
        embed.add_field(name="📊 Stats", value="/stats", inline=False)
        embed.add_field(name="🤖 Bot", value="/bot_on, /bot_off, /bot_ping", inline=False)
        embed.add_field(name="💬 Autre", value="/say, /say_dm", inline=False)
        await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(Other(bot))