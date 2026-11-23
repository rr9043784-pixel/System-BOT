# -*- coding: utf-8 -*-
"""
LEGENDS ECONOMY
Discord.py 2.6+ | Python 3.13+
SQLite persistence | Components V2
"""

import os
import sqlite3
import random
import logging
import asyncio
from datetime import datetime, date, timedelta, time
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

log = logging.getLogger("LEGENDS_ECONOMY")

OWNER_ID = 1176149190192152626
VERIFIED_ROLE_ID = 1546987754968326154
NEWS_CHANNEL_ID = 1558092423614304328
PING_ROLE_ID = 1541715546356060200
LEGEND_ECONOMY_ROLE_ID = 1574503562275328101
BAKU = ZoneInfo("Asia/Baku")

DATA_DIR = os.environ.get("DATA_DIR", ".")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "legends_economy.db")

INCLUDED = "<:Included:1557532189883629609>"
DISABLED = "<:Disabled:1557532191406166076>"

# Economy order is also the order used in the owner panel.
ECONOMIES = {
    "summer": {
        "name": "☀️ Summer Season",
        "category": 1574132296959918160,
        "channels": [1574433873478295612, 1574434769180037182, 1574434988370165892],
        "currency": "<:Summer_money:1574503961904414820>",
        "start": (6, 1), "end": (8, 31),
    },
    "spring": {
        "name": "🌸 Spring Season",
        "category": 1574132105028436008,
        "channels": [1574433842440441886, 1574435361273286656, 1574435414654193754],
        "currency": "<:Spring_money:1574503947258036405>",
        "start": (3, 1), "end": (5, 31),
    },
    "autumn": {
        "name": "🍂 Autumn Season",
        "category": 1574132571770720467,
        "channels": [1574433822735335485, 1574435556828389476, 1574435612054790306],
        "currency": "<:Autumn_money:1574503959505408061>",
        "start": (9, 1), "end": (11, 30),
    },
    "winter": {
        "name": "❄️ Winter Season",
        "category": 1574132669988610168,
        "channels": [1574433785875800156, 1574435721958260926, 1574435769760751666],
        "currency": "<:Winter_money:1574503964089647144>",
        "start": (12, 1), "end": (2, 28),
    },
    "halloween": {
        "name": "🎃 Halloween",
        "category": 1564365334356688926,
        "channels": [1564365579144663040, 1564365633129549844, 1564365740629434409],
        "currency": "<:Halloween_money:1574503970989285488>",
        "start": (10, 25), "end": (10, 31),
    },
    "valentines": {
        "name": "❤️ Valentine's Day",
        "category": 1574133104975548478,
        "channels": [1574433763449114686, 1574435911293337723, 1574435963092865104],
        "currency": "<:Valentines_money:1574503966840979466>",
        "start": (2, 7), "end": (2, 14),
    },
    "newyear": {
        "name": "🎆 New Year",
        "category": 1574133258315239536,
        "channels": [1574433734445244527, 1574436121260073093, 1574436153463934976],
        "currency": "<:New_year_money:1574503954669371422>",
        "start": (12, 25), "end": (1, 7),
    },
    "christmas": {
        "name": "🎄 Christmas",
        "category": 1574133410061090856,
        "channels": [1574433712559358152, 1574436340278231040, 1574436383630696539],
        "currency": "<:Christmas_money:1574503973988339712>",
        "start": (12, 20), "end": (12, 26),
    },
    "easter": {
        "name": "🐰 Easter",
        "category": 1574133610997350571,
        "channels": [1574433670348152955, 1574436503227072542, 1574436538954023063],
        "currency": "<:easter_egg_money:1574503976320245970>",
        "start": None, "end": None,
    },
    "stpatrick": {
        "name": "🍀 St. Patrick's Day",
        "category": 1574133969329459370,
        "channels": [1574433650991169686, 1574436638048780491, 1574436697834258522],
        "currency": "<:Stpatricks_money:1574503952118980618>",
        "start": (3, 10), "end": (3, 17),
    },
    "independence": {
        "name": "🎆 Independence Day",
        "category": 1574134293893087313,
        "channels": [1574433607483785296, 1574436922388910191, 1574436952462327938],
        "currency": "<:Independence_money:1574503949552189620>",
        "start": (5, 21), "end": (5, 28),
    },
}

