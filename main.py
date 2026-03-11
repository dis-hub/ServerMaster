import discord
from discord import app_commands, ChannelType, guild, ui
from discord.ui import View, Button, Select, Modal, TextInput
from discord.ext import commands, tasks
import os
import asyncio
import random
import re
import json
import requests
import time
from datetime import datetime, timedelta
import io
from discord.utils import utcnow
import math
from dotenv import load_dotenv
load_dotenv()

intents = discord.Intents.all()


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="+", intents=intents, help_command=None)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"Systèmes synchronisés pour {self.user}")

bot = MyBot()

OWNER_IDS = [1447233337830936807, 1477344366769999913]


def is_team_owner():
    async def predicate(ctx):
        return ctx.author.id in OWNER_IDS
    return commands.check(predicate)

async def update_status():
    guild_count = len(bot.guilds)
    activity = discord.CustomActivity(
        name=f"/help - {guild_count} server"
    )
    await bot.change_presence(
        status=discord.Status.online,  
        activity=activity
    ) 


@bot.event
async def on_ready():
    print('Le bot est prêt !')
    await update_status()



@bot.event
async def on_guild_join(guild):
    await update_status()


@bot.event
async def on_guild_remove(guild):
    await update_status()


@bot.command()
@is_team_owner()
async def statut(ctx, mode: str, *, texte: str = None):
    mode = mode.lower()
    
    status_map = {
        "online": discord.Status.online,
        "idle": discord.Status.idle,
        "dnd": discord.Status.dnd,
        "invisible": discord.Status.invisible,
        "live": discord.Status.online
    }

    new_status = status_map.get(mode, discord.Status.online)
    
    activity = None
    if texte:
        if mode == "live":
            activity = discord.Streaming(name=texte, url="https://www.twitch.tv/discord")
        else:
            activity = discord.Game(name=texte)


    await bot.change_presence(status=f"{new_status}", activity=activity)
    
    if texte:
        message_confirm = f"Statut **{mode}** défini avec : *{texte}*"
    else:
        message_confirm = f"Statut **{mode}** défini."
        
    await ctx.send(message_confirm)




@bot.command()
@commands.has_permissions(manage_nicknames=True)
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"Latence: `{latency}ms`")


LOG_CHANNEL_ID = 1481343685340692683

@bot.event
async def on_guild_join(guild: discord.Guild):
    # Génère un lien d'invitation depuis le premier salon disponible
    invite_url = None
    for channel in guild.text_channels:
        try:
            invite = await channel.create_invite(max_age=0, max_uses=0, unique=False)
            invite_url = invite.url
            break
        except discord.Forbidden:
            continue

    embed = discord.Embed(
        title="🎉 Nouveau serveur rejoint !",
        color=0x5865F2
    )
    embed.add_field(name="Nom du serveur", value=guild.name, inline=False)
    embed.add_field(
        name="Lien d'invitation",
        value=invite_url if invite_url else "❌ Impossible de générer un lien",
        inline=False
    )
    embed.add_field(name="Membres", value=str(guild.member_count), inline=True)
    embed.add_field(name="ID du serveur", value=str(guild.id), inline=True)

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    embed.set_footer(text=f"Bot ajouté à {guild.name}")

    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(embed=embed)
    else:
        print(f"⚠️ Salon de log introuvable (ID: {LOG_CHANNEL_ID})")



@bot.command()
@is_team_owner()
async def regle(ctx):
    embed = discord.Embed(
        title="*DISCORD HUB | SERVER RULES*",
        url="https://dis-hub.github.io/",
        description="**1. General Conduct**\n> `-` **Respect is Key** : Treat all members, staff, and guests with respect. No hate speech, racism, sexism, or harassment will be tolerated.\n\n> `-` **No Toxicity** : Avoid arguments, drama, or provocative behavior. If you have a conflict, take it to DMs or contact a Moderator.\n\n> `-` **Language** : Please use English or French in all public channels to ensure everyone can understand and participate.\n\n**2. Chat & Content**\n> `-` **No Spamming** : Do not flood the chat with symbols, emojis, caps, or repetitive messages.\n\n> `-` **Right Channel** : Use the appropriate channels for their intended purpose. (Check the channel descriptions!)\n\n> `-` **No NSFW** : This is a SFW (Safe For Work) server. No adult content, gore, or suggestive material is allowed.\n\n> `-` **External Links** : Do not post suspicious links, screamers, or any form of malware.\n\n**3. Advertising & Promotion**\n> `-` **No Self-Promotion** : Do not DM members or post invite links/advertisements without official partnership or permission from the Staff.\n\n> `-` **No Begging** : Do not ask for Nitro, roles, or money.\n\n**4. Enforcement**\n> `-` **Follow Discord ToS** : You must comply with the [Discord Community Guidelines](https://discord.com/guidelines)\n\n> `-` **Staff Authority** : The Staff team has the final say in all matters. Bypassing a mute or ban with an alt account will result in a permanent ban.\n\n**Need Assistance?**\nIf you have questions or need to report a member, please head over to <#1480830542311198730>",
        color=0x5865F2
    )

    await ctx.send(embed=embed)

