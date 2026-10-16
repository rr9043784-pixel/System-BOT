import random
import time

import discord
from discord.ext import commands
from discord import app_commands


ROLL_MAX_CHOICES = [
    app_commands.Choice(name="2", value=2),
    app_commands.Choice(name="5", value=5),
    app_commands.Choice(name="10", value=10),
    app_commands.Choice(name="25", value=25),
    app_commands.Choice(name="50", value=50),
    app_commands.Choice(name="75", value=75),
    app_commands.Choice(name="100", value=100),
]


def user_thumbnail(user: discord.abc.User) -> discord.ui.Thumbnail:
    return discord.ui.Thumbnail(media=user.display_avatar.url)


class OwnerOnlyView(discord.ui.LayoutView):
    def __init__(self, owner_id: int):
        super().__init__(timeout=None)
        self.owner_id = owner_id
        self.expires_at = time.monotonic() + 300

    async def interaction_check(
        self, interaction: discord.Interaction
    ) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ Only the person who used this command "
                "can interact with these buttons.",
                ephemeral=True,
            )
            return False

        if time.monotonic() >= self.expires_at:
            await interaction.response.send_message(
                "⌛ This button has expired. Please run the command again.",
                ephemeral=True,
            )
            return False

        return True


def make_roll_view(
    user: discord.abc.User,
    result: int,
    maximum: int,
) -> OwnerOnlyView:
    view = OwnerOnlyView(user.id)

    container = discord.ui.Container(
        accent_colour=discord.Colour.blurple(),
    )

    container.add_item(
        discord.ui.Section(
            discord.ui.TextDisplay(
                "## 🎲 Number Generator\n"
                f"**Result:** `{result}`\n"
                f"**Range:** `1–{maximum}`"
            ),
            accessory=user_thumbnail(user),
        )
    )

    container.add_item(discord.ui.Separator())

    button = discord.ui.Button(
        label="Again",
        emoji="🔄",
        style=discord.ButtonStyle.primary,
        custom_id=f"roll_again_{user.id}",
    )

    async def again_callback(interaction: discord.Interaction):
        if not await view.interaction_check(interaction):
            return

        new_result = random.randint(1, maximum)
        new_view = make_roll_view(
            interaction.user,
            new_result,
            maximum,
        )
        await interaction.response.edit_message(view=new_view)

    button.callback = again_callback
    container.add_item(discord.ui.ActionRow(button))
    view.add_item(container)

    return view


def make_color_view(
    user: discord.abc.User,
    color_value: int,
) -> OwnerOnlyView:
    view = OwnerOnlyView(user.id)

    color = discord.Colour(color_value)
    hex_color = f"#{color_value:06X}"

    red = (color_value >> 16) & 255
    green = (color_value >> 8) & 255
    blue = color_value & 255

    container = discord.ui.Container(
        accent_colour=color,
    )

    container.add_item(
        discord.ui.Section(
            discord.ui.TextDisplay(
                "## 🎨 Random Color\n"
                f"**HEX:** `{hex_color}`\n"
                f"**RGB:** `{red}, {green}, {blue}`"
            ),
            accessory=user_thumbnail(user),
        )
    )

    container.add_item(discord.ui.Separator())

    button = discord.ui.Button(
        label="Another Color",
        emoji="🔄",
        style=discord.ButtonStyle.primary,
        custom_id=f"color_again_{user.id}",
    )

    async def again_callback(interaction: discord.Interaction):
        if not await view.interaction_check(interaction):
            return

        new_color_value = random.randint(0, 0xFFFFFF)
        new_view = make_color_view(
            interaction.user,
            new_color_value,
        )
        await interaction.response.edit_message(view=new_view)

    button.callback = again_callback
    container.add_item(discord.ui.ActionRow(button))
    view.add_item(container)

    return view


class RollCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="roll",
        description="Generate a random number",
    )
    @app_commands.describe(
        maximum="The maximum number",
    )
    @app_commands.choices(maximum=ROLL_MAX_CHOICES)
    async def roll(
        self,
        interaction: discord.Interaction,
        maximum: app_commands.Choice[int] | None = None,
    ):
        max_value = maximum.value if maximum else 100
        result = random.randint(1, max_value)

        view = make_roll_view(
            interaction.user,
            result,
            max_value,
        )

        await interaction.response.send_message(
            view=view,
            ephemeral=False,
        )

    @app_commands.command(
        name="color",
        description="Generate a random color",
    )
    async def color(self, interaction: discord.Interaction):
        color_value = random.randint(0, 0xFFFFFF)

        view = make_color_view(
            interaction.user,
            color_value,
        )

        await interaction.response.send_message(
            view=view,
            ephemeral=False,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(RollCommands(bot))
