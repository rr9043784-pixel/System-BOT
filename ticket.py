import os
import json
import calendar
from datetime import datetime, timedelta

import discord
from discord.ext import commands, tasks


# =========================
# SETTINGS
# =========================

OWNER_ID = 1176149190192152626

TICKET_CATEGORY_ID = 1555925139546439700
SUPPORT_ROLE_ID = 1527295101867524106
AFTER_CLOSE_CHANNEL_ID = 1527278068526219305

# Role given after application is accepted
STAFF_HOST_ROLE_ID = 1542739534343700500
MODERATOR_ROLE_ID = 1539734753736134856

DATA_FILE = "ticket_data.json"


# =========================
# DATA
# =========================

DEFAULT_DATA = {
    "panel": None,
    "next_ticket": 1,
    "tickets": {},
    "applications": {},
    "blocks": {}
}


def load_data():
    if not os.path.exists(DATA_FILE):
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
        json.dump(data, f, indent=4, ensure_ascii=False)


# =========================
# HELPERS
# =========================

def is_owner(member):
    return member.id == OWNER_ID


def is_support(member):
    return any(role.id == SUPPORT_ROLE_ID for role in member.roles)


def is_owner_or_support(member):
    return is_owner(member) or is_support(member)


def get_ticket_number(channel_id):
    data = load_data()

    for number, ticket in data["tickets"].items():
        if ticket.get("channel_id") == channel_id:
            return number

    return None


def get_application(channel_id):
    data = load_data()
    return data["applications"].get(str(channel_id))


def has_role(member, role_id):
    return any(role.id == role_id for role in member.roles)


# =========================
# LANGUAGES
# =========================

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


# =========================
# ISSUES
# =========================

ISSUES = [
    ("❓", "Question"),
    ("🚨", "Report"),
    ("🐛", "Bug"),
    ("🤖", "Bot Bug"),
    ("📌", "Other"),
]


# =========================
# APPLICATION QUESTIONS
# =========================

STAFF_HOST_QUESTIONS = [
    "🛡️ Which role are you applying for — Staff or Host?",
    "📝 Why do you want this role and why do you think you are suitable for it?",
    "🕐 How much time can you usually dedicate to the server?",
    "📋 Do you have any experience working on other servers?",
    "❓ Is there anything else you would like to add to your application?",
    "🏆 At what times will you be able to create tournaments?"
]


MODERATOR_QUESTIONS = [
    "🛡️ Why do you want to become a Moderator?",
    "📝 Why should we choose you?",
    "🕐 How much time can you dedicate to the server?",
    "📋 Do you have any moderation experience on other servers?",
    "⚖️ What would you do if your friend broke the rules?",
    "🧠 What would you do if two members started having a conflict?"
]


# =========================
# COG
# =========================

class TicketCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.check_blocks.start()

        # Persistent views
        bot.add_view(TicketPanelView(self))
        bot.add_view(LanguageView(self))
        bot.add_view(IssueView(self))
        bot.add_view(ApplicationDecisionView(self))

    def cog_unload(self):
        self.check_blocks.cancel()

    # =========================
    # BLOCK CHECKER
    # =========================

    @tasks.loop(minutes=1)
    async def check_blocks(self):
        data = load_data()

        changed = False
        now = datetime.utcnow().timestamp()

        for user_id, user_blocks in list(data["blocks"].items()):

            if not isinstance(user_blocks, dict):
                continue

            for block_type, expires_at in list(user_blocks.items()):

                if expires_at <= now:
                    del user_blocks[block_type]
                    changed = True

                    try:
                        user = await self.bot.fetch_user(int(user_id))

                        if block_type == "staff":
                            role_name = "Staff┃| Host"
                        else:
                            role_name = "Moderator"

                        await user.send(
                            f"**Ticket:** Your **{role_name}** application block has expired. "
                            f"You can apply again."
                        )

                    except Exception:
                        pass

            if not user_blocks:
                del data["blocks"][user_id]

        if changed:
            save_data(data)

    @check_blocks.before_loop
    async def before_check_blocks(self):
        await self.bot.wait_until_ready()

    # =========================
    # !ticket
    # =========================

    @commands.group(name="ticket", invoke_without_command=True)
    async def ticket(self, ctx):
        if not is_owner(ctx.author):
            return

        await ctx.send(
            "**Ticket Commands:**\n"
            "`!ticket panel`\n"
            "`!ticket block <user> staff`\n"
            "`!ticket block <user> moder`"
        )

    # =========================
    # !ticket panel
    # =========================

    @ticket.command(name="panel")
    async def ticket_panel(self, ctx):

        if not is_owner(ctx.author):
            return

        data = load_data()

        # Don't create duplicate panel
        if data.get("panel"):
            try:
                channel = self.bot.get_channel(data["panel"]["channel_id"])

                if channel:
                    await channel.fetch_message(data["panel"]["message_id"])

                    await ctx.message.delete()
                    return

            except Exception:
                pass

        embed = discord.Embed(
            title="Support & Applications",
            description=(
                "Choose an option below.\n\n"
                "🛠️ **Support Ticket**\n"
                "Contact the support team.\n\n"
                "🛡️ **Staff┃| Host**\n"
                "Apply for Staff or Host.\n\n"
                "🔨 **Moderator**\n"
                "Apply for Moderator."
            ),
            color=discord.Color.dark_gray()
        )

        message = await ctx.send(
            embed=embed,
            view=TicketPanelView(self)
        )

        data["panel"] = {
            "channel_id": message.channel.id,
            "message_id": message.id
        }

        save_data(data)

        try:
            await ctx.message.delete()
        except Exception:
            pass

    # =========================
    # !ticket block
    # =========================

    @ticket.command(name="block")
    async def ticket_block(self, ctx, user: discord.Member = None, block_type: str = None):

        if not is_owner(ctx.author):
            return

        if user is None or block_type is None:
            await ctx.send(
                "Usage: `!ticket block <user> staff` or "
                "`!ticket block <user> moder`",
                delete_after=5
            )
            return

        block_type = block_type.lower()

        if block_type not in ("staff", "moder"):
            await ctx.send(
                "Invalid type. Use `staff` or `moder`.",
                delete_after=5
            )
            return

        data = load_data()

        user_id = str(user.id)

        if user_id not in data["blocks"]:
            data["blocks"][user_id] = {}

        expires = (
            datetime.utcnow() + timedelta(days=30)
        ).timestamp()

        data["blocks"][user_id][block_type] = expires

        save_data(data)

        role_name = "Staff┃| Host" if block_type == "staff" else "Moderator"

        try:
            await user.send(
                f"**Ticket:** You have been blocked from applying for "
                f"**{role_name}** for 1 month."
            )
        except Exception:
            pass

        await ctx.send(
            f"Blocked {user.mention} from **{role_name}** applications for 1 month.",
            delete_after=5
        )

    # =========================
    # !answer ticket
    # =========================

    @commands.command(name="answer")
    async def answer(self, ctx, ticket_word=None, ticket_number=None, *, message=None):

        if not is_owner_or_support(ctx.author):
            return

        if ticket_word != "ticket" or ticket_number is None or message is None:
            return

        data = load_data()

        ticket = data["tickets"].get(str(ticket_number))

        if not ticket:
            return

        user_id = ticket.get("user_id")
        channel_id = ticket.get("channel_id")

        try:
            user = await self.bot.fetch_user(int(user_id))
        except Exception:
            return

        try:
            await user.send(f"**Support:** {message}")
        except Exception:
            pass

        channel = self.bot.get_channel(channel_id)

        if channel:
            await channel.send(
                f"**Support:** {message}"
            )

    # =========================
    # !close ticket
    # =========================

    @commands.command(name="close")
    async def close(self, ctx, ticket_word=None, ticket_number=None):

        if not is_owner_or_support(ctx.author):
            return

        if ticket_word != "ticket" or ticket_number is None:
            return

        data = load_data()

        ticket = data["tickets"].get(str(ticket_number))

        if not ticket:
            return

        user_id = ticket.get("user_id")
        channel_id = ticket.get("channel_id")

        try:
            user = await self.bot.fetch_user(int(user_id))
        except Exception:
            user = None

        after_channel = self.bot.get_channel(AFTER_CLOSE_CHANNEL_ID)

        after_link = (
            after_channel.mention
            if after_channel
            else "the after-close channel"
        )

        if user:
            try:
                await user.send(
                    f"**Support:** Your ticket has been closed.\n"
                    f"You can continue here: {after_link}"
                )
            except Exception:
                pass

        channel = self.bot.get_channel(channel_id)

        if channel:
            try:
                await channel.delete()
            except Exception:
                pass

        del data["tickets"][str(ticket_number)]
        save_data(data)


    # =========================
    # CREATE APPLICATION
    # =========================

    async def start_application(self, interaction, application_type):

        member = interaction.user

        # =================================
        # ROLE CHECK
        # =================================

        if application_type == "staff":

            if has_role(member, STAFF_HOST_ROLE_ID):
                await interaction.response.send_message(
                    "❌ You already have the **Staff┃| Host** role.",
                    ephemeral=True
                )
                return

            role_name = "Staff┃| Host"

        else:

            if has_role(member, MODERATOR_ROLE_ID):
                await interaction.response.send_message(
                    "❌ You already have the **Moderator** role.",
                    ephemeral=True
                )
                return

            role_name = "Moderator"

        # =================================
        # BLOCK CHECK
        # =================================

        data = load_data()

        user_blocks = data["blocks"].get(str(member.id), {})

        if application_type in user_blocks:

            expires_at = user_blocks[application_type]

            if expires_at > datetime.utcnow().timestamp():

                expires = datetime.fromtimestamp(expires_at).strftime(
                    "%d.%m.%Y"
                )

                await interaction.response.send_message(
                    f"❌ You are blocked from applying for "
                    f"**{role_name}** until **{expires}**.",
                    ephemeral=True
                )
                return

        # =================================
        # EXISTING APPLICATION
        # =================================

        for application in data["applications"].values():

            if application.get("user_id") == member.id:
                await interaction.response.send_message(
                    "❌ You already have an active application.",
                    ephemeral=True
                )
                return

        await interaction.response.send_message(
            "📩 Check your DMs.",
            ephemeral=True
        )

        try:
            await member.send(
                f"**Application:** You are applying for **{role_name}**.\n\n"
                "Please answer the questions below."
            )
        except Exception:
            return

        questions = (
            STAFF_HOST_QUESTIONS
            if application_type == "staff"
            else MODERATOR_QUESTIONS
        )

        answers = []

        for question in questions:

            try:
                await member.send(question)

                def check(message):
                    return (
                        message.author.id == member.id
                        and isinstance(message.channel, discord.DMChannel)
                    )

                answer = await self.bot.wait_for(
                    "message",
                    timeout=1800,
                    check=check
                )

                answers.append(answer.content)

            except Exception:

                try:
                    await member.send(
                        "❌ Your application timed out."
                    )
                except Exception:
                    pass

                return

        guild = interaction.guild

        category = guild.get_channel(TICKET_CATEGORY_ID)

        if category is None:
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),

            member: discord.PermissionOverwrite(
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

        overwrites[guild.me] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            manage_channels=True
        )

        channel = await guild.create_text_channel(
            name=f"🛠️┃| {member.display_name}",
            category=category,
            overwrites=overwrites
        )

        application_id = str(channel.id)

        data = load_data()

        data["applications"][application_id] = {
            "user_id": member.id,
            "type": application_type,
            "role_name": role_name,
            "answers": answers,
            "channel_id": channel.id
        }

        save_data(data)

        embed = discord.Embed(
            title=f"{role_name} Application",
            color=discord.Color.dark_gray()
        )

        embed.set_author(
            name=str(member),
            icon_url=member.display_avatar.url
        )

        for index, answer in enumerate(answers):

            if application_type == "staff":
                question = STAFF_HOST_QUESTIONS[index]
            else:
                question = MODERATOR_QUESTIONS[index]

            embed.add_field(
                name=question,
                value=answer[:1024] if answer else "No answer",
                inline=False
            )

        embed.set_footer(
            text=f"Applicant ID: {member.id}"
        )

        await channel.send(
            content=f"<@&{SUPPORT_ROLE_ID}>",
            embed=embed,
            view=ApplicationDecisionView(self)
        )

        try:
            await member.send(
                f"**Application:** Your **{role_name}** application "
                f"has been submitted successfully."
            )
        except Exception:
            pass

    # =========================
    # SUPPORT TICKET
    # =========================

    async def create_support_ticket(
        self,
        interaction,
        language,
        issue
    ):

        member = interaction.user
        guild = interaction.guild

        data = load_data()

        # Only one support ticket
        for ticket in data["tickets"].values():

            if ticket.get("user_id") == member.id:

                await interaction.response.send_message(
                    "❌ You already have an open Support Ticket.",
                    ephemeral=True
                )
                return

        await interaction.response.send_message(
            "📩 Check your DMs.",
            ephemeral=True
        )

        category = guild.get_channel(TICKET_CATEGORY_ID)

        if category is None:
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),

            member: discord.PermissionOverwrite(
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

        overwrites[guild.me] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            manage_channels=True
        )

        number = data["next_ticket"]
        data["next_ticket"] += 1

        channel = await guild.create_text_channel(
            name=f"🛠️┃| {member.display_name}",
            category=category,
            overwrites=overwrites
        )

        data["tickets"][str(number)] = {
            "user_id": member.id,
            "channel_id": channel.id,
            "language": language,
            "issue": issue
        }

        save_data(data)

        await channel.send(
            f"<@&{SUPPORT_ROLE_ID}>\n"
            f"**Ticket #{number}**\n\n"
            f"**User:** {member.mention}\n"
            f"**Language:** {language}\n"
            f"**Issue:** {issue}\n\n"
            f"Waiting for the user's message..."
        )

        try:
            await member.send(
                f"**Support Ticket #{number}** has been created successfully.\n\n"
                "Please send your problem in this DM."
            )
        except Exception:
            pass

    # =========================
    # DM LISTENER
    # =========================

    @commands.Cog.listener()
    async def on_message(self, message):

        # IMPORTANT:
        # Do not process guild commands here.
        # main.py should call bot.process_commands(message) once.
        if message.guild is not None:
            return

        if message.author.bot:
            return

        data = load_data()

        for number, ticket in data["tickets"].items():

            if ticket.get("user_id") != message.author.id:
                continue

            channel = self.bot.get_channel(
                ticket.get("channel_id")
            )

            if channel:

                await channel.send(
                    f"**User:** {message.content}"
                )

            try:
                await message.channel.send(
                    "✅ Your message has been sent to the support team."
                )
            except Exception:
                pass

            return


