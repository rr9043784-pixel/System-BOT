import os
import asyncio
import json

import discord
from discord import app_commands
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread


# =================================================
# Tokens
# =================================================

TOKEN = os.environ["DISCORD_TOKEN"]


# =================================================
# Settings
# =================================================

OWNER_ID = 1176149190192152626

STATS_DATA_FILE = "stats_data.json"

STATS_CHANNEL_ID = 1542994435472760953


# =================================================
# Flask
# =================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "Tournament Bot is online!"


def run_flask():

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )


# =================================================
# Stats Data
# =================================================

def load_stats_data():

    if not os.path.exists(STATS_DATA_FILE):

        return {
            "message_id": None,
            "channel_id": STATS_CHANNEL_ID,
            "guild_id": None
        }

    try:

        with open(
            STATS_DATA_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

            # Always use the current stats channel
            data["channel_id"] = STATS_CHANNEL_ID

            return data

    except Exception as e:

        print(
            f"❌ Failed to load stats_data.json: {e}"
        )

        return {
            "message_id": None,
            "channel_id": STATS_CHANNEL_ID,
            "guild_id": None
        }


def save_stats_data(data):

    temp_file = STATS_DATA_FILE + ".tmp"

    with open(
        temp_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4
        )

    os.replace(
        temp_file,
        STATS_DATA_FILE
    )


stats_data = load_stats_data()


# =================================================
# Discord Bot
# =================================================

intents = discord.Intents.default()

intents.message_content = True
intents.members = True


class TournamentBot(commands.Bot):

    async def setup_hook(self):

        # =================================================
        # message.py
        # =================================================

        try:

            await self.load_extension(
                "message"
            )

            print(
                "✅ message.py loaded!"
            )

        except Exception as e:

            print(
                f"❌ Failed to load message.py: {e}"
            )


        # =================================================
        # ticket.py
        # =================================================

        try:

            await self.load_extension(
                "ticket"
            )

            print(
                "✅ ticket.py loaded!"
            )

        except Exception as e:

            print(
                f"❌ Failed to load ticket.py: {e}"
            )


        # =================================================
        # chests.py
        # =================================================

        try:

            await self.load_extension(
                "chests"
            )

            print(
                "✅ chests.py loaded!"
            )

        except Exception as e:

            print(
                f"❌ Failed to load chests.py: {e}"
            )


        # =================================================
        # drops.py
        # =================================================

        try:

            await self.load_extension(
                "drops"
            )

            print(
                "✅ drops.py loaded!"
            )

        except Exception as e:

            print(
                f"❌ Failed to load drops.py: {e}"
            )


        # =================================================
        # Sync Slash Commands
        # =================================================

        try:

            await self.tree.sync()

            print(
                "✅ Slash commands synced!"
            )

        except Exception as e:

            print(
                f"❌ Failed to sync slash commands: {e}"
            )


bot = TournamentBot(
    command_prefix="!",
    intents=intents
)


# =================================================
# Presence
# =================================================

async def set_bot_presence():

    try:

        await bot.change_presence(
            status=discord.Status.idle,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Over server security 🎮『𝗟𝗘𝗚𝗘𝗡𝗗𝗦』🇷🇺🇬🇧"
            )
        )

        print(
            "🟡 Presence: IDLE | Watching Over server security"
        )

    except Exception as e:

        print(
            f"❌ Failed to set bot presence: {e}"
        )


# =================================================
# Bot Ready
# =================================================

@bot.event
async def on_ready():

    print(
        f"🤖 Logged in as {bot.user}"
    )

    await set_bot_presence()

    if not update_stats_message.is_running():

        update_stats_message.start()


# =================================================
# Owner Check
# =================================================

def owner_only():

    async def predicate(
        interaction: discord.Interaction
    ):

        return interaction.user.id == OWNER_ID

    return app_commands.check(
        predicate
    )


# =================================================
# STATS TEXT
# =================================================

