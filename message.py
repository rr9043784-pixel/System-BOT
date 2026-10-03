import discord
from discord.ext import commands


# =========================================================
# ROLE IDs
# =========================================================

# Language
RUSSIAN_ROLE = 1540457657771757578
ENGLISH_ROLE = 1540457933639262258

# Nickname colors
BLACK_ROLE = 1531987548652441702
BLUE_ROLE = 1541333122287935528
PURPLE_ROLE = 1541332958063890452
PINK_ROLE = 1541333562375274496
BRIGHT_GREEN_ROLE = 1541334227893624862

# Platforms
MOBILE_ROLE = 1545281085678686281
TABLET_ROLE = 1545281561329533030
PC_ROLE = 1545280805905895504
XBOX_ROLE = 1545281911151398942
PLAYSTATION_ROLE = 1545281770818248805
NINTENDO_ROLE = 1545283995665834086


# =========================================================
# OWNER
# =========================================================

OWNER_ID = 1176149190192152626


# =========================================================
# ROLE GROUPS
# =========================================================

COLOR_ROLES = [
    BLACK_ROLE,
    BLUE_ROLE,
    PURPLE_ROLE,
    PINK_ROLE,
    BRIGHT_GREEN_ROLE,
]

LANGUAGE_ROLES = [
    RUSSIAN_ROLE,
    ENGLISH_ROLE,
]

PLATFORM_ROLES = [
    MOBILE_ROLE,
    TABLET_ROLE,
    PC_ROLE,
    XBOX_ROLE,
    PLAYSTATION_ROLE,
    NINTENDO_ROLE,
]


# =========================================================
# ROLE FUNCTION
# =========================================================

async def replace_role(member, role_id, role_group):
    role = member.guild.get_role(role_id)

    if role is None:
        return False

    # Remove old role from the same category
    for old_role_id in role_group:
        old_role = member.guild.get_role(old_role_id)

        if (
            old_role
            and old_role in member.roles
            and old_role.id != role_id
        ):
            try:
                await member.remove_roles(old_role)
            except discord.Forbidden:
                return False

    # Add new role
    if role not in member.roles:
        try:
            await member.add_roles(role)
        except discord.Forbidden:
            return False

    return True


# =========================================================
# COLOR SELECT
# =========================================================

class ColorSelect(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(
                label="Black",
                emoji="🖤",
                value=str(BLACK_ROLE)
            ),
            discord.SelectOption(
                label="Blue",
                emoji="💙",
                value=str(BLUE_ROLE)
            ),
            discord.SelectOption(
                label="Purple",
                emoji="💜",
                value=str(PURPLE_ROLE)
            ),
            discord.SelectOption(
                label="Pink",
                emoji="🩷",
                value=str(PINK_ROLE)
            ),
            discord.SelectOption(
                label="Bright Green",
                emoji="💚",
                value=str(BRIGHT_GREEN_ROLE)
            ),
        ]

        super().__init__(
            placeholder="🎨 Choose a nickname color...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="features_color",
        )

    async def callback(self, interaction: discord.Interaction):

        role_id = int(self.values[0])

        success = await replace_role(
            interaction.user,
            role_id,
            COLOR_ROLES
        )

        if success:
            role = interaction.guild.get_role(role_id)

            await interaction.response.send_message(
                f"🎨 Your nickname color is now **{role.name}**!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ I couldn't update your nickname color.",
                ephemeral=True
            )


# =========================================================
# LANGUAGE SELECT
# =========================================================

class LanguageSelect(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(
                label="Russian",
                emoji="🇷🇺",
                value=str(RUSSIAN_ROLE)
            ),
            discord.SelectOption(
                label="English",
                emoji="🇬🇧",
                value=str(ENGLISH_ROLE)
            ),
        ]

        super().__init__(
            placeholder="🌐 Choose your language...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="features_language",
        )

    async def callback(self, interaction: discord.Interaction):

        role_id = int(self.values[0])

        success = await replace_role(
            interaction.user,
            role_id,
            LANGUAGE_ROLES
        )

        if success:
            role = interaction.guild.get_role(role_id)

            await interaction.response.send_message(
                f"🌐 Your language is now **{role.name}**!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ I couldn't update your language.",
                ephemeral=True
            )


# =========================================================
# PLATFORM SELECT
# =========================================================

class PlatformSelect(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(
                label="Mobile",
                emoji="📱",
                value=str(MOBILE_ROLE)
            ),
            discord.SelectOption(
                label="Tablet",
                emoji="📟",
                value=str(TABLET_ROLE)
            ),
            discord.SelectOption(
                label="PC",
                emoji="💻",
                value=str(PC_ROLE)
            ),
            discord.SelectOption(
                label="Xbox",
                emoji="🟢",
                value=str(XBOX_ROLE)
            ),
            discord.SelectOption(
                label="PlayStation",
                emoji="🎮",
                value=str(PLAYSTATION_ROLE)
            ),
            discord.SelectOption(
                label="Nintendo Switch",
                emoji="🕹️",
                value=str(NINTENDO_ROLE)
            ),
        ]

        super().__init__(
            placeholder="📱 Choose your platform...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="features_platform",
        )

    async def callback(self, interaction: discord.Interaction):

        role_id = int(self.values[0])

        success = await replace_role(
            interaction.user,
            role_id,
            PLATFORM_ROLES
        )

        if success:
            role = interaction.guild.get_role(role_id)

            await interaction.response.send_message(
                f"📱 Your platform is now **{role.name}**!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ I couldn't update your platform.",
                ephemeral=True
            )


# =========================================================
# FEATURES VIEW
# =========================================================

class FeaturesView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(ColorSelect())
        self.add_item(LanguageSelect())
        self.add_item(PlatformSelect())


# =========================================================
# MESSAGE COG
# =========================================================

class Message(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # -----------------------------------------------------
    # !features panel
    # -----------------------------------------------------

    @commands.command()
    async def features(self, ctx, action=None):

        # ONLY OWNER CAN USE THIS COMMAND
        if ctx.author.id != OWNER_ID:
            return

        if action is None or action.lower() != "panel":
            return

        embed = discord.Embed(
            title="✨ Features",
            description=(
                "Choose your preferences using the menus below!\n\n"

                "🎨 **Nickname Color**\n"
                "Choose a color for your nickname. "
                "You can change it at any time.\n\n"

                "🌐 **Language**\n"
                "Choose your preferred language. "
                "This can also help with language-specific channels.\n\n"

                "📱 **Platform**\n"
                "Choose the platform you play on.\n\n"

                "⬇️ **Menu** ⬇️"
            ),
            color=discord.Color.from_rgb(88, 101, 242)
        )

        embed.set_footer(
            text="Select an option from the menus below."
        )

        await ctx.send(
            embed=embed,
            view=FeaturesView()
        )


# =========================================================
# SETUP
# =========================================================

async def setup(bot):
    await bot.add_cog(Message(bot))

    # Register the view so menus continue working after restart
    bot.add_view(FeaturesView())
