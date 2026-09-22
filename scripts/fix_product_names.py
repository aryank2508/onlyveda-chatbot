"""Fix wrong product names that slipped through during import."""
import json

PROTOCOLS_PATH = 'data/disease_protocols.json'
PRODUCTS_PATH = 'data/products.json'

# Name corrections: wrong_name -> correct_name
CORRECTIONS = {
    "OnlyVeda Pro Wal": "OnlyVeda Prowal Synbiotic Gut Restorer",
    "OnlyVeda Maha Yograj Guggul": "OnlyVeda Mahayograj Guggul",
    "OnlyVeda Strnus Oil": "OnlyVeda Strenus Herbal Massage Oil",
    "OnlyVeda Hadjoj": "OnlyVeda Hadjod Bone Healer",
}

with open(PROTOCOLS_PATH) as f:
    protocols = json.load(f)

with open(PRODUCTS_PATH) as f:
    products = json.load(f)

# Fix in protocols
fixes_in_protocols = 0
for disease, data in protocols.items():
    for supp in data.get('supplements', []):
        if supp['name'] in CORRECTIONS:
            old = supp['name']
            supp['name'] = CORRECTIONS[old]
            fixes_in_protocols += 1

# Fix in products: remove wrong-named ones (they'll be replaced if needed)
products_to_remove = set(CORRECTIONS.keys())
products = [p for p in products if p['name'] not in products_to_remove]

print(f"Fixed {fixes_in_protocols} supplement references in protocols")
print(f"Removed {len(CORRECTIONS)} wrong-named products from products.json")

with open(PROTOCOLS_PATH, 'w', encoding='utf-8') as f:
    json.dump(protocols, f, ensure_ascii=False, indent=2)

with open(PRODUCTS_PATH, 'w', encoding='utf-8') as f:
    json.dump(products, f, ensure_ascii=False, indent=2)

print(f"Total protocols: {len(protocols)}")
print(f"Total products:  {len(products)}")
print("Cleanup done!")
