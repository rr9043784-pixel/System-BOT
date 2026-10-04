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
        "reason": "Money Drop",
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
        except (urllib.error.HTTPError, urllib.error.URLError):
            return False
        except Exception:
            return False

    return await asyncio.to_thread(request)


# =========================
# MONEY DROP VIEW
# =========================

class MoneyDropView(discord.ui.View):

    def __init__(
        self,
        amount: int,
        quantity: int,
        allowed_user_id: int | None = None,
        allowed_role_id: int | None = None,
    ):
        super().__init__(timeout=None)

        self.amount = amount
        self.quantity = quantity
        self.allowed_user_id = allowed_user_id
        self.allowed_role_id = allowed_role_id

        self.claimed_users = set()
        self.claimed_names = []

        self.lock = asyncio.Lock()

        self.claim_button = discord.ui.Button(
            label=f"🎁 Claim reward 0/{quantity}",
            style=discord.ButtonStyle.green,
            custom_id="money_drop_claim",
        )

        self.claim_button.callback = self.claim_reward
        self.add_item(self.claim_button)

    def create_embed(self):
        claimed = len(self.claimed_users)

        description = (
            f"{MONEY_EMOJI} **Reward:** {self.amount:,}\n\n"
            f"**👥 Claims:** {claimed}/{self.quantity}"
        )

        if self.allowed_user_id is not None:
            description += (
                f"\n\n**Only:** <@{self.allowed_user_id}> can claim"
            )

        elif self.allowed_role_id is not None:
            description += (
                f"\n\n**Only:** <@&{self.allowed_role_id}> can claim"
            )

        if self.claimed_names:
            description += "\n\n**👥 Claimed by:**"

            for name in self.claimed_names[:10]:
                description += f"\n• {name}"

        return discord.Embed(
            title="💰 Money drop",
            description=description,
            color=discord.Color.green(),
        )

    async def claim_reward(self, interaction: discord.Interaction):

        async with self.lock:

            if len(self.claimed_users) >= self.quantity:
                await interaction.response.send_message(
                    "This money drop is already full.",
                    ephemeral=True,
                )
                return

            user_id = interaction.user.id

            if user_id in self.claimed_users:
                await interaction.response.send_message(
                    "You already claimed this reward.",
                    ephemeral=True,
                )
                return

            if (
                self.allowed_user_id is not None
                and user_id != self.allowed_user_id
            ):
                await interaction.response.send_message(
                    "You cannot claim this money drop.",
                    ephemeral=True,
                )
                return

            if self.allowed_role_id is not None:

                if not isinstance(interaction.user, discord.Member):
                    await interaction.response.send_message(
                        "You cannot claim this money drop.",
                        ephemeral=True,
                    )
                    return

                if self.allowed_role_id not in [
                    role.id for role in interaction.user.roles
                ]:
                    await interaction.response.send_message(
                        "You cannot claim this money drop.",
                        ephemeral=True,
                    )
                    return

            success = await add_ub_money(
                user_id,
                self.amount,
            )

            if not success:
                await interaction.response.send_message(
                    "❌ **Error** The reward could not be given.",
                    ephemeral=True,
                )
                return

            self.claimed_users.add(user_id)
            self.claimed_names.append(interaction.user.mention)

            claimed = len(self.claimed_users)

            self.claim_button.label = (
                f"🎁 Claim reward {claimed}/{self.quantity}"
            )

            if claimed >= self.quantity:
                self.claim_button.disabled = True

            try:
                await interaction.message.edit(
                    content="**Money drop**",
                    embed=self.create_embed(),
                    view=self,
                )
            except Exception:
                pass

            await interaction.response.send_message(
                f"🎉 **You received "
                f"{MONEY_EMOJI} {self.amount:,}!**",
                ephemeral=True,
            )


# =========================
# CHEST DROP VIEW
# =========================

