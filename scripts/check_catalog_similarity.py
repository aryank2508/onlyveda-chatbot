import json

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

print(f"Total products: {len(products)}")

# Check any products with similar names
for i in range(len(products)):
    for j in range(i + 1, len(products)):
        p1 = products[i]['name']
        p2 = products[j]['name']
        # simple similarity check
        s1 = set(p1.lower().split())
        s2 = set(p2.lower().split())
        overlap = len(s1 & s2)
        if overlap >= 3 and abs(len(s1) - len(s2)) <= 2:
            print(f"Potential similarity: '{p1}' vs '{p2}'")
