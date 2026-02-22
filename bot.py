import os
import requests
import time
import random
import json
import re

TOKEN = os.getenv('BOT_TOKEN')
STEL_SSID = os.getenv('STEL_SSID')  # Получи из браузера: fragment.com -> DevTools -> Network -> Cookies -> stel_ssid

FRAGMENT_API = "https://fragment.com/api"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://fragment.com/gifts",
    "Origin": "https://fragment.com",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}

# Актуальные коллекции с Fragment.com
GIFT_COLLECTIONS = {
    "astralshard":    "🔮 Astral Shards",
    "sakuraflower":   "🌸 Sakura Flowers",
    "homemadecake":   "🎂 Homemade Cakes",
    "cookieheart":    "🍪 Cookie Hearts",
    "vintagecigar":   "🚬 Vintage Cigars",
    "plushpepe":      "🐸 Plush Pepes",
    "eternalcandle":  "🕯 Eternal Candles",
    "lolpop":         "🍭 Lol Pops",
    "signetring":     "💍 Signet Rings",
    "tophat":         "🎩 Top Hats",
    "evileye":        "🧿 Evil Eyes",
    "lovepotion":     "🧪 Love Potions",
    "durovscap":      "🧢 Durov's Caps",
    "heartlocket":    "💛 Heart Lockets",
    "diamondring":    "💎 Diamond Rings",
    "swisswatch":     "⌚ Swiss Watches",
    "toybear":        "🧸 Toy Bears",
    "witchhat":       "🎃 Witch Hats",
    "snoopdogg":      "🎤 Snoop Doggs",
    "lootbag":        "💰 Loot Bags",
}

FEMALE_NAMES = [
    "anna","kate","maria","nastya","lena","olga","yulia","natasha","sasha","dasha",
    "masha","sonya","anya","vika","alina","kristina","polina","irina","sveta","tanya",
    "kseniya","diana","elena","vera","lisa","xenia","ksenia","katya","ira","olesya",
    "milana","sofia","valeriya","valeria","camilla","kamilla","amina","aisha",
    "girl","woman","lady","princess","queen","babe","beauty","angel","cute","baby",
    "mia","emma","luna","sara","nina","rita","zara","lola","nora","rosa",
]

user_states = {}
user_temp = {}
cache = {}  # {slug: [items]}

# ─── FRAGMENT API ──────────────────────────────────────────────────────────────

def get_fragment_hash():
    """Получает актуальный hash для API из главной страницы Fragment"""
    try:
        r = requests.get(
            "https://fragment.com/gifts",
            headers={**HEADERS, "Accept": "text/html"},
            cookies={"stel_ssid": STEL_SSID} if STEL_SSID else {},
            timeout=15
        )
        match = re.search(r'api\?hash=([a-f0-9]+)', r.text)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"Hash fetch error: {e}")
    return "6bc2314d461dbf7309"  # fallback hash

def fragment_request(method, params):
    """Делает запрос к Fragment API"""
    hash_val = get_fragment_hash()
    url = f"{FRAGMENT_API}?hash={hash_val}"
    
    data = {"method": method, **params}
    
    cookies = {}
    if STEL_SSID:
        cookies["stel_ssid"] = STEL_SSID

    try:
        r = requests.post(url, data=data, headers=HEADERS, cookies=cookies, timeout=20)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"Fragment request error: {e}")
    return None

def fetch_collection_gifts(slug, count=120, sort="price_asc", filter_type=""):
    """
    Получает NFT из коллекции через Fragment API.
    Возвращает список items с username, name, num, price, ссылками.
    """
    results = []
    
    # Метод 1: Fragment API searchGifts
    payload = {
        "type": "searchGifts",
        "collection": slug,
        "count": count,
        "sort": sort,
    }
    if filter_type:
        payload["filter"] = filter_type

    response = fragment_request("searchGifts", payload)
    
    if response and response.get("ok"):
        items = response.get("gifts", response.get("items", []))
        for item in items:
            results.append(parse_gift_item(item, slug))
    
    # Метод 2: Прямой scrape страницы коллекции
    if not results:
        results = scrape_collection_page(slug, count, sort)
    
    return results

