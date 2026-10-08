import os
import re
import json
import time
import unicodedata
import urllib.parse
import urllib.request
import urllib.error

import discord
from discord.ext import commands, tasks


# =================================================
# Settings
# =================================================

OWNER_ID = 1176149190192152626

BAD_WORDS_FILE = "bad_words.json"
WARNINGS_FILE = "automod_warnings.json"

WIKTIONARY_API = (
    "https://ru.wiktionary.org/w/api.php"
)

WIKTIONARY_CATEGORY = (
    "Категория:Матерные выражения/ru"
)

# Обновлять список из Викисловаря раз в 24 часа
WORD_UPDATE_INTERVAL = 86400

# Через сколько секунд удалить сообщение с предупреждением
WARNING_DELETE_AFTER = 8

# Антиспам
SPAM_MESSAGES = 5
SPAM_INTERVAL = 6

# Максимальное количество одинаковых сообщений
DUPLICATE_MESSAGES = 3
DUPLICATE_INTERVAL = 10


# =================================================
# Files
# =================================================

def load_json(filename, default):

    if not os.path.exists(filename):
        return default

    try:

        with open(
            filename,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception as e:

        print(
            f"❌ Failed to load {filename}: {e}"
        )

        return default


def save_json(filename, data):

    temp = filename + ".tmp"

    with open(
        temp,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )

    os.replace(
        temp,
        filename
    )


bad_words = load_json(
    BAD_WORDS_FILE,
    {
        "updated": 0,
        "words": []
    }
)

warnings_data = load_json(
    WARNINGS_FILE,
    {}
)


# =================================================
# Unicode normalization
# =================================================

CONFUSABLES = str.maketrans({

    # Latin -> Cyrillic
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

    "A": "а",
    "B": "в",
    "C": "с",
    "E": "е",
    "H": "н",
    "K": "к",
    "M": "м",
    "O": "о",
    "P": "р",
    "T": "т",
    "X": "х",
    "Y": "у",

    # Common substitutions
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

    # Unicode normalization
    text = unicodedata.normalize(
        "NFKC",
        text
    )

    # Lowercase
    text = text.lower()

    # Replace common Latin lookalikes
    text = text.translate(
        CONFUSABLES
    )

    # Remove combining marks
    text = "".join(
        char
        for char in unicodedata.normalize(
            "NFD",
            text
        )
        if unicodedata.category(char) != "Mn"
    )

    # Keep letters and numbers,
    # remove punctuation / spaces.
    text = "".join(
        char
        for char in text
        if char.isalnum()
    )

    return text


# =================================================
# Wiktionary
# =================================================

def download_wiktionary_words():

    print(
        "📚 Downloading forbidden words from Wiktionary..."
    )

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
            "formatversion": "2"
        }

        if continuation:

            params["cmcontinue"] = continuation


        url = (
            WIKTIONARY_API
            + "?"
            + urllib.parse.urlencode(
                params
            )
        )

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent":
                    "TournamentBot-AutoMod/1.0"
            }
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=30
            ) as response:

                data = json.loads(
                    response.read().decode(
                        "utf-8"
                    )
                )

        except Exception as e:

            print(
                f"❌ Failed to download Wiktionary words: {e}"
            )

            break


        pages = (
            data
            .get("query", {})
            .get("categorymembers", [])
        )


        for page in pages:

            title = page.get(
                "title",
                ""
            )

            if not title:
                continue

            # Don't add category itself
            if title.startswith(
                "Категория:"
            ):
                continue

            normalized = normalize_text(
                title
            )

            if len(normalized) >= 2:

                words.add(
                    normalized
                )


        continue_data = data.get(
            "continue"
        )

        if not continue_data:
            break

        continuation = continue_data.get(
            "cmcontinue"
        )

        if not continuation:
            break


    result = sorted(
        words
    )

    if result:

        save_json(
            BAD_WORDS_FILE,
            {
                "updated": int(
                    time.time()
                ),
                "words": result
            }
        )

        print(
            f"✅ Wiktionary list updated: {len(result)} entries."
        )

        return result


    print(
        "⚠️ Wiktionary returned no words. Keeping old list."
    )

    return bad_words.get(
        "words",
        []
    )


# =================================================
# Update words on startup
# =================================================

def words_need_update():

    updated = bad_words.get(
        "updated",
        0
    )

    return (
        time.time() - updated
        >= WORD_UPDATE_INTERVAL
    )


