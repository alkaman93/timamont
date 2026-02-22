import os
import requests
import time
import random
import json

TOKEN = os.getenv('BOT_TOKEN')

# Fragment scraper — имитирует запросы браузера к fragment.com
FRAGMENT_URL = "https://fragment.com/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://fragment.com/gifts",
    "Origin": "https://fragment.com",
}

# Известные slug коллекций Telegram подарков
GIFT_COLLECTIONS = {
    "astralshard":      "🔮 Astral Shard",
    "sakuraflower":     "🌸 Sakura Flower",
    "homemadecake":     "🎂 Homemade Cake",
    "cookieheart":      "🍪 Cookie Heart",
    "vintagecigar":     "🚬 Vintage Cigar",
    "plushpepe":        "🐸 Plush Pepe",
    "eternitycandl":    "🕯 Eternity Candle",
    "boxingglove":      "🥊 Boxing Glove",
    "toncrystal":       "💎 TON Crystal",
    "bunnyear":         "🐰 Bunny Ear",
    "sharpetongue":     "😈 Sharp Tongue",
    "venomouspot":      "☠️ Venomous Pot",
    "lovepotion":       "🧪 Love Potion",
    "evileve":          "🧿 Evil Eve",
    "lolpop":           "🍭 Lol Pop",
    "signetring":       "💍 Signet Ring",
    "tophat":           "🎩 Top Hat",
    "kissedlips":       "💋 Kissed Lips",
}

user_states = {}
user_temp = {}
cache = {}  # {collection_slug: [{"username":..., "name":..., "num":..., "model":..., "backdrop":..., "symbol":...}]}

FEMALE_NAMES = [
    "anna","kate","maria","nastya","lena","olga","yulia","natasha","sasha","dasha",
    "masha","sonya","anya","vika","alina","kristina","polina","irina","sveta","tanya",
    "kseniya","diana","elena","vera","lisa","xenia","ksenia","katya","ira","olesya",
    "milana","sofia","valeriya","valeria","camilla","kamilla","amina","aisha",
    "girl","woman","lady","princess","queen","babe","beauty","angel","cute","baby"
]

# ===== FRAGMENT SCRAPER =====
def fetch_fragment_gifts(collection_slug, count=100):
    """Парсит владельцев NFT подарков с fragment.com"""
    results = []
    try:
        # Fragment использует POST запрос к своему API
        payload = {
            "type": "gifts",
            "query": f"collection:{collection_slug}",
            "count": count,
            "sort": "price_asc"
        }
        r = requests.post(
            FRAGMENT_URL,
            data={"query": json.dumps(payload)},
            headers=HEADERS,
            timeout=15
        )
        if r.status_code == 200:
            try:
                data = r.json()
                items = data.get("items", data.get("gifts", []))
                for item in items:
                    username = item.get("owner_username", item.get("username", ""))
                    name = item.get("owner_name", item.get("name", ""))
                    num = item.get("num", item.get("number", ""))
                    attrs = item.get("attributes", {})
                    model = attrs.get("Model", attrs.get("model", ""))
                    backdrop = attrs.get("Backdrop", attrs.get("backdrop", ""))
                    symbol = attrs.get("Symbol", attrs.get("symbol", ""))
                    price = item.get("price", 0)
                    if username or name:
                        results.append({
                            "username": username,
                            "name": name,
                            "num": num,
                            "model": model,
                            "backdrop": backdrop,
                            "symbol": symbol,
                            "price": price,
                            "collection": collection_slug
                        })
            except:
                pass
    except Exception as e:
        print(f"Fragment error: {e}")

    # Если fragment не дал данные — пробуем через прямой скрапинг страницы
    if not results:
        results = scrape_fragment_page(collection_slug, count)

    return results

