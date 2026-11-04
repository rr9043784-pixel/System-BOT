import os
import io
import json
import base64
import logging
import sqlite3

import discord
from discord.ext import commands
from openai import AsyncOpenAI

# =========================================================
# CONFIGURATION
# =========================================================

DB_PATH = os.getenv("AI_DB_PATH", "ai_chats.db")
CHAT_CATEGORY_ID = int(os.getenv("AI_CATEGORY_ID", "0"))

# FreeTheAI OpenAI-compatible API.
API_KEY = os.getenv("FTAI_API_KEY") or os.getenv("OPENAI_API_KEY")
API_BASE_URL = os.getenv(
    "AI_BASE_URL",
    "https://api.freetheai.org/v1",
)
CHAT_MODEL = os.getenv(
    "AI_MODEL",
    "fta/zai/glm-5.3-flash",
)

MAX_IMAGE_SIZE = 5 * 1024 * 1024
MAX_HISTORY_MESSAGES = 12

SYSTEM_PROMPT = """
You are a helpful, friendly AI assistant inside a Discord server.
Automatically detect the language used by the user and reply in that
same language. Support every language your model can understand.
Keep the conversation natural and useful, like a capable general
assistant. You can help with programming, education, translations,
ideas, writing, and questions about uploaded images.
Be accurate and honest. If you do not know, say so.
Never claim to have created an image unless you actually did.
Do not generate videos.
"""

logging.basicConfig(level=logging.INFO)


# =========================================================
# DATABASE
# =========================================================

