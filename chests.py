import os
import json
import random
import asyncio
import tempfile
import time

import discord
import numpy as np
from discord.ext import commands


DATA_FILE = "chests_data.json"

MENU_TIMEOUT = 300
DAILY_COOLDOWN = 86400
WEEKLY_COOLDOWN = 604800

ULTRA_ROLE_ID = 1529128872036143164
PHOENIX_ROLE_ID = 1557679056864940072

PHOENIX_MAX = 2

OWNER_ID = 1176149190192152626


LANGUAGES = {
    "en": "🇬🇧 English",
    "ru": "🇷🇺 Russian",
    "ro": "🇷🇴 Romanian",
    "uz": "🇺🇿 Uzbek",
    "kk": "🇰🇿 Kazakh",
    "tr": "🇹🇷 Turkish",
    "es": "🇪🇸 Spanish",
    "fr": "🇫🇷 French",
    "de": "🇩🇪 German",
    "it": "🇮🇹 Italian",
    "uk": "🇺🇦 Ukrainian",
    "pl": "🇵🇱 Polish"
}


ROLE_REWARDS = [
    {
        "name": {
            "en": "Common",
            "ru": "Обычная",
            "ro": "Comună",
            "uz": "Oddiy",
            "kk": "Кәдімгі",
            "tr": "Yaygın",
            "es": "Común",
            "fr": "Commune",
            "de": "Gewöhnlich",
            "it": "Comune",
            "uk": "Звичайна",
            "pl": "Zwykła"
        },
        "emoji": "⚪",
        "role_id": 1529127245128667308,
        "chance": 40.0
    },
    {
        "name": {
            "en": "Uncommon",
            "ru": "Необычная",
            "ro": "Neobișnuită",
            "uz": "Noodatiy",
            "kk": "Ерекше",
            "tr": "Sıradışı",
            "es": "Poco común",
            "fr": "Peu commune",
            "de": "Ungewöhnlich",
            "it": "Non comune",
            "uk": "Незвичайна",
            "pl": "Niezwykła"
        },
        "emoji": "🟢",
        "role_id": 1529155257081401575,
        "chance": 25.0
    },
    {
        "name": {
            "en": "Rare",
            "ru": "Редкая",
            "ro": "Rară",
            "uz": "Noyob",
            "kk": "Сирек",
            "tr": "Nadir",
            "es": "Rara",
            "fr": "Rare",
            "de": "Selten",
            "it": "Rara",
            "uk": "Рідкісна",
            "pl": "Rzadka"
        },
        "emoji": "🔵",
        "role_id": 1529127682392985731,
        "chance": 17.0
    },
    {
        "name": {
            "en": "Epic",
            "ru": "Эпическая",
            "ro": "Epică",
            "uz": "Epik",
            "kk": "Эпикалық",
            "tr": "Epik",
            "es": "Épica",
            "fr": "Épique",
            "de": "Episch",
            "it": "Epica",
            "uk": "Епічна",
            "pl": "Epicka"
        },
        "emoji": "🟣",
        "role_id": 1529127837192159494,
        "chance": 10.0
    },
    {
        "name": {
            "en": "Heroic",
            "ru": "Героическая",
            "ro": "Eroică",
            "uz": "Qahramonona",
            "kk": "Батырлық",
            "tr": "Kahramanca",
            "es": "Heroica",
            "fr": "Héroïque",
            "de": "Heldenhaft",
            "it": "Eroica",
            "uk": "Героїчна",
            "pl": "Bohaterska"
        },
        "emoji": "🟠",
        "role_id": 1529155677476356198,
        "chance": 5.0
    },
    {
        "name": {
            "en": "Mythic",
            "ru": "Мифическая",
            "ro": "Mitică",
            "uz": "Afsonaviy",
            "kk": "Мифтік",
            "tr": "Mistik",
            "es": "Mítica",
            "fr": "Mythique",
            "de": "Mythisch",
            "it": "Mitica",
            "uk": "Міфічна",
            "pl": "Mityczna"
        },
        "emoji": "🔴",
        "role_id": 1529128399094681760,
        "chance": 2.2
    },
    {
        "name": {
            "en": "Legendary",
            "ru": "Легендарная",
            "ro": "Legendară",
            "uz": "Afsonaviy",
            "kk": "Аңызға айналған",
            "tr": "Efsanevi",
            "es": "Legendaria",
            "fr": "Légendaire",
            "de": "Legendär",
            "it": "Leggendaria",
            "uk": "Легендарна",
            "pl": "Legendarną"
        },
        "emoji": "🟡",
        "role_id": 1529128791916544111,
        "chance": 0.6
    },
    {
        "name": {
            "en": "Cosmic",
            "ru": "Космическая",
            "ro": "Cosmică",
            "uz": "Kosmik",
            "kk": "Ғарыштық",
            "tr": "Kozmik",
            "es": "Cósmica",
            "fr": "Cosmique",
            "de": "Kosmisch",
            "it": "Cosmica",
            "uk": "Космічна",
            "pl": "Kosmiczna"
        },
        "emoji": "🌌",
        "role_id": 1529156030317990019,
        "chance": 0.15
    },
    {
        "name": {
            "en": "Galactic",
            "ru": "Галактическая",
            "ro": "Galactică",
            "uz": "Galaktik",
            "kk": "Галактикалық",
            "tr": "Galaktik",
            "es": "Galáctica",
            "fr": "Galactique",
            "de": "Galaktisch",
            "it": "Galattica",
            "uk": "Галактична",
            "pl": "Galaktyczna"
        },
        "emoji": "🌠",
        "role_id": 1529156293393383474,
        "chance": 0.04
    },
    {
        "name": {
            "en": "Ultra",
            "ru": "Ultra",
            "ro": "Ultra",
            "uz": "Ultra",
            "kk": "Ultra",
            "tr": "Ultra",
            "es": "Ultra",
            "fr": "Ultra",
            "de": "Ultra",
            "it": "Ultra",
            "uk": "Ultra",
            "pl": "Ultra"
        },
        "emoji": "💎",
        "role_id": ULTRA_ROLE_ID,
        "chance": 0.01
    },
    {
        "name": {
            "en": "Phoenix",
            "ru": "Phoenix",
            "ro": "Phoenix",
            "uz": "Phoenix",
            "kk": "Phoenix",
            "tr": "Phoenix",
            "es": "Phoenix",
            "fr": "Phoenix",
            "de": "Phoenix",
            "it": "Phoenix",
            "uk": "Phoenix",
            "pl": "Phoenix"
        },
        "emoji": "🔥",
        "role_id": PHOENIX_ROLE_ID,
        "chance": 0.001
    }
]


