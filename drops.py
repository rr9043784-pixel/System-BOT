import os
import asyncio
import urllib.request
import urllib.error

import discord
from discord.ext import commands


# =========================
# SETTINGS
# =========================

OWNER_ID = 1176149190192152626
GUILD_ID = 1520800006905266216

UB_TOKEN = os.environ["UNBELIEVABOAT_TOKEN"]

MONEY_EMOJI = "<:MoneyR:1534220684178231397>"


# =========================
# UNBELIEVABOAT
# =========================

def ub_request(method, url, data=None):
    headers = {
        "Authorization": UB_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8")
            return response.status, body

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        return e.code, body

    except Exception as e:
        return 0, str(e)


async def add_money(user_id: int, amount: int):
    url = (
        f"https://unbelievaboat.com/api/v1/guilds/"
        f"{GUILD_ID}/users/{user_id}"
    )

    data = f'{{"cash":{amount}}}'.encode()

    status, body = await asyncio.to_thread(
        ub_request,
        "PATCH",
        url,
        data,
    )

    return status, body


async def remove_money(user_id: int, amount: int):
    url = (
        f"https://unbelievaboat.com/api/v1/guilds/"
        f"{GUILD_ID}/users/{user_id}"
    )

    data = f'{{"cash":{-amount}}}'.encode()

    status, body = await asyncio.to_thread(
        ub_request,
        "PATCH",
        url,
        data,
    )

    return status, body


# =========================
# DROP VIEW
# =========================

class DropView(discord.ui.View):

    def __init__(
        self,
        bot,
        amount: int,
        quantity: int,
        drop_type: str = "money",
        role_id: int | None = None,
        user_id: int | None = None,
    ):
        super().__init__(timeout=None)

        self.bot = bot
        self.amount = amount
        self.quantity = quantity
        self.drop_type = drop_type
        self.role_id = role_id
        self.user_id = user_id

        self.claimed = set()
        self.lock = asyncio.Lock()

        self.claim_button = discord.ui.Button(
            label=f"🎁 Claim reward 0/{quantity}",
            style=discord.ButtonStyle.green,
            custom_id=f"drop_claim_{id(self)}",
        )

        self.claim_button.callback = self.claim

        self.add_item(self.claim_button)

    # =========================
    # CHECK ACCESS
    # =========================

    def can_claim(self, member: discord.Member):

        if self.user_id is not None:
            if member.id != self.user_id:
                return False

        if self.role_id is not None:
            if self.role_id not in [role.id for role in member.roles]:
                return False

        return True

    # =========================
    # CLAIM
    # =========================

    async def claim(self, interaction: discord.Interaction):

        if not interaction.guild:
            await interaction.response.send_message(
                "❌ **Error** This drop can only be claimed in the server.",
                ephemeral=True,
            )
            return

        member = interaction.guild.get_member(interaction.user.id)

        if member is None:
            await interaction.response.send_message(
                "❌ **Error** Your member information could not be found.",
                ephemeral=True,
            )
            return

        async with self.lock:

            if len(self.claimed) >= self.quantity:
                await interaction.response.send_message(
                    "❌ **Error** This drop has already been fully claimed.",
                    ephemeral=True,
                )
                return

            if interaction.user.id in self.claimed:
                await interaction.response.send_message(
                    "❌ **Error** You have already claimed this reward.",
                    ephemeral=True,
                )
                return

            if not self.can_claim(member):

                if self.user_id is not None:
                    message = (
                        "❌ **Error** "
                        "This reward is reserved for another user."
                    )
                elif self.role_id is not None:
                    message = (
                        "❌ **Error** "
                        "You don't have the required role."
                    )
                else:
                    message = (
                        "❌ **Error** "
                        "You are not allowed to claim this reward."
                    )

                await interaction.response.send_message(
                    message,
                    ephemeral=True,
                )
                return

            # =========================
            # MONEY
            # =========================

            if self.drop_type == "money":

                await interaction.response.defer(
                    ephemeral=True
                )

                status, body = await add_money(
                    member.id,
                    self.amount,
                )

                if status not in (200, 201):

                    await interaction.followup.send(
                        "❌ **Error** The reward could not be given.",
                        ephemeral=True,
                    )
                    return

                self.claimed.add(member.id)

                await self.update_message(interaction)

                await interaction.followup.send(
                    f"🎉 You received "
                    f"{MONEY_EMOJI} {self.amount:,}!",
                    ephemeral=True,
                )

                try:
                    await member.send(
                        f"🎉 You received "
                        f"{MONEY_EMOJI} {self.amount:,} "
                        f"from a money drop!"
                    )
                except Exception:
                    pass

                return

            # =========================
            # CHEST
            # =========================

            if self.drop_type in ("normal", "mega", "ultra"):

                await interaction.response.defer(
                    ephemeral=True
                )

                chests = self.bot.get_cog("Chests")

                if chests is None:
                    await interaction.followup.send(
                        "❌ **Error** The chest system is unavailable.",
                        ephemeral=True,
                    )
                    return

                try:

                    if self.drop_type == "normal":
                        await chests.add_chests(
                            member.id,
                            self.amount,
                            "chests",
                        )

                    elif self.drop_type == "mega":
                        await chests.add_chests(
                            member.id,
                            self.amount,
                            "mega_chests",
                        )

                    elif self.drop_type == "ultra":
                        await chests.add_chests(
                            member.id,
                            self.amount,
                            "ultra_chests",
                        )

                except Exception:

                    await interaction.followup.send(
                        "❌ **Error** The reward could not be given.",
                        ephemeral=True,
                    )
                    return

                self.claimed.add(member.id)

                await self.update_message(interaction)

                names = {
                    "normal": "Normal Chest",
                    "mega": "Mega Chest",
                    "ultra": "Ultra Chest",
                }

                chest_name = names[self.drop_type]

                await interaction.followup.send(
                    f"🎉 You received **{self.amount} × {chest_name}**!",
                    ephemeral=True,
                )

                return

    # =========================
    # UPDATE MESSAGE
    # =========================

    async def update_message(self, interaction):

        claimed_count = len(self.claimed)

        self.claim_button.label = (
            f"🎁 Claim reward "
            f"{claimed_count}/{self.quantity}"
        )

        if claimed_count >= self.quantity:
            self.claim_button.disabled = True

        try:
            await interaction.message.edit(
                view=self
            )
        except Exception:
            pass


# =========================
# DROPS COG
# =========================

class Drops(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # =========================
    # OWNER CHECK
    # =========================

    async def cog_check(self, ctx):

        if ctx.author.id != OWNER_ID:
            return False

        return True

    # =========================
    # MONEY GROUP
    # =========================

    @commands.group(
        name="money",
        invoke_without_command=True,
    )
    async def money(self, ctx):

        if ctx.invoked_subcommand is None:
            await ctx.send(
                "❌ **Usage:** `!money economy <amount> <quantity> [user] [role]`",
                delete_after=5,
            )

    # =========================
    # MONEY ECONOMY
    # =========================

    @money.command(
        name="economy"
    )
    async def money_economy(
        self,
        ctx,
        amount: int,
        quantity: int,
        user: discord.Member | None = None,
        role: discord.Role | None = None,
    ):

        if amount <= 0:
            await ctx.send(
                "❌ **Error** Amount must be greater than 0.",
                delete_after=5,
            )
            return

        if quantity <= 0:
            await ctx.send(
                "❌ **Error** Quantity must be greater than 0.",
                delete_after=5,
            )
            return

        if user is not None and role is not None:
            await ctx.send(
                "❌ **Error** You can use either a user or a role, not both.",
                delete_after=5,
            )
            return

        view = DropView(
            self.bot,
            amount=amount,
            quantity=quantity,
            drop_type="money",
            role_id=role.id if role else None,
            user_id=user.id if user else None,
        )

        embed = discord.Embed(
            description=(
                "**Money drop**\n\n"
                f"{MONEY_EMOJI} **{amount:,}**\n\n"
                f"Available rewards: **{quantity}**"
            ),
            color=discord.Color.green(),
        )

        if user:
            embed.add_field(
                name="User",
                value=user.mention,
                inline=True,
            )

        if role:
            embed.add_field(
                name="Role",
                value=role.mention,
                inline=True,
            )

        embed.add_field(
            name="Claimed",
            value="0",
            inline=True,
        )

        message = await ctx.send(
            embed=embed,
            view=view,
        )

        try:
            await ctx.message.delete()
        except Exception:
            pass

        view.message_id = message.id

    # =========================
    # DROP COMMAND
    # =========================

    @commands.command(
        name="drop"
    )
    async def drop(
        self,
        ctx,
        chest_type: str,
        amount: int,
        quantity: int,
        role: discord.Role | None = None,
        user: discord.Member | None = None,
    ):

        chest_type = chest_type.lower()

        aliases = {
            "normal": "normal",
            "chest": "normal",
            "chests": "normal",

            "mega": "mega",
            "megachest": "mega",
            "mega_chest": "mega",

            "ultra": "ultra",
            "ultrachest": "ultra",
            "ultra_chest": "ultra",
        }

        if chest_type not in aliases:
            await ctx.send(
                "❌ **Error** Chest type must be "
                "`normal`, `mega` or `ultra`.",
                delete_after=5,
            )
            return

        chest_type = aliases[chest_type]

        if amount <= 0:
            await ctx.send(
                "❌ **Error** Amount must be greater than 0.",
                delete_after=5,
            )
            return

        if quantity <= 0:
            await ctx.send(
                "❌ **Error** Quantity must be greater than 0.",
                delete_after=5,
            )
            return

        if role is not None and user is not None:
            await ctx.send(
                "❌ **Error** You can use either a role or a user, not both.",
                delete_after=5,
            )
            return

        names = {
            "normal": "Normal Chest",
            "mega": "Mega Chest",
            "ultra": "Ultra Chest",
        }

        chest_name = names[chest_type]

        view = DropView(
            self.bot,
            amount=amount,
            quantity=quantity,
            drop_type=chest_type,
            role_id=role.id if role else None,
            user_id=user.id if user else None,
        )

        embed = discord.Embed(
            description=(
                "**Chest drop**\n\n"
                f"🎁 **{chest_name}**\n"
                f"Amount per person: **{amount}**\n\n"
                f"Available rewards: **{quantity}**"
            ),
            color=discord.Color.green(),
        )

        if role:
            embed.add_field(
                name="Role",
                value=role.mention,
                inline=True,
            )

        if user:
            embed.add_field(
                name="User",
                value=user.mention,
                inline=True,
            )

        embed.add_field(
            name="Claimed",
            value="0",
            inline=True,
        )

        message = await ctx.send(
            embed=embed,
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
