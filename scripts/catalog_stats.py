import json
from collections import Counter

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

print(f"Total Unique OnlyVeda Products in Master Database: {len(products)}")

# Categories
cats = Counter(p.get('category', 'General') for p in products)
print("\n--- Products by Category ---")
for cat, count in cats.most_common():
    print(f"  {cat}: {count} products")

# Sources
sources_count = Counter()
for p in products:
    srcs = p.get('sources', ['Unknown'])
    for s in srcs:
        sources_count[s] += 1

print("\n--- Products presence per Source ---")
for src, count in sources_count.most_common():
    print(f"  {src}: {count} products")

# Combinations
combo_count = Counter()
for p in products:
    combo = tuple(sorted(p.get('sources', ['Unknown'])))
    combo_count[combo] += 1

print("\n--- Source Overlap Combinations ---")
for combo, count in combo_count.most_common():
    print(f"  {count} products found in: {' + '.join(combo)}")
