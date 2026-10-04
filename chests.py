import os
import json
import random
import tempfile
import time
import shutil

import discord
import numpy as np
from discord.ext import commands


# =========================================================
# SETTINGS
# =========================================================

DATA_FILE = "chests_data.json"

MENU_TIMEOUT = 300
DAILY_COOLDOWN = 86400
WEEKLY_COOLDOWN = 604800

OWNER_ID = 1176149190192152626
ULTRA_ROLE_ID = 1529128872036143164


# =========================================================
# CHEST ROLES
# =========================================================

ROLE_REWARDS = [
    ("Common", 1529127245128667308, 40.0),
    ("Uncommon", 1529155257081401575, 25.0),
    ("Rare", 1529127682392985731, 17.0),
    ("Epic", 1529127837192159494, 10.0),
    ("Heroic", 1529155677476356198, 5.0),
    ("Mythic", 1529128399094681760, 2.2),
    ("Legendary", 1529128791916544111, 0.6),
    ("Cosmic", 1529156030317990019, 0.15),
    ("Galactic", 1529156293393383474, 0.04),
    ("Ultra", 1529128872036143164, 0.01),
]


# =========================================================
# DEFAULT DATA
# =========================================================

DEFAULT_USER_DATA = {
    "chests": 0,
    "mega_chests": 0,
    "ultra_chests": 0,
    "language": None,
    "daily_next": 0,
    "weekly_next": 0
}


# =========================================================
# COG
# =========================================================

