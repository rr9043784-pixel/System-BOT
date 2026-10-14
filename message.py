import discord
from discord.ext import commands

# =========================================================
# OWNER
# =========================================================

OWNER_ID = 1176149190192152626

# =========================================================
# FEATURE ROLE IDS
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

# =========================================================
# PING ROLE IDS
# =========================================================

YOUTUBE_ROLE_ID = 1541715251018465351
TOURNAMENT_ROLE_ID = 1541715118872731768
GIVEAWAY_ROLE_ID = 1541716902752157798
NEWS_ROLE_ID = 1541715546356060200

LANGUAGE_ROLES = {RUSSIAN_ROLE_ID, ENGLISH_ROLE_ID}
COLOR_ROLES = {
    BLACK_ROLE_ID, BLUE_ROLE_ID, PURPLE_ROLE_ID,
    PINK_ROLE_ID, GREEN_ROLE_ID
}
PLATFORM_ROLES = {
    MOBILE_ROLE_ID, TABLET_ROLE_ID, PC_ROLE_ID,
    XBOX_ROLE_ID, PLAYSTATION_ROLE_ID, SWITCH_ROLE_ID
}
PING_ROLES = {
    YOUTUBE_ROLE_ID, TOURNAMENT_ROLE_ID,
    GIVEAWAY_ROLE_ID, NEWS_ROLE_ID
}


# =========================================================
# ROLE FUNCTION
# =========================================================

async def replace_role(member, role_id, role_group):
    if not isinstance(member, discord.Member):
        return False

    guild = member.guild
    selected_role = guild.get_role(role_id)

    if selected_role is None:
        return False

    remove_roles = [
        role for role in member.roles
        if role.id in role_group and role.id != role_id
    ]

    if remove_roles:
        await member.remove_roles(*remove_roles)

    if selected_role not in member.roles:
        await member.add_roles(selected_role)

    return True


# =========================================================
# FEATURE SELECT MENUS
# =========================================================

class RoleSelect(discord.ui.Select):
    def __init__(self, placeholder, custom_id, options, role_group, message_type):
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options,
            custom_id=custom_id
        )
        self.role_group = role_group
        self.message_type = message_type

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "❌ Use this menu in the server.",
                ephemeral=True
            )
            return

        role_id = int(self.values[0])

        try:
            success = await replace_role(
                interaction.user, role_id, self.role_group
            )

            if not success:
                await interaction.response.send_message(
                    "❌ The selected role could not be found.",
                    ephemeral=True
                )
                return

            role = interaction.guild.get_role(role_id)

            await interaction.response.send_message(
                f"✅ Your {self.message_type} has been set to **{role.name}**.",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to manage this role.",
                ephemeral=True
            )
        except discord.HTTPException:
            await interaction.response.send_message(
                "❌ Something went wrong. Please try again.",
                ephemeral=True
            )


def language_select():
    return RoleSelect(
        "🌐 Choose your language",
        "features_language_v2",
        [
            discord.SelectOption(label="Russian", emoji="🇷🇺", value=str(RUSSIAN_ROLE_ID)),
            discord.SelectOption(label="English", emoji="🇬🇧", value=str(ENGLISH_ROLE_ID)),
        ],
        LANGUAGE_ROLES,
        "language"
    )


def color_select():
    return RoleSelect(
        "🎨 Choose your nickname color",
        "features_color_v2",
        [
            discord.SelectOption(label="Black", emoji="⚫", value=str(BLACK_ROLE_ID)),
            discord.SelectOption(label="Blue", emoji="🔵", value=str(BLUE_ROLE_ID)),
            discord.SelectOption(label="Purple", emoji="🟣", value=str(PURPLE_ROLE_ID)),
            discord.SelectOption(label="Pink", emoji="🩷", value=str(PINK_ROLE_ID)),
            discord.SelectOption(label="Bright Green", emoji="🟢", value=str(GREEN_ROLE_ID)),
        ],
        COLOR_ROLES,
        "nickname color"
    )


