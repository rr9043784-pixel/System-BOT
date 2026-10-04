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

            return data

        except Exception as e:

            print(
                f"❌ Failed to load {DATA_FILE}: {e}"
            )

            return {
                "users": {}
            }

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
                    os.remove(
                        temp_path
                    )
                except OSError:
                    pass

                raise

    def get_user_data(
        self,
        user_id
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

    async def add_chests(
        self,
        user_id,
        amount,
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

    # =========================================================
    # TEXT
    # =========================================================

    def language(
        self,
        user_id
    ):

        language = self.get_user_data(
            user_id
        ).get("language")

        return language or "en"

    def text(
        self,
        user_id,
        key,
        **kwargs
    ):

        lang = self.language(
            user_id
        )

        texts = {

            "not_owner": {
                "en": "❌ These chests don't belong to you.",
                "ru": "❌ Эти сундуки принадлежат не вам."
            },

            "expired": {
                "en": (
                    "⏰ This chest menu has expired.\n\n"
                    "Please use !chests to open a new chest menu."
                ),
                "ru": (
                    "⏰ Срок действия этого меню сундуков истёк.\n\n"
                    "Используйте !chests, чтобы открыть новое меню."
                )
            },

            "no_chests": {
                "en": "❌ You don't have any of these chests.",
                "ru": "❌ У вас нет таких сундуков."
            },

            "ultra_block": {
                "en": (
                    "❌ You cannot open any chests because "
                    "you already have the 💎 Ultra role."
                ),
                "ru": (
                    "❌ Вы не можете открывать сундуки, "
                    "потому что у вас уже есть роль 💎 Ultra."
                )
            },

            "daily_block": {
                "en": (
                    "❌ You cannot claim the Daily Chest "
                    "because you already have the 💎 Ultra role."
                ),
                "ru": (
                    "❌ Вы не можете получить ежедневный сундук, "
                    "потому что у вас уже есть роль 💎 Ultra."
                )
            },

            "weekly_block": {
                "en": (
                    "❌ You cannot claim the Weekly Mega Chest "
                    "because you already have the 💎 Ultra role."
                ),
                "ru": (
                    "❌ Вы не можете получить еженедельный мега-сундук, "
                    "потому что у вас уже есть роль 💎 Ultra."
                )
            },

            "error": {
                "en": "❌ Something went wrong.",
                "ru": "❌ Произошла ошибка."
            },

            "daily_unavailable": {
                "en": (
                    "❌ Daily Chest is not available yet.\n"
                    "Next: {timestamp}"
                ),
                "ru": (
                    "❌ Ежедневный сундук пока недоступен.\n"
                    "Следующий: {timestamp}"
                )
            },

            "weekly_unavailable": {
                "en": (
                    "❌ Weekly Mega Chest is not available yet.\n"
                    "Next: {timestamp}"
                ),
                "ru": (
                    "❌ Еженедельный мега-сундук пока недоступен.\n"
                    "Следующий: {timestamp}"
                )
            }

        }

        result = texts.get(
            key,
            {
                "en": key,
                "ru": key
            }
        ).get(
            lang,
            key
        )

        return result.format(
            **kwargs
        )

    # =========================================================
    # ROLES
    # =========================================================

    def has_ultra_role(
        self,
        member
    ):

        return any(
            role.id == ULTRA_ROLE_ID
            for role in member.roles
        )

    def get_highest_role_index(
        self,
        member
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

    def roll_role(self):

        number = random.random() * 100
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
    # MAIN VIEW
    # =========================================================

    class MainView(
        discord.ui.View
    ):

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

            now = int(
                time.time()
            )

            if user["daily_next"] <= now:

                daily = "📅 Daily Chest: Available"

            else:

                daily = (
                    "📅 Daily Chest: "
                    f"<t:{user['daily_next']}:R>"
                )

            if user["weekly_next"] <= now:

                weekly = (
                    "📆 Weekly Mega: Available"
                )

            else:

                weekly = (
                    "📆 Weekly Mega: "
                    f"<t:{user['weekly_next']}:R>"
                )

            total = (
                user["chests"]
                + user["mega_chests"]
                + user["ultra_chests"]
            )

            language = self.cog.language(
                self.owner_id
            )

            language_text = (
                "🇬🇧 English"
                if language == "en"
                else "🇷🇺 Русский"
            )

            description = (
                f"🌐 Language: {language_text}\n\n"
                f"🎁 Chest: {user['chests']}\n"
                f"💎 Mega Chest: {user['mega_chests']}\n"
                f"⚡ Ultra Chest: {user['ultra_chests']}\n\n"
                f"**Total: {total} Chests**\n\n"
                f"{daily}\n"
                f"{weekly}"
            )

            return discord.Embed(
                title=(
                    f"🎁 {self.owner_id}"
                ),
                description=description,
                color=discord.Color.blurple()
            )

        # -----------------------------------------------------
        # CHEST
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # MEGA
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # ULTRA
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # DAILY
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # WEEKLY
        # -----------------------------------------------------

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

    # =========================================================
    # CHEST VIEW
    # =========================================================

    class ChestView(
        discord.ui.View
    ):

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
                title="🎁 Chest",
                description=(
                    f"🎁 Chest: {user['chests']}\n\n"
                    "Open one Chest or open all Chests."
                ),
                color=discord.Color.blurple()
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
                embed=view.embed(),
                view=view
            )

    # =========================================================
    # MEGA VIEW
    # =========================================================

    class MegaView(
        discord.ui.View
    ):

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
                title="💎 Mega Chest",
                description=(
                    f"💎 Mega Chest: {user['mega_chests']}\n\n"
                    "Opening gives 1–10 normal Chests.\n"
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
                embed=view.embed(),
                view=view
            )

    # =========================================================
    # ULTRA VIEW
    # =========================================================

    class UltraView(
        discord.ui.View
    ):

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
                title="⚡ Ultra Chest",
                description=(
                    f"⚡ Ultra Chest: {user['ultra_chests']}\n\n"
                    "Opening gives 10–20 normal Chests.\n"
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
                embed=view.embed(),
                view=view
            )

    # =========================================================
    # NORMAL CHEST OPEN
    # =========================================================

    async def open_normal(
        self,
        interaction,
        user_id,
        open_all
    ):

        await interaction.response.defer()

        try:

            async with self.open_lock:

                member = interaction.user

                if self.has_ultra_role(
                    member
                ):

                    await interaction.edit_original_response(
                        content=self.text(
                            user_id,
                            "ultra_block"
                        ),
                        embed=None,
                        view=None
                    )

                    return

                user = self.get_user_data(
                    user_id
                )

                if user["chests"] <= 0:

                    await interaction.edit_original_response(
                        content=self.text(
                            user_id,
                            "no_chests"
                        ),
                        embed=None,
                        view=None
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

                    view = self.ChestView(
                        self,
                        user_id
                    )

                    await interaction.edit_original_response(
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
                    f"🏆 Reward:\n"
                    f"{reward['emoji']} **{reward['name']}**\n"
                )

                if not role_given:

                    description += (
                        "\n⬇️ Your current role is higher "
                        "or equal.\n"
                        "The reward was not given.\n"
                    )

                if mega_bonus or ultra_bonus:

                    description += (
                        "\n💎 Bonus:\n"
                    )

                    if mega_bonus:

                        description += (
                            "💎 +1 Mega Chest\n"
                        )

                    if ultra_bonus:

                        description += (
                            "⚡ +1 Ultra Chest\n"
                        )

                description += (
                    f"\n📦 Chest remaining: "
                    f"{user['chests']}"
                )

                embed = discord.Embed(
                    title="🎁 Chest Opened!",
                    description=description,
                    color=discord.Color.green()
                )

                view = self.ChestView(
                    self,
                    user_id
                )

                await interaction.edit_original_response(
                    embed=embed,
                    view=view
                )

        except Exception as e:

            print(
                f"❌ Normal chest error: {repr(e)}"
            )

            try:

                await interaction.edit_original_response(
                    content=self.text(
                        user_id,
                        "error"
                    ),
                    embed=None,
                    view=None
                )

            except Exception as error:

                print(
                    f"❌ Error sending normal chest error: "
                    f"{repr(error)}"
                )

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
                highest_index = index

        if highest_index >= 0:

            await self.give_role_if_higher(
                member,
                ROLE_REWARDS[highest_index]
            )

        lines = [
            f"🎁 Chest × {count}",
            ""
        ]

        for index, amount in enumerate(
            role_counts
        ):

            amount = int(amount)

            if amount <= 0:
                continue

            reward = ROLE_REWARDS[index]

            lines.append(
                f"{reward['emoji']} "
                f"{reward['name']} × {amount}"
            )

        if mega_count:

            lines.append(
                f"\n💎 Mega Chest × {mega_count}"
            )

        if ultra_count:

            lines.append(
                f"⚡ Ultra Chest × {ultra_count}"
            )

        return discord.Embed(
            title="🎁 Opened All",
            description="\n".join(lines),
            color=discord.Color.green()
        )

    # =========================================================
    # MEGA OPEN
    # =========================================================

    async def open_mega(
        self,
        interaction,
        user_id,
        open_all
    ):

        await interaction.response.defer()

        try:

            async with self.open_lock:

                member = interaction.user

                if self.has_ultra_role(
                    member
                ):

                    await interaction.edit_original_response(
                        content=self.text(
                            user_id,
                            "ultra_block"
                        ),
                        embed=None,
                        view=None
                    )

                    return

                user = self.get_user_data(
                    user_id
                )

                if user["mega_chests"] <= 0:

                    await interaction.edit_original_response(
                        content=self.text(
                            user_id,
                            "no_chests"
                        ),
                        embed=None,
                        view=None
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

                    normal_count = (
                        count - lucky
                    )

                    total_normal = 0

                    if normal_count:

                        total_normal = int(
                            np.random.randint(
                                1,
                                11,
                                size=normal_count
                            ).sum()
                        )

                    total_normal += (
                        lucky * 20
                    )

                    user["chests"] += (
                        total_normal
                    )

                    await self.save_data()

                    description = (
                        f"💎 Mega Chest × {count}\n\n"
                        f"🎁 Chest × {total_normal}"
                    )

                    if lucky:

                        description += (
                            f"\n\n⭐ Lucky: "
                            f"{lucky} × 20"
                        )

                    embed = discord.Embed(
                        title="💎 Opened All",
                        description=description,
                        color=discord.Color.blue()
                    )

                    view = self.MegaView(
                        self,
                        user_id
                    )

                    await interaction.edit_original_response(
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
                    title="💎 Mega Chest Opened!",
                    description=(
                        f"🎁 **+{reward} Chest**\n\n"
                        f"💎 Mega Chest remaining: "
                        f"{user['mega_chests']}"
                    ),
                    color=discord.Color.blue()
                )

                view = self.MegaView(
                    self,
                    user_id
                )

                await interaction.edit_original_response(
                    embed=embed,
                    view=view
                )

        except Exception as e:

            print(
                f"❌ Mega chest error: {repr(e)}"
            )

            try:

                await interaction.edit_original_response(
                    content=self.text(
                        user_id,
                        "error"
                    ),
                    embed=None,
                    view=None
                )

            except Exception as error:

                print(
                    f"❌ Error sending mega chest error: "
                    f"{repr(error)}"
                )

    # =========================================================
    # ULTRA OPEN
    # =========================================================

    async def open_ultra(
        self,
        interaction,
        user_id,
        open_all
    ):

        await interaction.response.defer()

        try:

            async with self.open_lock:

                member = interaction.user

                if self.has_ultra_role(
                    member
                ):

                    await interaction.edit_original_response(
                        content=self.text(
                            user_id,
                            "ultra_block"
                        ),
                        embed=None,
                        view=None
                    )

                    return

                user = self.get_user_data(
                    user_id
                )

                if user["ultra_chests"] <= 0:

                    await interaction.edit_original_response(
                        content=self.text(
                            user_id,
                            "no_chests"
                        ),
                        embed=None,
                        view=None
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

                    normal_count = (
                        count - lucky
                    )

                    total_normal = 0

                    if normal_count:

                        total_normal = int(
                            np.random.randint(
                                10,
                                21,
                                size=normal_count
                            ).sum()
                        )

                    total_normal += (
                        lucky * 30
                    )

                    user["chests"] += (
                        total_normal
                    )

                    await self.save_data()

                    description = (
                        f"⚡ Ultra Chest × {count}\n\n"
                        f"🎁 Chest × {total_normal}"
                    )

                    if lucky:

                        description += (
                            f"\n\n⭐ Lucky: "
                            f"{lucky} × 30"
                        )

                    embed = discord.Embed(
                        title="⚡ Opened All",
                        description=description,
                        color=discord.Color.gold()
                    )

                    view = self.UltraView(
                        self,
                        user_id
                    )

                    await interaction.edit_original_response(
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
                    title="⚡ Ultra Chest Opened!",
                    description=(
                        f"🎁 **+{reward} Chest**\n\n"
                        f"⚡ Ultra Chest remaining: "
                        f"{user['ultra_chests']}"
                    ),
                    color=discord.Color.gold()
                )

                view = self.UltraView(
                    self,
                    user_id
                )

                await interaction.edit_original_response(
                    embed=embed,
                    view=view
                )

        except Exception as e:

            print(
                f"❌ Ultra chest error: {repr(e)}"
            )

            try:

                await interaction.edit_original_response(
                    content=self.text(
                        user_id,
                        "error"
                    ),
                    embed=None,
                    view=None
                )

            except Exception as error:

                print(
                    f"❌ Error sending ultra chest error: "
                    f"{repr(error)}"
                )

    # =========================================================
    # DAILY
    # =========================================================

    async def claim_daily(
        self,
        interaction,
        user_id
    ):

        await interaction.response.defer()

        try:

            async with self.open_lock:

                member = interaction.user

                if self.has_ultra_role(
                    member
                ):

                    await interaction.edit_original_response(
                        content=self.text(
                            user_id,
                            "daily_block"
                        ),
                        embed=None,
                        view=None
                    )

                    return

                user = self.get_user_data(
                    user_id
                )

                now = int(
                    time.time()
                )

                if user["daily_next"] > now:

                    await interaction.edit_original_response(
                        content=self.text(
                            user_id,
                            "daily_unavailable",
                            timestamp=(
                                f"<t:{user['daily_next']}:R>"
                            )
                        ),
                        embed=None,
                        view=None
                    )

                    return

                user["daily_next"] = (
                    now + DAILY_COOLDOWN
                )

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
                    f"🏆 Reward:\n"
                    f"{reward['emoji']} **{reward['name']}**\n"
                )

                if not role_given:

                    description += (
                        "\n⬇️ Your current role is higher "
                        "or equal.\n"
                    )

                if mega_bonus:

                    description += (
                        "\n💎 +1 Mega Chest"
                    )

                if ultra_bonus:

                    description += (
                        "\n⚡ +1 Ultra Chest"
                    )

                description += (
                    f"\n\n📅 Next Daily Chest: "
                    f"<t:{user['daily_next']}:R>"
                )

                embed = discord.Embed(
                    title="📅 Daily Chest Claimed!",
                    description=description,
                    color=discord.Color.green()
                )

                view = self.MainView(
                    self,
                    user_id
                )

                await interaction.edit_original_response(
                    embed=embed,
                    view=view
                )

        except Exception as e:

            print(
                f"❌ Daily error: {repr(e)}"
            )

            try:

                await interaction.edit_original_response(
                    content=self.text(
                        user_id,
                        "error"
                    ),
                    embed=None,
                    view=None
                )

            except Exception as error:

                print(
                    f"❌ Error sending daily error: "
                    f"{repr(error)}"
                )

    # =========================================================
    # WEEKLY
    # =========================================================

    async def claim_weekly(
        self,
        interaction,
        user_id
    ):

        await interaction.response.defer()

        try:

            async with self.open_lock:

                member = interaction.user

                if self.has_ultra_role(
                    member
                ):

                    await interaction.edit_original_response(
                        content=self.text(
                            user_id,
                            "weekly_block"
                        ),
                        embed=None,
                        view=None
                    )

                    return

                user = self.get_user_data(
                    user_id
                )

                now = int(
                    time.time()
                )

                if user["weekly_next"] > now:

                    await interaction.edit_original_response(
                        content=self.text(
                            user_id,
                            "weekly_unavailable",
                            timestamp=(
                                f"<t:{user['weekly_next']}:R>"
                            )
                        ),
                        embed=None,
                        view=None
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

                embed = discord.Embed(
                    title="📆 Weekly Mega Claimed!",
                    description=(
                        f"🎁 **+{reward} Chest**\n\n"
                        f"📆 Next Weekly Mega: "
                        f"<t:{user['weekly_next']}:R>"
                    ),
                    color=discord.Color.blue()
                )

                view = self.MainView(
                    self,
                    user_id
                )

                await interaction.edit_original_response(
                    embed=embed,
                    view=view
                )

        except Exception as e:

            print(
                f"❌ Weekly error: {repr(e)}"
            )

            try:

                await interaction.edit_original_response(
                    content=self.text(
                        user_id,
                        "error"
                    ),
                    embed=None,
                    view=None
                )

            except Exception as error:

                print(
                    f"❌ Error sending weekly error: "
                    f"{repr(error)}"
                )

    # =========================================================
    # LANGUAGE VIEW
    # =========================================================

    class LanguageView(
        discord.ui.View
    ):

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

        @discord.ui.button(
            label="🇬🇧 EN",
            style=discord.ButtonStyle.primary
        )
        async def english(
            self,
            interaction,
            button
        ):

            if interaction.user.id != self.owner_id:

                await interaction.response.send_message(
                    self.cog.text(
                        self.owner_id,
                        "not_owner"
                    ),
                    ephemeral=True
                )

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
                content=(
                    f"🎁 Chests "
                    f"{interaction.user.mention}"
                ),
                embed=view.embed(),
                view=view
            )

        @discord.ui.button(
            label="🇷🇺 RU",
            style=discord.ButtonStyle.primary
        )
        async def russian(
            self,
            interaction,
            button
        ):

            if interaction.user.id != self.owner_id:

                await interaction.response.send_message(
                    self.cog.text(
                        self.owner_id,
                        "not_owner"
                    ),
                    ephemeral=True
                )

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
                content=(
                    f"🎁 Сундуки "
                    f"{interaction.user.mention}"
                ),
                embed=view.embed(),
                view=view
            )

    # =========================================================
    # COMMAND
    # =========================================================

    @commands.command(
        name="chests"
    )
    async def chests_command(
        self,
        ctx
    ):

        user = self.get_user_data(
            ctx.author.id
        )

        if not user.get(
            "language"
        ):

            embed = discord.Embed(
                title="🌐 Select your language",
                description=(
                    "Please select the language "
                    "for the chest system."
                ),
                color=discord.Color.blurple()
            )

            view = self.LanguageView(
                self,
                ctx.author.id
            )

            await ctx.send(
                content=ctx.author.mention,
                embed=embed,
                view=view
            )

        else:

            view = self.MainView(
                self,
                ctx.author.id
            )

            await ctx.send(
                content=(
                    f"🎁 Chests "
                    f"{ctx.author.mention}"
                ),
                embed=view.embed(),
                view=view
            )

        try:

            await ctx.message.delete()

        except (
            discord.Forbidden,
            discord.HTTPException
        ):

            pass


# =============================================================
# SETUP
# =============================================================

async def setup(bot):

    await bot.add_cog(
        Chests(bot)
    )

    print(
        "✅ Chests cog loaded!"
    )
