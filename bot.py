import os
import requests
import time
import random
import json
import re
from bs4 import BeautifulSoup

TOKEN = os.getenv('BOT_TOKEN')
# Получи stel_ssid из браузера: fragment.com -> F12 -> Network -> любой запрос -> Cookies -> stel_ssid
STEL_SSID = os.getenv('STEL_SSID', '')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "Referer": "https://fragment.com/gifts",
}

GIFT_COLLECTIONS = {
    "astralshard":   "🔮 Astral Shards",
    "plushpepe":     "🐸 Plush Pepes",
    "sakuraflower":  "🌸 Sakura Flowers",
    "homemadecake":  "🎂 Homemade Cakes",
    "cookieheart":   "🍪 Cookie Hearts",
    "vintagecigar":  "🚬 Vintage Cigars",
    "eternalcandle": "🕯 Eternal Candles",
    "lolpop":        "🍭 Lol Pops",
    "signetring":    "💍 Signet Rings",
    "tophat":        "🎩 Top Hats",
    "evileye":       "🧿 Evil Eyes",
    "lovepotion":    "🧪 Love Potions",
    "durovscap":     "🧢 Durov's Caps",
    "heartlocket":   "💛 Heart Lockets",
    "diamondring":   "💎 Diamond Rings",
    "swisswatch":    "⌚ Swiss Watches",
    "toybear":       "🧸 Toy Bears",
    "witchhat":      "🎃 Witch Hats",
    "snoopdogg":     "🎤 Snoop Doggs",
    "lootbag":       "💰 Loot Bags",
}

FEMALE_NAMES = [
    "anna","kate","maria","nastya","lena","olga","yulia","natasha","sasha","dasha",
    "masha","sonya","anya","vika","alina","kristina","polina","irina","sveta","tanya",
    "kseniya","diana","elena","vera","lisa","xenia","ksenia","katya","ira","olesya",
    "milana","sofia","valeriya","valeria","camilla","kamilla","amina","aisha",
    "girl","woman","lady","princess","queen","babe","beauty","angel","cute","baby",
    "mia","emma","luna","sara","nina","rita","zara","lola","nora","rosa","bella",
]

user_temp = {}
cache = {}

# ─── FRAGMENT SCRAPER ─────────────────────────────────────────────────────────

def get_cookies():
    c = {}
    if STEL_SSID:
        c["stel_ssid"] = STEL_SSID
    return c

def parse_price(text):
    if not text:
        return 0
    text = re.sub(r'[^\d.,]', '', str(text)).replace(',', '')
    try:
        return float(text)
    except:
        return 0

def fetch_collection_page(slug, sort="price_asc", filter_type="", count=60):
    """
    Скрапит страницу коллекции Fragment.
    Возвращает список NFT с owner_name, username, profile_link, nft_link, price.
    """
    results = []
    try:
        params = {"sort": sort}
        if filter_type:
            params["filter"] = filter_type

        r = requests.get(
            f"https://fragment.com/gifts/{slug}",
            params=params,
            headers={**HEADERS, "Accept": "text/html,application/xhtml+xml"},
            cookies=get_cookies(),
            timeout=20
        )

        if r.status_code != 200:
            print(f"[{slug}] HTTP {r.status_code}")
            return results

        html = r.text
        items_raw = []

        # Ищем JSON данные в скриптах
        patterns = [
            r'"gifts"\s*:\s*(\[[\s\S]+?\])\s*[,}]',
            r'"items"\s*:\s*(\[[\s\S]+?\])\s*[,}]',
            r'initData\s*\(\s*([\s\S]+?)\)\s*;',
        ]
        for pat in patterns:
            m = re.search(pat, html)
            if not m:
                continue
            try:
                raw = m.group(1).strip()
                if raw.startswith('['):
                    items_raw = json.loads(raw)
                else:
                    parsed = json.loads(raw)
                    items_raw = (parsed.get("gifts") or parsed.get("items") or [])
                if items_raw:
                    break
            except Exception as e:
                print(f"[{slug}] JSON parse: {e}")

        # Если JSON не нашли — парсим HTML карточки через BeautifulSoup
        if not items_raw:
            soup = BeautifulSoup(html, "html.parser")
            # Fragment рендерит карточки как ссылки вида /gift/slug-num
            for a in soup.select("a[href*='/gift/']"):
                href = a.get("href", "")
                m = re.search(rf'/{slug}-(\d+)', href)
                if not m:
                    continue
                num = m.group(1)

                # Цена из текста карточки
                price_text = ""
                for el in a.find_all(string=True):
                    if re.search(r'\d', el):
                        price_text = el.strip()
                        break

                # Имя владельца
                owner_el = a.find(class_=re.compile(r'owner|user|name', re.I))
                owner_name = owner_el.get_text(strip=True) if owner_el else ""

                items_raw.append({
                    "num": num,
                    "owner_name": owner_name,
                    "price": parse_price(price_text),
                    "href": href,
                })

        # Строим результаты
        for item in items_raw[:count]:
            result = build_item(item, slug)
            if result:
                results.append(result)

        print(f"[{slug}] Загружено {len(results)} NFT")

    except Exception as e:
        print(f"[{slug}] fetch error: {e}")

    return results

