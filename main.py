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

async def check_hierarchy(ctx, member: discord.Member, action: str):
    # Owner bypass total
    if ctx.author.id == ctx.guild.owner_id:
        return True

    # Vérifie auteur vs membre
    if member.top_role >= ctx.author.top_role:
        await ctx.send(f"Tu ne peux pas {action} un membre avec un rôle supérieur ou égal au tien.")
        return False

    # Vérifie bot vs membre
    if member.top_role >= ctx.guild.me.top_role:
        await ctx.send(f"Je ne peux pas {action} ce membre.")
        return False

    return True

OWNER_IDS = [1447233337830936807, 1477344366769999913]


def is_team_owner():
    async def predicate(ctx):
        return ctx.author.id in OWNER_IDS
    return commands.check(predicate)

async def update_status() -> None:
    guild_count = len(bot.guilds)
    activity = discord.CustomActivity(
        name=f"/help • {guild_count} serveur{'s' if guild_count != 1 else ''}"
    )
    try:
        await bot.change_presence(status=discord.Status.online, activity=activity)
        print(f"[Status] Mis à jour : {guild_count} serveur(s)")
    except discord.HTTPException as e:
        print(f"[Status] Erreur HTTP : {e}")
    except Exception as e:
        print(f"[Status] Erreur inattendue : {e}")


@bot.event
async def on_ready() -> None:
    print(f"[Bot] Connecté en tant que {bot.user} (ID: {bot.user.id})")
    print(f"[Bot] Présent sur {len(bot.guilds)} serveur(s)")
    await update_status()

@bot.event
async def on_guild_join(guild: discord.Guild) -> None:
    await update_status()


@bot.event
async def on_guild_remove(guild: discord.Guild) -> None:
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

tree = bot.tree

# ──────────────────────────────────────────────────────────────────────────────
# PERSISTANCE — Limite 2 serveurs par owner
# ──────────────────────────────────────────────────────────────────────────────

DB_FILE = "user_servers.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def get_user_servers(user_id: int) -> list:
    return load_db().get(str(user_id), [])

def add_user_server(user_id: int, guild_id: int):
    db  = load_db()
    key = str(user_id)
    if key not in db:
        db[key] = []
    if guild_id not in db[key]:
        db[key].append(guild_id)
    save_db(db)

def remove_user_server(user_id: int, guild_id: int):
    db  = load_db()
    key = str(user_id)
    if key in db and guild_id in db[key]:
        db[key].remove(guild_id)
        save_db(db)

def count_user_servers(user_id: int) -> int:
    return len(get_user_servers(user_id))

# Stocke les reponses de setup en cours
setup_data = {}

# ──────────────────────────────────────────────────────────────────────────────
# EMOJIS & META PAR TYPE
# ──────────────────────────────────────────────────────────────────────────────

