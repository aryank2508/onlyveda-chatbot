import json
import re
import csv
import openpyxl

# Master Synonym / Alias Dictionary: maps any raw name / spelling / variation -> Canonical OnlyVeda Product Name
SYNONYMS = {
    # Heart & Vitals
    "linopress": "OnlyVeda Linopress",
    "linopress 30 caps in jar": "OnlyVeda Linopress",
    "l arginine": "OnlyVeda L-Arginine Plus",
    "l arginine plus": "OnlyVeda L-Arginine Plus",
    "l arginie": "OnlyVeda L-Arginine Plus",
    "l-arginine 30 cap in jar": "OnlyVeda L-Arginine Plus",
    "arjuna tablet": "OnlyVeda Terminalia Arjuna Extract",
    "arjun 120 tab in jar": "OnlyVeda Terminalia Arjuna Extract",
    "arjuna": "OnlyVeda Terminalia Arjuna Extract",
    "heart detox plus": "OnlyVeda Heart Detox Plus",
    "coenzyme q10": "OnlyVeda CoQ10 (Coenzyme Q10)",
    "co enzyme q 10": "OnlyVeda CoQ10 (Coenzyme Q10)",
    "omega 3": "OnlyVeda Omega-3 Fish Oil",
    "omega 3 capsule": "OnlyVeda Omega-3 Fish Oil",

    # Ashyuka / General Tonics
    "ashyuka": "OnlyVeda Ashyuka Plus Syrup",
    "ashyuka plus": "OnlyVeda Ashyuka Plus Syrup",
    "ashyuka health drink": "OnlyVeda Ashyuka Plus Syrup",
    "new ashyuka plus sy 450ml": "OnlyVeda Ashyuka Plus Syrup",

    # Immunity & Essentials
    "immuferin": "OnlyVeda Immuferin Immuno-Shield",
    "immufein": "OnlyVeda Immuferin Immuno-Shield",
    "immufeirn": "OnlyVeda Immuferin Immuno-Shield",
    "immuferi": "OnlyVeda Immuferin Immuno-Shield",
    "immuferin 30 caps in jar": "OnlyVeda Immuferin Immuno-Shield",
    "2 caps of immuferin in soframycin cream": "OnlyVeda Immuferin Immuno-Shield",
    "active 365": "OnlyVeda Active 365 Daily Essential",
    "active 365`": "OnlyVeda Active 365 Daily Essential",
    "active 365 60 caps": "OnlyVeda Active 365 Daily Essential",
    "daily complete multivitamin": "OnlyVeda Daily Complete Multivitamin",
    "multi vitamin men/women": "OnlyVeda Daily Complete Multivitamin",
    "multivitamin for men/women": "OnlyVeda Daily Complete Multivitamin",
    "multivitamin men/ women": "OnlyVeda Daily Complete Multivitamin",
    "multivitamin men/women": "OnlyVeda Daily Complete Multivitamin",
    "multivitamin for men": "OnlyVeda Daily Complete Multivitamin",
    "multivitamin effer. tablets for men": "OnlyVeda Multivitamin Effervescent For Men",
    "multivitamin effer. tablets for women": "OnlyVeda Multivitamin Effervescent For Women",
    "multivitamin for kids gummies": "OnlyVeda Multivitamin For Kids Gummies",
    "multivitamin for women": "OnlyVeda Daily Complete Multivitamin Women",
    "multivtiamin for women": "OnlyVeda Daily Complete Multivitamin Women",
    "multivitamin for women 30 tab": "OnlyVeda Daily Complete Multivitamin Women",
    "vitamin c": "OnlyVeda Natural Vitamin C + Zinc",
    "vitamin d3": "OnlyVeda Pure Vitamin D3 Chewables",
    "wal d3": "OnlyVeda Wal D3 Sublingual Spray",

    # Bones, Joints & Pain
    "serronil": "OnlyVeda Serronil Joint Care",
    "serronil 30 caps": "OnlyVeda Serronil Joint Care",
    "calcimus": "OnlyVeda Calcimus Coral Calcium Complex",
    "calcimus 30 chewable tab": "OnlyVeda Calcimus Coral Calcium Complex",
    "calciumus": "OnlyVeda Calciumus Forte",
    "hadjod": "OnlyVeda Hadjod Bone Healer",
    "hadjoj": "OnlyVeda Hadjod Bone Healer",
    "hadjod tab": "OnlyVeda Hadjod Bone Healer",
    "strenus caps": "OnlyVeda Strenus Pain Relief Capsules",
    "strenus capsule": "OnlyVeda Strenus Pain Relief Capsules",
    "strenus 10x10 caps": "OnlyVeda Strenus Pain Relief Capsules",
    "strenus oil": "OnlyVeda Strenus Herbal Massage Oil",
    "strnus oil": "OnlyVeda Strenus Herbal Massage Oil",
    "new strenus oil 50ml": "OnlyVeda Strenus Herbal Massage Oil",
    "strenus oil 50ml": "OnlyVeda Strenus Herbal Massage Oil",
    "ashwagandha tablet": "OnlyVeda KSM-66 Ashwagandha Pure Tablet",
    "ashwagandha 120 tab in jar": "OnlyVeda KSM-66 Ashwagandha Pure Tablet",
    "ksm 66": "OnlyVeda KSM-66 Ashwagandha Pure Tablet",
    "mahayograj": "OnlyVeda Mahayograj Guggul",
    "maha yograj guggul": "OnlyVeda Mahayograj Guggul",
    "maha yograj guggal tab": "OnlyVeda Mahayograj Guggul",

    # Respiratory & Lungs
    "respitone": "OnlyVeda Respitone Pulmonary Shield",
    "respitone 30 caps in jar": "OnlyVeda Respitone Pulmonary Shield",
    "n acetyl cysteine": "OnlyVeda N-Acetyl Cysteine (NAC 600mg)",
    "n acetyl cystein": "OnlyVeda N-Acetyl Cysteine (NAC 600mg)",
    "n acetyl cystein (nac)": "OnlyVeda N-Acetyl Cysteine (NAC 600mg)",
    "lung detox 30 capsules": "OnlyVeda Lung Detox Capsules",
    "piyo lung detox effer tab": "OnlyVeda Piyo Lung Detox Effervescent Tablet",
    "walinctus": "OnlyVeda Walinctus Herbal Cough Syrup",
    "walinctus cough syrup": "OnlyVeda Walinctus Herbal Cough Syrup",
    "walictus cough syrup": "OnlyVeda Walinctus Herbal Cough Syrup",
    "walinctus syrup 100ml": "OnlyVeda Walinctus Herbal Cough Syrup",
    "shitopaladi": "OnlyVeda Sitopaladi Churna",
    "sitopaladi 120 tab in jar": "OnlyVeda Sitopaladi Churna",
    "throatwal": "OnlyVeda Throatwal Soothing Lozenges & Gargle",
    "throatwal spray 30ml": "OnlyVeda Throatwal Spray",
    "kanchanar guggul": "OnlyVeda Kanchanar Guggul Traditional",
    "kanchnar 120 tab in jar": "OnlyVeda Kanchanar Guggul Traditional",

    # Digestion, Liver, Gut & Piles
    "hepatreat": "OnlyVeda Hepatreat Hepatic Care",
    "hepatreat syrup": "OnlyVeda Hepatreat Hepatic Care",
    "hepatreat tablet": "OnlyVeda Hepatreat Hepatic Tablets",
    "hepatreat 30 tab in jar": "OnlyVeda Hepatreat Hepatic Tablets",
    "rhiza": "OnlyVeda Rhiza Mucosal Gut Shield",
    "rhiza syrup": "OnlyVeda Rhiza Mucosal Gut Shield",
    "avipattikar": "OnlyVeda Avipattikar Pitta-Balance Tablet",
    "avipathikar tablet": "OnlyVeda Avipattikar Pitta-Balance Tablet",
    "avipattikar 120 tab in jar": "OnlyVeda Avipattikar Pitta-Balance Tablet",
    "laxia": "OnlyVeda Laxia Gentle Overnight Colon Cleanse",
    "laxia powder": "OnlyVeda Laxia Gentle Overnight Colon Cleanse",
    "triphala": "OnlyVeda Triphala Satwik Pure Digestive Detox",
    "trifala/satwik": "OnlyVeda Triphala Satwik Pure Digestive Detox",
    "satwik / trifala": "OnlyVeda Triphala Satwik Pure Digestive Detox",
    "triphala 120 tab in jar": "OnlyVeda Triphala Satwik Pure Digestive Detox",
    "satvik 120 tab in jar": "OnlyVeda Satvik Pure Digestive Detox",
    "prowal": "OnlyVeda Prowal Synbiotic Gut Restorer",
    "pro wal": "OnlyVeda Prowal Synbiotic Gut Restorer",
    "prowell 30 caps in jar": "OnlyVeda Prowal Synbiotic Gut Restorer",
    "milk thistle": "OnlyVeda Milk Thistle Silymarin Detox",
    "milk thistle capsule": "OnlyVeda Milk Thistle Silymarin Detox",
    "liver detox": "OnlyVeda Liver Detox Formula",
    "liver detox 30 tab in jar": "OnlyVeda Liver Detox Formula",
    "piyo liver detox effer tab": "OnlyVeda Piyo Liver Detox Effervescent Tablet",
    "anurect caps": "OnlyVeda Anurect Piles Capsules",
    "anurect 30 caps in jar": "OnlyVeda Anurect Piles Capsules",
    "anurect ointment": "OnlyVeda Anurect Piles Ointment",
    "anurect ointmnet 25 gm": "OnlyVeda Anurect Piles Ointment",
    "kam dudha ras": "OnlyVeda Kamdudha Ras",
    "kamdudha ras 120 tab in jar": "OnlyVeda Kamdudha Ras",
    "arogya vardhini": "OnlyVeda Arogyavardhini Vati",
    "arogyavardhini 120 tab in jar": "OnlyVeda Arogyavardhini Vati",
    "walzyme": "OnlyVeda Walzyme Digestive Enzymes",
    "walzyme syrup": "OnlyVeda Walzyme Digestive Enzymes",

    # Kidney & Urinary
    "stowip": "OnlyVeda Stowip Kidney & Urinary Kit",
    "stowip kit": "OnlyVeda Stowip Kidney & Urinary Kit",
    "kidney detox": "OnlyVeda Kidney Detox Formula",
    "kidney detox 30 caps in jar": "OnlyVeda Kidney Detox Formula",
    "punch tulsi": "OnlyVeda Panch Tulsi Drops",
    "cranberry caps": "OnlyVeda Cranberry Extract Capsules",
    "cranberry-amla 30 cap in jar": "OnlyVeda Cranberry Extract Capsules",
    "chandra prabha tablet": "OnlyVeda Chandraprabha Vati",
    "chandraprabha 120 tab in jar": "OnlyVeda Chandraprabha Vati",
    "piyo uti effer. tab": "OnlyVeda Piyo UTI Effervescent Tablet",

    # Diabetes & Weight
    "blood sugar control": "OnlyVeda Blood Sugar Control Formula",
    "diabetic care": "OnlyVeda Blood Sugar Control Formula",
    "marsulin syrup 200ml": "OnlyVeda Marsulin Diabetic Syrup",
    "marsulin 30 tab in jar": "OnlyVeda Marsulin Diabetic Tablets",
    "mamejava ghan 120 tab in jar": "OnlyVeda Mamejava Ghan Tablets",
    "piyo diabetic care effer tab": "OnlyVeda Piyo Diabetic Care Effervescent Tablet",
    "biomelt liquid": "OnlyVeda Biomelt Weight Management Liquid",
    "biomelt capsule": "OnlyVeda Biomelt Weight Management Capsules",
    "biomelt weight management kit": "OnlyVeda Biomelt Weight Management Kit",
    "apple cider vinegar": "OnlyVeda Apple Cider Vinegar",
    "apple cider vinegar 30 cap in jar": "OnlyVeda Apple Cider Vinegar",
    "meal replacement": "OnlyVeda Meal Replacement Shake",

    # Brain, Sleep & Stress
    "intelget": "OnlyVeda Intelget Brain & Memory Capsules",
    "intelget 30 cap in jar": "OnlyVeda Intelget Brain & Memory Capsules",
    "intelget syrup": "OnlyVeda Intelget Brain & Memory Syrup",
    "melatonin spray": "OnlyVeda Melatonin Sleep Spray",

    # Men's Health & Vitality
    "hot male plus": "OnlyVeda Hot Male Plus",
    "hotmale plus": "OnlyVeda Hot Male Plus",
    "hotmale plus 30 caps": "OnlyVeda Hot Male Plus",
    "hot male oil": "OnlyVeda Hot Male Oil",
    "shilajit caps": "OnlyVeda Pure Shilajit Capsules",
    "shilajit 30 tab in jar": "OnlyVeda Pure Shilajit Tablets",
    "shilajit gummies": "OnlyVeda Shilajit Gummies",
    "t booster": "OnlyVeda T-Booster Testosterone Support",
    "testosterone booster 30 tab": "OnlyVeda T-Booster Testosterone Support",

    # Women's Health
    "hot x": "OnlyVeda Hot X Female Vitality",
    "u she plus": "OnlyVeda U-She Plus Feminine Care",
    "u-she plus sy 200ml": "OnlyVeda U-She Plus Feminine Care",
    "u-she hygiene wash": "OnlyVeda U-She Intimate Hygiene Wash",
    "u-she wings": "OnlyVeda U-She Wings Sanitary Pads",
    "evareg": "OnlyVeda Evareg Menstrual Regulator",
    "evareg 10 x 10 caps": "OnlyVeda Evareg Menstrual Regulator",
    "ferrof caps": "OnlyVeda Ferrof Iron & Folic Capsules",
    "ferrof 30 caps": "OnlyVeda Ferrof Iron & Folic Capsules",
    "shatavari 120 tab in jar": "OnlyVeda Shatavari Rejuvenation Tablets",

    # Skin, Hair & Cosmetics
    "xemma cream": "OnlyVeda Xemma Anti-Acne & Blemish Cream",
    "xemma spf 50 with glowing": "OnlyVeda Xemma SPF 50 Glowing Cream",
    "anti acne face wash": "OnlyVeda Clarifying Anti-Acne Face Wash",
    "ella gorgeus kit": "OnlyVeda Ella Gorgeous Radiance Kit",
    "sun screen lotion": "OnlyVeda Broad-Spectrum SPF 50 Herbal Sunscreen",
    "spf cream": "OnlyVeda Broad-Spectrum SPF 50 Herbal Sunscreen",
    "serum": "OnlyVeda Advanced Anti-Ageing Face Serum",
    "anti wrinkle cream": "OnlyVeda Advanced Anti-Ageing Face Serum",
    "glutathione effercescent tablet": "OnlyVeda Glutathione Effervescent",
    "hair 2x": "OnlyVeda Hair 2X Growth Formula",
    "hair 2x kit": "OnlyVeda Hair 2X Growth Kit",
    "lohasu": "OnlyVeda Lohasu Blood Purifier Tablet",
    "lohasu tablet": "OnlyVeda Lohasu Blood Purifier Tablet",
    "raktashu syrup": "OnlyVeda Raktashu Blood Purifier Syrup",
    "neem tablet": "OnlyVeda Neem Purify Tablet",
    "khuj guard": "OnlyVeda Khuj Guard Anti-Itch Cream",
    "khuj guard cream": "OnlyVeda Khuj Guard Anti-Itch Cream",
    "khujguard ointment 25 gm": "OnlyVeda Khuj Guard Anti-Itch Cream",
    "raalon skin disease cream": "OnlyVeda Raalon Skin Disease Cream",
    "pearl essence cream": "OnlyVeda Pearl Essence Cream",
    "ella gorgeos onion hair oil": "OnlyVeda Ella Gorgeous Onion Hair Oil",
    "ella gorgeos neem+tulsi+aloevera facewash": "OnlyVeda Ella Gorgeous Neem Tulsi Facewash",
    "ella gorgeos anti-acne facewash": "OnlyVeda Ella Gorgeous Anti-Acne Facewash",
    "ella gorgeos apple cider vinegar conditioning shampoo": "OnlyVeda Ella Gorgeous ACV Shampoo",
    "ella gorgeos anti-hair fall shampoo": "OnlyVeda Ella Gorgeous Anti-Hair Fall Shampoo",
    "resnovae herbal shampoo 200ml": "OnlyVeda Resnovae Herbal Shampoo",
    "xerocare 30 gm": "OnlyVeda Xerocare Skin Cream",
    "premium skin care soap (noni extract)": "OnlyVeda Premium Noni Skin Care Soap",
    "pearl moisturising soap (75gm x 4)": "OnlyVeda Pearl Moisturising Soap",
    "pearl herbal soap (75 gm x 4)": "OnlyVeda Pearl Herbal Soap",
    "pearl essence orange peel soap (100 gm x 4)": "OnlyVeda Pearl Orange Peel Soap",

    # Dental, Eye & Fever
    "mouth wash": "OnlyVeda Herbal Ayurvedic Mouth Wash",
    "oraplax teeth whitening powder": "OnlyVeda Oraplax Teeth Whitening Powder",
    "oraplax toothpaste (2x100gm)": "OnlyVeda Oraplax Herbal Toothpaste",
    "i well": "OnlyVeda I-Well Eye Health Capsules",
    "i-well 30 cap in jar": "OnlyVeda I-Well Eye Health Capsules",
    "saptamrut loh": "OnlyVeda Saptamrit Loh Eye Tablet",
    "cariwal": "OnlyVeda Cariwal Platelet Support",
    "cariwal 30 tabs in jar": "OnlyVeda Cariwal Platelet Support",
    "maha sudarshan": "OnlyVeda Maha Sudarshan Tablet",
    "mahasudarshan 120 tab in jar": "OnlyVeda Maha Sudarshan Tablet",
    "ors effervescent": "OnlyVeda ORS Electrolyte Effervescent",

    # Single Herb Ayurvedic Classic Tablets
    "amla 120 tab in jar": "OnlyVeda Amla Pure Tablets",
    "aloevera 120 tab in jar": "OnlyVeda Aloe Vera Pure Tablets",
    "punarnavadi 120 tab in jar": "OnlyVeda Punarnavadi Traditional Tablets",

    # Piyo & Beverages & Teas
    "piyo body detox effer tab": "OnlyVeda Piyo Body Detox Effervescent Tablet",
    "piyo sea buckthorn effer tab": "OnlyVeda Piyo Sea Buckthorn Effervescent Tablet",
    "piyo green tea": "OnlyVeda Piyo Herbal Green Tea",
    "piyo coffee": "OnlyVeda Piyo Ayurvedic Wellness Coffee",
    "ez sip tea 250gm": "OnlyVeda EZ Sip Premium Tea",

    # Protein & Nutrition
    "wellpro 200gm": "OnlyVeda Wellpro High Protein Powder",
    "zinc zma 30 tab in jar": "OnlyVeda Zinc ZMA Essential Tablets",

    # Home Care
    "cistoca disinfectant floor cleaner 1 ltr": "OnlyVeda Cistoca Disinfectant Floor Cleaner",
    "cistoca toilet cleaner 500 ml": "OnlyVeda Cistoca Toilet Cleaner",
    "cistoca liquid detergent 1 ltr": "OnlyVeda Cistoca Liquid Detergent",
    "cistoca dish wash liquid 500 ml": "OnlyVeda Cistoca Dish Wash Liquid",

    # Agriculture
    "mt-89 100ml": "OnlyVeda MT-89 Bio-Agri Growth Promoter",
    "mt-humic 500 ml": "OnlyVeda MT-Humic Organic Plant Booster"
}