def build_item(item, slug):
    """Нормализует один NFT item"""
    num = str(item.get("num", item.get("number", item.get("gift_id", ""))))

    # Владелец
    owner = item.get("owner", {})
    if isinstance(owner, dict):
        raw_name = owner.get("name", owner.get("title", ""))
        username  = owner.get("username", "")
    else:
        raw_name = item.get("owner_name", item.get("name", ""))
        username  = item.get("username", item.get("owner_username", ""))

    username = (username or "").lstrip("@").strip()

    # Цена
    price_raw = item.get("price", 0)
    if isinstance(price_raw, dict):
        price = float(price_raw.get("amount", 0)) / 1e9
    elif isinstance(price_raw, str):
        price = parse_price(price_raw)
    else:
        price = float(price_raw) if price_raw else 0

    # Атрибуты
    attrs = item.get("attributes", item.get("attrs", {}))
    if isinstance(attrs, list):
        attrs = {a.get("name", ""): a.get("value", "") for a in attrs}

    nft_link = (f"https://fragment.com/gift/{slug}-{num}"
                if num else f"https://fragment.com/gifts/{slug}")

    # Профиль
    profile_link = ""
    display_name = ""
    if username:
        profile_link = f"https://t.me/{username}"
        display_name = f"@{username}"
    elif raw_name:
        display_name = raw_name
        # Если имя выглядит как TG username — делаем ссылку
        if re.match(r'^[a-zA-Z][a-zA-Z0-9_]{4,31}$', raw_name):
            profile_link = f"https://t.me/{raw_name}"
            display_name = f"@{raw_name}"

    return {
        "num": num,
        "username": username,
        "owner_name": raw_name,
        "display_name": display_name,
        "profile_link": profile_link,
        "nft_link": nft_link,
        "price": price,
        "model": attrs.get("Model", attrs.get("model", "")),
        "backdrop": attrs.get("Backdrop", attrs.get("backdrop", "")),
        "symbol": attrs.get("Symbol", attrs.get("symbol", "")),
        "collection": slug,
    }

def scrape_nft_page(slug, num):
    """
    Скрапит страницу отдельного NFT чтобы получить owner_name / username.
    Fragment показывает владельца на странице /gift/slug-num
    """
    result = {"owner_name": "", "username": "", "profile_link": "", "display_name": ""}
    try:
        url = f"https://fragment.com/gift/{slug}-{num}"
        r = requests.get(url,
            headers={**HEADERS, "Accept": "text/html,application/xhtml+xml"},
            cookies=get_cookies(), timeout=15)
        if r.status_code != 200:
            return result

        soup = BeautifulSoup(r.text, "html.parser")

        # Ищем секцию с владельцем — Fragment показывает "Owned by @username"
        for el in soup.find_all("a", href=True):
            href = el["href"]
            if href.startswith("https://t.me/"):
                username = href.replace("https://t.me/", "").strip("/")
                name = el.get_text(strip=True).lstrip("@")
                result["username"] = username
                result["owner_name"] = name
                result["profile_link"] = href
                result["display_name"] = f"@{username}"
                return result

        # Ищем owner в JSON внутри страницы
        html = r.text
        m = re.search(r'"owner"\s*:\s*\{([^}]+)\}', html)
        if m:
            try:
                owner = json.loads("{" + m.group(1) + "}")
                username = owner.get("username", "").lstrip("@")
                name = owner.get("name", "")
                if username:
                    result["username"] = username
                    result["owner_name"] = name or username
                    result["profile_link"] = f"https://t.me/{username}"
                    result["display_name"] = f"@{username}"
                elif name:
                    result["owner_name"] = name
                    result["display_name"] = name
            except:
                pass

    except Exception as e:
        print(f"NFT page ({slug}-{num}): {e}")
    return result

