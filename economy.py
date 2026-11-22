
import discord
from discord.ext import commands
import logging

# =========================================================
# LEGENDS ECONOMY | SEASONAL ROLE CREATOR
# Python 3.13 | discord.py 2.6+
# =========================================================

OWNER_ID = 1176149190192152626

logger = logging.getLogger("LEGENDS_ECONOMY")

# =========================================================
# SEASONAL ROLE DATABASE
# =========================================================

SEASONS = [
    {
        "name": "Valentine's Day",
        "emoji": "❤️",
        "roles": [
            ("💌・Love Letter (Level 1)", "#FFC0CB"),
            ("🌹・Rose Heart (Level 2)", "#FF91AF"),
            ("💝・Sweet Romance (Level 3)", "#FF69B4"),
            ("💗・Eternal Love (Level 4)", "#E75480"),
            ("💘・Valentine Legend (Level 5)", "#DC143C"),
            ("❤️・Valentine God (Level ∞)", "#8B003A"),
        ],
    },
    {
        "name": "New Year",
        "emoji": "🎆",
        "roles": [
            ("🎄・New Year Spark (Level 1)", "#BDE0FE"),
            ("🎁・Gift Hunter (Level 2)", "#87CEEB"),
            ("❄️・Winter Magic (Level 3)", "#4169E1"),
            ("🌟・Golden Midnight (Level 4)", "#DAA520"),
            ("🎆・New Year Legend (Level 5)", "#FFD700"),
            ("🎆・New Year God (Level ∞)", "#8B6914"),
        ],
    },
    {
        "name": "Christmas",
        "emoji": "🎄",
        "roles": [
            ("🔔・Jingle Bell (Level 1)", "#90EE90"),
            ("⛄・Snow Buddy (Level 2)", "#32CD32"),
            ("🎅・Santa's Helper (Level 3)", "#228B22"),
            ("❄️・Frost Master (Level 4)", "#C41E3A"),
            ("🎄・Christmas Legend (Level 5)", "#B22222"),
            ("🎄・Christmas God (Level ∞)", "#6B1020"),
        ],
    },
    {
        "name": "Halloween",
        "emoji": "🎃",
        "roles": [
            ("🎃・Pumpkin Soul (Level 1)", "#FF7518"),
            ("👻・Ghost Hunter (Level 2)", "#E65C00"),
            ("🦇・Dark Spirit (Level 3)", "#9932CC"),
            ("🕸️・Nightmare King (Level 4)", "#6A0DAD"),
            ("💀・Halloween Legend (Level 5)", "#4B0082"),
            ("🎃・Halloween God (Level ∞)", "#2B003F"),
        ],
    },
    {
        "name": "Easter",
        "emoji": "🐰",
        "roles": [
            ("🥚・Egg Finder (Level 1)", "#FFF0A6"),
            ("🐣・Little Chick (Level 2)", "#FFD1DC"),
            ("🌷・Spring Bloom (Level 3)", "#C8A2C8"),
            ("🐰・Bunny Spirit (Level 4)", "#A8D8B9"),
            ("💐・Easter Legend (Level 5)", "#B19CD9"),
            ("🐰・Easter God (Level ∞)", "#8055A5"),
        ],
    },
    {
        "name": "St. Patrick's Day",
        "emoji": "🍀",
        "roles": [
            ("🍀・Lucky Charm (Level 1)", "#ADFF2F"),
            ("💚・Green Clover (Level 2)", "#7CFC00"),
            ("🌈・Rainbow Hunter (Level 3)", "#32CD32"),
            ("🪙・Gold Keeper (Level 4)", "#228B22"),
            ("☘️・Lucky Legend (Level 5)", "#006400"),
            ("🍀・Luck God (Level ∞)", "#003300"),
        ],
    },
    {
        "name": "Independence Day",
        "emoji": "🎆",
        "roles": [
            ("🎇・First Spark (Level 1)", "#ADD8E6"),
            ("🗽・Freedom Soul (Level 2)", "#6495ED"),
            ("⭐・Star Guardian (Level 3)", "#4169E1"),
            ("🦅・Liberty Spirit (Level 4)", "#DC143C"),
            ("🎆・Freedom Legend (Level 5)", "#B22222"),
            ("🎆・Liberty God (Level ∞)", "#8B0000"),
        ],
    },
    {
        "name": "Summer Season",
        "emoji": "☀️",
        "roles": [
            ("🌤️・Summer Breeze (Level 1)", "#FFF176"),
            ("🏖️・Sunny Days (Level 2)", "#FFD54F"),
            ("🌊・Ocean Soul (Level 3)", "#40C4FF"),
            ("🌴・Tropical Paradise (Level 4)", "#00A6C7"),
            ("☀️・Summer Legend (Level 5)", "#008B8B"),
            ("☀️・Summer God (Level ∞)", "#006994"),
        ],
    },
    {
        "name": "Spring Season",
        "emoji": "🌸",
        "roles": [
            ("🌱・Spring Bloom (Level 1)", "#C1E1C1"),
            ("🌷・Pink Blossom (Level 2)", "#FFB6C1"),
            ("🦋・Butterfly Soul (Level 3)", "#DDA0DD"),
            ("🌺・Floral Paradise (Level 4)", "#DA70D6"),
            ("🌸・Spring Legend (Level 5)", "#DB7093"),
            ("🌸・Spring God (Level ∞)", "#8B3A62"),
        ],
    },
    {
        "name": "Autumn Season",
        "emoji": "🍂",
        "roles": [
            ("🍁・Autumn Leaf (Level 1)", "#F4A460"),
            ("🍂・Golden Fall (Level 2)", "#DEB887"),
            ("🌾・Harvest Soul (Level 3)", "#D2691E"),
            ("🦊・Forest Guardian (Level 4)", "#CD853F"),
            ("🍁・Autumn Legend (Level 5)", "#A0522D"),
            ("🍂・Autumn God (Level ∞)", "#704214"),
        ],
    },
    {
        "name": "Winter Season",
        "emoji": "❄️",
        "roles": [
            ("❄️・Snowflake (Level 1)", "#BDEBFF"),
            ("⛄・Frost Walker (Level 2)", "#87CEEB"),
            ("🧊・Ice Soul (Level 3)", "#4DB8FF"),
            ("🌨️・Frozen Spirit (Level 4)", "#2980B9"),
            ("❄️・Winter Legend (Level 5)", "#4169E1"),
            ("❄️・Winter God (Level ∞)", "#172B70"),
        ],
    },
]

