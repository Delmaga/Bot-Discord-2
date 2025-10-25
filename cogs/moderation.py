# cogs/moderation.py
import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import re

def load_json(path, default):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_path = "data/moderation.json"
        self.data = load_json(self.data_path, {"bans": {}, "mutes": {}, "warns": {}})

    def parse_time(self, time_str):
        total = 0
        for amount, unit in re.findall(r'(\d+)([dhms])', time_str.lower()):
            amount = int(amount)
            total += amount * {'d': 86400, 'h': 3600, 'm': 60, 's': 1}[unit]
        return total

    @commands.slash_command(name="ban", description="Bannir un membre")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, membre: discord.Member, temps: str, raison: str):
        seconds = self.parse_time(temps)
        await membre.ban(reason=raison)
        self.data["bans"][str(membre.id)] = {"moderator": str(ctx.author.id), "reason": raison, "timestamp": datetime.utcnow().isoformat()}
        save_json(self.data_path, self.data)
        await ctx.respond(f"✅ {membre.mention} banni pour {temps}. Raison : {raison}")

    @commands.slash_command(name="unban", description="Débannir un utilisateur")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: str):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await ctx.guild.unban(user)
            self.data["bans"].pop(user_id, None)
            save_json(self.data_path, self.data)
            await ctx.respond(f"✅ {user} débanni.")
        except:
            await ctx.respond("❌ Utilisateur non trouvé.")

    @commands.slash_command(name="mute", description="Muter un membre")
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, membre: discord.Member, temps: str, raison: str):
        seconds = self.parse_time(temps)
        await membre.timeout(datetime.utcnow() + timedelta(seconds=seconds), reason=raison)
        self.data["mutes"][str(membre.id)] = {"moderator": str(ctx.author.id), "reason": raison}
        save_json(self.data_path, self.data)
        await ctx.respond(f"✅ {membre.mention} muté pour {temps}. Raison : {raison}")

    @commands.slash_command(name="unmute", description="Démute un membre")
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, membre: discord.Member):
        await membre.timeout(None)
        self.data["mutes"].pop(str(membre.id), None)
        save_json(self.data_path, self.data)
        await ctx.respond(f"✅ {membre.mention} démuté.")

    @commands.slash_command(name="warn", description="Avertir un membre")
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, membre: discord.Member, raison: str):
        gid = str(ctx.guild.id)
        uid = str(membre.id)
        if gid not in self.data["warns"]:
            self.data["warns"][gid] = {}
        if uid not in self.data["warns"][gid]:
            self.data["warns"][gid][uid] = []
        self.data["warns"][gid][uid].append({"moderator": str(ctx.author.id), "reason": raison, "timestamp": datetime.utcnow().isoformat()})
        save_json(self.data_path, self.data)
        await ctx.respond(f"✅ {membre.mention} averti : {raison}")

    @commands.slash_command(name="kick", description="Expulser un membre")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, membre: discord.Member, raison: str):
        await membre.kick(reason=raison)
        await ctx.respond(f"✅ {membre.mention} expulsé. Raison : {raison}")

def setup(bot):
    bot.add_cog(Moderation(bot))