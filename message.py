import discord
from discord.ext import commands

# =========================================================
# OWNER
# =========================================================
OWNER_ID = 1176149190192152626

# =========================================================
# ROLE IDS
# =========================================================
RUSSIAN_ROLE_ID = 1540457657771757578
ENGLISH_ROLE_ID = 1540457933639262258

BLACK_ROLE_ID = 1531987548652441702
BLUE_ROLE_ID = 1541333122287935528
PURPLE_ROLE_ID = 1541332958063890452
PINK_ROLE_ID = 1541333562375274496
GREEN_ROLE_ID = 1541334227893624862

MOBILE_ROLE_ID = 1545281085678686281
TABLET_ROLE_ID = 1545281561329533030
PC_ROLE_ID = 1545280805905895504
XBOX_ROLE_ID = 1545281911151398942
PLAYSTATION_ROLE_ID = 1545281770818248805
SWITCH_ROLE_ID = 1545283995665834086

YOUTUBE_ROLE_ID = 1541715251018465351
TOURNAMENT_ROLE_ID = 1541715118872731768
GIVEAWAY_ROLE_ID = 1541716902752157798
NEWS_ROLE_ID = 1541715546356060200

LANGUAGE_ROLES = {RUSSIAN_ROLE_ID, ENGLISH_ROLE_ID}
COLOR_ROLES = {BLACK_ROLE_ID, BLUE_ROLE_ID, PURPLE_ROLE_ID, PINK_ROLE_ID, GREEN_ROLE_ID}
PLATFORM_ROLES = {MOBILE_ROLE_ID, TABLET_ROLE_ID, PC_ROLE_ID, XBOX_ROLE_ID, PLAYSTATION_ROLE_ID, SWITCH_ROLE_ID}
PING_ROLES = {YOUTUBE_ROLE_ID, TOURNAMENT_ROLE_ID, GIVEAWAY_ROLE_ID, NEWS_ROLE_ID}


async def replace_role(member, role_id, role_group):
    if not isinstance(member, discord.Member):
        return False
    guild = member.guild
    selected_role = guild.get_role(role_id)
    if selected_role is None:
        return False
    roles_to_remove = [r for r in member.roles if r.id in role_group and r.id != role_id]
    if roles_to_remove:
        await member.remove_roles(*roles_to_remove)
    if selected_role not in member.roles:
        await member.add_roles(selected_role)
    return True


class RoleSelect(discord.ui.Select):
    def __init__(self, placeholder, custom_id, options, role_group, role_name):
        super().__init__(placeholder=placeholder, min_values=1, max_values=1,
                         options=options, custom_id=custom_id)
        self.role_group = role_group
        self.role_name = role_name

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("❌ Use this menu in the server.", ephemeral=True)
            return
        try:
            role_id = int(self.values[0])
            if not await replace_role(interaction.user, role_id, self.role_group):
                await interaction.response.send_message("❌ The selected role could not be found.", ephemeral=True)
                return
            role = interaction.guild.get_role(role_id)
            await interaction.response.send_message(
                f"✅ Your {self.role_name} has been set to **{role.name}**.", ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to manage this role.", ephemeral=True)
        except discord.HTTPException:
            await interaction.response.send_message("❌ Something went wrong. Please try again.", ephemeral=True)


def language_select():
    return RoleSelect("🌐 Choose your language", "features_language_v2", [
        discord.SelectOption(label="Russian", emoji="🇷🇺", value=str(RUSSIAN_ROLE_ID)),
        discord.SelectOption(label="English", emoji="🇬🇧", value=str(ENGLISH_ROLE_ID)),
    ], LANGUAGE_ROLES, "language")


def color_select():
    return RoleSelect("🎨 Choose your nickname color", "features_color_v2", [
        discord.SelectOption(label="Black", emoji="⚫", value=str(BLACK_ROLE_ID)),
        discord.SelectOption(label="Blue", emoji="🔵", value=str(BLUE_ROLE_ID)),
        discord.SelectOption(label="Purple", emoji="🟣", value=str(PURPLE_ROLE_ID)),
        discord.SelectOption(label="Pink", emoji="🩷", value=str(PINK_ROLE_ID)),
        discord.SelectOption(label="Bright Green", emoji="🟢", value=str(GREEN_ROLE_ID)),
    ], COLOR_ROLES, "nickname color")


def platform_select():
    return RoleSelect("🎮 Choose your platform", "features_platform_v2", [
        discord.SelectOption(label="Mobile", emoji="📱", value=str(MOBILE_ROLE_ID)),
        discord.SelectOption(label="Tablet", emoji="📲", value=str(TABLET_ROLE_ID)),
        discord.SelectOption(label="PC", emoji="💻", value=str(PC_ROLE_ID)),
        discord.SelectOption(label="Xbox", emoji="🎮", value=str(XBOX_ROLE_ID)),
        discord.SelectOption(label="PlayStation", emoji="🎮", value=str(PLAYSTATION_ROLE_ID)),
        discord.SelectOption(label="Nintendo Switch", emoji="🕹️", value=str(SWITCH_ROLE_ID)),
    ], PLATFORM_ROLES, "platform")


class FeaturesView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Container(
            discord.ui.TextDisplay("# ✨ Features\nChoose your preferences using the menus below."),
            discord.ui.Separator(),
            discord.ui.TextDisplay("### 🎨 Nickname Color\nChoose a color for your nickname."),
            discord.ui.ActionRow(color_select()),
            discord.ui.Separator(),
            discord.ui.TextDisplay("### 🌐 Language\nChoose your preferred language."),
            discord.ui.ActionRow(language_select()),
            discord.ui.Separator(),
            discord.ui.TextDisplay("### 🎮 Platform\nChoose the platform you play on."),
            discord.ui.ActionRow(platform_select()),
            discord.ui.Separator(),
            discord.ui.TextDisplay("-# Select an option from the menus above."),
            accent_colour=discord.Colour.from_rgb(88, 101, 242),
        ))


