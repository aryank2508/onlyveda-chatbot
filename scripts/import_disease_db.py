"""
Import new disease/treatment database from Excel into OnlyVeda data files.
Maps raw product names -> official OnlyVeda product names.
Adds new disease protocols + new products to the JSON databases.
"""

import json
import openpyxl
from pathlib import Path

EXCEL_PATH = r'C:\Users\aryan\Desktop\onlyveda_chatbot\disease and treatment database (2).xlsx'
PROTOCOLS_PATH = 'data/disease_protocols.json'
PRODUCTS_PATH = 'data/products.json'

# ─── PRODUCT NAME MAP ──────────────────────────────────────────────────────────
# Maps raw Excel product names -> official OnlyVeda product names
PRODUCT_NAME_MAP = {
    # Already existing products
    "LINOPRESS":                             "OnlyVeda Linopress",
    "L ARGININE":                            "OnlyVeda L-Arginine Plus",
    "L ARGININE PLUS":                       "OnlyVeda L-Arginine Plus",
    "L ARGINIE":                             "OnlyVeda L-Arginine Plus",
    "ARJUNA TABLET":                         "OnlyVeda Terminalia Arjuna Extract",
    "ASHYUKA HEALTH DRINK":                  "OnlyVeda Ashyuka Plus Syrup",
    "ASHYUKA PLUS":                          "OnlyVeda Ashyuka Plus Syrup",
    "ASHYUKA":                               "OnlyVeda Ashyuka Plus Syrup",
    "IMMUFERIN":                             "OnlyVeda Immuferin Immuno-Shield",
    "IMMUFEIN":                              "OnlyVeda Immuferin Immuno-Shield",
    "IMMUFEIRN":                             "OnlyVeda Immuferin Immuno-Shield",
    "IMMUFERI":                              "OnlyVeda Immuferin Immuno-Shield",
    "ACTIVE 365":                            "OnlyVeda Active 365 Daily Essential",
    "SERRONIL":                              "OnlyVeda Serronil Joint Care",
    "CALCIMUS":                              "OnlyVeda Calcimus Coral Calcium Complex",
    "VITAMIN D3":                            "OnlyVeda Pure Vitamin D3 Chewables",
    "WAL D3":                                "OnlyVeda Wal D3 Sublingual Spray",
    "HADJOD":                                "OnlyVeda Hadjod Bone Healer",
    "STRENUS CAPSULE":                       "OnlyVeda Strenus Pain Relief Capsules",
    "STRENUS CAPS":                          "OnlyVeda Strenus Pain Relief Capsules",
    "STRENUS OIL":                           "OnlyVeda Strenus Herbal Massage Oil",
    "ASHWAGANDHA TABLET":                    "OnlyVeda KSM-66 Ashwagandha Pure Tablet",
    "KSM 66":                                "OnlyVeda KSM-66 Ashwagandha Pure Tablet",
    "MULTIVITAMIN MEN/WOMEN":                "OnlyVeda Daily Complete Multivitamin",
    "MULTIVITAMIN FOR MEN/WOMEN":            "OnlyVeda Daily Complete Multivitamin",
    "MULTIVITAMIN MEN/ WOMEN":              "OnlyVeda Daily Complete Multivitamin",
    "MULTI VITAMIN MEN/WOMEN":              "OnlyVeda Daily Complete Multivitamin",
    "MULTIVITAMIN FOR WOMEN":               "OnlyVeda Daily Complete Multivitamin Women",
    "MULTIVTIAMIN FOR WOMEN":               "OnlyVeda Daily Complete Multivitamin Women",
    "RESPITONE":                             "OnlyVeda Respitone Pulmonary Shield",
    "N ACETYL CYSTEINE":                     "OnlyVeda N-Acetyl Cysteine (NAC 600mg)",
    "N ACETYL CYSTEIN":                      "OnlyVeda N-Acetyl Cysteine (NAC 600mg)",
    "N ACETYL CYSTEIN (NAC)":               "OnlyVeda N-Acetyl Cysteine (NAC 600mg)",
    "KANCHANAR GUGGUL":                     "OnlyVeda Kanchanar Guggul Traditional",
    "VITAMIN C":                             "OnlyVeda Natural Vitamin C + Zinc",
    "HEPATREAT":                             "OnlyVeda Hepatreat Hepatic Care",
    "HEPATREAT SYRUP":                       "OnlyVeda Hepatreat Hepatic Care",
    "HEPATREAT TABLET":                      "OnlyVeda Hepatreat Hepatic Tablets",
    "HEPATREAT HEPATIC TABLETS":            "OnlyVeda Hepatreat Hepatic Tablets",
    "MOUTH WASH":                            "OnlyVeda Herbal Ayurvedic Mouth Wash",
    "XEMMA CREAM":                           "OnlyVeda Xemma Anti-Acne & Blemish Cream",
    "ANTI ACNE FACE WASH":                  "OnlyVeda Clarifying Anti-Acne Face Wash",
    "ELLA GORGEUS KIT":                     "OnlyVeda Ella Gorgeous Radiance Kit",
    "SUN SCREEN LOTION":                    "OnlyVeda Broad-Spectrum SPF 50 Herbal Sunscreen",
    "SPF CREAM":                             "OnlyVeda Broad-Spectrum SPF 50 Herbal Sunscreen",
    "SERUM":                                 "OnlyVeda Advanced Anti-Ageing Face Serum",
    "ANTI WRINKLE CREAM":                   "OnlyVeda Advanced Anti-Ageing Face Serum",
    "THROATWAL":                             "OnlyVeda Throatwal Soothing Lozenges & Gargle",
    "RHIZA":                                 "OnlyVeda Rhiza Mucosal Gut Shield",
    "AVIPATHIKAR TABLET":                   "OnlyVeda Avipattikar Pitta-Balance Tablet",
    "LAXIA":                                 "OnlyVeda Laxia Gentle Overnight Colon Cleanse",
    "LAXIA POWDER":                          "OnlyVeda Laxia Gentle Overnight Colon Cleanse",
    "TRIFALA/SATWIK":                        "OnlyVeda Triphala Satwik Pure Digestive Detox",
    "SATWIK / TRIFALA":                     "OnlyVeda Triphala Satwik Pure Digestive Detox",
    "TRIPHALA":                              "OnlyVeda Triphala Satwik Pure Digestive Detox",
    "PROWAL":                                "OnlyVeda Prowal Synbiotic Gut Restorer",
    "MILK THISTLE":                          "OnlyVeda Milk Thistle Silymarin Detox",
    "MILK THISTLE CAPSULE":                 "OnlyVeda Milk Thistle Silymarin Detox",
    "LIVER DETOX":                           "OnlyVeda Liver Detox Formula",
    "CALCIUMUS":                             "OnlyVeda Calciumus Forte",
    "GLUTATHIONE EFFERCESCENT TABLET":      "OnlyVeda Glutathione Effervescent",
    "SHITOPALADI":                           "OnlyVeda Sitopaladi Churna",
    "WALICTUS COUGH SYRUP":                 "OnlyVeda Walinctus Herbal Cough Syrup",
    "WALINCTUS COUGH SYRUP":               "OnlyVeda Walinctus Herbal Cough Syrup",
    "WALINCTUS":                             "OnlyVeda Walinctus Herbal Cough Syrup",

    # New products from this Excel
    "HEART DETOX PLUS":                     "OnlyVeda Heart Detox Plus",
    "COENZYME Q10":                         "OnlyVeda CoQ10 (Coenzyme Q10)",
    "CO ENZYME Q 10":                       "OnlyVeda CoQ10 (Coenzyme Q10)",
    "OMEGA 3 CAPSULE":                      "OnlyVeda Omega-3 Fish Oil",
    "OMEGA 3":                              "OnlyVeda Omega-3 Fish Oil",
    "BLOOD SUGAR CONTROL":                  "OnlyVeda Blood Sugar Control Formula",
    "DIABETIC CARE":                        "OnlyVeda Blood Sugar Control Formula",
    "INTELGET":                             "OnlyVeda Intelget Brain & Memory Capsules",
    "MAHAYOGRAJ":                           "OnlyVeda Mahayograj Guggul",
    "AROGYA VARDHINI":                      "OnlyVeda Arogyavardhini Vati",
    "KAM DUDHA RAS":                        "OnlyVeda Kamdudha Ras",
    "STOWIP":                               "OnlyVeda Stowip Kidney & Urinary Kit",
    "KIDNEY DETOX":                         "OnlyVeda Kidney Detox Formula",
    "PUNCH TULSI":                          "OnlyVeda Panch Tulsi Drops",
    "HAIR 2X":                              "OnlyVeda Hair 2X Growth Formula",
    "HOT MALE PLUS":                        "OnlyVeda Hot Male Plus",
    "HOT MALE OIL":                         "OnlyVeda Hot Male Oil",
    "HOTMALE PLUS":                         "OnlyVeda Hot Male Plus",
    "SHILAJIT CAPS":                        "OnlyVeda Pure Shilajit Capsules",
    "T BOOSTER":                            "OnlyVeda T-Booster Testosterone Support",
    "HOT X":                                "OnlyVeda Hot X Female Vitality",
    "U SHE PLUS":                           "OnlyVeda U-She Plus Feminine Care",
    "EVAREG":                               "OnlyVeda Evareg Menstrual Regulator",
    "FERROF CAPS":                          "OnlyVeda Ferrof Iron & Folic Capsules",
    "CRANBERRY CAPS":                       "OnlyVeda Cranberry Extract Capsules",
    "CHANDRA PRABHA TABLET":               "OnlyVeda Chandraprabha Vati",
    "LOHASU":                               "OnlyVeda Lohasu Blood Purifier Tablet",
    "LOHASU TABLET":                        "OnlyVeda Lohasu Blood Purifier Tablet",
    "NEEM TABLET":                          "OnlyVeda Neem Purify Tablet",
    "KHUJ GUARD CREAM":                     "OnlyVeda Khuj Guard Anti-Itch Cream",
    "KHUJ GUARD":                           "OnlyVeda Khuj Guard Anti-Itch Cream",
    "I WELL":                               "OnlyVeda I-Well Eye Health Capsules",
    "SAPTAMRUT LOH":                        "OnlyVeda Saptamrit Loh Eye Tablet",
    "CARIWAL":                              "OnlyVeda Cariwal Platelet Support",
    "MAHA SUDARSHAN":                       "OnlyVeda Maha Sudarshan Tablet",
    "ORS EFFERVESCENT":                     "OnlyVeda ORS Electrolyte Effervescent",
    "ANURECT CAPS":                         "OnlyVeda Anurect Piles Capsules",
    "ANURECT OINTMENT":                     "OnlyVeda Anurect Piles Ointment",
    "MELATONIN SPRAY":                      "OnlyVeda Melatonin Sleep Spray",
    "BIOMELT LIQUID":                       "OnlyVeda Biomelt Weight Management Liquid",
    "BIOMELT CAPSULE":                      "OnlyVeda Biomelt Weight Management Capsules",
    "APPLE CIDER VINEGAR":                  "OnlyVeda Apple Cider Vinegar",
    "MEAL REPLACEMENT":                     "OnlyVeda Meal Replacement Shake",
    "WALZYME":                              "OnlyVeda Walzyme Digestive Enzymes",
    "SAPTAMRUT LOH":                        "OnlyVeda Saptamrit Loh Eye Tablet",
}

