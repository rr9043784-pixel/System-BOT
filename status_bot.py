import json
import logging
import os
from urllib.parse import urlparse

import discord
from discord import app_commands
from discord.ext import commands

OWNER_ID = 1176149190192152626
STATUS_DATA_FILE = "status_data.json"

DEFAULT_CONFIG = {
    "status": "idle",
    "activity_type": "watching",
    "activity_text": "👻 Monitors the order on the server 👻⠀ ➜➜ 🎮『𝗟𝗘𝗚𝗘𝗡𝗗𝗦』🇷🇺🇬🇧",
    "streaming_url": "",
}

# The same custom status emojis used in main.py.
STATUS_OPTIONS = [
    discord.SelectOption(
        label="Online",
        value="online",
        emoji=discord.PartialEmoji(name="Online_pc_status", id=1557533156322582649),
    ),
    discord.SelectOption(
        label="Idle",
        value="idle",
        emoji=discord.PartialEmoji(name="Idle_status", id=1557533355711660082),
    ),
    discord.SelectOption(
        label="Do Not Disturb",
        value="dnd",
        emoji=discord.PartialEmoji(
            name="Doesnotbother_Status",
            id=1557533152639983646,
        ),
    ),
    discord.SelectOption(
        label="Invisible",
        value="invisible",
        emoji=discord.PartialEmoji(name="Offline_status", id=1557533351546458163),
    ),
]

ACTIVITY_OPTIONS = [
    discord.SelectOption(label="Playing", value="playing", emoji="🎮"),
    discord.SelectOption(label="Watching", value="watching", emoji="👀"),
    discord.SelectOption(label="Listening", value="listening", emoji="🎧"),
    discord.SelectOption(label="Competing", value="competing", emoji="🏆"),
    discord.SelectOption(
        label="Streaming",
        value="streaming",
        emoji=discord.PartialEmoji(
            name="Streaming_Status",
            id=1557533349105631284,
        ),
    ),
    discord.SelectOption(label="No Activity", value="none", emoji="➖"),
]


def load_status_config():
    if not os.path.exists(STATUS_DATA_FILE):
        return DEFAULT_CONFIG.copy()

    try:
        with open(STATUS_DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return DEFAULT_CONFIG.copy()

        config = DEFAULT_CONFIG.copy()
        for key in ("status", "activity_type", "activity_text", "streaming_url"):
            if key in data:
                config[key] = data[key]

        if config["status"] not in {"online", "idle", "dnd", "invisible"}:
            config["status"] = DEFAULT_CONFIG["status"]

        if config["activity_type"] not in {
            "playing", "watching", "listening", "competing", "streaming", "none"
        }:
            config["activity_type"] = DEFAULT_CONFIG["activity_type"]

        if not isinstance(config["activity_text"], str):
            config["activity_text"] = DEFAULT_CONFIG["activity_text"]

        if not isinstance(config["streaming_url"], str):
            config["streaming_url"] = ""

        return config

    except (OSError, json.JSONDecodeError):
        logging.exception("Could not read status_data.json")
        return DEFAULT_CONFIG.copy()


def save_status_config(config):
    temp_file = STATUS_DATA_FILE + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=4)
    os.replace(temp_file, STATUS_DATA_FILE)


def validate_streaming_url(url: str) -> bool:
    """Discord streaming presence requires a Twitch or YouTube URL."""
    try:
        parsed = urlparse(url.strip())
        host = (parsed.hostname or "").lower()
        return (
            parsed.scheme == "https"
            and host in {
                "twitch.tv",
                "www.twitch.tv",
                "youtube.com",
                "www.youtube.com",
                "youtu.be",
                "m.youtube.com",
            }
            and bool(parsed.path.strip("/"))
        )
    except (TypeError, ValueError):
        return False


