import random
import secrets
import string
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, available_timezones

import discord
from discord.ext import commands
from discord import app_commands


# =========================================================
# CONFIG
# =========================================================

ROLL_MAX_CHOICES = [
    app_commands.Choice(name="2", value=2),
    app_commands.Choice(name="5", value=5),
    app_commands.Choice(name="10", value=10),
    app_commands.Choice(name="25", value=25),
    app_commands.Choice(name="50", value=50),
    app_commands.Choice(name="75", value=75),
    app_commands.Choice(name="100", value=100),
]

TIMEZONE_PAGE_SIZE = 25
VIEW_TIMEOUT = 300

PASSWORD_SYMBOLS = "!@#$%^&*()-_=+[]{};:,.?"


# =========================================================
# COMMON COMPONENTS V2 HELPERS
# =========================================================

def user_thumbnail(user: discord.abc.User) -> discord.ui.Thumbnail:
    return discord.ui.Thumbnail(media=user.display_avatar.url)


class OwnerOnlyView(discord.ui.LayoutView):
    def __init__(self, owner_id: int):
        super().__init__(timeout=VIEW_TIMEOUT)
        self.owner_id = owner_id
        self.expires_at = time.monotonic() + VIEW_TIMEOUT
        self.controls = []

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ Only the person who started this interaction "
                "can use these buttons.",
                ephemeral=True,
            )
            return False

        if time.monotonic() >= self.expires_at:
            await interaction.response.send_message(
                "⌛ This menu has expired. Run the command again.",
                ephemeral=True,
            )
            return False

        return True


def disable_view(view: OwnerOnlyView):
    for control in view.controls:
        control.disabled = True


def make_container(
    title: str,
    description: str,
    user: discord.abc.User,
    accent: discord.Colour = discord.Colour.blurple(),
) -> discord.ui.Container:
    container = discord.ui.Container(accent_colour=accent)

    container.add_item(
        discord.ui.Section(
            discord.ui.TextDisplay(
                f"## {title}\n{description}"
            ),
            accessory=user_thumbnail(user),
        )
    )

    return container


# =========================================================
# NUMBER GENERATOR
# =========================================================

def make_roll_view(
    user: discord.abc.User,
    result: int,
    maximum: int,
) -> OwnerOnlyView:
    view = OwnerOnlyView(user.id)

    container = make_container(
        "🎲 Number Generator",
        f"**Result:** `{result}`\n"
        f"**Range:** `1–{maximum}`",
        user,
    )

    container.add_item(discord.ui.Separator())

    button = discord.ui.Button(
        label="Again",
        emoji="🔄",
        style=discord.ButtonStyle.primary,
    )

    async def again_callback(interaction: discord.Interaction):
        new_result = random.randint(1, maximum)

        new_view = make_roll_view(
            interaction.user,
            new_result,
            maximum,
        )

        await interaction.response.edit_message(view=new_view)

    button.callback = again_callback
    view.controls = [button]

    container.add_item(discord.ui.ActionRow(button))
    view.add_item(container)

    return view


# =========================================================
# COLOR GENERATOR
# =========================================================

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

    container = make_container(
        "🎨 Random Color",
        f"**HEX:** `{hex_color}`\n"
        f"**RGB:** `{red}, {green}, {blue}`",
        user,
        color,
    )

    container.add_item(discord.ui.Separator())

    button = discord.ui.Button(
        label="Another Color",
        emoji="🔄",
        style=discord.ButtonStyle.primary,
    )

    async def again_callback(interaction: discord.Interaction):
        new_color = random.randint(0, 0xFFFFFF)

        new_view = make_color_view(
            interaction.user,
            new_color,
        )

        await interaction.response.edit_message(view=new_view)

    button.callback = again_callback
    view.controls = [button]

    container.add_item(discord.ui.ActionRow(button))
    view.add_item(container)

    return view


# =========================================================
# PASSWORD GENERATOR
# =========================================================

def generate_password(
    length: int,
    uppercase: bool,
    lowercase: bool,
    digits: bool,
    symbols: bool,
) -> str:
    groups = []

    if uppercase:
        groups.append(string.ascii_uppercase)

    if lowercase:
        groups.append(string.ascii_lowercase)

    if digits:
        groups.append(string.digits)

    if symbols:
        groups.append(PASSWORD_SYMBOLS)

    if not groups:
        raise ValueError("Select at least one character type.")

    if length < len(groups):
        raise ValueError(
            "Password length is too short for the selected options."
        )

    # Guarantee at least one character from every selected group.
    password_chars = [
        secrets.choice(group)
        for group in groups
    ]

    all_chars = "".join(groups)

    password_chars.extend(
        secrets.choice(all_chars)
        for _ in range(length - len(password_chars))
    )

    secrets.SystemRandom().shuffle(password_chars)

    return "".join(password_chars)


