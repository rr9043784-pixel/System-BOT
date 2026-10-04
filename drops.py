import os
import asyncio
import urllib.request
import urllib.error

import discord
from discord.ext import commands


# =========================
# Settings
# =========================

OWNER_ID = 1176149190192152626

UB_TOKEN = os.environ["UNBELIEVABOAT_TOKEN"]
UB_GUILD_ID = "1520800006905266216"

MONEY_EMOJI = "<:MoneyR:1534220684178231397>"


# =========================
# UnbelievaBoat
# =========================

async def add_ub_money(user_id: int, amount: int):
    """
    Adds/removes money from a user's UnbelievaBoat balance.
    Positive amount = add
    Negative amount = remove
    """

    url = (
        f"https://unbelievaboat.com/api/v1/guilds/"
        f"{UB_GUILD_ID}/users/{user_id}"
    )

    data = (
        '{"cash": ' + str(amount) + '}'
    ).encode("utf-8")

    def request():
        req = urllib.request.Request(
            url,
            data=data,
            method="PATCH",
            headers={
                "Authorization": UB_TOKEN,
                "Content-Type": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                return response.status, response.read().decode("utf-8")

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            return e.code, body

        except Exception as e:
            return 0, str(e)

    return await asyncio.to_thread(request)


# =========================
# Helpers
# =========================

def format_money(amount: int) -> str:
    return f"{amount:,}"


def get_member_restriction_text(
    target_user: discord.User | None,
    target_role: discord.Role | None
):
    if target_user:
        return f"User: {target_user.mention}"

    if target_role:
        return f"Role: {target_role.mention}"

    return "Everyone"


# =========================
# Money Drop View
# =========================

class MoneyDropView(discord.ui.View):

    def __init__(
        self,
        amount: int,
        quantity: int,
        target_user: discord.User | None = None,
        target_role: discord.Role | None = None
    ):
        super().__init__(timeout=None)

        self.amount = amount
        self.max_claims = quantity

        self.target_user = target_user
        self.target_role = target_role

        self.claimed_users: list[int] = []

        self.claim_lock = asyncio.Lock()

        self.claim_button = discord.ui.Button(
            label=f"🎁 Claim reward 0/{self.max_claims}",
            style=discord.ButtonStyle.primary,
            custom_id=f"money_drop_{id(self)}"
        )

        self.claim_button.callback = self.claim_reward

        self.add_item(self.claim_button)

    async def check_restriction(
        self,
        interaction: discord.Interaction
    ):
        if self.target_user:
            if interaction.user.id != self.target_user.id:
                return False

        if self.target_role:
            if not isinstance(interaction.user, discord.Member):
                return False

            if self.target_role not in interaction.user.roles:
                return False

        return True

    async def claim_reward(
        self,
        interaction: discord.Interaction
    ):
        async with self.claim_lock:

            if not await self.check_restriction(interaction):
                await interaction.response.send_message(
                    "❌ You are not allowed to claim this reward.",
                    ephemeral=True
                )
                return

            if interaction.user.id in self.claimed_users:
                await interaction.response.send_message(
                    "❌ You have already claimed this reward.",
                    ephemeral=True
                )
                return

            if len(self.claimed_users) >= self.max_claims:
                await interaction.response.send_message(
                    "❌ This drop is already full.",
                    ephemeral=True
                )
                return

            await interaction.response.defer(ephemeral=True)

            status, body = await add_ub_money(
                interaction.user.id,
                self.amount
            )

            if status not in (200, 201):
                await interaction.followup.send(
                    "❌ An error occurred while giving you the reward.",
                    ephemeral=True
                )
                return

            self.claimed_users.append(interaction.user.id)

            current = len(self.claimed_users)

            if current >= self.max_claims:
                self.claim_button.label = "🎁 Full drop"
                self.claim_button.disabled = True
            else:
                self.claim_button.label = (
                    f"🎁 Claim reward {current}/{self.max_claims}"
                )

            message = interaction.message

            if message:
                try:
                    await message.edit(view=self)
                except Exception:
                    pass

            await interaction.followup.send(
                f"✅ You received "
                f"{MONEY_EMOJI} {format_money(self.amount)}!",
                ephemeral=True
            )


# =========================
# Chest Drop View
# =========================

class ChestDropView(discord.ui.View):

    def __init__(
        self,
        chest_type: str,
        amount: int,
        quantity: int,
        target_user: discord.User | None = None,
        target_role: discord.Role | None = None
    ):
        super().__init__(timeout=None)

        self.chest_type = chest_type
        self.amount = amount
        self.max_claims = quantity

        self.target_user = target_user
        self.target_role = target_role

        self.claimed_users: list[int] = []

        self.claim_lock = asyncio.Lock()

        chest_names = {
            "chest": "🎁 Chest",
            "mega": "💎 Mega Chest",
            "ultra": "⚡ Ultra Chest"
        }

        self.chest_name = chest_names.get(
            chest_type,
            "🎁 Chest"
        )

        self.claim_button = discord.ui.Button(
            label=f"🎁 Claim reward 0/{self.max_claims}",
            style=discord.ButtonStyle.primary,
            custom_id=f"chest_drop_{id(self)}"
        )

        self.claim_button.callback = self.claim_reward

        self.add_item(self.claim_button)

    async def check_restriction(
        self,
        interaction: discord.Interaction
    ):
        if self.target_user:
            if interaction.user.id != self.target_user.id:
                return False

        if self.target_role:
            if not isinstance(interaction.user, discord.Member):
                return False

            if self.target_role not in interaction.user.roles:
                return False

        return True

    async def claim_reward(
        self,
        interaction: discord.Interaction
    ):
        async with self.claim_lock:

            if not await self.check_restriction(interaction):
                await interaction.response.send_message(
                    "❌ You are not allowed to claim this reward.",
                    ephemeral=True
                )
                return

            if interaction.user.id in self.claimed_users:
                await interaction.response.send_message(
                    "❌ You have already claimed this reward.",
                    ephemeral=True
                )
                return

            if len(self.claimed_users) >= self.max_claims:
                await interaction.response.send_message(
                    "❌ This drop is already full.",
                    ephemeral=True
                )
                return

            chests = self.view_bot.get_cog("Chests")

            if chests is None:
                await interaction.response.send_message(
                    "❌ The chest system is currently unavailable.",
                    ephemeral=True
                )
                return

            await interaction.response.defer(ephemeral=True)

            try:
                await chests.add_chests(
                    interaction.user.id,
                    self.amount,
                    chest_type=self.chest_type
                )

            except Exception:
                await interaction.followup.send(
                    "❌ An error occurred while giving you the chest.",
                    ephemeral=True
                )
                return

            self.claimed_users.append(interaction.user.id)

            current = len(self.claimed_users)

            if current >= self.max_claims:
                self.claim_button.label = "🎁 Full drop"
                self.claim_button.disabled = True
            else:
                self.claim_button.label = (
                    f"🎁 Claim reward {current}/{self.max_claims}"
                )

            if interaction.message:
                try:
                    await interaction.message.edit(view=self)
                except Exception:
                    pass

            await interaction.followup.send(
                f"✅ You received "
                f"**{self.amount} × {self.chest_name}**!",
                ephemeral=True
            )

    @property
    def view_bot(self):
        return self.bot

    def set_bot(self, bot):
        self.bot = bot


# =========================
# Drops Cog
# =========================

class Drops(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def owner_only(self, ctx):
        if ctx.author.id != OWNER_ID:
            return False

        return True

    # =========================
    # Money Drop
    # =========================

    @commands.command()
    async def money(
        self,
        ctx,
        subcommand=None,
        amount: int = None,
        target_user: discord.User = None,
        quantity: int = 1,
        target_role: discord.Role = None
    ):
        """
        !money economy <amount> [user] <quantity> [role]
        """

        if ctx.author.id != OWNER_ID:
            return

        if subcommand != "economy":
            return

        if amount is None:
            return

        if amount <= 0:
            return

        if quantity <= 0:
            return

        if quantity > 1000:
            quantity = 1000

        view = MoneyDropView(
            amount=amount,
            quantity=quantity,
            target_user=target_user,
            target_role=target_role
        )

        embed = discord.Embed(
            title="Money drop",
            description=(
                f"💰 Reward: "
                f"{MONEY_EMOJI} **{format_money(amount)}**\n\n"
                f"🎁 Winners: **{quantity}**\n"
                f"🔒 {get_member_restriction_text(target_user, target_role)}"
            ),
            color=discord.Color.green()
        )

        await ctx.send(
            content="**Money drop**",
            embed=embed,
            view=view
        )

        try:
            await ctx.message.delete()
        except Exception:
            pass

    # =========================
    # Chest Drop
    # =========================

    @commands.command()
    async def drop(
        self,
        ctx,
        chest_type: str = None,
        amount: int = 1,
        quantity: int = 1,
        target_role: discord.Role = None,
        target_user: discord.User = None
    ):
        """
        !drop <chest_type> <amount> <quantity> [role] [user]

        chest_type:
        chest
        mega
        ultra
        """

        if ctx.author.id != OWNER_ID:
            return

        if chest_type is None:
            return

        chest_type = chest_type.lower()

        if chest_type not in ("chest", "mega", "ultra"):
            return

        if amount <= 0:
            return

        if quantity <= 0:
            return

        if quantity > 1000:
            quantity = 1000

        chests = self.bot.get_cog("Chests")

        if chests is None:
            await ctx.send(
                "❌ The chest system is currently unavailable.",
                delete_after=5
            )
            return

        view = ChestDropView(
            chest_type=chest_type,
            amount=amount,
            quantity=quantity,
            target_user=target_user,
            target_role=target_role
        )

        view.set_bot(self.bot)

        chest_names = {
            "chest": "🎁 Chest",
            "mega": "💎 Mega Chest",
            "ultra": "⚡ Ultra Chest"
        }

        chest_name = chest_names[chest_type]

        embed = discord.Embed(
            title="Chest drop",
            description=(
                f"🎁 Reward: **{amount} × {chest_name}**\n\n"
                f"👥 Winners: **{quantity}**\n"
                f"🔒 {get_member_restriction_text(target_user, target_role)}"
            ),
            color=discord.Color.dark_grey()
        )

        await ctx.send(
            content="**Chest drop**",
            embed=embed,
            view=view
        )

        try:
            await ctx.message.delete()
        except Exception:
            pass


# =========================
# Setup
# =========================

async def setup(bot):
    await bot.add_cog(
        Drops(bot)
    )

    print("✅ Drops loaded!") 
