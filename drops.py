import os
import json
import asyncio
import urllib.request
import urllib.error

import discord
from discord.ext import commands


# =========================================================
# LEGENDS DROPS
# Python 3.13 | discord.py 2.6+
# =========================================================

OWNER_ID = 1176149190192152626

# Set these in Railway Variables.
UB_GUILD_ID = os.getenv("UNBELIEVABOAT_GUILD_ID", "1520800006905266216")
UB_TOKEN = os.getenv("UNB_TOKEN", "").strip()

MONEY_EMOJI = "<:MoneyR:1534220684178231397>"
CHEST_EMOJIS = {
    "normal": "<:Chest:1569403637392736336>",
    "mega": "<:Mega_Chest:1569403640567963861>",
    "ultra": "<:Ultra_Chest:1569403638554566820>",
}
CHEST_NAMES = {
    "normal": "Normal Chest",
    "mega": "Mega Chest",
    "ultra": "Ultra Chest",
}
CHEST_KEYS = {
    "normal": "chest",
    "mega": "mega",
    "ultra": "ultra",
}

MAX_AMOUNT = 1_000_000_000
MAX_CLAIMS = 100


# =========================================================
# UNBELIEVABOAT API
# =========================================================

def _ub_add_cash_sync(user_id: int, amount: int):
    if not UB_TOKEN:
        raise RuntimeError(
            "UNBELIEVABOAT_TOKEN is missing in Railway Variables."
        )

    if not UB_GUILD_ID:
        raise RuntimeError(
            "UNBELIEVABOAT_GUILD_ID is missing in Railway Variables."
        )

    url = (
        "https://unbelievaboat.com/api/v1/guilds/"
        f"{UB_GUILD_ID}/users/{user_id}"
    )
    payload = json.dumps({
        "cash": amount,
        "reason": "LEGENDS Money Drop",
    }).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=payload,
        method="PATCH",
        headers={
            "Authorization": UB_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            if response.status not in (200, 201, 204):
                raise RuntimeError(
                    f"UnbelievaBoat returned HTTP {response.status}."
                )
            return True
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(
            f"UnbelievaBoat API error HTTP {error.code}: {details}"
        ) from error
    except urllib.error.URLError as error:
        raise RuntimeError(
            f"Could not connect to UnbelievaBoat: {error.reason}"
        ) from error


async def add_ub_money(user_id: int, amount: int):
    return await asyncio.to_thread(
        _ub_add_cash_sync, int(user_id), int(amount)
    )


# =========================================================
# HELPERS
# =========================================================

def owner_only():
    async def predicate(ctx):
        return ctx.author.id == OWNER_ID
    return commands.check(predicate)


def parse_member_id(value: str):
    value = (value or "").strip()
    if not value:
        return None
    value = value.replace("<@", "").replace(">", "").replace("!", "")
    if not value.isdigit():
        raise ValueError("Target user must be a member mention or numeric ID.")
    return int(value)


def parse_role_id(value: str):
    value = (value or "").strip()
    if not value:
        return None
    value = value.replace("<@&", "").replace(">", "")
    if not value.isdigit():
        raise ValueError("Target role must be a role mention or numeric ID.")
    return int(value)


def normalize_chest_type(value: str):
    value = value.lower().strip()
    aliases = {
        "normal": "normal",
        "chest": "normal",
        "normalchest": "normal",
        "mega": "mega",
        "megachest": "mega",
        "ultra": "ultra",
        "ultrachest": "ultra",
    }
    if value not in aliases:
        raise ValueError("Choose `normal`, `mega`, or `ultra`.")
    return aliases[value]


def validate_drop(amount: int, claims: int):
    if amount <= 0 or amount > MAX_AMOUNT:
        raise ValueError(f"Amount must be between 1 and {MAX_AMOUNT:,}.")
    if claims <= 0 or claims > MAX_CLAIMS:
        raise ValueError(f"Claims must be between 1 and {MAX_CLAIMS}.")


# =========================================================
# COMPONENTS V2 DROP MENU
# =========================================================

class DropSetupModal(discord.ui.Modal):
    def __init__(self, cog, drop_type: str):
        self.cog = cog
        self.drop_type = drop_type

        title = (
            "Create Money Drop"
            if drop_type == "money"
            else f"Create {CHEST_NAMES[drop_type]} Drop"
        )
        super().__init__(title=title, timeout=300)

        self.amount_input = discord.ui.TextInput(
            label="Amount per claim",
            placeholder="Example: 1000",
            required=True,
            max_length=12,
        )
        self.claims_input = discord.ui.TextInput(
            label="Number of claims",
            placeholder="Example: 5",
            required=True,
            max_length=3,
        )
        self.user_input = discord.ui.TextInput(
            label="Target user (optional)",
            placeholder="Mention or user ID",
            required=False,
            max_length=30,
        )
        self.role_input = discord.ui.TextInput(
            label="Target role (optional)",
            placeholder="Mention or role ID",
            required=False,
            max_length=30,
        )

        self.add_item(self.amount_input)
        self.add_item(self.claims_input)
        self.add_item(self.user_input)
        self.add_item(self.role_input)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message(
                "Only the bot owner can create drops.",
                ephemeral=True,
            )

        try:
            amount = int(str(self.amount_input.value).replace(",", "").strip())
            claims = int(str(self.claims_input.value).strip())
            validate_drop(amount, claims)
            target_user_id = parse_member_id(self.user_input.value)
            target_role_id = parse_role_id(self.role_input.value)
        except ValueError as error:
            return await interaction.response.send_message(
                f"❌ {error}",
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            await self.cog.create_drop_message(
                channel=interaction.channel,
                drop_type=self.drop_type,
                amount=amount,
                claims=claims,
                target_user_id=target_user_id,
                target_role_id=target_role_id,
            )
        except Exception as error:
            return await interaction.followup.send(
                f"❌ Could not create the drop: `{str(error)[:700]}`",
                ephemeral=True,
            )

        await interaction.followup.send(
            "✅ Drop created successfully.",
            ephemeral=True,
        )


class DropTypeSelect(discord.ui.Select):
    def __init__(self, cog):
        self.cog = cog
        options = [
            discord.SelectOption(
                label="Money Drop",
                value="money",
                description="Give UnbelievaBoat cash to claimants",
                emoji="💰",
            ),
            discord.SelectOption(
                label="Normal Chest",
                value="normal",
                description="Give Normal Chests",
                emoji=discord.PartialEmoji.from_str(CHEST_EMOJIS["normal"]),
            ),
            discord.SelectOption(
                label="Mega Chest",
                value="mega",
                description="Give Mega Chests",
                emoji=discord.PartialEmoji.from_str(CHEST_EMOJIS["mega"]),
            ),
            discord.SelectOption(
                label="Ultra Chest",
                value="ultra",
                description="Give Ultra Chests",
                emoji=discord.PartialEmoji.from_str(CHEST_EMOJIS["ultra"]),
            ),
        ]
        super().__init__(
            placeholder="Select the drop type...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="legends_drops:type",
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message(
                "Only the bot owner can use this menu.",
                ephemeral=True,
            )
        await interaction.response.send_modal(
            DropSetupModal(self.cog, self.values[0])
        )


class DropMenuView(discord.ui.LayoutView):
    def __init__(self, cog):
        super().__init__(timeout=300)
        container = discord.ui.Container(
            discord.ui.TextDisplay(
                "## LEGENDS DROP CENTER\n"
                "Choose what you want to create.\n\n"
                "💰 **Money Drop** — UnbelievaBoat cash\n"
                f"{CHEST_EMOJIS['normal']} **Normal Chest**\n"
                f"{CHEST_EMOJIS['mega']} **Mega Chest**\n"
                f"{CHEST_EMOJIS['ultra']} **Ultra Chest**"
            ),
            discord.ui.ActionRow(DropTypeSelect(cog)),
        )
        self.add_item(container)


# =========================================================
# DROP CLAIM BUTTON
# =========================================================

class ClaimDropButton(discord.ui.Button):
    def __init__(self, drop_view):
        self.drop_view = drop_view
        super().__init__(
            label="Claim",
            style=discord.ButtonStyle.success,
            emoji="🎁",
            custom_id=None,
        )

    async def callback(self, interaction: discord.Interaction):
        await self.drop_view.claim(interaction)


class DropClaimView(discord.ui.LayoutView):
    def __init__(
        self,
        cog,
        drop_type: str,
        amount: int,
        claims: int,
        target_user_id=None,
        target_role_id=None,
    ):
        super().__init__(timeout=86400)
        self.cog = cog
        self.drop_type = drop_type
        self.amount = amount
        self.total_claims = claims
        self.remaining = claims
        self.target_user_id = target_user_id
        self.target_role_id = target_role_id
        self.claimed_users = set()
        self.claimed_names = []
        self.lock = asyncio.Lock()
        self.message = None
        self.expired = False

        self.button = ClaimDropButton(self)
        self.refresh_layout()

    def reward_label(self):
        if self.drop_type == "money":
            return f"{MONEY_EMOJI} **{self.amount:,}**"
        return (
            f"{CHEST_EMOJIS[self.drop_type]} "
            f"**{self.amount:,} {CHEST_NAMES[self.drop_type]}(s)**"
        )

    def refresh_layout(self):
        self.clear_items()

        target_text = ""
        if self.target_user_id:
            target_text += f"\n**Target user:** <@{self.target_user_id}>"
        if self.target_role_id:
            target_text += f"\n**Target role:** <@&{self.target_role_id}>"

        progress = (
            f"**Claims:** {self.total_claims - self.remaining}"
            f"/{self.total_claims}"
        )
        description = (
            "## 🎉 LEGENDS DROP\n"
            f"**Reward per claim:** {self.reward_label()}\n"
            f"{progress}\n"
            f"**Remaining:** {self.remaining}"
            f"{target_text}\n\n"
            "Press **Claim** to receive your reward."
        )
        if self.remaining <= 0:
            description = (
                "## ✅ DROP COMPLETED\n"
                f"**Reward:** {self.reward_label()}\n"
                f"**Claims:** {self.total_claims}/{self.total_claims}\n"
                "All rewards have been claimed."
                f"{target_text}"
            )

        button = ClaimDropButton(self)
        button.disabled = self.remaining <= 0
        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(description),
                discord.ui.ActionRow(button),
            )
        )
        self.button = button

    async def claim(self, interaction: discord.Interaction):
        if interaction.guild is None:
            return await interaction.response.send_message(
                "Drops can only be claimed inside the server.",
                ephemeral=True,
            )

        member = interaction.user
        if not isinstance(member, discord.Member):
            member = interaction.guild.get_member(interaction.user.id)

        if member is None:
            return await interaction.response.send_message(
                "Could not verify your server membership.",
                ephemeral=True,
            )

        async with self.lock:
            if self.remaining <= 0:
                return await interaction.response.send_message(
                    "This drop has already been fully claimed.",
                    ephemeral=True,
                )

            if member.id in self.claimed_users:
                return await interaction.response.send_message(
                    "You have already claimed this drop.",
                    ephemeral=True,
                )

            if self.target_user_id or self.target_role_id:
                user_allowed = (
                    self.target_user_id is not None
                    and member.id == self.target_user_id
                )
                role_allowed = (
                    self.target_role_id is not None
                    and any(role.id == self.target_role_id for role in member.roles)
                )
                if not (user_allowed or role_allowed):
                    return await interaction.response.send_message(
                        "You are not eligible to claim this drop.",
                        ephemeral=True,
                    )

            await interaction.response.defer(ephemeral=True, thinking=True)

            try:
                if self.drop_type == "money":
                    await add_ub_money(member.id, self.amount)
                else:
                    chest_cog = self.cog.bot.get_cog("Chests")
                    if chest_cog is None:
                        raise RuntimeError(
                            "The Chests extension is not loaded."
                        )

                    success = await chest_cog.add_chests(
                        member.id,
                        self.amount,
                        CHEST_KEYS[self.drop_type],
                    )
                    if not success:
                        raise RuntimeError(
                            "The chest reward could not be added."
                        )
            except Exception as error:
                return await interaction.followup.send(
                    f"❌ Reward could not be delivered: `{str(error)[:700]}`",
                    ephemeral=True,
                )

            self.claimed_users.add(member.id)
            self.claimed_names.append(member.display_name)
            self.remaining -= 1

            self.refresh_layout()
            if self.message:
                try:
                    await self.message.edit(view=self)
                except discord.HTTPException:
                    pass

            await interaction.followup.send(
                f"✅ You claimed {self.reward_label()}!",
                ephemeral=True,
            )

    async def on_timeout(self):
        self.expired = self.remaining > 0
        self.remaining = 0
        self.refresh_layout()
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


# =========================================================
# COG
# =========================================================

class Drops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def create_drop_message(
        self,
        channel,
        drop_type,
        amount,
        claims,
        target_user_id=None,
        target_role_id=None,
    ):
        validate_drop(amount, claims)

        if drop_type not in ("money", "normal", "mega", "ultra"):
            raise ValueError("Unknown drop type.")

        if channel is None or not hasattr(channel, "send"):
            raise RuntimeError("The target channel is unavailable.")

        view = DropClaimView(
            self,
            drop_type,
            amount,
            claims,
            target_user_id,
            target_role_id,
        )
        message = await channel.send(
            view=view,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        view.message = message
        return message

    @commands.command(name="drops")
    @owner_only()
    async def drops_menu(self, ctx):
        """Open the Components V2 drop creator."""
        await ctx.send(view=DropMenuView(self))

    @commands.command(name="money")
    @owner_only()
    async def money_drop(
        self,
        ctx,
        economy: str,
        amount: int,
        quantity: int,
        target_user: discord.Member = None,
        target_role: discord.Role = None,
    ):
        """
        Usage:
        !money economy 1000 5
        !money economy 1000 5 @member
        !money economy 1000 5 @member @role
        """
        try:
            validate_drop(amount, quantity)
        except ValueError as error:
            return await ctx.send(f"❌ {error}")

        if not UB_TOKEN:
            return await ctx.send(
                "❌ `UNBELIEVABOAT_TOKEN` is missing in Railway Variables."
            )

        try:
            await self.create_drop_message(
                ctx.channel,
                "money",
                amount,
                quantity,
                target_user.id if target_user else None,
                target_role.id if target_role else None,
            )
        except Exception as error:
            return await ctx.send(
                f"❌ Could not create the Money Drop: `{str(error)[:700]}`"
            )

    @commands.command(name="drop")
    @owner_only()
    async def chest_drop(self, ctx, chest_type: str, amount: int, quantity: int):
        """
        Usage:
        !drop normal 2 5
        !drop mega 1 3
        !drop ultra 1 1
        Add a member mention or role mention to restrict the drop.
        """
        try:
            drop_type = normalize_chest_type(chest_type)
            validate_drop(amount, quantity)
        except ValueError as error:
            return await ctx.send(f"❌ {error}")

        target_user_id = (
            ctx.message.mentions[0].id if ctx.message.mentions else None
        )
        target_role_id = (
            ctx.message.role_mentions[0].id if ctx.message.role_mentions else None
        )

        try:
            await self.create_drop_message(
                ctx.channel,
                drop_type,
                amount,
                quantity,
                target_user_id,
                target_role_id,
            )
        except Exception as error:
            return await ctx.send(
                f"❌ Could not create the Chest Drop: `{str(error)[:700]}`"
            )

    @commands.command(name="remove")
    @owner_only()
    async def remove_chests(
        self,
        ctx,
        chest_type: str,
        amount: int,
        target_user: discord.Member,
    ):
        """
        Usage:
        !remove normal 5 @member
        !remove mega 1 @member
        !remove ultra 1 @member
        """
        try:
            drop_type = normalize_chest_type(chest_type)
            if amount <= 0:
                raise ValueError("Amount must be greater than zero.")
        except ValueError as error:
            return await ctx.send(f"❌ {error}")

        chest_cog = self.bot.get_cog("Chests")
        if chest_cog is None:
            return await ctx.send("❌ The Chests extension is not loaded.")

        user_data = chest_cog.get_user_data(target_user.id)
        data_key = {
            "normal": "chests",
            "mega": "mega_chests",
            "ultra": "ultra_chests",
        }[drop_type]

        current = int(user_data.get(data_key, 0))
        if current < amount:
            return await ctx.send(
                f"❌ {target_user.mention} only has **{current:,}** "
                f"{CHEST_NAMES[drop_type]}(s)."
            )

        user_data[data_key] = current - amount
        await chest_cog.save_data()

        await ctx.send(
            f"✅ Removed **{amount:,}** "
            f"{CHEST_EMOJIS[drop_type]} {CHEST_NAMES[drop_type]}(s) "
            f"from {target_user.mention}."
        )


async def setup(bot):
    await bot.add_cog(Drops(bot))
