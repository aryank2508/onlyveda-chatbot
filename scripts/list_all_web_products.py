import json
import re

with open('data/raw_collected_sources.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

web = data['website_products']
for p in web:
    # fix price
    raw_price = p['price']
    clean = re.sub(r'^8377', '', raw_price)
    p['price'] = clean

print(f"Total website products: {len(web)}\n")

categories = {}
for p in web:
    cat = p['category']
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(p)

for cat, prods in categories.items():
    print(f"=== {cat} ({len(prods)}) ===")
    for p in prods:
        print(f"  • {p['name']} (Price: Rs. {p['price']}) -> {p['link']}")
    print()