def update_words():

    global bad_words

    if not words_need_update():

        print(
            f"📚 Using cached AutoMod word list: "
            f"{len(bad_words.get('words', []))} entries."
        )

        return


    words = download_wiktionary_words()

    bad_words = {
        "updated": int(
            time.time()
        ),
        "words": words
    }


# =================================================
# Forbidden words
# =================================================

def contains_bad_word(text):

    normalized = normalize_text(
        text
    )

    if not normalized:
        return False


    for word in bad_words.get(
        "words",
        []
    ):

        if not word:
            continue

        # Exact normalized match
        if normalized == word:
            return True

        # Detect word/phrase even when
        # spaces or punctuation were inserted.
        if len(word) >= 4 and word in normalized:
            return True


    return False


# =================================================
# Links
# =================================================

LINK_PATTERNS = [

    re.compile(
        r"(https?://\S+)",
        re.IGNORECASE
    ),

    re.compile(
        r"(www\.\S+)",
        re.IGNORECASE
    ),

    re.compile(
        r"(discord\.gg/\S+)",
        re.IGNORECASE
    ),

    re.compile(
        r"(discord(?:app)?\.com/invite/\S+)",
        re.IGNORECASE
    ),

    re.compile(
        r"\b[a-z0-9-]+\.(com|net|org|io|gg|me|ru|xyz|dev|app|site|online)\b",
        re.IGNORECASE
    )

]


def contains_link(text):

    for pattern in LINK_PATTERNS:

        if pattern.search(text):

            return True

    return False


# =================================================
# Spam
# =================================================

message_history = {}


def is_spam(message):

    guild_id = message.guild.id
    user_id = message.author.id

    key = (
        guild_id,
        user_id
    )

    now = time.time()

    history = message_history.setdefault(
        key,
        []
    )

    history.append(
        (
            now,
            message.content
        )
    )

    # Keep recent messages
    history[:] = [
        item
        for item in history
        if now - item[0] <= SPAM_INTERVAL
    ]


    if len(history) >= SPAM_MESSAGES:

        return True


    # Duplicate message detection
    if len(history) >= DUPLICATE_MESSAGES:

        recent = [
            item[1]
            for item in history[
                -DUPLICATE_MESSAGES:
            ]
        ]

        if (
            all(
                text.strip().lower()
                == recent[0].strip().lower()
                for text in recent
            )
            and len(recent[0].strip()) > 0
        ):

            return True


    return False


# =================================================
# Warnings
# =================================================

def get_warning_count(
    guild_id,
    user_id
):

    guild_data = warnings_data.setdefault(
        str(guild_id),
        {}
    )

    return int(
        guild_data.get(
            str(user_id),
            0
        )
    )


def set_warning_count(
    guild_id,
    user_id,
    count
):

    guild_data = warnings_data.setdefault(
        str(guild_id),
        {}
    )

    guild_data[
        str(user_id)
    ] = count

    save_json(
        WARNINGS_FILE,
        warnings_data
    )


# =================================================
# Punishments
# =================================================