def scrape_fragment_page(collection_slug, count=50):
    """Скрапит страницу fragment.com/gifts/collection"""
    results = []
    try:
        r = requests.get(
            f"https://fragment.com/gifts/{collection_slug}",
            headers={**HEADERS, "Accept": "text/html,application/xhtml+xml"},
            timeout=15
        )
        if r.status_code == 200:
            text = r.text
            # Ищем JSON с данными в HTML
            import re
            # Fragment вставляет данные в JS переменную
            match = re.search(r'var\s+pageData\s*=\s*({.+?});\s*\n', text, re.DOTALL)
            if match:
                try:
                    page_data = json.loads(match.group(1))
                    items = page_data.get("items", [])
                    for item in items:
                        username = item.get("username", "")
                        name = item.get("name", "")
                        results.append({
                            "username": username,
                            "name": name,
                            "num": item.get("num", ""),
                            "model": item.get("model", ""),
                            "backdrop": item.get("backdrop", ""),
                            "symbol": item.get("symbol", ""),
                            "price": item.get("price", 0),
                            "collection": collection_slug
                        })
                except:
                    pass
    except Exception as e:
        print(f"Scrape error: {e}")
    return results

def get_all_collections_nfts():
    """Загружает NFT из всех коллекций"""
    all_items = []
    for slug in GIFT_COLLECTIONS:
        if slug in cache:
            all_items.extend(cache[slug])
        else:
            items = fetch_fragment_gifts(slug, count=200)
            cache[slug] = items
            all_items.extend(items)
            time.sleep(1)
    return all_items

def filter_by_price(items, min_ton, max_ton):
    result = []
    seen = set()
    for item in items:
        price = float(item.get("price", 0))
        username = item.get("username", "")
        if not username:
            continue
        if min_ton <= price <= max_ton and username not in seen:
            seen.add(username)
            result.append(item)
    return result

def is_female(username, name):
    text = (username + " " + name).lower()
    return any(n in text for n in FEMALE_NAMES)

# ===== TELEGRAM =====
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

