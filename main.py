import os
import json
import logging
from threading import Thread

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
    return "Tournament Bot is online!"


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
    try:
        await bot.change_presence(
            status=discord.Status.idle,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=(
                    "👻 Monitors the order on the server 👻⠀ "
                    "➜➜ 🎮『𝗟𝗘𝗚𝗘𝗡𝗗𝗦』🇷🇺🇬🇧"
                ),
            ),
        )

        logging.info("Presence set: Idle / Watching")

    except Exception:
        logging.exception("Failed to set bot presence")


# =========================================================
# STATISTICS TEXT
# =========================================================

def build_stats_text(guild: discord.Guild) -> str:
    members = guild.members

    total_members = len(members)
    humans = sum(not member.bot for member in members)
    bots_count = sum(member.bot for member in members)

    online = sum(
        not member.bot and member.status == discord.Status.online
        for member in members
    )

    idle = sum(
        not member.bot and member.status == discord.Status.idle
        for member in members
    )

    dnd = sum(
        not member.bot and member.status == discord.Status.dnd
        for member in members
    )

    offline = sum(
        not member.bot and member.status == discord.Status.offline
        for member in members
    )

    streaming = sum(
        not member.bot
        and any(
            isinstance(activity, discord.Streaming)
            for activity in member.activities
        )
        for member in members
    )

    text_channels = sum(
        isinstance(channel, discord.TextChannel)
        for channel in guild.channels
    )

    voice_channels = sum(
        isinstance(channel, discord.VoiceChannel)
        for channel in guild.channels
    )

    categories = sum(
        isinstance(channel, discord.CategoryChannel)
        for channel in guild.channels
    )

    roles = max(len(guild.roles) - 1, 0)

    boosts = guild.premium_subscription_count or 0
    boost_level = getattr(guild, "premium_tier", 0)

    try:
        boost_level_number = int(
            getattr(boost_level, "value", boost_level)
        )
    except (TypeError, ValueError):
        boost_level_number = 0

    boost_levels = {
        0: "No Level",
        1: "Level 1",
        2: "Level 2",
        3: "Level 3",
    }

    boost_level_text = boost_levels.get(
        boost_level_number,
        f"Level {boost_level_number}",
    )

    created = f"<t:{int(guild.created_at.timestamp())}:F>"
    updated = f"<t:{int(discord.utils.utcnow().timestamp())}:R>"

    return (
        "📊 **BOT Statistics**\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 **Members:** {total_members:,}\n"
        f"👤 Humans: {humans:,}\n"
        f"🤖 Bots: {bots_count:,}\n\n"
        "⬇️ **Status**\n"
        f"{ONLINE_PC_STATUS} Online: {online:,}\n"
        f"{IDLE_STATUS} Idle: {idle:,}\n"
        f"{DND_STATUS} Do Not Disturb: {dnd:,}\n"
        f"{STREAMING_STATUS} Streaming: {streaming:,}\n"
        f"{OFFLINE_STATUS} Offline: {offline:,}\n\n"
        "📁 **Channels**\n"
        f"Text: {text_channels:,}\n"
        f"Voice: {voice_channels:,}\n"
        f"Categories: {categories:,}\n\n"
        f"🎭 **Roles:** {roles:,}\n\n"
        "🚀 **Server Boosts**\n"
        f"Boosts: {boosts:,}\n"
        f"Level: {boost_level_text}\n\n"
        f"📅 **Server Created:** {created}\n"
        f"🔄 **Updated:** {updated}\n\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )


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

    channel = await get_stats_channel()

    if channel is None:
        logging.error("Statistics channel not found.")
        return

    text = build_stats_text(guild)

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
            await message.edit(content=text)

            logging.info("Stats message updated.")
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
        message = await channel.send(text)

        stats_data = {
            "message_id": message.id,
            "channel_id": STATS_CHANNEL_ID,
            "guild_id": guild.id,
        }

        save_stats_data(stats_data)

        logging.info(
            "Stats message created: %s",
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
            "Creating stats in channel %s...",
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