def make_password_view(
    user: discord.abc.User,
    password: str,
    length: int,
    uppercase: bool,
    lowercase: bool,
    digits: bool,
    symbols: bool,
) -> OwnerOnlyView:
    view = OwnerOnlyView(user.id)

    container = make_container(
        "🔐 Password Generator",
        f"**Password:**\n```{password}```\n"
        f"**Length:** `{length}`\n"
        f"**Uppercase:** `{'Yes' if uppercase else 'No'}`\n"
        f"**Lowercase:** `{'Yes' if lowercase else 'No'}`\n"
        f"**Numbers:** `{'Yes' if digits else 'No'}`\n"
        f"**Symbols:** `{'Yes' if symbols else 'No'}`",
        user,
        discord.Colour.green(),
    )

    container.add_item(discord.ui.Separator())

    again = discord.ui.Button(
        label="Generate Again",
        emoji="🔄",
        style=discord.ButtonStyle.primary,
    )

    async def again_callback(interaction: discord.Interaction):
        new_password = generate_password(
            length,
            uppercase,
            lowercase,
            digits,
            symbols,
        )

        new_view = make_password_view(
            interaction.user,
            new_password,
            length,
            uppercase,
            lowercase,
            digits,
            symbols,
        )

        await interaction.response.edit_message(view=new_view)

    again.callback = again_callback
    view.controls = [again]

    container.add_item(discord.ui.ActionRow(again))
    view.add_item(container)

    return view


# =========================================================
# GRADIENT GENERATOR
# =========================================================

def generate_gradient():
    first = random.randint(0, 0xFFFFFF)
    second = random.randint(0, 0xFFFFFF)
    angle = random.randint(0, 360)

    first_hex = f"#{first:06X}"
    second_hex = f"#{second:06X}"

    css = (
        f"linear-gradient({angle}deg, "
        f"{first_hex} 0%, {second_hex} 100%)"
    )

    return first, second, angle, css


def make_gradient_view(
    user: discord.abc.User,
    first: int,
    second: int,
    angle: int,
    css: str,
) -> OwnerOnlyView:
    view = OwnerOnlyView(user.id)

    container = make_container(
        "🌈 Gradient Generator",
        f"**First Color:** `#{first:06X}`\n"
        f"**Second Color:** `#{second:06X}`\n"
        f"**Angle:** `{angle}°`\n\n"
        f"**CSS Code:**\n```css\nbackground: {css};\n```",
        user,
        discord.Colour(first),
    )

    container.add_item(discord.ui.Separator())

    again = discord.ui.Button(
        label="Generate Again",
        emoji="🔄",
        style=discord.ButtonStyle.primary,
    )

    async def again_callback(interaction: discord.Interaction):
        new_first, new_second, new_angle, new_css = generate_gradient()

        new_view = make_gradient_view(
            interaction.user,
            new_first,
            new_second,
            new_angle,
            new_css,
        )

        await interaction.response.edit_message(view=new_view)

    again.callback = again_callback
    view.controls = [again]

    container.add_item(discord.ui.ActionRow(again))
    view.add_item(container)

    return view


# =========================================================
# TIMESTAMP GENERATOR — TIMEZONE SELECTOR
# =========================================================

TIMEZONES = sorted(available_timezones())


