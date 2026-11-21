import json
import logging
import os
from typing import Dict, List, Tuple

import discord
from discord.ext import commands

# =========================================================
# RULES SYSTEM CONFIGURATION
# =========================================================

OWNER_ID = 1176149190192152626
LANGUAGE_FILE = "rules_languages.json"
VIEW_TIMEOUT = 300
ACCENT_COLOR = 0x5865F2

LANGUAGES = [
    ("en", "🇬🇧 English"),
    ("ru", "🇷🇺 Russian"),
    ("ro", "🇷🇴 Romanian"),
    ("uz", "🇺🇿 Uzbek"),
    ("kk", "🇰🇿 Kazakh"),
    ("tr", "🇹🇷 Turkish"),
    ("es", "🇪🇸 Spanish"),
    ("fr", "🇫🇷 French"),
    ("de", "🇩🇪 German"),
    ("it", "🇮🇹 Italian"),
    ("uk", "🇺🇦 Ukrainian"),
    ("pl", "🇵🇱 Polish"),
]

# Localized interface labels and category names.
I18N = {
    "en": {
        "title": "LEGENDS SERVER RULES",
        "subtitle": "Please read all rules carefully. By staying in this server, you agree to follow them.",
        "choose_language": "🌐 SELECT YOUR LANGUAGE",
        "language_hint": "Choose the language in which you want to read the server rules.",
        "choose_category": "📂 CHOOSE A RULE CATEGORY",
        "category_hint": "Select a category from the menu below. The rules will appear in this private message.",
        "all_rules": "All rules",
        "staff_note": "STAFF & MODERATION",
        "staff_text": "Moderators must provide a clear punishment reason and keep screenshot evidence for every action. Never abuse staff permissions.",
        "punishment": "PUNISHMENT ORDER",
        "punishment_text": "Normal escalation: 1 Warn ➜ Mute 1 Hour ➜ Mute 1 Day ➜ Kick ➜ Ban. Serious violations may receive a stronger punishment immediately.",
        "select_placeholder": "Select a category...",
        "back": "Back",
        "page": "Page",
        "expired": "This rules panel has expired. Run !rules again.",
        "private_only": "This menu belongs to the person who opened it.",
        "language_saved": "Language selected. Your private rules panel is ready.",
        "category_names": [
            "📌 General Rules", "💬 Chat Rules", "🤝 Respect & Behavior",
            "🚫 Spam & Flood", "🔞 Inappropriate Content", "📢 Advertising",
            "🎭 Nicknames & Profiles", "🎮 Gaming Rules", "🏆 Tournament Rules",
            "🎫 Support & Tickets", "🛡️ Staff Rules", "⚠️ Punishments",
            "🔐 Security & Privacy"
        ],
    },
    "ru": {
        "title": "ПРАВИЛА СЕРВЕРА LEGENDS",
        "subtitle": "Внимательно прочитайте все правила. Оставаясь на сервере, вы соглашаетесь их соблюдать.",
        "choose_language": "🌐 ВЫБЕРИТЕ ЯЗЫК",
        "language_hint": "Выберите язык, на котором хотите читать правила сервера.",
        "choose_category": "📂 ВЫБЕРИТЕ КАТЕГОРИЮ ПРАВИЛ",
        "category_hint": "Выберите категорию в меню ниже. Правила появятся в этом скрытом сообщении.",
        "all_rules": "Все правила",
        "staff_note": "ПРАВИЛА АДМИНИСТРАЦИИ",
        "staff_text": "Модераторы обязаны указывать понятную причину наказания и сохранять скриншот-доказательство каждого действия. Запрещено злоупотреблять правами.",
        "punishment": "ПОСЛЕДОВАТЕЛЬНОСТЬ НАКАЗАНИЙ",
        "punishment_text": "Обычная последовательность: 1 Warn ➜ Mute 1 Hour ➜ Mute 1 Day ➜ Kick ➜ Ban. За серьёзные нарушения может сразу выдаваться более строгое наказание.",
        "select_placeholder": "Выберите категорию...",
        "back": "Назад",
        "page": "Страница",
        "expired": "Это меню правил устарело. Введите !rules ещё раз.",
        "private_only": "Это меню доступно только тому, кто его открыл.",
        "language_saved": "Язык выбран. Ваше скрытое меню правил готово.",
        "category_names": [
            "📌 Основные правила", "💬 Правила чата", "🤝 Уважение и поведение",
            "🚫 Спам и флуд", "🔞 Недопустимый контент", "📢 Реклама",
            "🎭 Никнеймы и профили", "🎮 Игровые правила", "🏆 Правила турниров",
            "🎫 Поддержка и тикеты", "🛡️ Правила администрации", "⚠️ Наказания",
            "🔐 Безопасность и конфиденциальность"
        ],
    },
    "ro": {
        "title": "REGULILE SERVERULUI LEGENDS",
        "subtitle": "Citiți cu atenție toate regulile. Rămânând pe server, acceptați să le respectați.",
        "choose_language": "🌐 ALEGEȚI LIMBA",
        "language_hint": "Alegeți limba în care doriți să citiți regulile serverului.",
        "choose_category": "📂 ALEGEȚI O CATEGORIE",
        "category_hint": "Selectați o categorie din meniul de mai jos.",
        "all_rules": "Toate regulile",
        "staff_note": "REGULI PENTRU STAFF",
        "staff_text": "Moderatorii trebuie să ofere motivul clar al sancțiunii și să păstreze capturi de ecran ca dovezi pentru fiecare acțiune. Abuzul de permisiuni este interzis.",
        "punishment": "ORDINEA SANCȚIUNILOR",
        "punishment_text": "Ordine normală: 1 Warn ➜ Mute 1 Hour ➜ Mute 1 Day ➜ Kick ➜ Ban. Încălcările grave pot primi imediat o sancțiune mai severă.",
        "select_placeholder": "Alegeți o categorie...",
        "back": "Înapoi", "page": "Pagina",
        "expired": "Panoul a expirat. Folosiți din nou !rules.",
        "private_only": "Acest meniu este disponibil doar persoanei care l-a deschis.",
        "language_saved": "Limba a fost selectată. Panoul privat este gata.",
        "category_names": [
            "📌 Reguli generale", "💬 Reguli de chat", "🤝 Respect și comportament",
            "🚫 Spam și flood", "🔞 Conținut neadecvat", "📢 Publicitate",
            "🎭 Porecle și profiluri", "🎮 Reguli de joc", "🏆 Reguli de turneu",
            "🎫 Suport și tichete", "🛡️ Reguli pentru staff", "⚠️ Sancțiuni",
            "🔐 Siguranță și confidențialitate"
        ],
    },
    "uz": {
        "title": "LEGENDS SERVER QOIDALARI",
        "subtitle": "Barcha qoidalarni diqqat bilan o‘qing. Serverda qolish orqali ularga rioya qilishga rozilik bildirasiz.",
        "choose_language": "🌐 TILNI TANLANG",
        "language_hint": "Server qoidalarini qaysi tilda o‘qishni tanlang.",
        "choose_category": "📂 QOIDALAR KATEGORIYASINI TANLANG",
        "category_hint": "Quyidagi menyudan kategoriyani tanlang.",
        "all_rules": "Barcha qoidalar",
        "staff_note": "MODERATORLAR QOIDALARI",
        "staff_text": "Moderatorlar har bir jazo uchun aniq sabab yozishi va skrinshot dalilini saqlashi shart. Vakolatlarni suiiste’mol qilish taqiqlanadi.",
        "punishment": "JAZOLAR TARTIBI",
        "punishment_text": "Oddiy tartib: 1 Warn ➜ Mute 1 Hour ➜ Mute 1 Day ➜ Kick ➜ Ban. Jiddiy qoidabuzarliklar uchun darhol qattiqroq jazo berilishi mumkin.",
        "select_placeholder": "Kategoriyani tanlang...",
        "back": "Orqaga", "page": "Sahifa",
        "expired": "Menyu muddati tugadi. !rules buyrug‘ini qayta kiriting.",
        "private_only": "Bu menyu faqat uni ochgan foydalanuvchi uchun.",
        "language_saved": "Til tanlandi. Shaxsiy qoidalar paneli tayyor.",
        "category_names": [
            "📌 Umumiy qoidalar", "💬 Chat qoidalari", "🤝 Hurmat va xulq",
            "🚫 Spam va flood", "🔞 Nomaqbul kontent", "📢 Reklama",
            "🎭 Niklar va profillar", "🎮 O‘yin qoidalari", "🏆 Turnir qoidalari",
            "🎫 Yordam va ticketlar", "🛡️ Moderatorlar qoidalari", "⚠️ Jazolar",
            "🔐 Xavfsizlik va maxfiylik"
        ],
    },
    "kk": {
        "title": "LEGENDS СЕРВЕРІНІҢ ЕРЕЖЕЛЕРІ",
        "subtitle": "Барлық ережені мұқият оқыңыз. Серверде қалу арқылы оларды сақтауға келісесіз.",
        "choose_language": "🌐 ТІЛДІ ТАҢДАҢЫЗ",
        "language_hint": "Сервер ережелерін оқитын тілді таңдаңыз.",
        "choose_category": "📂 ЕРЕЖЕ САНАТЫН ТАҢДАҢЫЗ",
        "category_hint": "Төмендегі мәзірден санатты таңдаңыз.",
        "all_rules": "Барлық ережелер",
        "staff_note": "ҚЫЗМЕТКЕРЛЕР ЕРЕЖЕЛЕРІ",
        "staff_text": "Модераторлар әр жазаға нақты себеп жазып, әр әрекетке скриншот дәлелін сақтауы керек. Өкілеттікті теріс пайдалануға тыйым салынады.",
        "punishment": "ЖАЗАЛАУ РЕТІ",
        "punishment_text": "Қалыпты реті: 1 Warn ➜ Mute 1 Hour ➜ Mute 1 Day ➜ Kick ➜ Ban. Ауыр бұзушылықтар үшін бірден қатаң жаза берілуі мүмкін.",
        "select_placeholder": "Санатты таңдаңыз...",
        "back": "Артқа", "page": "Бет",
        "expired": "Мәзірдің уақыты аяқталды. !rules пәрменін қайта қолданыңыз.",
        "private_only": "Бұл мәзір оны ашқан пайдаланушыға ғана арналған.",
        "language_saved": "Тіл таңдалды. Жеке ережелер панелі дайын.",
        "category_names": [
            "📌 Жалпы ережелер", "💬 Чат ережелері", "🤝 Құрмет және тәртіп",
            "🚫 Спам және флуд", "🔞 Жарамсыз контент", "📢 Жарнама",
            "🎭 Лақап аттар мен профильдер", "🎮 Ойын ережелері", "🏆 Турнир ережелері",
            "🎫 Қолдау және тикеттер", "🛡️ Қызметкерлер ережелері", "⚠️ Жазалар",
            "🔐 Қауіпсіздік және құпиялылық"
        ],
    },
    "tr": {
        "title": "LEGENDS SUNUCU KURALLARI",
        "subtitle": "Lütfen tüm kuralları dikkatlice okuyun. Sunucuda kalarak kurallara uymayı kabul edersiniz.",
        "choose_language": "🌐 DİLİNİZİ SEÇİN",
        "language_hint": "Sunucu kurallarını okumak istediğiniz dili seçin.",
        "choose_category": "📂 KURAL KATEGORİSİ SEÇİN",
        "category_hint": "Aşağıdaki menüden bir kategori seçin.",
        "all_rules": "Tüm kurallar",
        "staff_note": "YETKİLİ KURALLARI",
        "staff_text": "Moderatörler her ceza için açık bir neden belirtmeli ve her işlem için ekran görüntüsü kanıtı saklamalıdır. Yetkileri kötüye kullanmak yasaktır.",
        "punishment": "CEZA SIRALAMASI",
        "punishment_text": "Normal sıra: 1 Warn ➜ Mute 1 Hour ➜ Mute 1 Day ➜ Kick ➜ Ban. Ağır ihlallerde doğrudan daha ağır ceza verilebilir.",
        "select_placeholder": "Kategori seçin...",
        "back": "Geri", "page": "Sayfa",
        "expired": "Menünün süresi doldu. !rules komutunu tekrar kullanın.",
        "private_only": "Bu menü yalnızca açan kişiye aittir.",
        "language_saved": "Dil seçildi. Özel kurallar paneliniz hazır.",
        "category_names": [
            "📌 Genel kurallar", "💬 Sohbet kuralları", "🤝 Saygı ve davranış",
            "🚫 Spam ve flood", "🔞 Uygunsuz içerik", "📢 Reklam",
            "🎭 Takma adlar ve profiller", "🎮 Oyun kuralları", "🏆 Turnuva kuralları",
            "🎫 Destek ve ticketlar", "🛡️ Yetkili kuralları", "⚠️ Cezalar",
            "🔐 Güvenlik ve gizlilik"
        ],
    },
    "es": {
        "title": "REGLAS DEL SERVIDOR LEGENDS",
        "subtitle": "Lee todas las reglas con atención. Al permanecer en el servidor, aceptas cumplirlas.",
        "choose_language": "🌐 ELIGE TU IDIOMA",
        "language_hint": "Elige el idioma en el que quieres leer las reglas.",
        "choose_category": "📂 ELIGE UNA CATEGORÍA",
        "category_hint": "Selecciona una categoría en el menú de abajo.",
        "all_rules": "Todas las reglas",
        "staff_note": "REGLAS DEL STAFF",
        "staff_text": "Los moderadores deben indicar un motivo claro para cada sanción y guardar una captura como prueba de cada acción. Está prohibido abusar de los permisos.",
        "punishment": "ORDEN DE SANCIONES",
        "punishment_text": "Orden habitual: 1 Warn ➜ Mute 1 Hour ➜ Mute 1 Day ➜ Kick ➜ Ban. Las infracciones graves pueden recibir una sanción más severa de inmediato.",
        "select_placeholder": "Selecciona una categoría...",
        "back": "Atrás", "page": "Página",
        "expired": "El panel ha caducado. Usa !rules de nuevo.",
        "private_only": "Este menú solo pertenece a quien lo abrió.",
        "language_saved": "Idioma seleccionado. Tu panel privado está listo.",
        "category_names": [
            "📌 Reglas generales", "💬 Reglas del chat", "🤝 Respeto y conducta",
            "🚫 Spam e inundación", "🔞 Contenido inapropiado", "📢 Publicidad",
            "🎭 Apodos y perfiles", "🎮 Reglas de juegos", "🏆 Reglas de torneos",
            "🎫 Soporte y tickets", "🛡️ Reglas del staff", "⚠️ Sanciones",
            "🔐 Seguridad y privacidad"
        ],
    },
    "fr": {
        "title": "RÈGLES DU SERVEUR LEGENDS",
        "subtitle": "Veuillez lire attentivement toutes les règles. En restant sur le serveur, vous acceptez de les respecter.",
        "choose_language": "🌐 CHOISISSEZ VOTRE LANGUE",
        "language_hint": "Choisissez la langue dans laquelle lire les règles.",
        "choose_category": "📂 CHOISISSEZ UNE CATÉGORIE",
        "category_hint": "Sélectionnez une catégorie dans le menu ci-dessous.",
        "all_rules": "Toutes les règles",
        "staff_note": "RÈGLES DU STAFF",
        "staff_text": "Les modérateurs doivent indiquer une raison claire pour chaque sanction et conserver une capture d’écran comme preuve de chaque action. L’abus de permissions est interdit.",
        "punishment": "ORDRE DES SANCTIONS",
        "punishment_text": "Ordre normal : 1 Warn ➜ Mute 1 Hour ➜ Mute 1 Day ➜ Kick ➜ Ban. Les infractions graves peuvent entraîner immédiatement une sanction plus sévère.",
        "select_placeholder": "Choisissez une catégorie...",
        "back": "Retour", "page": "Page",
        "expired": "Ce panneau a expiré. Relancez !rules.",
        "private_only": "Ce menu appartient uniquement à la personne qui l’a ouvert.",
        "language_saved": "Langue sélectionnée. Votre panneau privé est prêt.",
        "category_names": [
            "📌 Règles générales", "💬 Règles du chat", "🤝 Respect et comportement",
            "🚫 Spam et flood", "🔞 Contenu inapproprié", "📢 Publicité",
            "🎭 Pseudos et profils", "🎮 Règles de jeu", "🏆 Règles des tournois",
            "🎫 Assistance et tickets", "🛡️ Règles du staff", "⚠️ Sanctions",
            "🔐 Sécurité et confidentialité"
        ],
    },
    "de": {
        "title": "LEGENDS SERVERREGELN",
        "subtitle": "Bitte lies alle Regeln sorgfältig. Wenn du auf dem Server bleibst, stimmst du ihnen zu.",
        "choose_language": "🌐 SPRACHE AUSWÄHLEN",
        "language_hint": "Wähle die Sprache, in der du die Serverregeln lesen möchtest.",
        "choose_category": "📂 REGELKATEGORIE AUSWÄHLEN",
        "category_hint": "Wähle unten eine Kategorie aus.",
        "all_rules": "Alle Regeln",
        "staff_note": "TEAMREGELN",
        "staff_text": "Moderatoren müssen für jede Strafe einen klaren Grund angeben und einen Screenshot als Beweis für jede Maßnahme aufbewahren. Der Missbrauch von Berechtigungen ist verboten.",
        "punishment": "STRAFENREIHENFOLGE",
        "punishment_text": "Normale Reihenfolge: 1 Warn ➜ Mute 1 Hour ➜ Mute 1 Day ➜ Kick ➜ Ban. Schwere Verstöße können sofort strenger bestraft werden.",
        "select_placeholder": "Kategorie auswählen...",
        "back": "Zurück", "page": "Seite",
        "expired": "Dieses Menü ist abgelaufen. Verwende !rules erneut.",
        "private_only": "Dieses Menü gehört nur der Person, die es geöffnet hat.",
        "language_saved": "Sprache ausgewählt. Dein privates Regelmenü ist bereit.",
        "category_names": [
            "📌 Allgemeine Regeln", "💬 Chatregeln", "🤝 Respekt und Verhalten",
            "🚫 Spam und Flood", "🔞 Unangemessene Inhalte", "📢 Werbung",
            "🎭 Namen und Profile", "🎮 Spielregeln", "🏆 Turnierregeln",
            "🎫 Support und Tickets", "🛡️ Teamregeln", "⚠️ Strafen",
            "🔐 Sicherheit und Datenschutz"
        ],
    },
    "it": {
        "title": "REGOLE DEL SERVER LEGENDS",
        "subtitle": "Leggi attentamente tutte le regole. Restando nel server, accetti di rispettarle.",
        "choose_language": "🌐 SCEGLI LA LINGUA",
        "language_hint": "Scegli la lingua in cui vuoi leggere le regole.",
        "choose_category": "📂 SCEGLI UNA CATEGORIA",
        "category_hint": "Seleziona una categoria dal menu qui sotto.",
        "all_rules": "Tutte le regole",
        "staff_note": "REGOLE DELLO STAFF",
        "staff_text": "I moderatori devono indicare un motivo chiaro per ogni sanzione e conservare uno screenshot come prova di ogni azione. È vietato abusare dei permessi.",
        "punishment": "ORDINE DELLE SANZIONI",
        "punishment_text": "Ordine normale: 1 Warn ➜ Mute 1 Hour ➜ Mute 1 Day ➜ Kick ➜ Ban. Le violazioni gravi possono ricevere subito una sanzione più severa.",
        "select_placeholder": "Seleziona una categoria...",
        "back": "Indietro", "page": "Pagina",
        "expired": "Il pannello è scaduto. Usa di nuovo !rules.",
        "private_only": "Questo menu appartiene solo a chi lo ha aperto.",
        "language_saved": "Lingua selezionata. Il pannello privato è pronto.",
        "category_names": [
            "📌 Regole generali", "💬 Regole della chat", "🤝 Rispetto e comportamento",
            "🚫 Spam e flood", "🔞 Contenuti inappropriati", "📢 Pubblicità",
            "🎭 Nickname e profili", "🎮 Regole di gioco", "🏆 Regole dei tornei",
            "🎫 Supporto e ticket", "🛡️ Regole dello staff", "⚠️ Sanzioni",
            "🔐 Sicurezza e privacy"
        ],
    },
    "uk": {
        "title": "ПРАВИЛА СЕРВЕРА LEGENDS",
        "subtitle": "Уважно прочитайте всі правила. Залишаючись на сервері, ви погоджуєтеся їх дотримуватися.",
        "choose_language": "🌐 ОБЕРІТЬ МОВУ",
        "language_hint": "Оберіть мову, якою хочете читати правила сервера.",
        "choose_category": "📂 ОБЕРІТЬ КАТЕГОРІЮ ПРАВИЛ",
        "category_hint": "Оберіть категорію в меню нижче.",
        "all_rules": "Усі правила",
        "staff_note": "ПРАВИЛА АДМІНІСТРАЦІЇ",
        "staff_text": "Модератори повинні вказувати чітку причину кожного покарання та зберігати скриншот-доказ кожної дії. Зловживати правами заборонено.",
        "punishment": "ПОСЛІДОВНІСТЬ ПОКАРАНЬ",
        "punishment_text": "Звичайна послідовність: 1 Warn ➜ Mute 1 Hour ➜ Mute 1 Day ➜ Kick ➜ Ban. За серйозні порушення можливе одразу суворіше покарання.",
        "select_placeholder": "Оберіть категорію...",
        "back": "Назад", "page": "Сторінка",
        "expired": "Час дії меню минув. Введіть !rules ще раз.",
        "private_only": "Це меню доступне лише тому, хто його відкрив.",
        "language_saved": "Мову обрано. Приватна панель готова.",
        "category_names": [
            "📌 Загальні правила", "💬 Правила чату", "🤝 Повага та поведінка",
            "🚫 Спам і флуд", "🔞 Неприйнятний контент", "📢 Реклама",
            "🎭 Нікнейми та профілі", "🎮 Ігрові правила", "🏆 Правила турнірів",
            "🎫 Підтримка та тікети", "🛡️ Правила адміністрації", "⚠️ Покарання",
            "🔐 Безпека та приватність"
        ],
    },
    "pl": {
        "title": "ZASADY SERWERA LEGENDS",
        "subtitle": "Przeczytaj uważnie wszystkie zasady. Pozostając na serwerze, zgadzasz się ich przestrzegać.",
        "choose_language": "🌐 WYBIERZ JĘZYK",
        "language_hint": "Wybierz język, w którym chcesz czytać zasady serwera.",
        "choose_category": "📂 WYBIERZ KATEGORIĘ ZASAD",
        "category_hint": "Wybierz kategorię z menu poniżej.",
        "all_rules": "Wszystkie zasady",
        "staff_note": "ZASADY EKIPY",
        "staff_text": "Moderatorzy muszą podać jasny powód każdej kary i zachować zrzut ekranu jako dowód każdego działania. Nadużywanie uprawnień jest zabronione.",
        "punishment": "KOLEJNOŚĆ KAR",
        "punishment_text": "Standardowa kolejność: 1 Warn ➜ Mute 1 Hour ➜ Mute 1 Day ➜ Kick ➜ Ban. Poważne naruszenia mogą od razu skutkować surowszą karą.",
        "select_placeholder": "Wybierz kategorię...",
        "back": "Wstecz", "page": "Strona",
        "expired": "Panel wygasł. Uruchom ponownie !rules.",
        "private_only": "To menu należy tylko do osoby, która je otworzyła.",
        "language_saved": "Wybrano język. Prywatny panel jest gotowy.",
        "category_names": [
            "📌 Zasady ogólne", "💬 Zasady czatu", "🤝 Szacunek i zachowanie",
            "🚫 Spam i flood", "🔞 Nieodpowiednie treści", "📢 Reklama",
            "🎭 Nicki i profile", "🎮 Zasady gier", "🏆 Zasady turniejów",
            "🎫 Pomoc i zgłoszenia", "🛡️ Zasady ekipy", "⚠️ Kary",
            "🔐 Bezpieczeństwo i prywatność"
        ],
    },
}

