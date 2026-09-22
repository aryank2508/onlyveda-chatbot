import json
import re

with open('data/disease_protocols.json', 'r', encoding='utf-8') as f:
    protocols = json.load(f)

with open('data/products.json', 'r', encoding='utf-8') as f:
    catalog = json.load(f)

# Build a lookup: lower_name -> canonical_name
canonical_lookup = {}
for p in catalog:
    c_name = p['name']
    canonical_lookup[c_name.lower()] = c_name
    canonical_lookup[c_name.lower().replace("onlyveda ", "")] = c_name
    canonical_lookup[re.sub(r'[^a-z0-9]', '', c_name.lower())] = c_name
    canonical_lookup[re.sub(r'[^a-z0-9]', '', c_name.lower().replace("onlyveda ", ""))] = c_name

# Add explicit manual aliases
manual_aliases = {
    "l arginine": "OnlyVeda L-Arginine Plus",
    "l arginie": "OnlyVeda L-Arginine Plus",
    "arjuna tablet": "OnlyVeda Terminalia Arjuna Extract",
    "ashyuka": "OnlyVeda Ashyuka Plus Syrup",
    "ashyuka health drink": "OnlyVeda Ashyuka Plus Syrup",
    "ashyuka plus": "OnlyVeda Ashyuka Plus Syrup",
    "hadjoj": "OnlyVeda Hadjod Bone Healer",
    "multi vitamin men/women": "OnlyVeda Daily Complete Multivitamin",
    "multivitamin men/ women": "OnlyVeda Daily Complete Multivitamin",
    "multivitamin men/women": "OnlyVeda Daily Complete Multivitamin",
    "multivitamin for men/women": "OnlyVeda Daily Complete Multivitamin",
    "multivtiamin for women": "OnlyVeda Daily Complete Multivitamin Women",
    "multivitamin for women": "OnlyVeda Daily Complete Multivitamin Women",
    "n acetyl cystein": "OnlyVeda N-Acetyl Cysteine (NAC 600mg)",
    "n acetyl cysteine": "OnlyVeda N-Acetyl Cysteine (NAC 600mg)",
    "n acetyl cystein (nac)": "OnlyVeda N-Acetyl Cysteine (NAC 600mg)",
    "trifala/satwik": "OnlyVeda Triphala Satwik Pure Digestive Detox",
    "satwik / trifala": "OnlyVeda Triphala Satwik Pure Digestive Detox",
    "ella gorgeus kit": "OnlyVeda Ella Gorgeous Radiance Kit",
    "sun screen lotion": "OnlyVeda Broad-Spectrum SPF 50 Herbal Sunscreen",
    "spf cream": "OnlyVeda Broad-Spectrum SPF 50 Herbal Sunscreen",
    "serum": "OnlyVeda Advanced Anti-Ageing Face Serum",
    "anti wrinkle cream": "OnlyVeda Advanced Anti-Ageing Face Serum",
    "strenus caps": "OnlyVeda Strenus Pain Relief Capsules",
    "strenus capsule": "OnlyVeda Strenus Pain Relief Capsules",
    "strenus oil": "OnlyVeda Strenus Herbal Massage Oil",
    "strnus oil": "OnlyVeda Strenus Herbal Massage Oil",
    "walictus cough syrup": "OnlyVeda Walinctus Herbal Cough Syrup",
    "walinctus cough syrup": "OnlyVeda Walinctus Herbal Cough Syrup",
    "wal d3": "OnlyVeda Wal D3 Sublingual Spray",
    "vitamin c": "OnlyVeda Natural Vitamin C + Zinc",
    "vitamin d3": "OnlyVeda Pure Vitamin D3 Chewables",
    "calciumus": "OnlyVeda Calciumus Forte",
    "calcimus": "OnlyVeda Calcimus Coral Calcium Complex",
    "glutathione effercescent tablet": "OnlyVeda Glutathione Effervescent",
    "mouth wash": "OnlyVeda Herbal Ayurvedic Mouth Wash",
    "saptamrut loh": "OnlyVeda Saptamrit Loh Eye Tablet",
    "punch tulsi": "OnlyVeda Panch Tulsi Drops",
    "pro wal": "OnlyVeda Prowal Synbiotic Gut Restorer",
    "prowal": "OnlyVeda Prowal Synbiotic Gut Restorer",
    "active 365": "OnlyVeda Active 365 Daily Essential",
    "active 365`": "OnlyVeda Active 365 Daily Essential",
    "immufein": "OnlyVeda Immuferin Immuno-Shield",
    "immufeirn": "OnlyVeda Immuferin Immuno-Shield",
    "immuferi": "OnlyVeda Immuferin Immuno-Shield",
    "2 caps of immuferin in soframycin cream": "OnlyVeda Immuferin Immuno-Shield",
    "shitopaladi": "OnlyVeda Sitopaladi Churna",
    "lohasu": "OnlyVeda Lohasu Blood Purifier Tablet",
    "lohasu tablet": "OnlyVeda Lohasu Blood Purifier Tablet",
    "khuj guard": "OnlyVeda Khuj Guard Anti-Itch Cream",
    "khuj guard cream": "OnlyVeda Khuj Guard Anti-Itch Cream",
    "hotmale plus": "OnlyVeda Hot Male Plus",
    "hot male plus": "OnlyVeda Hot Male Plus",
    "t booster": "OnlyVeda T-Booster Testosterone Support",
    "u she plus": "OnlyVeda U-She Plus Feminine Care",
    "evareg": "OnlyVeda Evareg Menstrual Regulator",
    "ferrof caps": "OnlyVeda Ferrof Iron & Folic Capsules",
    "cranberry caps": "OnlyVeda Cranberry Extract Capsules",
    "chandra prabha tablet": "OnlyVeda Chandraprabha Vati",
    "arogya vardhini": "OnlyVeda Arogyavardhini Vati",
    "kam dudha ras": "OnlyVeda Kamdudha Ras",
    "stowip": "OnlyVeda Stowip Kidney & Urinary Kit",
    "kidney detox": "OnlyVeda Kidney Detox Formula",
    "i well": "OnlyVeda I-Well Eye Health Capsules",
    "cariwal": "OnlyVeda Cariwal Platelet Support",
    "maha sudarshan": "OnlyVeda Maha Sudarshan Tablet",
    "ors effervescent": "OnlyVeda ORS Electrolyte Effervescent",
    "anurect caps": "OnlyVeda Anurect Piles Capsules",
    "anurect ointment": "OnlyVeda Anurect Piles Ointment",
    "melatonin spray": "OnlyVeda Melatonin Sleep Spray",
    "biomelt liquid": "OnlyVeda Biomelt Weight Management Liquid",
    "biomelt capsule": "OnlyVeda Biomelt Weight Management Capsules",
    "apple cider vinegar": "OnlyVeda Apple Cider Vinegar",
    "meal replacement": "OnlyVeda Meal Replacement Shake",
    "walzyme": "OnlyVeda Walzyme Digestive Enzymes",
    "xemma cream": "OnlyVeda Xemma Anti-Acne & Blemish Cream",
    "ashwagandha tablet": "OnlyVeda KSM-66 Ashwagandha Pure Tablet",
    "immuferin": "OnlyVeda Immuferin Immuno-Shield",
    "rhiza": "OnlyVeda Rhiza Mucosal Gut Shield",
    "hepatreat": "OnlyVeda Hepatreat Hepatic Care",
    "hepatreat tablet": "OnlyVeda Hepatreat Hepatic Tablets",
    "anti acne face wash": "OnlyVeda Clarifying Anti-Acne Face Wash",
    "kanchanar guggul": "OnlyVeda Kanchanar Guggul Traditional",
    "laxia": "OnlyVeda Laxia Gentle Overnight Colon Cleanse",
    "milk thistle": "OnlyVeda Milk Thistle Silymarin Detox",
    "serronil": "OnlyVeda Serronil Joint Care",
    "respitone": "OnlyVeda Respitone Pulmonary Shield",
    "liver detox": "OnlyVeda Liver Detox Formula",
    "avipathikar tablet": "OnlyVeda Avipattikar Pitta-Balance Tablet",
    "throatwal": "OnlyVeda Throatwal Soothing Lozenges & Gargle"
}

