
import os
import json
import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands, tasks

# =========================================================
# CONFIGURATION
# =========================================================

OWNER_ID = 1176149190192152626
STATS_CHANNEL_ID = 1542994435472760953

DATA_FILE = "info_server_data.json"
LANGUAGE_FILE = "info_languages.json"

logger = logging.getLogger("SystemBot.Info")

LANGUAGES = {
    "en": ("🇬🇧", "English"),
    "ru": ("🇷🇺", "Русский"),
    "ro": ("🇷🇴", "Română"),
    "uz": ("🇺🇿", "O‘zbekcha"),
    "kk": ("🇰🇿", "Қазақша"),
    "tr": ("🇹🇷", "Türkçe"),
    "es": ("🇪🇸", "Español"),
    "fr": ("🇫🇷", "Français"),
    "de": ("🇩🇪", "Deutsch"),
    "it": ("🇮🇹", "Italiano"),
    "uk": ("🇺🇦", "Українська"),
    "pl": ("🇵🇱", "Polski"),
}

TEXTS = {
    "en": {
        "title": "SERVER INFORMATION",
        "description": "Select a section to explore server information.",
        "language": "Select your language",
        "language_desc": "Choose the language for your private information panel.",
        "language_saved": "Language saved!",
        "general": "General Information",
        "members": "Members & Bots",
        "channels": "Channels",
        "roles": "Roles",
        "boosts": "Server Boosts",
        "emojis": "Emojis & Stickers",
        "security": "Security",
        "settings": "Server Settings",
        "back": "Back",
        "change_language": "Change language",
        "members_total": "Total members",
        "humans": "Humans",
        "bots": "Bots",
        "online": "Online",
        "idle": "Idle",
        "dnd": "Do Not Disturb",
        "offline": "Offline",
        "text_channels": "Text channels",
        "voice_channels": "Voice channels",
        "categories": "Categories",
        "forum_channels": "Forums",
        "total_channels": "Total channels",
        "total_roles": "Total roles",
        "everyone": "Everyone role",
        "boost_level": "Boost level",
        "boost_count": "Boosts",
        "boosters": "Boosters",
        "emoji_count": "Emojis",
        "sticker_count": "Stickers",
        "animated": "Animated emojis",
        "verification": "Verification level",
        "mfa": "2FA moderation",
        "content_filter": "Content filter",
        "created": "Created",
        "owner": "Server owner",
        "region": "Preferred language",
        "max_members": "Member limit",
        "roles_page": "Roles list",
        "no_data": "No information available.",
        "private": "This panel is private. Only you can see it.",
        "not_owner": "You are not allowed to use this command.",
        "panel_created": "Server information panel has been created.",
        "panel_error": "Could not create the information panel.",
        "page": "Page",
    },
    "ru": {
        "title": "ИНФОРМАЦИЯ О СЕРВЕРЕ",
        "description": "Выберите раздел, чтобы посмотреть информацию о сервере.",
        "language": "Выберите язык",
        "language_desc": "Выберите язык для своей личной панели информации.",
        "language_saved": "Язык сохранён!",
        "general": "Общая информация",
        "members": "Участники и боты",
        "channels": "Каналы",
        "roles": "Роли",
        "boosts": "Бусты сервера",
        "emojis": "Эмодзи и стикеры",
        "security": "Безопасность",
        "settings": "Настройки сервера",
        "back": "Назад",
        "change_language": "Изменить язык",
        "members_total": "Всего участников",
        "humans": "Люди",
        "bots": "Боты",
        "online": "В сети",
        "idle": "Не активны",
        "dnd": "Не беспокоить",
        "offline": "Не в сети",
        "text_channels": "Текстовые каналы",
        "voice_channels": "Голосовые каналы",
        "categories": "Категории",
        "forum_channels": "Форумы",
        "total_channels": "Всего каналов",
        "total_roles": "Всего ролей",
        "everyone": "Роль Everyone",
        "boost_level": "Уровень бустов",
        "boost_count": "Бусты",
        "boosters": "Бустеры",
        "emoji_count": "Эмодзи",
        "sticker_count": "Стикеры",
        "animated": "Анимированные эмодзи",
        "verification": "Уровень проверки",
        "mfa": "2FA для модерации",
        "content_filter": "Фильтр контента",
        "created": "Создан",
        "owner": "Владелец сервера",
        "region": "Язык сервера",
        "max_members": "Лимит участников",
        "roles_page": "Список ролей",
        "no_data": "Информация отсутствует.",
        "private": "Эта панель приватная. Её видишь только ты.",
        "not_owner": "У тебя нет доступа к этой команде.",
        "panel_created": "Панель информации о сервере создана.",
        "panel_error": "Не удалось создать панель информации.",
        "page": "Страница",
    },
}