def parse_gift_item(item, slug):
    """Парсит один NFT item в единый формат"""
    num = item.get("num", item.get("number", item.get("gift_id", "")))
    
    # Информация о владельце
    owner = item.get("owner", {})
    if isinstance(owner, dict):
        username = owner.get("username", owner.get("name", ""))
        owner_name = owner.get("name", owner.get("title", ""))
        owner_id = owner.get("id", "")
    else:
        username = item.get("owner_username", item.get("username", ""))
        owner_name = item.get("owner_name", item.get("name", ""))
        owner_id = ""

    # Цена
    price_raw = item.get("price", 0)
    if isinstance(price_raw, dict):
        price = float(price_raw.get("amount", 0)) / 1e9  # наноTON -> TON
    else:
        price = float(price_raw) if price_raw else 0

    # Атрибуты NFT
    attrs = item.get("attributes", item.get("attrs", {}))
    if isinstance(attrs, list):
        attrs = {a.get("name", ""): a.get("value", "") for a in attrs}

    # Статус (продается / продано / на аукционе)
    status = item.get("status", "")
    is_sale = status in ("", "sale", "for_sale") or item.get("sale")
    is_auction = status == "auction" or item.get("auction")

    # Ссылки
    nft_slug = f"{slug}-{num}"
    fragment_link = f"https://fragment.com/gift/{nft_slug}"
    
    # Профиль владельца
    profile_link = ""
    if username:
        clean_u = username.lstrip("@")
        profile_link = f"https://t.me/{clean_u}"
    elif owner_id:
        profile_link = f"https://t.me/+{owner_id}"

    return {
        "username": username.lstrip("@") if username else "",
        "owner_name": owner_name,
        "owner_id": owner_id,
        "num": num,
        "price": price,
        "model": attrs.get("Model", attrs.get("model", "")),
        "backdrop": attrs.get("Backdrop", attrs.get("backdrop", "")),
        "symbol": attrs.get("Symbol", attrs.get("symbol", "")),
        "status": status,
        "is_sale": is_sale,
        "is_auction": is_auction,
        "collection": slug,
        "nft_link": fragment_link,
        "profile_link": profile_link,
    }

def scrape_collection_page(slug, count=50, sort="price_asc"):
    """Резервный: скрапит HTML страницу коллекции"""
    results = []
    try:
        params = {"sort": sort}
        r = requests.get(
            f"https://fragment.com/gifts/{slug}",
            params=params,
            headers={**HEADERS, "Accept": "text/html,application/xhtml+xml"},
            cookies={"stel_ssid": STEL_SSID} if STEL_SSID else {},
            timeout=20
        )
        if r.status_code != 200:
            return results

        text = r.text

        # Ищем JSON-данные внутри HTML (Fragment вставляет их в <script>)
        patterns = [
            r'initData\s*\(\s*({.+?})\s*\)',
            r'Gifts\s*\(\s*({.+?})\s*\)',
            r'"gifts"\s*:\s*(\[.+?\])(?=\s*[,}])',
            r'"items"\s*:\s*(\[.+?\])(?=\s*[,}])',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if not match:
                continue
            try:
                raw = match.group(1)
                if raw.startswith('['):
                    items = json.loads(raw)
                else:
                    parsed = json.loads(raw)
                    items = (parsed.get("gifts") or parsed.get("items") or 
                             parsed.get("nfts") or [])
                
                for item in items[:count]:
                    results.append(parse_gift_item(item, slug))
                
                if results:
                    print(f"Scraped {len(results)} items from HTML for {slug}")
                    return results
            except Exception as parse_err:
                print(f"Parse error ({slug}): {parse_err}")
                continue

    except Exception as e:
        print(f"Scrape error ({slug}): {e}")
    
    return results

def get_all_collections_nfts():
    """Загружает NFT из всех коллекций (с кешем)"""
    all_items = []
    for slug in GIFT_COLLECTIONS:
        if slug in cache and cache[slug]:
            all_items.extend(cache[slug])
        else:
            items = fetch_collection_gifts(slug, count=200)
            cache[slug] = items
            all_items.extend(items)
            time.sleep(0.8)
    return all_items

def filter_by_price(items, min_ton, max_ton):
    result = []
    seen = set()
    for item in items:
        price = item.get("price", 0)
        username = item.get("username", "")
        nft_link = item.get("nft_link", "")
        if not (username or nft_link):
            continue
        if min_ton <= price <= max_ton:
            key = username or nft_link
            if key not in seen:
                seen.add(key)
                result.append(item)
    return result

def is_female(username, name):
    text = (username + " " + name).lower()
    return any(n in text for n in FEMALE_NAMES)

# ─── TELEGRAM ─────────────────────────────────────────────────────────────────

def tg_request(method, data):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    try:
        r = requests.post(url, json=data, timeout=10)
        return r.json()
    except Exception as e:
        print(f"TG error: {e}")
        return None

def send_message(chat_id, text, reply_markup=None):
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        data["reply_markup"] = reply_markup
    return tg_request("sendMessage", data)

def send_inline(chat_id, text, buttons):
    return tg_request("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {"inline_keyboard": buttons},
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    })