class Chests(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.data_load_failed = False
        self.data = self.load_data()

    # =====================================================
    # DATA
    # =====================================================

    def load_data(self):

        if not os.path.exists(DATA_FILE):
            return {"users": {}}

        try:

            with open(
                DATA_FILE,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(f)

            if not isinstance(data, dict):
                raise ValueError("Invalid data")

            if not isinstance(
                data.get("users"),
                dict
            ):
                raise ValueError("Invalid users data")

            data.setdefault("users", {})

            return data

        except Exception as error:

            print(
                f"❌ Failed to load {DATA_FILE}: "
                f"{repr(error)}"
            )

            backup_file = DATA_FILE + ".bak"

            if os.path.exists(backup_file):

                try:

                    with open(
                        backup_file,
                        "r",
                        encoding="utf-8"
                    ) as f:
                        backup_data = json.load(f)

                    if (
                        isinstance(backup_data, dict)
                        and isinstance(
                            backup_data.get("users"),
                            dict
                        )
                    ):

                        print(
                            "✅ Restored chest data from backup."
                        )

                        return backup_data

                except Exception as backup_error:

                    print(
                        "❌ Failed to load backup: "
                        f"{repr(backup_error)}"
                    )

            self.data_load_failed = True

            print(
                "⚠️ Chest data is unavailable. "
                "Saving is disabled to protect existing data."
            )

            return {"users": {}}

    def save_data(self):

        # NEVER overwrite the original file if loading failed.
        if self.data_load_failed:

            print(
                "⚠️ Save skipped because chest data "
                "could not be loaded safely."
            )

            return False

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
            ) as f:

                json.dump(
                    self.data,
                    f,
                    ensure_ascii=False,
                    indent=4
                )

                f.flush()
                os.fsync(
                    f.fileno()
                )

            # Keep a backup of the last known-good file.
            if os.path.exists(DATA_FILE):

                backup_file = DATA_FILE + ".bak"

                try:

                    shutil.copy2(
                        DATA_FILE,
                        backup_file
                    )

                except OSError as backup_error:

                    print(
                        "⚠️ Could not create backup: "
                        f"{repr(backup_error)}"
                    )

            os.replace(
                temp_path,
                DATA_FILE
            )

            return True

        except Exception:

            try:
                os.remove(temp_path)
            except Exception:
                pass

            raise

    def get_user_data(self, user_id):

        user_id = str(user_id)

        if user_id not in self.data["users"]:

            self.data["users"][user_id] = {
                **DEFAULT_USER_DATA
            }

            self.save_data()

        else:

            changed = False

            for key, value in DEFAULT_USER_DATA.items():

                if key not in self.data["users"][user_id]:

                    self.data["users"][user_id][key] = value
                    changed = True

            if changed:
                self.save_data()

        return self.data["users"][user_id]

    # =====================================================
    # HIDDEN INTERACTION ERROR
    # =====================================================

    async def hidden_error(
        self,
        interaction,
        message="❌ An error occurred."
    ):

        try:

            if interaction.response.is_done():

                await interaction.followup.send(
                    message,
                    ephemeral=True
                )

            else:

                await interaction.response.send_message(
                    message,
                    ephemeral=True
                )

        except Exception as error:

            print(
                "❌ Failed to send hidden error: "
                f"{repr(error)}"
            )

    # =====================================================
    # ADD CHESTS
    # =====================================================

    async def add_chests(
        self,
        user_id,
        amount,
        chest_type="chest"
    ):

        user = self.get_user_data(user_id)

        amount = int(amount)

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

    # =====================================================
    # LANGUAGE
    # =====================================================

    def language_text(self, user):

        return (
            "🇬🇧 English"
            if user.get("language") == "en"
            else "🇷🇺 Russian"
        )

    def is_russian(self, user):

        return user.get("language") == "ru"

    # =====================================================
    # ROLE HELPERS
    # =====================================================

    def get_highest_role_index(self, member):

        role_ids = {
            role_id: index
            for index, (_, role_id, _) in enumerate(
                ROLE_REWARDS
            )
        }

        highest = -1

        for role in member.roles:

            if role.id in role_ids:

                highest = max(
                    highest,
                    role_ids[role.id]
                )

        return highest

    async def give_best_role(
        self,
        member,
        rolled_index
    ):

        current_index = self.get_highest_role_index(
            member
        )

        if rolled_index <= current_index:
            return False, None

        role_name, role_id, _ = ROLE_REWARDS[
            rolled_index
        ]

        new_role = member.guild.get_role(
            role_id
        )

        if new_role is None:
            return False, None

        roles_to_remove = []

        for index in range(rolled_index):

            role = member.guild.get_role(
                ROLE_REWARDS[index][1]
            )

            if role and role in member.roles:
                roles_to_remove.append(role)

        if roles_to_remove:

            try:

                await member.remove_roles(
                    *roles_to_remove
                )

            except Exception:
                pass

        try:

            await member.add_roles(
                new_role
            )

        except Exception:
            return False, None

        return True, role_name

    # =====================================================
    # CHEST ROLL
    # =====================================================

    def roll_normal(self):

        chances = [
            item[2]
            for item in ROLE_REWARDS
        ]

        values = np.random.multinomial(
            1,
            np.array(chances) / 100
        )

        return int(
            np.argmax(values)
        )

    # =====================================================
    # NORMAL CHEST
    # =====================================================

    async def open_normal(
        self,
        interaction
    ):

        try:

            user = self.get_user_data(
                interaction.user.id
            )

            if user["chests"] <= 0:

                await self.hidden_error(
                    interaction,
                    "❌ You don't have any Chests."
                )
                return

            if isinstance(
                interaction.user,
                discord.Member
            ):

                if any(
                    role.id == ULTRA_ROLE_ID
                    for role in interaction.user.roles
                ):

                    await self.hidden_error(
                        interaction,
                        "❌ You cannot open chests while you have the Ultra role."
                    )
                    return

            user["chests"] -= 1
            self.save_data()

            rolled = self.roll_normal()

            given, role_name = await self.give_best_role(
                interaction.user,
                rolled
            )

            reward_name = ROLE_REWARDS[rolled][0]

            if given:

                text = (
                    f"🎁 **Chest opened!**\n\n"
                    f"🏆 You received **{reward_name}**!"
                )

            else:

                current = self.get_highest_role_index(
                    interaction.user
                )

                if current >= 0:
                    current_name = ROLE_REWARDS[current][0]
                else:
                    current_name = "None"

                text = (
                    f"🎁 **Chest opened!**\n\n"
                    f"🎲 Rolled: **{reward_name}**\n"
                    f"🏆 Your current highest role: **{current_name}**\n\n"
                    "You already have an equal or higher role."
                )

            await interaction.response.edit_message(
                embed=discord.Embed(
                    description=text,
                    color=discord.Color.blurple()
                ),
                view=ChestOpenView(
                    self,
                    interaction.user.id
                )
            )

        except Exception as error:

            print(
                f"❌ open_normal error: {repr(error)}"
            )

            await self.hidden_error(
                interaction
            )

    # =====================================================
    # NORMAL OPEN ALL
    # =====================================================

    async def open_normal_all(
        self,
        interaction
    ):

        try:

            user = self.get_user_data(
                interaction.user.id
            )

            amount = int(user["chests"])

            if amount <= 0:

                await self.hidden_error(
                    interaction,
                    "❌ You don't have any Chests."
                )
                return

            if isinstance(
                interaction.user,
                discord.Member
            ):

                if any(
                    role.id == ULTRA_ROLE_ID
                    for role in interaction.user.roles
                ):

                    await self.hidden_error(
                        interaction,
                        "❌ You cannot open chests while you have the Ultra role."
                    )
                    return

            chances = np.array([
                item[2]
                for item in ROLE_REWARDS
            ]) / 100

            results = np.random.multinomial(
                amount,
                chances
            )

            highest_rolled = -1

            for index, count in enumerate(results):

                if count > 0:
                    highest_rolled = index

            user["chests"] = 0
            self.save_data()

            given, role_name = await self.give_best_role(
                interaction.user,
                highest_rolled
            )

            lines = [
                f"🎁 **Opened {amount:,} Chests!**",
                ""
            ]

            for index, count in enumerate(results):

                if count > 0:

                    lines.append(
                        f"**{ROLE_REWARDS[index][0]}:** "
                        f"{int(count):,}"
                    )

            if given:

                lines.extend([
                    "",
                    f"🏆 New highest role: **{role_name}**"
                ])

            else:

                lines.extend([
                    "",
                    "You already have an equal or higher role."
                ])

            await interaction.response.edit_message(
                embed=discord.Embed(
                    description="\n".join(lines),
                    color=discord.Color.blurple()
                ),
                view=ChestOpenView(
                    self,
                    interaction.user.id
                )
            )

        except Exception as error:

            print(
                f"❌ open_normal_all error: {repr(error)}"
            )

            await self.hidden_error(
                interaction
            )

    # =====================================================
    # MEGA CHEST
    # =====================================================

    def mega_reward(self):

        if random.random() <= 0.05:
            return 20

        return random.randint(1, 10)

    async def open_mega(
        self,
        interaction
    ):

        try:

            user = self.get_user_data(
                interaction.user.id
            )

            if user["mega_chests"] <= 0:

                await self.hidden_error(
                    interaction,
                    "❌ You don't have any Mega Chests."
                )
                return

            if isinstance(
                interaction.user,
                discord.Member
            ):

                if any(
                    role.id == ULTRA_ROLE_ID
                    for role in interaction.user.roles
                ):

                    await self.hidden_error(
                        interaction,
                        "❌ You cannot open chests while you have the Ultra role."
                    )
                    return

            user["mega_chests"] -= 1

            amount = self.mega_reward()

            user["chests"] += amount

            self.save_data()

            await interaction.response.edit_message(
                embed=discord.Embed(
                    description=(
                        "💎 **Mega Chest opened!**\n\n"
                        f"🎁 You received **{amount} Chest"
                        f"{'s' if amount != 1 else ''}**!"
                    ),
                    color=discord.Color.blurple()
                ),
                view=MegaOpenView(
                    self,
                    interaction.user.id
                )
            )

        except Exception as error:

            print(
                f"❌ open_mega error: {repr(error)}"
            )

            await self.hidden_error(
                interaction
            )

    async def open_mega_all(
        self,
        interaction
    ):

        try:

            user = self.get_user_data(
                interaction.user.id
            )

            amount = int(user["mega_chests"])

            if amount <= 0:

                await self.hidden_error(
                    interaction,
                    "❌ You don't have any Mega Chests."
                )
                return

            lucky = np.random.binomial(
                amount,
                0.05
            )

            normal = amount - lucky

            total = (
                normal * 5.5
                + lucky * 14.5
            )

            total = int(round(total))

            if amount < 100000:

                total = sum(
                    20 if random.random() <= 0.05
                    else random.randint(1, 10)
                    for _ in range(amount)
                )

            user["mega_chests"] = 0
            user["chests"] += total

            self.save_data()

            await interaction.response.edit_message(
                embed=discord.Embed(
                    description=(
                        f"💎 **Opened {amount:,} Mega Chests!**\n\n"
                        f"🎁 You received **{total:,} Chests**!"
                    ),
                    color=discord.Color.blurple()
                ),
                view=MegaOpenView(
                    self,
                    interaction.user.id
                )
            )

        except Exception as error:

            print(
                f"❌ open_mega_all error: {repr(error)}"
            )

            await self.hidden_error(
                interaction
            )

    # =====================================================
    # ULTRA CHEST
    # =====================================================

    def ultra_reward(self):

        if random.random() <= 0.05:
            return 30

        return random.randint(10, 20)

    async def open_ultra(
        self,
        interaction
    ):

        try:

            user = self.get_user_data(
                interaction.user.id
            )

            if user["ultra_chests"] <= 0:

                await self.hidden_error(
                    interaction,
                    "❌ You don't have any Ultra Chests."
                )
                return

            if isinstance(
                interaction.user,
                discord.Member
            ):

                if any(
                    role.id == ULTRA_ROLE_ID
                    for role in interaction.user.roles
                ):

                    await self.hidden_error(
                        interaction,
                        "❌ You cannot open chests while you have the Ultra role."
                    )
                    return

            user["ultra_chests"] -= 1

            amount = self.ultra_reward()

            user["chests"] += amount

            self.save_data()

            await interaction.response.edit_message(
                embed=discord.Embed(
                    description=(
                        "⚡ **Ultra Chest opened!**\n\n"
                        f"🎁 You received **{amount} Chests**!"
                    ),
                    color=discord.Color.blurple()
                ),
                view=UltraOpenView(
                    self,
                    interaction.user.id
                )
            )

        except Exception as error:

            print(
                f"❌ open_ultra error: {repr(error)}"
            )

            await self.hidden_error(
                interaction
            )

    async def open_ultra_all(
        self,
        interaction
    ):

        try:

            user = self.get_user_data(
                interaction.user.id
            )

            amount = int(user["ultra_chests"])

            if amount <= 0:

                await self.hidden_error(
                    interaction,
                    "❌ You don't have any Ultra Chests."
                )
                return

            lucky = np.random.binomial(
                amount,
                0.05
            )

            normal = amount - lucky

            total = (
                normal * 15
                + lucky * 30
            )

            if amount < 100000:

                total = sum(
                    30 if random.random() <= 0.05
                    else random.randint(10, 20)
                    for _ in range(amount)
                )

            user["ultra_chests"] = 0
            user["chests"] += total

            self.save_data()

            await interaction.response.edit_message(
                embed=discord.Embed(
                    description=(
                        f"⚡ **Opened {amount:,} Ultra Chests!**\n\n"
                        f"🎁 You received **{total:,} Chests**!"
                    ),
                    color=discord.Color.blurple()
                ),
                view=UltraOpenView(
                    self,
                    interaction.user.id
                )
            )

        except Exception as error:

            print(
                f"❌ open_ultra_all error: {repr(error)}"
            )

            await self.hidden_error(
                interaction
            )

    # =====================================================
    # DAILY
    # =====================================================

    async def daily(
        self,
        interaction
    ):

        try:

            user = self.get_user_data(
                interaction.user.id
            )

            if isinstance(
                interaction.user,
                discord.Member
            ):

                if any(
                    role.id == ULTRA_ROLE_ID
                    for role in interaction.user.roles
                ):

                    await self.hidden_error(
                        interaction,
                        "❌ You cannot open chests while you have the Ultra role."
                    )
                    return

            now = time.time()

            if now < user["daily_next"]:

                remaining = int(
                    user["daily_next"] - now
                )

                hours = remaining // 3600
                minutes = (
                    remaining % 3600
                ) // 60

                await self.hidden_error(
                    interaction,
                    f"⏰ Daily Chest is unavailable.\n\n"
                    f"Available again in **{hours}h {minutes}m**."
                )
                return

            user["daily_next"] = now + DAILY_COOLDOWN
            user["chests"] += 1

            self.save_data()

            await interaction.response.edit_message(
                embed=discord.Embed(
                    description=(
                        "📅 **Daily Chest claimed!**\n\n"
                        "🎁 You received **1 Chest**!"
                    ),
                    color=discord.Color.blurple()
                ),
                view=MainView(
                    self,
                    interaction.user.id
                )
            )

        except Exception as error:

            print(
                f"❌ daily error: {repr(error)}"
            )

            await self.hidden_error(
                interaction
            )

    # =====================================================
    # WEEKLY
    # =====================================================

    async def weekly(
        self,
        interaction
    ):

        try:

            user = self.get_user_data(
                interaction.user.id
            )

            if isinstance(
                interaction.user,
                discord.Member
            ):

                if any(
                    role.id == ULTRA_ROLE_ID
                    for role in interaction.user.roles
                ):

                    await self.hidden_error(
                        interaction,
                        "❌ You cannot open chests while you have the Ultra role."
                    )
                    return

            now = time.time()

            if now < user["weekly_next"]:

                remaining = int(
                    user["weekly_next"] - now
                )

                days = remaining // 86400
                hours = (
                    remaining % 86400
                ) // 3600

                await self.hidden_error(
                    interaction,
                    f"⏰ Weekly Mega is unavailable.\n\n"
                    f"Available again in **{days}d {hours}h**."
                )
                return

            user["weekly_next"] = now + WEEKLY_COOLDOWN
            user["mega_chests"] += 1

            self.save_data()

            await interaction.response.edit_message(
                embed=discord.Embed(
                    description=(
                        "📆 **Weekly Mega claimed!**\n\n"
                        "💎 You received **1 Mega Chest**!"
                    ),
                    color=discord.Color.blurple()
                ),
                view=MainView(
                    self,
                    interaction.user.id
                )
            )

        except Exception as error:

            print(
                f"❌ weekly error: {repr(error)}"
            )

            await self.hidden_error(
                interaction
            )

    # =====================================================
    # MAIN EMBED
    # =====================================================

    def main_embed(
        self,
        member
    ):

        user = self.get_user_data(
            member.id
        )

        total = (
            user["chests"]
            + user["mega_chests"]
            + user["ultra_chests"]
        )

        daily_available = (
            time.time() >= user["daily_next"]
        )

        weekly_available = (
            time.time() >= user["weekly_next"]
        )

        language = self.language_text(user)

        return discord.Embed(
            title=f"🎁 {member.display_name}'s Chests",
            description=(
                f"🌐 **Language:** {language}\n\n"
                f"🎁 **Chest:** {user['chests']:,}\n"
                f"💎 **Mega Chest:** {user['mega_chests']:,}\n"
                f"⚡ **Ultra Chest:** {user['ultra_chests']:,}\n\n"
                f"**Total: {total:,} Chests**\n\n"
                f"📅 **Daily Chest:** "
                f"{'Available' if daily_available else 'Unavailable'}\n"
                f"📆 **Weekly Mega:** "
                f"{'Available' if weekly_available else 'Unavailable'}"
            ),
            color=discord.Color.blurple()
        )

    # =====================================================
    # !chests
    # =====================================================

    @commands.command(name="chests")
    async def chests_command(
        self,
        ctx
    ):

        user_id = str(ctx.author.id)

        # If data could not be loaded safely,
        # NEVER create/save new data over the old file.
        if self.data_load_failed:

            await ctx.send(
                "❌ Chest data is temporarily unavailable. "
                "Your data was not changed."
            )

            try:
                await ctx.message.delete()
            except Exception:
                pass

            return

        # IMPORTANT:
        # Do NOT create user data before checking language.
        exists = user_id in self.data["users"]

        if not exists:

            await ctx.send(
                "🌐 **Select your language**\n\n"
                "Please select the language for the chest system.",
                view=LanguageView(
                    self,
                    ctx.author.id
                )
            )

            try:
                await ctx.message.delete()
            except Exception:
                pass

            return

        user = self.get_user_data(
            ctx.author.id
        )

        # Language is stored permanently.
        if user.get("language") is None:

            await ctx.send(
                "🌐 **Select your language**\n\n"
                "Please select the language for the chest system.",
                view=LanguageView(
                    self,
                    ctx.author.id
                )
            )

            try:
                await ctx.message.delete()
            except Exception:
                pass

            return

        # IMPORTANT:
        # This command only READS chest counts.
        # It does not add or remove any chests.
        message = await ctx.send(
            embed=self.main_embed(
                ctx.author
            ),
            view=MainView(
                self,
                ctx.author.id
            )
        )

        MainView.message = message

        try:
            await ctx.message.delete()
        except Exception:
            pass

    # =====================================================
    # ADMIN
    # =====================================================

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

        if ctx.invoked_subcommand is None:

            await ctx.send(
                "Available admin commands:\n"
                "`!admin chests`",
                delete_after=10
            )

    @admin.command(name="chests")
    async def admin_chests(
        self,
        ctx
    ):

        if ctx.author.id != OWNER_ID:
            return

        await ctx.send(
            embed=discord.Embed(
                title="🎁 Chest Administration",
                description=(
                    "Use the button below to add chests "
                    "to a user."
                ),
                color=discord.Color.blurple()
            ),
            view=AdminChestsView(self)
        )

        try:
            await ctx.message.delete()
        except Exception:
            pass


# =========================================================
# LANGUAGE VIEW
# =========================================================

class LanguageView(discord.ui.View):

    def __init__(
        self,
        cog,
        user_id
    ):

        super().__init__(timeout=300)

        self.cog = cog
        self.user_id = user_id

    async def on_error(
        self,
        interaction,
        error,
        item
    ):

        print(
            f"❌ LanguageView error: {repr(error)}"
        )

        await self.cog.hidden_error(
            interaction
        )

    async def interaction_check(
        self,
        interaction
    ):

        if interaction.user.id != self.user_id:

            await interaction.response.send_message(
                "❌ These chests don't belong to you.",
                ephemeral=True
            )

            return False

        return True

    @discord.ui.button(
        label="EN",
        emoji="🇬🇧",
        style=discord.ButtonStyle.primary
    )
    async def english(
        self,
        interaction,
        button
    ):

        user = self.cog.get_user_data(
            interaction.user.id
        )

        user["language"] = "en"

        self.cog.save_data()

        await interaction.response.edit_message(
            content=None,
            embed=self.cog.main_embed(
                interaction.user
            ),
            view=MainView(
                self.cog,
                interaction.user.id
            )
        )

    @discord.ui.button(
        label="RU",
        emoji="🇷🇺",
        style=discord.ButtonStyle.primary
    )
    async def russian(
        self,
        interaction,
        button
    ):

        user = self.cog.get_user_data(
            interaction.user.id
        )

        user["language"] = "ru"

        self.cog.save_data()

        await interaction.response.edit_message(
            content=None,
            embed=self.cog.main_embed(
                interaction.user
            ),
            view=MainView(
                self.cog,
                interaction.user.id
            )
        )


# =========================================================
# MAIN VIEW
# =========================================================

class MainView(discord.ui.View):

    message = None

    def __init__(
        self,
        cog,
        user_id
    ):

        super().__init__(timeout=300)

        self.cog = cog
        self.user_id = user_id

    async def on_error(
        self,
        interaction,
        error,
        item
    ):

        print(
            f"❌ MainView error: {repr(error)}"
        )

        await self.cog.hidden_error(
            interaction
        )

    async def interaction_check(
        self,
        interaction
    ):

        if interaction.user.id != self.user_id:

            await interaction.response.send_message(
                "❌ These chests don't belong to you.",
                ephemeral=True
            )

            return False

        return True

    @discord.ui.button(
        label="Chest",
        emoji="🎁",
        style=discord.ButtonStyle.primary
    )
    async def chest(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="🎁 Chest",
                description=(
                    f"You have "
                    f"**{self.cog.get_user_data(self.user_id)['chests']:,}** "
                    f"Chests."
                ),
                color=discord.Color.blurple()
            ),
            view=ChestOpenView(
                self.cog,
                self.user_id
            )
        )

    @discord.ui.button(
        label="Mega Chest",
        emoji="💎",
        style=discord.ButtonStyle.primary
    )
    async def mega(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="💎 Mega Chest",
                description=(
                    f"You have "
                    f"**{self.cog.get_user_data(self.user_id)['mega_chests']:,}** "
                    f"Mega Chests."
                ),
                color=discord.Color.blurple()
            ),
            view=MegaOpenView(
                self.cog,
                self.user_id
            )
        )

    @discord.ui.button(
        label="Ultra Chest",
        emoji="⚡",
        style=discord.ButtonStyle.primary
    )
    async def ultra(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="⚡ Ultra Chest",
                description=(
                    f"You have "
                    f"**{self.cog.get_user_data(self.user_id)['ultra_chests']:,}** "
                    f"Ultra Chests."
                ),
                color=discord.Color.blurple()
            ),
            view=UltraOpenView(
                self.cog,
                self.user_id
            )
        )

    @discord.ui.button(
        label="Daily Chest",
        emoji="📅",
        style=discord.ButtonStyle.secondary
    )
    async def daily_button(
        self,
        interaction,
        button
    ):

        await self.cog.daily(
            interaction
        )

    @discord.ui.button(
        label="Weekly Mega",
        emoji="📆",
        style=discord.ButtonStyle.secondary
    )
    async def weekly_button(
        self,
        interaction,
        button
    ):

        await self.cog.weekly(
            interaction
        )


