import os
import json
import calendar
from datetime import datetime, timezone

import discord
from discord.ext import commands, tasks


# =========================================================
# SETTINGS
# =========================================================

OWNER_ID = 1176149190192152626

TICKET_CATEGORY_ID = 1555925139546439700
SUPPORT_ROLE_ID = 1527295101867524106
AFTER_CLOSE_CHANNEL_ID = 1527278068526219305

DATA_FILE = "ticket_data.json"


# =========================================================
# DATA
# =========================================================

DEFAULT_DATA = {
    "panel": {
        "message_id": None,
        "channel_id": None
    },
    "next_ticket": 1,
    "tickets": {},
    "applications": {},
    "blocks": {}
}


def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA.copy()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        for key, value in DEFAULT_DATA.items():
            if key not in data:
                data[key] = value

        return data

    except Exception:
        return DEFAULT_DATA.copy()


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# =========================================================
# HELPERS
# =========================================================

def utc_now():
    return datetime.now(timezone.utc)


def iso_now():
    return utc_now().isoformat()


def parse_date(value):
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return utc_now()


def add_one_month(dt):
    year = dt.year
    month = dt.month

    if month == 12:
        year += 1
        month = 1
    else:
        month += 1

    day = min(dt.day, calendar.monthrange(year, month)[1])

    return dt.replace(
        year=year,
        month=month,
        day=day
    )


def format_date(value):
    dt = parse_date(value)
    return dt.strftime("%B %d, %Y at %H:%M UTC")


def ticket_number(number):
    return f"{number:04d}"


def is_support(member):
    return any(role.id == SUPPORT_ROLE_ID for role in member.roles)


def get_category(guild):
    return guild.get_channel(TICKET_CATEGORY_ID)


def get_close_channel(guild):
    return guild.get_channel(AFTER_CLOSE_CHANNEL_ID)


# =========================================================
# LANGUAGE / ISSUE OPTIONS
# =========================================================

LANGUAGES = [
    ("🇬🇧", "English", "English"),
    ("🇷🇺", "Russian", "Russian"),
    ("🇩🇪", "German", "German"),
    ("🇫🇷", "French", "French"),
    ("🇺🇿", "Uzbek", "Uzbek"),
    ("🇷🇴", "Romanian", "Romanian"),
    ("🇺🇦", "Ukrainian", "Ukrainian"),
    ("🇹🇷", "Turkish", "Turkish"),
    ("🇧🇾", "Belarusian", "Belarusian"),
    ("🇧🇷", "Brazilian", "Brazilian"),
    ("🇪🇸", "Spanish", "Spanish"),
]

ISSUES = [
    ("❓", "Question", "Question"),
    ("🚨", "Report", "Report"),
    ("🐛", "Bug", "Bug"),
    ("🤖", "Bot Bug", "Bot Bug"),
    ("ℹ️", "Other", "Other"),
]


# =========================================================
# APPLICATION QUESTIONS
# =========================================================

STAFF_QUESTIONS = [
    "🛡️ Which role are you applying for — Staff or Host?",
    "📝 Why do you want this role and why do you think you are suitable for it?",
    "🕐 How much time can you usually dedicate to the server?",
    "📋 Do you have any experience working on other servers?",
    "❓ Is there anything else you would like to add to your application?",
    "🏆 At what times will you be able to create tournaments?",
]

MODERATOR_QUESTIONS = [
    "🛡️ Why do you want to become a Moderator?",
    "📝 Why should we choose you?",
    "🕐 How much time can you dedicate to the server?",
    "📋 Do you have any moderation experience on other servers?",
    "⚖️ What would you do if your friend broke the rules?",
    "🧠 What would you do if two members started having a conflict?",
]


# =========================================================
# MAIN COG
# =========================================================

