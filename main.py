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


# =========================
# Tokens
# =========================

TOKEN = os.environ["DISCORD_TOKEN"]
UB_TOKEN = os.environ["UNBELIEVABOAT_TOKEN"]


# =========================
# Settings
# =========================

OWNER_ID = 1176149190192152626

UB_GUILD_ID = "1520800006905266216"

VIDEO_ROLE_ID = 1541715251018465351
TOURNAMENT_ROLE_ID = 1541715118872731768
GIVEAWAY_ROLE_ID = 1541716902752157798
NEWS_ROLE_ID = 1541715546356060200

PING_ROLE_IDS = [
    VIDEO_ROLE_ID,
    TOURNAMENT_ROLE_ID,
    GIVEAWAY_ROLE_ID,
    NEWS_ROLE_ID
]


# =========================
# Flask
# =========================

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


# =========================================================
# UnbelievaBoat
# =========================================================

async def add_ub_money(
    user_id: int,
    amount: int
):

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
        method="PATCH",
        headers={
            "Authorization": UB_TOKEN,
            "Content-Type": "application/json"
        }
    )

    try:

        response = await asyncio.to_thread(
            urllib.request.urlopen,
            request
        )

        response.read()

        return True

    except urllib.error.HTTPError as e:

        error_text = e.read().decode(
            errors="ignore"
        )

        print(
            f"❌ UnbelievaBoat API error "
            f"{e.code}: {error_text}"
        )

        return False

    except Exception as e:

        print(
            f"❌ UnbelievaBoat error: {e}"
        )

        return False


# =========================================================
# Money Drop
# =========================================================

class MoneyDropView(discord.ui.View):

    def __init__(
        self,
        amount: int,
        quantity: int,
        allowed_user_id=None,
        allowed_role_id=None
    ):

        super().__init__(
            timeout=None
        )

        self.amount = amount
        self.quantity = quantity

        self.allowed_user_id = allowed_user_id
        self.allowed_role_id = allowed_role_id

        self.claimed_users = set()

        self.update_button()


    # =========================
    # Update Button
    # =========================

    def update_button(self):

        claimed = len(
            self.claimed_users
        )

        self.claim_button.label = (
            f"🎁 Claim reward {claimed}/{self.quantity}"
        )

        self.claim_button.disabled = (
            claimed >= self.quantity
        )


    # =========================
    # Claim
    # =========================

    @discord.ui.button(
        label="🎁 Claim reward 0/1",
        style=discord.ButtonStyle.success,
        custom_id="money_drop_claim"
    )
    async def claim_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        user = interaction.user


        # =========================
        # Already claimed
        # =========================

        if user.id in self.claimed_users:

            await interaction.response.send_message(
                "❌ **You already claimed this reward.**",
                ephemeral=True
            )

            return


        # =========================
        # Full
        # =========================

        if len(self.claimed_users) >= self.quantity:

            await interaction.response.send_message(
                "❌ **This money drop is full.**",
                ephemeral=True
            )

            return


        # =========================
        # User restriction
        # =========================

        if (
            self.allowed_user_id is not None
            and user.id != self.allowed_user_id
        ):

            await interaction.response.send_message(
                "❌ **You cannot claim this money drop.**\n"
                "This reward is reserved for another user.",
                ephemeral=True
            )

            return


        # =========================
        # Role restriction
        # =========================

        if self.allowed_role_id is not None:

            if interaction.guild is None:

                await interaction.response.send_message(
                    "❌ **This reward can only be claimed in a server.**",
                    ephemeral=True
                )

                return


            try:

                member = await interaction.guild.fetch_member(
                    user.id
                )

            except discord.HTTPException:

                await interaction.response.send_message(
                    "❌ **I couldn't check your roles.**",
                    ephemeral=True
                )

                return


            role = interaction.guild.get_role(
                self.allowed_role_id
            )

            if role is None:

                await interaction.response.send_message(
                    "❌ **The required role could not be found.**",
                    ephemeral=True
                )

                return


            if role not in member.roles:

                await interaction.response.send_message(
                    "❌ **You cannot claim this money drop.**\n"
                    f"You need the {role.mention} role.",
                    ephemeral=True
                )

                return


        # =========================
        # Add money
        # =========================

        success = await add_ub_money(
            user.id,
            self.amount
        )

        if not success:

            await interaction.response.send_message(
                "❌ **Something went wrong.**\n"
                "The reward could not be added.",
                ephemeral=True
            )

            return


        # =========================
        # Save claim
        # =========================

        self.claimed_users.add(
            user.id
        )

        self.update_button()


        # =========================
        # Update message
        # =========================

        claimed = len(
            self.claimed_users
        )

        await interaction.response.edit_message(
            content=(
                "**Money drop**\n"
                "Click the button below to receive the reward\n"
                f"> {claimed}/{self.quantity}\n"
                f"Full drop {'✅' if claimed >= self.quantity else '❌'}"
                + (
                    f"\nOnly <@{self.allowed_user_id}> can claim"
                    if self.allowed_user_id is not None
                    else (
                        f"\nOnly <@&{self.allowed_role_id}> can claim"
                        if self.allowed_role_id is not None
                        else ""
                    )
                )
            ),
            view=self
        )


