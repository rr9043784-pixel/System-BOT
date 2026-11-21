import os
import json
import logging
from threading import Thread
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks
from flask import Flask

# =========================================================
# CONFIGURATION
# =========================================================

TOKEN = os.environ.get("DISCORD_TOKEN")
OWNER_ID = 1176149190192152626

STATS_DATA_FILE = "stats_data.json"
STATS_CHANNEL_ID = 1542994435472760953

ONLINE_PC_STATUS = "<:Online_pc_status:1557533156322582649>"
IDLE_STATUS = "<:Idle_status:1557533355711660082>"
DND_STATUS = "<:Doesnotbother_Status:1557533152639983646>"
STREAMING_STATUS = "<:Streaming_Status:1557533349105631284>"
OFFLINE_STATUS = "<:Offline_status:1557533351546458163>"

EXTENSIONS = [
    "message",
    "ticket",
    "chests",
    "rps",
    "drops",
    "verification",
    "welcome",
    "suggest",
    "automod",
    "generates",
    "gameprofiles",
    "announcement_site",
    "status_bot",
    "voice_bot",
    "info",
    "rules",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# =========================================================
# FLASK / RAILWAY
# =========================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "System-BOT is online!"


@app.route("/health")
def health():
    return {"status": "ok"}


def run_flask():
    port = int(os.environ.get("PORT", "8080"))
    app.run(
        host="0.0.0.0",
        port=port,
        use_reloader=False,
    )


# =========================================================
# STATS DATA
# =========================================================

def load_stats_data():
    default_data = {
        "message_id": None,
        "channel_id": STATS_CHANNEL_ID,
        "guild_id": None,
    }

    if not os.path.exists(STATS_DATA_FILE):
        return default_data

    try:
        with open(STATS_DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return default_data

        data["channel_id"] = STATS_CHANNEL_ID
        data.setdefault("message_id", None)
        data.setdefault("guild_id", None)

        return data

    except Exception:
        logging.exception("Failed to load stats_data.json")
        return default_data


def save_stats_data(data):
    temp_file = STATS_DATA_FILE + ".tmp"

    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

    os.replace(temp_file, STATS_DATA_FILE)


stats_data = load_stats_data()


# =========================================================
# DISCORD BOT
# =========================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True


class TournamentBot(commands.Bot):

    async def setup_hook(self):
        for extension in EXTENSIONS:
            try:
                await self.load_extension(extension)
                logging.info("Loaded extension: %s.py", extension)

            except Exception:
                logging.exception(
                    "Failed to load extension: %s.py",
                    extension,
                )

        try:
            synced = await self.tree.sync()
            logging.info(
                "Slash commands synced: %s",
                len(synced),
            )

        except Exception:
            logging.exception("Failed to sync slash commands")


bot = TournamentBot(
    command_prefix="!",
    intents=intents,
)

bot.web_app = app


# =========================================================
# BOT PRESENCE
# =========================================================

async def set_bot_presence():
    """Restore the presence saved by status_bot.py."""
    try:
        from status_bot import apply_saved_presence

        await apply_saved_presence(bot)
        logging.info("Bot presence restored from status_data.json")

    except Exception:
        logging.exception("Failed to restore saved bot presence")


# =========================================================
# STATISTICS HELPERS
# =========================================================

def format_number(number):
    return f"{number:,}"


def get_enum_name(value):
    if value is None:
        return "Unknown"

    return getattr(value, "name", str(value)).replace("_", " ").title()


def get_member_statistics(guild):
    members = guild.members

    humans = [member for member in members if not member.bot]
    bots = [member for member in members if member.bot]

    online = sum(
        member.status == discord.Status.online
        for member in humans
    )

    idle = sum(
        member.status == discord.Status.idle
        for member in humans
    )

    dnd = sum(
        member.status == discord.Status.dnd
        for member in humans
    )

    offline = sum(
        member.status in (
            discord.Status.offline,
            discord.Status.invisible,
        )
        for member in humans
    )

    streaming = sum(
        any(
            isinstance(activity, discord.Streaming)
            for activity in member.activities
        )
        for member in humans
    )

    return {
        "cached": len(members),
        "total": guild.member_count or len(members),
        "humans": len(humans),
        "bots": len(bots),
        "online": online,
        "idle": idle,
        "dnd": dnd,
        "offline": offline,
        "streaming": streaming,
    }


def get_channel_statistics(guild):
    channels = guild.channels

    text_channels = [
        channel for channel in channels
        if isinstance(channel, discord.TextChannel)
        and not channel.is_news()
    ]

    announcement_channels = [
        channel for channel in channels
        if isinstance(channel, discord.TextChannel)
        and channel.is_news()
    ]

    voice_channels = [
        channel for channel in channels
        if isinstance(channel, discord.VoiceChannel)
    ]

    stage_channels = [
        channel for channel in channels
        if isinstance(channel, discord.StageChannel)
    ]

    categories = [
        channel for channel in channels
        if isinstance(channel, discord.CategoryChannel)
    ]

    forum_channels = [
        channel for channel in channels
        if isinstance(channel, discord.ForumChannel)
    ]

    threads = guild.threads

    return {
        "text": len(text_channels),
        "announcements": len(announcement_channels),
        "voice": len(voice_channels),
        "stage": len(stage_channels),
        "categories": len(categories),
        "forums": len(forum_channels),
        "threads": len(threads),
        "total": len(channels),
    }


def get_role_statistics(guild):
    roles = guild.roles

    normal_roles = [
        role for role in roles
        if not role.is_default() and not role.managed
    ]

    managed_roles = [
        role for role in roles
        if role.managed
    ]

    members_with_roles = sum(
        len(member.roles) > 1
        for member in guild.members
    )

    return {
        "total": max(len(roles) - 1, 0),
        "normal": len(normal_roles),
        "managed": len(managed_roles),
        "members_with_roles": members_with_roles,
    }


def get_emoji_statistics(guild):
    emojis = guild.emojis

    animated = sum(emoji.animated for emoji in emojis)
    static = len(emojis) - animated

    return {
        "total": len(emojis),
        "animated": animated,
        "static": static,
        "stickers": len(guild.stickers),
    }


def get_boost_statistics(guild):
    boosts = guild.premium_subscription_count or 0
    tier = guild.premium_tier

    levels = {
        0: "No Level",
        1: "Level 1",
        2: "Level 2",
        3: "Level 3",
    }

    return {
        "count": boosts,
        "tier": levels.get(tier, f"Level {tier}"),
        "boosters": sum(
            member.premium_since is not None
            for member in guild.members
        ),
    }


def get_server_age(guild):
    now = datetime.now(timezone.utc)
    created = guild.created_at

    days = max((now - created).days, 0)
    years, remaining_days = divmod(days, 365)

    if years:
        return f"{years} years, {remaining_days} days"

    return f"{days} days"


def get_server_security(guild):
    return {
        "verification": get_enum_name(guild.verification_level),
        "content_filter": get_enum_name(guild.explicit_content_filter),
        "notifications": get_enum_name(guild.default_notifications),
        "mfa": get_enum_name(guild.mfa_level),
        "afk_timeout": f"{guild.afk_timeout // 60} minutes",
    }


# =========================================================
# COMPONENTS V2 STATISTICS
# =========================================================

def build_stats_view(guild: discord.Guild):
    members = get_member_statistics(guild)
    channels = get_channel_statistics(guild)
    roles = get_role_statistics(guild)
    emojis = get_emoji_statistics(guild)
    boosts = get_boost_statistics(guild)
    security = get_server_security(guild)

    created = f"<t:{int(guild.created_at.timestamp())}:F>"
    created_relative = f"<t:{int(guild.created_at.timestamp())}:R>"
    updated = f"<t:{int(discord.utils.utcnow().timestamp())}:F>"

    owner = guild.owner.mention if guild.owner else f"<@{guild.owner_id}>"

    icon_text = (
        f"[Server Icon]({guild.icon.url})"
        if guild.icon else "No icon"
    )

    banner_text = (
        f"[Server Banner]({guild.banner.url})"
        if guild.banner else "No banner"
    )

    features = [
        feature.replace("_", " ").title()
        for feature in guild.features
    ]

    features_text = (
        ", ".join(features[:10])
        if features else "No special features"
    )

    if len(features) > 10:
        features_text += f" and {len(features) - 10} more"

    boost_progress = (
        "Enabled"
        if guild.premium_progress_bar_enabled
        else "Disabled"
    )

    system_channel = (
        guild.system_channel.mention
        if guild.system_channel else "Not configured"
    )

    rules_channel = (
        guild.rules_channel.mention
        if guild.rules_channel else "Not configured"
    )

    updates_channel = (
        guild.public_updates_channel.mention
        if guild.public_updates_channel else "Not configured"
    )

    afk_channel = (
        guild.afk_channel.mention
        if guild.afk_channel else "Not configured"
    )

    member_info = (
        f"**Total Members:** {format_number(members['total'])}\n"
        f"**Humans:** {format_number(members['humans'])}\n"
        f"**Bots:** {format_number(members['bots'])}\n"
        f"**Cached Members:** {format_number(members['cached'])}\n"
        f"**Members with Roles:** {format_number(roles['members_with_roles'])}"
    )

    status_info = (
        f"{ONLINE_PC_STATUS} **Online:** {format_number(members['online'])}\n"
        f"{IDLE_STATUS} **Idle:** {format_number(members['idle'])}\n"
        f"{DND_STATUS} **Do Not Disturb:** {format_number(members['dnd'])}\n"
        f"{STREAMING_STATUS} **Streaming:** {format_number(members['streaming'])}\n"
        f"{OFFLINE_STATUS} **Offline:** {format_number(members['offline'])}\n"
        "-# Status counts are based on cached human members. Streaming can overlap with Online."
    )

    channel_info = (
        f"**Total Channels:** {format_number(channels['total'])}\n"
        f"**Text Channels:** {format_number(channels['text'])}\n"
        f"**Announcement Channels:** {format_number(channels['announcements'])}\n"
        f"**Voice Channels:** {format_number(channels['voice'])}\n"
        f"**Stage Channels:** {format_number(channels['stage'])}\n"
        f"**Forum Channels:** {format_number(channels['forums'])}\n"
        f"**Categories:** {format_number(channels['categories'])}\n"
        f"**Active Cached Threads:** {format_number(channels['threads'])}"
    )

    role_info = (
        f"**Total Roles:** {format_number(roles['total'])}\n"
        f"**Normal Roles:** {format_number(roles['normal'])}\n"
        f"**Managed Roles:** {format_number(roles['managed'])}"
    )

    boost_info = (
        f"**Boost Count:** {format_number(boosts['count'])}\n"
        f"**Server Level:** {boosts['tier']}\n"
        f"**Cached Boosters:** {format_number(boosts['boosters'])}\n"
        f"**Boost Progress Bar:** {boost_progress}"
    )

    emoji_info = (
        f"**Total Emojis:** {format_number(emojis['total'])}\n"
        f"**Static Emojis:** {format_number(emojis['static'])}\n"
        f"**Animated Emojis:** {format_number(emojis['animated'])}\n"
        f"**Stickers:** {format_number(emojis['stickers'])}"
    )

    security_info = (
        f"**Verification Level:** {security['verification']}\n"
        f"**Explicit Content Filter:** {security['content_filter']}\n"
        f"**Default Notifications:** {security['notifications']}\n"
        f"**2FA Requirement:** {security['mfa']}\n"
        f"**AFK Timeout:** {security['afk_timeout']}"
    )

    server_info = (
        f"**Server Name:** {guild.name}\n"
        f"**Server ID:** `{guild.id}`\n"
        f"**Owner:** {owner}\n"
        f"**Preferred Language:** {guild.preferred_locale}\n"
        f"**Server Age:** {get_server_age(guild)}\n"
        f"**Created:** {created}\n"
        f"**Created Relative:** {created_relative}\n"
        f"**Icon:** {icon_text}\n"
        f"**Banner:** {banner_text}"
    )

    channel_settings = (
        f"**System Channel:** {system_channel}\n"
        f"**Rules Channel:** {rules_channel}\n"
        f"**Community Updates:** {updates_channel}\n"
        f"**AFK Channel:** {afk_channel}"
    )

    server_features = (
        f"**Features:** {features_text}\n"
        f"**Maximum Members:** {format_number(guild.max_members or 0)}\n"
        f"**File Upload Limit:** {guild.filesize_limit // (1024 * 1024)} MB"
    )

    view = discord.ui.LayoutView(timeout=None)

    container = discord.ui.Container(
        discord.ui.TextDisplay(
            "# 📊 LEGENDS SERVER STATISTICS\n"
            f"### {guild.name}\n"
            "-# Live server information • Automatically updated every minute"
        ),
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.large),

        discord.ui.TextDisplay(
            "## 👥 Member Statistics\n"
            f"{member_info}"
        ),
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),

        discord.ui.TextDisplay(
            "## 🟢 Member Status\n"
            f"{status_info}"
        ),
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),

        discord.ui.TextDisplay(
            "## 📁 Channel Statistics\n"
            f"{channel_info}"
        ),
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),

        discord.ui.TextDisplay(
            "## 🎭 Role Statistics\n"
            f"{role_info}"
        ),
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),

        discord.ui.TextDisplay(
            "## 🚀 Server Boosts\n"
            f"{boost_info}"
        ),
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),

        discord.ui.TextDisplay(
            "## 😀 Emojis & Stickers\n"
            f"{emoji_info}"
        ),
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),

        discord.ui.TextDisplay(
            "## 🔐 Security Settings\n"
            f"{security_info}"
        ),
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),

        discord.ui.TextDisplay(
            "## ⚙️ Server Information\n"
            f"{server_info}"
        ),
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),

        discord.ui.TextDisplay(
            "## 📌 Channel Configuration\n"
            f"{channel_settings}"
        ),
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),

        discord.ui.TextDisplay(
            "## ✨ Server Features\n"
            f"{server_features}"
        ),
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.large),

        discord.ui.TextDisplay(
            "### 🔄 Statistics Update\n"
            f"**Last Updated:** {updated}\n"
            "-# Powered by LEGENDS System-BOT"
        ),
        accent_colour=discord.Color.from_rgb(88, 101, 242),
    )

    view.add_item(container)

    return view


