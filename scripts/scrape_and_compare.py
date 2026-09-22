import urllib.request
import re
import csv
import openpyxl
import json
import time

# ==========================================
# PART 1: SCRAPE ONLYVEDA WEBSITE
# ==========================================
print("=== 1. SCRAPING ALL PRODUCTS FROM https://onlyvedaa.com ===")

categories = [
    (39, "Agriculture Product", 1),
    (31, "Ayurvedic", 4),
    (32, "Cosmetic", 1),
    (34, "Herbo Nutraceuticals", 3),
    (38, "Home Care", 1),
    (35, "OTC", 1),
    (44, "Piyo", 1),
    (36, "Protein Powder", 1),
    (37, "Spray", 1),
]

website_products = []
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for cat_id, cat_name, max_pages in categories:
    for page in range(1, max_pages + 1):
        url = f"https://onlyvedaa.com/product/{cat_id}?page={page}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                # Find all product-card divs
                # Pattern: <h3 class="product-title">(.*?)</h3>
                # Also price: <span class="current-price">(.*?)</span>
                # Also link: href="https://onlyvedaa.com/product-info/..."
                cards = re.findall(
                    r'<div class="product-card">.*?<a\s+href="([^"]*product-info/[^"]*)".*?<h3 class="product-title">(.*?)</h3>.*?<span class="current-price">(.*?)</span>',
                    html,
                    re.DOTALL
                )
                print(f"[{cat_name}] Page {page}: found {len(cards)} products")
                for link, title, price in cards:
                    clean_title = re.sub(r'<[^>]+>', '', title).strip()
                    clean_price = re.sub(r'[^\d]', '', price).strip()
                    website_products.append({
                        "name": clean_title,
                        "category": cat_name,
                        "price": clean_price,
                        "link": link.strip(),
                        "source": "Website"
                    })
        except Exception as e:
            print(f"Error fetching {url}: {e}")
        time.sleep(0.5)

print(f"Total products scraped from website: {len(website_products)}")

# ==========================================
# PART 2: EXTRACT FROM diseases_wise_1.csv
# ==========================================
print("\n=== 2. EXTRACTING FROM diseases_wise_1.csv ===")
csv_path = r'C:\Users\aryan\Desktop\onlyveda_chatbot\diseases_wise_1.csv'
csv_products = set()

with open(csv_path, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        supp = row.get('Supplement') or row.get('supplement') or ''
        supp = supp.strip()
        if supp and supp.lower() not in ('none', 'nan', ''):
            # Split slashes if multiple products like 'satwik / trifala'
            csv_products.add(supp)

print(f"Unique raw supplement entries in CSV: {len(csv_products)}")

# ==========================================
# PART 3: EXTRACT FROM disease and treatment database (2).xlsx
# ==========================================
print("\n=== 3. EXTRACTING FROM disease and treatment database (2).xlsx ===")
excel_path = r'C:\Users\aryan\Desktop\onlyveda_chatbot\disease and treatment database (2).xlsx'
wb = openpyxl.load_workbook(excel_path)
ws = wb['Sheet1']

excel_products = set()
for row in ws.iter_rows(min_row=2, values_only=True):
    supp = row[3]
    if supp and str(supp).strip() and str(supp).strip().lower() not in ('none', 'nan', ''):
        excel_products.add(str(supp).strip())

print(f"Unique raw supplement entries in Excel: {len(excel_products)}")

# Save raw collected data to json for detailed analysis
with open('data/raw_collected_sources.json', 'w', encoding='utf-8') as f:
    json.dump({
        "website_products": website_products,
        "csv_products": sorted(list(csv_products)),
        "excel_products": sorted(list(excel_products))
    }, f, indent=2, ensure_ascii=False)

print("\nRaw data saved to data/raw_collected_sources.json")
