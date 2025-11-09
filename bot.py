# bot.py
import os
import discord
import sys

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("❌ TOKEN manquant", file=sys.stderr)
    sys.exit(1)

intents = discord.Intents.all()
bot = discord.Bot(intents=intents)  # ← CECI EST OBLIGATOIRE

@bot.event
async def on_ready():
    print("✅ Gestion Seïko#3167 en ligne.")
    synced = await bot.tree.sync()
    print(f"🌐 {len(synced)} commandes synchronisées.")

for filename in os.listdir("./cogs"):
    if filename.endswith(".py") and filename != "__init__.py":
        try:
            bot.load_extension(f"cogs.{filename[:-3]}")
        except Exception as e:
            print(f"❌ Erreur {filename}: {e}")

bot.run(TOKEN)