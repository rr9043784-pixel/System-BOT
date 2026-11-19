import asyncio
import logging
import time
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

OWNER_ID = 1176149190192152626
CHANNELS_PER_PAGE = 25
CONNECT_TIMEOUT = 25

DURATIONS = {
    "5 minutes": 300,
    "15 minutes": 900,
    "30 minutes": 1800,
    "1 hour": 3600,
    "3 hours": 10800,
    "6 hours": 21600,
    "12 hours": 43200,
    "24 hours": 86400,
    "Infinite": None,
}


class BotVoiceView(discord.ui.LayoutView):
    """Components V2 control panel for the bot's voice connection."""

    def __init__(
        self,
        cog: "BotVoice",
        owner_id: int,
        guild: discord.Guild,
        *,
        page: int = 0,
        selected_channel_id: Optional[int] = None,
        duration_key: Optional[str] = None,
        notice: Optional[str] = None,
    ):
        super().__init__(timeout=600)
        self.cog = cog
        self.owner_id = owner_id
        self.guild = guild
        self.page = max(0, page)
        self.selected_channel_id = selected_channel_id
        self.duration_key = duration_key
        self.notice = notice
        self.message = None
        self._build_layout()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ This control panel belongs to the bot owner.",
                ephemeral=True,
            )
            return False
        return True

    def _bot_member(self):
        return self.guild.me or self.guild.get_member(self.cog.bot.user.id)

    def _available_channels(self):
        member = self._bot_member()
        if member is None:
            return []

        channels = []
        for channel in self.guild.channels:
            if channel.type not in (
                discord.ChannelType.voice,
                discord.ChannelType.stage_voice,
            ):
                continue

            permissions = channel.permissions_for(member)
            if permissions.view_channel and permissions.connect:
                channels.append(channel)

        return sorted(
            channels,
            key=lambda channel: (
                channel.category.position if channel.category else -1,
                channel.position,
                channel.name.casefold(),
            ),
        )

    def _connected_voice_client(self):
        voice_client = self.guild.voice_client
        if voice_client and voice_client.is_connected():
            return voice_client
        return None

    def _status_text(self) -> str:
        voice_client = self._connected_voice_client()
        if voice_client:
            expiry = self.cog.expirations.get(self.guild.id, "missing")
            if expiry is None:
                duration = "Infinite"
            elif expiry == "missing":
                duration = "Timer not available"
            else:
                duration = f"<t:{int(expiry)}:R>"

            return (
                "🟢 **Status:** Connected\n"
                f"🔊 **Channel:** {voice_client.channel.mention}\n"
                f"⏱️ **Disconnect:** {duration}"
            )

        channel = (
            self.guild.get_channel(self.selected_channel_id)
            if self.selected_channel_id
            else None
        )
        channel_text = channel.mention if channel else "Not selected"
        duration_text = self.duration_key or "Not selected"

        return (
            "⚪ **Status:** Disconnected\n"
            f"🔊 **Channel:** {channel_text}\n"
            f"⏱️ **Duration:** {duration_text}"
        )

    def _build_layout(self):
        self.clear_items()

        connected = self._connected_voice_client() is not None
        channels = self._available_channels()
        total_pages = max(1, (len(channels) + CHANNELS_PER_PAGE - 1) // CHANNELS_PER_PAGE)
        self.page = min(self.page, total_pages - 1)

        start = self.page * CHANNELS_PER_PAGE
        page_channels = channels[start:start + CHANNELS_PER_PAGE]

        text = (
            "# 🔊 Bot Voice Control\n"
            "Manage the bot's voice connection.\n\n"
            f"{self._status_text()}\n\n"
            f"📄 **Channel page:** {self.page + 1}/{total_pages}"
        )
        if self.notice:
            text += f"\n\n{self.notice}"

        container_items = [
            discord.ui.TextDisplay(text),
            discord.ui.Separator(),
        ]

        # If already connected, this new panel exposes only the Leave button.
        if connected:
            leave_button = discord.ui.Button(
                label="Leave Voice",
                emoji="🔇",
                style=discord.ButtonStyle.danger,
            )
            leave_button.callback = self.leave_voice
            container_items.append(discord.ui.ActionRow(leave_button))
            self.add_item(
                discord.ui.Container(
                    *container_items,
                    accent_colour=discord.Colour.blurple(),
                )
            )
            return

        if page_channels:
            options = []
            for channel in page_channels:
                category = channel.category.name if channel.category else "No category"
                options.append(
                    discord.SelectOption(
                        label=channel.name[:100],
                        value=str(channel.id),
                        description=f"{category} • {channel.type.name.replace('_', ' ').title()}"[:100],
                        default=(channel.id == self.selected_channel_id),
                    )
                )

            channel_select = discord.ui.Select(
                placeholder="Choose a voice channel",
                min_values=1,
                max_values=1,
                options=options,
                disabled=self.selected_channel_id is not None,
            )
            channel_select.callback = self.channel_selected
            container_items.append(discord.ui.ActionRow(channel_select))
        else:
            container_items.append(
                discord.ui.TextDisplay(
                    "⚠️ No voice channels are visible to the bot. "
                    "Give the bot **View Channel** and **Connect** permissions."
                )
            )

        previous_button = discord.ui.Button(
            label="Previous Page",
            emoji="⬅️",
            style=discord.ButtonStyle.secondary,
            disabled=(self.page <= 0 or self.selected_channel_id is not None),
        )
        previous_button.callback = self.previous_page

        next_button = discord.ui.Button(
            label="Next Page",
            emoji="➡️",
            style=discord.ButtonStyle.secondary,
            disabled=(
                self.page >= total_pages - 1
                or self.selected_channel_id is not None
            ),
        )
        next_button.callback = self.next_page

        container_items.append(
            discord.ui.ActionRow(previous_button, next_button)
        )

        if self.selected_channel_id is not None:
            change_button = discord.ui.Button(
                label="Change Channel",
                emoji="🔄",
                style=discord.ButtonStyle.primary,
            )
            change_button.callback = self.change_channel
            container_items.append(discord.ui.ActionRow(change_button))

            duration_select = discord.ui.Select(
                placeholder="Select connection duration",
                min_values=1,
                max_values=1,
                options=[
                    discord.SelectOption(
                        label=name,
                        value=name,
                        default=(name == self.duration_key),
                    )
                    for name in DURATIONS
                ],
            )
            duration_select.callback = self.duration_selected
            container_items.append(discord.ui.ActionRow(duration_select))

        join_button = discord.ui.Button(
            label="Join Voice",
            emoji="🔊",
            style=discord.ButtonStyle.success,
            disabled=(
                self.selected_channel_id is None
                or self.duration_key is None
            ),
        )
        join_button.callback = self.join_voice
        container_items.append(discord.ui.ActionRow(join_button))

        self.add_item(
            discord.ui.Container(
                *container_items,
                accent_colour=discord.Colour.blurple(),
            )
        )

    async def _refresh(self, interaction: discord.Interaction):
        new_view = BotVoiceView(
            self.cog,
            self.owner_id,
            self.guild,
            page=self.page,
            selected_channel_id=self.selected_channel_id,
            duration_key=self.duration_key,
            notice=self.notice,
        )
        await interaction.response.edit_message(view=new_view)

    async def channel_selected(self, interaction: discord.Interaction):
        channel_id = int(interaction.data["values"][0])
        channel = self.guild.get_channel(channel_id)

        if channel is None:
            try:
                channel = await self.guild.fetch_channel(channel_id)
            except discord.Forbidden:
                await interaction.response.send_message(
                    "❌ The bot cannot access that private channel. "
                    "Give it **View Channel** and **Connect** permissions.",
                    ephemeral=True,
                )
                return
            except discord.HTTPException:
                await interaction.response.send_message(
                    "❌ Could not load that channel. Please try again.",
                    ephemeral=True,
                )
                return

        if channel.type not in (
            discord.ChannelType.voice,
            discord.ChannelType.stage_voice,
        ):
            await interaction.response.send_message(
                "❌ Please choose a voice or stage channel.",
                ephemeral=True,
            )
            return

        member = self._bot_member()
        permissions = channel.permissions_for(member) if member else None
        if not permissions or not permissions.view_channel or not permissions.connect:
            await interaction.response.send_message(
                "❌ The bot needs **View Channel** and **Connect** permissions "
                "in this channel.",
                ephemeral=True,
            )
            return

        self.selected_channel_id = channel.id
        self.duration_key = None
        self.notice = None
        await self._refresh(interaction)

    async def previous_page(self, interaction: discord.Interaction):
        self.page = max(0, self.page - 1)
        self.notice = None
        await self._refresh(interaction)

    async def next_page(self, interaction: discord.Interaction):
        channels = self._available_channels()
        total_pages = max(1, (len(channels) + CHANNELS_PER_PAGE - 1) // CHANNELS_PER_PAGE)
        self.page = min(total_pages - 1, self.page + 1)
        self.notice = None
        await self._refresh(interaction)

    async def change_channel(self, interaction: discord.Interaction):
        self.selected_channel_id = None
        self.duration_key = None
        self.notice = "Choose another voice channel from the list."
        await self._refresh(interaction)

    async def duration_selected(self, interaction: discord.Interaction):
        self.duration_key = interaction.data["values"][0]
        self.notice = None
        await self._refresh(interaction)

    async def join_voice(self, interaction: discord.Interaction):
        if self.selected_channel_id is None or self.duration_key is None:
            await interaction.response.send_message(
                "❌ Select a channel and duration first.",
                ephemeral=True,
            )
            return

        if self._connected_voice_client():
            await interaction.response.send_message(
                "❌ The bot is already connected to a voice channel.",
                ephemeral=True,
            )
            return

        channel = self.guild.get_channel(self.selected_channel_id)
        if channel is None:
            await interaction.response.send_message(
                "❌ The selected channel no longer exists. Select it again.",
                ephemeral=True,
            )
            return

        member = self._bot_member()
        permissions = channel.permissions_for(member) if member else None
        if not permissions or not permissions.view_channel or not permissions.connect:
            await interaction.response.send_message(
                "❌ The bot needs **View Channel** and **Connect** permissions "
                "in the selected channel.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        try:
            await asyncio.wait_for(
                channel.connect(timeout=20.0, reconnect=False),
                timeout=CONNECT_TIMEOUT,
            )

            seconds = DURATIONS[self.duration_key]
            expiry = time.time() + seconds if seconds is not None else None
            self.cog.set_expiration(self.guild.id, expiry)

            updated = BotVoiceView(
                self.cog,
                self.owner_id,
                self.guild,
                page=self.page,
                selected_channel_id=channel.id,
                duration_key=self.duration_key,
            )
            await interaction.edit_original_response(view=updated)

        except asyncio.TimeoutError:
            logging.exception("Timed out while connecting to voice channel")
            await interaction.followup.send(
                "❌ Discord voice connection timed out. Check the bot's "
                "permissions and try again.",
                ephemeral=True,
            )
        except discord.Forbidden:
            logging.exception("Discord denied the voice connection")
            await interaction.followup.send(
                "❌ Discord denied the connection. Check **View Channel** "
                "and **Connect** permissions for the bot.",
                ephemeral=True,
            )
        except discord.ClientException as error:
            logging.exception("Discord voice client error")
            await interaction.followup.send(
                f"❌ Voice client error: `{str(error)[:300]}`",
                ephemeral=True,
            )
        except RuntimeError as error:
            logging.exception("Runtime error while connecting to voice")
            if "nacl" in str(error).lower() or "voice" in str(error).lower():
                message = (
                    "❌ Voice support is unavailable. Make sure `PyNaCl>=1.5.0` "
                    "is in requirements.txt and Railway completed a fresh deploy."
                )
            else:
                message = f"❌ Connection error: `{str(error)[:300]}`"
            await interaction.followup.send(message, ephemeral=True)
        except Exception as error:
            logging.exception("Unexpected error while joining voice")
            await interaction.followup.send(
                f"❌ Unexpected connection error: `{type(error).__name__}: "
                f"{str(error)[:250]}`. Check Railway logs for details.",
                ephemeral=True,
            )

    async def leave_voice(self, interaction: discord.Interaction):
        voice_client = self._connected_voice_client()
        if voice_client is None:
            self.cog.cancel_expiration(self.guild.id)
            self.notice = "The bot is already disconnected."
            await self._refresh(interaction)
            return

        await interaction.response.defer()
        try:
            await voice_client.disconnect(force=True)
            self.cog.cancel_expiration(self.guild.id)

            updated = BotVoiceView(
                self.cog,
                self.owner_id,
                self.guild,
                page=self.page,
            )
            await interaction.edit_original_response(view=updated)
        except Exception as error:
            logging.exception("Failed to leave voice channel")
            await interaction.followup.send(
                f"❌ Could not leave the voice channel: `{type(error).__name__}`.",
                ephemeral=True,
            )

    async def on_timeout(self):
        self.stop()


class BotVoice(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.expirations: dict[int, Optional[float]] = {}
        self.expiry_tasks: dict[int, asyncio.Task] = {}

    def set_expiration(self, guild_id: int, expiry: Optional[float]):
        self.cancel_expiration(guild_id)
        self.expirations[guild_id] = expiry
        if expiry is not None:
            self.expiry_tasks[guild_id] = asyncio.create_task(
                self.disconnect_after(guild_id, expiry)
            )

    def cancel_expiration(self, guild_id: int):
        task = self.expiry_tasks.pop(guild_id, None)
        if task and not task.done():
            task.cancel()
        self.expirations.pop(guild_id, None)

    async def disconnect_after(self, guild_id: int, expiry: float):
        try:
            await asyncio.sleep(max(0, expiry - time.time()))
            guild = self.bot.get_guild(guild_id)
            if guild and guild.voice_client and guild.voice_client.is_connected():
                await guild.voice_client.disconnect(force=True)
                logging.info("Bot voice duration expired in guild %s", guild_id)
        except asyncio.CancelledError:
            pass
        except Exception:
            logging.exception("Automatic voice disconnect failed")
        finally:
            self.expiry_tasks.pop(guild_id, None)
            self.expirations.pop(guild_id, None)

    @app_commands.command(
        name="botvoice",
        description="Open the bot voice control panel",
    )
    async def botvoice(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                "❌ You do not have permission to use this command.",
                ephemeral=True,
            )
            return

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True,
            )
            return

        view = BotVoiceView(self, interaction.user.id, interaction.guild)
        await interaction.response.send_message(
            view=view,
            ephemeral=True,
        )
        try:
            view.message = await interaction.original_response()
        except discord.HTTPException:
            pass

    def cog_unload(self):
        for task in self.expiry_tasks.values():
            task.cancel()


async def setup(bot: commands.Bot):
    await bot.add_cog(BotVoice(bot))
