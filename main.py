
from __future__ import annotations

import os
import re
import json
import difflib
import asyncio
from pathlib import Path
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands


# =========================
# CONFIGURATION
# =========================

OWNER_ID = 1176149190192152626
SUGGESTIONS_CHANNEL_ID = 1546116339922501682

DATA_FILE = Path(
    os.getenv("SUGGESTIONS_DATA_FILE", "suggestions.json")
)

MAX_LENGTH = 1000
COOLDOWN = 600
MAX_DAILY = 3
SIMILARITY_LIMIT = 0.65
PAGE_SIZE = 5

STATUSES = ("Pending", "Accepted", "Rejected")

DATA = {
    "next_id": 1,
    "suggestions": {},
    "last_submit": {},
    "submit_dates": {},
}

LOCK = asyncio.Lock()


# =========================
# STORAGE
# =========================

def load_data():
    global DATA

    if not DATA_FILE.exists():
        save_data()
        return

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            loaded = json.load(file)

        if isinstance(loaded, dict):
            DATA.update(loaded)

        DATA.setdefault("next_id", 1)
        DATA.setdefault("suggestions", {})
        DATA.setdefault("last_submit", {})
        DATA.setdefault("submit_dates", {})

    except (OSError, json.JSONDecodeError):
        print("[Suggest] Could not load suggestions.json")


def save_data():
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    temporary = DATA_FILE.with_suffix(".tmp")

    with temporary.open("w", encoding="utf-8") as file:
        json.dump(DATA, file, ensure_ascii=False, indent=2)

    temporary.replace(DATA_FILE)


def now():
    return datetime.now(timezone.utc)


def timestamp(value=None):
    value = value or now()
    return value.isoformat()


def parse_date(value):
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return now()


def get_suggestion(suggestion_id):
    return DATA["suggestions"].get(str(suggestion_id))


def active_suggestions():
    return [
        suggestion
        for suggestion in DATA["suggestions"].values()
        if not suggestion.get("deleted", False)
    ]


def display_status(status):
    if status == "Accepted":
        return "✅ Accepted"
    if status == "Rejected":
        return "❌ Rejected"
    return "🕒 Pending"


def shorten(value, limit=180):
    value = str(value)
    return value if len(value) <= limit else value[:limit - 3] + "..."


def normalize_text(value):
    value = value.lower().strip()
    value = re.sub(r"<@!?\d+>", "", value)
    value = re.sub(r"\s+", " ", value)
    return value


# =========================
# EMBEDS
# =========================

def make_embed(suggestion):
    suggestion_id = int(suggestion["id"])

    embed = discord.Embed(
        title=f"💡 Suggestion #{suggestion_id:03d}",
        description=suggestion["text"],
        color=(
            discord.Color.green()
            if suggestion["status"] == "Accepted"
            else discord.Color.red()
            if suggestion["status"] == "Rejected"
            else discord.Color.blurple()
        ),
        timestamp=parse_date(suggestion["created_at"]),
    )

    embed.add_field(
        name="Author",
        value=f"<@{suggestion['author_id']}>",
        inline=True,
    )

    embed.add_field(
        name="Status",
        value=display_status(suggestion["status"]),
        inline=True,
    )

    embed.add_field(
        name="Edited",
        value="Yes" if suggestion.get("edited") else "No",
        inline=True,
    )

    votes = suggestion.get("votes", {})
    upvotes = sum(1 for vote in votes.values() if vote == "for")
    downvotes = sum(1 for vote in votes.values() if vote == "against")

    embed.add_field(
        name="Community Votes",
        value=f"👍 {upvotes}  ·  👎 {downvotes}",
        inline=False,
    )

    comments = suggestion.get("comments", [])

    if comments:
        embed.add_field(
            name="Owner Comment",
            value=shorten(comments[-1], 1000),
            inline=False,
        )

    embed.set_footer(text="Suggestion System")

    return embed