async def apply_saved_presence(bot):
    """Apply the saved presence. Called on startup and by main.py's stats loop."""
    config = load_status_config()

    status_map = {
        "online": discord.Status.online,
        "idle": discord.Status.idle,
        "dnd": discord.Status.dnd,
        "invisible": discord.Status.invisible,
    }

    activity_map = {
        "playing": discord.ActivityType.playing,
        "watching": discord.ActivityType.watching,
        "listening": discord.ActivityType.listening,
        "competing": discord.ActivityType.competing,
    }

    activity = None
    activity_type = config["activity_type"]
    activity_text = config["activity_text"].strip()

    if activity_type == "streaming" and activity_text:
        streaming_url = config["streaming_url"].strip()
        if validate_streaming_url(streaming_url):
            activity = discord.Streaming(
                name=activity_text[:128],
                url=streaming_url,
            )
        else:
            logging.warning(
                "Saved streaming activity has no valid Twitch/YouTube URL; "
                "applying presence without an activity."
            )
    elif activity_type != "none" and activity_text:
        activity = discord.Activity(
            type=activity_map[activity_type],
            name=activity_text[:128],
        )

    await bot.change_presence(
        status=status_map[config["status"]],
        activity=activity,
    )


class StatusTextModal(discord.ui.Modal, title="Edit Activity"):
    activity_text = discord.ui.TextInput(
        label="Activity text",
        placeholder="Enter the text shown under the bot's name",
        max_length=128,
        required=True,
    )
    streaming_url = discord.ui.TextInput(
        label="Streaming URL (Twitch or YouTube)",
        placeholder="https://www.twitch.tv/your_channel",
        max_length=200,
        required=False,
    )

    def __init__(self, view):
        super().__init__()
        self.parent_view = view
        self.activity_text.default = view.config["activity_text"][:128]
        self.streaming_url.default = view.config.get("streaming_url", "")[:200]

    async def on_submit(self, interaction: discord.Interaction):
        self.parent_view.config["activity_text"] = str(self.activity_text).strip()
        self.parent_view.config["streaming_url"] = str(self.streaming_url).strip()

        if self.parent_view.config["activity_type"] == "streaming":
            url = self.parent_view.config["streaming_url"]
            if not validate_streaming_url(url):
                await interaction.response.send_message(
                    "❌ Enter a valid HTTPS Twitch or YouTube channel/stream URL. "
                    "Then open **Edit Text** again and save it.",
                    ephemeral=True,
                )
                return

        await interaction.response.send_message(
            "✅ Activity text and streaming link updated in this panel. "
            "Press **Apply** to publish the changes.",
            ephemeral=True,
        )


