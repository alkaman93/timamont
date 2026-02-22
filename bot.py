import os
import requests
import time
import random

TOKEN = os.getenv('BOT_TOKEN')
CHANNEL = os.getenv('CHANNEL_USERNAME', '@GiftExchangers')  # канал для обязательной подписки
TON_API = "https://tonapi.io/v2"
TON_API_KEY = os.getenv('TON_API_KEY', '')

COLLECTIONS = {
    "gem_signets":      {"name": "💎 Gem Signets",      "address": "EQAqtF5tZIgNZal80ChzdPMvZCN8OEbJCVJPn_0xNPghQJPW"},
    "signet_rings":     {"name": "💍 Signet Rings",     "address": "EQCrGA9slCoksgD-NyRDjtHySKN0Ts8k6hdueJkUkZZdD4_K"},
    "stellar_rockets":  {"name": "🚀 Stellar Rockets",  "address": "EQDIruSTyxvq60gUH8j2kkj3qzoBrBaJy9WkKbeNNRasWe4j"},
    "love_potions":     {"name": "🧪 Love Potions",     "address": "EQD7yDu2WCgd9Uzx1dF_DQkWK7IZJJ4Mp9M9g1rGUUiQE43m"},
    "lol_pops":         {"name": "🍭 Lol Pops",         "address": "EQC6zjid8vJNEWqcXk10XjsdDLRKbcPZzbHusuEW6FokOWIm"},
    "ton_gifts":        {"name": "🎁 TON Gifts",        "address": "EQBpMhoMDsN0DjQZXFFBup7l5gbt-UtMzTHN5qaqQtc90CLD"},
}

# Имена которые считаются женскими для поиска девушек
FEMALE_NAMES = [
    "anna","kate","maria","nastya","lena","olga","yulia","natasha","sasha","dasha",
    "masha","sonya","anya","vika","alina","kristina","polina","irina","sveta","tanya",
    "kseniya","diana","elena","vera","lisa","xenia","ksenia","katya","ira","olesya",
    "milana","sofiya","sofia","valeriya","valeria","camilla","kamilla","amina","aisha",
    "girl","girls","woman","lady","female","she","her","princess","queen","babe"
]

user_states = {}
user_temp = {}
cache = {}

# ===== TG =====
def tg_request(method, data):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    try:
        r = requests.post(url, json=data, timeout=10)
        return r.json()
    except Exception as e:
        print(f"TG error: {e}")
        return None

def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if reply_markup:
        data["reply_markup"] = reply_markup
    return tg_request("sendMessage", data)

def send_inline(chat_id, text, buttons):
    return tg_request("sendMessage", {
        "chat_id": chat_id, "text": text,
        "reply_markup": {"inline_keyboard": buttons},
        "parse_mode": "HTML", "disable_web_page_preview": True
    })

def edit_inline(chat_id, message_id, text, buttons=None):
    data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if buttons is not None:
        data["reply_markup"] = {"inline_keyboard": buttons}
    tg_request("editMessageText", data)

def answer_callback(callback_id, text=None):
    data = {"callback_query_id": callback_id}
    if text:
        data["text"] = text
    tg_request("answerCallbackQuery", data)

def check_subscription(user_id):
    try:
        r = tg_request("getChatMember", {"chat_id": CHANNEL, "user_id": user_id})
        if r and r.get("ok"):
            status = r["result"].get("status", "")
            return status in ["member", "administrator", "creator"]
    except:
        pass
    return False

def main_keyboard():
    return {"keyboard": [
        [{"text": "🎲 Рандом поиск"}, {"text": "🎯 Поиск по модели"}],
        [{"text": "👱‍♀️ Поиск девушек"}, {"text": "📊 Статистика"}],
        [{"text": "🏠 Главное меню"}]
    ], "resize_keyboard": True}

# ===== TON API =====
def ton_headers():
    h = {"Accept": "application/json"}
    if TON_API_KEY:
        h["Authorization"] = f"Bearer {TON_API_KEY}"
    return h

def load_collection(address, limit=500):
    all_items = []
    offset = 0
    while len(all_items) < limit:
        try:
            r = requests.get(f"{TON_API}/nfts/collections/{address}/items",
                params={"limit": 100, "offset": offset}, headers=ton_headers(), timeout=20)
            if r.status_code != 200:
                break
            items = r.json().get("nft_items", [])
            if not items:
                break
            all_items.extend(items)
            if len(items) < 100:
                break
            offset += 100
            time.sleep(0.3)
        except Exception as e:
            print(f"TON error: {e}")
            break
    return all_items

