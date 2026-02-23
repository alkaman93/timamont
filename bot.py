import os
import requests
import time
import random
import json

TOKEN = os.getenv('BOT_TOKEN')

GETGEMS_API = "https://api.getgems.io/graphql"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Origin": "https://getgems.io",
    "Referer": "https://getgems.io/",
}

# Коллекции Telegram Gifts на Getgems
COLLECTIONS = {
    "astralshard":   {"name": "🔮 Astral Shard",     "addr": "EQAOl3-PQpFdpOBfLT7MoB7qNuqOYBRbGXhzRBrdPE5B"},
    "homemadecake":  {"name": "🎂 Homemade Cake",    "addr": "EQAjqVfbcTMPvvJKGdHMjJf6-9NiKIiqXlSJfZIfKlMJqOIR"},
    "lolpop":        {"name": "🍭 Lol Pop",           "addr": "EQC6zjid8vJNEWqcXk10XjsdDLRKbcPZzbHusuEW6FokOWIm"},
    "signetring":    {"name": "💍 Signet Ring",       "addr": "EQCrGA9slCoksgD-NyRDjtHySKN0Ts8k6hdueJkUkZZdD4_K"},
    "lovepotion":    {"name": "🧪 Love Potion",       "addr": "EQD7yDu2WCgd9Uzx1dF_DQkWK7IZJJ4Mp9M9g1rGUUiQE43m"},
    "sakura":        {"name": "🌸 Sakura Flower",     "addr": "EQDIruSTyxvq60gUH8j2kkj3qzoBrBaJy9WkKbeNNRasWe4j"},
    "cookieheart":   {"name": "🍪 Cookie Heart",      "addr": "EQAqtF5tZIgNZal80ChzdPMvZCN8OEbJCVJPn_0xNPghQJPW"},
    "bdaycandle":    {"name": "🕯 B-Day Candle",      "addr": "EQBpMhoMDsN0DjQZXFFBup7l5gbt-UtMzTHN5qaqQtc90CLD"},
}

FEMALE_NAMES = [
    "anna","kate","maria","nastya","lena","olga","yulia","natasha","sasha","dasha",
    "masha","sonya","anya","vika","alina","kristina","polina","irina","sveta","tanya",
    "diana","elena","vera","lisa","ksenia","katya","ira","milana","sofia","valeriya",
    "camilla","amina","kira","zara","mila","girl","woman","lady","princess","queen"
]

user_temp = {}
cache = {}

# ===== GETGEMS API =====
def getgems_query(query, variables=None):
    try:
        r = requests.post(
            GETGEMS_API,
            json={"query": query, "variables": variables or {}},
            headers=HEADERS,
            timeout=20
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"Getgems error: {e}")
    return {}

def get_collection_items(collection_addr, limit=50, cursor=None):
    """Получает NFT из коллекции с юзернеймами владельцев"""
    query = """
    query GetCollectionItems($collectionAddress: String!, $first: Int!, $after: String) {
      nftItemsByCollection(
        collectionAddress: $collectionAddress
        first: $first
        after: $after
      ) {
        cursor
        items {
          name
          address
          sale {
            ... on NftSaleFixPrice {
              fullPrice
            }
          }
          attributes {
            traitType
            value
          }
          owner {
            isScam
            address
            ... on NftItemOwnerUser {
              user {
                address
                username: name
                telegramUsername
              }
            }
          }
        }
      }
    }
    """
    variables = {
        "collectionAddress": collection_addr,
        "first": limit,
    }
    if cursor:
        variables["after"] = cursor

    data = getgems_query(query, variables)
    result = data.get("data", {}).get("nftItemsByCollection", {})
    return result.get("items", []), result.get("cursor")