@bot.command()
async def test(ctx):
    await ctx.send("Test")


setup_data = {}

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS — Formatage des noms
# ──────────────────────────────────────────────────────────────────────────────

def format_category(fmt, name):
    return {
        "fire":    f"🔥 | {name.upper()}",
        "dash":    f"━━━ {name.upper()} ━━━",
        "bracket": f"[ {name.upper()} ]",
        "arrow":   f"» {name.upper()}",
        "plain":   name.upper(),
    }.get(fmt, name.upper())

def format_channel(fmt, name):
    slug = name.lower().replace(" ", "-")
    return {
        "fire":    f"🔹｜{slug}",
        "dash":    f"─ {slug}",
        "bracket": f"▸ {slug}",
        "arrow":   f"» {slug}",
        "plain":   slug,
    }.get(fmt, slug)

# ──────────────────────────────────────────────────────────────────────────────
# TEMPLATES — Catégories & Salons par type
# ──────────────────────────────────────────────────────────────────────────────

ALL_TEMPLATES = {
    "gaming": [
        {"name": "INFORMATIONS", "staff_only": False, "channels": [
            {"name": "annonces",    "type": "text",  "topic": "📢 Annonces officielles"},
            {"name": "règles",      "type": "text",  "topic": "📜 Les règles du serveur"},
            {"name": "rôles",       "type": "text",  "topic": "🎭 Choisissez vos rôles"},
        ]},
        {"name": "GÉNÉRAL", "staff_only": False, "channels": [
            {"name": "général",         "type": "text",  "topic": "💬 Discussion générale"},
            {"name": "gaming",          "type": "text",  "topic": "🎮 Parlez de vos jeux"},
            {"name": "clips-screens",   "type": "text",  "topic": "🖼️ Partagez vos moments"},
            {"name": "blagues-memes",   "type": "text",  "topic": "😂 LMAO"},
        ]},
        {"name": "GAMING", "staff_only": False, "channels": [
            {"name": "LFG",         "type": "text",  "topic": "🔍 Cherche partenaires"},
            {"name": "tournois",    "type": "text",  "topic": "🏆 Tournois & compétitions"},
            {"name": "classements", "type": "text",  "topic": "📊 Vos ranks"},
        ]},
        {"name": "VOCAL", "staff_only": False, "channels": [
            {"name": "Gaming 1",    "type": "voice"},
            {"name": "Gaming 2",    "type": "voice"},
            {"name": "Gaming 3",    "type": "voice"},
            {"name": "Musique 🎵",  "type": "voice"},
            {"name": "AFK",         "type": "voice"},
        ]},
        {"name": "EVENTS", "staff_only": False, "channels": [
            {"name": "événements",  "type": "text",  "topic": "🎉 Événements à venir"},
            {"name": "giveaways",   "type": "text",  "topic": "🎁 Giveaways"},
            {"name": "Event Voice", "type": "voice"},
        ]},
        {"name": "STAFF", "staff_only": True, "channels": [
            {"name": "staff-général",   "type": "text",  "topic": "🛠️ Salon privé staff"},
            {"name": "sanctions",       "type": "text",  "topic": "🔨 Log des sanctions"},
            {"name": "logs-bot",        "type": "text",  "topic": "🤖 Logs automatiques"},
            {"name": "Staff Vocal",     "type": "voice"},
        ]},
    ],
    "community": [
        {"name": "INFORMATIONS", "staff_only": False, "channels": [
            {"name": "annonces",        "type": "text",  "topic": "📢 Annonces officielles"},
            {"name": "règles",          "type": "text",  "topic": "📜 Les règles du serveur"},
            {"name": "rôles",           "type": "text",  "topic": "🎭 Choisissez vos rôles"},
            {"name": "partenariats",    "type": "text",  "topic": "🤝 Partenaires du serveur"},
        ]},
        {"name": "COMMUNAUTÉ", "staff_only": False, "channels": [
            {"name": "général",         "type": "text",  "topic": "💬 Discussion générale"},
            {"name": "présentations",   "type": "text",  "topic": "👋 Présentez-vous !"},
            {"name": "médias",          "type": "text",  "topic": "🖼️ Photos & vidéos"},
            {"name": "memes",           "type": "text",  "topic": "😂 Humour"},
        ]},
        {"name": "DISCUSSIONS", "staff_only": False, "channels": [
            {"name": "actualités",      "type": "text",  "topic": "📰 News"},
            {"name": "suggestions",     "type": "text",  "topic": "💡 Vos idées"},
            {"name": "questions",       "type": "text",  "topic": "❓ Posez vos questions"},
            {"name": "débats",          "type": "text",  "topic": "🗣️ On en parle"},
        ]},
        {"name": "VOCAL", "staff_only": False, "channels": [
            {"name": "Lounge",          "type": "voice"},
            {"name": "Discussion",      "type": "voice"},
            {"name": "Cinéma 🎬",       "type": "voice"},
            {"name": "AFK",             "type": "voice"},
        ]},
        {"name": "EVENTS", "staff_only": False, "channels": [
            {"name": "événements",      "type": "text",  "topic": "🎉 Events"},
            {"name": "concours",        "type": "text",  "topic": "🏆 Concours"},
            {"name": "Event Voice",     "type": "voice"},
        ]},
        {"name": "STAFF", "staff_only": True, "channels": [
            {"name": "staff",           "type": "text",  "topic": "🛠️ Staff only"},
            {"name": "sanctions",       "type": "text",  "topic": "🔨 Sanctions"},
            {"name": "logs",            "type": "text",  "topic": "📋 Logs"},
            {"name": "Staff Vocal",     "type": "voice"},
        ]},
    ],
    "business": [
        {"name": "ENTREPRISE", "staff_only": False, "channels": [
            {"name": "annonces",        "type": "text",  "topic": "📢 Annonces"},
            {"name": "règles",          "type": "text",  "topic": "📜 Règles internes"},
            {"name": "général",         "type": "text",  "topic": "💬 Discussion générale"},
        ]},
        {"name": "PROJETS", "staff_only": False, "channels": [
            {"name": "projets-actifs",  "type": "text",  "topic": "📁 Projets en cours"},
            {"name": "idées",           "type": "text",  "topic": "💡 Nouvelles idées"},
            {"name": "ressources",      "type": "text",  "topic": "📚 Ressources"},
            {"name": "livrables",       "type": "text",  "topic": "✅ Livrables"},
        ]},
        {"name": "ÉQUIPES", "staff_only": False, "channels": [
            {"name": "marketing",       "type": "text",  "topic": "📣 Marketing"},
            {"name": "développement",   "type": "text",  "topic": "💻 Dev"},
            {"name": "design",          "type": "text",  "topic": "🎨 Design"},
            {"name": "support",         "type": "text",  "topic": "🛠️ Support client"},
        ]},
        {"name": "RÉUNIONS", "staff_only": False, "channels": [
            {"name": "planning",        "type": "text",  "topic": "🗓️ Planning"},
            {"name": "compte-rendu",    "type": "text",  "topic": "📝 CR de réunions"},
            {"name": "Réunion 1",       "type": "voice"},
            {"name": "Réunion 2",       "type": "voice"},
        ]},
        {"name": "DIRECTION", "staff_only": True, "channels": [
            {"name": "direction",       "type": "text",  "topic": "👑 Direction uniquement"},
            {"name": "finances",        "type": "text",  "topic": "💰 Finances"},
            {"name": "logs",            "type": "text",  "topic": "📋 Logs"},
            {"name": "Direction Vocal", "type": "voice"},
        ]},
        {"name": "STAFF", "staff_only": True, "channels": [
            {"name": "staff",           "type": "text",  "topic": "🛠️ Staff only"},
            {"name": "logs-bot",        "type": "text",  "topic": "🤖 Logs bot"},
            {"name": "Staff Vocal",     "type": "voice"},
        ]},
    ],
    "education": [
        {"name": "INFORMATIONS", "staff_only": False, "channels": [
            {"name": "annonces",        "type": "text",  "topic": "📢 Annonces"},
            {"name": "règles",          "type": "text",  "topic": "📜 Règles"},
            {"name": "programme",       "type": "text",  "topic": "📅 Programme des cours"},
        ]},
        {"name": "COURS", "staff_only": False, "channels": [
            {"name": "général",         "type": "text",  "topic": "💬 Discussion générale"},
            {"name": "cours-1",         "type": "text",  "topic": "📖 Cours 1"},
            {"name": "cours-2",         "type": "text",  "topic": "📖 Cours 2"},
            {"name": "ressources",      "type": "text",  "topic": "📚 Ressources & docs"},
        ]},
        {"name": "AIDE", "staff_only": False, "channels": [
            {"name": "questions",       "type": "text",  "topic": "❓ Questions"},
            {"name": "entraide",        "type": "text",  "topic": "🤝 Entraide étudiants"},
            {"name": "exercices",       "type": "text",  "topic": "✏️ Exercices"},
        ]},
        {"name": "VOCAL", "staff_only": False, "channels": [
            {"name": "Cours Vocal",     "type": "voice"},
            {"name": "Travail de groupe","type": "voice"},
            {"name": "AFK",             "type": "voice"},
        ]},
        {"name": "STAFF", "staff_only": True, "channels": [
            {"name": "professeurs",     "type": "text",  "topic": "👨‍🏫 Espace profs"},
            {"name": "logs",            "type": "text",  "topic": "📋 Logs"},
            {"name": "Staff Vocal",     "type": "voice"},
        ]},
    ],
    "creative": [
        {"name": "INFORMATIONS", "staff_only": False, "channels": [
            {"name": "annonces",        "type": "text",  "topic": "📢 Annonces"},
            {"name": "règles",          "type": "text",  "topic": "📜 Règles"},
            {"name": "présentations",   "type": "text",  "topic": "👋 Présentez-vous"},
        ]},
        {"name": "CRÉATIONS", "staff_only": False, "channels": [
            {"name": "général",         "type": "text",  "topic": "💬 Discussion"},
            {"name": "partage-art",     "type": "text",  "topic": "🎨 Partagez vos créas"},
            {"name": "musique",         "type": "text",  "topic": "🎵 Vos tracks"},
            {"name": "vidéos",          "type": "text",  "topic": "🎬 Vos vidéos"},
        ]},
        {"name": "PROJETS", "staff_only": False, "channels": [
            {"name": "wip",             "type": "text",  "topic": "🔧 Work in progress"},
            {"name": "feedbacks",       "type": "text",  "topic": "💬 Demandez des retours"},
            {"name": "collabs",         "type": "text",  "topic": "🤝 Cherche collab"},
        ]},
        {"name": "VOCAL", "staff_only": False, "channels": [
            {"name": "Lounge Créatif",  "type": "voice"},
            {"name": "Brainstorming",   "type": "voice"},
            {"name": "AFK",             "type": "voice"},
        ]},
        {"name": "STAFF", "staff_only": True, "channels": [
            {"name": "staff",           "type": "text",  "topic": "🛠️ Staff only"},
            {"name": "logs",            "type": "text",  "topic": "📋 Logs"},
            {"name": "Staff Vocal",     "type": "voice"},
        ]},
    ],
}