TYPE_META = {
    "gaming": {
        "emoji_cat":      "🎮",
        "emoji_text":     "🕹️",
        "emoji_voice":    "🎧",
        "emoji_announce": "📣",
        "emoji_rules":    "📜",
        "emoji_roles":    "🎯",
        "emoji_general":  "💬",
        "emoji_staff":    "⚔️",
        "emoji_event":    "🏆",
        "color":          0x5865F2,
        "label":          "Gaming",
    },
    "community": {
        "emoji_cat":      "🌍",
        "emoji_text":     "💬",
        "emoji_voice":    "🔊",
        "emoji_announce": "📢",
        "emoji_rules":    "📋",
        "emoji_roles":    "🎭",
        "emoji_general":  "🗣️",
        "emoji_staff":    "🛠️",
        "emoji_event":    "🎉",
        "color":          0x2ECC71,
        "label":          "Communaute",
    },
    "business": {
        "emoji_cat":      "💼",
        "emoji_text":     "📁",
        "emoji_voice":    "📞",
        "emoji_announce": "📊",
        "emoji_rules":    "📝",
        "emoji_roles":    "🏷️",
        "emoji_general":  "🤝",
        "emoji_staff":    "👔",
        "emoji_event":    "📅",
        "color":          0xF39C12,
        "label":          "Business",
    },
    "education": {
        "emoji_cat":      "📚",
        "emoji_text":     "✏️",
        "emoji_voice":    "🎙️",
        "emoji_announce": "📣",
        "emoji_rules":    "📖",
        "emoji_roles":    "🎓",
        "emoji_general":  "🧠",
        "emoji_staff":    "👨‍🏫",
        "emoji_event":    "🗓️",
        "color":          0x3498DB,
        "label":          "Education",
    },
    "creative": {
        "emoji_cat":      "🎨",
        "emoji_text":     "✍️",
        "emoji_voice":    "🎵",
        "emoji_announce": "📡",
        "emoji_rules":    "🖼️",
        "emoji_roles":    "🌈",
        "emoji_general":  "💡",
        "emoji_staff":    "🎬",
        "emoji_event":    "⭐",
        "color":          0xE74C3C,
        "label":          "Creatif",
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS — Formatage
# ──────────────────────────────────────────────────────────────────────────────

def format_category(fmt, name, emoji):
    return {
        "fire":    f"{emoji} ┃ {name.upper()}",
        "dash":    f"━━ {emoji}{name.upper()} ━━",
        "bracket": f"[{emoji} {name.upper()}]",
        "arrow":   f"{emoji} » {name.upper()}",
        "plain":   f"{emoji}{name.upper()}",
    }.get(fmt, f"{emoji}{name.upper()}")

def format_channel(fmt, name, emoji):
    slug = name.lower().replace(" ", "-")
    return {
        "fire":    f"{emoji}┃{slug}",
        "dash":    f"─{slug}",
        "bracket": f"▸{slug}",
        "arrow":   f"{emoji}{slug}",
        "plain":   slug,
    }.get(fmt, slug)

# ──────────────────────────────────────────────────────────────────────────────
# TEMPLATES
# ──────────────────────────────────────────────────────────────────────────────

def get_template(srv_type):
    TEMPLATES = {
        "gaming": [
            {"name": "INFORMATIONS", "staff_only": False, "emoji_key": "emoji_announce", "channels": [
                {"name": "annonces",      "type": "text",  "emoji_key": "emoji_announce", "topic": "📣Annonces officielles"},
                {"name": "regles",        "type": "text",  "emoji_key": "emoji_rules",    "topic": "📜Les regles du serveur"},
                {"name": "roles",         "type": "text",  "emoji_key": "emoji_roles",    "topic": "🎯Choisissez vos roles"},
            ]},
            {"name": "GENERAL", "staff_only": False, "emoji_key": "emoji_general", "channels": [
                {"name": "general",       "type": "text",  "emoji_key": "emoji_general",  "topic": "💬Discussion generale"},
                {"name": "gaming",        "type": "text",  "emoji_key": "emoji_cat",      "topic": "🎮Parlez de vos jeux"},
                {"name": "clips-screens", "type": "text",  "emoji_key": "emoji_text",     "topic": "🕹️Partagez vos moments"},
                {"name": "memes-blagues", "type": "text",  "emoji_key": "emoji_text",     "topic": "😂Humour & memes"},
            ]},
            {"name": "GAMING", "staff_only": False, "emoji_key": "emoji_cat", "channels": [
                {"name": "LFG",           "type": "text",  "emoji_key": "emoji_text",     "topic": "🔍Looking for group"},
                {"name": "tournois",      "type": "text",  "emoji_key": "emoji_event",    "topic": "🏆Tournois & competitions"},
                {"name": "classements",   "type": "text",  "emoji_key": "emoji_text",     "topic": "📊Ranks & classements"},
            ]},
            {"name": "VOCAL", "staff_only": False, "emoji_key": "emoji_voice", "channels": [
                {"name": "Gaming 1",      "type": "voice", "emoji_key": "emoji_voice"},
                {"name": "Gaming 2",      "type": "voice", "emoji_key": "emoji_voice"},
                {"name": "Gaming 3",      "type": "voice", "emoji_key": "emoji_voice"},
                {"name": "Musique",       "type": "voice", "emoji_key": "emoji_voice"},
                {"name": "AFK",           "type": "voice", "emoji_key": "emoji_voice"},
            ]},
            {"name": "EVENTS", "staff_only": False, "emoji_key": "emoji_event", "channels": [
                {"name": "evenements",    "type": "text",  "emoji_key": "emoji_event",    "topic": "🏆Evenements a venir"},
                {"name": "giveaways",     "type": "text",  "emoji_key": "emoji_event",    "topic": "🎁Giveaways"},
                {"name": "Event Vocal",   "type": "voice", "emoji_key": "emoji_voice"},
            ]},
            {"name": "STAFF", "staff_only": True, "emoji_key": "emoji_staff", "channels": [
                {"name": "staff-general", "type": "text",  "emoji_key": "emoji_staff",    "topic": "⚔️Salon prive staff"},
                {"name": "sanctions",     "type": "text",  "emoji_key": "emoji_staff",    "topic": "🔨Log sanctions"},
                {"name": "logs-bot",      "type": "text",  "emoji_key": "emoji_staff",    "topic": "🤖Logs auto"},
                {"name": "Staff Vocal",   "type": "voice", "emoji_key": "emoji_voice"},
            ]},
        ],
        "community": [
            {"name": "INFORMATIONS", "staff_only": False, "emoji_key": "emoji_announce", "channels": [
                {"name": "annonces",      "type": "text",  "emoji_key": "emoji_announce", "topic": "📢Annonces officielles"},
                {"name": "regles",        "type": "text",  "emoji_key": "emoji_rules",    "topic": "📋Les regles"},
                {"name": "roles",         "type": "text",  "emoji_key": "emoji_roles",    "topic": "🎭Choisissez vos roles"},
                {"name": "partenariats",  "type": "text",  "emoji_key": "emoji_text",     "topic": "🤝Partenaires"},
            ]},
            {"name": "COMMUNAUTE", "staff_only": False, "emoji_key": "emoji_cat", "channels": [
                {"name": "general",       "type": "text",  "emoji_key": "emoji_general",  "topic": "🗣️Discussion generale"},
                {"name": "presentations", "type": "text",  "emoji_key": "emoji_text",     "topic": "👋Presentez-vous"},
                {"name": "medias",        "type": "text",  "emoji_key": "emoji_text",     "topic": "🖼️Photos & videos"},
                {"name": "memes",         "type": "text",  "emoji_key": "emoji_text",     "topic": "😂Memes"},
            ]},
            {"name": "DISCUSSIONS", "staff_only": False, "emoji_key": "emoji_general", "channels": [
                {"name": "actualites",    "type": "text",  "emoji_key": "emoji_text",     "topic": "📰News"},
                {"name": "suggestions",   "type": "text",  "emoji_key": "emoji_text",     "topic": "💡Vos idees"},
                {"name": "questions",     "type": "text",  "emoji_key": "emoji_text",     "topic": "❓Questions"},
                {"name": "debats",        "type": "text",  "emoji_key": "emoji_text",     "topic": "🗣️Debats"},
            ]},
            {"name": "VOCAL", "staff_only": False, "emoji_key": "emoji_voice", "channels": [
                {"name": "Lounge",        "type": "voice", "emoji_key": "emoji_voice"},
                {"name": "Discussion",    "type": "voice", "emoji_key": "emoji_voice"},
                {"name": "Cinema",        "type": "voice", "emoji_key": "emoji_voice"},
                {"name": "AFK",           "type": "voice", "emoji_key": "emoji_voice"},
            ]},
            {"name": "EVENTS", "staff_only": False, "emoji_key": "emoji_event", "channels": [
                {"name": "evenements",    "type": "text",  "emoji_key": "emoji_event",    "topic": "🎉Evenements"},
                {"name": "concours",      "type": "text",  "emoji_key": "emoji_event",    "topic": "🏅Concours"},
                {"name": "Event Vocal",   "type": "voice", "emoji_key": "emoji_voice"},
            ]},
            {"name": "STAFF", "staff_only": True, "emoji_key": "emoji_staff", "channels": [
                {"name": "staff",         "type": "text",  "emoji_key": "emoji_staff",    "topic": "🛠️Staff only"},
                {"name": "sanctions",     "type": "text",  "emoji_key": "emoji_staff",    "topic": "🔨Sanctions"},
                {"name": "logs",          "type": "text",  "emoji_key": "emoji_staff",    "topic": "📋Logs"},
                {"name": "Staff Vocal",   "type": "voice", "emoji_key": "emoji_voice"},
            ]},
        ],
        "business": [
            {"name": "ENTREPRISE", "staff_only": False, "emoji_key": "emoji_cat", "channels": [
                {"name": "annonces",      "type": "text",  "emoji_key": "emoji_announce", "topic": "📊Annonces internes"},
                {"name": "regles",        "type": "text",  "emoji_key": "emoji_rules",    "topic": "📝Regles & charte"},
                {"name": "general",       "type": "text",  "emoji_key": "emoji_general",  "topic": "🤝Discussion"},
            ]},
            {"name": "PROJETS", "staff_only": False, "emoji_key": "emoji_text", "channels": [
                {"name": "projets-actifs","type": "text",  "emoji_key": "emoji_text",     "topic": "📁Projets en cours"},
                {"name": "idees",         "type": "text",  "emoji_key": "emoji_text",     "topic": "💡Nouvelles idees"},
                {"name": "ressources",    "type": "text",  "emoji_key": "emoji_text",     "topic": "📚Ressources & outils"},
                {"name": "livrables",     "type": "text",  "emoji_key": "emoji_text",     "topic": "✅Livrables"},
            ]},
            {"name": "EQUIPES", "staff_only": False, "emoji_key": "emoji_cat", "channels": [
                {"name": "marketing",     "type": "text",  "emoji_key": "emoji_text",     "topic": "📣Marketing"},
                {"name": "developpement", "type": "text",  "emoji_key": "emoji_text",     "topic": "💻Dev"},
                {"name": "design",        "type": "text",  "emoji_key": "emoji_text",     "topic": "🎨Design"},
                {"name": "support",       "type": "text",  "emoji_key": "emoji_text",     "topic": "🛠️Support"},
            ]},
            {"name": "REUNIONS", "staff_only": False, "emoji_key": "emoji_event", "channels": [
                {"name": "planning",      "type": "text",  "emoji_key": "emoji_event",    "topic": "🗓️Planning"},
                {"name": "compte-rendu",  "type": "text",  "emoji_key": "emoji_text",     "topic": "📝CR reunions"},
                {"name": "Reunion 1",     "type": "voice", "emoji_key": "emoji_voice"},
                {"name": "Reunion 2",     "type": "voice", "emoji_key": "emoji_voice"},
            ]},
            {"name": "DIRECTION", "staff_only": True, "emoji_key": "emoji_staff", "channels": [
                {"name": "direction",     "type": "text",  "emoji_key": "emoji_staff",    "topic": "💼Direction uniquement"},
                {"name": "finances",      "type": "text",  "emoji_key": "emoji_staff",    "topic": "💰Finances"},
                {"name": "Direction Vocal","type": "voice","emoji_key": "emoji_voice"},
            ]},
            {"name": "STAFF", "staff_only": True, "emoji_key": "emoji_staff", "channels": [
                {"name": "staff",         "type": "text",  "emoji_key": "emoji_staff",    "topic": "👔Staff interne"},
                {"name": "logs-bot",      "type": "text",  "emoji_key": "emoji_staff",    "topic": "🤖Logs"},
                {"name": "Staff Vocal",   "type": "voice", "emoji_key": "emoji_voice"},
            ]},
        ],
        "education": [
            {"name": "INFORMATIONS", "staff_only": False, "emoji_key": "emoji_announce", "channels": [
                {"name": "annonces",      "type": "text",  "emoji_key": "emoji_announce", "topic": "📣Annonces"},
                {"name": "regles",        "type": "text",  "emoji_key": "emoji_rules",    "topic": "📖Reglement"},
                {"name": "programme",     "type": "text",  "emoji_key": "emoji_text",     "topic": "🗓️Programme des cours"},
            ]},
            {"name": "COURS", "staff_only": False, "emoji_key": "emoji_cat", "channels": [
                {"name": "general",       "type": "text",  "emoji_key": "emoji_general",  "topic": "🧠Discussion etudiants"},
                {"name": "cours-1",       "type": "text",  "emoji_key": "emoji_text",     "topic": "✏️Cours 1"},
                {"name": "cours-2",       "type": "text",  "emoji_key": "emoji_text",     "topic": "✏️Cours 2"},
                {"name": "ressources",    "type": "text",  "emoji_key": "emoji_text",     "topic": "📚Ressources"},
            ]},
            {"name": "AIDE", "staff_only": False, "emoji_key": "emoji_text", "channels": [
                {"name": "questions",     "type": "text",  "emoji_key": "emoji_text",     "topic": "❓Questions"},
                {"name": "entraide",      "type": "text",  "emoji_key": "emoji_text",     "topic": "🤝Entraide"},
                {"name": "exercices",     "type": "text",  "emoji_key": "emoji_text",     "topic": "✏️Exercices"},
            ]},
            {"name": "VOCAL", "staff_only": False, "emoji_key": "emoji_voice", "channels": [
                {"name": "Cours Live",    "type": "voice", "emoji_key": "emoji_voice"},
                {"name": "Groupe 1",      "type": "voice", "emoji_key": "emoji_voice"},
                {"name": "Groupe 2",      "type": "voice", "emoji_key": "emoji_voice"},
                {"name": "AFK",           "type": "voice", "emoji_key": "emoji_voice"},
            ]},
            {"name": "STAFF", "staff_only": True, "emoji_key": "emoji_staff", "channels": [
                {"name": "professeurs",   "type": "text",  "emoji_key": "emoji_staff",    "topic": "👨‍🏫Espace profs"},
                {"name": "notes-internes","type": "text",  "emoji_key": "emoji_staff",    "topic": "📋Notes internes"},
                {"name": "Staff Vocal",   "type": "voice", "emoji_key": "emoji_voice"},
            ]},
        ],
        "creative": [
            {"name": "INFORMATIONS", "staff_only": False, "emoji_key": "emoji_announce", "channels": [
                {"name": "annonces",      "type": "text",  "emoji_key": "emoji_announce", "topic": "📡Annonces"},
                {"name": "regles",        "type": "text",  "emoji_key": "emoji_rules",    "topic": "🖼️Regles"},
                {"name": "presentations", "type": "text",  "emoji_key": "emoji_text",     "topic": "👋presentez-vous"},
            ]},
            {"name": "CREATIONS", "staff_only": False, "emoji_key": "emoji_cat", "channels": [
                {"name": "general",       "type": "text",  "emoji_key": "emoji_general",  "topic": "💡Discussion createurs"},
                {"name": "art-visuel",    "type": "text",  "emoji_key": "emoji_text",     "topic": "🎨Art visuel"},
                {"name": "musique",       "type": "text",  "emoji_key": "emoji_voice",    "topic": "🎵Musique & tracks"},
                {"name": "videos",        "type": "text",  "emoji_key": "emoji_text",     "topic": "🎬Videos & montages"},
                {"name": "ecriture",      "type": "text",  "emoji_key": "emoji_text",     "topic": "✍️Prose & poesie"},
            ]},
            {"name": "PROJETS", "staff_only": False, "emoji_key": "emoji_text", "channels": [
                {"name": "wip",           "type": "text",  "emoji_key": "emoji_text",     "topic": "🔧Work In Progress"},
                {"name": "feedbacks",     "type": "text",  "emoji_key": "emoji_text",     "topic": "💬Retours constructifs"},
                {"name": "collabs",       "type": "text",  "emoji_key": "emoji_text",     "topic": "🤝Cherche collab"},
            ]},
            {"name": "VOCAL", "staff_only": False, "emoji_key": "emoji_voice", "channels": [
                {"name": "Lounge Creatif","type": "voice", "emoji_key": "emoji_voice"},
                {"name": "Brainstorming", "type": "voice", "emoji_key": "emoji_voice"},
                {"name": "Session Live",  "type": "voice", "emoji_key": "emoji_voice"},
                {"name": "AFK",           "type": "voice", "emoji_key": "emoji_voice"},
            ]},
            {"name": "STAFF", "staff_only": True, "emoji_key": "emoji_staff", "channels": [
                {"name": "staff-creatif", "type": "text",  "emoji_key": "emoji_staff",    "topic": "🎬Moderateurs creatifs"},
                {"name": "logs",          "type": "text",  "emoji_key": "emoji_staff",    "topic": "📋Logs & sanctions"},
                {"name": "Staff Vocal",   "type": "voice", "emoji_key": "emoji_voice"},
            ]},
        ],
    }
    return TEMPLATES.get(srv_type, TEMPLATES["community"])


ROLES_TEMPLATES = {
    "gaming": [
        {"name": "👑 Owner",         "color": 0xFFD700, "hoist": True,  "level": "admin"},
        {"name": "⚔️ Admin",         "color": 0xFF4500, "hoist": True,  "level": "admin"},
        {"name": "🛡️ Moderateur",   "color": 0x1E90FF, "hoist": True,  "level": "mod"},
        {"name": "🎮 VIP Gamer",     "color": 0xF1C40F, "hoist": True,  "level": "member"},
        {"name": "🕹️ Membre",        "color": 0x2ECC71, "hoist": True,  "level": "member"},
        {"name": "🤖 Bot",           "color": 0x95A5A6, "hoist": True,  "level": "admin"},
        {"name": "🔇 Muted",         "color": 0x7F8C8D, "hoist": False, "level": "muted"},
    ],
    "community": [
        {"name": "👑 Owner",         "color": 0xFFD700, "hoist": True,  "level": "admin"},
        {"name": "🛠️ Admin",         "color": 0xE74C3C, "hoist": True,  "level": "admin"},
        {"name": "🌍 Moderateur",    "color": 0x3498DB, "hoist": True,  "level": "mod"},
        {"name": "🌟 VIP",           "color": 0xF39C12, "hoist": True,  "level": "member"},
        {"name": "👥 Membre",        "color": 0x2ECC71, "hoist": True,  "level": "member"},
        {"name": "🤖 Bot",           "color": 0x95A5A6, "hoist": True,  "level": "admin"},
        {"name": "🔇 Muted",         "color": 0x7F8C8D, "hoist": False, "level": "muted"},
    ],
    "business": [
        {"name": "👑 CEO",           "color": 0xFFD700, "hoist": True,  "level": "admin"},
        {"name": "💼 Manager",       "color": 0xE74C3C, "hoist": True,  "level": "admin"},
        {"name": "📊 Moderateur",    "color": 0x3498DB, "hoist": True,  "level": "mod"},
        {"name": "🏆 Senior",        "color": 0xF39C12, "hoist": True,  "level": "member"},
        {"name": "💡 Employe",       "color": 0x2ECC71, "hoist": True,  "level": "member"},
        {"name": "🤖 Bot",           "color": 0x95A5A6, "hoist": True,  "level": "admin"},
        {"name": "🔇 Muted",         "color": 0x7F8C8D, "hoist": False, "level": "muted"},
    ],
    "education": [
        {"name": "👑 Directeur",     "color": 0xFFD700, "hoist": True,  "level": "admin"},
        {"name": "👨‍🏫 Professeur", "color": 0xE74C3C, "hoist": True,  "level": "mod"},
        {"name": "🎓 VIP Etudiant",  "color": 0xF39C12, "hoist": True,  "level": "member"},
        {"name": "🎒 Etudiant",      "color": 0x2ECC71, "hoist": True,  "level": "member"},
        {"name": "🤖 Bot",           "color": 0x95A5A6, "hoist": True,  "level": "admin"},
        {"name": "🔇 Muted",         "color": 0x7F8C8D, "hoist": False, "level": "muted"},
    ],
    "creative": [
        {"name": "👑 Fondateur",     "color": 0xFFD700, "hoist": True,  "level": "admin"},
        {"name": "🎬 Admin Creatif", "color": 0xE74C3C, "hoist": True,  "level": "admin"},
        {"name": "🎨 Moderateur",    "color": 0x3498DB, "hoist": True,  "level": "mod"},
        {"name": "⭐ Artiste VIP",   "color": 0xF39C12, "hoist": True,  "level": "member"},
        {"name": "✍️ Createur",      "color": 0x2ECC71, "hoist": True,  "level": "member"},
        {"name": "🤖 Bot",           "color": 0x95A5A6, "hoist": True,  "level": "admin"},
        {"name": "🔇 Muted",         "color": 0x7F8C8D, "hoist": False, "level": "muted"},
    ],
}

# ──────────────────────────────────────────────────────────────────────────────
# VIEWS — Questions interactives
# ──────────────────────────────────────────────────────────────────────────────

class TypeView(ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=180)
        self.guild_id = guild_id

    async def _handle(self, interaction, value, label):
        setup_data[self.guild_id]["type"] = value
        self.stop()
        for c in self.children: c.disabled = True
        meta = TYPE_META[value]
        await interaction.response.edit_message(
            embed=discord.Embed(description=f"{meta['emoji_cat']} Type : **{label}**", color=meta["color"]),
            view=self
        )
        await ask_function(interaction.channel, self.guild_id)

    @ui.button(label="🎮 Gaming",     style=discord.ButtonStyle.primary)
    async def gaming(self, i, b):    await self._handle(i, "gaming",    "Gaming")
    @ui.button(label="🌍 Communaute", style=discord.ButtonStyle.primary)
    async def community(self, i, b): await self._handle(i, "community", "Communaute")
    @ui.button(label="💼 Business",   style=discord.ButtonStyle.primary)
    async def business(self, i, b):  await self._handle(i, "business",  "Business")
    @ui.button(label="📚 Education",  style=discord.ButtonStyle.primary)
    async def education(self, i, b): await self._handle(i, "education", "Education")
    @ui.button(label="🎨 Creatif",    style=discord.ButtonStyle.primary)
    async def creative(self, i, b):  await self._handle(i, "creative",  "Creatif")


class FunctionView(ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=180)
        self.guild_id = guild_id

    async def _handle(self, interaction, value, label, emoji):
        setup_data[self.guild_id]["function"] = value
        srv_type = setup_data[self.guild_id].get("type", "community")
        self.stop()
        for c in self.children: c.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(description=f"{emoji} Fonction : **{label}**", color=TYPE_META[srv_type]["color"]),
            view=self
        )
        await ask_format(interaction.channel, self.guild_id)

    @ui.button(label="💬 Communaute", style=discord.ButtonStyle.success)
    async def community(self, i, b): await self._handle(i, "community", "Communaute", "💬")
    @ui.button(label="🛠️ Support",    style=discord.ButtonStyle.success)
    async def support(self, i, b):   await self._handle(i, "support",   "Support",    "🛠️")
    @ui.button(label="🎉 Evenements", style=discord.ButtonStyle.success)
    async def events(self, i, b):    await self._handle(i, "events",    "Evenements", "🎉")
    @ui.button(label="📁 Portfolio",  style=discord.ButtonStyle.success)
    async def portfolio(self, i, b): await self._handle(i, "portfolio", "Portfolio",  "📁")
    @ui.button(label="🎭 Roleplay",   style=discord.ButtonStyle.success)
    async def roleplay(self, i, b):  await self._handle(i, "roleplay",  "Roleplay",   "🎭")


class FormatView(ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=180)
        self.guild_id = guild_id

    async def _handle(self, interaction, value, label):
        setup_data[self.guild_id]["format"] = value
        srv_type = setup_data[self.guild_id].get("type", "community")
        self.stop()
        for c in self.children: c.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(description=f"✅ Format : **{label}**", color=TYPE_META[srv_type]["color"]),
            view=self
        )
        await ask_categories(interaction.channel, self.guild_id)

    @ui.button(label="🔥 ┃ SALON",       style=discord.ButtonStyle.secondary)
    async def fire(self, i, b):    await self._handle(i, "fire",    "🔥 ┃ SALON")
    @ui.button(label="━━ emoji SALON ━━", style=discord.ButtonStyle.secondary)
    async def dash(self, i, b):    await self._handle(i, "dash",    "━━ emoji SALON ━━")
    @ui.button(label="[ emoji SALON ]",  style=discord.ButtonStyle.secondary)
    async def bracket(self, i, b): await self._handle(i, "bracket", "[ emoji SALON ]")
    @ui.button(label="emoji » SALON",    style=discord.ButtonStyle.secondary)
    async def arrow(self, i, b):   await self._handle(i, "arrow",   "emoji » SALON")
    @ui.button(label="📝 salon-simple",  style=discord.ButtonStyle.secondary)
    async def plain(self, i, b):   await self._handle(i, "plain",   "Simple")


