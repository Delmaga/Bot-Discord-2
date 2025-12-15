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
        self.config_path = "data/moderation_config.json"
        self.data = load_json(self.data_path, {"bans": {}, "mutes": {}, "warns": {}})
        self.config = load_json(self.config_path, {})

    def parse_time(self, time_str):
        total = 0
        for amount, unit in re.findall(r'(\d+)([dhms])', time_str.lower()):
            amount = int(amount)
            total += amount * {'d': 86400, 'h': 3600, 'm': 60, 's': 1}[unit]
        return total

    def get_log_channel(self, guild_id):
        cid = self.config.get(str(guild_id), {}).get("log_channel")
        return self.bot.get_channel(int(cid)) if cid else None

    @commands.slash_command(name="ban", description="Bannir un membre")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, membre: discord.Member, temps: str, raison: str):
        # ✅ Vérification : pas d'auto-modération
        if membre == ctx.author:
            return await ctx.respond("❌ Vous ne pouvez pas vous bannir vous-même.", ephemeral=True)

        # ✅ Vérification : pas d'admin
        if membre.guild_permissions.administrator:
            return await ctx.respond("❌ Vous ne pouvez pas bannir un administrateur.", ephemeral=True)

        # ✅ Raison minimale
        if len(raison.strip()) < 5:
            return await ctx.respond("❌ La raison doit faire au moins 5 caractères.", ephemeral=True)

        seconds = self.parse_time(temps)
        await membre.ban(reason=raison)

        # ✅ Sauvegarde
        self.data["bans"][str(membre.id)] = {
            "moderator": str(ctx.author.id),
            "reason": raison,
            "timestamp": datetime.utcnow().isoformat()
        }
        save_json(self.data_path, self.data)

        # ✅ Notification en MP
        try:
            await membre.send(
                f"⚠️ Vous avez été **banni** du serveur **{ctx.guild.name}**.\n"
                f"**Raison** : {raison}\n"
                f"**Durée** : {temps}\n\n"
                "Si vous pensez qu’il s’agit d’une erreur, contactez un administrateur."
            )
        except:
            pass

        # ✅ Log dans le salon dédié
        log_ch = self.get_log_channel(ctx.guild.id)
        if log_ch:
            await log_ch.send(
                f"🔨 **Ban** | {membre} ({membre.id})\n"
                f"📝 Raison : {raison}\n"
                f"👤 Modérateur : {ctx.author}"
            )

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

            # ✅ Log
            log_ch = self.get_log_channel(ctx.guild.id)
            if log_ch:
                await log_ch.send(f"🔓 **Unban** | {user} ({user.id})\n👤 Modérateur : {ctx.author}")

        except Exception as e:
            await ctx.respond("❌ Utilisateur non trouvé.")

    @commands.slash_command(name="mute", description="Muter un membre")
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, membre: discord.Member, temps: str, raison: str):
        # ✅ Vérification : pas d'auto-modération
        if membre == ctx.author:
            return await ctx.respond("❌ Vous ne pouvez pas vous muter vous-même.", ephemeral=True)

        # ✅ Vérification : pas d'admin
        if membre.guild_permissions.administrator:
            return await ctx.respond("❌ Vous ne pouvez pas muter un administrateur.", ephemeral=True)

        # ✅ Raison minimale
        if len(raison.strip()) < 5:
            return await ctx.respond("❌ La raison doit faire au moins 5 caractères.", ephemeral=True)

        seconds = self.parse_time(temps)
        await membre.timeout(datetime.utcnow() + timedelta(seconds=seconds), reason=raison)

        # ✅ Sauvegarde
        self.data["mutes"][str(membre.id)] = {
            "moderator": str(ctx.author.id),
            "reason": raison
        }
        save_json(self.data_path, self.data)

        # ✅ Notification en MP
        try:
            await membre.send(
                f"🔇 Vous avez été **muté** du serveur **{ctx.guild.name}**.\n"
                f"**Raison** : {raison}\n"
                f"**Durée** : {temps}\n\n"
                "Si vous pensez qu’il s’agit d’une erreur, contactez un administrateur."
            )
        except:
            pass

        # ✅ Log
        log_ch = self.get_log_channel(ctx.guild.id)
        if log_ch:
            await log_ch.send(
                f"🔇 **Mute** | {membre} ({membre.id})\n"
                f"⏱️ Durée : {temps}\n"
                f"📝 Raison : {raison}\n"
                f"👤 Modérateur : {ctx.author}"
            )

        await ctx.respond(f"✅ {membre.mention} muté pour {temps}. Raison : {raison}")

    @commands.slash_command(name="unmute", description="Démute un membre")
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, membre: discord.Member):
        # ✅ Vérification : pas d'auto-unmute
        if membre == ctx.author:
            return await ctx.respond("❌ Vous ne pouvez pas vous démuter vous-même.", ephemeral=True)

        await membre.timeout(None)
        self.data["mutes"].pop(str(membre.id), None)
        save_json(self.data_path, self.data)

        # ✅ Notification en MP
        try:
            await membre.send(f"🔊 Vous avez été **démuté** du serveur **{ctx.guild.name}**.")
        except:
            pass

        # ✅ Log
        log_ch = self.get_log_channel(ctx.guild.id)
        if log_ch:
            await log_ch.send(f"🔊 **Unmute** | {membre} ({membre.id})\n👤 Modérateur : {ctx.author}")

        await ctx.respond(f"✅ {membre.mention} démuté.")

    @commands.slash_command(name="warn", description="Avertir un membre")
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, membre: discord.Member, raison: str):
        # ✅ Vérification : pas d'auto-warn
        if membre == ctx.author:
            return await ctx.respond("❌ Vous ne pouvez pas vous avertir vous-même.", ephemeral=True)

        # ✅ Vérification : pas d'admin
        if membre.guild_permissions.administrator:
            return await ctx.respond("❌ Vous ne pouvez pas avertir un administrateur.", ephemeral=True)

        # ✅ Raison minimale
        if len(raison.strip()) < 5:
            return await ctx.respond("❌ La raison doit faire au moins 5 caractères.", ephemeral=True)

        gid = str(ctx.guild.id)
        uid = str(membre.id)

        if gid not in self.data["warns"]:
            self.data["warns"][gid] = {}
        if uid not in self.data["warns"][gid]:
            self.data["warns"][gid][uid] = []

        self.data["warns"][gid][uid].append({
            "moderator": str(ctx.author.id),
            "reason": raison,
            "timestamp": datetime.utcnow().isoformat()
        })
        save_json(self.data_path, self.data)

        # ✅ Notification en MP
        try:
            await membre.send(
                f"⚠️ Vous avez été **averti** sur le serveur **{ctx.guild.name}**.\n"
                f"**Raison** : {raison}\n\n"
                "Plusieurs avertissements peuvent mener à un ban ou un mute."
            )
        except:
            pass

        # ✅ Log
        log_ch = self.get_log_channel(ctx.guild.id)
        if log_ch:
            await log_ch.send(
                f"⚠️ **Warn** | {membre} ({membre.id})\n"
                f"📝 Raison : {raison}\n"
                f"👤 Modérateur : {ctx.author}"
            )

        await ctx.respond(f"✅ {membre.mention} averti : {raison}")

    @commands.slash_command(name="kick", description="Expulser un membre")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, membre: discord.Member, raison: str):
        # ✅ Vérification : pas d'auto-kick
        if membre == ctx.author:
            return await ctx.respond("❌ Vous ne pouvez pas vous expulser vous-même.", ephemeral=True)

        # ✅ Vérification : pas d'admin
        if membre.guild_permissions.administrator:
            return await ctx.respond("❌ Vous ne pouvez pas expulser un administrateur.", ephemeral=True)

        # ✅ Raison minimale
        if len(raison.strip()) < 5:
            return await ctx.respond("❌ La raison doit faire au moins 5 caractères.", ephemeral=True)

        await membre.kick(reason=raison)

        # ✅ Notification en MP
        try:
            await membre.send(
                f"🚪 Vous avez été **expulsé** du serveur **{ctx.guild.name}**.\n"
                f"**Raison** : {raison}\n\n"
                "Vous pouvez demander à être réinvité si vous le souhaitez."
            )
        except:
            pass

        # ✅ Log
        log_ch = self.get_log_channel(ctx.guild.id)
        if log_ch:
            await log_ch.send(
                f"🚪 **Kick** | {membre} ({membre.id})\n"
                f"📝 Raison : {raison}\n"
                f"👤 Modérateur : {ctx.author}"
            )

        await ctx.respond(f"✅ {membre.mention} expulsé. Raison : {raison}")

    @commands.slash_command(name="modlog", description="Voir l'historique de modération d'un membre")
    @commands.has_permissions(manage_guild=True)
    async def modlog(self, ctx, membre: discord.Member):
        gid = str(ctx.guild.id)
        uid = str(membre.id)
        warns = self.data["warns"].get(gid, {}).get(uid, [])
        if not warns:
            return await ctx.respond(f"📋 Aucun avertissement pour {membre}.", ephemeral=True)

        log_lines = [
            f"⚠️ **{w['reason']}** — <t:{int(datetime.fromisoformat(w['timestamp']).timestamp())}:R>"
            for w in warns
        ]
        await ctx.respond("\n".join(log_lines[:10]), ephemeral=True)

def setup(bot):
    bot.add_cog(Moderation(bot))