TOTAL_ROLES = sum(len(season["roles"]) for season in SEASONS)


# =========================================================
# HELPERS
# =========================================================

def hex_to_color(value: str) -> discord.Color:
    return discord.Color(int(value.replace("#", ""), 16))


# =========================================================
# REPORT BUILDER
# =========================================================

def build_reports(results, created, existing, failed):

    # Four separate messages:
    # 3 seasons per message, 18 roles maximum.
    # This avoids Discord's 6000-character combined embed limit.

    chunks = [
        SEASONS[0:3],
        SEASONS[3:6],
        SEASONS[6:9],
        SEASONS[9:11],
    ]

    reports = []

    for index, chunk in enumerate(chunks):

        lines = []

        if index == 0:
            lines.extend([
                "**CREATION SUMMARY**",
                f"Total planned: `{TOTAL_ROLES}`",
                f"Created: `{created}`",
                f"Existing / updated: `{existing}`",
                f"Failed: `{failed}`",
                "",
                "━━━━━━━━━━━━━━━━━━━━",
                "",
            ])

        for season in chunk:

            lines.append(
                f"**{season['emoji']} {season['name']}**"
            )

            for role_name, hex_color in season["roles"]:

                result = results.get(role_name)

                if result is None:
                    line = (
                        f"❌ **{role_name}** "
                        f"· `{hex_color}` · Failed"
                    )
                else:
                    role, status = result

                    if status == "created":
                        status_text = "✅ Created"
                    elif status == "updated":
                        status_text = "🔄 Updated"
                    else:
                        status_text = "♻️ Existing"

                    line = (
                        f"• **{role_name}**\n"
                        f"  ID: `{role.id}` "
                        f"· Color: `{hex_color}` "
                        f"· {status_text}"
                    )

                lines.append(line)

            lines.append("")

        embed = discord.Embed(
            title=f"🎭 SEASONAL ROLES REPORT • {index + 1}/4",
            description="\n".join(lines),
            color=discord.Color.blurple(),
        )

        embed.set_footer(
            text="LEGENDS ECONOMY • System-BOT"
        )

        reports.append(embed)

    return reports


