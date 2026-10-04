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

OWNER_ID = 1176149190192152626

ULTRA_ROLE_ID = 1529128872036143164


ROLE_REWARDS = [
    {
        "name_en": "Common",
        "name_ru": "Обычная",
        "role_id": 1529127245128667308,
        "chance": 40.0,
    },
    {
        "name_en": "Uncommon",
        "name_ru": "Необычная",
        "role_id": 1529155257081401575,
        "chance": 25.0,
    },
    {
        "name_en": "Rare",
        "name_ru": "Редкая",
        "role_id": 1529127682392985731,
        "chance": 17.0,
    },
    {
        "name_en": "Epic",
        "name_ru": "Эпическая",
        "role_id": 1529127837192159494,
        "chance": 10.0,
    },
    {
        "name_en": "Heroic",
        "name_ru": "Героическая",
        "role_id": 1529155677476356198,
        "chance": 5.0,
    },
    {
        "name_en": "Mythic",
        "name_ru": "Мифическая",
        "role_id": 1529128399094681760,
        "chance": 2.2,
    },
    {
        "name_en": "Legendary",
        "name_ru": "Легендарная",
        "role_id": 1529128791916544111,
        "chance": 0.6,
    },
    {
        "name_en": "Cosmic",
        "name_ru": "Космическая",
        "role_id": 1529156030317990019,
        "chance": 0.15,
    },
    {
        "name_en": "Galactic",
        "name_ru": "Галактическая",
        "role_id": 1529156293393383474,
        "chance": 0.04,
    },
    {
        "name_en": "Ultra",
        "name_ru": "Ультра",
        "role_id": 1529128872036143164,
        "chance": 0.01,
    },
]


DEFAULT_USER_DATA = {
    "chests": 0,
    "mega_chests": 0,
    "ultra_chests": 0,
    "language": "en",
    "daily_next": 0,
    "weekly_next": 0,
}


