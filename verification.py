import os
import json
import time

import discord
from discord.ext import commands, tasks

OWNER_ID = 1176149190192152626

VERIFICATION_CHANNEL_ID = 1546998884830683176
APPLICATIONS_CHANNEL_ID = 1547237068315566180
SELECTION_CHANNEL_ID = 1541336807508017252
VERIFIED_ROLE_ID = 1546987754968326154

DATA_FILE = "verification_data.json"
BLACKLIST_DURATION = 15 * 24 * 60 * 60


# =========================
# DATA
# =========================

def load_data():
    if not os.path.exists(DATA_FILE):
        data = {
            "applications": {},
            "blacklist": {}
        }
        save_data(data)
        return data

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        data.setdefault("applications", {})
        data.setdefault("blacklist", {})

        return data

    except Exception:
        return {
            "applications": {},
            "blacklist": {}
        }


def save_data(data=None):
    if data is None:
        data = load_data()

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_user_application(user_id):
    data = load_data()

    for application in data["applications"].values():
        if str(application["user_id"]) == str(user_id):
            return application

    return None


def find_application_by_message(message_id):
    data = load_data()

    for application in data["applications"].values():
        if str(application.get("message_id")) == str(message_id):
            return application

    return None


def is_blacklisted(user_id):
    data = load_data()

    entry = data["blacklist"].get(str(user_id))

    if not entry:
        return False

    if time.time() >= entry["expires_at"]:
        del data["blacklist"][str(user_id)]
        save_data(data)
        return False

    return True


def get_blacklist_expiration(user_id):
    data = load_data()

    entry = data["blacklist"].get(str(user_id))

    if not entry:
        return None

    return entry["expires_at"]


# =========================
# VERIFICATION MODAL
# =========================

class VerificationModal(discord.ui.Modal, title="Server Verification"):

    reason = discord.ui.TextInput(
        label="Why do you want to join this server?",
        placeholder="Tell us why you want to join this server...",
        style=discord.TextStyle.paragraph,
        required=True,
        min_length=5,
        max_length=1000
    )

    why_accept = discord.ui.TextInput(
        label="Why should we accept you?",
        placeholder="Tell us why we should accept your application...",
        style=discord.TextStyle.paragraph,
        required=True,
        min_length=5,
        max_length=1000
    )

    how_found = discord.ui.TextInput(
        label="How did you find our server?",
        placeholder="Friend, Discord, game, social media, etc...",
        style=discord.TextStyle.short,
        required=True,
        min_length=2,
        max_length=500
    )

    why_verification = discord.ui.TextInput(
        label="Why do you want to pass verification?",
        placeholder="Tell us why you want to complete verification...",
        style=discord.TextStyle.paragraph,
        required=True,
        min_length=5,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):

        user_id = interaction.user.id

        # =========================
        # BLACKLIST CHECK
        # =========================

        if is_blacklisted(user_id):
            expires_at = get_blacklist_expiration(user_id)

            await interaction.response.send_message(
                "❌ You are currently blacklisted from verification.\n\n"
                f"⏳ You can apply again <t:{int(expires_at)}:R>.\n"
                f"📅 <t:{int(expires_at)}:F>",
                ephemeral=True
            )
            return

        # =========================
        # EXISTING APPLICATION
        # =========================

        existing = get_user_application(user_id)

        if existing:
            status = existing.get("status")

            if status == "pending":
                await interaction.response.send_message(
                    "⏳ You have already submitted a verification application.\n"
                    "Please wait for it to be reviewed.",
                    ephemeral=True
                )
                return

            if status == "accepted":
                await interaction.response.send_message(
                    "✅ Your verification application has already been accepted.",
                    ephemeral=True
                )
                return

        # =========================
        # APPLICATION CHANNEL
        # =========================

        channel = interaction.client.get_channel(APPLICATIONS_CHANNEL_ID)

        if channel is None:
            await interaction.response.send_message(
                "❌ Verification application channel was not found.",
                ephemeral=True
            )
            return

        # =========================
        # EMBED
        # =========================

        embed = discord.Embed(
            title="🛡️ New Verification Application",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="👤 User",
            value=f"{interaction.user.mention}\n"
                  f"**Name:** {interaction.user}\n"
                  f"**ID:** `{interaction.user.id}`",
            inline=False
        )

        embed.add_field(
            name="📝 Why do you want to join this server?",
            value=str(self.reason),
            inline=False
        )

        embed.add_field(
            name="💭 Why should we accept you?",
            value=str(self.why_accept),
            inline=False
        )

        embed.add_field(
            name="🌐 How did you find our server?",
            value=str(self.how_found),
            inline=False
        )

        embed.add_field(
            name="🔐 Why do you want to pass verification?",
            value=str(self.why_verification),
            inline=False
        )

        embed.add_field(
            name="📊 Status",
            value="⏳ Pending",
            inline=False
        )

        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        message = await channel.send(
            embed=embed,
            view=ApplicationView()
        )

        # =========================
        # SAVE APPLICATION
        # =========================

        data = load_data()

        data["applications"][str(user_id)] = {
            "user_id": user_id,
            "message_id": message.id,
            "channel_id": channel.id,

            "reason": str(self.reason),
            "why_accept": str(self.why_accept),
            "how_found": str(self.how_found),
            "why_verification": str(self.why_verification),

            "status": "pending",
            "created_at": time.time()
        }

        save_data(data)

        await interaction.response.send_message(
            "✅ Your verification application has been sent for review.\n"
            "Please wait a little.",
            ephemeral=True
        )


