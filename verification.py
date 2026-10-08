import os
import json
import time

import discord
from discord.ext import commands, tasks


# =========================================================
# SETTINGS
# =========================================================

OWNER_ID = 1176149190192152626

# Channel where the verification panel is sent
VERIFICATION_CHANNEL_ID = 1546998884830683176

# Channel where verification applications are sent
APPLICATIONS_CHANNEL_ID = 1547237068315566180

# Channel users must use/select before verification
SELECTION_CHANNEL_ID = 1541336807508017252

# Role given after successful verification
VERIFIED_ROLE_ID = 1546987754968326154

# Data file
DATA_FILE = "verification_data.json"

# 15 days
BLACKLIST_DURATION = 15 * 24 * 60 * 60


# =========================================================
# DATA
# =========================================================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "applications": {},
            "blacklist": {}
        }

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            data = {}

        data.setdefault("applications", {})
        data.setdefault("blacklist", {})

        return data

    except Exception:
        return {
            "applications": {},
            "blacklist": {}
        }


DATA = load_data()


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(DATA, file, indent=4, ensure_ascii=False)


# =========================================================
# HELPERS
# =========================================================

def get_user_application(user_id):
    return DATA["applications"].get(str(user_id))


def find_application_by_message(message_id):
    message_id = int(message_id)

    for user_id, application in DATA["applications"].items():
        if application.get("message_id") == message_id:
            return user_id, application

    return None, None


def is_blacklisted(user_id):
    user_id = str(user_id)

    entry = DATA["blacklist"].get(user_id)

    if not entry:
        return False

    expires_at = entry.get("expires_at", 0)

    if time.time() >= expires_at:
        return False

    return True


def get_blacklist_expiration(user_id):
    entry = DATA["blacklist"].get(str(user_id))

    if not entry:
        return None

    return entry.get("expires_at")


# =========================================================
# VERIFICATION MODAL
# =========================================================

class VerificationModal(discord.ui.Modal, title="Server Verification"):

    reason = discord.ui.TextInput(
        label="Why do you want to join this server?",
        placeholder="Tell us why you want to join this server...",
        style=discord.TextStyle.paragraph,
        required=True,
        min_length=5,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):

        user_id = str(interaction.user.id)

        # -------------------------------------------------
        # BLACKLIST CHECK
        # -------------------------------------------------

        if is_blacklisted(interaction.user.id):

            expires_at = get_blacklist_expiration(
                interaction.user.id
            )

            if expires_at:

                timestamp = int(expires_at)

                await interaction.response.send_message(
                    "❌ You cannot submit a new verification application yet.\n"
                    f"Your waiting period ends <t:{timestamp}:R> "
                    f"(<t:{timestamp}:F>).",
                    ephemeral=True
                )

            else:

                await interaction.response.send_message(
                    "❌ You cannot submit a new verification application yet.",
                    ephemeral=True
                )

            return

        # -------------------------------------------------
        # EXISTING APPLICATION
        # -------------------------------------------------

        existing = get_user_application(
            interaction.user.id
        )

        if existing:

            status = existing.get("status")

            if status == "pending":

                await interaction.response.send_message(
                    "⏳ You already have a verification application "
                    "waiting for review.\n"
                    "Please wait for a decision.",
                    ephemeral=True
                )

                return

            if status == "accepted":

                await interaction.response.send_message(
                    "✅ Your verification application has already been accepted.",
                    ephemeral=True
                )

                return

        # -------------------------------------------------
        # APPLICATION CHANNEL
        # -------------------------------------------------

        channel = interaction.client.get_channel(
            APPLICATIONS_CHANNEL_ID
        )

        if channel is None:

            await interaction.response.send_message(
                "❌ The verification system is currently unavailable.",
                ephemeral=True
            )

            return

        # -------------------------------------------------
        # APPLICATION EMBED
        # -------------------------------------------------

        embed = discord.Embed(
            title="🛡️ New Verification Application",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="👤 User",
            value=(
                f"{interaction.user.mention}\n"
                f"`{interaction.user}`\n"
                f"ID: `{interaction.user.id}`"
            ),
            inline=False
        )

        embed.add_field(
            name="📝 Why do you want to join?",
            value=str(self.reason.value),
            inline=False
        )

        embed.add_field(
            name="📊 Status",
            value="⏳ Pending",
            inline=False
        )

        embed.set_thumbnail(
            url=interaction.user.display_avatar.url
        )

        embed.set_footer(
            text="Verification System"
        )

        # -------------------------------------------------
        # SEND APPLICATION
        # -------------------------------------------------

        message = await channel.send(
            embed=embed,
            view=ApplicationView()
        )

        # -------------------------------------------------
        # SAVE APPLICATION
        # -------------------------------------------------

        DATA["applications"][user_id] = {
            "message_id": message.id,
            "channel_id": APPLICATIONS_CHANNEL_ID,
            "reason": str(self.reason.value),
            "status": "pending",
            "created_at": time.time()
        }

        save_data()

        # -------------------------------------------------
        # USER RESPONSE
        # -------------------------------------------------

        await interaction.response.send_message(
            "✅ Your verification application has been sent for review.\n"
            "Please wait a little.",
            ephemeral=True
        )


