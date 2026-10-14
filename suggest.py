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

# Requires discord.py 2.6.0+ for Component V2 LayoutView.
OWNER_ID = 1176149190192152626
SUGGESTIONS_CHANNEL_ID = 1546116339922501682
DATA_FILE = Path(os.getenv("SUGGESTIONS_DATA_FILE", "suggestions.json"))

MAX_LENGTH = 1000
COOLDOWN = 600
MAX_DAILY = 3
MINE_DAYS = 14
PAGE_SIZE = 5

DATA = {
    "next_id": 1,
    "suggestions": {},
    "last_submit": {},
    "submit_dates": {},
}
LOCK = asyncio.Lock()


def load_data():
    global DATA
    if DATA_FILE.exists():
        try:
            saved = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                DATA.update(saved)
        except (json.JSONDecodeError, OSError):
            pass
    DATA.setdefault("next_id", 1)
    DATA.setdefault("suggestions", {})
    DATA.setdefault("last_submit", {})
    DATA.setdefault("submit_dates", {})
    for s in DATA["suggestions"].values():
        s.setdefault("votes_for", [])
        s.setdefault("votes_against", [])
        s.setdefault("comments", [])
        s.setdefault("reject_reason", None)
        s.setdefault("deleted", False)
        s.setdefault("message_id", None)


