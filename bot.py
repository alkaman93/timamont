import requests
import json

GETGEMS_API = "https://api.getgems.io/graphql"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Origin": "https://getgems.io",
    "Referer": "https://getgems.io/",
}

# Берём одну коллекцию для теста
ADDR = "EQAOl3-PQpFdpOBfLT7MoB7qNuqOYBRbGXhzRBrdPE5B"  # Astral Shard

query = """
query GetCollectionItems($collectionAddress: String!, $first: Int!) {
  nftItemsByCollection(
    collectionAddress: $collectionAddress
    first: $first
  ) {
    cursor
    items {
      name
      address
      owner {
        __typename
        isScam
        address
        ... on NftItemOwnerUser {
          user {
            __typename
            address
            name
            telegramUsername
            username
          }
        }
      }
    }
  }
}
"""

r = requests.post(
    GETGEMS_API,
    json={"query": query, "variables": {"collectionAddress": ADDR, "first": 5}},
    headers=HEADERS,
    timeout=20
)

print("Status:", r.status_code)
data = r.json()

# Печатаем сырой ответ первых 5 items
items = data.get("data", {}).get("nftItemsByCollection", {}).get("items", [])
print(f"\nПришло items: {len(items)}")
for i, item in enumerate(items):
    print(f"\n--- Item {i+1} ---")
    print(json.dumps(item, indent=2, ensure_ascii=False))
