import json

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

print(f"Total Unique OnlyVeda Products: {len(products)}\n")

for i, p in enumerate(products, 1):
    srcs = ", ".join(p.get('sources', ['Catalog']))
    cat = p.get('category', 'General')
    price = p.get('price_inr', '499')
    print(f"{i:3d}. {p['name']} | Cat: {cat} | Price: Rs. {price} | Sources: [{srcs}]")
