import os
import requests
import time
import json
import random

TOKEN = os.getenv('BOT_TOKEN')

GETGEMS_API = "https://api.getgems.io/graphql"

# Разные User-Agent для ротации
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

def get_headers():
    return {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "User-Agent": random.choice(USER_AGENTS),
        "Origin": "https://getgems.io",
        "Referer": "https://getgems.io/collection/" ,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Connection": "keep-alive",
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

# Используем сессию с куками как браузер
session = requests.Session()
cache = {}

def init_session():
    """Инициализируем сессию — заходим на сайт как браузер"""
    try:
        session.get(
            "https://getgems.io",
            headers={
                "User-Agent": random.choice(USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            timeout=15
        )
        time.sleep(1)
        print("Сессия инициализирована")
    except Exception as e:
        print(f"Init session error: {e}")

def getgems_query(query, variables=None, retry=3):
    for attempt in range(retry):
        try:
            r = session.post(
                GETGEMS_API,
                json={"query": query, "variables": variables or {}},
                headers=get_headers(),
                timeout=20
            )
            print(f"  API status: {r.status_code}")
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 403:
                print(f"  403 — пробуем переинициализировать сессию...")
                init_session()
                time.sleep(2 + attempt * 2)
            else:
                time.sleep(1)
        except Exception as e:
            print(f"  Request error: {e}")
            time.sleep(2)
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
            __typename
            isScam
            address
            ... on NftItemOwnerUser {
              user {
                address
                name
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
    display_name = (user.get("name") or "").strip()

    if not telegram_username and not display_name:
        return None

    attrs = {a["traitType"]: a["value"] for a in item.get("attributes", [])}

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
        "model":             attrs.get("Model", ""),
        "backdrop":          attrs.get("Backdrop", ""),
        "symbol":            attrs.get("Symbol", ""),
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

    print(f"\nLoading {col_name}...")

    for page in range(10):
        items, cursor = get_collection_items(addr, limit=50, cursor=cursor)
        if not items:
            print(f"  Нет items на странице {page+1}, стоп")
            break

        for item in items:
            parsed = parse_item(item, col_name)
            if parsed:
                all_items.append(parsed)

        print(f"  Страница {page+1}: всего с username = {len(all_items)}")

        if not cursor or len(all_items) >= max_items:
            break
        time.sleep(random.uniform(1.0, 2.5))  # случайная задержка

    cache[col_key] = all_items
    print(f"  Итого: {len(all_items)}")
    return all_items


def load_all():
    all_items = []
    for key in COLLECTIONS:
        items = load_collection(key)
        all_items.extend(items)
    return all_items


def find_users_with_nft(min_nfts=1):
    all_items = load_all()
    users = {}
    for item in all_items:
        key = item["telegram_username"] or item["display_name"]
        if not key:
            continue
        if key not in users:
            users[key] = []
        users[key].append(item)
    return {u: nfts for u, nfts in users.items() if len(nfts) >= min_nfts}


def save_to_json(users: dict, filename="nft_users.json"):
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
    print(f"\n💾 Сохранено в {filename} ({len(output)} пользователей)")


def print_users_report(min_nfts=1):
    init_session()  # сначала инициализируем сессию

    users = find_users_with_nft(min_nfts=min_nfts)

    print(f"\n{'='*60}")
    print(f"Найдено пользователей с NFT и username: {len(users)}")
    print(f"{'='*60}\n")

    for username, nfts in sorted(users.items(), key=lambda x: -len(x[1])):
        tg   = nfts[0]["telegram_username"]
        link = f"@{tg}" if tg else username
        print(f"{link} — {len(nfts)} NFT:")
        for nft in nfts:
            sale_info = f" | 💰 {nft['price']:.2f} TON" if nft["for_sale"] else ""
            print(f"  • {nft['collection']} — {nft['nft_name']}{sale_info}")
        print()

    save_to_json(users)


if __name__ == "__main__":
    print_users_report(min_nfts=1)
