"""
Builds official OnlyVeda product catalog and disease protocol mapping
directly from diseases_wise_1.csv.
"""

import csv
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "diseases_wise_1.csv")
PROTOCOLS_PATH = os.path.join(BASE_DIR, "data", "disease_protocols.json")
PRODUCTS_PATH = os.path.join(BASE_DIR, "data", "products.json")

def clean_dose(supp, dose):
    dose = dose.strip()
    if dose == '01-01-2001':
        if any(x in supp.lower() for x in ['oil', 'cream', 'wash', 'serum', 'lotion']):
            return 'Apply / Use 2-3 times daily'
        else:
            return '1-1-1 (1 Morning, 1 Afternoon, 1 Night)'
    elif not dose or dose == '-':
        return 'As directed by physician'
    elif dose in ['1 -0-1', '1-0-1-']:
        return '1-0-1 (1 Morning, 1 Night)'
    elif dose == '2 -2-2-':
        return '2-2-2 (2 Morning, 2 Afternoon, 2 Night)'
    return dose

# 1. Parse CSV into disease protocols
with open(CSV_PATH, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

protocols = {}
for r in rows:
    cat = ' '.join(r['Category'].strip().split())
    dis = r['Disease'].strip()
    supp = (r.get('Suggested Supplement') or r.get('Supplement') or '').strip().replace('`', '').strip()
    dose = clean_dose(supp, r.get('Dose', ''))

    if dis not in protocols:
        protocols[dis] = {
            'disease': dis,
            'category': cat,
            'supplements': []
        }
    protocols[dis]['supplements'].append({
        'name': supp,
        'dose': dose
    })

os.makedirs(os.path.dirname(PROTOCOLS_PATH), exist_ok=True)
with open(PROTOCOLS_PATH, 'w', encoding='utf-8') as f:
    json.dump(protocols, f, indent=2, ensure_ascii=False)
print(f"Saved {len(protocols)} disease protocols to {PROTOCOLS_PATH}")

# 2. Comprehensive metadata for OnlyVeda product catalog
product_meta = {
    'linopress': {
        'name': 'OnlyVeda Linopress',
        'category': 'Heart & Cardiovascular',
        'key_ingredients': ['Flaxseed Lignans (ALA)', 'Terminalia Arjuna', 'CoQ10', 'Garlic Bulb Extract'],
        'benefits': 'Clinically formulated for optimal blood pressure management, arterial elasticity, and healthy blood flow.',
        'size': '60 Capsules',
        'price_inr': 799
    },
    'L arginine': {
        'name': 'OnlyVeda L-Arginine Plus',
        'category': 'Heart & Cardiovascular',
        'key_ingredients': ['Pure L-Arginine (1000mg)', 'L-Citrulline', 'Folic Acid'],
        'benefits': 'Boosts nitric oxide production, relaxes blood vessels, and supports cardiovascular stamina.',
        'size': '60 Tablets',
        'price_inr': 699
    },
    'Arjuna tablet': {
        'name': 'OnlyVeda Terminalia Arjuna Extract',
        'category': 'Heart & Cardiovascular',
        'key_ingredients': ['Pure Arjuna Bark Standardized Extract (500mg)'],
        'benefits': 'Strengthens cardiac muscles, regulates blood pressure, and reduces LDL cholesterol plaque.',
        'size': '60 Tablets',
        'price_inr': 499
    },
    'Ashyuka plus': {
        'name': 'OnlyVeda Ashyuka Plus Syrup',
        'category': 'Multi-System Healing & Vitality',
        'key_ingredients': ['Ashoka Bark', 'Lodhra', 'Shatavari', 'Guduchi', 'Manjistha'],
        'benefits': 'Potent multi-herbal formulation for cholesterol balance, respiratory relief, gut healing, and cellular rejuvenation.',
        'size': '200 ml Syrup',
        'price_inr': 599
    },
    'immuferin': {
        'name': 'OnlyVeda Immuferin Immuno-Shield',
        'category': 'Immunity & Infection Defense',
        'key_ingredients': ['Lactoferrin', 'Colostrum', 'Curcumin', 'Zinc Glycinate', 'Giloy'],
        'benefits': 'Advanced immune modulator; combats systemic inflammation, bacterial and viral infections, and accelerates tissue recovery.',
        'size': '60 Veggie Capsules',
        'price_inr': 999
    },
    'Active 365': {
        'name': 'OnlyVeda Active 365 Daily Essential',
        'category': 'Daily Vitality & Cellular Defense',
        'key_ingredients': ['365 Herbal & Mineral Complex', 'Spirulina', 'Ginseng', 'Green Tea Extract'],
        'benefits': 'Full-spectrum cellular energizer, combats muscular aches, fatigue, and free-radical stress throughout the body.',
        'size': '60 Tablets',
        'price_inr': 849
    },
    'serronil': {
        'name': 'OnlyVeda Serronil Joint Care',
        'category': 'Joint & Bone Care',
        'key_ingredients': ['Serratiopeptidase', 'Boswellia Shallaki (300mg)', 'Curcumin 95%'],
        'benefits': 'Fast-acting anti-inflammatory enzyme complex that breaks down joint stiffness, eases swelling, and relieves arthritic pain.',
        'size': '60 Capsules',
        'price_inr': 899
    },
    'Calcimus': {
        'name': 'OnlyVeda Calcimus Coral Calcium Complex',
        'category': 'Bone & Dental Health',
        'key_ingredients': ['Bio-Available Coral Calcium (500mg)', 'Magnesium', 'Zinc', 'Cissus (Hadjod)'],
        'benefits': 'High-absorption calcium that restores bone mineral density, strengthens teeth enamel, and prevents fractures.',
        'size': '60 Tablets',
        'price_inr': 549
    },
    'Wal D3': {
        'name': 'OnlyVeda Wal D3 Sublingual Spray',
        'category': 'Bone & Immune Health',
        'key_ingredients': ['Plant-Based Vitamin D3 (Cholecalciferol 2000 IU/spray)'],
        'benefits': 'Ultra-fast sublingual absorption to rebuild bone cartilage, enhance calcium uptake, and support joint mobility.',
        'size': '30 ml Oral Spray',
        'price_inr': 499
    },
    'Hadjoj': {
        'name': 'OnlyVeda Hadjod Bone Healer',
        'category': 'Bone Fracture & Density',
        'key_ingredients': ['Cissus Quadrangularis (Asthisamharaka) Standardized Extract (500mg)'],
        'benefits': 'Traditional bone-setter herb that accelerates fracture union, stimulates osteoblasts, and repairs connective tissue.',
        'size': '60 Tablets',
        'price_inr': 449
    },
    'Strenus caps': {
        'name': 'OnlyVeda Strenus Pain Relief Capsules',
        'category': 'Musculoskeletal & Back Care',
        'key_ingredients': ['Shallaki', 'Nirgundi', 'Rasna', 'Ashwagandha'],
        'benefits': 'Relieves deep muscular backache, spinal spasms, and stiffness in lumbar joints.',
        'size': '60 Capsules',
        'price_inr': 649
    },
    'Strenus oil': {
        'name': 'OnlyVeda Strenus Herbal Massage Oil',
        'category': 'Topical Pain Relief',
        'key_ingredients': ['Mahanarayan Taila', 'Gandhapura Oil (Wintergreen)', 'Camphor', 'Eucalyptus'],
        'benefits': 'Penetrating Ayurvedic massage oil for instant relief from backache, knee pain, and muscular tightness.',
        'size': '100 ml Bottle',
        'price_inr': 399
    },
    'Ashwagandha tablet': {
        'name': 'OnlyVeda KSM-66 Ashwagandha Pure Tablet',
        'category': 'Nerve & Spine Health',
        'key_ingredients': ['KSM-66 Ashwagandha Extract (500mg)'],
        'benefits': 'Strengthens nervous system, soothes spinal nerve inflammation, and alleviates cervical spondylitis.',
        'size': '60 Tablets',
        'price_inr': 599
    },
    'Multivitamin men/women': {
        'name': 'OnlyVeda Daily Complete Multivitamin',
        'category': 'Nutritional Balance',
        'key_ingredients': ['24 Essential Vitamins & Trace Minerals', 'Probiotics', 'Ginkgo Biloba'],
        'benefits': 'Prevents micronutrient deficiencies, strengthens mucosal lining, and boosts cellular vitality.',
        'size': '60 Tablets',
        'price_inr': 699
    },
    'respitone': {
        'name': 'OnlyVeda Respitone Pulmonary Shield',
        'category': 'Respiratory & Lungs',
        'key_ingredients': ['Vasaka (Adhatoda)', 'Pushkarmool', 'Kantakari', 'Licorice', 'Tulsi'],
        'benefits': 'Clears constricted airways, reduces bronchial wheezing, dilutes stubborn lung mucus, and eases asthmatic breathing.',
        'size': '200 ml / 60 Tablets',
        'price_inr': 549
    },
    'n acetyl cysteine': {
        'name': 'OnlyVeda N-Acetyl Cysteine (NAC 600mg)',
        'category': 'Respiratory & Lungs',
        'key_ingredients': ['N-Acetyl L-Cysteine (600mg)'],
        'benefits': 'Powerful mucolytic and glutathione precursor that dissolves thick respiratory phlegm and protects lung tissue.',
        'size': '60 Effervescent Tablets',
        'price_inr': 899
    },
    'kanchanar guggul': {
        'name': 'OnlyVeda Kanchanar Guggul Traditional',
        'category': 'Lymphatic & Respiratory Health',
        'key_ingredients': ['Kanchanar Bark', 'Shuddha Guggulu', 'Triphala', 'Trikatu'],
        'benefits': 'Classical Ayurvedic formulation to eliminate deep cellular congestion and cystic growths.',
        'size': '60 Tablets',
        'price_inr': 449
    },
    'Vitamin C': {
        'name': 'OnlyVeda Natural Vitamin C + Zinc',
        'category': 'Oral Health & Healing',
        'key_ingredients': ['Phyllanthus Emblica (Amla Extract 1000mg)', 'Zinc Citrate'],
        'benefits': 'Rapid oral ulcer healing, strengthens bleeding gums, and bolsters collagen in periodontal tissues.',
        'size': '60 Chewables',
        'price_inr': 399
    },
    'Hepatreat': {
        'name': 'OnlyVeda Hepatreat Hepatic Care',
        'category': 'Liver & Stomach Detox',
        'key_ingredients': ['Milk Thistle 80% Silymarin', 'Bhumi Amla', 'Kalmegh', 'Kutki'],
        'benefits': 'Reverses sluggish liver function, regulates bile secretion, resolves chronic constipation, and heals digestive ulcers.',
        'size': '60 Tablets',
        'price_inr': 749
    },
    'mouth wash': {
        'name': 'OnlyVeda Herbal Ayurvedic Mouth Wash',
        'category': 'Dental & Oral Care',
        'key_ingredients': ['Clove Oil (Laung)', 'Neem Extract', 'Bakul', 'Tea Tree Oil'],
        'benefits': 'Combats pyorrhea pathogens, stops bleeding gums, removes plaque, and freshens breath all day.',
        'size': '200 ml Bottle',
        'price_inr': 299
    },
    'Xemma cream': {
        'name': 'OnlyVeda Xemma Anti-Acne & Blemish Cream',
        'category': 'Skin & Face Care',
        'key_ingredients': ['Tea Tree Oil', 'Neem', 'Salicylic Acid from Willow Bark', 'Aloe Vera'],
        'benefits': 'Clears active cystic acne, diminishes dark blemish spots, and unclogs facial pores.',
        'size': '50g Tube',
        'price_inr': 449
    },
    'Anti acne face wash': {
        'name': 'OnlyVeda Clarifying Anti-Acne Face Wash',
        'category': 'Skin & Face Care',
        'key_ingredients': ['Neem Extract', 'Tulsi', 'Green Tea', 'Zinc PCA'],
        'benefits': 'Purifies excess sebum, prevents breakouts, and soothes facial irritation.',
        'size': '150 ml',
        'price_inr': 349
    },
    'ella gorgeus kit': {
        'name': 'OnlyVeda Ella Gorgeous Radiance Kit',
        'category': 'Skin & Face Care',
        'key_ingredients': ['Kumkumadi Oil', 'L-Glutathione', 'Saffron Extract', 'Niacinamide'],
        'benefits': 'Complete 3-step skincare regimen for skin brightening, melanin reduction, and natural glow.',
        'size': 'Complete Treatment Kit',
        'price_inr': 1499
    },
    'sun screen lotion': {
        'name': 'OnlyVeda Broad-Spectrum SPF 50 Herbal Sunscreen',
        'category': 'Skin Protection',
        'key_ingredients': ['Carrot Seed Oil', 'Raspberry Extract', 'Zinc Oxide', 'Aloe Vera'],
        'benefits': 'UVA/UVB shielding prevents hyperpigmentation, tanning, and premature photo-aging.',
        'size': '100 ml Lotion',
        'price_inr': 499
    },
    'serum': {
        'name': 'OnlyVeda Advanced Anti-Ageing Face Serum',
        'category': 'Skin & Anti-Ageing',
        'key_ingredients': ['Bakuchiol (Natural Retinol Alternative)', 'Hyaluronic Acid', 'Gotu Kola'],
        'benefits': 'Smooths fine lines and wrinkles, stimulates natural collagen, and firms sagging facial contours.',
        'size': '30 ml Dropper',
        'price_inr': 899
    },
    'Throatwal': {
        'name': 'OnlyVeda Throatwal Soothing Lozenges & Gargle',
        'category': 'Throat & Tonsil Care',
        'key_ingredients': ['Yashtimadhu (Licorice)', 'Khadira', 'Peppermint', 'Pippali'],
        'benefits': 'Immediate relief from tonsillitis swelling, sore throat friction, and difficulty swallowing.',
        'size': '100 ml / 30 Lozenges',
        'price_inr': 349
    },
    'Rhiza': {
        'name': 'OnlyVeda Rhiza Mucosal Gut Shield',
        'category': 'Stomach & Gastric Health',
        'key_ingredients': ['Deglycyrrhizinated Licorice (DGL)', 'Slippery Elm', 'Marshmallow Root'],
        'benefits': 'Forms a protective bio-layer over stomach mucosa, neutralizes acid reflux (GERD), and extinguishes heartburn.',
        'size': '60 Chewables',
        'price_inr': 649
    },
    'Avipathikar tablet': {
        'name': 'OnlyVeda Avipattikar Pitta-Balance Tablet',
        'category': 'Stomach & Gastric Health',
        'key_ingredients': ['Amla', 'Haritaki', 'Bibhitaki', 'Trikatu', 'Nishoth', 'Cardamom'],
        'benefits': 'Classical Ayurvedic Pitta-pacifying digestive that eliminates severe gas, hyperacidity, and sour burps.',
        'size': '60 Tablets',
        'price_inr': 399
    },
    'Laxia': {
        'name': 'OnlyVeda Laxia Gentle Overnight Colon Cleanse',
        'category': 'Digestive & Bowel Health',
        'key_ingredients': ['Senna Standardized Extract', 'Haritaki', 'Castor Seed Oil Extracts'],
        'benefits': 'Non-habit-forming overnight relief from acute and stubborn constipation; ensures smooth, effortless morning bowel movement.',
        'size': '30 Tablets',
        'price_inr': 349
    },
    'Trifala/satwik': {
        'name': 'OnlyVeda Triphala Satwik Pure Digestive Detox',
        'category': 'Digestive Health',
        'key_ingredients': ['Equal proportion Amla, Haritaki, Bibhitaki'],
        'benefits': 'Tones colon muscles, provides natural prebiotic fiber, and promotes regular gentle bowel elimination.',
        'size': '60 Tablets / 100g Powder',
        'price_inr': 399
    },
    'prowal': {
        'name': 'OnlyVeda Prowal Synbiotic Gut Restorer',
        'category': 'Stomach & Intestinal Health',
        'key_ingredients': ['50 Billion Spore-Forming Probiotics', 'Prebiotic FOS', 'Zinc'],
        'benefits': 'Stops diarrhea and loose motions, restores gut flora disrupted by infections, and heals mucosal lining.',
        'size': '30 Veggie Capsules',
        'price_inr': 799
    },
    'Milk thistle': {
        'name': 'OnlyVeda Milk Thistle Silymarin Detox',
        'category': 'Liver & Systemic Detox',
        'key_ingredients': ['Milk Thistle 80% Silymarin Extract (300mg)', 'Dandelion Root'],
        'benefits': 'Purifies internal toxins, clears liver-related acne, and balances uric acid.',
        'size': '60 Veggie Capsules',
        'price_inr': 749
    },
    'liver detox': {
        'name': 'OnlyVeda Liver Detox Formula',
        'category': 'Liver & Systemic Detox',
        'key_ingredients': ['Kalmegh', 'Bhumi Amla', 'Kutki', 'Punarnava'],
        'benefits': 'Purifies toxins, clears excess uric acid, prevents gout crystallisation, and supports hepatic metabolism.',
        'size': '60 Capsules',
        'price_inr': 699
    },
    'calciumus': {
        'name': 'OnlyVeda Calciumus Forte',
        'category': 'Bone & Dental Health',
        'key_ingredients': ['Elemental Calcium (from Shankh Bhasma)', 'Vitamin D3', 'Magnesium', 'Zinc'],
        'benefits': 'Strengthens bone matrix, enhances rapid fracture healing, and rebuilds tooth enamel against cavities.',
        'size': '60 Tablets',
        'price_inr': 499
    },
    'Vitamin D3': {
        'name': 'OnlyVeda Pure Vitamin D3 Chewables',
        'category': 'Dental & Bone Health',
        'key_ingredients': ['Vitamin D3 (Cholecalciferol 60,000 IU equivalent)', 'Phosphorus'],
        'benefits': 'Essential for tooth mineralization, calcium absorption in oral bones, and cavity prevention.',
        'size': '30 Chewable Tablets',
        'price_inr': 399
    },
    'Hepatreat tablet': {
        'name': 'OnlyVeda Hepatreat Hepatic Tablets',
        'category': 'Stomach & Gastric Ulcer Care',
        'key_ingredients': ['Standardized Silymarin 80%', 'Yashtimadhu', 'Amla', 'Kutki'],
        'benefits': 'Soothes inflamed stomach lining, heals gastric and peptic mucosal ulcers, and regulates digestive enzymes.',
        'size': '60 Tablets',
        'price_inr': 749
    }
}

# Aliases to map raw supplement strings to product_meta keys
aliases = {
    'ashyuka plus': 'Ashyuka plus',
    'immuferin': 'immuferin',
    'calcimus': 'Calcimus',
    'prowal': 'prowal',
    'serronil': 'serronil',
    'Serronil': 'serronil',
    'wal D3': 'Wal D3',
    'Vitamin c': 'Vitamin C',
    'hepatreat': 'Hepatreat',
    'Multi vitamin men/women': 'Multivitamin men/women',
    'Multivitamin for men/women': 'Multivitamin men/women',
    'Multivitamin men/ women': 'Multivitamin men/women',
    'Active 365`': 'Active 365'
}

products_list = []
idx = 1
for raw_key, meta in product_meta.items():
    matched_diseases = []
    matched_doses = []
    for dis_name, p_info in protocols.items():
        for s in p_info['supplements']:
            s_name = s['name'].strip()
            mapped_key = aliases.get(s_name, s_name)
            if mapped_key.lower() == raw_key.lower():
                matched_diseases.append(dis_name)
                matched_doses.append(f"{dis_name}: {s['dose']}")

    prod = {
        'product_id': f"OV-PROD-{idx:03d}",
        'name': meta['name'],
        'raw_name': raw_key,
        'category': meta['category'],
        'key_ingredients': meta['key_ingredients'],
        'benefits': meta['benefits'],
        'health_concerns': matched_diseases,
        'dosage_and_usage': ' | '.join(matched_doses) if matched_doses else '1 tablet twice daily after meals',
        'contraindications': 'Consult physician during pregnancy or if taking prescription allopathic medication.',
        'price_inr': meta['price_inr'],
        'size': meta['size'],
        'in_stock': True,
        'tags': [raw_key.lower(), meta['name'].lower(), meta['category'].lower()] + [d.lower() for d in matched_diseases]
    }
    products_list.append(prod)
    idx += 1

with open(PRODUCTS_PATH, 'w', encoding='utf-8') as f:
    json.dump(products_list, f, indent=2, ensure_ascii=False)

print(f"Saved {len(products_list)} OnlyVeda official products to {PRODUCTS_PATH}!")
