import json

with open('data/disease_protocols.json', 'r', encoding='utf-8') as f:
    protocols = json.load(f)

with open('data/products.json', 'r', encoding='utf-8') as f:
    catalog = json.load(f)

catalog_names = {p['name'] for p in catalog}

# Map variations to canonical catalog names
CANONICAL_MAP = {
    "OnlyVeda L Arginine": "OnlyVeda L-Arginine Plus",
    "OnlyVeda L Arginie": "OnlyVeda L-Arginine Plus",
    "OnlyVeda Arjuna Tablet": "OnlyVeda Terminalia Arjuna Extract",
    "OnlyVeda Arjuna": "OnlyVeda Terminalia Arjuna Extract",
    "OnlyVeda Ashyuka": "OnlyVeda Ashyuka Plus Syrup",
    "OnlyVeda Ashyuka Health Drink": "OnlyVeda Ashyuka Plus Syrup",
    "OnlyVeda Immufein": "OnlyVeda Immuferin Immuno-Shield",
    "OnlyVeda Immufeirn": "OnlyVeda Immuferin Immuno-Shield",
    "OnlyVeda Immuferi": "OnlyVeda Immuferin Immuno-Shield",
    "OnlyVeda 2 Caps Of Immuferin In Soframycin Cream": "OnlyVeda Immuferin Immuno-Shield",
    "OnlyVeda Multi Vitamin Men/Women": "OnlyVeda Daily Complete Multivitamin",
    "OnlyVeda Multivitamin For Men/Women": "OnlyVeda Daily Complete Multivitamin",
    "OnlyVeda Multivitamin Men/ Women": "OnlyVeda Daily Complete Multivitamin",
    "OnlyVeda Multivitamin Men/Women": "OnlyVeda Daily Complete Multivitamin",
    "OnlyVeda Multivtiamin For Women": "OnlyVeda Daily Complete Multivitamin Women",
    "OnlyVeda Calcimus": "OnlyVeda Calcimus Coral Calcium Complex",
    "OnlyVeda Calciumus": "OnlyVeda Calciumus Forte",
    "OnlyVeda Hadjoj": "OnlyVeda Hadjod Bone Healer",
    "OnlyVeda Strenus Caps": "OnlyVeda Strenus Pain Relief Capsules",
    "OnlyVeda Strenus Capsule": "OnlyVeda Strenus Pain Relief Capsules",
    "OnlyVeda Strnus Oil": "OnlyVeda Strenus Herbal Massage Oil",
    "OnlyVeda Strenus Oil": "OnlyVeda Strenus Herbal Massage Oil",
    "OnlyVeda Ashwagandha Tablet": "OnlyVeda KSM-66 Ashwagandha Pure Tablet",
    "OnlyVeda Maha Yograj Guggul": "OnlyVeda Mahayograj Guggul",
    "OnlyVeda N Acetyl Cysteine": "OnlyVeda N-Acetyl Cysteine (NAC 600mg)",
    "OnlyVeda N Acetyl Cystein": "OnlyVeda N-Acetyl Cysteine (NAC 600mg)",
    "OnlyVeda N Acetyl Cystein (Nac)": "OnlyVeda N-Acetyl Cysteine (NAC 600mg)",
    "OnlyVeda Walictus Cough Syrup": "OnlyVeda Walinctus Herbal Cough Syrup",
    "OnlyVeda Walinctus Cough Syrup": "OnlyVeda Walinctus Herbal Cough Syrup",
    "OnlyVeda Walinctus": "OnlyVeda Walinctus Herbal Cough Syrup",
    "OnlyVeda Shitopaladi": "OnlyVeda Sitopaladi Churna",
    "OnlyVeda Kanchanar Guggul": "OnlyVeda Kanchanar Guggul Traditional",
    "OnlyVeda Hepatreat": "OnlyVeda Hepatreat Hepatic Care",
    "OnlyVeda Hepatreat Syrup": "OnlyVeda Hepatreat Hepatic Care",
    "OnlyVeda Hepatreat Tablet": "OnlyVeda Hepatreat Hepatic Tablets",
    "OnlyVeda Rhiza": "OnlyVeda Rhiza Mucosal Gut Shield",
    "OnlyVeda Avipathikar Tablet": "OnlyVeda Avipattikar Pitta-Balance Tablet",
    "OnlyVeda Laxia": "OnlyVeda Laxia Gentle Overnight Colon Cleanse",
    "OnlyVeda Laxia Powder": "OnlyVeda Laxia Gentle Overnight Colon Cleanse",
    "OnlyVeda Trifala/Satwik": "OnlyVeda Triphala Satwik Pure Digestive Detox",
    "OnlyVeda Satwik / Trifala": "OnlyVeda Triphala Satwik Pure Digestive Detox",
    "OnlyVeda Triphala": "OnlyVeda Triphala Satwik Pure Digestive Detox",
    "OnlyVeda Prowal": "OnlyVeda Prowal Synbiotic Gut Restorer",
    "OnlyVeda Pro Wal": "OnlyVeda Prowal Synbiotic Gut Restorer",
    "OnlyVeda Milk Thistle": "OnlyVeda Milk Thistle Silymarin Detox",
    "OnlyVeda Milk Thistle Capsule": "OnlyVeda Milk Thistle Silymarin Detox",
    "OnlyVeda Liver Detox": "OnlyVeda Liver Detox Formula",
    "OnlyVeda Anurect Caps": "OnlyVeda Anurect Piles Capsules",
    "OnlyVeda Anurect Ointment": "OnlyVeda Anurect Piles Ointment",
    "OnlyVeda Kam Dudha Ras": "OnlyVeda Kamdudha Ras",
    "OnlyVeda Arogya Vardhini": "OnlyVeda Arogyavardhini Vati",
    "OnlyVeda Stowip": "OnlyVeda Stowip Kidney & Urinary Kit",
    "OnlyVeda Kidney Detox": "OnlyVeda Kidney Detox Formula",
    "OnlyVeda Punch Tulsi": "OnlyVeda Panch Tulsi Drops",
    "OnlyVeda Cranberry Caps": "OnlyVeda Cranberry Extract Capsules",
    "OnlyVeda Chandra Prabha Tablet": "OnlyVeda Chandraprabha Vati",
    "OnlyVeda Hotmale Plus": "OnlyVeda Hot Male Plus",
    "OnlyVeda Shilajit Caps": "OnlyVeda Pure Shilajit Capsules",
    "OnlyVeda T Booster": "OnlyVeda T-Booster Testosterone Support",
    "OnlyVeda U She Plus": "OnlyVeda U-She Plus Feminine Care",
    "OnlyVeda Evareg": "OnlyVeda Evareg Menstrual Regulator",
    "OnlyVeda Ferrof Caps": "OnlyVeda Ferrof Iron & Folic Capsules",
    "OnlyVeda Lohasu": "OnlyVeda Lohasu Blood Purifier Tablet",
    "OnlyVeda Lohasu Tablet": "OnlyVeda Lohasu Blood Purifier Tablet",
    "OnlyVeda Neem Tablet": "OnlyVeda Neem Purify Tablet",
    "OnlyVeda Khuj Guard": "OnlyVeda Khuj Guard Anti-Itch Cream",
    "OnlyVeda Khuj Guard Cream": "OnlyVeda Khuj Guard Anti-Itch Cream",
    "OnlyVeda Ella Gorgeus Kit": "OnlyVeda Ella Gorgeous Radiance Kit",
    "OnlyVeda Sun Screen Lotion": "OnlyVeda Broad-Spectrum SPF 50 Herbal Sunscreen",
    "OnlyVeda Spf Cream": "OnlyVeda Broad-Spectrum SPF 50 Herbal Sunscreen",
    "OnlyVeda Serum": "OnlyVeda Advanced Anti-Ageing Face Serum",
    "OnlyVeda Anti Wrinkle Cream": "OnlyVeda Advanced Anti-Ageing Face Serum",
    "OnlyVeda Glutathione Effercescent Tablet": "OnlyVeda Glutathione Effervescent",
    "OnlyVeda Hair 2X": "OnlyVeda Hair 2X Growth Formula",
    "OnlyVeda Mouth Wash": "OnlyVeda Herbal Ayurvedic Mouth Wash",
    "OnlyVeda I Well": "OnlyVeda I-Well Eye Health Capsules",
    "OnlyVeda Saptamrut Loh": "OnlyVeda Saptamrit Loh Eye Tablet",
    "OnlyVeda Cariwal": "OnlyVeda Cariwal Platelet Support",
    "OnlyVeda Maha Sudarshan": "OnlyVeda Maha Sudarshan Tablet",
    "OnlyVeda Ors Effervescent": "OnlyVeda ORS Electrolyte Effervescent",
    "OnlyVeda Melatonin Spray": "OnlyVeda Melatonin Sleep Spray",
    "OnlyVeda Biomelt Liquid": "OnlyVeda Biomelt Weight Management Liquid",
    "OnlyVeda Biomelt Capsule": "OnlyVeda Biomelt Weight Management Capsules",
    "OnlyVeda Apple Cider Vinegar": "OnlyVeda Apple Cider Vinegar",
    "OnlyVeda Meal Replacement": "OnlyVeda Meal Replacement Shake",
    "OnlyVeda Walzyme": "OnlyVeda Walzyme Digestive Enzymes"
}