def db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with db() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS ai_chats (
                channel_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                channel_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS ai_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def register_chat(channel_id, user_id, guild_id, channel_name):
    with db() as con:
        con.execute("""
            INSERT OR REPLACE INTO ai_chats
            (channel_id, user_id, guild_id, channel_name)
            VALUES (?, ?, ?, ?)
        """, (channel_id, user_id, guild_id, channel_name))


def get_chat(channel_id):
    with db() as con:
        return con.execute(
            "SELECT * FROM ai_chats WHERE channel_id = ?",
            (channel_id,),
        ).fetchone()


def get_user_chats(user_id, guild_id):
    with db() as con:
        return con.execute("""
            SELECT * FROM ai_chats
            WHERE user_id = ? AND guild_id = ?
            ORDER BY created_at DESC
        """, (user_id, guild_id)).fetchall()


def delete_chat_data(channel_id):
    with db() as con:
        con.execute(
            "DELETE FROM ai_history WHERE channel_id = ?",
            (channel_id,),
        )
        con.execute(
            "DELETE FROM ai_chats WHERE channel_id = ?",
            (channel_id,),
        )


def normalize_content(role, content):
    """
    Convert old Responses API history to Chat Completions format.
    This keeps existing SQLite chat history compatible.
    """
    if isinstance(content, str):
        return content

    if not isinstance(content, list):
        return str(content)

    normalized = []
    for item in content:
        if not isinstance(item, dict):
            continue

        item_type = item.get("type")

        if item_type in ("input_text", "text"):
            normalized.append({
                "type": "text",
                "text": item.get("text", ""),
            })

        elif item_type == "input_image":
            image_url = item.get("image_url")
            if image_url:
                normalized.append({
                    "type": "image_url",
                    "image_url": {"url": image_url},
                })

        elif item_type == "image_url":
            image_url = item.get("image_url")
            if isinstance(image_url, str):
                normalized.append({
                    "type": "image_url",
                    "image_url": {"url": image_url},
                })
            elif isinstance(image_url, dict):
                normalized.append(item)

    if not normalized:
        return str(content)

    # Chat Completions accepts multimodal arrays for user messages.
    if role == "user":
        return normalized

    return "\n".join(
        item.get("text", "")
        for item in normalized
        if item.get("type") == "text"
    )


def load_history(channel_id):
    with db() as con:
        rows = con.execute("""
            SELECT role, content FROM ai_history
            WHERE channel_id = ?
            ORDER BY id DESC LIMIT ?
        """, (channel_id, MAX_HISTORY_MESSAGES)).fetchall()

    rows = list(reversed(rows))
    result = []

    for row in rows:
        try:
            content = json.loads(row["content"])
        except (ValueError, TypeError):
            content = row["content"]

        result.append({
            "role": row["role"],
            "content": normalize_content(row["role"], content),
        })

    return result


def save_history_message(channel_id, role, content):
    if not isinstance(content, str):
        content = json.dumps(content, ensure_ascii=False)

    with db() as con:
        con.execute("""
            INSERT INTO ai_history (channel_id, role, content)
            VALUES (?, ?, ?)
        """, (channel_id, role, content))

        con.execute("""
            DELETE FROM ai_history
            WHERE channel_id = ?
              AND id NOT IN (
                  SELECT id FROM ai_history
                  WHERE channel_id = ?
                  ORDER BY id DESC
                  LIMIT ?
              )
        """, (
            channel_id,
            channel_id,
            MAX_HISTORY_MESSAGES,
        ))


# =========================================================
# PRIVATE CHAT CHANNEL
# =========================================================

async def create_private_chat(bot, guild, user):
    bot_member = guild.me

    if bot_member is None:
        bot_member = guild.get_member(bot.user.id)

    if bot_member is None:
        raise RuntimeError("Could not find bot member in this server.")

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=False
        ),
        user: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            attach_files=True,
            embed_links=True,
        ),
        bot_member: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            manage_channels=True,
            attach_files=True,
            embed_links=True,
        ),
    }

    category = None
    if CHAT_CATEGORY_ID:
        candidate = guild.get_channel(CHAT_CATEGORY_ID)
        if isinstance(candidate, discord.CategoryChannel):
            category = candidate

    safe_name = "".join(
        char.lower() if char.isalnum() else "-"
        for char in user.display_name
    ).strip("-")

    channel_name = f"ai-{(safe_name[:35] or 'user')}"
    channel = await guild.create_text_channel(
        name=channel_name,
        category=category,
        overwrites=overwrites,
        topic=f"Private AI chat for user ID {user.id}",
        reason="Creating a private AI chat",
    )

    register_chat(channel.id, user.id, guild.id, channel.name)

    await channel.send(
        f"**AI Chat**\n"
        f"Welcome, {user.mention}!\n\n"
        "Send a message to start chatting. You can also attach "
        "an image and ask questions about it.\n\n"
        "The assistant automatically replies in your language.\n"
        "Use `!openai panel` to manage your chats."
    )

    return channel


# =========================================================
# PAGINATED CHAT SELECT MENU
# =========================================================