# Diseases to skip (empty protocols or not enough info)
SKIP_DISEASES = {"PCOD", "GANGRENE"}


def normalize_product(raw):
    """Normalize raw product name to official OnlyVeda name."""
    raw = raw.strip().upper()
    # Try direct map
    if raw in PRODUCT_NAME_MAP:
        return PRODUCT_NAME_MAP[raw]
    # Try partial match
    for key, val in PRODUCT_NAME_MAP.items():
        if key in raw or raw in key:
            return val
    # Return as OnlyVeda prefixed unknown
    return f"OnlyVeda {raw.title()}"


def build_protocols_from_excel():
    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb['Sheet1']

    diseases = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        cat = str(row[0] or '').strip().rstrip('\xa0').upper()
        disease = str(row[1] or '').strip().rstrip('\xa0')
        product_raw = str(row[3] or '').strip()
        dose = str(row[4] or '').strip() if row[4] else '1-0-1'

        if not disease or not product_raw:
            continue
        disease_upper = disease.upper().strip()
        if disease_upper in SKIP_DISEASES:
            continue

        if disease not in diseases:
            diseases[disease] = {'category': cat, 'supplements': []}

        official_name = normalize_product(product_raw)
        # Deduplicate
        existing_names = [s['name'] for s in diseases[disease]['supplements']]
        if official_name not in existing_names:
            diseases[disease]['supplements'].append({
                'name': official_name,
                'dose': dose if dose and dose.strip() and dose != 'None' else '1-0-1'
            })

    return diseases


