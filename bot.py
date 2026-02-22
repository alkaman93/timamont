import os
import requests
import time
import json

TOKEN = os.getenv('BOT_TOKEN')
TON_API = "https://tonapi.io/v2"
TON_API_KEY = os.getenv('TON_API_KEY', '')

# Реальные коллекции Telegram NFT подарков с getgems.io
COLLECTIONS = {
    "gem_signets": {
        "name": "💎 Gem Signets",
        "address": "EQAqtF5tZIgNZal80ChzdPMvZCN8OEbJCVJPn_0xNPghQJPW"
    },
    "signet_rings": {
        "name": "💍 Signet Rings",
        "address": "EQCrGA9slCoksgD-NyRDjtHySKN0Ts8k6hdueJkUkZZdD4_K"
    },
    "stellar_rockets": {
        "name": "🚀 Stellar Rockets",
        "address": "EQDIruSTyxvq60gUH8j2kkj3qzoBrBaJy9WkKbeNNRasWe4j"
    },
    "love_potions": {
        "name": "🧪 Love Potions",
        "address": "EQD7yDu2WCgd9Uzx1dF_DQkWK7IZJJ4Mp9M9g1rGUUiQE43m"
    },
    "lol_pops": {
        "name": "🍭 Lol Pops",
        "address": "EQC6zjid8vJNEWqcXk10XjsdDLRKbcPZzbHusuEW6FokOWIm"
    },
    "ton_gifts": {
        "name": "🎁 TON Gifts",
        "address": "EQBpMhoMDsN0DjQZXFFBup7l5gbt-UtMzTHN5qaqQtc90CLD"
    }
}

user_states = {}
user_temp = {}
cache = {}  # кэш NFT по коллекциям

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
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        data["reply_markup"] = reply_markup
    return tg_request("sendMessage", data)

def send_inline(chat_id, text, buttons):
    return tg_request("sendMessage", {
        "chat_id": chat_id, "text": text,
        "reply_markup": {"inline_keyboard": buttons},
        "parse_mode": "HTML"
    })

def edit_inline(chat_id, message_id, text, buttons=None):
    data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
    if buttons is not None:
        data["reply_markup"] = {"inline_keyboard": buttons}
    tg_request("editMessageText", data)

def answer_callback(callback_id, text=None):
    data = {"callback_query_id": callback_id}
    if text:
        data["text"] = text
    tg_request("answerCallbackQuery", data)

def main_keyboard():
    return {"keyboard": [[{"text": "🔍 Найти NFT"}], [{"text": "📋 Все коллекции"}]], "resize_keyboard": True}

# ===== TON API =====
def ton_headers():
    h = {"Accept": "application/json"}
    if TON_API_KEY:
        h["Authorization"] = f"Bearer {TON_API_KEY}"
    return h

def load_collection_nfts(address, limit=500):
    """Загружает NFT коллекции из TON API"""
    all_items = []
    offset = 0
    while len(all_items) < limit:
        try:
            url = f"{TON_API}/nfts/collections/{address}/items"
            r = requests.get(url, params={"limit": 100, "offset": offset}, headers=ton_headers(), timeout=20)
            if r.status_code != 200:
                break
            data = r.json()
            items = data.get("nft_items", [])
            if not items:
                break
            all_items.extend(items)
            if len(items) < 100:
                break
            offset += 100
            time.sleep(0.5)
        except Exception as e:
            print(f"TON load error: {e}")
            break
    return all_items

def parse_attributes_from_items(items):
    """Собирает все уникальные атрибуты из NFT"""
    attrs = {}
    for item in items:
        meta = item.get("metadata", {})
        for attr in meta.get("attributes", []):
            trait = attr.get("trait_type", "").strip()
            value = str(attr.get("value", "")).strip()
            if trait and value:
                attrs.setdefault(trait, set()).add(value)
    return {k: sorted(v) for k, v in attrs.items()}