class ChatListView(discord.ui.View):

    PAGE_SIZE = 25

    def __init__(self, bot, user_id, guild_id, chats, page=0):
        super().__init__(timeout=180)
        self.bot = bot
        self.user_id = user_id
        self.guild_id = guild_id
        self.chats = chats
        self.page = page
        self.build_items()

    async def interaction_check(self, interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This menu belongs to another user.",
                ephemeral=True,
            )
            return False
        return True

    def build_items(self):
        start = self.page * self.PAGE_SIZE
        page_chats = self.chats[start:start + self.PAGE_SIZE]

        if page_chats:
            options = [
                discord.SelectOption(
                    label=chat["channel_name"][:100],
                    value=str(chat["channel_id"]),
                    description=f"Chat ID: {chat['channel_id']}",
                )
                for chat in page_chats
            ]

            select = discord.ui.Select(
                placeholder="Select a chat to open",
                min_values=1,
                max_values=1,
                options=options,
            )
            select.callback = self.select_chat
            self.add_item(select)

        if self.page > 0:
            previous = discord.ui.Button(
                label="Previous Page",
                style=discord.ButtonStyle.secondary,
                row=1,
            )
            previous.callback = self.previous_page
            self.add_item(previous)

        if start + self.PAGE_SIZE < len(self.chats):
            next_button = discord.ui.Button(
                label="Next Page",
                style=discord.ButtonStyle.primary,
                row=1,
            )
            next_button.callback = self.next_page
            self.add_item(next_button)

    async def select_chat(self, interaction):
        channel_id = int(interaction.data["values"][0])
        record = get_chat(channel_id)

        if not record or record["user_id"] != self.user_id:
            await interaction.response.send_message(
                "Chat not found or access denied.",
                ephemeral=True,
            )
            return

        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except (discord.NotFound, discord.Forbidden):
                delete_chat_data(channel_id)
                await interaction.response.send_message(
                    "This chat no longer exists or is inaccessible.",
                    ephemeral=True,
                )
                return

        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "This chat is not a text channel.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"Your chat: {channel.mention}",
            ephemeral=True,
        )

    async def previous_page(self, interaction):
        self.page -= 1
        self.clear_items()
        self.build_items()
        await interaction.response.edit_message(
            content=self.page_text(),
            view=self,
        )

    async def next_page(self, interaction):
        self.page += 1
        self.clear_items()
        self.build_items()
        await interaction.response.edit_message(
            content=self.page_text(),
            view=self,
        )

    def page_text(self):
        total_pages = max(
            1,
            (len(self.chats) + self.PAGE_SIZE - 1) // self.PAGE_SIZE,
        )
        return (
            f"**Your AI Chats**\n"
            f"Page {self.page + 1} of {total_pages}\n"
            "Select a chat from the menu below."
        )


# =========================================================
# PANEL BUTTONS
# =========================================================