def platform_select():
    return RoleSelect(
        "🎮 Choose your platform",
        "features_platform_v2",
        [
            discord.SelectOption(label="Mobile", emoji="📱", value=str(MOBILE_ROLE_ID)),
            discord.SelectOption(label="Tablet", emoji="📲", value=str(TABLET_ROLE_ID)),
            discord.SelectOption(label="PC", emoji="💻", value=str(PC_ROLE_ID)),
            discord.SelectOption(label="Xbox", emoji="🎮", value=str(XBOX_ROLE_ID)),
            discord.SelectOption(label="PlayStation", emoji="🎮", value=str(PLAYSTATION_ROLE_ID)),
            discord.SelectOption(label="Nintendo Switch", emoji="🕹️", value=str(SWITCH_ROLE_ID)),
        ],
        PLATFORM_ROLES,
        "platform"
    )


# =========================================================
# FEATURES VIEW — COMPONENT V2
# =========================================================

class FeaturesView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)

        container = discord.ui.Container(
            discord.ui.TextDisplay(
                "# ✨ Features\nChoose your preferences using the menus below."
            ),
            discord.ui.Separator(),
            discord.ui.TextDisplay(
                "### 🎨 Nickname Color\nChoose a color for your nickname."
            ),
            discord.ui.ActionRow(color_select()),
            discord.ui.Separator(),
            discord.ui.TextDisplay(
                "### 🌐 Language\nChoose your preferred language."
            ),
            discord.ui.ActionRow(language_select()),
            discord.ui.Separator(),
            discord.ui.TextDisplay(
                "### 🎮 Platform\nChoose the platform you play on."
            ),
            discord.ui.ActionRow(platform_select()),
            discord.ui.Separator(),
            discord.ui.TextDisplay("-# Select an option from the menus above."),
            accent_colour=discord.Colour.from_rgb(88, 101, 242)
        )

        self.add_item(container)


# =========================================================
# PING BUTTONS
# =========================================================

class PingButton(discord.ui.Button):
    def __init__(self, label, emoji, role_id, custom_id):
        super().__init__(
            label=label,
            emoji=emoji,
            style=discord.ButtonStyle.secondary,
            custom_id=custom_id
        )
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "❌ Use this button in the server.",
                ephemeral=True
            )
            return

        role = interaction.guild.get_role(self.role_id)

        if role is None:
            await interaction.response.send_message(
                "❌ The selected role could not be found.",
                ephemeral=True
            )
            return

        try:
            if role in interaction.user.roles:
                await interaction.user.remove_roles(role)
                text = f"🔕 **{role.name}** notifications disabled."
            else:
                await interaction.user.add_roles(role)
                text = f"🔔 **{role.name}** notifications enabled."

            await interaction.response.send_message(text, ephemeral=True)

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to manage this role.",
                ephemeral=True
            )
        except discord.HTTPException:
            await interaction.response.send_message(
                "❌ Something went wrong. Please try again.",
                ephemeral=True
            )


class RemovePingRolesButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Remove all ping roles",
            emoji="❌",
            style=discord.ButtonStyle.secondary,
            custom_id="features_remove_ping_roles_v2"
        )

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "❌ Use this button in the server.",
                ephemeral=True
            )
            return

        roles = [
            role for role in interaction.user.roles
            if role.id in PING_ROLES
        ]

        try:
            if roles:
                await interaction.user.remove_roles(*roles)

            await interaction.response.send_message(
                "✅ All notification roles have been removed.",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to manage these roles.",
                ephemeral=True
            )
        except discord.HTTPException:
            await interaction.response.send_message(
                "❌ Something went wrong. Please try again.",
                ephemeral=True
            )