def make_vote_embed(suggestion):
    votes = suggestion.get("votes", {})
    upvotes = sum(1 for vote in votes.values() if vote == "for")
    downvotes = sum(1 for vote in votes.values() if vote == "against")

    return discord.Embed(
        title=f"🗳️ Vote on Suggestion #{int(suggestion['id']):03d}",
        description=(
            f"👍 **For:** {upvotes}\n"
            f"👎 **Against:** {downvotes}\n\n"
            "Each member can vote once. Votes cannot be changed."
        ),
        color=discord.Color.blurple(),
    )


async def get_suggestion_channel(bot):
    channel = bot.get_channel(SUGGESTIONS_CHANNEL_ID)

    if channel is None:
        try:
            channel = await bot.fetch_channel(SUGGESTIONS_CHANNEL_ID)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    return channel if hasattr(channel, "send") else None


async def refresh_suggestion(bot, suggestion):
    channel = await get_suggestion_channel(bot)

    if channel is None:
        return

    main_message_id = suggestion.get("message_id")
    vote_message_id = suggestion.get("vote_message_id")

    if main_message_id:
        try:
            message = await channel.fetch_message(int(main_message_id))
            await message.edit(
                embed=make_embed(suggestion),
                view=SuggestionView(int(suggestion["id"])),
            )
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass

    if vote_message_id:
        try:
            message = await channel.fetch_message(int(vote_message_id))
            await message.edit(
                embed=make_vote_embed(suggestion),
                view=VoteView(
                    int(suggestion["id"]),
                    disabled=suggestion["status"] != "Pending",
                ),
            )
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass


# =========================
# LIMITS AND SIMILAR IDEAS
# =========================

def check_limits(user_id):
    key = str(user_id)
    current = now()

    last_value = DATA["last_submit"].get(key)

    if last_value:
        last_submit = parse_date(last_value)
        elapsed = (current - last_submit).total_seconds()

        if elapsed < COOLDOWN:
            remaining = int(COOLDOWN - elapsed)
            minutes = remaining // 60
            seconds = remaining % 60

            return (
                "⏳ Please wait "
                f"**{minutes}m {seconds}s** before submitting another suggestion."
            )

    today = current.date().isoformat()
    dates = DATA["submit_dates"].get(key, [])

    dates = [
        value for value in dates
        if value == today
    ]

    DATA["submit_dates"][key] = dates

    if len(dates) >= MAX_DAILY:
        return f"❌ You can submit up to **{MAX_DAILY} suggestions per day**."

    return None


def find_similar(text):
    normalized = normalize_text(text)
    matches = []

    for suggestion in active_suggestions():
        if suggestion["status"] != "Pending":
            continue

        existing = normalize_text(suggestion["text"])

        ratio = difflib.SequenceMatcher(
            None,
            normalized,
            existing,
        ).ratio()

        if ratio >= SIMILARITY_LIMIT:
            matches.append((ratio, suggestion))

    matches.sort(key=lambda item: item[0], reverse=True)

    return [suggestion for _, suggestion in matches[:3]]


# =========================
# PUBLISH SUGGESTION
# =========================

async def publish_suggestion(bot, user, text_value):
    channel = await get_suggestion_channel(bot)

    if channel is None:
        return None

    suggestion_id = int(DATA["next_id"])

    suggestion = {
        "id": suggestion_id,
        "author_id": user.id,
        "text": text_value,
        "status": "Pending",
        "votes": {},
        "comments": [],
        "created_at": timestamp(),
        "edited": False,
        "deleted": False,
        "message_id": None,
        "vote_message_id": None,
    }

    DATA["next_id"] = suggestion_id + 1
    DATA["suggestions"][str(suggestion_id)] = suggestion

    try:
        main_message = await channel.send(
            embed=make_embed(suggestion),
            view=SuggestionView(suggestion_id),
        )

        suggestion["message_id"] = main_message.id

        vote_message = await channel.send(
            embed=make_vote_embed(suggestion),
            view=VoteView(suggestion_id),
        )

        suggestion["vote_message_id"] = vote_message.id

    except (discord.Forbidden, discord.HTTPException):
        DATA["suggestions"].pop(str(suggestion_id), None)
        DATA["next_id"] = suggestion_id
        save_data()
        return None

    key = str(user.id)
    today = now().date().isoformat()

    DATA["last_submit"][key] = timestamp()

    dates = DATA["submit_dates"].setdefault(key, [])
    dates.append(today)

    save_data()

    try:
        await user.send(
            f"✅ Your suggestion **#{suggestion_id:03d}** "
            "has been submitted successfully."
        )
    except discord.Forbidden:
        pass

    return suggestion_id


