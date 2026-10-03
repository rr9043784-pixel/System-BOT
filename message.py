import discord
from discord.ext import commands


# =========================================================
# OWNER
# =========================================================

OWNER_ID = 1176149190192152626


# =========================================================
# FEATURE ROLE IDS
# =========================================================

# Language
RUSSIAN_ROLE_ID = 1540457657771757578
ENGLISH_ROLE_ID = 1540457933639262258

# Colors
BLACK_ROLE_ID = 1531987548652441702
BLUE_ROLE_ID = 1541333122287935528
PURPLE_ROLE_ID = 1541332958063890452
PINK_ROLE_ID = 1541333562375274496
GREEN_ROLE_ID = 1541334227893624862

# Platforms
MOBILE_ROLE_ID = 1545281085678686281
TABLET_ROLE_ID = 1545281561329533030
PC_ROLE_ID = 1545280805905895504
XBOX_ROLE_ID = 1545281911151398942
PLAYSTATION_ROLE_ID = 1545281770818248805
SWITCH_ROLE_ID = 1545283995665834086


# =========================================================
# PING ROLE IDS
# =========================================================

YOUTUBE_ROLE_ID = 1541715251018465351
TOURNAMENT_ROLE_ID = 1541715118872731768
GIVEAWAY_ROLE_ID = 1541716902752157798
NEWS_ROLE_ID = 1541715546356060200


# =========================================================
# ROLE GROUPS
# =========================================================

LANGUAGE_ROLES = {
    RUSSIAN_ROLE_ID,
    ENGLISH_ROLE_ID,
}

COLOR_ROLES = {
    BLACK_ROLE_ID,
    BLUE_ROLE_ID,
    PURPLE_ROLE_ID,
    PINK_ROLE_ID,
    GREEN_ROLE_ID,
}

PLATFORM_ROLES = {
    MOBILE_ROLE_ID,
    TABLET_ROLE_ID,
    PC_ROLE_ID,
    XBOX_ROLE_ID,
    PLAYSTATION_ROLE_ID,
    SWITCH_ROLE_ID,
}

PING_ROLES = {
    YOUTUBE_ROLE_ID,
    TOURNAMENT_ROLE_ID,
    GIVEAWAY_ROLE_ID,
    NEWS_ROLE_ID,
}


# =========================================================
# FEATURE ROLE FUNCTION
# =========================================================

async def replace_role(
    member: discord.Member,
    role_id: int,
    role_group: set[int],
):
    guild = member.guild

    selected_role = guild.get_role(role_id)

    if selected_role is None:
        return False

    roles_to_remove = [
        role
        for role in member.roles
        if role.id in role_group and role.id != role_id
    ]

    if roles_to_remove:
        await member.remove_roles(*roles_to_remove)

    if selected_role not in member.roles:
        await member.add_roles(selected_role)

    return True


# =========================================================
# LANGUAGE SELECT
# =========================================================

class LanguageSelect(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(
                label="Russian",
                description="Choose Russian",
                emoji="🇷🇺",
                value=str(RUSSIAN_ROLE_ID),
            ),
            discord.SelectOption(
                label="English",
                description="Choose English",
                emoji="🇬🇧",
                value=str(ENGLISH_ROLE_ID),
            ),
        ]

        super().__init__(
            placeholder="🌐 Choose your language",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="features_language_v2",
        )

    async def callback(self, interaction: discord.Interaction):

        role_id = int(self.values[0])

        try:
            success = await replace_role(
                interaction.user,
                role_id,
                LANGUAGE_ROLES,
            )

            if not success:
                await interaction.response.send_message(
                    "❌ The selected role could not be found.",
                    ephemeral=True,
                )
                return

            role = interaction.guild.get_role(role_id)

            await interaction.response.send_message(
                f"✅ Your language has been set to **{role.name}**.",
                ephemeral=True,
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to manage this role.",
                ephemeral=True,
            )

        except Exception:
            await interaction.response.send_message(
                "❌ Something went wrong while changing your role.",
                ephemeral=True,
            )


# =========================================================
# COLOR SELECT
# =========================================================