def build_disease_key(disease_name):
    """Create a lowercase key for the disease."""
    return disease_name.lower().strip()


def main():
    # Load existing data
    with open(PROTOCOLS_PATH) as f:
        existing_protocols = json.load(f)
    with open(PRODUCTS_PATH) as f:
        existing_products = json.load(f)

    existing_product_names = {p['name'] for p in existing_products}
    existing_protocol_keys = {k.lower().strip() for k in existing_protocols.keys()}

    print(f"Existing protocols: {len(existing_protocols)}")
    print(f"Existing products: {len(existing_products)}")

    # Parse Excel
    new_diseases = build_protocols_from_excel()
    print(f"\nDiseases in Excel: {len(new_diseases)}")

    added_protocols = 0
    updated_protocols = 0
    new_products_to_add = []

    for disease_name, info in new_diseases.items():
        supplements = info['supplements']
        if not supplements:
            continue

        disease_key = build_disease_key(disease_name)

        # Build protocol entry
        protocol_entry = {
            "disease": disease_name,
            "category": info['category'],
            "localized_names": {
                "en": disease_name,
                "hi": disease_name,
                "gu": disease_name,
                "mr": disease_name,
                "bn": disease_name,
                "te": disease_name,
                "ta": disease_name,
                "kn": disease_name,
                "or": disease_name,
                "ml": disease_name,
                "ur": disease_name
            },
            "supplements": supplements
        }

        if disease_key not in existing_protocol_keys:
            # New disease — add it
            existing_protocols[disease_name] = protocol_entry
            existing_protocol_keys.add(disease_key)
            added_protocols += 1
            print(f"  [NEW] {disease_name} ({len(supplements)} products)")
        else:
            # Existing — check if we can enrich with new supplements
            existing_key = next((k for k in existing_protocols if k.lower().strip() == disease_key), None)
            if existing_key:
                existing_sups = existing_protocols[existing_key].get('supplements', [])
                existing_sup_names = {s['name'] for s in existing_sups}
                newly_added = []
                for s in supplements:
                    if s['name'] not in existing_sup_names:
                        existing_sups.append(s)
                        existing_sup_names.add(s['name'])
                        newly_added.append(s['name'])
                if newly_added:
                    existing_protocols[existing_key]['supplements'] = existing_sups
                    updated_protocols += 1
                    print(f"  [UPDATED] {existing_key}: added {newly_added}")

        # Track brand-new products not in products.json
        for s in supplements:
            if s['name'] not in existing_product_names:
                existing_product_names.add(s['name'])
                new_products_to_add.append(s['name'])

    print(f"\nSummary:")
    print(f"  Added protocols:   {added_protocols}")
    print(f"  Updated protocols: {updated_protocols}")
    print(f"  New products referenced: {len(new_products_to_add)}")
    for p in new_products_to_add:
        print(f"    -> {p}")

    # Add new products to products.json with placeholder data
    for pname in new_products_to_add:
        existing_products.append({
            "name": pname,
            "category": "Nutraceutical",
            "key_ingredients": [],
            "benefits": f"OnlyVeda {pname.replace('OnlyVeda ', '')} - specialized Ayurvedic formulation.",
            "dosage_and_usage": "1-0-1 (as directed by healthcare advisor)",
            "price_inr": "499",
            "size": "60 Tablets / 30ml"
        })

    # Save updated files
    with open(PROTOCOLS_PATH, 'w', encoding='utf-8') as f:
        json.dump(existing_protocols, f, ensure_ascii=False, indent=2)
    with open(PRODUCTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(existing_products, f, ensure_ascii=False, indent=2)

    print(f"\nTotal protocols now: {len(existing_protocols)}")
    print(f"Total products now:  {len(existing_products)}")
    print("\nFiles saved successfully!")


if __name__ == '__main__':
    main()