# Rule text is kept in clear, consistent English so that the legal meaning
# does not change between languages. Interface/category labels are localized.
# Each rule has a stable number (for example 3.3 or 11.2).
RULES: List[Tuple[str, List[str]]] = [
    ("General Rules", [
        "1.1 — Follow Discord Terms of Service and Community Guidelines.",
        "1.2 — Follow all instructions from authorized server staff.",
        "1.3 — Do not use loopholes to bypass server rules or moderation.",
        "1.4 — Do not disrupt the normal operation of the server.",
        "1.5 — Do not impersonate the server owner, staff, bots, or other members.",
        "1.6 — Do not use alternate accounts to evade restrictions or punishments.",
        "1.7 — Keep your account and behavior appropriate for this community.",
        "1.8 — If a rule is unclear, ask staff before assuming an action is allowed.",
    ]),
    ("Chat Rules", [
        "2.1 — Keep messages relevant to the channel topic.",
        "2.2 — Use the correct channels for discussions, media, and support.",
        "2.3 — Do not send excessive capital letters or disruptive message formatting.",
        "2.4 — Do not flood the chat with repeated or meaningless messages.",
        "2.5 — Do not misuse mentions or ping members without a valid reason.",
        "2.6 — Do not share malicious, misleading, or deliberately disruptive links.",
        "2.7 — Keep conversations readable and do not derail ongoing discussions.",
    ]),
    ("Respect & Behavior", [
        "3.1 — Treat every member with respect.",
        "3.2 — Harassment, bullying, threats, and targeted humiliation are prohibited.",
        "3.3 — Do not provoke unnecessary arguments or deliberately start conflicts.",
        "3.4 — Respect other members' opinions and personal boundaries.",
        "3.5 — Discrimination or hateful conduct is not allowed.",
        "3.6 — Do not encourage others to break server rules.",
        "3.7 — If a conflict starts, stop escalating it and contact staff when needed.",
    ]),
    ("Spam & Flood", [
        "4.1 — Repeated messages sent to flood a channel are prohibited.",
        "4.2 — Do not spam emojis, stickers, reactions, or attachments.",
        "4.3 — Do not mass-mention users or roles.",
        "4.4 — Do not copy and paste the same message across multiple channels.",
        "4.5 — Do not use bots, scripts, or alternate accounts to spam.",
        "4.6 — Avoid unnecessary soundboard or voice-channel spam.",
    ]),
    ("Inappropriate Content", [
        "5.1 — Do not post sexual, explicit, or otherwise age-inappropriate content.",
        "5.2 — Do not share graphic, shocking, or disturbing media.",
        "5.3 — Do not post content that promotes violence, hatred, or harassment.",
        "5.4 — Do not share illegal, stolen, or malicious material.",
        "5.5 — Use spoiler tags when content may unexpectedly spoil a game or story.",
        "5.6 — Staff may remove content that makes the community unsafe or uncomfortable.",
    ]),
    ("Advertising", [
        "6.1 — Unapproved advertising is prohibited.",
        "6.2 — Do not advertise other Discord servers in messages, profiles, or DMs to members.",
        "6.3 — Do not send unsolicited promotional links or referral codes.",
        "6.4 — Partnerships and promotions require prior staff approval.",
        "6.5 — Do not repeatedly ask members to subscribe, follow, or join external pages.",
    ]),
    ("Nicknames & Profiles", [
        "7.1 — Nicknames must not contain insults, slurs, threats, or inappropriate wording.",
        "7.2 — Do not use a nickname or avatar intended to impersonate another person.",
        "7.3 — Profile pictures, banners, and statuses must follow server rules.",
        "7.4 — Do not use deceptive names to imitate staff or official bots.",
        "7.5 — Staff may request a nickname or profile change when it violates these rules.",
    ]),
    ("Gaming Rules", [
        "8.1 — Play fairly and do not use cheats, exploits, or unauthorized tools in community events.",
        "8.2 — Do not scam, deceive, or intentionally sabotage other players.",
        "8.3 — Respect game-specific channels and their instructions.",
        "8.4 — Do not falsely claim another player's achievements or results.",
        "8.5 — Keep game-related arguments respectful.",
        "8.6 — Follow the rules of the game and any additional event instructions.",
    ]),
    ("Tournament Rules", [
        "9.1 — Follow the tournament host's instructions and the published tournament format.",
        "9.2 — Do not use cheats, exploits, or unfair methods during a tournament.",
        "9.3 — Do not fake results, screenshots, match outcomes, or player identities.",
        "9.4 — Be ready at the announced time and communicate delays to the host.",
        "9.5 — Do not interfere with active matches or disrupt tournament channels.",
        "9.6 — The host may review evidence and decide disputed results.",
        "9.7 — Respect the final tournament decision unless an appeal process is provided.",
    ]),
    ("Support & Tickets", [
        "10.1 — Open a ticket only for a genuine question or issue.",
        "10.2 — Explain your issue clearly and provide relevant information.",
        "10.3 — Do not spam, duplicate, or repeatedly reopen tickets without a reason.",
        "10.4 — Do not share another member's private information in a ticket.",
        "10.5 — Be respectful to support staff and allow time for a response.",
        "10.6 — Do not create false reports or submit fabricated evidence.",
    ]),
    ("Staff Rules", [
        "11.1 — Staff members must act fairly, calmly, and professionally.",
        "11.2 — A screenshot or other verifiable evidence is mandatory for every punishment.",
        "11.3 — A clear and specific reason must always be written when issuing a punishment.",
        "11.4 — Staff must keep the evidence and punishment details available for review.",
        "11.5 — Never use moderation permissions for personal arguments, revenge, or entertainment.",
        "11.6 — Do not threaten members with punishments or misuse staff status.",
        "11.7 — Do not fabricate, edit misleadingly, or hide evidence.",
        "11.8 — Staff members must follow the same community rules as everyone else.",
        "11.9 — If a staff member is involved in a dispute, another staff member should review it.",
        "11.10 — Private staff information and internal discussions must remain confidential.",
    ]),
    ("Punishments", [
        "12.1 — Standard escalation: 1 Warn ➜ Mute 1 Hour ➜ Mute 1 Day ➜ Kick ➜ Ban.",
        "12.2 — Every punishment must include a clear reason.",
        "12.3 — Screenshot or verifiable evidence must be saved for every punishment.",
        "12.4 — Staff should normally follow the escalation order for repeated minor violations.",
        "12.5 — Serious violations may receive an immediate stronger punishment.",
        "12.6 — Do not issue punishments based on rumors or personal dislike.",
        "12.7 — Incorrect punishments must be reviewed and corrected by authorized staff.",
        "12.8 — Members may appeal a punishment through the official support system.",
    ]),
    ("Security & Privacy", [
        "13.1 — Never share passwords, authentication codes, or account recovery details.",
        "13.2 — Do not publish another person's private or identifying information.",
        "13.3 — Do not send suspicious files, phishing links, or malicious downloads.",
        "13.4 — Report suspicious accounts, scams, or security issues to staff.",
        "13.5 — Do not attempt to access another member's account or private data.",
        "13.6 — Be careful with links and files sent by unknown users.",
        "13.7 — Do not use the server to coordinate scams or steal accounts.",
    ]),
]


