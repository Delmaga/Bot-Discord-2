import discord
from discord.ext import commands
import json
import os

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

class AvisSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_path = "data/avis.json"
        self.avis = load_json(self.data_path, {})

    @commands.slash_command(name="avis", description="Donner un avis")
    async def avis(self, ctx, étoiles: discord.Option(int, min_value=1, max_value=5), description: str):
        gid = str(ctx.guild.id)
        if gid not in self.avis:
            self.avis[gid] = []
        self.avis[gid].append({"user": str(ctx.author.id), "stars": étoiles, "desc": description})
        save_json(self.data_path, self.avis)
        stars_display = "⭐" * étoiles + "☆" * (5 - étoiles)
        await ctx.respond(f"✅ Avis soumis :\n{stars_display}\n\"{description}\"")

    @commands.slash_command(name="avis_stat", description="Voir la moyenne des avis")
    async def avis_stat(self, ctx):
        gid = str(ctx.guild.id)
        if gid not in self.avis or not self.avis[gid]:
            return await ctx.respond("📭 Aucun avis.")
        total = sum(item["stars"] for item in self.avis[gid])
        avg = total / len(self.avis[gid])
        await ctx.respond(f"⭐ **Moyenne des avis** : {avg:.2f}/5 ({len(self.avis[gid])} avis)")

def setup(bot):
    bot.add_cog(AvisSystem(bot))