ROLES_TEMPLATES = {
    "gaming": [
        {"name": "👑 Owner",        "color": 0xFFD700, "hoist": True,  "level": "admin"},
        {"name": "⚔️ Admin",        "color": 0xFF4500, "hoist": True,  "level": "admin"},
        {"name": "🛡️ Modérateur",  "color": 0x1E90FF, "hoist": True,  "level": "mod"},
        {"name": "⭐ VIP",          "color": 0xF1C40F, "hoist": True,  "level": "member"},
        {"name": "🎮 Membre",       "color": 0x2ECC71, "hoist": True,  "level": "member"},
        {"name": "🤖 Bot",          "color": 0x95A5A6, "hoist": True,  "level": "admin"},
        {"name": "🔇 Muted",        "color": 0x7F8C8D, "hoist": False, "level": "muted"},
    ],
    "community": [
        {"name": "👑 Owner",        "color": 0xFFD700, "hoist": True,  "level": "admin"},
        {"name": "🛠️ Admin",        "color": 0xE74C3C, "hoist": True,  "level": "admin"},
        {"name": "🛡️ Modérateur",  "color": 0x3498DB, "hoist": True,  "level": "mod"},
        {"name": "🌟 VIP",          "color": 0xF39C12, "hoist": True,  "level": "member"},
        {"name": "👥 Membre",       "color": 0x2ECC71, "hoist": True,  "level": "member"},
        {"name": "🤖 Bot",          "color": 0x95A5A6, "hoist": True,  "level": "admin"},
        {"name": "🔇 Muted",        "color": 0x7F8C8D, "hoist": False, "level": "muted"},
    ],
    "business": [
        {"name": "👑 CEO",          "color": 0xFFD700, "hoist": True,  "level": "admin"},
        {"name": "💼 Manager",      "color": 0xE74C3C, "hoist": True,  "level": "admin"},
        {"name": "🔧 Modérateur",   "color": 0x3498DB, "hoist": True,  "level": "mod"},
        {"name": "💡 Employé",      "color": 0x2ECC71, "hoist": True,  "level": "member"},
        {"name": "🤖 Bot",          "color": 0x95A5A6, "hoist": True,  "level": "admin"},
        {"name": "🔇 Muted",        "color": 0x7F8C8D, "hoist": False, "level": "muted"},
    ],
    "education": [
        {"name": "👑 Directeur",    "color": 0xFFD700, "hoist": True,  "level": "admin"},
        {"name": "👨‍🏫 Professeur", "color": 0xE74C3C, "hoist": True,  "level": "mod"},
        {"name": "📚 Étudiant VIP", "color": 0xF39C12, "hoist": True,  "level": "member"},
        {"name": "🎒 Étudiant",     "color": 0x2ECC71, "hoist": True,  "level": "member"},
        {"name": "🤖 Bot",          "color": 0x95A5A6, "hoist": True,  "level": "admin"},
        {"name": "🔇 Muted",        "color": 0x7F8C8D, "hoist": False, "level": "muted"},
    ],
    "creative": [
        {"name": "👑 Fondateur",    "color": 0xFFD700, "hoist": True,  "level": "admin"},
        {"name": "🎨 Admin",        "color": 0xE74C3C, "hoist": True,  "level": "admin"},
        {"name": "🛡️ Modérateur",  "color": 0x3498DB, "hoist": True,  "level": "mod"},
        {"name": "⭐ Artiste VIP",  "color": 0xF39C12, "hoist": True,  "level": "member"},
        {"name": "✏️ Créateur",     "color": 0x2ECC71, "hoist": True,  "level": "member"},
        {"name": "🤖 Bot",          "color": 0x95A5A6, "hoist": True,  "level": "admin"},
        {"name": "🔇 Muted",        "color": 0x7F8C8D, "hoist": False, "level": "muted"},
    ],
}