class PingView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)

        container = discord.ui.Container(
            discord.ui.TextDisplay(
                "# 🔔 Choose\nChoose which notifications you want to receive."
            ),
            discord.ui.Separator(),
            discord.ui.TextDisplay("### ▶️ YouTube\nGet notified about new YouTube content."),
            discord.ui.ActionRow(
                PingButton("YouTube", "▶️", YOUTUBE_ROLE_ID, "ping_youtube_v2")
            ),
            discord.ui.Separator(),
            discord.ui.TextDisplay("### 🏆 Tournament\nGet notified about tournaments and events."),
            discord.ui.ActionRow(
                PingButton("Tournament", "🏆", TOURNAMENT_ROLE_ID, "ping_tournament_v2")
            ),
            discord.ui.Separator(),
            discord.ui.TextDisplay("### 🎁 Giveaway\nGet notified about giveaways."),
            discord.ui.ActionRow(
                PingButton("Giveaway", "🎁", GIVEAWAY_ROLE_ID, "ping_giveaway_v2")
            ),
            discord.ui.Separator(),
            discord.ui.TextDisplay("### 📰 News\nGet notified about important server news."),
            discord.ui.ActionRow(
                PingButton("News", "📰", NEWS_ROLE_ID, "ping_news_v2")
            ),
            discord.ui.Separator(),
            discord.ui.ActionRow(RemovePingRolesButton()),
            discord.ui.Separator(),
            discord.ui.TextDisplay(
                "-# Click a button to enable or disable a notification role."
            ),
            accent_colour=discord.Colour.from_rgb(88, 101, 242)
        )

        self.add_item(container)


# =========================================================
# ECONOMY COMMANDS — 12 LANGUAGES
# =========================================================