# =========================================================
# GET STATS CHANNEL
# =========================================================

async def get_stats_channel():
    try:
        channel = bot.get_channel(STATS_CHANNEL_ID)

        if channel is None:
            channel = await bot.fetch_channel(STATS_CHANNEL_ID)

        if isinstance(channel, discord.TextChannel):
            return channel

        logging.error(
            "Stats channel %s is not a text channel.",
            STATS_CHANNEL_ID,
        )

    except discord.NotFound:
        logging.error(
            "Stats channel %s does not exist.",
            STATS_CHANNEL_ID,
        )

    except discord.Forbidden:
        logging.error(
            "Bot cannot access stats channel %s.",
            STATS_CHANNEL_ID,
        )

    except discord.HTTPException:
        logging.exception("Failed to fetch stats channel")

    except Exception:
        logging.exception("Stats channel error")

    return None


# =========================================================
# UPDATE STATISTICS
# =========================================================

async def update_stats_for_guild(guild: discord.Guild):
    global stats_data

    if guild is None:
        return

    # Try to fill the member cache so the statistics are more complete.
    if not guild.chunked:
        try:
            await guild.chunk(cache=True)
        except (discord.Forbidden, discord.HTTPException):
            logging.warning("Could not fully chunk guild members.")

    channel = await get_stats_channel()

    if channel is None:
        logging.error("Statistics channel not found.")
        return

    view = build_stats_view(guild)

    message_id = stats_data.get("message_id")
    stored_guild_id = stats_data.get("guild_id")
    stored_channel_id = stats_data.get("channel_id")

    if stored_channel_id != STATS_CHANNEL_ID:
        message_id = None
        stats_data["message_id"] = None
        stats_data["channel_id"] = STATS_CHANNEL_ID

    if message_id and stored_guild_id == guild.id:
        try:
            message = await channel.fetch_message(int(message_id))

            await message.edit(
                content=None,
                embeds=[],
                view=view,
            )

            logging.info("Components V2 stats message updated.")
            return

        except discord.NotFound:
            logging.warning(
                "Old stats message not found. Creating a new one."
            )
            stats_data["message_id"] = None

        except discord.Forbidden:
            logging.error("Bot has no permission to edit stats.")
            return

        except discord.HTTPException:
            logging.exception("Failed to edit stats")
            return

    try:
        message = await channel.send(view=view)

        stats_data = {
            "message_id": message.id,
            "channel_id": STATS_CHANNEL_ID,
            "guild_id": guild.id,
        }

        save_stats_data(stats_data)

        logging.info(
            "Components V2 stats message created: %s",
            message.id,
        )

    except discord.Forbidden:
        logging.error("Bot has no permission to send stats.")

    except discord.HTTPException:
        logging.exception("Failed to create stats message")

    except Exception:
        logging.exception("Unexpected stats error")