class PingButton(discord.ui.Button):
    def __init__(self, label, emoji, role_id, custom_id):
        super().__init__(label=label, emoji=emoji, style=discord.ButtonStyle.secondary, custom_id=custom_id)
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("❌ Use this button in the server.", ephemeral=True)
            return
        role = interaction.guild.get_role(self.role_id)
        if role is None:
            await interaction.response.send_message("❌ The selected role could not be found.", ephemeral=True)
            return
        try:
            if role in interaction.user.roles:
                await interaction.user.remove_roles(role)
                message = f"🔕 **{role.name}** notifications disabled."
            else:
                await interaction.user.add_roles(role)
                message = f"🔔 **{role.name}** notifications enabled."
            await interaction.response.send_message(message, ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to manage this role.", ephemeral=True)
        except discord.HTTPException:
            await interaction.response.send_message("❌ Something went wrong. Please try again.", ephemeral=True)


class RemovePingRolesButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Remove all ping roles", emoji="❌",
                         style=discord.ButtonStyle.secondary, custom_id="features_remove_ping_roles_v2")

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("❌ Use this button in the server.", ephemeral=True)
            return
        roles = [r for r in interaction.user.roles if r.id in PING_ROLES]
        try:
            if roles:
                await interaction.user.remove_roles(*roles)
            await interaction.response.send_message("✅ All notification roles have been removed.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to manage these roles.", ephemeral=True)
        except discord.HTTPException:
            await interaction.response.send_message("❌ Something went wrong. Please try again.", ephemeral=True)


class PingView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Container(
            discord.ui.TextDisplay("# 🔔 Choose\nChoose which notifications you want to receive."),
            discord.ui.Separator(),
            discord.ui.TextDisplay("### ▶️ YouTube\nGet notified about new YouTube content."),
            discord.ui.ActionRow(PingButton("YouTube", "▶️", YOUTUBE_ROLE_ID, "ping_youtube_v2")),
            discord.ui.Separator(),
            discord.ui.TextDisplay("### 🏆 Tournament\nGet notified about tournaments and events."),
            discord.ui.ActionRow(PingButton("Tournament", "🏆", TOURNAMENT_ROLE_ID, "ping_tournament_v2")),
            discord.ui.Separator(),
            discord.ui.TextDisplay("### 🎁 Giveaway\nGet notified about giveaways."),
            discord.ui.ActionRow(PingButton("Giveaway", "🎁", GIVEAWAY_ROLE_ID, "ping_giveaway_v2")),
            discord.ui.Separator(),
            discord.ui.TextDisplay("### 📰 News\nGet notified about important server news."),
            discord.ui.ActionRow(PingButton("News", "📰", NEWS_ROLE_ID, "ping_news_v2")),
            discord.ui.Separator(),
            discord.ui.ActionRow(RemovePingRolesButton()),
            discord.ui.Separator(),
            discord.ui.TextDisplay("-# Click a button to enable or disable a notification role."),
            accent_colour=discord.Colour.from_rgb(88, 101, 242),
        ))


