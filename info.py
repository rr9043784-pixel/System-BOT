import os
import json
import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands

# =========================================================
# SYSTEM-BOT | INFO SERVER
# Python 3.13 | discord.py 2.6+
# =========================================================

OWNER_ID = 1176149190192152626
LANGUAGE_FILE = "info_languages.json"
logger = logging.getLogger("SystemBot.Info")

LANGUAGES = {
    "en": ("🇬🇧", "English"),
    "ru": ("🇷🇺", "Russian"),
    "ro": ("🇷🇴", "Romanian"),
    "uz": ("🇺🇿", "Uzbek"),
    "kk": ("🇰🇿", "Kazakh"),
    "tr": ("🇹🇷", "Turkish"),
    "es": ("🇪🇸", "Spanish"),
    "fr": ("🇫🇷", "French"),
    "de": ("🇩🇪", "German"),
    "it": ("🇮🇹", "Italian"),
    "uk": ("🇺🇦", "Ukrainian"),
    "pl": ("🇵🇱", "Polish"),
}

# UI labels are translated for all 12 choices.
# Role descriptions below preserve the wording supplied for the server.
T = {
    "en": ["SELECT YOUR LANGUAGE", "Choose your preferred language to continue.",
           "SERVER INFORMATION", "Welcome to the LEGENDS server information center.",
           "General information", "Members & bots", "Channels", "Roles",
           "Server boosts", "Emojis & stickers", "Security", "Server settings",
           "Change language", "Back", "Previous page", "Next page", "Page"],
    "ru": ["ВЫБЕРИТЕ ЯЗЫК", "Выберите язык, чтобы продолжить.",
           "ИНФОРМАЦИЯ О СЕРВЕРЕ", "Добро пожаловать в информационный центр LEGENDS.",
           "Общая информация", "Участники и боты", "Каналы", "Роли",
           "Бусты сервера", "Эмодзи и стикеры", "Безопасность", "Настройки сервера",
           "Изменить язык", "Назад", "Предыдущая страница", "Следующая страница", "Страница"],
    "ro": ["SELECTAȚI LIMBA", "Alegeți limba preferată pentru a continua.",
           "INFORMAȚII DESPRE SERVER", "Bun venit în centrul de informații LEGENDS.",
           "Informații generale", "Membri și boți", "Canale", "Roluri",
           "Boosturi server", "Emoji și stickere", "Securitate", "Setări server",
           "Schimbă limba", "Înapoi", "Pagina anterioară", "Pagina următoare", "Pagina"],
    "uz": ["TILNI TANLANG", "Davom etish uchun tilni tanlang.",
           "SERVER MA’LUMOTLARI", "LEGENDS server ma’lumot markaziga xush kelibsiz.",
           "Umumiy ma’lumot", "A’zolar va botlar", "Kanallar", "Rollar",
           "Server boostlari", "Emoji va stikerlar", "Xavfsizlik", "Server sozlamalari",
           "Tilni o‘zgartirish", "Orqaga", "Oldingi sahifa", "Keyingi sahifa", "Sahifa"],
    "kk": ["ТІЛДІ ТАҢДАҢЫЗ", "Жалғастыру үшін тілді таңдаңыз.",
           "СЕРВЕР ТУРАЛЫ АҚПАРАТ", "LEGENDS ақпарат орталығына қош келдіңіз.",
           "Жалпы ақпарат", "Қатысушылар мен боттар", "Арналар", "Рөлдер",
           "Сервер бусттары", "Эмодзи мен стикерлер", "Қауіпсіздік", "Сервер баптаулары",
           "Тілді өзгерту", "Артқа", "Алдыңғы бет", "Келесі бет", "Бет"],
    "tr": ["DİLİNİZİ SEÇİN", "Devam etmek için tercih ettiğiniz dili seçin.",
           "SUNUCU BİLGİLERİ", "LEGENDS sunucu bilgi merkezine hoş geldiniz.",
           "Genel bilgiler", "Üyeler ve botlar", "Kanallar", "Roller",
           "Sunucu takviyeleri", "Emojiler ve çıkartmalar", "Güvenlik", "Sunucu ayarları",
           "Dili değiştir", "Geri", "Önceki sayfa", "Sonraki sayfa", "Sayfa"],
    "es": ["SELECCIONA TU IDIOMA", "Elige tu idioma preferido para continuar.",
           "INFORMACIÓN DEL SERVIDOR", "Bienvenido al centro de información de LEGENDS.",
           "Información general", "Miembros y bots", "Canales", "Roles",
           "Mejoras del servidor", "Emojis y stickers", "Seguridad", "Ajustes del servidor",
           "Cambiar idioma", "Atrás", "Página anterior", "Página siguiente", "Página"],
    "fr": ["CHOISISSEZ VOTRE LANGUE", "Choisissez votre langue préférée pour continuer.",
           "INFORMATIONS DU SERVEUR", "Bienvenue dans le centre d’information LEGENDS.",
           "Informations générales", "Membres et bots", "Salons", "Rôles",
           "Boosts du serveur", "Emojis et autocollants", "Sécurité", "Paramètres du serveur",
           "Changer de langue", "Retour", "Page précédente", "Page suivante", "Page"],
    "de": ["SPRACHE AUSWÄHLEN", "Wähle deine bevorzugte Sprache, um fortzufahren.",
           "SERVERINFORMATIONEN", "Willkommen im LEGENDS-Informationszentrum.",
           "Allgemeine Informationen", "Mitglieder & Bots", "Kanäle", "Rollen",
           "Server-Boosts", "Emojis & Sticker", "Sicherheit", "Servereinstellungen",
           "Sprache ändern", "Zurück", "Vorherige Seite", "Nächste Seite", "Seite"],
    "it": ["SELEZIONA LA LINGUA", "Scegli la lingua preferita per continuare.",
           "INFORMAZIONI DEL SERVER", "Benvenuto nel centro informazioni LEGENDS.",
           "Informazioni generali", "Membri e bot", "Canali", "Ruoli",
           "Boost del server", "Emoji e adesivi", "Sicurezza", "Impostazioni server",
           "Cambia lingua", "Indietro", "Pagina precedente", "Pagina successiva", "Pagina"],
    "uk": ["ОБЕРІТЬ МОВУ", "Оберіть бажану мову, щоб продовжити.",
           "ІНФОРМАЦІЯ ПРО СЕРВЕР", "Ласкаво просимо до інформаційного центру LEGENDS.",
           "Загальна інформація", "Учасники та боти", "Канали", "Ролі",
           "Буст серверу", "Емодзі та стікери", "Безпека", "Налаштування серверу",
           "Змінити мову", "Назад", "Попередня сторінка", "Наступна сторінка", "Сторінка"],
    "pl": ["WYBIERZ JĘZYK", "Wybierz preferowany język, aby kontynuować.",
           "INFORMACJE O SERWERZE", "Witamy w centrum informacji LEGENDS.",
           "Informacje ogólne", "Użytkownicy i boty", "Kanały", "Role",
           "Ulepszenia serwera", "Emoji i naklejki", "Bezpieczeństwo", "Ustawienia serwera",
           "Zmień język", "Wstecz", "Poprzednia strona", "Następna strona", "Strona"],
}

