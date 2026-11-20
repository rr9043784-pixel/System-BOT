import os
import re
import json
import time
import shutil
import asyncio
import logging
import unicodedata
import urllib.parse
import urllib.request

from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands, tasks


# =========================================================
# CONFIGURATION
# =========================================================

OWNER_ID = 1176149190192152626
LOG_CHANNEL_ID = 1523192981170159677

DATA_DIR = "/data"

BAD_WORDS_FILE = os.path.join(DATA_DIR, "bad_words.json")
WARNINGS_FILE = os.path.join(DATA_DIR, "automod_warnings.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "automod_settings.json")
HISTORY_FILE = os.path.join(DATA_DIR, "automod_history.json")

WIKTIONARY_API = "https://ru.wiktionary.org/w/api.php"
WIKTIONARY_CATEGORY = "Категория:Матерные выражения/ru"

WORD_UPDATE_INTERVAL = 86400

SPAM_MESSAGES = 5
SPAM_INTERVAL = 6
DUPLICATE_MESSAGES = 3
DUPLICATE_INTERVAL = 10

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("SystemBOT.AutoMod")


# =========================================================
# STORAGE
# =========================================================

os.makedirs(DATA_DIR, exist_ok=True)


def migrate_file(filename):
    destination = os.path.join(DATA_DIR, filename)

    if os.path.exists(destination):
        return

    old_path = os.path.join(os.getcwd(), filename)

    if os.path.exists(old_path):
        try:
            shutil.copy2(old_path, destination)
            log.info("Migrated %s to /data", filename)
        except Exception:
            log.exception("Migration failed: %s", filename)


for filename in (
    "bad_words.json",
    "automod_warnings.json",
    "automod_settings.json",
    "automod_history.json",
):
    migrate_file(filename)


def load_json(path, default):
    if not os.path.exists(path):
        return default

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data

    except Exception:
        log.exception("Failed to load JSON: %s", path)
        return default


def save_json(path, data):
    temporary = path + ".tmp"

    try:
        with open(temporary, "w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=4
            )

        os.replace(temporary, path)

    except Exception:
        log.exception("Failed to save JSON: %s", path)


bad_words = load_json(
    BAD_WORDS_FILE,
    {"updated": 0, "words": []}
)

warnings_data = load_json(WARNINGS_FILE, {})
settings_data = load_json(SETTINGS_FILE, {})
history_data = load_json(HISTORY_FILE, {})

if not isinstance(bad_words, dict):
    bad_words = {"updated": 0, "words": []}

if not isinstance(bad_words.get("words"), list):
    bad_words["words"] = []

if not isinstance(warnings_data, dict):
    warnings_data = {}

if not isinstance(settings_data, dict):
    settings_data = {}

if not isinstance(history_data, dict):
    history_data = {}


# =========================================================
# SETTINGS
# =========================================================

DEFAULT_SETTINGS = {
    "enabled": True,
    "bad_words": True,
    "links": True,
    "spam": True,
    "duplicates": True,
    "bypass_protection": True,
}


def get_settings(guild_id):
    key = str(guild_id)

    if not isinstance(settings_data.get(key), dict):
        settings_data[key] = DEFAULT_SETTINGS.copy()

    for name, value in DEFAULT_SETTINGS.items():
        settings_data[key].setdefault(name, value)

    return settings_data[key]


def save_settings():
    save_json(SETTINGS_FILE, settings_data)


# =========================================================
# TEXT NORMALIZATION
# =========================================================

CONFUSABLES = str.maketrans({
    "a": "а",
    "b": "в",
    "c": "с",
    "e": "е",
    "h": "н",
    "k": "к",
    "m": "м",
    "o": "о",
    "p": "р",
    "t": "т",
    "x": "х",
    "y": "у",
    "@": "а",
    "0": "о",
    "3": "з",
    "4": "ч",
    "6": "б",
    "8": "в",
    "$": "с",
})


def normalize_text(text):
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", str(text))
    text = text.lower().translate(CONFUSABLES)

    text = "".join(
        char
        for char in unicodedata.normalize("NFD", text)
        if unicodedata.category(char) != "Mn"
    )

    return "".join(
        char for char in text
        if char.isalnum()
    )


def contains_bad_word(text, bypass_protection=True):
    normalized = normalize_text(text)

    if not normalized:
        return False

    for word in bad_words.get("words", []):
        word = normalize_text(word)

        if not word:
            continue

        if normalized == word:
            return True

        if bypass_protection and len(word) >= 4:
            if word in normalized:
                return True

    return False


# =========================================================
# WIKTIONARY
# =========================================================

def download_wiktionary_words():
    words = set()
    continuation = None

    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": WIKTIONARY_CATEGORY,
            "cmlimit": "500",
            "cmtype": "page",
            "format": "json",
            "formatversion": "2",
        }

        if continuation:
            params["cmcontinue"] = continuation

        url = (
            WIKTIONARY_API
            + "?"
            + urllib.parse.urlencode(params)
        )

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "SystemBOT-AutoMod/1.0"
            },
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=30
            ) as response:
                data = json.loads(
                    response.read().decode("utf-8")
                )

        except Exception:
            log.exception("Wiktionary download failed")
            break

        for page in data.get(
            "query", {}
        ).get("categorymembers", []):

            title = page.get("title", "")

            if title.startswith("Категория:"):
                continue

            word = normalize_text(title)

            if len(word) >= 2:
                words.add(word)

        continuation_data = data.get("continue")

        if not continuation_data:
            break

        continuation = continuation_data.get("cmcontinue")

        if not continuation:
            break

    result = sorted(words)

    if result:
        save_json(
            BAD_WORDS_FILE,
            {
                "updated": int(time.time()),
                "words": result,
            },
        )

        return result

    return bad_words.get("words", [])