def get_collection_nfts(slug, count=100, sort="price_asc", filter_type=""):
    cache_key = f"{slug}:{sort}:{filter_type}"
    if cache_key in cache and cache[cache_key]:
        return cache[cache_key]

    items = fetch_collection_page(slug, sort=sort, filter_type=filter_type, count=count)

    # Для NFT без владельца — грузим отдельные страницы (только первые 15)
    enriched = 0
    for i, item in enumerate(items):
        if enriched >= 15:
            break
        if not item.get("username") and not item.get("owner_name") and item.get("num"):
            extra = scrape_nft_page(slug, item["num"])
            if extra.get("username") or extra.get("owner_name"):
                items[i].update(extra)
                enriched += 1
                time.sleep(0.4)

    cache[cache_key] = items
    return items

def get_all_nfts():
    all_items = []
    for slug in GIFT_COLLECTIONS:
        items = get_collection_nfts(slug)
        all_items.extend(items)
        time.sleep(0.5)
    return all_items

def filter_by_price(items, mn, mx):
    result, seen = [], set()
    for item in items:
        price = item.get("price", 0)
        key = item.get("nft_link", "")
        if key and mn <= price <= mx and key not in seen:
            seen.add(key)
            result.append(item)
    return result

def is_female(username, name):
    text = (username + " " + name).lower()
    return any(n in text for n in FEMALE_NAMES)

# ─── TELEGRAM ─────────────────────────────────────────────────────────────────

def tg(method, data):
    try:
        r = requests.post(f"https://api.telegram.org/bot{TOKEN}/{method}",
                          json=data, timeout=10)
        return r.json()
    except Exception as e:
        print(f"TG: {e}")
        return None

def send_msg(chat_id, text):
    tg("sendMessage", {"chat_id": chat_id, "text": text,
                        "parse_mode": "HTML", "disable_web_page_preview": True})

def send_kb(chat_id, text, buttons):
    tg("sendMessage", {"chat_id": chat_id, "text": text,
                        "reply_markup": {"inline_keyboard": buttons},
                        "parse_mode": "HTML", "disable_web_page_preview": True})

def edit_kb(chat_id, msg_id, text, buttons=None):
    d = {"chat_id": chat_id, "message_id": msg_id, "text": text,
         "parse_mode": "HTML", "disable_web_page_preview": True}
    if buttons is not None:
        d["reply_markup"] = {"inline_keyboard": buttons}
    tg("editMessageText", d)

def answer_cb(cb_id, text=None):
    d = {"callback_query_id": cb_id}
    if text:
        d["text"] = text
    tg("answerCallbackQuery", d)

# ─── ФОРМАТИРОВАНИЕ ───────────────────────────────────────────────────────────

