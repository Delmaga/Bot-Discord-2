# bot.py - TEST MINIMAL
import os
import discord

print("✅ Script lancé")

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("❌ ERREUR : TOKEN manquant")
else:
    print("🟢 TOKEN présent")

intents = discord.Intents.all()
bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} est en ligne !")

bot.run(TOKEN)