# =========================================================
# CHEST OPEN VIEW
# =========================================================

class ChestOpenView(discord.ui.View):

    def __init__(
        self,
        cog,
        user_id=None
    ):

        super().__init__(timeout=300)

        self.cog = cog
        self.user_id = user_id

    async def on_error(
        self,
        interaction,
        error,
        item
    ):

        print(
            f"❌ ChestOpenView error: {repr(error)}"
        )

        await self.cog.hidden_error(
            interaction
        )

    async def interaction_check(
        self,
        interaction
    ):

        if (
            self.user_id is not None
            and interaction.user.id != self.user_id
        ):

            await interaction.response.send_message(
                "❌ These chests don't belong to you.",
                ephemeral=True
            )

            return False

        return True

    @discord.ui.button(
        label="Open",
        emoji="🎁",
        style=discord.ButtonStyle.success
    )
    async def open(
        self,
        interaction,
        button
    ):

        await self.cog.open_normal(
            interaction
        )

    @discord.ui.button(
        label="Open All",
        emoji="📦",
        style=discord.ButtonStyle.success
    )
    async def open_all(
        self,
        interaction,
        button
    ):

        await self.cog.open_normal_all(
            interaction
        )

    @discord.ui.button(
        label="Back",
        emoji="◀️",
        style=discord.ButtonStyle.secondary
    )
    async def back(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            embed=self.cog.main_embed(
                interaction.user
            ),
            view=MainView(
                self.cog,
                interaction.user.id
            )
        )