class CategoriesView(ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=180)
        self.guild_id = guild_id

    async def _handle(self, interaction, value, label):
        setup_data[self.guild_id]["num_cat"] = value
        srv_type = setup_data[self.guild_id].get("type", "community")
        self.stop()
        for c in self.children: c.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(description=f"✅ Categories : **{label}**", color=TYPE_META[srv_type]["color"]),
            view=self
        )
        await build_server(interaction.channel, interaction.guild, self.guild_id)

    @ui.button(label="2 Categories",  style=discord.ButtonStyle.danger)
    async def c2(self, i, b): await self._handle(i, 2, "2 Categories")
    @ui.button(label="3 Categories",  style=discord.ButtonStyle.danger)
    async def c3(self, i, b): await self._handle(i, 3, "3 Categories")
    @ui.button(label="4 Categories",  style=discord.ButtonStyle.danger)
    async def c4(self, i, b): await self._handle(i, 4, "4 Categories")
    @ui.button(label="5 Categories",  style=discord.ButtonStyle.danger)
    async def c5(self, i, b): await self._handle(i, 5, "5 Categories")
    @ui.button(label="6+ Categories", style=discord.ButtonStyle.danger)
    async def c6(self, i, b): await self._handle(i, 6, "6+ Categories")


# ──────────────────────────────────────────────────────────────────────────────
# CONFIRMATION /leave
# ──────────────────────────────────────────────────────────────────────────────

