import os
import re
import json
import time
import unicodedata
import urllib.parse
import urllib.request

from datetime import timedelta

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

# Обновление списка слов — каждые 24 часа
WORD_UPDATE_INTERVAL = 86400


# =================================================
# Anti Spam
# =================================================

SPAM_MESSAGES = 5
SPAM_INTERVAL = 6

DUPLICATE_MESSAGES = 3
DUPLICATE_INTERVAL = 10


# =================================================
# JSON
# =================================================

def load_json(
    filename,
    default
):

    if not os.path.exists(filename):

        return default

    try:

        with open(
            filename,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as e:

        print(
            f"❌ Failed to load {filename}: {e}"
        )

        return default


def save_json(
    filename,
    data
):

    temp_file = filename + ".tmp"

    try:

        with open(
            temp_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=4
            )

        os.replace(
            temp_file,
            filename
        )

    except Exception as e:

        print(
            f"❌ Failed to save {filename}: {e}"
        )


# =================================================
# Data
# =================================================

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
# Character normalization
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

    # Uppercase
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


def normalize_text(
    text
):

    if not text:

        return ""

    text = unicodedata.normalize(
        "NFKC",
        text
    )

    text = text.lower()

    text = text.translate(
        CONFUSABLES
    )

    # Убираем диакритические знаки
    text = "".join(
        char
        for char in unicodedata.normalize(
            "NFD",
            text
        )
        if unicodedata.category(char) != "Mn"
    )

    # Убираем пробелы и символы.
    # Например:
    # с.п.а.м -> спам
    # с п а м -> спам
    # с-п-а-м -> спам
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
                f"❌ Wiktionary request failed: {e}"
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


        continuation_data = data.get(
            "continue"
        )

        if not continuation_data:

            break


        continuation = continuation_data.get(
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
            f"✅ Wiktionary list updated: {len(result)} words."
        )

        return result


    print(
        "⚠️ Wiktionary returned no words. Using cached list."
    )

    return bad_words.get(
        "words",
        []
    )


# =================================================
# Word update
# =================================================

def update_words():

    global bad_words

    updated = bad_words.get(
        "updated",
        0
    )

    if (
        time.time() - updated
        < WORD_UPDATE_INTERVAL
    ):

        print(
            f"📚 AutoMod word cache: "
            f"{len(bad_words.get('words', []))} words."
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
# Bad word detection
# =================================================

def contains_bad_word(
    text
):

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


        # Полное совпадение
        if normalized == word:

            return True


        # Обнаружение внутри текста
        if len(word) >= 4:

            if word in normalized:

                return True


    return False


# =================================================
# Links
# =================================================

LINK_PATTERNS = [

    re.compile(
        r"https?://\S+",
        re.IGNORECASE
    ),

    re.compile(
        r"www\.\S+",
        re.IGNORECASE
    ),

    re.compile(
        r"discord\.gg/\S+",
        re.IGNORECASE
    ),

    re.compile(
        r"discord(?:app)?\.com/invite/\S+",
        re.IGNORECASE
    ),

    re.compile(
        r"\b[a-z0-9-]+\."
        r"(?:com|net|org|io|gg|me|ru|xyz|dev|app|site|online)"
        r"\b",
        re.IGNORECASE
    )

]


def contains_link(
    text
):

    for pattern in LINK_PATTERNS:

        if pattern.search(text):

            return True

    return False


# =================================================
# Spam tracking
# =================================================

message_history = {}


def is_spam(
    message
):

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


    # Удаляем старые сообщения
    history[:] = [
        item
        for item in history
        if now - item[0] <= SPAM_INTERVAL
    ]


    # Слишком много сообщений
    if len(history) >= SPAM_MESSAGES:

        return True


    # Одинаковые сообщения
    if len(history) >= DUPLICATE_MESSAGES:

        recent = [
            item[1].strip().lower()
            for item in history[
                -DUPLICATE_MESSAGES:
            ]
        ]

        if (
            len(recent) == DUPLICATE_MESSAGES
            and recent[0]
            and all(
                text == recent[0]
                for text in recent
            )
        ):

            return True


    return False


# =================================================
# Warning system
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
# DM notification
# =================================================

async def send_dm(
    member,
    guild,
    violation,
    punishment,
    count
):

    try:

        embed = discord.Embed(
            title="🛡️ AutoMod Action",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="Server",
            value=guild.name,
            inline=False
        )

        embed.add_field(
            name="Violation",
            value=violation,
            inline=False
        )

        embed.add_field(
            name="Punishment",
            value=punishment,
            inline=False
        )

        embed.add_field(
            name="Violation count",
            value=f"{count}/5",
            inline=False
        )

        embed.set_footer(
            text="Please follow the server rules."
        )

        await member.send(
            embed=embed
        )

        return True

    except (
        discord.Forbidden,
        discord.HTTPException
    ):

        print(
            f"⚠️ Could not DM {member}."
        )

        return False


# =================================================
# Punishment
# =================================================

async def punish_member(
    member,
    violation
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

        punishment = "⚠️ Warning"

        await send_dm(
            member,
            guild,
            violation,
            punishment,
            count
        )

        return punishment


    # =================================================
    # 2 — Mute 1 hour
    # =================================================

    if count == 2:

        punishment = "🔇 Mute for 1 hour"

        try:

            await member.edit(
                timed_out_until=(
                    discord.utils.utcnow()
                    + timedelta(hours=1)
                ),
                reason=violation
            )

        except (
            discord.Forbidden,
            discord.HTTPException
        ) as e:

            print(
                f"❌ Failed to mute {member}: {e}"
            )


        await send_dm(
            member,
            guild,
            violation,
            punishment,
            count
        )

        return punishment


    # =================================================
    # 3 — Mute 1 day
    # =================================================

    if count == 3:

        punishment = "🔇 Mute for 1 day"

        try:

            await member.edit(
                timed_out_until=(
                    discord.utils.utcnow()
                    + timedelta(days=1)
                ),
                reason=violation
            )

        except (
            discord.Forbidden,
            discord.HTTPException
        ) as e:

            print(
                f"❌ Failed to mute {member}: {e}"
            )


        await send_dm(
            member,
            guild,
            violation,
            punishment,
            count
        )

        return punishment


    # =================================================
    # 4 — Kick
    # =================================================

    if count == 4:

        punishment = "👢 Kick"

        await send_dm(
            member,
            guild,
            violation,
            punishment,
            count
        )

        try:

            await member.kick(
                reason=violation
            )

        except (
            discord.Forbidden,
            discord.HTTPException
        ) as e:

            print(
                f"❌ Failed to kick {member}: {e}"
            )


        return punishment


    # =================================================
    # 5 — Permanent Ban
    # =================================================

    punishment = "🔨 Permanent ban"

    await send_dm(
        member,
        guild,
        violation,
        punishment,
        count
    )

    try:

        await guild.ban(
            member,
            reason=violation,
            delete_message_days=0
        )

    except (
        discord.Forbidden,
        discord.HTTPException
    ) as e:

        print(
            f"❌ Failed to ban {member}: {e}"
        )


    return punishment


# =================================================
# AutoMod Cog
# =================================================

class AutoMod(
    commands.Cog
):

    def __init__(
        self,
        bot
    ):

        self.bot = bot

        self.update_words_loop.start()


    def cog_unload(
        self
    ):

        self.update_words_loop.cancel()


    # =================================================
    # Word update loop
    # =================================================

    @tasks.loop(
        seconds=WORD_UPDATE_INTERVAL
    )
    async def update_words_loop(
        self
    ):

        try:

            update_words()

        except Exception as e:

            print(
                f"❌ AutoMod word update failed: {e}"
            )


    @update_words_loop.before_loop
    async def before_words_loop(
        self
    ):

        await self.bot.wait_until_ready()


    # =================================================
    # Message AutoMod
    # =================================================

    @commands.Cog.listener()
    async def on_message(
        self,
        message
    ):

        # Игнорируем ботов
        if message.author.bot:

            return


        # Только серверы
        if message.guild is None:

            return


        # Администраторов не наказываем
        if message.author.guild_permissions.administrator:

            return


        content = message.content.strip()

        if not content:

            return


        # =================================================
        # LINK
        # =================================================

        if contains_link(content):

            violation = (
                "Sending links is not allowed."
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
                violation
            )

            print(
                f"🛡️ AutoMod | "
                f"{message.author} | "
                f"Link | "
                f"{punishment}"
            )

            return


        # =================================================
        # BAD WORD
        # =================================================

        if contains_bad_word(content):

            violation = (
                "Forbidden language."
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
                violation
            )

            print(
                f"🛡️ AutoMod | "
                f"{message.author} | "
                f"Forbidden language | "
                f"{punishment}"
            )

            return


        # =================================================
        # SPAM
        # =================================================

        if is_spam(message):

            violation = (
                "Spam."
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
                violation
            )

            print(
                f"🛡️ AutoMod | "
                f"{message.author} | "
                f"Spam | "
                f"{punishment}"
            )

            return


# =================================================
# Setup
# =================================================

async def setup(
    bot
):

    # Загружаем список сразу при старте
    try:

        update_words()

    except Exception as e:

        print(
            f"❌ Failed to update Wiktionary list: {e}"
        )


    await bot.add_cog(
        AutoMod(bot)
    )

    print(
        "✅ automod.py loaded!"
    )