SECTION_EMOJIS = ["📊", "👥", "📁", "🎭", "🚀", "😀", "🔐", "⚙️"]
SECTION_KEYS = ["general", "members", "channels", "roles", "boosts", "emojis", "security", "settings"]


def load_languages():
    try:
        with open(LANGUAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def save_languages(data):
    temp = LANGUAGE_FILE + ".tmp"
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(temp, LANGUAGE_FILE)


def tr(lang, index):
    return T.get(lang, T["en"])[index]


def role_is_separator(role):
    name = role.name.strip()
    if not name:
        return True
    separators = set(" -_│┃|•・─━═＝=⋆★☆◆◇")
    return all(char in separators for char in name)


# Each entry: (role ID or None, accepted exact names, description)
ROLE_GROUPS = {
    "🤖 SYSTEM┃| SERVER": [
        (None, ["System┃| BOT"], "Main server bot."),
        (None, ["System2┃| BOT"], "Second main server bot."),
        (None, ["Stumble Guys┃| BOT"], "Server gaming bot. Game: Stumble Guys."),
        (None, ["LuckyPrize┃| BOT"], "Friend's bot. Friend: <@1190322918048149595>. Bot owner: <@1176149190192152626>."),
    ],
    "👑 ОСНОВНЫЕ РОЛИ": [
        (None, ["Verified"], "You receive this role after completing server verification."),
        (None, ["ВЛАДЕЛЕЦ／OWNER", "ВЛАДЕЛЕЦ/OWNER"], "Server owner: <@1176149190192152626>."),
        (None, ["Помощник／Assistant", "Помощник/Assistant"], "Owner's assistant."),
        (None, ["Ведущий Турниров／Host Tournaments", "Ведущий Турниров/Host Tournaments"], "Hosts tournaments for the game Stumble Guys."),
        (None, ["Модератор／Moderator", "Модератор/Moderator"], "Server moderator. Keeps the server orderly."),
        (None, ["МЕНЕДЖЕР ПОДДЕРЖКИ／SUPPORT MANAGER", "МЕНЕДЖЕР ПОДДЕРЖКИ/SUPPORT MANAGER"], "Helps members who need assistance."),
        (None, ["ТЕСТЕР／TESTER", "ТЕСТЕР/TESTER"], "Tests new server systems before release."),
        (None, ["ЮТУБЕР／YOUTUBER", "ЮТУБЕР/YOUTUBER"], "Available only from 1,000 subscribers. Contact support: <#1527278068526219305>."),
        (None, ["УЧАСТНИК／MEMBER", "УЧАСТНИК/MEMBER"], "Automatically assigned to all members."),
    ],
    "🎮 ПЛАТФОРМА": [
        (None, ["▣ ┃PC", "▣┃PC"], "For playing on a computer or laptop."),
        (None, ["▯┃Mobile", "▯ ┃Mobile"], "For playing on a phone."),
        (None, ["▱┃Tablet", "▱ ┃Tablet"], "For playing on a tablet."),
        (None, ["◇ ┃Xbox", "◇┃Xbox"], "For playing on Xbox."),
        (None, ["◈ ┃PlayStation", "◈┃PlayStation"], "For playing on PlayStation."),
        (None, ["⬡ ┃Nintendo Switch", "⬡┃Nintendo Switch"], "For playing on Nintendo Switch."),
    ],
    "🎨 ЦВЕТНЫЕ НИКИ": [
        (None, ["Чёрный／Black", "Чёрный/Black"], "Black nickname."),
        (None, ["Синий／Blue", "Синий/Blue"], "Blue nickname."),
        (None, ["Фиолетовый／Purple", "Фиолетовый/Purple"], "Purple nickname."),
        (None, ["Розовый／Pink", "Розовый/Pink"], "Pink nickname."),
        (None, ["Ярко Зелёный／Bright Green", "Ярко Зелёный/Bright Green"], "Bright green nickname."),
    ],
    "⭐ РОЛЬ ЗА УРОВЕНЬ": [
        (1527640074986983555, [], "Requires level 5."),
        (1527640434082316459, [], "Requires level 10."),
        (1527640780112527512, [], "Requires level 15."),
        (1527641087047372931, [], "Requires level 20."),
        (1527641260574376037, [], "Requires level 25."),
        (1527642018250096670, [], "Requires level 30."),
        (1527642367329439947, [], "Requires level 35."),
        (1527643045032628254, [], "Requires level 40."),
        (1527643250163454052, [], "Requires level 45."),
        (1527643560113868861, [], "Requires level 50."),
    ],
    "🎁 CHEST": [
        (None, ["Phoenix 2／2", "Phoenix 2/2"], "This role can only drop from a chest."),
        (None, ["Ultra"], "This role can only drop from a chest."),
        (None, ["Галактическая／Galactic", "Галактическая/Galactic"], "This role can only drop from a chest."),
        (None, ["Космическая／Cosmic", "Космическая/Cosmic"], "This role can only drop from a chest."),
        (None, ["Легендарная／Legendary", "Легендарная/Legendary"], "This role can only drop from a chest."),
        (None, ["Героическая／Heroic", "Героическая/Heroic"], "This role can only drop from a chest."),
        (None, ["Мифическая／Mythic", "Мифическая/Mythic"], "This role can only drop from a chest."),
        (None, ["Эпическая／Epic", "Эпическая/Epic"], "This role can only drop from a chest."),
        (None, ["Редкая／Rare", "Редкая/Rare"], "This role can only drop from a chest."),
        (None, ["Необычная／Uncommon", "Необычная/Uncommon"], "This role can only drop from a chest."),
        (None, ["Обычная／Common", "Обычная/Common"], "This role can only drop from a chest."),
    ],
    "💎 EXCLUSIVE": [
        (None, ["💎 ЛЕГЕНДА／LEGEND 💎", "💎 ЛЕГЕНДА/LEGEND 💎"], "Available only during events."),
    ],
    "🌐 LANGUAGE": [
        (None, ["Russian"], "Can be obtained in <#1541336807508017252>."),
        (None, ["English"], "Can be obtained in <#1541336807508017252>."),
    ],
    "🔔 PING ROLES": [
        (1541715251018465351, [], "Can be obtained in <#1541718209533575228>."),
        (1541715118872731768, [], "Can be obtained in <#1541718209533575228>."),
        (1541716902752157798, [], "Can be obtained in <#1541718209533575228>."),
        (1541715546356060200, [], "Can be obtained in <#1541718209533575228>."),
    ],
}

ROLE_CATEGORY_KEYS = list(ROLE_GROUPS.keys())


class V2View(discord.ui.LayoutView):
    """Base helper for Discord Components V2 layouts."""

    def __init__(self, timeout=300):
        super().__init__(timeout=timeout)

    def panel(self, *components):
        self.add_item(discord.ui.Container(
            *components,
            accent_colour=discord.Colour.from_rgb(88, 101, 242)
        ))


class LanguageSelect(discord.ui.Select):
    def __init__(self, cog):
        self.cog = cog
        options = [
            discord.SelectOption(label=name, value=code, emoji=emoji)
            for code, (emoji, name) in LANGUAGES.items()
        ]
        super().__init__(
            placeholder="Select your language",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="info_server_language"
        )

    async def callback(self, interaction: discord.Interaction):
        lang = self.values[0]
        self.cog.languages[str(interaction.user.id)] = lang
        save_languages(self.cog.languages)

        await interaction.response.send_message(
            view=MainInfoView(self.cog, interaction.guild, interaction.user.id, lang),
            ephemeral=True
        )


class PublicLanguageView(V2View):
    def __init__(self, cog):
        super().__init__(timeout=600)
        self.panel(
            discord.ui.TextDisplay("## 🌐 SELECT YOUR LANGUAGE"),
            discord.ui.TextDisplay("Choose your preferred language to continue."),
            discord.ui.Separator(),
            discord.ui.ActionRow(LanguageSelect(cog))
        )


class MainInfoView(V2View):
    def __init__(self, cog, guild, user_id, lang):
        super().__init__(timeout=600)
        self.cog, self.guild, self.user_id, self.lang = cog, guild, user_id, lang

        rows = []
        for start in (0, 4):
            buttons = []
            for i in range(start, start + 4):
                button = discord.ui.Button(
                    emoji=SECTION_EMOJIS[i],
                    label=tr(lang, 4 + i),
                    style=discord.ButtonStyle.secondary,
                    custom_id=f"info_private_{i}_{user_id}"
                )

                async def callback(interaction, index=i):
                    if interaction.user.id != self.user_id:
                        return await interaction.response.send_message(
                            "This private panel belongs to another user.",
                            ephemeral=True
                        )
                    await interaction.response.edit_message(
                        view=SectionView(self.cog, self.guild, self.user_id, self.lang, index, 0)
                    )

                button.callback = callback
                buttons.append(button)
            rows.append(discord.ui.ActionRow(*buttons))

        language_button = discord.ui.Button(
            label="🌐 " + tr(lang, 12),
            style=discord.ButtonStyle.primary,
            custom_id=f"info_change_language_{user_id}"
        )

        async def change_language(interaction):
            if interaction.user.id != self.user_id:
                return await interaction.response.send_message(
                    "This private panel belongs to another user.", ephemeral=True
                )
            await interaction.response.send_message(
                view=LanguageChangeView(self.cog, self.guild, self.user_id),
                ephemeral=True
            )

        language_button.callback = change_language

        self.panel(
            discord.ui.TextDisplay(f"## 📚 {tr(lang, 2)}"),
            discord.ui.TextDisplay(tr(lang, 3)),
            discord.ui.Separator(),
            discord.ui.TextDisplay(
                "\n".join(
                    f"{SECTION_EMOJIS[i]} — {tr(lang, 4 + i)}"
                    for i in range(8)
                )
            ),
            discord.ui.Separator(),
            *rows,
            discord.ui.ActionRow(language_button)
        )


class LanguageChangeView(V2View):
    def __init__(self, cog, guild, user_id):
        super().__init__(timeout=300)
        self.panel(
            discord.ui.TextDisplay("## 🌐 SELECT YOUR LANGUAGE"),
            discord.ui.TextDisplay("Choose your preferred language."),
            discord.ui.Separator(),
            discord.ui.ActionRow(LanguageSelectForPrivate(cog, guild, user_id))
        )


class LanguageSelectForPrivate(discord.ui.Select):
    def __init__(self, cog, guild, user_id):
        self.cog, self.guild, self.user_id = cog, guild, user_id
        options = [
            discord.SelectOption(label=name, value=code, emoji=emoji)
            for code, (emoji, name) in LANGUAGES.items()
        ]
        super().__init__(
            placeholder="Select your language",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "This private panel belongs to another user.", ephemeral=True
            )
        lang = self.values[0]
        self.cog.languages[str(self.user_id)] = lang
        save_languages(self.cog.languages)
        await interaction.response.edit_message(
            view=MainInfoView(self.cog, self.guild, self.user_id, lang)
        )


class RoleCategorySelect(discord.ui.Select):
    def __init__(self, view):
        self.parent_view = view
        options = [
            discord.SelectOption(label=key[:100], value=str(i), emoji=key.split()[0])
            for i, key in enumerate(ROLE_CATEGORY_KEYS)
        ]
        super().__init__(
            placeholder="Choose a role category",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction):
        if interaction.user.id != self.parent_view.user_id:
            return await interaction.response.send_message(
                "This private panel belongs to another user.", ephemeral=True
            )
        self.parent_view.category_index = int(self.values[0])
        self.parent_view.page = 0
        await interaction.response.edit_message(
            view=SectionView(
                self.parent_view.cog,
                self.parent_view.guild,
                self.parent_view.user_id,
                self.parent_view.lang,
                3,
                0,
                self.parent_view.category_index
            )
        )


class SectionView(V2View):
    def __init__(self, cog, guild, user_id, lang, section_index, page=0, category_index=0):
        super().__init__(timeout=600)
        self.cog, self.guild, self.user_id, self.lang = cog, guild, user_id, lang
        self.section_index, self.page, self.category_index = section_index, page, category_index
        title = tr(lang, 4 + section_index)
        body = self.build_body()

        controls = []
        if section_index == 3:
            controls.append(discord.ui.ActionRow(RoleCategorySelect(self)))

        nav = []
        if page > 0:
            previous = discord.ui.Button(label="⬅️ " + tr(lang, 14), style=discord.ButtonStyle.secondary)
            async def prev_callback(interaction):
                await self.change_page(interaction, page - 1)
            previous.callback = prev_callback
            nav.append(previous)

        if self.has_next_page():
            nxt = discord.ui.Button(label=tr(lang, 15) + " ➡️", style=discord.ButtonStyle.secondary)
            async def next_callback(interaction):
                await self.change_page(interaction, page + 1)
            nxt.callback = next_callback
            nav.append(nxt)

        back = discord.ui.Button(label="↩️ " + tr(lang, 13), style=discord.ButtonStyle.primary)
        async def back_callback(interaction):
            if interaction.user.id != self.user_id:
                return await interaction.response.send_message(
                    "This private panel belongs to another user.", ephemeral=True
                )
            await interaction.response.edit_message(
                view=MainInfoView(cog, guild, user_id, lang)
            )
        back.callback = back_callback
        nav.append(back)
        if nav:
            controls.append(discord.ui.ActionRow(*nav))

        self.panel(
            discord.ui.TextDisplay(f"## {SECTION_EMOJIS[section_index]} {title}"),
            discord.ui.Separator(),
            discord.ui.TextDisplay(body),
            discord.ui.Separator(),
            *controls
        )

    async def change_page(self, interaction, new_page):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "This private panel belongs to another user.", ephemeral=True
            )
        await interaction.response.edit_message(
            view=SectionView(
                self.cog, self.guild, self.user_id, self.lang,
                self.section_index, new_page, self.category_index
            )
        )

    def has_next_page(self):
        if self.section_index == 3:
            entries = self.get_role_entries()
            return (self.page + 1) * 8 < len(entries)
        if self.section_index == 2:
            return False
        return False

    def get_role_entries(self):
        category = ROLE_CATEGORY_KEYS[self.category_index]
        entries = []
        for role_id, names, description in ROLE_GROUPS[category]:
            role = self.guild.get_role(role_id) if role_id else None
            if role is None and names:
                role = discord.utils.find(
                    lambda r: r.name in names,
                    self.guild.roles
                )
            if role is None or role_is_separator(role):
                continue
            entries.append((role, description))
        return entries

    def build_body(self):
        guild = self.guild
        if guild is None:
            return "Server information is unavailable."

        if self.section_index == 0:
            owner = guild.owner.mention if guild.owner else "Unknown"
            return (
                f"**Server:** {guild.name}\n"
                f"**Server ID:** `{guild.id}`\n"
                f"**Owner:** {owner}\n"
                f"**Created:** <t:{int(guild.created_at.timestamp())}:F>\n"
                f"**Members:** {guild.member_count:,}\n"
                f"**Roles:** {len(guild.roles):,}\n"
                f"**Channels:** {len(guild.channels):,}"
            )

        if self.section_index == 1:
            members = guild.members
            humans = sum(not m.bot for m in members)
            bots = sum(m.bot for m in members)
            online = sum(m.status == discord.Status.online for m in members)
            idle = sum(m.status == discord.Status.idle for m in members)
            dnd = sum(m.status == discord.Status.dnd for m in members)
            offline = sum(m.status == discord.Status.offline for m in members)
            return (
                f"**Total members:** {guild.member_count:,}\n"
                f"**Humans:** {humans:,}\n**Bots:** {bots:,}\n\n"
                f"🟢 **Online:** {online:,}\n"
                f"🌙 **Idle:** {idle:,}\n"
                f"⛔ **Do Not Disturb:** {dnd:,}\n"
                f"⚫ **Offline:** {offline:,}"
            )

        if self.section_index == 2:
            return (
                f"**Total channels:** {len(guild.channels):,}\n"
                f"**Text channels:** {len(guild.text_channels):,}\n"
                f"**Voice channels:** {len(guild.voice_channels):,}\n"
                f"**Categories:** {len(guild.categories):,}\n"
                f"**Forums:** {len(guild.forums):,}"
            )

        if self.section_index == 3:
            category = ROLE_CATEGORY_KEYS[self.category_index]
            entries = self.get_role_entries()
            start = self.page * 8
            page_entries = entries[start:start + 8]
            lines = [f"### {category}"]
            if not page_entries:
                lines.append("No matching roles were found on this server.")
            for role, description in page_entries:
                lines.append(f"{role.mention}\n-# {description}")
            lines.append(f"\n-# {tr(self.lang, 16)} {self.page + 1}")
            return "\n\n".join(lines)

        if self.section_index == 4:
            boosters = sum(m.premium_since is not None for m in guild.members)
            return (
                f"**Boost level:** {guild.premium_tier}\n"
                f"**Total boosts:** {guild.premium_subscription_count or 0}\n"
                f"**Boosters:** {boosters}"
            )

        if self.section_index == 5:
            animated = sum(e.animated for e in guild.emojis)
            return (
                f"**Emojis:** {len(guild.emojis)}\n"
                f"**Animated emojis:** {animated}\n"
                f"**Stickers:** {len(guild.stickers)}"
            )

        if self.section_index == 6:
            return (
                f"**Verification level:** {str(guild.verification_level).replace('_', ' ').title()}\n"
                f"**2FA moderation:** {'Enabled' if guild.mfa_level else 'Disabled'}\n"
                f"**Content filter:** {str(guild.explicit_content_filter).replace('_', ' ').title()}"
            )

        if self.section_index == 7:
            return (
                f"**Server ID:** `{guild.id}`\n"
                f"**Preferred locale:** {guild.preferred_locale}\n"
                f"**Default notifications:** {str(guild.default_notifications).replace('_', ' ').title()}\n"
                f"**System channel:** {guild.system_channel.mention if guild.system_channel else 'Not set'}\n"
                f"**AFK channel:** {guild.afk_channel.mention if guild.afk_channel else 'Not set'}\n"
                f"**AFK timeout:** {guild.afk_timeout} seconds\n"
                f"**File size limit:** {guild.filesize_limit:,} bytes"
            )

        return "No information available."


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.languages = load_languages()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        content = message.content.strip().lower()

        if content == "!commands system":
            if message.author.id != OWNER_ID:
                return
            await message.reply(
                "**System-BOT | Info commands**\n"
                "`!info server` — Open the server information setup.",
                mention_author=False,
                delete_after=30
            )
            return

        if content != "!info server":
            return

        if message.author.id != OWNER_ID:
            await message.reply(
                "You are not allowed to use this command.",
                mention_author=False,
                delete_after=5
            )
            return

        try:
            await message.delete()
        except discord.Forbidden:
            pass

        try:
            await message.channel.send(view=PublicLanguageView(self))
        except Exception:
            logger.exception("Could not send language selector")
            try:
                await message.author.send("Could not create the language selection message.")
            except discord.Forbidden:
                pass


async def setup(bot):
    await bot.add_cog(Info(bot))
