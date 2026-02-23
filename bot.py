import os
import requests
import time
import random
import re
import json

TOKEN = os.getenv('BOT_TOKEN')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://fragment.com",
    "Referer": "https://fragment.com/gifts",
}

FEMALE_NAMES = [
    "anna","kate","maria","nastya","lena","olga","yulia","natasha","sasha","dasha",
    "masha","sonya","anya","vika","alina","kristina","polina","irina","sveta","tanya",
    "kseniya","diana","elena","vera","lisa","ksenia","katya","ira","olesya","milana",
    "sofia","valeriya","valeria","camilla","amina","aisha","girl","woman","lady",
    "princess","queen","babe","beauty","angel","cute","baby","kira","zara","mila"
]

user_states = {}
user_temp = {}
cache = {}
collections_cache = None

# ===== FRAGMENT API =====
def fragment_request(params):
    """Делает POST запрос к Fragment API"""
    try:
        r = requests.post(
            "https://fragment.com/api",
            data=params,
            headers=HEADERS,
            timeout=20
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"Fragment API error: {e}")
    return {}

def get_all_collections():
    """Получает все коллекции подарков"""
    global collections_cache
    if collections_cache:
        return collections_cache
    data = fragment_request({
        "type": "gifts",
        "count": 200
    })
    cols = data.get("gifts", {}).get("items", [])
    if not cols:
        # Пробуем другой формат
        data = fragment_request({
            "method": "getGifts",
            "count": 200
        })
        cols = data.get("items", [])
    collections_cache = cols
    return cols

def get_gift_owners(slug, count=100, filter_type="sale"):
    """Получает владельцев NFT из конкретной коллекции"""
    if slug in cache:
        return cache[slug]

    owners = []
    # Пробуем несколько форматов запроса
    formats = [
        {"type": "gifts", "slug": slug, "count": count, "filter": filter_type},
        {"type": "getGifts", "collection": slug, "count": count},
        {"slug": slug, "type": "gifts", "count": count, "filter": "sale", "sort": "price_asc"},
        {"method": "gifts.getItems", "slug": slug, "count": count},
    ]

    for params in formats:
        try:
            data = fragment_request(params)
            items = (data.get("items") or
                     data.get("gifts", {}).get("items") or
                     data.get("html", ""))

            if isinstance(items, list) and items:
                for item in items:
                    username = (item.get("username") or
                               item.get("owner_username") or
                               item.get("tg_username") or "")
                    name = item.get("name", "")
                    num = item.get("num", item.get("number", ""))
                    price = item.get("price", 0)
                    attrs = item.get("attributes", item.get("attrs", {}))
                    model = attrs.get("model", attrs.get("Model", "")) if isinstance(attrs, dict) else ""
                    backdrop = attrs.get("backdrop", attrs.get("Backdrop", "")) if isinstance(attrs, dict) else ""
                    symbol = attrs.get("symbol", attrs.get("Symbol", "")) if isinstance(attrs, dict) else ""

                    owners.append({
                        "username": username,
                        "name": name,
                        "num": num,
                        "price": price,
                        "model": model,
                        "backdrop": backdrop,
                        "symbol": symbol,
                        "slug": slug
                    })
                if owners:
                    break

            # Если вернулся HTML — парсим
            if isinstance(items, str) and len(items) > 100:
                owners = parse_html_for_owners(items, slug)
                if owners:
                    break
        except Exception as e:
            print(f"Format error {params}: {e}")
            continue

    # Если ничего не получили через API — парсим HTML страницу
    if not owners:
        owners = scrape_collection_page(slug, count)

    cache[slug] = owners
    return owners

def scrape_collection_page(slug, count=100):
    """Парсит HTML страницу коллекции на fragment.com"""
    owners = []
    try:
        r = requests.get(
            f"https://fragment.com/gifts/{slug}",
            params={"sort": "price_asc", "filter": "sale"},
            headers={**HEADERS,
                     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                     "X-Requested-With": ""},
            timeout=20
        )
        if r.status_code == 200:
            owners = parse_html_for_owners(r.text, slug)
    except Exception as e:
        print(f"Scrape error {slug}: {e}")
    return owners

