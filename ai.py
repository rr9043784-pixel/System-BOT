
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

CHAT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")

MAX_IMAGE_SIZE = 8 * 1024 * 1024
MAX_HISTORY_MESSAGES = 12

SYSTEM_PROMPT = """
You are a helpful AI assistant inside a Discord server.
Respond in the same language as the user.
You can help with programming, education, translations,
ideas, writing, and questions about uploaded images.
Be accurate and honest. If you do not know, say so.
Never claim to have created an image unless you did.
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
            "content": content,
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

        # Retain recent context without growing forever.
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

    safe_name = (safe_name[:35] or "user")
    channel_name = f"ai-{safe_name}"

    channel = await guild.create_text_channel(
        name=channel_name,
        category=category,
        overwrites=overwrites,
        topic=f"Private AI chat for user ID {user.id}",
        reason="Creating a private OpenAI chat",
    )

    register_chat(
        channel.id,
        user.id,
        guild.id,
        channel.name,
    )

    await channel.send(
        f"**AI Chat**\n"
        f"Welcome, {user.mention}!\n\n"
        "Send a message to start chatting. You can also attach "
        "an image and ask questions about it.\n\n"
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
            options = []

            for chat in page_chats:
                options.append(discord.SelectOption(
                    label=chat["channel_name"][:100],
                    value=str(chat["channel_id"]),
                    description=f"Chat ID: {chat['channel_id']}",
                ))

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
            (len(self.chats) + self.PAGE_SIZE - 1)
            // self.PAGE_SIZE,
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
        api_key = os.getenv("OPENAI_API_KEY")

        self.client = (
            AsyncOpenAI(api_key=api_key)
            if api_key else None
        )

    async def cog_load(self):
        init_db()

        if self.client is None:
            logging.error(
                "OPENAI_API_KEY is missing. AI chat will not work."
            )
        else:
            logging.info("OpenAI client initialized.")

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
            title="OpenAI Assistant",
            description=(
                "Chat with AI, ask questions, analyze images, "
                "and create images.\n\n"
                "**Features**\n"
                "• Private chat channels\n"
                "• Saved chat history\n"
                "• Image understanding\n"
                "• Image generation\n"
                "• Multiple languages\n\n"
                "Video processing is not supported."
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

        attachments = list(message.attachments)
        image_attachments = []
        unsupported = []

        for attachment in attachments:
            content_type = attachment.content_type or ""

            if content_type.startswith("image/"):
                image_attachments.append(attachment)
            else:
                # Includes video and other non-image files.
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

        user_content = [{
            "type": "input_text",
            "text": message.content.strip() or "Describe this image.",
        }]

        for attachment in image_attachments[:3]:
            if attachment.size > MAX_IMAGE_SIZE:
                await message.reply(
                    f"`{attachment.filename}` is too large. "
                    "Maximum image size is 8 MB."
                )
                return

            try:
                raw = await attachment.read()
                encoded = base64.b64encode(raw).decode("ascii")
                mime = attachment.content_type or "image/png"

                user_content.append({
                    "type": "input_image",
                    "image_url": f"data:{mime};base64,{encoded}",
                })

            except Exception:
                logging.exception("Failed to read image attachment")
                await message.reply("I could not read that image.")
                return

        save_history_message(
            message.channel.id,
            "user",
            user_content,
        )

        history = load_history(message.channel.id)

        async with message.channel.typing():
            try:
                response = await self.client.responses.create(
                    model=CHAT_MODEL,
                    instructions=SYSTEM_PROMPT,
                    input=history,
                    max_output_tokens=1500,
                )

                answer = response.output_text or (
                    "I could not generate a response."
                )

                save_history_message(
                    message.channel.id,
                    "assistant",
                    answer,
                )

                # Discord message limit is 2000 characters.
                for start in range(0, len(answer), 1900):
                    await message.reply(
                        answer[start:start + 1900],
                        mention_author=False,
                    )

            except Exception:
                logging.exception("OpenAI chat request failed")

                await message.reply(
                    "I couldn't answer right now. Check the API key, "
                    "API billing, and model access."
                )

    @commands.command(name="aiimage")
    @commands.guild_only()
    async def create_image(self, ctx, *, prompt: str):
        if self.client is None:
            await ctx.reply("AI is not configured.")
            return

        if not prompt.strip():
            await ctx.reply(
                "Example: `!aiimage a fantasy treasure chest`"
            )
            return

        async with ctx.typing():
            try:
                result = await self.client.images.generate(
                    model=IMAGE_MODEL,
                    prompt=prompt,
                    size="1024x1024",
                )

                encoded = result.data[0].b64_json

                if not encoded:
                    await ctx.reply(
                        "No image was returned by the image service."
                    )
                    return

                image_bytes = base64.b64decode(encoded)

                file = discord.File(
                    io.BytesIO(image_bytes),
                    filename="ai_image.png",
                )

                await ctx.reply(
                    content=f"**Generated image:** {prompt[:500]}",
                    file=file,
                    mention_author=False,
                )

            except Exception:
                logging.exception("Image generation failed")
                await ctx.reply(
                    "Image generation failed. Check API billing, "
                    "image model availability, and permissions."
                )


async def setup(bot):
    await bot.add_cog(AICog(bot))