def parse_item(item):
    """Парсит NFT item и возвращает словарь с данными"""
    owner = item.get("owner", {})
    user = owner.get("user", {}) if owner else {}

    username = user.get("telegramUsername", "") or user.get("username", "") or ""
    name = user.get("username", "")

    # Атрибуты
    attrs = {a["traitType"]: a["value"] for a in item.get("attributes", [])}
    model = attrs.get("Model", attrs.get("model", ""))
    backdrop = attrs.get("Backdrop", attrs.get("backdrop", ""))
    symbol = attrs.get("Symbol", attrs.get("symbol", ""))

    # Цена
    price = 0
    sale = item.get("sale")
    if sale and sale.get("fullPrice"):
        try:
            price = int(sale["fullPrice"]) / 1e9
        except:
            pass

    return {
        "username": username,
        "name": name,
        "nft_name": item.get("name", ""),
        "model": model,
        "backdrop": backdrop,
        "symbol": symbol,
        "price": price,
    }

def load_collection(col_key, max_items=200):
    if col_key in cache:
        return cache[col_key]

    addr = COLLECTIONS[col_key]["addr"]
    all_items = []
    cursor = None

    for _ in range(4):  # максимум 4 страницы
        items, cursor = get_collection_items(addr, limit=50, cursor=cursor)
        for item in items:
            parsed = parse_item(item)
            if parsed["username"] or parsed["name"]:
                all_items.append(parsed)
        if not cursor or len(all_items) >= max_items:
            break
        time.sleep(0.5)

    cache[col_key] = all_items
    return all_items

def load_all():
    all_items = []
    for key in COLLECTIONS:
        items = load_collection(key)
        all_items.extend(items)
        time.sleep(0.3)
    return all_items

def is_female(username, name=""):
    text = (username + " " + name).lower()
    return any(n in text for n in FEMALE_NAMES)

# ===== TELEGRAM =====
def tg(method, data):
    try:
        r = requests.post(f"https://api.telegram.org/bot{TOKEN}/{method}", json=data, timeout=10)
        return r.json()
    except Exception as e:
        print(f"TG error: {e}")
        return None

def send(chat_id, text, buttons=None):
    d = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if buttons:
        d["reply_markup"] = {"inline_keyboard": buttons}
    return tg("sendMessage", d)