def get_nft_price(item):
    """Пытается получить цену NFT в TON"""
    try:
        sale = item.get("sale", {})
        if sale:
            price = sale.get("price", {})
            if price:
                val = int(price.get("value", 0))
                return val / 1e9  # nanotons -> TON
    except:
        pass
    return 0

def get_owner_info(item):
    owner = item.get("owner", {})
    username = ""
    name = ""
    address = ""
    if owner:
        user_info = owner.get("user", {})
        if user_info:
            username = user_info.get("username", "")
            name = user_info.get("name", "")
        address = owner.get("address", "")
    return username, name, address

def parse_attrs(item):
    meta = item.get("metadata", {})
    return {a["trait_type"]: str(a["value"]) for a in meta.get("attributes", [])}

def get_all_nfts():
    """Загружает все NFT из всех коллекций с кэшированием"""
    all_items = []
    for key, col in COLLECTIONS.items():
        if key not in cache:
            items = load_collection(col["address"])
            cache[key] = items
        all_items.extend(cache[key])
    return all_items

def is_female(username, name):
    text = (username + " " + name).lower()
    return any(n in text for n in FEMALE_NAMES)

def format_results_page(results, page, mode_label):
    per_page = 10
    total_pages = max(1, (len(results) + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    chunk = results[start:start+per_page]

    text = (
        f"🎯 <b>Результаты поиска</b>\n"
        f"📊 Найдено: <b>{len(results)}</b> пользователей\n"
        f"🎯 Режим: {mode_label}\n\n"
    )
    for i, item in enumerate(chunk, start+1):
        username, name, address = item["username"], item["name"], item["address"]
        if username:
            text += f"{i}. @{username} | <a href='https://t.me/{username}'>Написать</a>\n"
        else:
            short = address[:8] + "..." if address else "???"
            text += f"{i}. <code>{short}</code>\n"

    text += f"\n📊 Страница {page}/{total_pages}"

    buttons = []
    nav = []
    if page > 1:
        nav.append({"text": "⬅️ Назад", "callback_data": f"page_{page-1}"})
    nav.append({"text": f"{page}/{total_pages}", "callback_data": "noop"})
    if page < total_pages:
        nav.append({"text": "➡️ Вперед", "callback_data": f"page_{page+1}"})
    if nav:
        buttons.append(nav)
    buttons.append([{"text": "🔄 Искать снова", "callback_data": "main_search"}])
    buttons.append([{"text": "🏠 Главное меню", "callback_data": "main_menu"}])

    return text, buttons

# ===== HANDLERS =====
def send_subscription_request(chat_id):
    send_inline(chat_id,
        f"🔒 <b>Для использования бота необходимо подписаться на канал!</b>\n\n"
        f"После подписки нажми кнопку ниже.\n\n"
        f"<b>Примечание:</b> Если вы уже подали заявку, пожалуйста, подождите пока её примут.\n"
        f"Кнопка '✅ Я подписался' заработает только после принятия заявки.",
        [
            [{"text": "📢 Подписаться на канал", "url": f"https://t.me/{CHANNEL.lstrip('@')}"}],
            [{"text": "✅ Я подписался", "callback_data": "check_sub"}]
        ]
    )

def send_main_menu(chat_id):
    send_inline(chat_id,
        "🔍 <b>Выберите тип поиска:</b>\n\n"
        "🎲 <b>Рандом поиск</b> - поиск по режимам (легкий, средний, жирный)\n"
        "🎯 <b>Поиск по модели</b> - точный поиск по конкретным NFT\n"
        "👱‍♀️ <b>Поиск девушек</b> - поиск по женским именам",
        [
            [{"text": "🎲 Рандом поиск", "callback_data": "random_search"}],
            [{"text": "🎯 Поиск по модели", "callback_data": "model_search"}],
            [{"text": "👱‍♀️ Поиск девушек", "callback_data": "girl_search"}],
            [{"text": "🏠 Главное меню", "callback_data": "main_menu"}]
        ]
    )

def handle_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    user_id = message["from"]["id"]

    if text == "/start":
        user_states.pop(user_id, None)
        user_temp.pop(user_id, None)
        send_main_menu(chat_id)
        return

    if text == "🏠 Главное меню":
        send_main_menu(chat_id)
        return

    if text == "🎲 Рандом поиск":
        tg_request("sendMessage", {
            "chat_id": chat_id,
            "text": (
                "🎯 <b>Выберите режим поиска:</b>\n\n"
                "🟢 <b>Легкий режим</b>\n"
                "Недорогие подарки до 3 TON\n"
                "Самые неопытные пользователи\n\n"
                "🟡 <b>Средний режим</b>\n"
                "Хорошие подарки от 3 до 15 TON\n"
                "Более опытные пользователи\n\n"
                "🔴 <b>Жирный режим</b>\n"
                "Дорогие подарки от 15 до 600 TON\n"
                "Опытные коллекционеры"
            ),
            "parse_mode": "HTML",
            "reply_markup": {"inline_keyboard": [
                [{"text": "🟢 Легкий режим", "callback_data": "mode_easy"}],
                [{"text": "🟡 Средний режим", "callback_data": "mode_medium"}],
                [{"text": "🔴 Жирный режим", "callback_data": "mode_hard"}],
                [{"text": "🏠 Главное меню", "callback_data": "main_menu"}]
            ]}
        })
        return

    if text == "🎯 Поиск по модели":
        tg_request("sendMessage", {
            "chat_id": chat_id,
            "text": "🎯 <b>Выберите коллекцию для поиска по модели:</b>",
            "parse_mode": "HTML",
            "reply_markup": {"inline_keyboard": [
                [{"text": col["name"], "callback_data": f"model_col_{key}"}]
                for key, col in COLLECTIONS.items()
            ] + [[{"text": "🏠 Главное меню", "callback_data": "main_menu"}]]}
        })
        return

    if text == "👱‍♀️ Поиск девушек":
        send_inline(chat_id,
            "👱‍♀️ <b>Поиск девушек</b>\n\n"
            "Ищу владельцев NFT с женскими именами в юзернейме или имени...\n\n"
            "✅ Выбран режим: 👱‍♀️ Поиск девушек\n"
            "📝 Шаблон: По женским именам\n\n"
            "Нажмите кнопку ниже чтобы начать поиск:",
            [
                [{"text": "🔍 Начать поиск NFT", "callback_data": "do_girl_search"}],
                [{"text": "🏠 Главное меню", "callback_data": "main_menu"}]
            ]
        )
        return

    if text == "📊 Статистика":
        total_cached = sum(len(v) for v in cache.values())
        send_message(chat_id,
            f"📊 <b>Статистика бота</b>\n\n"
            f"🗂 Коллекций: {len(COLLECTIONS)}\n"
            f"📦 NFT в кэше: {total_cached}\n"
            f"👥 Активных сессий: {len(user_states)}"
        )
        return

def handle_callback(callback):
    callback_id = callback["id"]
    chat_id = callback["message"]["chat"]["id"]
    message_id = callback["message"]["message_id"]
    data = callback["data"]
    user_id = callback["from"]["id"]

    answer_callback(callback_id)

    if data == "noop":
        return

    # Проверка подписки


    if data == "main_menu":
        edit_inline(chat_id, message_id,
            "🔍 <b>Выберите тип поиска:</b>\n\n"
            "🎲 <b>Рандом поиск</b> - поиск по режимам (легкий, средний, жирный)\n"
            "🎯 <b>Поиск по модели</b> - точный поиск по конкретным NFT\n"
            "👱‍♀️ <b>Поиск девушек</b> - поиск по женским именам",
            [
                [{"text": "🎲 Рандом поиск", "callback_data": "random_search"}],
                [{"text": "🎯 Поиск по модели", "callback_data": "model_search"}],
                [{"text": "👱‍♀️ Поиск девушек", "callback_data": "girl_search"}],
            ]
        )
        return

    if data == "main_search":
        edit_inline(chat_id, message_id,
            "🔍 <b>Выберите тип поиска:</b>",
            [
                [{"text": "🎲 Рандом поиск", "callback_data": "random_search"}],
                [{"text": "🎯 Поиск по модели", "callback_data": "model_search"}],
                [{"text": "👱‍♀️ Поиск девушек", "callback_data": "girl_search"}],
            ]
        )
        return

    if data == "random_search":
        edit_inline(chat_id, message_id,
            "🎯 <b>Выберите режим поиска:</b>\n\n"
            "🟢 <b>Легкий режим</b>\nНедорогие подарки до 3 TON\nСамые неопытные пользователи\n\n"
            "🟡 <b>Средний режим</b>\nХорошие подарки от 3 до 15 TON\nБолее опытные пользователи\n\n"
            "🔴 <b>Жирный режим</b>\nДорогие подарки от 15 до 600 TON\nОпытные коллекционеры",
            [
                [{"text": "🟢 Легкий режим", "callback_data": "mode_easy"}],
                [{"text": "🟡 Средний режим", "callback_data": "mode_medium"}],
                [{"text": "🔴 Жирный режим", "callback_data": "mode_hard"}],
                [{"text": "◀️ Назад", "callback_data": "main_menu"}]
            ]
        )
        return

    if data in ["mode_easy", "mode_medium", "mode_hard"]:
        modes = {
            "mode_easy":   ("🟢 Легкий режим",  0,  3),
            "mode_medium": ("🟡 Средний режим", 3,  15),
            "mode_hard":   ("🔴 Жирный режим",  15, 600),
        }
        label, min_ton, max_ton = modes[data]
        user_temp[user_id] = {"mode": data, "label": label, "min_ton": min_ton, "max_ton": max_ton}

        edit_inline(chat_id, message_id,
            f"✅ <b>Выбран режим: {label}</b>\n"
            f"📝 Шаблон: Стандартный\n\n"
            f"Нажмите кнопку ниже чтобы начать поиск:",
            [
                [{"text": "🔍 Начать поиск NFT", "callback_data": "do_random_search"}],
                [{"text": "◀️ Назад к режимам", "callback_data": "random_search"}],
                [{"text": "🏠 Главное меню", "callback_data": "main_menu"}]
            ]
        )
        return

    if data == "do_random_search":
        label = user_temp.get(user_id, {}).get("label", "🟡 Средний режим")
        min_ton = user_temp.get(user_id, {}).get("min_ton", 3)
        max_ton = user_temp.get(user_id, {}).get("max_ton", 15)

        edit_inline(chat_id, message_id, "⏳ <b>Загружаю NFT и ищу пользователей...</b>", [])

        all_items = get_all_nfts()
        results = []
        for item in all_items:
            price = get_nft_price(item)
            username, name, address = get_owner_info(item)
            if not username:
                continue
            if min_ton <= price <= max_ton:
                results.append({"username": username, "name": name, "address": address, "price": price})

        # Дедупликация по юзернейму
        seen = set()
        unique = []
        for r in results:
            if r["username"] not in seen:
                seen.add(r["username"])
                unique.append(r)

        random.shuffle(unique)
        user_temp[user_id]["results"] = unique
        user_temp[user_id]["page"] = 1

        if not unique:
            edit_inline(chat_id, message_id,
                f"❌ <b>Ничего не найдено в режиме {label}</b>\n\nПопробуй другой режим.",
                [
                    [{"text": "🔄 Другой режим", "callback_data": "random_search"}],
                    [{"text": "🏠 Главное меню", "callback_data": "main_menu"}]
                ]
            )
            return

        text, buttons = format_results_page(unique, 1, label)
        edit_inline(chat_id, message_id, text, buttons)
        return

    if data == "model_search":
        edit_inline(chat_id, message_id,
            "🎯 <b>Выберите коллекцию для поиска по модели:</b>",
            [[{"text": col["name"], "callback_data": f"model_col_{key}"}]
             for key, col in COLLECTIONS.items()] +
            [[{"text": "◀️ Назад", "callback_data": "main_menu"}]]
        )
        return

    if data.startswith("model_col_"):
        col_key = data[10:]
        col = COLLECTIONS.get(col_key)
        if not col:
            return

        edit_inline(chat_id, message_id, f"⏳ <b>Загружаю {col['name']}...</b>", [])

        if col_key not in cache:
            items = load_collection(col["address"])
            cache[col_key] = items
        else:
            items = cache[col_key]

        # Собираем уникальные модели
        models = set()
        for item in items:
            attrs = parse_attrs(item)
            model = attrs.get("Model") or attrs.get("model") or attrs.get("Name") or attrs.get("name")
            if model:
                models.add(model)

        if not models:
            edit_inline(chat_id, message_id,
                f"❌ Атрибуты не найдены в коллекции {col['name']}",
                [[{"text": "◀️ Назад", "callback_data": "model_search"}]]
            )
            return

        user_temp[user_id] = {"col_key": col_key, "items": items}

        buttons = []
        row = []
        for m in sorted(models)[:20]:
            row.append({"text": m, "callback_data": f"select_model_{m}"})
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([{"text": "◀️ Назад", "callback_data": "model_search"}])

        edit_inline(chat_id, message_id,
            f"<b>{col['name']}</b>\nВыбери модель NFT:",
            buttons
        )
        return

    if data.startswith("select_model_"):
        model_name = data[13:]
        items = user_temp.get(user_id, {}).get("items", [])
        col_key = user_temp.get(user_id, {}).get("col_key", "")
        col_name = COLLECTIONS.get(col_key, {}).get("name", "")

        results = []
        seen = set()
        for item in items:
            attrs = parse_attrs(item)
            item_model = attrs.get("Model") or attrs.get("model") or attrs.get("Name") or attrs.get("name") or ""
            if item_model == model_name:
                username, name, address = get_owner_info(item)
                if username and username not in seen:
                    seen.add(username)
                    results.append({"username": username, "name": name, "address": address})

        user_temp[user_id]["results"] = results
        user_temp[user_id]["page"] = 1

        if not results:
            edit_inline(chat_id, message_id,
                f"❌ Владельцев NFT «{model_name}» с юзернеймами не найдено.",
                [[{"text": "◀️ Назад", "callback_data": f"model_col_{col_key}"}]]
            )
            return

        label = f"🎯 {col_name} | {model_name}"
        text, buttons = format_results_page(results, 1, label)
        edit_inline(chat_id, message_id, text, buttons)
        return

    if data == "girl_search":
        edit_inline(chat_id, message_id,
            "👱‍♀️ <b>Поиск девушек</b>\n\n"
            "Ищу NFT владельцев с женскими именами в профиле...\n\n"
            "✅ Выбран режим: 👱‍♀️ Поиск девушек\n"
            "📝 Шаблон: По женским именам\n\n"
            "Нажмите кнопку ниже чтобы начать поиск:",
            [
                [{"text": "🔍 Начать поиск NFT", "callback_data": "do_girl_search"}],
                [{"text": "◀️ Назад", "callback_data": "main_menu"}]
            ]
        )
        return

    if data == "do_girl_search":
        edit_inline(chat_id, message_id, "⏳ <b>Ищу девушек среди владельцев NFT...</b>", [])

        all_items = get_all_nfts()
        results = []
        seen = set()
        for item in all_items:
            username, name, address = get_owner_info(item)
            if not username:
                continue
            if is_female(username, name) and username not in seen:
                seen.add(username)
                results.append({"username": username, "name": name, "address": address})

        random.shuffle(results)
        user_temp[user_id] = {"results": results, "page": 1}

        if not results:
            edit_inline(chat_id, message_id,
                "❌ <b>Девушек не найдено.</b>\n\nПопробуй позже — база обновляется.",
                [
                    [{"text": "🔄 Попробовать снова", "callback_data": "do_girl_search"}],
                    [{"text": "🏠 Главное меню", "callback_data": "main_menu"}]
                ]
            )
            return

        label = "👱‍♀️ Поиск девушек"
        text, buttons = format_results_page(results, 1, label)
        edit_inline(chat_id, message_id, text, buttons)
        return

    if data.startswith("page_"):
        page = int(data[5:])
        results = user_temp.get(user_id, {}).get("results", [])
        label = user_temp.get(user_id, {}).get("label", "🔍 Поиск")
        if not results:
            return
        text, buttons = format_results_page(results, page, label)
        edit_inline(chat_id, message_id, text, buttons)
        return

def main():
    print("NFT Parser Bot started!")
    tg_request("deleteWebhook", {})
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            r = requests.get(url, params={"offset": offset, "timeout": 30}, timeout=35)
            if r.status_code == 200:
                data = r.json()
                if data.get("ok"):
                    for update in data["result"]:
                        offset = update["update_id"] + 1
                        if "message" in update:
                            try: handle_message(update["message"])
                            except Exception as e: print(f"Err msg: {e}")
                        elif "callback_query" in update:
                            try: handle_callback(update["callback_query"])
                            except Exception as e: print(f"Err cb: {e}")
            time.sleep(0.3)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