async def punish_member(
    member,
    violation_reason
):

    guild = member.guild

    guild_id = guild.id
    user_id = member.id


    count = get_warning_count(
        guild_id,
        user_id
    )

    count += 1

    set_warning_count(
        guild_id,
        user_id,
        count
    )


    # =================================================
    # 1 — Warning
    # =================================================

    if count == 1:

        try:

            await member.send(
                "⚠️ **Warning**\n\n"
                f"Your message was removed in **{guild.name}** "
                f"because it violated the server rules.\n\n"
                f"Reason: **{violation_reason}**\n\n"
                "This is your first violation."
            )

        except (
            discord.Forbidden,
            discord.HTTPException
        ):

            pass

        return "⚠️ Warning"


    # =================================================
    # 2 — Mute 1 Hour
    # =================================================

    if count == 2:

        duration = discord.utils.utcnow() + discord.timedelta(
            hours=1
        )

        try:

            await member.edit(
                timed_out_until=duration,
                reason=violation_reason
            )

        except Exception as e:

            print(
                f"❌ Failed to timeout {member}: {e}"
            )

        try:

            await member.send(
                "🔇 **Muted for 1 hour**\n\n"
                f"Your message was removed in **{guild.name}**.\n\n"
                f"Reason: **{violation_reason}**"
            )

        except (
            discord.Forbidden,
            discord.HTTPException
        ):

            pass

        return "🔇 Mute 1 hour"


    # =================================================
    # 3 — Mute 1 Day
    # =================================================

    if count == 3:

        duration = discord.utils.utcnow() + discord.timedelta(
            days=1
        )

        try:

            await member.edit(
                timed_out_until=duration,
                reason=violation_reason
            )

        except Exception as e:

            print(
                f"❌ Failed to timeout {member}: {e}"
            )

        try:

            await member.send(
                "🔇 **Muted for 1 day**\n\n"
                f"Your message was removed in **{guild.name}**.\n\n"
                f"Reason: **{violation_reason}**"
            )

        except (
            discord.Forbidden,
            discord.HTTPException
        ):

            pass

        return "🔇 Mute 1 day"


    # =================================================
    # 4 — Kick
    # =================================================

    if count == 4:

        try:

            await member.send(
                "👢 **Kicked**\n\n"
                f"You were kicked from **{guild.name}** "
                "because of repeated rule violations."
            )

        except (
            discord.Forbidden,
            discord.HTTPException
        ):

            pass


        try:

            await member.kick(
                reason=violation_reason
            )

        except Exception as e:

            print(
                f"❌ Failed to kick {member}: {e}"
            )

        return "👢 Kick"


    # =================================================
    # 5+ — Permanent Ban
    # =================================================

    if count >= 5:

        try:

            await member.send(
                "🔨 **Permanently banned**\n\n"
                f"You were permanently banned from "
                f"**{guild.name}** because of repeated "
                "rule violations."
            )

        except (
            discord.Forbidden,
            discord.HTTPException
        ):

            pass


        try:

            await guild.ban(
                member,
                reason=violation_reason,
                delete_message_days=0
            )

        except Exception as e:

            print(
                f"❌ Failed to ban {member}: {e}"
            )

        return "🔨 Permanent ban"


    return None


# =================================================
# AutoMod Cog
# =================================================

class AutoMod(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        self.update_words_loop.start()

        # Download immediately on startup
        try:

            update_words()

        except Exception as e:

            print(
                f"❌ AutoMod word update failed: {e}"
            )


    def cog_unload(self):

        self.update_words_loop.cancel()


    # =================================================
    # Daily Word Update
    # =================================================

    @tasks.loop(
        seconds=WORD_UPDATE_INTERVAL
    )
    async def update_words_loop(self):

        try:

            update_words()

        except Exception as e:

            print(
                f"❌ Failed to update AutoMod words: {e}"
            )


    @update_words_loop.before_loop
    async def before_words_loop(self):

        await self.bot.wait_until_ready()


    # =================================================
    # Message AutoMod
    # =================================================

    @commands.Cog.listener()
    async def on_message(
        self,
        message
    ):

        # Ignore bots
        if message.author.bot:
            return

        # Ignore DMs
        if message.guild is None:
            return

        # Ignore administrators
        if message.author.guild_permissions.administrator:
            return

        content = message.content.strip()

        if not content:
            return


        # =================================================
        # Check link
        # =================================================

        if contains_link(content):

            reason = "Links are not allowed."

            try:

                await message.delete()

            except (
                discord.NotFound,
                discord.Forbidden,
                discord.HTTPException
            ):

                pass


            punishment = await punish_member(
                message.author,
                reason
            )

            print(
                f"🛡️ AutoMod | {message.author} | "
                f"Link | {punishment}"
            )

            return


        # =================================================
        # Check forbidden words
        # =================================================

        if contains_bad_word(content):

            reason = (
                "Forbidden language is not allowed."
            )

            try:

                await message.delete()

            except (
                discord.NotFound,
                discord.Forbidden,
                discord.HTTPException
            ):

                pass


            punishment = await punish_member(
                message.author,
                reason
            )

            print(
                f"🛡️ AutoMod | {message.author} | "
                f"Forbidden language | {punishment}"
            )

            return


        # =================================================
        # Check spam
        # =================================================

        if is_spam(message):

            reason = "Spam is not allowed."

            try:

                await message.delete()

            except (
                discord.NotFound,
                discord.Forbidden,
                discord.HTTPException
            ):

                pass


            punishment = await punish_member(
                message.author,
                reason
            )

            print(
                f"🛡️ AutoMod | {message.author} | "
                f"Spam | {punishment}"
            )

            return


# =================================================
# Setup
# =================================================

async def setup(bot):

    await bot.add_cog(
        AutoMod(bot)
    )

    print(
        "✅ automod.py loaded!"
)