ECONOMY_COMMANDS = {
    "en": """
# 💰 Economy Commands

## 🎮 Games
`. sm <amount/all>` — Play the slot machine.
`. bj <amount/all/half>` — Play blackjack; half uses half your money.
`. cf <amount/all>` — Play cock-fight.
`. roulette <amount/all> <black/red> <number 2-36>` — Play roulette.
`. russian-roulette <amount/all>` — Play Russian roulette.
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
Example: `. item-info Клан`
""",

    "ru": """
# 💰 Команды экономики

## 🎮 Игры
`. sm <сумма/all>` — Игровой автомат.
`. bj <сумма/all/half>` — Блэкджек; half — половина денег.
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
Пример: `. item-info Клан`
""",

    "ro": """
# 💰 Comenzi Economie

## 🎮 Jocuri
`. sm <sumă/all>` — Joacă la sloturi.
`. bj <sumă/all/half>` — Joacă blackjack; half înseamnă jumătate din bani.
`. cf <sumă/all>` — Joacă lupte de cocoși.
`. roulette <sumă/all> <black/red> <număr 2-36>` — Joacă ruletă.
`. russian-roulette <sumă/all>` — Ruletă rusească.
`. russian-roulette start` — Începe ruleta rusească.
`. buy c` — Cumpără o găină pentru luptele de cocoși.

## 💵 Câștiguri
`. work` — Muncește pentru bani.
`. crime` — Încearcă să câștigi bani prin infracțiuni.
`. slut` — Comandă pentru câștiguri.
`. collect` — Colectează câștigurile disponibile.

## 💳 Bani
`. bal` — Verifică soldul.
`. dep` — Depune bani.
`. with` — Retrage bani.
`. give` — Trimite bani altui utilizator.
`. rob` — Încearcă să jefuiești un utilizator.

## 🛒 Magazin
`. store` — Deschide magazinul.
`. inv` — Vezi inventarul.
`. help` — Ajutor pentru botul economic.

## 📦 Informații despre obiecte
`. item-info <numele obiectului>` — Informații despre obiect.
Exemplu: `. item-info Клан`
""",

    "uz": """
# 💰 Iqtisod buyruqlari

## 🎮 O'yinlar
`. sm <miqdor/all>` — Slot o'yinini o'ynash.
`. bj <miqdor/all/half>` — Blackjack; half — pulning yarmi.
`. cf <miqdor/all>` — Xo'roz jangini o'ynash.
`. roulette <miqdor/all> <black/red> <2-36 soni>` — Ruletka o'ynash.
`. russian-roulette <miqdor/all>` — Rus ruletkasi.
`. russian-roulette start` — Rus ruletkasini boshlash.
`. buy c` — Xo'roz jangi uchun tovuq sotib olish.

## 💵 Daromad
`. work` — Ishlab pul topish.
`. crime` — Jinoyat orqali pul topishga urinish.
`. slut` — Pul topish buyrug'i.
`. collect` — Mavjud daromadni yig'ish.

## 💳 Pul
`. bal` — Balansni tekshirish.
`. dep` — Pulni hisobga qo'yish.
`. with` — Pulni yechish.
`. give` — Boshqa foydalanuvchiga pul berish.
`. rob` — Boshqa foydalanuvchini tunashga urinish.

## 🛒 Do'kon
`. store` — Do'konni ochish.
`. inv` — Inventarni ko'rish.
`. help` — Iqtisod botining yordami.

## 📦 Buyum haqida
`. item-info <buyum nomi>` — Buyum haqida ma'lumot.
Misol: `. item-info Клан`
""",

    "kk": """
# 💰 Экономика командалары

## 🎮 Ойындар
`. sm <сома/all>` — Слот ойынын ойнау.
`. bj <сома/all/half>` — Блэкджек; half — ақшаның жартысы.
`. cf <сома/all>` — Әтеш төбелесін ойнау.
`. roulette <сома/all> <black/red> <2-36 саны>` — Рулетка ойнау.
`. russian-roulette <сома/all>` — Орыс рулеткасы.
`. russian-roulette start` — Орыс рулеткасын бастау.
`. buy c` — Әтеш төбелесіне тауық сатып алу.

## 💵 Табыс
`. work` — Жұмыс істеп ақша табу.
`. crime` — Қылмыс арқылы ақша табуға тырысу.
`. slut` — Ақша табу командасы.
`. collect` — Қолжетімді табысты жинау.

## 💳 Ақша
`. bal` — Балансты тексеру.
`. dep` — Ақша салу.
`. with` — Ақша шешу.
`. give` — Басқа пайдаланушыға ақша беру.
`. rob` — Басқа пайдаланушыны тонауға тырысу.

## 🛒 Дүкен
`. store` — Дүкенді ашу.
`. inv` — Заттар тізімін көру.
`. help` — Экономика ботының көмегі.

## 📦 Зат туралы ақпарат
`. item-info <зат атауы>` — Зат туралы ақпарат алу.
Мысал: `. item-info Клан`
""",

    "tr": """
# 💰 Ekonomi Komutları

## 🎮 Oyunlar
`. sm <miktar/all>` — Slot makinesi oyna.
`. bj <miktar/all/half>` — Blackjack; half paranızın yarısıdır.
`. cf <miktar/all>` — Horoz dövüşü oyna.
`. roulette <miktar/all> <black/red> <2-36 sayı>` — Rulet oyna.
`. russian-roulette <miktar/all>` — Rus ruleti.
`. russian-roulette start` — Rus ruletini başlat.
`. buy c` — Horoz dövüşü için tavuk satın al.

## 💵 Kazanç
`. work` — Çalışarak para kazan.
`. crime` — Suç işleyerek para kazanmaya çalış.
`. slut` — Para kazanma komutu.
`. collect` — Mevcut kazancını topla.

## 💳 Para
`. bal` — Bakiyeni kontrol et.
`. dep` — Para yatır.
`. with` — Para çek.
`. give` — Başka bir kullanıcıya para gönder.
`. rob` — Başka bir kullanıcıyı soymaya çalış.

## 🛒 Mağaza
`. store` — Mağazayı aç.
`. inv` — Envanteri kontrol et.
`. help` — Ekonomi botunun yardımını göster.

## 📦 Eşya Bilgisi
`. item-info <eşya adı>` — Eşya hakkında bilgi göster.
Örnek: `. item-info Клан`
""",

    "es": """
# 💰 Comandos de Economía

## 🎮 Juegos
`. sm <cantidad/all>` — Jugar a la tragaperras.
`. bj <cantidad/all/half>` — Blackjack; half usa la mitad de tu dinero.
`. cf <cantidad/all>` — Peleas de gallos.
`. roulette <cantidad/all> <black/red> <número 2-36>` — Ruleta.
`. russian-roulette <cantidad/all>` — Ruleta rusa.
`. russian-roulette start` — Iniciar la ruleta rusa.
`. buy c` — Comprar una gallina para las peleas.

## 💵 Ganancias
`. work` — Trabajar para ganar dinero.
`. crime` — Intentar ganar dinero mediante delitos.
`. slut` — Comando para ganar dinero.
`. collect` — Recoger ganancias disponibles.

## 💳 Dinero
`. bal` — Consultar el saldo.
`. dep` — Depositar dinero.
`. with` — Retirar dinero.
`. give` — Dar dinero a otro usuario.
`. rob` — Intentar robar a otro usuario.

## 🛒 Tienda
`. store` — Abrir la tienda.
`. inv` — Consultar el inventario.
`. help` — Ayuda del bot económico.

## 📦 Información de objetos
`. item-info <nombre del objeto>` — Información del objeto.
Ejemplo: `. item-info Клан`
""",

    "fr": """
# 💰 Commandes Économie

## 🎮 Jeux
`. sm <montant/all>` — Jouer à la machine à sous.
`. bj <montant/all/half>` — Blackjack ; half utilise la moitié de votre argent.
`. cf <montant/all>` — Combats de coqs.
`. roulette <montant/all> <black/red> <nombre 2-36>` — Jouer à la roulette.
`. russian-roulette <montant/all>` — Roulette russe.
`. russian-roulette start` — Démarrer une partie de roulette russe.
`. buy c` — Acheter une poule pour les combats de coqs.

## 💵 Gains
`. work` — Travailler pour gagner de l'argent.
`. crime` — Essayer de gagner de l'argent par le crime.
`. slut` — Commande pour gagner de l'argent.
`. collect` — Récupérer les gains disponibles.

## 💳 Argent
`. bal` — Vérifier le solde.
`. dep` — Déposer de l'argent.
`. with` — Retirer de l'argent.
`. give` — Donner de l'argent à un autre utilisateur.
`. rob` — Essayer de voler un autre utilisateur.

## 🛒 Boutique
`. store` — Ouvrir la boutique.
`. inv` — Consulter l'inventaire.
`. help` — Aide du bot économique.

## 📦 Informations sur les objets
`. item-info <nom de l'objet>` — Afficher les informations d'un objet.
Exemple : `. item-info Клан`
""",

    "de": """
# 💰 Wirtschaftsbefehle

## 🎮 Spiele
`. sm <betrag/all>` — Spielautomaten spielen.
`. bj <betrag/all/half>` — Blackjack; half verwendet die Hälfte deines Geldes.
`. cf <betrag/all>` — Hahnenkämpfe spielen.
`. roulette <betrag/all> <black/red> <Zahl 2-36>` — Roulette spielen.
`. russian-roulette <betrag/all>` — Russisches Roulette.
`. russian-roulette start` — Russisches Roulette starten.
`. buy c` — Ein Huhn für Hahnenkämpfe kaufen.

## 💵 Einnahmen
`. work` — Durch Arbeit Geld verdienen.
`. crime` — Versuchen, durch Verbrechen Geld zu verdienen.
`. slut` — Befehl zum Geldverdienen.
`. collect` — Verfügbare Einnahmen abholen.

## 💳 Geld
`. bal` — Kontostand prüfen.
`. dep` — Geld einzahlen.
`. with` — Geld abheben.
`. give` — Geld an einen anderen Nutzer geben.
`. rob` — Versuchen, einen anderen Nutzer auszurauben.

## 🛒 Shop
`. store` — Shop öffnen.
`. inv` — Inventar ansehen.
`. help` — Hilfe des Wirtschaftsbots anzeigen.

## 📦 Gegenstandsinformationen
`. item-info <Gegenstandsname>` — Informationen über einen Gegenstand anzeigen.
Beispiel: `. item-info Клан`
""",

    "it": """
# 💰 Comandi Economia

## 🎮 Giochi
`. sm <importo/all>` — Gioca alle slot machine.
`. bj <importo/all/half>` — Blackjack; half usa metà dei tuoi soldi.
`. cf <importo/all>` — Combattimenti tra galli.
`. roulette <importo/all> <black/red> <numero 2-36>` — Gioca alla roulette.
`. russian-roulette <importo/all>` — Roulette russa.
`. russian-roulette start` — Avvia una partita di roulette russa.
`. buy c` — Compra una gallina per i combattimenti.

## 💵 Guadagni
`. work` — Lavora per guadagnare denaro.
`. crime` — Prova a guadagnare denaro con il crimine.
`. slut` — Comando per guadagnare denaro.
`. collect` — Raccogli i guadagni disponibili.

## 💳 Denaro
`. bal` — Controlla il saldo.
`. dep` — Deposita denaro.
`. with` — Preleva denaro.
`. give` — Dai denaro a un altro utente.
`. rob` — Prova a derubare un altro utente.

## 🛒 Negozio
`. store` — Apri il negozio.
`. inv` — Controlla l'inventario.
`. help` — Mostra l'aiuto del bot economico.

## 📦 Informazioni sugli oggetti
`. item-info <nome oggetto>` — Mostra informazioni su un oggetto.
Esempio: `. item-info Клан`
""",

    "uk": """
# 💰 Команди економіки

## 🎮 Ігри
`. sm <сума/all>` — Грати в ігровий автомат.
`. bj <сума/all/half>` — Блекджек; half використовує половину грошей.
`. cf <сума/all>` — Півнячі бої.
`. roulette <сума/all> <black/red> <число 2-36>` — Грати в рулетку.
`. russian-roulette <сума/all>` — Російська рулетка.
`. russian-roulette start` — Почати російську рулетку.
`. buy c` — Купити курку для півнячих боїв.

## 💵 Заробіток
`. work` — Заробити гроші роботою.
`. crime` — Спробувати заробити злочином.
`. slut` — Команда для заробітку.
`. collect` — Забрати доступний заробіток.

## 💳 Гроші
`. bal` — Перевірити баланс.
`. dep` — Покласти гроші на рахунок.
`. with` — Зняти гроші.
`. give` — Передати гроші іншому користувачу.
`. rob` — Спробувати пограбувати іншого користувача.

## 🛒 Магазин
`. store` — Відкрити магазин.
`. inv` — Переглянути інвентар.
`. help` — Допомога економічного бота.

## 📦 Інформація про предмети
`. item-info <назва предмета>` — Інформація про предмет.
Приклад: `. item-info Клан`
""",

    "pl": """
# 💰 Komendy Ekonomii

## 🎮 Gry
`. sm <kwota/all>` — Graj na automacie.
`. bj <kwota/all/half>` — Blackjack; half oznacza połowę pieniędzy.
`. cf <kwota/all>` — Walki kogutów.
`. roulette <kwota/all> <black/red> <liczba 2-36>` — Graj w ruletkę.
`. russian-roulette <kwota/all>` — Rosyjska ruletka.
`. russian-roulette start` — Rozpocznij rosyjską ruletkę.
`. buy c` — Kup kurę do walk kogutów.

## 💵 Zarobki
`. work` — Pracuj, aby zarobić pieniądze.
`. crime` — Spróbuj zarobić na przestępstwie.
`. slut` — Komenda do zarabiania pieniędzy.
`. collect` — Odbierz dostępne zarobki.

## 💳 Pieniądze
`. bal` — Sprawdź saldo.
`. dep` — Wpłać pieniądze.
`. with` — Wypłać pieniądze.
`. give` — Przekaż pieniądze innemu użytkownikowi.
`. rob` — Spróbuj okraść innego użytkownika.

## 🛒 Sklep
`. store` — Otwórz sklep.
`. inv` — Sprawdź ekwipunek.
`. help` — Pomoc bota ekonomicznego.

## 📦 Informacje o przedmiotach
`. item-info <nazwa przedmiotu>` — Pokaż informacje o przedmiocie.
Przykład: `. item-info Клан`
"""
}