# =========================================================
# AUTOMATIC STATS UPDATE
# =========================================================

@tasks.loop(minutes=1)
async def update_stats_message():
    await set_bot_presence()

    guild_id = stats_data.get("guild_id")

    if not guild_id:
        return

    guild = bot.get_guild(int(guild_id))

    if guild is not None:
        await update_stats_for_guild(guild)


@update_stats_message.before_loop
async def before_stats_loop():
    await bot.wait_until_ready()


# =========================================================
# BOT READY
# =========================================================

@bot.event
async def on_ready():
    logging.info(
        "Logged in as %s (%s)",
        bot.user,
        bot.user.id if bot.user else "?",
    )

    await set_bot_presence()

    if not update_stats_message.is_running():
        update_stats_message.start()

    logging.info("Bot is ready!")


# =========================================================
# OWNER CHECK
# =========================================================

def owner_only():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.id == OWNER_ID

    return app_commands.check(predicate)


# =========================================================
# PREFIX COMMANDS
# =========================================================

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.content.strip().lower() == "!my stats bot":

        if message.author.id != OWNER_ID:
            return

        if message.guild is None:
            return

        try:
            await message.delete()
        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException,
        ):
            pass

        stats_data["guild_id"] = message.guild.id
        stats_data["channel_id"] = STATS_CHANNEL_ID
        stats_data["message_id"] = None

        save_stats_data(stats_data)

        logging.info(
            "Creating Components V2 stats in channel %s...",
            STATS_CHANNEL_ID,
        )

        await update_stats_for_guild(message.guild)
        return

    await bot.process_commands(message)