class Chests(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = self.load_data()

    # =========================================================
    # DATA
    # =========================================================

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return {"users": {}}

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "users" not in data:
                data["users"] = {}

            return data

        except Exception as e:
            print(f"❌ Failed to load chest data: {e}")
            return {"users": {}}

    def save_data(self):
        directory = os.path.dirname(os.path.abspath(DATA_FILE))
        os.makedirs(directory, exist_ok=True)

        fd, temp_path = tempfile.mkstemp(
            prefix="chests_",
            suffix=".tmp",
            dir=directory
        )

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(
                    self.data,
                    f,
                    ensure_ascii=False,
                    indent=4
                )

            os.replace(temp_path, DATA_FILE)

        except Exception:
            try:
                os.remove(temp_path)
            except Exception:
                pass

            raise

    def get_user_data(self, user_id):
        user_id = str(user_id)

        if user_id not in self.data["users"]:
            self.data["users"][user_id] = DEFAULT_USER_DATA.copy()
            self.save_data()

        user = self.data["users"][user_id]

        for key, value in DEFAULT_USER_DATA.items():
            if key not in user:
                user[key] = value

        return user

    async def add_chests(self, user_id, amount, chest_type="chest"):
        try:
            amount = int(amount)

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

            self.save_data()
            return True

        except Exception as e:
            print(f"❌ add_chests error: {e}")
            return False

    # =========================================================
    # LANGUAGE
    # =========================================================

    def language(self, user_id):
        return self.get_user_data(user_id).get("language", "en")

    def t(self, user_id, key):
        lang = self.language(user_id)

        texts = {
            "select_language_title": {
                "en": "🌐 Select your language",
                "ru": "🌐 Выберите язык",
            },
            "select_language_text": {
                "en": "Please select the language for the chest system.",
                "ru": "Выберите язык для системы сундуков.",
            },

            "main_title": {
                "en": "🎁 Chests",
                "ru": "🎁 Сундуки",
            },

            "language_en": {
                "en": "English",
                "ru": "Английский",
            },

            "language_ru": {
                "en": "Russian",
                "ru": "Русский",
            },

            "chest": {
                "en": "🎁 Chest",
                "ru": "🎁 Сундук",
            },

            "mega": {
                "en": "💎 Mega Chest",
                "ru": "💎 Мега-сундук",
            },

            "ultra": {
                "en": "⚡ Ultra Chest",
                "ru": "⚡ Ультра-сундук",
            },

            "daily": {
                "en": "📅 Daily Chest",
                "ru": "📅 Ежедневный сундук",
            },

            "weekly": {
                "en": "📆 Weekly Mega",
                "ru": "📆 Еженедельный мега",
            },

            "total": {
                "en": "Total",
                "ru": "Всего",
            },

            "available": {
                "en": "Available",
                "ru": "Доступен",
            },

            "unavailable": {
                "en": "Unavailable",
                "ru": "Недоступен",
            },

            "open": {
                "en": "Open",
                "ru": "Открыть",
            },

            "open_all": {
                "en": "Open All",
                "ru": "Открыть все",
            },

            "back": {
                "en": "Back",
                "ru": "Назад",
            },

            "expired_title": {
                "en": "⏰ This chest menu has expired.",
                "ru": "⏰ Это меню сундуков истекло.",
            },

            "expired_text": {
                "en": "Please use !chests to open a new chest menu.",
                "ru": "Используйте !chests, чтобы открыть новое меню сундуков.",
            },

            "not_yours": {
                "en": "❌ These chests don't belong to you.",
                "ru": "❌ Эти сундуки принадлежат не вам.",
            },

            "ultra_block": {
                "en": "❌ You cannot open chests while you have the Ultra role.",
                "ru": "❌ Вы не можете открывать сундуки, пока у вас есть роль Ultra.",
            },

            "no_chests": {
                "en": "❌ You don't have any of these chests.",
                "ru": "❌ У вас нет таких сундуков.",
            },

            "already_role": {
                "en": "You already have this role or a higher role.",
                "ru": "У вас уже есть эта или более высокая роль.",
            },

            "daily_claimed": {
                "en": "❌ Your Daily Chest is not available yet.",
                "ru": "❌ Ежедневный сундук пока недоступен.",
            },

            "weekly_claimed": {
                "en": "❌ Your Weekly Mega is not available yet.",
                "ru": "❌ Еженедельный мега-сундук пока недоступен.",
            },

            "daily_received": {
                "en": "📅 You received a Daily Chest!",
                "ru": "📅 Вы получили ежедневный сундук!",
            },

            "weekly_received": {
                "en": "📆 You received a Weekly Mega Chest!",
                "ru": "📆 Вы получили еженедельный мега-сундук!",
            },
        }

        return texts.get(key, {}).get(lang, key)

    # =========================================================
    # ROLE SYSTEM
    # =========================================================

    def has_ultra_role(self, member):
        return any(role.id == ULTRA_ROLE_ID for role in member.roles)

    def get_highest_role_index(self, member):
        highest = -1

        for index, reward in enumerate(ROLE_REWARDS):
            if any(role.id == reward["role_id"] for role in member.roles):
                highest = max(highest, index)

        return highest

    def roll_role(self):
        roll = random.uniform(0, 100)

        current = 0

        for reward in ROLE_REWARDS:
            current += reward["chance"]

            if roll <= current:
                return reward

        return ROLE_REWARDS[0]

    async def give_role_if_higher(self, member, reward):
        reward_index = ROLE_REWARDS.index(reward)
        highest_index = self.get_highest_role_index(member)

        if reward_index <= highest_index:
            return False

        roles_to_remove = []

        for index in range(reward_index):
            role = member.guild.get_role(
                ROLE_REWARDS[index]["role_id"]
            )

            if role and role in member.roles:
                roles_to_remove.append(role)

        if roles_to_remove:
            try:
                await member.remove_roles(*roles_to_remove)
            except discord.HTTPException:
                pass

        role = member.guild.get_role(reward["role_id"])

        if role is None:
            return False

        try:
            await member.add_roles(role)
            return True
        except discord.HTTPException:
            return False

    # =========================================================
    # CHEST OPENING
    # =========================================================

    async def open_one_normal(self, member):
        reward = self.roll_role()

        role_given = await self.give_role_if_higher(
            member,
            reward
        )

        mega_bonus = random.random() < 0.05
        ultra_bonus = random.random() < 0.01

        user = self.get_user_data(member.id)

        if mega_bonus:
            user["mega_chests"] += 1

        if ultra_bonus:
            user["ultra_chests"] += 1

        self.save_data()

        return reward, role_given, mega_bonus, ultra_bonus

    async def open_normal_all(self, member, amount):
        user = self.get_user_data(member.id)

        amount = int(amount)

        if amount <= 0:
            return None

        # Role distribution
        chances = np.array(
            [reward["chance"] for reward in ROLE_REWARDS],
            dtype=float
        )

        chances = chances / chances.sum()

        counts = np.random.multinomial(
            amount,
            chances
        )

        mega_count = int(
            np.random.binomial(amount, 0.05)
        )

        ultra_count = int(
            np.random.binomial(amount, 0.01)
        )

        # Determine highest role actually rolled
        highest_reward_index = int(
            np.max(
                np.nonzero(counts)[0]
            )
        ) if np.any(counts) else -1

        highest_reward = (
            ROLE_REWARDS[highest_reward_index]
            if highest_reward_index >= 0
            else None
        )

        role_given = False

        if highest_reward:
            role_given = await self.give_role_if_higher(
                member,
                highest_reward
            )

        user["mega_chests"] += mega_count
        user["ultra_chests"] += ultra_count

        self.save_data()

        return {
            "counts": counts,
            "mega": mega_count,
            "ultra": ultra_count,
            "highest_reward": highest_reward,
            "role_given": role_given,
        }

    # =========================================================
    # MAIN VIEW
    # =========================================================

    class MainView(discord.ui.View):
        def __init__(self, cog, user_id):
            super().__init__(timeout=MENU_TIMEOUT)

            self.cog = cog
            self.user_id = user_id

        async def interaction_check(self, interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message(
                    self.cog.t(
                        interaction.user.id,
                        "not_yours"
                    ),
                    ephemeral=True
                )
                return False

            return True

        async def on_timeout(self):
            pass

        def language_label(self):
            if self.cog.language(self.user_id) == "ru":
                return "🌐 Русский"

            return "🌐 English"

        @discord.ui.button(
            label="🎁 Chest",
            style=discord.ButtonStyle.primary,
            custom_id="chests_main_chest"
        )
        async def chest_button(self, interaction, button):
            view = self.cog.ChestView(
                self.cog,
                self.user_id
            )

            await interaction.response.edit_message(
                embed=self.cog.make_chest_embed(
                    interaction.user
                ),
                view=view
            )

        @discord.ui.button(
            label="💎 Mega Chest",
            style=discord.ButtonStyle.primary,
            custom_id="chests_main_mega"
        )
        async def mega_button(self, interaction, button):
            view = self.cog.MegaView(
                self.cog,
                self.user_id
            )

            await interaction.response.edit_message(
                embed=self.cog.make_mega_embed(
                    interaction.user
                ),
                view=view
            )

        @discord.ui.button(
            label="⚡ Ultra Chest",
            style=discord.ButtonStyle.primary,
            custom_id="chests_main_ultra"
        )
        async def ultra_button(self, interaction, button):
            view = self.cog.UltraView(
                self.cog,
                self.user_id
            )

            await interaction.response.edit_message(
                embed=self.cog.make_ultra_embed(
                    interaction.user
                ),
                view=view
            )

        @discord.ui.button(
            label="📅 Daily Chest",
            style=discord.ButtonStyle.secondary,
            custom_id="chests_main_daily"
        )
        async def daily_button(self, interaction, button):
            await self.cog.claim_daily(
                interaction,
                self.user_id
            )

        @discord.ui.button(
            label="📆 Weekly Mega",
            style=discord.ButtonStyle.secondary,
            custom_id="chests_main_weekly"
        )
        async def weekly_button(self, interaction, button):
            await self.cog.claim_weekly(
                interaction,
                self.user_id
            )

    # =========================================================
    # NORMAL CHEST VIEW
    # =========================================================

    class ChestView(discord.ui.View):
        def __init__(self, cog, user_id):
            super().__init__(timeout=MENU_TIMEOUT)

            self.cog = cog
            self.user_id = user_id

        async def interaction_check(self, interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message(
                    self.cog.t(
                        interaction.user.id,
                        "not_yours"
                    ),
                    ephemeral=True
                )
                return False

            return True

        @discord.ui.button(
            label="Open",
            style=discord.ButtonStyle.success,
            custom_id="chests_open_normal"
        )
        async def open_button(self, interaction, button):
            await self.cog.open_normal(
                interaction,
                self.user_id
            )

        @discord.ui.button(
            label="Open All",
            style=discord.ButtonStyle.success,
            custom_id="chests_open_normal_all"
        )
        async def open_all_button(self, interaction, button):
            await self.cog.open_normal_all_button(
                interaction,
                self.user_id
            )

        @discord.ui.button(
            label="Back",
            style=discord.ButtonStyle.secondary,
            custom_id="chests_normal_back"
        )
        async def back_button(self, interaction, button):
            await interaction.response.edit_message(
                embed=self.cog.make_main_embed(
                    interaction.user
                ),
                view=self.cog.MainView(
                    self.cog,
                    self.user_id
                )
            )

    # =========================================================
    # MEGA VIEW
    # =========================================================

    class MegaView(discord.ui.View):
        def __init__(self, cog, user_id):
            super().__init__(timeout=MENU_TIMEOUT)

            self.cog = cog
            self.user_id = user_id

        async def interaction_check(self, interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message(
                    self.cog.t(
                        interaction.user.id,
                        "not_yours"
                    ),
                    ephemeral=True
                )
                return False

            return True

        @discord.ui.button(
            label="Open",
            style=discord.ButtonStyle.success,
            custom_id="chests_open_mega"
        )
        async def open_button(self, interaction, button):
            await self.cog.open_mega(
                interaction,
                self.user_id
            )

        @discord.ui.button(
            label="Open All",
            style=discord.ButtonStyle.success,
            custom_id="chests_open_mega_all"
        )
        async def open_all_button(self, interaction, button):
            await self.cog.open_mega_all(
                interaction,
                self.user_id
            )

        @discord.ui.button(
            label="Back",
            style=discord.ButtonStyle.secondary,
            custom_id="chests_mega_back"
        )
        async def back_button(self, interaction, button):
            await interaction.response.edit_message(
                embed=self.cog.make_main_embed(
                    interaction.user
                ),
                view=self.cog.MainView(
                    self.cog,
                    self.user_id
                )
            )

    # =========================================================
    # ULTRA VIEW
    # =========================================================

    class UltraView(discord.ui.View):
        def __init__(self, cog, user_id):
            super().__init__(timeout=MENU_TIMEOUT)

            self.cog = cog
            self.user_id = user_id

        async def interaction_check(self, interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message(
                    self.cog.t(
                        interaction.user.id,
                        "not_yours"
                    ),
                    ephemeral=True
                )
                return False

            return True

        @discord.ui.button(
            label="Open",
            style=discord.ButtonStyle.success,
            custom_id="chests_open_ultra"
        )
        async def open_button(self, interaction, button):
            await self.cog.open_ultra(
                interaction,
                self.user_id
            )

        @discord.ui.button(
            label="Open All",
            style=discord.ButtonStyle.success,
            custom_id="chests_open_ultra_all"
        )
        async def open_all_button(self, interaction, button):
            await self.cog.open_ultra_all(
                interaction,
                self.user_id
            )

        @discord.ui.button(
            label="Back",
            style=discord.ButtonStyle.secondary,
            custom_id="chests_ultra_back"
        )
        async def back_button(self, interaction, button):
            await interaction.response.edit_message(
                embed=self.cog.make_main_embed(
                    interaction.user
                ),
                view=self.cog.MainView(
                    self.cog,
                    self.user_id
                )
            )

    # =========================================================
    # EMBEDS
    # =========================================================

    def make_main_embed(self, member):
        user = self.get_user_data(member.id)

        lang = self.language(member.id)

        daily_available = (
            time.time() >= user["daily_next"]
        )

        weekly_available = (
            time.time() >= user["weekly_next"]
        )

        total = (
            user["chests"]
            + user["mega_chests"]
            + user["ultra_chests"]
        )

        embed = discord.Embed(
            title=f"🎁 {member.display_name}'s Chests",
            color=discord.Color.dark_gray()
        )

        embed.description = (
            f"🌐 Language: "
            f"{'🇷🇺 Russian' if lang == 'ru' else '🇬🇧 English'}\n\n"

            f"🎁 {self.t(member.id, 'chest')}: "
            f"**{user['chests']:,}**\n"

            f"💎 {self.t(member.id, 'mega')}: "
            f"**{user['mega_chests']:,}**\n"

            f"⚡ {self.t(member.id, 'ultra')}: "
            f"**{user['ultra_chests']:,}**\n\n"

            f"{self.t(member.id, 'total')}: **{total:,}**\n\n"

            f"📅 {self.t(member.id, 'daily')}: "
            f"**{self.t(member.id, 'available') if daily_available else self.t(member.id, 'unavailable')}**\n"

            f"📆 {self.t(member.id, 'weekly')}: "
            f"**{self.t(member.id, 'available') if weekly_available else self.t(member.id, 'unavailable')}**"
        )

        return embed

    def make_chest_embed(self, member):
        user = self.get_user_data(member.id)

        embed = discord.Embed(
            title=self.t(member.id, "chest"),
            description=(
                f"🎁 {self.t(member.id, 'chest')}: "
                f"**{user['chests']:,}**"
            ),
            color=discord.Color.dark_gray()
        )

        return embed

    def make_mega_embed(self, member):
        user = self.get_user_data(member.id)

        embed = discord.Embed(
            title=self.t(member.id, "mega"),
            description=(
                f"💎 {self.t(member.id, 'mega')}: "
                f"**{user['mega_chests']:,}**\n\n"
                f"🎁 1 Mega Chest → **1–10 Chest**\n"
                f"🍀 5% chance → **20 Chest**"
            ),
            color=discord.Color.dark_gray()
        )

        return embed

    def make_ultra_embed(self, member):
        user = self.get_user_data(member.id)

        embed = discord.Embed(
            title=self.t(member.id, "ultra"),
            description=(
                f"⚡ {self.t(member.id, 'ultra')}: "
                f"**{user['ultra_chests']:,}**\n\n"
                f"🎁 1 Ultra Chest → **10–20 Chest**\n"
                f"🍀 5% chance → **30 Chest**"
            ),
            color=discord.Color.dark_gray()
        )

        return embed

    # =========================================================
    # NORMAL OPEN
    # =========================================================

    async def open_normal(self, interaction, user_id):
        try:
            if self.has_ultra_role(interaction.user):
                await interaction.response.send_message(
                    self.t(user_id, "ultra_block"),
                    ephemeral=True
                )
                return

            user = self.get_user_data(user_id)

            if user["chests"] <= 0:
                await interaction.response.send_message(
                    self.t(user_id, "no_chests"),
                    ephemeral=True
                )
                return

            await interaction.response.defer()

            user["chests"] -= 1
            self.save_data()

            reward, role_given, mega_bonus, ultra_bonus = (
                await self.open_one_normal(interaction.user)
            )

            lang = self.language(user_id)

            role_name = (
                reward["name_ru"]
                if lang == "ru"
                else reward["name_en"]
            )

            result = (
                f"🎁 **{role_name}**\n"
                f"🎯 Chance: **{reward['chance']}%**"
            )

            if role_given:
                result += (
                    "\n\n✅ "
                    + (
                        "You received a new role!"
                        if lang == "en"
                        else "Вы получили новую роль!"
                    )
                )
            else:
                result += (
                    "\n\nℹ️ "
                    + (
                        "You already have this role or a higher one."
                        if lang == "en"
                        else "У вас уже есть эта или более высокая роль."
                    )
                )

            if mega_bonus:
                result += (
                    "\n💎 +1 Mega Chest"
                    if lang == "en"
                    else "\n💎 +1 Мега-сундук"
                )

            if ultra_bonus:
                result += (
                    "\n⚡ +1 Ultra Chest"
                    if lang == "en"
                    else "\n⚡ +1 Ультра-сундук"
                )

            embed = discord.Embed(
                title="🎁 Chest Opened"
                if lang == "en"
                else "🎁 Сундук открыт",
                description=result,
                color=discord.Color.dark_gray()
            )

            await interaction.edit_original_response(
                embed=embed,
                view=self.ChestView(
                    self,
                    user_id
                )
            )

        except Exception as e:
            print(f"❌ Normal chest error: {repr(e)}")

            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Something went wrong.",
                    ephemeral=True
                )
            else:
                try:
                    await interaction.followup.send(
                        "❌ Something went wrong.",
                        ephemeral=True
                    )
                except Exception:
                    pass

    async def open_normal_all_button(self, interaction, user_id):
        try:
            if self.has_ultra_role(interaction.user):
                await interaction.response.send_message(
                    self.t(user_id, "ultra_block"),
                    ephemeral=True
                )
                return

            user = self.get_user_data(user_id)

            amount = user["chests"]

            if amount <= 0:
                await interaction.response.send_message(
                    self.t(user_id, "no_chests"),
                    ephemeral=True
                )
                return

            await interaction.response.defer()

            user["chests"] = 0
            self.save_data()

            result = await self.open_normal_all(
                interaction.user,
                amount
            )

            lang = self.language(user_id)

            description = (
                f"🎁 **{amount:,}** "
                + (
                    "chests opened!"
                    if lang == "en"
                    else "сундуков открыто!"
                )
                + "\n\n"
            )

            for index, reward in enumerate(ROLE_REWARDS):
                count = int(result["counts"][index])

                if count > 0:
                    name = (
                        reward["name_ru"]
                        if lang == "ru"
                        else reward["name_en"]
                    )

                    description += (
                        f"• **{name}**: `{count:,}`\n"
                    )

            if result["mega"] > 0:
                description += (
                    f"\n💎 +**{result['mega']:,}** "
                    + (
                        "Mega Chest"
                        if lang == "en"
                        else "Мега-сундук"
                    )
                )

            if result["ultra"] > 0:
                description += (
                    f"\n⚡ +**{result['ultra']:,}** "
                    + (
                        "Ultra Chest"
                        if lang == "en"
                        else "Ультра-сундук"
                    )
                )

            if result["highest_reward"]:
                reward = result["highest_reward"]

                if result["role_given"]:
                    description += (
                        "\n\n✅ "
                        + (
                            "Your highest rolled role was given."
                            if lang == "en"
                            else "Вам выдана самая высокая выпавшая роль."
                        )
                    )
                else:
                    description += (
                        "\n\nℹ️ "
                        + (
                            "You already have an equal or higher role."
                            if lang == "en"
                            else "У вас уже есть такая или более высокая роль."
                        )
                    )

            embed = discord.Embed(
                title=(
                    "🎁 Chests Opened"
                    if lang == "en"
                    else "🎁 Сундуки открыты"
                ),
                description=description,
                color=discord.Color.dark_gray()
            )

            await interaction.edit_original_response(
                embed=embed,
                view=self.ChestView(
                    self,
                    user_id
                )
            )

        except Exception as e:
            print(f"❌ Open all error: {repr(e)}")

            try:
                await interaction.followup.send(
                    "❌ Something went wrong.",
                    ephemeral=True
                )
            except Exception:
                pass

    # =========================================================
    # MEGA OPEN
    # =========================================================

    async def open_mega(self, interaction, user_id):
        try:
            if self.has_ultra_role(interaction.user):
                await interaction.response.send_message(
                    self.t(user_id, "ultra_block"),
                    ephemeral=True
                )
                return

            user = self.get_user_data(user_id)

            if user["mega_chests"] <= 0:
                await interaction.response.send_message(
                    self.t(user_id, "no_chests"),
                    ephemeral=True
                )
                return

            await interaction.response.defer()

            user["mega_chests"] -= 1

            lucky = random.random() < 0.05

            amount = 20 if lucky else random.randint(1, 10)

            user["chests"] += amount

            self.save_data()

            lang = self.language(user_id)

            description = (
                f"💎 **Mega Chest Opened!**\n\n"
                f"🎁 +**{amount}** "
                + (
                    "Chest"
                    if lang == "en"
                    else "сундук"
                )
            )

            if lucky:
                description += (
                    "\n\n🍀 **5% Lucky Reward!**"
                    if lang == "en"
                    else "\n\n🍀 **Счастливый приз 5%!**"
                )

            embed = discord.Embed(
                title="💎 Mega Chest",
                description=description,
                color=discord.Color.dark_gray()
            )

            await interaction.edit_original_response(
                embed=embed,
                view=self.MegaView(
                    self,
                    user_id
                )
            )

        except Exception as e:
            print(f"❌ Mega chest error: {repr(e)}")

            try:
                await interaction.followup.send(
                    "❌ Something went wrong.",
                    ephemeral=True
                )
            except Exception:
                pass

    async def open_mega_all(self, interaction, user_id):
        try:
            if self.has_ultra_role(interaction.user):
                await interaction.response.send_message(
                    self.t(user_id, "ultra_block"),
                    ephemeral=True
                )
                return

            user = self.get_user_data(user_id)

            amount = user["mega_chests"]

            if amount <= 0:
                await interaction.response.send_message(
                    self.t(user_id, "no_chests"),
                    ephemeral=True
                )
                return

            await interaction.response.defer()

            lucky = int(
                np.random.binomial(
                    amount,
                    0.05
                )
            )

            normal_count = amount - lucky

            normal_rewards = (
                int(
                    np.random.randint(
                        1,
                        11,
                        size=normal_count
                    ).sum()
                )
                if normal_count > 0
                else 0
            )

            total_chests = (
                normal_rewards
                + lucky * 20
            )

            user["mega_chests"] = 0
            user["chests"] += total_chests

            self.save_data()

            lang = self.language(user_id)

            description = (
                f"💎 **{amount:,} Mega Chest** "
                + (
                    "opened!"
                    if lang == "en"
                    else "открыто!"
                )
                + "\n\n"
                f"🎁 +**{total_chests:,} Chest**"
            )

            if lucky:
                description += (
                    f"\n🍀 Lucky: **{lucky:,}**"
                )

            embed = discord.Embed(
                title="💎 Mega Chests",
                description=description,
                color=discord.Color.dark_gray()
            )

            await interaction.edit_original_response(
                embed=embed,
                view=self.MegaView(
                    self,
                    user_id
                )
            )

        except Exception as e:
            print(f"❌ Mega all error: {repr(e)}")

            try:
                await interaction.followup.send(
                    "❌ Something went wrong.",
                    ephemeral=True
                )
            except Exception:
                pass

    # =========================================================
    # ULTRA OPEN
    # =========================================================

    async def open_ultra(self, interaction, user_id):
        try:
            if self.has_ultra_role(interaction.user):
                await interaction.response.send_message(
                    self.t(user_id, "ultra_block"),
                    ephemeral=True
                )
                return

            user = self.get_user_data(user_id)

            if user["ultra_chests"] <= 0:
                await interaction.response.send_message(
                    self.t(user_id, "no_chests"),
                    ephemeral=True
                )
                return

            await interaction.response.defer()

            user["ultra_chests"] -= 1

            lucky = random.random() < 0.05

            amount = (
                30
                if lucky
                else random.randint(10, 20)
            )

            user["chests"] += amount

            self.save_data()

            lang = self.language(user_id)

            description = (
                f"⚡ **Ultra Chest Opened!**\n\n"
                f"🎁 +**{amount}** "
                + (
                    "Chest"
                    if lang == "en"
                    else "сундук"
                )
            )

            if lucky:
                description += (
                    "\n\n🍀 **5% Lucky Reward!**"
                    if lang == "en"
                    else "\n\n🍀 **Счастливый приз 5%!**"
                )

            embed = discord.Embed(
                title="⚡ Ultra Chest",
                description=description,
                color=discord.Color.dark_gray()
            )

            await interaction.edit_original_response(
                embed=embed,
                view=self.UltraView(
                    self,
                    user_id
                )
            )

        except Exception as e:
            print(f"❌ Ultra chest error: {repr(e)}")

            try:
                await interaction.followup.send(
                    "❌ Something went wrong.",
                    ephemeral=True
                )
            except Exception:
                pass

    async def open_ultra_all(self, interaction, user_id):
        try:
            if self.has_ultra_role(interaction.user):
                await interaction.response.send_message(
                    self.t(user_id, "ultra_block"),
                    ephemeral=True
                )
                return

            user = self.get_user_data(user_id)

            amount = user["ultra_chests"]

            if amount <= 0:
                await interaction.response.send_message(
                    self.t(user_id, "no_chests"),
                    ephemeral=True
                )
                return

            await interaction.response.defer()

            lucky = int(
                np.random.binomial(
                    amount,
                    0.05
                )
            )

            normal_count = amount - lucky

            normal_rewards = (
                int(
                    np.random.randint(
                        10,
                        21,
                        size=normal_count
                    ).sum()
                )
                if normal_count > 0
                else 0
            )

            total_chests = (
                normal_rewards
                + lucky * 30
            )

            user["ultra_chests"] = 0
            user["chests"] += total_chests

            self.save_data()

            lang = self.language(user_id)

            description = (
                f"⚡ **{amount:,} Ultra Chest** "
                + (
                    "opened!"
                    if lang == "en"
                    else "открыто!"
                )
                + "\n\n"
                f"🎁 +**{total_chests:,} Chest**"
            )

            if lucky:
                description += (
                    f"\n🍀 Lucky: **{lucky:,}**"
                )

            embed = discord.Embed(
                title="⚡ Ultra Chests",
                description=description,
                color=discord.Color.dark_gray()
            )

            await interaction.edit_original_response(
                embed=embed,
                view=self.UltraView(
                    self,
                    user_id
                )
            )

        except Exception as e:
            print(f"❌ Ultra all error: {repr(e)}")

            try:
                await interaction.followup.send(
                    "❌ Something went wrong.",
                    ephemeral=True
                )
            except Exception:
                pass

    # =========================================================
    # DAILY
    # =========================================================

    async def claim_daily(self, interaction, user_id):
        try:
            if self.has_ultra_role(interaction.user):
                await interaction.response.send_message(
                    self.t(user_id, "ultra_block"),
                    ephemeral=True
                )
                return

            user = self.get_user_data(user_id)

            now = time.time()

            if now < user["daily_next"]:
                await interaction.response.send_message(
                    self.t(user_id, "daily_claimed"),
                    ephemeral=True
                )
                return

            await interaction.response.defer()

            user["chests"] += 1
            user["daily_next"] = int(
                now + DAILY_COOLDOWN
            )

            self.save_data()

            embed = discord.Embed(
                title="📅 Daily Chest",
                description=self.t(
                    user_id,
                    "daily_received"
                ),
                color=discord.Color.dark_gray()
            )

            await interaction.edit_original_response(
                embed=embed,
                view=self.MainView(
                    self,
                    user_id
                )
            )

        except Exception as e:
            print(f"❌ Daily chest error: {repr(e)}")

            try:
                await interaction.followup.send(
                    "❌ Something went wrong.",
                    ephemeral=True
                )
            except Exception:
                pass

    # =========================================================
    # WEEKLY
    # =========================================================

    async def claim_weekly(self, interaction, user_id):
        try:
            if self.has_ultra_role(interaction.user):
                await interaction.response.send_message(
                    self.t(user_id, "ultra_block"),
                    ephemeral=True
                )
                return

            user = self.get_user_data(user_id)

            now = time.time()

            if now < user["weekly_next"]:
                await interaction.response.send_message(
                    self.t(user_id, "weekly_claimed"),
                    ephemeral=True
                )
                return

            await interaction.response.defer()

            user["mega_chests"] += 1
            user["weekly_next"] = int(
                now + WEEKLY_COOLDOWN
            )

            self.save_data()

            embed = discord.Embed(
                title="📆 Weekly Mega",
                description=self.t(
                    user_id,
                    "weekly_received"
                ),
                color=discord.Color.dark_gray()
            )

            await interaction.edit_original_response(
                embed=embed,
                view=self.MainView(
                    self,
                    user_id
                )
            )

        except Exception as e:
            print(f"❌ Weekly chest error: {repr(e)}")

            try:
                await interaction.followup.send(
                    "❌ Something went wrong.",
                    ephemeral=True
                )
            except Exception:
                pass

    # =========================================================
    # LANGUAGE VIEW
    # =========================================================

    class LanguageView(discord.ui.View):
        def __init__(self, cog, user_id):
            super().__init__(timeout=MENU_TIMEOUT)

            self.cog = cog
            self.user_id = user_id

        async def interaction_check(self, interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message(
                    self.cog.t(
                        interaction.user.id,
                        "not_yours"
                    ),
                    ephemeral=True
                )
                return False

            return True

        @discord.ui.button(
            label="🇬🇧 EN",
            style=discord.ButtonStyle.primary,
            custom_id="chests_language_en"
        )
        async def english(self, interaction, button):
            user = self.cog.get_user_data(
                self.user_id
            )

            user["language"] = "en"
            self.cog.save_data()

            await interaction.response.edit_message(
                embed=self.cog.make_main_embed(
                    interaction.user
                ),
                view=self.cog.MainView(
                    self.cog,
                    self.user_id
                )
            )

        @discord.ui.button(
            label="🇷🇺 RU",
            style=discord.ButtonStyle.primary,
            custom_id="chests_language_ru"
        )
        async def russian(self, interaction, button):
            user = self.cog.get_user_data(
                self.user_id
            )

            user["language"] = "ru"
            self.cog.save_data()

            await interaction.response.edit_message(
                embed=self.cog.make_main_embed(
                    interaction.user
                ),
                view=self.cog.MainView(
                    self.cog,
                    self.user_id
                )
            )

    # =========================================================
    # ADMIN CHEST MODAL
    # =========================================================

    class AdminChestModal(discord.ui.Modal):
        def __init__(self, cog):
            super().__init__(
                title="Admin — Give Chests"
            )

            self.cog = cog

            self.user_input = discord.ui.TextInput(
                label="User",
                placeholder="User ID or @mention",
                required=True,
                max_length=30
            )

            self.amount_input = discord.ui.TextInput(
                label="Quantity",
                placeholder="Example: 10",
                required=True,
                max_length=10
            )

            self.chest_input = discord.ui.TextInput(
                label="Chest",
                placeholder="chest / mega / ultra",
                required=True,
                max_length=20
            )

            self.add_item(self.user_input)
            self.add_item(self.amount_input)
            self.add_item(self.chest_input)

        async def on_submit(self, interaction):
            try:
                await interaction.response.defer(
                    ephemeral=True
                )

                # USER
                user_text = self.user_input.value.strip()

                if user_text.startswith("<@"):
                    user_text = (
                        user_text
                        .replace("<@", "")
                        .replace("!", "")
                        .replace(">", "")
                    )

                try:
                    user_id = int(user_text)
                except ValueError:
                    await interaction.followup.send(
                        "❌ Invalid user ID or mention.",
                        ephemeral=True
                    )
                    return

                # AMOUNT
                try:
                    amount = int(
                        self.amount_input.value.strip()
                    )
                except ValueError:
                    await interaction.followup.send(
                        "❌ Quantity must be a number.",
                        ephemeral=True
                    )
                    return

                if amount <= 0:
                    await interaction.followup.send(
                        "❌ Quantity must be greater than 0.",
                        ephemeral=True
                    )
                    return

                # CHEST TYPE
                chest_text = (
                    self.chest_input.value
                    .strip()
                    .lower()
                )

                chest_aliases = {
                    "chest": "chest",
                    "normal": "chest",
                    "сундук": "chest",
                    "обычный": "chest",

                    "mega": "mega",
                    "мега": "mega",
                    "мега-сундук": "mega",

                    "ultra": "ultra",
                    "ультра": "ultra",
                    "ультра-сундук": "ultra",
                }

                chest_type = chest_aliases.get(
                    chest_text
                )

                if chest_type is None:
                    await interaction.followup.send(
                        "❌ Invalid chest type.\n\n"
                        "Use: `chest`, `mega` or `ultra`.",
                        ephemeral=True
                    )
                    return

                # MEMBER
                member = interaction.guild.get_member(
                    user_id
                )

                if member is None:
                    try:
                        member = await interaction.guild.fetch_member(
                            user_id
                        )
                    except discord.NotFound:
                        await interaction.followup.send(
                            "❌ User was not found on this server.",
                            ephemeral=True
                        )
                        return
                    except discord.HTTPException:
                        await interaction.followup.send(
                            "❌ Failed to find this user.",
                            ephemeral=True
                        )
                        return

                success = await self.cog.add_chests(
                    user_id,
                    amount,
                    chest_type=chest_type
                )

                if not success:
                    await interaction.followup.send(
                        "❌ Failed to give the chests.",
                        ephemeral=True
                    )
                    return

                chest_names = {
                    "chest": "🎁 Chest",
                    "mega": "💎 Mega Chest",
                    "ultra": "⚡ Ultra Chest",
                }

                await interaction.followup.send(
                    f"✅ Successfully gave "
                    f"**{amount:,} × "
                    f"{chest_names[chest_type]}** "
                    f"to {member.mention}.",
                    ephemeral=True
                )

            except Exception as e:
                print(
                    f"❌ Admin chest form error: "
                    f"{repr(e)}"
                )

                try:
                    await interaction.followup.send(
                        "❌ Something went wrong while "
                        "giving the chests.",
                        ephemeral=True
                    )
                except Exception:
                    pass

    # =========================================================
    # ADMIN VIEW
    # =========================================================

    class AdminChestsView(discord.ui.View):
        def __init__(self, cog):
            super().__init__(timeout=None)

            self.cog = cog

        @discord.ui.button(
            label="⚙️ Admin Chests",
            style=discord.ButtonStyle.primary,
            custom_id="admin_chests_open_form"
        )
        async def open_form(
            self,
            interaction,
            button
        ):
            try:
                if interaction.user.id != OWNER_ID:
                    await interaction.response.send_message(
                        "❌ You are not allowed to use this.",
                        ephemeral=True
                    )
                    return

                await interaction.response.send_modal(
                    self.cog.AdminChestModal(
                        self.cog
                    )
                )

            except Exception as e:
                print(
                    f"❌ Admin chest button error: "
                    f"{repr(e)}"
                )

                try:
                    if not interaction.response.is_done():
                        await interaction.response.send_message(
                            "❌ Something went wrong.",
                            ephemeral=True
                        )
                    else:
                        await interaction.followup.send(
                            "❌ Something went wrong.",
                            ephemeral=True
                        )
                except Exception:
                    pass

    # =========================================================
    # !CHESTS
    # =========================================================

    @commands.command(name="chests")
    async def chests_command(self, ctx):
        try:
            user = self.get_user_data(
                ctx.author.id
            )

            if not user.get("language"):
                await ctx.send(
                    embed=discord.Embed(
                        title="🌐 Select your language",
                        description=(
                            "Please select the language "
                            "for the chest system."
                        ),
                        color=discord.Color.dark_gray()
                    ),
                    view=self.LanguageView(
                        self,
                        ctx.author.id
                    )
                )

            else:
                await ctx.send(
                    embed=self.make_main_embed(
                        ctx.author
                    ),
                    view=self.MainView(
                        self,
                        ctx.author.id
                    )
                )

            try:
                await ctx.message.delete()
            except (
                discord.Forbidden,
                discord.HTTPException
            ):
                pass

        except Exception as e:
            print(
                f"❌ !chests error: {repr(e)}"
            )

    # =========================================================
    # !ADMIN CHESTS
    # =========================================================

    @commands.command(name="admin")
    async def admin_command(
        self,
        ctx,
        section=None
    ):
        try:
            if ctx.author.id != OWNER_ID:
                return

            if section is None:
                return

            if section.lower() != "chests":
                return

            await ctx.send(
                content="⚙️ **Admin Chests**",
                view=self.AdminChestsView(
                    self
                )
            )

            try:
                await ctx.message.delete()
            except (
                discord.Forbidden,
                discord.HTTPException
            ):
                pass

        except Exception as e:
            print(
                f"❌ !admin chests error: "
                f"{repr(e)}"
            )


# =============================================================
# SETUP
# =============================================================

async def setup(bot):
    cog = Chests(bot)

    await bot.add_cog(cog)

    bot.add_view(
        Chests.AdminChestsView(cog)
    )

    print("✅ Chests cog loaded!")
