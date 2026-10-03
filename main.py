import os
import asyncio
import json
import urllib.request
import urllib.error

import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask
from threading import Thread


# =================================================
# SETTINGS
# =================================================

TOKEN = os.environ["DISCORD_TOKEN"]
UB_TOKEN = os.environ["UNBELIEVABOAT_TOKEN"]

OWNER_ID = 1176149190192152626
UB_GUILD_ID = "1520800006905266216"

MONEY_EMOJI = "<:MoneyR:1534220684178231397>"


# =================================================
# FLASK
# =================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "Tournament Bot is online!"


def run_flask():
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )


# =================================================
# UNBELIEVABOAT
# =================================================

def add_ub_money(user_id: int, amount: int):

    url = (
        f"https://unbelievaboat.com/api/v1/"
        f"guilds/{UB_GUILD_ID}/users/{user_id}"
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

        with urllib.request.urlopen(request, timeout=10) as response:

            return response.status == 200

    except urllib.error.HTTPError as e:

        print(
            f"UnbelievaBoat HTTP error: "
            f"{e.code} {e.reason}"
        )

        return False

    except Exception as e:

        print(
            f"UnbelievaBoat error: {e}"
        )

        return False


# =================================================
# MONEY DROP VIEW
# =================================================

class MoneyDropView(discord.ui.View):

    def __init__(
        self,
        amount: int,
        quantity: int,
        allowed_user_id: int | None = None,
        allowed_role_id: int | None = None
    ):

        super().__init__(
            timeout=None
        )

        self.amount = amount
        self.quantity = quantity

        self.allowed_user_id = allowed_user_id
        self.allowed_role_id = allowed_role_id

        self.claimed_users = set()
        self.claimed_names = []

        self.message = None

    def update_button(self):

        button = self.children[0]

        button.label = (
            f"🎁 Claim reward "
            f"{len(self.claimed_users)}/{self.quantity}"
        )

        if len(self.claimed_users) >= self.quantity:

            button.disabled = True

    def build_embed(self):

        embed = discord.Embed(
            title="💰 Money drop",
            description=(
                f"**Reward:** "
                f"{MONEY_EMOJI} "
                f"{self.amount:,}\n\n"
                f"**Claims:** "
                f"{len(self.claimed_users)}/"
                f"{self.quantity}"
            ),
            color=discord.Color.green()
        )

        if self.claimed_names:

            shown_names = self.claimed_names[:10]

            embed.add_field(
                name="Claimed by",
                value="\n".join(
                    f"• {name}"
                    for name in shown_names
                ),
                inline=False
            )

        if len(self.claimed_names) > 10:

            embed.add_field(
                name="More",
                value=(
                    f"+{len(self.claimed_names) - 10} "
                    f"more"
                ),
                inline=False
            )

        if len(self.claimed_users) >= self.quantity:

            embed.set_footer(
                text="Full drop"
            )

        return embed

    @discord.ui.button(
        label="🎁 Claim reward 0/1",
        style=discord.ButtonStyle.success,
        custom_id="money_drop_claim"
    )
    async def claim(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        user = interaction.user

        # =============================================
        # ALREADY CLAIMED
        # =============================================

        if user.id in self.claimed_users:

            await interaction.response.send_message(
                "❌ **You already claimed this reward.**",
                ephemeral=True
            )

            return

        # =============================================
        # FULL
        # =============================================

        if len(self.claimed_users) >= self.quantity:

            await interaction.response.send_message(
                "❌ **This money drop is full.**",
                ephemeral=True
            )

            return

        # =============================================
        # USER RESTRICTION
        # =============================================

        if self.allowed_user_id is not None:

            if user.id != self.allowed_user_id:

                await interaction.response.send_message(
                    "❌ **You cannot claim this reward.**",
                    ephemeral=True
                )

                return

        # =============================================
        # ROLE RESTRICTION
        # =============================================

        if self.allowed_role_id is not None:

            if not isinstance(user, discord.Member):

                await interaction.response.send_message(
                    "❌ **You cannot claim this reward.**",
                    ephemeral=True
                )

                return

            if self.allowed_role_id not in [
                role.id for role in user.roles
            ]:

                await interaction.response.send_message(
                    "❌ **You cannot claim this reward.**",
                    ephemeral=True
                )

                return

        # =============================================
        # GIVE MONEY
        # =============================================

        success = await asyncio.to_thread(
            add_ub_money,
            user.id,
            self.amount
        )

        if not success:

            await interaction.response.send_message(
                "❌ **Failed to give the reward. Please try again later.**",
                ephemeral=True
            )

            return

        # =============================================
        # SAVE CLAIM
        # =============================================

        self.claimed_users.add(
            user.id
        )

        self.claimed_names.append(
            user.display_name
        )

        # =============================================
        # UPDATE
        # =============================================

        self.update_button()

        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self
        )

        # =============================================
        # SUCCESS MESSAGE
        # =============================================

        try:

            await interaction.followup.send(
                f"🎉 **You received "
                f"{MONEY_EMOJI} "
                f"{self.amount:,}!**",
                ephemeral=True
            )

        except Exception:

            pass


# =================================================
# BOT
# =================================================

class TournamentBot(commands.Bot):

    def __init__(self):

        intents = discord.Intents.default()

        intents.message_content = True

        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):

        # =============================================
        # LOAD message.py
        # =============================================

        try:

            await self.load_extension(
                "message"
            )

            print(
                "✅ message.py loaded!"
            )

        except Exception as e:

            print(
                f"❌ Failed to load message.py: {e}"
            )

        # =============================================
        # LOAD ticket.py
        # =============================================

        try:

            await self.load_extension(
                "ticket"
            )

            print(
                "✅ ticket.py loaded!"
            )

        except Exception as e:

            print(
                f"❌ Failed to load ticket.py: {e}"
            )

        # =============================================
        # SYNC SLASH COMMANDS
        # =============================================

        try:

            synced = await self.tree.sync()

            print(
                f"✅ Synced {len(synced)} slash command(s)"
            )

        except Exception as e:

            print(
                f"❌ Slash command sync failed: {e}"
            )


