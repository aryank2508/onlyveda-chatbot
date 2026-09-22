import json
import re

with open('data/raw_collected_sources.json', 'r', encoding='utf-8') as f:
    raw = json.load(f)

web = raw['website_products']
csv_prods = raw['csv_products']
excel_prods = raw['excel_products']

print(f"Total Scraped Website Products: {len(web)}")
print(f"Total CSV Raw Entries: {len(csv_prods)}")
print(f"Total Excel Raw Entries: {len(excel_prods)}")

# Current products.json
with open('data/products.json', 'r', encoding='utf-8') as f:
    current_catalog = json.load(f)

print(f"Total Current Products in Chatbot: {len(current_catalog)}")