def load_languages() -> Dict[str, str]:
    try:
        with open(LANGUAGE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def save_languages(data: Dict[str, str]) -> None:
    temporary = LANGUAGE_FILE + ".tmp"
    with open(temporary, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    os.replace(temporary, LANGUAGE_FILE)


def tr(language: str) -> dict:
    return I18N.get(language, I18N["en"])


def make_v2_container(*items, accent_colour=ACCENT_COLOR):
    return discord.ui.Container(*items, accent_colour=discord.Colour(accent_colour))


class RulesBaseView(discord.ui.LayoutView):
    def __init__(self, owner_id: int, timeout: int = VIEW_TIMEOUT):
        super().__init__(timeout=timeout)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                I18N["en"]["private_only"], ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        for item in self.walk_children():
            if hasattr(item, "disabled"):
                item.disabled = True
        # The original ephemeral response may no longer be editable after expiry.
        # Discord will automatically stop accepting the expired components.


class PublicLanguageView(discord.ui.LayoutView):
    def __init__(self, owner_id: int):
        super().__init__(timeout=180)
        self.owner_id = owner_id

        intro = discord.ui.TextDisplay(
            f"## {I18N['en']['choose_language']}\n"
            f"{I18N['en']['language_hint']}\n\n"
            "Select one of the 12 available languages below."
        )
        separator = discord.ui.Separator()
        select = LanguageSelect(owner_id)
        row = discord.ui.ActionRow(select)
        self.add_item(make_v2_container(intro, separator, row))

    async def on_timeout(self):
        for item in self.walk_children():
            if hasattr(item, "disabled"):
                item.disabled = True


class LanguageSelect(discord.ui.Select):
    def __init__(self, owner_id: int):
        self.owner_id = owner_id
        options = [
            discord.SelectOption(label=label.split(" ", 1)[1], value=code, emoji=label.split(" ", 1)[0])
            for code, label in LANGUAGES
        ]
        super().__init__(
            placeholder="Choose your language...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="rules:language",
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                I18N["en"]["private_only"], ephemeral=True
            )
            return

        language = self.values[0]
        languages = load_languages()
        languages[str(interaction.user.id)] = language
        try:
            save_languages(languages)
        except OSError:
            logging.exception("Could not save rules language preference.")

        view = RulesPanelView(interaction.user.id, language)
        await interaction.response.send_message(
            view=view,
            ephemeral=True,
        )


class CategorySelect(discord.ui.Select):
    def __init__(self, parent_view: "RulesPanelView"):
        self.parent_view = parent_view
        lang = tr(parent_view.language)
        options = []
        for index, category_name in enumerate(lang["category_names"]):
            options.append(
                discord.SelectOption(
                    label=category_name[:100],
                    value=str(index),
                    description=f"Category {index + 1} • {len(RULES[index][1])} rules",
                )
            )
        super().__init__(
            placeholder=lang["select_placeholder"],
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"rules:category:{parent_view.owner_id}",
        )

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.selected_category = int(self.values[0])
        self.parent_view.page = 0
        await self.parent_view.refresh(interaction)


class RulesPanelView(RulesBaseView):
    def __init__(self, owner_id: int, language: str):
        super().__init__(owner_id)
        self.language = language if language in I18N else "en"
        self.selected_category = -1
        self.page = 0
        self.add_item(self.build_container())

    def build_container(self):
        lang = tr(self.language)
        children = [
            discord.ui.TextDisplay(f"# 📜 {lang['title']}"),
            discord.ui.TextDisplay(lang["language_saved"]),
            discord.ui.TextDisplay(lang["subtitle"]),
            discord.ui.Separator(),
            discord.ui.TextDisplay(f"### {lang['choose_category']}\n{lang['category_hint']}"),
            discord.ui.ActionRow(CategorySelect(self)),
            discord.ui.Separator(),
        ]

        if self.selected_category == -1:
            children.append(
                discord.ui.TextDisplay(
                    "## 📚 RULE CATEGORIES\n" +
                    "\n".join(
                        f"**{index + 1}.** {lang['category_names'][index]}"
                        for index in range(len(RULES))
                    )
                )
            )
            children.append(discord.ui.Separator())
            children.append(discord.ui.TextDisplay(
                f"### 🛡️ {lang['staff_note']}\n{lang['staff_text']}"
            ))
            children.append(discord.ui.TextDisplay(
                f"### ⚠️ {lang['punishment']}\n{lang['punishment_text']}"
            ))
        else:
            category_index = self.selected_category
            category_title = lang["category_names"][category_index]
            rules = RULES[category_index][1]
            per_page = 8
            total_pages = max(1, (len(rules) + per_page - 1) // per_page)
            self.page = max(0, min(self.page, total_pages - 1))
            start = self.page * per_page
            current_rules = rules[start:start + per_page]
            body = "\n\n".join(current_rules)

            children.append(discord.ui.TextDisplay(
                f"## {category_title}\n\n{body}"
            ))
            if category_index == 10:
                children.append(discord.ui.Separator())
                children.append(discord.ui.TextDisplay(
                    f"### 🛡️ {lang['staff_note']}\n{lang['staff_text']}"
                ))
            if category_index == 11:
                children.append(discord.ui.Separator())
                children.append(discord.ui.TextDisplay(
                    f"### ⚠️ {lang['punishment']}\n{lang['punishment_text']}"
                ))
            children.append(discord.ui.Separator())
            children.append(discord.ui.TextDisplay(
                f"-# {lang['page']} {self.page + 1}/{total_pages}"
            ))

            nav = discord.ui.ActionRow()
            nav.add_item(BackToCategoriesButton(self))
            if self.page > 0:
                nav.add_item(PreviousPageButton(self))
            if self.page < total_pages - 1:
                nav.add_item(NextPageButton(self))
            children.append(nav)

        return make_v2_container(*children)

    async def refresh(self, interaction: discord.Interaction):
        self.clear_items()
        self.add_item(self.build_container())
        await interaction.response.edit_message(view=self)

    async def on_timeout(self):
        self.clear_items()


class BackToCategoriesButton(discord.ui.Button):
    def __init__(self, parent_view: RulesPanelView):
        self.parent_view = parent_view
        super().__init__(
            style=discord.ButtonStyle.secondary,
            emoji="↩️",
            custom_id=f"rules:back:{parent_view.owner_id}",
        )

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.selected_category = -1
        self.parent_view.page = 0
        await self.parent_view.refresh(interaction)


class PreviousPageButton(discord.ui.Button):
    def __init__(self, parent_view: RulesPanelView):
        self.parent_view = parent_view
        super().__init__(
            style=discord.ButtonStyle.secondary,
            emoji="⬅️",
            custom_id=f"rules:previous:{parent_view.owner_id}",
        )

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.page -= 1
        await self.parent_view.refresh(interaction)


class NextPageButton(discord.ui.Button):
    def __init__(self, parent_view: RulesPanelView):
        self.parent_view = parent_view
        super().__init__(
            style=discord.ButtonStyle.secondary,
            emoji="➡️",
            custom_id=f"rules:next:{parent_view.owner_id}",
        )

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.page += 1
        await self.parent_view.refresh(interaction)


class Rules(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        content = message.content.strip().lower()

        if content == "!rules":
            if message.author.id != OWNER_ID:
                return

            try:
                await message.delete()
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                pass

            try:
                await message.channel.send(view=PublicLanguageView(message.author.id))
            except discord.HTTPException:
                logging.exception("Could not send rules language selector.")
            return

        # Separate help command to avoid silently changing the existing !commands System handler.
        if content == "!commands Rules" or content == "!commands rules":
            if message.author.id != OWNER_ID:
                return
            try:
                await message.delete()
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                pass
            await message.channel.send(
                "## 📜 RULES SYSTEM\n"
                "`!rules` — Open the private server rules panel."
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Rules(bot))