def filter_items(items, filters):
    """Фильтрует NFT по атрибутам"""
    result = []
    for item in items:
        meta = item.get("metadata", {})
        item_attrs = {a["trait_type"]: str(a["value"]) for a in meta.get("attributes", [])}
        match = all(item_attrs.get(k) == v for k, v in filters.items())
        if match:
            owner = item.get("owner", {})
            username = ""
            name = "—"
            if owner:
                user_info = owner.get("user", {})
                if user_info:
                    username = user_info.get("username", "")
                    name = user_info.get("name", "")
            result.append({
                "nft_name": meta.get("name", "NFT"),
                "username": username,
                "owner_name": name,
                "address": owner.get("address", "") if owner else "",
                "attrs": item_attrs
            })
    return result

def get_cached(col_key):
    if col_key in cache:
        return cache[col_key]["items"], cache[col_key]["attrs"]
    return None, None

def save_cache(col_key, items, attrs):
    cache[col_key] = {"items": items, "attrs": attrs}

# ===== ХЭНДЛЕРЫ =====
def show_collections(chat_id, message_id=None):
    buttons = [[{"text": col["name"], "callback_data": f"col_{key}"}]
               for key, col in COLLECTIONS.items()]
    text = "<b>🎁 Выбери коллекцию Telegram NFT:</b>"
    if message_id:
        edit_inline(chat_id, message_id, text, buttons)
    else:
        send_inline(chat_id, text, buttons)

def show_attributes(chat_id, message_id, user_id):
    attrs = user_temp[user_id].get("attrs", {})
    filters = user_temp[user_id].get("filters", {})
    col_key = user_temp[user_id].get("col_key", "")
    col_name = COLLECTIONS.get(col_key, {}).get("name", "")
    items = user_temp[user_id].get("items", [])

    filter_lines = "\n".join([f"  • {k}: <b>{v}</b>" for k, v in filters.items()]) if filters else "  нет"
    text = (
        f"<b>{col_name}</b>\n"
        f"📦 Загружено NFT: {len(items)}\n\n"
        f"<b>Активные фильтры:</b>\n{filter_lines}\n\n"
        f"<b>Выбери атрибут для фильтра:</b>"
    )

    buttons = []
    for trait, values in attrs.items():
        mark = " ✅" if trait in filters else ""
        buttons.append([{"text": f"🏷 {trait}{mark} ({len(values)} вар.)", "callback_data": f"attr_{trait}"}])

    buttons.append([{"text": "🔍 Искать!", "callback_data": "do_search"}])
    if filters:
        buttons.append([{"text": "🗑 Сбросить фильтры", "callback_data": f"col_{col_key}"}])
    buttons.append([{"text": "◀️ К коллекциям", "callback_data": "show_cols"}])

    edit_inline(chat_id, message_id, text, buttons)

def handle_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    user_id = message["from"]["id"]

    if text == "/start":
        user_states.pop(user_id, None)
        user_temp.pop(user_id, None)
        send_message(chat_id,
            "<b>🎁 NFT Gift Finder</b>\n\n"
            "Ищу людей по NFT подаркам Telegram.\n\n"
            "Выбери коллекцию → фильтруй по модели, фону, символу → получи список владельцев с юзернеймами!\n\n"
            "Нажми <b>🔍 Найти NFT</b>",
            main_keyboard()
        )
        return

    if text in ["🔍 Найти NFT", "📋 Все коллекции"]:
        user_temp[user_id] = {}
        show_collections(chat_id)
        return