# =========================
# VOTING
# =========================

class VoteView(discord.ui.View):
    def __init__(self, suggestion_id, disabled=False):
        super().__init__(timeout=None)

        self.suggestion_id = suggestion_id

        for label, vote_type, emoji in (
            ("Vote For", "for", "👍"),
            ("Vote Against", "against", "👎"),
        ):
            button = discord.ui.Button(
                label=label,
                emoji=emoji,
                style=(
                    discord.ButtonStyle.success
                    if vote_type == "for"
                    else discord.ButtonStyle.danger
                ),
                custom_id=f"suggest:vote:{vote_type}:{suggestion_id}",
                disabled=disabled,
            )

            async def callback(interaction, selected=vote_type):
                await self.cast_vote(interaction, selected)

            button.callback = callback
            self.add_item(button)

    async def cast_vote(self, interaction, vote_type):
        suggestion = get_suggestion(self.suggestion_id)

        if not suggestion or suggestion.get("deleted"):
            await interaction.response.send_message(
                "❌ This suggestion is no longer available.",
                ephemeral=True,
            )
            return

        if suggestion["status"] != "Pending":
            await interaction.response.send_message(
                "❌ Voting is closed for this suggestion.",
                ephemeral=True,
            )
            return

        if interaction.user.id == int(suggestion["author_id"]):
            await interaction.response.send_message(
                "❌ You cannot vote on your own suggestion.",
                ephemeral=True,
            )
            return

        votes = suggestion.setdefault("votes", {})
        user_key = str(interaction.user.id)

        if user_key in votes:
            await interaction.response.send_message(
                "❌ You have already voted. Your vote cannot be changed.",
                ephemeral=True,
            )
            return

        async with LOCK:
            votes[user_key] = vote_type
            save_data()

        await interaction.response.send_message(
            "✅ Your vote has been recorded.",
            ephemeral=True,
        )

        await refresh_suggestion(interaction.client, suggestion)


# =========================
# SUGGESTION ACTION BUTTONS
# =========================