def update_words():
    global bad_words

    updated = bad_words.get("updated", 0)

    if time.time() - updated < WORD_UPDATE_INTERVAL:
        return

    words = download_wiktionary_words()

    if words:
        bad_words = {
            "updated": int(time.time()),
            "words": words,
        }

        save_json(BAD_WORDS_FILE, bad_words)


# =========================================================
# LINK FILTER
# =========================================================

LINK_PATTERNS = [
    re.compile(r"https?://\S+", re.I),
    re.compile(r"www\.\S+", re.I),
    re.compile(r"discord\.gg/\S+", re.I),
    re.compile(r"discord(?:app)?\.com/invite/\S+", re.I),
    re.compile(
        r"\b[a-z0-9-]+\.(?:com|net|org|io|gg|me|ru|xyz|dev|app|site|online)\b",
        re.I,
    ),
]


def contains_link(text):
    return any(
        pattern.search(text)
        for pattern in LINK_PATTERNS
    )


# =========================================================
# SPAM TRACKING
# =========================================================

message_history = {}


def is_spam(message, duplicate_enabled=True):
    key = (
        message.guild.id,
        message.author.id,
    )

    now = time.time()

    history = message_history.setdefault(key, [])
    history.append((now, message.content))

    history[:] = [
        item for item in history
        if now - item[0] <= SPAM_INTERVAL
    ]

    if len(history) >= SPAM_MESSAGES:
        return True, "Spam"

    if duplicate_enabled and len(history) >= DUPLICATE_MESSAGES:
        recent = [
            item[1].strip().lower()
            for item in history[-DUPLICATE_MESSAGES:]
        ]

        if recent[0] and all(
            text == recent[0]
            for text in recent
        ):
            return True, "Duplicate messages"

    return False, None


# =========================================================
# WARNING SYSTEM
# =========================================================

def get_warnings(guild_id, user_id):
    guild_data = warnings_data.setdefault(
        str(guild_id),
        {}
    )

    value = guild_data.get(str(user_id), [])

    # Migrate old integer counters.
    if isinstance(value, int):
        value = [
            {
                "id": index + 1,
                "reason": "Imported previous warning",
                "moderator": "AutoMod",
                "timestamp": int(time.time()),
            }
            for index in range(max(0, value))
        ]

        guild_data[str(user_id)] = value
        save_json(WARNINGS_FILE, warnings_data)

    if not isinstance(value, list):
        value = []

    return value


def warning_count(guild_id, user_id):
    return len(get_warnings(guild_id, user_id))


def add_warning(guild_id, user_id, reason, moderator):
    records = get_warnings(guild_id, user_id)

    record = {
        "id": int(time.time() * 1000),
        "reason": reason,
        "moderator": str(moderator),
        "timestamp": int(time.time()),
    }

    records.append(record)

    warnings_data[str(guild_id)][str(user_id)] = records
    save_json(WARNINGS_FILE, warnings_data)

    return record