bot = TournamentBot()


# =================================================
# EVENTS
# =================================================

@bot.event
async def on_ready():

    print(
        f"✅ Logged in as {bot.user}"
    )

    print(
        f"🆔 Bot ID: {bot.user.id}"
    )


# =================================================
# OWNER CHECK
# =================================================

def owner_only():

    async def predicate(
        interaction: discord.Interaction
    ):

        return interaction.user.id == OWNER_ID

    return app_commands.check(
        predicate
    )


# =================================================
# /send message
# =================================================

@bot.tree.command(
    name="send",
    description="Send a bot message"
)
@app_commands.describe(
    text="Message to send",
    channel="Channel to send the message in"
)
@owner_only()
async def send_message(
    interaction: discord.Interaction,
    text: str,
    channel: discord.TextChannel | None = None
):

    target = channel or interaction.channel

    if target is None:

        await interaction.response.send_message(
            "❌ **Channel not found.**",
            ephemeral=True
        )

        return

    await target.send(
        f"**BOT:** {text}"
    )

    await interaction.response.send_message(
        "✅ **Message sent.**",
        ephemeral=True
    )


# =================================================
# /send dms
# =================================================

@bot.tree.command(
    name="send_dms",
    description="Send a message to all server members via DM"
)
@app_commands.describe(
    text="Message to send"
)
@owner_only()
async def send_dms(
    interaction: discord.Interaction,
    text: str
):

    await interaction.response.send_message(
        "📨 **Sending DMs...**",
        ephemeral=True
    )

    guild = interaction.guild

    if guild is None:

        return

    sent = 0
    failed = 0

    for member in guild.members:

        if member.bot:
            continue

        try:

            await member.send(
                f"**BOT:** {text}\n"
                f"-# server {guild.name}"
            )

            sent += 1

        except Exception:

            failed += 1

        await asyncio.sleep(1)

    try:

        await interaction.edit_original_response(
            content=(
                f"✅ **DM sending finished.**\n"
                f"Sent: `{sent}`\n"
                f"Failed: `{failed}`"
            )
        )

    except Exception:

        pass


