# cogs/voice.py
import discord
from discord.ext import commands
import json
import os

def load_config():
    os.makedirs("data", exist_ok=True)
    path = "data/voice_config.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"channels": {}}

def save_config(data):
    with open("data/voice_config.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

class VoiceSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()

    @discord.slash_command(name="voc", description="Créer un salon vocal dynamique")
    @commands.has_permissions(manage_channels=True)
    async def voc(self, ctx, nom: str = "Assistance"):
        base_name = f"𓆩⟡𓆪🔴۰{nom}۰"
        channel = await ctx.guild.create_voice_channel(
            name=base_name,
            reason=f"Voc dynamique par {ctx.author}"
        )
        self.config["channels"][str(channel.id)] = {
            "base_name": base_name,
            "guild_id": str(ctx.guild.id)
        }
        save_config(self.config)
        await ctx.respond(f"✅ Voc principale créée : `{base_name}`", ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # 1. SI L'UTILISATEUR REJOINT UNE VOC PRINCIPALE
        if after.channel and str(after.channel.id) in self.config["channels"]:
            config = self.config["channels"][str(after.channel.id)]
            base_name = config["base_name"]
            guild = after.channel.guild

            # Liste TOUTES les voc temporaires existantes (même vides)
            temp_channels = [
                ch for ch in guild.voice_channels
                if ch.name.startswith(base_name + " ") and ch.name != base_name
            ]

            # Trouve le premier numéro libre (1, 2, 3...)
            used_numbers = set()
            for ch in temp_channels:
                try:
                    num = int(ch.name.split()[-1])
                    used_numbers.add(num)
                except:
                    pass

            num = 1
            while num in used_numbers:
                num += 1

            # Crée la nouvelle voc
            new_channel = await guild.create_voice_channel(
                name=f"{base_name} {num}",
                category=after.channel.category,
                reason=f"Voc temporaire pour {member}"
            )

            # Déplace l'utilisateur
            await member.edit(voice_channel=new_channel)

        # 2. SI UNE VOC TEMPORAIRE DEVIENT VIDE → SUPPRIME-LA
        if before.channel and len(before.channel.members) == 0:
            for channel_id, config in self.config["channels"].items():
                base_name = config["base_name"]
                # Vérifie si c'est une voc temporaire (et non la principale)
                if (before.channel.name.startswith(base_name + " ") and 
                    before.channel.name != base_name):
                    await before.channel.delete(reason="Voc temporaire vide")
                    break

def setup(bot):
    bot.add_cog(VoiceSystem(bot))