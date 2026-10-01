import os
import discord
from discord import app_commands
from flask import Flask
from threading import Thread

TOKEN = os.environ["DISCORD_TOKEN"]

# Flask для Railway
app = Flask(__name__)

@app.route("/")
def home():
    return "Tournament Bot is online!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Discord
class Bot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

bot = Bot()

@bot.tree.command(name="send", description="Send a message to a channel")
@app_commands.describe(
    text="Text to send",
    channel="Channel where the message will be sent"
)
async def send(
    interaction: discord.Interaction,
    text: str,
    channel: discord.TextChannel
):
    await channel.send(f"**BOT:** {text}")
    await interaction.response.send_message(
        "✅ Message sent!",
        ephemeral=True
    )

Thread(target=run_flask, daemon=True).start()
bot.run(TOKEN)
