# cogs/bypass.py
from discord.ext import commands
import discord
from discord.commands import Option
import json
import os

class BypassSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_path = "data/bypass.json"
        self.load_data()

    def load_data(self):
        os.makedirs("data", exist_ok=True)
        if os.path.exists(self.data_path):
            with open(self.data_path, "r", encoding="utf-8") as f:
                self.bypass_data = json.load(f)
        else:
            self.bypass_data = {}
            self.save_data()

    def save_data(self):
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(self.bypass_data, indent=4, ensure_ascii=False)

    def get_guild_data(self, guild_id):
        return self.bypass_data.get(str(guild_id), {})

    def set_guild_data(self, guild_id, data):
        self.bypass_data[str(guild_id)] = data
        self.save_data()

    bypass_group = discord.SlashCommandGroup("bypass", "Gérer les accès manuels aux salons")

    @bypass_group.command(name="add", description="Donner l'accès à un membre dans un salon (bypass)")
    async def bypass_add(
        self,
        ctx,
        membre: Option(discord.Member, "Membre à ajouter"),
        salon: Option(discord.TextChannel, "Salon concerné", required=False)
    ):
        channel = salon or ctx.channel
        if not isinstance(channel, discord.TextChannel):
            return await ctx.respond("❌ Ce n'est pas un salon textuel.", ephemeral=True)

        try:
            await channel.set_permissions(
                membre,
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            )
        except discord.Forbidden:
            return await ctx.respond("❌ Je n'ai pas la permission de modifier ce salon.", ephemeral=True)

        guild_id = str(ctx.guild.id)
        channel_id = str(channel.id)
        user_id = str(membre.id)

        guild_data = self.get_guild_data(ctx.guild.id)
        if channel_id not in guild_data:
            guild_data[channel_id] = []
        if user_id not in guild_data[channel_id]:
            guild_data[channel_id].append(user_id)
        self.set_guild_data(ctx.guild.id, guild_data)

        await ctx.respond(
            f"✅ Accès forcé accordé à {membre.mention} dans {channel.mention}.",
            allowed_mentions=discord.AllowedMentions(users=False)
        )

    @bypass_group.command(name="del", description="Retirer l'accès d'un membre dans un salon (bypass)")
    async def bypass_del(
        self,
        ctx,
        membre: Option(discord.Member, "Membre à retirer"),
        salon: Option(discord.TextChannel, "Salon concerné", required=False)
    ):
        channel = salon or ctx.channel
        if not isinstance(channel, discord.TextChannel):
            return await ctx.respond("❌ Ce n'est pas un salon textuel.", ephemeral=True)

        try:
            await channel.set_permissions(membre, overwrite=None)
        except discord.Forbidden:
            return await ctx.respond("❌ Je n'ai pas la permission de modifier ce salon.", ephemeral=True)

        guild_id = str(ctx.guild.id)
        channel_id = str(channel.id)
        user_id = str(membre.id)

        guild_data = self.get_guild_data(ctx.guild.id)
        if channel_id in guild_data and user_id in guild_data[channel_id]:
            guild_data[channel_id].remove(user_id)
            if not guild_data[channel_id]:
                del guild_data[channel_id]
            self.set_guild_data(ctx.guild.id, guild_data)

        await ctx.respond(
            f"✅ Accès retiré à {membre.mention} dans {channel.mention}.",
            allowed_mentions=discord.AllowedMentions(users=False)
        )

    @bypass_group.command(name="list", description="Liste les membres avec accès forcé dans un salon")
    async def bypass_list(
        self,
        ctx,
        salon: Option(discord.TextChannel, "Salon concerné", required=False)
    ):
        channel = salon or ctx.channel
        if not isinstance(channel, discord.TextChannel):
            return await ctx.respond("❌ Ce n'est pas un salon textuel.", ephemeral=True)

        guild_data = self.get_guild_data(ctx.guild.id)
        channel_id = str(channel.id)

        if channel_id not in guild_data or not guild_data[channel_id]:
            return await ctx.respond(f"📭 Aucun membre avec accès forcé dans {channel.mention}.", ephemeral=True)

        members = []
        for user_id in guild_data[channel_id]:
            member = ctx.guild.get_member(int(user_id))
            if member:
                members.append(f"- {member.mention} (`{member}`)")
            else:
                members.append(f"- ❌ Utilisateur supprimé (ID: {user_id})")

        embed = discord.Embed(
            title=f"🔐 Bypass - {channel.name}",
            description="\n".join(members),
            color=0x5865F2
        )
        embed.set_footer(text=f"Salon ID: {channel.id}")

        await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(BypassSystem(bot))