class LeaveConfirmView(ui.View):
    def __init__(self, guild: discord.Guild, owner_id: int):
        super().__init__(timeout=60)
        self.guild    = guild
        self.owner_id = owner_id

    @ui.button(label="✅ Confirmer", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        self.stop()
        for c in self.children: c.disabled = True

        embed = discord.Embed(
            title="♻️ Reset en cours...",
            description=(
                "```\n"
                "🗑️  Suppression de tous les salons...\n"
                "🎭  Suppression de tous les roles...\n"
                "🏗️  Creation du salon general par defaut...\n"
                "👋  Depart du bot...\n"
                "```"
            ),
            color=0xE74C3C
        )
        await interaction.response.edit_message(embed=embed, view=self)

        guild = self.guild

        # 1. Supprimer tous les salons
        for ch in list(guild.channels):
            try:
                await ch.delete()
                await asyncio.sleep(0.3)
            except Exception:
                pass

        # 2. Supprimer tous les roles (sauf @everyone et celui du bot)
        for role in list(guild.roles):
            if role.is_default() or role.managed:
                continue
            try:
                await role.delete()
                await asyncio.sleep(0.3)
            except Exception:
                pass

        # 3. Recreer un salon #general par defaut
        try:
            general = await guild.create_text_channel(
                "general",
                topic="Salon par defaut — reconfigure le serveur en ajoutant ServerBuilder a nouveau."
            )

            goodbye = discord.Embed(
                title="👋 ServerBuilder a quitte le serveur",
                description=(
                    "Le serveur a ete **remis a zero** avec succes.\n\n"
                    "**Ce qui a ete supprime :**\n"
                    "🗑️  Tous les salons & categories\n"
                    "🎭  Tous les roles personnalises\n\n"
                    "**Ton slot a ete libere.** Tu peux maintenant reinviter le bot "
                    "sur un autre serveur ou reconfigurer celui-ci.\n\n"
                    "A bientot ! 🚀"
                ),
                color=0xE74C3C
            )
            goodbye.set_footer(text="ServerBuilder v2.0 • Slot libere avec succes")
            await general.send(embed=goodbye)
            await asyncio.sleep(2)
        except Exception:
            pass

        # 4. Liberer le slot et quitter
        remove_user_server(self.owner_id, guild.id)
        await guild.leave()

    @ui.button(label="❌ Annuler", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        self.stop()
        for c in self.children: c.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(
                description="❌ Commande annulee. Le bot reste sur le serveur.",
                color=0x95A5A6
            ),
            view=self
        )


# ──────────────────────────────────────────────────────────────────────────────
# SLASH COMMAND — /leave
# ──────────────────────────────────────────────────────────────────────────────

@tree.command(name="leave", description="Remet le serveur a zero et libere votre slot ServerBuilder")
async def leave_command(interaction: discord.Interaction):
    guild    = interaction.guild
    owner_id = guild.owner_id

    # Seul le proprietaire peut utiliser cette commande
    if interaction.user.id != owner_id:
        await interaction.response.send_message(
            embed=discord.Embed(
                description="🚫 Seul le **proprietaire du serveur** peut utiliser cette commande.",
                color=0xE74C3C
            ),
            ephemeral=True
        )
        return

    # Verifie que ce serveur est bien enregistre
    if guild.id not in get_user_servers(owner_id):
        await interaction.response.send_message(
            embed=discord.Embed(
                description="⚠️ Ce serveur n'est pas enregistre dans ServerBuilder.",
                color=0xF39C12
            ),
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="⚠️ Confirmation requise",
        description=(
            "Tu es sur le point de **remettre ce serveur a zero** et de faire **quitter le bot**.\n\n"
            "**Ce qui sera supprime :**\n"
            "🗑️  Tous les salons & categories\n"
            "🎭  Tous les roles personnalises\n\n"
            "**Ce qui sera garde :**\n"
            "✅  Un salon `#general` vide sera recrée\n"
            "✅  Ton slot ServerBuilder sera libere\n\n"
            "⚠️ **Cette action est irreversible.** Es-tu sur ?"
        ),
        color=0xF39C12
    )
    embed.set_footer(text="Tu as 60 secondes pour confirmer.")
    await interaction.response.send_message(embed=embed, view=LeaveConfirmView(guild, owner_id))


# ──────────────────────────────────────────────────────────────────────────────
# QUESTIONS DE SETUP
# ──────────────────────────────────────────────────────────────────────────────

async def ask_type(channel, guild_id):
    e = discord.Embed(
        title="🎮 Question 1 / 4 — Type de serveur",
        description="Quel est le **type** de ton serveur ?",
        color=0x5865F2
    )
    e.add_field(name="🎮 Gaming",     value="Gaming & esport",          inline=True)
    e.add_field(name="🌍 Communaute", value="Communautaire & social",    inline=True)
    e.add_field(name="💼 Business",   value="Professionnel & equipe",    inline=True)
    e.add_field(name="📚 Education",  value="Scolaire & formation",      inline=True)
    e.add_field(name="🎨 Creatif",    value="Art & creation",            inline=True)
    e.set_footer(text="Clique sur un bouton 👇")
    await channel.send(embed=e, view=TypeView(guild_id))

async def ask_function(channel, guild_id):
    srv_type = setup_data[guild_id].get("type", "community")
    meta     = TYPE_META[srv_type]
    e = discord.Embed(
        title=f"{meta['emoji_cat']} Question 2 / 4 — Fonction principale",
        description="Quelle est la **fonction principale** de ton serveur ?",
        color=meta["color"]
    )
    await channel.send(embed=e, view=FunctionView(guild_id))

async def ask_format(channel, guild_id):
    srv_type  = setup_data[guild_id].get("type", "community")
    meta      = TYPE_META[srv_type]
    cat_emoji = meta["emoji_cat"]
    e = discord.Embed(
        title=f"{meta['emoji_text']} Question 3 / 4 — Format des salons",
        description=(
            f"Quel **format** pour les noms de salons ?\n\n"
            f"`{cat_emoji} ┃ SALON` — Style Fire\n"
            f"`━━ {cat_emoji} SALON ━━` — Style Dash\n"
            f"`[ {cat_emoji} SALON ]` — Style Bracket\n"
            f"`{cat_emoji} » SALON` — Style Arrow\n"
            f"`📝 salon-simple` — Style Simple"
        ),
        color=meta["color"]
    )
    await channel.send(embed=e, view=FormatView(guild_id))

async def ask_categories(channel, guild_id):
    srv_type = setup_data[guild_id].get("type", "community")
    meta     = TYPE_META[srv_type]
    e = discord.Embed(
        title=f"{meta['emoji_event']} Question 4 / 4 — Nombre de categories",
        description=(
            "Combien de **categories** veux-tu ?\n"
            f"*(La categorie {meta['emoji_staff']} STAFF est toujours incluse)*"
        ),
        color=meta["color"]
    )
    await channel.send(embed=e, view=CategoriesView(guild_id))

# ──────────────────────────────────────────────────────────────────────────────
# BUILD SERVER
# ──────────────────────────────────────────────────────────────────────────────

async def build_server(channel, guild: discord.Guild, guild_id):
    data     = setup_data[guild_id]
    srv_type = data["type"]
    fmt      = data["format"]
    num_cat  = data["num_cat"]
    meta     = TYPE_META[srv_type]
    owner_id = guild.owner_id

    add_user_server(owner_id, guild.id)

    await channel.send(embed=discord.Embed(
        title=f"{meta['emoji_cat']} Construction en cours...",
        description=(
            f"```\n"
            f"{meta['emoji_announce']} Suppression des anciens salons...\n"
            f"{meta['emoji_roles']}  Creation des roles...\n"
            f"{meta['emoji_cat']}  Creation des categories...\n"
            f"{meta['emoji_text']}  Creation des salons...\n"
            f"{meta['emoji_staff']}  Configuration des permissions...\n"
            f"```"
        ),
        color=meta["color"]
    ).set_footer(text="Patience, ca arrive ! 🚀"))

    created = {"roles": [], "cats": 0, "channels": 0}
    errors  = []

    for ch in list(guild.channels):
        try:
            await ch.delete(); await asyncio.sleep(0.35)
        except Exception as e:
            errors.append(f"Suppression: {e}")

    role_map   = {}
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
            else:
                perms = discord.Permissions(
                    read_messages=True, send_messages=True, connect=True, speak=True,
                    read_message_history=True, add_reactions=True, attach_files=True
                )
            role = await guild.create_role(
                name=rd["name"], color=discord.Color(rd["color"]),
                hoist=rd["hoist"], permissions=perms, mentionable=True
            )
            role_map[lvl]       = role_map.get(lvl, role)
            role_map[rd["name"]] = role
            created["roles"].append(rd["name"])
            await asyncio.sleep(0.35)
        except Exception as e:
            errors.append(f"Role {rd['name']}: {e}")

    staff_role  = role_map.get("mod")
    member_role = role_map.get("member")
    muted_role  = role_map.get("muted")

    template    = get_template(srv_type)
    normal_cats = [c for c in template if not c["staff_only"]]
    staff_cats  = [c for c in template if c["staff_only"]]
    selected    = normal_cats[:num_cat] + staff_cats

    for cat_data in selected:
        try:
            cat_emoji = meta[cat_data["emoji_key"]]
            cat_name  = format_category(fmt, cat_data["name"], cat_emoji)
            is_staff  = cat_data["staff_only"]

            ow = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False, connect=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True, connect=True),
            }
            if is_staff:
                if staff_role:
                    ow[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, connect=True, speak=True)
            else:
                if member_role:
                    ow[member_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, connect=True, speak=True, read_message_history=True)
                if staff_role:
                    ow[staff_role]  = discord.PermissionOverwrite(read_messages=True, send_messages=True, connect=True, speak=True, manage_messages=True)

            category = await guild.create_category(cat_name, overwrites=ow)
            created["cats"] += 1
            await asyncio.sleep(0.35)

            for ch_data in cat_data.get("channels", []):
                try:
                    ch_emoji = meta[ch_data["emoji_key"]]
                    ch_name  = format_channel(fmt, ch_data["name"], ch_emoji)
                    ch_ow    = dict(ow)
                    if muted_role:
                        ch_ow[muted_role] = discord.PermissionOverwrite(send_messages=False, speak=False, add_reactions=False)
                    if ch_data["type"] == "text":
                        await guild.create_text_channel(ch_name, category=category, overwrites=ch_ow, topic=ch_data.get("topic", ""))
                    else:
                        await guild.create_voice_channel(ch_name, category=category, overwrites=ch_ow)
                    created["channels"] += 1
                    await asyncio.sleep(0.35)
                except Exception as e:
                    errors.append(f"Salon {ch_data['name']}: {e}")
        except Exception as e:
            errors.append(f"Cat {cat_data['name']}: {e}")

    remaining = max(0, 2 - count_user_servers(owner_id))
    embed = discord.Embed(
        title=f"{meta['emoji_event']} Serveur configure avec succes !",
        description=f"**{guild.name}** est pret a accueillir ses membres 🚀",
        color=meta["color"]
    )
    embed.add_field(
        name="📊 Resume",
        value=f"{meta['emoji_roles']} **Roles** : {len(created['roles'])}\n{meta['emoji_cat']} **Categories** : {created['cats']}\n{meta['emoji_text']} **Salons** : {created['channels']}",
        inline=True
    )
    embed.add_field(
        name="⚙️ Config",
        value=f"{meta['emoji_cat']} **Type** : {meta['label']}\n{meta['emoji_text']} **Fonction** : {data['function'].capitalize()}\n{meta['emoji_announce']} **Format** : {fmt}",
        inline=True
    )
    embed.add_field(name=f"{meta['emoji_roles']} Roles crees", value="\n".join(created["roles"]) or "Aucun", inline=False)
    embed.add_field(
        name="💡 Liberer un slot",
        value="Utilise `/leave` pour remettre ce serveur a zero et liberer ton slot ServerBuilder.",
        inline=False
    )
    if errors:
        embed.add_field(name=f"⚠️ Erreurs ({len(errors)})", value="\n".join(errors[:5]), inline=False)
    embed.set_footer(text=f"ServerMaster v1.0 • Quota restant : {remaining} serveur(s) sur 2")

    first = next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
    if first:
        await first.send(embed=embed)

    setup_data.pop(guild_id, None)

