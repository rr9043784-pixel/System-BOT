import os
import asyncio
import json

import discord
from discord import app_commands
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread


# =================================================
# Tokensimport os
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

STATS_CHANNEL_ID = 1539734753736134856


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

            if not data.get("channel_id"):

                data["channel_id"] = STATS_CHANNEL_ID

            return data

    except Exception:

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
        # Load message.py
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
        # Load ticket.py
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
        # Load chests.py
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
        # Load drops.py
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
# Bot Ready
# =================================================

@bot.event
async def on_ready():

    print(
        f"🤖 Logged in as {bot.user}"
    )

    # =================================================
    # Status
    # =================================================

    await bot.change_presence(
        status=discord.Status.idle,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="over server security 🎮『𝗟𝗘𝗚𝗘𝗡𝗗𝗦』🇷🇺🇬🇧"
        )
    )

    # =================================================
    # Start Stats
    # =================================================

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
# STATS
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


async def update_stats_for_guild(
    guild: discord.Guild
):

    global stats_data

    if not guild:
        return


    text = build_stats_text(
        guild
    )


    # =================================================
    # Existing Message
    # =================================================

    message_id = stats_data.get(
        "message_id"
    )

    channel_id = stats_data.get(
        "channel_id"
    )

    guild_id = stats_data.get(
        "guild_id"
    )


    if (
        message_id
        and channel_id
        and guild_id == guild.id
    ):

        channel = guild.get_channel(
            channel_id
        )

        if channel:

            try:

                message = await channel.fetch_message(
                    message_id
                )

                await message.edit(
                    content=text
                )

                return

            except discord.NotFound:

                stats_data["message_id"] = None

            except discord.HTTPException:

                return


    # =================================================
    # Stats Channel
    # =================================================

    channel = guild.get_channel(
        STATS_CHANNEL_ID
    )


    if channel is None:

        return


    # =================================================
    # Create New Message
    # =================================================

    try:

        message = await channel.send(
            text
        )

        stats_data = {
            "message_id": message.id,
            "channel_id": channel.id,
            "guild_id": guild.id
        }

        save_stats_data(
            stats_data
        )

    except (
        discord.Forbidden,
        discord.HTTPException
    ):

        pass


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

    if (
        message.content.strip().lower()
        == "!my stats bot"
    ):

        if message.author.id != OWNER_ID:
            return

        try:

            await message.delete()

        except (
            discord.Forbidden,
            discord.HTTPException
        ):

            pass


        if message.guild is None:
            return


        await update_stats_for_guild(
            message.guild
        )

        return


    # =================================================
    # Other prefix commands
    # =================================================

    await bot.process_commands(
        message
    )


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

STATS_CHANNEL_ID = 1539734753736134856


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

            if not data.get("channel_id"):

                data["channel_id"] = STATS_CHANNEL_ID

            return data

    except Exception:

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
        # Load message.py
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
        # Load ticket.py
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
        # Load chests.py
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
        # Load drops.py
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
# Bot Ready
# =================================================

@bot.event
async def on_ready():

    print(
        f"🤖 Logged in as {bot.user}"
    )

    # =================================================
    # Status
    # =================================================

    await bot.change_presence(
        status=discord.Status.idle,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Over server security 🎮『𝗟𝗘𝗚𝗘𝗡𝗗𝗦』🇷🇺🇬🇧"
        )
    )

    # =================================================
    # Start Stats
    # =================================================

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
# STATS
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


async def update_stats_for_guild(
    guild: discord.Guild
):

    global stats_data

    if not guild:
        return


    text = build_stats_text(
        guild
    )


    # =================================================
    # Existing Message
    # =================================================

    message_id = stats_data.get(
        "message_id"
    )

    channel_id = stats_data.get(
        "channel_id"
    )

    guild_id = stats_data.get(
        "guild_id"
    )


    if (
        message_id
        and channel_id
        and guild_id == guild.id
    ):

        channel = guild.get_channel(
            channel_id
        )

        if channel:

            try:

                message = await channel.fetch_message(
                    message_id
                )

                await message.edit(
                    content=text
                )

                return

            except discord.NotFound:

                stats_data["message_id"] = None

            except discord.HTTPException:

                return


    # =================================================
    # Stats Channel
    # =================================================

    channel = guild.get_channel(
        STATS_CHANNEL_ID
    )


    if channel is None:

        return


    # =================================================
    # Create New Message
    # =================================================

    try:

        message = await channel.send(
            text
        )

        stats_data = {
            "message_id": message.id,
            "channel_id": channel.id,
            "guild_id": guild.id
        }

        save_stats_data(
            stats_data
        )

    except (
        discord.Forbidden,
        discord.HTTPException
    ):

        pass


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

    if (
        message.content.strip().lower()
        == "!my stats bot"
    ):

        if message.author.id != OWNER_ID:
            return

        try:

            await message.delete()

        except (
            discord.Forbidden,
            discord.HTTPException
        ):

            pass


        if message.guild is None:
            return


        await update_stats_for_guild(
            message.guild
        )

        return


    # =================================================
    # Other prefix commands
    # =================================================

    await bot.process_commands(
        message
    )


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
# Start Bot
# =================================================

bot.run(TOKEN)
