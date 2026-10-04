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
        "Content-Type": "application/json"
    }

    def request():
        req = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method="PATCH"
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                return 200 <= response.status < 300
        except Exception:
            return False

    return await asyncio.to_thread(request)


# =========================
# MONEY DROP VIEW
# =========================

class MoneyDropView(discord.ui.View):

    def __init__(
        self,
        bot,
        amount,
        quantity,
        target_user=None,
        target_role=None
    ):
        super().__init__(timeout=None)

        self.bot = bot
        self.amount = amount
        self.quantity = quantity
        self.target_user = target_user
        self.target_role = target_role

        self.claimed = 0
        self.claimed_users = []

        self.lock = asyncio.Lock()

        self.claim_button = discord.ui.Button(
            label=f"🎁 Claim reward 0/{quantity}",
            style=discord.ButtonStyle.success
        )

        self.claim_button.callback = self.claim
        self.add_item(self.claim_button)

    def get_embed(self):

        description = (
            "Click the button below to receive the reward.\n\n"
            f"**Reward:** {MONEY_EMOJI} {self.amount:,}\n"
            f"**Claims:** {self.claimed}/{self.quantity}\n"
            f"**Full drop:** "
            f"{'✅' if self.claimed >= self.quantity else '❌'}"
        )

        if self.target_user:
            description += (
                f"\n**Only:** {self.target_user.mention}"
            )

        if self.target_role:
            description += (
                f"\n**Only:** {self.target_role.mention}"
            )

        if self.claimed_users:
            description += (
                "\n**Claimed by:** "
                + ", ".join(
                    user.mention
                    for user in self.claimed_users[:10]
                )
            )

        return discord.Embed(
            title="💰 Money Drop",
            description=description,
            color=discord.Color.green()
        )

    async def claim(self, interaction: discord.Interaction):

        async with self.lock:

            user = interaction.user

            if self.target_user:
                if user.id != self.target_user.id:
                    await interaction.response.send_message(
                        "❌ You cannot claim this drop.",
                        ephemeral=True
                    )
                    return

            if self.target_role:
                if self.target_role not in user.roles:
                    await interaction.response.send_message(
                        "❌ You cannot claim this drop.",
                        ephemeral=True
                    )
                    return

            if user.id in [u.id for u in self.claimed_users]:
                await interaction.response.send_message(
                    "❌ You have already claimed this drop.",
                    ephemeral=True
                )
                return

            if self.claimed >= self.quantity:
                await interaction.response.send_message(
                    "❌ This drop is already full.",
                    ephemeral=True
                )
                return

            success = await add_ub_money(
                user.id,
                self.amount
            )

            if not success:
                await interaction.response.send_message(
                    "❌ Failed to give the reward.",
                    ephemeral=True
                )
                return

            self.claimed += 1
            self.claimed_users.append(user)

            self.claim_button.label = (
                f"🎁 Claim reward "
                f"{self.claimed}/{self.quantity}"
            )

            if self.claimed >= self.quantity:
                self.claim_button.disabled = True

            await interaction.message.edit(
                embed=self.get_embed(),
                view=self
            )

            await interaction.response.send_message(
                f"✅ You received **{MONEY_EMOJI} "
                f"{self.amount:,}**.",
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
        target_role=None,
        target_user=None
    ):
        super().__init__(timeout=None)

        self.bot = bot
        self.chest_type = chest_type
        self.amount = amount
        self.quantity = quantity
        self.target_role = target_role
        self.target_user = target_user

        self.claimed = 0
        self.claimed_users = []

        self.lock = asyncio.Lock()

        if chest_type == "normal":
            self.chest_name = "Normal Chest"
            self.chest_emoji = "🎁"

        elif chest_type == "mega":
            self.chest_name = "Mega Chest"
            self.chest_emoji = "💎"

        else:
            self.chest_name = "Ultra Chest"
            self.chest_emoji = "⚡"

        self.claim_button = discord.ui.Button(
            label=f"🎁 Claim reward 0/{quantity}",
            style=discord.ButtonStyle.success
        )

        self.claim_button.callback = self.claim
        self.add_item(self.claim_button)

    def chest_key(self):
        return {
            "normal": "chest",
            "mega": "mega",
            "ultra": "ultra"
        }[self.chest_type]

    def get_embed(self):

        description = (
            "Click the button below to receive the reward.\n\n"
            f"**Reward:** {self.amount} × "
            f"{self.chest_name} {self.chest_emoji}\n"
            f"**Claims:** {self.claimed}/{self.quantity}\n"
            f"**Full drop:** "
            f"{'✅' if self.claimed >= self.quantity else '❌'}"
        )

        if self.target_role:
            description += (
                f"\n**Only:** {self.target_role.mention}"
            )

        if self.target_user:
            description += (
                f"\n**Only:** {self.target_user.mention}"
            )

        if self.claimed_users:
            description += (
                "\n**Claimed by:** "
                + ", ".join(
                    user.mention
                    for user in self.claimed_users[:10]
                )
            )

        return discord.Embed(
            title="🎁 Chest Drop",
            description=description,
            color=discord.Color.green()
        )

    async def claim(self, interaction: discord.Interaction):

        async with self.lock:

            user = interaction.user

            if self.target_user:
                if user.id != self.target_user.id:
                    await interaction.response.send_message(
                        "❌ You cannot claim this drop.",
                        ephemeral=True
                    )
                    return

            if self.target_role:
                if self.target_role not in user.roles:
                    await interaction.response.send_message(
                        "❌ You cannot claim this drop.",
                        ephemeral=True
                    )
                    return

            if user.id in [u.id for u in self.claimed_users]:
                await interaction.response.send_message(
                    "❌ You have already claimed this drop.",
                    ephemeral=True
                )
                return

            if self.claimed >= self.quantity:
                await interaction.response.send_message(
                    "❌ This drop is already full.",
                    ephemeral=True
                )
                return

            chests = self.bot.get_cog("Chests")

            if chests is None:
                await interaction.response.send_message(
                    "❌ Chest system is unavailable.",
                    ephemeral=True
                )
                return

            success = await chests.add_chests(
                user.id,
                self.amount,
                self.chest_key()
            )

            if not success:
                await interaction.response.send_message(
                    "❌ Failed to give the chest reward.",
                    ephemeral=True
                )
                return

            self.claimed += 1
            self.claimed_users.append(user)

            self.claim_button.label = (
                f"🎁 Claim reward "
                f"{self.claimed}/{self.quantity}"
            )

            if self.claimed >= self.quantity:
                self.claim_button.disabled = True

            await interaction.message.edit(
                embed=self.get_embed(),
                view=self
            )

            await interaction.response.send_message(
                f"✅ You received **{self.amount} × "
                f"{self.chest_name} {self.chest_emoji}**.",
                ephemeral=True
            )