class AIPanelView(discord.ui.View):

    def __init__(self, bot, user_id):
        super().__init__(timeout=300)
        self.bot = bot
        self.user_id = user_id

    async def interaction_check(self, interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This panel belongs to another user.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(
        label="Open Chat",
        emoji="💬",
        style=discord.ButtonStyle.primary,
    )
    async def open_chat(self, interaction, button):
        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            channel = await create_private_chat(
                self.bot,
                interaction.guild,
                interaction.user,
            )
            await interaction.followup.send(
                f"Your private AI chat is ready: {channel.mention}",
                ephemeral=True,
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "I need permission to manage channels and send messages.",
                ephemeral=True,
            )
        except Exception:
            logging.exception("Failed to create AI chat")
            await interaction.followup.send(
                "Could not create your chat. Please try again.",
                ephemeral=True,
            )

    @discord.ui.button(
        label="My Chats",
        emoji="📚",
        style=discord.ButtonStyle.secondary,
    )
    async def my_chats(self, interaction, button):
        if interaction.guild is None:
            await interaction.response.send_message(
                "Use this panel inside a server.",
                ephemeral=True,
            )
            return

        chats = get_user_chats(
            interaction.user.id,
            interaction.guild.id,
        )

        if not chats:
            await interaction.response.send_message(
                "You have no saved chats yet. Click Open Chat first.",
                ephemeral=True,
            )
            return

        view = ChatListView(
            self.bot,
            interaction.user.id,
            interaction.guild.id,
            chats,
        )

        await interaction.response.send_message(
            view.page_text(),
            view=view,
            ephemeral=True,
        )


# =========================================================
# AI COG / EXTENSION
# =========================================================

class AICog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.client = (
            AsyncOpenAI(
                api_key=API_KEY,
                base_url=API_BASE_URL,
                timeout=90.0,
                max_retries=2,
            )
            if API_KEY else None
        )

    async def cog_load(self):
        init_db()

        if self.client is None:
            logging.error(
                "FTAI_API_KEY is missing. AI chat will not work."
            )
        else:
            logging.info(
                "AI client initialized with model %s.",
                CHAT_MODEL,
            )

    async def cog_unload(self):
        if self.client is not None:
            await self.client.close()

    @commands.group(
        name="openai",
        invoke_without_command=True,
    )
    async def openai_command(self, ctx):
        await ctx.send(
            "Use `!openai panel` to open the AI panel."
        )

    @openai_command.command(name="panel")
    @commands.guild_only()
    async def openai_panel(self, ctx):
        embed = discord.Embed(
            title="AI Assistant",
            description=(
                "Chat with an AI assistant, ask questions, "
                "and analyze images.\n\n"
                "**Features**\n"
                "• Private chat channels\n"
                "• Saved chat history\n"
                "• Image understanding\n"
                "• Automatic language detection\n"
                "• Multilingual conversations\n\n"
                "Image generation is not included in the free chat API."
            ),
            color=discord.Color.blurple(),
        )

        await ctx.send(
            embed=embed,
            view=AIPanelView(self.bot, ctx.author.id),
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.guild is None:
            return

        record = get_chat(message.channel.id)
        if record is None:
            return

        if record["user_id"] != message.author.id:
            return

        # Do not answer prefix commands in the private channel.
        if message.content.startswith("!"):
            return

        if self.client is None:
            await message.reply(
                "AI is not configured yet. Please contact the server owner."
            )
            return

        image_attachments = []
        unsupported = []

        for attachment in message.attachments:
            content_type = attachment.content_type or ""
            if content_type.startswith("image/"):
                image_attachments.append(attachment)
            else:
                unsupported.append(attachment.filename)

        if unsupported:
            await message.reply(
                "I can process images only. These attachments "
                "are not supported: "
                + ", ".join(unsupported[:5])
            )
            return

        if not message.content.strip() and not image_attachments:
            await message.reply(
                "Send a text message or attach an image."
            )
            return

        user_content = []
        user_text = message.content.strip() or "Describe this image."
        user_content.append({
            "type": "text",
            "text": user_text,
        })

        for attachment in image_attachments[:3]:
            if attachment.size > MAX_IMAGE_SIZE:
                await message.reply(
                    f"`{attachment.filename}` is too large. "
                    "Maximum image size is 5 MB."
                )
                return

            try:
                raw = await attachment.read()
                encoded = base64.b64encode(raw).decode("ascii")
                mime = attachment.content_type or "image/png"

                user_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime};base64,{encoded}"
                    },
                })
            except Exception:
                logging.exception("Failed to read image attachment")
                await message.reply("I could not read that image.")
                return

        content_to_save = (
            user_text if not image_attachments else user_content
        )

        save_history_message(
            message.channel.id,
            "user",
            content_to_save,
        )
        history = load_history(message.channel.id)

        async with message.channel.typing():
            try:
                response = await self.client.chat.completions.create(
                    model=CHAT_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT,
                        },
                        *history,
                    ],
                    max_tokens=1500,
                )

                answer = response.choices[0].message.content or (
                    "I could not generate a response."
                )

                if not isinstance(answer, str):
                    answer = str(answer)

                save_history_message(
                    message.channel.id,
                    "assistant",
                    answer,
                )

                for start in range(0, len(answer), 1900):
                    await message.reply(
                        answer[start:start + 1900],
                        mention_author=False,
                    )

            except Exception as error:
                logging.exception("AI chat request failed")
                error_text = str(error).lower()

                if "check-in" in error_text or "check in" in error_text:
                    user_message = (
                        "Free AI access needs today's account check-in. "
                        "Please ask the account administrator to complete it."
                    )
                elif "429" in error_text or "rate limit" in error_text:
                    user_message = (
                        "The free AI request limit is currently reached "
                        "or another request is still running. Please try later."
                    )
                elif "text only" in error_text or "image" in error_text:
                    user_message = (
                        "This model could not process the attached image. "
                        "Please try a text message or use an image-capable model."
                    )
                else:
                    user_message = (
                        "I couldn't answer right now. The AI service may be "
                        "busy, the daily limit may be reached, or the API "
                        "configuration may be incorrect."
                    )

                await message.reply(user_message)

    @commands.command(name="aiimage")
    @commands.guild_only()
    async def create_image(self, ctx, *, prompt: str = ""):
        await ctx.reply(
            "Image generation is not available through the free chat model. "
            "Text chat and image understanding are supported."
        )


async def setup(bot):
    await bot.add_cog(AICog(bot))