# Every economy has six sequential levels: L1, L2, L3, L4, L5, L∞.
# Role IDs and colors are kept exactly as supplied.
ROLE_DATA = {
    "valentines": [
        ("💌・Love Letter",1574122212934422723,"#FFC0CB"),
        ("🌹・Rose Heart",1574122213672489050,"#FF91AF"),
        ("💝・Sweet Romance",1574122214612144128,"#FF69B4"),
        ("💗・Eternal Love",1574122215262388438,"#E75480"),
        ("💘・Valentine Legend",1574122216155648062,"#DC143C"),
        ("❤️・Valentine God",1574122217116139655,"#8B003A"),
    ],
    "newyear": [
        ("🎄・New Year Spark",1574122218235891843,"#BDE0FE"),
        ("🎁・Gift Hunter",1574122218806444176,"#87CEEB"),
        ("❄️・Winter Magic",1574122219523678248,"#4169E1"),
        ("🌟・Golden Midnight",1574122220379312249,"#DAA520"),
        ("🎆・New Year Legend",1574122221629210644,"#FFD700"),
        ("🎆・New Year God",1574122222308560947,"#8B6914"),
    ],
    "christmas": [
        ("🔔・Jingle Bell",1574122222971396178,"#90EE90"),
        ("⛄・Snow Buddy",1574122224242397224,"#32CD32"),
        ("🎅・Santa's Helper",1574122224921739345,"#228B22"),
        ("❄️・Frost Master",1574122226377035937,"#C41E3A"),
        ("🎄・Christmas Legend",1574122227031609405,"#B22222"),
        ("🎄・Christmas God",1574122227832725734,"#6B1020"),
    ],
    "halloween": [
        ("🎃・Pumpkin Soul",1574122228780367942,"#FF7518"),
        ("👻・Ghost Hunter",1574122229405450454,"#E65C00"),
        ("🦇・Dark Spirit",1574122231246758078,"#9932CC"),
        ("🕸️・Nightmare King",1574122231519248548,"#6A0DAD"),
        ("💀・Halloween Legend",1574122232601382912,"#4B0082"),
        ("🎃・Halloween God",1574122233373397002,"#2B003F"),
    ],
    "easter": [
        ("🥚・Egg Finder",1574122234099015811,"#FFF0A6"),
        ("🐣・Little Chick",1574122235235405967,"#FFD1DC"),
        ("🌷・Spring Bloom",1574122236275855440,"#C8A2C8"),
        ("🐰・Bunny Spirit",1574122238704353522,"#A8D8B9"),
        ("💐・Easter Legend",1574122239572578335,"#B19CD9"),
        ("🐰・Easter God",1574122240583405658,"#8055A5"),
    ],
    "stpatrick": [
        ("🍀・Lucky Charm",1574122241401028648,"#ADFF2F"),
        ("💚・Green Clover",1574122245872291853,"#7CFC00"),
        ("🌈・Rainbow Hunter",1574122246572744827,"#32CD32"),
        ("🪙・Gold Keeper",1574122247759593583,"#228B22"),
        ("☘️・Lucky Legend",1574122249332596847,"#006400"),
        ("🍀・Luck God",1574122250058334288,"#003300"),
    ],
    "independence": [
        ("🎇・First Spark",1574122251165376634,"#ADD8E6"),
        ("🗽・Freedom Soul",1574122252910206986,"#6495ED"),
        ("⭐・Star Guardian",1574122253656793131,"#4169E1"),
        ("🦅・Liberty Spirit",1574122254797770923,"#DC143C"),
        ("🎆・Freedom Legend",1574122255401877676,"#B22222"),
        ("🎆・Liberty God",1574122256760574103,"#8B0000"),
    ],
    "summer": [
        ("🌤️・Summer Breeze",1574122257255506152,"#FFF176"),
        ("🏖️・Sunny Days",1574122258161475615,"#FFD54F"),
        ("🌊・Ocean Soul",1574122259302584540,"#40C4FF"),
        ("🌴・Tropical Paradise",1574122260103438468,"#00A6C7"),
        ("☀️・Summer Legend",1574122260900356241,"#008B8B"),
        ("☀️・Summer God",1574122265132671017,"#006994"),
    ],
    "spring": [
        ("🌱・Spring Bloom",1574122265715413062,"#C1E1C1"),
        ("🌷・Pink Blossom",1574122266600411267,"#FFB6C1"),
        ("🦋・Butterfly Soul",1574122267246600302,"#DDA0DD"),
        ("🌺・Floral Paradise",1574122268236447834,"#DA70D6"),
        ("🌸・Spring Legend",1574122269104414892,"#DB7093"),
        ("🌸・Spring God",1574122270106976351,"#8B3A62"),
    ],
    "autumn": [
        ("🍁・Autumn Leaf",1574122271281254443,"#F4A460"),
        ("🍂・Golden Fall",1574122272283693137,"#DEB887"),
        ("🌾・Harvest Soul",1574122272984404018,"#D2691E"),
        ("🦊・Forest Guardian",1574122273768738842,"#CD853F"),
        ("🍁・Autumn Legend",1574122275320635493,"#A0522D"),
        ("🍂・Autumn God",1574122276058693898,"#704214"),
    ],
    "winter": [
        ("❄️・Snowflake",1574122277111603392,"#BDEBFF"),
        ("⛄・Frost Walker",1574122277958721576,"#87CEEB"),
        ("🧊・Ice Soul",1574122278218760346,"#4DB8FF"),
        ("🌨️・Frozen Spirit",1574122279581913278,"#2980B9"),
        ("❄️・Winter Legend",1574122280492081343,"#4169E1"),
        ("❄️・Winter God",1574122281368686622,"#172B70"),
    ],
}

LEVEL_PRICES = [300_000, 500_000, 800_000, 1_050_000, 1_500_000, 4_000_000]
LEVEL_INCOME = [50_000, 100_000, 200_000, 300_000, 500_000, 1_000_000]
COMMANDS_TEXT = (
    "`,work` — earn 10,000–20,000 (1h cooldown)\n"
    "`,slut` — 50/50 risk game (1h cooldown)\n"
    "`,crime` — 50/50 risk game (1h cooldown)\n"
    "`,rob @member` — attempt a robbery (24h cooldown)\n"
    "`,collect` — collect role income (24h cooldown)\n"
    "`,bal [@member]` — view wallet and bank\n"
    "`,dep <amount|all>` — deposit money\n"
    "`,with <amount|all>` — withdraw money\n"
    "`,shop` — view seasonal roles\n"
    "`,buy <1-6>` — purchase or upgrade a role\n"
    "`,gift @member <1-6>` — buy a role for someone\n"
    "`,transfer @member <1-6>` — transfer your owned role\n"
)