class ColorSelect(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(
                label="Black",
                description="Choose black",
                emoji="⚫",
                value=str(BLACK_ROLE_ID),
            ),
            discord.SelectOption(
                label="Blue",
                description="Choose blue",
                emoji="🔵",
                value=str(BLUE_ROLE_ID),
            ),
            discord.SelectOption(
                label="Purple",
                description="Choose purple",
                emoji="🟣",
                value=str(PURPLE_ROLE_ID),
            ),
            discord.SelectOption(
                label="Pink",
                description="Choose pink",
                emoji="🩷",
                value=str(PINK_ROLE_ID),
            ),
            discord.SelectOption(
                label="Bright Green",
                description="Choose bright green",
                emoji="🟢",
                value=str(GREEN_ROLE_ID),
            ),
        ]

        super().__init__(
            placeholder="🎨 Choose your nickname color",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="features_color_v2",
        )

    async def callback(self, interaction: discord.Interaction):

        role_id = int(self.values[0])

        try:
            success = await replace_role(
                interaction.user,
                role_id,
                COLOR_ROLES,
            )

            if not success:
                await interaction.response.send_message(
                    "❌ The selected role could not be found.",
                    ephemeral=True,
                )
                return

            role = interaction.guild.get_role(role_id)

            await interaction.response.send_message(
                f"✅ Your nickname color has been set to **{role.name}**.",
                ephemeral=True,
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to manage this role.",
                ephemeral=True,
            )

        except Exception:
            await interaction.response.send_message(
                "❌ Something went wrong while changing your role.",
                ephemeral=True,
            )


# =========================================================
# PLATFORM SELECT
# =========================================================

class PlatformSelect(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(
                label="Mobile",
                description="I play on mobile",
                emoji="📱",
                value=str(MOBILE_ROLE_ID),
            ),
            discord.SelectOption(
                label="Tablet",
                description="I play on tablet",
                emoji="📲",
                value=str(TABLET_ROLE_ID),
            ),
            discord.SelectOption(
                label="PC",
                description="I play on PC",
                emoji="💻",
                value=str(PC_ROLE_ID),
            ),
            discord.SelectOption(
                label="Xbox",
                description="I play on Xbox",
                emoji="🎮",
                value=str(XBOX_ROLE_ID),
            ),
            discord.SelectOption(
                label="PlayStation",
                description="I play on PlayStation",
                emoji="🎮",
                value=str(PLAYSTATION_ROLE_ID),
            ),
            discord.SelectOption(
                label="Nintendo Switch",
                description="I play on Nintendo Switch",
                emoji="🕹️",
                value=str(SWITCH_ROLE_ID),
            ),
        ]

        super().__init__(
            placeholder="🎮 Choose your platform",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="features_platform_v2",
        )

    async def callback(self, interaction: discord.Interaction):

        role_id = int(self.values[0])

        try:
            success = await replace_role(
                interaction.user,
                role_id,
                PLATFORM_ROLES,
            )

            if not success:
                await interaction.response.send_message(
                    "❌ The selected role could not be found.",
                    ephemeral=True,
                )
                return

            role = interaction.guild.get_role(role_id)

            await interaction.response.send_message(
                f"✅ Your platform has been set to **{role.name}**.",
                ephemeral=True,
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to manage this role.",
                ephemeral=True,
            )

        except Exception:
            await interaction.response.send_message(
                "❌ Something went wrong while changing your role.",
                ephemeral=True,
            )


# =========================================================
# FEATURES COMPONENTS V2
# =========================================================

class FeaturesView(discord.ui.LayoutView):

    def __init__(self):
        super().__init__(timeout=None)

        container = discord.ui.Container(

            discord.ui.TextDisplay(
                "# ✨ Features\n"
                "Choose your preferences using the menus below."
            ),

            discord.ui.Separator(
                visible=True,
                spacing=discord.SeparatorSpacing.small,
            ),

            discord.ui.TextDisplay(
                "### 🎨 Nickname Color\n"
                "Choose a color for your nickname. "
                "You can change it at any time."
            ),

            discord.ui.ActionRow(
                ColorSelect()
            ),

            discord.ui.Separator(
                visible=True,
                spacing=discord.SeparatorSpacing.small,
            ),

            discord.ui.TextDisplay(
                "### 🌐 Language\n"
                "Choose your preferred language. "
                "This can also help with language-specific channels."
            ),

            discord.ui.ActionRow(
                LanguageSelect()
            ),

            discord.ui.Separator(
                visible=True,
                spacing=discord.SeparatorSpacing.small,
            ),

            discord.ui.TextDisplay(
                "### 🎮 Platform\n"
                "Choose the platform you play on."
            ),

            discord.ui.ActionRow(
                PlatformSelect()
            ),

            discord.ui.Separator(
                visible=True,
                spacing=discord.SeparatorSpacing.small,
            ),

            discord.ui.TextDisplay(
                "-# Select an option from the menus above."
            ),

            accent_colour=discord.Colour.from_rgb(88, 101, 242),
        )

        self.add_item(container)


# =========================================================
# PING BUTTON
# =========================================================