def fmt_results(results, page, label):
    per = 8
    total = max(1, (len(results) + per - 1) // per)
    page  = max(1, min(page, total))
    start = (page - 1) * per
    chunk = results[start:start + per]

    text = (
        f"🎁 <b>Результаты поиска</b>\n"
        f"📊 Найдено: <b>{len(results)}</b> NFT\n"
        f"🔍 {label}\n\n"
    )

    for i, it in enumerate(chunk, start + 1):
        col       = GIFT_COLLECTIONS.get(it.get("collection", ""), "")
        num       = it.get("num", "")
        price     = it.get("price", 0)
        nft_link  = it.get("nft_link", "")
        p_link    = it.get("profile_link", "")
        display   = it.get("display_name", "") or it.get("owner_name", "") or "—"
        model     = it.get("model", "")

        nft_label = f"{col} #{num}" if num else col
        price_str = f"{price:.1f} TON" if price else "—"

        # NFT ссылка
        if nft_link:
            text += f"{i}. <a href='{nft_link}'>🎁 {nft_label}</a>"
        else:
            text += f"{i}. 🎁 {nft_label}"
        if model:
            text += f" [{model}]"
        text += f" · 💰 {price_str}\n"

        # Профиль владельца
        if p_link:
            text += f"   👤 <a href='{p_link}'>{display}</a> · <a href='{p_link}'>✉️ Написать</a>\n"
        elif display != "—":
            text += f"   👤 {display}\n"
        else:
            text += f"   👤 <i>Профиль не найден</i>\n"

        text += "\n"

    text += f"📄 {page}/{total}"

    nav = []
    if page > 1:
        nav.append({"text": "⬅️", "callback_data": f"page_{page-1}"})
    nav.append({"text": f"{page}/{total}", "callback_data": "noop"})
    if page < total:
        nav.append({"text": "➡️", "callback_data": f"page_{page+1}"})

    buttons = []
    if nav:
        buttons.append(nav)
    buttons.append([{"text": "🏠 Главное меню", "callback_data": "main_menu"}])
    return text, buttons

def main_menu(chat_id, msg_id=None):
    ssid_status = "✅ STEL_SSID задан" if STEL_SSID else "⚠️ STEL_SSID не задан (нужен для данных)"
    text = f"🎁 <b>NFT Gift Parser</b>\n{ssid_status}\n\nВыбери режим:"
    buttons = [
        [{"text": "🎲 По цене", "callback_data": "random_search"}],
        [{"text": "📦 По коллекции", "callback_data": "col_search"}],
        [{"text": "🎯 По модели", "callback_data": "model_search"}],
        [{"text": "👱‍♀️ Поиск девушек", "callback_data": "girl_search"}],
        [{"text": "🏷 На продаже сейчас", "callback_data": "forsale_search"}],
        [{"text": "🗑 Сбросить кеш", "callback_data": "clear_cache"}],
    ]
    if msg_id:
        edit_kb(chat_id, msg_id, text, buttons)
    else:
        send_kb(chat_id, text, buttons)

# ─── HANDLERS ─────────────────────────────────────────────────────────────────

def handle_message(msg):
    chat_id = msg["chat"]["id"]
    uid     = msg["from"]["id"]
    text    = msg.get("text", "")

    if text == "/start":
        user_temp.pop(uid, None)
        send_msg(chat_id,
            "🎁 <b>NFT Gift Parser v2</b>\n\n"
            "Получай ссылки на NFT и профили TG владельцев!\n\n"
            "📌 <b>Как получить STEL_SSID:</b>\n"
            "1. Открой <b>fragment.com</b> в браузере\n"
            "2. <code>F12</code> → Network → кликни любой запрос\n"
            "3. Cookies → скопируй <code>stel_ssid</code>\n"
            "4. Задай переменную: <code>STEL_SSID=значение</code>"
        )
        main_menu(chat_id)

def handle_callback(cb):
    cb_id   = cb["id"]
    chat_id = cb["message"]["chat"]["id"]
    msg_id  = cb["message"]["message_id"]
    data    = cb["data"]
    uid     = cb["from"]["id"]

    answer_cb(cb_id)

    if data == "noop":
        return
    if data == "main_menu":
        main_menu(chat_id, msg_id)
        return
    if data == "clear_cache":
        cache.clear()
        edit_kb(chat_id, msg_id, "✅ Кеш очищен!",
                [[{"text": "🏠 Меню", "callback_data": "main_menu"}]])
        return

    # ── РАНДОМ ────────────────────────────────────────────────────────────────
    if data == "random_search":
        edit_kb(chat_id, msg_id, "💰 <b>Выбери ценовой диапазон:</b>", [
            [{"text": "🟢 До 3 TON",    "callback_data": "mode_easy"}],
            [{"text": "🟡 3–15 TON",    "callback_data": "mode_medium"}],
            [{"text": "🔴 15–100 TON",  "callback_data": "mode_hard"}],
            [{"text": "💎 100+ TON",    "callback_data": "mode_whale"}],
            [{"text": "◀️ Назад",       "callback_data": "main_menu"}],
        ])
        return

    if data in ["mode_easy", "mode_medium", "mode_hard", "mode_whale"]:
        modes = {
            "mode_easy":   ("🟢 До 3 TON",    0,   3),
            "mode_medium": ("🟡 3–15 TON",    3,   15),
            "mode_hard":   ("🔴 15–100 TON",  15,  100),
            "mode_whale":  ("💎 100+ TON",    100, 999999),
        }
        label, mn, mx = modes[data]
        user_temp[uid] = {"label": label, "min": mn, "max": mx}
        edit_kb(chat_id, msg_id, f"✅ <b>{label}</b>", [
            [{"text": "🔍 Искать", "callback_data": "do_random"}],
            [{"text": "◀️ Назад", "callback_data": "random_search"}],
        ])
        return

    if data == "do_random":
        label = user_temp.get(uid, {}).get("label", "Поиск")
        mn    = user_temp.get(uid, {}).get("min", 0)
        mx    = user_temp.get(uid, {}).get("max", 15)
        edit_kb(chat_id, msg_id, "⏳ <b>Парсю Fragment.com...</b>", [])
        items   = get_all_nfts()
        results = filter_by_price(items, mn, mx)
        random.shuffle(results)
        user_temp[uid]["results"] = results
        if not results:
            edit_kb(chat_id, msg_id,
                "❌ Ничего не найдено\n\nПроверь STEL_SSID — без него Fragment не отдаёт данные.",
                [[{"text": "🔄 Снова", "callback_data": "do_random"}],
                 [{"text": "◀️ Назад", "callback_data": "random_search"}]])
            return
        text, buttons = fmt_results(results, 1, label)
        edit_kb(chat_id, msg_id, text, buttons)
        return

    # ── НА ПРОДАЖЕ ────────────────────────────────────────────────────────────
    if data == "forsale_search":
        buttons = [[{"text": n, "callback_data": f"sale_{s}"}]
                   for s, n in GIFT_COLLECTIONS.items()]
        buttons.append([{"text": "◀️ Назад", "callback_data": "main_menu"}])
        edit_kb(chat_id, msg_id, "🏷 <b>Коллекция (только на продаже):</b>", buttons)
        return

    if data.startswith("sale_"):
        slug     = data[5:]
        col_name = GIFT_COLLECTIONS.get(slug, slug)
        edit_kb(chat_id, msg_id, f"⏳ Загружаю: <b>{col_name}</b>...", [])
        items   = get_collection_nfts(slug, count=100, sort="price_asc", filter_type="sale")
        results = [i for i in items if i.get("nft_link")]
        user_temp[uid] = {"results": results, "label": f"🏷 {col_name}"}
        if not results:
            edit_kb(chat_id, msg_id, f"❌ Нет данных для {col_name}",
                    [[{"text": "◀️ Назад", "callback_data": "forsale_search"}]])
            return
        text, buttons = fmt_results(results, 1, f"🏷 {col_name}")
        edit_kb(chat_id, msg_id, text, buttons)
        return

    # ── ПО КОЛЛЕКЦИИ ──────────────────────────────────────────────────────────
    if data == "col_search":
        buttons = [[{"text": n, "callback_data": f"col_{s}"}]
                   for s, n in GIFT_COLLECTIONS.items()]
        buttons.append([{"text": "◀️ Назад", "callback_data": "main_menu"}])
        edit_kb(chat_id, msg_id, "📦 <b>Выбери коллекцию:</b>", buttons)
        return

    if data.startswith("col_") and len(data) > 4:
        slug = data[4:]
        if slug not in GIFT_COLLECTIONS:
            return
        col_name = GIFT_COLLECTIONS[slug]
        edit_kb(chat_id, msg_id, f"⏳ Парсю <b>{col_name}</b>...", [])
        items   = get_collection_nfts(slug)
        results = [i for i in items if i.get("nft_link")]
        user_temp[uid] = {"results": results, "label": f"📦 {col_name}"}
        if not results:
            edit_kb(chat_id, msg_id,
                f"❌ Нет данных для {col_name}\n\nНужен <b>STEL_SSID</b>.",
                [[{"text": "🔄 Снова", "callback_data": data}],
                 [{"text": "◀️ Назад", "callback_data": "col_search"}]])
            return
        text, buttons = fmt_results(results, 1, f"📦 {col_name}")
        edit_kb(chat_id, msg_id, text, buttons)
        return

    # ── ПО МОДЕЛИ ─────────────────────────────────────────────────────────────
    if data == "model_search":
        buttons = [[{"text": n, "callback_data": f"msel_{s}"}]
                   for s, n in GIFT_COLLECTIONS.items()]
        buttons.append([{"text": "◀️ Назад", "callback_data": "main_menu"}])
        edit_kb(chat_id, msg_id, "🎯 <b>Коллекция для поиска по модели:</b>", buttons)
        return

    if data.startswith("msel_"):
        slug     = data[5:]
        col_name = GIFT_COLLECTIONS.get(slug, slug)
        edit_kb(chat_id, msg_id, f"⏳ Загружаю {col_name}...", [])
        items  = get_collection_nfts(slug)
        models = sorted(set(i.get("model", "") for i in items if i.get("model")))
        if not models:
            edit_kb(chat_id, msg_id, "❌ Модели не найдены. Нужен STEL_SSID.",
                    [[{"text": "◀️ Назад", "callback_data": "model_search"}]])
            return
        user_temp[uid] = {"col_slug": slug, "col_items": items, "col_name": col_name}
        buttons, row = [], []
        for m in models[:24]:
            row.append({"text": m, "callback_data": f"mod_{m}"})
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([{"text": "◀️ Назад", "callback_data": "model_search"}])
        edit_kb(chat_id, msg_id, f"🎯 <b>{col_name}</b>\nВыбери модель:", buttons)
        return

    if data.startswith("mod_"):
        model    = data[4:]
        items    = user_temp.get(uid, {}).get("col_items", [])
        col_name = user_temp.get(uid, {}).get("col_name", "")
        results  = [i for i in items if i.get("model") == model]
        user_temp[uid]["results"] = results
        if not results:
            edit_kb(chat_id, msg_id, f"❌ Модель «{model}» не найдена.",
                    [[{"text": "◀️ Назад", "callback_data": "model_search"}]])
            return
        text, buttons = fmt_results(results, 1, f"🎯 {col_name} | {model}")
        edit_kb(chat_id, msg_id, text, buttons)
        return

    # ── ПОИСК ДЕВУШЕК ─────────────────────────────────────────────────────────
    if data == "girl_search":
        edit_kb(chat_id, msg_id, "👱‍♀️ <b>Поиск девушек</b>", [
            [{"text": "🔍 Начать", "callback_data": "do_girl"}],
            [{"text": "◀️ Назад", "callback_data": "main_menu"}],
        ])
        return

    if data == "do_girl":
        edit_kb(chat_id, msg_id, "⏳ <b>Ищу девушек...</b>", [])
        all_items = get_all_nfts()
        results, seen = [], set()
        for item in all_items:
            u = item.get("username", "")
            n = item.get("owner_name", "")
            if is_female(u, n):
                key = u or item.get("nft_link", "")
                if key and key not in seen:
                    seen.add(key)
                    results.append(item)
        random.shuffle(results)
        user_temp[uid] = {"results": results, "label": "👱‍♀️ Девушки"}
        if not results:
            edit_kb(chat_id, msg_id, "❌ Не найдено. Нужен STEL_SSID.",
                    [[{"text": "🔄 Снова", "callback_data": "do_girl"}],
                     [{"text": "🏠 Меню",  "callback_data": "main_menu"}]])
            return
        text, buttons = fmt_results(results, 1, "👱‍♀️ Девушки")
        edit_kb(chat_id, msg_id, text, buttons)
        return

    # ── ПАГИНАЦИЯ ─────────────────────────────────────────────────────────────
    if data.startswith("page_"):
        page    = int(data[5:])
        results = user_temp.get(uid, {}).get("results", [])
        label   = user_temp.get(uid, {}).get("label", "Поиск")
        if not results:
            return
        text, buttons = fmt_results(results, page, label)
        edit_kb(chat_id, msg_id, text, buttons)
        return

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("NFT Gift Parser Bot v2")
    if not TOKEN:
        print("ERROR: BOT_TOKEN не задан!")
        return
    print("✅ STEL_SSID задан" if STEL_SSID else
          "⚠️  STEL_SSID не задан!\n   fragment.com -> F12 -> Network -> Cookies -> stel_ssid")
    print("=" * 50)

    tg("deleteWebhook", {})
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
                    for upd in data["result"]:
                        offset = upd["update_id"] + 1
                        if "message" in upd:
                            try:
                                handle_message(upd["message"])
                            except Exception as e:
                                print(f"Msg: {e}")
                        elif "callback_query" in upd:
                            try:
                                handle_callback(upd["callback_query"])
                            except Exception as e:
                                print(f"CB: {e}")
            time.sleep(0.3)
        except KeyboardInterrupt:
            print("Stopped.")
            break
        except Exception as e:
            print(f"Loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
