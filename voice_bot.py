import asyncio
import logging
import time
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

OWNER_ID = 1176149190192152626

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


class BotVoiceView(discord.ui.View):
    def __init__(self, cog: "BotVoice", owner_id: int, guild: discord.Guild):
        super().__init__(timeout=600)
        self.cog = cog
        self.owner_id = owner_id
        self.guild = guild
        self.selected_channel: Optional[discord.VoiceChannel] = None
        self.duration_key: Optional[str] = None
        self.message = None

        connected = bool(guild.voice_client and guild.voice_client.is_connected())

        self.channel_select = discord.ui.ChannelSelect(
            channel_types=[discord.ChannelType.voice],
            placeholder="Select a voice channel",
            min_values=1,
            max_values=1,
            row=0,
            disabled=connected,
        )
        self.channel_select.callback = self.channel_selected
        self.add_item(self.channel_select)

        self.duration_select = discord.ui.Select(
            placeholder="Select connection duration",
            min_values=1,
            max_values=1,
            options=[discord.SelectOption(label=name, value=name) for name in DURATIONS],
            row=1,
            disabled=True,
        )
        self.duration_select.callback = self.duration_selected
        self.add_item(self.duration_select)

        self.join_button = discord.ui.Button(
            label="Join Voice", emoji="🔊",
            style=discord.ButtonStyle.success, row=2, disabled=True,
        )
        self.join_button.callback = self.join_voice
        self.add_item(self.join_button)

        self.leave_button = discord.ui.Button(
            label="Leave Voice", emoji="🔇",
            style=discord.ButtonStyle.danger, row=2, disabled=not connected,
        )
        self.leave_button.callback = self.leave_voice
        self.add_item(self.leave_button)

        if connected:
            self.selected_channel = guild.voice_client.channel

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ This control panel belongs to the bot owner.", ephemeral=True
            )
            return False
        return True

    def build_embed(self) -> discord.Embed:
        vc = self.guild.voice_client
        connected = bool(vc and vc.is_connected())
        if connected:
            channel_text, status = vc.channel.mention, "🟢 Connected"
            expiry = self.cog.expirations.get(self.guild.id)
            duration_text = "Infinite" if expiry is None else (
                f"<t:{int(expiry)}:R>" if expiry else "Not set"
            )
        elif self.selected_channel:
            channel_text, status = self.selected_channel.mention, "🟡 Channel selected"
            duration_text = self.duration_key or "Not selected"
        else:
            channel_text, status, duration_text = "Not selected", "⚪ Waiting for channel", "Not selected"

        embed = discord.Embed(
            title="🔊 Bot Voice Control",
            description=(
                "Control the bot's voice connection from this panel.\n\n"
                f"**Status:** {status}\n"
                f"**Voice channel:** {channel_text}\n"
                f"**Duration:** {duration_text}"
            ),
            color=discord.Color.blurple(),
        )
        embed.set_footer(text="Only the bot owner can use these controls.")
        return embed

    async def channel_selected(self, interaction: discord.Interaction):
        channel = self.channel_select.values[0]
        if not isinstance(channel, discord.VoiceChannel):
            await interaction.response.send_message(
                "❌ Please select a standard voice channel.", ephemeral=True
            )
            return
        if self.guild.voice_client and self.guild.voice_client.is_connected():
            await interaction.response.send_message(
                "❌ The bot is already connected to a voice channel.", ephemeral=True
            )
            return
        self.selected_channel = channel
        self.channel_select.disabled = True
        self.duration_select.disabled = False
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def duration_selected(self, interaction: discord.Interaction):
        self.duration_key = self.duration_select.values[0]
        self.duration_select.disabled = True
        self.join_button.disabled = False
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def join_voice(self, interaction: discord.Interaction):
        if self.selected_channel is None or self.duration_key is None:
            await interaction.response.send_message(
                "❌ Select a voice channel and duration first.", ephemeral=True
            )
            return
        if self.guild.voice_client and self.guild.voice_client.is_connected():
            await interaction.response.send_message(
                "❌ The bot is already connected to a voice channel.", ephemeral=True
            )
            return
        if not self.selected_channel.permissions_for(self.guild.me).connect:
            await interaction.response.send_message(
                "❌ I need the **Connect** permission in that voice channel.", ephemeral=True
            )
            return

        await interaction.response.defer()
        try:
            await self.selected_channel.connect()
            seconds = DURATIONS[self.duration_key]
            expiry = time.time() + seconds if seconds is not None else None
            self.cog.set_expiration(self.guild.id, expiry)
            self.channel_select.disabled = True
            self.duration_select.disabled = True
            self.join_button.disabled = True
            self.leave_button.disabled = False
            await interaction.edit_original_response(embed=self.build_embed(), view=self)
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I don't have permission to join that voice channel.", ephemeral=True
            )
        except (discord.ClientException, discord.HTTPException):
            logging.exception("Failed to join voice channel")
            await interaction.followup.send(
                "❌ Failed to join the voice channel.", ephemeral=True
            )

    async def leave_voice(self, interaction: discord.Interaction):
        vc = self.guild.voice_client
        if vc is None or not vc.is_connected():
            self.leave_button.disabled = True
            await interaction.response.edit_message(embed=self.build_embed(), view=self)
            return
        await interaction.response.defer()
        try:
            await vc.disconnect(force=True)
            self.cog.cancel_expiration(self.guild.id)
            self.channel_select.disabled = False
            self.duration_select.disabled = True
            self.join_button.disabled = True
            self.leave_button.disabled = True
            self.selected_channel = None
            self.duration_key = None
            await interaction.edit_original_response(embed=self.build_embed(), view=self)
        except discord.HTTPException:
            logging.exception("Failed to leave voice channel")
            await interaction.followup.send(
                "❌ Failed to leave the voice channel.", ephemeral=True
            )

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass


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
        name="botvoice", description="Open the bot voice control panel"
    )
    async def botvoice(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                "❌ You do not have permission to use this command.", ephemeral=True
            )
            return
        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.", ephemeral=True
            )
            return
        view = BotVoiceView(self, interaction.user.id, interaction.guild)
        await interaction.response.send_message(
            embed=view.build_embed(), view=view, ephemeral=True
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
