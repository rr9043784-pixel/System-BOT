import os
import asyncio
import json
import urllib.request
import urllib.error

import discord
from discord.ext import commands


# =========================
# SETTINGS
# =========================

OWNER_ID = 1176149190192152626
UB_GUILD_ID = "1520800006905266216"

UB_TOKEN = os.environ["UNBELIEVABOAT_TOKEN"]

MONEY_EMOJI = "<:MoneyR:1534220684178231397>"


# =========================
# UNBELIEVABOAT
# =========================

async def add_ub_money(user_id, amount):

    url = (
        f"https://unbelievaboat.com/api/"
        f"v1/guilds/{UB_GUILD_ID}/users/{user_id}"
    )

    data = json.dumps({
        "cash": amount,
        "reason": "Money Drop"
    }).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        method="PATCH"
    )

    request.add_header(
        "Authorization",
        UB_TOKEN
    )

    request.add_header(
        "Content-Type",
        "application/json"
    )

    try:

        await asyncio.to_thread(
            urllib.request.urlopen,
            request
        )

        return True

    except Exception:

        return False


# =========================
# MONEY DROP VIEW
# =========================

class MoneyDropView(discord.ui.View):

    def __init__(
        self,
        amount,
        quantity,
        allowed_user_id=None,
        allowed_role_id=None
    ):

        super().__init__(timeout=None)

        self.amount = amount
        self.quantity = quantity

        self.allowed_user_id = allowed_user_id
        self.allowed_role_id = allowed_role_id

        self.claimed_users = set()
        self.claimed_names = []

        self.lock = asyncio.Lock()

        self.button = discord.ui.Button(
            label=f"🎁 Claim reward 0/{quantity}",
            style=discord.ButtonStyle.green
        )

        self.button.callback = self.claim

        self.add_item(self.button)

    def get_embed(self):

        claimed = len(self.claimed_users)

        description = (
            "Click the button below to receive the reward.\n\n"
            f"**Reward:** {MONEY_EMOJI} {self.amount:,}\n"
            f"**Claims:** {claimed}/{self.quantity}\n"
            f"**Full drop:** "
            f"{'✅' if claimed >= self.quantity else '❌'}"
        )

        if self.allowed_user_id:

            description += (
                f"\n\n**Only:** "
                f"<@{self.allowed_user_id}> can claim"
            )

        elif self.allowed_role_id:

            description += (
                f"\n\n**Only:** "
                f"<@&{self.allowed_role_id}> can claim"
            )

        if self.claimed_names:

            description += "\n\n**Claimed by:**"

            for name in self.claimed_names[:10]:
                description += f"\n• {name}"

        return discord.Embed(
            title="💰 Money Drop",
            description=description,
            color=discord.Color.green()
        )

    async def claim(
        self,
        interaction: discord.Interaction
    ):

        async with self.lock:

            if len(self.claimed_users) >= self.quantity:

                await interaction.response.send_message(
                    "This drop is already full.",
                    ephemeral=True
                )

                return

            user_id = interaction.user.id

            if user_id in self.claimed_users:

                await interaction.response.send_message(
                    "You already claimed this reward.",
                    ephemeral=True
                )

                return

            if (
                self.allowed_user_id is not None
                and user_id != self.allowed_user_id
            ):

                await interaction.response.send_message(
                    "You cannot claim this reward.",
                    ephemeral=True
                )

                return

            if self.allowed_role_id is not None:

                if not isinstance(
                    interaction.user,
                    discord.Member
                ):

                    await interaction.response.send_message(
                        "You cannot claim this reward.",
                        ephemeral=True
                    )

                    return

                if self.allowed_role_id not in [
                    role.id
                    for role in interaction.user.roles
                ]:

                    await interaction.response.send_message(
                        "You cannot claim this reward.",
                        ephemeral=True
                    )

                    return

            success = await add_ub_money(
                user_id,
                self.amount
            )

            if not success:

                await interaction.response.send_message(
                    "❌ **Error** The reward could not be given.",
                    ephemeral=True
                )

                return

            self.claimed_users.add(user_id)

            self.claimed_names.append(
                interaction.user.mention
            )

            claimed = len(
                self.claimed_users
            )

            self.button.label = (
                f"🎁 Claim reward "
                f"{claimed}/{self.quantity}"
            )

            if claimed >= self.quantity:
                self.button.disabled = True

            await interaction.response.edit_message(
                embed=self.get_embed(),
                view=self
            )

            await interaction.followup.send(
                f"✅ You received "
                f"**{MONEY_EMOJI} {self.amount:,}**.",
                ephemeral=True
            )