class ChestDropView(discord.ui.View):

    def __init__(
        self,
        bot,
        chest_type: str,
        amount: int,
        quantity: int,
        allowed_user_id: int | None = None,
        allowed_role_id: int | None = None,
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

        self.claim_button = discord.ui.Button(
            label=f"🎁 Claim reward 0/{quantity}",
            style=discord.ButtonStyle.green,
            custom_id=f"chest_drop_{chest_type}",
        )

        self.claim_button.callback = self.claim_reward
        self.add_item(self.claim_button)

    def chest_name(self):

        names = {
            "chest": "Normal Chest",
            "mega": "Mega Chest",
            "ultra": "Ultra Chest",
        }

        return names[self.chest_type]

    def chest_emoji(self):

        emojis = {
            "chest": "🎁",
            "mega": "💎",
            "ultra": "⚡",
        }

        return emojis[self.chest_type]

    def create_embed(self):

        claimed = len(self.claimed_users)

        description = (
            f"{self.chest_emoji()} **Reward:** "
            f"{self.amount} × {self.chest_name()}\n\n"
            f"**👥 Claims:** {claimed}/{self.quantity}"
        )

        if self.allowed_user_id is not None:
            description += (
                f"\n\n**Only:** <@{self.allowed_user_id}> can claim"
            )

        elif self.allowed_role_id is not None:
            description += (
                f"\n\n**Only:** <@&{self.allowed_role_id}> can claim"
            )

        if self.claimed_names:
            description += "\n\n**👥 Claimed by:**"

            for name in self.claimed_names[:10]:
                description += f"\n• {name}"

        return discord.Embed(
            title="🎁 Chest drop",
            description=description,
            color=discord.Color.green(),
        )

    async def claim_reward(self, interaction: discord.Interaction):

        async with self.lock:

            if len(self.claimed_users) >= self.quantity:
                await interaction.response.send_message(
                    "This chest drop is already full.",
                    ephemeral=True,
                )
                return

            user_id = interaction.user.id

            if user_id in self.claimed_users:
                await interaction.response.send_message(
                    "You already claimed this reward.",
                    ephemeral=True,
                )
                return

            if (
                self.allowed_user_id is not None
                and user_id != self.allowed_user_id
            ):
                await interaction.response.send_message(
                    "You cannot claim this chest drop.",
                    ephemeral=True,
                )
                return

            if self.allowed_role_id is not None:

                if not isinstance(interaction.user, discord.Member):
                    await interaction.response.send_message(
                        "You cannot claim this chest drop.",
                        ephemeral=True,
                    )
                    return

                if self.allowed_role_id not in [
                    role.id for role in interaction.user.roles
                ]:
                    await interaction.response.send_message(
                        "You cannot claim this chest drop.",
                        ephemeral=True,
                    )
                    return

            chests = self.bot.get_cog("Chests")

            if chests is None:
                await interaction.response.send_message(
                    "❌ **Error** The chest system is unavailable.",
                    ephemeral=True,
                )
                return

            try:
                await chests.add_chests(
                    user_id,
                    self.amount,
                    chest_type=self.chest_type,
                )
            except Exception:
                await interaction.response.send_message(
                    "❌ **Error** The reward could not be given.",
                    ephemeral=True,
                )
                return

            self.claimed_users.add(user_id)
            self.claimed_names.append(interaction.user.mention)

            claimed = len(self.claimed_users)

            self.claim_button.label = (
                f"🎁 Claim reward {claimed}/{self.quantity}"
            )

            if claimed >= self.quantity:
                self.claim_button.disabled = True

            try:
                await interaction.message.edit(
                    content="**Chest drop**",
                    embed=self.create_embed(),
                    view=self,
                )
            except Exception:
                pass

            await interaction.response.send_message(
                f"🎉 **You received "
                f"{self.amount} × {self.chest_name()}!**",
                ephemeral=True,
            )


# =========================
# DROPS COG
# =========================

class Drops(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # =========================
    # !MONEY ECONOMY
    # =========================

    @commands.command(name="money")
    async def money(
        self,
        ctx,
        subcommand=None,
        amount: int | None = None,
        quantity: int = 1,
        target_user: discord.User | None = None,
        target_role: discord.Role | None = None,
    ):

        if ctx.author.id != OWNER_ID:
            return

        if subcommand != "economy":
            return

        if amount is None or amount <= 0:
            return

        if quantity <= 0 or quantity > 1000:
            return

        if target_user is not None and target_role is not None:
            return

        view = MoneyDropView(
            amount=amount,
            quantity=quantity,
            allowed_user_id=(
                target_user.id
                if target_user is not None
                else None
            ),
            allowed_role_id=(
                target_role.id
                if target_role is not None
                else None
            ),
        )

        message = await ctx.send(
            content="**Money drop**",
            embed=view.create_embed(),
            view=view,
        )

        try:
            await ctx.message.delete()
        except Exception:
            pass

        view.message_id = message.id

    # =========================
    # !DROP
    # =========================

    @commands.command(name="drop")
    async def drop(
        self,
        ctx,
        chest_type: str,
        amount: int,
        quantity: int,
        target_role: discord.Role | None = None,
        target_user: discord.User | None = None,
    ):

        if ctx.author.id != OWNER_ID:
            return

        chest_type = chest_type.lower()

        aliases = {
            "normal": "chest",
            "chest": "chest",
            "chests": "chest",

            "mega": "mega",
            "megachest": "mega",
            "mega_chest": "mega",

            "ultra": "ultra",
            "ultrachest": "ultra",
            "ultra_chest": "ultra",
        }

        if chest_type not in aliases:
            await ctx.send(
                "❌ **Error** Use `normal`, `mega` or `ultra`.",
                delete_after=5,
            )
            return

        chest_type = aliases[chest_type]

        if amount <= 0:
            return

        if quantity <= 0 or quantity > 1000:
            return

        if target_user is not None and target_role is not None:
            return

        view = ChestDropView(
            bot=self.bot,
            chest_type=chest_type,
            amount=amount,
            quantity=quantity,
            allowed_user_id=(
                target_user.id
                if target_user is not None
                else None
            ),
            allowed_role_id=(
                target_role.id
                if target_role is not None
                else None
            ),
        )

        message = await ctx.send(
            content="**Chest drop**",
            embed=view.create_embed(),
            view=view,
        )

        try:
            await ctx.message.delete()
        except Exception:
            pass

        view.message_id = message.id


# =========================
# SETUP
# =========================

async def setup(bot):

    await bot.add_cog(
        Drops(bot)
    )

    print("✅ Drops cog loaded!")