class SuggestionView(discord.ui.View):
    def __init__(self, suggestion_id):
        super().__init__(timeout=None)
        self.suggestion_id = suggestion_id

    async def interaction_check(self, interaction):
        suggestion = get_suggestion(self.suggestion_id)

        if not suggestion or suggestion.get("deleted"):
            await interaction.response.send_message(
                "❌ This suggestion is no longer available.",
                ephemeral=True,
            )
            return False

        return True

    @discord.ui.button(
        label="Edit",
        emoji="✏️",
        style=discord.ButtonStyle.primary,
        custom_id="suggest:edit",
    )
    async def edit_button(self, interaction, button):
        suggestion = get_suggestion(self.suggestion_id)

        if interaction.user.id != int(suggestion["author_id"]):
            await interaction.response.send_message(
                "❌ Only the author can edit this suggestion.",
                ephemeral=True,
            )
            return

        if suggestion["status"] != "Pending":
            await interaction.response.send_message(
                "❌ Only pending suggestions can be edited.",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(
            EditSuggestionModal(self.suggestion_id)
        )

    @discord.ui.button(
        label="Delete",
        emoji="🗑️",
        style=discord.ButtonStyle.danger,
        custom_id="suggest:delete",
    )
    async def delete_button(self, interaction, button):
        suggestion = get_suggestion(self.suggestion_id)

        if (
            interaction.user.id != int(suggestion["author_id"])
            and interaction.user.id != OWNER_ID
        ):
            await interaction.response.send_message(
                "❌ You cannot delete this suggestion.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            "Are you sure you want to delete this suggestion?",
            view=DeleteConfirmView(self.suggestion_id, interaction.user.id),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Accept",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="suggest:accept",
    )
    async def accept_button(self, interaction, button):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                "❌ Only the bot owner can accept suggestions.",
                ephemeral=True,
            )
            return

        suggestion = get_suggestion(self.suggestion_id)

        if suggestion["status"] != "Pending":
            await interaction.response.send_message(
                "This suggestion has already been reviewed.",
                ephemeral=True,
            )
            return

        async with LOCK:
            suggestion["status"] = "Accepted"
            save_data()

        await interaction.response.send_message(
            "✅ Suggestion accepted.",
            ephemeral=True,
        )

        await refresh_suggestion(interaction.client, suggestion)
        await notify_author(interaction.client, suggestion, "Accepted")

    @discord.ui.button(
        label="Reject",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="suggest:reject",
    )
    async def reject_button(self, interaction, button):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                "❌ Only the bot owner can reject suggestions.",
                ephemeral=True,
            )
            return

        suggestion = get_suggestion(self.suggestion_id)

        if suggestion["status"] != "Pending":
            await interaction.response.send_message(
                "This suggestion has already been reviewed.",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(
            RejectSuggestionModal(self.suggestion_id)
        )

    @discord.ui.button(
        label="Comment",
        emoji="💬",
        style=discord.ButtonStyle.secondary,
        custom_id="suggest:comment",
    )
    async def comment_button(self, interaction, button):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                "❌ Only the bot owner can comment.",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(
            OwnerCommentModal(self.suggestion_id)
        )


async def notify_author(bot, suggestion, status):
    try:
        user = await bot.fetch_user(int(suggestion["author_id"]))

        await user.send(
            f"📢 Your suggestion **#{int(suggestion['id']):03d}** "
            f"has been **{status.lower()}**."
        )
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass


# =========================
# EDIT MODAL
# =========================

class EditSuggestionModal(discord.ui.Modal):
    def __init__(self, suggestion_id):
        super().__init__(title="Edit Suggestion")

        self.suggestion_id = suggestion_id
        suggestion = get_suggestion(suggestion_id)

        self.text_input = discord.ui.TextInput(
            label="Suggestion",
            style=discord.TextStyle.paragraph,
            max_length=MAX_LENGTH,
            required=True,
            default=suggestion["text"] if suggestion else "",
        )

        self.add_item(self.text_input)

    async def on_submit(self, interaction):
        suggestion = get_suggestion(self.suggestion_id)

        if not suggestion or suggestion.get("deleted"):
            await interaction.response.send_message(
                "❌ Suggestion not found.",
                ephemeral=True,
            )
            return

        if interaction.user.id != int(suggestion["author_id"]):
            await interaction.response.send_message(
                "❌ Only the author can edit this suggestion.",
                ephemeral=True,
            )
            return

        if suggestion["status"] != "Pending":
            await interaction.response.send_message(
                "❌ Only pending suggestions can be edited.",
                ephemeral=True,
            )
            return

        new_text = self.text_input.value.strip()

        if not new_text:
            await interaction.response.send_message(
                "❌ The suggestion cannot be empty.",
                ephemeral=True,
            )
            return

        async with LOCK:
            suggestion["text"] = new_text
            suggestion["edited"] = True
            save_data()

        await interaction.response.send_message(
            "✅ Your suggestion has been updated.",
            ephemeral=True,
        )

        await refresh_suggestion(interaction.client, suggestion)


# =========================
# DELETE CONFIRMATION
# =========================

class DeleteConfirmView(discord.ui.View):
    def __init__(self, suggestion_id, requester_id):
        super().__init__(timeout=60)
        self.suggestion_id = suggestion_id
        self.requester_id = requester_id

    @discord.ui.button(
        label="Confirm Delete",
        style=discord.ButtonStyle.danger,
    )
    async def confirm(self, interaction, button):
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message(
                "❌ This confirmation belongs to another user.",
                ephemeral=True,
            )
            return

        suggestion = get_suggestion(self.suggestion_id)

        if not suggestion:
            await interaction.response.edit_message(
                content="Suggestion not found.",
                view=None,
            )
            return

        async with LOCK:
            suggestion["deleted"] = True
            save_data()

        await interaction.response.edit_message(
            content="🗑️ Suggestion deleted.",
            view=None,
        )

        channel = await get_suggestion_channel(interaction.client)

        if channel:
            for key in ("message_id", "vote_message_id"):
                message_id = suggestion.get(key)

                if message_id:
                    try:
                        message = await channel.fetch_message(int(message_id))
                        await message.delete()
                    except (
                        discord.NotFound,
                        discord.Forbidden,
                        discord.HTTPException,
                    ):
                        pass

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
    )
    async def cancel(self, interaction, button):
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message(
                "❌ This confirmation belongs to another user.",
                ephemeral=True,
            )
            return

        await interaction.response.edit_message(
            content="Deletion cancelled.",
            view=None,
        )


