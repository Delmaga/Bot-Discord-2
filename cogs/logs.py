# cogs/logs.py
import discord
from discord.ext import commands
import json
import os
from datetime import datetime

def load_json(path, default):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

class LogsSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = "data/logs_config.json"
        self.config = load_json(self.config_path, {})

    def get_log_channel(self, guild_id, log_type):
        guild_data = self.config.get(str(guild_id), {})
        channel_id = guild_data.get(log_type)
        return self.bot.get_channel(int(channel_id)) if channel_id else None

    async def send_log(self, guild_id, log_type, embed):
        channel = self.get_log_channel(guild_id, log_type)
        if channel:
            try:
                await channel.send(embed=embed)
            except:
                pass

    logs = discord.SlashCommandGroup("logs", "Configuration des logs")

    @logs.command(name="message", description="Salon pour les logs de messages")
    @commands.has_permissions(administrator=True)
    async def message(self, ctx, salon: discord.TextChannel):
        gid = str(ctx.guild.id)
        if gid not in self.config:
            self.config[gid] = {}
        self.config[gid]["message"] = str(salon.id)
        save_json(self.config_path, self.config)
        await ctx.respond(f"✅ Logs messages → {salon.mention}", ephemeral=True)

    @logs.command(name="modération", description="Salon pour les logs de modération")
    @commands.has_permissions(administrator=True)
    async def moderation(self, ctx, salon: discord.TextChannel):
        gid = str(ctx.guild.id)
        if gid not in self.config:
            self.config[gid] = {}
        self.config[gid]["moderation"] = str(salon.id)
        save_json(self.config_path, self.config)
        await ctx.respond(f"✅ Logs modération → {salon.mention}", ephemeral=True)

    @logs.command(name="ticket", description="Salon pour les logs de tickets")
    @commands.has_permissions(administrator=True)
    async def ticket(self, ctx, salon: discord.TextChannel):
        gid = str(ctx.guild.id)
        if gid not in self.config:
            self.config[gid] = {}
        self.config[gid]["ticket"] = str(salon.id)
        save_json(self.config_path, self.config)
        await ctx.respond(f"✅ Logs tickets → {salon.mention}", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        embed = discord.Embed(
            title="📥 Message envoyé",
            description=f"**Auteur** : {message.author.mention}\n**Salon** : {message.channel.mention}\n**Contenu** : {message.content[:1000]}",
            color=0x5865F2,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"ID: {message.id}")
        await self.send_log(message.guild.id, "message", embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or not before.guild or before.content == after.content:
            return
        embed = discord.Embed(
            title="✏️ Message modifié",
            description=f"**Auteur** : {before.author.mention}\n**Avant** : {before.content[:500]}\n**Après** : {after.content[:500]}",
            color=0xFEE75C,
            timestamp=datetime.utcnow()
        )
        await self.send_log(before.guild.id, "message", embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild:
            return
        embed = discord.Embed(
            title="🗑️ Message supprimé",
            description=f"**Auteur** : {message.author.mention}\n**Contenu** : {message.content[:1000]}",
            color=0xED4245,
            timestamp=datetime.utcnow()
        )
        await self.send_log(message.guild.id, "message", embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if not hasattr(channel, 'guild'):
            return
        embed = discord.Embed(title="🆕 Salon créé", description=f"**{channel.name}**", color=0x57F287, timestamp=datetime.utcnow())
        await self.send_log(channel.guild.id, "moderation", embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if not hasattr(channel, 'guild'):
            return
        embed = discord.Embed(title="❌ Salon supprimé", description=f"**{channel.name}**", color=0xED4245, timestamp=datetime.utcnow())
        await self.send_log(channel.guild.id, "moderation", embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        embed = discord.Embed(title="➕ Rôle créé", description=f"**{role.name}**", color=0x57F287, timestamp=datetime.utcnow())
        await self.send_log(role.guild.id, "moderation", embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        embed = discord.Embed(title="➖ Rôle supprimé", description=f"**{role.name}**", color=0xED4245, timestamp=datetime.utcnow())
        await self.send_log(role.guild.id, "moderation", embed)

def setup(bot):
    bot.add_cog(LogsSystem(bot))