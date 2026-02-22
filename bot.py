import os
import requests
import time

TOKEN = os.getenv('BOT_TOKEN')

# TON API
TON_API = "https://tonapi.io/v2"
TON_API_KEY = os.getenv('TON_API_KEY', '')  # опционально, без него тоже работает но лимит ниже

# Известные коллекции Telegram NFT подарков
COLLECTIONS = {
    "tg_gifts": {
        "name": "🎁 Telegram Gifts",
        "address": "EQAVGhk_3rUA3ypZAZ1SkVGnwAJmRokWIlkIutigrVYWs167"
    }
}

user_states = {}
user_temp = {}
# Кэш атрибутов чтобы не грузить каждый раз
cache_attributes = {}

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

def edit_message(chat_id, message_id, text, buttons=None):
    data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
    if buttons:
        data["reply_markup"] = {"inline_keyboard": buttons}
    tg_request("editMessageText", data)

def answer_callback(callback_id, text=None):
    data = {"callback_query_id": callback_id}
    if text:
        data["text"] = text
    tg_request("answerCallbackQuery", data)

def main_keyboard():
    return {"keyboard": [[{"text": "🔍 Найти NFT"}], [{"text": "📋 Коллекции"}]], "resize_keyboard": True}

def ton_headers():
    h = {"Accept": "application/json"}
    if TON_API_KEY:
        h["Authorization"] = f"Bearer {TON_API_KEY}"
    return h

def get_collection_nfts(collection_address, limit=1000, offset=0):
    """Получает NFT из коллекции"""
    try:
        url = f"{TON_API}/nfts/collections/{collection_address}/items"
        r = requests.get(url, params={"limit": limit, "offset": offset}, headers=ton_headers(), timeout=15)
        data = r.json()
        return data.get("nft_items", [])
    except Exception as e:
        print(f"TON API error: {e}")
        return []

def parse_attributes(nft_items):
    """Парсит все уникальные атрибуты из списка NFT"""
    attrs = {}  # {trait_type: set(values)}
    for item in nft_items:
        metadata = item.get("metadata", {})
        attributes = metadata.get("attributes", [])
        for attr in attributes:
            trait = attr.get("trait_type", "")
            value = attr.get("value", "")
            if trait and value:
                attrs.setdefault(trait, set()).add(str(value))
    return {k: sorted(v) for k, v in attrs.items()}

def filter_nfts_by_attr(nft_items, trait_type, value):
    """Фильтрует NFT по атрибуту"""
    results = []
    for item in nft_items:
        metadata = item.get("metadata", {})
        attributes = metadata.get("attributes", [])
        for attr in attributes:
            if attr.get("trait_type", "") == trait_type and str(attr.get("value", "")) == value:
                owner = item.get("owner", {})
                username = ""
                # Пробуем получить username
                if owner:
                    user_info = owner.get("user", {})
                    if user_info:
                        username = user_info.get("username", "")
                results.append({
                    "name": metadata.get("name", "Unknown NFT"),
                    "owner_address": owner.get("address", "") if owner else "",
                    "username": username,
                    "attrs": {a["trait_type"]: a["value"] for a in attributes}
                })
                break
    return results

def load_collection(collection_key):
    """Загружает и кэширует NFT коллекции"""
    if collection_key in cache_attributes:
        return cache_attributes[collection_key]["items"], cache_attributes[collection_key]["attrs"]
    
    address = COLLECTIONS[collection_key]["address"]
    items = get_collection_nfts(address, limit=1000)
    attrs = parse_attributes(items)
    cache_attributes[collection_key] = {"items": items, "attrs": attrs}
    return items, attrs

def handle_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    user_id = message["from"]["id"]

    if text == "/start":
        user_states.pop(user_id, None)
        user_temp.pop(user_id, None)
        send_message(chat_id,
            "<b>🎁 NFT Gift Finder</b>\n\n"
            "Ищу людей по NFT подаркам в Telegram.\n\n"
            "Выбери параметры — фон, модель и тд — и получи список владельцев!\n\n"
            "Нажми <b>🔍 Найти NFT</b>",
            main_keyboard()
        )
        return

    if text == "🔍 Найти NFT" or text == "📋 Коллекции":
        user_temp[user_id] = {}
        user_states[user_id] = "waiting_collection"
        buttons = [[{"text": col["name"], "callback_data": f"col_{key}"}] for key, col in COLLECTIONS.items()]
        send_inline(chat_id, "<b>Выбери коллекцию:</b>", buttons)
        return

