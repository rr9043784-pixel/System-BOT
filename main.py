import os
import asyncio
import json
import discord
from discord import app_commands
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread


# =========================
# Tokens
# =========================

TOKEN = os.environ["DISCORD_TOKEN"]


# =========================
# Settings
# =========================

OWNER_ID = 1176149190192152626

STATS_DATA_FILE = "stats_data.json"
STATS_CHANNEL_ID = 1542994435472760953


# =========================
# Flask
# =========================

app = Flask(__name__)


@app.route("/")
def home():
    return "Tournament Bot is online!"


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


Thread(target=run_flask, daemon=True).start()


# =========================
# Persistent stats data
# =========================

def load_stats_data():
    if not os.path.exists(STATS_DATA_FILE):
        return {
            "message_id": None,
            "channel_id": STATS_CHANNEL_ID,
            "guild_id": None
        }

    try:
        with open(STATS_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError

        data.setdefault("message_id", None)
        data.setdefault("channel_id", STATS_CHANNEL_ID)
        data.setdefault("guild_id", None)

        return data

    except (json.JSONDecodeError, OSError, ValueError):
        return {
            "message_id": None,
            "channel_id": STATS_CHANNEL_ID,
            "guild_id": None
        }


def save_stats_data(data):
    temp_file = STATS_DATA_FILE + ".tmp"

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    os.replace(temp_file, STATS_DATA_FILE)


stats_data = load_stats_data()


# =========================
# Intents
# =========================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True


# =========================
# Bot
# =========================

class TournamentBot(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):

        extensions = [
            "cogs.message",
            "cogs.ticket",
            "cogs.chests",
            "cogs.drops",
            "cogs.verification"
        ]

        for extension in extensions:
            try:
                await self.load_extension(extension)
                print(f"Loaded: {extension}")
            except Exception as e:
                print(f"Failed to load {extension}: {e}")

        await self.tree.sync()
        print("Slash commands synced.")


bot = TournamentBot()


# =========================
# Presence
# =========================

async def set_bot_presence():

    await bot.change_presence(
        status=discord.Status.idle,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Over server security 🎮『𝗟𝗘𝗚𝗘𝗡𝗗𝗦』🇷🇺🇬🇧"
        )
    )


# =========================
# Status stats
# =========================

def get_member_status_counts(guild):

    online = 0
    idle = 0
    dnd = 0
    offline = 0
    streaming = 0

    for member in guild.members:

        if member.bot:
            continue

        status = member.status

        if status == discord.Status.online:
            online += 1

        elif status == discord.Status.idle:
            idle += 1

        elif status == discord.Status.dnd:
            dnd += 1

        else:
            offline += 1

        for activity in member.activities:
            if isinstance(activity, discord.Streaming):
                streaming += 1
                break

    return online, idle, dnd, streaming, offline


def create_stats_embed(guild):

    online, idle, dnd, streaming, offline = get_member_status_counts(guild)

    embed = discord.Embed(
        description=(
            "⬇️ **Status**\n"
            f"<:Online_pc_status:1557533156322582649> Online: **{online:,}**\n"
            f"<:Idle_status:1557533355711660082> Idle: **{idle:,}**\n"
            f"<:Doesnotbother_Status:1557533152639983646> Do Not Disturb: **{dnd:,}**\n"
            f"<:Streaming_Status:1557533349105631284> Streaming: **{streaming:,}**\n"
            f"<:Offline_status:1557533351546458163> Offline: **{offline:,}**"
        )
    )

    return embed


# =========================
# Update stats message
# =========================

@tasks.loop(minutes=1)
async def update_stats_message():

    channel = bot.get_channel(STATS_CHANNEL_ID)

    if channel is None:
        return

    guild = channel.guild

    embed = create_stats_embed(guild)

    message_id = stats_data.get("message_id")

    try:

        if message_id:

            try:
                message = await channel.fetch_message(message_id)
                await message.edit(embed=embed)
                return

            except discord.NotFound:
                pass

        message = await channel.send(embed=embed)

        stats_data["message_id"] = message.id
        stats_data["channel_id"] = channel.id
        stats_data["guild_id"] = guild.id

        save_stats_data(stats_data)

    except discord.HTTPException as e:
        print(f"Stats update error: {e}")


@update_stats_message.before_loop
async def before_stats_update():

    await bot.wait_until_ready()


# =========================
# Ready
# =========================

@bot.event
async def on_ready():

    print(f"Logged in as {bot.user} ({bot.user.id})")

    await set_bot_presence()

    if not update_stats_message.is_running():
        update_stats_message.start()


# =========================
# Owner check
# =========================

def owner_only():

    async def predicate(interaction: discord.Interaction):

        if interaction.user.id != OWNER_ID:
            raise app_commands.CheckFailure(
                "You do not have permission."
            )

        return True

    return app_commands.check(predicate)