def save_data():
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = DATA_FILE.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(DATA, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(DATA_FILE)


def now():
    return datetime.now(timezone.utc)


def timestamp():
    return now().isoformat()


def parse_date(value):
    if not value:
        return None
    try:
        result = datetime.fromisoformat(value)
        return result if result.tzinfo else result.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def get_suggestion(suggestion_id):
    return DATA["suggestions"].get(str(suggestion_id))


def display_status(status):
    return {
        "Pending": "🟡 Pending",
        "Accepted": "✅ Accepted",
        "Rejected": "❌ Rejected",
        "Deleted": "🗑️ Deleted",
    }.get(status, status)


def shorten(text, limit=200):
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[:limit - 1] + "…"


def make_suggestion_view(suggestion_id):
    return SuggestionView(suggestion_id)


async def get_suggestion_channel(bot):
    channel = bot.get_channel(SUGGESTIONS_CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(SUGGESTIONS_CHANNEL_ID)
        except (discord.HTTPException, discord.Forbidden, discord.NotFound):
            return None
    return channel


async def send_dm(bot, user_id, message):
    try:
        user = bot.get_user(int(user_id))
        if user is None:
            user = await bot.fetch_user(int(user_id))
        await user.send(message)
    except (discord.HTTPException, discord.Forbidden, discord.NotFound):
        pass


def suggestion_body(s):
    status = display_status(s["status"])
    text = s["text"]
    if s.get("deleted"):
        text = "*This suggestion has been deleted.*"

    lines = [
        f"## 💡 Suggestion #{int(s['id']):03d}",
        f"**Author:** <@{s['author_id']}>",
        f"**Status:** {status}",
        "",
        text,
        "",
        f"**👍 For:** {len(s['votes_for'])}  •  **👎 Against:** {len(s['votes_against'])}",
    ]

    if s.get("edited"):
        lines.append("✏️ *Edited*")
    if s.get("reject_reason"):
        lines.extend(["", f"**Rejection reason:** {s['reject_reason']}"])
    comments = s.get("comments", [])
    if comments:
        lines.extend(["", "### 💬 Owner Comments"])
        for item in comments[-3:]:
            date = parse_date(item.get("date"))
            date_text = discord.utils.format_dt(date, style="d") if date else ""
            lines.append(f"**Owner** {date_text}\n{item['text']}")
    lines.extend(["", "-# RULL Suggestions"])
    return "\n".join(lines)


async def refresh_suggestion(bot, s):
    channel = await get_suggestion_channel(bot)
    if channel is None or not s.get("message_id"):
        return
    try:
        message = await channel.fetch_message(int(s["message_id"]))
        await message.edit(view=SuggestionView(int(s["id"])))
    except (discord.HTTPException, discord.Forbidden, discord.NotFound):
        pass


def find_similar(text):
    normalized = re.sub(r"\W+", " ", text.lower()).strip()
    matches = []
    for key, s in DATA["suggestions"].items():
        if s.get("deleted") or s.get("status") == "Rejected":
            continue
        other = re.sub(r"\W+", " ", s.get("text", "").lower()).strip()
        if not other:
            continue
        score = difflib.SequenceMatcher(None, normalized, other).ratio()
        if score >= 0.62:
            matches.append((int(key), score))
    matches.sort(key=lambda item: item[1], reverse=True)
    return matches[0][0] if matches else None


def check_limits(user_id):
    key = str(user_id)
    current = now()
    last = parse_date(DATA["last_submit"].get(key))
    if last:
        elapsed = (current - last).total_seconds()
        if elapsed < COOLDOWN:
            remaining = int(COOLDOWN - elapsed)
            return (
                f"Please wait **{remaining // 60}m "
                f"{remaining % 60}s** before submitting again."
            )

    cutoff = current - timedelta(hours=24)
    dates = DATA["submit_dates"].get(key, [])
    recent = [
        value for value in dates
        if parse_date(value) and parse_date(value) > cutoff
    ]
    DATA["submit_dates"][key] = recent
    if len(recent) >= MAX_DAILY:
        return "You can submit up to **3 suggestions per 24 hours**."
    return None


async def publish_suggestion(bot, user, text):
    channel = await get_suggestion_channel(bot)
    if channel is None or not hasattr(channel, "send"):
        return None

    sid = int(DATA["next_id"])
    DATA["next_id"] = sid + 1
    s = {
        "id": sid,
        "author_id": user.id,
        "text": text,
        "status": "Pending",
        "created_at": timestamp(),
        "edited": False,
        "votes_for": [],
        "votes_against": [],
        "comments": [],
        "reject_reason": None,
        "message_id": None,
        "deleted": False,
    }
    DATA["suggestions"][str(sid)] = s
    key = str(user.id)
    DATA["last_submit"][key] = timestamp()
    DATA["submit_dates"].setdefault(key, []).append(timestamp())
    save_data()

    try:
        message = await channel.send(view=SuggestionView(sid))
        s["message_id"] = message.id
        save_data()
    except discord.HTTPException:
        save_data()
        return None

    await send_dm(
        bot,
        OWNER_ID,
        f"📩 New suggestion **#{sid:03d}**\n"
        f"Author: {user} (`{user.id}`)\n\n{text}",
    )
    return sid


class SuggestionView(discord.ui.LayoutView):
    """Single Component V2 message containing author, voting, and admin controls."""

    def __init__(self, suggestion_id: int):
        super().__init__(timeout=None)
        self.suggestion_id = int(suggestion_id)
        s = get_suggestion(self.suggestion_id)
        if not s:
            s = {
                "id": self.suggestion_id, "author_id": 0, "text": "Suggestion unavailable.",
                "status": "Deleted", "votes_for": [], "votes_against": [],
                "comments": [], "deleted": True,
            }

        active = s.get("status") == "Pending" and not s.get("deleted")

        edit = discord.ui.Button(
            label="Edit", emoji="✏️", style=discord.ButtonStyle.primary,
            custom_id=f"suggest:edit:{self.suggestion_id}", disabled=not active,
        )
        delete = discord.ui.Button(
            label="Delete", emoji="🗑️", style=discord.ButtonStyle.secondary,
            custom_id=f"suggest:delete:{self.suggestion_id}", disabled=not active,
        )
        vote_for = discord.ui.Button(
            label=f"Vote For · {len(s.get('votes_for', []))}", emoji="👍",
            style=discord.ButtonStyle.success,
            custom_id=f"suggest:yes:{self.suggestion_id}", disabled=not active,
        )
        vote_against = discord.ui.Button(
            label=f"Vote Against · {len(s.get('votes_against', []))}", emoji="👎",
            style=discord.ButtonStyle.danger,
            custom_id=f"suggest:no:{self.suggestion_id}", disabled=not active,
        )
        accept = discord.ui.Button(
            label="Accept", emoji="✅", style=discord.ButtonStyle.success,
            custom_id=f"suggest:accept:{self.suggestion_id}", disabled=not active,
        )
        reject = discord.ui.Button(
            label="Reject", emoji="❌", style=discord.ButtonStyle.danger,
            custom_id=f"suggest:reject:{self.suggestion_id}", disabled=not active,
        )
        comment = discord.ui.Button(
            label="Comment", emoji="💬", style=discord.ButtonStyle.secondary,
            custom_id=f"suggest:comment:{self.suggestion_id}", disabled=not active,
        )
        admin_delete = discord.ui.Button(
            label="Admin Delete", emoji="🗑️", style=discord.ButtonStyle.secondary,
            custom_id=f"suggest:admin_delete:{self.suggestion_id}",
            disabled=bool(s.get("deleted")),
        )

        edit.callback = self.on_edit
        delete.callback = self.on_author_delete
        vote_for.callback = self.on_vote_for
        vote_against.callback = self.on_vote_against
        accept.callback = self.on_accept
        reject.callback = self.on_reject
        comment.callback = self.on_comment
        admin_delete.callback = self.on_admin_delete

        container = discord.ui.Container(
            discord.ui.TextDisplay(suggestion_body(s)),
            discord.ui.Separator(),
            discord.ui.TextDisplay("### 🔐 Author Controls"),
            discord.ui.ActionRow(edit, delete),
            discord.ui.Separator(),
            discord.ui.TextDisplay("### 🗳️ Community Voting"),
            discord.ui.ActionRow(vote_for, vote_against),
            discord.ui.Separator(),
            discord.ui.TextDisplay("### 🛡️ Admin Controls"),
            discord.ui.ActionRow(accept, reject, comment, admin_delete),
        )
        self.add_item(container)

    async def get_pending(self, interaction, owner_only=False):
        s = get_suggestion(self.suggestion_id)
        if not s or s.get("deleted"):
            await interaction.response.send_message(
                "This suggestion no longer exists.", ephemeral=True
            )
            return None
        if owner_only and interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                "Only the bot owner can use this control.", ephemeral=True
            )
            return None
        if s["status"] != "Pending":
            await interaction.response.send_message(
                "This suggestion has already been reviewed.", ephemeral=True
            )
            return None
        return s

    async def on_edit(self, interaction):
        s = await self.get_pending(interaction)
        if s is None:
            return
        if interaction.user.id != int(s["author_id"]):
            await interaction.response.send_message(
                "Only the suggestion author can edit it.", ephemeral=True
            )
            return
        await interaction.response.send_modal(EditSuggestionModal(self.suggestion_id))

    async def on_author_delete(self, interaction):
        s = get_suggestion(self.suggestion_id)
        if not s or s.get("deleted"):
            await interaction.response.send_message(
                "This suggestion no longer exists.", ephemeral=True
            )
            return
        if interaction.user.id != int(s["author_id"]):
            await interaction.response.send_message(
                "Use Admin Delete if you are the bot owner.", ephemeral=True
            )
            return
        if s["status"] != "Pending":
            await interaction.response.send_message(
                "You can only delete your own pending suggestion.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            "Confirm deletion of your suggestion.",
            view=DeleteConfirmView(self.suggestion_id, interaction.user.id, False),
            ephemeral=True,
        )

    async def on_admin_delete(self, interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                "Only the bot owner can use Admin Delete.", ephemeral=True
            )
            return
        s = get_suggestion(self.suggestion_id)
        if not s or s.get("deleted"):
            await interaction.response.send_message(
                "This suggestion has already been deleted.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            "Confirm administrative deletion.",
            view=DeleteConfirmView(self.suggestion_id, interaction.user.id, True),
            ephemeral=True,
        )

    async def on_vote_for(self, interaction):
        await self.cast_vote(interaction, True)

    async def on_vote_against(self, interaction):
        await self.cast_vote(interaction, False)

    async def cast_vote(self, interaction, positive):
        s = await self.get_pending(interaction)
        if s is None:
            return
        if interaction.user.bot:
            await interaction.response.send_message("Bots cannot vote.", ephemeral=True)
            return
        if interaction.user.id == int(s["author_id"]):
            await interaction.response.send_message(
                "You cannot vote on your own suggestion.", ephemeral=True
            )
            return
        all_votes = [int(uid) for uid in s["votes_for"] + s["votes_against"]]
        if interaction.user.id in all_votes:
            await interaction.response.send_message(
                "You have already voted. Votes cannot be changed.", ephemeral=True
            )
            return
        if positive:
            s["votes_for"].append(interaction.user.id)
        else:
            s["votes_against"].append(interaction.user.id)
        save_data()
        await interaction.response.send_message("Your vote has been recorded!", ephemeral=True)
        await refresh_suggestion(interaction.client, s)

    async def on_accept(self, interaction):
        s = await self.get_pending(interaction, owner_only=True)
        if s is None:
            return
        s["status"] = "Accepted"
        s["decision_at"] = timestamp()
        save_data()
        await interaction.response.send_message(
            f"Suggestion #{self.suggestion_id:03d} accepted.", ephemeral=True
        )
        await refresh_suggestion(interaction.client, s)
        await send_dm(
            interaction.client, s["author_id"],
            f"✅ Your suggestion **#{self.suggestion_id:03d}** has been accepted!\n\n"
            f"**Suggestion:** {s['text']}",
        )

    async def on_reject(self, interaction):
        s = await self.get_pending(interaction, owner_only=True)
        if s is None:
            return
        await interaction.response.send_modal(RejectSuggestionModal(self.suggestion_id))

    async def on_comment(self, interaction):
        s = await self.get_pending(interaction, owner_only=True)
        if s is None:
            return
        await interaction.response.send_modal(OwnerCommentModal(self.suggestion_id))


class DeleteConfirmView(discord.ui.View):
    def __init__(self, suggestion_id, requester_id, owner_delete):
        super().__init__(timeout=60)
        self.suggestion_id = int(suggestion_id)
        self.requester_id = int(requester_id)
        self.owner_delete = bool(owner_delete)

    async def interaction_check(self, interaction):
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message(
                "This confirmation belongs to another user.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Confirm Delete", emoji="🗑️", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction, button):
        s = get_suggestion(self.suggestion_id)
        if not s or s.get("deleted"):
            await interaction.response.send_message(
                "This suggestion no longer exists.", ephemeral=True
            )
            return
        if self.owner_delete:
            if interaction.user.id != OWNER_ID:
                await interaction.response.send_message(
                    "Only the bot owner can do this.", ephemeral=True
                )
                return
        elif interaction.user.id != int(s["author_id"]) or s["status"] != "Pending":
            await interaction.response.send_message(
                "Only the author can delete a pending suggestion.", ephemeral=True
            )
            return
        s["deleted"] = True
        s["status"] = "Deleted"
        save_data()
        await refresh_suggestion(interaction.client, s)
        await interaction.response.edit_message(
            content=f"Suggestion #{self.suggestion_id:03d} deleted.", view=None
        )

    @discord.ui.button(label="Cancel", emoji="↩️", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(content="Deletion cancelled.", view=None)


class EditSuggestionModal(discord.ui.Modal, title="Edit Suggestion"):
    text = discord.ui.TextInput(
        label="Suggestion", placeholder="Describe your suggestion...",
        min_length=5, max_length=MAX_LENGTH, style=discord.TextStyle.paragraph,
    )

    def __init__(self, suggestion_id):
        super().__init__()
        self.suggestion_id = int(suggestion_id)
        s = get_suggestion(suggestion_id)
        if s:
            self.text.default = s["text"]

    async def on_submit(self, interaction):
        s = get_suggestion(self.suggestion_id)
        if (not s or s.get("deleted") or interaction.user.id != int(s["author_id"])
                or s["status"] != "Pending"):
            await interaction.response.send_message(
                "This suggestion cannot be edited.", ephemeral=True
            )
            return
        s["text"] = str(self.text.value).strip()
        s["edited"] = True
        s["edited_at"] = timestamp()
        save_data()
        await interaction.response.send_message(
            "Your suggestion has been updated.", ephemeral=True
        )
        await refresh_suggestion(interaction.client, s)


class RejectSuggestionModal(discord.ui.Modal, title="Reject Suggestion"):
    reason = discord.ui.TextInput(
        label="Reason for rejection", placeholder="Explain why this was rejected...",
        min_length=3, max_length=500, style=discord.TextStyle.paragraph,
    )

    def __init__(self, suggestion_id):
        super().__init__()
        self.suggestion_id = int(suggestion_id)

    async def on_submit(self, interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                "Only the bot owner can reject suggestions.", ephemeral=True
            )
            return
        s = get_suggestion(self.suggestion_id)
        if not s or s.get("deleted") or s["status"] != "Pending":
            await interaction.response.send_message(
                "This suggestion is no longer pending.", ephemeral=True
            )
            return
        s["status"] = "Rejected"
        s["reject_reason"] = str(self.reason.value).strip()
        s["decision_at"] = timestamp()
        save_data()
        await interaction.response.send_message(
            f"Suggestion #{self.suggestion_id:03d} rejected.", ephemeral=True
        )
        await refresh_suggestion(interaction.client, s)
        await send_dm(
            interaction.client, s["author_id"],
            f"❌ Your suggestion **#{self.suggestion_id:03d}** was rejected.\n"
            f"**Reason:** {s['reject_reason']}\n\n**Suggestion:** {s['text']}",
        )


class OwnerCommentModal(discord.ui.Modal, title="Owner Comment"):
    comment = discord.ui.TextInput(
        label="Comment", placeholder="Write your comment...",
        min_length=1, max_length=500, style=discord.TextStyle.paragraph,
    )

    def __init__(self, suggestion_id):
        super().__init__()
        self.suggestion_id = int(suggestion_id)

    async def on_submit(self, interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                "Only the bot owner can comment.", ephemeral=True
            )
            return
        s = get_suggestion(self.suggestion_id)
        if not s or s.get("deleted") or s["status"] != "Pending":
            await interaction.response.send_message(
                "You can only comment on pending suggestions.", ephemeral=True
            )
            return
        s.setdefault("comments", []).append({
            "text": str(self.comment.value).strip(), "date": timestamp()
        })
        save_data()
        await interaction.response.send_message("Your comment has been added.", ephemeral=True)
        await refresh_suggestion(interaction.client, s)


class SuggestionModal(discord.ui.Modal, title="Submit Suggestion"):
    text = discord.ui.TextInput(
        label="Your suggestion", placeholder="Describe your idea clearly...",
        min_length=5, max_length=MAX_LENGTH, style=discord.TextStyle.paragraph,
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction):
        text_value = str(self.text.value).strip()
        if len(text_value) < 5:
            await interaction.response.send_message(
                "Your suggestion must contain at least 5 characters.", ephemeral=True
            )
            return

        async with LOCK:
            error = check_limits(interaction.user.id)
            if error:
                save_data()
                await interaction.response.send_message(error, ephemeral=True)
                return
            similar_id = find_similar(text_value)

        if similar_id is not None:
            await interaction.response.send_message(
                f"⚠️ Your suggestion may be similar to **#{similar_id:03d}**.\n"
                "Submit it anyway?",
                view=SimilarView(self.bot, interaction.user.id, text_value, similar_id),
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        await self.finish_submission(interaction, text_value)

    async def finish_submission(self, interaction, text_value):
        async with LOCK:
            error = check_limits(interaction.user.id)
            if error:
                save_data()
                await interaction.followup.send(error, ephemeral=True)
                return
            sid = await publish_suggestion(self.bot, interaction.user, text_value)

        if sid is None:
            await interaction.followup.send(
                "I couldn't publish your suggestion. Please try again later.", ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"✅ Your suggestion **#{sid:03d}** has been submitted!", ephemeral=True
            )


class SimilarView(discord.ui.View):
    def __init__(self, bot, user_id, text_value, similar_id):
        super().__init__(timeout=120)
        self.bot = bot
        self.user_id = int(user_id)
        self.text_value = text_value
        self.similar_id = int(similar_id)

    async def interaction_check(self, interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This confirmation belongs to another user.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Submit Anyway", emoji="✅", style=discord.ButtonStyle.success)
    async def submit_anyway(self, interaction, button):
        async with LOCK:
            error = check_limits(interaction.user.id)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return
        await interaction.response.send_modal(ConfirmSimilarModal(self.bot, self.text_value))

    @discord.ui.button(label="Cancel", emoji="✖️", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(
            content="Suggestion submission cancelled.", view=None
        )


class ConfirmSimilarModal(discord.ui.Modal, title="Submit Similar Suggestion"):
    text = discord.ui.TextInput(
        label="Your suggestion", min_length=5, max_length=MAX_LENGTH,
        style=discord.TextStyle.paragraph, required=True,
    )

    def __init__(self, bot, value):
        super().__init__()
        self.bot = bot
        self.text.default = value

    async def on_submit(self, interaction):
        value = str(self.text.value).strip()
        async with LOCK:
            error = check_limits(interaction.user.id)
            if error:
                save_data()
                await interaction.response.send_message(error, ephemeral=True)
                return
            sid = await publish_suggestion(self.bot, interaction.user, value)
        if sid is None:
            await interaction.response.send_message(
                "I couldn't publish your suggestion. Please try again later.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"✅ Your suggestion **#{sid:03d}** has been submitted!", ephemeral=True
            )


class SuggestEntryView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot

    @discord.ui.button(label="Write Suggestion", emoji="💡", style=discord.ButtonStyle.primary)
    async def open_form(self, interaction, button):
        await interaction.response.send_modal(SuggestionModal(self.bot))


class MineView(discord.ui.View):
    def __init__(self, user_id, page=0, status_filter="All"):
        super().__init__(timeout=180)
        self.user_id = int(user_id)
        self.page = page
        self.status_filter = status_filter
        self.update_controls()

    def get_items(self):
        cutoff = now() - timedelta(days=MINE_DAYS)
        items = []
        for s in DATA["suggestions"].values():
            if s.get("deleted") or int(s["author_id"]) != self.user_id:
                continue
            created = parse_date(s.get("created_at"))
            if not created or created < cutoff:
                continue
            if self.status_filter != "All" and s["status"] != self.status_filter:
                continue
            items.append(s)
        return sorted(items, key=lambda s: int(s["id"]), reverse=True)

    def update_controls(self):
        self.clear_items()
        options = [
            discord.SelectOption(label=value, value=value, default=self.status_filter == value)
            for value in ("All", "Pending", "Accepted", "Rejected")
        ]
        select = discord.ui.Select(placeholder="Filter by status", options=options, row=0)
        select.callback = self.select_filter
        self.add_item(select)

        previous = discord.ui.Button(
            label="Previous", emoji="◀️", style=discord.ButtonStyle.secondary,
            row=1, disabled=self.page <= 0,
        )
        previous.callback = self.previous_page
        self.add_item(previous)

        pages = max(1, (len(self.get_items()) + PAGE_SIZE - 1) // PAGE_SIZE)
        next_button = discord.ui.Button(
            label="Next", emoji="▶️", style=discord.ButtonStyle.secondary,
            row=1, disabled=self.page >= pages - 1,
        )
        next_button.callback = self.next_page
        self.add_item(next_button)

    async def interaction_check(self, interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "These pages belong to another user.", ephemeral=True
            )
            return False
        return True

    def make_page_embed(self):
        items = self.get_items()
        pages = max(1, (len(items) + PAGE_SIZE - 1) // PAGE_SIZE)
        self.page = max(0, min(self.page, pages - 1))
        embed = discord.Embed(
            title="📋 My Suggestions",
            description=f"Suggestions from the last {MINE_DAYS} days.",
            color=discord.Color.blurple(),
        )
        selected = items[self.page * PAGE_SIZE:(self.page + 1) * PAGE_SIZE]
        if not selected:
            embed.description += "\n\nNo suggestions found."
        else:
            for s in selected:
                embed.add_field(
                    name=f"#{int(s['id']):03d} • {display_status(s['status'])}",
                    value=shorten(s["text"], 300),
                    inline=False,
                )
        embed.set_footer(text=f"Page {self.page + 1}/{pages}")
        return embed

    async def select_filter(self, interaction):
        self.status_filter = interaction.data["values"][0]
        self.page = 0
        self.update_controls()
        await interaction.response.edit_message(embed=self.make_page_embed(), view=self)

    async def previous_page(self, interaction):
        self.page = max(0, self.page - 1)
        self.update_controls()
        await interaction.response.edit_message(embed=self.make_page_embed(), view=self)

    async def next_page(self, interaction):
        self.page += 1
        self.update_controls()
        await interaction.response.edit_message(embed=self.make_page_embed(), view=self)


class SuggestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _send_mine(self, message):
        view = MineView(message.author.id)
        try:
            await message.author.send(embed=view.make_page_embed(), view=view)
            if message.guild:
                await message.channel.send(
                    f"{message.author.mention}, check your DMs.", delete_after=8
                )
        except discord.Forbidden:
            if message.guild:
                await message.channel.send(
                    "I couldn't DM you. Enable direct messages and try again.", delete_after=10
                )

    @commands.command(name="commands")
    async def suggest_commands(self, ctx, system: str = None):
        """Show the available commands and controls for a system."""
        if system is None or system.lower() != "suggest":
            return

        embed = discord.Embed(
            title="💡 Suggestion System — Commands",
            description="Here are all available commands and controls for the Suggestion System.",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="📝 User Commands",
            value=(
                "`?suggest` — Open the Suggestion Center.\n"
                "`?suggest help` — View suggestion rules.\n"
                "`?suggest mine` — View your suggestions from the last 14 days."
            ),
            inline=False,
        )
        embed.add_field(
            name="🔘 Suggestion Buttons",
            value=(
                "`Write Suggestion` — Submit a suggestion.\n"
                "`Edit` — Edit your own pending suggestion.\n"
                "`Delete` — Delete your own pending suggestion.\n"
                "`Vote For` — Vote in favor.\n"
                "`Vote Against` — Vote against."
            ),
            inline=False,
        )
        embed.add_field(
            name="🛡️ Owner Controls",
            value=(
                "`Accept` — Accept a suggestion.\n"
                "`Reject` — Reject a suggestion with a reason.\n"
                "`Comment` — Add an owner comment.\n"
                "`Admin Delete` — Administratively delete a suggestion."
            ),
            inline=False,
        )
        embed.set_footer(text="RULL • Suggestion System")
        try:
    await ctx.message.delete()
except (discord.Forbidden, discord.HTTPException):
    pass

await ctx.send(embed=embed, reference=None)

    async def _send_help(self, message):
        embed = discord.Embed(
            title="💡 Suggestion Rules",
            color=discord.Color.blurple(),
            description=(
                "• Keep suggestions clear and respectful.\n"
                "• Maximum length: 1000 characters.\n"
                "• You can submit 3 suggestions per 24 hours.\n"
                "• There is a 10-minute cooldown between submissions.\n"
                "• You cannot vote on your own suggestion.\n"
                "• Votes cannot be changed after voting.\n"
                "• You can edit or delete your suggestion while it is pending.\n"
                "• Recent suggestions: `?suggest mine`."
            ),
        )
        try:
            await message.author.send(embed=embed)
        except discord.Forbidden:
            if message.guild:
                await message.channel.send(
                    "I couldn't DM you. Enable direct messages and try again.", delete_after=10
                )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.content:
            return
        content = message.content.strip().lower()
        if content not in ("?suggest", "?suggest help", "?suggest mine"):
            return
        try:
            await message.delete()
        except (discord.HTTPException, discord.Forbidden):
            pass

        if content == "?suggest help":
            await self._send_help(message)
        elif content == "?suggest mine":
            await self._send_mine(message)
        else:
            try:
                await message.author.send(
                    "💡 **Suggestion Center**\nUse the button below to submit a suggestion.",
                    view=SuggestEntryView(self.bot),
                )
                if message.guild:
                    await message.channel.send(
                        f"{message.author.mention}, I've sent you a DM.", delete_after=8
                    )
            except discord.Forbidden:
                if message.guild:
                    await message.channel.send(
                        "I couldn't DM you. Please enable direct messages and try `?suggest` again.",
                        delete_after=12,
                    )


async def setup(bot: commands.Bot):
    load_data()
    await bot.add_cog(SuggestCog(bot))

    # Restore persistent Component V2 views for existing public suggestions.
    for s in DATA["suggestions"].values():
        if s.get("deleted") and s.get("status") != "Deleted":
            continue
        if s.get("message_id"):
            bot.add_view(SuggestionView(int(s["id"])), message_id=int(s["message_id"]))
