import os
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask
from threading import Thread

TOKEN = os.environ["DISCORD_TOKEN"]

# =========================
# Settings
# =========================

OWNER_ID = 1176149190192152626

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
    app.run(host="0.0.0.0", port=port)


# =========================
# Discord Bot
# =========================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================
# Slash Commands Sync
# =========================

@bot.event
async def on_ready():

    try:
        await bot.tree.sync()
        print("✅ Slash commands synced!")

    except Exception as e:
        print(f"❌ Failed to sync slash commands: {e}")

    print(f"🤖 Logged in as {bot.user}")


# =========================
# Owner Check
# =========================

def owner_only():

    async def predicate(interaction: discord.Interaction):
        return interaction.user.id == OWNER_ID

    return app_commands.check(predicate)


# =========================
# /send
# =========================

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


bot.tree.add_command(send_group)


# =========================
# /clear
# =========================

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


bot.tree.add_command(clear_group)


# =========================
# Ping Panel
# =========================

class PingPanel(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    async def toggle_role(
        self,
        interaction: discord.Interaction,
        role_id: int,
        role_name: str
    ):

        role = interaction.guild.get_role(role_id)

        if role is None:

            await interaction.response.send_message(
                "❌ **Error**\n"
                "The role could not be found.",
                ephemeral=True
            )

            return

        member = interaction.guild.get_member(
            interaction.user.id
        )

        if member is None:

            await interaction.response.send_message(
                "❌ **Error**\n"
                "Your member information could not be found.",
                ephemeral=True
            )

            return

        try:

            if role in member.roles:

                await member.remove_roles(role)

                await interaction.response.send_message(
                    f"✅ **Role removed!**\n"
                    f"You no longer have the {role_name} role.",
                    ephemeral=True
                )

            else:

                await member.add_roles(role)

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

        member = interaction.guild.get_member(
            interaction.user.id
        )

        if member is None:

            await interaction.response.send_message(
                "❌ **Error**\n"
                "Your member information could not be found.",
                ephemeral=True
            )

            return

        roles_to_remove = []

        for role_id in PING_ROLE_IDS:

            role = interaction.guild.get_role(role_id)

            if role and role in member.roles:
                roles_to_remove.append(role)

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


# =========================
# !ping panel
# =========================

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


    panel_text = (
        "**⚙️ Click on reactions to get the roles you need! ⚙️**\n\n"
        f"🔴 <@&{VIDEO_ROLE_ID}> - You will receive notifications about a new video.\n"
        f"🏆 <@&{TOURNAMENT_ROLE_ID}> - You will receive notifications about a new tournament.\n"
        f"🎁 <@&{GIVEAWAY_ROLE_ID}> - You will receive notifications about the draw "
        f"(The draw is related to the currency of the server, it is not related to money in any way!)\n"
        f"📢 <@&{NEWS_ROLE_ID}> - You will receive notifications about new news on the server!"
    )


    await ctx.send(
        panel_text,
        view=PingPanel()
    )


    # Delete !ping panel
    try:

        await ctx.message.delete()

    except discord.Forbidden:
        pass

    except discord.HTTPException:
        pass


# =========================
# Prefix Command Errors
# =========================

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


# =========================
# Slash Command Errors
# =========================

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


# =========================
# Start
# =========================

Thread(
    target=run_flask,
    daemon=True
).start()

bot.run(TOKEN)