total_sups_before = 0
total_sups_after = 0

for dis, info in protocols.items():
    sups = info.get('supplements', [])
    total_sups_before += len(sups)
    
    seen = set()
    cleaned_sups = []
    for s in sups:
        raw_name = s['name'].strip()
        canonical = CANONICAL_MAP.get(raw_name, raw_name)
        if canonical not in seen:
            seen.add(canonical)
            cleaned_sups.append({
                "name": canonical,
                "dose": s.get("dose", "1-0-1")
            })
    info['supplements'] = cleaned_sups
    total_sups_after += len(cleaned_sups)

print(f"Total protocol supplement references before: {total_sups_before}")
print(f"Total protocol supplement references after: {total_sups_after} (removed {total_sups_before - total_sups_after} duplicate entries)")

# Verify all supplements exist in catalog
unmatched = set()
for dis, info in protocols.items():
    for s in info['supplements']:
        if s['name'] not in catalog_names:
            unmatched.add(s['name'])

print(f"Unmatched supplements across all protocols: {len(unmatched)}")
for u in unmatched:
    print(f"  Unmatched: {u}")

with open('data/disease_protocols.json', 'w', encoding='utf-8') as f:
    json.dump(protocols, f, indent=2, ensure_ascii=False)

print("\nSuccessfully updated data/disease_protocols.json!")