def remove_warning(guild_id, user_id):
    records = get_warnings(guild_id, user_id)

    if not records:
        return None

    removed = records.pop()

    warnings_data[str(guild_id)][str(user_id)] = records
    save_json(WARNINGS_FILE, warnings_data)

    return removed


# =========================================================
# MODERATION HISTORY
# =========================================================

def add_history(
    guild,
    member,
    moderator,
    action,
    reason,
    extra=None,
):
    record = {
        "member_id": member.id,
        "member": str(member),
        "moderator": str(moderator),
        "action": action,
        "reason": reason,
        "extra": extra or {},
        "timestamp": int(time.time()),
    }

    history_data.setdefault(
        str(guild.id),
        []
    ).append(record)

    save_json(HISTORY_FILE, history_data)

    return record


# =========================================================
# MODERATION LOGS
# =========================================================

async def send_log(
    guild,
    member,
    moderator,
    action,
    reason,
    source="Manual Moderation",
    extra=None,
):
    channel = guild.get_channel(LOG_CHANNEL_ID)

    if channel is None:
        try:
            channel = await guild.fetch_channel(
                LOG_CHANNEL_ID
            )
        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException,
        ):
            log.exception("Moderation log channel unavailable")
            return

    count = warning_count(guild.id, member.id)

    embed = discord.Embed(
        title="🛡️ Moderation Log",
        color=discord.Color.red(),
        timestamp=discord.utils.utcnow(),
    )

    embed.add_field(
        name="👤 Member",
        value=(
            f"{member.mention}\n"
            f"`{member}`\n"
            f"ID: `{member.id}`"
        ),
        inline=False,
    )

    moderator_name = str(moderator)
    moderator_id = getattr(moderator, "id", None)

    if moderator_id:
        moderator_name += f"\nID: `{moderator_id}`"

    embed.add_field(
        name="🛡️ Moderator",
        value=moderator_name[:1024],
        inline=True,
    )

    embed.add_field(
        name="⚖️ Action",
        value=str(action)[:1024],
        inline=True,
    )

    embed.add_field(
        name="📊 Warnings",
        value=str(count),
        inline=True,
    )

    embed.add_field(
        name="📝 Reason",
        value=str(reason)[:1024],
        inline=False,
    )

    embed.add_field(
        name="📌 Source",
        value=source,
        inline=True,
    )

    if extra:
        for name, value in extra.items():
            embed.add_field(
                name=str(name)[:256],
                value=str(value)[:1024],
                inline=True,
            )

    embed.set_footer(
        text=f"System-BOT • {guild.name}"
    )

    try:
        await channel.send(embed=embed)
    except discord.HTTPException:
        log.exception("Failed to send moderation log")


# =========================================================
# PRIVATE NOTICE TO MEMBER
# =========================================================

async def notify_member(
    member,
    guild,
    violation,
    punishment,
    count,
):
    try:
        embed = discord.Embed(
            title="🛡️ AutoMod Notification",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow(),
        )

        embed.add_field(
            name="Server",
            value=guild.name,
            inline=False,
        )

        embed.add_field(
            name="Violation",
            value=str(violation)[:1024],
            inline=False,
        )

        embed.add_field(
            name="Punishment",
            value=str(punishment)[:1024],
            inline=False,
        )

        embed.add_field(
            name="Warning Count",
            value=str(count),
            inline=False,
        )

        embed.set_footer(
            text="Please follow the server rules."
        )

        # This DM goes only to the violating member.
        await member.send(embed=embed)

    except (discord.Forbidden, discord.HTTPException):
        log.info(
            "Could not DM violating member %s",
            member.id,
        )


# =========================================================
# AUTOMATIC PUNISHMENT
# =========================================================

async def automatic_punishment(
    member,
    violation,
    channel=None,
):
    guild = member.guild

    record = add_warning(
        guild.id,
        member.id,
        violation,
        "AutoMod",
    )

    count = warning_count(
        guild.id,
        member.id,
    )

    punishment = "Warning"

    try:
        if count == 2:
            punishment = "Timeout for 1 hour"

            await member.timeout(
                timedelta(hours=1),
                reason=violation,
            )

        elif count == 3:
            punishment = "Timeout for 1 day"

            await member.timeout(
                timedelta(days=1),
                reason=violation,
            )

        elif count == 4:
            punishment = "Kick"

            await member.kick(
                reason=violation
            )

        elif count >= 5:
            punishment = "Ban"

            await guild.ban(
                member,
                reason=violation,
                delete_message_seconds=0,
            )

    except (
        discord.Forbidden,
        discord.HTTPException,
    ):
        log.exception("Automatic punishment failed")

        punishment += (
            " (Action failed — check bot permissions)"
        )

    await notify_member(
        member,
        guild,
        violation,
        punishment,
        count,
    )

    moderator = guild.me or member

    extra = {
        "Violation count": count,
        "Warning ID": record["id"],
    }

    if channel is not None:
        extra["Channel"] = (
            f"#{channel.name} (`{channel.id}`)"
        )

    add_history(
        guild,
        member,
        "AutoMod",
        punishment,
        violation,
        extra,
    )

    await send_log(
        guild,
        member,
        moderator,
        punishment,
        violation,
        source="Automatic AutoMod",
        extra=extra,
    )

    return punishment