def make_timezone_view(
    user: discord.abc.User,
    page: int = 0,
) -> OwnerOnlyView:
    view = OwnerOnlyView(user.id)

    total_pages = max(
        1,
        (len(TIMEZONES) + TIMEZONE_PAGE_SIZE - 1)
        // TIMEZONE_PAGE_SIZE,
    )

    page = max(0, min(page, total_pages - 1))

    start = page * TIMEZONE_PAGE_SIZE
    end = start + TIMEZONE_PAGE_SIZE
    page_timezones = TIMEZONES[start:end]

    container = make_container(
        "🌍 Choose Timezone",
        f"Select your timezone.\n"
        f"**Page:** `{page + 1}/{total_pages}`\n"
        "After selecting a timezone, the next step opens "
        "in a new private message.",
        user,
    )

    options = [
        discord.SelectOption(
            label=timezone_name[:100],
            value=timezone_name,
        )
        for timezone_name in page_timezones
    ]

    select = discord.ui.Select(
        placeholder="Select a timezone...",
        options=options,
        min_values=1,
        max_values=1,
    )

    async def select_callback(interaction: discord.Interaction):
        timezone_name = select.values[0]

        disable_view(view)

        # Disable the old timezone selector.
        await interaction.response.edit_message(view=view)

        # Open the next private step.
        await interaction.followup.send(
            view=make_time_view(
                interaction.user,
                timezone_name,
            ),
            ephemeral=True,
        )

    select.callback = select_callback
    container.add_item(discord.ui.ActionRow(select))

    previous = discord.ui.Button(
        label="Previous",
        emoji="◀️",
        style=discord.ButtonStyle.secondary,
        disabled=(page == 0),
    )

    next_page = discord.ui.Button(
        label="Next Page",
        emoji="▶️",
        style=discord.ButtonStyle.primary,
        disabled=(page >= total_pages - 1),
    )

    async def previous_callback(interaction: discord.Interaction):
        await interaction.response.edit_message(
            view=make_timezone_view(interaction.user, page - 1)
        )

    async def next_callback(interaction: discord.Interaction):
        await interaction.response.edit_message(
            view=make_timezone_view(interaction.user, page + 1)
        )

    previous.callback = previous_callback
    next_page.callback = next_callback

    view.controls = [select, previous, next_page]

    container.add_item(
        discord.ui.ActionRow(previous, next_page)
    )

    view.add_item(container)
    return view


# =========================================================
# TIMESTAMP GENERATOR — TIME SELECTION
# =========================================================

def make_time_view(
    user: discord.abc.User,
    timezone_name: str,
) -> OwnerOnlyView:
    view = OwnerOnlyView(user.id)

    container = make_container(
        "🕒 Choose Time",
        f"**Timezone:** `{timezone_name}`\n"
        "Choose a preset or enter your own date and time.",
        user,
    )

    container.add_item(discord.ui.Separator())

    buttons = []

    presets = [
        ("In 1 Minute", 1),
        ("In 5 Minutes", 5),
        ("In 10 Minutes", 10),
    ]

    for label, minutes in presets:
        button = discord.ui.Button(
            label=label,
            style=discord.ButtonStyle.primary,
        )

        async def preset_callback(
            interaction: discord.Interaction,
            minutes=minutes,
        ):
            timezone = ZoneInfo(timezone_name)

            target = (
                datetime.now(timezone)
                + timedelta(minutes=minutes)
            )

            disable_view(view)
            await interaction.response.edit_message(view=view)

            await interaction.followup.send(
                view=make_format_view(
                    interaction.user,
                    timezone_name,
                    target,
                ),
                ephemeral=True,
            )

        button.callback = preset_callback
        buttons.append(button)

    custom = discord.ui.Button(
        label="Enter Custom Time",
        emoji="✍️",
        style=discord.ButtonStyle.success,
    )

    async def custom_callback(interaction: discord.Interaction):
        await interaction.response.send_modal(
            CustomTimeModal(
                owner_id=interaction.user.id,
                timezone_name=timezone_name,
            )
        )

    custom.callback = custom_callback
    buttons.append(custom)

    choose_date = discord.ui.Button(
        label="Choose Date",
        emoji="📅",
        style=discord.ButtonStyle.secondary,
    )

    async def choose_date_callback(interaction: discord.Interaction):
        await interaction.response.send_modal(
            CustomTimeModal(
                owner_id=interaction.user.id,
                timezone_name=timezone_name,
            )
        )

    choose_date.callback = choose_date_callback
    buttons.append(choose_date)

    view.controls = buttons

    # Keep rows within Discord's five-button row limit.
    container.add_item(
        discord.ui.ActionRow(*buttons[:3])
    )
    container.add_item(
        discord.ui.ActionRow(*buttons[3:])
    )

    view.add_item(container)
    return view


# =========================================================
# TIMESTAMP GENERATOR — CUSTOM TIME MODAL
# =========================================================