for k, v in manual_aliases.items():
    canonical_lookup[k] = v
    canonical_lookup[f"onlyveda {k}"] = v

total_before = 0
total_after = 0
unmatched_set = set()

for dis, info in protocols.items():
    sups = info.get('supplements', [])
    total_before += len(sups)
    cleaned = []
    seen = set()
    for s in sups:
        raw = s['name'].strip()
        low = raw.lower().replace('`', '').strip()
        clean_key = re.sub(r'[^a-z0-9]', '', low)
        
        c_name = manual_aliases.get(low) or canonical_lookup.get(low) or canonical_lookup.get(clean_key)
        if not c_name:
            if not raw.startswith("OnlyVeda "):
                c_name = f"OnlyVeda {raw}"
            else:
                c_name = raw
            unmatched_set.add(raw)
            
        if c_name not in seen:
            seen.add(c_name)
            cleaned.append({
                "name": c_name,
                "dose": s.get("dose", "1-0-1")
            })
    info['supplements'] = cleaned
    total_after += len(cleaned)

print(f"Total supplement entries before: {total_before}")
print(f"Total supplement entries after deduplication: {total_after} (removed {total_before - total_after} duplicates)")
print(f"Remaining unmatched: {len(unmatched_set)}")
for u in unmatched_set:
    print(f"  Unmatched: {u}")

with open('data/disease_protocols.json', 'w', encoding='utf-8') as f:
    json.dump(protocols, f, indent=2, ensure_ascii=False)

print("Updated data/disease_protocols.json successfully!")