# =========================================================
# COMPONENTS V2 HELPERS
# =========================================================

def make_container(*items):
    return discord.ui.Container(*items)


class PanelButton(discord.ui.Button):

    def __init__(
        self,
        label,
        action,
        style=discord.ButtonStyle.secondary,
        emoji=None,
        disabled=False,
    ):
        super().__init__(
            label=label,
            style=style,
            emoji=emoji,
            disabled=disabled,
        )

        self.action = action

    async def callback(self, interaction):
        await self.view.handle_action(
            interaction,
            self.action,
        )


class MemberSelect(discord.ui.Select):

    def __init__(self, members):
        options = []

        for member in members[:25]:
            options.append(
                discord.SelectOption(
                    label=str(
                        member.display_name or member
                    )[:100],
                    value=str(member.id),
                    description=f"ID: {member.id}",
                )
            )

        super().__init__(
            placeholder="Select a member...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction):
        await self.view.select_member(
            interaction,
            int(self.values[0]),
        )


# =========================================================
# OWNER CHECK
# =========================================================

def is_owner(interaction):
    return interaction.user.id == OWNER_ID


# =========================================================
# MEMBER PICKER
# =========================================================

class MemberPickerView(discord.ui.LayoutView):

    def __init__(self, guild, members):
        super().__init__(timeout=300)

        self.guild = guild

        self.members = sorted(
            members,
            key=lambda member: (
                member.display_name or str(member)
            ).lower(),
        )

        self.page = 0
        self.per_page = 25

        self.build()

    def build(self):
        self.clear_items()

        start = self.page * self.per_page

        current = self.members[
            start:start + self.per_page
        ]

        total_pages = max(
            1,
            (
                len(self.members)
                + self.per_page - 1
            ) // self.per_page,
        )

        container = make_container(
            discord.ui.TextDisplay(
                "# 🛡️ Member Management\n"
                "Select a server member to open "
                "their private moderation panel."
            ),
            discord.ui.Separator(),
            discord.ui.TextDisplay(
                f"**Members:** {len(self.members)}\n"
                f"**Page:** {self.page + 1}/{total_pages}"
            ),
        )

        if current:
            container.add_item(
                discord.ui.ActionRow(
                    MemberSelect(current)
                )
            )
        else:
            container.add_item(
                discord.ui.TextDisplay(
                    "No members found."
                )
            )

        previous = PanelButton(
            "Previous Page",
            "previous",
            disabled=self.page <= 0,
        )

        next_button = PanelButton(
            "Next Page",
            "next",
            disabled=(
                self.page >= total_pages - 1
            ),
        )

        container.add_item(
            discord.ui.ActionRow(
                previous,
                next_button,
            )
        )

        self.add_item(container)

    async def interaction_check(self, interaction):
        if not is_owner(interaction):
            await interaction.response.send_message(
                "You cannot use this panel.",
                ephemeral=True,
            )
            return False

        return True

    async def select_member(
        self,
        interaction,
        member_id,
    ):
        member = self.guild.get_member(member_id)

        if member is None:
            try:
                member = await self.guild.fetch_member(
                    member_id
                )
            except (
                discord.NotFound,
                discord.HTTPException,
            ):
                await interaction.response.send_message(
                    "Member is no longer available.",
                    ephemeral=True,
                )
                return

        await interaction.response.edit_message(
            view=MemberPanelView(member)
        )

    async def handle_action(
        self,
        interaction,
        action,
    ):
        if action == "previous":
            self.page = max(
                0,
                self.page - 1,
            )

        elif action == "next":
            maximum = max(
                0,
                (
                    len(self.members) - 1
                ) // self.per_page,
            )

            self.page = min(
                maximum,
                self.page + 1,
            )

        self.build()

        await interaction.response.edit_message(
            view=self
        )


# =========================================================
# REASON MODAL
# =========================================================

class ReasonModal(discord.ui.Modal):

    def __init__(self, member, action):
        super().__init__(
            title=f"{action} — Reason"
        )

        self.member = member
        self.action = action

        self.reason = discord.ui.TextInput(
            label="Reason (required)",
            placeholder="Enter the reason...",
            required=True,
            min_length=2,
            max_length=500,
            style=discord.TextStyle.paragraph,
        )

        self.add_item(self.reason)

    async def on_submit(self, interaction):
        if not is_owner(interaction):
            await interaction.response.send_message(
                "You cannot use this action.",
                ephemeral=True,
            )
            return

        reason = str(
            self.reason.value
        ).strip()

        if len(reason) < 2:
            await interaction.response.send_message(
                "A valid reason is required.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

        member = self.member
        guild = member.guild
        action = self.action

        try:
            if action == "Warn Add":
                add_warning(
                    guild.id,
                    member.id,
                    reason,
                    interaction.user,
                )

            elif action == "Warn Remove":
                removed = remove_warning(
                    guild.id,
                    member.id,
                )

                if removed is None:
                    await interaction.followup.send(
                        "This member has no warnings.",
                        ephemeral=True,
                    )
                    return

            elif action == "Mute":
                await member.timeout(
                    timedelta(hours=1),
                    reason=reason,
                )

            elif action == "Unmute":
                await member.timeout(
                    None,
                    reason=reason,
                )

            elif action == "Kick":
                await member.kick(
                    reason=reason
                )

            elif action == "Ban":
                await guild.ban(
                    member,
                    reason=reason,
                    delete_message_seconds=0,
                )

            else:
                await interaction.followup.send(
                    "Unknown action.",
                    ephemeral=True,
                )
                return

            add_history(
                guild,
                member,
                interaction.user,
                action,
                reason,
            )

            await send_log(
                guild,
                member,
                interaction.user,
                action,
                reason,
                source="Manual Moderation",
            )

            await interaction.followup.send(
                f"✅ **{action}** completed for "
                f"**{member}**.",
                ephemeral=True,
            )

            if action in (
                "Warn Add",
                "Mute",
                "Ban",
                "Kick",
            ):
                await notify_member(
                    member,
                    guild,
                    reason,
                    action,
                    warning_count(
                        guild.id,
                        member.id,
                    ),
                )

        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Missing permissions or role "
                "hierarchy prevents this action.",
                ephemeral=True,
            )

        except discord.HTTPException:
            log.exception(
                "Manual moderation action failed"
            )

            await interaction.followup.send(
                "❌ Discord could not complete this action.",
                ephemeral=True,
            )


# =========================================================
# UNBAN MODAL
# =========================================================

class UnbanModal(discord.ui.Modal):

    def __init__(self, guild):
        super().__init__(
            title="Unban Member"
        )

        self.guild = guild

        self.user_id = discord.ui.TextInput(
            label="User ID",
            placeholder="Enter Discord user ID",
            required=True,
            max_length=25,
        )

        self.reason = discord.ui.TextInput(
            label="Reason (required)",
            placeholder="Enter the reason...",
            required=True,
            min_length=2,
            max_length=500,
        )

        self.add_item(self.user_id)
        self.add_item(self.reason)

    async def on_submit(self, interaction):
        if not is_owner(interaction):
            await interaction.response.send_message(
                "You cannot use this action.",
                ephemeral=True,
            )
            return

        try:
            user_id = int(
                str(self.user_id.value).strip()
            )

            if user_id <= 0:
                raise ValueError

        except ValueError:
            await interaction.response.send_message(
                "Invalid user ID.",
                ephemeral=True,
            )
            return

        reason = str(
            self.reason.value
        ).strip()

        if len(reason) < 2:
            await interaction.response.send_message(
                "A valid reason is required.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

        try:
            ban_entry = await self.guild.fetch_ban(
                discord.Object(id=user_id)
            )

            user = ban_entry.user

            await self.guild.unban(
                user,
                reason=reason,
            )

            record = {
                "member_id": user_id,
                "member": str(user),
                "moderator": str(interaction.user),
                "action": "Unban",
                "reason": reason,
                "timestamp": int(time.time()),
            }

            history_data.setdefault(
                str(self.guild.id),
                [],
            ).append(record)

            save_json(
                HISTORY_FILE,
                history_data,
            )

            embed = discord.Embed(
                title="🛡️ Moderation Log",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow(),
            )

            embed.add_field(
                name="Member",
                value=f"{user} (`{user_id}`)",
                inline=False,
            )

            embed.add_field(
                name="Moderator",
                value=str(interaction.user),
                inline=True,
            )

            embed.add_field(
                name="Action",
                value="Unban",
                inline=True,
            )

            embed.add_field(
                name="Reason",
                value=reason[:1024],
                inline=False,
            )

            embed.add_field(
                name="Source",
                value="Manual Moderation",
                inline=True,
            )

            channel = self.guild.get_channel(
                LOG_CHANNEL_ID
            )

            if channel is None:
                try:
                    channel = await self.guild.fetch_channel(
                        LOG_CHANNEL_ID
                    )
                except discord.HTTPException:
                    channel = None

            if channel is not None:
                await channel.send(embed=embed)

            await interaction.followup.send(
                f"✅ Unbanned **{user}** (`{user_id}`).",
                ephemeral=True,
            )

        except discord.NotFound:
            await interaction.followup.send(
                "This user is not banned.",
                ephemeral=True,
            )

        except discord.Forbidden:
            await interaction.followup.send(
                "Missing Ban Members permission.",
                ephemeral=True,
            )

        except discord.HTTPException:
            log.exception("Unban failed")

            await interaction.followup.send(
                "Discord could not complete the unban.",
                ephemeral=True,
            )


# =========================================================
# MEMBER PANEL
# =========================================================

class MemberPanelView(discord.ui.LayoutView):

    def __init__(self, member):
        super().__init__(timeout=300)

        self.member = member
        self.build()

    def build(self):
        self.clear_items()

        member = self.member
        guild = member.guild

        warnings = get_warnings(
            guild.id,
            member.id,
        )

        count = len(warnings)

        status = (
            "Timed out"
            if member.is_timed_out()
            else "Active"
        )

        joined = (
            discord.utils.format_dt(
                member.joined_at,
                "D",
            )
            if member.joined_at
            else "Unknown"
        )

        container = make_container(
            discord.ui.TextDisplay(
                "# 🛡️ Member Management\n"
                "Private System-BOT moderation panel"
            ),
            discord.ui.Separator(),
            discord.ui.TextDisplay(
                f"## 👤 {member}\n"
                f"**User ID:** `{member.id}`\n"
                f"**Account:** "
                f"{discord.utils.format_dt(member.created_at, 'D')}\n"
                f"**Joined:** {joined}\n"
                f"**Status:** {status}"
            ),
            discord.ui.Separator(),
            discord.ui.TextDisplay(
                "## 📊 Moderation Information\n"
                f"**Warnings:** `{count}`\n"
                f"**Roles:** `{max(0, len(member.roles) - 1)}`\n"
                f"**Highest role:** {member.top_role.mention}"
            ),
            discord.ui.Separator(),
            discord.ui.TextDisplay(
                "## ⚖️ Moderation Actions"
            ),
        )

        container.add_item(
            discord.ui.ActionRow(
                PanelButton(
                    "Warn Add",
                    "Warn Add",
                    discord.ButtonStyle.primary,
                ),
                PanelButton(
                    "Warn Remove",
                    "Warn Remove",
                ),
                PanelButton(
                    "Warning User",
                    "Warning User",
                ),
            )
        )

        container.add_item(
            discord.ui.ActionRow(
                PanelButton(
                    "Warning List",
                    "Warning List",
                ),
                PanelButton(
                    "Mute",
                    "Mute",
                    discord.ButtonStyle.danger,
                ),
                PanelButton(
                    "Unmute",
                    "Unmute",
                    discord.ButtonStyle.success,
                ),
            )
        )

        container.add_item(
            discord.ui.ActionRow(
                PanelButton(
                    "Kick",
                    "Kick",
                    discord.ButtonStyle.danger,
                ),
                PanelButton(
                    "Ban",
                    "Ban",
                    discord.ButtonStyle.danger,
                ),
                PanelButton(
                    "Unban",
                    "Unban",
                ),
            )
        )

        container.add_item(
            discord.ui.ActionRow(
                PanelButton(
                    "AutoMod Settings",
                    "settings",
                ),
                PanelButton(
                    "Refresh",
                    "refresh",
                ),
            )
        )

        self.add_item(container)

    async def interaction_check(self, interaction):
        if not is_owner(interaction):
            await interaction.response.send_message(
                "You cannot use this panel.",
                ephemeral=True,
            )
            return False

        return True

    async def handle_action(
        self,
        interaction,
        action,
    ):
        if action == "refresh":
            self.build()

            await interaction.response.edit_message(
                view=self
            )
            return

        if action == "settings":
            await interaction.response.edit_message(
                view=AutoModSettingsView(
                    self.member.guild,
                    self.member,
                )
            )
            return

        if action == "Warning User":
            count = warning_count(
                self.member.guild.id,
                self.member.id,
            )

            await interaction.response.send_message(
                f"**{self.member}** currently has "
                f"**{count}** warning(s).",
                ephemeral=True,
            )
            return

        if action == "Warning List":
            records = get_warnings(
                self.member.guild.id,
                self.member.id,
            )

            if not records:
                description = "No warnings found."
            else:
                lines = []

                for index, record in enumerate(
                    records[-15:],
                    1,
                ):
                    timestamp = record.get(
                        "timestamp",
                        0,
                    )

                    reason = record.get(
                        "reason",
                        "No reason",
                    )

                    moderator = record.get(
                        "moderator",
                        "Unknown",
                    )

                    lines.append(
                        f"**{index}.** {reason[:250]}\n"
                        f"Moderator: {moderator}\n"
                        f"Date: <t:{timestamp}:f>"
                    )

                description = "\n\n".join(lines)

            embed = discord.Embed(
                title="📋 Warning History",
                description=description[:4000],
                color=discord.Color.orange(),
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )
            return

        if action == "Unban":
            await interaction.response.send_modal(
                UnbanModal(self.member.guild)
            )
            return

        await interaction.response.send_modal(
            ReasonModal(
                self.member,
                action,
            )
        )


# =========================================================
# AUTOMOD SETTINGS PANEL
# =========================================================

class SettingButton(discord.ui.Button):

    def __init__(self, label, setting):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.secondary,
        )

        self.setting = setting

    async def callback(self, interaction):
        if not is_owner(interaction):
            await interaction.response.send_message(
                "You cannot change AutoMod settings.",
                ephemeral=True,
            )
            return

        settings = get_settings(
            self.view.guild.id
        )

        settings[self.setting] = not settings[
            self.setting
        ]

        save_settings()

        self.view.build()

        await interaction.response.edit_message(
            view=self.view
        )


class AutoModSettingsView(discord.ui.LayoutView):

    def __init__(self, guild, member=None):
        super().__init__(timeout=300)

        self.guild = guild
        self.member = member

        self.build()

    def build(self):
        self.clear_items()

        settings = get_settings(
            self.guild.id
        )

        labels = {
            "enabled": "AutoMod",
            "bad_words": "Bad Words Filter",
            "links": "Link Filter",
            "spam": "Anti-Spam",
            "duplicates": "Duplicate Messages",
            "bypass_protection": "Bypass Protection",
        }

        container = make_container(
            discord.ui.TextDisplay(
                "# ⚙️ AutoMod Settings\n"
                "Select a setting to enable or disable it."
            ),
            discord.ui.Separator(),
        )

        for key, label in labels.items():
            status = (
                "🟢 Enabled"
                if settings[key]
                else "🔴 Disabled"
            )

            container.add_item(
                discord.ui.TextDisplay(
                    f"**{label}** — {status}"
                )
            )

            container.add_item(
                discord.ui.ActionRow(
                    SettingButton(label, key)
                )
            )

        container.add_item(
            discord.ui.Separator()
        )

        container.add_item(
            discord.ui.ActionRow(
                PanelButton(
                    "Back to Member",
                    "back_member",
                    disabled=self.member is None,
                ),
                PanelButton(
                    "Back to Member List",
                    "back_list",
                ),
            )
        )

        self.add_item(container)

    async def interaction_check(self, interaction):
        if not is_owner(interaction):
            await interaction.response.send_message(
                "You cannot use this panel.",
                ephemeral=True,
            )
            return False

        return True

    async def handle_action(
        self,
        interaction,
        action,
    ):
        if action == "back_member" and self.member:
            await interaction.response.edit_message(
                view=MemberPanelView(self.member)
            )

        elif action == "back_list":
            members = list(self.guild.members)

            await interaction.response.edit_message(
                view=MemberPickerView(
                    self.guild,
                    members,
                )
            )


# =========================================================
# AUTOMOD COG + /edit member
# =========================================================

class AutoMod(
    commands.GroupCog,
    group_name="edit",
    group_description="Owner-only member management",
):

    def __init__(self, bot):
        self.bot = bot
        self.update_words_loop.start()

    def cog_unload(self):
        self.update_words_loop.cancel()

    # -----------------------------------------------------
    # /edit member
    # -----------------------------------------------------

    @app_commands.command(
        name="member",
        description="Open the private member moderation panel",
    )
    async def edit_member(
        self,
        interaction: discord.Interaction,
    ):
        if not is_owner(interaction):
            await interaction.response.send_message(
                "❌ This command is owner-only.",
                ephemeral=True,
            )
            return

        if interaction.guild is None:
            await interaction.response.send_message(
                "Use this command inside a server.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

        try:
            members = [
                member
                async for member in (
                    interaction.guild.fetch_members(
                        limit=None
                    )
                )
            ]

        except discord.HTTPException:
            log.exception(
                "Could not fetch all server members"
            )

            members = list(
                interaction.guild.members
            )

        # Exclude bots from the member selector.
        members = [
            member
            for member in members
            if not member.bot
        ]

        await interaction.followup.send(
            view=MemberPickerView(
                interaction.guild,
                members,
            ),
            ephemeral=True,
        )

    # -----------------------------------------------------
    # !commands System
    # -----------------------------------------------------

    @commands.Cog.listener()
    async def on_commands_system_message(self, message):
        if message.author.bot:
            return

        if message.author.id != OWNER_ID:
            return

        if message.guild is None:
            return

        if message.content.strip().lower() != "!commands system":
            return

        embed = discord.Embed(
            title="🛡️ System-BOT Commands",
            color=discord.Color.blurple(),
        )

        embed.add_field(
            name="AutoMod",
            value=(
                "`/edit member` — Open member moderation panel"
            ),
            inline=False,
        )

        embed.add_field(
            name="Member Moderation",
            value=(
                "Warn Add\n"
                "Warn Remove\n"
                "Warning User\n"
                "Warning List\n"
                "Mute / Unmute\n"
                "Kick\n"
                "Ban / Unban"
            ),
            inline=False,
        )

        embed.add_field(
            name="AutoMod Settings",
            value=(
                "Enable / Disable AutoMod\n"
                "Bad Words Filter\n"
                "Link Filter\n"
                "Anti-Spam\n"
                "Duplicate Messages\n"
                "Bypass Protection"
            ),
            inline=False,
        )

        await message.channel.send(embed=embed)

    # -----------------------------------------------------
    # WORD UPDATE LOOP
    # -----------------------------------------------------

    @tasks.loop(seconds=WORD_UPDATE_INTERVAL)
    async def update_words_loop(self):
        try:
            await asyncio.to_thread(
                update_words
            )
        except Exception:
            log.exception(
                "Word update failed"
            )

    @update_words_loop.before_loop
    async def before_words_loop(self):
        await self.bot.wait_until_ready()

    # -----------------------------------------------------
    # AUTOMOD MESSAGE LISTENER
    # -----------------------------------------------------

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.guild is None:
            return

        if message.author.guild_permissions.administrator:
            return

        settings = get_settings(
            message.guild.id
        )

        if not settings["enabled"]:
            return

        content = message.content.strip()

        if not content:
            return

        violation = None

        if (
            settings["links"]
            and contains_link(content)
        ):
            violation = "Sending links is not allowed."

        elif (
            settings["bad_words"]
            and contains_bad_word(
                content,
                bypass_protection=settings[
                    "bypass_protection"
                ],
            )
        ):
            violation = "Forbidden language."

        else:
            spam, spam_reason = is_spam(
                message,
                duplicate_enabled=settings[
                    "duplicates"
                ],
            )

            if settings["spam"] and spam:
                violation = (
                    spam_reason or "Spam"
                )

        if not violation:
            return

        try:
            await message.delete()
        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException,
        ):
            log.exception(
                "Could not delete violating message"
            )

        await automatic_punishment(
            message.author,
            violation,
            channel=message.channel,
        )


# =========================================================
# SETUP
# =========================================================

async def setup(bot):
    try:
        await asyncio.to_thread(
            update_words
        )
    except Exception:
        log.exception(
            "Initial word update failed"
        )

    await bot.add_cog(
        AutoMod(bot)
    )

    log.info(
        "AutoMod loaded successfully"
    )