# =========================
# OWNER REJECTION MODAL
# =========================

class RejectSuggestionModal(discord.ui.Modal):
    def __init__(self, suggestion_id):
        super().__init__(title="Reject Suggestion")
        self.suggestion_id = suggestion_id

        self.reason = discord.ui.TextInput(
            label="Reason (optional)",
            placeholder="Explain why this suggestion was rejected...",
            required=False,
            max_length=500,
            style=discord.TextStyle.paragraph,
        )

        self.add_item(self.reason)

    async def on_submit(self, interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                "❌ Only the bot owner can reject suggestions.",
                ephemeral=True,
            )
            return

        suggestion = get_suggestion(self.suggestion_id)

        if not suggestion:
            await interaction.response.send_message(
                "Suggestion not found.",
                ephemeral=True,
            )
            return

        if suggestion["status"] != "Pending":
            await interaction.response.send_message(
                "This suggestion has already been reviewed.",
                ephemeral=True,
            )
            return

        async with LOCK:
            suggestion["status"] = "Rejected"

            reason = self.reason.value.strip()
            if reason:
                suggestion.setdefault("comments", []).append(
                    f"Rejection reason: {reason}"
                )

            save_data()

        await interaction.response.send_message(
            "❌ Suggestion rejected.",
            ephemeral=True,
        )

        await refresh_suggestion(interaction.client, suggestion)
        await notify_author(interaction.client, suggestion, "Rejected")


# =========================
# OWNER COMMENT MODAL
# =========================

class OwnerCommentModal(discord.ui.Modal):
    def __init__(self, suggestion_id):
        super().__init__(title="Comment on Suggestion")
        self.suggestion_id = suggestion_id

        self.comment = discord.ui.TextInput(
            label="Comment",
            placeholder="Write your comment...",
            required=True,
            max_length=1000,
            style=discord.TextStyle.paragraph,
        )

        self.add_item(self.comment)

    async def on_submit(self, interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                "❌ Only the bot owner can comment.",
                ephemeral=True,
            )
            return

        suggestion = get_suggestion(self.suggestion_id)

        if not suggestion:
            await interaction.response.send_message(
                "Suggestion not found.",
                ephemeral=True,
            )
            return

        async with LOCK:
            suggestion.setdefault("comments", []).append(
                self.comment.value.strip()
            )
            save_data()

        await interaction.response.send_message(
            "💬 Comment added.",
            ephemeral=True,
        )

        await refresh_suggestion(interaction.client, suggestion)

        try:
            user = await interaction.client.fetch_user(
                int(suggestion["author_id"])
            )
            await user.send(
                f"💬 The owner commented on suggestion "
                f"**#{int(suggestion['id']):03d}**:\n"
                f"{self.comment.value.strip()}"
            )
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass


