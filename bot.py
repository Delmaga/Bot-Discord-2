# bot.py
import os
import discord
import sys

# 🔒 Récupère le token depuis les variables d'environnement
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("❌ ERREUR : La variable d'environnement 'TOKEN' est manquante.", file=sys.stderr)
    sys.exit(1)

# 🎛️ Intents complets (nécessaires pour les logs, membres, etc.)
intents = discord.Intents.all()

# 🤖 Création du bot (obligatoirement discord.Bot pour les slash commands)
bot = discord.Bot(intents=intents)

# 📦 Chargement des cogs au démarrage
@bot.event
async def on_ready():
    print(f"✅ {bot.user} est en ligne sur {len(bot.guilds)} serveur(s).")
    try:
        # 🌐 Synchronisation globale des slash commands
        synced = await bot.tree.sync()
        print(f"🌐 {len(synced)} commandes synchronisées.")
    except Exception as e:
        print(f"❌ Erreur de synchronisation : {e}")
    # 🎮 Statut personnalisé
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="/help")
    )

# 🔌 Chargement automatique de tous les cogs dans le dossier 'cogs/'
for filename in os.listdir("./cogs"):
    if filename.endswith(".py") and filename != "__init__.py":
        try:
            bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"📦 Cog chargé : {filename}")
        except Exception as e:
            print(f"❌ Erreur lors du chargement de {filename}: {e}")

# 🚀 Lancement du bot
print("🚀 Démarrage du bot...")
bot.run(TOKEN)