# ──────────────────────────────────────────────────────────────────────────────
# VIEWS — Boutons interactifs
# ──────────────────────────────────────────────────────────────────────────────

class TypeView(ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=180)
        self.guild_id = guild_id

    async def _handle(self, interaction, value, label):
        setup_data[self.guild_id]["type"] = value
        self.stop()
        for c in self.children: c.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(description=f"✅  Type sélectionné : **{label}**", color=0x2ECC71), view=self
        )
        await ask_function(interaction.channel, self.guild_id)

    @ui.button(label="🎮 Gaming",       style=discord.ButtonStyle.primary)
    async def gaming(self, i, b):    await self._handle(i, "gaming",    "Gaming")
    @ui.button(label="🌍 Communauté",   style=discord.ButtonStyle.primary)
    async def community(self, i, b): await self._handle(i, "community", "Communauté")
    @ui.button(label="💼 Business",     style=discord.ButtonStyle.primary)
    async def business(self, i, b):  await self._handle(i, "business",  "Business")
    @ui.button(label="📚 Éducation",    style=discord.ButtonStyle.primary)
    async def education(self, i, b): await self._handle(i, "education", "Éducation")
    @ui.button(label="🎨 Créatif",      style=discord.ButtonStyle.primary)
    async def creative(self, i, b):  await self._handle(i, "creative",  "Créatif")