# =========================
# DROPS COG
# =========================

class Drops(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # =========================
    # FIND USER / ROLE
    # =========================

    def get_role_and_user(self, ctx, arguments):

        target_role = None
        target_user = None

        for argument in arguments:

            # ROLE
            if argument.startswith("<@&") and argument.endswith(">"):

                try:
                    role_id = int(argument[3:-1])
                except ValueError:
                    continue

                for role in ctx.message.role_mentions:
                    if role.id == role_id:
                        target_role = role
                        break

            # USER
            elif argument.startswith("<@") and argument.endswith(">"):

                clean = argument[2:-1]

                if clean.startswith("!"):
                    clean = clean[1:]

                try:
                    user_id = int(clean)
                except ValueError:
                    continue

                for user in ctx.message.mentions:
                    if user.id == user_id:
                        target_user = user
                        break

        return target_role, target_user

    # =========================
    # MONEY DROP
    # =========================

    @commands.command(name="money")
    async def money(
        self,
        ctx,
        subcommand=None,
        amount=None,
        quantity=None,
        *arguments
    ):

        if ctx.author.id != OWNER_ID:
            return

        if subcommand != "economy":
            return

        try:
            amount = int(amount)
            quantity = int(quantity)
        except (TypeError, ValueError):
            await ctx.send(
                "❌ Usage: `!money economy <amount> "
                "<quantity> [user] [role]`"
            )
            return

        if amount <= 0 or quantity <= 0:
            await ctx.send(
                "❌ Amount and quantity must be greater than 0."
            )
            return

        target_role, target_user = (
            self.get_role_and_user(ctx, arguments)
        )

        view = MoneyDropView(
            self.bot,
            amount,
            quantity,
            target_user,
            target_role
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
        quantity=None,
        *arguments
    ):

        if ctx.author.id != OWNER_ID:
            return

        if not chest_type or not amount or not quantity:
            await ctx.send(
                "❌ Usage: `!drop <chest_type> "
                "<amount> <quantity> [role] [user]`"
            )
            return

        chest_type = chest_type.lower()

        chest_types = {
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

        if chest_type not in chest_types:
            await ctx.send(
                "❌ Chest type must be `normal`, `mega` or `ultra`."
            )
            return

        chest_type = chest_types[chest_type]

        try:
            amount = int(amount)
            quantity = int(quantity)
        except (TypeError, ValueError):
            await ctx.send(
                "❌ Amount and quantity must be numbers."
            )
            return

        if amount <= 0 or quantity <= 0:
            await ctx.send(
                "❌ Amount and quantity must be greater than 0."
            )
            return

        target_role, target_user = (
            self.get_role_and_user(ctx, arguments)
        )

        view = ChestDropView(
            self.bot,
            chest_type,
            amount,
            quantity,
            target_role,
            target_user
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
        *arguments
    ):

        if ctx.author.id != OWNER_ID:
            return

        if not chest_type or not amount or not arguments:
            await ctx.send(
                "❌ Usage: `!remove <chest_type> "
                "<amount> <user>`"
            )
            return

        chest_type = chest_type.lower()

        chest_types = {
            "normal": ("chest", "Normal Chest", "🎁"),
            "chest": ("chest", "Normal Chest", "🎁"),
            "chests": ("chest", "Normal Chest", "🎁"),

            "mega": ("mega", "Mega Chest", "💎"),
            "mega-chest": ("mega", "Mega Chest", "💎"),
            "mega_chest": ("mega", "Mega Chest", "💎"),

            "ultra": ("ultra", "Ultra Chest", "⚡"),
            "ultra-chest": ("ultra", "Ultra Chest", "⚡"),
            "ultra_chest": ("ultra", "Ultra Chest", "⚡")
        }

        if chest_type not in chest_types:
            await ctx.send(
                "❌ Chest type must be `normal`, `mega` or `ultra`."
            )
            return

        chest_key, chest_name, chest_emoji = (
            chest_types[chest_type]
        )

        try:
            amount = int(amount)
        except (TypeError, ValueError):
            await ctx.send(
                "❌ Amount must be a number."
            )
            return

        if amount <= 0:
            await ctx.send(
                "❌ Amount must be greater than 0."
            )
            return

        # =========================
        # FIND USER
        # =========================

        target_user = None

        for argument in arguments:

            if not (
                argument.startswith("<@")
                and argument.endswith(">")
            ):
                continue

            clean = argument[2:-1]

            if clean.startswith("!"):
                clean = clean[1:]

            try:
                user_id = int(clean)
            except ValueError:
                continue

            for user in ctx.message.mentions:
                if user.id == user_id:
                    target_user = user
                    break

        if target_user is None:
            await ctx.send(
                "❌ Please mention a user."
            )
            return

        # =========================
        # GET CHESTS COG
        # =========================

        chests = self.bot.get_cog("Chests")

        if chests is None:
            await ctx.send(
                "❌ Chest system is unavailable."
            )
            return

        # =========================
        # GET USER DATA
        # =========================

        user_data = chests.get_user_data(
            target_user.id
        )

        current_amount = int(
            user_data.get(chest_key, 0)
        )

        if current_amount < amount:
            await ctx.send(
                f"❌ {target_user.mention} does not have "
                f"enough {chest_name}s.\n"
                f"Current: **{current_amount}**"
            )
            return

        # =========================
        # REMOVE
        # =========================

        user_data[chest_key] = current_amount - amount

        await chests.save_data()

        await ctx.send(
            f"✅ Removed **{amount} × {chest_name} "
            f"{chest_emoji}** from {target_user.mention}.\n"
            f"Remaining: **{user_data[chest_key]}**"
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
