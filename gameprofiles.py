"""
Game Profiles — System-BOT
Discord.py 2.6+ (Components V2 / LayoutView)

Add this file as gameprofiles.py and load it as an extension:
    await bot.load_extension("gameprofiles")

Required:
    pip install -U "discord.py>=2.6" aiohttp pillow

Optional Railway variable for Brawl Stars:
    BRAWL_STARS_API_TOKEN = your official Supercell API token

Roblox and Minecraft profile lookups use public endpoints.
Brawl Stars player statistics require a valid official API token.
"""

from __future__ import annotations

import base64
import io
import os
import re
from datetime import datetime, timezone
from typing import Any

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

try:
    from PIL import Image
except ImportError:
    Image = None


# ───────────────────────────── Settings ─────────────────────────────

ROBLOX_EMOJI = "<:Roblox_icon:1567966255095484677>"
MINECRAFT_EMOJI = "<:Minecraft_icon:1567966252880896060>"
BRAWL_EMOJI = "<:Brawl_Stars_icon:1567966256945172642>"

BRAWL_STARS_API_TOKEN = os.getenv("BRAWL_STARS_API_TOKEN", "").strip()
VIEW_TIMEOUT = 300  # 5 minutes
PAGE_SIZE = 3

GAME_LIST = [
    ("roblox", "Roblox", ROBLOX_EMOJI),
    ("minecraft", "Minecraft", MINECRAFT_EMOJI),
    ("brawlstars", "Brawl Stars", BRAWL_EMOJI),
]

DEFAULT_ACCENT = discord.Colour(0x5865F2)


# ───────────────────────────── HTTP helpers ─────────────────────────

async def fetch_json(url: str, *, headers: dict[str, str] | None = None,
                     method: str = "GET", payload: dict | None = None) -> Any:
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.request(method, url, headers=headers, json=payload) as resp:
            if resp.status == 404:
                raise LookupError("No profile was found for that username or player tag.")
            if resp.status == 429:
                raise RuntimeError("The game API is rate-limiting requests. Please try again later.")
            if resp.status == 401 or resp.status == 403:
                raise RuntimeError("The game API rejected the request. Check the API token or access.")
            if resp.status >= 500:
                raise RuntimeError("The game API is temporarily unavailable. Please try again later.")
            if resp.status >= 400:
                body = (await resp.text())[:300]
                raise RuntimeError(f"Game API error ({resp.status}): {body}")
            return await resp.json(content_type=None)


async def fetch_bytes(url: str) -> bytes:
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise RuntimeError("Could not load the profile image.")
            return await resp.read()


def color_from_image(data: bytes) -> discord.Colour:
    """Get a representative color from an avatar/skin image."""
    if Image is None:
        return DEFAULT_ACCENT
    try:
        image = Image.open(io.BytesIO(data)).convert("RGB")
        image.thumbnail((48, 48))
        pixels = list(image.getdata())
        # Ignore nearly white/black pixels; they usually make poor UI accents.
        useful = [p for p in pixels if max(p) - min(p) > 25 and 35 < sum(p) / 3 < 225]
        sample = useful or pixels
        if not sample:
            return DEFAULT_ACCENT
        r = sum(p[0] for p in sample) // len(sample)
        g = sum(p[1] for p in sample) // len(sample)
        b = sum(p[2] for p in sample) // len(sample)
        return discord.Colour.from_rgb(r, g, b)
    except Exception:
        return DEFAULT_ACCENT


def clean_tag(value: str) -> str:
    return value.strip().upper().replace("#", "").replace(" ", "")


def format_date(value: str | None) -> str:
    if not value:
        return "Not publicly available"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return discord.utils.format_dt(dt, style="D")
    except Exception:
        return value


# ───────────────────────────── Profile lookups ──────────────────────

