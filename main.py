import os
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
# Status Emojis
# =================================================

ONLINE_PC_STATUS = "<:Online_pc_status:1557533156322582649>"
IDLE_STATUS = "<:Idle_status:1557533355711660082>"
DND_STATUS = "<:Doesnotbother_Status:1557533152639983646>"
STREAMING_STATUS = "<:Streaming_Status:1557533349105631284>"
OFFLINE_STATUS = "<:Offline_status:1557533351546458163>"


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
intents.presences = True


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
        # verification.py
        # =================================================

        try:

            await self.load_extension(
                "verification"
            )

            print(
                "✅ verification.py loaded!"
            )

        except Exception as e:

            print(
                f"❌ Failed to load verification.py: {e}"
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
            "🟡 Presence set: Idle | Watching Over server security"
        )

    except Exception as e:

        print(
            f"❌ Failed to set presence: {e}"
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

    print(
        "✅ Bot is ready!"
    )


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

def build_stats_text(
    guild: discord.Guild
):

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


    # =================================================
    # Status
    # =================================================

    online = sum(
        1
        for member in members
        if (
            not member.bot
            and member.status == discord.Status.online
        )
    )

    idle = sum(
        1
        for member in members
        if (
            not member.bot
            and member.status == discord.Status.idle
        )
    )

    dnd = sum(
        1
        for member in members
        if (
            not member.bot
            and member.status == discord.Status.dnd
        )
    )

    offline = sum(
        1
        for member in members
        if (
            not member.bot
            and member.status == discord.Status.offline
        )
    )


    # =================================================
    # Streaming
    # =================================================

    streaming = sum(
        1
        for member in members
        if (
            not member.bot
            and any(
                isinstance(
                    activity,
                    discord.Streaming
                )
                for activity in member.activities
            )
        )
    )


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

    boost_level = getattr(
        guild,
        "premium_tier",
        0
    )

    try:

        boost_level_number = int(
            getattr(
                boost_level,
                "value",
                boost_level
            )
        )

    except (
        TypeError,
        ValueError
    ):

        boost_level_number = 0


    boost_levels = {
        0: "No Level",
        1: "Level 1",
        2: "Level 2",
        3: "Level 3"
    }

    boost_level_text = boost_levels.get(
        boost_level_number,
        f"Level {boost_level_number}"
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


    # =================================================
    # Final Stats
    # =================================================

    return (
        "📊 **BOT Statistics**\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "\n"
        f"👥 **Members:** {total_members:,}\n"
        f"👤 Humans: {humans:,}\n"
        f"🤖 Bots: {bots_count:,}\n"
        "\n"
        "⬇️ **Status**\n"
        f"{ONLINE_PC_STATUS} Online: {online:,}\n"
        f"{IDLE_STATUS} Idle: {idle:,}\n"
        f"{DND_STATUS} Do Not Disturb: {dnd:,}\n"
        f"{STREAMING_STATUS} Streaming: {streaming:,}\n"
        f"{OFFLINE_STATUS} Offline: {offline:,}\n"
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

        channel = bot.get_channel(
            STATS_CHANNEL_ID
        )

        if channel is not None:

            if isinstance(
                channel,
                discord.TextChannel
            ):

                return channel


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


    channel = await get_stats_channel()

    if channel is None:

        print(
            "❌ Statistics message cannot be created because the channel was not found."
        )

        return


    message_id = stats_data.get(
        "message_id"
    )

    stored_guild_id = stats_data.get(
        "guild_id"
    )

    stored_channel_id = stats_data.get(
        "channel_id"
    )


    # =================================================
    # Channel changed
    # =================================================

    if stored_channel_id != STATS_CHANNEL_ID:

        message_id = None

        stats_data["message_id"] = None
        stats_data["channel_id"] = STATS_CHANNEL_ID


    # =================================================
    # Edit Existing Message
    # =================================================

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


    if message.content.strip().lower() == "!my stats bot":

        if message.author.id != OWNER_ID:
            return

        if message.guild is None:
            return


        try:

            await message.delete()

        except (
            discord.Forbidden,
            discord.HTTPException
        ):

            pass


        stats_data["guild_id"] = message.guild.id
        stats_data["channel_id"] = STATS_CHANNEL_ID
        stats_data["message_id"] = None

        save_stats_data(
            stats_data
        )


        print(
            f"📊 Creating stats in channel {STATS_CHANNEL_ID}..."
        )


        await update_stats_for_guild(
            message.guild
        )

        return


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

    await set_bot_presence()


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
# OPEN DMS
# =================================================

class OpenDMsView(discord.ui.View):

    def __init__(
        self,
        user_id: int
    ):

        super().__init__(
            timeout=300
        )

        self.user_id = user_id
        self.check_button = None


        # =================================================
        # Settings
        # =================================================

        settings_button = discord.ui.Button(
            label="Through Settings",
            emoji="⚙️",
            style=discord.ButtonStyle.link,
            url="https://discord.com/settings/privacy"
        )

        self.add_item(
            settings_button
        )


        # =================================================
        # Bot Profile
        # =================================================

        profile_button = discord.ui.Button(
            label="Through Bot Profile",
            emoji="🤖",
            style=discord.ButtonStyle.secondary
        )

        profile_button.callback = self.profile_callback

        self.add_item(
            profile_button
        )


        # =================================================
        # Check DMs
        # =================================================

        self.check_button = discord.ui.Button(
            label="Check DMs",
            emoji="🔍",
            style=discord.ButtonStyle.success
        )

        self.check_button.callback = self.check_dms_callback

        self.add_item(
            self.check_button
        )


    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):

        if interaction.user.id != self.user_id:

            await interaction.response.send_message(
                "❌ This panel belongs to another user.",
                ephemeral=True
            )

            return False

        return True


    async def profile_callback(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.send_message(
            "🤖 Open my profile and use **Add App** to add the bot to your apps.",
            ephemeral=True
        )


    async def check_dms_callback(
        self,
        interaction: discord.Interaction
    ):

        if self.check_button.disabled:

            await interaction.response.send_message(
                "✅ Your DMs are already open!",
                ephemeral=True
            )

            return


        try:

            test_message = await interaction.user.send(
                "✅ DM check successful."
            )

            try:

                await test_message.delete()

            except (
                discord.Forbidden,
                discord.HTTPException
            ):

                pass


            self.check_button.disabled = True

            await interaction.response.edit_message(
                view=self
            )

            await interaction.followup.send(
                "✅ Your DMs are now open!",
                ephemeral=True
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ Your DMs are still closed.",
                ephemeral=True
            )

        except discord.HTTPException:

            await interaction.response.send_message(
                "❌ I couldn't check your DMs right now.",
                ephemeral=True
            )


# =================================================
# /open
# =================================================

open_group = app_commands.Group(
    name="open",
    description="Open and check settings"
)


@open_group.command(
    name="dms",
    description="Check and open your DMs with the bot"
)
async def open_dms(
    interaction: discord.Interaction
):

    try:

        # =================================================
        # Check DMs first
        # =================================================

        test_message = await interaction.user.send(
            "✅ DM check successful."
        )

        try:

            await test_message.delete()

        except (
            discord.Forbidden,
            discord.HTTPException
        ):

            pass


        await interaction.response.send_message(
            "✅ Your DMs are already open!",
            ephemeral=True
        )

        return


    except discord.Forbidden:

        pass


    except discord.HTTPException:

        await interaction.response.send_message(
            "❌ I couldn't check your DMs right now.",
            ephemeral=True
        )

        return


    # =================================================
    # DMs are closed
    # =================================================

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
        color=discord.Color.blurple()
    )


    view = OpenDMsView(
        interaction.user.id
    )


    await interaction.response.send_message(
        embed=embed,
        view=view,
        ephemeral=True
    )


bot.tree.add_command(
    open_group
)


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