# =========================================================
# ECONOMY LANGUAGE SELECT
# =========================================================

ECONOMY_LANGUAGES = [
    ("🇬🇧 English", "en"),
    ("🇷🇺 Russian", "ru"),
    ("🇷🇴 Romanian", "ro"),
    ("🇺🇿 Uzbek", "uz"),
    ("🇰🇿 Kazakh", "kk"),
    ("🇹🇷 Turkish", "tr"),
    ("🇪🇸 Spanish", "es"),
    ("🇫🇷 French", "fr"),
    ("🇩🇪 German", "de"),
    ("🇮🇹 Italian", "it"),
    ("🇺🇦 Ukrainian", "uk"),
    ("🇵🇱 Polish", "pl"),
]


class EconomyLanguageSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=label.split(" ", 1)[1],
                emoji=label.split(" ", 1)[0],
                value=code
            )
            for label, code in ECONOMY_LANGUAGES
        ]

        super().__init__(
            placeholder="🌐 Choose a language / Выбери язык",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="economy_commands_language_v1"
        )

    async def callback(self, interaction: discord.Interaction):
        language = self.values[0]
        text = ECONOMY_COMMANDS.get(
            language,
            ECONOMY_COMMANDS["en"]
        )

        # Discord message content has a 2000-character limit.
        # Use an embed so the help text can be displayed in one message.
        embed = discord.Embed(
            description=text,
            colour=discord.Colour.from_rgb(88, 101, 242)
        )
        embed.set_footer(text="Economy Commands")

        await interaction.response.edit_message(
            content=None,
            embed=embed,
            view=None
        )