def handle_callback(callback):
    callback_id = callback["id"]
    chat_id = callback["message"]["chat"]["id"]
    message_id = callback["message"]["message_id"]
    data = callback["data"]
    user_id = callback["from"]["id"]

    answer_callback(callback_id)

    # Выбор коллекции
    if data.startswith("col_"):
        col_key = data.replace("col_", "")
        user_temp.setdefault(user_id, {})["collection"] = col_key
        user_states[user_id] = "loading"

        edit_message(chat_id, message_id, "<b>⏳ Загружаю NFT коллекции... Это может занять 10-20 сек</b>")

        items, attrs = load_collection(col_key)

        if not attrs:
            edit_message(chat_id, message_id, "<b>❌ Не удалось загрузить коллекцию. Попробуй позже.</b>")
            return

        user_temp[user_id]["items"] = items
        user_temp[user_id]["attrs"] = attrs
        user_temp[user_id]["filters"] = {}
        user_states[user_id] = "choosing_trait"

        # Показываем доступные атрибуты
        buttons = []
        for trait in list(attrs.keys())[:8]:
            buttons.append([{"text": f"🏷 {trait}", "callback_data": f"trait_{trait}"}])
        buttons.append([{"text": "🔍 Искать с текущими фильтрами", "callback_data": "do_search"}])

        col_name = COLLECTIONS[col_key]["name"]
        edit_message(chat_id, message_id,
            f"<b>{col_name}</b>\n"
            f"Загружено: {len(items)} NFT\n\n"
            f"<b>Выбери атрибут для фильтрации:</b>",
            buttons
        )
        return

    # Выбор атрибута
    if data.startswith("trait_"):
        trait_key = data.replace("trait_", "")
        user_temp.setdefault(user_id, {})["current_trait"] = trait_key
        user_states[user_id] = "choosing_value"

        attrs = user_temp[user_id].get("attrs", {})
        values = attrs.get(trait_key, [])

        # Кнопки значений (по 2 в ряд)
        buttons = []
        row = []
        for i, val in enumerate(values[:20]):
            row.append({"text": str(val), "callback_data": f"val_{val}"})
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([{"text": "◀️ Назад к атрибутам", "callback_data": f"col_{user_temp[user_id].get('collection', '')}"}])

        edit_message(chat_id, message_id,
            f"<b>Атрибут: {trait_key}</b>\n\nВыбери значение:",
            buttons
        )
        return

    # Выбор значения
    if data.startswith("val_"):
        value = data.replace("val_", "")
        trait_key = user_temp[user_id].get("current_trait", "")
        user_temp[user_id].setdefault("filters", {})[trait_key] = value
        user_states[user_id] = "choosing_trait"

        attrs = user_temp[user_id].get("attrs", {})
        filters = user_temp[user_id].get("filters", {})

        # Показываем текущие фильтры и атрибуты
        filter_text = "\n".join([f"• {k}: <b>{v}</b>" for k, v in filters.items()])
        buttons = []
        for trait in list(attrs.keys())[:8]:
            already = " ✅" if trait in filters else ""
            buttons.append([{"text": f"🏷 {trait}{already}", "callback_data": f"trait_{trait}"}])
        buttons.append([{"text": "🔍 Искать!", "callback_data": "do_search"}])
        buttons.append([{"text": "🗑 Сбросить фильтры", "callback_data": f"col_{user_temp[user_id].get('collection', '')}"}])

        col_key = user_temp[user_id].get("collection", "")
        items_count = len(user_temp[user_id].get("items", []))
        edit_message(chat_id, message_id,
            f"<b>Текущие фильтры:</b>\n{filter_text}\n\n"
            f"Добавь ещё фильтры или нажми 🔍 Искать:",
            buttons
        )
        return

    # Поиск
    if data == "do_search":
        items = user_temp[user_id].get("items", [])
        filters = user_temp[user_id].get("filters", {})

        edit_message(chat_id, message_id, "<b>⏳ Ищу...</b>")

        # Фильтруем
        results = items
        for trait_key, value in filters.items():
            filtered = []
            for item in results:
                attrs_list = item.get("metadata", {}).get("attributes", [])
                for attr in attrs_list:
                    if attr.get("trait_type") == trait_key and str(attr.get("value", "")) == value:
                        filtered.append(item)
                        break
            results = filtered

        if not results:
            edit_message(chat_id, message_id,
                "<b>❌ Ничего не найдено с такими фильтрами.\nПопробуй изменить параметры.</b>",
                [[{"text": "🔄 Попробовать снова", "callback_data": f"col_{user_temp[user_id].get('collection', '')}"}]]
            )
            return

        # Показываем первые 100
        show = results[:100]
        filter_text = " | ".join([f"{k}: {v}" for k, v in filters.items()]) if filters else "без фильтров"

        chunks = [show[i:i+25] for i in range(0, len(show), 25)]
        edit_message(chat_id, message_id,
            f"<b>✅ Найдено: {len(results)} NFT</b>\n"
            f"<b>Фильтры:</b> {filter_text}\n\n"
            f"Показываю первые {len(show)}:"
        )

        for idx, chunk in enumerate(chunks):
            text = f"<b>Список {idx*25+1}-{idx*25+len(chunk)}:</b>\n\n"
            for i, item in enumerate(chunk, idx*25+1):
                owner = item.get("owner", {})
                username = ""
                if owner:
                    user_info = owner.get("user", {})
                    if user_info:
                        username = user_info.get("username", "")
                name = item.get("metadata", {}).get("name", "NFT")
                if username:
                    text += f"{i}. @{username} — {name}\n"
                else:
                    addr = owner.get("address", "???")[:8] if owner else "???"
                    text += f"{i}. <code>{addr}...</code> — {name}\n"
            send_message(chat_id, text)
            time.sleep(0.3)

        send_message(chat_id,
            "<b>✅ Готово!</b>",
            main_keyboard()
        )
        return

def main():
    print("NFT Finder Bot started!")
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
