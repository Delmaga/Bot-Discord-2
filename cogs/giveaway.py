# cogs/giveaway.py
import discord
from discord.ext import commands
import json
import os
import random
import re
from datetime import datetime

def load_json(path, default):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            return json.loads(content) if content else default
    return default

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Vue avec bouton "Participer"
class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_id):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id
        self.add_item(discord.ui.Button(
            label="🎉 Participer",
            style=discord.ButtonStyle.green,
            custom_id=f"gw_join_{giveaway_id}"
        ))

# Écouteur global pour le bouton
class GiveawayHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id", "")
        if not custom_id.startswith("gw_join_"):
            return

        giveaway_id = custom_id.replace("gw_join_", "")
        guild_id = str(interaction.guild.id)
        giveaways = load_json("data/giveaways.json", {})

        # Vérifier que le giveaway existe et n'est pas terminé
        if guild_id not in giveaways or giveaway_id not in giveaways[guild_id]:
            return await interaction.response.send_message("❌ Ce giveaway n'existe plus.", ephemeral=True)

        giveaway = giveaways[guild_id][giveaway_id]
        if giveaway.get("ended", False):
            return await interaction.response.send_message("✅ Ce giveaway est terminé.", ephemeral=True)

        user_id = str(interaction.user.id)
        if user_id in giveaway["participants"]:
            return await interaction.response.send_message("✅ Vous participez déjà !", ephemeral=True)

        giveaway["participants"].append(user_id)
        save_json("data/giveaways.json", giveaways)
        await interaction.response.send_message("✅ Participation enregistrée !", ephemeral=True)

class GiveawaySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def parse_time(self, time_str):
        total = 0
        matches = re.findall(r'(\d+)([dhms])', time_str.lower())
        for value, unit in matches:
            value = int(value)
            total += value * {'d': 86400, 'h': 3600, 'm': 60, 's': 1}[unit]
        return total

    giveaway = discord.SlashCommandGroup("giveaway", "Gérer les giveaways")

    @giveaway.command(name="create", description="Créer un giveaway")
    @commands.has_permissions(manage_guild=True)
    async def create(self, ctx, titre: str, description: str, temps: str, gagnants: int, salon: discord.TextChannel = None):
        seconds = self.parse_time(temps)
        if seconds <= 0:
            return await ctx.respond("❌ Format de temps invalide. Ex: `2h30m`", ephemeral=True)

        end_timestamp = int((datetime.now().timestamp() + seconds))
        channel = salon or ctx.channel

        # Sauvegarder le giveaway
        giveaways = load_json("data/giveaways.json", {})
        guild_id = str(ctx.guild.id)
        if guild_id not in giveaways:
            giveaways[guild_id] = {}

        giveaway_id = str(end_timestamp)  # ID unique basé sur l'heure de fin
        giveaways[guild_id][giveaway_id] = {
            "title": titre,
            "description": description,
            "end_time": end_timestamp,
            "winners": gagnants,
            "channel_id": str(channel.id),
            "participants": [],
            "ended": False
        }
        save_json("data/giveaways.json", giveaways)

        # Envoyer l'embed
        embed = discord.Embed(
            title=titre,
            description=description,
            color=0x5865F2
        )
        embed.add_field(name="Gagnants", value=str(gagnants))
        embed.add_field(name="Fin", value=f"<t:{end_timestamp}:R>")
        embed.set_footer(text="Cliquez sur 🎉 Participer ci-dessous !")

        view = GiveawayView(giveaway_id)
        await channel.send(embed=embed, view=view)
        await ctx.respond("✅ Giveaway lancé !", ephemeral=True)

    @giveaway.command(name="end", description="Terminer un giveaway maintenant")
    @commands.has_permissions(manage_guild=True)
    async def end(self, ctx, giveaway_id: str):
        giveaways = load_json("data/giveaways.json", {})
        guild_id = str(ctx.guild.id)

        if guild_id not in giveaways or giveaway_id not in giveaways[guild_id]:
            return await ctx.respond("❌ Giveaway introuvable.", ephemeral=True)

        giveaway = giveaways[guild_id][giveaway_id]
        if giveaway["ended"]:
            return await ctx.respond("✅ Ce giveaway est déjà terminé.", ephemeral=True)

        giveaway["ended"] = True
        save_json("data/giveaways.json", giveaways)

        # Tirage
        channel = self.bot.get_channel(int(giveaway["channel_id"]))
        if not channel:
            return await ctx.respond("❌ Salon introuvable.", ephemeral=True)

        valid_participants = []
        for uid in giveaway["participants"]:
            member = channel.guild.get_member(int(uid))
            if member:
                valid_participants.append(member)

        if not valid_participants:
            result = "❌ Aucun participant valide."
        else:
            winners = random.sample(valid_participants, min(giveaway["winners"], len(valid_participants)))
            winner_mentions = " ".join([w.mention for w in winners])
            result = f"🎉 **Félicitations** : {winner_mentions} !"

        await channel.send(f"**Résultat du giveaway : {giveaway['title']}**\n{result}")
        await ctx.respond("✅ Giveaway terminé et résultats publiés.", ephemeral=True)

    @giveaway.command(name="list", description="Liste des giveaways actifs")
    @commands.has_permissions(manage_guild=True)
    async def list_giveaways(self, ctx):
        giveaways = load_json("data/giveaways.json", {})
        guild_id = str(ctx.guild.id)

        if guild_id not in giveaways or not giveaways[guild_id]:
            return await ctx.respond("📭 Aucun giveaway actif.", ephemeral=True)

        lines = []
        for gwid, gw in giveaways[guild_id].items():
            status = "✅ Terminé" if gw["ended"] else "⏳ Actif"
            lines.append(f"- **{gw['title']}** ({status}) — Fin : <t:{gw['end_time']}:R>")

        embed = discord.Embed(title="🎁 Giveaways", description="\n".join(lines[:10]), color=0x5865F2)
        await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(GiveawayHandler(bot))  # Pour gérer les boutons
    bot.add_cog(GiveawaySystem(bot))   # Pour les commandes