def parse_html_for_owners(html, slug):
    """Парсит HTML Fragment в поисках юзернеймов"""
    owners = []
    try:
        # Ищем JSON данные в скрипте
        patterns = [
            r'initData\s*=\s*({.+?});\s*(?:\n|var )',
            r'pageData\s*=\s*({.+?});\s*(?:\n|var )',
            r'"items"\s*:\s*(\[.+?\])\s*[,}]',
            r'var gifts\s*=\s*({.+?});\s*\n',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    obj = json.loads(match.group(1))
                    items = obj if isinstance(obj, list) else obj.get("items", [])
                    for item in items:
                        username = item.get("username", item.get("owner", {}).get("username", ""))
                        owners.append({
                            "username": username,
                            "name": item.get("name", ""),
                            "num": item.get("num", ""),
                            "price": item.get("price", 0),
                            "model": item.get("model", ""),
                            "backdrop": item.get("backdrop", ""),
                            "symbol": item.get("symbol", ""),
                            "slug": slug
                        })
                    if owners:
                        break
                except:
                    pass

        # Ищем юзернеймы прямо в HTML через regex
        if not owners:
            # t.me/username ссылки
            usernames = re.findall(r'(?:t\.me|tg://resolve\?domain=)/([a-zA-Z0-9_]{5,})', html)
            # data-username атрибуты
            usernames += re.findall(r'data-(?:username|owner)=["\']([a-zA-Z0-9_]{5,})["\']', html)
            seen = set()
            for u in usernames:
                if u not in seen and u.lower() not in ['fragment', 'gifts', 'auction']:
                    seen.add(u)
                    owners.append({"username": u, "name": "", "num": "", "price": 0,
                                  "model": "", "backdrop": "", "symbol": "", "slug": slug})
    except Exception as e:
        print(f"Parse HTML error: {e}")
    return owners

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
    data = {"chat_id": chat_id, "message_id": message_id,
            "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if buttons is not None:
        data["reply_markup"] = {"inline_keyboard": buttons}
    tg_request("editMessageText", data)

def answer_callback(callback_id, text=None):
    d = {"callback_query_id": callback_id}
    if text:
        d["text"] = text
    tg_request("answerCallbackQuery", d)

def is_female(username, name):
    text = (username + " " + name).lower()
    return any(n in text for n in FEMALE_NAMES)

def format_results(results, page, label):
    per_page = 10
    total_pages = max(1, (len(results) + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    chunk = results[start:start + per_page]

    text = (
        f"🎯 <b>Результаты поиска</b>\n"
        f"📊 Найдено: <b>{len(results)}</b> пользователей\n"
        f"🎯 Режим: {label}\n\n"
    )
    for i, item in enumerate(chunk, start + 1):
        u = item.get("username", "")
        if u:
            text += f"{i}. @{u} | <a href='https://t.me/{u}'>Написать</a>\n"
        else:
            text += f"{i}. {item.get('name', '—')}\n"

    text += f"\n📊 Страница {page}/{total_pages}"

    nav = []
    if page > 1:
        nav.append({"text": "⬅️", "callback_data": f"page_{page-1}"})
    nav.append({"text": f"{page}/{total_pages}", "callback_data": "noop"})
    if page < total_pages:
        nav.append({"text": "➡️", "callback_data": f"page_{page+1}"})

    buttons = []
    if nav:
        buttons.append(nav)
    buttons.append([{"text": "🔄 Искать снова", "callback_data": "main_menu"}])
    buttons.append([{"text": "🏠 Главное меню", "callback_data": "main_menu"}])
    return text, buttons

# Все известные коллекции
KNOWN_SLUGS = [
    "astralshard", "sakuraflower", "homemadecake", "cookieheart",
    "vintagecigar", "plushpepe", "eternalcandle", "boxingglove",
    "toncrystal", "bunnyear", "sharpetongue", "venomouspot",
    "lovepotion", "evileve", "lolpop", "signetring",
    "tophat", "kissedlips", "bdaycandle", "jesterlol",
    "minioscars", "spunkysprite", "hearteyecat"
]

def get_all_owners():
    all_owners = []
    for slug in KNOWN_SLUGS:
        items = get_gift_owners(slug)
        all_owners.extend(items)
        time.sleep(0.5)
    return all_owners

def send_main_menu(chat_id, message_id=None):
    text = (
        "🔍 <b>Выберите тип поиска:</b>\n\n"
        "🎲 <b>Рандом поиск</b> — по режимам (легкий, средний, жирный)\n"
        "🎯 <b>Поиск по модели</b> — по конкретной модели NFT\n"
        "👱‍♀️ <b>Поиск девушек</b> — по женским именам\n"
        "📦 <b>По коллекции</b> — все владельцы коллекции"
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
            "Выбери тип поиска и получи список юзернеймов с кнопкой Написать!")
        send_main_menu(chat_id)

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
            "mode_easy":   ("🟢 Легкий режим",  0,   3),
            "mode_medium": ("🟡 Средний режим", 3,  15),
            "mode_hard":   ("🔴 Жирный режим",  15, 600),
        }
        label, min_t, max_t = modes[data]
        user_temp[user_id] = {"label": label, "min_t": min_t, "max_t": max_t}
        edit_inline(chat_id, message_id,
            f"✅ <b>Выбран режим: {label}</b>\n💰 Диапазон: {min_t}–{max_t} TON\n\nНажми чтобы начать поиск:",
            [
                [{"text": "🔍 Начать поиск NFT", "callback_data": "do_random"}],
                [{"text": "◀️ Назад", "callback_data": "random_search"}],
                [{"text": "🏠 Меню", "callback_data": "main_menu"}]
            ]
        )
        return

    if data == "do_random":
        label = user_temp.get(user_id, {}).get("label", "🟡 Средний режим")
        min_t = user_temp.get(user_id, {}).get("min_t", 3)
        max_t = user_temp.get(user_id, {}).get("max_t", 15)
        edit_inline(chat_id, message_id, "⏳ <b>Парсю Fragment.com...</b>", [])
        all_owners = get_all_owners()
        results = []
        seen = set()
        for item in all_owners:
            u = item.get("username", "")
            if not u:
                continue
            try:
                price = float(str(item.get("price", 0)).replace(",", "").replace(" TON", ""))
            except:
                price = 0
            if min_t <= price <= max_t and u not in seen:
                seen.add(u)
                results.append(item)
        random.shuffle(results)
        user_temp[user_id].update({"results": results, "page": 1})
        if not results:
            edit_inline(chat_id, message_id,
                f"❌ <b>Юзернеймов в режиме {label} не найдено.</b>\n\nFragment мог заблокировать запрос — попробуй позже.",
                [[{"text": "🔄 Повторить", "callback_data": "do_random"}],
                 [{"text": "◀️ Назад", "callback_data": "random_search"}]]
            )
            return
        text, buttons = format_results(results, 1, label)
        edit_inline(chat_id, message_id, text, buttons)
        return

    if data == "col_search":
        buttons = [[{"text": s, "callback_data": f"col_{s}"}] for s in KNOWN_SLUGS[:12]]
        buttons.append([{"text": "◀️ Назад", "callback_data": "main_menu"}])
        edit_inline(chat_id, message_id, "<b>📦 Выбери коллекцию:</b>", buttons)
        return

    if data.startswith("col_"):
        slug = data[4:]
        edit_inline(chat_id, message_id, f"⏳ <b>Парсю {slug} с Fragment...</b>", [])
        items = get_gift_owners(slug)
        results = [i for i in items if i.get("username")]
        user_temp[user_id] = {"results": results, "page": 1, "label": f"📦 {slug}"}
        if not results:
            edit_inline(chat_id, message_id,
                f"❌ Юзернеймов в коллекции {slug} не найдено.\nFragment мог заблокировать запрос.",
                [[{"text": "🔄 Повторить", "callback_data": data}],
                 [{"text": "◀️ Назад", "callback_data": "col_search"}]]
            )
            return
        text, buttons = format_results(results, 1, f"📦 {slug}")
        edit_inline(chat_id, message_id, text, buttons)
        return

    if data == "model_search":
        buttons = [[{"text": s, "callback_data": f"msel_{s}"}] for s in KNOWN_SLUGS[:12]]
        buttons.append([{"text": "◀️ Назад", "callback_data": "main_menu"}])
        edit_inline(chat_id, message_id, "<b>🎯 Выбери коллекцию для поиска по модели:</b>", buttons)
        return

    if data.startswith("msel_"):
        slug = data[5:]
        edit_inline(chat_id, message_id, f"⏳ <b>Загружаю {slug}...</b>", [])
        items = get_gift_owners(slug)
        models = sorted(set(i.get("model","") for i in items if i.get("model")))
        if not models:
            edit_inline(chat_id, message_id,
                f"❌ Модели не найдены в {slug}.",
                [[{"text": "◀️ Назад", "callback_data": "model_search"}]]
            )
            return
        user_temp[user_id] = {"col_slug": slug, "col_items": items}
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
        edit_inline(chat_id, message_id, f"<b>🎯 {slug}</b>\nВыбери модель:", buttons)
        return

    if data.startswith("mod_"):
        model = data[4:]
        items = user_temp.get(user_id, {}).get("col_items", [])
        slug = user_temp.get(user_id, {}).get("col_slug", "")
        results = [i for i in items if i.get("model") == model and i.get("username")]
        user_temp[user_id].update({"results": results, "page": 1, "label": f"🎯 {slug} | {model}"})
        if not results:
            edit_inline(chat_id, message_id,
                f"❌ Владельцев с моделью «{model}» не найдено.",
                [[{"text": "◀️ Назад", "callback_data": f"msel_{slug}"}]]
            )
            return
        text, buttons = format_results(results, 1, f"🎯 {slug} | {model}")
        edit_inline(chat_id, message_id, text, buttons)
        return

    if data == "girl_search":
        edit_inline(chat_id, message_id,
            "👱‍♀️ <b>Поиск девушек</b>\n\nИщу NFT владельцев с женскими именами...\n\nНажми чтобы начать:",
            [
                [{"text": "🔍 Начать поиск", "callback_data": "do_girl"}],
                [{"text": "◀️ Назад", "callback_data": "main_menu"}]
            ]
        )
        return

    if data == "do_girl":
        edit_inline(chat_id, message_id, "⏳ <b>Ищу девушек...</b>", [])
        all_owners = get_all_owners()
        results = []
        seen = set()
        for item in all_owners:
            u = item.get("username", "")
            n = item.get("name", "")
            if u and is_female(u, n) and u not in seen:
                seen.add(u)
                results.append(item)
        random.shuffle(results)
        user_temp[user_id] = {"results": results, "page": 1, "label": "👱‍♀️ Девушки"}
        if not results:
            edit_inline(chat_id, message_id,
                "❌ Девушек не найдено. Fragment мог заблокировать запрос.",
                [[{"text": "🔄 Повторить", "callback_data": "do_girl"}],
                 [{"text": "🏠 Меню", "callback_data": "main_menu"}]]
            )
            return
        text, buttons = format_results(results, 1, "👱‍♀️ Девушки")
        edit_inline(chat_id, message_id, text, buttons)
        return

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
            r = requests.get(
                f"https://api.telegram.org/bot{TOKEN}/getUpdates",
                params={"offset": offset, "timeout": 30}, timeout=35
            )
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