# =========================================================
# /open dms
# =========================================================

class OpenDMsView(discord.ui.View):

    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id

        settings_button = discord.ui.Button(
            label="Through Settings",
            emoji="⚙️",
            style=discord.ButtonStyle.link,
            url="https://discord.com/settings/privacy",
        )

        self.add_item(settings_button)

        profile_button = discord.ui.Button(
            label="Through Bot Profile",
            emoji="🤖",
            style=discord.ButtonStyle.secondary,
        )

        profile_button.callback = self.profile_callback
        self.add_item(profile_button)

        self.check_button = discord.ui.Button(
            label="Check DMs",
            emoji="🔍",
            style=discord.ButtonStyle.success,
        )

        self.check_button.callback = self.check_dms_callback
        self.add_item(self.check_button)

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:

        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ This panel belongs to another user.",
                ephemeral=True,
            )
            return False

        return True

    async def profile_callback(
        self,
        interaction: discord.Interaction,
    ):

        await interaction.response.send_message(
            "🤖 Open my profile and use **Add App** to add the bot to your apps.",
            ephemeral=True,
        )

    async def check_dms_callback(
        self,
        interaction: discord.Interaction,
    ):

        try:
            test_message = await interaction.user.send(
                "✅ DM check successful."
            )

            try:
                await test_message.delete()
            except (discord.Forbidden, discord.HTTPException):
                pass

            self.check_button.disabled = True

            await interaction.response.edit_message(view=self)

            await interaction.followup.send(
                "✅ Your DMs are now open!",
                ephemeral=True,
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Your DMs are still closed.",
                ephemeral=True,
            )

        except discord.HTTPException:
            await interaction.response.send_message(
                "❌ I couldn't check your DMs right now.",
                ephemeral=True,
            )


