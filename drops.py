import os
import json
import asyncio
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

async def add_ub_money(user_id: int, amount: int) -> bool:
    url = (
        f"https://unbelievaboat.com/api/v1/guilds/"
        f"{UB_GUILD_ID}/users/{user_id}"
    )

    data = json.dumps({
        "cash": amount,
        "reason": "Money Drop"
    }).encode("utf-8")

    headers = {
        "Authorization": UB_TOKEN,
        "Content-Type": "application/json",
    }

    def request():
        req = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method="PATCH",
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                return 200 <= response.status < 300
        except Exception:
            return False

    return await asyncio.to_thread(request)


# =========================
# MONEY DROP
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

    def get_text(self):
        claimed = len(self.claimed_users)

        text = (
            "Click the button below to receive the reward.\n\n"
            f"**Reward:** {MONEY_EMOJI} {self.amount:,}\n"
            f"**Claims:** {claimed}/{self.quantity}\n"
            f"**Full drop:** "
            f"{'✅' if claimed >= self.quantity else '❌'}"
        )

        if self.allowed_user_id:
            text += (
                f"\n\n**Only:** <@{self.allowed_user_id}> can claim"
            )

        elif self.allowed_role_id:
            text += (
                f"\n\n**Only:** <@&{self.allowed_role_id}> can claim"
            )

        if self.claimed_names:
            text += "\n\n**Claimed by:**"

            for name in self.claimed_names[:10]:
                text += f"\n• {name}"

        return text

    async def claim(self, interaction: discord.Interaction):

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

                if not isinstance(interaction.user, discord.Member):
                    await interaction.response.send_message(
                        "You cannot claim this reward.",
                        ephemeral=True
                    )
                    return

                if self.allowed_role_id not in [
                    role.id for role in interaction.user.roles
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
            self.claimed_names.append(interaction.user.mention)

            claimed = len(self.claimed_users)

            self.button.label = (
                f"🎁 Claim reward {claimed}/{self.quantity}"
            )

            if claimed >= self.quantity:
                self.button.disabled = True

            await interaction.response.edit_message(
                content=self.get_text(),
                view=self
            )


# =========================
# CHEST DROP
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

    def get_text(self):
        claimed = len(self.claimed_users)

        text = (
            "Click the button below to receive the reward.\n\n"
            f"**Reward:** {self.chest_emoji()} "
            f"{self.amount} × {self.chest_name()}\n"
            f"**Claims:** {claimed}/{self.quantity}\n"
            f"**Full drop:** "
            f"{'✅' if claimed >= self.quantity else '❌'}"
        )

        if self.allowed_user_id:
            text += (
                f"\n\n**Only:** <@{self.allowed_user_id}> can claim"
            )

        elif self.allowed_role_id:
            text += (
                f"\n\n**Only:** <@&{self.allowed_role_id}> can claim"
            )

        if self.claimed_names:
            text += "\n\n**Claimed by:**"

            for name in self.claimed_names[:10]:
                text += f"\n• {name}"

        return text

    async def claim(self, interaction: discord.Interaction):

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

                if not isinstance(interaction.user, discord.Member):
                    await interaction.response.send_message(
                        "You cannot claim this reward.",
                        ephemeral=True
                    )
                    return

                if self.allowed_role_id not in [
                    role.id for role in interaction.user.roles
                ]:
                    await interaction.response.send_message(
                        "You cannot claim this reward.",
                        ephemeral=True
                    )
                    return

            chests = self.bot.get_cog("Chests")

            if chests is None:
                await interaction.response.send_message(
                    "❌ **Error** The chest system is unavailable.",
                    ephemeral=True
                )
                return

            try:
                chest_key = {
                    "normal": "chests",
                    "mega": "mega_chests",
                    "ultra": "ultra_chests"
                }[self.chest_type]

                await chests.add_chests(
                    user_id,
                    self.amount,
                    chest_key
                )

            except Exception:
                await interaction.response.send_message(
                    "❌ **Error** The reward could not be given.",
                    ephemeral=True
                )
                return

            self.claimed_users.add(user_id)
            self.claimed_names.append(interaction.user.mention)

            claimed = len(self.claimed_users)

            self.button.label = (
                f"🎁 Claim reward {claimed}/{self.quantity}"
            )

            if claimed >= self.quantity:
                self.button.disabled = True

            await interaction.response.edit_message(
                content=self.get_text(),
                view=self
            )


# =========================
# DROPS COG
# =========================

class Drops(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # =========================
    # !money economy
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
        except (TypeError, ValueError):
            return

        if amount <= 0 or quantity <= 0:
            return

        if target_user and target_role:
            return

        view = MoneyDropView(
            amount=amount,
            quantity=quantity,
            allowed_user_id=(
                target_user.id if target_user else None
            ),
            allowed_role_id=(
                target_role.id if target_role else None
            )
        )

        await ctx.send(
            content=view.get_text(),
            view=view
        )

        try:
            await ctx.message.delete()
        except Exception:
            pass

    # =========================
    # !drop
    # =========================

    @commands.command(name="drop")
    async def drop(
        self,
        ctx,
        chest_type=None,
        amount=None,
        quantity=None,
        target_role: discord.Role = None,
        target_user: discord.User = None
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
        except (TypeError, ValueError):
            return

        if amount <= 0 or quantity <= 0:
            return

        if target_user and target_role:
            return

        view = ChestDropView(
            bot=self.bot,
            chest_type=chest_type,
            amount=amount,
            quantity=quantity,
            allowed_user_id=(
                target_user.id if target_user else None
            ),
            allowed_role_id=(
                target_role.id if target_role else None
            )
        )

        await ctx.send(
            content=view.get_text(),
            view=view
        )

        try:
            await ctx.message.delete()
        except Exception:
            pass


# =========================
# SETUP
# =========================

async def setup(bot):
    await bot.add_cog(Drops(bot))
    print("✅ Drops cog loaded!")