class FunctionView(ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=180)
        self.guild_id = guild_id

    async def _handle(self, interaction, value, label):
        setup_data[self.guild_id]["function"] = value
        self.stop()
        for c in self.children: c.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(description=f"✅  Fonction sélectionnée : **{label}**", color=0x2ECC71), view=self
        )
        await ask_format(interaction.channel, self.guild_id)

    @ui.button(label="💬 Communauté",   style=discord.ButtonStyle.success)
    async def community(self, i, b): await self._handle(i, "community", "Communauté")
    @ui.button(label="🛠️ Support",      style=discord.ButtonStyle.success)
    async def support(self, i, b):   await self._handle(i, "support",   "Support")
    @ui.button(label="🎉 Événements",   style=discord.ButtonStyle.success)
    async def events(self, i, b):    await self._handle(i, "events",    "Événements")
    @ui.button(label="📁 Portfolio",    style=discord.ButtonStyle.success)
    async def portfolio(self, i, b): await self._handle(i, "portfolio", "Portfolio")
    @ui.button(label="🎭 Roleplay",     style=discord.ButtonStyle.success)
    async def roleplay(self, i, b):  await self._handle(i, "roleplay",  "Roleplay")


class FormatView(ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=180)
        self.guild_id = guild_id

    async def _handle(self, interaction, value, label):
        setup_data[self.guild_id]["format"] = value
        self.stop()
        for c in self.children: c.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(description=f"✅  Format sélectionné : **{label}**", color=0x2ECC71), view=self
        )
        await ask_categories(interaction.channel, self.guild_id)

    @ui.button(label="🔥 | SALONS",     style=discord.ButtonStyle.secondary)
    async def fire(self, i, b):    await self._handle(i, "fire",    "🔥 | SALONS")
    @ui.button(label="━━━ SALONS ━━━",  style=discord.ButtonStyle.secondary)
    async def dash(self, i, b):    await self._handle(i, "dash",    "━━━ SALONS ━━━")
    @ui.button(label="[ SALONS ]",      style=discord.ButtonStyle.secondary)
    async def bracket(self, i, b): await self._handle(i, "bracket", "[ SALONS ]")
    @ui.button(label="» SALONS",        style=discord.ButtonStyle.secondary)
    async def arrow(self, i, b):   await self._handle(i, "arrow",   "» SALONS")
    @ui.button(label="SALONS simple",   style=discord.ButtonStyle.secondary)
    async def plain(self, i, b):   await self._handle(i, "plain",   "Simple")