# =========================================================
# MEGA OPEN VIEW
# =========================================================

class MegaOpenView(discord.ui.View):

    def __init__(
        self,
        cog,
        user_id=None
    ):

        super().__init__(timeout=300)

        self.cog = cog
        self.user_id = user_id

    async def on_error(
        self,
        interaction,
        error,
        item
    ):

        print(
            f"❌ MegaOpenView error: {repr(error)}"
        )

        await self.cog.hidden_error(
            interaction
        )

    async def interaction_check(
        self,
        interaction
    ):

        if (
            self.user_id is not None
            and interaction.user.id != self.user_id
        ):

            await interaction.response.send_message(
                "❌ These chests don't belong to you.",
                ephemeral=True
            )

            return False

        return True

    @discord.ui.button(
        label="Open",
        emoji="💎",
        style=discord.ButtonStyle.success
    )
    async def open(
        self,
        interaction,
        button
    ):

        await self.cog.open_mega(
            interaction
        )

    @discord.ui.button(
        label="Open All",
        emoji="📦",
        style=discord.ButtonStyle.success
    )
    async def open_all(
        self,
        interaction,
        button
    ):

        await self.cog.open_mega_all(
            interaction
        )

    @discord.ui.button(
        label="Back",
        emoji="◀️",
        style=discord.ButtonStyle.secondary
    )
    async def back(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            embed=self.cog.main_embed(
                interaction.user
            ),
            view=MainView(
                self.cog,
                interaction.user.id
            )
        )


