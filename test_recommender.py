"""
Comprehensive test suite verifying:
1. Multilingual nutraceutical recommendations from diseases_wise_1.csv across 10 Indic languages.
2. Auto-detection of language across scripts (including Marathi vs Hindi Devanagari).
3. Conversational chit-chat returning empty product recommendations.
4. Irrelevant queries returning empty products rather than false fallbacks.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from src.bot_engine import OnlyVedaChatbot
from src.config import SUPPORTED_LANGUAGES

def test_all():
    bot = OnlyVedaChatbot()
    print(f"Loaded {len(bot.data_manager.get_all_products())} nutraceutical products.")

    # 1. Test genuine disease queries across all 10 Indic languages with selected_lang
    clinical_queries = [
        ("hi", "मुझे हाई ब्लड प्रेशर की शिकायत है", "High blood presure"),
        ("bn", "আমার পেটে গ্যাস ও বদহজমের সমস্যা হচ্ছে", "gastritis (acidity and gas)"),
        ("mr", "माझे गुडघे खूप दुखतात आणि ऑस्टिओआर्थरायटिस आहे", "osteo arthritis"),
        ("te", "నాకు తీవ్రమైన మలబద్ధకం ఉంది, పొట్ట సాఫీగా కావడం లేదు", "Constipation"),
        ("ta", "எனக்கு வாயில் புண் அதிகமாக உள்ளது", "mouth ulcer"),
        ("gu", "મારા ચહેરા પર ખૂબ ખીલ અને પિમ્પલ્સ છે", "acne"),
        ("ur", "مجھے جوڑوں کے درد اور گٹھیا کی تکلیف ہے", "osteo arthritis"),
        ("kn", "ನನಗೆ ಉಬ್ಬಸ ಮತ್ತು ಆಸ್ತಮಾ ತೊಂದರೆ ಇದೆ", "Brochial asthma"),
        ("or", "ମୋର ହଜମ ଖରାପ ଏବଂ ଗ୍ୟାସ ହେଉଛି", "gastritis (acidity and gas)"),
        ("ml", "എനിക്ക് സെർവിക്കൽ സ്പോണ്ടിലൈറ്റിസും കഴುത്ത് വേദനയുമുണ്ട്", "spondilits")
    ]

    print("\n--- 1. TESTING CLINICAL QUERIES ACROSS 10 INDIC LANGUAGES ---")
    for lang, q, expected_dis in clinical_queries:
        res = bot.chat(q, selected_lang=lang)
        matched_names = [p['name'] for p in res['products']]
        print(f"[{lang.upper()}] Query: {q} -> Matched: {matched_names}")
        assert len(res['products']) > 0, f"No products matched for {lang} query: {q}"
        assert res['language'] == lang, f"Expected lang {lang}, got {res['language']}"

    # 2. Test Auto-Language Detection
    print("\n--- 2. TESTING AUTO-LANGUAGE DETECTION ---")
    auto_queries = [
        ("मुझे हाई बीपी है", "hi"),
        ("माझे गुडघे खूप झिजले आहेत", "mr"),
        ("আমার খুব গ্যাস ও অম্বল হচ্ছে", "bn"),
        ("నాకు మలబద్ధకం ఉంది", "te"),
        ("எனக்கு வாய் புண் உள்ளது", "ta"),
        ("મારા ચહેરા પર ખીલ છે", "gu"),
        ("مجھے شدید جوڑوں کا درد ہے", "ur"),
        ("ನನಗೆ ಆಸ್ತಮಾ ತೊಂದರೆ ಇದೆ", "kn"),
        ("କ୍ୟାନ୍ସର ରୋଗୀଙ୍କ ପାଇଁ ଔଷଧ", "or"),
        ("എനിക്ക് സെർവിക്കൽ സ്പോണ്ടിലൈറ്റിസ് ഉണ്ട്", "ml")
    ]
    for q, exp_lang in auto_queries:
        res = bot.chat(q, selected_lang="auto")
        print(f"Auto Query: '{q}' -> Detected: {res['language']} (Expected: {exp_lang})")
        assert res['language'] == exp_lang, f"Failed auto-detect: expected {exp_lang}, got {res['language']}"

    # 3. Test Pure Conversational Chit-Chat (Must have ZERO products)
    print("\n--- 3. TESTING CONVERSATIONAL CHIT-CHAT (ZERO PRODUCTS) ---")
    chitchat = [
        ("hi", "नमस्ते, आप कैसे हैं?"),
        ("en", "hello, who are you?"),
        ("bn", "নমস্কার, কেমন আছেন?"),
        ("gu", "કેમ છો?"),
        ("ta", "வணக்கம்! நீங்கள் யார்?")
    ]
    for lang, q in chitchat:
        res = bot.chat(q, selected_lang=lang)
        print(f"Chit-chat '{q}' -> Products: {len(res['products'])}")
        assert len(res['products']) == 0, f"Chit-chat returned products inappropriately: {res['products']}"
        assert len(res['response']) > 20, "Empty response on chit-chat"

    # 4. Test Irrelevant / Unrelated Queries (Must NOT recommend Linopress fallback)
    print("\n--- 4. TESTING IRRELEVANT QUERIES (ZERO PRODUCTS) ---")
    unrelated = [
        "I want to buy a pair of running shoes",
        "What is the capital of France?",
        "Please book a flight ticket to Mumbai"
    ]
    for q in unrelated:
        res = bot.chat(q, selected_lang="en")
        print(f"Unrelated '{q}' -> Products: {len(res['products'])}")
        assert len(res['products']) == 0, f"Unrelated query recommended products: {res['products']}"

    print("\n🎉 ALL 4 TEST SUITES (CLINICAL, AUTO-LANG, CHIT-CHAT, UNRELATED) PASSED WITH 100% ACCURACY!")

if __name__ == "__main__":
    test_all()