# =========================================================
# Discord Bot
# =========================================================

intents = discord.Intents.default()
intents.message_content = True


class TournamentBot(commands.Bot):

    async def setup_hook(self):

        # Persistent Ping Panel
        self.add_view(
            PingPanel()
        )

        # Slash commands
        try:

            await self.tree.sync()

            print(
                "✅ Slash commands synced!"
            )

        except Exception as e:

            print(
                f"❌ Failed to sync slash commands: {e}"
            )


bot = TournamentBot(
    command_prefix="!",
    intents=intents
)


# =========================================================
# Ping Panel
# =========================================================

class PingPanel(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )


    # =========================
    # Get Member
    # =========================

    async def get_member(
        self,
        interaction: discord.Interaction
    ):

        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ **Error**\n"
                "This button can only be used inside a server.",
                ephemeral=True
            )

            return None


        try:

            member = await interaction.guild.fetch_member(
                interaction.user.id
            )

            return member

        except discord.NotFound:

            await interaction.response.send_message(
                "❌ **Error**\n"
                "Your member information could not be found.",
                ephemeral=True
            )

            return None

        except discord.HTTPException:

            await interaction.response.send_message(
                "❌ **Error**\n"
                "I couldn't get your member information.",
                ephemeral=True
            )

            return None


    # =========================
    # Toggle Role
    # =========================

    async def toggle_role(
        self,
        interaction: discord.Interaction,
        role_id: int,
        role_name: str
    ):

        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ **Error**\n"
                "This button can only be used inside a server.",
                ephemeral=True
            )

            return


        role = interaction.guild.get_role(
            role_id
        )

        if role is None:

            await interaction.response.send_message(
                "❌ **Error**\n"
                "The role could not be found.",
                ephemeral=True
            )

            return


        member = await self.get_member(
            interaction
        )

        if member is None:
            return


        try:

            if role in member.roles:

                await member.remove_roles(
                    role
                )

                await interaction.response.send_message(
                    f"✅ **Role removed!**\n"
                    f"You no longer have the {role_name} role.",
                    ephemeral=True
                )

            else:

                await member.add_roles(
                    role
                )

                await interaction.response.send_message(
                    f"✅ **Role added!**\n"
                    f"You now have the {role_name} role.",
                    ephemeral=True
                )


        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ **Error**\n"
                "I don't have permission to manage this role.",
                ephemeral=True
            )

        except discord.HTTPException:

            await interaction.response.send_message(
                "❌ **Error**\n"
                "I couldn't update your role.",
                ephemeral=True
            )


    # =========================
    # Video Ping
    # =========================

    @discord.ui.button(
        label="🔴 Video Ping",
        style=discord.ButtonStyle.primary,
        custom_id="ping_video"
    )
    async def video(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await self.toggle_role(
            interaction,
            VIDEO_ROLE_ID,
            "Video Ping"
        )


    # =========================
    # Tournament Ping
    # =========================

    @discord.ui.button(
        label="🏆 Tournament Ping",
        style=discord.ButtonStyle.primary,
        custom_id="ping_tournament"
    )
    async def tournament(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await self.toggle_role(
            interaction,
            TOURNAMENT_ROLE_ID,
            "Tournament Ping"
        )


    # =========================
    # Giveaway Ping
    # =========================

    @discord.ui.button(
        label="🎁 Giveaway Ping",
        style=discord.ButtonStyle.primary,
        custom_id="ping_giveaway"
    )
    async def giveaway(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await self.toggle_role(
            interaction,
            GIVEAWAY_ROLE_ID,
            "Giveaway Ping"
        )


    # =========================
    # News Ping
    # =========================

    @discord.ui.button(
        label="📢 News Ping",
        style=discord.ButtonStyle.primary,
        custom_id="ping_news"
    )
    async def news(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await self.toggle_role(
            interaction,
            NEWS_ROLE_ID,
            "News Ping"
        )


    # =========================
    # Remove All
    # =========================

    @discord.ui.button(
        label="❌ Remove all ping roles",
        style=discord.ButtonStyle.secondary,
        custom_id="ping_remove_all"
    )
    async def remove_all(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ **Error**\n"
                "This button can only be used inside a server.",
                ephemeral=True
            )

            return


        member = await self.get_member(
            interaction
        )

        if member is None:
            return


        roles_to_remove = []

        for role_id in PING_ROLE_IDS:

            role = interaction.guild.get_role(
                role_id
            )

            if role and role in member.roles:

                roles_to_remove.append(
                    role
                )


        try:

            if roles_to_remove:

                await member.remove_roles(
                    *roles_to_remove
                )


            await interaction.response.send_message(
                "🗑️ **Roles removed!**\n"
                "All ping roles have been removed from you.",
                ephemeral=True
            )


        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ **Error**\n"
                "I don't have permission to remove these roles.",
                ephemeral=True
            )

        except discord.HTTPException:

            await interaction.response.send_message(
                "❌ **Error**\n"
                "I couldn't remove your ping roles.",
                ephemeral=True
            )


# =========================================================
# Bot Ready
# =========================================================

@bot.event
async def on_ready():

    print(
        f"🤖 Logged in as {bot.user}"
    )


# =========================================================
# Owner Check
# =========================================================

def owner_only():

    async def predicate(
        interaction: discord.Interaction
    ):

        return interaction.user.id == OWNER_ID

    return app_commands.check(
        predicate
    )


# =========================================================
# /send
# =========================================================

send_group = app_commands.Group(
    name="send",
    description="Send messages"
)


@send_group.command(
    name="message",
    description="Send a message to a channel"
)
@app_commands.describe(
    text="Text to send",
    channel="Channel where the message will be sent"
)
@owner_only()
async def send_message(
    interaction: discord.Interaction,
    text: str,
    channel: discord.TextChannel
):

    try:

        await channel.send(
            f"**BOT:** {text}"
        )

        await interaction.response.send_message(
            "Message sent successfully.",
            ephemeral=True
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I don't have permission to send messages in that channel.",
            ephemeral=True
        )

    except discord.HTTPException:

        await interaction.response.send_message(
            "❌ Failed to send the message.",
            ephemeral=True
        )


@send_group.command(
    name="dms",
    description="Send a direct message to a user"
)
@app_commands.describe(
    user="User to send the DM to",
    message="Message to send"
)
@owner_only()
async def send_dms(
    interaction: discord.Interaction,
    user: discord.User,
    message: str
):

    try:

        server_name = (
            interaction.guild.name
            if interaction.guild
            else "Unknown Server"
        )

        await user.send(
            f"**BOT:** {message}\n"
            f"-# Server: {server_name}"
        )

        await interaction.response.send_message(
            "DM sent successfully.",
            ephemeral=True
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ Could not send a DM. The user's DMs are closed.",
            ephemeral=True
        )

    except discord.HTTPException:

        await interaction.response.send_message(
            "❌ Could not send the DM.",
            ephemeral=True
        )


bot.tree.add_command(
    send_group
)


# =========================================================
# /clear
# =========================================================

clear_group = app_commands.Group(
    name="clear",
    description="Clear messages"
)


@clear_group.command(
    name="message",
    description="Delete messages from a channel"
)
@app_commands.describe(
    channel="Channel to clear",
    number_of_messages="Number of messages to delete"
)
@owner_only()
async def clear_message(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    number_of_messages: app_commands.Range[int, 1, 100]
):

    try:

        deleted = await channel.purge(
            limit=number_of_messages
        )

        await interaction.response.send_message(
            f"✅ Successfully deleted {len(deleted)} messages.",
            ephemeral=True
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I don't have permission to delete messages in this channel.",
            ephemeral=True
        )

    except discord.HTTPException:

        await interaction.response.send_message(
            "❌ Failed to delete messages.",
            ephemeral=True
        )


bot.tree.add_command(
    clear_group
)


# =========================================================
# !ping panel
# =========================================================

@bot.command(
    name="ping"
)
async def ping_command(
    ctx: commands.Context,
    option: str = None
):

    if ctx.author.id != OWNER_ID:

        await ctx.send(
            "❌ **Permission denied**\n"
            "You don't have permission to use this command.",
            delete_after=5
        )

        return


    if option is None or option.lower() != "panel":

        await ctx.send(
            "❌ **Invalid command**\n"
            "Use `!ping panel`.",
            delete_after=5
        )

        return


    embed = discord.Embed(
        description=(
            "**⚙️ Click on reactions to get the roles you need! ⚙️**\n\n"
            f"🔴 <@&{VIDEO_ROLE_ID}> - You will receive notifications about a new video.\n"
            f"🏆 <@&{TOURNAMENT_ROLE_ID}> - You will receive notifications about a new tournament.\n"
            f"🎁 <@&{GIVEAWAY_ROLE_ID}> - You will receive notifications about the draw "
            f"(The draw is related to the currency of the server, it is not related to money in any way!)\n"
            f"📢 <@&{NEWS_ROLE_ID}> - You will receive notifications about new news on the server!"
        )
    )


    await ctx.send(
        embed=embed,
        view=PingPanel()
    )


    try:

        await ctx.message.delete()

    except discord.Forbidden:

        pass

    except discord.HTTPException:

        pass


# =========================================================
# !money economy
# =========================================================

@bot.command(
    name="money"
)
async def money_command(
    ctx: commands.Context,
    economy: str = None,
    amount: str = None,
    *args
):

    # =========================
    # Owner only
    # =========================

    if ctx.author.id != OWNER_ID:

        await ctx.send(
            "❌ **Permission denied**",
            delete_after=5
        )

        return


    # =========================
    # Check economy
    # =========================

    if economy is None or economy.lower() != "economy":

        await ctx.send(
            "❌ **Invalid command**\n"
            "Use `!money economy <amount> [user/quantity/role]`.",
            delete_after=5
        )

        return


    # =========================
    # Amount
    # =========================

    try:

        amount_int = int(amount)

    except (TypeError, ValueError):

        await ctx.send(
            "❌ **Invalid amount.**\n"
            "Amount must be a whole number.",
            delete_after=5
        )

        return


    if amount_int <= 0:

        await ctx.send(
            "❌ **Invalid amount.**\n"
            "Amount must be greater than 0.",
            delete_after=5
        )

        return


    # =========================
    # Parse arguments
    # =========================

    allowed_user_id = None
    allowed_role_id = None

    quantity = 1

    for arg in args:

        # User mention
        if arg.startswith("<@") and not arg.startswith("<@&"):

            cleaned = (
                arg
                .replace("<@", "")
                .replace("!", "")
                .replace(">", "")
            )

            try:

                user_id = int(cleaned)

            except ValueError:

                await ctx.send(
                    "❌ **Invalid user mention.**",
                    delete_after=5
                )

                return


            if allowed_role_id is not None:

                await ctx.send(
                    "❌ You can choose **either a user or a role**, "
                    "not both.",
                    delete_after=5
                )

                return


            if allowed_user_id is not None:

                await ctx.send(
                    "❌ Only one user can be selected.",
                    delete_after=5
                )

                return


            allowed_user_id = user_id

        # Role mention
        elif arg.startswith("<@&"):

            cleaned = (
                arg
                .replace("<@&", "")
                .replace(">", "")
            )

            try:

                role_id = int(cleaned)

            except ValueError:

                await ctx.send(
                    "❌ **Invalid role mention.**",
                    delete_after=5
                )

                return


            if allowed_user_id is not None:

                await ctx.send(
                    "❌ You can choose **either a user or a role**, "
                    "not both.",
                    delete_after=5
                )

                return


            if allowed_role_id is not None:

                await ctx.send(
                    "❌ Only one role can be selected.",
                    delete_after=5
                )

                return


            allowed_role_id = role_id

        # Quantity
        else:

            try:

                parsed_quantity = int(arg)

            except ValueError:

                await ctx.send(
                    "❌ **Invalid quantity.**\n"
                    "Quantity must be a whole number.",
                    delete_after=5
                )

                return


            if parsed_quantity <= 0:

                await ctx.send(
                    "❌ **Invalid quantity.**\n"
                    "Quantity must be greater than 0.",
                    delete_after=5
                )

                return


            quantity = parsed_quantity


    # =========================
    # Check role
    # =========================

    if allowed_role_id is not None:

        role = ctx.guild.get_role(
            allowed_role_id
        )

        if role is None:

            await ctx.send(
                "❌ **The selected role could not be found.**",
                delete_after=5
            )

            return


    # =========================
    # Create View
    # =========================

    view = MoneyDropView(
        amount=amount_int,
        quantity=quantity,
        allowed_user_id=allowed_user_id,
        allowed_role_id=allowed_role_id
    )


    # =========================
    # Restriction text
    # =========================

    restriction = ""

    if allowed_user_id is not None:

        restriction = (
            f"\nOnly <@{allowed_user_id}> can claim"
        )

    elif allowed_role_id is not None:

        restriction = (
            f"\nOnly <@&{allowed_role_id}> can claim"
        )


    # =========================
    # Send Money Drop
    # =========================

    message = await ctx.send(
        content=(
            "**Money drop**\n"
            "Click the button below to receive the reward\n"
            f"> 0/{quantity}\n"
            f"Full drop ❌"
            f"{restriction}"
        ),
        view=view
    )


    # =========================
    # Delete command
    # =========================

    try:

        await ctx.message.delete()

    except discord.Forbidden:

        pass

    except discord.HTTPException:

        pass


# =========================================================
# Prefix Command Errors
# =========================================================

@ping_command.error
async def ping_command_error(
    ctx: commands.Context,
    error
):

    try:

        await ctx.send(
            "❌ **Error**\n"
            "Something went wrong while processing the command.",
            delete_after=5
        )

    except discord.HTTPException:

        pass


# =========================================================
# Slash Command Errors
# =========================================================

@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):

    if isinstance(
        error,
        app_commands.CheckFailure
    ):

        if not interaction.response.is_done():

            await interaction.response.send_message(
                "❌ You do not have permission to use this command.",
                ephemeral=True
            )


# =========================================================
# Start Flask
# =========================================================

Thread(
    target=run_flask,
    daemon=True
).start()


# =========================================================
# Start Bot
# =========================================================

bot.run(TOKEN) 