# =========================================================
# ULTRA OPEN VIEW
# =========================================================

class UltraOpenView(discord.ui.View):

    def __init__(
        self,
        cog,
        user_id=None
    ):

        super().__init__(timeout=300)

        self.cog = cog
        self.user_id = user_id

    async def on_error(
        self,
        interaction,
        error,
        item
    ):

        print(
            f"❌ UltraOpenView error: {repr(error)}"
        )

        await self.cog.hidden_error(
            interaction
        )

    async def interaction_check(
        self,
        interaction
    ):

        if (
            self.user_id is not None
            and interaction.user.id != self.user_id
        ):

            await interaction.response.send_message(
                "❌ These chests don't belong to you.",
                ephemeral=True
            )

            return False

        return True

    @discord.ui.button(
        label="Open",
        emoji="⚡",
        style=discord.ButtonStyle.success
    )
    async def open(
        self,
        interaction,
        button
    ):

        await self.cog.open_ultra(
            interaction
        )

    @discord.ui.button(
        label="Open All",
        emoji="📦",
        style=discord.ButtonStyle.success
    )
    async def open_all(
        self,
        interaction,
        button
    ):

        await self.cog.open_ultra_all(
            interaction
        )

    @discord.ui.button(
        label="Back",
        emoji="◀️",
        style=discord.ButtonStyle.secondary
    )
    async def back(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            embed=self.cog.main_embed(
                interaction.user
            ),
            view=MainView(
                self.cog,
                interaction.user.id
            )
        )


