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
            content = f.read().strip()
            return json.loads(content) if content else default
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

    logs = discord.SlashCommandGroup("logs", "Configurer les salons de logs")

    @logs.command(name="message", description="Salon pour les logs de messages")
    @commands.has_permissions(administrator=True)
    async def message(self, ctx, salon: discord.TextChannel):
        gid = str(ctx.guild.id)
        if gid not in self.config:
            self.config[gid] = {}
        self.config[gid]["message"] = str(salon.id)
        save_json(self.config_path, self.config)
        embed = discord.Embed(
            description=f"✅ **Logs messages** → {salon.mention}",
            color=0x57F287
        )
        await ctx.respond(embed=embed, ephemeral=False)

    @logs.command(name="modération", description="Salon pour les logs de modération")
    @commands.has_permissions(administrator=True)
    async def moderation(self, ctx, salon: discord.TextChannel):
        gid = str(ctx.guild.id)
        if gid not in self.config:
            self.config[gid] = {}
        self.config[gid]["moderation"] = str(salon.id)
        save_json(self.config_path, self.config)
        embed = discord.Embed(
            description=f"✅ **Logs modération** → {salon.mention}",
            color=0x57F287
        )
        await ctx.respond(embed=embed, ephemeral=False)

    @logs.command(name="ticket", description="Salon pour les logs de tickets")
    @commands.has_permissions(administrator=True)
    async def ticket(self, ctx, salon: discord.TextChannel):
        gid = str(ctx.guild.id)
        if gid not in self.config:
            self.config[gid] = {}
        self.config[gid]["ticket"] = str(salon.id)
        save_json(self.config_path, self.config)
        embed = discord.Embed(
            description=f"✅ **Logs tickets** → {salon.mention}",
            color=0x57F287
        )
        await ctx.respond(embed=embed, ephemeral=False)

    # ========== LOGS MESSAGES ==========
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        embed = discord.Embed(
            title="",
            description="```ansi\n"
                        "[2;34m┌──────────────────────────────┐[0m\n"
                        "[2;34m│ [0m📥 [1;36mMESSAGE ENVOYÉ [0m[2;34m │[0m\n"
                        "[2;34m└──────────────────────────────┘[0m\n"
                        "```",
            color=0x2b2d31,
            timestamp=datetime.utcnow()
        )
        embed.add_field(
            name="```ansi\n[2;37m👤 AUTEUR[0m```",
            value=f"{message.author.mention}",
            inline=True
        )
        embed.add_field(
            name="```ansi\n[2;37m# SALON[0m```",
            value=f"{message.channel.mention}",
            inline=True
        )
        embed.add_field(
            name="```ansi\n[2;37m💬 CONTENU[0m```",
            value=f"```{message.content[:500]}```" if message.content else "*(Pièce jointe)*",
            inline=False
        )
        embed.set_footer(text=f"ID: {message.id}")
        await self.send_log(message.guild.id, "message", embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or not before.guild or before.content == after.content:
            return
        embed = discord.Embed(
            title="",
            description="```ansi\n"
                        "[2;34m┌──────────────────────────────┐[0m\n"
                        "[2;34m│ [0m✏️ [1;36mMESSAGE MODIFIÉ [0m[2;34m │[0m\n"
                        "[2;34m└──────────────────────────────┘[0m\n"
                        "```",
            color=0xFEE75C,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="```ansi\n[2;37mAvant[0m```", value=f"```{before.content[:250]}```", inline=False)
        embed.add_field(name="```ansi\n[2;37mAprès[0m```", value=f"```{after.content[:250]}```", inline=False)
        embed.set_footer(text=f"Auteur: {before.author} • ID: {before.id}")
        await self.send_log(before.guild.id, "message", embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild:
            return
        embed = discord.Embed(
            title="",
            description="```ansi\n"
                        "[2;34m┌──────────────────────────────┐[0m\n"
                        "[2;34m│ [0m🗑️ [1;36mMESSAGE SUPPRIMÉ [0m[2;34m │[0m\n"
                        "[2;34m└──────────────────────────────┘[0m\n"
                        "```",
            color=0xED4245,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="```ansi\n[2;37mAuteur[0m```", value=message.author.mention, inline=True)
        embed.add_field(name="```ansi\n[2;37mSalon[0m```", value=message.channel.mention, inline=True)
        embed.add_field(name="```ansi\n[2;37mContenu[0m```", value=f"```{message.content[:500]}```", inline=False)
        embed.set_footer(text=f"ID: {message.id}")
        await self.send_log(message.guild.id, "message", embed)

    # ========== LOGS MODÉRATION ==========
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if not hasattr(channel, 'guild'):
            return
        embed = discord.Embed(
            title="",
            description="```ansi\n"
                        "[2;34m┌──────────────────────────────┐[0m\n"
                        "[2;34m│ [0m🆕 [1;36mSALON CRÉÉ [0m[2;34m │[0m\n"
                        "[2;34m└──────────────────────────────┘[0m\n"
                        "```",
            color=0x57F287,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="```ansi\n[2;37mNom[0m```", value=f"`{channel.name}`", inline=True)
        embed.add_field(name="```ansi\n[2;37mType[0m```", value=type(channel).__name__, inline=True)
        await self.send_log(channel.guild.id, "moderation", embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        embed = discord.Embed(
            title="",
            description="```ansi\n"
                        "[2;34m┌──────────────────────────────┐[0m\n"
                        "[2;34m│ [0m➕ [1;36mRÔLE CRÉÉ [0m[2;34m │[0m\n"
                        "[2;34m└──────────────────────────────┘[0m\n"
                        "```",
            color=0x57F287,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="```ansi\n[2;37mRôle[0m```", value=role.mention, inline=True)
        embed.add_field(name="```ansi\n[2;37mCouleur[0m```", value=str(role.color), inline=True)
        await self.send_log(role.guild.id, "moderation", embed)

def setup(bot):
    bot.add_cog(LogsSystem(bot))