# =========================
# CHEST DROP VIEW
# =========================

class ChestDropView(discord.ui.View):

    def __init__(
        self,
        bot,
        chest_type,
        amount,
        quantity,
        allowed_user_id=None,
        allowed_role_id=None
    ):

        super().__init__(timeout=None)

        self.bot = bot
        self.chest_type = chest_type

        self.amount = amount
        self.quantity = quantity

        self.allowed_user_id = allowed_user_id
        self.allowed_role_id = allowed_role_id

        self.claimed_users = set()
        self.claimed_names = []

        self.lock = asyncio.Lock()

        self.button = discord.ui.Button(
            label=f"🎁 Claim reward 0/{quantity}",
            style=discord.ButtonStyle.green
        )

        self.button.callback = self.claim

        self.add_item(self.button)

    def chest_name(self):

        return {
            "normal": "Normal Chest",
            "mega": "Mega Chest",
            "ultra": "Ultra Chest"
        }[self.chest_type]

    def chest_emoji(self):

        return {
            "normal": "🎁",
            "mega": "💎",
            "ultra": "⚡"
        }[self.chest_type]

    def chest_key(self):

        return {
            "normal": "chest",
            "mega": "mega",
            "ultra": "ultra"
        }[self.chest_type]

    def get_embed(self):

        claimed = len(
            self.claimed_users
        )

        description = (
            "Click the button below to receive the reward.\n\n"
            f"**Reward:** "
            f"{self.chest_emoji()} "
            f"{self.amount} × "
            f"{self.chest_name()}\n"
            f"**Claims:** "
            f"{claimed}/{self.quantity}\n"
            f"**Full drop:** "
            f"{'✅' if claimed >= self.quantity else '❌'}"
        )

        if self.allowed_user_id:

            description += (
                f"\n\n**Only:** "
                f"<@{self.allowed_user_id}> can claim"
            )

        elif self.allowed_role_id:

            description += (
                f"\n\n**Only:** "
                f"<@&{self.allowed_role_id}> can claim"
            )

        if self.claimed_names:

            description += "\n\n**Claimed by:**"

            for name in self.claimed_names[:10]:
                description += f"\n• {name}"

        return discord.Embed(
            title="🎁 Chest Drop",
            description=description,
            color=discord.Color.green()
        )

    async def claim(
        self,
        interaction: discord.Interaction
    ):

        async with self.lock:

            if len(self.claimed_users) >= self.quantity:

                await interaction.response.send_message(
                    "This drop is already full.",
                    ephemeral=True
                )

                return

            user_id = interaction.user.id

            if user_id in self.claimed_users:

                await interaction.response.send_message(
                    "You already claimed this reward.",
                    ephemeral=True
                )

                return

            if (
                self.allowed_user_id is not None
                and user_id != self.allowed_user_id
            ):

                await interaction.response.send_message(
                    "You cannot claim this reward.",
                    ephemeral=True
                )

                return

            if self.allowed_role_id is not None:

                if not isinstance(
                    interaction.user,
                    discord.Member
                ):

                    await interaction.response.send_message(
                        "You cannot claim this reward.",
                        ephemeral=True
                    )

                    return

                if self.allowed_role_id not in [
                    role.id
                    for role in interaction.user.roles
                ]:

                    await interaction.response.send_message(
                        "You cannot claim this reward.",
                        ephemeral=True
                    )

                    return

            chests = self.bot.get_cog(
                "Chests"
            )

            if chests is None:

                await interaction.response.send_message(
                    "❌ **Error** "
                    "The chest system is unavailable.",
                    ephemeral=True
                )

                return

            success = await chests.add_chests(
                user_id,
                self.amount,
                self.chest_key()
            )

            if not success:

                await interaction.response.send_message(
                    "❌ **Error** "
                    "The reward could not be given.",
                    ephemeral=True
                )

                return

            self.claimed_users.add(
                user_id
            )

            self.claimed_names.append(
                interaction.user.mention
            )

            claimed = len(
                self.claimed_users
            )

            self.button.label = (
                f"🎁 Claim reward "
                f"{claimed}/{self.quantity}"
            )

            if claimed >= self.quantity:
                self.button.disabled = True

            await interaction.response.edit_message(
                embed=self.get_embed(),
                view=self
            )

            await interaction.followup.send(
                f"✅ You received "
                f"**{self.amount} × "
                f"{self.chest_name()} "
                f"{self.chest_emoji()}**.",
                ephemeral=True
            )


