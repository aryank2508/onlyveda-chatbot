import json
import re

# Load raw collected data
with open('data/raw_collected_sources.json', 'r', encoding='utf-8') as f:
    raw = json.load(f)

web = raw['website_products']
csv_prods = raw['csv_products']
excel_prods = raw['excel_products']

with open('data/products.json', 'r', encoding='utf-8') as f:
    current_products = json.load(f)

# Let's clean prices from web
for p in web:
    raw_price = str(p.get('price', ''))
    clean_p = re.sub(r'^8377', '', raw_price)
    p['price'] = clean_p if clean_p else '499'

# Master dictionary of canonical products
# Key: canonical normalized lowercase key
# Value: product dict
master_products = {}

def clean_key(name):
    n = name.lower()
    n = re.sub(r'onlyveda\s+', '', n)
    n = re.sub(r'\b(caps?|tablets?|tab|capsules?|syrup|sy|liquid|powder|cream|ointment|drops?|spray|kit|in jar|10x10|30|60|120|200ml|500ml|1 ltr|50ml|25 gm|30 gm|100ml|450ml|250ml|75gm|100 gm|4x75gm|4x100gm)\b', '', n)
    n = re.sub(r'[^a-z0-9]', '', n)
    return n

# 1. First, register all current products in products.json
for p in current_products:
    name = p['name']
    if not name.startswith("OnlyVeda "):
        name = f"OnlyVeda {name}"
    k = clean_key(name)
    master_products[k] = {
        "name": name,
        "category": p.get("category", "Nutraceutical"),
        "key_ingredients": p.get("key_ingredients", []),
        "benefits": p.get("benefits", ""),
        "dosage_and_usage": p.get("dosage_and_usage", "1-0-1 (as directed by healthcare advisor)"),
        "price_inr": str(p.get("price_inr", "499")),
        "size": p.get("size", "Standard Pack"),
        "source": "Spreadsheet/Database"
    }

print(f"Loaded {len(master_products)} products from current catalog.")

# 2. Map and add all website products
added_from_web = 0
matched_web = 0

for p in web:
    raw_name = p['name']
    # Build clean canonical OnlyVeda name
    canonical_name = raw_name
    if not canonical_name.startswith("OnlyVeda "):
        canonical_name = f"OnlyVeda {canonical_name}"
    
    k = clean_key(canonical_name)
    
    if k in master_products:
        matched_web += 1
        # Update price, link, category if better
        if p.get('price'):
            master_products[k]['price_inr'] = p['price']
        if p.get('link'):
            master_products[k]['link'] = p['link']
        if p.get('category'):
            master_products[k]['category'] = p['category']
    else:
        # Check if partial match exists
        found_match = False
        for mk, mp in master_products.items():
            if k in mk or mk in k and len(min(k, mk)) >= 5:
                matched_web += 1
                found_match = True
                if p.get('price'):
                    mp['price_inr'] = p['price']
                if p.get('link'):
                    mp['link'] = p['link']
                break
        
        if not found_match:
            added_from_web += 1
            master_products[k] = {
                "name": canonical_name,
                "category": p.get("category", "General"),
                "key_ingredients": [],
                "benefits": f"OnlyVeda {raw_name} - authentic herbal & wellness product from OnlyVeda catalog.",
                "dosage_and_usage": "As directed on pack or by healthcare advisor",
                "price_inr": str(p.get("price", "499")),
                "size": "Standard Pack",
                "link": p.get("link", ""),
                "source": "Website"
            }

print(f"Website products matched with existing: {matched_web}")
print(f"New website products added: {added_from_web}")
print(f"Total master products after website: {len(master_products)}")

# 3. Check CSV products
print(f"\nChecking CSV products ({len(csv_prods)}):")
for cp in csv_prods:
    k = clean_key(cp)
    found = False
    for mk in master_products.keys():
        if k in mk or mk in k and len(min(k, mk)) >= 4:
            found = True
            break
    if not found:
        print(f"  Unmatched CSV: {cp}")

# 4. Check Excel products
print(f"\nChecking Excel products ({len(excel_prods)}):")
excel_unmatched = []
for ep in excel_prods:
    k = clean_key(ep)
    found = False
    for mk in master_products.keys():
        if k in mk or mk in k and len(min(k, mk)) >= 4:
            found = True
            break
    if not found:
        excel_unmatched.append(ep)

print(f"Unmatched Excel count: {len(excel_unmatched)}")
for u in excel_unmatched:
    print(f"  Unmatched Excel: {u}")
