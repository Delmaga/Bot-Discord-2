# bot.py
import os
import discord

TOKEN = os.getenv("TOKEN")
intents = discord.Intents.all()
bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print("✅ Bot en ligne")
    await bot.tree.sync()  # ← Fonctionne uniquement avec discord.Bot

@bot.slash_command()
async def test(ctx):
    await ctx.respond("✅ Ça marche !")

bot.run(TOKEN)