async def get_roblox_profile(username: str) -> dict:
    username = username.strip()
    if not username or len(username) > 20:
        raise ValueError("Enter a valid Roblox username (1–20 characters).")

    lookup = await fetch_json(
        "https://users.roblox.com/v1/usernames/users",
        method="POST",
        payload={"usernames": [username], "excludeBannedUsers": False},
    )
    users = lookup.get("data", [])
    if not users:
        raise LookupError("That Roblox username was not found.")

    user = users[0]
    user_id = int(user["id"])
    profile = await fetch_json(f"https://users.roblox.com/v1/users/{user_id}")

    thumb_data = await fetch_json(
        "https://thumbnails.roblox.com/v1/users/avatar-headshot"
        f"?userIds={user_id}&size=420x420&format=Png&isCircular=false"
    )
    avatar = (thumb_data.get("data") or [{}])[0].get("imageUrl")
    image_bytes = await fetch_bytes(avatar) if avatar else b""

    return {
        "game": "Roblox",
        "username": profile.get("name", username),
        "display_name": profile.get("displayName", profile.get("name", username)),
        "id": str(user_id),
        "description": profile.get("description") or "No description provided.",
        "created": format_date(profile.get("created")),
        "url": f"https://www.roblox.com/users/{user_id}/profile",
        "avatar": avatar,
        "image_bytes": image_bytes,
        "accent": color_from_image(image_bytes) if image_bytes else DEFAULT_ACCENT,
        "fields": [
            ("Display Name", profile.get("displayName", profile.get("name", username))),
            ("User ID", str(user_id)),
            ("Created", format_date(profile.get("created"))),
            ("Description", (profile.get("description") or "No description provided.")[:900]),
        ],
    }


async def get_minecraft_profile(username: str) -> dict:
    username = username.strip()
    if not re.fullmatch(r"[A-Za-z0-9_]{3,16}", username):
        raise ValueError("Enter a valid Minecraft username (3–16 letters, numbers or underscores).")

    profile = await fetch_json(f"https://api.mojang.com/users/profiles/minecraft/{username}")
    uuid = profile.get("id", "")
    name = profile.get("name", username)

    skin_url = f"https://crafatar.com/renders/body/{uuid}?overlay"
    avatar_url = f"https://crafatar.com/avatars/{uuid}?size=256&overlay"
    image_bytes = await fetch_bytes(avatar_url)

    # Mojang does not expose account creation date through this public profile endpoint.
    return {
        "game": "Minecraft",
        "username": name,
        "display_name": name,
        "id": uuid,
        "description": "Minecraft Java/Bedrock username lookup (Mojang profile).",
        "created": "Not publicly available through Mojang's public API",
        "url": f"https://namemc.com/profile/{uuid}",
        "avatar": avatar_url,
        "image_bytes": image_bytes,
        "accent": color_from_image(image_bytes),
        "fields": [
            ("Username", name),
            ("UUID", uuid),
            ("Account Created", "Not publicly available"),
            ("Profile", f"[View Minecraft profile](https://namemc.com/profile/{uuid})"),
        ],
    }


async def get_brawlstars_profile(player_tag: str) -> dict:
    if not BRAWL_STARS_API_TOKEN:
        raise RuntimeError(
            "Brawl Stars profile lookup is not configured yet. "
            "Add the official Supercell API token to Railway as "
            "`BRAWL_STARS_API_TOKEN`, then redeploy."
        )

    tag = clean_tag(player_tag)
    if not re.fullmatch(r"[A-Z0-9]{3,15}", tag):
        raise ValueError("Enter a valid Brawl Stars player tag (with or without #).")

    headers = {"Authorization": f"Bearer {BRAWL_STARS_API_TOKEN}"}
    player = await fetch_json(f"https://api.brawlstars.com/v1/players/%23{tag}", headers=headers)

    icon_id = (player.get("icon") or {}).get("id")
    avatar = (
        f"https://cdn.brawlify.com/profile-icons/regular/{icon_id}.png"
        if icon_id else None
    )
    image_bytes = await fetch_bytes(avatar) if avatar else b""

    club = player.get("club") or {}
    return {
        "game": "Brawl Stars",
        "username": player.get("name", tag),
        "display_name": player.get("name", tag),
        "id": f"#{player.get('tag', tag)}",
        "description": "Brawl Stars player profile.",
        "created": "Not publicly available",
        "url": f"https://brawlify.com/stats/profile/{tag}",
        "avatar": avatar,
        "image_bytes": image_bytes,
        "accent": color_from_image(image_bytes) if image_bytes else DEFAULT_ACCENT,
        "fields": [
            ("Player Tag", f"#{player.get('tag', tag)}"),
            ("Trophies", f"{player.get('trophies', 0):,}"),
            ("Highest Trophies", f"{player.get('highestTrophies', 0):,}"),
            ("Experience Level", str(player.get("expLevel", "Unknown"))),
            ("3v3 Victories", f"{player.get('3vs3Victories', 0):,}"),
            ("Solo Victories", f"{player.get('soloVictories', 0):,}"),
            ("Duo Victories", f"{player.get('duoVictories', 0):,}"),
            ("Club", club.get("name", "No club")),
        ],
    }