# =========================================================
# ECONOMY COMMANDS — 12 LANGUAGES
# =========================================================
# Command names are kept the same in all languages; explanations are translated.
ECONOMY_COMMANDS = {
    "en": """# 💰 Economy Commands

## 🎮 Games
`. sm <amount/all>` — Play the slot machine.
`. bj <amount/all/half>` — Play blackjack.
`. cf <amount/all>` — Play cock-fight.
`. roulette <amount/all> <black/red> <number 2-36>` — Play roulette.
`. russian-roulette <amount/all>` — Russian roulette.
`. russian-roulette start` — Start a Russian roulette game.
`. buy c` — Buy a chicken for Cock-fight.

## 💵 Earnings
`. work` — Work to earn money.
`. crime` — Try to earn money through crime.
`. slut` — Earn money using this command.
`. collect` — Collect available earnings.

## 💳 Money
`. bal` — Check your balance.
`. dep` — Deposit money.
`. with` — Withdraw money.
`. give` — Give money to another user.
`. rob` — Try to rob another user.

## 🛒 Shop
`. store` — Open the shop.
`. inv` — Check your inventory.
`. help` — Show the economy bot's help.

## 📦 Item Information
`. item-info <item name>` — View information about an item.
Example: `. item-info Клан`""",
    "ru": """# 💰 Команды экономики

## 🎮 Игры
`. sm <сумма/all>` — Игровой автомат.
`. bj <сумма/all/half>` — Блэкджек.
`. cf <сумма/all>` — Петушиные бои.
`. roulette <сумма/all> <black/red> <число 2-36>` — Рулетка.
`. russian-roulette <сумма/all>` — Русская рулетка.
`. russian-roulette start` — Начать русскую рулетку.
`. buy c` — Купить курицу для петушиных боёв.

## 💵 Заработок
`. work` — Заработать работой.
`. crime` — Попробовать заработать преступлением.
`. slut` — Команда заработка.
`. collect` — Забрать доступный заработок.

## 💳 Деньги
`. bal` — Проверить баланс.
`. dep` — Положить деньги на счёт.
`. with` — Снять деньги.
`. give` — Передать деньги другому пользователю.
`. rob` — Попробовать ограбить другого пользователя.

## 🛒 Магазин
`. store` — Открыть магазин.
`. inv` — Посмотреть инвентарь.
`. help` — Справка экономического бота.

## 📦 Информация о предметах
`. item-info <название предмета>` — Информация о предмете.
Пример: `. item-info Клан`""",
    "ro": "# 💰 Comenzi Economie\n\n`. sm <sumă/all>` — Joacă la sloturi.\n`. bj <sumă/all/half>` — Blackjack.\n`. cf <sumă/all>` — Lupte de cocoși.\n`. roulette <sumă/all> <black/red> <număr 2-36>` — Ruletă.\n`. russian-roulette <sumă/all>` — Ruletă rusească.\n`. russian-roulette start` — Începe ruleta rusească.\n`. buy c` — Cumpără o găină.\n`. work` — Câștigă bani muncind.\n`. crime` — Încearcă să câștigi bani prin infracțiuni.\n`. collect` — Colectează câștigurile.\n`. bal` — Verifică soldul.\n`. dep` — Depune bani.\n`. with` — Retrage bani.\n`. give` — Trimite bani.\n`. rob` — Încearcă să jefuiești.\n`. store` — Deschide magazinul.\n`. inv` — Vezi inventarul.\n`. help` — Ajutor.\n`. item-info <obiect>` — Informații despre obiect.",
    "uz": "# 💰 Iqtisod buyruqlari\n\n`. sm <miqdor/all>` — Slot o'yini.\n`. bj <miqdor/all/half>` — Blackjack.\n`. cf <miqdor/all>` — Xo'roz jangi.\n`. roulette <miqdor/all> <black/red> <2-36>` — Ruletka.\n`. russian-roulette <miqdor/all>` — Rus ruletkasi.\n`. russian-roulette start` — Rus ruletkasini boshlash.\n`. buy c` — Tovuq sotib olish.\n`. work` — Ishlab pul topish.\n`. crime` — Jinoyat orqali pul topishga urinish.\n`. collect` — Daromadni yig'ish.\n`. bal` — Balansni tekshirish.\n`. dep` — Pul qo'yish.\n`. with` — Pul yechish.\n`. give` — Pul berish.\n`. rob` — O'g'irlashga urinish.\n`. store` — Do'kon.\n`. inv` — Inventar.\n`. help` — Yordam.\n`. item-info <buyum>` — Buyum haqida ma'lumot.",
    "kk": "# 💰 Экономика командалары\n\n`. sm <сома/all>` — Слот ойыны.\n`. bj <сома/all/half>` — Блэкджек.\n`. cf <сома/all>` — Әтеш төбелесі.\n`. roulette <сома/all> <black/red> <2-36>` — Рулетка.\n`. russian-roulette <сома/all>` — Орыс рулеткасы.\n`. russian-roulette start` — Орыс рулеткасын бастау.\n`. buy c` — Тауық сатып алу.\n`. work` — Жұмыс істеп ақша табу.\n`. crime` — Қылмыс арқылы ақша табуға тырысу.\n`. collect` — Табысты жинау.\n`. bal` — Балансты тексеру.\n`. dep` — Ақша салу.\n`. with` — Ақша шешу.\n`. give` — Ақша беру.\n`. rob` — Тонауға тырысу.\n`. store` — Дүкен.\n`. inv` — Заттар тізімі.\n`. help` — Көмек.\n`. item-info <зат>` — Зат туралы ақпарат.",
    "tr": "# 💰 Ekonomi Komutları\n\n`. sm <miktar/all>` — Slot makinesi.\n`. bj <miktar/all/half>` — Blackjack.\n`. cf <miktar/all>` — Horoz dövüşü.\n`. roulette <miktar/all> <black/red> <2-36>` — Rulet.\n`. russian-roulette <miktar/all>` — Rus ruleti.\n`. russian-roulette start` — Rus ruletini başlat.\n`. buy c` — Tavuk satın al.\n`. work` — Çalışarak para kazan.\n`. crime` — Suçla para kazanmaya çalış.\n`. collect` — Kazancı topla.\n`. bal` — Bakiyeyi kontrol et.\n`. dep` — Para yatır.\n`. with` — Para çek.\n`. give` — Para gönder.\n`. rob` — Soymaya çalış.\n`. store` — Mağaza.\n`. inv` — Envanter.\n`. help` — Yardım.\n`. item-info <eşya>` — Eşya bilgisi.",
    "es": "# 💰 Comandos de Economía\n\n`. sm <cantidad/all>` — Tragaperras.\n`. bj <cantidad/all/half>` — Blackjack.\n`. cf <cantidad/all>` — Peleas de gallos.\n`. roulette <cantidad/all> <black/red> <número 2-36>` — Ruleta.\n`. russian-roulette <cantidad/all>` — Ruleta rusa.\n`. russian-roulette start` — Iniciar ruleta rusa.\n`. buy c` — Comprar una gallina.\n`. work` — Trabajar para ganar dinero.\n`. crime` — Intentar ganar dinero mediante delitos.\n`. collect` — Recoger ganancias.\n`. bal` — Consultar saldo.\n`. dep` — Depositar.\n`. with` — Retirar.\n`. give` — Dar dinero.\n`. rob` — Intentar robar.\n`. store` — Tienda.\n`. inv` — Inventario.\n`. help` — Ayuda.\n`. item-info <objeto>` — Información del objeto.",
    "fr": "# 💰 Commandes Économie\n\n`. sm <montant/all>` — Machine à sous.\n`. bj <montant/all/half>` — Blackjack.\n`. cf <montant/all>` — Combats de coqs.\n`. roulette <montant/all> <black/red> <nombre 2-36>` — Roulette.\n`. russian-roulette <montant/all>` — Roulette russe.\n`. russian-roulette start` — Démarrer la roulette russe.\n`. buy c` — Acheter une poule.\n`. work` — Gagner de l'argent en travaillant.\n`. crime` — Essayer de gagner de l'argent par le crime.\n`. collect` — Récupérer les gains.\n`. bal` — Vérifier le solde.\n`. dep` — Déposer.\n`. with` — Retirer.\n`. give` — Donner de l'argent.\n`. rob` — Essayer de voler.\n`. store` — Boutique.\n`. inv` — Inventaire.\n`. help` — Aide.\n`. item-info <objet>` — Informations sur un objet.",
    "de": "# 💰 Wirtschaftsbefehle\n\n`. sm <betrag/all>` — Spielautomaten.\n`. bj <betrag/all/half>` — Blackjack.\n`. cf <betrag/all>` — Hahnenkämpfe.\n`. roulette <betrag/all> <black/red> <Zahl 2-36>` — Roulette.\n`. russian-roulette <betrag/all>` — Russisches Roulette.\n`. russian-roulette start` — Russisches Roulette starten.\n`. buy c` — Huhn kaufen.\n`. work` — Geld durch Arbeit verdienen.\n`. crime` — Durch Verbrechen Geld verdienen.\n`. collect` — Einnahmen abholen.\n`. bal` — Kontostand prüfen.\n`. dep` — Einzahlen.\n`. with` — Abheben.\n`. give` — Geld geben.\n`. rob` — Ausrauben versuchen.\n`. store` — Shop.\n`. inv` — Inventar.\n`. help` — Hilfe.\n`. item-info <Gegenstand>` — Gegenstandsinformationen.",
    "it": "# 💰 Comandi Economia\n\n`. sm <importo/all>` — Slot machine.\n`. bj <importo/all/half>` — Blackjack.\n`. cf <importo/all>` — Combattimenti tra galli.\n`. roulette <importo/all> <black/red> <numero 2-36>` — Roulette.\n`. russian-roulette <importo/all>` — Roulette russa.\n`. russian-roulette start` — Avvia la roulette russa.\n`. buy c` — Compra una gallina.\n`. work` — Guadagna lavorando.\n`. crime` — Prova a guadagnare con il crimine.\n`. collect` — Raccogli i guadagni.\n`. bal` — Controlla il saldo.\n`. dep` — Deposita.\n`. with` — Preleva.\n`. give` — Dai denaro.\n`. rob` — Prova a derubare.\n`. store` — Negozio.\n`. inv` — Inventario.\n`. help` — Aiuto.\n`. item-info <oggetto>` — Informazioni sull'oggetto.",
    "uk": "# 💰 Команди економіки\n\n`. sm <сума/all>` — Ігровий автомат.\n`. bj <сума/all/half>` — Блекджек.\n`. cf <сума/all>` — Півнячі бої.\n`. roulette <сума/all> <black/red> <число 2-36>` — Рулетка.\n`. russian-roulette <сума/all>` — Російська рулетка.\n`. russian-roulette start` — Почати російську рулетку.\n`. buy c` — Купити курку.\n`. work` — Заробити гроші роботою.\n`. crime` — Спробувати заробити злочином.\n`. collect` — Забрати заробіток.\n`. bal` — Перевірити баланс.\n`. dep` — Покласти гроші.\n`. with` — Зняти гроші.\n`. give` — Передати гроші.\n`. rob` — Спробувати пограбувати.\n`. store` — Магазин.\n`. inv` — Інвентар.\n`. help` — Допомога.\n`. item-info <предмет>` — Інформація про предмет.",
    "pl": "# 💰 Komendy Ekonomii\n\n`. sm <kwota/all>` — Automat.\n`. bj <kwota/all/half>` — Blackjack.\n`. cf <kwota/all>` — Walki kogutów.\n`. roulette <kwota/all> <black/red> <liczba 2-36>` — Ruletka.\n`. russian-roulette <kwota/all>` — Rosyjska ruletka.\n`. russian-roulette start` — Rozpocznij rosyjską ruletkę.\n`. buy c` — Kup kurę.\n`. work` — Zarabiaj pracą.\n`. crime` — Spróbuj zarobić na przestępstwie.\n`. collect` — Odbierz zarobki.\n`. bal` — Sprawdź saldo.\n`. dep` — Wpłać.\n`. with` — Wypłać.\n`. give` — Przekaż pieniądze.\n`. rob` — Spróbuj okraść.\n`. store` — Sklep.\n`. inv` — Ekwipunek.\n`. help` — Pomoc.\n`. item-info <przedmiot>` — Informacje o przedmiocie."
}


class EconomyLanguageSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="English", emoji="🇬🇧", value="en"),
            discord.SelectOption(label="Russian", emoji="🇷🇺", value="ru"),
            discord.SelectOption(label="Romanian", emoji="🇷🇴", value="ro"),
            discord.SelectOption(label="Uzbek", emoji="🇺🇿", value="uz"),
            discord.SelectOption(label="Kazakh", emoji="🇰🇿", value="kk"),
            discord.SelectOption(label="Turkish", emoji="🇹🇷", value="tr"),
            discord.SelectOption(label="Spanish", emoji="🇪🇸", value="es"),
            discord.SelectOption(label="French", emoji="🇫🇷", value="fr"),
            discord.SelectOption(label="German", emoji="🇩🇪", value="de"),
            discord.SelectOption(label="Italian", emoji="🇮🇹", value="it"),
            discord.SelectOption(label="Ukrainian", emoji="🇺🇦", value="uk"),
            discord.SelectOption(label="Polish", emoji="🇵🇱", value="pl"),
        ]
        super().__init__(placeholder="🌐 Choose your language", min_values=1, max_values=1,
                         options=options, custom_id="economy_commands_language_v2")

    async def callback(self, interaction: discord.Interaction):
        content = ECONOMY_COMMANDS.get(self.values[0], ECONOMY_COMMANDS["en"])
        chunks = [content[i:i + 1900] for i in range(0, len(content), 1900)]
        await interaction.response.send_message(chunks[0], ephemeral=True)
        for chunk in chunks[1:]:
            await interaction.followup.send(chunk, ephemeral=True)