def parse_custom_time(
    raw: str,
    timezone_name: str,
) -> datetime:
    timezone = ZoneInfo(timezone_name)
    now = datetime.now(timezone)

    raw = raw.strip()

    # Full date and time.
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(raw, fmt)
            result = parsed.replace(tzinfo=timezone)

            if result <= now:
                raise ValueError(
                    "That date and time is in the past. "
                    "Please enter a future time."
                )

            return result

        except ValueError as error:
            if "in the past" in str(error):
                raise

    # Time only, e.g. 14:00.
    try:
        parsed_time = datetime.strptime(raw, "%H:%M").time()

        result = datetime.combine(
            now.date(),
            parsed_time,
            tzinfo=timezone,
        )

        if result <= now:
            result += timedelta(days=1)

        return result

    except ValueError:
        pass

    # Weekday and time, e.g. Monday 14:00.
    for fmt in ("%A %H:%M", "%a %H:%M"):
        try:
            parsed = datetime.strptime(raw, fmt)

            target_weekday = parsed.weekday()
            days_ahead = (target_weekday - now.weekday()) % 7

            result = datetime.combine(
                now.date() + timedelta(days=days_ahead),
                parsed.time(),
                tzinfo=timezone,
            )

            if result <= now:
                result += timedelta(days=7)

            return result

        except ValueError:
            pass

    raise ValueError(
        "Invalid format. Use `14:00`, `Monday 14:00`, "
        "or `2026-12-25 14:00`."
    )


class CustomTimeModal(discord.ui.Modal):
    def __init__(
        self,
        owner_id: int,
        timezone_name: str,
    ):
        super().__init__(
            title="Enter Custom Date and Time",
            timeout=VIEW_TIMEOUT,
        )

        self.owner_id = owner_id
        self.timezone_name = timezone_name

        self.time_input = discord.ui.TextInput(
            label="Date and time",
            placeholder="14:00, Monday 14:00, or 2026-12-25 14:00",
            required=True,
            max_length=80,
        )

        self.add_item(self.time_input)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ This form belongs to another user.",
                ephemeral=True,
            )
            return

        try:
            target = parse_custom_time(
                self.time_input.value,
                self.timezone_name,
            )

        except ValueError as error:
            await interaction.response.send_message(
                f"❌ {error}",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            view=make_format_view(
                interaction.user,
                self.timezone_name,
                target,
            ),
            ephemeral=True,
        )


# =========================================================
# TIMESTAMP GENERATOR — FORMAT SELECTOR
# =========================================================

TIMESTAMP_FORMATS = [
    ("Short Time", "t", "16:20"),
    ("Long Time", "T", "16:20:30"),
    ("Short Date", "d", "20/10/2026"),
    ("Long Date", "D", "20 October 2026"),
    ("Short Date & Time", "f", "20 October 2026 16:20"),
    ("Long Date & Time", "F", "Tuesday, 20 October 2026 16:20"),
    ("Relative Time", "R", "in 5 minutes"),
]


def make_format_view(
    user: discord.abc.User,
    timezone_name: str,
    target: datetime,
) -> OwnerOnlyView:
    view = OwnerOnlyView(user.id)

    container = make_container(
        "🧾 Choose Timestamp Format",
        f"**Timezone:** `{timezone_name}`\n"
        f"**Selected time:** `{target.strftime('%Y-%m-%d %H:%M:%S')}`\n"
        "Choose how Discord should display the timestamp.",
        user,
    )

    options = [
        discord.SelectOption(
            label=name,
            value=fmt,
            description=f"Example: {example}"[:100],
        )
        for name, fmt, example in TIMESTAMP_FORMATS
    ]

    select = discord.ui.Select(
        placeholder="Select a timestamp format...",
        options=options,
        min_values=1,
        max_values=1,
    )

    async def select_callback(interaction: discord.Interaction):
        selected_format = select.values[0]

        disable_view(view)
        await interaction.response.edit_message(view=view)

        await interaction.followup.send(
            view=make_timestamp_result_view(
                interaction.user,
                timezone_name,
                target,
                selected_format,
            ),
            ephemeral=True,
        )

    select.callback = select_callback
    view.controls = [select]

    container.add_item(discord.ui.ActionRow(select))
    view.add_item(container)

    return view


# =========================================================
# TIMESTAMP GENERATOR — RESULT
# =========================================================