def resolve_product(raw_name):
    clean = raw_name.strip().lower()
    clean = re.sub(r'onlyveda\s+', '', clean).strip()
    if clean in SYNONYMS:
        return SYNONYMS[clean]
    # Check partial
    for k, v in SYNONYMS.items():
        if k == clean or clean.startswith(k) or k.startswith(clean):
            return v
    # Fallback to Title Case with OnlyVeda prefix
    clean_title = re.sub(r'[^a-zA-Z0-9\s]', ' ', clean).title()
    clean_title = ' '.join(clean_title.split())
    return f"OnlyVeda {clean_title}"

# Load raw sources
with open('data/raw_collected_sources.json', 'r', encoding='utf-8') as f:
    raw = json.load(f)

web = raw['website_products']
csv_prods = raw['csv_products']
excel_prods = raw['excel_products']

# Master dictionary: canonical_name -> product record
master_catalog = {}

# Process website products
for p in web:
    c_name = resolve_product(p['name'])
    raw_p = str(p.get('price', ''))
    clean_price = re.sub(r'^8377', '', raw_p) or '499'
    
    if c_name not in master_catalog:
        master_catalog[c_name] = {
            "name": c_name,
            "category": p.get('category', 'Nutraceutical'),
            "key_ingredients": [],
            "benefits": f"{c_name} - authentic herbal and healthcare formulation by OnlyVeda.",
            "dosage_and_usage": "As directed on packaging or by healthcare physician",
            "price_inr": clean_price,
            "size": "Standard Pack",
            "link": p.get('link', ''),
            "sources": ["Website"]
        }
    else:
        if "Website" not in master_catalog[c_name]["sources"]:
            master_catalog[c_name]["sources"].append("Website")
        if p.get('link') and not master_catalog[c_name].get('link'):
            master_catalog[c_name]['link'] = p['link']
        if clean_price and clean_price != '499':
            master_catalog[c_name]['price_inr'] = clean_price

