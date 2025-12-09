# bot.py
import os
import discord
import sys

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("❌ TOKEN manquant", file=sys.stderr)
    sys.exit(1)

intents = discord.Intents.all()
bot = discord.Bot(intents=intents)  # ← Obligatoire

@bot.event
async def on_ready():
    print("✅ Seïko en ligne.")
    await bot.sync_commands()  # ← CORRECTION ICI
    print("🌐 Commandes synchronisées.")

for filename in os.listdir("./cogs"):
    if filename.endswith(".py") and filename != "__init__.py":
        try:
            bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"📦 {filename} chargé")
        except Exception as e:
            print(f"❌ Erreur {filename}: {e}")

bot.run(TOKEN)