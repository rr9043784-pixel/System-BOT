import os
import discord
from discord import app_commands
from flask import Flask
from threading import Thread

TOKEN = os.environ["DISCORD_TOKEN"]

# Твой Discord ID
OWNER_ID = 1176149190192152626


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

class Bot(discord.Client):

    def __init__(self):
        intents = discord.Intents.default()

        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


bot = Bot()


# =========================
# Owner only
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


# =========================
# /send message
# =========================

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

    await channel.send(
        f"**BOT:** {text}"
    )

    await interaction.response.send_message(
        "Message sent successfully.",
        ephemeral=True
    )


# =========================
# /send dms
# =========================

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

        # Название сервера
        server_name = (
            interaction.guild.name
            if interaction.guild
            else "Unknown Server"
        )

        # Сообщение в DM
        await user.send(
            f"**BOT:** {message}\n"
            f"-# сервер {server_name}"
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


# Добавляем /send
bot.tree.add_command(send_group)


# =========================
# Command errors
# =========================

@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):

    if isinstance(error, app_commands.CheckFailure):

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