# =========================================================
# ADMIN MODAL
# =========================================================

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

        try:

            if interaction.user.id != OWNER_ID:

                await interaction.response.send_message(
                    "❌ You do not have permission to use this.",
                    ephemeral=True
                )
                return

            # User
            raw_user = self.user.value.strip()

            raw_user = (
                raw_user
                .replace("<@", "")
                .replace("!", "")
                .replace(">", "")
            )

            try:
                user_id = int(raw_user)

            except ValueError:

                await interaction.response.send_message(
                    "❌ Invalid user ID or mention.",
                    ephemeral=True
                )
                return

            # Quantity
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

            # Chest
            chest_type = self.chest.value.strip().lower()

            aliases = {
                "chest": "chest",
                "normal": "chest",
                "сундук": "chest",
                "обычный": "chest",

                "mega": "mega",
                "мега": "mega",
                "мега-сундук": "mega",

                "ultra": "ultra",
                "ультра": "ultra",
                "ультра-сундук": "ultra"
            }

            chest_type = aliases.get(
                chest_type
            )

            if chest_type is None:

                await interaction.response.send_message(
                    "❌ Chest must be `chest`, `mega` or `ultra`.",
                    ephemeral=True
                )
                return

            success = await self.cog.add_chests(
                user_id,
                amount,
                chest_type
            )

            if not success:

                await interaction.response.send_message(
                    "❌ Failed to add chests.",
                    ephemeral=True
                )
                return

            names = {
                "chest": "Chest",
                "mega": "Mega Chest",
                "ultra": "Ultra Chest"
            }

            await interaction.response.send_message(
                f"✅ Added **{amount:,} {names[chest_type]}** "
                f"to <@{user_id}>.",
                ephemeral=True
            )

        except Exception as error:

            print(
                f"❌ AdminChestModal error: {repr(error)}"
            )

            await self.cog.hidden_error(
                interaction
            )


# =========================================================
# ADMIN VIEW
# =========================================================

class AdminChestsView(discord.ui.View):

    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    async def on_error(
        self,
        interaction,
        error,
        item
    ):

        print(
            f"❌ AdminChestsView error: {repr(error)}"
        )

        await self.cog.hidden_error(
            interaction
        )

    @discord.ui.button(
        label="Add Chests",
        emoji="🎁",
        style=discord.ButtonStyle.primary,
        custom_id="admin_chests_open_form"
    )
    async def add_chests(
        self,
        interaction,
        button
    ):

        if interaction.user.id != OWNER_ID:

            await interaction.response.send_message(
                "❌ You do not have permission to use this.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            AdminChestModal(
                self.cog
            )
        )


# =========================================================
# SETUP
# =========================================================

async def setup(bot):

    cog = Chests(bot)

    await bot.add_cog(
        cog
    )

    bot.add_view(
        AdminChestsView(cog)
    )

    print(
        "✅ Chests cog loaded!"
            )