def build_stats_text(guild: discord.Guild):

    members = guild.members

    total_members = len(members)

    humans = sum(
        1
        for member in members
        if not member.bot
    )

    bots_count = sum(
        1
        for member in members
        if member.bot
    )

    online = sum(
        1
        for member in members
        if member.status == discord.Status.online
    )

    idle = sum(
        1
        for member in members
        if member.status == discord.Status.idle
    )

    dnd = sum(
        1
        for member in members
        if member.status == discord.Status.dnd
    )

    offline = sum(
        1
        for member in members
        if member.status == discord.Status.offline
    )


    # =================================================
    # Devices
    # =================================================

    pc = 0
    mobile = 0

    for member in members:

        if member.bot:
            continue

        if member.status == discord.Status.offline:
            continue

        client_status = member.client_status

        if not client_status:
            continue

        if "mobile" in client_status:

            mobile += 1

        elif (
            "desktop" in client_status
            or "web" in client_status
        ):

            pc += 1


    # =================================================
    # Channels
    # =================================================

    text_channels = sum(
        1
        for channel in guild.channels
        if isinstance(
            channel,
            discord.TextChannel
        )
    )

    voice_channels = sum(
        1
        for channel in guild.channels
        if isinstance(
            channel,
            discord.VoiceChannel
        )
    )

    categories = sum(
        1
        for channel in guild.channels
        if isinstance(
            channel,
            discord.CategoryChannel
        )
    )


    # =================================================
    # Roles
    # =================================================

    roles = max(
        len(guild.roles) - 1,
        0
    )


    # =================================================
    # Boosts
    # =================================================

    boosts = guild.premium_subscription_count or 0

    boost_level = guild.premium_tier

    if isinstance(
        boost_level,
        discord.PremiumTier
    ):

        boost_level_text = boost_level.name.replace(
            "tier_",
            "Tier "
        )

    else:

        boost_level_text = str(
            boost_level
        )


    # =================================================
    # Created
    # =================================================

    created = (
        f"<t:{int(guild.created_at.timestamp())}:F>"
    )


    # =================================================
    # Updated
    # =================================================

    updated = (
        f"<t:{int(discord.utils.utcnow().timestamp())}:R>"
    )


    return (
        "📊 **BOT Statistics**\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "\n"
        f"👥 **Members:** {total_members:,}\n"
        f"👤 Humans: {humans:,}\n"
        f"🤖 Bots: {bots_count:,}\n"
        "\n"
        "🟢 **Status**\n"
        f"Online: {online:,}\n"
        f"Idle: {idle:,}\n"
        f"Do Not Disturb: {dnd:,}\n"
        f"Offline: {offline:,}\n"
        "\n"
        "📱 **Devices**\n"
        f"PC: {pc:,}\n"
        f"Mobile: {mobile:,}\n"
        "\n"
        "📁 **Channels**\n"
        f"Text: {text_channels:,}\n"
        f"Voice: {voice_channels:,}\n"
        f"Categories: {categories:,}\n"
        "\n"
        f"🎭 **Roles:** {roles:,}\n"
        "\n"
        "🚀 **Server Boosts**\n"
        f"Boosts: {boosts:,}\n"
        f"Level: {boost_level_text}\n"
        "\n"
        f"📅 **Server Created:** {created}\n"
        f"🔄 **Updated:** {updated}\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )


# =================================================
# Get Stats Channel
# =================================================

async def get_stats_channel():

    try:

        channel = await bot.fetch_channel(
            STATS_CHANNEL_ID
        )

        if not isinstance(
            channel,
            discord.TextChannel
        ):

            print(
                f"❌ Stats channel {STATS_CHANNEL_ID} is not a text channel."
            )

            return None

        return channel

    except discord.NotFound:

        print(
            f"❌ Stats channel {STATS_CHANNEL_ID} does not exist."
        )

    except discord.Forbidden:

        print(
            f"❌ Bot cannot access stats channel {STATS_CHANNEL_ID}."
        )

    except discord.HTTPException as e:

        print(
            f"❌ Failed to fetch stats channel: {e}"
        )

    except Exception as e:

        print(
            f"❌ Stats channel error: {e}"
        )

    return None


# =================================================
# Update Stats
# =================================================

async def update_stats_for_guild(
    guild: discord.Guild
):

    global stats_data

    if guild is None:
        return


    text = build_stats_text(
        guild
    )


    # =================================================
    # Get Stats Channel
    # =================================================

    channel = await get_stats_channel()

    if channel is None:

        print(
            "❌ Statistics message cannot be created because the channel was not found."
        )

        return


    # =================================================
    # Existing Message
    # =================================================

    message_id = stats_data.get(
        "message_id"
    )

    stored_channel_id = stats_data.get(
        "channel_id"
    )

    stored_guild_id = stats_data.get(
        "guild_id"
    )


    # If channel changed, forget old message
    if stored_channel_id != STATS_CHANNEL_ID:

        message_id = None

        stats_data["message_id"] = None
        stats_data["channel_id"] = STATS_CHANNEL_ID


    if (
        message_id
        and stored_guild_id == guild.id
    ):

        try:

            message = await channel.fetch_message(
                message_id
            )

            await message.edit(
                content=text
            )

            print(
                "🔄 Stats message updated."
            )

            return

        except discord.NotFound:

            print(
                "⚠️ Old stats message not found. Creating a new one."
            )

            stats_data["message_id"] = None

        except discord.Forbidden:

            print(
                "❌ Bot has no permission to edit the stats message."
            )

            return

        except discord.HTTPException as e:

            print(
                f"❌ Failed to edit stats message: {e}"
            )

            return


    # =================================================
    # Create New Stats Message
    # =================================================

    try:

        message = await channel.send(
            text
        )

        stats_data = {
            "message_id": message.id,
            "channel_id": STATS_CHANNEL_ID,
            "guild_id": guild.id
        }

        save_stats_data(
            stats_data
        )

        print(
            f"✅ Stats message created: {message.id}"
        )

    except discord.Forbidden:

        print(
            "❌ Bot has no permission to send messages in the stats channel."
        )

    except discord.HTTPException as e:

        print(
            f"❌ Failed to create stats message: {e}"
        )

    except Exception as e:

        print(
            f"❌ Unexpected stats error: {e}"
        )


# =================================================
# !my stats bot
# =================================================

@bot.event
async def on_message(message):

    if message.author.bot:
        return


    # =================================================
    # !my stats bot
    # =================================================

    if message.content.strip().lower() == "!my stats bot":

        if message.author.id != OWNER_ID:
            return


        if message.guild is None:
            return


        # Delete command
        try:

            await message.delete()

        except (
            discord.Forbidden,
            discord.HTTPException
        ):

            pass


        # Save current guild
        stats_data["guild_id"] = message.guild.id
        stats_data["channel_id"] = STATS_CHANNEL_ID

        # Reset old message because channel ID changed
        stats_data["message_id"] = None

        save_stats_data(
            stats_data
        )


        print(
            f"📊 Creating stats in channel {STATS_CHANNEL_ID}..."
        )


        # Create stats
        await update_stats_for_guild(
            message.guild
        )

        return


    # =================================================
    # Other Prefix Commands
    # =================================================

    await bot.process_commands(
        message
    )


# =================================================
# Presence Auto Refresh
# =================================================

@tasks.loop(
    seconds=10
)
async def update_presence():

    await set_bot_presence()


@update_presence.before_loop
async def before_presence_loop():

    await bot.wait_until_ready()


# =================================================
# Stats Auto Update Every 1 Minute
# =================================================

@tasks.loop(
    minutes=1
)
async def update_stats_message():

    guild_id = stats_data.get(
        "guild_id"
    )

    if not guild_id:
        return


    guild = bot.get_guild(
        guild_id
    )

    if not guild:
        return


    await update_stats_for_guild(
        guild
    )


@update_stats_message.before_loop
async def before_stats_loop():

    await bot.wait_until_ready()


# =================================================
# /send
# =================================================

send_group = app_commands.Group(
    name="send",
    description="Send messages"
)


@send_group.command(
    name="message",
    description="Send a message to a channel"
)
@app_commands.describe(
    text="Text to send",
    channel="Channel where the message will be sent"
)
@owner_only()
async def send_message(
    interaction: discord.Interaction,
    text: str,
    channel: discord.TextChannel
):

    try:

        await channel.send(
            f"**BOT:** {text}"
        )

        await interaction.response.send_message(
            "Message sent successfully.",
            ephemeral=True
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I don't have permission to send messages in that channel.",
            ephemeral=True
        )

    except discord.HTTPException:

        await interaction.response.send_message(
            "❌ Failed to send the message.",
            ephemeral=True
        )


@send_group.command(
    name="dms",
    description="Send a direct message to a user"
)
@app_commands.describe(
    user="User to send the DM to",
    message="Message to send"
)
@owner_only()
async def send_dms(
    interaction: discord.Interaction,
    user: discord.User,
    message: str
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
            ephemeral=True
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ Could not send a DM. The user's DMs are closed.",
            ephemeral=True
        )

    except discord.HTTPException:

        await interaction.response.send_message(
            "❌ Could not send the DM.",
            ephemeral=True
        )


bot.tree.add_command(
    send_group
)


# =================================================
# /clear
# =================================================

clear_group = app_commands.Group(
    name="clear",
    description="Clear messages"
)


@clear_group.command(
    name="message",
    description="Delete messages from a channel"
)
@app_commands.describe(
    channel="Channel to clear",
    number_of_messages="Number of messages to delete"
)
@owner_only()
async def clear_message(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    number_of_messages: app_commands.Range[int, 1, 100]
):

    try:

        deleted = await channel.purge(
            limit=number_of_messages
        )

        if len(deleted) == 1:

            await interaction.response.send_message(
                "1",
                ephemeral=True
            )

        else:

            await interaction.response.defer(
                ephemeral=True
            )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I don't have permission to delete messages in this channel.",
            ephemeral=True
        )

    except discord.HTTPException:

        await interaction.response.send_message(
            "❌ Failed to delete messages.",
            ephemeral=True
        )


bot.tree.add_command(
    clear_group
)


# =================================================
# Slash Command Errors
# =================================================

@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):

    if isinstance(
        error,
        app_commands.CheckFailure
    ):

        if not interaction.response.is_done():

            await interaction.response.send_message(
                "❌ You do not have permission to use this command.",
                ephemeral=True
            )


# =================================================
# Start Flask
# =================================================

Thread(
    target=run_flask,
    daemon=True
).start()


# =================================================
# Start Presence Loop
# =================================================

update_presence.start()


# =================================================
# Start Bot
# =================================================

bot.run(TOKEN)