class EconomyLanguageView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(EconomyLanguageSelect())


# =========================================================
# COG
# =========================================================

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

    @commands.command(name="economy")
    async def economy(self, ctx, action=None):
        if not action or action.lower() != "commands":
            return

        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            pass

        try:
            await ctx.author.send(
                content=(
                    "🌐 **Economy Commands**\n"
                    "Choose your language below.\n\n"
                    "Выбери язык, чтобы посмотреть команды экономики."
                ),
                view=EconomyLanguageView()
            )

        except discord.Forbidden:
            try:
                await ctx.send(
                    f"{ctx.author.mention}, I couldn't DM you. "
                    "Please enable direct messages from server members "
                    "and try `!economy commands` again.",
                    delete_after=15
                )
            except discord.HTTPException:
                pass

    @commands.command(name="commands")
    async def commands_message(self, ctx, system=None):
        if not system or system.lower() != "message":
            return

        embed = discord.Embed(
            title="📚 Message System Commands",
            description=(
                "`!features panel` — Create the Features panel.\n"
                "`!ping panel` — Create the notification roles panel.\n"
                "`!economy commands` — Choose a language and view economy commands.\n"
                "`!commands Message` — Show this command list."
            ),
            colour=discord.Colour.from_rgb(88, 101, 242)
        )

        try:
            await ctx.author.send(embed=embed)

            try:
                await ctx.message.delete()
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                pass

        except discord.Forbidden:
            await ctx.send(
                f"{ctx.author.mention}, please enable DMs to receive "
                "the Message System command list.",
                delete_after=15
            )


# =========================================================
# SETUP
# =========================================================

async def setup(bot):
    await bot.add_cog(Message(bot))

    bot.add_view(FeaturesView())
    bot.add_view(PingView())
    bot.add_view(EconomyLanguageView())

    print(
        "✅ FeaturesView, PingView and EconomyLanguageView registered!"
        )