open_group = app_commands.Group(
    name="open",
    description="Open and check settings",
)


@open_group.command(
    name="dms",
    description="Check and open your DMs with the bot",
)
async def open_dms(interaction: discord.Interaction):

    try:
        test_message = await interaction.user.send(
            "✅ DM check successful."
        )

        try:
            await test_message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass

        await interaction.response.send_message(
            "✅ Your DMs are already open!",
            ephemeral=True,
        )
        return

    except discord.Forbidden:
        pass

    except discord.HTTPException:
        await interaction.response.send_message(
            "❌ I couldn't check your DMs right now.",
            ephemeral=True,
        )
        return

    embed = discord.Embed(
        title="📩 Open DMs",
        description=(
            "Your DMs are currently closed.\n\n"
            "**Choose one of the methods below:**\n\n"
            "⚙️ **Through Settings**\n"
            "Open your Discord Privacy settings and allow "
            "direct messages from server members.\n\n"
            "🤖 **Through Bot Profile**\n"
            "Open my profile and use **Add App**.\n\n"
            "🔍 **Check DMs**\n"
            "After changing the settings, press the button "
            "to check again."
        ),
        color=discord.Color.blurple(),
    )

    await interaction.response.send_message(
        embed=embed,
        view=OpenDMsView(interaction.user.id),
        ephemeral=True,
    )