class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

        self.check_blocks.start()

        # Persistent views
        bot.add_view(TicketPanelView(self))
        bot.add_view(LanguageView(self))
        bot.add_view(IssueView(self))
        bot.add_view(ApplicationDecisionView(self))

    def cog_unload(self):
        self.check_blocks.cancel()

    # =====================================================
    # BACKGROUND BLOCK CHECK
    # =====================================================

    @tasks.loop(minutes=1)
    async def check_blocks(self):
        changed = False
        now = utc_now()

        for user_id, block in list(self.data["blocks"].items()):
            expires = parse_date(block["expires_at"])

            if now >= expires:
                guild_id = block.get("guild_id")
                guild = self.bot.get_guild(guild_id) if guild_id else None

                user = None

                if guild:
                    user = guild.get_member(int(user_id))

                if user is None:
                    try:
                        user = await self.bot.fetch_user(int(user_id))
                    except Exception:
                        user = None

                if user:
                    block_type = block["type"]

                    try:
                        await user.send(
                            f"✅ Your {block_type} application block has expired.\n\n"
                            f"You can now submit a new application."
                        )
                    except Exception:
                        pass

                del self.data["blocks"][user_id]
                changed = True

        if changed:
            save_data(self.data)

    @check_blocks.before_loop
    async def before_block_check(self):
        await self.bot.wait_until_ready()

    # =====================================================
    # PANEL
    # =====================================================

    @commands.group(name="ticket", invoke_without_command=True)
    @commands.is_owner()
    async def ticket(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "Available commands:\n"
                "`!ticket panel`\n"
                "`!ticket block <user> staff`\n"
                "`!ticket block <user> moder`",
                delete_after=10
            )

    @ticket.command(name="panel")
    @commands.is_owner()
    async def ticket_panel(self, ctx):
        panel_message_id = self.data["panel"].get("message_id")
        panel_channel_id = self.data["panel"].get("channel_id")

        # Check whether an existing panel still exists
        if panel_message_id and panel_channel_id:
            try:
                channel = self.bot.get_channel(panel_channel_id)

                if channel:
                    await channel.fetch_message(panel_message_id)

                    await ctx.send(
                        "Ticket panel has already been created.",
                        delete_after=5
                    )

                    try:
                        await ctx.message.delete()
                    except Exception:
                        pass

                    return

            except Exception:
                # Old panel was deleted, so a new one can be created.
                pass

        embed = discord.Embed(
            title="Support Center",
            description=(
                "Choose the type of request you want to create.\n\n"
                "🔵 **Support Ticket**\n"
                "For questions, reports, bugs and other support requests.\n\n"
                "🟢 **Staff┃|Host**\n"
                "Submit an application for Staff or Host.\n\n"
                "🔴 **Moderator**\n"
                "Submit an application for Moderator."
            ),
            color=discord.Color.blurple()
        )

        message = await ctx.send(
            embed=embed,
            view=TicketPanelView(self)
        )

        self.data["panel"]["message_id"] = message.id
        self.data["panel"]["channel_id"] = ctx.channel.id
        save_data(self.data)

        try:
            await ctx.message.delete()
        except Exception:
            pass

    # =====================================================
    # BLOCK COMMAND
    # =====================================================

    @ticket.command(name="block")
    @commands.is_owner()
    async def ticket_block(
        self,
        ctx,
        member: discord.Member,
        application_type: str
    ):
        application_type = application_type.lower()

        if application_type not in ("staff", "moder"):
            await ctx.send(
                "Use `staff` or `moder`.",
                delete_after=7
            )
            return

        now = utc_now()
        expires = add_one_month(now)

        self.data["blocks"][str(member.id)] = {
            "type": "Staff┃|Host" if application_type == "staff" else "Moderator",
            "blocked_at": now.isoformat(),
            "expires_at": expires.isoformat(),
            "guild_id": ctx.guild.id
        }

        save_data(self.data)

        block_name = (
            "Staff┃|Host"
            if application_type == "staff"
            else "Moderator"
        )

        embed = discord.Embed(
            title="🔒 Application Blocked",
            color=discord.Color.red()
        )

        embed.add_field(
            name="User",
            value=member.mention,
            inline=False
        )

        embed.add_field(
            name="Application",
            value=block_name,
            inline=True
        )

        embed.add_field(
            name="Blocked",
            value=format_date(now.isoformat()),
            inline=False
        )

        embed.add_field(
            name="Available again",
            value=format_date(expires.isoformat()),
            inline=False
        )

        await ctx.send(embed=embed)

        try:
            await member.send(
                f"🔒 Your **{block_name}** application has been blocked.\n\n"
                f"📅 Blocked: **{format_date(now.isoformat())}**\n"
                f"🔓 Available again: **{format_date(expires.isoformat())}**"
            )
        except Exception:
            pass

    # =====================================================
    # ANSWER COMMAND
    # !answer ticket 0001 message
    # =====================================================

    @commands.command(name="answer")
    async def answer(self, ctx, subcommand=None, number=None, *, text=None):
        if subcommand != "ticket" or number is None or not text:
            await ctx.send(
                "Usage: `!answer ticket <number> <message>`",
                delete_after=7
            )
            return

        if not isinstance(ctx.author, discord.Member) or not is_support(ctx.author):
            await ctx.send(
                "You do not have permission to use this command.",
                delete_after=5
            )
            return

        ticket = self.data["tickets"].get(str(number))

        if not ticket:
            await ctx.send(
                "Ticket not found.",
                delete_after=5
            )
            return

        if ticket.get("closed"):
            await ctx.send(
                "This ticket is already closed.",
                delete_after=5
            )
            return

        try:
            user = await self.bot.fetch_user(int(ticket["user_id"]))

            await user.send(
                f"**Support:** {text}"
            )

        except discord.Forbidden:
            await ctx.send(
                "I could not send a DM to this user.",
                delete_after=5
            )
            return

        channel = self.bot.get_channel(ticket["channel_id"])

        if channel:
            embed = discord.Embed(
                description=f"**Support:** {text}",
                color=discord.Color.light_grey()
            )
            embed.set_author(
                name=f"Support • {ctx.author.display_name}"
            )

            await channel.send(embed=embed)

        try:
            await ctx.message.delete()
        except Exception:
            pass

    # =====================================================
    # CLOSE COMMAND
    # !close ticket 0001
    # =====================================================

    @commands.command(name="close")
    async def close(self, ctx, subcommand=None, number=None):
        if subcommand != "ticket" or number is None:
            await ctx.send(
                "Usage: `!close ticket <number>`",
                delete_after=7
            )
            return

        if not isinstance(ctx.author, discord.Member) or not is_support(ctx.author):
            await ctx.send(
                "You do not have permission to use this command.",
                delete_after=5
            )
            return

        ticket = self.data["tickets"].get(str(number))

        if not ticket:
            await ctx.send(
                "Ticket not found.",
                delete_after=5
            )
            return

        if ticket.get("closed"):
            await ctx.send(
                "This ticket is already closed.",
                delete_after=5
            )
            return

        user_id = int(ticket["user_id"])

        try:
            user = await self.bot.fetch_user(user_id)

            close_channel = self.bot.get_channel(AFTER_CLOSE_CHANNEL_ID)

            if close_channel:
                link = close_channel.jump_url
            else:
                link = f"https://discord.com/channels/{ctx.guild.id}/{AFTER_CLOSE_CHANNEL_ID}"

            await user.send(
                "🔒 **Your ticket has been closed.**\n\n"
                f"To create a new ticket, go to {link}"
            )

        except Exception:
            pass

        ticket["closed"] = True
        save_data(self.data)

        channel = self.bot.get_channel(ticket["channel_id"])

        if channel:
            try:
                await channel.delete(
                    reason=f"Ticket {number} closed by {ctx.author}"
                )
            except Exception:
                pass

    # =====================================================
    # BUTTON: SUPPORT
    # =====================================================

    async def start_support(self, interaction):
        user_id = str(interaction.user.id)

        # Already has open support ticket
        for ticket in self.data["tickets"].values():
            if (
                str(ticket["user_id"]) == user_id
                and ticket["type"] == "support"
                and not ticket.get("closed")
            ):
                await interaction.response.send_message(
                    "🎫 You already have an open Support Ticket.",
                    ephemeral=True
                )
                return

        try:
            await interaction.user.send(
                "🌐 **Choose your language for the support ticket:**",
                view=LanguageView(self)
            )

            await interaction.response.send_message(
                "📩 Please check your DMs.",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I could not send you a DM. Please enable DMs from this server.",
                ephemeral=True
            )

    # =====================================================
    # BUTTON: STAFF / HOST
    # =====================================================

    async def start_application(self, interaction, app_type):
        user_id = str(interaction.user.id)

        # Block check
        block = self.data["blocks"].get(user_id)

        if block:
            expires = parse_date(block["expires_at"])

            if utc_now() < expires:
                correct_type = (
                    "Staff┃|Host"
                    if app_type == "staff"
                    else "Moderator"
                )

                if block["type"] == correct_type:
                    await interaction.response.send_message(
                        f"🔒 You cannot submit a **{correct_type}** application yet.\n\n"
                        f"📅 Blocked: **{format_date(block['blocked_at'])}**\n"
                        f"🔓 You can apply again: **{format_date(block['expires_at'])}**",
                        ephemeral=True
                    )
                    return

        # Existing application
        application = self.data["applications"].get(user_id)

        if application:
            if application.get("type") == app_type:
                await interaction.response.send_message(
                    "📋 You already have an active application of this type.",
                    ephemeral=True
                )
                return

        # Existing flow
        if user_id in self.data.get("application_flows", {}):
            flow = self.data["application_flows"][user_id]

            if flow.get("type") == app_type:
                await interaction.response.send_message(
                    "📋 You are already completing an application.",
                    ephemeral=True
                )
                return

        questions = (
            STAFF_QUESTIONS
            if app_type == "staff"
            else MODERATOR_QUESTIONS
        )

        self.data.setdefault("application_flows", {})

        self.data["application_flows"][user_id] = {
            "type": app_type,
            "step": 0,
            "answers": []
        }

        save_data(self.data)

        title = (
            "🟢 Staff┃|Host Application"
            if app_type == "staff"
            else "🔴 Moderator Application"
        )

        try:
            await interaction.user.send(
                f"{title}\n\n"
                f"**Question 1/{len(questions)}**\n"
                f"{questions[0]}"
            )

            await interaction.response.send_message(
                "📩 Please check your DMs.",
                ephemeral=True
            )

        except discord.Forbidden:
            del self.data["application_flows"][user_id]
            save_data(self.data)

            await interaction.response.send_message(
                "❌ I could not send you a DM. Please enable DMs from this server.",
                ephemeral=True
            )

    # =====================================================
    # LANGUAGE SELECT
    # =====================================================

    async def select_language(self, interaction, value):
        user_id = str(interaction.user.id)

        emoji, name, value_name = next(
            item for item in LANGUAGES if item[2] == value
        )

        # Store temporary support setup
        self.data.setdefault("support_flows", {})
        self.data["support_flows"][user_id] = {
            "language": name,
            "emoji": emoji
        }

        save_data(self.data)

        await interaction.response.edit_message(
            content=f"✅ **Language selected:** {emoji} {name}",
            view=None
        )

        await interaction.followup.send(
            "📌 **Choose the type of issue:**",
            view=IssueView(self)
        )

    # =====================================================
    # ISSUE SELECT
    # =====================================================

    async def select_issue(self, interaction, value):
        user_id = str(interaction.user.id)

        flow = self.data.get("support_flows", {}).get(user_id)

        if not flow:
            await interaction.response.send_message(
                "❌ This ticket setup has expired. Please start again.",
                ephemeral=True
            )
            return

        emoji, name, value_name = next(
            item for item in ISSUES if item[2] == value
        )

        flow["issue"] = name
        flow["issue_emoji"] = emoji

        save_data(self.data)

        await interaction.response.edit_message(
            content=f"✅ **Issue selected:** {emoji} {name}",
            view=None
        )

        ticket = await self.create_support_ticket(
            interaction.user,
            flow
        )

        if ticket:
            del self.data["support_flows"][user_id]
            save_data(self.data)

            await interaction.followup.send(
                "🎫 **Support request created**\n\n"
                "Your request is now in our support system.\n\n"
                f"🌐 **Language:** {flow['emoji']} {flow['language']}\n"
                f"📌 **Issue:** {flow['issue_emoji']} {flow['issue']}\n\n"
                "📝 **Tell us what happened**\n"
                "Send your problem in your next message. You can also include "
                "useful details or screenshots.\n\n"
                "💬 **Stay in this DM**\n"
                "Our support team will review your request and contact you here."
            )

    # =====================================================
    # CREATE SUPPORT TICKET
    # =====================================================

    async def create_support_ticket(self, user, flow):
        guild = self.bot.guilds[0]

        category = get_category(guild)

        if category is None:
            try:
                await user.send(
                    "❌ The ticket category could not be found."
                )
            except Exception:
                pass
            return None

        number = self.data["next_ticket"]
        self.data["next_ticket"] += 1

        number_text = ticket_number(number)

        channel_name = f"🛠️┃| {user.display_name}"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )
        }

        support_role = guild.get_role(SUPPORT_ROLE_ID)

        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )

        if guild.me:
            overwrites[guild.me] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True
            )

        try:
            channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                reason=f"Support Ticket #{number_text}"
            )

        except Exception as e:
            try:
                await user.send(
                    f"❌ I could not create your ticket channel.\n`{e}`"
                )
            except Exception:
                pass

            return None

        self.data["tickets"][number_text] = {
            "user_id": user.id,
            "channel_id": channel.id,
            "type": "support",
            "closed": False,
            "language": flow["language"],
            "language_emoji": flow["emoji"],
            "issue": flow["issue"],
            "issue_emoji": flow["issue_emoji"],
            "created_at": iso_now()
        }

        save_data(self.data)

        embed = discord.Embed(
            title=f"🎫 Support Ticket #{number_text}",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="User",
            value=f"{user.mention}\n`{user}`",
            inline=False
        )

        embed.add_field(
            name="Language",
            value=f"{flow['emoji']} {flow['language']}",
            inline=True
        )

        embed.add_field(
            name="Issue",
            value=f"{flow['issue_emoji']} {flow['issue']}",
            inline=True
        )

        embed.set_footer(
            text=f"Ticket #{number_text}"
        )

        await channel.send(
            content=support_role.mention if support_role else None,
            embed=embed
        )

        return {
            "number": number_text,
            "channel": channel
        }

    # =====================================================
    # APPLICATION ANSWER
    # =====================================================

    async def process_application_message(self, message):
        user_id = str(message.author.id)

        flows = self.data.get("application_flows", {})
        flow = flows.get(user_id)

        if not flow:
            return False

        if not message.guild is None:
            return False

        questions = (
            STAFF_QUESTIONS
            if flow["type"] == "staff"
            else MODERATOR_QUESTIONS
        )

        step = flow["step"]

        answer = message.content.strip()

        if not answer and message.attachments:
            answer = "[Attachment]"

        if not answer:
            return True

        flow["answers"].append(answer)
        flow["step"] += 1

        # More questions
        if flow["step"] < len(questions):
            save_data(self.data)

            await message.channel.send(
                f"**Question {flow['step'] + 1}/{len(questions)}**\n"
                f"{questions[flow['step']]}"
            )

            return True

        # Finished
        app_type = flow["type"]
        answers = flow["answers"]

        del self.data["application_flows"][user_id]

        application = await self.create_application(
            message.author,
            app_type,
            answers
        )

        if application:
            self.data["applications"][user_id] = {
                "type": app_type,
                "channel_id": application["channel"].id,
                "ticket_number": application["number"],
                "submitted_at": iso_now()
            }

            save_data(self.data)

            await message.channel.send(
                "✅ **Application submitted!**\n\n"
                "Please wait **1–2 days** and we will contact you with the result."
            )

        else:
            save_data(self.data)

            await message.channel.send(
                "❌ Your application could not be created. Please contact support."
            )

        return True

    # =====================================================
    # CREATE APPLICATION CHANNEL
    # =====================================================

    async def create_application(self, user, app_type, answers):
        guild = self.bot.guilds[0]
        category = get_category(guild)

        if category is None:
            return None

        number = self.data["next_ticket"]
        self.data["next_ticket"] += 1

        number_text = ticket_number(number)

        channel_name = f"🛠️┃| {user.display_name}"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )
        }

        support_role = guild.get_role(SUPPORT_ROLE_ID)

        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )

        if guild.me:
            overwrites[guild.me] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True
            )

        channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            reason=f"{app_type} application #{number_text}"
        )

        title = (
            "🟢 Staff┃|Host Application"
            if app_type == "staff"
            else "🔴 Moderator Application"
        )

        embed = discord.Embed(
            title=title,
            color=(
                discord.Color.green()
                if app_type == "staff"
                else discord.Color.red()
            )
        )

        embed.add_field(
            name="Applicant",
            value=f"{user.mention}\n`{user}`",
            inline=False
        )

        embed.add_field(
            name="Application",
            value=app_type,
            inline=True
        )

        embed.add_field(
            name="Ticket",
            value=f"#{number_text}",
            inline=True
        )

        await channel.send(
            content=support_role.mention if support_role else None,
            embed=embed,
            view=ApplicationDecisionView(self)
        )

        for index, answer in enumerate(answers, start=1):
            question = (
                STAFF_QUESTIONS[index - 1]
                if app_type == "staff"
                else MODERATOR_QUESTIONS[index - 1]
            )

            answer_embed = discord.Embed(
                color=discord.Color.light_grey()
            )

            answer_embed.add_field(
                name=question,
                value=answer[:1024],
                inline=False
            )

            await channel.send(embed=answer_embed)

        return {
            "number": number_text,
            "channel": channel
        }

    # =====================================================
    # APPLICATION DECISION
    # =====================================================

    async def decide_application(
        self,
        interaction,
        accepted
    ):
        if not isinstance(interaction.user, discord.Member):
            return

        if not is_support(interaction.user):
            await interaction.response.send_message(
                "❌ You do not have permission to decide applications.",
                ephemeral=True
            )
            return

        channel_id = interaction.channel.id

        target_user_id = None
        application_type = None

        for user_id, application in self.data["applications"].items():
            if application.get("channel_id") == channel_id:
                target_user_id = int(user_id)
                application_type = application["type"]
                break

        if target_user_id is None:
            await interaction.response.send_message(
                "❌ Application not found.",
                ephemeral=True
            )
            return

        try:
            user = await self.bot.fetch_user(target_user_id)
        except Exception:
            user = None

        if accepted:
            result_text = (
                "✅ **Your application has been accepted!**\n\n"
                "Congratulations! A member of the team will contact you "
                "with the next steps."
            )
        else:
            result_text = (
                "❌ **Your application has been rejected.**\n\n"
                "Thank you for taking the time to apply."
            )

        if user:
            try:
                await user.send(result_text)
            except Exception:
                pass

        await interaction.response.edit_message(
            content=(
                "✅ **Application Accepted**"
                if accepted
                else "❌ **Application Rejected**"
            ),
            embed=None,
            view=None
        )

        del self.data["applications"][str(target_user_id)]
        save_data(self.data)

        await interaction.channel.send(
            f"{'✅ Accepted' if accepted else '❌ Rejected'} "
            f"by {interaction.user.mention}."
        )

        await interaction.channel.delete(
            reason=(
                "Application accepted"
                if accepted
                else "Application rejected"
            )
        )

    # =====================================================
    # DM LISTENER
    # =====================================================

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.guild is not None:
            return

        # Application answers
        handled = await self.process_application_message(message)

        if handled:
            return

        # Support ticket messages
        user_id = str(message.author.id)

        ticket = None
        ticket_number_found = None

        for number, data in self.data["tickets"].items():
            if (
                str(data["user_id"]) == user_id
                and data["type"] == "support"
                and not data.get("closed")
            ):
                ticket = data
                ticket_number_found = number
                break

        if not ticket:
            return

        channel = self.bot.get_channel(ticket["channel_id"])

        if not channel:
            return

        embed = discord.Embed(
            description=message.content or "[No text]",
            color=discord.Color.blurple()
        )

        embed.set_author(
            name=f"{message.author} • User"
        )

        embed.set_footer(
            text=f"Ticket #{ticket_number_found}"
        )

        files = []

        for attachment in message.attachments[:10]:
            try:
                files.append(await attachment.to_file())
            except Exception:
                pass

        await channel.send(
            embed=embed,
            files=files
        )