def edit(chat_id, mid, text, buttons=None):
    d = {"chat_id": chat_id, "message_id": mid, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if buttons is not None:
        d["reply_markup"] = {"inline_keyboard": buttons}
    tg("editMessageText", d)

def answer(cbid, text=None):
    d = {"callback_query_id": cbid}
    if text:
        d["text"] = text
    tg("answerCallbackQuery", d)

def format_results(results, page, label):
    per = 10
    total = max(1, (len(results) + per - 1) // per)
    page = max(1, min(page, total))
    chunk = results[(page-1)*per : page*per]

    text = f"🎯 <b>Результаты поиска</b>\n📊 Найдено: <b>{len(results)}</b>\n🎯 Режим: {label}\n\n"
    for i, item in enumerate(chunk, (page-1)*per + 1):
        u = item.get("username", "")
        if u:
            text += f"{i}. @{u} | <a href='https://t.me/{u}'>Написать</a>\n"
        else:
            text += f"{i}. {item.get('name', '—')}\n"
    text += f"\n📊 Страница {page}/{total}"

    nav = []
    if page > 1:
        nav.append({"text": "⬅️", "callback_data": f"page_{page-1}"})
    nav.append({"text": f"{page}/{total}", "callback_data": "noop"})
    if page < total:
        nav.append({"text": "➡️", "callback_data": f"page_{page+1}"})

    buttons = [nav] if nav else []
    buttons.append([{"text": "🔄 Искать снова", "callback_data": "main_menu"}])
    return text, buttons

def main_menu_buttons():
    return [
        [{"text": "🎲 Рандом поиск", "callback_data": "random_search"}],
        [{"text": "🎯 Поиск по модели", "callback_data": "model_search"}],
        [{"text": "👱‍♀️ Поиск девушек", "callback_data": "girl_search"}],
        [{"text": "📦 По коллекции", "callback_data": "col_search"}],
    ]

def handle_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    uid = message["from"]["id"]
    if text == "/start":
        user_temp.pop(uid, None)
        send(chat_id,
            "<b>🎁 NFT Gift Parser</b>\n\n"
            "Парсю владельцев Telegram NFT подарков через Getgems.\n\n"
            "Получаю реальные @юзернеймы с кнопкой Написать!",
            main_menu_buttons()
        )

def handle_callback(cb):
    cbid = cb["id"]
    chat_id = cb["message"]["chat"]["id"]
    mid = cb["message"]["message_id"]
    data = cb["data"]
    uid = cb["from"]["id"]
    answer(cbid)

    if data == "noop":
        return

    if data == "main_menu":
        edit(chat_id, mid, "🔍 <b>Выберите тип поиска:</b>", main_menu_buttons())
        return

    if data == "random_search":
        edit(chat_id, mid,
            "🎯 <b>Выберите режим поиска:</b>\n\n"
            "🟢 <b>Легкий</b> — до 3 TON\n"
            "🟡 <b>Средний</b> — 3–15 TON\n"
            "🔴 <b>Жирный</b> — 15–600 TON",
            [
                [{"text": "🟢 Легкий режим", "callback_data": "mode_easy"}],
                [{"text": "🟡 Средний режим", "callback_data": "mode_medium"}],
                [{"text": "🔴 Жирный режим", "callback_data": "mode_hard"}],
                [{"text": "◀️ Назад", "callback_data": "main_menu"}],
            ]
        )
        return

    if data in ["mode_easy", "mode_medium", "mode_hard"]:
        modes = {"mode_easy": ("🟢 Легкий", 0, 3), "mode_medium": ("🟡 Средний", 3, 15), "mode_hard": ("🔴 Жирный", 15, 600)}
        label, mn, mx = modes[data]
        user_temp[uid] = {"label": label, "mn": mn, "mx": mx}
        edit(chat_id, mid,
            f"✅ <b>Режим: {label}</b>\n💰 {mn}–{mx} TON\n\nНажми чтобы начать поиск:",
            [
                [{"text": "🔍 Начать поиск NFT", "callback_data": "do_random"}],
                [{"text": "◀️ Назад", "callback_data": "random_search"}],
            ]
        )
        return

    if data == "do_random":
        label = user_temp.get(uid, {}).get("label", "🟡 Средний")
        mn = user_temp.get(uid, {}).get("mn", 3)
        mx = user_temp.get(uid, {}).get("mx", 15)
        edit(chat_id, mid, "⏳ <b>Загружаю NFT с Getgems...</b>", [])

        all_items = load_all()
        results, seen = [], set()
        for item in all_items:
            u = item.get("username", "")
            if not u:
                continue
            p = item.get("price", 0)
            if mn <= p <= mx and u not in seen:
                seen.add(u)
                results.append(item)
        random.shuffle(results)
        user_temp[uid].update({"results": results, "page": 1})

        if not results:
            edit(chat_id, mid,
                f"❌ <b>В режиме {label} юзернеймов не найдено.</b>\n\nПопробуй другой режим или коллекцию.",
                [[{"text": "◀️ Назад", "callback_data": "random_search"}]]
            )
            return
        text, buttons = format_results(results, 1, label)
        edit(chat_id, mid, text, buttons)
        return

    if data == "girl_search":
        edit(chat_id, mid,
            "👱‍♀️ <b>Поиск девушек</b>\n\nИщу по женским именам в юзернейме\n\nНажми чтобы начать:",
            [
                [{"text": "🔍 Начать поиск", "callback_data": "do_girl"}],
                [{"text": "◀️ Назад", "callback_data": "main_menu"}],
            ]
        )
        return

    if data == "do_girl":
        edit(chat_id, mid, "⏳ <b>Ищу девушек...</b>", [])
        all_items = load_all()
        results, seen = [], set()
        for item in all_items:
            u = item.get("username", "")
            if u and is_female(u, item.get("name", "")) and u not in seen:
                seen.add(u)
                results.append(item)
        random.shuffle(results)
        user_temp[uid] = {"results": results, "page": 1, "label": "👱‍♀️ Девушки"}
        if not results:
            edit(chat_id, mid, "❌ Не найдено.", [[{"text": "🔄 Повторить", "callback_data": "do_girl"}]])
            return
        text, buttons = format_results(results, 1, "👱‍♀️ Девушки")
        edit(chat_id, mid, text, buttons)
        return

    if data == "col_search":
        buttons = [[{"text": v["name"], "callback_data": f"col_{k}"}] for k, v in COLLECTIONS.items()]
        buttons.append([{"text": "◀️ Назад", "callback_data": "main_menu"}])
        edit(chat_id, mid, "<b>📦 Выбери коллекцию:</b>", buttons)
        return

    if data.startswith("col_"):
        col_key = data[4:]
        if col_key not in COLLECTIONS:
            return
        col_name = COLLECTIONS[col_key]["name"]
        edit(chat_id, mid, f"⏳ <b>Загружаю {col_name}...</b>", [])
        items = load_collection(col_key)
        results = [i for i in items if i.get("username")]
        user_temp[uid] = {"results": results, "page": 1, "label": f"📦 {col_name}"}
        if not results:
            edit(chat_id, mid, f"❌ Юзернеймов в {col_name} не найдено.",
                [[{"text": "◀️ Назад", "callback_data": "col_search"}]])
            return
        text, buttons = format_results(results, 1, f"📦 {col_name}")
        edit(chat_id, mid, text, buttons)
        return

    if data == "model_search":
        buttons = [[{"text": v["name"], "callback_data": f"msel_{k}"}] for k, v in COLLECTIONS.items()]
        buttons.append([{"text": "◀️ Назад", "callback_data": "main_menu"}])
        edit(chat_id, mid, "<b>🎯 Выбери коллекцию для поиска по модели:</b>", buttons)
        return

    if data.startswith("msel_"):
        col_key = data[5:]
        col_name = COLLECTIONS.get(col_key, {}).get("name", col_key)
        edit(chat_id, mid, f"⏳ <b>Загружаю {col_name}...</b>", [])
        items = load_collection(col_key)
        models = sorted(set(i.get("model", "") for i in items if i.get("model")))
        if not models:
            edit(chat_id, mid, f"❌ Модели не найдены в {col_name}.",
                [[{"text": "◀️ Назад", "callback_data": "model_search"}]])
            return
        user_temp[uid] = {"col_key": col_key, "col_items": items}
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
        edit(chat_id, mid, f"<b>{col_name}</b>\nВыбери модель:", buttons)
        return

    if data.startswith("mod_"):
        model = data[4:]
        items = user_temp.get(uid, {}).get("col_items", [])
        col_key = user_temp.get(uid, {}).get("col_key", "")
        col_name = COLLECTIONS.get(col_key, {}).get("name", "")
        results = [i for i in items if i.get("model") == model and i.get("username")]
        user_temp[uid].update({"results": results, "page": 1, "label": f"🎯 {col_name} | {model}"})
        if not results:
            edit(chat_id, mid, f"❌ Нет владельцев с моделью «{model}» и юзернеймом.",
                [[{"text": "◀️ Назад", "callback_data": f"msel_{col_key}"}]])
            return
        text, buttons = format_results(results, 1, f"🎯 {col_name} | {model}")
        edit(chat_id, mid, text, buttons)
        return

    if data.startswith("page_"):
        page = int(data[5:])
        results = user_temp.get(uid, {}).get("results", [])
        label = user_temp.get(uid, {}).get("label", "🔍")
        if not results:
            return
        user_temp[uid]["page"] = page
        text, buttons = format_results(results, page, label)
        edit(chat_id, mid, text, buttons)
        return

def main():
    print("NFT Parser (Getgems) started!")
    tg("deleteWebhook", {})
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