def handle_callback(callback):
    callback_id = callback["id"]
    chat_id = callback["message"]["chat"]["id"]
    message_id = callback["message"]["message_id"]
    data = callback["data"]
    user_id = callback["from"]["id"]

    answer_callback(callback_id)

    # К коллекциям
    if data == "show_cols":
        user_temp[user_id] = {}
        show_collections(chat_id, message_id)
        return

    # Выбор коллекции
    if data.startswith("col_"):
        col_key = data[4:]
        if col_key not in COLLECTIONS:
            return

        col = COLLECTIONS[col_key]
        user_temp[user_id] = {"col_key": col_key, "filters": {}}

        # Проверяем кэш
        items, attrs = get_cached(col_key)
        if items:
            user_temp[user_id]["items"] = items
            user_temp[user_id]["attrs"] = attrs
            show_attributes(chat_id, message_id, user_id)
            return

        # Загружаем
        edit_inline(chat_id, message_id,
            f"<b>⏳ Загружаю {col['name']}...</b>\n\nЭто займёт 10-30 секунд, подожди!",
            []
        )

        items = load_collection_nfts(col["address"])
        if not items:
            edit_inline(chat_id, message_id,
                "<b>❌ Не удалось загрузить коллекцию.\nПопробуй позже или возьми TON API ключ на tonapi.io</b>",
                [[{"text": "◀️ Назад", "callback_data": "show_cols"}]]
            )
            return

        attrs = parse_attributes_from_items(items)
        save_cache(col_key, items, attrs)
        user_temp[user_id]["items"] = items
        user_temp[user_id]["attrs"] = attrs
        show_attributes(chat_id, message_id, user_id)
        return

    # Выбор атрибута
    if data.startswith("attr_"):
        trait = data[5:]
        attrs = user_temp.get(user_id, {}).get("attrs", {})
        values = attrs.get(trait, [])
        user_temp[user_id]["current_trait"] = trait

        # Кнопки значений по 2 в ряд
        buttons = []
        row = []
        for val in values[:24]:
            row.append({"text": val, "callback_data": f"val_{val}"})
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([{"text": "◀️ Назад", "callback_data": "back_to_attrs"}])

        edit_inline(chat_id, message_id,
            f"<b>Атрибут: {trait}</b>\nВыбери значение:",
            buttons
        )
        return

    # Назад к атрибутам
    if data == "back_to_attrs":
        show_attributes(chat_id, message_id, user_id)
        return

    # Выбор значения
    if data.startswith("val_"):
        value = data[4:]
        trait = user_temp[user_id].get("current_trait", "")
        if trait:
            user_temp[user_id].setdefault("filters", {})[trait] = value
        show_attributes(chat_id, message_id, user_id)
        return

    # Поиск
    if data == "do_search":
        items = user_temp[user_id].get("items", [])
        filters = user_temp[user_id].get("filters", {})

        edit_inline(chat_id, message_id, "<b>⏳ Ищу совпадения...</b>", [])

        results = filter_items(items, filters)

        if not results:
            edit_inline(chat_id, message_id,
                "<b>❌ Ничего не найдено с такими фильтрами.</b>\n\nПопробуй другие параметры.",
                [
                    [{"text": "🔄 Изменить фильтры", "callback_data": "back_to_attrs"}],
                    [{"text": "◀️ К коллекциям", "callback_data": "show_cols"}]
                ]
            )
            return

        col_name = COLLECTIONS.get(user_temp[user_id].get("col_key", ""), {}).get("name", "")
        filter_text = " | ".join([f"{k}: {v}" for k, v in filters.items()]) or "без фильтров"
        show = results[:100]

        edit_inline(chat_id, message_id,
            f"<b>✅ {col_name}</b>\n"
            f"<b>Фильтры:</b> {filter_text}\n"
            f"<b>Найдено:</b> {len(results)} NFT (показываю {len(show)})",
            [[{"text": "🔄 Новый поиск", "callback_data": "show_cols"}]]
        )

        # Отправляем списком по 25
        chunks = [show[i:i+25] for i in range(0, len(show), 25)]
        for idx, chunk in enumerate(chunks):
            text = f"<b>👤 Владельцы {idx*25+1}–{idx*25+len(chunk)}:</b>\n\n"
            for i, item in enumerate(chunk, idx*25+1):
                if item["username"]:
                    user_str = f"@{item['username']}"
                else:
                    addr = item["address"][:10] + "..." if item["address"] else "неизвестен"
                    user_str = f"<code>{addr}</code>"
                text += f"{i}. {user_str} — {item['nft_name']}\n"
            send_message(chat_id, text)
            time.sleep(0.3)

        send_message(chat_id, "<b>✅ Поиск завершён!</b>", main_keyboard())
        return

def main():
    print("NFT Gift Finder started!")
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