def edit_inline(chat_id, message_id, text, buttons=None):
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if buttons is not None:
        data["reply_markup"] = {"inline_keyboard": buttons}
    tg_request("editMessageText", data)

def answer_callback(callback_id, text=None):
    data = {"callback_query_id": callback_id}
    if text:
        data["text"] = text
    tg_request("answerCallbackQuery", data)

# ─── ФОРМАТИРОВАНИЕ РЕЗУЛЬТАТОВ ───────────────────────────────────────────────

def format_results(results, page, label):
    per_page = 8
    total_pages = max(1, (len(results) + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    chunk = results[start:start + per_page]

    col_name = GIFT_COLLECTIONS.get(
        chunk[0].get("collection", "") if chunk else "",
        ""
    )

    text = (
        f"🎯 <b>Результаты поиска</b>\n"
        f"📊 Найдено: <b>{len(results)}</b> NFT\n"
        f"🔍 Режим: {label}\n\n"
    )

    for i, item in enumerate(chunk, start + 1):
        username = item.get("username", "")
        owner_name = item.get("owner_name", "")
        num = item.get("num", "")
        price = item.get("price", 0)
        collection = item.get("collection", "")
        nft_link = item.get("nft_link", "")
        profile_link = item.get("profile_link", "")
        model = item.get("model", "")
        col_display = GIFT_COLLECTIONS.get(collection, collection)

        # Строка NFT
        nft_label = f"{col_display} #{num}" if num else col_display
        price_str = f"{price:.1f} TON" if price else "—"

        text += f"<b>{i}.</b> "

        # Ссылка на NFT
        if nft_link:
            text += f'<a href="{nft_link}">🎁 {nft_label}</a>'
        else:
            text += f"🎁 {nft_label}"

        if model:
            text += f" | {model}"
        text += f" | 💰 {price_str}\n"

        # Ссылка на профиль владельца
        if username:
            text += f"   👤 <a href='https://t.me/{username}'>@{username}</a>"
            if profile_link:
                text += f" | <a href='https://t.me/{username}'>Написать</a>"
        elif owner_name:
            text += f"   👤 {owner_name}"
            if profile_link:
                text += f" | <a href='{profile_link}'>Открыть</a>"
        else:
            text += "   👤 <i>Нет юзернейма</i>"
        
        text += "\n\n"

    text += f"📄 Страница {page}/{total_pages}"

    # Навигация
    nav = []
    if page > 1:
        nav.append({"text": "⬅️", "callback_data": f"page_{page - 1}"})
    nav.append({"text": f"{page}/{total_pages}", "callback_data": "noop"})
    if page < total_pages:
        nav.append({"text": "➡️", "callback_data": f"page_{page + 1}"})

    buttons = []
    if nav:
        buttons.append(nav)
    buttons.append([{"text": "🔄 Обновить", "callback_data": "noop"}])
    buttons.append([{"text": "🏠 Главное меню", "callback_data": "main_menu"}])
    return text, buttons

def send_main_menu(chat_id, message_id=None):
    text = (
        "🎁 <b>NFT Gift Parser — Fragment.com</b>\n\n"
        "Выбери режим поиска:\n\n"
        "🎲 <b>Рандом</b> — по диапазону цены (TON)\n"
        "📦 <b>По коллекции</b> — все NFT из конкретной коллекции\n"
        "🎯 <b>По модели</b> — точный поиск по редкости\n"
        "👱‍♀️ <b>Девушки</b> — поиск по женским именам\n"
        "🏷 <b>На продаже</b> — только выставленные на продажу"
    )
    buttons = [
        [{"text": "🎲 Рандом поиск", "callback_data": "random_search"}],
        [{"text": "📦 По коллекции", "callback_data": "col_search"}],
        [{"text": "🎯 По модели", "callback_data": "model_search"}],
        [{"text": "👱‍♀️ Поиск девушек", "callback_data": "girl_search"}],
        [{"text": "🏷 На продаже сейчас", "callback_data": "forsale_search"}],
        [{"text": "🗑 Сбросить кеш", "callback_data": "clear_cache"}],
    ]
    if message_id:
        edit_inline(chat_id, message_id, text, buttons)
    else:
        send_inline(chat_id, text, buttons)

# ─── HANDLERS ─────────────────────────────────────────────────────────────────

def handle_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    user_id = message["from"]["id"]

    if text == "/start":
        user_states.pop(user_id, None)
        user_temp.pop(user_id, None)
        send_message(
            chat_id,
            "🎁 <b>NFT Gift Parser</b>\n\n"
            "Парсю владельцев NFT подарков Telegram с Fragment.com\n"
            "Получай ссылки на NFT и профили владельцев!\n\n"
            "⚠️ <b>Важно:</b> Для работы нужна переменная <code>STEL_SSID</code>\n"
            "Получи её из браузера: fragment.com → DevTools → Network → Cookies"
        )
        send_main_menu(chat_id)
        return

    if text == "/cache":
        info = "\n".join(f"• {s}: {len(cache.get(s, []))} items" for s in GIFT_COLLECTIONS if s in cache)
        send_message(chat_id, f"📦 <b>Кеш:</b>\n{info or 'Пусто'}")
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

    if data == "clear_cache":
        cache.clear()
        edit_inline(chat_id, message_id, "✅ Кеш очищен!", [
            [{"text": "🏠 Главное меню", "callback_data": "main_menu"}]
        ])
        return

    # ── РАНДОМ ПОИСК ──────────────────────────────────────────────────────────
    if data == "random_search":
        edit_inline(chat_id, message_id,
            "🎯 <b>Выберите ценовой диапазон:</b>\n\n"
            "🟢 <b>Бюджетный</b> — до 3 TON\n"
            "🟡 <b>Средний</b> — 3–15 TON\n"
            "🔴 <b>Жирный</b> — 15–600 TON\n"
            "💎 <b>Элита</b> — от 600 TON",
            [
                [{"text": "🟢 До 3 TON", "callback_data": "mode_easy"}],
                [{"text": "🟡 3–15 TON", "callback_data": "mode_medium"}],
                [{"text": "🔴 15–600 TON", "callback_data": "mode_hard"}],
                [{"text": "💎 600+ TON", "callback_data": "mode_whale"}],
                [{"text": "◀️ Назад", "callback_data": "main_menu"}],
            ]
        )
        return

    if data in ["mode_easy", "mode_medium", "mode_hard", "mode_whale"]:
        modes = {
            "mode_easy":   ("🟢 Бюджетный (до 3 TON)",   0,    3),
            "mode_medium": ("🟡 Средний (3–15 TON)",      3,    15),
            "mode_hard":   ("🔴 Жирный (15–600 TON)",     15,   600),
            "mode_whale":  ("💎 Киты (600+ TON)",          600,  999999),
        }
        label, min_ton, max_ton = modes[data]
        user_temp[user_id] = {"label": label, "min_ton": min_ton, "max_ton": max_ton}
        edit_inline(chat_id, message_id,
            f"✅ Режим: <b>{label}</b>\nДиапазон: {min_ton}–{max_ton} TON\n\nНачать поиск?",
            [
                [{"text": "🔍 Начать поиск", "callback_data": "do_random"}],
                [{"text": "◀️ Назад", "callback_data": "random_search"}],
            ]
        )
        return

    if data == "do_random":
        label = user_temp.get(user_id, {}).get("label", "Поиск")
        min_ton = user_temp.get(user_id, {}).get("min_ton", 0)
        max_ton = user_temp.get(user_id, {}).get("max_ton", 15)
        edit_inline(chat_id, message_id, "⏳ <b>Парсю Fragment.com...</b>", [])
        all_items = get_all_collections_nfts()
        results = filter_by_price(all_items, min_ton, max_ton)
        random.shuffle(results)
        user_temp[user_id]["results"] = results
        user_temp[user_id]["page"] = 1
        if not results:
            edit_inline(chat_id, message_id,
                f"❌ <b>Ничего не найдено</b> в режиме {label}\n\n"
                "Возможные причины:\n"
                "• Не задан STEL_SSID (нужен для авторизации)\n"
                "• Fragment блокирует запросы\n"
                "• В этом диапазоне нет NFT с юзернеймами",
                [
                    [{"text": "🔄 Попробовать снова", "callback_data": "do_random"}],
                    [{"text": "◀️ Назад", "callback_data": "random_search"}],
                ]
            )
            return
        text, buttons = format_results(results, 1, label)
        edit_inline(chat_id, message_id, text, buttons)
        return

    # ── НА ПРОДАЖЕ ────────────────────────────────────────────────────────────
    if data == "forsale_search":
        buttons = [[{"text": name, "callback_data": f"sale_{slug}"}]
                   for slug, name in GIFT_COLLECTIONS.items()]
        buttons.append([{"text": "◀️ Назад", "callback_data": "main_menu"}])
        edit_inline(chat_id, message_id, "🏷 <b>Выбери коллекцию (только на продаже):</b>", buttons)
        return

    if data.startswith("sale_"):
        slug = data[5:]
        col_name = GIFT_COLLECTIONS.get(slug, slug)
        edit_inline(chat_id, message_id, f"⏳ Загружаю выставленные на продажу в <b>{col_name}</b>...", [])
        items = fetch_collection_gifts(slug, count=200, sort="price_asc", filter_type="sale")
        cache[slug] = items
        results = [i for i in items if i.get("username") or i.get("nft_link")]
        user_temp[user_id] = {"results": results, "page": 1, "label": f"🏷 {col_name} (продажа)"}
        if not results:
            edit_inline(chat_id, message_id,
                f"❌ Нет NFT на продаже в {col_name} или Fragment блокирует.",
                [[{"text": "◀️ Назад", "callback_data": "forsale_search"}]]
            )
            return
        text, buttons = format_results(results, 1, f"🏷 {col_name}")
        edit_inline(chat_id, message_id, text, buttons)
        return

    # ── ПО КОЛЛЕКЦИИ ──────────────────────────────────────────────────────────
    if data == "col_search":
        buttons = [[{"text": name, "callback_data": f"col_{slug}"}]
                   for slug, name in GIFT_COLLECTIONS.items()]
        buttons.append([{"text": "◀️ Назад", "callback_data": "main_menu"}])
        edit_inline(chat_id, message_id, "📦 <b>Выбери коллекцию:</b>", buttons)
        return

    if data.startswith("col_") and not data.startswith("col_search"):
        slug = data[4:]
        col_name = GIFT_COLLECTIONS.get(slug, slug)
        edit_inline(chat_id, message_id, f"⏳ Парсю <b>{col_name}</b>...", [])
        if slug not in cache or not cache[slug]:
            items = fetch_collection_gifts(slug, count=200)
            cache[slug] = items
        else:
            items = cache[slug]
        results = [i for i in items if i.get("username") or i.get("nft_link")]
        user_temp[user_id] = {"results": results, "page": 1, "label": f"📦 {col_name}"}
        if not results:
            edit_inline(chat_id, message_id,
                f"❌ <b>Нет данных для {col_name}</b>\n\n"
                "Нужен STEL_SSID для авторизации на Fragment.\n"
                "Получи его из браузера и добавь в .env",
                [
                    [{"text": "🔄 Попробовать снова", "callback_data": data}],
                    [{"text": "◀️ Назад", "callback_data": "col_search"}],
                ]
            )
            return
        text, buttons = format_results(results, 1, f"📦 {col_name}")
        edit_inline(chat_id, message_id, text, buttons)
        return

    # ── ПО МОДЕЛИ ─────────────────────────────────────────────────────────────
    if data == "model_search":
        buttons = [[{"text": name, "callback_data": f"msel_{slug}"}]
                   for slug, name in GIFT_COLLECTIONS.items()]
        buttons.append([{"text": "◀️ Назад", "callback_data": "main_menu"}])
        edit_inline(chat_id, message_id, "🎯 <b>Выбери коллекцию для поиска по модели:</b>", buttons)
        return

    if data.startswith("msel_"):
        slug = data[5:]
        col_name = GIFT_COLLECTIONS.get(slug, slug)
        edit_inline(chat_id, message_id, f"⏳ Загружаю {col_name}...", [])
        if slug not in cache or not cache[slug]:
            items = fetch_collection_gifts(slug, count=200)
            cache[slug] = items
        else:
            items = cache[slug]
        models = sorted(set(i.get("model", "") for i in items if i.get("model")))
        if not models:
            edit_inline(chat_id, message_id,
                f"❌ Модели не найдены в {col_name}. Нужен STEL_SSID.",
                [[{"text": "◀️ Назад", "callback_data": "model_search"}]]
            )
            return
        user_temp[user_id] = {"col_slug": slug, "col_items": items, "col_name": col_name}
        buttons = []
        row = []
        for m in models[:24]:
            row.append({"text": m, "callback_data": f"mod_{m}"})
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([{"text": "◀️ Назад", "callback_data": "model_search"}])
        edit_inline(chat_id, message_id, f"🎯 <b>{col_name}</b>\nВыбери модель:", buttons)
        return

    if data.startswith("mod_"):
        model = data[4:]
        items = user_temp.get(user_id, {}).get("col_items", [])
        col_name = user_temp.get(user_id, {}).get("col_name", "")
        results = [i for i in items if i.get("model") == model]
        user_temp[user_id]["results"] = results
        user_temp[user_id]["page"] = 1
        label = f"🎯 {col_name} | {model}"
        if not results:
            edit_inline(chat_id, message_id,
                f"❌ Не найдено NFT с моделью «{model}».",
                [[{"text": "◀️ Назад", "callback_data": "model_search"}]]
            )
            return
        text, buttons = format_results(results, 1, label)
        edit_inline(chat_id, message_id, text, buttons)
        return

    # ── ПОИСК ДЕВУШЕК ─────────────────────────────────────────────────────────
    if data == "girl_search":
        edit_inline(chat_id, message_id,
            "👱‍♀️ <b>Поиск девушек</b>\n\nИщу владельцев NFT с женскими именами...",
            [
                [{"text": "🔍 Начать поиск", "callback_data": "do_girl"}],
                [{"text": "◀️ Назад", "callback_data": "main_menu"}],
            ]
        )
        return

    if data == "do_girl":
        edit_inline(chat_id, message_id, "⏳ <b>Ищу девушек среди владельцев NFT...</b>", [])
        all_items = get_all_collections_nfts()
        results = []
        seen = set()
        for item in all_items:
            u = item.get("username", "")
            n = item.get("owner_name", "")
            if is_female(u, n):
                key = u or item.get("nft_link", "")
                if key and key not in seen:
                    seen.add(key)
                    results.append(item)
        random.shuffle(results)
        user_temp[user_id] = {"results": results, "page": 1, "label": "👱‍♀️ Девушки"}
        if not results:
            edit_inline(chat_id, message_id,
                "❌ <b>Девушек не найдено.</b>\nНужен STEL_SSID для загрузки данных.",
                [
                    [{"text": "🔄 Попробовать снова", "callback_data": "do_girl"}],
                    [{"text": "🏠 Меню", "callback_data": "main_menu"}],
                ]
            )
            return
        text, buttons = format_results(results, 1, "👱‍♀️ Девушки")
        edit_inline(chat_id, message_id, text, buttons)
        return

    # ── ПАГИНАЦИЯ ─────────────────────────────────────────────────────────────
    if data.startswith("page_"):
        page = int(data[5:])
        results = user_temp.get(user_id, {}).get("results", [])
        label = user_temp.get(user_id, {}).get("label", "Поиск")
        if not results:
            return
        user_temp[user_id]["page"] = page
        text, buttons = format_results(results, page, label)
        edit_inline(chat_id, message_id, text, buttons)
        return

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("NFT Gift Parser Bot started!")
    if not TOKEN:
        print("ERROR: BOT_TOKEN не задан!")
        return
    if not STEL_SSID:
        print("WARNING: STEL_SSID не задан — данные с Fragment будут пустыми!")
        print("Получи stel_ssid из браузера: fragment.com -> DevTools -> Network -> Cookies")
    print("=" * 50)

    tg_request("deleteWebhook", {})
    offset = 0

    while True:
        try:
            r = requests.get(
                f"https://api.telegram.org/bot{TOKEN}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=35
            )
            if r.status_code == 200:
                data = r.json()
                if data.get("ok"):
                    for update in data["result"]:
                        offset = update["update_id"] + 1
                        if "message" in update:
                            try:
                                handle_message(update["message"])
                            except Exception as e:
                                print(f"Message error: {e}")
                        elif "callback_query" in update:
                            try:
                                handle_callback(update["callback_query"])
                            except Exception as e:
                                print(f"Callback error: {e}")
            time.sleep(0.3)

        except KeyboardInterrupt:
            print("Bot stopped.")
            break
        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