def format_results(results, page, label):
    per_page = 10
    total_pages = max(1, (len(results) + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    chunk = results[start:start+per_page]

    text = (
        f"🎯 <b>Результаты поиска</b>\n"
        f"📊 Найдено: <b>{len(results)}</b> пользователей\n"
        f"🎯 Режим: {label}\n\n"
    )
    for i, item in enumerate(chunk, start+1):
        u = item.get("username", "")
        if u:
            text += f"{i}. @{u} | <a href='https://t.me/{u}'>Написать</a>\n"
        else:
            text += f"{i}. {item.get('name', '—')}\n"

    text += f"\n📊 Страница {page}/{total_pages}"

    nav = []
    if page > 1:
        nav.append({"text": "⬅️ Назад", "callback_data": f"page_{page-1}"})
    nav.append({"text": f"{page}/{total_pages}", "callback_data": "noop"})
    if page < total_pages:
        nav.append({"text": "➡️ Вперед", "callback_data": f"page_{page+1}"})

    buttons = []
    if nav:
        buttons.append(nav)
    buttons.append([{"text": "🔄 Искать снова", "callback_data": "main_menu"}])
    buttons.append([{"text": "🏠 Главное меню", "callback_data": "main_menu"}])
    return text, buttons

def send_main_menu(chat_id, message_id=None):
    text = (
        "🔍 <b>Выберите тип поиска:</b>\n\n"
        "🎲 <b>Рандом поиск</b> — поиск по режимам (легкий, средний, жирный)\n"
        "🎯 <b>Поиск по модели</b> — точный поиск по конкретным NFT\n"
        "👱‍♀️ <b>Поиск девушек</b> — поиск по женским именам\n"
        "📦 <b>По коллекции</b> — все владельцы конкретной коллекции"
    )
    buttons = [
        [{"text": "🎲 Рандом поиск", "callback_data": "random_search"}],
        [{"text": "🎯 Поиск по модели", "callback_data": "model_search"}],
        [{"text": "👱‍♀️ Поиск девушек", "callback_data": "girl_search"}],
        [{"text": "📦 По коллекции", "callback_data": "col_search"}],
    ]
    if message_id:
        edit_inline(chat_id, message_id, text, buttons)
    else:
        send_inline(chat_id, text, buttons)

# ===== HANDLERS =====
def handle_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    user_id = message["from"]["id"]

    if text == "/start":
        user_states.pop(user_id, None)
        user_temp.pop(user_id, None)
        send_message(chat_id,
            "<b>🎁 NFT Gift Parser</b>\n\n"
            "Парсю владельцев NFT подарков Telegram с Fragment.com\n\n"
            "Выбери тип поиска и получи список с юзернеймами и кнопкой Написать!",
        )
        send_main_menu(chat_id)
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

    if data == "main_menu":
        send_main_menu(chat_id, message_id)
        return

    # Рандом поиск
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
        user_temp[user_id] = {"label": label, "min_ton": min_ton, "max_ton": max_ton}

        edit_inline(chat_id, message_id,
            f"✅ <b>Выбран режим: {label}</b>\n"
            f"💰 Диапазон: {min_ton} — {max_ton} TON\n\n"
            f"Нажмите кнопку ниже чтобы начать поиск:",
            [
                [{"text": "🔍 Начать поиск NFT", "callback_data": "do_random"}],
                [{"text": "◀️ Назад к режимам", "callback_data": "random_search"}],
                [{"text": "🏠 Главное меню", "callback_data": "main_menu"}]
            ]
        )
        return

    if data == "do_random":
        label = user_temp.get(user_id, {}).get("label", "🟡 Средний режим")
        min_ton = user_temp.get(user_id, {}).get("min_ton", 3)
        max_ton = user_temp.get(user_id, {}).get("max_ton", 15)

        edit_inline(chat_id, message_id, "⏳ <b>Парсю Fragment.com, подожди...</b>", [])

        all_items = get_all_collections_nfts()
        results = filter_by_price(all_items, min_ton, max_ton)
        random.shuffle(results)

        user_temp[user_id]["results"] = results
        user_temp[user_id]["page"] = 1

        if not results:
            edit_inline(chat_id, message_id,
                f"❌ <b>Ничего не найдено в режиме {label}</b>\n\nFragment может блокировать запросы. Попробуй позже.",
                [
                    [{"text": "🔄 Попробовать снова", "callback_data": "do_random"}],
                    [{"text": "◀️ Другой режим", "callback_data": "random_search"}]
                ]
            )
            return

        text, buttons = format_results(results, 1, label)
        edit_inline(chat_id, message_id, text, buttons)
        return

    # Поиск по коллекции
    if data == "col_search":
        buttons = [[{"text": name, "callback_data": f"col_{slug}"}]
                   for slug, name in GIFT_COLLECTIONS.items()]
        buttons.append([{"text": "◀️ Назад", "callback_data": "main_menu"}])
        edit_inline(chat_id, message_id, "<b>📦 Выбери коллекцию:</b>", buttons)
        return

    if data.startswith("col_"):
        slug = data[4:]
        col_name = GIFT_COLLECTIONS.get(slug, slug)
        edit_inline(chat_id, message_id, f"⏳ <b>Парсю {col_name} с Fragment...</b>", [])

        if slug not in cache:
            items = fetch_fragment_gifts(slug, count=200)
            cache[slug] = items
        else:
            items = cache[slug]

        results = [i for i in items if i.get("username")]
        user_temp[user_id] = {"results": results, "page": 1, "label": f"📦 {col_name}"}

        if not results:
            edit_inline(chat_id, message_id,
                f"❌ <b>Владельцы с юзернеймами не найдены в {col_name}</b>\n\nFragment может блокировать запросы.",
                [
                    [{"text": "🔄 Попробовать снова", "callback_data": data}],
                    [{"text": "◀️ Назад", "callback_data": "col_search"}]
                ]
            )
            return

        text, buttons = format_results(results, 1, f"📦 {col_name}")
        edit_inline(chat_id, message_id, text, buttons)
        return

    # Поиск по модели
    if data == "model_search":
        buttons = [[{"text": name, "callback_data": f"msel_{slug}"}]
                   for slug, name in GIFT_COLLECTIONS.items()]
        buttons.append([{"text": "◀️ Назад", "callback_data": "main_menu"}])
        edit_inline(chat_id, message_id, "<b>🎯 Выбери коллекцию для поиска по модели:</b>", buttons)
        return

    if data.startswith("msel_"):
        slug = data[5:]
        col_name = GIFT_COLLECTIONS.get(slug, slug)
        edit_inline(chat_id, message_id, f"⏳ <b>Загружаю {col_name}...</b>", [])

        if slug not in cache:
            items = fetch_fragment_gifts(slug, count=200)
            cache[slug] = items
        else:
            items = cache[slug]

        models = sorted(set(i.get("model","") for i in items if i.get("model")))

        if not models:
            edit_inline(chat_id, message_id,
                f"❌ Модели не найдены в {col_name}",
                [[{"text": "◀️ Назад", "callback_data": "model_search"}]]
            )
            return

        user_temp[user_id] = {"col_slug": slug, "col_items": items, "col_name": col_name}
        buttons = []
        row = []
        for m in models[:20]:
            row.append({"text": m, "callback_data": f"mod_{m}"})
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([{"text": "◀️ Назад", "callback_data": "model_search"}])

        edit_inline(chat_id, message_id, f"<b>🎯 {col_name}</b>\nВыбери модель:", buttons)
        return

    if data.startswith("mod_"):
        model = data[4:]
        items = user_temp.get(user_id, {}).get("col_items", [])
        col_name = user_temp.get(user_id, {}).get("col_name", "")
        results = [i for i in items if i.get("model") == model and i.get("username")]
        user_temp[user_id]["results"] = results
        user_temp[user_id]["page"] = 1
        label = f"🎯 {col_name} | {model}"

        if not results:
            edit_inline(chat_id, message_id,
                f"❌ Владельцев с моделью «{model}» и юзернеймом не найдено.",
                [[{"text": "◀️ Назад", "callback_data": "model_search"}]]
            )
            return

        text, buttons = format_results(results, 1, label)
        edit_inline(chat_id, message_id, text, buttons)
        return

    # Поиск девушек
    if data == "girl_search":
        edit_inline(chat_id, message_id,
            "👱‍♀️ <b>Поиск девушек</b>\n\n"
            "Ищу NFT владельцев с женскими именами...\n\n"
            "✅ Режим: 👱‍♀️ Поиск девушек\n\n"
            "Нажми кнопку чтобы начать:",
            [
                [{"text": "🔍 Начать поиск", "callback_data": "do_girl"}],
                [{"text": "◀️ Назад", "callback_data": "main_menu"}]
            ]
        )
        return

    if data == "do_girl":
        edit_inline(chat_id, message_id, "⏳ <b>Ищу девушек среди NFT владельцев...</b>", [])
        all_items = get_all_collections_nfts()
        results = []
        seen = set()
        for item in all_items:
            u = item.get("username", "")
            n = item.get("name", "")
            if u and is_female(u, n) and u not in seen:
                seen.add(u)
                results.append(item)
        random.shuffle(results)
        user_temp[user_id] = {"results": results, "page": 1, "label": "👱‍♀️ Поиск девушек"}

        if not results:
            edit_inline(chat_id, message_id,
                "❌ <b>Девушек не найдено.</b>\n\nFragment может блокировать запросы. Попробуй позже.",
                [
                    [{"text": "🔄 Попробовать снова", "callback_data": "do_girl"}],
                    [{"text": "🏠 Меню", "callback_data": "main_menu"}]
                ]
            )
            return

        text, buttons = format_results(results, 1, "👱‍♀️ Поиск девушек")
        edit_inline(chat_id, message_id, text, buttons)
        return

    # Пагинация
    if data.startswith("page_"):
        page = int(data[5:])
        results = user_temp.get(user_id, {}).get("results", [])
        label = user_temp.get(user_id, {}).get("label", "🔍 Поиск")
        if not results:
            return
        user_temp[user_id]["page"] = page
        text, buttons = format_results(results, page, label)
        edit_inline(chat_id, message_id, text, buttons)
        return

def main():
    print("NFT Parser started!")
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
                            except Exception as e: print(f"Err: {e}")
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