# =========================================================
# SEASONAL ROLE CREATOR
# =========================================================

async def create_seasonal_roles(guild: discord.Guild):

    results = {}

    created = 0
    existing = 0
    failed = 0

    for season in SEASONS:

        for role_name, hex_color in season["roles"]:

            try:

                role = discord.utils.get(
                    guild.roles,
                    name=role_name,
                )

                desired_color = hex_to_color(hex_color)

                if role is not None:

                    if role.managed:
                        failed += 1

                        logger.warning(
                            "Cannot edit managed role: %s",
                            role_name,
                        )
                        continue

                    if role.color != desired_color:

                        role = await role.edit(
                            colour=desired_color,
                            reason="LEGENDS ECONOMY seasonal role setup",
                        )

                        results[role_name] = (role, "updated")

                    else:
                        results[role_name] = (role, "existing")

                    existing += 1
                    continue

                role = await guild.create_role(
                    name=role_name,
                    colour=desired_color,
                    hoist=False,
                    mentionable=False,
                    reason="LEGENDS ECONOMY seasonal role setup",
                )

                results[role_name] = (role, "created")
                created += 1

            except discord.Forbidden:

                failed += 1

                logger.error(
                    "Missing permission or role hierarchy prevents processing: %s",
                    role_name,
                )

            except discord.HTTPException:

                failed += 1

                logger.exception(
                    "Discord API failed processing role: %s",
                    role_name,
                )

            except Exception:

                failed += 1

                logger.exception(
                    "Unexpected error processing role: %s",
                    role_name,
                )

    return results, created, existing, failed


# =========================================================
# PRIVATE OWNER PANEL
# =========================================================

class SeasonalRolesPanel(discord.ui.View):

    def __init__(self, guild_id: int):
        super().__init__(timeout=300)

        self.guild_id = guild_id
        self.processing = False

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:

        if interaction.user.id != OWNER_ID:

            await interaction.response.send_message(
                "❌ This panel belongs to the bot owner.",
                ephemeral=True,
            )

            return False

        return True

    @discord.ui.button(
        label="Create Seasonal Roles",
        emoji="🎭",
        style=discord.ButtonStyle.primary,
        custom_id="legends_economy_create_seasonal_roles",
    )
    async def create_roles_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        if self.processing:
            await interaction.response.send_message(
                "⏳ Seasonal role creation is already running.",
                ephemeral=True,
            )
            return

        guild = interaction.client.get_guild(self.guild_id)

        if guild is None:
            await interaction.response.send_message(
                "❌ The original server could not be found.",
                ephemeral=True,
            )
            return

        bot_member = guild.me

        if bot_member is None:
            await interaction.response.send_message(
                "❌ Bot member information is unavailable.",
                ephemeral=True,
            )
            return

        if not bot_member.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "❌ The bot needs the **Manage Roles** permission.",
                ephemeral=True,
            )
            return

        missing = sum(
            1
            for season in SEASONS
            for role_name, _ in season["roles"]
            if discord.utils.get(guild.roles, name=role_name) is None
        )

        current_roles = len(guild.roles) - 1

        if current_roles + missing > 250:
            await interaction.response.send_message(
                "❌ The server does not have enough available role slots.\n"
                f"Missing roles: `{missing}`\n"
                f"Current roles: `{current_roles}`\n"
                "Discord allows a maximum of 250 server roles.",
                ephemeral=True,
            )
            return

        self.processing = True
        button.disabled = True

        await interaction.response.defer()

        try:
            await interaction.message.edit(view=self)
        except discord.HTTPException:
            pass

        results, created, existing, failed = (
            await create_seasonal_roles(guild)
        )

        reports = build_reports(
            results,
            created,
            existing,
            failed,
        )

        sent = 0

        try:

            for embed in reports:

                await interaction.channel.send(
                    embed=embed,
                    allowed_mentions=discord.AllowedMentions.none(),
                )

                sent += 1

            logger.info(
                "Seasonal role report sent: %s/%s messages. "
                "Created=%s Existing=%s Failed=%s",
                sent,
                len(reports),
                created,
                existing,
                failed,
            )

        except discord.HTTPException:

            logger.exception(
                "Could not send seasonal role report. Sent %s/%s messages.",
                sent,
                len(reports),
            )

            await interaction.followup.send(
                "⚠️ Roles were processed, but the report could not be "
                f"fully delivered. Messages sent: `{sent}/{len(reports)}`.",
                ephemeral=True,
            )


