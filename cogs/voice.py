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

    @discord.slash_command(name="voc", description="Créer une voc publique avec vocs temporaires staff-only")
    @commands.has_permissions(manage_channels=True)
    async def voc(self, ctx, nom: str, roles: str):
        """
        roles = IDs des rôles staff (séparés par des virgules)
        """
        role_ids = [rid.strip() for rid in roles.split(",") if rid.strip().isdigit()]
        if not role_ids:
            return await ctx.respond("❌ Veuillez fournir des ID de rôles valides.", ephemeral=True)

        valid_roles = []
        for rid in role_ids:
            role = ctx.guild.get_role(int(rid))
            if not role:
                return await ctx.respond(f"❌ Rôle non trouvé : `{rid}`", ephemeral=True)
            valid_roles.append(role)

        base_name = f"𓆩⟡𓆪🔴۰{nom}۰"

        # ✅ VOC PRINCIPALE : publique (tout le monde voit + rejoint)
        channel = await ctx.guild.create_voice_channel(
            name=base_name,
            reason=f"Voc publique par {ctx.author}"
        )

        self.config["channels"][str(channel.id)] = {
            "base_name": base_name,
            "guild_id": str(ctx.guild.id),
            "role_ids": [str(r.id) for r in valid_roles]
        }
        save_config(self.config)

        roles_list = ", ".join([r.mention for r in valid_roles])
        await ctx.respond(f"✅ Voc publique créée : `{base_name}`\n**Staff autorisés** : {roles_list}", ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # ✅ SI REJOINT LA VOC PRINCIPALE (publique)
        if after.channel and str(after.channel.id) in self.config["channels"]:
            config = self.config["channels"][str(after.channel.id)]
            base_name = config["base_name"]
            guild = after.channel.guild
            role_ids = config["role_ids"]

            # Crée la voc temporaire
            temp_channels = [
                ch for ch in guild.voice_channels
                if ch.name.startswith(base_name + " ") and ch.name != base_name
            ]
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

            # ✅ PERMISSIONS : voc temporaire = staff-only
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=False,  # ❌ Tout le monde ne voit PAS
                    connect=False
                )
            }
            for rid in role_ids:
                role = guild.get_role(int(rid))
                if role:
                    overwrites[role] = discord.PermissionOverwrite(
                        view_channel=True,  # ✅ Staff voit
                        connect=True        # ✅ Staff peut rejoindre
                    )

            new_channel = await guild.create_voice_channel(
                name=f"{base_name} {num}",
                overwrites=overwrites,
                category=after.channel.category,
                reason=f"Voc temporaire pour {member}"
            )

            # Déplace le client
            await member.edit(voice_channel=new_channel)

        # ✅ Supprime les vocs temporaires vides
        if before.channel and len(before.channel.members) == 0:
            for channel_id, config in self.config["channels"].items():
                base_name = config["base_name"]
                if (before.channel.name.startswith(base_name + " ") and 
                    before.channel.name != base_name):
                    await before.channel.delete(reason="Voc temporaire vide")
                    break

def setup(bot):
    bot.add_cog(VoiceSystem(bot))