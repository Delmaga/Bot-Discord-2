# bot.py
import os
import discord
import sys

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("❌ TOKEN manquant", file=sys.stderr)
    sys.exit(1)

intents = discord.Intents.all()
bot = discord.Bot(intents=intents)  # ← Obligatoire pour les slash commands

@bot.event
async def on_ready():
    print(f"✅ {bot.user} est en ligne sur {len(bot.guilds)} serveur(s).")
    try:
        synced = await bot.tree.sync()
        print(f"🌐 {len(synced)} commandes synchronisées.")
    except Exception as e:
        print(f"❌ Erreur sync : {e}")

# Charger les cogs
for filename in os.listdir("./cogs"):
    if filename.endswith(".py") and filename != "__init__.py":
        try:
            bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"📦 Cog chargé : {filename}")
        except Exception as e:
            print(f"❌ Erreur dans {filename}: {e}")

bot.run(TOKEN)