# Для остальных языков интерфейс пока использует английские подписи.
# Словари можно расширять без изменения логики системы.
for language in LANGUAGES:
    if language not in TEXTS:
        TEXTS[language] = TEXTS["en"]


def load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
    except Exception:
        logger.exception("Could not read %s", path)
    return default


def save_json(path, data):
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    os.replace(temporary, path)


def get_text(language, key):
    return TEXTS.get(language, TEXTS["en"]).get(
        key, TEXTS["en"].get(key, key)
    )


def is_separator_role(role):
    name = role.name.strip()
    if not name:
        return True

    allowed = set(" -_│┃|•・─━═＝=⋆★☆◆◇")
    return all(character in allowed for character in name)


def format_date(value):
    return discord.utils.format_dt(value, style="F")


# =========================================================
# PUBLIC PANEL
# =========================================================

class PublicInfoView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

        buttons = [
            ("📊", "general"),
            ("👥", "members"),
            ("📁", "channels"),
            ("🎭", "roles"),
            ("🚀", "boosts"),
            ("😀", "emojis"),
            ("🔐", "security"),
            ("⚙️", "settings"),
        ]

        for emoji, section in buttons:
            button = discord.ui.Button(
                emoji=emoji,
                style=discord.ButtonStyle.secondary,
                custom_id=f"info_server:{section}",
                row=len(self.children) // 4,
            )

            async def callback(interaction, selected=section):
                await self.cog.open_section(interaction, selected)

            button.callback = callback
            self.add_item(button)


# =========================================================
# LANGUAGE SELECTOR
# =========================================================

class LanguageSelect(discord.ui.Select):
    def __init__(self, cog, user_id):
        self.cog = cog
        self.user_id = user_id

        options = [
            discord.SelectOption(
                label=name,
                value=code,
                emoji=emoji
            )
            for code, (emoji, name) in LANGUAGES.items()
        ]

        super().__init__(
            placeholder="🌐 Select your language / Выберите язык",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="info_language_select"
        )

    async def callback(self, interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This menu belongs to another user.",
                ephemeral=True
            )
            return

        language = self.values[0]
        self.cog.languages[str(self.user_id)] = language
        self.cog.save_languages()

        await interaction.response.edit_message(
            content=get_text(language, "language_saved"),
            embed=self.cog.build_menu_embed(language),
            view=PrivateInfoView(self.cog, self.user_id, language)
        )


class LanguageView(discord.ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=300)
        self.add_item(LanguageSelect(cog, user_id))


# =========================================================
# PRIVATE INFORMATION MENU
# =========================================================

