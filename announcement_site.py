import os
import json
import secrets
import asyncio
import logging
import urllib.parse
import urllib.request
import urllib.error

import discord
from discord import app_commands
from flask import request, session, redirect, jsonify, render_template_string

logger = logging.getLogger(__name__)

OWNER_ID = 1176149190192152626

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")

REDIRECT_URI = os.getenv(
    "DISCORD_REDIRECT_URI",
    "https://system-bot-production-1021.up.railway.app/announcement/callback"
)

BASE_URL = os.getenv(
    "ANNOUNCEMENT_BASE_URL",
    "https://system-bot-production-1021.up.railway.app"
).rstrip("/")

DISCORD_API = "https://discord.com/api/v10"


HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>System-BOT | Announcement Studio</title>

<style>
*{box-sizing:border-box}
body{margin:0;background:#080b12;color:#f1f5f9;font-family:Arial,sans-serif}
header{padding:22px;background:#0c111b;border-bottom:1px solid #242e40;display:flex;justify-content:space-between}
.logo{font-weight:900;font-size:19px}
.logo span{color:#6875ff}
a{color:#aab4c5;text-decoration:none}
.container{max-width:1050px;margin:35px auto;padding:15px}
.hero{margin-bottom:25px}
.hero h1{font-size:30px}
.hero p{color:#9ba8bd}
.badge{background:#222b42;color:#aab4ff;padding:7px 12px;border-radius:20px;font-size:12px}
.card{background:#111722;border:1px solid #242e40;border-radius:16px;padding:23px;margin-bottom:20px}
h2{font-size:19px;margin-top:0}
label{display:block;color:#aab4c5;font-size:13px;margin:16px 0 8px}
input,textarea,select{width:100%;padding:13px;border-radius:9px;border:1px solid #303b50;background:#090e17;color:white;outline:none;font-size:14px}
input:focus,textarea:focus,select:focus{border-color:#6875ff}
textarea{min-height:110px;resize:vertical}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:15px}
button{border:0;border-radius:9px;padding:13px 18px;background:#5865f2;color:white;font-weight:bold;cursor:pointer;margin-top:15px}
button:hover{background:#4752c4}
button:disabled{opacity:.5}
.secondary{background:#293348}
.colorrow{display:flex;gap:10px}
.colorrow input[type=color]{width:65px;height:46px;padding:3px}
.preview{border-left:5px solid #5865f2;background:#1b2028;border-radius:7px;padding:16px;margin-top:18px;white-space:pre-wrap;overflow-wrap:anywhere}
.status{margin-top:15px;color:#aab4c5;white-space:pre-wrap}
.hidden{display:none}
.hint{font-size:12px;color:#9ba8bd}
@media(max-width:650px){.grid{grid-template-columns:1fr}.container{margin:15px auto}.card{padding:16px}.hero h1{font-size:24px}}
</style>
</head>

<body>
<header>
<div class="logo">SYSTEM<span>-BOT</span> / ANNOUNCEMENT STUDIO</div>
<a href="/announcement/logout">Logout</a>
</header>

<div class="container">
<div class="hero">
<span class="badge">PRIVATE OWNER DASHBOARD</span>
<h1>Announcement Studio</h1>
<p>Create and publish announcements to your Discord server.</p>
</div>

<div class="card">
<h2>📡 Destination</h2>
<label>Discord Server</label>
<select id="guild"><option value="">Loading servers...</option></select>

<label>Announcement Channel</label>
<select id="channel"><option value="">Select a server first</option></select>
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
<textarea id="content" maxlength="2000" placeholder="Write your announcement..."></textarea>

<div id="embedEditor" class="hidden">
<div class="grid">
<div>
<label>Embed Title</label>
<input id="title" maxlength="256" placeholder="Announcement title">
</div>
<div>
<label>Footer</label>
<input id="footer" maxlength="2048" placeholder="Announcement footer">
</div>
</div>

<label>Embed Description</label>
<textarea id="description" maxlength="4096" placeholder="Embed description..."></textarea>

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
<textarea id="components" style="min-height:200px" placeholder='[
  {"type":10,"content":"Welcome to LEGENDS!"},
  {"type":14,"divider":true},
  {"type":10,"content":"New announcement"}
]'></textarea>
<p class="hint">Supported: Text Display (type 10) and Separator (type 14).</p>
</div>

<button class="secondary" onclick="previewAnnouncement()">Preview</button>
<div id="preview" class="preview hidden"></div>
<button id="sendButton" onclick="sendAnnouncement()">🚀 Publish Announcement</button>
<div id="status" class="status"></div>
</div>
</div>

<script>
let csrfToken = "";

const guildSelect = document.getElementById("guild");
const channelSelect = document.getElementById("channel");
const typeSelect = document.getElementById("type");
const statusBox = document.getElementById("status");

function status(text){
    statusBox.textContent = text;
}

async function api(url, options = {}){
    if(!csrfToken){
        const r = await fetch("/announcement/api/session");
        const d = await r.json();

        if(!r.ok) throw new Error(d.error || "Session expired");

        csrfToken = d.csrf_token;
    }

    const r = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": csrfToken,
            ...(options.headers || {})
        }
    });

    const d = await r.json();

    if(!r.ok) throw new Error(d.error || "Request failed");

    return d;
}

typeSelect.addEventListener("change", () => {
    document.getElementById("embedEditor").classList.toggle(
        "hidden", typeSelect.value !== "embed"
    );

    document.getElementById("v2Editor").classList.toggle(
        "hidden", typeSelect.value !== "v2"
    );
});

document.getElementById("colorPicker").addEventListener("input", e => {
    document.getElementById("colorHex").value = e.target.value.toUpperCase();
});

document.getElementById("colorHex").addEventListener("input", e => {
    if(/^#[0-9A-Fa-f]{6}$/.test(e.target.value)){
        document.getElementById("colorPicker").value = e.target.value;
    }
});

async function loadGuilds(){
    try{
        const d = await api("/announcement/api/guilds");
        guildSelect.innerHTML = "";

        d.guilds.forEach(g => {
            const o = document.createElement("option");
            o.value = g.id;
            o.textContent = g.name;
            guildSelect.appendChild(o);
        });

        if(d.guilds.length){
            await loadChannels();
        }else{
            guildSelect.innerHTML = '<option value="">No servers available</option>';
        }
    }catch(e){
        status(e.message);
    }
}

async function loadChannels(){
    channelSelect.innerHTML = '<option value="">Loading...</option>';

    if(!guildSelect.value) return;

    try{
        const d = await api(
            "/announcement/api/channels/" + encodeURIComponent(guildSelect.value)
        );

        channelSelect.innerHTML = "";

        d.channels.forEach(c => {
            const o = document.createElement("option");
            o.value = c.id;
            o.textContent = "#" + c.name;
            channelSelect.appendChild(o);
        });

        if(!d.channels.length){
            channelSelect.innerHTML = '<option value="">No available channels</option>';
        }
    }catch(e){
        status(e.message);
    }
}

guildSelect.addEventListener("change", loadChannels);

function previewAnnouncement(){
    const p = document.getElementById("preview");
    p.classList.remove("hidden");

    p.style.borderLeftColor = document.getElementById("colorHex").value;

    let text = document.getElementById("content").value;

    if(typeSelect.value === "embed"){
        text =
            document.getElementById("title").value + "\n\n" +
            document.getElementById("description").value + "\n\n" +
            text;
    }

    if(typeSelect.value === "v2"){
        text = document.getElementById("components").value;
    }

    p.textContent = text;
}

async function sendAnnouncement(){
    const button = document.getElementById("sendButton");

    if(!guildSelect.value || !channelSelect.value){
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
        color: document.getElementById("colorHex").value,
        footer: document.getElementById("footer").value,
        image: document.getElementById("image").value,
        components: document.getElementById("components").value
    };

    button.disabled = true;
    status("Publishing announcement...");

    try{
        await api("/announcement/api/send", {
            method: "POST",
            body: JSON.stringify(payload)
        });

        status("✅ Announcement published successfully!");
    }catch(e){
        status("❌ " + e.message);
    }finally{
        button.disabled = false;
    }
}

loadGuilds();
</script>
</body>
</html>
"""


# =========================================================
# DISCORD API
# =========================================================

def discord_api_request(url, method="GET", data=None, token=None):
    headers = {
        "User-Agent": "System-BOT Announcement Studio",
        "Accept": "application/json",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = None

    if data is not None:
        body = urllib.parse.urlencode(data).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    req = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        logger.error(
            "Discord API error: HTTP %s: %s",
            error.code,
            error_body[:1000],
        )
        raise


def is_owner():
    return str(session.get("discord_user_id", "")) == str(OWNER_ID)


def csrf_valid():
    supplied = request.headers.get("X-CSRF-Token", "")
    expected = session.get("csrf_token", "")

    return bool(expected) and secrets.compare_digest(supplied, expected)


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
# COMPONENTS V2
# =========================================================

def build_components_v2(component_data, content=""):
    if not isinstance(component_data, list):
        raise ValueError("Components V2 must be a JSON array.")

    if len(component_data) > 25:
        raise ValueError("Maximum 25 components are allowed.")

    view = discord.ui.LayoutView(timeout=None)

    if content.strip():
        view.add_item(
            discord.ui.TextDisplay(content=content[:2000])
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
                discord.ui.TextDisplay(content=text[:4000])
            )

        elif component_type == 14:
            view.add_item(
                discord.ui.Separator(
                    visible=bool(item.get("divider", True)),
                    spacing=discord.SeparatorSpacing.small,
                )
            )

        else:
            raise ValueError(
                f"Unsupported component type: {component_type}"
            )

    if not view.children:
        raise ValueError("Add at least one Components V2 element.")

    return view


# =========================================================
# EXTENSION
# =========================================================

async def setup(bot):

    web_app = bot.web_app

    if not web_app.secret_key:
        web_app.secret_key = os.getenv("FLASK_SECRET_KEY")

    if not web_app.secret_key:
        raise RuntimeError(
            "FLASK_SECRET_KEY is missing from Railway Variables."
        )

    web_app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_NAME="system_bot_session",
    )

    if not CLIENT_ID or not CLIENT_SECRET:
        logger.warning("Announcement Studio OAuth2 variables are missing.")

    # LOGIN

    @web_app.route("/announcement/login")
    def announcement_login():

        if not CLIENT_ID or not CLIENT_SECRET:
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

        return redirect(
            "https://discord.com/oauth2/authorize?"
            + urllib.parse.urlencode(params)
        )

    # OAUTH CALLBACK

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
                return "Access denied. This website is private.", 403

            session.clear()
            session["discord_user_id"] = str(user["id"])
            session["discord_username"] = user.get("username", "Owner")
            session["csrf_token"] = secrets.token_urlsafe(32)

            return redirect("/announcement")

        except urllib.error.HTTPError:
            logger.exception("Discord OAuth2 HTTP error")
            return "Discord OAuth2 failed. Check Railway logs.", 400

        except Exception:
            logger.exception("Discord OAuth2 callback failed")
            return "Discord authentication failed. Check Railway logs.", 500

    # LOGOUT

    @web_app.route("/announcement/logout")
    def announcement_logout():
        session.clear()
        return redirect("/announcement/login")

    # DASHBOARD

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

    # SESSION

    @web_app.route("/announcement/api/session")
    def announcement_session():

        if not is_owner():
            return jsonify(error="Unauthorized"), 401

        return jsonify(
            csrf_token=session.get("csrf_token"),
            username=session.get("discord_username"),
        )

    # GUILDS

    @web_app.route("/announcement/api/guilds")
    def announcement_guilds():

        if not is_owner():
            return jsonify(error="Unauthorized"), 401

        return jsonify(
            guilds=[
                {"id": str(g.id), "name": g.name}
                for g in bot.guilds
            ]
        )

    # CHANNELS

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
            logger.exception("Channel loading failed")
            return jsonify(error="Failed to load channels."), 500

    # SEND ANNOUNCEMENT

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

            async def send_message():

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
                            c in "0123456789abcdefABCDEF"
                            for c in color_text[1:]
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
                            raise ValueError("Invalid image URL.")

                        embed.set_image(url=image)

                    await channel.send(
                        content=content or None,
                        embed=embed,
                        allowed_mentions=discord.AllowedMentions.none(),
                    )

                elif message_type == "v2":

                    try:
                        components = json.loads(data.get("components", ""))
                    except (TypeError, json.JSONDecodeError):
                        raise ValueError("Invalid Components V2 JSON.")

                    view = build_components_v2(components, content)

                    await channel.send(
                        view=view,
                        allowed_mentions=discord.AllowedMentions.none(),
                    )

            future = asyncio.run_coroutine_threadsafe(
                send_message(),
                bot.loop,
            )

            future.result(timeout=30)

            return jsonify(success=True)

        except ValueError as error:
            return jsonify(error=str(error)), 400

        except discord.Forbidden:
            return jsonify(error="Bot has no permission to send messages."), 403

        except discord.HTTPException:
            logger.exception("Discord send error")
            return jsonify(error="Discord rejected the announcement."), 400

        except Exception:
            logger.exception("Announcement send failed")
            return jsonify(error="Failed to send announcement."), 500

    # REGISTER SLASH COMMAND

    send_group = bot.tree.get_command("send")

    if send_group is None or not isinstance(send_group, app_commands.Group):
        raise RuntimeError("Existing /send command group was not found.")

    if send_group.get_command("announcement") is None:

        @app_commands.command(
            name="announcement",
            description="Open the private Announcement Studio",
        )
        async def announcement_command(interaction: discord.Interaction):

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
                "Open your private dashboard to create and publish announcements.",
                view=view,
                ephemeral=True,
            )

        send_group.add_command(announcement_command)

    logger.info("Announcement Studio extension loaded successfully.")