bot.tree.add_command(open_group)


# =========================================================
# /send message and /send dms
# =========================================================

send_group = app_commands.Group(
    name="send",
    description="Send messages",
)


@send_group.command(
    name="message",
    description="Send a message to a channel",
)
@app_commands.describe(
    text="Text to send",
    channel="Channel where the message will be sent",
)
@owner_only()
async def send_message(
    interaction: discord.Interaction,
    text: str,
    channel: discord.TextChannel,
):

    try:
        await channel.send(f"**BOT:** {text}")

        await interaction.response.send_message(
            "Message sent successfully.",
            ephemeral=True,
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I don't have permission to send messages in that channel.",
            ephemeral=True,
        )

    except discord.HTTPException:
        await interaction.response.send_message(
            "❌ Failed to send the message.",
            ephemeral=True,
        )


@send_group.command(
    name="dms",
    description="Send a direct message to a user",
)
@app_commands.describe(
    user="User to send the DM to",
    message="Message to send",
)
@owner_only()
async def send_dms(
    interaction: discord.Interaction,
    user: discord.User,
    message: str,
):

    try:
        server_name = (
            interaction.guild.name
            if interaction.guild
            else "Unknown Server"
        )

        await user.send(
            f"**BOT:** {message}\n"
            f"-# Server: {server_name}"
        )

        await interaction.response.send_message(
            "DM sent successfully.",
            ephemeral=True,
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ Could not send a DM. The user's DMs are closed.",
            ephemeral=True,
        )

    except discord.HTTPException:
        await interaction.response.send_message(
            "❌ Could not send the DM.",
            ephemeral=True,
        )


bot.tree.add_command(send_group)


# =========================================================
# /clear message
# =========================================================

clear_group = app_commands.Group(
    name="clear",
    description="Clear messages",
)


@clear_group.command(
    name="message",
    description="Delete messages from a channel",
)
@app_commands.describe(
    channel="Channel to clear",
    number_of_messages="Number of messages to delete",
)
@owner_only()
async def clear_message(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    number_of_messages: app_commands.Range[int, 1, 100],
):

    try:
        await interaction.response.defer(ephemeral=True)

        deleted = await channel.purge(
            limit=number_of_messages
        )

        await interaction.followup.send(
            f"Deleted {len(deleted)} message(s).",
            ephemeral=True,
        )

    except discord.Forbidden:
        message = (
            "❌ I don't have permission to delete messages in this channel."
        )

        if interaction.response.is_done():
            await interaction.followup.send(
                message,
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                message,
                ephemeral=True,
            )

    except discord.HTTPException:
        message = "❌ Failed to delete the messages."

        if interaction.response.is_done():
            await interaction.followup.send(
                message,
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                message,
                ephemeral=True,
            )


bot.tree.add_command(clear_group)


# =========================================================
# SLASH COMMAND ERRORS
# =========================================================

@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
):

    if isinstance(error, app_commands.CheckFailure):
        message = "❌ You do not have permission to use this command."
    else:
        logging.error(
            "Slash command error: %s",
            error,
            exc_info=(
                type(error),
                error,
                error.__traceback__,
            ),
        )
        message = "❌ The command failed. Please try again later."

    try:
        if interaction.response.is_done():
            await interaction.followup.send(
                message,
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                message,
                ephemeral=True,
            )

    except (discord.HTTPException, discord.InteractionResponded):
        pass


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    if not TOKEN:
        raise RuntimeError(
            "DISCORD_TOKEN is missing from Railway Variables."
        )

    Thread(
        target=run_flask,
        daemon=True,
    ).start()

    bot.run(TOKEN)
