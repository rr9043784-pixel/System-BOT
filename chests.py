import os
import json
import random
import asyncio
import tempfile
import time

import discord
import numpy as np
from discord.ext import commands


# =================================================
# Settings
# =================================================

DATA_FILE = "chests_data.json"

MENU_TIMEOUT = 300

DAILY_COOLDOWN = 86400
WEEKLY_COOLDOWN = 604800

ULTRA_ROLE_ID = 1529128872036143164


# =================================================
# Chest Roles
# =================================================

ROLE_REWARDS = [
    {
        "name": "Common",
        "emoji": "⚪",
        "role_id": 1529127245128667308,
        "chance": 40.0
    },
    {
        "name": "Uncommon",
        "emoji": "🟢",
        "role_id": 1529155257081401575,
        "chance": 25.0
    },
    {
        "name": "Rare",
        "emoji": "🔵",
        "role_id": 1529127682392985731,
        "chance": 17.0
    },
    {
        "name": "Epic",
        "emoji": "🟣",
        "role_id": 1529127837192159494,
        "chance": 10.0
    },
    {
        "name": "Heroic",
        "emoji": "🟠",
        "role_id": 1529155677476356198,
        "chance": 5.0
    },
    {
        "name": "Mythic",
        "emoji": "🔴",
        "role_id": 1529128399094681760,
        "chance": 2.2
    },
    {
        "name": "Legendary",
        "emoji": "🟡",
        "role_id": 1529128791916544111,
        "chance": 0.6
    },
    {
        "name": "Cosmic",
        "emoji": "🌌",
        "role_id": 1529156030317990019,
        "chance": 0.15
    },
    {
        "name": "Galactic",
        "emoji": "🌠",
        "role_id": 1529156293393383474,
        "chance": 0.04
    },
    {
        "name": "Ultra",
        "emoji": "💎",
        "role_id": 1529128872036143164,
        "chance": 0.01
    }
]


# =================================================
# Data
# =================================================

DEFAULT_DATA = {
    "users": {}
}


# =================================================
# Chests Cog
# =================================================