LANGUAGES = [
    ("🇬🇧 English","en"),("🇷🇺 Russian","ru"),("🇷🇴 Romanian","ro"),
    ("🇺🇿 Uzbek","uz"),("🇰🇿 Kazakh","kk"),("🇹🇷 Turkish","tr"),
    ("🇪🇸 Spanish","es"),("🇫🇷 French","fr"),("🇩🇪 German","de"),
    ("🇮🇹 Italian","it"),("🇺🇦 Ukrainian","uk"),("🇵🇱 Polish","pl"),
]
INFO_TEXT = {
    "en": "This seasonal economy has its own currency, wallet, bank and six collectible role levels. Your purchased roles remain yours after the economy is switched off.",
    "ru": "У этой сезонной экономики есть собственная валюта, кошелёк, банк и шесть уровней коллекционных ролей. Купленные роли остаются у вас после отключения экономики.",
    "ro": "Această economie sezonieră are propria monedă, portofel, bancă și șase niveluri de roluri de colecție. Rolurile cumpărate rămân ale tale după dezactivare.",
    "uz": "Ushbu mavsumiy iqtisodiyotning o‘z valyutasi, hamyoni, banki va oltita kolleksiya roli darajasi bor. Xarid qilingan rollar iqtisodiyot o‘chirilgandan keyin ham qoladi.",
    "kk": "Бұл маусымдық экономиканың өз валютасы, әмияны, банкі және коллекциялық рөлдердің алты деңгейі бар. Сатып алынған рөлдер экономика өшірілгеннен кейін де сақталады.",
    "tr": "Bu sezonluk ekonominin kendi para birimi, cüzdanı, bankası ve altı koleksiyon rolü seviyesi vardır. Satın alınan roller ekonomi kapatıldıktan sonra da sende kalır.",
    "es": "Esta economía de temporada tiene su propia moneda, cartera, banco y seis niveles de roles coleccionables. Los roles comprados permanecen contigo al desactivarse.",
    "fr": "Cette économie saisonnière possède sa propre monnaie, un portefeuille, une banque et six niveaux de rôles à collectionner. Les rôles achetés restent acquis après sa désactivation.",
    "de": "Diese saisonale Wirtschaft hat eine eigene Währung, Geldbörse, Bank und sechs Sammelrollen-Stufen. Gekaufte Rollen bleiben auch nach der Deaktivierung erhalten.",
    "it": "Questa economia stagionale ha una valuta, un portafoglio, una banca e sei livelli di ruoli da collezionare. I ruoli acquistati restano tuoi dopo la disattivazione.",
    "uk": "Ця сезонна економіка має власну валюту, гаманець, банк і шість рівнів колекційних ролей. Придбані ролі залишаються у вас після вимкнення економіки.",
    "pl": "Ta sezonowa ekonomia ma własną walutę, portfel, bank i sześć poziomów ról kolekcjonerskich. Kupione role pozostają twoje po wyłączeniu ekonomii.",
}

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS balances (
            guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
            economy TEXT NOT NULL, wallet INTEGER NOT NULL DEFAULT 0,
            bank INTEGER NOT NULL DEFAULT 0, infinity INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(guild_id,user_id,economy)
        );
        CREATE TABLE IF NOT EXISTS cooldowns (
            guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
            economy TEXT NOT NULL, command TEXT NOT NULL, until_ts INTEGER NOT NULL,
            PRIMARY KEY(guild_id,user_id,economy,command)
        );
        CREATE TABLE IF NOT EXISTS ownership (
            guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
            economy TEXT NOT NULL, level INTEGER NOT NULL,
            PRIMARY KEY(guild_id,user_id,economy)
        );
        CREATE TABLE IF NOT EXISTS reminders (
            reminder_key TEXT PRIMARY KEY
        );
        CREATE TABLE IF NOT EXISTS panels (
            name TEXT PRIMARY KEY, channel_id INTEGER NOT NULL, message_id INTEGER NOT NULL
        );
        """)

def get_setting(key, default=None):
    with db() as con:
        row = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

def set_setting(key, value):
    with db() as con:
        con.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (key, str(value)))

def active_economy():
    return get_setting("active_economy")

def ensure_balance(guild_id, user_id, economy):
    with db() as con:
        con.execute("INSERT OR IGNORE INTO balances(guild_id,user_id,economy) VALUES(?,?,?)",
                    (guild_id, user_id, economy))
        return con.execute("SELECT * FROM balances WHERE guild_id=? AND user_id=? AND economy=?",
                           (guild_id,user_id,economy)).fetchone()

def get_balance(guild_id, user_id, economy):
    row = ensure_balance(guild_id,user_id,economy)
    return row["wallet"], row["bank"], bool(row["infinity"])

def change_balance(guild_id, user_id, economy, wallet_delta=0, bank_delta=0):
    with db() as con:
        con.execute("INSERT OR IGNORE INTO balances(guild_id,user_id,economy) VALUES(?,?,?)",
                    (guild_id,user_id,economy))
        row = con.execute("SELECT * FROM balances WHERE guild_id=? AND user_id=? AND economy=?",
                          (guild_id,user_id,economy)).fetchone()
        if row["infinity"]:
            return
        wallet = max(0, row["wallet"] + int(wallet_delta))
        bank = max(0, row["bank"] + int(bank_delta))
        con.execute("UPDATE balances SET wallet=?,bank=? WHERE guild_id=? AND user_id=? AND economy=?",
                    (wallet,bank,guild_id,user_id,economy))

def set_cooldown(guild_id, user_id, economy, command, seconds):
    until = int(datetime.now().timestamp()) + seconds
    with db() as con:
        con.execute("""INSERT INTO cooldowns VALUES(?,?,?,?,?)
        ON CONFLICT(guild_id,user_id,economy,command) DO UPDATE SET until_ts=excluded.until_ts""",
                    (guild_id,user_id,economy,command,until))

def cooldown_left(guild_id, user_id, economy, command):
    with db() as con:
        row = con.execute("SELECT until_ts FROM cooldowns WHERE guild_id=? AND user_id=? AND economy=? AND command=?",
                          (guild_id,user_id,economy,command)).fetchone()
    return max(0, row["until_ts"] - int(datetime.now().timestamp())) if row else 0

def owned_level(guild_id, user_id, economy):
    with db() as con:
        row = con.execute("SELECT level FROM ownership WHERE guild_id=? AND user_id=? AND economy=?",
                          (guild_id,user_id,economy)).fetchone()
    return row["level"] if row else 0

def set_owned_level(guild_id, user_id, economy, level):
    with db() as con:
        con.execute("""INSERT INTO ownership VALUES(?,?,?,?)
        ON CONFLICT(guild_id,user_id,economy) DO UPDATE SET level=excluded.level""",
                    (guild_id,user_id,economy,level))

def fmt(value):
    return "∞" if value is None else f"{value:,}"

def money_text(member, economy):
    wallet, bank, infinity = get_balance(member.guild.id, member.id, economy)
    symbol = ECONOMIES[economy]["currency"]
    if infinity:
        return f"**Wallet:** ∞ {symbol}\n**Bank:** ∞ {symbol}\n**Total:** ∞ {symbol}"
    return f"**Wallet:** {wallet:,} {symbol}\n**Bank:** {bank:,} {symbol}\n**Total:** {wallet+bank:,} {symbol}"

def v2_view(text, *, timeout=180):
    view = discord.ui.LayoutView(timeout=timeout)
    view.add_item(discord.ui.Container(discord.ui.TextDisplay(text)))
    return view

async def reply_v2(ctx_or_interaction, text, *, ephemeral=False, view=None):
    view = view or v2_view(text)
    if isinstance(ctx_or_interaction, discord.Interaction):
        if ctx_or_interaction.response.is_done():
            await ctx_or_interaction.followup.send(view=view, ephemeral=ephemeral)
        else:
            await ctx_or_interaction.response.send_message(view=view, ephemeral=ephemeral)
    else:
        await ctx_or_interaction.send(view=view)

def owner_only():
    async def predicate(ctx):
        return ctx.author.id == OWNER_ID
    return commands.check(predicate)

def easter_sunday(year):
    # Gregorian Easter computus.
    a=year%19; b=year//100; c=year%100; d=b//4; e=b%4
    f=(b+8)//25; g=(b-f+1)//3; h=(19*a+b-d-g+15)%30
    i=c//4; k=c%4; l=(32+2*e+2*i-h-k)%7
    m=(a+11*h+22*l)//451
    month=(h+l-7*m+114)//31
    day=((h+l-7*m+114)%31)+1
    return date(year,month,day)

def event_dates(key, year):
    cfg=ECONOMIES[key]
    if key == "easter":
        end=easter_sunday(year)
        return end-timedelta(days=6), end
    sm,sd=cfg["start"]; em,ed=cfg["end"]
    start=date(year,sm,sd)
    end_year=year+1 if (em,ed) < (sm,sd) else year
    if key == "winter":
        end=date(year+1,2,29 if (year+1)%4==0 and ((year+1)%100!=0 or (year+1)%400==0) else 28)
    else:
        end=date(end_year,em,ed)
    return start,end

class AdminButton(discord.ui.Button):
    def __init__(self, label, style, custom_id):
        super().__init__(label=label, style=style, custom_id=custom_id)
    async def callback(self, interaction):
        view = self.view
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("Only the bot owner can use this panel.", ephemeral=True)
        action = self.custom_id.split(":")
        if action[1] == "select":
            view.selected = action[2]
            view.page = "language"
        elif action[1] == "off":
            await view.cog.deactivate(interaction.guild)
            view.page = "home"
            view.selected = None
        elif action[1] == "lang":
            view.lang = action[2]
            view.page = "info"
        elif action[1] == "back":
            view.page = "home"
            view.selected = None
        elif action[1] == "backhome":
            view.page = "language"
        elif action[1] == "activate":
            await view.cog.activate(interaction.guild, action[2])
            view.page = "info"
        view.render()
        await interaction.response.edit_message(view=view)


class EconomyAdminView(discord.ui.LayoutView):
    def __init__(self, cog, selected=None, page="home", lang=None):
        super().__init__(timeout=900)
        self.cog=cog; self.selected=selected; self.page=page; self.lang=lang
        self.render()

    def render(self):
        self.clear_items()
        active=active_economy()
        if self.page == "home":
            lines=["## LEGENDS ECONOMY — OWNER PANEL",
                   f"**Active economy:** {ECONOMIES[active]['name'] if active in ECONOMIES else 'OFF'}",
                   "Select an economy to open its information and controls."]
            self.add_item(discord.ui.Container(discord.ui.TextDisplay("\n".join(lines))))
            keys=list(ECONOMIES.items())
            for start in range(0, len(keys), 5):
                row=discord.ui.ActionRow()
                for key,cfg in keys[start:start+5]:
                    style=discord.ButtonStyle.primary if key==active else discord.ButtonStyle.danger
                    button=AdminButton(label=cfg["name"],style=style,
                        custom_id=f"legends:select:{key}")
                    if key == active:
                        button.disabled = True
                    row.add_item(button)
                self.add_item(row)
            off=discord.ui.ActionRow()
            off.add_item(AdminButton(label="OFF ECONOMY",style=discord.ButtonStyle.danger,
                                           custom_id="legends:off"))
            self.add_item(off)
        elif self.page == "language":
            cfg=ECONOMIES[self.selected]
            self.add_item(discord.ui.Container(discord.ui.TextDisplay(
                f"## {cfg['name']}\nChoose a language to read the economy information.")))
            for start in range(0,len(LANGUAGES),4):
                row=discord.ui.ActionRow()
                for label,code in LANGUAGES[start:start+4]:
                    row.add_item(AdminButton(label=label,style=discord.ButtonStyle.secondary,
                        custom_id=f"legends:lang:{code}"))
                self.add_item(row)
            back=discord.ui.ActionRow()
            back.add_item(AdminButton(label="Back",style=discord.ButtonStyle.secondary,
                                            custom_id="legends:back"))
            self.add_item(back)
        else:
            cfg=ECONOMIES[self.selected]
            text=(f"## {cfg['name']}\n{INFO_TEXT.get(self.lang,'en')}\n\n"
                  f"**Commands**\n{COMMANDS_TEXT}\n"
                  f"**Status:** {INCLUDED if active==self.selected else DISABLED} "
                  f"{'Active' if active==self.selected else 'Inactive'}")
            self.add_item(discord.ui.Container(discord.ui.TextDisplay(text)))
            row=discord.ui.ActionRow()
            if active != self.selected:
                row.add_item(AdminButton(label="Activate Economy",style=discord.ButtonStyle.success,
                    custom_id=f"legends:activate:{self.selected}"))
            else:
                row.add_item(discord.ui.Button(label="Currently Active",style=discord.ButtonStyle.primary,
                    disabled=True,custom_id="legends:active"))
            row.add_item(AdminButton(label="Back",style=discord.ButtonStyle.secondary,
                                           custom_id="legends:backhome"))
            self.add_item(row)

    async def interaction_check(self, interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("Only the bot owner can use this panel.",ephemeral=True)
            return False
        return True


class EconomyRouter(discord.ui.View):
    def __init__(self, cog, *, timeout=None):
        super().__init__(timeout=timeout)
        self.cog=cog

    @discord.ui.button(label="Open economy panel",style=discord.ButtonStyle.primary,custom_id="legends:router")
    async def router(self, interaction, button):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("Only the bot owner can use this panel.",ephemeral=True)
        await interaction.response.send_message(view=EconomyAdminView(self.cog),ephemeral=True)

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot=bot
        init_db()
        if not self.reminder_loop.is_running():
            self.reminder_loop.start()

    def cog_unload(self):
        self.reminder_loop.cancel()

    async def activate(self, guild, key):
        previous=active_economy()
        if previous == key:
            return
        # Reset balances for the economy being left; purchased roles remain untouched.
        if previous in ECONOMIES:
            with db() as con:
                con.execute("UPDATE balances SET wallet=0,bank=0,infinity=0 WHERE economy=?",(previous,))
            await self.set_access(guild, previous, False)
        set_setting("active_economy",key)
        await self.set_access(guild,key,True)
        channel=guild.get_channel(NEWS_CHANNEL_ID)
        if channel:
            await channel.send(
                f"<@&{PING_ROLE_ID}> **{ECONOMIES[key]['name']} is now active!**\n"
                f"The seasonal economy is open. Use `,work`, `,bal` and `,shop` to get started.",
                allowed_mentions=discord.AllowedMentions(roles=True))
    async def deactivate(self, guild):
        previous=active_economy()
        if previous in ECONOMIES:
            with db() as con:
                con.execute("UPDATE balances SET wallet=0,bank=0,infinity=0 WHERE economy=?",(previous,))
            await self.set_access(guild,previous,False)
        set_setting("active_economy","")
    async def set_access(self,guild,key,enabled):
        cfg=ECONOMIES[key]
        ids=[cfg["category"],*cfg["channels"]]
        role=guild.get_role(VERIFIED_ROLE_ID)
        if not role:
            raise RuntimeError("Verified role was not found.")
        for cid in ids:
            channel=guild.get_channel(cid)
            if channel is None:
                log.warning("Economy channel/category %s not found",cid)
                continue
            overwrite=channel.overwrites_for(role)
            overwrite.view_channel=True if enabled else False
            await channel.set_permissions(role,overwrite=overwrite,reason="LEGENDS ECONOMY access toggle")

    @commands.group(name="economy",invoke_without_command=True)
    @owner_only()
    async def economy_panel(self,ctx):
        await ctx.send(view=EconomyAdminView(self))

    @economy_panel.group(name="set",invoke_without_command=True)
    @owner_only()
    async def economy_set(self,ctx):
        await reply_v2(ctx,"Use `!economy set bal` to open the balance manager.")

    @economy_set.command(name="bal")
    @owner_only()
    async def set_balance_panel(self,ctx):
        await reply_v2(ctx,
            "## Economy Balance Manager\n"
            "Use `!economy set amount @member <economy> <wallet|bank> <amount>`.\n"
            "Use `!economy set infinity @member <economy>` to set Wallet and Bank to ∞.")

    @economy_set.command(name="amount")
    @owner_only()
    async def set_amount(self,ctx,member:discord.Member,economy:str,account:str,amount:int):
        economy=economy.lower()
        if economy not in ECONOMIES or account.lower() not in ("wallet","bank") or amount<0:
            return await reply_v2(ctx,"Invalid economy, account, or amount.")
        ensure_balance(ctx.guild.id,member.id,economy)
        with db() as con:
            con.execute(f"UPDATE balances SET {account.lower()}=?,infinity=0 WHERE guild_id=? AND user_id=? AND economy=?",
                        (amount,ctx.guild.id,member.id,economy))
        await reply_v2(ctx,f"Set **{account.title()}** for {member.mention} to **{amount:,}**.")

    @economy_set.command(name="infinity")
    @owner_only()
    async def set_infinity(self,ctx,member:discord.Member,economy:str):
        economy=economy.lower()
        if economy not in ECONOMIES:
            return await reply_v2(ctx,"Unknown economy.")
        ensure_balance(ctx.guild.id,member.id,economy)
        with db() as con:
            con.execute("UPDATE balances SET infinity=1 WHERE guild_id=? AND user_id=? AND economy=?",
                        (ctx.guild.id,member.id,economy))
        await reply_v2(ctx,f"Granted **∞ Wallet and ∞ Bank** to {member.mention} in {ECONOMIES[economy]['name']}.")

    @commands.command(name="commands")
    async def commands_root(self,ctx,*args):
        if args and args[0].lower()=="system":
            await reply_v2(ctx,"## LEGENDS ECONOMY — COMMANDS\n"+COMMANDS_TEXT+
                "\n**Owner:** `!economy`, `!economy set bal`, `!economy set amount`, `!economy set infinity`.")
        else:
            await reply_v2(ctx,"Use `!commands System` to view the System-BOT economy commands.")

    async def require_active(self,ctx):
        key=active_economy()
        if key not in ECONOMIES:
            await reply_v2(ctx,"The economy is currently disabled.")
            return None
        if not ctx.guild:
            return None
        return key

    async def cooldown_check(self,ctx,key,command,seconds):
        left=cooldown_left(ctx.guild.id,ctx.author.id,key,command)
        if left:
            await reply_v2(ctx,f"Please wait **{left//3600}h {(left%3600)//60}m {left%60}s** before using this command again.")
            return False
        set_cooldown(ctx.guild.id,ctx.author.id,key,command,seconds)
        return True

    @commands.command(name="work")
    async def work(self,ctx):
        key=await self.require_active(ctx)
        if not key or not await self.cooldown_check(ctx,key,"work",3600): return
        amount=random.randint(10_000,20_000)
        change_balance(ctx.guild.id,ctx.author.id,key,wallet_delta=amount)
        await reply_v2(ctx,f"## Work completed!\nYou earned **{amount:,}** {ECONOMIES[key]['currency']}.\n\n{money_text(ctx.author,key)}")

    async def risk_game(self,ctx,command,minimum,maximum):
        key=await self.require_active(ctx)
        if not key or not await self.cooldown_check(ctx,key,command,3600): return
        wallet,_,infinity=get_balance(ctx.guild.id,ctx.author.id,key)
        if random.random()<0.5:
            amount=random.randint(minimum,maximum)
            change_balance(ctx.guild.id,ctx.author.id,key,wallet_delta=amount)
            result=f"**Success!** You earned **{amount:,}** {ECONOMIES[key]['currency']}."
        else:
            loss=0 if infinity else min(wallet,int(wallet*random.uniform(.05,.15)))
            change_balance(ctx.guild.id,ctx.author.id,key,wallet_delta=-loss)
            result=f"**Unlucky!** You lost **{loss:,}** {ECONOMIES[key]['currency']}."
        await reply_v2(ctx,f"## {command.title()}\n{result}\n\n{money_text(ctx.author,key)}")

    @commands.command(name="slut")
    async def slut(self,ctx):
        await self.risk_game(ctx,"slut",10_000,20_000)

    @commands.command(name="crime")
    async def crime(self,ctx):
        await self.risk_game(ctx,"crime",20_000,30_000)

    @commands.command(name="rob")
    async def rob(self,ctx,target:discord.Member=None):
        key=await self.require_active(ctx)
        if not key: return
        if target is None or target.bot or target.id==ctx.author.id:
            return await reply_v2(ctx,"Please mention another server member.")
        if not await self.cooldown_check(ctx,key,"rob",86400): return
        tw,_,tinf=get_balance(ctx.guild.id,target.id,key)
        if tw<=0 and not tinf:
            return await reply_v2(ctx,"That member has no wallet money to rob.")
        if random.random()<0.5:
            amount=tw if tinf else max(1,int(tw*random.uniform(.05,.15)))
            if not tinf:
                change_balance(ctx.guild.id,target.id,key,wallet_delta=-amount)
            change_balance(ctx.guild.id,ctx.author.id,key,wallet_delta=amount)
            result=f"**Success!** You took **{amount:,}** {ECONOMIES[key]['currency']} from {target.mention}."
        else:
            wallet,_,infinity=get_balance(ctx.guild.id,ctx.author.id,key)
            loss=0 if infinity else min(wallet,int(wallet*random.uniform(.05,.15)))
            change_balance(ctx.guild.id,ctx.author.id,key,wallet_delta=-loss)
            result=f"**Caught!** You lost **{loss:,}** {ECONOMIES[key]['currency']}."
        await reply_v2(ctx,f"## Robbery\n{result}\n\n{money_text(ctx.author,key)}")

    @commands.command(name="collect",aliases=["collect-income"])
    async def collect(self,ctx):
        key=await self.require_active(ctx)
        if not key or not await self.cooldown_check(ctx,key,"collect",86400): return
        level=owned_level(ctx.guild.id,ctx.author.id,key)
        if level<=0:
            return await reply_v2(ctx,"You need a seasonal role to collect passive income.")
        amount=LEVEL_INCOME[level-1]
        change_balance(ctx.guild.id,ctx.author.id,key,wallet_delta=amount)
        await reply_v2(ctx,f"## Income collected\nYour level **L{level if level<6 else '∞'}** role generated **{amount:,}** {ECONOMIES[key]['currency']}.\n\n{money_text(ctx.author,key)}")

    @commands.command(name="bal",aliases=["balance"])
    async def bal(self,ctx,member:discord.Member=None):
        key=await self.require_active(ctx)
        if not key: return
        member=member or ctx.author
        await reply_v2(ctx,f"## {member.display_name}'s Balance\n{money_text(member,key)}")

    async def move_money(self,ctx,amount_text,deposit):
        key=await self.require_active(ctx)
        if not key: return
        wallet,bank,infinity=get_balance(ctx.guild.id,ctx.author.id,key)
        if infinity:
            return await reply_v2(ctx,"Your Wallet and Bank are unlimited.")
        source=wallet if deposit else bank
        if amount_text.lower()=="all":
            amount=source
        else:
            try: amount=int(amount_text.replace(",",""))
            except ValueError: return await reply_v2(ctx,"Enter a valid amount or `all`.")
        if amount<=0 or amount>source:
            return await reply_v2(ctx,"You do not have enough money in that account.")
        if deposit:
            change_balance(ctx.guild.id,ctx.author.id,key,-amount,amount)
            action="deposited into your Bank"
        else:
            change_balance(ctx.guild.id,ctx.author.id,key,amount,-amount)
            action="withdrawn to your Wallet"
        await reply_v2(ctx,f"## Transaction complete\n**{amount:,}** {ECONOMIES[key]['currency']} {action}.\n\n{money_text(ctx.author,key)}")

    @commands.command(name="dep",aliases=["deposit"])
    async def deposit(self,ctx,amount:str):
        await self.move_money(ctx,amount,True)

    @commands.command(name="with",aliases=["withdraw"])
    async def withdraw(self,ctx,amount:str):
        await self.move_money(ctx,amount,False)

    @commands.command(name="shop")
    async def shop(self,ctx):
        key=await self.require_active(ctx)
        if not key: return
        roles=ROLE_DATA[key]
        lines=[f"## {ECONOMIES[key]['name']} — Role Shop"]
        for i,(name,rid,color) in enumerate(roles):
            lines.append(f"**L{i+1 if i<5 else '∞'}** — {name} — **{LEVEL_PRICES[i]:,}** {ECONOMIES[key]['currency']}")
        lines.append("\nUse `,buy <level>` to purchase the next role level.")
        await reply_v2(ctx,"\n".join(lines))

    async def purchase_role(self,ctx,level,target=None,gift=False):
        key=await self.require_active(ctx)
        if not key: return
        if not 1<=level<=6: return await reply_v2(ctx,"Level must be between 1 and 6.")
        buyer=ctx.author
        recipient=target or buyer
        current=owned_level(ctx.guild.id,recipient.id,key)
        if gift:
            if current>=level: return await reply_v2(ctx,"That member already owns this level or a higher one.")
        else:
            if current+1!=level:
                return await reply_v2(ctx,"Role levels must be purchased in order. You can only buy the next level.")
        wallet,bank,infinity=get_balance(ctx.guild.id,buyer.id,key)
        price=LEVEL_PRICES[level-1]
        if not infinity and wallet<price:
            return await reply_v2(ctx,f"You need **{price:,}** in your Wallet.")
        role_name,role_id,color=ROLE_DATA[key][level-1]
        role=ctx.guild.get_role(role_id)
        if role is None: return await reply_v2(ctx,"The configured seasonal role was not found.")
        if not gift and current:
            old=ctx.guild.get_role(ROLE_DATA[key][current-1][1])
            if old and old in buyer.roles: await buyer.remove_roles(old,reason="Seasonal role upgrade")
        try:
            await recipient.add_roles(role,reason="LEGENDS ECONOMY role purchase")
        except discord.Forbidden:
            return await reply_v2(ctx,"I cannot assign this role. Check my Manage Roles permission and role position.")
        if not infinity: change_balance(ctx.guild.id,buyer.id,key,wallet_delta=-price)
        set_owned_level(ctx.guild.id,recipient.id,key,level)
        await self.check_legend_role(ctx.guild,recipient)
        await reply_v2(ctx,f"## Purchase successful\n{recipient.mention} received **{role_name}**.\nPaid: **{price:,}** {ECONOMIES[key]['currency']}.")

    async def check_legend_role(self,guild,member):
        count=0
        for key in ECONOMIES:
            if owned_level(guild.id,member.id,key)==6:
                count+=1
        special=guild.get_role(LEGEND_ECONOMY_ROLE_ID)
        if special:
            if count==len(ECONOMIES) and special not in member.roles:
                await member.add_roles(special,reason="Collected all 11 Level Infinity seasonal roles")
            elif count<len(ECONOMIES) and special in member.roles:
                await member.remove_roles(special,reason="Seasonal collection no longer complete")

    @commands.command(name="buy")
    async def buy(self,ctx,level:int):
        await self.purchase_role(ctx,level)

    @commands.command(name="gift")
    async def gift(self,ctx,target:discord.Member,level:int):
        if target.bot or target.id==ctx.author.id:
            return await reply_v2(ctx,"Choose another server member.")
        await self.purchase_role(ctx,level,target,gift=True)

    @commands.command(name="transfer")
    async def transfer(self,ctx,target:discord.Member,level:int):
        key=await self.require_active(ctx)
        if not key: return
        if target.bot or target.id==ctx.author.id or not 1<=level<=6:
            return await reply_v2(ctx,"Invalid recipient or role level.")
        if owned_level(ctx.guild.id,ctx.author.id,key)!=level:
            return await reply_v2(ctx,"You must own exactly that role level to transfer it.")
        recipient_level=owned_level(ctx.guild.id,target.id,key)
        if recipient_level>=level:
            return await reply_v2(ctx,"The recipient already owns the same or a higher level.")
        role=ctx.guild.get_role(ROLE_DATA[key][level-1][1])
        if not role or role not in ctx.author.roles:
            return await reply_v2(ctx,"You do not currently have that Discord role.")
        view=TransferConfirmView(self,ctx.author,target,key,level)
        await ctx.send(view=view)

    @commands.command(name="transfer-confirm")
    async def transfer_confirm_placeholder(self,ctx):
        await reply_v2(ctx,"Use the confirmation button on the transfer message.")

    @tasks.loop(minutes=1)
    async def reminder_loop(self):
        now=datetime.now(BAKU)
        if now.hour not in (17,) or now.minute not in (0,50):
            return
        guild=next(iter(self.bot.guilds),None)
        if guild is None: return
        owner=self.bot.get_user(OWNER_ID)
        if owner is None:
            try: owner=await self.bot.fetch_user(OWNER_ID)
            except discord.HTTPException: return
        for key in ECONOMIES:
            years={now.year,now.year-1}
            for year in years:
                start,end=event_dates(key,year)
                for kind,day in (("start",start),("end",end)):
                    if day != now.date(): continue
                    stamp=f"{key}:{kind}:{day.isoformat()}:{now.minute}"
                    with db() as con:
                        exists=con.execute("SELECT 1 FROM reminders WHERE reminder_key=?",(stamp,)).fetchone()
                        if exists: continue
                        con.execute("INSERT INTO reminders VALUES(?)",(stamp,))
                    try:
                        await owner.send(
                            f"⏰ **LEGENDS ECONOMY reminder**\n"
                            f"{ECONOMIES[key]['name']} {kind} is scheduled for **18:00 Baku time** today. "
                            f"This is the { '1-hour' if now.minute==0 else '10-minute' } reminder. "
                            f"Remember: the bot will not switch the economy automatically."
                        )
                    except discord.Forbidden:
                        log.warning("Could not DM owner about %s",stamp)

    @reminder_loop.before_loop
    async def before_reminders(self):
        await self.bot.wait_until_ready()

class TransferConfirmView(discord.ui.View):
    def __init__(self,cog,giver,recipient,economy,level):
        super().__init__(timeout=120)
        self.cog=cog; self.giver=giver; self.recipient=recipient
        self.economy=economy; self.level=level

    @discord.ui.button(label="Confirm transfer",style=discord.ButtonStyle.success)
    async def confirm(self,interaction,button):
        if interaction.user.id!=self.giver.id:
            return await interaction.response.send_message("Only the sender can confirm this transfer.",ephemeral=True)
        guild=interaction.guild
        if owned_level(guild.id,self.giver.id,self.economy)!=self.level:
            return await interaction.response.send_message("Your role ownership has changed.",ephemeral=True)
        if owned_level(guild.id,self.recipient.id,self.economy)>=self.level:
            return await interaction.response.send_message("Recipient already has this level or higher.",ephemeral=True)
        role=guild.get_role(ROLE_DATA[self.economy][self.level-1][1])
        if not role or role not in self.giver.roles:
            return await interaction.response.send_message("The sender no longer has that role.",ephemeral=True)
        try:
            await self.giver.remove_roles(role,reason="Confirmed seasonal role transfer")
            await self.recipient.add_roles(role,reason="Confirmed seasonal role transfer")
        except discord.Forbidden:
            return await interaction.response.send_message("I cannot manage this role. Check role permissions.",ephemeral=True)
        with db() as con:
            con.execute("DELETE FROM ownership WHERE guild_id=? AND user_id=? AND economy=?",
                        (guild.id,self.giver.id,self.economy))
        set_owned_level(guild.id,self.recipient.id,self.economy,self.level)
        await self.cog.check_legend_role(guild,self.giver)
        await self.cog.check_legend_role(guild,self.recipient)
        for item in self.children: item.disabled=True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f"Transferred **{role.name}** to {self.recipient.mention}.",ephemeral=True)

    @discord.ui.button(label="Cancel",style=discord.ButtonStyle.danger)
    async def cancel(self,interaction,button):
        if interaction.user.id!=self.giver.id:
            return await interaction.response.send_message("Only the sender can cancel this transfer.",ephemeral=True)
        for item in self.children: item.disabled=True
        await interaction.response.edit_message(view=self)

async def setup(bot):
    # Keep the existing ! prefix and add comma commands without editing main.py.
    bot.command_prefix = commands.when_mentioned_or("!", ",")
    cog=Economy(bot)
    await bot.add_cog(cog)
    # Restore persistent router custom_id after every restart.
    bot.add_view(EconomyRouter(cog))
