import os
import requests
import time
import random
import json

TOKEN = os.getenv('BOT_TOKEN')

# GetGems GraphQL API — публичный, без авторизации
GETGEMS_API = "https://api.getgems.io/graphql"

# Адреса коллекций Telegram Gifts на GetGems
GIFT_COLLECTIONS = {
    "EQAVGhN_ZAP_pk4e8DWfFNNGBOdFpBNgJOay7GBdKbxMUGib": "🔮 Astral Shards",
    "EQBpMhoMDsN0DjQZXFFBup7l5gbt-UtMzTHN5qaqQtc90CLD": "🐸 Plush Pepes",
    "EQC_6-3RIWDQlMOzDFOmxv0fZHAGC5sS-eWDU-MkizFc2Vvo": "🌸 Sakura Flowers",
    "EQD-LkNjPCFKqHBmLkjMjDjVMiSLKqNMNNIHyNDBTXR6GHkY": "🎂 Homemade Cakes",
    "EQBj7VF8CpPya7C6pBHOQbBFxN2l77s6o22l4VW5LGMcVF2b": "🍪 Cookie Hearts",
    "EQDOkf1pJKJAnnuSBrJR4zZ1m-ZRwqiRoqyFqxPG4rlYSmH4": "🚬 Vintage Cigars",
    "EQDHByMtMgBm5B5xWRFrr0ePUuUXcRoiGnj-0_VsE04bCjGX": "🕯 Eternal Candles",
    "EQBRRQm9P6L7yJvb-HdGv-Q3gqX2vF55naFuLNGkCk4kBpgD": "🍭 Lol Pops",
    "EQA9GnLbHqxQzJpVgqTKsHIf8L9Hu3N_4xbcV6WFXlLtUiWD": "💍 Signet Rings",
    "EQCKWpx7cNMpvgYVqnCDGSQfla3QHnnNNqKosxSBBkCZPHvj": "🎩 Top Hats",
    "EQBx2o5P4bAR6TU5RcuWFKy7MElY39-TNXnw3P0IVXM6iXgN": "🧿 Evil Eyes",
    "EQAXrkqAAlI3YGilT6Pn76LCrFLk7Yk1xqcVIK6hEwGd7RZ5": "🧪 Love Potions",
    "EQD3LiMQ_KkfpbjI7BIpvxFBPME_keBNsJRGvnabBBrCqGla": "🧢 Durov's Caps",
    "EQBpx5a3NBt6m5e0s_eU6xd7psBSmKJTa6JEiaxPeT_Q5Hkl": "💛 Heart Lockets",
    "EQC5wQ0Qg7CJqMuXo5-CWr-y1e2cX5v8XYi6CgBrqhXxCw7f": "💎 Diamond Rings",
    "EQDfR8_H4Vj2JOmGEPpG3mW5-x8Zq_U7YBn2oR5kK8qN4Kup": "⌚ Swiss Watches",
    "EQBs7IBjMTb6HPZ5_7GhKSWQPAHHHGkQ1YSmMW5X5gT0mYl3": "🧸 Toy Bears",
    "EQDxBGJqVdU2X0s0MVfXZOPmS4l7IWxV9o2Kdn_LQXM3pXGn": "🎃 Witch Hats",
    "EQAEkMNyIQT2LfVJ4zZ8hSkKPqbFxFH2FJa3a-h5C8j0tWkN": "🎤 Snoop Doggs",
    "EQCFo8GPnDCdEjfWrNxRPDjhQKHHLmJBfNNkqcPeUVXCG0tZ": "💰 Loot Bags",
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

# ─── GETGEMS API ───────────────────────────────────────────────────────────────

GQL_COLLECTION_ITEMS = """
query NftCollectionItems($address: String!, $first: Int!, $after: String) {
  nftItemsByCollection(
    collectionAddress: $address
    first: $first
    after: $after
  ) {
    items {
      address
      name
      index
      owner {
        ... on NftItemOwnerUser {
          user {
            wallet { address }
            telegram { username name }
          }
        }
        ... on NftItemOwnerContract {
          contract { address }
        }
      }
      sale {
        ... on NftSaleFixPrice {
          price { value }
        }
        ... on NftSaleAuction {
          currentBid { value }
        }
      }
      attributes {
        traitType
        value
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

def gql_request(query, variables):
    """Делает GraphQL запрос к GetGems API"""
    try:
        r = requests.post(
            GETGEMS_API,
            json={"query": query, "variables": variables},
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0",
            },
            timeout=20
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"GQL error: {e}")
    return None

def fetch_collection(collection_address, collection_name, limit=50):
    """Получает NFT коллекции через GetGems GraphQL"""
    results = []
    cursor = None

    for _ in range(3):  # максимум 3 страницы
        variables = {
            "address": collection_address,
            "first": limit,
        }
        if cursor:
            variables["after"] = cursor

        data = gql_request(GQL_COLLECTION_ITEMS, variables)
        if not data:
            break

        items_data = (data.get("data") or {}).get("nftItemsByCollection") or {}
        items = items_data.get("items", [])
        page_info = items_data.get("pageInfo", {})

        for item in items:
            result = parse_getgems_item(item, collection_address, collection_name)
            if result:
                results.append(result)

        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
        time.sleep(0.3)

    return results

def parse_getgems_item(item, col_addr, col_name):
    """Парсит один NFT item из GetGems"""
    address = item.get("address", "")
    name = item.get("name", "")
    index = item.get("index", "")

    # Извлекаем номер из имени (например "Plush Pepe #1821" -> 1821)
    import re
    num_match = re.search(r'#(\d+)', name)
    num = num_match.group(1) if num_match else str(index)

    # Владелец
    username = ""
    owner_name = ""
    owner = item.get("owner") or {}

    user_data = owner.get("user") or {}
    tg_data = user_data.get("telegram") or {}
    username = (tg_data.get("username") or "").lstrip("@")
    owner_name = tg_data.get("name") or ""

    # Если нет TG данных — берём адрес кошелька
    wallet = (user_data.get("wallet") or {}).get("address", "")
    if not username and not owner_name and wallet:
        owner_name = wallet[:12] + "..."

    # Цена
    sale = item.get("sale") or {}
    price_raw = (sale.get("price") or sale.get("currentBid") or {}).get("value", 0)
    try:
        price = float(price_raw) / 1e9  # наноTON -> TON
    except:
        price = 0

    # Атрибуты
    attrs = {}
    for attr in (item.get("attributes") or []):
        attrs[attr.get("traitType", "")] = attr.get("value", "")

    # Ссылки
    nft_link = f"https://getgems.io/nft/{address}" if address else ""
    fragment_link = f"https://fragment.com/gift/{col_name.split()[-1].lower()}-{num}"

    profile_link = ""
    display_name = ""
    if username:
        profile_link = f"https://t.me/{username}"
        display_name = f"@{username}"
    elif owner_name:
        display_name = owner_name

    return {
        "num": num,
        "username": username,
        "owner_name": owner_name,
        "display_name": display_name,
        "profile_link": profile_link,
        "nft_link": nft_link or fragment_link,
        "price": price,
        "model": attrs.get("Model", attrs.get("model", "")),
        "backdrop": attrs.get("Backdrop", attrs.get("backdrop", "")),
        "symbol": attrs.get("Symbol", attrs.get("symbol", "")),
        "collection": col_addr,
        "collection_name": col_name,
    }

def get_collection_nfts(col_addr, col_name, force=False):
    if col_addr in cache and not force:
        return cache[col_addr]
    items = fetch_collection(col_addr, col_name, limit=50)
    cache[col_addr] = items
    print(f"[{col_name}] загружено {len(items)} NFT")
    return items

def get_all_nfts():
    all_items = []
    for addr, name in GIFT_COLLECTIONS.items():
        items = get_collection_nfts(addr, name)
        all_items.extend(items)
        time.sleep(0.3)
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

def answer_cb(cb_id):
    tg("answerCallbackQuery", {"callback_query_id": cb_id})

# ─── ФОРМАТИРОВАНИЕ ───────────────────────────────────────────────────────────

def fmt(results, page, label):
    per = 8
    total = max(1, (len(results) + per - 1) // per)
    page = max(1, min(page, total))
    start = (page - 1) * per
    chunk = results[start:start + per]

    text = (
        f"🎁 <b>Результаты</b>\n"
        f"📊 Найдено: <b>{len(results)}</b> NFT\n"
        f"🔍 {label}\n\n"
    )

    for i, it in enumerate(chunk, start + 1):
        col_name = it.get("collection_name", "")
        num = it.get("num", "")
        price = it.get("price", 0)
        nft_link = it.get("nft_link", "")
        p_link = it.get("profile_link", "")
        display = it.get("display_name", "") or "—"
        model = it.get("model", "")

        nft_label = f"{col_name} #{num}" if num else col_name
        price_str = f"{price:.1f} TON" if price else "не продаётся"

        if nft_link:
            text += f"{i}. <a href='{nft_link}'>🎁 {nft_label}</a>"
        else:
            text += f"{i}. 🎁 {nft_label}"

        if model:
            text += f" [{model}]"
        text += f"\n    💰 {price_str}\n"

        if p_link:
            text += f"    👤 <a href='{p_link}'>{display}</a> · <a href='{p_link}'>✉️ Написать</a>\n"
        elif display != "—":
            text += f"    👤 {display}\n"
        else:
            text += f"    👤 <i>Нет профиля TG</i>\n"

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
    buttons.append([{"text": "🏠 Меню", "callback_data": "main_menu"}])
    return text, buttons

def main_menu(chat_id, msg_id=None):
    text = (
        "🎁 <b>NFT Gift Parser</b>\n"
        "Данные с GetGems.io — без авторизации!\n\n"
        "Выбери режим:"
    )
    buttons = [
        [{"text": "🎲 По цене", "callback_data": "random_search"}],
        [{"text": "📦 По коллекции", "callback_data": "col_search"}],
        [{"text": "🎯 По модели", "callback_data": "model_search"}],
        [{"text": "👱‍♀️ Поиск девушек", "callback_data": "girl_search"}],
        [{"text": "🏷 На продаже", "callback_data": "sale_search"}],
        [{"text": "🗑 Сбросить кеш", "callback_data": "clear_cache"}],
    ]
    if msg_id:
        edit_kb(chat_id, msg_id, text, buttons)
    else:
        send_kb(chat_id, text, buttons)

# ─── HANDLERS ─────────────────────────────────────────────────────────────────

def handle_message(msg):
    chat_id = msg["chat"]["id"]
    uid = msg["from"]["id"]
    text = msg.get("text", "")

    if text == "/start":
        user_temp.pop(uid, None)
        send_msg(chat_id,
            "🎁 <b>NFT Gift Parser</b>\n\n"
            "Парсю владельцев NFT подарков Telegram!\n"
            "Данные с GetGems.io — работает без авторизации ✅\n\n"
            "Каждый результат содержит:\n"
            "🎁 Ссылку на NFT\n"
            "👤 Профиль владельца в TG\n"
            "✉️ Кнопку Написать"
        )
        main_menu(chat_id)

def handle_callback(cb):
    cb_id = cb["id"]
    chat_id = cb["message"]["chat"]["id"]
    msg_id = cb["message"]["message_id"]
    data = cb["data"]
    uid = cb["from"]["id"]

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
        edit_kb(chat_id, msg_id, "💰 <b>Выбери диапазон цены:</b>", [
            [{"text": "🟢 До 3 TON",   "callback_data": "mode_easy"}],
            [{"text": "🟡 3–15 TON",   "callback_data": "mode_medium"}],
            [{"text": "🔴 15–100 TON", "callback_data": "mode_hard"}],
            [{"text": "💎 100+ TON",   "callback_data": "mode_whale"}],
            [{"text": "◀️ Назад",      "callback_data": "main_menu"}],
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
        mn = user_temp.get(uid, {}).get("min", 0)
        mx = user_temp.get(uid, {}).get("max", 15)
        edit_kb(chat_id, msg_id, "⏳ <b>Загружаю данные с GetGems...</b>", [])
        items = get_all_nfts()
        results = filter_by_price(items, mn, mx)
        random.shuffle(results)
        user_temp[uid]["results"] = results
        if not results:
            edit_kb(chat_id, msg_id,
                "❌ Ничего не найдено в этом диапазоне.\nПопробуй другой диапазон.",
                [[{"text": "🔄 Снова", "callback_data": "random_search"}],
                 [{"text": "🏠 Меню",  "callback_data": "main_menu"}]])
            return
        text, buttons = fmt(results, 1, label)
        edit_kb(chat_id, msg_id, text, buttons)
        return

    # ── НА ПРОДАЖЕ ────────────────────────────────────────────────────────────
    if data == "sale_search":
        edit_kb(chat_id, msg_id, "⏳ <b>Ищу NFT на продаже...</b>", [])
        items = get_all_nfts()
        results = [i for i in items if i.get("price", 0) > 0]
        results.sort(key=lambda x: x.get("price", 0))
        user_temp[uid] = {"results": results, "label": "🏷 На продаже"}
        if not results:
            edit_kb(chat_id, msg_id, "❌ Нет NFT на продаже.",
                    [[{"text": "🏠 Меню", "callback_data": "main_menu"}]])
            return
        text, buttons = fmt(results, 1, "🏷 На продаже")
        edit_kb(chat_id, msg_id, text, buttons)
        return

    # ── ПО КОЛЛЕКЦИИ ──────────────────────────────────────────────────────────
    if data == "col_search":
        buttons = []
        for addr, name in GIFT_COLLECTIONS.items():
            short = addr[:8]
            buttons.append([{"text": name, "callback_data": f"col_{short}"}])
        buttons.append([{"text": "◀️ Назад", "callback_data": "main_menu"}])
        edit_kb(chat_id, msg_id, "📦 <b>Выбери коллекцию:</b>", buttons)
        return

    if data.startswith("col_") and len(data) > 4:
        short = data[4:]
        # Находим полный адрес по первым 8 символам
        col_addr = next((a for a in GIFT_COLLECTIONS if a.startswith(short)), None)
        if not col_addr:
            return
        col_name = GIFT_COLLECTIONS[col_addr]
        edit_kb(chat_id, msg_id, f"⏳ Загружаю <b>{col_name}</b>...", [])
        items = get_collection_nfts(col_addr, col_name)
        results = items
        user_temp[uid] = {"results": results, "label": f"📦 {col_name}"}
        if not results:
            edit_kb(chat_id, msg_id, f"❌ Нет данных для {col_name}",
                    [[{"text": "◀️ Назад", "callback_data": "col_search"}]])
            return
        text, buttons = fmt(results, 1, f"📦 {col_name}")
        edit_kb(chat_id, msg_id, text, buttons)
        return

    # ── ПО МОДЕЛИ ─────────────────────────────────────────────────────────────
    if data == "model_search":
        buttons = []
        for addr, name in GIFT_COLLECTIONS.items():
            short = addr[:8]
            buttons.append([{"text": name, "callback_data": f"msel_{short}"}])
        buttons.append([{"text": "◀️ Назад", "callback_data": "main_menu"}])
        edit_kb(chat_id, msg_id, "🎯 <b>Коллекция для поиска по модели:</b>", buttons)
        return

    if data.startswith("msel_"):
        short = data[5:]
        col_addr = next((a for a in GIFT_COLLECTIONS if a.startswith(short)), None)
        if not col_addr:
            return
        col_name = GIFT_COLLECTIONS[col_addr]
        edit_kb(chat_id, msg_id, f"⏳ Загружаю {col_name}...", [])
        items = get_collection_nfts(col_addr, col_name)
        models = sorted(set(i.get("model", "") for i in items if i.get("model")))
        if not models:
            edit_kb(chat_id, msg_id, "❌ Модели не найдены.",
                    [[{"text": "◀️ Назад", "callback_data": "model_search"}]])
            return
        user_temp[uid] = {"col_addr": col_addr, "col_items": items, "col_name": col_name}
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
        model = data[4:]
        items = user_temp.get(uid, {}).get("col_items", [])
        col_name = user_temp.get(uid, {}).get("col_name", "")
        results = [i for i in items if i.get("model") == model]
        user_temp[uid]["results"] = results
        if not results:
            edit_kb(chat_id, msg_id, f"❌ Модель «{model}» не найдена.",
                    [[{"text": "◀️ Назад", "callback_data": "model_search"}]])
            return
        text, buttons = fmt(results, 1, f"🎯 {col_name} | {model}")
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
            edit_kb(chat_id, msg_id, "❌ Не найдено.",
                    [[{"text": "🔄 Снова", "callback_data": "do_girl"}],
                     [{"text": "🏠 Меню",  "callback_data": "main_menu"}]])
            return
        text, buttons = fmt(results, 1, "👱‍♀️ Девушки")
        edit_kb(chat_id, msg_id, text, buttons)
        return

    # ── ПАГИНАЦИЯ ─────────────────────────────────────────────────────────────
    if data.startswith("page_"):
        page = int(data[5:])
        results = user_temp.get(uid, {}).get("results", [])
        label = user_temp.get(uid, {}).get("label", "Поиск")
        if not results:
            return
        text, buttons = fmt(results, page, label)
        edit_kb(chat_id, msg_id, text, buttons)
        return

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("NFT Gift Parser — GetGems API (без авторизации)")
    if not TOKEN:
        print("ERROR: BOT_TOKEN не задан!")
        return
    print("✅ Готов к работе!")
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