class EditStatusView(discord.ui.View):
    def __init__(self, owner_id: int):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.config = load_status_config()

        self.status_select = discord.ui.Select(
            placeholder="Choose bot status",
            min_values=1,
            max_values=1,
            options=self._status_select_options(),
            row=0,
        )
        self.status_select.callback = self.status_callback
        self.add_item(self.status_select)

        self.activity_select = discord.ui.Select(
            placeholder="Choose activity type",
            min_values=1,
            max_values=1,
            options=self._activity_select_options(),
            row=1,
        )
        self.activity_select.callback = self.activity_callback
        self.add_item(self.activity_select)

        edit_text_button = discord.ui.Button(
            label="Edit Text / Stream URL",
            emoji="✏️",
            style=discord.ButtonStyle.secondary,
            row=2,
        )
        edit_text_button.callback = self.edit_text_callback
        self.add_item(edit_text_button)

        apply_button = discord.ui.Button(
            label="Apply",
            emoji="✅",
            style=discord.ButtonStyle.success,
            row=2,
        )
        apply_button.callback = self.apply_callback
        self.add_item(apply_button)

        reset_button = discord.ui.Button(
            label="Reset",
            emoji="🔄",
            style=discord.ButtonStyle.danger,
            row=2,
        )
        reset_button.callback = self.reset_callback
        self.add_item(reset_button)

    def _status_select_options(self):
        return [
            discord.SelectOption(
                label=option.label,
                value=option.value,
                emoji=option.emoji,
                default=(option.value == self.config["status"]),
            )
            for option in STATUS_OPTIONS
        ]

    def _activity_select_options(self):
        return [
            discord.SelectOption(
                label=option.label,
                value=option.value,
                emoji=option.emoji,
                default=(option.value == self.config["activity_type"]),
            )
            for option in ACTIVITY_OPTIONS
        ]

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ This control panel belongs to the bot owner.",
                ephemeral=True,
            )
            return False
        return True

    def refresh_select_defaults(self):
        self.status_select.options = self._status_select_options()
        self.activity_select.options = self._activity_select_options()

    async def status_callback(self, interaction: discord.Interaction):
        self.config["status"] = self.status_select.values[0]
        self.refresh_select_defaults()
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    async def activity_callback(self, interaction: discord.Interaction):
        self.config["activity_type"] = self.activity_select.values[0]
        self.refresh_select_defaults()
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    async def edit_text_callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(StatusTextModal(self))

    async def apply_callback(self, interaction: discord.Interaction):
        if self.config["activity_type"] == "streaming":
            streaming_url = self.config["streaming_url"].strip()
            if not validate_streaming_url(streaming_url):
                await interaction.response.send_message(
                    "❌ Streaming needs a valid HTTPS Twitch or YouTube URL. "
                    "Press **Edit Text / Stream URL** and add your link.",
                    ephemeral=True,
                )
                return

        try:
            save_status_config(self.config)
            await apply_saved_presence(interaction.client)
            await interaction.response.edit_message(
                content="✅ **Bot status updated successfully.**",
                embed=self.make_embed(),
                view=self,
            )
        except (discord.HTTPException, OSError):
            logging.exception("Failed to apply bot status")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Failed to update the bot status. Check the bot logs.",
                    ephemeral=True,
                )

    async def reset_callback(self, interaction: discord.Interaction):
        try:
            if os.path.exists(STATUS_DATA_FILE):
                os.remove(STATUS_DATA_FILE)

            self.config = DEFAULT_CONFIG.copy()
            self.refresh_select_defaults()

            await apply_saved_presence(interaction.client)
            await interaction.response.edit_message(
                content="🔄 **Default bot status restored.**",
                embed=self.make_embed(),
                view=self,
            )
        except (discord.HTTPException, OSError):
            logging.exception("Failed to reset bot status")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Failed to reset the bot status. Check the bot logs.",
                    ephemeral=True,
                )

    def make_embed(self):
        status_labels = {
            "online": "<:Online_pc_status:1557533156322582649> Online",
            "idle": "<:Idle_status:1557533355711660082> Idle",
            "dnd": "<:Doesnotbother_Status:1557533152639983646> Do Not Disturb",
            "invisible": "<:Offline_status:1557533351546458163> Invisible",
        }
        activity_labels = {
            "playing": "🎮 Playing",
            "watching": "👀 Watching",
            "listening": "🎧 Listening",
            "competing": "🏆 Competing",
            "streaming": "<:Streaming_Status:1557533349105631284> Streaming",
            "none": "➖ No Activity",
        }

        text = self.config["activity_text"] or "Not set"
        description = (
            "Choose the bot's presence settings below, then press **Apply**.\n\n"
            f"**Status:** {status_labels[self.config['status']]}\n"
            f"**Activity:** {activity_labels[self.config['activity_type']]}\n"
            f"**Text:** {discord.utils.escape_markdown(text[:100])}"
        )

        if self.config["activity_type"] == "streaming":
            url = self.config.get("streaming_url", "").strip()
            description += (
                f"\n**Stream URL:** {discord.utils.escape_markdown(url)}"
                if url else "\n**Stream URL:** Not set"
            )

        return discord.Embed(
            title="⚙️ Edit Bot Status",
            description=description,
            color=discord.Color.blurple(),
        )


class StatusBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="editstatus",
        description="Edit the bot's online status and activity",
    )
    async def editstatus(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                "❌ You do not have permission to use this command.",
                ephemeral=True,
            )
            return

        view = EditStatusView(OWNER_ID)
        await interaction.response.send_message(
            embed=view.make_embed(),
            view=view,
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(StatusBot(bot))
    if bot.is_ready():
        await apply_saved_presence(bot)