# ───────────────────────────── Components V2 views ──────────────────

def game_emoji(name: str) -> str:
    return {
        "Roblox": ROBLOX_EMOJI,
        "Minecraft": MINECRAFT_EMOJI,
        "Brawl Stars": BRAWL_EMOJI,
    }.get(name, "🎮")


class GameProfileModal(discord.ui.Modal):
    def __init__(self, parent_view: "GameProfilesView", game_key: str):
        game_name = dict((key, name) for key, name, _ in GAME_LIST)[game_key]
        super().__init__(title=f"{game_name} Profile")
        self.parent_view = parent_view
        self.game_key = game_key

        label = {
            "roblox": "Roblox username",
            "minecraft": "Minecraft username",
            "brawlstars": "Brawl Stars player tag",
        }[game_key]
        placeholder = {
            "roblox": "Enter Roblox username",
            "minecraft": "Enter Minecraft username",
            "brawlstars": "Enter player tag (e.g. #ABC123)",
        }[game_key]

        self.username = discord.ui.TextInput(
            label=label,
            placeholder=placeholder,
            max_length=30,
            required=True,
        )
        self.add_item(self.username)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.parent_view.owner_id:
            await interaction.response.send_message(
                "Only the person who opened this menu can use it.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        try:
            if self.game_key == "roblox":
                profile = await get_roblox_profile(str(self.username))
            elif self.game_key == "minecraft":
                profile = await get_minecraft_profile(str(self.username))
            else:
                profile = await get_brawlstars_profile(str(self.username))

            self.parent_view.profile = profile
            self.parent_view.accent = profile["accent"]
            await self.parent_view.show_profile()
        except (ValueError, LookupError, RuntimeError, aiohttp.ClientError) as exc:
            await interaction.followup.send(f"⚠️ {exc}", ephemeral=True)
        except Exception:
            await interaction.followup.send(
                "Something went wrong while loading this profile. Please try again later.",
                ephemeral=True,
            )


class GameProfilesView(discord.ui.LayoutView):
    def __init__(self, owner_id: int):
        super().__init__(timeout=VIEW_TIMEOUT)
        self.owner_id = owner_id
        self.page = 0
        self.profile: dict | None = None
        self.accent = DEFAULT_ACCENT
        self.message: discord.Message | None = None
        self.expired = False
        self.build_menu()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This Game Profiles menu belongs to another user.",
                ephemeral=True,
            )
            return False
        if self.expired:
            await interaction.response.send_message(
                "This menu has expired. Run `/gameprofiles` again.",
                ephemeral=True,
            )
            return False
        return True

    def build_menu(self):
        self.clear_items()
        self.add_item(discord.ui.Container(
            discord.ui.Section(
                discord.ui.TextDisplay("# 🎮 Game Profiles\nChoose a game to view your profile."),
                accessory=discord.ui.Thumbnail(
                    "https://cdn.discordapp.com/embed/avatars/0.png",
                    description="Game Profiles"
                ),
            ),
            discord.ui.Separator(),
            discord.ui.TextDisplay(
                f"{ROBLOX_EMOJI} **Roblox**\n"
                f"{MINECRAFT_EMOJI} **Minecraft**\n"
                f"{BRAWL_EMOJI} **Brawl Stars**"
            ),
            discord.ui.Separator(),
            discord.ui.TextDisplay(
                "Select a game below to look up a profile.\n"
                "Only you can use these controls. This menu expires in **5 minutes**."
            ),
            accent_colour=self.accent,
        ))

        options = [
            discord.SelectOption(
                label=name,
                value=key,
                emoji=discord.PartialEmoji.from_str(custom_emoji),
                description=f"View a {name} profile",
            )
            for key, name, custom_emoji in GAME_LIST
        ]
        select = discord.ui.Select(
            placeholder="Choose a game...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"gameprofiles_select_{self.owner_id}",
        )

        async def select_callback(interaction: discord.Interaction):
            key = select.values[0]
            await interaction.response.send_modal(GameProfileModal(self, key))

        select.callback = select_callback
        self.add_item(discord.ui.ActionRow(select))

        # Page controls are included for future expansion. With the initial three games,
        # the single page is intentionally disabled.
        prev_button = discord.ui.Button(
            label="Back Page", emoji="⬅️", style=discord.ButtonStyle.secondary,
            disabled=True, custom_id=f"gameprofiles_prev_{self.owner_id}"
        )
        next_button = discord.ui.Button(
            label="Next Page", emoji="➡️", style=discord.ButtonStyle.secondary,
            disabled=True, custom_id=f"gameprofiles_next_{self.owner_id}"
        )
        prev_button.callback = self.page_back
        next_button.callback = self.page_next
        self.add_item(discord.ui.ActionRow(prev_button, next_button))

    async def show_profile(self):
        if not self.message or not self.profile:
            return

        profile = self.profile
        self.clear_items()

        description = profile.get("description", "No description provided.")
        fields_text = "\n".join(
            f"**{label}:** {value}" for label, value in profile.get("fields", [])
        )

        avatar_url = profile.get("avatar")
        accessory = discord.ui.Thumbnail(
            avatar_url or "https://cdn.discordapp.com/embed/avatars/0.png",
            description=f"{profile['game']} avatar"
        )

        container = discord.ui.Container(
            discord.ui.Section(
                discord.ui.TextDisplay(
                    f"# {game_emoji(profile['game'])} {profile['game']} Profile\n"
                    f"**{profile.get('display_name', profile['username'])}**\n"
                    f"`{profile['username']}`"
                ),
                accessory=accessory,
            ),
            discord.ui.Separator(),
            discord.ui.TextDisplay(fields_text[:3500]),
            discord.ui.Separator(),
            discord.ui.TextDisplay(
                f"**About**\n{description[:700]}\n\n"
                f"[🔗 View Profile]({profile['url']})"
            ),
            accent_colour=self.accent,
        )
        self.add_item(container)

        back = discord.ui.Button(
            label="Back", emoji="↩️", style=discord.ButtonStyle.secondary,
            custom_id=f"gameprofiles_back_{self.owner_id}"
        )
        back.callback = self.back_to_games
        self.add_item(discord.ui.ActionRow(back))

        await self.message.edit(view=self)

    async def back_to_games(self, interaction: discord.Interaction):
        self.profile = None
        self.accent = DEFAULT_ACCENT
        self.build_menu()
        await interaction.response.edit_message(view=self)

    async def page_back(self, interaction: discord.Interaction):
        await interaction.response.defer()

    async def page_next(self, interaction: discord.Interaction):
        await interaction.response.defer()

    async def on_timeout(self):
        self.expired = True
        self.clear_items()
        self.add_item(discord.ui.Container(
            discord.ui.TextDisplay(
                "# ⏰ Game Profiles Expired\n"
                "This menu has expired after **5 minutes**.\n"
                "Run `/gameprofiles` again to open a new menu."
            ),
            accent_colour=discord.Colour(0x747F8D),
        ))
        if self.message:
            try:
                await self.message.edit(view=self)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass


# ───────────────────────────── Cog ───────────────────────────────────

class GameProfiles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="gameprofiles",
        description="Open the interactive Roblox, Minecraft and Brawl Stars profile menu."
    )
    async def gameprofiles(self, interaction: discord.Interaction):
        view = GameProfilesView(interaction.user.id)
        await interaction.response.send_message(view=view, ephemeral=False)
        view.message = await interaction.original_response()


async def setup(bot: commands.Bot):
    await bot.add_cog(GameProfiles(bot))