# =========================
# DROPS COG
# =========================

class Drops(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    # =========================
    # MONEY
    # =========================

    @commands.command(name="money")
    async def money(
        self,
        ctx,
        subcommand=None,
        amount=None,
        quantity=None,
        target_user: discord.User = None,
        target_role: discord.Role = None
    ):

        if ctx.author.id != OWNER_ID:
            return

        if subcommand != "economy":
            return

        try:

            amount = int(amount)
            quantity = int(quantity)

        except (
            TypeError,
            ValueError
        ):

            return

        if amount <= 0 or quantity <= 0:
            return

        if target_user and target_role:
            return

        view = MoneyDropView(
            amount=amount,
            quantity=quantity,
            allowed_user_id=(
                target_user.id
                if target_user
                else None
            ),
            allowed_role_id=(
                target_role.id
                if target_role
                else None
            )
        )

        await ctx.send(
            embed=view.get_embed(),
            view=view
        )

        try:
            await ctx.message.delete()

        except Exception:
            pass


    # =========================
    # CHEST DROP
    # =========================

    @commands.command(name="drop")
    async def drop(
        self,
        ctx,
        chest_type=None,
        amount=None,
        quantity=None
    ):

        if ctx.author.id != OWNER_ID:
            return

        if chest_type is None:
            return

        chest_type = chest_type.lower()

        aliases = {

            "normal": "normal",
            "chest": "normal",
            "chests": "normal",

            "mega": "mega",
            "mega-chest": "mega",
            "mega_chest": "mega",

            "ultra": "ultra",
            "ultra-chest": "ultra",
            "ultra_chest": "ultra"
        }

        if chest_type not in aliases:
            return

        chest_type = aliases[chest_type]

        try:

            amount = int(amount)
            quantity = int(quantity)

        except (
            TypeError,
            ValueError
        ):

            return

        if amount <= 0 or quantity <= 0:
            return

        target_user = None
        target_role = None

        # =========================
        # USER MENTION
        # =========================

        if ctx.message.mentions:

            target_user = ctx.message.mentions[0]

        # =========================
        # ROLE MENTION
        # =========================

        elif ctx.message.role_mentions:

            target_role = ctx.message.role_mentions[0]

        # =========================
        # CREATE DROP
        # =========================

        view = ChestDropView(
            bot=self.bot,
            chest_type=chest_type,
            amount=amount,
            quantity=quantity,
            allowed_user_id=(
                target_user.id
                if target_user
                else None
            ),
            allowed_role_id=(
                target_role.id
                if target_role
                else None
            )
        )

        await ctx.send(
            embed=view.get_embed(),
            view=view
        )

        try:

            await ctx.message.delete()

        except Exception:

            pass


    # =========================
    # REMOVE CHESTS
    # =========================

    @commands.command(name="remove")
    async def remove(
        self,
        ctx,
        chest_type=None,
        amount=None,
        target_user: discord.User = None
    ):

        if ctx.author.id != OWNER_ID:
            return

        if not chest_type or not amount or not target_user:
            return

        chest_type = chest_type.lower()

        aliases = {

            "normal": "chests",
            "chest": "chests",
            "chests": "chests",

            "mega": "mega_chests",
            "mega-chest": "mega_chests",
            "mega_chest": "mega_chests",

            "ultra": "ultra_chests",
            "ultra-chest": "ultra_chests",
            "ultra_chest": "ultra_chests"
        }

        if chest_type not in aliases:
            return

        chest_key = aliases[chest_type]

        try:

            amount = int(amount)

        except (
            TypeError,
            ValueError
        ):

            return

        if amount <= 0:
            return

        chests = self.bot.get_cog(
            "Chests"
        )

        if chests is None:
            return

        user_data = chests.get_user_data(
            target_user.id
        )

        current_amount = int(
            user_data.get(chest_key, 0)
        )

        if current_amount < amount:

            await ctx.send(
                f"❌ {target_user.mention} does not have "
                f"enough chests."
            )

            return

        user_data[chest_key] = (
            current_amount - amount
        )

        await chests.save_data()

        await ctx.send(
            f"✅ Removed **{amount}** chest(s) "
            f"from {target_user.mention}."
        )

        try:

            await ctx.message.delete()

        except Exception:

            pass


# =========================
# SETUP
# =========================

async def setup(bot):

    await bot.add_cog(
        Drops(bot)
    )

    print(
        "✅ Drops cog loaded!"
            )
