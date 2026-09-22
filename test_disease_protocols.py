"""
Comprehensive test verifying disease protocol recommendations from diseases_wise_1.csv
across all 10 Indic languages (+ English).
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
from src.bot_engine import OnlyVedaChatbot

def test_disease_recommendations():
    bot = OnlyVedaChatbot()
    print(f"Loaded {len(bot.data_manager.get_all_products())} official OnlyVeda products.")

    test_cases = [
        ("hi", "मुझे हाई ब्लड प्रेशर की शिकायत है", "High blood presure", ["Linopress", "L-Arginine", "Arjuna"]),
        ("bn", "আমার খুব গ্যাস ও অ্যাসিডিটি হচ্ছে", "gastritis (acidity and gas)", ["Ashyuka", "Rhiza", "Avipattikar"]),
        ("mr", "माझे गुडघे खूप झिजले आहेत आणि ऑस्टिओआर्थरायटिस आहे", "osteo arthritis", ["Serronil", "Calcimus", "Wal D3"]),
        ("te", "నాకు తీవ్రమైన మలబద్ధకం ఉంది, పొట్ట సాఫీగా కావడం లేదు", "Constipation", ["Ashyuka", "Laxia", "Triphala"]),
        ("ta", "எனக்கு வாயில் புண் அதிகமாக உள்ளது", "mouth ulcer", ["Multivitamin", "Vitamin C", "Hepatreat"]),
        ("gu", "મારા ચહેરા પર ખૂબ ખીલ અને પિમ્પલ્સ છે", "acne", ["Active 365", "Xemma", "Face Wash"]),
        ("ur", "मुझे कमर और पीठ में شدید दर्द है", "Muscular back pain", ["Active 365", "Strenus", "Strenus"]),
        ("kn", "ನನಗೆ ಉಬ್ಬಸ ಮತ್ತು ಆಸ್ತಮಾ ತೊಂದರೆ ಇದೆ", "Brochial asthma", ["Respitone", "Cysteine", "Ashyuka"]),
        ("or", "କ୍ୟାନ୍ସର ରୋଗୀଙ୍କ ପାଇଁ କଣ ଔଷଧ ଅଛି?", "All type of cancer", ["Immuferin", "Ashyuka", "Active 365"]),
        ("ml", "എനിക്ക് സെർവിക്കൽ സ്പോണ്ടിലൈറ്റിസും കഴുത്ത് വേദനയുമുണ്ട്", "spondilits", ["Immuferin", "Active 365", "Ashwagandha"]),
        ("en", "I am suffering from chronic constipation for weeks", "Chronic constipation", ["Ashyuka", "Hepatreat", "Laxia"])
    ]

    for lang, query, expected_disease, expected_supps in test_cases:
        print(f"\n==========================================")
        print(f"[{lang.upper()}] Query: {query}")
        res = bot.chat(query, selected_lang=lang)
        
        disease_info = res.get("disease_protocol")
        matched_disease = disease_info["disease"] if disease_info else "General Match"
        print(f"Matched Disease: {matched_disease} (Expected: {expected_disease})")
        
        prods = [p['name'] for p in res['products']]
        doses = [p.get('prescribed_dose') for p in res['products']]
        print(f"Recommended OnlyVeda Products ({len(prods)}):")
        for p, d in zip(prods, doses):
            print(f"  - {p} | Dose: {d}")
            
        assert len(prods) > 0, f"No products recommended for {query}"
        for exp in expected_supps:
            found = any(exp.lower() in p.lower() for p in prods)
            assert found, f"Expected supplement '{exp}' not found in recommendations: {prods}"
            
        print("Response Preview:")
        print(res['response'][:180].replace('\n', ' ') + "...")
        print("Status: ✅ PASSED")

    print("\n🎉 ALL 11 MULTILINGUAL DISEASE PROTOCOL TESTS PASSED WITH 100% ACCURACY!")

if __name__ == "__main__":
    test_disease_recommendations()