class Chests(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.data = self.load_data()

        self.save_lock = asyncio.Lock()
        self.open_lock = asyncio.Lock()

    # =========================================================
    # DATA
    # =========================================================

    def load_data(self):

        if not os.path.exists(DATA_FILE):
            return {"users": {}}

        try:
            with open(
                DATA_FILE,
                "r",
                encoding="utf-8"
            ) as file:
                data = json.load(file)

            if not isinstance(data, dict):
                raise ValueError("Invalid data")

            data.setdefault("users", {})

            if not isinstance(data["users"], dict):
                raise ValueError("Invalid users data")

            return data

        except Exception as e:

            print(
                f"❌ Failed to load {DATA_FILE}: {e}"
            )

            return {"users": {}}

    async def save_data(self):

        async with self.save_lock:

            directory = os.path.dirname(
                os.path.abspath(DATA_FILE)
            )

            fd, temp_path = tempfile.mkstemp(
                dir=directory,
                prefix="chests_",
                suffix=".tmp"
            )

            try:

                with os.fdopen(
                    fd,
                    "w",
                    encoding="utf-8"
                ) as file:

                    json.dump(
                        self.data,
                        file,
                        ensure_ascii=False,
                        indent=4
                    )

                    file.flush()
                    os.fsync(
                        file.fileno()
                    )

                os.replace(
                    temp_path,
                    DATA_FILE
                )

            except Exception:

                try:
                    os.remove(temp_path)
                except OSError:
                    pass

                raise

    def get_user_data(self, user_id):

        user_id = str(user_id)

        if user_id not in self.data["users"]:

            self.data["users"][user_id] = {
                "chests": 0,
                "mega_chests": 0,
                "ultra_chests": 0,
                "language": None,
                "daily_next": 0,
                "weekly_next": 0
            }

        user = self.data["users"][user_id]

        user.setdefault("chests", 0)
        user.setdefault("mega_chests", 0)
        user.setdefault("ultra_chests", 0)
        user.setdefault("language", None)
        user.setdefault("daily_next", 0)
        user.setdefault("weekly_next", 0)

        return user

    async def add_chests(
        self,
        user_id,
        amount,
        chest_type="chest"
    ):

        try:
            amount = int(amount)
        except (TypeError, ValueError):
            return False

        if amount <= 0:
            return False

        user = self.get_user_data(user_id)

        if chest_type == "chest":
            user["chests"] += amount

        elif chest_type == "mega":
            user["mega_chests"] += amount

        elif chest_type == "ultra":
            user["ultra_chests"] += amount

        else:
            return False

        await self.save_data()

        return True

    # =========================================================
    # LANGUAGE
    # =========================================================

    def language(self, user_id):

        language = self.get_user_data(
            user_id
        ).get("language")

        return language if language in LANGUAGES else "en"

    def t(
        self,
        user_id,
        key,
        **kwargs
    ):

        lang = self.language(user_id)

        texts = {

            "title": {
                "en": "🎁 Chests",
                "ru": "🎁 Сундуки",
                "ro": "🎁 Cufere",
                "uz": "🎁 Sandiqlar",
                "kk": "🎁 Сандықтар",
                "tr": "🎁 Sandıklar",
                "es": "🎁 Cofres",
                "fr": "🎁 Coffres",
                "de": "🎁 Truhen",
                "it": "🎁 Forzieri",
                "uk": "🎁 Скрині",
                "pl": "🎁 Skrzynie"
            },

            "language_prompt": {
                "en": "🌐 Select your language",
                "ru": "🌐 Выберите язык",
                "ro": "🌐 Selectează limba",
                "uz": "🌐 Tilni tanlang",
                "kk": "🌐 Тілді таңдаңыз",
                "tr": "🌐 Dilinizi seçin",
                "es": "🌐 Selecciona tu idioma",
                "fr": "🌐 Choisissez votre langue",
                "de": "🌐 Sprache auswählen",
                "it": "🌐 Seleziona la lingua",
                "uk": "🌐 Оберіть мову",
                "pl": "🌐 Wybierz język"
            },

            "normal_chest": {
                "en": "🎁 Chest",
                "ru": "🎁 Сундук",
                "ro": "🎁 Cufăr",
                "uz": "🎁 Sandıq",
                "kk": "🎁 Сандық",
                "tr": "🎁 Sandık",
                "es": "🎁 Cofre",
                "fr": "🎁 Coffre",
                "de": "🎁 Truhe",
                "it": "🎁 Forziere",
                "uk": "🎁 Скриня",
                "pl": "🎁 Skrzynia"
            },

            "mega_chest": {
                "en": "💎 Mega Chest",
                "ru": "💎 Mega Chest",
                "ro": "💎 Mega Chest",
                "uz": "💎 Mega Chest",
                "kk": "💎 Mega Chest",
                "tr": "💎 Mega Chest",
                "es": "💎 Mega Chest",
                "fr": "💎 Mega Chest",
                "de": "💎 Mega Chest",
                "it": "💎 Mega Chest",
                "uk": "💎 Mega Chest",
                "pl": "💎 Mega Chest"
            },

            "ultra_chest": {
                "en": "⚡ Ultra Chest",
                "ru": "⚡ Ultra Chest",
                "ro": "⚡ Ultra Chest",
                "uz": "⚡ Ultra Chest",
                "kk": "⚡ Ultra Chest",
                "tr": "⚡ Ultra Chest",
                "es": "⚡ Ultra Chest",
                "fr": "⚡ Ultra Chest",
                "de": "⚡ Ultra Chest",
                "it": "⚡ Ultra Chest",
                "uk": "⚡ Ultra Chest",
                "pl": "⚡ Ultra Chest"
            },

            "chest": {
                "en": "🎁 Chest: {value}",
                "ru": "🎁 Сундук: {value}",
                "ro": "🎁 Cufere: {value}",
                "uz": "🎁 Sandıqlar: {value}",
                "kk": "🎁 Сандықтар: {value}",
                "tr": "🎁 Sandık: {value}",
                "es": "🎁 Cofres: {value}",
                "fr": "🎁 Coffres: {value}",
                "de": "🎁 Truhen: {value}",
                "it": "🎁 Forzieri: {value}",
                "uk": "🎁 Скрині: {value}",
                "pl": "🎁 Skrzynie: {value}"
            },

            "mega": {
                "en": "💎 Mega Chest: {value}",
                "ru": "💎 Mega Chest: {value}",
                "ro": "💎 Mega Chest: {value}",
                "uz": "💎 Mega Chest: {value}",
                "kk": "💎 Mega Chest: {value}",
                "tr": "💎 Mega Chest: {value}",
                "es": "💎 Mega Chest: {value}",
                "fr": "💎 Mega Chest: {value}",
                "de": "💎 Mega Chest: {value}",
                "it": "💎 Mega Chest: {value}",
                "uk": "💎 Mega Chest: {value}",
                "pl": "💎 Mega Chest: {value}"
            },

            "ultra": {
                "en": "⚡ Ultra Chest: {value}",
                "ru": "⚡ Ultra Chest: {value}",
                "ro": "⚡ Ultra Chest: {value}",
                "uz": "⚡ Ultra Chest: {value}",
                "kk": "⚡ Ultra Chest: {value}",
                "tr": "⚡ Ultra Chest: {value}",
                "es": "⚡ Ultra Chest: {value}",
                "fr": "⚡ Ultra Chest: {value}",
                "de": "⚡ Ultra Chest: {value}",
                "it": "⚡ Ultra Chest: {value}",
                "uk": "⚡ Ultra Chest: {value}",
                "pl": "⚡ Ultra Chest: {value}"
            },

            "total": {
                "en": "Total: {value} Chests",
                "ru": "Всего: {value} сундуков",
                "ro": "Total: {value} cufere",
                "uz": "Jami: {value} sandıq",
                "kk": "Барлығы: {value} сандық",
                "tr": "Toplam: {value} sandık",
                "es": "Total: {value} cofres",
                "fr": "Total : {value} coffres",
                "de": "Gesamt: {value} Truhen",
                "it": "Totale: {value} forzieri",
                "uk": "Всього: {value} скринь",
                "pl": "Łącznie: {value} skrzyń"
            },

            "daily_available": {
                "en": "📅 Daily Chest: Available",
                "ru": "📅 Ежедневный сундук: Доступен",
                "ro": "📅 Cufăr zilnic: Disponibil",
                "uz": "📅 Kunlik sandıq: Mavjud",
                "kk": "📅 Күнделікті сандық: Қолжетімді",
                "tr": "📅 Günlük Sandık: Hazır",
                "es": "📅 Cofre diario: Disponible",
                "fr": "📅 Coffre quotidien : Disponible",
                "de": "📅 Tägliche Truhe: Verfügbar",
                "it": "📅 Forziere giornaliero: Disponibile",
                "uk": "📅 Щоденна скриня: Доступна",
                "pl": "📅 Dzienna skrzynia: Dostępna"
            },

            "weekly_available": {
                "en": "📆 Weekly Mega: Available",
                "ru": "📆 Еженедельный Mega: Доступен",
                "ro": "📆 Mega săptămânal: Disponibil",
                "uz": "📆 Haftalik Mega: Mavjud",
                "kk": "📆 Апталық Mega: Қолжетімді",
                "tr": "📆 Haftalık Mega: Hazır",
                "es": "📆 Mega semanal: Disponible",
                "fr": "📆 Mega hebdomadaire : Disponible",
                "de": "📆 Wöchentlicher Mega: Verfügbar",
                "it": "📆 Mega settimanale: Disponibile",
                "uk": "📆 Щотижневий Mega: Доступний",
                "pl": "📆 Tygodniowy Mega: Dostępny"
            },

            "daily_next": {
                "en": "📅 Daily Chest: {timestamp}",
                "ru": "📅 Ежедневный сундук: {timestamp}",
                "ro": "📅 Cufăr zilnic: {timestamp}",
                "uz": "📅 Kunlik sandıq: {timestamp}",
                "kk": "📅 Күнделікті сандық: {timestamp}",
                "tr": "📅 Günlük Sandık: {timestamp}",
                "es": "📅 Cofre diario: {timestamp}",
                "fr": "📅 Coffre quotidien : {timestamp}",
                "de": "📅 Tägliche Truhe: {timestamp}",
                "it": "📅 Forziere giornaliero: {timestamp}",
                "uk": "📅 Щоденна скриня: {timestamp}",
                "pl": "📅 Dzienna skrzynia: {timestamp}"
            },

            "weekly_next": {
                "en": "📆 Weekly Mega: {timestamp}",
                "ru": "📆 Еженедельный Mega: {timestamp}",
                "ro": "📆 Mega săptămânal: {timestamp}",
                "uz": "📆 Haftalik Mega: {timestamp}",
                "kk": "📆 Апталық Mega: {timestamp}",
                "tr": "📆 Haftalık Mega: {timestamp}",
                "es": "📆 Mega semanal: {timestamp}",
                "fr": "📆 Mega hebdomadaire : {timestamp}",
                "de": "📆 Wöchentlicher Mega: {timestamp}",
                "it": "📆 Mega settimanale: {timestamp}",
                "uk": "📆 Щотижневий Mega: {timestamp}",
                "pl": "📆 Tygodniowy Mega: {timestamp}"
            },

            "open_one": {
                "en": "🔓 Open",
                "ru": "🔓 Открыть",
                "ro": "🔓 Deschide",
                "uz": "🔓 Ochish",
                "kk": "🔓 Ашу",
                "tr": "🔓 Aç",
                "es": "🔓 Abrir",
                "fr": "🔓 Ouvrir",
                "de": "🔓 Öffnen",
                "it": "🔓 Apri",
                "uk": "🔓 Відкрити",
                "pl": "🔓 Otwórz"
            },

            "open_all": {
                "en": "📦 Open All",
                "ru": "📦 Открыть все",
                "ro": "📦 Deschide tot",
                "uz": "📦 Hammasini ochish",
                "kk": "📦 Барлығын ашу",
                "tr": "📦 Hepsini Aç",
                "es": "📦 Abrir todo",
                "fr": "📦 Tout ouvrir",
                "de": "📦 Alle öffnen",
                "it": "📦 Apri tutto",
                "uk": "📦 Відкрити все",
                "pl": "📦 Otwórz wszystko"
            },

            "back": {
                "en": "🔙 Back",
                "ru": "🔙 Назад",
                "ro": "🔙 Înapoi",
                "uz": "🔙 Orqaga",
                "kk": "🔙 Артқа",
                "tr": "🔙 Geri",
                "es": "🔙 Atrás",
                "fr": "🔙 Retour",
                "de": "🔙 Zurück",
                "it": "🔙 Indietro",
                "uk": "🔙 Назад",
                "pl": "🔙 Wstecz"
            },

            "info": {
                "en": "ℹ️ Chest Information",
                "ru": "ℹ️ Информация о сундуках",
                "ro": "ℹ️ Informații despre cufere",
                "uz": "ℹ️ Sandiqlar haqida",
                "kk": "ℹ️ Сандықтар туралы ақпарат",
                "tr": "ℹ️ Sandık Bilgileri",
                "es": "ℹ️ Información de cofres",
                "fr": "ℹ️ Informations sur les coffres",
                "de": "ℹ️ Truheninformationen",
                "it": "ℹ️ Informazioni sui forzieri",
                "uk": "ℹ️ Інформація про скрині",
                "pl": "ℹ️ Informacje o skrzyniach"
            },

            "not_owner": {
                "en": "❌ These chests don't belong to you.",
                "ru": "❌ Эти сундуки принадлежат не вам.",
                "ro": "❌ Aceste cufere nu îți aparțin.",
                "uz": "❌ Bu sandiqlar sizniki emas.",
                "kk": "❌ Бұл сандықтар сізге тиесілі емес.",
                "tr": "❌ Bu sandıklar sana ait değil.",
                "es": "❌ Estos cofres no te pertenecen.",
                "fr": "❌ Ces coffres ne vous appartiennent pas.",
                "de": "❌ Diese Truhen gehören dir nicht.",
                "it": "❌ Questi forzieri non ti appartengono.",
                "uk": "❌ Ці скрині не належать вам.",
                "pl": "❌ Te skrzynie nie należą do ciebie."
            },

            "expired": {
                "en": "⏰ This chest menu has expired. Use !chests again.",
                "ru": "⏰ Срок действия меню истёк. Используйте !chests снова.",
                "ro": "⏰ Meniul a expirat. Folosește din nou !chests.",
                "uz": "⏰ Menyu muddati tugadi. !chests ni qayta ishlating.",
                "kk": "⏰ Мәзірдің мерзімі аяқталды. !chests қайта қолданыңыз.",
                "tr": "⏰ Sandık menüsünün süresi doldu. !chests kullanın.",
                "es": "⏰ El menú expiró. Usa !chests de nuevo.",
                "fr": "⏰ Le menu a expiré. Utilisez !chests.",
                "de": "⏰ Das Menü ist abgelaufen. Nutze !chests erneut.",
                "it": "⏰ Il menu è scaduto. Usa di nuovo !chests.",
                "uk": "⏰ Термін дії меню минув. Використайте !chests.",
                "pl": "⏰ Menu wygasło. Użyj ponownie !chests."
            },

            "no_chests": {
                "en": "❌ You don't have any of these chests.",
                "ru": "❌ У вас нет таких сундуков.",
                "ro": "❌ Nu ai astfel de cufere.",
                "uz": "❌ Sizda bunday sandiq yo‘q.",
                "kk": "❌ Сізде мұндай сандық жоқ.",
                "tr": "❌ Bu sandıktan sende yok.",
                "es": "❌ No tienes estos cofres.",
                "fr": "❌ Vous n'avez pas ce coffre.",
                "de": "❌ Du hast keine solchen Truhen.",
                "it": "❌ Non hai questi forzieri.",
                "uk": "❌ У вас немає таких скринь.",
                "pl": "❌ Nie masz takich skrzyń."
            },

            "phoenix_block": {
                "en": "🔥 You cannot open or claim chests because you already have the Phoenix role.",
                "ru": "🔥 Вы не можете открывать или получать сундуки, потому что у вас уже есть роль Phoenix.",
                "ro": "🔥 Nu poți deschide sau revendica cufere deoarece ai deja rolul Phoenix.",
                "uz": "🔥 Siz Phoenix roliga ega bo‘lganingiz uchun sandiqlarni ocholmaysiz yoki ololmaysiz.",
                "kk": "🔥 Сізде Phoenix рөлі бар, сондықтан сандықтарды аша немесе ала алмайсыз.",
                "tr": "🔥 Phoenix rolüne sahip olduğun için sandık açamaz veya alamazsın.",
                "es": "🔥 No puedes abrir ni reclamar cofres porque tienes el rol Phoenix.",
                "fr": "🔥 Vous ne pouvez pas ouvrir ou récupérer des coffres car vous avez le rôle Phoenix.",
                "de": "🔥 Du kannst keine Truhen öffnen oder beanspruchen, da du die Phoenix-Rolle hast.",
                "it": "🔥 Non puoi aprire o riscattare forzieri perché possiedi il ruolo Phoenix.",
                "uk": "🔥 Ви не можете відкривати або отримувати скрині, бо маєте роль Phoenix.",
                "pl": "🔥 Nie możesz otwierać ani odbierać skrzyń, ponieważ masz rolę Phoenix."
            },

            "daily_unavailable": {
                "en": "❌ Daily Chest is not available yet.\nNext: {timestamp}",
                "ru": "❌ Ежедневный сундук пока недоступен.\nСледующий: {timestamp}",
                "ro": "❌ Cufărul zilnic nu este încă disponibil.\nUrmătorul: {timestamp}",
                "uz": "❌ Kunlik sandıq hali mavjud emas.\nKeyingisi: {timestamp}",
                "kk": "❌ Күнделікті сандық әлі қолжетімсіз.\nКелесі: {timestamp}",
                "tr": "❌ Günlük Sandık henüz hazır değil.\nSonraki: {timestamp}",
                "es": "❌ El cofre diario aún no está disponible.\nSiguiente: {timestamp}",
                "fr": "❌ Le coffre quotidien n'est pas encore disponible.\nSuivant : {timestamp}",
                "de": "❌ Die tägliche Truhe ist noch nicht verfügbar.\nNächste: {timestamp}",
                "it": "❌ Il forziere giornaliero non è ancora disponibile.\nProssimo: {timestamp}",
                "uk": "❌ Щоденна скриня ще недоступна.\nНаступна: {timestamp}",
                "pl": "❌ Dzienna skrzynia nie jest jeszcze dostępna.\nNastępna: {timestamp}"
            },

            "weekly_unavailable": {
                "en": "❌ Weekly Mega is not available yet.\nNext: {timestamp}",
                "ru": "❌ Еженедельный Mega пока недоступен.\nСледующий: {timestamp}",
                "ro": "❌ Mega săptămânal nu este încă disponibil.\nUrmătorul: {timestamp}",
                "uz": "❌ Haftalik Mega hali mavjud emas.\nKeyingisi: {timestamp}",
                "kk": "❌ Апталық Mega әлі қолжетімсіз.\nКелесі: {timestamp}",
                "tr": "❌ Haftalık Mega henüz hazır değil.\nSonraki: {timestamp}",
                "es": "❌ El Mega semanal aún no está disponible.\nSiguiente: {timestamp}",
                "fr": "❌ Le Mega hebdomadaire n'est pas encore disponible.\nSuivant : {timestamp}",
                "de": "❌ Der wöchentliche Mega ist noch nicht verfügbar.\nNächster: {timestamp}",
                "it": "❌ Il Mega settimanale non è ancora disponibile.\nProssimo: {timestamp}",
                "uk": "❌ Щотижневий Mega ще недоступний.\nНаступний: {timestamp}",
                "pl": "❌ Tygodniowy Mega nie jest jeszcze dostępny.\nNastępny: {timestamp}"
            },

            "reward": {
                "en": "🏆 Reward:",
                "ru": "🏆 Награда:",
                "ro": "🏆 Recompensă:",
                "uz": "🏆 Mukofot:",
                "kk": "🏆 Сыйлық:",
                "tr": "🏆 Ödül:",
                "es": "🏆 Recompensa:",
                "fr": "🏆 Récompense :",
                "de": "🏆 Belohnung:",
                "it": "🏆 Ricompensa:",
                "uk": "🏆 Нагорода:",
                "pl": "🏆 Nagroda:"
            },

            "role_not_given": {
                "en": "⬇️ Your current role is higher or equal. The reward was not given.",
                "ru": "⬇️ Ваша текущая роль выше или такая же. Награда не выдана.",
                "ro": "⬇️ Rolul tău actual este mai mare sau egal. Recompensa nu a fost oferită.",
                "uz": "⬇️ Hozirgi rolingiz yuqori yoki teng. Mukofot berilmadi.",
                "kk": "⬇️ Қазіргі рөліңіз жоғары немесе тең. Сыйлық берілмеді.",
                "tr": "⬇️ Mevcut rolün daha yüksek veya eşit. Ödül verilmedi.",
                "es": "⬇️ Tu rol actual es superior o igual. No se otorgó la recompensa.",
                "fr": "⬇️ Votre rôle actuel est supérieur ou égal. La récompense n'a pas été donnée.",
                "de": "⬇️ Deine aktuelle Rolle ist höher oder gleich. Die Belohnung wurde nicht vergeben.",
                "it": "⬇️ Il tuo ruolo attuale è superiore o uguale. La ricompensa non è stata assegnata.",
                "uk": "⬇️ Ваша поточна роль вища або така сама. Нагороду не видано.",
                "pl": "⬇️ Twoja obecna rola jest wyższa lub równa. Nagroda nie została przyznana."
            },

            "bonus": {
                "en": "💎 Bonus:",
                "ru": "💎 Бонус:",
                "ro": "💎 Bonus:",
                "uz": "💎 Bonus:",
                "kk": "💎 Бонус:",
                "tr": "💎 Bonus:",
                "es": "💎 Bonificación:",
                "fr": "💎 Bonus :",
                "de": "💎 Bonus:",
                "it": "💎 Bonus:",
                "uk": "💎 Бонус:",
                "pl": "💎 Bonus:"
            },

            "mega_bonus": {
                "en": "+1 Mega Chest",
                "ru": "+1 Mega Chest",
                "ro": "+1 Mega Chest",
                "uz": "+1 Mega Chest",
                "kk": "+1 Mega Chest",
                "tr": "+1 Mega Chest",
                "es": "+1 Mega Chest",
                "fr": "+1 Mega Chest",
                "de": "+1 Mega Chest",
                "it": "+1 Mega Chest",
                "uk": "+1 Mega Chest",
                "pl": "+1 Mega Chest"
            },

            "ultra_bonus": {
                "en": "+1 Ultra Chest",
                "ru": "+1 Ultra Chest",
                "ro": "+1 Ultra Chest",
                "uz": "+1 Ultra Chest",
                "kk": "+1 Ultra Chest",
                "tr": "+1 Ultra Chest",
                "es": "+1 Ultra Chest",
                "fr": "+1 Ultra Chest",
                "de": "+1 Ultra Chest",
                "it": "+1 Ultra Chest",
                "uk": "+1 Ultra Chest",
                "pl": "+1 Ultra Chest"
            },

            "remaining_chest": {
                "en": "📦 Chest remaining: {value}",
                "ru": "📦 Осталось сундуков: {value}",
                "ro": "📦 Cufere rămase: {value}",
                "uz": "📦 Qolgan sandiqlar: {value}",
                "kk": "📦 Қалған сандықтар: {value}",
                "tr": "📦 Kalan sandık: {value}",
                "es": "📦 Cofres restantes: {value}",
                "fr": "📦 Coffres restants : {value}",
                "de": "📦 Verbleibende Truhen: {value}",
                "it": "📦 Forzieri rimasti: {value}",
                "uk": "📦 Залишилось скринь: {value}",
                "pl": "📦 Pozostałe skrzynie: {value}"
            },

            "remaining_mega": {
                "en": "💎 Mega Chest remaining: {value}",
                "ru": "💎 Осталось Mega Chest: {value}",
                "ro": "💎 Mega Chest rămase: {value}",
                "uz": "💎 Qolgan Mega Chest: {value}",
                "kk": "💎 Қалған Mega Chest: {value}",
                "tr": "💎 Kalan Mega Chest: {value}",
                "es": "💎 Mega Chest restantes: {value}",
                "fr": "💎 Mega Chest restants : {value}",
                "de": "💎 Verbleibende Mega Chest: {value}",
                "it": "💎 Mega Chest rimasti: {value}",
                "uk": "💎 Залишилось Mega Chest: {value}",
                "pl": "💎 Pozostałe Mega Chest: {value}"
            },

            "remaining_ultra": {
                "en": "⚡ Ultra Chest remaining: {value}",
                "ru": "⚡ Осталось Ultra Chest: {value}",
                "ro": "⚡ Ultra Chest rămase: {value}",
                "uz": "⚡ Qolgan Ultra Chest: {value}",
                "kk": "⚡ Қалған Ultra Chest: {value}",
                "tr": "⚡ Kalan Ultra Chest: {value}",
                "es": "⚡ Ultra Chest restantes: {value}",
                "fr": "⚡ Ultra Chest restants : {value}",
                "de": "⚡ Verbleibende Ultra Chest: {value}",
                "it": "⚡ Ultra Chest rimasti: {value}",
                "uk": "⚡ Залишилось Ultra Chest: {value}",
                "pl": "⚡ Pozostałe Ultra Chest: {value}"
            },

            "opened_all": {
                "en": "🎁 Opened All",
                "ru": "🎁 Открыты все",
                "ro": "🎁 Toate deschise",
                "uz": "🎁 Hammasi ochildi",
                "kk": "🎁 Барлығы ашылды",
                "tr": "🎁 Hepsi Açıldı",
                "es": "🎁 Todos abiertos",
                "fr": "🎁 Tous ouverts",
                "de": "🎁 Alle geöffnet",
                "it": "🎁 Tutti aperti",
                "uk": "🎁 Усі відкрито",
                "pl": "🎁 Wszystkie otwarte"
            },

            "chest_opened": {
                "en": "🎁 Chest Opened!",
                "ru": "🎁 Сундук открыт!",
                "ro": "🎁 Cufăr deschis!",
                "uz": "🎁 Sandıq ochildi!",
                "kk": "🎁 Сандық ашылды!",
                "tr": "🎁 Sandık Açıldı!",
                "es": "🎁 ¡Cofre abierto!",
                "fr": "🎁 Coffre ouvert !",
                "de": "🎁 Truhe geöffnet!",
                "it": "🎁 Forziere aperto!",
                "uk": "🎁 Скриню відкрито!",
                "pl": "🎁 Skrzynia otwarta!"
            },

            "mega_opened": {
                "en": "💎 Mega Chest Opened!",
                "ru": "💎 Mega Chest открыт!",
                "ro": "💎 Mega Chest deschis!",
                "uz": "💎 Mega Chest ochildi!",
                "kk": "💎 Mega Chest ашылды!",
                "tr": "💎 Mega Chest Açıldı!",
                "es": "💎 ¡Mega Chest abierto!",
                "fr": "💎 Mega Chest ouvert !",
                "de": "💎 Mega Chest geöffnet!",
                "it": "💎 Mega Chest aperto!",
                "uk": "💎 Mega Chest відкрито!",
                "pl": "💎 Mega Chest otwarty!"
            },

            "ultra_opened": {
                "en": "⚡ Ultra Chest Opened!",
                "ru": "⚡ Ultra Chest открыт!",
                "ro": "⚡ Ultra Chest deschis!",
                "uz": "⚡ Ultra Chest ochildi!",
                "kk": "⚡ Ultra Chest ашылды!",
                "tr": "⚡ Ultra Chest Açıldı!",
                "es": "⚡ ¡Ultra Chest abierto!",
                "fr": "⚡ Ultra Chest ouvert !",
                "de": "⚡ Ultra Chest geöffnet!",
                "it": "⚡ Ultra Chest aperto!",
                "uk": "⚡ Ultra Chest відкрито!",
                "pl": "⚡ Ultra Chest otwarty!"
            },

            "daily_claimed": {
                "en": "📅 Daily Chest Claimed!",
                "ru": "📅 Ежедневный сундук получен!",
                "ro": "📅 Cufărul zilnic primit!",
                "uz": "📅 Kunlik sandıq olindi!",
                "kk": "📅 Күнделікті сандық алынды!",
                "tr": "📅 Günlük Sandık Alındı!",
                "es": "📅 ¡Cofre diario reclamado!",
                "fr": "📅 Coffre quotidien récupéré !",
                "de": "📅 Tägliche Truhe erhalten!",
                "it": "📅 Forziere giornaliero ottenuto!",
                "uk": "📅 Щоденну скриню отримано!",
                "pl": "📅 Dzienna skrzynia odebrana!"
            },

            "weekly_claimed": {
                "en": "📆 Weekly Mega Claimed!",
                "ru": "📆 Еженедельный Mega получен!",
                "ro": "📆 Mega săptămânal primit!",
                "uz": "📆 Haftalik Mega olindi!",
                "kk": "📆 Апталық Mega алынды!",
                "tr": "📆 Haftalık Mega Alındı!",
                "es": "📆 ¡Mega semanal reclamado!",
                "fr": "📆 Mega hebdomadaire récupéré !",
                "de": "📆 Wöchentlicher Mega erhalten!",
                "it": "📆 Mega settimanale ottenuto!",
                "uk": "📆 Щотижневий Mega отримано!",
                "pl": "📆 Tygodniowy Mega odebrany!"
            },

            "normal_description": {
                "en": "Open one Chest or open all Chests.",
                "ru": "Откройте один сундук или все сундуки.",
                "ro": "Deschide un cufăr sau toate cuferele.",
                "uz": "Bitta yoki barcha sandiqlarni oching.",
                "kk": "Бір немесе барлық сандықтарды ашыңыз.",
                "tr": "Bir sandık veya tüm sandıkları aç.",
                "es": "Abre un cofre o todos los cofres.",
                "fr": "Ouvrez un coffre ou tous les coffres.",
                "de": "Öffne eine oder alle Truhen.",
                "it": "Apri un forziere o tutti i forzieri.",
                "uk": "Відкрийте одну або всі скрині.",
                "pl": "Otwórz jedną lub wszystkie skrzynie."
            },

            "mega_description": {
                "en": "Gives 1–10 normal Chests. 5% chance: 20.",
                "ru": "Даёт 1–10 обычных сундуков. Шанс 5%: 20.",
                "ro": "Oferă 1–10 cufere normale. Șansă 5%: 20.",
                "uz": "1–10 oddiy sandıq beradi. 5% imkoniyat: 20.",
                "kk": "1–10 кәдімгі сандық береді. 5% мүмкіндік: 20.",
                "tr": "1–10 normal Sandık verir. %5 şans: 20.",
                "es": "Da 1–10 cofres normales. 5% de probabilidad: 20.",
                "fr": "Donne 1–10 coffres normaux. 5 % : 20.",
                "de": "Gibt 1–10 normale Truhen. 5 % Chance: 20.",
                "it": "Dà 1–10 forzieri normali. 5% di possibilità: 20.",
                "uk": "Дає 1–10 звичайних скринь. Шанс 5%: 20.",
                "pl": "Daje 1–10 zwykłych skrzyń. 5% szans: 20."
            },

            "ultra_description": {
                "en": "Gives 10–20 normal Chests. 5% chance: 30.",
                "ru": "Даёт 10–20 обычных сундуков. Шанс 5%: 30.",
                "ro": "Oferă 10–20 cufere normale. Șansă 5%: 30.",
                "uz": "10–20 oddiy sandıq beradi. 5% imkoniyat: 30.",
                "kk": "10–20 кәдімгі сандық береді. 5% мүмкіндік: 30.",
                "tr": "10–20 normal Sandık verir. %5 şans: 30.",
                "es": "Da 10–20 cofres normales. 5% de probabilidad: 30.",
                "fr": "Donne 10–20 coffres normaux. 5 % : 30.",
                "de": "Gibt 10–20 normale Truhen. 5 % Chance: 30.",
                "it": "Dà 10–20 forzieri normali. 5% di possibilità: 30.",
                "uk": "Дає 10–20 звичайних скринь. Шанс 5%: 30.",
                "pl": "Daje 10–20 zwykłych skrzyń. 5% szans: 30."
            },

            "normal_amount": {
                "en": "🎁 Chest × {amount}",
                "ru": "🎁 Сундук × {amount}",
                "ro": "🎁 Cufăr × {amount}",
                "uz": "🎁 Sandıq × {amount}",
                "kk": "🎁 Сандық × {amount}",
                "tr": "🎁 Sandık × {amount}",
                "es": "🎁 Cofre × {amount}",
                "fr": "🎁 Coffre × {amount}",
                "de": "🎁 Truhe × {amount}",
                "it": "🎁 Forziere × {amount}",
                "uk": "🎁 Скриня × {amount}",
                "pl": "🎁 Skrzynia × {amount}"
            },

            "lucky": {
                "en": "⭐ Lucky reward: {amount} × {reward}",
                "ru": "⭐ Удачная награда: {amount} × {reward}",
                "ro": "⭐ Recompensă norocoasă: {amount} × {reward}",
                "uz": "⭐ Omadli mukofot: {amount} × {reward}",
                "kk": "⭐ Сәтті сыйлық: {amount} × {reward}",
                "tr": "⭐ Şanslı ödül: {amount} × {reward}",
                "es": "⭐ Recompensa afortunada: {amount} × {reward}",
                "fr": "⭐ Récompense chanceuse : {amount} × {reward}",
                "de": "⭐ Glücksbelohnung: {amount} × {reward}",
                "it": "⭐ Ricompensa fortunata: {amount} × {reward}",
                "uk": "⭐ Щаслива нагорода: {amount} × {reward}",
                "pl": "⭐ Szczęśliwa nagroda: {amount} × {reward}"
            },

            "normal_word": {
                "en": "Chest",
                "ru": "Сундук",
                "ro": "Cufăr",
                "uz": "Sandıq",
                "kk": "Сандық",
                "tr": "Sandık",
                "es": "Cofre",
                "fr": "Coffre",
                "de": "Truhe",
                "it": "Forziere",
                "uk": "Скриня",
                "pl": "Skrzynia"
            },

            "error": {
                "en": "❌ Something went wrong.",
                "ru": "❌ Произошла ошибка.",
                "ro": "❌ Ceva a mers prost.",
                "uz": "❌ Xatolik yuz berdi.",
                "kk": "❌ Қате орын алды.",
                "tr": "❌ Bir şeyler ters gitti.",
                "es": "❌ Algo salió mal.",
                "fr": "❌ Une erreur est survenue.",
                "de": "❌ Etwas ist schiefgelaufen.",
                "it": "❌ Qualcosa è andato storto.",
                "uk": "❌ Щось пішло не так.",
                "pl": "❌ Coś poszło nie tak."
            },

            "info_text": {
                "en": (
                    "**🎁 NORMAL CHEST**\n"
                    "⚪ Common — 40%\n"
                    "🟢 Uncommon — 25%\n"
                    "🔵 Rare — 17%\n"
                    "🟣 Epic — 10%\n"
                    "🟠 Heroic — 5%\n"
                    "🔴 Mythic — 2.2%\n"
                    "🟡 Legendary — 0.6%\n"
                    "🌌 Cosmic — 0.15%\n"
                    "🌠 Galactic — 0.04%\n"
                    "💎 Ultra — 0.01%\n"
                    "🔥 Phoenix — 0.001% (2/2 max)\n"
                    "5% → +1 Mega Chest\n"
                    "1% → +1 Ultra Chest\n\n"
                    "**💎 MEGA CHEST**\n"
                    "Gives 1–10 normal Chests.\n"
                    "5% → 20 normal Chests.\n\n"
                    "**⚡ ULTRA CHEST**\n"
                    "Gives 10–20 normal Chests.\n"
                    "5% → 30 normal Chests.\n\n"
                    "**📅 DAILY**\n"
                    "Available every 24 hours.\n"
                    "Role reward + 5% Mega + 1% Ultra.\n\n"
                    "**📆 WEEKLY**\n"
                    "Available every 7 days.\n"
                    "1–10 normal Chests, 5% → 20.\n\n"
                    "**🔥 PHOENIX**\n"
                    "Highest role. Maximum 2 users.\n"
                    "Phoenix holders cannot open or claim chests.\n"
                    "Ultra holders can still open and claim chests.\n\n"
                    "**🏆 ROLE SYSTEM**\n"
                    "A higher role replaces a lower role.\n"
                    "Equal or lower rewards are not given.\n"
                    "Open All rolls rewards independently for every chest.\n\n"
                    "**🌐 LANGUAGES**\n"
                    "English, Russian, Romanian, Uzbek, Kazakh, Turkish,\n"
                    "Spanish, French, German, Italian, Ukrainian, Polish.\n\n"
                    "**⏰ MENU**\n"
                    "The menu is active for 5 minutes.\n"
                    "Use !chests to open a new menu.\n"
                    "Use !chest info for this information."
                ),

                "ru": (
                    "**🎁 ОБЫЧНЫЙ СУНДУК**\n"
                    "⚪ Обычная — 40%\n"
                    "🟢 Необычная — 25%\n"
                    "🔵 Редкая — 17%\n"
                    "🟣 Эпическая — 10%\n"
                    "🟠 Героическая — 5%\n"
                    "🔴 Мифическая — 2.2%\n"
                    "🟡 Легендарная — 0.6%\n"
                    "🌌 Космическая — 0.15%\n"
                    "🌠 Галактическая — 0.04%\n"
                    "💎 Ultra — 0.01%\n"
                    "🔥 Phoenix — 0.001% (максимум 2/2)\n"
                    "5% → +1 Mega Chest\n"
                    "1% → +1 Ultra Chest\n\n"
                    "**💎 MEGA CHEST**\n"
                    "Даёт 1–10 обычных сундуков.\n"
                    "5% → 20 обычных сундуков.\n\n"
                    "**⚡ ULTRA CHEST**\n"
                    "Даёт 10–20 обычных сундуков.\n"
                    "5% → 30 обычных сундуков.\n\n"
                    "**📅 DAILY**\n"
                    "Доступен каждые 24 часа.\n"
                    "Награда роли + 5% Mega + 1% Ultra.\n\n"
                    "**📆 WEEKLY**\n"
                    "Доступен каждые 7 дней.\n"
                    "1–10 обычных сундуков, 5% → 20.\n\n"
                    "**🔥 PHOENIX**\n"
                    "Самая высокая роль. Максимум 2 пользователя.\n"
                    "Владельцы Phoenix не могут открывать или получать сундуки.\n"
                    "Владельцы Ultra всё ещё могут открывать и получать сундуки.\n\n"
                    "**🏆 СИСТЕМА РОЛЕЙ**\n"
                    "Более высокая роль заменяет более низкую.\n"
                    "Равная или более низкая награда не выдаётся.\n"
                    "При «Открыть все» каждый сундук получает отдельный ролл.\n\n"
                    "**🌐 ЯЗЫКИ**\n"
                    "English, Russian, Romanian, Uzbek, Kazakh, Turkish,\n"
                    "Spanish, French, German, Italian, Ukrainian, Polish.\n\n"
                    "**⏰ МЕНЮ**\n"
                    "Меню действует 5 минут.\n"
                    "Используйте !chests для нового меню.\n"
                    "Используйте !chest info для этой информации."
                )
            }
        }

        value = texts.get(
            key,
            {}
        ).get(
            lang
        )

        if value is None:
            value = texts.get(
                key,
                {}
            ).get(
                "en",
                key
            )

        return value.format(**kwargs)

    # =========================================================
    # ROLES
    # =========================================================

    def has_phoenix_role(self, member):

        return any(
            role.id == PHOENIX_ROLE_ID
            for role in member.roles
        )

    def has_ultra_role(self, member):

        return any(
            role.id == ULTRA_ROLE_ID
            for role in member.roles
        )

    def phoenix_count(self, guild):

        role = guild.get_role(
            PHOENIX_ROLE_ID
        )

        if role is None:
            return 0

        return sum(
            1
            for member in guild.members
            if role in member.roles
        )

    def get_highest_role_index(self, member):

        highest = -1

        for index, reward in enumerate(
            ROLE_REWARDS
        ):

            if any(
                role.id == reward["role_id"]
                for role in member.roles
            ):

                highest = index

        return highest

    def roll_role(self):

        number = random.random() * 100.001
        current = 0

        for reward in ROLE_REWARDS:

            current += reward["chance"]

            if number < current:
                return reward

        return ROLE_REWARDS[-1]

    async def give_role_if_higher(
        self,
        member,
        reward
    ):

        if (
            reward["role_id"] == PHOENIX_ROLE_ID
            and self.phoenix_count(member.guild) >= PHOENIX_MAX
        ):
            return False

        reward_index = ROLE_REWARDS.index(
            reward
        )

        current_index = self.get_highest_role_index(
            member
        )

        if reward_index <= current_index:
            return False

        roles_to_remove = []

        for index in range(
            current_index + 1
        ):

            if index >= len(
                ROLE_REWARDS
            ):
                break

            role = member.guild.get_role(
                ROLE_REWARDS[index]["role_id"]
            )

            if (
                role is not None
                and role in member.roles
            ):

                roles_to_remove.append(
                    role
                )

        if roles_to_remove:

            try:
                await member.remove_roles(
                    *roles_to_remove,
                    reason="Chest reward upgrade"
                )
            except discord.HTTPException:
                pass

        new_role = member.guild.get_role(
            reward["role_id"]
        )

        if new_role is None:
            return False

        try:

            await member.add_roles(
                new_role,
                reason="Chest reward"
            )

            return True

        except discord.HTTPException:

            return False

    # =========================================================
    # COMPONENTS V2 HELPERS
    # =========================================================

    def color_main(self):
        return discord.Color.blurple()

    def color_chest(self):
        return discord.Color.green()

    def color_mega(self):
        return discord.Color.blue()

    def color_ultra(self):
        return discord.Color.gold()

    def color_phoenix(self):
        return discord.Color.from_rgb(255, 80, 30)

    def color_daily(self):
        return discord.Color.green()

    def color_weekly(self):
        return discord.Color.blue()

    def color_info(self):
        return discord.Color.purple()

    def make_container(
        self,
        text,
        color
    ):

        return discord.ui.Container(
            discord.ui.TextDisplay(
                text
            ),
            accent_color=color
        )

    # =========================================================
    # LANGUAGE SELECT
    # =========================================================

    class LanguageView(discord.ui.LayoutView):

        def __init__(
            self,
            cog,
            owner_id
        ):

            super().__init__(
                timeout=300
            )

            self.cog = cog
            self.owner_id = owner_id

            container = discord.ui.Container(
                discord.ui.TextDisplay(
                    f"# {cog.t(owner_id, 'language_prompt')}\n\n"
                    "🇬🇧 English\n"
                    "🇷🇺 Russian\n"
                    "🇷🇴 Romanian\n"
                    "🇺🇿 Uzbek\n"
                    "🇰🇿 Kazakh\n"
                    "🇹🇷 Turkish\n"
                    "🇪🇸 Spanish\n"
                    "🇫🇷 French\n"
                    "🇩🇪 German\n"
                    "🇮🇹 Italian\n"
                    "🇺🇦 Ukrainian\n"
                    "🇵🇱 Polish"
                ),
                discord.ui.ActionRow(
                    self.create_select()
                ),
                accent_color=discord.Color.blurple()
            )

            self.add_item(container)

        def create_select(self):

            select = discord.ui.StringSelect(
                placeholder="Select language",
                min_values=1,
                max_values=1,
                options=[
                    discord.SelectOption(
                        label="English",
                        value="en",
                        emoji="🇬🇧"
                    ),
                    discord.SelectOption(
                        label="Russian",
                        value="ru",
                        emoji="🇷🇺"
                    ),
                    discord.SelectOption(
                        label="Romanian",
                        value="ro",
                        emoji="🇷🇴"
                    ),
                    discord.SelectOption(
                        label="Uzbek",
                        value="uz",
                        emoji="🇺🇿"
                    ),
                    discord.SelectOption(
                        label="Kazakh",
                        value="kk",
                        emoji="🇰🇿"
                    ),
                    discord.SelectOption(
                        label="Turkish",
                        value="tr",
                        emoji="🇹🇷"
                    ),
                    discord.SelectOption(
                        label="Spanish",
                        value="es",
                        emoji="🇪🇸"
                    ),
                    discord.SelectOption(
                        label="French",
                        value="fr",
                        emoji="🇫🇷"
                    ),
                    discord.SelectOption(
                        label="German",
                        value="de",
                        emoji="🇩🇪"
                    ),
                    discord.SelectOption(
                        label="Italian",
                        value="it",
                        emoji="🇮🇹"
                    ),
                    discord.SelectOption(
                        label="Ukrainian",
                        value="uk",
                        emoji="🇺🇦"
                    ),
                    discord.SelectOption(
                        label="Polish",
                        value="pl",
                        emoji="🇵🇱"
                    )
                ]
            )

            async def callback(interaction):

                if interaction.user.id != self.owner_id:

                    await interaction.response.send_message(
                        self.cog.t(
                            self.owner_id,
                            "not_owner"
                        ),
                        ephemeral=True
                    )

                    return

                language = select.values[0]

                user = self.cog.get_user_data(
                    self.owner_id
                )

                user["language"] = language

                await self.cog.save_data()

                view = self.cog.MainView(
                    self.cog,
                    self.owner_id
                )

                await interaction.response.edit_message(
                    view=view
                )

            select.callback = callback

            return select

    # =========================================================
    # MAIN VIEW
    # =========================================================

    class MainView(discord.ui.LayoutView):

        def __init__(
            self,
            cog,
            owner_id
        ):

            super().__init__(
                timeout=None
            )

            self.cog = cog
            self.owner_id = owner_id

            self.created_at = (
                asyncio.get_running_loop().time()
            )

            user = cog.get_user_data(
                owner_id
            )

            now = int(
                time.time()
            )

            if user["daily_next"] <= now:
                daily = cog.t(
                    owner_id,
                    "daily_available"
                )
            else:
                daily = cog.t(
                    owner_id,
                    "daily_next",
                    timestamp=f"<t:{user['daily_next']}:R>"
                )

            if user["weekly_next"] <= now:
                weekly = cog.t(
                    owner_id,
                    "weekly_available"
                )
            else:
                weekly = cog.t(
                    owner_id,
                    "weekly_next",
                    timestamp=f"<t:{user['weekly_next']}:R>"
                )

            total = (
                user["chests"]
                + user["mega_chests"]
                + user["ultra_chests"]
            )

            text = (
                f"# {cog.t(owner_id, 'title')}\n\n"
                f"{cog.t(owner_id, 'chest', value=user['chests'])}\n"
                f"{cog.t(owner_id, 'mega', value=user['mega_chests'])}\n"
                f"{cog.t(owner_id, 'ultra', value=user['ultra_chests'])}\n\n"
                f"**{cog.t(owner_id, 'total', value=total)}**\n\n"
                f"{daily}\n"
                f"{weekly}"
            )

            container = discord.ui.Container(
                discord.ui.TextDisplay(text),

                discord.ui.ActionRow(
                    self.create_button(
                        "🎁 Chest",
                        discord.ButtonStyle.success,
                        self.chest_callback
                    ),
                    self.create_button(
                        "💎 Mega Chest",
                        discord.ButtonStyle.primary,
                        self.mega_callback
                    ),
                    self.create_button(
                        "⚡ Ultra Chest",
                        discord.ButtonStyle.primary,
                        self.ultra_callback
                    )
                ),

                discord.ui.ActionRow(
                    self.create_button(
                        "📅 Daily",
                        discord.ButtonStyle.success,
                        self.daily_callback
                    ),
                    self.create_button(
                        "📆 Weekly",
                        discord.ButtonStyle.success,
                        self.weekly_callback
                    ),
                    self.create_button(
                        "ℹ️ Info",
                        discord.ButtonStyle.secondary,
                        self.info_callback
                    )
                ),

                accent_color=cog.color_main()
            )

            self.add_item(container)

        def create_button(
            self,
            label,
            style,
            callback
        ):

            button = discord.ui.Button(
                label=label,
                style=style
            )

            async def wrapped(interaction):

                if interaction.user.id != self.owner_id:

                    await interaction.response.send_message(
                        self.cog.t(
                            self.owner_id,
                            "not_owner"
                        ),
                        ephemeral=True
                    )

                    return

                if (
                    asyncio.get_running_loop().time()
                    - self.created_at
                    >= MENU_TIMEOUT
                ):

                    await interaction.response.send_message(
                        self.cog.t(
                            self.owner_id,
                            "expired"
                        ),
                        ephemeral=True
                    )

                    return

                await callback(interaction)

            button.callback = wrapped

            return button

        async def chest_callback(
            self,
            interaction
        ):

            await interaction.response.edit_message(
                view=self.cog.ChestView(
                    self.cog,
                    self.owner_id
                )
            )

        async def mega_callback(
            self,
            interaction
        ):

            await interaction.response.edit_message(
                view=self.cog.MegaView(
                    self.cog,
                    self.owner_id
                )
            )

        async def ultra_callback(
            self,
            interaction
        ):

            await interaction.response.edit_message(
                view=self.cog.UltraView(
                    self.cog,
                    self.owner_id
                )
            )

        async def daily_callback(
            self,
            interaction
        ):

            await self.cog.claim_daily(
                interaction,
                self.owner_id
            )

        async def weekly_callback(
            self,
            interaction
        ):

            await self.cog.claim_weekly(
                interaction,
                self.owner_id
            )

        async def info_callback(
            self,
            interaction
        ):

            await interaction.response.edit_message(
                view=self.cog.InfoView(
                    self.cog,
                    self.owner_id
                )
            )

    # =========================================================
    # CHEST VIEW
    # =========================================================

    class ChestView(discord.ui.LayoutView):

        def __init__(
            self,
            cog,
            owner_id
        ):

            super().__init__(
                timeout=None
            )

            self.cog = cog
            self.owner_id = owner_id

            self.created_at = (
                asyncio.get_running_loop().time()
            )

            user = cog.get_user_data(
                owner_id
            )

            open_button = discord.ui.Button(
                label=cog.t(
                    owner_id,
                    "open_one"
                ),
                style=discord.ButtonStyle.success
            )

            all_button = discord.ui.Button(
                label=cog.t(
                    owner_id,
                    "open_all"
                ),
                style=discord.ButtonStyle.success
            )

            back_button = discord.ui.Button(
                label=cog.t(
                    owner_id,
                    "back"
                ),
                style=discord.ButtonStyle.secondary
            )

            async def open_one(interaction):
                await self.cog.open_normal(
                    interaction,
                    self.owner_id,
                    False
                )

            async def open_all(interaction):
                await self.cog.open_normal(
                    interaction,
                    self.owner_id,
                    True
                )

            async def back(interaction):
                await interaction.response.edit_message(
                    view=self.cog.MainView(
                        self.cog,
                        self.owner_id
                    )
                )

            open_button.callback = open_one
            all_button.callback = open_all
            back_button.callback = back

            container = discord.ui.Container(
                discord.ui.TextDisplay(
                    f"# {cog.t(owner_id, 'normal_chest')}\n\n"
                    f"{cog.t(owner_id, 'chest', value=user['chests'])}\n\n"
                    f"{cog.t(owner_id, 'normal_description')}"
                ),

                discord.ui.ActionRow(
                    open_button,
                    all_button,
                    back_button
                ),

                accent_color=cog.color_chest()
            )

            self.add_item(container)

    # =========================================================
    # MEGA VIEW
    # =========================================================

    class MegaView(discord.ui.LayoutView):

        def __init__(
            self,
            cog,
            owner_id
        ):

            super().__init__(
                timeout=None
            )

            self.cog = cog
            self.owner_id = owner_id

            user = cog.get_user_data(
                owner_id
            )

            open_button = discord.ui.Button(
                label=cog.t(
                    owner_id,
                    "open_one"
                ),
                style=discord.ButtonStyle.success
            )

            all_button = discord.ui.Button(
                label=cog.t(
                    owner_id,
                    "open_all"
                ),
                style=discord.ButtonStyle.success
            )

            back_button = discord.ui.Button(
                label=cog.t(
                    owner_id,
                    "back"
                ),
                style=discord.ButtonStyle.secondary
            )

            open_button.callback = lambda i: cog.open_mega(
                i,
                owner_id,
                False
            )

            all_button.callback = lambda i: cog.open_mega(
                i,
                owner_id,
                True
            )

            back_button.callback = lambda i: i.response.edit_message(
                view=cog.MainView(
                    cog,
                    owner_id
                )
            )

            container = discord.ui.Container(
                discord.ui.TextDisplay(
                    f"# {cog.t(owner_id, 'mega_chest')}\n\n"
                    f"{cog.t(owner_id, 'mega', value=user['mega_chests'])}\n\n"
                    f"{cog.t(owner_id, 'mega_description')}"
                ),

                discord.ui.ActionRow(
                    open_button,
                    all_button,
                    back_button
                ),

                accent_color=cog.color_mega()
            )

            self.add_item(container)

    # =========================================================
    # ULTRA VIEW
    # =========================================================

    class UltraView(discord.ui.LayoutView):

        def __init__(
            self,
            cog,
            owner_id
        ):

            super().__init__(
                timeout=None
            )

            self.cog = cog
            self.owner_id = owner_id

            user = cog.get_user_data(
                owner_id
            )

            open_button = discord.ui.Button(
                label=cog.t(
                    owner_id,
                    "open_one"
                ),
                style=discord.ButtonStyle.success
            )

            all_button = discord.ui.Button(
                label=cog.t(
                    owner_id,
                    "open_all"
                ),
                style=discord.ButtonStyle.success
            )

            back_button = discord.ui.Button(
                label=cog.t(
                    owner_id,
                    "back"
                ),
                style=discord.ButtonStyle.secondary
            )

            open_button.callback = lambda i: cog.open_ultra(
                i,
                owner_id,
                False
            )

            all_button.callback = lambda i: cog.open_ultra(
                i,
                owner_id,
                True
            )

            back_button.callback = lambda i: i.response.edit_message(
                view=cog.MainView(
                    cog,
                    owner_id
                )
            )

            container = discord.ui.Container(
                discord.ui.TextDisplay(
                    f"# {cog.t(owner_id, 'ultra_chest')}\n\n"
                    f"{cog.t(owner_id, 'ultra', value=user['ultra_chests'])}\n\n"
                    f"{cog.t(owner_id, 'ultra_description')}"
                ),

                discord.ui.ActionRow(
                    open_button,
                    all_button,
                    back_button
                ),

                accent_color=cog.color_ultra()
            )

            self.add_item(container)

    # =========================================================
    # INFO VIEW
    # =========================================================

    class InfoView(discord.ui.LayoutView):

        def __init__(
            self,
            cog,
            owner_id
        ):

            super().__init__(
                timeout=None
            )

            self.cog = cog
            self.owner_id = owner_id

            back_button = discord.ui.Button(
                label=cog.t(
                    owner_id,
                    "back"
                ),
                style=discord.ButtonStyle.secondary
            )

            async def back(interaction):

                await interaction.response.edit_message(
                    view=cog.MainView(
                        cog,
                        owner_id
                    )
                )

            back_button.callback = back

            info = cog.t(
                owner_id,
                "info_text"
            )

            container = discord.ui.Container(
                discord.ui.TextDisplay(
                    f"# {cog.t(owner_id, 'info')}\n\n{info}"
                ),

                discord.ui.ActionRow(
                    back_button
                ),

                accent_color=cog.color_info()
            )

            self.add_item(container)

    # =========================================================
    # PHOENIX CHECK
    # =========================================================

    async def phoenix_block(
        self,
        interaction,
        user_id
    ):

        if self.has_phoenix_role(
            interaction.user
        ):

            if not interaction.response.is_done():

                await interaction.response.send_message(
                    self.t(
                        user_id,
                        "phoenix_block"
                    ),
                    ephemeral=True
                )

            else:

                await interaction.followup.send(
                    self.t(
                        user_id,
                        "phoenix_block"
                    ),
                    ephemeral=True
                )

            return True

        return False

    # =========================================================
    # NORMAL CHEST
    # =========================================================

    async def open_normal(
        self,
        interaction,
        user_id,
        open_all
    ):

        if await self.phoenix_block(
            interaction,
            user_id
        ):
            return

        await interaction.response.defer()

        try:

            async with self.open_lock:

                member = interaction.user

                user = self.get_user_data(
                    user_id
                )

                if user["chests"] <= 0:

                    await interaction.followup.send(
                        self.t(
                            user_id,
                            "no_chests"
                        ),
                        ephemeral=True
                    )

                    return

                if open_all:

                    count = int(
                        user["chests"]
                    )

                    user["chests"] = 0

                    await self.save_data()

                    result = await self.open_normal_all(
                        member,
                        count
                    )

                    await interaction.edit_original_response(
                        view=self.ChestView(
                            self,
                            user_id
                        )
                    )

                    await interaction.followup.send(
                        result.content
                        if result.content
                        else self.t(
                            user_id,
                            "opened_all"
                        ),
                        ephemeral=True
                    )

                    return

                user["chests"] -= 1

                reward = self.roll_role()

                if (
                    reward["role_id"] == PHOENIX_ROLE_ID
                    and self.phoenix_count(member.guild) >= PHOENIX_MAX
                ):

                    reward = ROLE_REWARDS[-2]

                mega_bonus = (
                    random.random() < 0.05
                )

                ultra_bonus = (
                    random.random() < 0.01
                )

                if mega_bonus:
                    user["mega_chests"] += 1

                if ultra_bonus:
                    user["ultra_chests"] += 1

                await self.save_data()

                role_given = await self.give_role_if_higher(
                    member,
                    reward
                )

                lang = self.language(
                    user_id
                )

                reward_name = reward["name"][lang]

                description = (
                    f"{self.t(user_id, 'reward')}\n"
                    f"{reward['emoji']} **{reward_name}**"
                )

                if not role_given:

                    description += (
                        f"\n\n{self.t(user_id, 'role_not_given')}"
                    )

                if mega_bonus or ultra_bonus:

                    description += (
                        f"\n\n{self.t(user_id, 'bonus')}"
                    )

                    if mega_bonus:

                        description += (
                            f"\n💎 {self.t(user_id, 'mega_bonus')}"
                        )

                    if ultra_bonus:

                        description += (
                            f"\n⚡ {self.t(user_id, 'ultra_bonus')}"
                        )

                description += (
                    f"\n\n"
                    f"{self.t(user_id, 'remaining_chest', value=user['chests'])}"
                )

                container = discord.ui.Container(
                    discord.ui.TextDisplay(
                        f"# {self.t(user_id, 'chest_opened')}\n\n"
                        f"{description}"
                    ),
                    accent_color=self.color_chest()
                )

                view = discord.ui.LayoutView(
                    timeout=None
                )

                view.add_item(container)

                await interaction.edit_original_response(
                    view=view
                )

        except Exception as e:

            print(
                f"❌ Normal chest error: {repr(e)}"
            )

            try:
                await interaction.followup.send(
                    self.t(
                        user_id,
                        "error"
                    ),
                    ephemeral=True
                )
            except Exception:
                pass

    # =========================================================
    # NORMAL OPEN ALL
    # =========================================================

    async def open_normal_all(
        self,
        member,
        count
    ):

        count = int(count)

        probabilities = np.array(
            [
                reward["chance"]
                for reward in ROLE_REWARDS
            ],
            dtype=np.float64
        )

        probabilities /= probabilities.sum()

        role_counts = np.random.multinomial(
            count,
            probabilities
        )

        mega_count = int(
            np.random.binomial(
                count,
                0.05
            )
        )

        ultra_count = int(
            np.random.binomial(
                count,
                0.01
            )
        )

        user = self.get_user_data(
            member.id
        )

        user["mega_chests"] += mega_count
        user["ultra_chests"] += ultra_count

        await self.save_data()

        highest_index = -1

        for index, amount in enumerate(
            role_counts
        ):

            if int(amount) > 0:

                if (
                    index == len(ROLE_REWARDS) - 1
                    and self.phoenix_count(member.guild) >= PHOENIX_MAX
                ):
                    continue

                highest_index = index

        if highest_index >= 0:

            await self.give_role_if_higher(
                member,
                ROLE_REWARDS[highest_index]
            )

        lines = [
            self.t(
                member.id,
                "normal_amount",
                amount=count
            ),
            ""
        ]

        lang = self.language(
            member.id
        )

        for index, amount in enumerate(
            role_counts
        ):

            amount = int(amount)

            if amount <= 0:
                continue

            reward = ROLE_REWARDS[index]

            if (
                reward["role_id"] == PHOENIX_ROLE_ID
                and self.phoenix_count(member.guild) >= PHOENIX_MAX
            ):
                continue

            reward_name = reward["name"][lang]

            lines.append(
                f"{reward['emoji']} "
                f"{reward_name} × {amount}"
            )

        if mega_count:

            lines.append(
                f"\n💎 "
                f"{self.t(member.id, 'mega_bonus')}: "
                f"{mega_count}"
            )

        if ultra_count:

            lines.append(
                f"⚡ "
                f"{self.t(member.id, 'ultra_bonus')}: "
                f"{ultra_count}"
            )

        view = discord.ui.LayoutView(
            timeout=None
        )

        view.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(
                    f"# {self.t(member.id, 'opened_all')}\n\n"
                    + "\n".join(lines)
                ),
                accent_color=self.color_chest()
            )
        )

        return view

    # =========================================================
    # MEGA OPEN
    # =========================================================

    async def open_mega(
        self,
        interaction,
        user_id,
        open_all
    ):

        if await self.phoenix_block(
            interaction,
            user_id
        ):
            return

        await interaction.response.defer()

        try:

            async with self.open_lock:

                user = self.get_user_data(
                    user_id
                )

                if user["mega_chests"] <= 0:

                    await interaction.followup.send(
                        self.t(
                            user_id,
                            "no_chests"
                        ),
                        ephemeral=True
                    )

                    return

                if open_all:

                    count = int(
                        user["mega_chests"]
                    )

                    user["mega_chests"] = 0

                    lucky = int(
                        np.random.binomial(
                            count,
                            0.05
                        )
                    )

                    normal_count = count - lucky

                    total_normal = 0

                    if normal_count:

                        total_normal = int(
                            np.random.randint(
                                1,
                                11,
                                size=normal_count
                            ).sum()
                        )

                    total_normal += lucky * 20

                    user["chests"] += total_normal

                    await self.save_data()

                    description = (
                        f"{self.t(user_id, 'mega', value=count)}\n\n"
                        f"{self.t(user_id, 'normal_amount', amount=total_normal)}"
                    )

                    if lucky:

                        description += (
                            f"\n\n"
                            f"{self.t(user_id, 'lucky', amount=lucky, reward=20)}"
                        )

                    view = discord.ui.LayoutView(
                        timeout=None
                    )

                    view.add_item(
                        discord.ui.Container(
                            discord.ui.TextDisplay(
                                f"# {self.t(user_id, 'opened_all')}\n\n"
                                f"{description}"
                            ),
                            accent_color=self.color_mega()
                        )
                    )

                    await interaction.edit_original_response(
                        view=view
                    )

                    return

                user["mega_chests"] -= 1

                if random.random() < 0.05:
                    reward = 20
                else:
                    reward = random.randint(
                        1,
                        10
                    )

                user["chests"] += reward

                await self.save_data()

                view = discord.ui.LayoutView(
                    timeout=None
                )

                view.add_item(
                    discord.ui.Container(
                        discord.ui.TextDisplay(
                            f"# {self.t(user_id, 'mega_opened')}\n\n"
                            f"🎁 **+{reward} {self.t(user_id, 'normal_word')}**\n\n"
                            f"{self.t(user_id, 'remaining_mega', value=user['mega_chests'])}"
                        ),
                        accent_color=self.color_mega()
                    )
                )

                await interaction.edit_original_response(
                    view=view
                )

        except Exception as e:

            print(
                f"❌ Mega chest error: {repr(e)}"
            )

            try:
                await interaction.followup.send(
                    self.t(
                        user_id,
                        "error"
                    ),
                    ephemeral=True
                )
            except Exception:
                pass

    # =========================================================
    # ULTRA OPEN
    # =========================================================

    async def open_ultra(
        self,
        interaction,
        user_id,
        open_all
    ):

        if await self.phoenix_block(
            interaction,
            user_id
        ):
            return

        await interaction.response.defer()

        try:

            async with self.open_lock:

                user = self.get_user_data(
                    user_id
                )

                if user["ultra_chests"] <= 0:

                    await interaction.followup.send(
                        self.t(
                            user_id,
                            "no_chests"
                        ),
                        ephemeral=True
                    )

                    return

                if open_all:

                    count = int(
                        user["ultra_chests"]
                    )

                    user["ultra_chests"] = 0

                    lucky = int(
                        np.random.binomial(
                            count,
                            0.05
                        )
                    )

                    normal_count = count - lucky

                    total_normal = 0

                    if normal_count:

                        total_normal = int(
                            np.random.randint(
                                10,
                                21,
                                size=normal_count
                            ).sum()
                        )

                    total_normal += lucky * 30

                    user["chests"] += total_normal

                    await self.save_data()

                    description = (
                        f"{self.t(user_id, 'ultra', value=count)}\n\n"
                        f"{self.t(user_id, 'normal_amount', amount=total_normal)}"
                    )

                    if lucky:

                        description += (
                            f"\n\n"
                            f"{self.t(user_id, 'lucky', amount=lucky, reward=30)}"
                        )

                    view = discord.ui.LayoutView(
                        timeout=None
                    )

                    view.add_item(
                        discord.ui.Container(
                            discord.ui.TextDisplay(
                                f"# {self.t(user_id, 'opened_all')}\n\n"
                                f"{description}"
                            ),
                            accent_color=self.color_ultra()
                        )
                    )

                    await interaction.edit_original_response(
                        view=view
                    )

                    return

                user["ultra_chests"] -= 1

                if random.random() < 0.05:
                    reward = 30
                else:
                    reward = random.randint(
                        10,
                        20
                    )

                user["chests"] += reward

                await self.save_data()

                view = discord.ui.LayoutView(
                    timeout=None
                )

                view.add_item(
                    discord.ui.Container(
                        discord.ui.TextDisplay(
                            f"# {self.t(user_id, 'ultra_opened')}\n\n"
                            f"🎁 **+{reward} {self.t(user_id, 'normal_word')}**\n\n"
                            f"{self.t(user_id, 'remaining_ultra', value=user['ultra_chests'])}"
                        ),
                        accent_color=self.color_ultra()
                    )
                )

                await interaction.edit_original_response(
                    view=view
                )

        except Exception as e:

            print(
                f"❌ Ultra chest error: {repr(e)}"
            )

            try:
                await interaction.followup.send(
                    self.t(
                        user_id,
                        "error"
                    ),
                    ephemeral=True
                )
            except Exception:
                pass

    # =========================================================
    # DAILY
    # =========================================================

    async def claim_daily(
        self,
        interaction,
        user_id
    ):

        if await self.phoenix_block(
            interaction,
            user_id
        ):
            return

        await interaction.response.defer()

        try:

            async with self.open_lock:

                user = self.get_user_data(
                    user_id
                )

                now = int(
                    time.time()
                )

                if user["daily_next"] > now:

                    await interaction.followup.send(
                        self.t(
                            user_id,
                            "daily_unavailable",
                            timestamp=f"<t:{user['daily_next']}:R>"
                        ),
                        ephemeral=True
                    )

                    return

                user["daily_next"] = (
                    now + DAILY_COOLDOWN
                )

                reward = self.roll_role()

                if (
                    reward["role_id"] == PHOENIX_ROLE_ID
                    and self.phoenix_count(interaction.guild) >= PHOENIX_MAX
                ):
                    reward = ROLE_REWARDS[-2]

                mega_bonus = (
                    random.random() < 0.05
                )

                ultra_bonus = (
                    random.random() < 0.01
                )

                if mega_bonus:
                    user["mega_chests"] += 1

                if ultra_bonus:
                    user["ultra_chests"] += 1

                await self.save_data()

                role_given = await self.give_role_if_higher(
                    interaction.user,
                    reward
                )

                lang = self.language(
                    user_id
                )

                reward_name = reward["name"][lang]

                description = (
                    f"{self.t(user_id, 'reward')}\n"
                    f"{reward['emoji']} **{reward_name}**"
                )

                if not role_given:

                    description += (
                        f"\n\n{self.t(user_id, 'role_not_given')}"
                    )

                if mega_bonus:

                    description += (
                        f"\n\n💎 {self.t(user_id, 'mega_bonus')}"
                    )

                if ultra_bonus:

                    description += (
                        f"\n⚡ {self.t(user_id, 'ultra_bonus')}"
                    )

                description += (
                    f"\n\n"
                    f"<t:{user['daily_next']}:R>"
                )

                view = discord.ui.LayoutView(
                    timeout=None
                )

                view.add_item(
                    discord.ui.Container(
                        discord.ui.TextDisplay(
                            f"# {self.t(user_id, 'daily_claimed')}\n\n"
                            f"{description}"
                        ),
                        accent_color=self.color_daily()
                    )
                )

                await interaction.edit_original_response(
                    view=view
                )

        except Exception as e:

            print(
                f"❌ Daily error: {repr(e)}"
            )

            try:
                await interaction.followup.send(
                    self.t(
                        user_id,
                        "error"
                    ),
                    ephemeral=True
                )
            except Exception:
                pass

    # =========================================================
    # WEEKLY
    # =========================================================

    async def claim_weekly(
        self,
        interaction,
        user_id
    ):

        if await self.phoenix_block(
            interaction,
            user_id
        ):
            return

        await interaction.response.defer()

        try:

            async with self.open_lock:

                user = self.get_user_data(
                    user_id
                )

                now = int(
                    time.time()
                )

                if user["weekly_next"] > now:

                    await interaction.followup.send(
                        self.t(
                            user_id,
                            "weekly_unavailable",
                            timestamp=f"<t:{user['weekly_next']}:R>"
                        ),
                        ephemeral=True
                    )

                    return

                user["weekly_next"] = (
                    now + WEEKLY_COOLDOWN
                )

                if random.random() < 0.05:
                    reward = 20
                else:
                    reward = random.randint(
                        1,
                        10
                    )

                user["chests"] += reward

                await self.save_data()

                view = discord.ui.LayoutView(
                    timeout=None
                )

                view.add_item(
                    discord.ui.Container(
                        discord.ui.TextDisplay(
                            f"# {self.t(user_id, 'weekly_claimed')}\n\n"
                            f"🎁 **+{reward} {self.t(user_id, 'normal_word')}**\n\n"
                            f"<t:{user['weekly_next']}:R>"
                        ),
                        accent_color=self.color_weekly()
                    )
                )

                await interaction.edit_original_response(
                    view=view
                )

        except Exception as e:

            print(
                f"❌ Weekly error: {repr(e)}"
            )

            try:
                await interaction.followup.send(
                    self.t(
                        user_id,
                        "error"
                    ),
                    ephemeral=True
                )
            except Exception:
                pass

    # =========================================================
    # ADMIN CHESTS
    # =========================================================

    @commands.group(
        name="admin",
        invoke_without_command=True
    )
    async def admin(
        self,
        ctx
    ):

        if ctx.author.id != OWNER_ID:
            return

        await ctx.send(
            "❌ Unknown admin command.",
            delete_after=5
        )

    @admin.command(
        name="chests"
    )
    async def admin_chests(
        self,
        ctx
    ):

        if ctx.author.id != OWNER_ID:
            return

        embed = discord.Embed(
            title="🎁 Chest Administration",
            description=(
                "Click the button below to add "
                "chests to a user."
            ),
            color=discord.Color.blurple()
        )

        await ctx.send(
            embed=embed,
            view=self.AdminChestsView(self)
        )

        try:
            await ctx.message.delete()

        except (
            discord.Forbidden,
            discord.HTTPException
        ):
            pass

    class AdminChestModal(
        discord.ui.Modal,
        title="Add Chests"
    ):

        user = discord.ui.TextInput(
            label="User",
            placeholder="User ID or @mention",
            required=True
        )

        quantity = discord.ui.TextInput(
            label="Quantity",
            placeholder="Example: 10",
            required=True
        )

        chest = discord.ui.TextInput(
            label="Chest",
            placeholder="chest / mega / ultra",
            required=True
        )

        def __init__(self, cog):

            super().__init__()

            self.cog = cog

        async def on_submit(
            self,
            interaction
        ):

            if interaction.user.id != OWNER_ID:

                await interaction.response.send_message(
                    "❌ You do not have permission to use this.",
                    ephemeral=True
                )

                return

            raw_user = self.user.value.strip()

            raw_user = (
                raw_user
                .replace("<@", "")
                .replace("!", "")
                .replace(">", "")
            )

            try:

                user_id = int(
                    raw_user
                )

            except ValueError:

                await interaction.response.send_message(
                    "❌ Invalid user ID or mention.",
                    ephemeral=True
                )

                return

            try:

                amount = int(
                    self.quantity.value.strip()
                )

                if amount <= 0:
                    raise ValueError

            except ValueError:

                await interaction.response.send_message(
                    "❌ Quantity must be a positive number.",
                    ephemeral=True
                )

                return

            chest_type = (
                self.chest.value
                .strip()
                .lower()
            )

            aliases = {
                "chest": "chest",
                "normal": "chest",
                "сундук": "chest",
                "обычный": "chest",

                "mega": "mega",
                "мега": "mega",
                "мега-сундук
