
import os
import json
import secrets
import logging
import asyncio
import urllib.parse
import urllib.request
import urllib.error

import discord
from discord import app_commands
from flask import (
    request,
    session,
    redirect,
    jsonify,
    render_template_string,
)

# =========================================================
# CONFIG
# =========================================================

OWNER_ID = 1176149190192152626

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv(
    "DISCORD_REDIRECT_URI",
    "https://system-bot-production-1021.up.railway.app/announcement/callback",
)

BASE_URL = os.getenv(
    "ANNOUNCEMENT_BASE_URL",
    "https://system-bot-production-1021.up.railway.app",
).rstrip("/")

DISCORD_API = "https://discord.com/api/v10"

logger = logging.getLogger(__name__)


# =========================================================
# WEBSITE HTML
# =========================================================

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>System-BOT | Announcement Studio</title>

<style>
*{box-sizing:border-box}
body{
    margin:0;
    background:#080b12;
    color:#f1f5f9;
    font-family:Inter,Arial,sans-serif
}
header{
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:22px;
    border-bottom:1px solid #222b3b;
    background:#0c111b
}
.logo{font-weight:900;font-size:20px}
.logo span{color:#6875ff}
.logout{color:#aab4c5;text-decoration:none}
.container{max-width:1100px;margin:30px auto;padding:16px}
.hero{margin-bottom:24px}
.hero h1{font-size:30px;margin-bottom:8px}
.hero p{color:#9ba8bd}
.card{
    background:#111722;
    border:1px solid #242e40;
    border-radius:16px;
    padding:24px;
    margin-bottom:20px;
    box-shadow:0 12px 35px #0002
}
h2{margin-top:0;font-size:19px}
label{
    display:block;
    color:#aab4c5;
    font-size:13px;
    margin:17px 0 8px
}
input,textarea,select{
    width:100%;
    padding:13px;
    border-radius:9px;
    border:1px solid #303b50;
    background:#090e17;
    color:white;
    outline:none;
    font-size:14px
}
input:focus,textarea:focus,select:focus{border-color:#6875ff}
textarea{min-height:110px;resize:vertical}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
button{
    border:0;
    border-radius:9px;
    padding:13px 18px;
    background:#5865f2;
    color:white;
    font-weight:bold;
    cursor:pointer;
    margin-top:16px
}
button:hover{background:#4752c4}
button:disabled{opacity:.5;cursor:not-allowed}
.secondary{background:#242e40}
.colorrow{display:flex;gap:10px}
.colorrow input[type=color]{width:65px;height:46px;padding:3px}
.preview{
    border-left:5px solid #5865f2;
    background:#1b2028;
    border-radius:7px;
    padding:16px;
    margin-top:18px;
    overflow-wrap:anywhere;
    white-space:pre-wrap
}
.preview-title{font-weight:bold;font-size:18px;margin-bottom:8px}
.preview-description{color:#d5d9e0}
.status{margin-top:15px;color:#aab4c5;white-space:pre-wrap}
.hidden{display:none}
.badge{
    display:inline-block;
    padding:6px 10px;
    border-radius:20px;
    background:#222b42;
    color:#9daaff;
    font-size:12px
}
@media(max-width:700px){
    .grid{grid-template-columns:1fr}
    .container{padding:10px}
    .card{padding:17px}
    .hero h1{font-size:24px}
}
</style>
</head>

<body>

<header>
    <div class="logo">SYSTEM<span>-BOT</span> / ANNOUNCEMENT STUDIO</div>
    <a class="logout" href="/announcement/logout">Logout</a>
</header>

<div class="container">

    <div class="hero">
        <span class="badge">PRIVATE OWNER DASHBOARD</span>
        <h1>Announcement Studio</h1>
        <p>Create and publish beautiful Discord announcements.</p>
    </div>

    <div class="card">
        <h2>📡 Destination</h2>

        <label>Discord Server</label>
        <select id="guild">
            <option value="">Loading servers...</option>
        </select>

        <label>Announcement Channel</label>
        <select id="channel">
            <option value="">Select a server first</option>
        </select>
    </div>

    <div class="card">
        <h2>📝 Message Editor</h2>

        <label>Announcement Type</label>
        <select id="type">
            <option value="text">Regular Message</option>
            <option value="embed">Embed</option>
            <option value="v2">Components V2</option>
        </select>

        <label>Message Text</label>
        <textarea id="content" maxlength="2000"
            placeholder="Write your announcement..."></textarea>

        <div id="embedEditor" class="hidden">
            <div class="grid">
                <div>
                    <label>Embed Title</label>
                    <input id="title" maxlength="256"
                        placeholder="Announcement title">
                </div>
                <div>
                    <label>Footer</label>
                    <input id="footer" maxlength="2048"
                        placeholder="Announcement footer">
                </div>
            </div>

            <label>Embed Description</label>
            <textarea id="description" maxlength="4096"
                placeholder="Embed description..."></textarea>

            <label>Embed Color</label>
            <div class="colorrow">
                <input type="color" id="colorPicker" value="#5865F2">
                <input id="colorHex" value="#5865F2" maxlength="7">
            </div>

            <label>Image URL (optional)</label>
            <input id="image" placeholder="https://example.com/image.png">
        </div>

        <div id="v2Editor" class="hidden">
            <label>Components V2 JSON</label>
            <textarea id="components" style="min-height:220px"
placeholder='[
  {"type":10,"content":"Welcome to LEGENDS!"},
  {"type":14,"divider":true},
  {"type":10,"content":"New announcement"}
]'></textarea>

            <p style="color:#aab4c5;font-size:12px">
                Supported components: Text Display (type 10),
                Separator (type 14), and URL Button (type 2, style 5).
            </p>
        </div>

        <button class="secondary" onclick="previewAnnouncement()">Preview</button>

        <div id="preview" class="preview hidden"></div>

        <button id="sendButton" onclick="sendAnnouncement()">
            🚀 Publish Announcement
        </button>

        <div id="status" class="status"></div>
    </div>
</div>

<script>
let csrfToken = "";

const guildSelect = document.getElementById("guild");
const channelSelect = document.getElementById("channel");
const typeSelect = document.getElementById("type");
const embedEditor = document.getElementById("embedEditor");
const v2Editor = document.getElementById("v2Editor");
const colorPicker = document.getElementById("colorPicker");
const colorHex = document.getElementById("colorHex");
const statusBox = document.getElementById("status");

function status(message) {
    statusBox.textContent = message;
}

async function api(url, options = {}) {
    if (!csrfToken) {
        const response = await fetch("/announcement/api/session");
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Session expired");
        }

        csrfToken = data.csrf_token;
    }

    const response = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": csrfToken,
            ...(options.headers || {})
        }
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || "Request failed");
    }

    return data;
}

typeSelect.addEventListener("change", () => {
    embedEditor.classList.toggle("hidden", typeSelect.value !== "embed");
    v2Editor.classList.toggle("hidden", typeSelect.value !== "v2");
});

colorPicker.addEventListener("input", () => {
    colorHex.value = colorPicker.value.toUpperCase();
});

colorHex.addEventListener("input", () => {
    if (/^#[0-9A-Fa-f]{6}$/.test(colorHex.value)) {
        colorPicker.value = colorHex.value;
    }
});

async function loadGuilds() {
    try {
        const data = await api("/announcement/api/guilds");

        guildSelect.innerHTML = "";

        data.guilds.forEach(guild => {
            const option = document.createElement("option");
            option.value = guild.id;
            option.textContent = guild.name;
            guildSelect.appendChild(option);
        });

        if (!data.guilds.length) {
            guildSelect.innerHTML =
                '<option value="">No servers available</option>';
        } else {
            await loadChannels();
        }
    } catch (error) {
        status(error.message);
    }
}

async function loadChannels() {
    const guildId = guildSelect.value;

    channelSelect.innerHTML =
        '<option value="">Loading channels...</option>';

    if (!guildId) return;

    try {
        const data = await api(
            "/announcement/api/channels/" + encodeURIComponent(guildId)
        );

        channelSelect.innerHTML = "";

        data.channels.forEach(channel => {
            const option = document.createElement("option");
            option.value = channel.id;
            option.textContent = "#" + channel.name;
            channelSelect.appendChild(option);
        });

        if (!data.channels.length) {
            channelSelect.innerHTML =
                '<option value="">No available channels</option>';
        }
    } catch (error) {
        status(error.message);
    }
}

guildSelect.addEventListener("change", loadChannels);

function previewAnnouncement() {
    const preview = document.getElementById("preview");
    preview.classList.remove("hidden");

    preview.style.borderLeftColor =
        /^#[0-9A-Fa-f]{6}$/.test(colorHex.value)
        ? colorHex.value
        : "#5865F2";

    preview.textContent = document.getElementById("content").value;

    if (typeSelect.value === "embed") {
        const title = document.getElementById("title").value;
        const description = document.getElementById("description").value;

        preview.textContent =
            (title ? title + "\n\n" : "") +
            description +
            "\n\n" +
            document.getElementById("content").value;
    }

    if (typeSelect.value === "v2") {
        preview.textContent =
            document.getElementById("components").value;
    }
}

async function sendAnnouncement() {
    const button = document.getElementById("sendButton");

    if (!guildSelect.value || !channelSelect.value) {
        status("Please select a server and channel.");
        return;
    }

    const payload = {
        guild_id: guildSelect.value,
        channel_id: channelSelect.value,
        type: typeSelect.value,
        content: document.getElementById("content").value,
        title: document.getElementById("title").value,
        description: document.getElementById("description").value,
        color: colorHex.value,
        image: document.getElementById("image").value,
        footer: document.getElementById("footer").value,
        components: document.getElementById("components").value
    };

    button.disabled = true;
    status("Publishing announcement...");

    try {
        await api("/announcement/api/send", {
            method: "POST",
            body: JSON.stringify(payload)
        });

        status("✅ Announcement published successfully!");
    } catch (error) {
        status("❌ " + error.message);
    } finally {
        button.disabled = false;
    }
}

loadGuilds();
</script>

</body>
</html>
"""
Продолжение того же файла:

<CodeBlock language="python" editable>
# =========================================================
# DISCORD API HELPERS
# =========================================================

def discord_api_request(url, method="GET", data=None, token=None):
    headers = {
        "User-Agent": "System-BOT Announcement Studio",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    encoded_data = None

    if data is not None:
        encoded_data = urllib.parse.urlencode(data).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    req = urllib.request.Request(
        url,
        data=encoded_data,
        headers=headers,
        method=method,
    )

    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def is_owner():
    return str(session.get("discord_user_id", "")) == str(OWNER_ID)


def csrf_valid():
    supplied = request.headers.get("X-CSRF-Token", "")
    expected = session.get("csrf_token", "")

    return bool(expected) and secrets.compare_digest(
        supplied,
        expected,
    )


def get_guild(bot, guild_id):
    try:
        guild_id = int(guild_id)
    except (TypeError, ValueError):
        raise ValueError("Invalid server ID.")

    guild = bot.get_guild(guild_id)

    if guild is None:
        raise ValueError("The bot is not in this server.")

    return guild


# =========================================================
# COMPONENTS V2 BUILDER
# =========================================================

def build_components_v2(component_data, content=""):
    """
    Supported JSON component types:
    10 = Text Display
    14 = Separator
    2  = URL Button (style 5)
    """

    if not isinstance(component_data, list):
        raise ValueError("Components V2 must be a JSON array.")

    if len(component_data) > 25:
        raise ValueError("Maximum 25 components are allowed.")

    view = discord.ui.LayoutView(timeout=None)

    if content.strip():
        view.add_item(
            discord.ui.TextDisplay(
                content=content[:2000]
            )
        )

    for item in component_data:
        if not isinstance(item, dict):
            raise ValueError("Each component must be an object.")

        component_type = item.get("type")

        if component_type == 10:
            text = item.get("content", "")

            if not isinstance(text, str) or not text.strip():
                raise ValueError("Text Display content cannot be empty.")

            view.add_item(
                discord.ui.TextDisplay(
                    content=text[:4000]
                )
            )

        elif component_type == 14:
            view.add_item(
                discord.ui.Separator(
                    visible=item.get("divider", True),
                    spacing=discord.SeparatorSpacing.small,
                )
            )

        elif component_type == 2:
            # Only URL buttons are supported in this editor.
            if item.get("style") != 5:
                raise ValueError(
                    "Only URL buttons (style 5) are supported."
                )

            label = item.get("label", "Open link")
            url = item.get("url", "")

            if not isinstance(url, str) or not url.startswith(
                ("https://", "http://")
            ):
                raise ValueError("Button URL must use HTTP or HTTPS.")

            button = discord.ui.Button(
                label=str(label)[:80],
                style=discord.ButtonStyle.link,
                url=url,
                disabled=bool(item.get("disabled", False)),
            )

            view.add_item(button)

        else:
            raise ValueError(
                f"Unsupported component type: {component_type}"
            )

    if not view.children:
        raise ValueError("Add at least one Components V2 element.")

    return view


# =========================================================
# EXTENSION SETUP
# =========================================================

async def setup(bot):

    web_app = bot.web_app

    # Flask session security.
    if not web_app.secret_key:
        web_app.secret_key = os.getenv("FLASK_SECRET_KEY")

    if not web_app.secret_key:
        raise RuntimeError(
            "FLASK_SECRET_KEY is missing from Railway Variables."
        )

    web_app.config["SESSION_COOKIE_HTTPONLY"] = True
    web_app.config["SESSION_COOKIE_SECURE"] = True
    web_app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    web_app.config["SESSION_COOKIE_NAME"] = "system_bot_session"

    if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
        logger.warning(
            "Announcement Studio OAuth2 variables are not configured."
        )

    # -----------------------------------------------------
    # LOGIN
    # -----------------------------------------------------

    @web_app.route("/announcement/login")
    def announcement_login():

        if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
            return "Discord OAuth2 is not configured.", 503

        state = secrets.token_urlsafe(32)
        session["oauth_state"] = state

        params = {
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": "identify",
            "state": state,
        }

        url = (
            "https://discord.com/oauth2/authorize?"
            + urllib.parse.urlencode(params)
        )

        return redirect(url)

    # -----------------------------------------------------
    # OAUTH CALLBACK
    # -----------------------------------------------------

    @web_app.route("/announcement/callback")
    def announcement_callback():

        if request.args.get("error"):
            return "Discord authorization was cancelled.", 400

        code = request.args.get("code")
        state = request.args.get("state")

        saved_state = session.pop("oauth_state", None)

        if (
            not code
            or not saved_state
            or not secrets.compare_digest(saved_state, state or "")
        ):
            return "Invalid OAuth2 state.", 400

        try:
            token_data = discord_api_request(
                f"{DISCORD_API}/oauth2/token",
                method="POST",
                data={
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": REDIRECT_URI,
                },
            )

            access_token = token_data["access_token"]

            user = discord_api_request(
                f"{DISCORD_API}/users/@me",
                token=access_token,
            )

            if str(user.get("id")) != str(OWNER_ID):
                session.clear()
                return (
                    "Access denied. This website is private.",
                    403,
                )

            # Do not keep the OAuth access token in the browser session.
            session.clear()

            session["discord_user_id"] = str(user["id"])
            session["discord_username"] = user.get(
                "username",
                "Owner",
            )
            session["csrf_token"] = secrets.token_urlsafe(32)

            return redirect("/announcement")

        except urllib.error.HTTPError:
            logger.exception("Discord OAuth2 HTTP error")
            return "Discord OAuth2 authentication failed.", 400

        except Exception:
            logger.exception("OAuth2 callback failed")
            return "Authentication failed.", 500

    # -----------------------------------------------------
    # LOGOUT
    # -----------------------------------------------------

    @web_app.route("/announcement/logout")
    def announcement_logout():

        session.clear()

        return redirect("/announcement/login")

    # -----------------------------------------------------
    # WEBSITE
    # -----------------------------------------------------

    @web_app.route("/announcement")
    def announcement_page():

        if not is_owner():
            return redirect("/announcement/login")

        response = web_app.make_response(
            render_template_string(HTML)
        )

        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"

        return response

    # -----------------------------------------------------
    # SESSION / CSRF
    # -----------------------------------------------------

    @web_app.route("/announcement/api/session")
    def announcement_session():

        if not is_owner():
            return jsonify(error="Unauthorized"), 401

        return jsonify(
            csrf_token=session.get("csrf_token"),
            username=session.get("discord_username"),
        )

    # -----------------------------------------------------
    # GUILDS
    # -----------------------------------------------------

    @web_app.route("/announcement/api/guilds")
    def announcement_guilds():

        if not is_owner():
            return jsonify(error="Unauthorized"), 401

        return jsonify(
            guilds=[
                {
                    "id": str(guild.id),
                    "name": guild.name,
                }
                for guild in bot.guilds
            ]
        )

    # -----------------------------------------------------
    # CHANNELS
    # -----------------------------------------------------

    @web_app.route("/announcement/api/channels/<guild_id>")
    def announcement_channels(guild_id):

        if not is_owner():
            return jsonify(error="Unauthorized"), 401

        try:
            guild = get_guild(bot, guild_id)

            channels = []

            for channel in guild.text_channels:
                permissions = channel.permissions_for(guild.me)

                if permissions.send_messages:
                    channels.append({
                        "id": str(channel.id),
                        "name": channel.name,
                    })

            return jsonify(channels=channels)

        except ValueError as error:
            return jsonify(error=str(error)), 400

        except Exception:
            logger.exception("Failed to load channels")
            return jsonify(error="Failed to load channels."), 500

    # -----------------------------------------------------
    # SEND ANNOUNCEMENT
    # -----------------------------------------------------

    @web_app.route("/announcement/api/send", methods=["POST"])
    def announcement_send():

        if not is_owner():
            return jsonify(error="Unauthorized"), 401

        if not csrf_valid():
            return jsonify(error="Invalid CSRF token."), 403

        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify(error="Invalid request."), 400

        message_type = data.get("type")

        if message_type not in ("text", "embed", "v2"):
            return jsonify(error="Invalid announcement type."), 400

        try:
            guild = get_guild(bot, data.get("guild_id"))

            try:
                channel_id = int(data.get("channel_id"))
            except (TypeError, ValueError):
                return jsonify(error="Invalid channel ID."), 400

            channel = guild.get_channel(channel_id)

            if not isinstance(channel, discord.TextChannel):
                return jsonify(error="Invalid text channel."), 400

            permissions = channel.permissions_for(guild.me)

            if not permissions.send_messages:
                return jsonify(error="Bot cannot send messages here."), 403

            content = str(data.get("content", ""))[:2000]

            async def send_announcement():

                if message_type == "text":

                    if not content.strip():
                        raise ValueError("Message cannot be empty.")

                    await channel.send(
                        content=content,
                        allowed_mentions=discord.AllowedMentions.none(),
                    )

                elif message_type == "embed":

                    title = str(data.get("title", ""))[:256]
                    description = str(data.get("description", ""))[:4096]
                    footer = str(data.get("footer", ""))[:2048]
                    image = str(data.get("image", ""))[:1000]
                    color_text = str(data.get("color", "#5865F2"))

                    if not content.strip() and not title and not description:
                        raise ValueError("Announcement cannot be empty.")

                    if not (
                        len(color_text) == 7
                        and color_text.startswith("#")
                        and all(
                            char in "0123456789abcdefABCDEF"
                            for char in color_text[1:]
                        )
                    ):
                        raise ValueError("Invalid HEX color.")

                    embed = discord.Embed(
                        title=title or None,
                        description=description or None,
                        color=int(color_text[1:], 16),
                    )

                    if footer:
                        embed.set_footer(text=footer)

                    if image:
                        if not image.startswith(("https://", "http://")):
                            raise ValueError(
                                "Image URL must use HTTP or HTTPS."
                            )

                        embed.set_image(url=image)

                    await channel.send(
                        content=content or None,
                        embed=embed,
                        allowed_mentions=discord.AllowedMentions.none(),
                    )

                elif message_type == "v2":

                    raw_components = data.get("components", "")

                    try:
                        component_data = json.loads(raw_components)
                    except (TypeError, json.JSONDecodeError):
                        raise ValueError("Invalid Components V2 JSON.")

                    view = build_components_v2(
                        component_data,
                        content=content,
                    )

                    await channel.send(
                        view=view,
                        allowed_mentions=discord.AllowedMentions.none(),
                    )

            future = asyncio.run_coroutine_threadsafe(
                send_announcement(),
                bot.loop,
            )

            future.result(timeout=30)

            return jsonify(success=True)

        except ValueError as error:
            return jsonify(error=str(error)), 400

        except discord.Forbidden:
            return jsonify(
                error="Bot has no permission to send messages."
            ), 403

        except discord.HTTPException:
            logger.exception("Discord send error")
            return jsonify(
                error="Discord rejected the announcement."
            ), 400

        except Exception:
            logger.exception("Announcement send failed")
            return jsonify(
                error="Failed to send announcement."
            ), 500

    # -----------------------------------------------------
    # /send announcement
    # -----------------------------------------------------

    send_group = bot.tree.get_command("send")

    if send_group is None or not isinstance(
        send_group,
        app_commands.Group,
    ):
        raise RuntimeError(
            "The existing /send command group was not found."
        )

    @app_commands.command(
        name="announcement",
        description="Open the private Announcement Studio",
    )
    async def send_announcement_command(
        interaction: discord.Interaction,
    ):

        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                "❌ You do not have permission to use this command.",
                ephemeral=True,
            )
            return

        view = discord.ui.View(timeout=300)

        view.add_item(
            discord.ui.Button(
                label="Open Announcement Studio",
                emoji="🎨",
                style=discord.ButtonStyle.link,
                url=f"{BASE_URL}/announcement",
            )
        )

        await interaction.response.send_message(
            "🎨 **Announcement Studio**\n\n"
            "Open your private dashboard to create and publish "
            "Discord announcements.",
            view=view,
            ephemeral=True,
        )

    send_group.add_command(send_announcement_command)

    logger.info("Announcement Studio extension loaded.")