# =========================================================
# VERIFICATION PANEL
# =========================================================

class VerificationPanelView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Start Verification",
        emoji="🔐",
        style=discord.ButtonStyle.primary,
        custom_id="verification:start"
    )
    async def start_verification(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        # -------------------------------------------------
        # BLACKLIST
        # -------------------------------------------------

        if is_blacklisted(interaction.user.id):

            expires_at = get_blacklist_expiration(
                interaction.user.id
            )

            if expires_at:

                timestamp = int(expires_at)

                await interaction.response.send_message(
                    "❌ You cannot start verification yet.\n"
                    f"Your waiting period ends <t:{timestamp}:R> "
                    f"(<t:{timestamp}:F>).",
                    ephemeral=True
                )

            else:

                await interaction.response.send_message(
                    "❌ You cannot start verification yet.",
                    ephemeral=True
                )

            return

        # -------------------------------------------------
        # EXISTING APPLICATION
        # -------------------------------------------------

        existing = get_user_application(
            interaction.user.id
        )

        if existing:

            status = existing.get("status")

            if status == "pending":

                await interaction.response.send_message(
                    "⏳ You already have a verification application "
                    "waiting for review.\n"
                    "Please wait for a decision.",
                    ephemeral=True
                )

                return

            if status == "accepted":

                await interaction.response.send_message(
                    "✅ You are already verified.",
                    ephemeral=True
                )

                return

        # -------------------------------------------------
        # OPEN MODAL
        # -------------------------------------------------

        await interaction.response.send_modal(
            VerificationModal()
        )


# =========================================================
# APPLICATION BUTTONS
# =========================================================

class ApplicationView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    # =====================================================
    # ACCEPT
    # =====================================================

    @discord.ui.button(
        label="Accept",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="verification:accept"
    )
    async def accept_application(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        # -------------------------------------------------
        # PERMISSION
        # -------------------------------------------------

        if interaction.user.id != OWNER_ID:

            await interaction.response.send_message(
                "❌ You do not have permission to process verification applications.",
                ephemeral=True
            )

            return

        # -------------------------------------------------
        # FIND APPLICATION
        # -------------------------------------------------

        user_id, application = find_application_by_message(
            interaction.message.id
        )

        if not application:

            await interaction.response.send_message(
                "❌ This verification application could not be found.",
                ephemeral=True
            )

            return

        # -------------------------------------------------
        # ALREADY PROCESSED
        # -------------------------------------------------

        if application.get("status") != "pending":

            await interaction.response.send_message(
                "⚠️ This application has already been processed.",
                ephemeral=True
            )

            return

        try:
            user_id_int = int(user_id)
        except (TypeError, ValueError):

            await interaction.response.send_message(
                "❌ Invalid user ID.",
                ephemeral=True
            )

            return

        guild = interaction.guild

        if guild is None:

            await interaction.response.send_message(
                "❌ This action can only be used inside a server.",
                ephemeral=True
            )

            return

        # -------------------------------------------------
        # FIND MEMBER
        # -------------------------------------------------

        member = guild.get_member(user_id_int)

        if member is None:

            try:
                member = await guild.fetch_member(user_id_int)
            except Exception:
                member = None

        # -------------------------------------------------
        # ROLE
        # -------------------------------------------------

        role = guild.get_role(
            VERIFIED_ROLE_ID
        )

        if role is None:

            await interaction.response.send_message(
                "❌ The verification role could not be found.",
                ephemeral=True
            )

            return

        # -------------------------------------------------
        # GIVE ROLE
        # -------------------------------------------------

        if member is not None:

            try:

                await member.add_roles(
                    role,
                    reason="Verification accepted"
                )

            except discord.Forbidden:

                await interaction.response.send_message(
                    "❌ I don't have permission to give the verification role.",
                    ephemeral=True
                )

                return

            except Exception:

                await interaction.response.send_message(
                    "❌ Failed to give the verification role.",
                    ephemeral=True
                )

                return

        # -------------------------------------------------
        # UPDATE DATA
        # -------------------------------------------------

        application["status"] = "accepted"
        application["processed_at"] = time.time()
        application["processed_by"] = interaction.user.id

        save_data()

        # -------------------------------------------------
        # UPDATE EMBED
        # -------------------------------------------------

        embed = (
            interaction.message.embeds[0]
            if interaction.message.embeds
            else discord.Embed()
        )

        fields = []

        for field in embed.fields:

            if field.name != "📊 Status":

                fields.append(field)

        embed.clear_fields()

        for field in fields:

            embed.add_field(
                name=field.name,
                value=field.value,
                inline=field.inline
            )

        embed.add_field(
            name="📊 Status",
            value=f"✅ Accepted by {interaction.user.mention}",
            inline=False
        )

        embed.color = discord.Color.green()

        # -------------------------------------------------
        # DISABLE BUTTONS
        # -------------------------------------------------

        for child in self.children:
            child.disabled = True

        await interaction.message.edit(
            embed=embed,
            view=self
        )

        # -------------------------------------------------
        # DM USER
        # -------------------------------------------------

        try:

            if member is not None:

                await member.send(
                    "✅ **Your verification application has been accepted!**\n\n"
                    "Welcome to the server! You now have access to the server chat."
                )

            else:

                user = await interaction.client.fetch_user(
                    user_id_int
                )

                await user.send(
                    "✅ **Your verification application has been accepted!**\n\n"
                    "Welcome to the server! You now have access to the server chat."
                )

        except Exception:
            pass

        # -------------------------------------------------
        # STAFF RESPONSE
        # -------------------------------------------------

        await interaction.response.send_message(
            f"✅ Verification application for <@{user_id_int}> has been accepted.",
            ephemeral=True
        )

    # =====================================================
    # REJECT
    # =====================================================

    @discord.ui.button(
        label="Reject",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="verification:reject"
    )
    async def reject_application(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        # -------------------------------------------------
        # PERMISSION
        # -------------------------------------------------

        if interaction.user.id != OWNER_ID:

            await interaction.response.send_message(
                "❌ You do not have permission to process verification applications.",
                ephemeral=True
            )

            return

        # -------------------------------------------------
        # FIND APPLICATION
        # -------------------------------------------------

        user_id, application = find_application_by_message(
            interaction.message.id
        )

        if not application:

            await interaction.response.send_message(
                "❌ This verification application could not be found.",
                ephemeral=True
            )

            return

        # -------------------------------------------------
        # ALREADY PROCESSED
        # -------------------------------------------------

        if application.get("status") != "pending":

            await interaction.response.send_message(
                "⚠️ This application has already been processed.",
                ephemeral=True
            )

            return

        try:
            user_id_int = int(user_id)
        except (TypeError, ValueError):

            await interaction.response.send_message(
                "❌ Invalid user ID.",
                ephemeral=True
            )

            return

        # -------------------------------------------------
        # 15-DAY BLACKLIST
        # -------------------------------------------------

        expires_at = time.time() + BLACKLIST_DURATION

        DATA["blacklist"][user_id] = {
            "expires_at": expires_at,
            "reason": "Verification application rejected"
        }

        # -------------------------------------------------
        # UPDATE APPLICATION
        # -------------------------------------------------

        application["status"] = "rejected"
        application["processed_at"] = time.time()
        application["processed_by"] = interaction.user.id
        application["blacklist_expires_at"] = expires_at

        save_data()

        timestamp = int(expires_at)

        # -------------------------------------------------
        # UPDATE EMBED
        # -------------------------------------------------

        embed = (
            interaction.message.embeds[0]
            if interaction.message.embeds
            else discord.Embed()
        )

        fields = []

        for field in embed.fields:

            if field.name != "📊 Status":

                fields.append(field)

        embed.clear_fields()

        for field in fields:

            embed.add_field(
                name=field.name,
                value=field.value,
                inline=field.inline
            )

        embed.add_field(
            name="📊 Status",
            value=(
                f"❌ Rejected by {interaction.user.mention}\n"
                f"Can apply again <t:{timestamp}:R> "
                f"(<t:{timestamp}:F>)"
            ),
            inline=False
        )

        embed.color = discord.Color.red()

        # -------------------------------------------------
        # DISABLE BUTTONS
        # -------------------------------------------------

        for child in self.children:
            child.disabled = True

        await interaction.message.edit(
            embed=embed,
            view=self
        )

        # -------------------------------------------------
        # DM USER
        # -------------------------------------------------

        try:

            user = await interaction.client.fetch_user(
                user_id_int
            )

            await user.send(
                "❌ **Your verification application was not accepted.**\n\n"
                "You can submit a new application after the 15-day waiting period.\n\n"
                f"Your waiting period ends <t:{timestamp}:R> "
                f"(<t:{timestamp}:F>)."
            )

        except Exception:
            pass

        # -------------------------------------------------
        # STAFF RESPONSE
        # -------------------------------------------------

        await interaction.response.send_message(
            f"❌ Verification application for <@{user_id_int}> has been rejected.\n"
            f"They can apply again <t:{timestamp}:R>.",
            ephemeral=True
        )


# =========================================================
# COG
# =========================================================

class Verification(commands.Cog):

    def __init__(self, bot):

        self.bot = bot
        self.check_blacklists.start()

    def cog_unload(self):

        self.check_blacklists.cancel()

    # =====================================================
    # BLACKLIST CHECK
    # =====================================================

    @tasks.loop(minutes=1)
    async def check_blacklists(self):

        now = time.time()
        expired_users = []

        for user_id, entry in list(
            DATA["blacklist"].items()
        ):

            expires_at = entry.get(
                "expires_at",
                0
            )

            if now >= expires_at:
                expired_users.append(user_id)

        if not expired_users:
            return

        for user_id in expired_users:

            DATA["blacklist"].pop(
                user_id,
                None
            )

            try:

                user = await self.bot.fetch_user(
                    int(user_id)
                )

                await user.send(
                    "✅ **Your 15-day verification waiting period has ended.**\n"
                    f"You can submit a new application in <#{VERIFICATION_CHANNEL_ID}>."
                )

            except Exception:
                pass

        save_data()

    @check_blacklists.before_loop
    async def before_blacklist_check(self):

        await self.bot.wait_until_ready()

    # =====================================================
    # !VERIFICATION PANEL
    # =====================================================

    @commands.command(name="verification")
    async def verification_command(
        self,
        ctx,
        action: str = None
    ):

        # Delete command
        try:
            await ctx.message.delete()
        except Exception:
            pass

        # Owner only
        if ctx.author.id != OWNER_ID:

            try:

                await ctx.send(
                    "❌ You do not have permission to use this command.",
                    delete_after=5
                )

            except Exception:
                pass

            return

        # Check command
        if action is None or action.lower() != "panel":

            try:

                await ctx.send(
                    "❌ Usage: `!verification panel`",
                    delete_after=5
                )

            except Exception:
                pass

            return

        # -------------------------------------------------
        # PANEL CHANNEL
        # -------------------------------------------------

        channel = self.bot.get_channel(
            VERIFICATION_CHANNEL_ID
        )

        if channel is None:

            try:

                await ctx.send(
                    "❌ Verification panel channel could not be found.",
                    delete_after=5
                )

            except Exception:
                pass

            return

        # -------------------------------------------------
        # PANEL EMBED
        # -------------------------------------------------

        embed = discord.Embed(
            title="🛡️ Server Verification",
            description=(
                "To get access to the server chat, "
                "verification is required.\n\n"

                f"**IMPORTANT:** You must go to "
                f"<#{SELECTION_CHANNEL_ID}> "
                "and choose what you need.\n\n"

                "Without selecting the required option, "
                "you will not be admitted to chatting.\n\n"

                "After you have made your selection, "
                "press **🔐 Start Verification** below "
                "and complete the verification application."
            ),
            color=discord.Color.blurple()
        )

        embed.set_footer(
            text="Server Verification"
        )

        # -------------------------------------------------
        # SEND PANEL
        # -------------------------------------------------

        await channel.send(
            embed=embed,
            view=VerificationPanelView()
        )


# =========================================================
# SETUP
# =========================================================

async def setup(bot):

    await bot.add_cog(
        Verification(bot)
    )

    # Persistent panel buttons
    bot.add_view(
        VerificationPanelView()
    )

    # Persistent application buttons
    bot.add_view(
        ApplicationView()
    )

    print("✅ verification.py loaded!")
