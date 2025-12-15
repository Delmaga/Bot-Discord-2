# cogs/welcome.py
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

class WelcomeSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = "data/welcome.json"
        self.config = load_json(self.config_path, {})

    @commands.Cog.listener()
    async def on_member_join(self, member):
        gid = str(member.guild.id)
        if gid not in self.config:
            return

        cfg = self.config[gid]
        channel = self.bot.get_channel(int(cfg["channel"]))
        if not channel:
            return

        # ✅ Mention de l'utilisateur ici
        welcome_message = cfg.get("description", "Bienvenue sur le serveur, ??!")
        welcome_message = welcome_message.replace("???", member.mention)  # Optionnel

        embed = discord.Embed(
            title=cfg.get("title", "Bienvenue !"),
            description=welcome_message,
            color=0x5865F2
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Merci de nous rejoindre !")

        # ✅ Envoie le message avec la mention
        await channel.send(member.mention, embed=embed)

        # Ajouter les rôles
        for rid in cfg.get("roles", []):
            role = member.guild.get_role(int(rid))
            if role:
                await member.add_roles(role)

    welcome = discord.SlashCommandGroup("welcome", "Configurer le message de bienvenue")

    @welcome.command(name="create", description="Configurer le message de bienvenue")
    @commands.has_permissions(administrator=True)
    async def create(self, ctx, titre: str, description: str, salon: discord.TextChannel):
        gid = str(ctx.guild.id)
        self.config[gid] = {
            "title": titre,
            "description": description,  # Tu peux utiliser ??? ou laisser vide
            "channel": str(salon.id),
            "roles": []
        }
        save_json(self.config_path, self.config)
        await ctx.respond(f"✅ Bienvenue configuré dans {salon.mention}.", ephemeral=False)

    @welcome.command(name="role", description="Ajouter un rôle à donner à l'arrivée")
    @commands.has_permissions(administrator=True)
    async def role(self, ctx, rôle: discord.Role):
        gid = str(ctx.guild.id)
        if gid not in self.config:
            return await ctx.respond("❌ Configure d'abord le message avec `/welcome create`.", ephemeral=False)
        if "roles" not in self.config[gid]:
            self.config[gid]["roles"] = []
        if str(rôle.id) not in self.config[gid]["roles"]:
            self.config[gid]["roles"].append(str(rôle.id))
        save_json(self.config_path, self.config)
        await ctx.respond(f"✅ Rôle {rôle.mention} ajouté.", ephemeral=False)

    @welcome.command(name="test", description="Tester le message de bienvenue")
    @commands.has_permissions(administrator=True)
    async def test(self, ctx):
        gid = str(ctx.guild.id)
        if gid not in self.config:
            return await ctx.respond("❌ Bienvenue non configuré.", ephemeral=False)
        cfg = self.config[gid]
        embed = discord.Embed(
            title=cfg.get("title", "Bienvenue !"),
            description=cfg.get("description", "").replace("???", ctx.author.mention),
            color=0x5865F2
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text="Test de bienvenue")
        await ctx.send(ctx.author.mention, embed=embed)
        await ctx.respond("✅ Test envoyé.", ephemeral=True)

def setup(bot):
    bot.add_cog(WelcomeSystem(bot))