# =========================================================
# PANEL VIEW
# =========================================================

class TicketPanelView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Support Ticket",
        emoji="🎫",
        style=discord.ButtonStyle.primary,
        custom_id="ticket:support"
    )
    async def support(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.cog.start_support(interaction)

    @discord.ui.button(
        label="Staff┃|Host",
        emoji="🛡️",
        style=discord.ButtonStyle.success,
        custom_id="ticket:staff"
    )
    async def staff(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.cog.start_application(
            interaction,
            "staff"
        )

    @discord.ui.button(
        label="Moderator",
        emoji="🔨",
        style=discord.ButtonStyle.danger,
        custom_id="ticket:moderator"
    )
    async def moderator(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.cog.start_application(
            interaction,
            "moderator"
        )


# =========================================================
# LANGUAGE VIEW
# =========================================================

class LanguageView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

        options = [
            discord.SelectOption(
                label=name,
                value=value,
                emoji=emoji
            )
            for emoji, name, value in LANGUAGES
        ]

        select = discord.ui.Select(
            placeholder="Choose your language",
            options=options,
            custom_id="ticket:language"
        )

        select.callback = self.callback
        self.add_item(select)

    async def callback(self, interaction):
        value = interaction.data["values"][0]
        await self.cog.select_language(
            interaction,
            value
        )


# =========================================================
# ISSUE VIEW
# =========================================================

class IssueView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

        options = [
            discord.SelectOption(
                label=name,
                value=value,
                emoji=emoji
            )
            for emoji, name, value in ISSUES
        ]

        select = discord.ui.Select(
            placeholder="Choose your issue",
            options=options,
            custom_id="ticket:issue"
        )

        select.callback = self.callback
        self.add_item(select)

    async def callback(self, interaction):
        value = interaction.data["values"][0]
        await self.cog.select_issue(
            interaction,
            value
        )


# =========================================================
# ACCEPT / REJECT VIEW
# =========================================================

class ApplicationDecisionView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Accept",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="ticket:application_accept"
    )
    async def accept(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.cog.decide_application(
            interaction,
            True
        )

    @discord.ui.button(
        label="Reject",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="ticket:application_reject"
    )
    async def reject(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.cog.decide_application(
            interaction,
            False
        )


# =========================================================
# SETUP
# =========================================================

async def setup(bot):
    await bot.add_cog(TicketCog(bot)) 