class EconomyLanguageView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(EconomyLanguageSelect())


class Message(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="features")
    async def features(self, ctx, action=None):
        if ctx.author.id != OWNER_ID:
            return
        if not action or action.lower() != "panel":
            return
        await ctx.send(view=FeaturesView())

    @commands.command(name="ping")
    async def ping(self, ctx, action=None):
        if ctx.author.id != OWNER_ID:
            return
        if not action or action.lower() != "panel":
            return
        await ctx.send(view=PingView())

    @commands.command(name="commands")
    async def commands_message(self, ctx, system=None):
        if not system:
            await ctx.send("Use `!commands economy`, `!commands message`, or `!commands suggest`.", delete_after=10)
            return

        system = system.lower()

        if system == "economy":
            embed = discord.Embed(
                title="💰 Economy Commands",
                description="Choose your language using the menu below.\nThe command list will be shown privately to you.",
                colour=discord.Colour.from_rgb(88, 101, 242),
            )
            await ctx.send(embed=embed, view=EconomyLanguageView())
            return

        if system == "message":
            description = """📚 **ALL BOT COMMANDS**

**🎁 CHESTS 🎁**
`!chests`
`!chest info`
`!remove <type_chest> <amount> <user>`
`!admin chests`

**💰 DROPS 💰**
`!money economy <amount> <quantity> [user] [role]`
`!drop <chest_type> <amount> <quantity> [role] [user]`

**🎫 TICKETS 🎫**
`!ticket panel`
`!ticket block @user staff`
`!ticket block @user moder`
`!ticket blocks`
`!answer ticket <number> <message>`
`!close ticket <number>`

**📋 FEATURES 📋**
`!features panel`

**🔔 PING 🔔**
`!ping panel`

**📘 ECONOMY 📘**
`!commands economy`

**💡 IDEA 💡**
`?suggest`
`?suggest help`
`?suggest mine`
`!commands suggest`

**🏆 TOURNAMENT 🏆**
`/create tour channel:#channel`
`!bracket r1`
`!bracket r2`
`!match 1 267899`
`!qual 1 @winner`
`!delete tour`
`!training tour @user`
`!team @user`
`!team @user1 @user2`
`!edit qualified`

**ℹ️ VERIFICATION ℹ️**
`!verification panel`

**🧹 CLEAR 🧹**
`/clear message <number>`

**📩 SEND 📩**
`/send message`
`/send dms`

**✂️ RPS ✂️**
`/rps`
`/classic rps`

**📊 STATS 📊**
`!my stats bot`"""
            embed = discord.Embed(
                title="📚 Message System Commands",
                description=description,
                colour=discord.Colour.from_rgb(88, 101, 242),
            )
            await ctx.send(embed=embed)
            return

        if system == "suggest":
            await ctx.send("Use `?suggest help` to view suggestion commands.", delete_after=10)
            return

        await ctx.send(
            "Unknown system. Use `!commands economy`, `!commands message`, or `!commands suggest`.",
            delete_after=10,
        )


async def setup(bot):
    await bot.add_cog(Message(bot))
    bot.add_view(FeaturesView())
    bot.add_view(PingView())
    bot.add_view(EconomyLanguageView())
    print("✅ FeaturesView, PingView and EconomyLanguageView registered!")