class PingButton(discord.ui.Button):

    def __init__(
        self,
        label: str,
        emoji: str,
        role_id: int,
        custom_id: str,
    ):
        super().__init__(
            label=label,
            emoji=emoji,
            style=discord.ButtonStyle.secondary,
            custom_id=custom_id,
        )

        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction):

        role = interaction.guild.get_role(self.role_id)

        if role is None:
            await interaction.response.send_message(
                "❌ The selected role could not be found.",
                ephemeral=True,
            )
            return

        try:
            if role in interaction.user.roles:

                await interaction.user.remove_roles(role)

                await interaction.response.send_message(
                    f"🔕 **{role.name}** notifications disabled.",
                    ephemeral=True,
                )

            else:

                await interaction.user.add_roles(role)

                await interaction.response.send_message(
                    f"🔔 **{role.name}** notifications enabled.",
                    ephemeral=True,
                )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to manage this role.",
                ephemeral=True,
            )

        except Exception:
            await interaction.response.send_message(
                "❌ Something went wrong while changing your notification role.",
                ephemeral=True,
            )


# =========================================================
# REMOVE ALL PING ROLES
# =========================================================

class RemovePingRolesButton(discord.ui.Button):

    def __init__(self):
        super().__init__(
            label="Remove all ping roles",
            emoji="❌",
            style=discord.ButtonStyle.danger,
            custom_id="features_remove_ping_roles_v2",
        )

    async def callback(self, interaction: discord.Interaction):

        roles_to_remove = [
            role
            for role in interaction.user.roles
            if role.id in PING_ROLES
        ]

        try:

            if roles_to_remove:
                await interaction.user.remove_roles(*roles_to_remove)

            await interaction.response.send_message(
                "✅ All notification roles have been removed.",
                ephemeral=True,
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to manage these roles.",
                ephemeral=True,
            )

        except Exception:
            await interaction.response.send_message(
                "❌ Something went wrong while removing your roles.",
                ephemeral=True,
            )


# =========================================================
# PING COMPONENTS V2
# =========================================================

class PingView(discord.ui.LayoutView):

    def __init__(self):
        super().__init__(timeout=None)

        container = discord.ui.Container(

            discord.ui.TextDisplay(
                "# 🔔 Choose\n"
                "Choose which notifications you want to receive."
            ),

            discord.ui.Separator(
                visible=True,
                spacing=discord.SeparatorSpacing.small,
            ),

            discord.ui.TextDisplay(
                "### ▶️ YouTube\n"
                "Get notified about new YouTube content."
            ),

            discord.ui.ActionRow(
                PingButton(
                    "YouTube",
                    "▶️",
                    YOUTUBE_ROLE_ID,
                    "ping_youtube_v2",
                )
            ),

            discord.ui.Separator(
                visible=True,
                spacing=discord.SeparatorSpacing.small,
            ),

            discord.ui.TextDisplay(
                "### 🏆 Tournament\n"
                "Get notified about tournaments and events."
            ),

            discord.ui.ActionRow(
                PingButton(
                    "Tournament",
                    "🏆",
                    TOURNAMENT_ROLE_ID,
                    "ping_tournament_v2",
                )
            ),

            discord.ui.Separator(
                visible=True,
                spacing=discord.SeparatorSpacing.small,
            ),

            discord.ui.TextDisplay(
                "### 🎁 Giveaway\n"
                "Get notified about giveaways."
            ),

            discord.ui.ActionRow(
                PingButton(
                    "Giveaway",
                    "🎁",
                    GIVEAWAY_ROLE_ID,
                    "ping_giveaway_v2",
                )
            ),

            discord.ui.Separator(
                visible=True,
                spacing=discord.SeparatorSpacing.small,
            ),

            discord.ui.TextDisplay(
                "### 📰 News\n"
                "Get notified about important server news."
            ),

            discord.ui.ActionRow(
                PingButton(
                    "News",
                    "📰",
                    NEWS_ROLE_ID,
                    "ping_news_v2",
                )
            ),

            discord.ui.Separator(
                visible=True,
                spacing=discord.SeparatorSpacing.small,
            ),

            discord.ui.ActionRow(
                RemovePingRolesButton()
            ),

            discord.ui.Separator(
                visible=True,
                spacing=discord.SeparatorSpacing.small,
            ),

            discord.ui.TextDisplay(
                "-# Click a button to enable or disable a notification role."
            ),

            accent_colour=discord.Colour.from_rgb(88, 101, 242),
        )

        self.add_item(container)


# =========================================================
# COG
# =========================================================

class Message(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # =====================================================
    # !features panel
    # =====================================================

    @commands.command(name="features")
    async def features(self, ctx, action=None):

        # Only owner can create the panel
        if ctx.author.id != OWNER_ID:
            return

        if action is None or action.lower() != "panel":
            return

        await ctx.send(
            view=FeaturesView()
        )

    # =====================================================
    # !ping panel
    # =====================================================

    @commands.command(name="ping")
    async def ping(self, ctx, action=None):

        # Only owner can create the panel
        if ctx.author.id != OWNER_ID:
            return

        if action is None or action.lower() != "panel":
            return

        await ctx.send(
            view=PingView()
        )


# =========================================================
# SETUP
# =========================================================

async def setup(bot):
    await bot.add_cog(Message(bot))
