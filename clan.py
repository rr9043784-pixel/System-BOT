import os
import re
import sqlite3
import logging
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands

# ============================================================
# LEGENDS CLANS | SYSTEM-BOT extension
# Python 3.13 | discord.py 2.6+
#
# Required bot permissions:
# Manage Roles, Manage Nicknames, Manage Threads, Send Messages,
# Send Messages in Threads, Create Public Threads, Moderate Members,
# View Channels, Read Message History.
#
# The bot's highest role must be above the clan roles it creates.
# Clan roles are identity roles only; their permissions stay empty.
# ============================================================

log = logging.getLogger("LEGENDS_CLANS")

OWNER_ID = 1176149190192152626
PURCHASE_ROLE_ID = 1574839275529306264
CLAN_FORUM_ID = 1574839165231566949

DATA_DIR = os.getenv("DATA_DIR", "/data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "clans.db")

TAG_RE = re.compile(r"^[A-Za-z]{2,3}$")
HEX_RE = re.compile(r"^#?[0-9A-Fa-f]{6}$")

# Membership caps unlock at these levels. Existing members are never
# removed if a clan later drops below a previously reached level.
CAPACITY_BY_LEVEL = {
    1: 3,
    5: 5,
    10: 10,
    25: 20,
}

UNLOCKS = {
    1: "Clan creation and management panel",
    5: "Clan Games",
    10: "Clan Battles",
    15: "Advanced Management",
    20: "Elite Rewards",
    25: "Maximum clan capacity (20 members)",
}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def normalize_tag(tag: str) -> str:
    return tag.strip().upper()


def small_caps(text: str) -> str:
    table = str.maketrans(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"
        "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ",
    )
    return text.translate(table)


def parse_color(value: str) -> discord.Color:
    value = value.strip()
    if not HEX_RE.fullmatch(value):
        raise ValueError("Enter a valid HEX color, for example #9B59B6.")
    value = value.lstrip("#")
    return discord.Color(int(value, 16))


def clan_prefix(tag: str) -> str:
    return f"{small_caps(tag)}┃"


def capacity_for_level(level: int) -> int:
    cap = 3
    for unlock_level, value in sorted(CAPACITY_BY_LEVEL.items()):
        if level >= unlock_level:
            cap = value
    return cap


class ClanDatabase:
    def __init__(self, path: str):
        self.path = path
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.db.executescript("""
        PRAGMA journal_mode=WAL;

        CREATE TABLE IF NOT EXISTS clans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            owner_id INTEGER NOT NULL,
            tag TEXT NOT NULL,
            name TEXT NOT NULL,
            color TEXT NOT NULL,
            level INTEGER NOT NULL DEFAULT 1,
            xp INTEGER NOT NULL DEFAULT 0,
            victories INTEGER NOT NULL DEFAULT 0,
            forum_thread_id INTEGER,
            panel_message_id INTEGER,
            divider_top_role_id INTEGER,
            color_role_id INTEGER,
            leader_role_id INTEGER,
            moderator_role_id INTEGER,
            member_role_id INTEGER,
            divider_bottom_role_id INTEGER,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS clan_members (
            clan_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            rank TEXT NOT NULL DEFAULT 'member',
            original_nick TEXT,
            joined_at TEXT NOT NULL,
            PRIMARY KEY (clan_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS clan_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clan_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            UNIQUE(clan_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS thread_warnings (
            thread_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            count INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(thread_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS clan_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clan_id INTEGER NOT NULL,
            actor_id INTEGER,
            action TEXT NOT NULL,
            details TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        """)
        self.db.commit()

    def execute(self, sql, params=()):
        cur = self.db.execute(sql, params)
        self.db.commit()
        return cur

    def one(self, sql, params=()):
        return self.db.execute(sql, params).fetchone()

    def all(self, sql, params=()):
        return self.db.execute(sql, params).fetchall()

    def get_clan(self, clan_id):
        return self.one("SELECT * FROM clans WHERE id=?", (clan_id,))

    def get_clan_for_user(self, user_id):
        return self.one("""
            SELECT c.* FROM clans c
            JOIN clan_members m ON m.clan_id=c.id
            WHERE m.user_id=?
        """, (user_id,))

    def members(self, clan_id):
        return self.all("""
            SELECT * FROM clan_members WHERE clan_id=?
            ORDER BY CASE rank WHEN 'leader' THEN 0 WHEN 'moderator' THEN 1 ELSE 2 END,
                     joined_at
        """, (clan_id,))

    def log(self, clan_id, actor_id, action, details=""):
        self.execute(
            "INSERT INTO clan_logs(clan_id,actor_id,action,details,created_at) VALUES(?,?,?,?,?)",
            (clan_id, actor_id, action, details, utc_now()),
        )


class RegistrationView(discord.ui.View):
    def __init__(self, cog, guild_id):
        super().__init__(timeout=600)
        self.cog = cog
        self.guild_id = guild_id

    @discord.ui.button(label="Register Clan", style=discord.ButtonStyle.success, emoji="🏰")
    async def register(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild_id != self.guild_id:
            return await interaction.response.send_message(
                "Please complete clan registration in the server where you received the purchase role.",
                ephemeral=True,
            )
        if self.cog.db.get_clan_for_user(interaction.user.id):
            return await interaction.response.send_message(
                "You are already a member of a clan.",
                ephemeral=True,
            )
        await interaction.response.send_modal(ClanRegistrationModal(self.cog, self.guild_id))


class ClanRegistrationModal(discord.ui.Modal, title="Create Your Clan"):
    tag = discord.ui.TextInput(
        label="Clan Tag (2–3 letters)",
        placeholder="RLL",
        min_length=2,
        max_length=3,
    )
    name = discord.ui.TextInput(
        label="Clan Name",
        placeholder="RULL[LEGEND]",
        min_length=3,
        max_length=32,
    )
    color = discord.ui.TextInput(
        label="Clan Color (HEX)",
        placeholder="#9B59B6",
        min_length=6,
        max_length=7,
    )

    def __init__(self, cog, guild_id):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        tag = normalize_tag(str(self.tag.value))
        name = str(self.name.value).strip()
        color_text = str(self.color.value).strip()

        if not TAG_RE.fullmatch(tag):
            return await interaction.response.send_message(
                "The clan tag must contain 2 or 3 English letters.",
                ephemeral=True,
            )
        try:
            color = parse_color(color_text)
        except ValueError as exc:
            return await interaction.response.send_message(str(exc), ephemeral=True)

        guild = interaction.guild
        if guild is None or guild.id != self.guild_id:
            return await interaction.response.send_message(
                "The server could not be verified. Please try again from the server.",
                ephemeral=True,
            )
        if self.cog.db.get_clan_for_user(interaction.user.id):
            return await interaction.response.send_message(
                "You are already a member of a clan.",
                ephemeral=True,
            )
        if self.cog.db.one(
            "SELECT id FROM clans WHERE guild_id=? AND LOWER(tag)=LOWER(?)",
            (guild.id, tag),
        ):
            return await interaction.response.send_message(
                "That clan tag is already in use. Please choose another one.",
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            clan = await self.cog.create_clan(guild, interaction.user, tag, name, color)
        except discord.Forbidden:
            return await interaction.followup.send(
                "I could not create the clan. Please check my Manage Roles, Manage Threads, "
                "and Manage Nicknames permissions, and make sure my highest role is above "
                "the roles I need to create.",
                ephemeral=True,
            )
        except Exception:
            log.exception("Clan creation failed")
            return await interaction.followup.send(
                "Clan creation failed. Please contact a server administrator.",
                ephemeral=True,
            )

        await interaction.followup.send(
            f"Your clan **{name}** (`{tag}`) has been created!",
            ephemeral=True,
        )


class ApplyModal(discord.ui.Modal, title="Apply to Join Clan"):
    message = discord.ui.TextInput(
        label="Why do you want to join?",
        placeholder="Write a short introduction...",
        style=discord.TextStyle.paragraph,
        min_length=5,
        max_length=500,
    )

    def __init__(self, cog, clan_id):
        super().__init__()
        self.cog = cog
        self.clan_id = clan_id

    async def on_submit(self, interaction: discord.Interaction):
        clan = self.cog.db.get_clan(self.clan_id)
        if not clan:
            return await interaction.response.send_message("This clan no longer exists.", ephemeral=True)
        if self.cog.db.get_clan_for_user(interaction.user.id):
            return await interaction.response.send_message("You are already in a clan.", ephemeral=True)

        existing = self.cog.db.one(
            "SELECT id,status FROM clan_applications WHERE clan_id=? AND user_id=?",
            (self.clan_id, interaction.user.id),
        )
        if existing and existing["status"] == "pending":
            return await interaction.response.send_message(
                "You already have a pending application for this clan.",
                ephemeral=True,
            )

        self.cog.db.execute("""
            INSERT INTO clan_applications(clan_id,user_id,message,status,created_at)
            VALUES(?,?,?,'pending',?)
            ON CONFLICT(clan_id,user_id) DO UPDATE SET
                message=excluded.message,status='pending',created_at=excluded.created_at
        """, (self.clan_id, interaction.user.id, str(self.message.value), utc_now()))

        await interaction.response.send_message(
            "Your application has been sent to the clan leadership.",
            ephemeral=True,
        )
        await self.cog.notify_leadership(clan, interaction.user, str(self.message.value))


class ClanPanelView(discord.ui.View):
    def __init__(self, cog, clan_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.clan_id = clan_id

        apply_button = discord.ui.Button(
            label="Apply to Join",
            style=discord.ButtonStyle.success,
            emoji="📨",
            custom_id=f"legends_clan:apply:{clan_id}",
        )
        apply_button.callback = self.apply
        self.add_item(apply_button)

        members_button = discord.ui.Button(
            label="Members",
            style=discord.ButtonStyle.secondary,
            emoji="👥",
            custom_id=f"legends_clan:members:{clan_id}",
        )
        members_button.callback = self.show_members
        self.add_item(members_button)

        leave_button = discord.ui.Button(
            label="Leave Clan",
            style=discord.ButtonStyle.danger,
            emoji="🚪",
            custom_id=f"legends_clan:leave:{clan_id}",
        )
        leave_button.callback = self.leave
        self.add_item(leave_button)

        manage_button = discord.ui.Button(
            label="Leadership",
            style=discord.ButtonStyle.primary,
            emoji="⚙️",
            custom_id=f"legends_clan:manage:{clan_id}",
        )
        manage_button.callback = self.manage
        self.add_item(manage_button)

    async def apply(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ApplyModal(self.cog, self.clan_id))

    async def show_members(self, interaction: discord.Interaction):
        clan = self.cog.db.get_clan(self.clan_id)
        if not clan:
            return await interaction.response.send_message("Clan not found.", ephemeral=True)
        rows = self.cog.db.members(self.clan_id)
        lines = []
        for row in rows:
            member = interaction.guild.get_member(row["user_id"]) if interaction.guild else None
            display = member.mention if member else f"`{row['user_id']}`"
            lines.append(f"**{row['rank'].title()}** — {display}")
        embed = discord.Embed(
            title=f"{clan['name']} · Members",
            description="\n".join(lines) if lines else "No members yet.",
            color=parse_color(clan["color"]),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def leave(self, interaction: discord.Interaction):
        clan = self.cog.db.get_clan(self.clan_id)
        member_row = self.cog.db.one(
            "SELECT * FROM clan_members WHERE clan_id=? AND user_id=?",
            (self.clan_id, interaction.user.id),
        )
        if not clan or not member_row:
            return await interaction.response.send_message("You are not in this clan.", ephemeral=True)
        if member_row["rank"] == "leader":
            return await interaction.response.send_message(
                "The clan leader cannot leave directly. Transfer leadership first or ask the server owner to disband the clan.",
                ephemeral=True,
            )
        await self.cog.remove_member(interaction.guild, interaction.user, clan)
        await interaction.response.send_message("You have left the clan.", ephemeral=True)

    async def manage(self, interaction: discord.Interaction):
        row = self.cog.db.one(
            "SELECT rank FROM clan_members WHERE clan_id=? AND user_id=?",
            (self.clan_id, interaction.user.id),
        )
        if not row or row["rank"] not in ("leader", "moderator"):
            return await interaction.response.send_message(
                "Only clan leaders and moderators can use leadership controls.",
                ephemeral=True,
            )
        clan = self.cog.db.get_clan(self.clan_id)
        if not clan:
            return await interaction.response.send_message("Clan not found.", ephemeral=True)
        pending = self.cog.db.all(
            "SELECT * FROM clan_applications WHERE clan_id=? AND status='pending' ORDER BY created_at",
            (self.clan_id,),
        )
        if not pending:
            return await interaction.response.send_message(
                "There are no pending applications.",
                ephemeral=True,
            )
        await interaction.response.send_message(
            f"There are **{len(pending)}** pending application(s). Use `/clan applications` to review them.",
            ephemeral=True,
        )


class ApplicationDecisionView(discord.ui.View):
    def __init__(self, cog, application_id):
        super().__init__(timeout=86400)
        self.cog = cog
        self.application_id = application_id

    async def _decide(self, interaction, accepted: bool):
        app = self.cog.db.one(
            "SELECT * FROM clan_applications WHERE id=?",
            (self.application_id,),
        )
        if not app or app["status"] != "pending":
            return await interaction.response.send_message("This application is no longer pending.", ephemeral=True)
        clan = self.cog.db.get_clan(app["clan_id"])
        actor_row = self.cog.db.one(
            "SELECT rank FROM clan_members WHERE clan_id=? AND user_id=?",
            (app["clan_id"], interaction.user.id),
        )
        if not actor_row or actor_row["rank"] not in ("leader", "moderator"):
            return await interaction.response.send_message("You cannot review this application.", ephemeral=True)

        if not accepted:
            self.cog.db.execute(
                "UPDATE clan_applications SET status='rejected' WHERE id=?",
                (self.application_id,),
            )
            await interaction.response.edit_message(content="Application rejected.", view=None)
            applicant = interaction.guild.get_member(app["user_id"]) if interaction.guild else None
            if applicant:
                try:
                    await applicant.send(f"Your application to **{clan['name']}** was declined.")
                except discord.Forbidden:
                    pass
            return

        if self.cog.db.get_clan_for_user(app["user_id"]):
            self.cog.db.execute(
                "UPDATE clan_applications SET status='rejected' WHERE id=?",
                (self.application_id,),
            )
            return await interaction.response.edit_message(
                content="The applicant has already joined another clan. Application closed.",
                view=None,
            )

        members = self.cog.db.members(app["clan_id"])
        if len(members) >= capacity_for_level(clan["level"]):
            return await interaction.response.send_message(
                f"This clan is full. Current capacity: {capacity_for_level(clan['level'])}.",
                ephemeral=True,
            )

        applicant = interaction.guild.get_member(app["user_id"]) if interaction.guild else None
        if not applicant:
            return await interaction.response.send_message("The applicant is no longer in this server.", ephemeral=True)

        await self.cog.add_member(interaction.guild, applicant, clan, "member")
        self.cog.db.execute(
            "UPDATE clan_applications SET status='accepted' WHERE id=?",
            (self.application_id,),
        )
        await interaction.response.edit_message(content=f"Accepted: {applicant.mention} joined **{clan['name']}**.", view=None)
        try:
            await applicant.send(f"Your application to **{clan['name']}** was accepted!")
        except discord.Forbidden:
            pass

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, emoji="✅")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._decide(interaction, True)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger, emoji="❌")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._decide(interaction, False)


class ClanApplicationsCommand(app_commands.Group):
    def __init__(self, cog):
        super().__init__(name="applications", description="Review clan applications")
        self.cog = cog

    @app_commands.command(name="list", description="Show pending applications for your clan")
    async def list_applications(self, interaction: discord.Interaction):
        clan = self.cog.db.get_clan_for_user(interaction.user.id)
        if not clan:
            return await interaction.response.send_message("You are not in a clan.", ephemeral=True)
        rank = self.cog.db.one(
            "SELECT rank FROM clan_members WHERE clan_id=? AND user_id=?",
            (clan["id"], interaction.user.id),
        )
        if not rank or rank["rank"] not in ("leader", "moderator"):
            return await interaction.response.send_message("Only leadership can review applications.", ephemeral=True)

        apps = self.cog.db.all(
            "SELECT * FROM clan_applications WHERE clan_id=? AND status='pending' ORDER BY created_at",
            (clan["id"],),
        )
        if not apps:
            return await interaction.response.send_message("No pending applications.", ephemeral=True)

        await interaction.response.send_message(
            f"Pending applications: **{len(apps)}**. I will send each application below.",
            ephemeral=True,
        )
        for app in apps[:10]:
            user = interaction.guild.get_member(app["user_id"])
            mention = user.mention if user else f"User ID: `{app['user_id']}`"
            embed = discord.Embed(
                title=f"Application · {clan['name']}",
                description=f"**Applicant:** {mention}\n\n**Message:**\n{app['message']}",
                color=parse_color(clan["color"]),
            )
            await interaction.followup.send(
                embed=embed,
                view=ApplicationDecisionView(self.cog, app["id"]),
                ephemeral=True,
            )


class ClanCommands(commands.GroupCog, group_name="clan", group_description="LEGENDS CLANS commands"):
    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    @app_commands.command(name="info", description="View your clan information")
    async def info(self, interaction: discord.Interaction):
        clan = self.cog.db.get_clan_for_user(interaction.user.id)
        if not clan:
            return await interaction.response.send_message("You are not in a clan.", ephemeral=True)
        members = self.cog.db.members(clan["id"])
        embed = discord.Embed(
            title=f"{clan['name']} [{clan['tag']}]",
            description=(
                f"**Level:** {clan['level']}\n"
                f"**XP:** {clan['xp']}\n"
                f"**Members:** {len(members)}/{capacity_for_level(clan['level'])}\n"
                f"**Victories:** {clan['victories']}\n"
                f"**Color:** `{clan['color']}`"
            ),
            color=parse_color(clan["color"]),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="leaderboard", description="View the top clans")
    async def leaderboard(self, interaction: discord.Interaction):
        clans = self.cog.db.all(
            "SELECT * FROM clans WHERE guild_id=? ORDER BY level DESC,xp DESC,victories DESC LIMIT 10",
            (interaction.guild_id,),
        )
        if not clans:
            return await interaction.response.send_message("No clans have been created yet.", ephemeral=True)
        lines = [
            f"**{index}.** `{row['tag']}` **{row['name']}** — Level {row['level']} · {row['xp']} XP"
            for index, row in enumerate(clans, 1)
        ]
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🏆 LEGENDS CLANS Leaderboard",
                description="\n".join(lines),
                color=discord.Color.gold(),
            ),
            ephemeral=True,
        )

    @app_commands.command(name="applications", description="Review applications for your clan")
    async def applications(self, interaction: discord.Interaction):
        clan = self.cog.db.get_clan_for_user(interaction.user.id)
        if not clan:
            return await interaction.response.send_message("You are not in a clan.", ephemeral=True)
        rank = self.cog.db.one(
            "SELECT rank FROM clan_members WHERE clan_id=? AND user_id=?",
            (clan["id"], interaction.user.id),
        )
        if not rank or rank["rank"] not in ("leader", "moderator"):
            return await interaction.response.send_message("Only leadership can review applications.", ephemeral=True)
        apps = self.cog.db.all(
            "SELECT * FROM clan_applications WHERE clan_id=? AND status='pending' ORDER BY created_at",
            (clan["id"],),
        )
        if not apps:
            return await interaction.response.send_message("No pending applications.", ephemeral=True)
        await interaction.response.send_message(
            f"Pending applications: **{len(apps)}**. Review cards will follow.",
            ephemeral=True,
        )
        for app in apps[:10]:
            user = interaction.guild.get_member(app["user_id"])
            embed = discord.Embed(
                title=f"Application · {clan['name']}",
                description=(
                    f"**Applicant:** {user.mention if user else app['user_id']}\n\n"
                    f"**Message:**\n{app['message']}"
                ),
                color=parse_color(clan["color"]),
            )
            await interaction.followup.send(
                embed=embed,
                view=ApplicationDecisionView(self.cog, app["id"]),
                ephemeral=True,
            )


class ClanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = ClanDatabase(DB_PATH)
        self._purchase_lock = set()

    async def cog_load(self):
        # Re-register persistent clan panels after a restart.
        for row in self.db.all("SELECT id,forum_thread_id,panel_message_id FROM clans"):
            if row["forum_thread_id"]:
                self.bot.add_view(ClanPanelView(self, row["id"]), message_id=row["panel_message_id"])

    async def cog_unload(self):
        self.db.db.close()

    async def create_clan(self, guild, leader, tag, name, color):
        forum = guild.get_channel(CLAN_FORUM_ID)
        if not isinstance(forum, discord.ForumChannel):
            raise RuntimeError("Configured clan channel is not a ForumChannel.")

        # Create identity roles with no permissions. Never grant permissions here.
        top = await guild.create_role(
            name=f"━━━ {tag} CLAN ━━━",
            permissions=discord.Permissions.none(),
            reason="LEGENDS CLANS setup",
        )
        color_role = await guild.create_role(
            name=f"{tag}┃Color",
            permissions=discord.Permissions.none(),
            colour=color,
            reason="LEGENDS CLANS setup",
        )
        leader_role = await guild.create_role(
            name=f"{tag}┃Leader",
            permissions=discord.Permissions.none(),
            reason="LEGENDS CLANS setup",
        )
        mod_role = await guild.create_role(
            name=f"{tag}┃Moderator",
            permissions=discord.Permissions.none(),
            reason="LEGENDS CLANS setup",
        )
        member_role = await guild.create_role(
            name=f"{tag}┃Member",
            permissions=discord.Permissions.none(),
            reason="LEGENDS CLANS setup",
        )
        bottom = await guild.create_role(
            name=f"━━━ {tag} END ━━━",
            permissions=discord.Permissions.none(),
            reason="LEGENDS CLANS setup",
        )

        cur = self.db.execute("""
            INSERT INTO clans(
                guild_id,owner_id,tag,name,color,level,xp,created_at,
                divider_top_role_id,color_role_id,leader_role_id,
                moderator_role_id,member_role_id,divider_bottom_role_id
            ) VALUES(?,?,?,?,?,1,0,?,?,?,?,?,?,?)
        """, (
            guild.id, leader.id, tag, name, str(color),
            utc_now(), top.id, color_role.id, leader_role.id, mod_role.id,
            member_role.id, bottom.id,
        ))
        clan_id = cur.lastrowid
        clan = self.db.get_clan(clan_id)

        await self.add_member(guild, leader, clan, "leader", roles_already_created=True)

        view = ClanPanelView(self, clan_id)
        description = (
            f"## 🏰 {name}\n"
            f"**Clan Tag:** `{tag}`\n"
            f"**Leader:** {leader.mention}\n"
            f"**Level:** 1 · **XP:** 0\n"
            f"**Members:** 1/{capacity_for_level(1)}\n\n"
            "Use **Apply to Join** to send an application.\n"
            "Clan members can use **Members** and **Leave Clan** from this panel.\n"
            "Leadership controls are available to clan leaders and moderators."
        )
        thread_name = f"{small_caps(tag)}┃{name}'s clan"
        result = await forum.create_thread(
            name=thread_name,
            content=description,
            view=view,
            reason="Create LEGENDS CLANS forum post",
        )
        thread = getattr(result, "thread", result)
        message = getattr(result, "message", None)
        if message is None:
            try:
                message = await thread.fetch_message(thread.id)
            except (discord.NotFound, discord.Forbidden, AttributeError):
                message = None

        self.db.execute(
            "UPDATE clans SET forum_thread_id=?,panel_message_id=? WHERE id=?",
            (thread.id, message.id if message else None, clan_id),
        )
        self.db.log(clan_id, leader.id, "clan_created", f"{name} [{tag}]")
        return self.db.get_clan(clan_id)

    async def add_member(self, guild, member, clan, rank="member", roles_already_created=False):
        if self.db.get_clan_for_user(member.id):
            raise ValueError("User already belongs to a clan.")

        original_nick = member.nick
        self.db.execute("""
            INSERT INTO clan_members(clan_id,user_id,rank,original_nick,joined_at)
            VALUES(?,?,?,?,?)
        """, (clan["id"], member.id, rank, original_nick, utc_now()))

        role_ids = [
            clan["divider_top_role_id"],
            clan["color_role_id"],
            clan["leader_role_id"] if rank == "leader" else
            clan["moderator_role_id"] if rank == "moderator" else clan["member_role_id"],
            clan["divider_bottom_role_id"],
        ]
        roles = [guild.get_role(role_id) for role_id in role_ids if role_id]
        roles = [role for role in roles if role]
        if roles:
            await member.add_roles(*roles, reason="LEGENDS CLANS membership")

        base_name = clan["name"] if rank == "leader" else (member.nick or member.name)
        nickname = f"{clan_prefix(clan['tag'])}{base_name}"[:32]
        try:
            await member.edit(nick=nickname, reason="LEGENDS CLANS nickname")
        except discord.Forbidden:
            log.warning("Cannot change nickname for member %s", member.id)

        self.db.log(clan["id"], member.id, "member_joined", rank)

    async def remove_member(self, guild, member, clan):
        row = self.db.one(
            "SELECT * FROM clan_members WHERE clan_id=? AND user_id=?",
            (clan["id"], member.id),
        )
        if not row:
            return
        role_ids = [
            clan["divider_top_role_id"], clan["color_role_id"],
            clan["leader_role_id"], clan["moderator_role_id"],
            clan["member_role_id"], clan["divider_bottom_role_id"],
        ]
        roles = [guild.get_role(role_id) for role_id in role_ids if role_id]
        roles = [role for role in roles if role and role in member.roles]
        if roles:
            await member.remove_roles(*roles, reason="LEGENDS CLANS membership ended")
        try:
            await member.edit(nick=row["original_nick"], reason="LEGENDS CLANS nickname reset")
        except discord.Forbidden:
            pass
        self.db.execute(
            "DELETE FROM clan_members WHERE clan_id=? AND user_id=?",
            (clan["id"], member.id),
        )
        self.db.log(clan["id"], member.id, "member_left", "")

    async def notify_leadership(self, clan, applicant, message):
        guild = self.bot.get_guild(clan["guild_id"])
        if not guild:
            return
        leadership = self.db.all(
            "SELECT user_id FROM clan_members WHERE clan_id=? AND rank IN ('leader','moderator')",
            (clan["id"],),
        )
        app = self.db.one(
            "SELECT id FROM clan_applications WHERE clan_id=? AND user_id=?",
            (clan["id"], applicant.id),
        )
        embed = discord.Embed(
            title=f"New application · {clan['name']}",
            description=f"**Applicant:** {applicant.mention}\n\n**Message:**\n{message}",
            color=parse_color(clan["color"]),
        )
        for row in leadership:
            member = guild.get_member(row["user_id"])
            if member:
                try:
                    await member.send(embed=embed, view=ApplicationDecisionView(self, app["id"]))
                except discord.Forbidden:
                    pass

    async def process_purchase_role(self, member):
        if member.bot or member.id in self._purchase_lock:
            return
        role = member.guild.get_role(PURCHASE_ROLE_ID)
        if not role or role not in member.roles:
            return
        self._purchase_lock.add(member.id)
        try:
            # Send the registration DM first. If DMs are closed, keep the purchase
            # role so the next member update / bot restart can retry the notification.
            try:
                await member.send(
                    "🏰 **LEGENDS CLANS registration**\n"
                    "Your clan purchase has been detected. Press the button below to register your clan.",
                    view=RegistrationView(self, member.guild.id),
                )
            except discord.Forbidden:
                log.warning("Could not DM clan registration to %s; purchase role remains for retry.", member.id)
                return
            await member.remove_roles(role, reason="LEGENDS CLANS purchase role consumed")
        finally:
            self._purchase_lock.discard(member.id)

    @commands.Cog.listener()
    async def on_ready(self):
        # Catch purchases that happened while the bot was offline.
        for guild in self.bot.guilds:
            role = guild.get_role(PURCHASE_ROLE_ID)
            if not role:
                continue
            for member in role.members:
                await self.process_purchase_role(member)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        before_has = any(role.id == PURCHASE_ROLE_ID for role in before.roles)
        after_has = any(role.id == PURCHASE_ROLE_ID for role in after.roles)
        if after_has and not before_has:
            await self.process_purchase_role(after)

        # Keep clan prefix if a member changes their nickname manually.
        row = self.db.get_clan_for_user(after.id)
        if row and before.nick != after.nick:
            member_row = self.db.one(
                "SELECT rank FROM clan_members WHERE clan_id=? AND user_id=?",
                (row["id"], after.id),
            )
            if member_row:
                rank = member_row["rank"]
                prefix = clan_prefix(row["tag"])
                current = after.nick or after.name
                if not current.startswith(prefix):
                    base = row["name"] if rank == "leader" else current
                    new_nick = f"{prefix}{base}"[:32]
                    try:
                        await after.edit(nick=new_nick, reason="Maintain LEGENDS CLANS nickname prefix")
                    except discord.Forbidden:
                        pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        clan = self.db.get_clan_for_user(member.id)
        if not clan:
            return
        row = self.db.one(
            "SELECT rank FROM clan_members WHERE clan_id=? AND user_id=?",
            (clan["id"], member.id),
        )
        self.db.execute(
            "DELETE FROM clan_members WHERE clan_id=? AND user_id=?",
            (clan["id"], member.id),
        )
        self.db.log(clan["id"], member.id, "member_left_server", "")
        if row and row["rank"] == "leader":
            guild = self.bot.get_guild(clan["guild_id"])
            if guild:
                owner = guild.get_member(OWNER_ID)
                if owner:
                    try:
                        await owner.send(
                            f"⚠️ The leader of **{clan['name']}** left the server. "
                            "Please appoint a new leader or disband the clan."
                        )
                    except discord.Forbidden:
                        pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not isinstance(message.channel, discord.Thread):
            return
        clan = self.db.one(
            "SELECT * FROM clans WHERE forum_thread_id=?",
            (message.channel.id,),
        )
        if not clan:
            return
        member_row = self.db.one(
            "SELECT rank FROM clan_members WHERE clan_id=? AND user_id=?",
            (clan["id"], message.author.id),
        )
        if member_row:
            return
        if message.author.guild_permissions.manage_messages or message.author.guild_permissions.administrator:
            return

        warning = self.db.one(
            "SELECT count FROM thread_warnings WHERE thread_id=? AND user_id=?",
            (message.channel.id, message.author.id),
        )
        count = (warning["count"] if warning else 0) + 1
        self.db.execute("""
            INSERT INTO thread_warnings(thread_id,user_id,count,updated_at)
            VALUES(?,?,?,?)
            ON CONFLICT(thread_id,user_id) DO UPDATE SET
                count=excluded.count,updated_at=excluded.updated_at
        """, (message.channel.id, message.author.id, count, utc_now()))

        try:
            await message.delete()
        except discord.Forbidden:
            log.warning("Missing Manage Messages in clan thread %s", message.channel.id)

        if count == 1:
            await message.channel.send(
                f"{message.author.mention} Please note: only clan members and authorized staff may chat in this clan thread.",
                delete_after=15,
            )
        else:
            minutes = 5 if count == 2 else 10
            try:
                await message.author.timeout(
                    timedelta(minutes=minutes),
                    reason=f"Repeated messages in a clan-only thread (warning {count})",
                )
                await message.channel.send(
                    f"{message.author.mention} has received a {minutes}-minute timeout for repeated messages in this clan thread.",
                    delete_after=15,
                )
            except discord.Forbidden:
                await message.channel.send(
                    f"{message.author.mention} You have received another warning. Staff may need to review this.",
                    delete_after=15,
                )

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        # Reserved for future moderation/audit integrations.
        return


async def setup(bot):
    cog = ClanCog(bot)
    await bot.add_cog(cog)
    await bot.add_cog(ClanCommands(cog))
