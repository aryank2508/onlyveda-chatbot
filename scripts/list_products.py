import json
p = json.load(open('data/products.json'))
print(f'Existing products: {len(p)}')
for x in p:
    print(f"  {x['name']}")
