import os
import asyncio
import json

import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask
from threading import Thread


# =================================================
# Tokens
# =================================================

TOKEN = os.environ["DISCORD_TOKEN"]


# =================================================
# Settings
# =================================================

OWNER_ID = 1176149190192152626


# =================================================
# Flask
# =================================================

app = Flask(__name__)


@app.route("/")
def home():

    return "Tournament Bot is online!"


def run_flask():

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )


# =================================================
# Discord Bot
# =================================================

intents = discord.Intents.default()

intents.message_content = True


class TournamentBot(commands.Bot):

    async def setup_hook(self):

        # =================================================
        # Load message.py
        # =================================================

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


        # =================================================
        # Load ticket.py
        # =================================================

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


        # =================================================
        # Load chests.py
        # =================================================

        try:

            await self.load_extension(
                "chests"
            )

            print(
                "✅ chests.py loaded!"
            )

        except Exception as e:

            print(
                f"❌ Failed to load chests.py: {e}"
            )


        # =================================================
        # Load drops.py
        # =================================================

        try:

            await self.load_extension(
                "drops"
            )

            print(
                "✅ drops.py loaded!"
            )

        except Exception as e:

            print(
                f"❌ Failed to load drops.py: {e}"
            )


        # =================================================
        # Sync Slash Commands
        # =================================================

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


# =================================================
# Bot Ready
# =================================================

@bot.event
async def on_ready():

    print(
        f"🤖 Logged in as {bot.user}"
    )


# =================================================
# Owner Check
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
# /send
# =================================================

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


# =================================================
# /clear
# =================================================

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


# =================================================
# Slash Command Errors
# =================================================

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


# =================================================
# Start Flask
# =================================================

Thread(
    target=run_flask,
    daemon=True
).start()


# =================================================
# Start Bot
# =================================================

bot.run(TOKEN)