# =========================
# REJECT MODAL
# =========================

class RejectModal(discord.ui.Modal, title="Reject Verification"):

    rejection_reason = discord.ui.TextInput(
        label="Reason for rejection",
        placeholder="Enter the reason why this application is rejected...",
        style=discord.TextStyle.paragraph,
        required=True,
        min_length=3,
        max_length=1000
    )

    def __init__(self, message_id):
        super().__init__()
        self.message_id = message_id

    async def on_submit(self, interaction: discord.Interaction):

        application = find_application_by_message(
            self.message_id
        )

        if not application:
            await interaction.response.send_message(
                "❌ Application data was not found.",
                ephemeral=True
            )
            return

        if application.get("status") != "pending":
            await interaction.response.send_message(
                "❌ This application has already been processed.",
                ephemeral=True
            )
            return

        user_id = int(application["user_id"])
        rejection_reason = str(self.rejection_reason)

        expires_at = time.time() + BLACKLIST_DURATION

        # =========================
        # SAVE BLACKLIST
        # =========================

        data = load_data()

        data["blacklist"][str(user_id)] = {
            "expires_at": expires_at,
            "reason": rejection_reason
        }

        user_application = data["applications"].get(str(user_id))

        if user_application:
            user_application["status"] = "rejected"
            user_application["processed_at"] = time.time()
            user_application["processed_by"] = interaction.user.id
            user_application["blacklist_expires_at"] = expires_at
            user_application["rejection_reason"] = rejection_reason

        save_data(data)

        # =========================
        # UPDATE EMBED
        # =========================

        channel = interaction.client.get_channel(
            APPLICATIONS_CHANNEL_ID
        )

        if channel is None:
            await interaction.response.send_message(
                "❌ Verification application channel was not found.",
                ephemeral=True
            )
            return

        try:
            message = await channel.fetch_message(
                self.message_id
            )
        except discord.NotFound:
            await interaction.response.send_message(
                "❌ Application message was not found.",
                ephemeral=True
            )
            return

        embed = message.embeds[0]

        for field in embed.fields:
            if field.name == "📊 Status":
                field.value = (
                    "❌ Rejected\n"
                    f"⏳ <t:{int(expires_at)}:R>\n"
                    f"📅 <t:{int(expires_at)}:F>"
                )

        embed.add_field(
            name="❌ Rejection Reason",
            value=rejection_reason,
            inline=False
        )

        embed.color = discord.Color.red()

        view = ApplicationView()

        for item in view.children:
            item.disabled = True

        await message.edit(
            embed=embed,
            view=view
        )

        # =========================
        # DM
        # =========================

        user = interaction.client.get_user(user_id)

        if user is None:
            try:
                user = await interaction.client.fetch_user(user_id)
            except discord.NotFound:
                user = None

        if user:
            try:
                await user.send(
                    "❌ **Your verification application has been rejected.**\n\n"
                    f"**Reason:** {rejection_reason}\n\n"
                    f"⏳ You can submit a new application <t:{int(expires_at)}:R>.\n"
                    f"📅 <t:{int(expires_at)}:F>"
                )
            except discord.Forbidden:
                pass

        await interaction.response.send_message(
            "❌ Verification application rejected.\n"
            f"User is blacklisted until <t:{int(expires_at)}:F>.",
            ephemeral=True
        )


# =========================
# VERIFICATION PANEL
# =========================

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

        user_id = interaction.user.id

        # =========================
        # BLACKLIST
        # =========================

        if is_blacklisted(user_id):
            expires_at = get_blacklist_expiration(user_id)

            await interaction.response.send_message(
                "❌ You are currently blacklisted from verification.\n\n"
                f"⏳ You can apply again <t:{int(expires_at)}:R>.\n"
                f"📅 <t:{int(expires_at)}:F>",
                ephemeral=True
            )
            return

        # =========================
        # EXISTING APPLICATION
        # =========================

        existing = get_user_application(user_id)

        if existing:
            status = existing.get("status")

            if status == "pending":
                await interaction.response.send_message(
                    "⏳ You have already submitted a verification application.\n"
                    "Please wait for it to be reviewed.",
                    ephemeral=True
                )
                return

            if status == "accepted":
                await interaction.response.send_message(
                    "✅ Your verification application has already been accepted.",
                    ephemeral=True
                )
                return

        await interaction.response.send_modal(
            VerificationModal()
        )


# =========================
# APPLICATION VIEW
# =========================