# Process CSV products
for p in csv_prods:
    c_name = resolve_product(p)
    if c_name not in master_catalog:
        master_catalog[c_name] = {
            "name": c_name,
            "category": "Nutraceutical / Classical Ayurvedic",
            "key_ingredients": [],
            "benefits": f"{c_name} - specialized clinical protocol formulation.",
            "dosage_and_usage": "1-0-1 (as directed by healthcare advisor)",
            "price_inr": "499",
            "size": "Standard Pack",
            "link": "",
            "sources": ["CSV (diseases_wise_1.csv)"]
        }
    else:
        if "CSV (diseases_wise_1.csv)" not in master_catalog[c_name]["sources"]:
            master_catalog[c_name]["sources"].append("CSV (diseases_wise_1.csv)")

# Process Excel products
for p in excel_prods:
    c_name = resolve_product(p)
    if c_name not in master_catalog:
        master_catalog[c_name] = {
            "name": c_name,
            "category": "Nutraceutical / Classical Ayurvedic",
            "key_ingredients": [],
            "benefits": f"{c_name} - specialized clinical treatment formulation.",
            "dosage_and_usage": "1-0-1 (as directed by healthcare advisor)",
            "price_inr": "499",
            "size": "Standard Pack",
            "link": "",
            "sources": ["Excel (disease and treatment database (2).xlsx)"]
        }
    else:
        if "Excel (disease and treatment database (2).xlsx)" not in master_catalog[c_name]["sources"]:
            master_catalog[c_name]["sources"].append("Excel (disease and treatment database (2).xlsx)")