class Chests(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        self.data = self.load_data()

        self.save_lock = asyncio.Lock()


    # =================================================
    # Load Data
    # =================================================

    def load_data(self):

        if not os.path.exists(DATA_FILE):

            return {
                "users": {}
            }

        try:

            with open(
                DATA_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            if not isinstance(data, dict):

                raise ValueError(
                    "Invalid chest data format"
                )

            if "users" not in data:

                data["users"] = {}

            return data

        except Exception as e:

            print(
                f"❌ Failed to load {DATA_FILE}: {e}"
            )

            return {
                "users": {}
            }


    # =================================================
    # Save Data
    # =================================================

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


    # =================================================
    # User Data
    # =================================================

    def get_user_data(
        self,
        user_id: int
    ):

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

        user.setdefault(
            "chests",
            0
        )

        user.setdefault(
            "mega_chests",
            0
        )

        user.setdefault(
            "ultra_chests",
            0
        )

        user.setdefault(
            "language",
            None
        )

        user.setdefault(
            "daily_next",
            0
        )

        user.setdefault(
            "weekly_next",
            0
        )

        return user


    # =================================================
    # Add Chests
    # =================================================

    async def add_chests(
        self,
        user_id: int,
        amount: int,
        chest_type="chest"
    ):

        try:

            amount = int(amount)

        except (
            TypeError,
            ValueError
        ):

            return False

        if amount <= 0:

            return False

        user = self.get_user_data(
            user_id
        )

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


    # =================================================
    # Language
    # =================================================

    def language(
        self,
        user_id: int
    ):

        return self.get_user_data(
            user_id
        ).get(
            "language"
        ) or "en"


    # =================================================
    # Translation
    # =================================================

    def text(
        self,
        user_id: int,
        key: str,
        **kwargs
    ):

        lang = self.language(
            user_id
        )

        texts = {

            "select_language_title": {
                "en": "🌐 Select your language",
                "ru": "🌐 Выберите язык"
            },

            "select_language_description": {
                "en": "Please select the language for the chest system.",
                "ru": "Пожалуйста, выберите язык для системы сундуков."
            },

            "chests_title": {
                "en": "🎁 Chests",
                "ru": "🎁 Сундуки"
            },

            "language": {
                "en": "🌐 Language: 🇬🇧 English",
                "ru": "🌐 Язык: 🇷🇺 Русский"
            },

            "chest": {
                "en": "🎁 Chest: {value}",
                "ru": "🎁 Сундук: {value}"
            },

            "mega": {
                "en": "💎 Mega Chest: {value}",
                "ru": "💎 Мега-сундук: {value}"
            },

            "ultra": {
                "en": "⚡ Ultra Chest: {value}",
                "ru": "⚡ Ультра-сундук: {value}"
            },

            "total": {
                "en": "Total: {value} Chests",
                "ru": "Всего: {value} сундуков"
            },

            "daily_available": {
                "en": "📅 Daily Chest: Available",
                "ru": "📅 Ежедневный сундук: Доступен"
            },

            "daily_next": {
                "en": "📅 Daily Chest: Available {timestamp}",
                "ru": "📅 Ежедневный сундук: Доступен {timestamp}"
            },

            "weekly_available": {
                "en": "📆 Weekly Mega Chest: Available",
                "ru": "📆 Еженедельный мега-сундук: Доступен"
            },

            "weekly_next": {
                "en": "📆 Weekly Mega Chest: Available {timestamp}",
                "ru": "📆 Еженедельный мега-сундук: Доступен {timestamp}"
            },

            "chest_opened": {
                "en": "🎁 Chest Opened!",
                "ru": "🎁 Сундук открыт!"
            },

            "mega_opened": {
                "en": "💎 Mega Chest Opened!",
                "ru": "💎 Мега-сундук открыт!"
            },

            "ultra_opened": {
                "en": "⚡ Ultra Chest Opened!",
                "ru": "⚡ Ультра-сундук открыт!"
            },

            "reward": {
                "en": "🏆 Reward:",
                "ru": "🏆 Награда:"
            },

            "bonus": {
                "en": "💎 Bonus:",
                "ru": "💎 Бонус:"
            },

            "mega_bonus": {
                "en": "+1 Mega Chest",
                "ru": "+1 Мега-сундук"
            },

            "ultra_bonus": {
                "en": "+1 Ultra Chest",
                "ru": "+1 Ультра-сундук"
            },

            "current_higher": {
                "en": "⬇️ Your current role is higher.\nThe reward was not given.",
                "ru": "⬇️ Ваша текущая роль выше.\nНаграда не была выдана."
            },

            "remaining": {
                "en": "📦 Chest remaining: {value}",
                "ru": "📦 Осталось сундуков: {value}"
            },

            "mega_remaining": {
                "en": "💎 Mega Chest remaining: {value}",
                "ru": "💎 Осталось мега-сундуков: {value}"
            },

            "ultra_remaining": {
                "en": "⚡ Ultra Chest remaining: {value}",
                "ru": "⚡ Осталось ультра-сундуков: {value}"
            },

            "opened_all": {
                "en": "🎁 Opened All",
                "ru": "🎁 Открыты все"
            },

            "opened": {
                "en": "Opened:",
                "ru": "Открыто:"
            },

            "total_opened": {
                "en": "Total Opened: {value} Chests",
                "ru": "Всего открыто: {value} сундуков"
            },

            "rewards": {
                "en": "Rewards:",
                "ru": "Награды:"
            },

            "no_chests": {
                "en": "❌ You don't have any of these chests.",
                "ru": "❌ У вас нет таких сундуков."
            },

            "ultra_block": {
                "en": "❌ You cannot open any chests because you already have the 💎 Ultra role.",
                "ru": "❌ Вы не можете открывать сундуки, потому что у вас уже есть роль 💎 Ultra."
            },

            "daily_block": {
                "en": "❌ You cannot claim the Daily Chest because you already have the 💎 Ultra role.",
                "ru": "❌ Вы не можете получить ежедневный сундук, потому что у вас уже есть роль 💎 Ultra."
            },

            "weekly_block": {
                "en": "❌ You cannot claim the Weekly Mega Chest because you already have the 💎 Ultra role.",
                "ru": "❌ Вы не можете получить еженедельный мега-сундук, потому что у вас уже есть роль 💎 Ultra."
            },

            "daily_claimed": {
                "en": "📅 Daily Chest claimed!",
                "ru": "📅 Ежедневный сундук получен!"
            },

            "weekly_claimed": {
                "en": "📆 Weekly Mega Chest claimed!",
                "ru": "📆 Еженедельный мега-сундук получен!"
            },

            "daily_unavailable": {
                "en": "❌ Daily Chest is not available yet.\nNext: {timestamp}",
                "ru": "❌ Ежедневный сундук пока недоступен.\nСледующий: {timestamp}"
            },

            "weekly_unavailable": {
                "en": "❌ Weekly Mega Chest is not available yet.\nNext: {timestamp}",
                "ru": "❌ Еженедельный мега-сундук пока недоступен.\nСледующий: {timestamp}"
            },

            "not_owner": {
                "en": "❌ These chests don't belong to you.",
                "ru": "❌ Эти сундуки принадлежат не вам."
            },

            "expired": {
                "en": "⏰ This chest menu has expired.\n\nPlease use !chests to open a new chest menu.",
                "ru": "⏰ Срок действия этого меню сундуков истёк.\n\nИспользуйте !chests, чтобы открыть новое меню."
            },

            "open": {
                "en": "🔓 Open",
                "ru": "🔓 Открыть"
            },

            "open_all": {
                "en": "📦 Open All",
                "ru": "📦 Открыть все"
            },

            "back": {
                "en": "🔙 Back",
                "ru": "🔙 Назад"
            },

            "chest_button": {
                "en": "🎁 Chest",
                "ru": "🎁 Сундук"
            },

            "mega_button": {
                "en": "💎 Mega Chest",
                "ru": "💎 Мега-сундук"
            },

            "ultra_button": {
                "en": "⚡ Ultra Chest",
                "ru": "⚡ Ультра-сундук"
            },

            "daily_button": {
                "en": "📅 Daily Chest",
                "ru": "📅 Ежедневный"
            },

            "weekly_button": {
                "en": "📆 Weekly Mega",
                "ru": "📆 Еженедельный Mega"
            },

            "you_received": {
                "en": "🎉 You received {amount} {chest}!",
                "ru": "🎉 Вы получили {amount} {chest}!"
            }
        }

        value = texts.get(
            key,
            {
                "en": key,
                "ru": key
            }
        ).get(
            lang,
            texts.get(
                key,
                {"en": key}
            ).get(
                "en",
                key
            )
        )

        return value.format(
            **kwargs
        )


    # =================================================
    # Ultra Role Check
    # =================================================

    def has_ultra_role(
        self,
        member: discord.Member
    ):

        return any(
            role.id == ULTRA_ROLE_ID
            for role in member.roles
        )


    # =================================================
    # Highest Role
    # =================================================

    def get_highest_role_index(
        self,
        member: discord.Member
    ):

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


    # =================================================
    # Roll One Role
    # =================================================

    def roll_role(self):

        number = random.random() * 100

        current = 0

        for reward in ROLE_REWARDS:

            current += reward["chance"]

            if number < current:

                return reward

        return ROLE_REWARDS[-1]


    # =================================================
    # Give Role
    # =================================================

    async def give_role_if_higher(
        self,
        member: discord.Member,
        reward
    ):

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


    # =================================================
    # Check Interaction
    # =================================================

    async def check_interaction(
        self,
        interaction,
        owner_id
    ):

        if interaction.user.id != owner_id:

            await interaction.response.send_message(
                self.text(
                    owner_id,
                    "not_owner"
                ),
                ephemeral=True
            )

            return False


        return True


    # =================================================
    # Language View
    # =================================================

    class LanguageView(discord.ui.View):

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

            self.created_at = asyncio.get_running_loop().time()


        async def valid(
            self,
            interaction
        ):

            if interaction.user.id != self.owner_id:

                await interaction.response.send_message(
                    "❌ These chests don't belong to you.",
                    ephemeral=True
                )

                return False

            if (
                asyncio.get_running_loop().time()
                - self.created_at
                >= MENU_TIMEOUT
            ):

                await interaction.response.send_message(
                    "⏰ This chest menu has expired.\n\n"
                    "Please use !chests to open a new chest menu.",
                    ephemeral=True
                )

                return False

            return True


        @discord.ui.button(
            label="🇬🇧 EN",
            style=discord.ButtonStyle.primary
        )
        async def english(
            self,
            interaction: discord.Interaction,
            button: discord.ui.Button
        ):

            if not await self.valid(
                interaction
            ):
                return

            user = self.cog.get_user_data(
                self.owner_id
            )

            user["language"] = "en"

            await self.cog.save_data()

            view = self.cog.MainView(
                self.cog,
                self.owner_id
            )

            await interaction.response.edit_message(
                content=f"<@{self.owner_id}>",
                embed=view.main_embed(),
                view=view,
                allowed_mentions=discord.AllowedMentions(
                    users=True
                )
            )


        @discord.ui.button(
            label="🇷🇺 RU",
            style=discord.ButtonStyle.primary
        )
        async def russian(
            self,
            interaction: discord.Interaction,
            button: discord.ui.Button
        ):

            if not await self.valid(
                interaction
            ):
                return

            user = self.cog.get_user_data(
                self.owner_id
            )

            user["language"] = "ru"

            await self.cog.save_data()

            view = self.cog.MainView(
                self.cog,
                self.owner_id
            )

            await interaction.response.edit_message(
                content=f"<@{self.owner_id}>",
                embed=view.main_embed(),
                view=view,
                allowed_mentions=discord.AllowedMentions(
                    users=True
                )
            )


    # =================================================
    # Main View
    # =================================================

    class MainView(discord.ui.View):

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

            self.created_at = asyncio.get_running_loop().time()


        async def valid(
            self,
            interaction
        ):

            if interaction.user.id != self.owner_id:

                await interaction.response.send_message(
                    self.cog.text(
                        self.owner_id,
                        "not_owner"
                    ),
                    ephemeral=True
                )

                return False


            if (
                asyncio.get_running_loop().time()
                - self.created_at
                >= MENU_TIMEOUT
            ):

                await interaction.response.send_message(
                    self.cog.text(
                        self.owner_id,
                        "expired"
                    ),
                    ephemeral=True
                )

                return False


            return True


        def main_embed(self):

            user = self.cog.get_user_data(
                self.owner_id
            )

            import time

            current_time = int(
                time.time()
            )

            daily_next = user["daily_next"]
            weekly_next = user["weekly_next"]


            if daily_next <= current_time:

                daily_text = self.cog.text(
                    self.owner_id,
                    "daily_available"
                )

            else:

                daily_text = self.cog.text(
                    self.owner_id,
                    "daily_next",
                    timestamp=f"<t:{daily_next}:R>"
                )


            if weekly_next <= current_time:

                weekly_text = self.cog.text(
                    self.owner_id,
                    "weekly_available"
                )

            else:

                weekly_text = self.cog.text(
                    self.owner_id,
                    "weekly_next",
                    timestamp=f"<t:{weekly_next}:R>"
                )


            total = (
                user["chests"]
                + user["mega_chests"]
                + user["ultra_chests"]
            )


            description = (
                f"{self.cog.text(self.owner_id, 'language')}\n\n"

                f"{self.cog.text(self.owner_id, 'chest', value=user['chests'])}\n"

                f"{self.cog.text(self.owner_id, 'mega', value=user['mega_chests'])}\n"

                f"{self.cog.text(self.owner_id, 'ultra', value=user['ultra_chests'])}\n\n"

                f"**{self.cog.text(self.owner_id, 'total', value=total)}**\n\n"

                f"{daily_text}\n"

                f"{weekly_text}"
            )


            return discord.Embed(
                title=self.cog.text(
                    self.owner_id,
                    "chests_title"
                ),
                description=description,
                color=discord.Color.blurple()
            )


        @discord.ui.button(
            label="🎁 Chest",
            style=discord.ButtonStyle.primary,
            row=0
        )
        async def chest(
            self,
            interaction,
            button
        ):

            if not await self.valid(
                interaction
            ):
                return

            view = self.cog.ChestView(
                self.cog,
                self.owner_id
            )

            await interaction.response.edit_message(
                embed=view.embed(),
                view=view
            )


        @discord.ui.button(
            label="💎 Mega Chest",
            style=discord.ButtonStyle.primary,
            row=0
        )
        async def mega(
            self,
            interaction,
            button
        ):

            if not await self.valid(
                interaction
            ):
                return

            view = self.cog.MegaView(
                self.cog,
                self.owner_id
            )

            await interaction.response.edit_message(
                embed=view.embed(),
                view=view
            )


        @discord.ui.button(
            label="⚡ Ultra Chest",
            style=discord.ButtonStyle.primary,
            row=0
        )
        async def ultra(
            self,
            interaction,
            button
        ):

            if not await self.valid(
                interaction
            ):
                return

            view = self.cog.UltraView(
                self.cog,
                self.owner_id
            )

            await interaction.response.edit_message(
                embed=view.embed(),
                view=view
            )


        @discord.ui.button(
            label="📅 Daily Chest",
            style=discord.ButtonStyle.success,
            row=1
        )
        async def daily(
            self,
            interaction,
            button
        ):

            if not await self.valid(
                interaction
            ):
                return

            await self.cog.claim_daily(
                interaction,
                self.owner_id
            )


        @discord.ui.button(
            label="📆 Weekly Mega",
            style=discord.ButtonStyle.success,
            row=1
        )
        async def weekly(
            self,
            interaction,
            button
        ):

            if not await self.valid(
                interaction
            ):
                return

            await self.cog.claim_weekly(
                interaction,
                self.owner_id
            )


    # =================================================
    # Chest View
    # =================================================

    class ChestView(discord.ui.View):

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

            self.created_at = asyncio.get_running_loop().time()


        async def valid(
            self,
            interaction
        ):

            if interaction.user.id != self.owner_id:

                await interaction.response.send_message(
                    self.cog.text(
                        self.owner_id,
                        "not_owner"
                    ),
                    ephemeral=True
                )

                return False

            if (
                asyncio.get_running_loop().time()
                - self.created_at
                >= MENU_TIMEOUT
            ):

                await interaction.response.send_message(
                    self.cog.text(
                        self.owner_id,
                        "expired"
                    ),
                    ephemeral=True
                )

                return False

            return True


        def embed(self):

            user = self.cog.get_user_data(
                self.owner_id
            )

            return discord.Embed(
                title=self.cog.text(
                    self.owner_id,
                    "chest"
                ),
                description=(
                    f"🎁 **Chest: {user['chests']}**\n\n"
                    "Open one Chest or open all Chests."
                ),
                color=discord.Color.green()
            )


        @discord.ui.button(
            label="🔓 Open",
            style=discord.ButtonStyle.success
        )
        async def open_one(
            self,
            interaction,
            button
        ):

            if not await self.valid(
                interaction
            ):
                return

            await self.cog.open_normal(
                interaction,
                self.owner_id,
                False
            )


        @discord.ui.button(
            label="📦 Open All",
            style=discord.ButtonStyle.success
        )
        async def open_all(
            self,
            interaction,
            button
        ):

            if not await self.valid(
                interaction
            ):
                return

            await self.cog.open_normal(
                interaction,
                self.owner_id,
                True
            )


        @discord.ui.button(
            label="🔙 Back",
            style=discord.ButtonStyle.secondary
        )
        async def back(
            self,
            interaction,
            button
        ):

            if not await self.valid(
                interaction
            ):
                return

            view = self.cog.MainView(
                self.cog,
                self.owner_id
            )

            await interaction.response.edit_message(
                embed=view.main_embed(),
                view=view
            )


    # =================================================
    # Mega View
    # =================================================

    class MegaView(discord.ui.View):

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

            self.created_at = asyncio.get_running_loop().time()


        async def valid(
            self,
            interaction
        ):

            if interaction.user.id != self.owner_id:

                await interaction.response.send_message(
                    self.cog.text(
                        self.owner_id,
                        "not_owner"
                    ),
                    ephemeral=True
                )

                return False


            if (
                asyncio.get_running_loop().time()
                - self.created_at
                >= MENU_TIMEOUT
            ):

                await interaction.response.send_message(
                    self.cog.text(
                        self.owner_id,
                        "expired"
                    ),
                    ephemeral=True
                )

                return False

            return True


        def embed(self):

            user = self.cog.get_user_data(
                self.owner_id
            )

            return discord.Embed(
                title=self.cog.text(
                    self.owner_id,
                    "mega"
                ),
                description=(
                    f"💎 **Mega Chest: "
                    f"{user['mega_chests']}**\n\n"
                    "Opening a Mega Chest gives "
                    "1–10 normal Chests.\n"
                    "5% chance: 20 normal Chests."
                ),
                color=discord.Color.blue()
            )


        @discord.ui.button(
            label="🔓 Open",
            style=discord.ButtonStyle.success
        )
        async def open_one(
            self,
            interaction,
            button
        ):

            if not await self.valid(
                interaction
            ):
                return

            await self.cog.open_mega(
                interaction,
                self.owner_id,
                False
            )


        @discord.ui.button(
            label="📦 Open All",
            style=discord.ButtonStyle.success
        )
        async def open_all(
            self,
            interaction,
            button
        ):

            if not await self.valid(
                interaction
            ):
                return

            await self.cog.open_mega(
                interaction,
                self.owner_id,
                True
            )


        @discord.ui.button(
            label="🔙 Back",
            style=discord.ButtonStyle.secondary
        )
        async def back(
            self,
            interaction,
            button
        ):

            if not await self.valid(
                interaction
            ):
                return

            view = self.cog.MainView(
                self.cog,
                self.owner_id
            )

            await interaction.response.edit_message(
                embed=view.main_embed(),
                view=view
            )


    # =================================================
    # Ultra View
    # =================================================

    class UltraView(discord.ui.View):

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

            self.created_at = asyncio.get_running_loop().time()


        async def valid(
            self,
            interaction
        ):

            if interaction.user.id != self.owner_id:

                await interaction.response.send_message(
                    self.cog.text(
                        self.owner_id,
                        "not_owner"
                    ),
                    ephemeral=True
                )

                return False


            if (
                asyncio.get_running_loop().time()
                - self.created_at
                >= MENU_TIMEOUT
            ):

                await interaction.response.send_message(
                    self.cog.text(
                        self.owner_id,
                        "expired"
                    ),
                    ephemeral=True
                )

                return False

            return True


        def embed(self):

            user = self.cog.get_user_data(
                self.owner_id
            )

            return discord.Embed(
                title=self.cog.text(
                    self.owner_id,
                    "ultra"
                ),
                description=(
                    f"⚡ **Ultra Chest: "
                    f"{user['ultra_chests']}**\n\n"
                    "Opening an Ultra Chest gives "
                    "10–20 normal Chests.\n"
                    "5% chance: 30 normal Chests."
                ),
                color=discord.Color.gold()
            )


        @discord.ui.button(
            label="🔓 Open",
            style=discord.ButtonStyle.success
        )
        async def open_one(
            self,
            interaction,
            button
        ):

            if not await self.valid(
                interaction
            ):
                return

            await self.cog.open_ultra(
                interaction,
                self.owner_id,
                False
            )


        @discord.ui.button(
            label="📦 Open All",
            style=discord.ButtonStyle.success
        )
        async def open_all(
            self,
            interaction,
            button
        ):

            if not await self.valid(
                interaction
            ):
                return

            await self.cog.open_ultra(
                interaction,
                self.owner_id,
                True
            )


        @discord.ui.button(
            label="🔙 Back",
            style=discord.ButtonStyle.secondary
        )
        async def back(
            self,
            interaction,
            button
        ):

            if not await self.valid(
                interaction
            ):
                return

            view = self.cog.MainView(
                self.cog,
                self.owner_id
            )

            await interaction.response.edit_message(
                embed=view.main_embed(),
                view=view
            )


    # =================================================
    # Normal Chest - One
    # =================================================

    async def open_normal(
        self,
        interaction,
        user_id,
        open_all
    ):

        member = interaction.user

        if self.has_ultra_role(
            member
        ):

            await interaction.response.send_message(
                self.text(
                    user_id,
                    "ultra_block"
                ),
                ephemeral=True
            )

            return


        user = self.get_user_data(
            user_id
        )


        if user["chests"] <= 0:

            await interaction.response.send_message(
                self.text(
                    user_id,
                    "no_chests"
                ),
                ephemeral=True
            )

            return


        if open_all:

            count = user["chests"]

            user["chests"] = 0

            await self.save_data()

            result = await self.open_normal_all(
                member,
                count
            )

            view = self.ChestView(
                self,
                user_id
            )

            await interaction.response.edit_message(
                embed=result,
                view=view
            )

            return


        user["chests"] -= 1

        reward = self.roll_role()

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


        description = (
            f"{self.text(user_id, 'reward')}\n"
            f"{reward['emoji']} **{reward['name']}**\n"
        )


        if not role_given:

            description += (
                f"\n{self.text(user_id, 'current_higher')}\n"
            )


        if mega_bonus or ultra_bonus:

            description += (
                f"\n{self.text(user_id, 'bonus')}\n"
            )

            if mega_bonus:

                description += (
                    f"{self.text(user_id, 'mega_bonus')}\n"
                )

            if ultra_bonus:

                description += (
                    f"{self.text(user_id, 'ultra_bonus')}\n"
                )


        description += (
            f"\n{self.text(user_id, 'remaining', value=user['chests'])}"
        )


        embed = discord.Embed(
            title=self.text(
                user_id,
                "chest_opened"
            ),
            description=description,
            color=discord.Color.green()
        )


        view = self.ChestView(
            self,
            user_id
        )

        await interaction.response.edit_message(
            embed=embed,
            view=view
        )


    # =================================================
    # Normal Chest - All
    # =================================================

    async def open_normal_all(
        self,
        member,
        count
    ):

        user_id = member.id

        if count <= 0:

            return discord.Embed(
                description=self.text(
                    user_id,
                    "no_chests"
                ),
                color=discord.Color.red()
            )


        probabilities = np.array(
            [
                reward["chance"] / 100
                for reward in ROLE_REWARDS
            ],
            dtype=float
        )

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
            user_id
        )

        user["mega_chests"] += mega_count
        user["ultra_chests"] += ultra_count

        await self.save_data()


        highest_index = -1

        for index, amount in enumerate(
            role_counts
        ):

            if amount > 0:

                highest_index = index


        if highest_index >= 0:

            await self.give_role_if_higher(
                member,
                ROLE_REWARDS[highest_index]
            )


        lines = [
            self.text(
                user_id,
                "opened"
            ),
            f"🎁 Chest × {count}"
        ]


        if mega_count:

            lines.append(
                f"💎 Mega Chest × {mega_count}"
            )


        if ultra_count:

            lines.append(
                f"⚡ Ultra Chest × {ultra_count}"
            )


        lines.append("")

        lines.append(
            self.text(
                user_id,
                "rewards"
            )
        )


        for index, amount in enumerate(
            role_counts
        ):

            if amount <= 0:
                continue

            reward = ROLE_REWARDS[index]

            lines.append(
                f"{reward['emoji']} "
                f"{reward['name']} × {int(amount)}"
            )


        embed = discord.Embed(
            title=self.text(
                user_id,
                "opened_all"
            ),
            description="\n".join(
                lines
            ),
            color=discord.Color.green()
        )

        return embed


    # =================================================
    # Mega Chest - One / All
    # =================================================

    async def open_mega(
        self,
        interaction,
        user_id,
        open_all
    ):

        member = interaction.user

        if self.has_ultra_role(
            member
        ):

            await interaction.response.send_message(
                self.text(
                    user_id,
                    "ultra_block"
                ),
                ephemeral=True
            )

            return


        user = self.get_user_data(
            user_id
        )


        if user["mega_chests"] <= 0:

            await interaction.response.send_message(
                self.text(
                    user_id,
                    "no_chests"
                ),
                ephemeral=True
            )

            return


        count = user["mega_chests"]


        if open_all:

            user["mega_chests"] = 0

            lucky = int(
                np.random.binomial(
                    count,
                    0.05
                )
            )

            normal_count = count - lucky

            normal_rewards = 0

            if normal_count:

                normal_rewards = int(
                    np.random.randint(
                        1,
                        11,
                        size=normal_count
                    ).sum()
                )

            total_normal = (
                normal_rewards
                + lucky * 20
            )

            user["chests"] += total_normal

            await self.save_data()


            description = (
                f"{self.text(user_id, 'opened')}\n"
                f"💎 Mega Chest × {count}\n\n"
                f"🎁 Chest × {total_normal}"
            )

            if lucky:

                description += (
                    f"\n\n⭐ Lucky 5% rewards: "
                    f"{lucky} × 20"
                )


            embed = discord.Embed(
                title=self.text(
                    user_id,
                    "opened_all"
                ),
                description=description,
                color=discord.Color.blue()
            )


            view = self.MegaView(
                self,
                user_id
            )

            await interaction.response.edit_message(
                embed=embed,
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


        embed = discord.Embed(
            title=self.text(
                user_id,
                "mega_opened"
            ),
            description=(
                f"🎁 **+{reward} Chest**\n\n"
                f"{self.text(user_id, 'mega_remaining', value=user['mega_chests'])}"
            ),
            color=discord.Color.blue()
        )


        view = self.MegaView(
            self,
            user_id
        )

        await interaction.response.edit_message(
            embed=embed,
            view=view
        )


    # =================================================
    # Ultra Chest - One / All
    # =================================================

    async def open_ultra(
        self,
        interaction,
        user_id,
        open_all
    ):

        member = interaction.user

        if self.has_ultra_role(
            member
        ):

            await interaction.response.send_message(
                self.text(
                    user_id,
                    "ultra_block"
                ),
                ephemeral=True
            )

            return


        user = self.get_user_data(
            user_id
        )


        if user["ultra_chests"] <= 0:

            await interaction.response.send_message(
                self.text(
                    user_id,
                    "no_chests"
                ),
                ephemeral=True
            )

            return


        count = user["ultra_chests"]


        if open_all:

            user["ultra_chests"] = 0

            lucky = int(
                np.random.binomial(
                    count,
                    0.05
                )
            )

            normal_count = count - lucky

            normal_rewards = 0

            if normal_count:

                normal_rewards = int(
                    np.random.randint(
                        10,
                        21,
                        size=normal_count
                    ).sum()
                )

            total_normal = (
                normal_rewards
                + lucky * 30
            )

            user["chests"] += total_normal

            await self.save_data()


            description = (
                f"{self.text(user_id, 'opened')}\n"
                f"⚡ Ultra Chest × {count}\n\n"
                f"🎁 Chest × {total_normal}"
            )

            if lucky:

                description += (
                    f"\n\n⭐ Lucky 5% rewards: "
                    f"{lucky} × 30"
                )


            embed = discord.Embed(
                title=self.text(
                    user_id,
                    "opened_all"
                ),
                description=description,
                color=discord.Color.gold()
            )


            view = self.UltraView(
                self,
                user_id
            )

            await interaction.response.edit_message(
                embed=embed,
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


        embed = discord.Embed(
            title=self.text(
                user_id,
                "ultra_opened"
            ),
            description=(
                f"🎁 **+{reward} Chest**\n\n"
                f"{self.text(user_id, 'ultra_remaining', value=user['ultra_chests'])}"
            ),
            color=discord.Color.gold()
        )


        view = self.UltraView(
            self,
            user_id
        )

        await interaction.response.edit_message(
            embed=embed,
            view=view
        )


    # =================================================
    # Daily Chest
    # =================================================

    async def claim_daily(
        self,
        interaction,
        user_id
    ):

        member = interaction.user

        if self.has_ultra_role(
            member
        ):

            await interaction.response.send_message(
                self.text(
                    user_id,
                    "daily_block"
                ),
                ephemeral=True
            )

            return


        user = self.get_user_data(
            user_id
        )

        now = int(
            time.time()
        )


        if user["daily_next"] > now:

            await interaction.response.send_message(
                self.text(
                    user_id,
                    "daily_unavailable",
                    timestamp=f"<t:{user['daily_next']}:R>"
                ),
                ephemeral=True
            )

            return


        user["daily_next"] = (
            now
            + DAILY_COOLDOWN
        )

        await self.save_data()


        reward = self.roll_role()

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


        description = (
            f"{self.text(user_id, 'reward')}\n"
            f"{reward['emoji']} **{reward['name']}**\n"
        )


        if not role_given:

            description += (
                f"\n{self.text(user_id, 'current_higher')}\n"
            )


        if mega_bonus or ultra_bonus:

            description += (
                f"\n{self.text(user_id, 'bonus')}\n"
            )

            if mega_bonus:

                description += (
                    f"{self.text(user_id, 'mega_bonus')}\n"
                )

            if ultra_bonus:

                description += (
                    f"{self.text(user_id, 'ultra_bonus')}\n"
                )


        description += (
            f"\n📅 Next Daily Chest: "
            f"<t:{user['daily_next']}:R>"
        )


        embed = discord.Embed(
            title=self.text(
                user_id,
                "daily_claimed"
            ),
            description=description,
            color=discord.Color.green()
        )


        view = self.MainView(
            self,
            user_id
        )

        await interaction.response.edit_message(
            embed=embed,
            view=view
        )


    # =================================================
    # Weekly Mega Chest
    # =================================================

    async def claim_weekly(
        self,
        interaction,
        user_id
    ):

        member = interaction.user

        if self.has_ultra_role(
            member
        ):

            await interaction.response.send_message(
                self.text(
                    user_id,
                    "weekly_block"
                ),
                ephemeral=True
            )

            return


        user = self.get_user_data(
            user_id
        )

        now = int(
            time.time()
        )


        if user["weekly_next"] > now:

            await interaction.response.send_message(
                self.text(
                    user_id,
                    "weekly_unavailable",
                    timestamp=f"<t:{user['weekly_next']}:R>"
                ),
                ephemeral=True
            )

            return


        user["weekly_next"] = (
            now
            + WEEKLY_COOLDOWN
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


        embed = discord.Embed(
            title=self.text(
                user_id,
                "weekly_claimed"
            ),
            description=(
                f"🎁 **+{reward} Chest**\n\n"
                f"📆 Next Weekly Mega Chest: "
                f"<t:{user['weekly_next']}:R>"
            ),
            color=discord.Color.blue()
        )


        view = self.MainView(
            self,
            user_id
        )

        await interaction.response.edit_message(
            embed=embed,
            view=view
        )


    # =================================================
    # !chests
    # =================================================

    @commands.command(
        name="chests"
    )
    async def chests_command(
        self,
        ctx: commands.Context
    ):

        user = self.get_user_data(
            ctx.author.id
        )


        # =================================================
        # First Use - Language
        # =================================================

        if not user.get("language"):

            embed = discord.Embed(
                title="🌐 Select your language",
                description=(
                    "Please select the language for the chest system."
                ),
                color=discord.Color.blurple()
            )

            view = self.LanguageView(
                self,
                ctx.author.id
            )

            await ctx.send(
                content=f"<@{ctx.author.id}>",
                embed=embed,
                view=view,
                allowed_mentions=discord.AllowedMentions(
                    users=True
                )
            )

        else:

            view = self.MainView(
                self,
                ctx.author.id
            )

            await ctx.send(
                content=f"<@{ctx.author.id}>",
                embed=view.main_embed(),
                view=view,
                allowed_mentions=discord.AllowedMentions(
                    users=True
                )
            )


        # =================================================
        # Delete Command
        # =================================================

        try:

            await ctx.message.delete()

        except (
            discord.Forbidden,
            discord.HTTPException
        ):

            pass


# =================================================
# Setup
# =================================================

async def setup(bot):

    await bot.add_cog(
        Chests(bot)
    )

    print(
        "✅ Chests cog loaded!"
        )
