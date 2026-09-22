import json
import re

with open('data/raw_collected_sources.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

web = data['website_products']
csv_prods = data['csv_products']
excel_prods = data['excel_products']

print(f"Total scraped from website: {len(web)}")
print(f"Unique entries in CSV: {len(csv_prods)}")
print(f"Unique entries in Excel: {len(excel_prods)}")

print("\n--- SAMPLE WEBSITE PRODUCTS (First 30) ---")
for p in web[:30]:
    print(f"  [{p['category']}] {p['name']} (Rs. {p['price']})")

print("\n--- ALL CSV ENTRIES (48) ---")
for p in csv_prods:
    print(f"  {p}")

print("\n--- ALL EXCEL ENTRIES (103) ---")
for p in excel_prods:
    print(f"  {p}")