class CategoriesView(ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=180)
        self.guild_id = guild_id

    async def _handle(self, interaction, value, label):
        setup_data[self.guild_id]["num_cat"] = value
        self.stop()
        for c in self.children: c.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(description=f"✅  Catégories : **{label}**", color=0x2ECC71), view=self
        )
        await build_server(interaction.channel, interaction.guild, self.guild_id)

    @ui.button(label="2 Catégories",   style=discord.ButtonStyle.danger)
    async def c2(self, i, b): await self._handle(i, 2, "2 Catégories")
    @ui.button(label="3 Catégories",   style=discord.ButtonStyle.danger)
    async def c3(self, i, b): await self._handle(i, 3, "3 Catégories")
    @ui.button(label="4 Catégories",   style=discord.ButtonStyle.danger)
    async def c4(self, i, b): await self._handle(i, 4, "4 Catégories")
    @ui.button(label="5 Catégories",   style=discord.ButtonStyle.danger)
    async def c5(self, i, b): await self._handle(i, 5, "5 Catégories")
    @ui.button(label="6+ Catégories",  style=discord.ButtonStyle.danger)
    async def c6(self, i, b): await self._handle(i, 6, "6+ Catégories")


# ──────────────────────────────────────────────────────────────────────────────
# QUESTIONS — Envoi des embeds de question
# ──────────────────────────────────────────────────────────────────────────────

async def ask_type(channel, guild_id):
    e = discord.Embed(
        title="❓ Question 1 / 4 — Type de serveur",
        description="Quel est le **type** de ton serveur ?",
        color=0x5865F2
    )
    e.set_footer(text="Clique sur un bouton ci-dessous")
    await channel.send(embed=e, view=TypeView(guild_id))

async def ask_function(channel, guild_id):
    e = discord.Embed(
        title="❓ Question 2 / 4 — Fonction principale",
        description="Quelle est la **fonction** principale de ton serveur ?",
        color=0x5865F2
    )
    await channel.send(embed=e, view=FunctionView(guild_id))

