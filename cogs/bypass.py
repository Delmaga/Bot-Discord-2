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

class BypassSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_path = "data/bypass.json"
        self.bypass_data = load_json(self.data_path, {})

    def get_guild_data(self, guild_id):
        return self.bypass_data.get(str(guild_id), {})

    def set_guild_data(self, guild_id, data):
        self.bypass_data[str(guild_id)] = data
        save_json(self.data_path, self.bypass_data)

    bypass = discord.SlashCommandGroup("bypass", "Gérer les accès manuels")

    @bypass.command(name="add", description="Donner l'accès à un membre dans un salon")
    async def add(self, ctx, membre: discord.Member, salon: discord.TextChannel = None):
        channel = salon or ctx.channel
        if not isinstance(channel, discord.TextChannel):
            return await ctx.respond("❌ Salon invalide.", ephemeral=True)
        try:
            await channel.set_permissions(membre, view_channel=True, send_messages=True)
        except discord.Forbidden:
            return await ctx.respond("❌ Permission refusée.", ephemeral=True)
        guild_id = str(ctx.guild.id)
        channel_id = str(channel.id)
        user_id = str(membre.id)
        guild_data = self.get_guild_data(ctx.guild.id)
        if channel_id not in guild_
            guild_data[channel_id] = []
        if user_id not in guild_data[channel_id]:
            guild_data[channel_id].append(user_id)
        self.set_guild_data(ctx.guild.id, guild_data)
        await ctx.respond(f"✅ Accès accordé à {membre.mention} dans {channel.mention}.", ephemeral=True)

    @bypass.command(name="del", description="Retirer l'accès d'un membre")
    async def delete(self, ctx, membre: discord.Member, salon: discord.TextChannel = None):
        channel = salon or ctx.channel
        if not isinstance(channel, discord.TextChannel):
            return await ctx.respond("❌ Salon invalide.", ephemeral=True)
        try:
            await channel.set_permissions(membre, overwrite=None)
        except discord.Forbidden:
            return await ctx.respond("❌ Permission refusée.", ephemeral=True)
        guild_id = str(ctx.guild.id)
        channel_id = str(channel.id)
        user_id = str(membre.id)
        guild_data = self.get_guild_data(ctx.guild.id)
        if channel_id in guild_data and user_id in guild_data[channel_id]:
            guild_data[channel_id].remove(user_id)
            if not guild_data[channel_id]:
                del guild_data[channel_id]
            self.set_guild_data(ctx.guild.id, guild_data)
        await ctx.respond(f"✅ Accès retiré à {membre.mention}.", ephemeral=True)

    @bypass.command(name="list", description="Lister les membres avec accès forcé")
    async def list_bypass(self, ctx, salon: discord.TextChannel = None):
        channel = salon or ctx.channel
        guild_data = self.get_guild_data(ctx.guild.id)
        channel_id = str(channel.id)
        if channel_id not in guild_data or not guild_data[channel_id]:
            return await ctx.respond("📭 Aucun membre avec accès forcé.", ephemeral=True)
        members = []
        for uid in guild_data[channel_id]:
            member = ctx.guild.get_member(int(uid))
            if member:
                members.append(f"- {member.mention}")
            else:
                members.append(f"- ID: {uid}")
        embed = discord.Embed(title="🔐 Membres en bypass", description="\n".join(members), color=0x5865F2)
        await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(BypassSystem(bot))