# ──────────────────────────────────────────────────────────────────────────────
# EVENTS
# ──────────────────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    await tree.sync()

@bot.event
async def on_guild_join(guild: discord.Guild):
    owner_id = guild.owner_id
    count    = count_user_servers(owner_id)

    channel = next(
        (c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None
    )
    if not channel:
        return

    # LIMITE ATTEINTE
    if count >= 2:
        embed = discord.Embed(
            title="🚫 Limite atteinte",
            description=(
                f"<@{owner_id}>, tu as deja **2 serveurs** configures avec **ServerMaster**.\n\n"
                "La limite est fixee a **2 serveurs par utilisateur**.\n\n"
                "**Pour liberer un slot :**\n"
                "• Va sur l'un de tes serveurs existants\n"
                "• Utilise la commande `/leave`\n"
                "• Le serveur sera remis a zero et le slot libere\n\n"
                "Le bot va **quitter ce serveur** dans 15 secondes."
            ),
            color=0xE74C3C
        )
        embed.set_footer(text="ServerMaster v1.0 • Limite de 2 serveurs par utilisateur")
        await channel.send(embed=embed)
        await asyncio.sleep(15)
        await guild.leave()
        return

    # SETUP NORMAL
    setup_data[guild.id] = {}
    remaining = 2 - count - 1

    embed = discord.Embed(
        title=f"👋 Salut **{guild.name}** !",
        description=(
            "Je suis **ServerMaster** 🛠️ — je vais configurer ton serveur en quelques clics.\n\n"
            "**Ce que je vais creer :**\n"
            "✅  Categories & salons adaptes au type choisi\n"
            "✅  Roles avec les bonnes permissions\n"
            "✅  Restrictions (muted, staff-only...)\n"
            "✅  Emojis adaptes a l'ambiance\n\n"
            "⚠️ **Attention** — tous les salons & roles existants seront remplaces.\n\n"
            f"📊 **Quota** : apres cette config, il te restera **{remaining}** serveur(s) dispo sur 2.\n"
            f"💡 Pour liberer un slot plus tard, utilise `/leave` sur ce serveur."
        ),
        color=0x5865F2
    )
    embed.set_thumbnail(url=guild.me.display_avatar.url)
    embed.set_footer(text="ServerMaster v1.0 • Reponds aux 4 questions 👇")
    await channel.send(embed=embed)
    await asyncio.sleep(1)
    await ask_type(channel, guild.id)


@bot.tree.command(name="ban", description="Bannir un membre")
@app_commands.describe(member="Le membre à bannir", reason="La raison du ban")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison fournie"):
    ctx = await commands.Context.from_interaction(interaction)
    if not await check_hierarchy(ctx, member, "bannir"):
        return
    await member.ban(reason=reason)
    await interaction.response.send_message(f"✅ {member} a été banni. Raison : {reason}")

@bot.tree.command(name="unban", description="Débannir un utilisateur")
@app_commands.describe(user_id="L'ID de l'utilisateur à débannir")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    user = await bot.fetch_user(int(user_id))
    await interaction.guild.unban(user)
    await interaction.response.send_message(f"✅ {user} a été débanni.")

@bot.tree.command(name="clear", description="Supprimer des messages")
@app_commands.describe(amount="Nombre de messages à supprimer (1-100)")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int = 10):
    if amount < 1 or amount > 100:
        await interaction.response.send_message("❌ Le nombre doit être entre 1 et 100.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"✅ {len(deleted)} messages supprimés.")

@bot.tree.command(name="kick", description="Expulser un membre")
@app_commands.describe(member="Le membre à expulser", reason="La raison du kick")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison fournie"):
    ctx = await commands.Context.from_interaction(interaction)
    if not await check_hierarchy(ctx, member, "expulser"):
        return
    await member.kick(reason=reason)
    await interaction.response.send_message(f"✅ {member} a été expulsé. Raison : {reason}")

@bot.tree.command(name="mute", description="Mute un membre")
@app_commands.describe(member="Le membre à mute", duration="Durée en minutes", reason="La raison du mute")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, duration: int = 10, reason: str = "Aucune raison fournie"):
    ctx = await commands.Context.from_interaction(interaction)
    if not await check_hierarchy(ctx, member, "mute"):
        return
    until = discord.utils.utcnow() + timedelta(minutes=duration)
    await member.timeout(until, reason=reason)
    await interaction.response.send_message(f"✅ {member} a été mute pour {duration} minutes. Raison : {reason}")

@bot.tree.command(name="unmute", description="Unmute un membre")
@app_commands.describe(member="Le membre à unmute")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, member: discord.Member):
    ctx = await commands.Context.from_interaction(interaction)
    if not await check_hierarchy(ctx, member, "unmute"):
        return
    await member.timeout(None)
    await interaction.response.send_message(f"✅ {member} a été unmute.")


bot.run(os.getenv('DISCORD_TOKEN'))