# Merge details from existing data/products.json if richer
with open('data/products.json', 'r', encoding='utf-8') as f:
    existing_file = json.load(f)

for ep in existing_file:
    c_name = resolve_product(ep['name'])
    if c_name in master_catalog:
        if ep.get('key_ingredients'):
            master_catalog[c_name]['key_ingredients'] = ep['key_ingredients']
        if ep.get('benefits') and len(ep['benefits']) > len(master_catalog[c_name]['benefits']):
            master_catalog[c_name]['benefits'] = ep['benefits']
        if ep.get('dosage_and_usage') and ep['dosage_and_usage'] != "1-0-1 (as directed by healthcare advisor)":
            master_catalog[c_name]['dosage_and_usage'] = ep['dosage_and_usage']
        if ep.get('size') and ep['size'] != "Standard Pack":
            master_catalog[c_name]['size'] = ep['size']
    else:
        master_catalog[c_name] = ep
        master_catalog[c_name]["sources"] = ["Existing Catalog"]

# Sort alphabetically
sorted_products = sorted(master_catalog.values(), key=lambda x: x['name'])

print(f"==================================================")
print(f" TOTAL CONSOLIDATED UNIQUE PRODUCTS: {len(sorted_products)}")
print(f"==================================================")

# Count by source
from collections import Counter
source_counts = Counter()
for p in sorted_products:
    src_tuple = tuple(sorted(p['sources']))
    source_counts[src_tuple] += 1

print("\nBreakdown by Source Combinations:")
for src, count in source_counts.most_common():
    print(f"  {count} products: {' + '.join(src)}")

# Save to data/products.json
with open('data/products.json', 'w', encoding='utf-8') as f:
    json.dump(sorted_products, f, indent=2, ensure_ascii=False)

print(f"\nSuccessfully wrote {len(sorted_products)} products to data/products.json")