def make_timestamp_result_view(
    user: discord.abc.User,
    timezone_name: str,
    target: datetime,
    timestamp_format: str,
) -> OwnerOnlyView:
    view = OwnerOnlyView(user.id)

    unix_timestamp = int(target.timestamp())
    code = f"<t:{unix_timestamp}:{timestamp_format}>"

    format_name = next(
        (
            name
            for name, fmt, _ in TIMESTAMP_FORMATS
            if fmt == timestamp_format
        ),
        "Timestamp",
    )

    container = make_container(
        "⏰ Timestamp Result",
        f"**Timezone:** `{timezone_name}`\n"
        f"**Date:** `{target.strftime('%A, %d %B %Y')}`\n"
        f"**Time:** `{target.strftime('%H:%M:%S')}`\n"
        f"**Format:** `{format_name}`\n\n"
        f"**Timestamp Code:** `{code}`\n\n"
        f"**Discord Preview:** {code}",
        user,
        discord.Colour.green(),
    )

    container.add_item(discord.ui.Separator())

    copy_button = discord.ui.Button(
        label="Show Copyable Code",
        emoji="📋",
        style=discord.ButtonStyle.primary,
    )

    async def copy_callback(interaction: discord.Interaction):
        await interaction.response.send_message(
            view=make_code_view(
                interaction.user,
                code,
            ),
            ephemeral=True,
        )

    copy_button.callback = copy_callback

    format_button = discord.ui.Button(
        label="Change Format",
        emoji="🔄",
        style=discord.ButtonStyle.secondary,
    )

    async def format_callback(interaction: discord.Interaction):
        await interaction.response.send_message(
            view=make_format_view(
                interaction.user,
                timezone_name,
                target,
            ),
            ephemeral=True,
        )

    format_button.callback = format_callback

    new_button = discord.ui.Button(
        label="New Timestamp",
        emoji="🆕",
        style=discord.ButtonStyle.success,
    )

    async def new_callback(interaction: discord.Interaction):
        await interaction.response.send_message(
            view=make_timezone_view(interaction.user),
            ephemeral=True,
        )

    new_button.callback = new_callback

    view.controls = [
        copy_button,
        format_button,
        new_button,
    ]

    container.add_item(
        discord.ui.ActionRow(
            copy_button,
            format_button,
            new_button,
        )
    )

    view.add_item(container)
    return view


def make_code_view(
    user: discord.abc.User,
    code: str,
) -> OwnerOnlyView:
    view = OwnerOnlyView(user.id)

    container = make_container(
        "📋 Copy Timestamp Code",
        "Copy the code below and paste it into a Discord message.\n\n"
        f"```text\n{code}\n```",
        user,
    )

    view.add_item(container)
    return view


# =========================================================
# SLASH COMMANDS
# =========================================================

class RollCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -----------------------------------------------------
    # /roll
    # -----------------------------------------------------

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

        await interaction.response.send_message(
            view=make_roll_view(
                interaction.user,
                result,
                max_value,
            ),
            ephemeral=False,
        )

    # -----------------------------------------------------
    # /color
    # -----------------------------------------------------

    @app_commands.command(
        name="color",
        description="Generate a random color",
    )
    async def color(self, interaction: discord.Interaction):
        color_value = random.randint(0, 0xFFFFFF)

        await interaction.response.send_message(
            view=make_color_view(
                interaction.user,
                color_value,
            ),
            ephemeral=False,
        )

    # -----------------------------------------------------
    # /password
    # -----------------------------------------------------

    @app_commands.command(
        name="password",
        description="Generate a secure random password",
    )
    @app_commands.describe(
        length="Password length (8–128)",
        uppercase="Include uppercase letters",
        lowercase="Include lowercase letters",
        digits="Include numbers",
        symbols="Include special characters",
    )
    async def password(
        self,
        interaction: discord.Interaction,
        length: app_commands.Range[int, 8, 128] = 20,
        uppercase: bool = True,
        lowercase: bool = True,
        digits: bool = True,
        symbols: bool = True,
    ):
        if not any([uppercase, lowercase, digits, symbols]):
            await interaction.response.send_message(
                "❌ Select at least one character type.",
                ephemeral=True,
            )
            return

        password_value = generate_password(
            length,
            uppercase,
            lowercase,
            digits,
            symbols,
        )

        await interaction.response.send_message(
            view=make_password_view(
                interaction.user,
                password_value,
                length,
                uppercase,
                lowercase,
                digits,
                symbols,
            ),
            ephemeral=True,
        )

    # -----------------------------------------------------
    # /gradient
    # -----------------------------------------------------

    @app_commands.command(
        name="gradient",
        description="Generate a random CSS gradient",
    )
    async def gradient(self, interaction: discord.Interaction):
        first, second, angle, css = generate_gradient()

        await interaction.response.send_message(
            view=make_gradient_view(
                interaction.user,
                first,
                second,
                angle,
                css,
            ),
            ephemeral=False,
        )

    # -----------------------------------------------------
    # /timestamp
    # -----------------------------------------------------

    @app_commands.command(
        name="timestamp",
        description="Create a Discord timestamp",
    )
    async def timestamp(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            view=make_timezone_view(interaction.user),
            ephemeral=True,
        )


# =========================================================
# EXTENSION SETUP
# =========================================================

async def setup(bot: commands.Bot):
    await bot.add_cog(RollCommands(bot))