class PrivateInfoView(discord.ui.View):
    def __init__(self, cog, user_id, language):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id
        self.language = language

        buttons = [
            ("📊", "general"),
            ("👥", "members"),
            ("📁", "channels"),
            ("🎭", "roles"),
            ("🚀", "boosts"),
            ("😀", "emojis"),
            ("🔐", "security"),
            ("⚙️", "settings"),
        ]

        for emoji, section in buttons:
            button = discord.ui.Button(
                emoji=emoji,
                label=get_text(language, section),
                style=discord.ButtonStyle.secondary,
                row=len(self.children) // 2,
            )

            async def callback(interaction, selected=section):
                if interaction.user.id != self.user_id:
                    await interaction.response.send_message(
                        "This panel belongs to another user.",
                        ephemeral=True
                    )
                    return

                await interaction.response.edit_message(
                    embed=self.cog.build_section_embed(
                        interaction.guild,
                        selected,
                        self.language
                    ),
                    view=SectionBackView(
                        self.cog,
                        self.user_id,
                        self.language
                    )
                )

            button.callback = callback
            self.add_item(button)

        language_button = discord.ui.Button(
            label="🌐 " + get_text(language, "change_language"),
            style=discord.ButtonStyle.primary,
            row=4
        )

        async def change_language(interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message(
                    "This panel belongs to another user.",
                    ephemeral=True
                )
                return

            await interaction.response.edit_message(
                content="🌐 Select your language / Выберите язык",
                embed=None,
                view=LanguageView(self.cog, self.user_id)
            )

        language_button.callback = change_language
        self.add_item(language_button)


class SectionBackView(discord.ui.View):
    def __init__(self, cog, user_id, language):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id
        self.language = language

        back = discord.ui.Button(
            label="⬅️ " + get_text(language, "back"),
            style=discord.ButtonStyle.secondary
        )

        async def callback(interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message(
                    "This panel belongs to another user.",
                    ephemeral=True
                )
                return

            await interaction.response.edit_message(
                content=get_text(language, "private"),
                embed=cog.build_menu_embed(language),
                view=PrivateInfoView(cog, user_id, language)
            )

        back.callback = callback
        self.add_item(back)


# =========================================================
# INFORMATION COG
# =========================================================

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_json(DATA_FILE, {})
        self.languages = load_json(LANGUAGE_FILE, {})

        self.public_view = PublicInfoView(self)
        self.bot.add_view(self.public_view)

        self.update_panel.start()

    def cog_unload(self):
        self.update_panel.cancel()

    def save_data(self):
        save_json(DATA_FILE, self.data)

    def save_languages(self):
        save_json(LANGUAGE_FILE, self.languages)

    # -----------------------------------------------------
    # EMBEDS
    # -----------------------------------------------------

    def build_menu_embed(self, language):
        embed = discord.Embed(
            title="🌐 " + get_text(language, "title"),
            description=(
                get_text(language, "description")
                + "\n\n"
                + get_text(language, "private")
            ),
            color=0x5865F2
        )
        embed.set_footer(text="LEGENDS • System-BOT")
        return embed

    def build_public_embed(self, guild):
        embed = discord.Embed(
            title="📊 SERVER INFORMATION",
            description=(
                f"**{guild.name}**\n"
                "Select an emoji button to open server information.\n\n"
                "🌐 On your first visit, choose your language."
            ),
            color=0x5865F2,
            timestamp=datetime.now(timezone.utc)
        )

        embed.add_field(
            name="👥 Members",
            value=f"{guild.member_count:,}",
            inline=True
        )
        embed.add_field(
            name="🎭 Roles",
            value=f"{len(guild.roles):,}",
            inline=True
        )
        embed.add_field(
            name="📁 Channels",
            value=f"{len(guild.channels):,}",
            inline=True
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.set_footer(text="LEGENDS • Automatically updated")
        return embed

    def build_section_embed(self, guild, section, language):
        t = lambda key: get_text(language, key)

        embed = discord.Embed(
            title=t(section),
            color=0x5865F2,
            timestamp=datetime.now(timezone.utc)
        )

        if section == "general":
            embed.add_field(name=t("owner"), value=guild.owner.mention if guild.owner else "Unknown", inline=True)
            embed.add_field(name=t("created"), value=format_date(guild.created_at), inline=False)
            embed.add_field(name=t("region"), value=str(guild.preferred_locale), inline=True)
            embed.add_field(name=t("max_members"), value=str(guild.max_members), inline=True)

        elif section == "members":
            members = guild.members
            humans = sum(not member.bot for member in members)
            bots = sum(member.bot for member in members)

            statuses = {
                "online": sum(member.status == discord.Status.online for member in members),
                "idle": sum(member.status == discord.Status.idle for member in members),
                "dnd": sum(member.status == discord.Status.dnd for member in members),
                "offline": sum(member.status == discord.Status.offline for member in members),
            }

            embed.add_field(name=t("members_total"), value=str(guild.member_count), inline=True)
            embed.add_field(name=t("humans"), value=str(humans), inline=True)
            embed.add_field(name=t("bots"), value=str(bots), inline=True)

            for key, amount in statuses.items():
                embed.add_field(name=t(key), value=str(amount), inline=True)

        elif section == "channels":
            channels = guild.channels
            embed.add_field(name=t("total_channels"), value=str(len(channels)), inline=True)
            embed.add_field(name=t("text_channels"), value=str(len(guild.text_channels)), inline=True)
            embed.add_field(name=t("voice_channels"), value=str(len(guild.voice_channels)), inline=True)
            embed.add_field(name=t("categories"), value=str(len(guild.categories)), inline=True)
            embed.add_field(
                name=t("forum_channels"),
                value=str(len(guild.forums)),
                inline=True
            )

        elif section == "roles":
            roles = [
                role for role in guild.roles
                if not role.is_default() and not is_separator_role(role)
            ]

            embed.add_field(
                name=t("total_roles"),
                value=str(len(roles)),
                inline=False
            )

            shown = roles[:25]
            if shown:
                embed.add_field(
                    name=t("roles_page"),
                    value="\n".join(
                        f"{role.mention} — {len(role.members)}"
                        for role in shown
                    ),
                    inline=False
                )

            if len(roles) > 25:
                embed.set_footer(
                    text=f"{t('page')} 1 • Showing 25 of {len(roles)} roles"
                )

        elif section == "boosts":
            embed.add_field(name=t("boost_level"), value=str(guild.premium_tier), inline=True)
            embed.add_field(name=t("boost_count"), value=str(guild.premium_subscription_count), inline=True)

            boosters = sum(
                member.premium_since is not None
                for member in guild.members
            )
            embed.add_field(name=t("boosters"), value=str(boosters), inline=True)

        elif section == "emojis":
            animated = sum(emoji.animated for emoji in guild.emojis)
            embed.add_field(name=t("emoji_count"), value=str(len(guild.emojis)), inline=True)
            embed.add_field(name=t("animated"), value=str(animated), inline=True)
            embed.add_field(name=t("sticker_count"), value=str(len(guild.stickers)), inline=True)

        elif section == "security":
            embed.add_field(
                name=t("verification"),
                value=str(guild.verification_level).replace("_", " ").title(),
                inline=True
            )
            embed.add_field(
                name=t("mfa"),
                value="Enabled" if guild.mfa_level else "Disabled",
                inline=True
            )
            embed.add_field(
                name=t("content_filter"),
                value=str(guild.explicit_content_filter).replace("_", " ").title(),
                inline=False
            )

        elif section == "settings":
            embed.add_field(name="Server ID", value=str(guild.id), inline=False)
            embed.add_field(name="Default notifications", value=str(guild.default_notifications).replace("_", " ").title(), inline=True)
            embed.add_field(name="System channel", value=guild.system_channel.mention if guild.system_channel else "Not set", inline=True)
            embed.add_field(name="AFK channel", value=guild.afk_channel.mention if guild.afk_channel else "Not set", inline=True)
            embed.add_field(name="AFK timeout", value=f"{guild.afk_timeout} seconds", inline=True)
            embed.add_field(name="Filesize limit", value=f"{guild.filesize_limit:,} bytes", inline=True)

        embed.set_footer(text="LEGENDS • System-BOT")
        return embed

    # -----------------------------------------------------
    # OPEN PRIVATE PANELS
    # -----------------------------------------------------

    async def open_section(self, interaction, section):
        language = self.languages.get(str(interaction.user.id))

        if not language:
            await interaction.response.send_message(
                content="🌐 Select your language / Выберите язык",
                view=LanguageView(self, interaction.user.id),
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            content=get_text(language, "private"),
            embed=self.build_section_embed(
                interaction.guild,
                section,
                language
            ),
            view=SectionBackView(
                self,
                interaction.user.id,
                language
            ),
            ephemeral=True
        )

    # -----------------------------------------------------
    # OWNER COMMAND
    # -----------------------------------------------------

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.content.strip().lower() != "!info server":
            return

        if message.author.id != OWNER_ID:
            await message.reply(
                "You are not allowed to use this command.",
                delete_after=5
            )
            return

        await message.delete()

        channel = self.bot.get_channel(STATS_CHANNEL_ID)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(STATS_CHANNEL_ID)
            except Exception:
                logger.exception("Stats channel not found")
                return

        if not isinstance(channel, discord.TextChannel):
            return

        guild = channel.guild

        try:
            message_id = self.data.get("message_id")

            if message_id:
                try:
                    old_message = await channel.fetch_message(message_id)
                    await old_message.delete()
                except discord.NotFound:
                    pass
                except discord.Forbidden:
                    pass

            panel = await channel.send(
                embed=self.build_public_embed(guild),
                view=self.public_view
            )

            self.data = {
                "message_id": panel.id,
                "channel_id": channel.id,
                "guild_id": guild.id
            }
            self.save_data()

            try:
                await message.author.send(
                    get_text(
                        self.languages.get(str(message.author.id), "en"),
                        "panel_created"
                    )
                )
            except discord.Forbidden:
                pass

        except Exception:
            logger.exception("Could not create information panel")

    # -----------------------------------------------------
    # AUTOMATIC UPDATE
    # -----------------------------------------------------

    @tasks.loop(minutes=1)
    async def update_panel(self):
        message_id = self.data.get("message_id")
        channel_id = self.data.get("channel_id")

        if not message_id or not channel_id:
            return

        channel = self.bot.get_channel(channel_id)
        if channel is None:
            return

        guild = channel.guild

        try:
            panel = await channel.fetch_message(message_id)
            await panel.edit(
                embed=self.build_public_embed(guild),
                view=self.public_view
            )
        except discord.NotFound:
            self.data = {}
            self.save_data()
        except discord.Forbidden:
            logger.warning("Missing permissions to update info panel")
        except Exception:
            logger.exception("Info panel update failed")

    @update_panel.before_loop
    async def before_update_panel(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Info(bot))
