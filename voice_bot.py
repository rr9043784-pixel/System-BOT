import asyncio
import importlib.util
import logging
import time
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

OWNER_ID = 1176149190192152626

# 23 channel choices + up to 2 navigation choices = Discord's 25-option limit.
CHANNELS_PER_PAGE = 23
CONNECT_TIMEOUT = 30

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

log = logging.getLogger(__name__)


def voice_dependency_status() -> tuple[bool, str]:
    """Return whether PyNaCl is importable, with a useful diagnostic."""
    try:
        import nacl  # noqa: F401
        return True, "PyNaCl is available."
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


class BotVoiceView(discord.ui.LayoutView):
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
        if self.cog.bot.user is None:
            return None
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

            perms = channel.permissions_for(member)
            if perms.view_channel and perms.connect:
                channels.append(channel)

        return sorted(
            channels,
            key=lambda channel: (
                channel.category.position if channel.category else -1,
                channel.position,
                channel.name.casefold(),
            ),
        )

    def _voice_client(self):
        vc = self.guild.voice_client
        return vc if vc and vc.is_connected() else None

    def _status_text(self) -> str:
        vc = self._voice_client()
        if vc:
            expiry = self.cog.expirations.get(self.guild.id, "missing")
            if expiry is None:
                timer_text = "Infinite"
            elif expiry == "missing":
                timer_text = "Timer unavailable"
            else:
                timer_text = f"<t:{int(expiry)}:R>"
            return (
                "🟢 **Status:** Connected\n"
                f"🔊 **Channel:** {vc.channel.mention}\n"
                f"⏱️ **Disconnect:** {timer_text}"
            )

        channel = (
            self.guild.get_channel(self.selected_channel_id)
            if self.selected_channel_id
            else None
        )
        return (
            "⚪ **Status:** Disconnected\n"
            f"🔊 **Channel:** {channel.mention if channel else 'Not selected'}\n"
            f"⏱️ **Duration:** {self.duration_key or 'Not selected'}"
        )

    def _build_layout(self):
        self.clear_items()
        vc = self._voice_client()
        connected = vc is not None

        body = [
            discord.ui.TextDisplay("# 🔊 Bot Voice Control"),
            discord.ui.TextDisplay(
                "Manage the bot's voice connection.\n\n"
                f"{self._status_text()}"
            ),
            discord.ui.Separator(),
        ]

        if self.notice:
            body.append(discord.ui.TextDisplay(self.notice))
            body.append(discord.ui.Separator())

        if connected:
            leave = discord.ui.Button(
                label="Leave Voice",
                emoji="🔇",
                style=discord.ButtonStyle.danger,
            )
            leave.callback = self.leave_voice
            body.append(discord.ui.ActionRow(leave))
            self.add_item(
                discord.ui.Container(*body, accent_colour=discord.Colour.blurple())
            )
            return

        channels = self._available_channels()
        page_count = max(1, (len(channels) + CHANNELS_PER_PAGE - 1) // CHANNELS_PER_PAGE)
        self.page = min(self.page, page_count - 1)

        # The navigation entries are actual options in the channel dropdown.
        start = self.page * CHANNELS_PER_PAGE
        page_channels = channels[start:start + CHANNELS_PER_PAGE]
        options = []

        if self.page > 0:
            options.append(
                discord.SelectOption(
                    label="⬅️ Previous Page",
                    value="__previous_page__",
                    description=f"Go to page {self.page}",
                )
            )

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

        if self.page < page_count - 1:
            options.append(
                discord.SelectOption(
                    label="➡️ Next Page",
                    value="__next_page__",
                    description=f"Go to page {self.page + 2}",
                )
            )

        if options:
            channel_menu = discord.ui.Select(
                placeholder=f"Choose a voice channel • Page {self.page + 1}/{page_count}",
                min_values=1,
                max_values=1,
                options=options,
                disabled=self.selected_channel_id is not None,
            )
            channel_menu.callback = self.channel_selected
            body.append(discord.ui.ActionRow(channel_menu))
        else:
            body.append(
                discord.ui.TextDisplay(
                    "⚠️ No voice channels are visible to the bot. "
                    "Grant **View Channel** and **Connect** permissions."
                )
            )

        # Keep the duration menu visible at all times; unlock it after channel selection.
        duration_menu = discord.ui.Select(
            placeholder=(
                f"Duration: {self.duration_key}"
                if self.duration_key
                else "Select connection duration"
            ),
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
            disabled=self.selected_channel_id is None,
        )
        duration_menu.callback = self.duration_selected
        body.append(discord.ui.ActionRow(duration_menu))

        if self.selected_channel_id is not None:
            change = discord.ui.Button(
                label="Change Channel",
                emoji="🔄",
                style=discord.ButtonStyle.secondary,
            )
            change.callback = self.change_channel
            body.append(discord.ui.ActionRow(change))

        join = discord.ui.Button(
            label="Join Voice",
            emoji="🔊",
            style=discord.ButtonStyle.success,
            disabled=(
                self.selected_channel_id is None
                or self.duration_key is None
            ),
        )
        join.callback = self.join_voice
        body.append(discord.ui.ActionRow(join))

        self.add_item(
            discord.ui.Container(*body, accent_colour=discord.Colour.blurple())
        )

    async def _replace_view(self, interaction: discord.Interaction, *, notice=None):
        new_view = BotVoiceView(
            self.cog,
            self.owner_id,
            self.guild,
            page=self.page,
            selected_channel_id=self.selected_channel_id,
            duration_key=self.duration_key,
            notice=notice,
        )
        await interaction.response.edit_message(view=new_view)

    async def channel_selected(self, interaction: discord.Interaction):
        value = interaction.data["values"][0]

        if value == "__previous_page__":
            self.page = max(0, self.page - 1)
            await self._replace_view(interaction)
            return
        if value == "__next_page__":
            channels = self._available_channels()
            pages = max(1, (len(channels) + CHANNELS_PER_PAGE - 1) // CHANNELS_PER_PAGE)
            self.page = min(pages - 1, self.page + 1)
            await self._replace_view(interaction)
            return

        try:
            channel_id = int(value)
        except (TypeError, ValueError):
            await interaction.response.send_message(
                "❌ Invalid channel selection. Please try again.",
                ephemeral=True,
            )
            return

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
                "❌ Please select a voice or stage channel.",
                ephemeral=True,
            )
            return

        member = self._bot_member()
        perms = channel.permissions_for(member) if member else None
        if not perms or not perms.view_channel or not perms.connect:
            await interaction.response.send_message(
                "❌ The bot needs **View Channel** and **Connect** permissions "
                "in that channel.",
                ephemeral=True,
            )
            return

        self.selected_channel_id = channel.id
        self.duration_key = None
        await self._replace_view(interaction)

    async def duration_selected(self, interaction: discord.Interaction):
        self.duration_key = interaction.data["values"][0]
        await self._replace_view(interaction)

    async def change_channel(self, interaction: discord.Interaction):
        self.selected_channel_id = None
        self.duration_key = None
        await self._replace_view(
            interaction,
            notice="Choose a different voice channel from the channel menu.",
        )

    async def join_voice(self, interaction: discord.Interaction):
        if self.selected_channel_id is None or self.duration_key is None:
            await interaction.response.send_message(
                "❌ Select a channel and duration first.",
                ephemeral=True,
            )
            return

        if self._voice_client():
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
        perms = channel.permissions_for(member) if member else None
        if not perms or not perms.view_channel or not perms.connect:
            await interaction.response.send_message(
                "❌ The bot needs **View Channel** and **Connect** permissions "
                "in the selected channel.",
                ephemeral=True,
            )
            return

        has_nacl, nacl_detail = voice_dependency_status()
        if not has_nacl:
            log.error("PyNaCl import failed: %s", nacl_detail)
            await interaction.response.send_message(
                "❌ Voice support is not installed correctly on the host.\n"
                "Railway must install `discord.py[voice]` and `PyNaCl`.\n"
                f"**Diagnostic:** `{nacl_detail[:250]}`",
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
            log.exception("Voice connection timed out")
            await interaction.followup.send(
                "❌ Discord voice connection timed out. Check the channel "
                "permissions and Railway logs.",
                ephemeral=True,
            )
        except discord.Forbidden:
            log.exception("Discord denied voice connection")
            await interaction.followup.send(
                "❌ Discord denied the connection. Check **View Channel** "
                "and **Connect** permissions.",
                ephemeral=True,
            )
        except discord.ClientException as error:
            log.exception("Discord voice client error")
            await interaction.followup.send(
                f"❌ Voice client error: `{str(error)[:300]}`",
                ephemeral=True,
            )
        except Exception as error:
            log.exception("Unexpected error joining voice")
            await interaction.followup.send(
                f"❌ Connection failed: `{type(error).__name__}: "
                f"{str(error)[:250]}`. Check Railway logs.",
                ephemeral=True,
            )

    async def leave_voice(self, interaction: discord.Interaction):
        vc = self._voice_client()
        if vc is None:
            self.cog.cancel_expiration(self.guild.id)
            await self._replace_view(interaction, notice="The bot is already disconnected.")
            return

        await interaction.response.defer()
        try:
            await vc.disconnect(force=True)
            self.cog.cancel_expiration(self.guild.id)
            updated = BotVoiceView(
                self.cog,
                self.owner_id,
                self.guild,
                page=self.page,
            )
            await interaction.edit_original_response(view=updated)
        except Exception as error:
            log.exception("Failed to disconnect from voice")
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
                log.info("Voice duration expired in guild %s", guild_id)
        except asyncio.CancelledError:
            pass
        except Exception:
            log.exception("Automatic voice disconnect failed")
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
        await interaction.response.send_message(view=view, ephemeral=True)

    def cog_unload(self):
        for task in self.expiry_tasks.values():
            task.cancel()


async def setup(bot: commands.Bot):
    await bot.add_cog(BotVoice(bot))