# =========================
# PANEL VIEW
# =========================

class TicketPanelView(discord.ui.View):

    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Support Ticket",
        emoji="🛠️",
        style=discord.ButtonStyle.secondary,
        custom_id="ticket_support"
    )
    async def support(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_message(
            "📩 Check your DMs.",
            ephemeral=True
        )

        try:
            await interaction.user.send(
                "**Support Ticket**\n\n"
                "Please select your language:",
                view=LanguageView(self.cog)
            )
        except Exception:
            pass

    @discord.ui.button(
        label="Staff┃| Host",
        emoji="🛡️",
        style=discord.ButtonStyle.secondary,
        custom_id="ticket_staff_host"
    )
    async def staff(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        member = interaction.user

        if has_role(member, STAFF_HOST_ROLE_ID):
            await interaction.response.send_message(
                "❌ You already have the **Staff┃| Host** role.",
                ephemeral=True
            )
            return

        await self.cog.start_application(
            interaction,
            "staff"
        )

    @discord.ui.button(
        label="Moderator",
        emoji="🔨",
        style=discord.ButtonStyle.secondary,
        custom_id="ticket_moderator"
    )
    async def moderator(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        member = interaction.user

        if has_role(member, MODERATOR_ROLE_ID):
            await interaction.response.send_message(
                "❌ You already have the **Moderator** role.",
                ephemeral=True
            )
            return

        await self.cog.start_application(
            interaction,
            "moder"
        )


# =========================
# LANGUAGE VIEW
# =========================

class LanguageView(discord.ui.View):

    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.select(
        placeholder="Select your language",
        custom_id="ticket_language",
        options=[
            discord.SelectOption(
                label=name,
                emoji=emoji,
                value=value
            )
            for emoji, name, value in LANGUAGES
        ]
    )
    async def language(
        self,
        interaction: discord.Interaction,
        select: discord.ui.Select
    ):

        language = select.values[0]

        await interaction.response.edit_message(
            content=f"Language selected: **{language}**\n\n"
                    "Now select your issue.",
            view=IssueView(self.cog)
        )


# =========================
# ISSUE VIEW
# =========================

class IssueView(discord.ui.View):

    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.select(
        placeholder="Select your issue",
        custom_id="ticket_issue",
        options=[
            discord.SelectOption(
                label=label,
                emoji=emoji,
                value=label
            )
            for emoji, label in ISSUES
        ]
    )
    async def issue(
        self,
        interaction: discord.Interaction,
        select: discord.ui.Select
    ):

        issue = select.values[0]

        # We need language from the previous message.
        # If unavailable, use English.
        language = "English"

        await interaction.response.edit_message(
            content=(
                f"Language: **{language}**\n"
                f"Issue: **{issue}**\n\n"
                "Creating your ticket..."
            ),
            view=None
        )

        await self.cog.create_support_ticket(
            interaction,
            language,
            issue
        )


# =========================
# APPLICATION DECISION VIEW
# =========================

class ApplicationDecisionView(discord.ui.View):

    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Accept",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="application_accept"
    )
    async def accept(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not is_owner_or_support(interaction.user):
            await interaction.response.send_message(
                "❌ You do not have permission to do this.",
                ephemeral=True
            )
            return

        application = get_application(
            interaction.channel.id
        )

        if not application:
            await interaction.response.send_message(
                "❌ Application data was not found.",
                ephemeral=True
            )
            return

        guild = interaction.guild

        user_id = application["user_id"]
        application_type = application["type"]

        member = guild.get_member(user_id)

        if member is None:
            try:
                member = await guild.fetch_member(user_id)
            except Exception:
                await interaction.response.send_message(
                    "❌ I could not find the applicant in the server.",
                    ephemeral=True
                )
                return

        # =========================
        # SELECT ROLE
        # =========================

        if application_type == "staff":
            role_id = STAFF_HOST_ROLE_ID
            role_name = "Staff┃| Host"
        else:
            role_id = MODERATOR_ROLE_ID
            role_name = "Moderator"

        role = guild.get_role(role_id)

        if role is None:
            await interaction.response.send_message(
                f"❌ The **{role_name}** role was not found.",
                ephemeral=True
            )
            return

        # =========================
        # ROLE HIERARCHY CHECK
        # =========================

        if guild.me.top_role <= role:
            await interaction.response.send_message(
                f"❌ I cannot give **{role_name}** because my bot role "
                f"is not higher than that role.",
                ephemeral=True
            )
            return

        # =========================
        # GIVE ROLE
        # =========================

        try:
            await member.add_roles(
                role,
                reason="Application accepted"
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                f"❌ I could not give **{role_name}** to the applicant.\n"
                "Please check my Manage Roles permission and role hierarchy.",
                ephemeral=True
            )
            return

        except Exception:
            await interaction.response.send_message(
                f"❌ An error occurred while giving **{role_name}**.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"✅ Application accepted. **{role_name}** has been given.",
            ephemeral=True
        )

        # Disable buttons before deletion
        for item in self.children:
            item.disabled = True

        try:
            await interaction.message.edit(
                view=self
            )
        except Exception:
            pass

        try:
            await member.send(
                f"🎉 **Your application has been accepted!**\n\n"
                f"You have received the **{role_name}** role."
            )
        except Exception:
            pass

        data = load_data()

        data["applications"].pop(
            str(interaction.channel.id),
            None
        )

        save_data(data)

        await interaction.channel.delete()

    @discord.ui.button(
        label="Reject",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="application_reject"
    )
    async def reject(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not is_owner_or_support(interaction.user):
            await interaction.response.send_message(
                "❌ You do not have permission to do this.",
                ephemeral=True
            )
            return

        application = get_application(
            interaction.channel.id
        )

        if not application:
            await interaction.response.send_message(
                "❌ Application data was not found.",
                ephemeral=True
            )
            return

        user_id = application["user_id"]

        try:
            member = await interaction.guild.fetch_member(
                user_id
            )
        except Exception:
            member = None

        await interaction.response.send_message(
            "❌ Application rejected.",
            ephemeral=True
        )

        if member:
            try:
                await member.send(
                    "❌ **Your application has been rejected.**"
                )
            except Exception:
                pass

        data = load_data()

        data["applications"].pop(
            str(interaction.channel.id),
            None
        )

        save_data(data)

        await interaction.channel.delete()


# =========================
# SETUP
# =========================

async def setup(bot):
    await bot.add_cog(TicketCog(bot))