# =========================================================
# !economy
# =========================================================

@commands.command(name="economy")
async def economy_command(ctx: commands.Context):

    if ctx.author.id != OWNER_ID:
        return

    if ctx.guild is None:
        return

    try:
        await ctx.message.delete()
    except discord.HTTPException:
        pass

    embed = discord.Embed(
        title="💰 LEGENDS ECONOMY",
        description=(
            "## 🎭 Seasonal Roles Management\n\n"
            "Welcome to the LEGENDS ECONOMY administration panel.\n\n"
            f"**Season Collections:** `{len(SEASONS)}`\n"
            f"**Total Seasonal Roles:** `{TOTAL_ROLES}`\n\n"
            "Press the button below to create all seasonal roles "
            "with their predefined names and themed HEX colors.\n\n"
            "-# Owner-only management panel."
        ),
        color=discord.Color.blurple(),
    )

    embed.set_footer(
        text="LEGENDS ECONOMY • System-BOT"
    )

    view = SeasonalRolesPanel(ctx.guild.id)

    try:

        await ctx.author.send(
            embed=embed,
            view=view,
        )

    except discord.Forbidden:

        await ctx.send(
            "❌ I couldn't send you a DM. Please enable direct messages."
        )


# =========================================================
# !commands System
# =========================================================

async def system_commands_callback(ctx: commands.Context):

    embed = discord.Embed(
        title="⚙️ SYSTEM-BOT COMMANDS",
        description=(
            "### 💰 LEGENDS ECONOMY\n\n"
            "`!economy` — Open the private economy management panel.\n\n"
            "### 🎭 SEASONAL ROLES\n\n"
            "Use the Create Seasonal Roles button inside the panel "
            "to create all 66 seasonal roles.\n\n"
            "-# LEGENDS ECONOMY • System-BOT"
        ),
        color=discord.Color.blurple(),
    )

    await ctx.send(embed=embed)


# =========================================================
# EXTENSION SETUP
# =========================================================

async def setup(bot: commands.Bot):

    bot.add_command(economy_command)

    command_group = bot.get_command("commands")

    if command_group is None:

        command_group = commands.Group(
            name="commands",
            invoke_without_command=True,
        )

        bot.add_command(command_group)

    if isinstance(command_group, commands.Group):

        if command_group.get_command("system") is None:

            system_command = commands.Command(
                system_commands_callback,
                name="system",
                help="Show System-BOT commands.",
            )

            command_group.add_command(system_command)

        else:

            logger.warning(
                "!commands system already exists. "
                "Economy command list was not registered."
            )

    else:

        logger.warning(
            "The !commands name is already used by a non-group command."
        )

    logger.info(
        "LEGENDS ECONOMY loaded: %s seasons, %s seasonal roles.",
        len(SEASONS),
        TOTAL_ROLES,
    )