# =================================================
# /clear message
# =================================================

@bot.tree.command(
    name="clear",
    description="Delete messages"
)
@app_commands.describe(
    amount="Number of messages to delete"
)
@owner_only()
async def clear_messages(
    interaction: discord.Interaction,
    amount: app_commands.Range[int, 1, 100]
):

    await interaction.response.defer(
        ephemeral=True
    )

    channel = interaction.channel

    if not isinstance(
        channel,
        discord.TextChannel
    ):

        await interaction.followup.send(
            "❌ **This command can only be used in a text channel.**",
            ephemeral=True
        )

        return

    deleted = await channel.purge(
        limit=amount
    )

    # 1 message
    if len(deleted) == 1:

        await interaction.followup.send(
            "🗑️ **Successfully deleted 1 message.**",
            ephemeral=True
        )

    # More than 1
    else:

        await interaction.followup.send(
            f"🗑️ **Successfully deleted "
            f"{len(deleted)} messages.**",
            ephemeral=True
        )


# =================================================
# !money economy
# =================================================

@bot.command(
    name="money"
)
async def money_command(
    ctx: commands.Context,
    economy: str = None,
    amount: int = None,
    target: str = None,
    quantity: int = 1,
    role: discord.Role = None
):

    # =============================================
    # OWNER ONLY
    # =============================================

    if ctx.author.id != OWNER_ID:

        try:
            await ctx.message.delete()
        except Exception:
            pass

        return

    # =============================================
    # CHECK SUBCOMMAND
    # =============================================

    if economy != "economy":

        try:

            await ctx.message.delete()

        except Exception:

            pass

        return

    # =============================================
    # CHECK AMOUNT
    # =============================================

    if amount is None or amount <= 0:

        try:

            await ctx.message.delete()

        except Exception:

            pass

        return

    # =============================================
    # CHECK QUANTITY
    # =============================================

    if quantity <= 0:

        quantity = 1

    # =============================================
    # PARSE TARGET
    # =============================================

    allowed_user_id = None
    allowed_role_id = None

    # Mentioned user
    if ctx.message.mentions:

        allowed_user_id = (
            ctx.message.mentions[0].id
        )

    # Role
    if role is not None:

        allowed_role_id = role.id

    # =============================================
    # DO NOT ALLOW BOTH
    # =============================================

    if (
        allowed_user_id is not None
        and allowed_role_id is not None
    ):

        try:

            await ctx.message.delete()

        except Exception:

            pass

        return

    # =============================================
    # CREATE DROP
    # =============================================

    view = MoneyDropView(
        amount=amount,
        quantity=quantity,
        allowed_user_id=allowed_user_id,
        allowed_role_id=allowed_role_id
    )

    message = await ctx.send(
        embed=view.build_embed(),
        view=view
    )

    view.message = message

    # =============================================
    # DELETE COMMAND
    # =============================================

    try:

        await ctx.message.delete()

    except Exception:

        pass


# =================================================
# PREFIX COMMAND ERROR
# =================================================

@money_command.error
async def money_command_error(
    ctx: commands.Context,
    error
):

    try:

        await ctx.message.delete()

    except Exception:

        pass


# =================================================
# SLASH COMMAND ERROR
# =================================================

@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error
):

    if isinstance(
        error,
        app_commands.CheckFailure
    ):

        if interaction.response.is_done():

            await interaction.followup.send(
                "❌ **You do not have permission to use this command.**",
                ephemeral=True
            )

        else:

            await interaction.response.send_message(
                "❌ **You do not have permission to use this command.**",
                ephemeral=True
            )

        return

    print(
        f"Slash command error: {error}"
    )


# =================================================
# START FLASK
# =================================================

Thread(
    target=run_flask,
    daemon=True
).start()


# =================================================
# START BOT
# =================================================

bot.run(TOKEN)