# =========================
# /send
# =========================

send_group = app_commands.Group(
    name="send",
    description="Send messages"
)


@send_group.command(
    name="message",
    description="Send a message to a channel"
)
@owner_only()
async def send_message(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    text: str
):

    try:

        await channel.send(f"**BOT:** {text}")

        await interaction.response.send_message(
            "✅ Message sent.",
            ephemeral=True
        )

    except discord.HTTPException:

        await interaction.response.send_message(
            "❌ Failed to send the message.",
            ephemeral=True
        )


@send_group.command(
    name="dms",
    description="Send a DM to a user"
)
@owner_only()
async def send_dms(
    interaction: discord.Interaction,
    user: discord.User,
    message: str
):

    try:

        await user.send(
            f"**BOT:** {message}\n"
            f"-# Server: {interaction.guild.name if interaction.guild else 'Unknown'}"
        )

        await interaction.response.send_message(
            "✅ DM sent.",
            ephemeral=True
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I can't send DMs to this user.",
            ephemeral=True
        )

    except discord.HTTPException:

        await interaction.response.send_message(
            "❌ Failed to send the DM.",
            ephemeral=True
        )


bot.tree.add_command(send_group)


# =========================
# /open dms bot
# =========================

open_group = app_commands.Group(
    name="open",
    description="Open and check settings"
)

dms_group = app_commands.Group(
    name="dms",
    description="Direct messages"
)


class OpenDMsView(discord.ui.View):

    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id

    @discord.ui.button(
        label="Through Settings",
        style=discord.ButtonStyle.link,
        url="https://discord.com/settings/privacy"
    )
    async def settings_button(self, interaction, button):
        pass

    @discord.ui.button(
        label="Through Bot Profile",
        style=discord.ButtonStyle.link,
        url="https://discord.com/users/@me"
    )
    async def profile_button(self, interaction, button):
        pass

    @discord.ui.button(
        label="Check DMs",
        emoji="🔄",
        style=discord.ButtonStyle.primary
    )
    async def check_button(self, interaction, button):

        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ This button is not for you.",
                ephemeral=True
            )
            return

        try:

            test_message = await interaction.user.send(" ")
            await test_message.delete()

            button.disabled = True

            await interaction.response.edit_message(
                content="",
                view=self
            )

            await interaction.followup.send(
                "✅ Your DMs are open!",
                ephemeral=True
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ Your DMs are still closed. Please use one of the methods above and try again.",
                ephemeral=True
            )

        except discord.HTTPException:

            await interaction.response.send_message(
                "❌ I couldn't check your DMs right now. Try again later.",
                ephemeral=True
            )


@dms_group.command(
    name="bot",
    description="Check and open your DMs with the bot"
)
async def open_dms_bot(interaction: discord.Interaction):

    try:

        test_message = await interaction.user.send(" ")
        await test_message.delete()

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

    embed = discord.Embed(
        title="📩 Open your DMs",
        description=(
            "Your DMs with the bot are currently closed.\n\n"
            "**Method 1 — Through Settings**\n"
            "Open your Discord privacy settings and allow direct messages.\n\n"
            "**Method 2 — Through Bot Profile**\n"
            "Open the bot profile and use **Add App** if available.\n\n"
            "After that, press **🔄 Check DMs**."
        )
    )

    await interaction.response.send_message(
        embed=embed,
        view=OpenDMsView(interaction.user.id),
        ephemeral=True
    )


open_group.add_command(dms_group)
bot.tree.add_command(open_group)


# =========================
# /clear message
# =========================

clear_group = app_commands.Group(
    name="clear",
    description="Clear messages"
)


@clear_group.command(
    name="message",
    description="Delete messages from a channel"
)
@owner_only()
async def clear_message(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    number_of_messages: app_commands.Range[int, 1, 100]
):

    await interaction.response.defer(ephemeral=True)

    try:

        deleted = await channel.purge(
            limit=number_of_messages
        )

        if number_of_messages == 1:

            await interaction.followup.send(
                str(len(deleted)),
                ephemeral=True
            )

        # More than 1:
        # intentionally no response.

    except discord.Forbidden:

        await interaction.followup.send(
            "❌ I don't have permission to delete messages.",
            ephemeral=True
        )

    except discord.HTTPException:

        await interaction.followup.send(
            "❌ Failed to delete messages.",
            ephemeral=True
        )


bot.tree.add_command(clear_group)


# =========================
# App command errors
# =========================

@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error
):

    if isinstance(error, app_commands.CheckFailure):

        if interaction.response.is_done():
            await interaction.followup.send(
                "❌ You do not have permission to use this command.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ You do not have permission to use this command.",
                ephemeral=True
            )

        return

    print(f"Slash command error: {error}")


# =========================
# Run
# =========================

bot.run(TOKEN)