# =========================
# NEW SUGGESTION MODAL
# =========================

class SuggestionModal(discord.ui.Modal):
    def __init__(self, bot):
        super().__init__(title="Submit a Suggestion")
        self.bot = bot

        self.text_input = discord.ui.TextInput(
            label="Your suggestion",
            placeholder="Describe your idea...",
            style=discord.TextStyle.paragraph,
            min_length=5,
            max_length=MAX_LENGTH,
            required=True,
        )

        self.add_item(self.text_input)

    async def on_submit(self, interaction):
        text_value = self.text_input.value.strip()

        if len(text_value) < 5:
            await interaction.response.send_message(
                "❌ Please write at least 5 characters.",
                ephemeral=True,
            )
            return

        async with LOCK:
            error = check_limits(interaction.user.id)

        if error:
            await interaction.response.send_message(
                error,
                ephemeral=True,
            )
            return

        similar = find_similar(text_value)

        if similar:
            embed = discord.Embed(
                title="⚠️ Similar Suggestions Found",
                description=(
                    "Your idea looks similar to an existing suggestion.\n"
                    "You can review the matches or submit it anyway."
                ),
                color=discord.Color.orange(),
            )

            for suggestion in similar:
                embed.add_field(
                    name=(
                        f"Suggestion "
                        f"#{int(suggestion['id']):03d}"
                    ),
                    value=shorten(suggestion["text"], 400),
                    inline=False,
                )

            await interaction.response.send_message(
                embed=embed,
                view=SimilarView(
                    self.bot,
                    interaction.user.id,
                    text_value,
                ),
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        async with LOCK:
            error = check_limits(interaction.user.id)

            if error:
                save_data()
                await interaction.followup.send(
                    error,
                    ephemeral=True,
                )
                return

            suggestion_id = await publish_suggestion(
                self.bot,
                interaction.user,
                text_value,
            )

        if suggestion_id is None:
            await interaction.followup.send(
                "❌ Could not publish your suggestion. "
                "Please try again later.",
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            f"✅ Your suggestion **#{suggestion_id:03d}** was submitted!",
            ephemeral=True,
        )


# =========================
# SIMILAR SUGGESTIONS VIEW
# =========================

class SimilarView(discord.ui.View):
    def __init__(self, bot, author_id, text_value):
        super().__init__(timeout=180)
        self.bot = bot
        self.author_id = author_id
        self.text_value = text_value

    @discord.ui.button(
        label="Submit Anyway",
        style=discord.ButtonStyle.success,
    )
    async def submit_anyway(self, interaction, button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ This confirmation belongs to another user.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        async with LOCK:
            error = check_limits(interaction.user.id)

            if error:
                save_data()
                await interaction.followup.send(
                    error,
                    ephemeral=True,
                )
                return

            suggestion_id = await publish_suggestion(
                self.bot,
                interaction.user,
                self.text_value,
            )

        if suggestion_id is None:
            await interaction.followup.send(
                "❌ I couldn't submit your suggestion. "
                "Please try again later.",
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            f"✅ Your suggestion **#{suggestion_id:03d}** has been submitted!",
            ephemeral=True,
        )

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
    )
    async def cancel(self, interaction, button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ This confirmation belongs to another user.",
                ephemeral=True,
            )
            return

        await interaction.response.edit_message(
            content="Submission cancelled.",
            embed=None,
            view=None,
        )


# =========================
# OPEN SUGGESTION FORM
# =========================

class SuggestEntryView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot

    @discord.ui.button(
        label="Create Suggestion",
        emoji="💡",
        style=discord.ButtonStyle.primary,
    )
    async def create_suggestion(self, interaction, button):
        await interaction.response.send_modal(
            SuggestionModal(self.bot)
        )


# =========================
# MY SUGGESTIONS PAGINATION
# =========================

class MineView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.page = 0
        self.entries = []
        self.update_entries()

    def update_entries(self):
        self.entries = sorted(
            [
                suggestion
                for suggestion in active_suggestions()
                if int(suggestion["author_id"]) == self.user_id
            ],
            key=lambda item: int(item["id"]),
            reverse=True,
        )

    def make_page_embed(self):
        self.update_entries()

        pages = max(
            1,
            (len(self.entries) + PAGE_SIZE - 1) // PAGE_SIZE,
        )

        self.page = max(0, min(self.page, pages - 1))

        start = self.page * PAGE_SIZE
        current = self.entries[start:start + PAGE_SIZE]

        embed = discord.Embed(
            title="📋 My Suggestions",
            description=(
                f"Page **{self.page + 1}/{pages}**\n"
                f"Total suggestions: **{len(self.entries)}**"
            ),
            color=discord.Color.blurple(),
        )

        if not current:
            embed.add_field(
                name="No suggestions",
                value="You haven't submitted any suggestions yet.",
                inline=False,
            )
        else:
            for suggestion in current:
                embed.add_field(
                    name=(
                        f"#{int(suggestion['id']):03d} · "
                        f"{display_status(suggestion['status'])}"
                    ),
                    value=shorten(suggestion["text"], 250),
                    inline=False,
                )

        self.previous.disabled = self.page <= 0
        self.next.disabled = self.page >= pages - 1

        return embed

    async def interaction_check(self, interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ This menu belongs to another user.",
                ephemeral=True,
            )
            return False

        return True

    @discord.ui.button(
        label="Previous",
        emoji="◀️",
        style=discord.ButtonStyle.secondary,
    )
    async def previous(self, interaction, button):
        self.page -= 1

        await interaction.response.edit_message(
            embed=self.make_page_embed(),
            view=self,
        )

    @discord.ui.button(
        label="Next",
        emoji="▶️",
        style=discord.ButtonStyle.secondary,
    )
    async def next(self, interaction, button):
        self.page += 1

        await interaction.response.edit_message(
            embed=self.make_page_embed(),
            view=self,
        )


# =========================
# PREFIX HANDLER: ? ONLY
# =========================

class SuggestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.strip().lower()

        if content not in {
            "?suggest",
            "?suggest help",
            "?suggest mine",
        }:
            return

        try:
            await message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass

        try:
            if content == "?suggest":
                await message.author.send(
                    "💡 **Create a Suggestion**\n"
                    "Press the button below to submit your idea.",
                    view=SuggestEntryView(self.bot),
                )

            elif content == "?suggest help":
                embed = discord.Embed(
                    title="💡 Suggestion Help",
                    description=(
                        "`?suggest` — create a suggestion\n"
                        "`?suggest mine` — view your suggestions\n"
                        "`?suggest help` — show this help message"
                    ),
                    color=discord.Color.blurple(),
                )

                await message.author.send(embed=embed)

            elif content == "?suggest mine":
                view = MineView(message.author.id)

                await message.author.send(
                    embed=view.make_page_embed(),
                    view=view,
                )

        except discord.Forbidden:
            try:
                await message.channel.send(
                    "❌ Enable Direct Messages from server members "
                    "and try again.",
                    delete_after=10,
                )
            except discord.HTTPException:
                pass


# =========================
# EXTENSION SETUP
# =========================

async def setup(bot):
    load_data()

    await bot.add_cog(SuggestCog(bot))

    for suggestion in active_suggestions():
        suggestion_id = int(suggestion["id"])

        message_id = suggestion.get("message_id")
        if message_id:
            bot.add_view(
                SuggestionView(suggestion_id),
                message_id=int(message_id),
            )

        vote_message_id = suggestion.get("vote_message_id")
        if vote_message_id:
            bot.add_view(
                VoteView(
                    suggestion_id,
                    disabled=suggestion["status"] != "Pending",
                ),
                message_id=int(vote_message_id),
            )
