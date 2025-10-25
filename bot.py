import os
import discord
from discord.ext import commands
import sys

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("❌ ERREUR : TOKEN manquant dans les variables d'environnement.", file=sys.stderr)
    sys.exit(1)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} est en ligne sur {len(bot.guilds)} serveur(s).")
    try:
        synced = await bot.tree.sync()
        print(f"🌐 {len(synced)} commandes synchronisées.")
    except Exception as e:
        print(f"❌ Erreur de synchronisation : {e}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="/help"))

for filename in os.listdir("./cogs"):
    if filename.endswith(".py") and filename != "__init__.py":
        try:
            bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"📦 Cog chargé : {filename}")
        except Exception as e:
            print(f"❌ Erreur dans {filename}: {e}")

bot.run(TOKEN)