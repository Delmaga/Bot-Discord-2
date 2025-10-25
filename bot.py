# bot.py
import discord
from discord.ext import commands
import json
import os

# Charger le token (en local ou depuis Railway)
if os.path.exists("config.json"):
    with open("config.json") as f:
        config = json.load(f)
    TOKEN = config["token"]
else:
    TOKEN = os.getenv("TOKEN")  # Pour Railway

# Intents complets (nécessaires pour les logs, modération, etc.)
intents = discord.Intents.all()
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None,
    case_insensitive=True
)

# Charger tous les cogs
@bot.event
async def on_ready():
    print(f"✅ {bot.user} est en ligne !")
    print(f"🔗 Connecté à {len(bot.guilds)} serveur(s)")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="/bypass"))

# Auto-load des cogs
for filename in os.listdir("./cogs"):
    if filename.endswith(".py") and filename != "__init__.py":
        try:
            bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"📦 Cog chargé : {filename}")
        except Exception as e:
            print(f"❌ Erreur chargement {filename}: {e}")

# Lancer le bot
bot.run(TOKEN)