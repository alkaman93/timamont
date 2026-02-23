import os
import requests
import time
import json

TOKEN = os.getenv('BOT_TOKEN')

GETGEMS_API = "https://api.getgems.io/graphql"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Origin": "https://getgems.io",
    "Referer": "https://getgems.io/",
}

COLLECTIONS = {
    "astralshard":  {"name": "🔮 Astral Shard",  "addr": "EQAOl3-PQpFdpOBfLT7MoB7qNuqOYBRbGXhzRBrdPE5B"},
    "homemadecake": {"name": "🎂 Homemade Cake", "addr": "EQAjqVfbcTMPvvJKGdHMjJf6-9NiKIiqXlSJfZIfKlMJqOIR"},
    "lolpop":       {"name": "🍭 Lol Pop",        "addr": "EQC6zjid8vJNEWqcXk10XjsdDLRKbcPZzbHusuEW6FokOWIm"},
    "signetring":   {"name": "💍 Signet Ring",    "addr": "EQCrGA9slCoksgD-NyRDjtHySKN0Ts8k6hdueJkUkZZdD4_K"},
    "lovepotion":   {"name": "🧪 Love Potion",    "addr": "EQD7yDu2WCgd9Uzx1dF_DQkWK7IZJJ4Mp9M9g1rGUUiQE43m"},
    "sakura":       {"name": "🌸 Sakura Flower",  "addr": "EQDIruSTyxvq60gUH8j2kkj3qzoBrBaJy9WkKbeNNRasWe4j"},
    "cookieheart":  {"name": "🍪 Cookie Heart",   "addr": "EQAqtF5tZIgNZal80ChzdPMvZCN8OEbJCVJPn_0xNPghQJPW"},
    "bdaycandle":   {"name": "🕯 B-Day Candle",   "addr": "EQBpMhoMDsN0DjQZXFFBup7l5gbt-UtMzTHN5qaqQtc90CLD"},
}

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
    variables = {"collectionAddress": collection_addr, "first": limit}
    if cursor:
        variables["after"] = cursor

    data = getgems_query(query, variables)
    result = data.get("data", {}).get("nftItemsByCollection", {})
    return result.get("items", []), result.get("cursor")


def parse_item(item, col_name):
    owner = item.get("owner", {}) or {}
    user = owner.get("user", {}) or {}

    telegram_username = (user.get("telegramUsername") or "").strip()
    display_name = (user.get("username") or "").strip()

    # Пропускаем если нет ни юзернейма ни имени
    if not telegram_username and not display_name:
        return None

    attrs = {a["traitType"]: a["value"] for a in item.get("attributes", [])}
    model    = attrs.get("Model",    attrs.get("model",    ""))
    backdrop = attrs.get("Backdrop", attrs.get("backdrop", ""))
    symbol   = attrs.get("Symbol",   attrs.get("symbol",   ""))

    price = 0
    sale = item.get("sale")
    if sale and sale.get("fullPrice"):
        try:
            price = int(sale["fullPrice"]) / 1e9
        except:
            pass

    return {
        "telegram_username": telegram_username,
        "display_name":      display_name,
        "nft_name":          item.get("name", ""),
        "collection":        col_name,
        "model":             model,
        "backdrop":          backdrop,
        "symbol":            symbol,
        "price":             price,
        "for_sale":          price > 0,
    }


def load_collection(col_key, max_items=500):
    if col_key in cache:
        return cache[col_key]

    col      = COLLECTIONS[col_key]
    addr     = col["addr"]
    col_name = col["name"]
    all_items = []
    cursor = None

    print(f"Loading {col_name}...")

    for page in range(10):  # до 10 страниц по 50 = 500 NFT
        items, cursor = get_collection_items(addr, limit=50, cursor=cursor)
        if not items:
            break

        for item in items:
            parsed = parse_item(item, col_name)
            if parsed:
                all_items.append(parsed)

        print(f"  Страница {page + 1}: найдено {len(all_items)} пользователей")

        if not cursor or len(all_items) >= max_items:
            break
        time.sleep(0.5)

    cache[col_key] = all_items
    print(f"  Итого с username: {len(all_items)}\n")
    return all_items


def load_all():
    all_items = []
    for key in COLLECTIONS:
        items = load_collection(key)
        all_items.extend(items)
    return all_items


def find_users_with_nft(min_nfts=1):
    """
    Возвращает словарь: username -> список NFT
    Только люди у которых есть Telegram username и хотя бы min_nfts NFT
    """
    all_items = load_all()

    users = {}
    for item in all_items:
        key = item["telegram_username"] or item["display_name"]
        if not key:
            continue
        if key not in users:
            users[key] = []
        users[key].append(item)

    # Фильтр по минимальному кол-ву NFT
    filtered = {u: nfts for u, nfts in users.items() if len(nfts) >= min_nfts}
    return filtered


def save_to_json(users: dict, filename="nft_users.json"):
    """Сохраняет результат в JSON файл"""
    output = []
    for username, nfts in sorted(users.items(), key=lambda x: -len(x[1])):
        tg = nfts[0]["telegram_username"]
        output.append({
            "username":      username,
            "telegram_link": f"@{tg}" if tg else None,
            "nft_count":     len(nfts),
            "nfts":          nfts,
        })

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"💾 Сохранено в {filename}")


def print_users_report(min_nfts=1):
    users = find_users_with_nft(min_nfts=min_nfts)

    print(f"\n{'='*60}")
    print(f"Найдено пользователей с NFT и username: {len(users)}")
    print(f"{'='*60}\n")

    # Сортируем по количеству NFT (больше = выше)
    for username, nfts in sorted(users.items(), key=lambda x: -len(x[1])):
        tg   = nfts[0]["telegram_username"]
        link = f"@{tg}" if tg else username

        print(f"{link} — {len(nfts)} NFT:")
        for nft in nfts:
            sale_info = f" | 💰 {nft['price']:.2f} TON" if nft["for_sale"] else ""
            print(f"  • {nft['collection']} — {nft['nft_name']}{sale_info}")
        print()

    # Сохраняем в JSON
    save_to_json(users)


if __name__ == "__main__":
    print_users_report(min_nfts=1)