class ApplicationView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Accept",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="verification:accept"
    )
    async def accept(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                "❌ You do not have permission to process verification applications.",
                ephemeral=True
            )
            return

        application = find_application_by_message(
            interaction.message.id
        )

        if not application:
            await interaction.response.send_message(
                "❌ Application data was not found.",
                ephemeral=True
            )
            return

        if application.get("status") != "pending":
            await interaction.response.send_message(
                "❌ This application has already been processed.",
                ephemeral=True
            )
            return

        user_id = int(application["user_id"])

        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "❌ Guild was not found.",
                ephemeral=True
            )
            return

        member = guild.get_member(user_id)

        if member is None:
            try:
                member = await guild.fetch_member(user_id)
            except discord.NotFound:
                await interaction.response.send_message(
                    "❌ User is no longer in the server.",
                    ephemeral=True
                )
                return

        role = guild.get_role(VERIFIED_ROLE_ID)

        if role is None:
            await interaction.response.send_message(
                "❌ Verified role was not found.",
                ephemeral=True
            )
            return

        try:
            await member.add_roles(role)
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to give the verified role.",
                ephemeral=True
            )
            return

        # =========================
        # UPDATE DATA
        # =========================

        data = load_data()

        user_application = data["applications"].get(str(user_id))

        if user_application:
            user_application["status"] = "accepted"
            user_application["processed_at"] = time.time()
            user_application["processed_by"] = interaction.user.id

        save_data(data)

        # =========================
        # UPDATE EMBED
        # =========================

        embed = interaction.message.embeds[0]

        for field in embed.fields:
            if field.name == "📊 Status":
                field.value = "✅ Accepted"

        embed.color = discord.Color.green()

        for item in self.children:
            item.disabled = True

        await interaction.message.edit(
            embed=embed,
            view=self
        )

        # =========================
        # DM
        # =========================

        try:
            await member.send(
                "✅ **Your verification application has been accepted!**\n\n"
                "Welcome to the server! 🎉"
            )
        except discord.Forbidden:
            pass

        await interaction.response.send_message(
            f"✅ Verification accepted for {member.mention}.",
            ephemeral=True
        )

    @discord.ui.button(
        label="Reject",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="verification:reject"
    )
    async def reject(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                "❌ You do not have permission to process verification applications.",
                ephemeral=True
            )
            return

        application = find_application_by_message(
            interaction.message.id
        )

        if not application:
            await interaction.response.send_message(
                "❌ Application data was not found.",
                ephemeral=True
            )
            return

        if application.get("status") != "pending":
            await interaction.response.send_message(
                "❌ This application has already been processed.",
                ephemeral=True
            )
            return

        # Открываем форму причины отклонения
        await interaction.response.send_modal(
            RejectModal(interaction.message.id)
        )


# =========================
# COG
# =========================

class Verification(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.check_blacklists.start()

    def cog_unload(self):
        self.check_blacklists.cancel()

    # =========================
    # BLACKLIST CHECK
    # =========================

    @tasks.loop(minutes=1)
    async def check_blacklists(self):

        data = load_data()
        changed = False

        now = time.time()

        for user_id, entry in list(data["blacklist"].items()):

            if now < entry["expires_at"]:
                continue

            del data["blacklist"][user_id]
            changed = True

            user = self.bot.get_user(int(user_id))

            if user is None:
                try:
                    user = await self.bot.fetch_user(int(user_id))
                except discord.NotFound:
                    user = None

            if user:

                try:
                    await user.send(
                        "✅ **Your 15-day verification waiting period has ended.**\n"
                        f"You can submit a new application in <#{VERIFICATION_CHANNEL_ID}>."
                    )
                except discord.Forbidden:
                    pass

        if changed:
            save_data(data)

    @check_blacklists.before_loop
    async def before_blacklists(self):
        await self.bot.wait_until_ready()

    # =========================
    # PANEL COMMAND
    # =========================

    @commands.command(name="verification")
    async def verification_command(
        self,
        ctx,
        action=None
    ):

        if ctx.author.id != OWNER_ID:
            return

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        if action != "panel":
            return

        channel = self.bot.get_channel(
            VERIFICATION_CHANNEL_ID
        )

        if channel is None:
            return

        embed = discord.Embed(
            title="🛡️ Server Verification",
            description=(
                "Verification is required to access the server.\n\n"
                f"**IMPORTANT:** First go to <#{SELECTION_CHANNEL_ID}> "
                "and choose what you need.\n"
                "Without selecting it, you will not be admitted to the chat.\n\n"
                "After selecting what you need, press **Start Verification** "
                "below and complete the application."
            ),
            color=discord.Color.blurple()
        )

        embed.set_footer(
            text="Please answer all questions honestly."
        )

        await channel.send(
            embed=embed,
            view=VerificationPanelView()
        )


# =========================
# SETUP
# =========================

async def setup(bot):
    await bot.add_cog(Verification(bot))

    bot.add_view(
        VerificationPanelView()
    )

    bot.add_view(
        ApplicationView()
    )

    print("✅ verification.py loaded!")
