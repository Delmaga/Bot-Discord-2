# === COMMANDES SLASH (en groupe) ===
ticket = discord.SlashCommandGroup("ticket", "Gérer les tickets — SEÏKO v4.0")

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @ticket.command(name="create", description="Ouvrir un ticket")
    async def ticket_create(self, ctx, category: discord.Option(str, choices=["Support", "Bug", "Autre"])):
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data["config"]:
            data["config"][guild_id] = {"ping_role": None, "footer": "By Seïko • v4.0"}
            save_data(data)

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True, manage_channels=True)
        }

        ping_line = ""
        role_id = data["config"][guild_id]["ping_role"]
        if role_id:
            role = ctx.guild.get_role(int(role_id))
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                ping_line = f"{role.mention}"

        channel = await ctx.guild.create_text_channel(
            name=f"ticket-{ctx.author.name}",
            overwrites=overwrites,
            reason=f"Ticket ouvert par {ctx.author}"
        )

        ticket_id = str(channel.id)
        data["tickets"][ticket_id] = {
            "user_id": str(ctx.author.id),
            "category": category,
            "created_at": datetime.now(datetime.timezone.utc).isoformat(),
            "state": "OPEN"
        }
        save_data(data)

        message_lines = [
            "🟦 **TICKET — Seïko**",
            ping_line,
            "───────────────────────────────────────",
            f"📁 Catégorie : {category}",
            f"👤 Utilisateur : {ctx.author.name}",
            f"🕒 Heure : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "───────────────────────────────────────",
            "▶️ En attente de prise en charge...",
            "",
            "Merci de détailler votre demande.",
            "Un membre du staff vous répondra sous 24-48h."
        ]

        await channel.send(content="\n".join(message_lines))
        await ctx.respond(f"✅ Ticket créé : {channel.mention}", ephemeral=False)

    @ticket.command(name="category-add", description="Ajouter une catégorie")
    @commands.has_permissions(administrator=True)
    async def ticket_category_add(self, ctx, nom: str, description: str, emoji: str):
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data["config"]:
            data["config"][guild_id] = {"categories": [], "ping_role": None}
        config = data["config"][guild_id]
        if "categories" not in config:
            config["categories"] = []
        config["categories"].append({"name": nom, "description": description, "emoji": emoji})
        data["config"][guild_id] = config
        save_data(data)
        await ctx.respond(f"✅ Catégorie `{nom}` ajoutée.", ephemeral=False)

    @ticket.command(name="category-del", description="Supprimer une catégorie")
    @commands.has_permissions(administrator=True)
    async def ticket_category_del(self, ctx, nom: str):
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data["config"]:
            return await ctx.respond("❌ Aucune configuration.", ephemeral=False)
        config = data["config"][guild_id]
        if "categories" not in config:
            config["categories"] = []
        before = len(config["categories"])
        config["categories"] = [c for c in config["categories"] if c["name"] != nom]
        if len(config["categories"]) == before:
            return await ctx.respond(f"❌ Catégorie `{nom}` non trouvée.", ephemeral=False)
        data["config"][guild_id] = config
        save_data(data)
        await ctx.respond(f"✅ Catégorie `{nom}` supprimée.", ephemeral=False)

    @ticket.command(name="category-edit", description="Modifier une catégorie")
    @commands.has_permissions(administrator=True)
    async def ticket_category_edit(self, ctx, nom: str, nouveau_nom: str, nouvelle_description: str, nouveaux_emojis: str):
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data["config"]:
            return await ctx.respond("❌ Aucune configuration.", ephemeral=False)
        config = data["config"][guild_id]
        if "categories" not in config:
            config["categories"] = []
        for cat in config["categories"]:
            if cat["name"] == nom:
                cat["name"] = nouveau_nom
                cat["description"] = nouvelle_description
                cat["emoji"] = nouveaux_emojis
                data["config"][guild_id] = config
                save_data(data)
                return await ctx.respond(f"✅ Catégorie mise à jour.", ephemeral=False)
        await ctx.respond(f"❌ Catégorie `{nom}` non trouvée.", ephemeral=False)

    @ticket.command(name="ping", description="Définir le rôle staff")
    @commands.has_permissions(administrator=True)
    async def ticket_ping(self, ctx, role: discord.Role):
        data = load_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data["config"]:
            data["config"][guild_id] = {}
        data["config"][guild_id]["ping_role"] = role.id
        save_data(data)
        await ctx.respond(f"✅ Rôle de ping : {role.mention}", ephemeral=False)

def setup(bot):
    bot.add_cog(TicketSystem(bot))
    bot.add_cog(TicketHandler(bot))