async def ask_format(channel, guild_id):
    e = discord.Embed(
        title="❓ Question 3 / 4 — Format des salons",
        description=(
            "Quel **format** veux-tu pour les noms de salons ?\n\n"
            "🔥 `🔥 | SALON`\n"
            "━━━ `━━━ SALON ━━━`\n"
            "[ ] `[ SALON ]`\n"
            "»  `» SALON`\n"
            "📝 `salon-simple`"
        ),
        color=0x5865F2
    )
    await channel.send(embed=e, view=FormatView(guild_id))

async def ask_categories(channel, guild_id):
    e = discord.Embed(
        title="❓ Question 4 / 4 — Nombre de catégories",
        description=(
            "Combien de **catégories** veux-tu ?\n"
            "*(La catégorie STAFF est toujours incluse en bonus)*"
        ),
        color=0x5865F2
    )
    await channel.send(embed=e, view=CategoriesView(guild_id))

# ──────────────────────────────────────────────────────────────────────────────
# BUILD SERVER — Création automatique
# ──────────────────────────────────────────────────────────────────────────────

async def build_server(channel, guild: discord.Guild, guild_id):
    data      = setup_data[guild_id]
    srv_type  = data["type"]
    fmt       = data["format"]
    num_cat   = data["num_cat"]

    # Message de chargement
    loading = discord.Embed(
        title="⚙️ Construction en cours...",
        description=(
            "```\n"
            "🔨 Suppression des anciens salons...\n"
            "🎭 Création des rôles...\n"
            "📂 Création des catégories...\n"
            "💬 Création des salons...\n"
            "🔒 Configuration des permissions...\n"
            "```"
        ),
        color=0xF39C12
    )
    loading.set_footer(text="Patience, ça arrive ! 🚀")
    loading_msg = await channel.send(embed=loading)

    created  = {"roles": [], "cats": 0, "channels": 0}
    errors   = []

    # ── Suppression des salons existants ──
    for ch in list(guild.channels):
        try:
            await ch.delete()
            await asyncio.sleep(0.4)
        except Exception as e:
            errors.append(f"Suppression: {e}")

    # ── Création des rôles ──
    role_map = {}
    roles_list = ROLES_TEMPLATES.get(srv_type, ROLES_TEMPLATES["community"])

    for rd in reversed(roles_list):
        try:
            lvl = rd["level"]
            if lvl == "admin":
                perms = discord.Permissions.all()
            elif lvl == "mod":
                perms = discord.Permissions(
                    manage_messages=True, kick_members=True, ban_members=True,
                    mute_members=True, deafen_members=True, move_members=True,
                    read_messages=True, send_messages=True, connect=True, speak=True,
                    read_message_history=True, manage_nicknames=True, view_audit_log=True
                )
            elif lvl == "muted":
                perms = discord.Permissions(read_messages=True, read_message_history=True)
            else:  # member
                perms = discord.Permissions(
                    read_messages=True, send_messages=True, connect=True, speak=True,
                    read_message_history=True, add_reactions=True, attach_files=True
                )

            role = await guild.create_role(
                name=rd["name"],
                color=discord.Color(rd["color"]),
                hoist=rd["hoist"],
                permissions=perms,
                mentionable=True
            )
            role_map[rd["level"]] = role_map.get(rd["level"], role)
            role_map[rd["name"]] = role
            created["roles"].append(rd["name"])
            await asyncio.sleep(0.4)
        except Exception as e:
            errors.append(f"Rôle {rd['name']}: {e}")

    staff_role  = role_map.get("mod")
    member_role = role_map.get("member")
    muted_role  = role_map.get("muted")

    # ── Création des catégories & salons ──
    template = ALL_TEMPLATES.get(srv_type, ALL_TEMPLATES["community"])

    # Sépare STAFF des autres catégories
    normal_cats = [c for c in template if not c["staff_only"]]
    staff_cats  = [c for c in template if c["staff_only"]]

    # Limite aux num_cat demandées + toujours ajouter STAFF
    selected = normal_cats[:num_cat] + staff_cats

    for cat_data in selected:
        try:
            cat_name = format_category(fmt, cat_data["name"])
            is_staff = cat_data["staff_only"]

            # Permissions de la catégorie
            ow = {
                guild.default_role: discord.PermissionOverwrite(
                    read_messages=False,
                    connect=False
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True,
                    manage_channels=True, connect=True
                ),
            }
            if is_staff:
                if staff_role:
                    ow[staff_role] = discord.PermissionOverwrite(
                        read_messages=True, send_messages=True, connect=True, speak=True
                    )
            else:
                if member_role:
                    ow[member_role] = discord.PermissionOverwrite(
                        read_messages=True, send_messages=True,
                        connect=True, speak=True, read_message_history=True
                    )
                if staff_role:
                    ow[staff_role] = discord.PermissionOverwrite(
                        read_messages=True, send_messages=True,
                        connect=True, speak=True, manage_messages=True
                    )

            category = await guild.create_category(cat_name, overwrites=ow)
            created["cats"] += 1
            await asyncio.sleep(0.4)

            for ch_data in cat_data.get("channels", []):
                try:
                    ch_name = format_channel(fmt, ch_data["name"])
                    ch_ow   = dict(ow)

                    # Muted ne peut pas écrire
                    if muted_role:
                        ch_ow[muted_role] = discord.PermissionOverwrite(
                            send_messages=False, speak=False, add_reactions=False
                        )

                    if ch_data["type"] == "text":
                        await guild.create_text_channel(
                            ch_name, category=category,
                            overwrites=ch_ow,
                            topic=ch_data.get("topic", "")
                        )
                    else:
                        await guild.create_voice_channel(
                            ch_name, category=category,
                            overwrites=ch_ow
                        )
                    created["channels"] += 1
                    await asyncio.sleep(0.4)
                except Exception as e:
                    errors.append(f"Salon {ch_data['name']}: {e}")

        except Exception as e:
            errors.append(f"Catégorie {cat_data['name']}: {e}")

    # ── Embed de succès ──
    embed = discord.Embed(
        title="✅ Serveur configuré avec succès !",
        description=f"**{guild.name}** est prêt à accueillir ses membres 🚀",
        color=0x2ECC71
    )
    embed.add_field(
        name="📊 Résumé",
        value=(
            f"🎭 **Rôles créés** : {len(created['roles'])}\n"
            f"📂 **Catégories** : {created['cats']}\n"
            f"💬 **Salons** : {created['channels']}"
        ),
        inline=True
    )
    embed.add_field(
        name="⚙️ Configuration",
        value=(
            f"🏷️ **Type** : {srv_type.capitalize()}\n"
            f"🔧 **Fonction** : {data['function'].capitalize()}\n"
            f"🎨 **Format** : {fmt}"
        ),
        inline=True
    )
    embed.add_field(
        name="🎭 Rôles",
        value="\n".join(created["roles"]) or "Aucun",
        inline=False
    )
    if errors:
        embed.add_field(
            name=f"⚠️ Erreurs ({len(errors)})",
            value="\n".join(errors[:5]),
            inline=False
        )
    embed.set_footer(text="ServerBuilder • Merci d'utiliser le bot ! 🎉")

    # Envoie dans le premier salon disponible
    first = next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
    if first:
        await first.send(embed=embed)

    # Nettoyage
    setup_data.pop(guild_id, None)

@bot.event
async def on_guild_join(guild: discord.Guild):
    setup_data[guild.id] = {}

    channel = next(
        (c for c in guild.text_channels if c.permissions_for(guild.me).send_messages),
        None
    )
    if not channel:
        return

    embed = discord.Embed(
        title=f"👋 Salut **{guild.name}** !",
        description=(
            "Je suis **ServerBuilder** 🛠️ — je vais configurer ton serveur en quelques clics.\n\n"
            "**Ce que je vais créer :**\n"
            "✅  Les **catégories** et **salons** adaptés\n"
            "✅  Les **rôles** avec les bonnes permissions\n"
            "✅  Les **restrictions** (muted, staff-only...)\n\n"
            "⚠️ **Attention** — tous les salons et rôles existants seront remplacés.\n\n"
            "Réponds aux **4 questions** ci-dessous pour démarrer !"
        ),
        color=0x5865F2
    )
    embed.set_thumbnail(url=guild.me.display_avatar.url)
    embed.set_footer(text="ServerBuilder • Setup Wizard v1.0")

    await channel.send(embed=embed)
    await asyncio.sleep(1)
    await ask_type(channel, guild.id)





bot.run(os.getenv('DISCORD_TOKEN'))