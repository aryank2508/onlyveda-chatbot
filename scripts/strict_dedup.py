import json

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

print(f"Products before strict deduplication: {len(products)}")

deduped = {}
for p in products:
    name = p['name'].strip()
    if name not in deduped:
        deduped[name] = p
    else:
        # Merge fields
        existing = deduped[name]
        for src in p.get('sources', []):
            if 'sources' not in existing:
                existing['sources'] = []
            if src not in existing['sources']:
                existing['sources'].append(src)
        if p.get('link') and not existing.get('link'):
            existing['link'] = p['link']
        if p.get('key_ingredients') and not existing.get('key_ingredients'):
            existing['key_ingredients'] = p['key_ingredients']
        if p.get('benefits') and len(p['benefits']) > len(existing.get('benefits', '')):
            existing['benefits'] = p['benefits']

final_list = sorted(deduped.values(), key=lambda x: x['name'])
print(f"Products after strict exact name deduplication: {len(final_list)}")

# Now check near-duplicates (e.g. slight phrasing differences)
print("\nChecking for near-duplicates:")
for i in range(len(final_list)):
    for j in range(i + 1, len(final_list)):
        n1 = final_list[i]['name']
        n2 = final_list[j]['name']
        if n1.lower().replace('-', ' ').replace('  ', ' ') == n2.lower().replace('-', ' ').replace('  ', ' '):
            print(f"  Exact match ignoring punctuation: '{n1}' vs '{n2}'")

# Save cleaned
with open('data/products.json', 'w', encoding='utf-8') as f:
    json.dump(final_list, f, indent=2, ensure_ascii=False)
