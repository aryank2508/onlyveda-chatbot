"""
Chatbot Engine for OnlyVeda Multilingual Nutraceutical Recommendations.
Integrates exact disease-to-supplement protocols from diseases_wise_1.csv
with hybrid retrieval and localized Indic response generation.
"""

import os
import re
import unicodedata
from typing import List, Dict, Any, Optional, Tuple
import urllib.request
import json

from src.config import (
    SUPPORTED_LANGUAGES,
    SYSTEM_PROMPT_INDIC_TEMPLATE,
    SYSTEM_PROMPT_GENERAL_CONSULTATION,
    SYSTEM_PROMPT_NUTRACEUTICAL_EXPLANATION,
    CONVERSATIONAL_PATTERNS,
    CONVERSATIONAL_RESPONSES,
    DEFAULT_GEMINI_API_KEY,
    EDUCATIONAL_PATTERNS,
    WELLNESS_PATTERNS,
    NON_HEALTH_PATTERNS,
    TREATMENT_OVERRIDE_PATTERNS,
    OFFLINE_EDUCATIONAL_KNOWLEDGE
)
from src.data_manager import ProductDataManager
from src.recommender import NutraceuticalRecommender
from src.memory_manager import ConversationMemory


class OnlyVedaChatbot:
    def __init__(
        self,
        data_manager: Optional[ProductDataManager] = None,
        api_key: Optional[str] = None,
        memory: Optional[ConversationMemory] = None
    ):
        self.data_manager = data_manager or ProductDataManager()
        self.memory = memory or ConversationMemory()
        self.recommender = NutraceuticalRecommender(self.data_manager)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or DEFAULT_GEMINI_API_KEY
        self.history: List[Dict[str, str]] = []

    def set_api_key(self, api_key: str):
        """Update API key at runtime from UI."""
        self.api_key = api_key.strip() if api_key else None

    def reload_data(self):
        """Reload data and rebuild search index when new products are fed."""
        self.data_manager.load_products()
        self.recommender = NutraceuticalRecommender(self.data_manager)

    def detect_language(self, text: str) -> str:
        """
        Heuristic language detection for Indic scripts based on Unicode ranges
        with specialized lexical disambiguation for Devanagari (Marathi vs Hindi).
        """
        marathi_markers = {
            'आहे', 'आहेत', 'नाही', 'माझे', 'माझ्या', 'माझा', 'माझी', 'च्या', 'चे', 'ची',
            'ला', 'मध्ये', 'झाले', 'झाली', 'खूप', 'कसे', 'कसा', 'काय',
            'कंबरदुखी', 'सांधेदुखी', 'त्रास', 'गुडघे', 'पोटात', 'दुखतात', 'दुखणे', 'दुखते'
        }
        hindi_markers = {
            'है', 'हैं', 'का', 'के', 'की', 'को', 'में', 'से', 'पर', 'और', 'या', 'मुझे', 'मेरा', 'मेरी', 'बहुत', 'ज्यादा', 'क्या', 'कौन'
        }

        has_devanagari = False
        for char in text:
            code = ord(char)
            if 0x0900 <= code <= 0x097F:
                has_devanagari = True
            elif 0x0980 <= code <= 0x09FF:
                return "bn"  # Bengali
            elif 0x0A80 <= code <= 0x0AFF:
                return "gu"  # Gujarati
            elif 0x0B00 <= code <= 0x0B7F:
                return "or"  # Odia
            elif 0x0B80 <= code <= 0x0BFF:
                return "ta"  # Tamil
            elif 0x0C00 <= code <= 0x0C7F:
                return "te"  # Telugu
            elif 0x0C80 <= code <= 0x0CFF:
                return "kn"  # Kannada
            elif 0x0D00 <= code <= 0x0D7F:
                return "ml"  # Malayalam
            elif 0x0600 <= code <= 0x06FF:
                return "ur"  # Arabic/Urdu

        if has_devanagari:
            # Check for Marathi specific character 'ळ' (U+0933)
            if '\u0933' in text:
                return "mr"
            clean_words = set(''.join(ch for ch in text if not unicodedata.category(ch).startswith('P')).split())
            if clean_words & marathi_markers and not (clean_words & hindi_markers):
                return "mr"
            if clean_words & marathi_markers:
                # If both present, check count
                mr_count = len(clean_words & marathi_markers)
                hi_count = len(clean_words & hindi_markers)
                if mr_count > hi_count:
                    return "mr"
            return "hi"

        return "en"

    def detect_conversational_intent(self, text: str) -> Optional[str]:
        """
        Detects if the query is a conversational prompt (greeting, identity, etc.)
        safely across all Indic Unicode scripts.
        """
        cleaned = ''.join(ch for ch in text if not unicodedata.category(ch).startswith('P')).strip().lower()
        if not cleaned:
            return None

        words = cleaned.split()

        for intent, patterns in CONVERSATIONAL_PATTERNS.items():
            for p in patterns:
                p_lower = p.lower().strip()
                if cleaned == p_lower:
                    return intent
                if len(words) <= 8:
                    if re.search(r'(?:\s|^)' + re.escape(p_lower) + r'(?:\s|$)', cleaned):
                        return intent
                    if len(p_lower) >= 3 and p_lower in cleaned:
                        return intent

        return None

    def get_quick_suggestions(self, lang: str, has_products: bool = False, disease_name: Optional[str] = None) -> List[str]:
        """Quick tap suggestion follow-ups removed per user request."""
        return []

    def _call_gemini_api(
        self,
        prompt: str,
        target_lang: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[str]:
        """Call Gemini API with multi-model fallback chain and multi-turn memory support."""
        if not self.api_key:
            return None

        # Fallback chain of models to withstand 429 quota exhaustion and 503 service limits
        models_to_try = [
            "gemini-flash-lite-latest",
            "gemini-flash-latest",
            "gemma-4-26b-a4b-it",
            "gemini-2.5-flash"
        ]

        contents = []
        if conversation_history:
            for msg in conversation_history[-6:]:
                role = "user" if msg.get("role") == "user" else "model"
                text = msg.get("content", "").strip()
                if text:
                    if len(text) > 400:
                        text = text[:400] + "..."
                    contents.append({
                        "role": role,
                        "parts": [{"text": text}]
                    })

        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 1200
            }
        }
        encoded_data = json.dumps(payload).encode("utf-8")

        for model_name in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
            try:
                req = urllib.request.Request(
                    url,
                    data=encoded_data,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=6) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    candidates = result.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
            except Exception as e:
                # Log model failure and attempt next in chain
                print(f"Gemini API model {model_name} attempt failed: {e}. Trying next available model...")
                continue

        print("All Gemini API models exhausted or offline. Falling back to native localized generator.")
        return None

    def detect_health_topic(self, text: str) -> Optional[str]:
        """Detect health topic across all 11 Indic languages (+ English) with strict word boundaries."""
        cleaned = text.strip().lower()

        # Word-boundary check helper for short/ambiguous English & Indic roots
        def has_word(pattern_str: str) -> bool:
            return bool(re.search(pattern_str, cleaned))

        if has_word(r'\b(?:pain|hurt|ache|aches)\b') or any(w in cleaned for w in ["दर्द", "दुखावा", "दुखणे", "दुखतात", "દુખાવો", "నొప్పి", "నొప్పులు", "வலி", "வலிகள்", "വേദന", "ব্যথা", "ବିନ୍ଧା", "ದರಜ", "ನೋವು", "درد"]):
            return "pain"
        elif (has_word(r'\b(?:heart|cardiac|cardiovascular|artery|arteries|angina|arrhythmia)\b') or
              any(w in cleaned for w in ["हार्ट", "हृदय", "હૃદય", "గుండె", "இதய", "ಹೃದಯ", "ഹൃദയം", "হৃদ"]) or
              (has_word(r'(?:\s|^)दिल(?:\s|$)') and not any(cw in cleaned for cw in ["दिल्ली", "delhi", "दिलचस्प"]))):
            return "heart_disease"
        elif has_word(r'\b(?:bp|blood\s+pressure|hypertension)\b') or any(w in cleaned for w in ["रक्तचाप", "ब्लड प्रेशर", "બ્લડ પ્રેશર", "రక్తపోటు", "ரத்த அழுத்தம்", "উচ্চ রক্তচাপ"]):
            return "blood_pressure"
        elif any(w in cleaned for w in ["cholesterol", "lipid", "triglyceride", "कोलेस्ट्रॉल", "કોલેસ્ટ્રોલ", "కొలెస్ట్రాల్", "கொலஸ்ட்ரால்"]):
            return "cholesterol"
        elif any(w in cleaned for w in ["diabetes", "sugar", "glucose", "insulin", "मधुमेह", "शुगर", "डायबिटीज", "ડાયાબિટીસ", "சர்க்கரை", "మధుమేహం", "ಮಧುಮೇಹ", "പ്രമേഹം", "ডায়াবেটিস"]):
            return "diabetes"
        elif any(w in cleaned for w in ["stress", "anxiety", "depression", "insomnia", "cortisol", "restless", "mental health", "तनाव", "चिंता", "नींद", "अनिद्रा", "बेचैनी", "डिप्रेशन", "તણાવ", "ઊંઘ", "ఒత్తిడి", "నిద్ర", "ഉറക്കം", "মানসিক চাপ", "மன அழுத்தம்"]):
            return "stress_sleep"
        elif any(w in cleaned for w in ["migraine", "headache", "माइग्रेन", "सिरदर्द", "माथाना दुखावो", "ماइग्रेन"]):
            return "migraine"
        elif any(w in cleaned for w in ["sleep", "melatonin", "नींद", "ઊંઘ", "నిద్ర", "உறக்கம்", "ഉറക്കം", "ঘুম"]):
            return "sleep_disorder"
        elif any(w in cleaned for w in ["immunity", "immune", "infection", "cold", "fever", "ojas", "इम्युनिटी", "संक्रमण", "बुखार", "सर्दी", "रोग प्रतिरोधक", "રોગપ્રતિકારક", "రోగనిరోధక", "রোগ প্রতিরোধ", "நோய் எதிர்ப்பு", "रोगप्रतिकारक"]):
            return "immunity"
        elif any(w in cleaned for w in ["dengue", "डेंगू", "ডেঙ্গু", "ڈینگی"]):
            return "dengue"
        elif any(w in cleaned for w in ["flu", "influenza", "seasonal flu", "फ्लू", "ફ્લૂ"]):
            return "flu"
        elif any(w in cleaned for w in ["tuberculosis", "tb", "क्षय", "टीबी", "ટીબી", "క్షయ"]):
            return "tuberculosis"
        elif any(w in cleaned for w in ["asthma", "lung", "lungs", "cough", "breath", "wheezing", "bronchitis", "sinus", "दमा", "अस्थमा", "फेफड़े", "खांसी", "बलगम", "शिन्यूसाइटिस", "સાઇनसाइटिस", "శ్వాస", "इनहेलर", "COPD"]):
            return "asthma_lungs"
        elif has_word(r'\b(?:gas|acidity|gerd|heartburn|indigestion|digestion|stomach|gut|ibs|colitis)\b') or any(w in cleaned for w in ["पेट दर्द", "पाचन", "एसिडिटी", "गैस", "अपच", "एसिड", "આઈ.બી.એસ.", "IBS", "Gujarat", "జీర్ణ", "অম্বল", "হজম"]):
            return "digestion"
        elif any(w in cleaned for w in ["constipation", "bowel", "stool", "hard stool", "कब्ज", "पेट साफ", "शौच", "કબજિયાત", "बद्धकोष्ठता", "మలబద్ధకం", "மலச்சிக்கல்", "മലബന്ധം", "কোষ্ঠকাঠিন্য"]):
            return "constipation"
        elif any(w in cleaned for w in ["stomach ulcer", "peptic ulcer", "gastric ulcer", "ulcer", "पेट के छाले", "अल्सर", "ਅਲਸਰ", "పేగు"]):
            return "stomach_ulcer"
        elif any(w in cleaned for w in ["diarrhea", "diarrhoea", "loose motion", "dysentery", "दस्त", "जुलाब", "ઝાડા", "విరేచనాలు", "পেট খারাপ"]):
            return "diarrhea"
        elif any(w in cleaned for w in ["piles", "hemorrhoids", "anal", "fissure", "fistula", "बवासीर", "पाइल्स", "ਹੇਮੋਰਾਇਡਸ"]):
            return "piles_anal"
        elif any(w in cleaned for w in ["kidney", "kidney stone", "urinary", "urine", "bladder", "गुर्दा", "पथरी", "किडनी", "किडनी स्टोन", "ਗੁਰਦਾ", "కిడ్నీ", "சிறுநீரகம்"]):
            return "kidney"
        elif any(w in cleaned for w in ["liver", "fatty liver", "jaundice", "hepatitis", "cirrhosis", "लिवर", "जिगर", "पीलिया", "हेपेटाइटिस", "लिव्हर", "ਜਿਗਰ", "కాలేయం", "கல்லீரல்", "കരൾ", "লিভার", "সিরোসিস"]):
            return "liver"
        elif any(w in cleaned for w in ["arthritis", "osteoarthritis", "joint", "knee", "knees", "gout", "stiffness", "uric acid", "rheumatoid", "गठिया", "जोड़ों", "घुटना", "घुटनों", "सांधे", "सांधेदुखी", "गुडघे", "ਗਠੀਆ", "ఆర్థరైటిస్", "மூட்டுவலி"]):
            return "joints_arthritis"
        elif any(w in cleaned for w in ["fracture", "bone", "bones", "osteoporosis", "density", "हड्डी", "हड्डियों", "फ्रैक्चर", "हाड", "ਹੱਡੀ", "ఎముకలు", "எலும்பு", "হাড়"]):
            return "bone_fracture"
        elif any(w in cleaned for w in ["back pain", "spine", "lumbar", "कमर दर्द", "पीठ दर्द", "कमर", "कंबरदुखी", "ਕਮਰ ਦਰਦ", "నడుము", "முதுகு"]):
            return "back_pain"
        elif any(w in cleaned for w in ["spondylitis", "cervical", "neck pain", "sciatica", "sciatic", "cytica", "गर्दन दर्द", "गर्दन", "सर्वाइकल", "साइटिका", "ਸਰਵਾਇਕਲ", "మెడ నొప్పి", "கழுத்து வலி"]):
            return "spondylitis"
        elif any(w in cleaned for w in ["acne", "pimple", "pimples", "blemish", "eczema", "psoriasis", "skin allergy", "rash", "ring worm", "कील", "मुंहासे", "पिंपल", "एक्जिमा", "सोरायसिस", "ਮੁਹਾਂਸੇ", "మొటిమలు", "பருக்கள்", "ব্রণ"]):
            return "skin_acne"
        elif any(w in cleaned for w in ["skin glow", "pigmentation", "wrinkle", "wrinkles", "anti-ageing", "skin lightening", "fair skin", "dark spots", "त्वचा", "चमक", "झाइयां", "झुर्रियां", "ਗੋਰੀ ਚਮੜੀ", " చర్మం"]):
            return "skin_brightening"
        elif any(w in cleaned for w in ["hair", "hair fall", "dandruff", "baldness", "grey hair", "बाल", "बाल झड़ना", "बालों", "केस गळणे", "ਵਾਲ ਝੜਨਾ", "జుట్టు రాలడం", "முடி உதிர்தல்", "চুল পড়া"]):
            return "hair_care"
        elif any(w in cleaned for w in ["mouth ulcer", "mouth", "cavity", "cavities", "pyorrhea", "teeth", "tooth", "dental", "मुंह के छाले", "दांत", "ਦੰਦ", "పంటి", "வாய் புண்", "মুখে ঘা"]):
            return "mouth_dental"
        elif any(w in cleaned for w in ["tonsil", "tonsillitis", "throat", "sore throat", "टॉन्सिल", "गला", "गले में खराश", "ਟੌਂਸਲ", "గొంతు నొప్పి", "தொண்டை வலி"]):
            return "tonsillitis"
        elif has_word(r'\b(?:ear|ears|otitis)\b') or any(w in cleaned for w in ["कान", "ਕੰਨ", "చెవి", "காது", "ಕಿವಿ", "ചെവി"]):
            return "ear_infection"
        elif any(w in cleaned for w in ["eye", "eyes", "vision", "cataract", "आंख", "ਅੱਖ", "కళ్ళు", "கண்", "ക്ഷ്", "চোখ"]):
            return "eye_health"
        elif any(w in cleaned for w in ["thyroid", "थायरॉइड", "थायरॉयड", "ਥਾਇਰਾਇਡ", "థైరాయిడ్", "தைராய்டு"]):
            return "thyroid"
        elif any(w in cleaned for w in ["weight", "obesity", "overweight", "fat", "slim", "वजन", "मोटापा", "ਮੋਟਾਪਾ", "బరువు", "உடல் பருமன்", "ওজন"]):
            return "obesity"
        elif any(w in cleaned for w in ["period", "menstrual", "menstruation", "pcod", "pcos", "leucorrhoea", "vaginal", "माहवारी", "मासिक धर्म", "पीरियड्स", "ਮਹੀਨਾਵਾਰੀ", "ঋতুস্রাব"]):
            return "womens_health"
        elif any(w in cleaned for w in ["libido", "sexual", "erectile", "testosterone", "semen", "sperm", "virility", "यौन", "सेक्स", "ਜਿਨਸੀ", "లైంగిక", "பாலியல்"]):
            return "sexual_health"
        elif any(w in cleaned for w in ["varicose", "veins", "vericose", "नसें", "ਨਾੜੀਆਂ", "నరాలు"]):
            return "varicose_veins"
        elif any(w in cleaned for w in ["parkinson", "paralysis", "stroke", "पक्षाघात", "लकवा", "पार्किंसन", "ਲਕਵਾ", "పక్షవాతం"]):
            return "neurological"
        elif any(w in cleaned for w in ["vertigo", "dizziness", "चक्कर", "ਚੱਕਰ", "తలతిరుగుట", "தலைச்சுற்றல்"]):
            return "vertigo"
        elif any(w in cleaned for w in ["cancer", "tumor", "कैंसर", "ਕੈਂਸਰ", "క్యాన్సర్", "புற்றுநோய்", "ক্যান্সার"]):
            return "cancer"
        elif any(w in cleaned for w in ["vitality", "energy", "stamina", "fatigue", "weakness", "appetite", "कमजोरी", "थकान", "सुस्ती", "ताकत", "ਕਮਜ਼ੋਰੀ", "బలహీనత", "சோர்வு", "দুর্বলতা"]):
            return "vitality_energy"
        elif any(w in cleaned for w in ["nutraceutical", "nutraceuticals", "supplement", "vitamin", "mineral", "न्यूट्रास्युटिकल", "ਨਿਊਟ੍ਰਾਸਿਊਟੀਕਲ"]):
            return "nutraceutical"
        elif has_word(r'\b(?:ayurveda|ayurvedic|dosha|doshas|vata|pitta|kapha|agni|ama)\b') or any(w in cleaned for w in ["आयुर्वेद", "वात", "पित्त", "कफ"]):
            return "ayurveda"
        return None


    def is_non_health_query(self, text: str) -> bool:
        """Determines if query is completely off-topic or non-health related."""
        cleaned = text.strip().lower()

        for pat in NON_HEALTH_PATTERNS:
            if re.search(pat, cleaned):
                return True

        non_health_words = [
            "python", "coding", "code", "javascript", "developer", "weather", "temperature",
            "prime minister", "president", "capital of", "capital city", "cricket", "ipl", "football",
            "movie", "film", "cinema", "song", "joke", "chutkula", "bitcoin", "crypto",
            "docker", "container", "machine learning", "neural network", "vlookup", "excel",
            "square root", "quadratic", "equation", "roman empire", "multiplied by"
        ]
        return any(nh in cleaned for nh in non_health_words)

    def detect_educational_intent(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Detects if query is an educational, conceptual, or classification inquiry
        (e.g., 'what is pain', 'which are heart dieses', 'हार्ट की कौन सी बीमारियां होती हैं').
        """
        cleaned = text.strip().lower()

        # If query is non-health (joke, python, weather, math, etc.), it's not educational health
        if self.is_non_health_query(text):
            return False, None

        # If user explicitly states they have a personal disease or requests medicine, it's a treatment request
        for top in TREATMENT_OVERRIDE_PATTERNS:
            if re.search(top, cleaned):
                return False, None

        is_edu = False
        for ep in EDUCATIONAL_PATTERNS:
            if re.search(ep, cleaned):
                is_edu = True
                break

        if not is_edu:
            return False, None

        topic = self.detect_health_topic(cleaned)
        # An inquiry is educational health ONLY if a real health topic is present
        if not topic:
            return False, None

        return True, topic

    def detect_wellness_intent(self, text: str) -> Tuple[bool, Optional[str]]:
        """Detects if query is a health tip or wellness improvement goal."""
        cleaned = text.strip().lower()
        for wp in WELLNESS_PATTERNS:
            if re.search(wp, cleaned):
                topic = self.detect_health_topic(cleaned)
                return True, topic or "general"
        return False, None

    def _get_supportive_products_for_topic(self, topic: Optional[str]) -> List[Dict[str, Any]]:
        """Retrieve relevant OnlyVeda products matching the health domain with prescribed doses."""
        prod_map = {
            "pain": ["OnlyVeda Strenus Pain Relief Capsules", "OnlyVeda Strenus Herbal Massage Oil", "OnlyVeda Serronil Joint Care"],
            "heart_disease": ["OnlyVeda Linopress", "OnlyVeda L-Arginine Plus", "OnlyVeda Terminalia Arjuna Extract"],
            "blood_pressure": ["OnlyVeda Linopress", "OnlyVeda L-Arginine Plus", "OnlyVeda Terminalia Arjuna Extract"],
            "cholesterol": ["OnlyVeda Linopress", "OnlyVeda Terminalia Arjuna Extract", "OnlyVeda Ashyuka Plus Syrup"],
            "diabetes": ["OnlyVeda Active 365 Daily Essential", "OnlyVeda Milk Thistle Silymarin Detox", "OnlyVeda Triphala Satwik Pure Digestive Detox"],
            "digestion": ["OnlyVeda Ashyuka Plus Syrup", "OnlyVeda Rhiza Mucosal Gut Shield", "OnlyVeda Avipattikar Pitta-Balance Tablet"],
            "constipation": ["OnlyVeda Ashyuka Plus Syrup", "OnlyVeda Laxia Gentle Overnight Colon Cleanse", "OnlyVeda Triphala Satwik Pure Digestive Detox"],
            "stomach_ulcer": ["OnlyVeda Hepatreat Hepatic Tablets", "OnlyVeda Rhiza Mucosal Gut Shield", "OnlyVeda Ashyuka Plus Syrup"],
            "diarrhea": ["OnlyVeda Prowal Synbiotic Gut Restorer", "OnlyVeda Immuferin Immuno-Shield", "OnlyVeda Ashyuka Plus Syrup"],
            "piles_anal": ["OnlyVeda Anurect Piles Capsules", "OnlyVeda Anurect Piles Ointment", "OnlyVeda Active 365 Daily Essential", "OnlyVeda Hepatreat Hepatic Care"],
            "kidney": ["OnlyVeda Stowip Kidney & Urinary Kit", "OnlyVeda Kidney Detox Formula", "OnlyVeda Panch Tulsi Drops", "OnlyVeda Rhiza Mucosal Gut Shield"],
            "joints_arthritis": ["OnlyVeda Serronil Joint Care", "OnlyVeda Calcimus Coral Calcium Complex", "OnlyVeda Wal D3 Sublingual Spray"],
            "bone_fracture": ["OnlyVeda Hadjod Bone Healer", "OnlyVeda Calciumus Forte", "OnlyVeda Calcimus Coral Calcium Complex"],
            "back_pain": ["OnlyVeda Strenus Pain Relief Capsules", "OnlyVeda Strenus Herbal Massage Oil", "OnlyVeda Active 365 Daily Essential"],
            "spondylitis": ["OnlyVeda Immuferin Immuno-Shield", "OnlyVeda Active 365 Daily Essential", "OnlyVeda KSM-66 Ashwagandha Pure Tablet", "OnlyVeda Mahayograj Guggul"],
            "stress_sleep": ["OnlyVeda KSM-66 Ashwagandha Pure Tablet", "OnlyVeda Active 365 Daily Essential", "OnlyVeda Ashyuka Plus Syrup"],
            "sleep_disorder": ["OnlyVeda Melatonin Sleep Spray", "OnlyVeda KSM-66 Ashwagandha Pure Tablet", "OnlyVeda Ashyuka Plus Syrup"],
            "migraine": ["OnlyVeda Ashyuka Plus Syrup", "OnlyVeda Daily Complete Multivitamin", "OnlyVeda Intelget Brain & Memory Capsules"],
            "vertigo": ["OnlyVeda Daily Complete Multivitamin", "OnlyVeda Intelget Brain & Memory Capsules"],
            "immunity": ["OnlyVeda Immuferin Immuno-Shield", "OnlyVeda Natural Vitamin C + Zinc", "OnlyVeda Active 365 Daily Essential"],
            "dengue": ["OnlyVeda Cariwal Platelet Support", "OnlyVeda Immuferin Immuno-Shield", "OnlyVeda Maha Sudarshan Tablet", "OnlyVeda Rhiza Mucosal Gut Shield"],
            "flu": ["OnlyVeda Immuferin Immuno-Shield", "OnlyVeda Throatwal Soothing Lozenges & Gargle", "OnlyVeda Walinctus Herbal Cough Syrup"],
            "tuberculosis": ["OnlyVeda Daily Complete Multivitamin", "OnlyVeda Respitone Pulmonary Shield", "OnlyVeda Immuferin Immuno-Shield", "OnlyVeda Liver Detox Formula"],
            "asthma_lungs": ["OnlyVeda Respitone Pulmonary Shield", "OnlyVeda N-Acetyl Cysteine (NAC 600mg)", "OnlyVeda Ashyuka Plus Syrup", "OnlyVeda Walinctus Herbal Cough Syrup"],
            "skin_acne": ["OnlyVeda Active 365 Daily Essential", "OnlyVeda Xemma Anti-Acne & Blemish Cream", "OnlyVeda Clarifying Anti-Acne Face Wash", "OnlyVeda Milk Thistle Silymarin Detox"],
            "skin_brightening": ["OnlyVeda Ella Gorgeous Radiance Kit", "OnlyVeda Broad-Spectrum SPF 50 Herbal Sunscreen", "OnlyVeda Glutathione Effervescent", "OnlyVeda Active 365 Daily Essential"],
            "hair_care": ["OnlyVeda Hair 2X Growth Formula", "OnlyVeda Daily Complete Multivitamin", "OnlyVeda Active 365 Daily Essential"],
            "liver": ["OnlyVeda Milk Thistle Silymarin Detox", "OnlyVeda Liver Detox Formula", "OnlyVeda Hepatreat Hepatic Care", "OnlyVeda Ashyuka Plus Syrup"],
            "mouth_dental": ["OnlyVeda Herbal Ayurvedic Mouth Wash", "OnlyVeda Natural Vitamin C + Zinc", "OnlyVeda Daily Complete Multivitamin"],
            "ear_infection": ["OnlyVeda Immuferin Immuno-Shield", "OnlyVeda Active 365 Daily Essential"],
            "tonsillitis": ["OnlyVeda Throatwal Soothing Lozenges & Gargle", "OnlyVeda Immuferin Immuno-Shield", "OnlyVeda Active 365 Daily Essential"],
            "eye_health": ["OnlyVeda I-Well Eye Health Capsules", "OnlyVeda Saptamrit Loh Eye Tablet", "OnlyVeda Triphala Satwik Pure Digestive Detox"],
            "thyroid": ["OnlyVeda Ashyuka Plus Syrup", "OnlyVeda Immuferin Immuno-Shield", "OnlyVeda Daily Complete Multivitamin"],
            "obesity": ["OnlyVeda Biomelt Weight Management Capsules", "OnlyVeda Biomelt Weight Management Liquid", "OnlyVeda Apple Cider Vinegar", "OnlyVeda Hepatreat Hepatic Tablets"],
            "womens_health": ["OnlyVeda Evareg Menstrual Regulator", "OnlyVeda U-She Plus Feminine Care", "OnlyVeda Immuferin Immuno-Shield", "OnlyVeda Daily Complete Multivitamin Women"],
            "sexual_health": ["OnlyVeda Hot Male Plus", "OnlyVeda T-Booster Testosterone Support", "OnlyVeda Pure Shilajit Capsules"],
            "varicose_veins": ["OnlyVeda L-Arginine Plus", "OnlyVeda Ashyuka Plus Syrup"],
            "neurological": ["OnlyVeda Daily Complete Multivitamin", "OnlyVeda KSM-66 Ashwagandha Pure Tablet", "OnlyVeda Ashyuka Plus Syrup"],
            "cancer": ["OnlyVeda Immuferin Immuno-Shield", "OnlyVeda Ashyuka Plus Syrup", "OnlyVeda Active 365 Daily Essential"],
            "vitality_energy": ["OnlyVeda Active 365 Daily Essential", "OnlyVeda Daily Complete Multivitamin", "OnlyVeda KSM-66 Ashwagandha Pure Tablet"],
            "nutraceutical": ["OnlyVeda Active 365 Daily Essential", "OnlyVeda Daily Complete Multivitamin"],
            "ayurveda": ["OnlyVeda KSM-66 Ashwagandha Pure Tablet", "OnlyVeda Triphala Satwik Pure Digestive Detox", "OnlyVeda Active 365 Daily Essential"],
            "general": ["OnlyVeda Active 365 Daily Essential", "OnlyVeda Daily Complete Multivitamin"]
        }

        target_names = prod_map.get(topic or "general", prod_map["general"])
        matched = []
        all_prods = self.data_manager.get_all_products()

        # Preset default clinical doses for formulations
        preset_doses = {
            "OnlyVeda Linopress": "1-0-1 (1 Morning, 1 Night)",
            "OnlyVeda L-Arginine Plus": "1-0-0 (1 Morning)",
            "OnlyVeda Terminalia Arjuna Extract": "1-0-1 (1 Morning, 1 Night)",
            "OnlyVeda Strenus Pain Relief Capsules": "1-0-1 (1 Morning, 1 Night)",
            "OnlyVeda Strenus Herbal Massage Oil": "Apply / Use 2-3 times daily",
            "OnlyVeda Serronil Joint Care": "1-1-1 (1 Morning, 1 Afternoon, 1 Night)",
            "OnlyVeda Calcimus Coral Calcium Complex": "0-1-0 (Afternoon)",
            "OnlyVeda Wal D3 Sublingual Spray": "4 spray in a day",
            "OnlyVeda Active 365 Daily Essential": "1-0-1",
            "OnlyVeda Ashyuka Plus Syrup": "20 ml twice daily",
            "OnlyVeda Immuferin Immuno-Shield": "2-2-2 (2 Morning, 2 Afternoon, 2 Night)",
            "OnlyVeda Respitone Pulmonary Shield": "1-1-1",
            "OnlyVeda N-Acetyl Cysteine (NAC 600mg)": "1-0-1",
            "OnlyVeda Triphala Satwik Pure Digestive Detox": "0-0-1 (Night with warm water)",
            "OnlyVeda Laxia Gentle Overnight Colon Cleanse": "0-0-1 (Night with warm water)",
            "OnlyVeda Rhiza Mucosal Gut Shield": "1-0-1",
            "OnlyVeda Avipattikar Pitta-Balance Tablet": "1-0-1",
            "OnlyVeda Milk Thistle Silymarin Detox": "1-0-0",
            "OnlyVeda Liver Detox Formula": "1-0-1",
            "OnlyVeda Daily Complete Multivitamin": "1-0-0",
            "OnlyVeda Natural Vitamin C + Zinc": "1-0-1",
            "OnlyVeda KSM-66 Ashwagandha Pure Tablet": "1-0-1",
            "OnlyVeda Xemma Anti-Acne & Blemish Cream": "Apply / Use 2-3 times daily",
            "OnlyVeda Clarifying Anti-Acne Face Wash": "Apply / Use 2-3 times daily",
            "OnlyVeda Throatwal Soothing Lozenges & Gargle": "1-0-1",
            "OnlyVeda Prowal Synbiotic Gut Restorer": "1-0-1",
            "OnlyVeda Hadjod Bone Healer": "1-0-1",
            "OnlyVeda Calciumus Forte": "1-0-1",
            "OnlyVeda Kanchanar Guggul Traditional": "1-0-1",
            "OnlyVeda Hepatreat Hepatic Care": "1-0-1",
            "OnlyVeda Hepatreat Hepatic Tablets": "1-0-1"
        }

        for t in target_names:
            for p in all_prods:
                if p.get("name") == t:
                    prod_copy = dict(p)
                    if t in preset_doses:
                        prod_copy["prescribed_dose"] = preset_doses[t]
                    elif "prescribed_dose" not in prod_copy:
                        raw_dose = prod_copy.get("dosage_and_usage", "1-0-1")
                        if " | " in raw_dose:
                            first_part = raw_dose.split(" | ")[0]
                            if ":" in first_part:
                                first_part = first_part.split(":", 1)[1].strip()
                            prod_copy["prescribed_dose"] = first_part
                        else:
                            prod_copy["prescribed_dose"] = raw_dose
                    matched.append(prod_copy)
                    break
        return matched

    def _format_product_recommendation_section(
        self,
        products: List[Dict[str, Any]],
        lang: str,
        is_prescription: bool = False
    ) -> str:
        """Format an accurate, localized OnlyVeda product recommendation section with doses, herbs, and benefits."""
        if not products:
            return ""

        headings = {
            "section_title": {
                "en": "Recommended OnlyVeda Products for You",
                "hi": "आपके लिए OnlyVeda के अनुशंसित उत्पाद",
                "gu": "તમારા માટે OnlyVeda ની ભલામણ કરેલ પ્રોડક્ટ્સ",
                "mr": "तुमच्यासाठी OnlyVeda ची शिफारस केलेली उत्पादने",
                "bn": "আপনার জন্য OnlyVeda-র প্রস্তাবিত পণ্য",
                "te": "మీ కోసం OnlyVeda సూచించిన ఉత్పత్తులు",
                "ta": "உங்களுக்கான OnlyVeda பரிந்துரைக்கப்பட்ட தயாரிப்புகள்",
                "kn": "ನಿಮಗಾಗಿ OnlyVeda ಶಿಫಾರಸು ಮಾಡಿದ ಉತ್ಪನ್ನಗಳು",
                "or": "ଆପଣଙ୍କ ପାଇଁ OnlyVeda ର ପରାମର୍ଶିତ ଉତ୍ପାଦ",
                "ml": "നിങ്ങൾക്കായി OnlyVeda ശുപാർശ ചെയ്യുന്ന ഉൽപ്പന്നങ്ങൾ",
                "ur": "آپ کے لیے تجویز کردہ OnlyVeda مصنوعات"
            },
            "dose": {
                "en": "Prescribed Dose", "hi": "निर्धारित खुराक (Dose)", "gu": "નિયત માત્રા (Dose)",
                "mr": "ठरवून दिलेली मात्रा (Dose)", "bn": "নির্দিষ্ট সেবন মাত্রা (Dose)", "te": "సూచించిన మోతాదు (Dose)",
                "ta": "பரிந்துரைக்கப்பட்ட அளவு (Dose)", "kn": "ನಿಗದಿತ ಪ್ರಮಾಣ (Dose)", "or": "ନିର୍ଦ୍ଧାରିତ ମାତ୍ରା (Dose)",
                "ml": "നിർദ്ദേശിച്ച അളവ് (Dose)", "ur": "تجویز کردہ خوراک (Dose)"
            },
            "herbs": {
                "en": "Key Active Herbs", "hi": "मुख्य घटक (Key Herbs)", "gu": "મુખ્ય ઘટકો",
                "mr": "मुख्य आयुर्वेदिक घटक", "bn": "প্রধান উপাদান", "te": "ముఖ్య మూలికలు",
                "ta": "முக்கிய மூலிகைகள்", "kn": "ಮುಖ್ಯ ಗಿಡಮೂಲಿಕೆಗಳು", "or": "ମୁଖ୍ୟ ଉପାଦାନ",
                "ml": "പ്രധാന ചേരുവകൾ", "ur": "اہم اجزاء"
            },
            "benefits": {
                "en": "Action & Health Benefits", "hi": "स्वास्थ्य लाभ व प्रभाव", "gu": "આરોગ્ય લાભો",
                "mr": "आरोग्य फायदे", "bn": "স্বাস্থ্য উপকারিতা", "te": "ఆరోగ్య ప్రయోజనాలు",
                "ta": "ஆரோக்கிய நன்மைகள்", "kn": "ಆರೋಗ್ಯ ಪ್ರಯೋಜನಗಳು", "or": "ସ୍ୱାସ୍ଥ୍ୟ ଲାଭ",
                "ml": "ആരോഗ്യ ഗുണങ്ങൾ", "ur": "طبی فوائد"
            }
        }

        h_title = headings["section_title"].get(lang, headings["section_title"]["en"])
        h_dose = headings["dose"].get(lang, headings["dose"]["en"])
        h_herbs = headings["herbs"].get(lang, headings["herbs"]["en"])
        h_ben = headings["benefits"].get(lang, headings["benefits"]["en"])

        lines = [f"### 🌿 {h_title}:", ""]
        for idx, prod in enumerate(products, 1):
            name = prod.get("name", "")
            price = prod.get("price_inr", "499")
            size = prod.get("size", "")
            dose = prod.get("prescribed_dose", prod.get("dosage_and_usage", "1-0-1"))
            ings = ", ".join(prod.get("key_ingredients", []))
            ben = prod.get("benefits", "")

            price_tag = f" (₹{price} • {size})" if size else f" (₹{price})"
            lines.append(f"#### {idx}. **{name}**{price_tag}")
            lines.append(f"- **📋 {h_dose}:** `{dose}`")
            if ings:
                lines.append(f"- **🌿 {h_herbs}:** {ings}")
            if ben:
                lines.append(f"- **✨ {h_ben}:** {ben}")
            lines.append("")

        return "\n".join(lines)

    def decide_product_suggestion(
        self,
        clean_msg: str,
        lang: str,
        session_ctx: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Intelligently analyzes the user prompt to decide whether a product suggestion is warranted:
        - CATEGORY A: DO NOT SUGGEST (Greetings, identity, gratitude, farewell, non-health questions).
        - CATEGORY B: SUGGEST ACCURATELY (Disease symptoms, educational health topics, wellness goals, product inquiries, follow-ups).
        """
        cleaned = clean_msg.strip().lower()
        if not cleaned:
            return {
                "should_suggest": False,
                "intent": "greeting",
                "topic": None,
                "disease_protocol": None,
                "products": []
            }

        conversational_intent = self.detect_conversational_intent(clean_msg)
        health_topic = self.detect_health_topic(clean_msg)
        rec_result = self.recommender.recommend(clean_msg, top_k=4)
        disease_protocol = rec_result.get("disease_protocol")

        # 1. Check for non-health off-topic queries FIRST
        if self.is_non_health_query(clean_msg):
            return {
                "should_suggest": False,
                "intent": "non_health",
                "topic": None,
                "disease_protocol": None,
                "products": []
            }

        conversational_intent = self.detect_conversational_intent(clean_msg)
        health_topic = self.detect_health_topic(clean_msg)

        # 2. Check for pure conversational intent (greetings, identity, gratitude, farewell, help)
        if conversational_intent:
            has_treatment_request = any(re.search(top, cleaned) for top in TREATMENT_OVERRIDE_PATTERNS)
            if not health_topic or (len(clean_msg.split()) <= 8 and not has_treatment_request):
                return {
                    "should_suggest": False,
                    "intent": conversational_intent,
                    "topic": None,
                    "disease_protocol": None,
                    "products": []
                }

        # 3. Check for multi-turn follow-up referencing prior consultation
        last_prods = session_ctx.get("last_products", [])
        last_dis = session_ctx.get("last_disease")
        followup_patterns = [
            r'\b(?:milk|दूध|દૂધ|పాలు|பால்|ಹಾಲು|দুধ|ଦୁଗ୍ଧ|دودھ|പാൽ)\b',
            r'(?:side\s*effect|आडअसर|આડઅસર|साइड\s*इफेक्ट|नुकसान|సైడ్\s*ఎఫెక్ట్|பக்க\s*விளைவு|ಸೈಡ್\s*ಎಫೆಕ್ಟ್|పార్శ్వప్రतिक୍ରિયા|نقصان)',
            r'\b(?:how\s+long|how\s+many\s+days|how\s+many\s+months|कितने\s+दिन|કેટલા\s+દિવસ|ఎన్ని\s+రోజులు|எத்தனை\s+நாட்கள்|ಎಷ್ಟು\s+ದಿನ|কত\s+দিন|କେତେ\s+ଦିନ|کتنے\s+دن)\b',
            r'\b(?:how\s+to\s+take|when\s+to\s+take|before\s+food|after\s+food|empty\s+stomach|कब्\s+लें|कैसे\s+लें|जम્યા\s+પહેલા)\b'
        ]
        is_followup_match = any(re.search(fp, cleaned) for fp in followup_patterns)
        if is_followup_match and last_prods and not health_topic:
            return {
                "should_suggest": True,
                "intent": "followup",
                "topic": last_dis,
                "disease_protocol": {"disease": last_dis} if last_dis else None,
                "products": last_prods
            }

        # 4. Check for Educational Inquiry (e.g. 'what is pain', 'which are heart dieses', 'what is diabetes')
        # Educational = JUST explain, NO product suggestion. User must share personal symptoms to get products.
        is_edu, edu_topic = self.detect_educational_intent(clean_msg)
        if is_edu and edu_topic:
            return {
                "should_suggest": False,
                "intent": "educational",
                "topic": edu_topic,
                "disease_protocol": None,
                "products": []
            }


        # 5. Check for exact Disease Protocol from diseases_wise_1.csv
        rec_result = self.recommender.recommend(clean_msg, top_k=4)
        disease_protocol = rec_result.get("disease_protocol")
        if disease_protocol and rec_result.get("products"):
            return {
                "should_suggest": True,
                "intent": "disease_protocol",
                "topic": disease_protocol.get("disease"),
                "disease_protocol": disease_protocol,
                "products": rec_result.get("products", [])
            }

        # 6. Check for Wellness Goal (e.g. 'how to reduce stress', 'tips for sleep', 'how to stop hair fall')
        is_wellness, wellness_topic = self.detect_wellness_intent(clean_msg)
        if is_wellness and (wellness_topic or health_topic):
            topic = wellness_topic or health_topic
            supportive_prods = self._get_supportive_products_for_topic(topic)
            return {
                "should_suggest": True,
                "intent": "wellness_goal",
                "topic": topic,
                "disease_protocol": None,
                "products": supportive_prods
            }

        # 7. Check for general health topic or symptom detected
        if health_topic:
            supportive_prods = self._get_supportive_products_for_topic(health_topic)
            return {
                "should_suggest": True,
                "intent": "health_inquiry",
                "topic": health_topic,
                "disease_protocol": None,
                "products": supportive_prods
            }

        # 8. Check if recommender found high-confidence products (direct product name inquiry)
        if rec_result.get("products"):
            top_prod = rec_result.get("products")[0]
            top_name_lower = top_prod.get("name", "").lower()
            if any(term in cleaned for term in ["onlyveda", "tablet", "syrup", "capsule", "powder", "cream", "lotion", "oil"]) or top_name_lower in cleaned:
                return {
                    "should_suggest": True,
                    "intent": "product_inquiry",
                    "topic": "catalog_match",
                    "disease_protocol": None,
                    "products": rec_result.get("products")
                }

        # 9. Fallback: No health symptoms, no educational concept, no product match
        return {
            "should_suggest": False,
            "intent": "non_health",
            "topic": None,
            "disease_protocol": None,
            "products": []
        }


    def _generate_educational_offline_response(self, query: str, lang: str, topic: Optional[str]) -> str:
        """Fallback rich educational response when offline or API quota is exhausted."""
        lang_cfg = SUPPORTED_LANGUAGES.get(lang, SUPPORTED_LANGUAGES["en"])
        topic_knowledge = OFFLINE_EDUCATIONAL_KNOWLEDGE.get(topic or "general", OFFLINE_EDUCATIONAL_KNOWLEDGE["general"])
        content = topic_knowledge.get(lang, topic_knowledge.get("en", topic_knowledge.get("hi", "")))
        if not content:
            content = OFFLINE_EDUCATIONAL_KNOWLEDGE["general"].get(lang, OFFLINE_EDUCATIONAL_KNOWLEDGE["general"]["en"])
        return f"{content}\n\n---\n{lang_cfg['disclaimer']}"

    def _generate_localized_template_response(
        self,
        user_query: str,
        products: List[Dict[str, Any]],
        lang: str,
        disease_protocol: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Built-in fallback generator providing authentic, fluent Indic responses
        strictly recommending OnlyVeda formulary products with exact doses from diseases_wise_1.csv.
        """
        lang_cfg = SUPPORTED_LANGUAGES.get(lang, SUPPORTED_LANGUAGES["en"])
        disclaimer = lang_cfg["disclaimer"]

        if not products:
            return f"{lang_cfg['no_product_found']}\n\n{disclaimer}"

        headings = {
            "dose": {
                "en": "Prescribed Dose", "hi": "निर्धारित खुराक (Dose)", "bn": "নির্দিষ্ট সেবন মাত্রা (Dose)", "mr": "ठरवून दिलेली मात्रा (Dose)",
                "te": "సూచించిన మోతాదు (Dose)", "ta": "பரிந்துரைக்கப்பட்ட அளவு (Dose)", "gu": "નિયત માત્રા (Dose)",
                "ur": "تجویز کردہ خوراک (Dose)", "kn": "ನಿಗದಿತ ಪ್ರಮಾಣ (Dose)", "or": "ନିର୍ଦ୍ଧାରିତ ମାତ୍ରା (Dose)", "ml": "നിർദ്ദേശിച്ച അളവ് (Dose)"
            },
            "ingredients": {
                "en": "Key Active Herbs", "hi": "मुख्य घटक (Key Herbs)", "bn": "প্রধান উপাদান", "mr": "मुख्य आयुर्वेदिक घटक",
                "te": "ముఖ్య మూలికలు", "ta": "முக்கிய மூலிகைகள்", "gu": "મુખ્ય આયુર્વેદિક ઘટકો",
                "ur": "اہم اجزاء", "kn": "ಮುಖ್ಯ ಗಿಡಮೂಲಿಕೆಗಳು", "or": "ମୁଖ୍ୟ ଉପାଦାନ", "ml": "പ്രധാന ചേരുവകൾ"
            },
            "benefits": {
                "en": "Action & Health Benefits", "hi": "स्वास्थ्य लाभ व प्रभाव", "bn": "স্বাস্থ্য উপকারিতা", "mr": "आरोग्य फायदे",
                "te": "ఆరోగ్య ప్రయోజనాలు", "ta": "ஆரோக்கிய நன்மைகள்", "gu": "આરોગ્ય લાભો",
                "ur": "طبی فوائد", "kn": "ಆರೋಗ್ಯ ಪ್ರಯೋಜನಗಳು", "or": "ସ୍ୱାସ୍ଥ୍ୟ ଲାଭ", "ml": "ആരോഗ്യ ഗുണങ്ങൾ"
            },
            "protocol_intro": {
                "en": "Based on our clinical formulary for",
                "hi": "OnlyVeda के प्रमाणित उपचार चार्ट के अनुसार,",
                "bn": "OnlyVeda-র নির্ধারিত চিকিৎসা নির্দেশিকা অনুযায়ী,",
                "mr": "OnlyVeda च्या अधिकृत वैद्यकीय फॉर्म्युलरीनुसार,",
                "te": "OnlyVeda అధికారిక చికిత్సా విధానం ప్రకారం,",
                "ta": "OnlyVeda-வின் அங்கீகரிக்கப்பட்ட மருத்துவ வழிகாட்டுதலின்படி,",
                "gu": "OnlyVeda ના પ્રમાણિત સારવાર ચાર્ટ મુજબ,",
                "ur": "OnlyVeda کے مصدقہ فارمولری چارٹ کے مطابق،",
                "kn": "OnlyVeda ನ ಅಧಿಕೃತ ಚಿಕಿತ್ಸಾ ಪದ್ಧತಿಯ ಪ್ರಕಾರ,",
                "or": "OnlyVeda ର ପ୍ରମାଣିତ ଚିକିତ୍ସା ନିର୍ଦ୍ଦେଶିକା ଅନୁସାରେ,",
                "ml": "OnlyVeda-യുടെ ഔദ്യോഗിക ചികിത്സാ നിർദ്ദേശപ്രകാരം,"
            },
            "protocol_subtitle": {
                "en": "here is the exact OnlyVeda supplement protocol:",
                "hi": "यहाँ OnlyVeda का सटीक सप्लीमेंट संयोजन और खुराक दी गई है:",
                "bn": "এখানে OnlyVeda-র সুনির্দিষ্ট পরিপূরক ও সেবনমাত্রা দেওয়া হলো:",
                "mr": "खालीलप्रमाणे OnlyVeda सप्लिमेंट्स व त्यांची अचूक मात्रा घ्यावी:",
                "te": "క్రింది OnlyVeda సప్లిమెంట్లు మరియు వాటి మోతాదును సూచించడమైనది:",
                "ta": "கீழ்க்கண்ட OnlyVeda தயாரிப்புகள் மற்றும் அவற்றின் சரியான அளவுகள்:",
                "gu": "નીચે દર્શાવેલ OnlyVeda પ્રોડક્ટ્સ અને તેમની યોગ્ય માત્રા લેવી:",
                "ur": "مندرجہ ذیل OnlyVeda سپلیمنٹس اور ان کی درست خوراک تجویز کی جاتی ہے:",
                "kn": "ಕೆಳಗಿನ OnlyVeda ಉತ್ಪನ್ನಗಳು ಮತ್ತು ಅವುಗಳ ನಿಖರ ಪ್ರಮಾಣವನ್ನು ತೆಗೆದುಕೊಳ್ಳಿ:",
                "or": "ନିମ୍ନଲିଖିତ OnlyVeda ଉତ୍ପାଦ ଏବଂ ତାର ସଠିକ୍ ମାତ୍ରା ସେବନ କରନ୍ତୁ:",
                "ml": "താഴെ പറയുന്ന OnlyVeda ഉൽപ്പന്നങ്ങളും അവയുടെ കൃത്യമായ അളവും പാലിക്കുക:"
            }
        }

        h_dose = headings["dose"].get(lang, headings["dose"]["en"])
        h_ing = headings["ingredients"].get(lang, headings["ingredients"]["en"])
        h_ben = headings["benefits"].get(lang, headings["benefits"]["en"])
        h_intro = headings["protocol_intro"].get(lang, headings["protocol_intro"]["en"])
        h_sub = headings["protocol_subtitle"].get(lang, headings["protocol_subtitle"]["en"])

        response_lines = []

        if disease_protocol:
            dis_key = disease_protocol.get("disease", "")
            localized_dis = disease_protocol.get("localized_names", {}).get(lang, dis_key)
            response_lines.append(f"### 🌿 {h_intro} **{localized_dis}**, {h_sub}")
            response_lines.append("")
        else:
            intros = {
                "en": "Based on your health inquiry, here are the recommended OnlyVeda supplements:",
                "hi": "आपकी स्वास्थ्य समस्या को देखते हुए, OnlyVeda के निम्नलिखित उत्पाद अनुशंसित हैं:",
                "bn": "আপনার স্বাস্থ্য সমস্যার জন্য OnlyVeda-র নিম্নলিখিত পণ্যগুলি অত্যন্ত কার্যকরী:",
                "mr": "तुमच्या आरोग्य समस्येसाठी OnlyVeda ची खालील उत्पादने अत्यंत प्रभावी आहेत:",
                "te": "మీ ఆరోగ్య సమస్యను దృష్టిలో ఉంచుకుని OnlyVeda సూచించే ఉత్పత్తులు ఇవి:",
                "ta": "உங்கள் ஆரோக்கிய நலனுக்காக OnlyVeda பரிந்துரைக்கும் தயாரிப்புகள்:",
                "gu": "તમારી સ્વાસ્થ્ય સમસ્યા માટે OnlyVeda ની નીચેની પ્રોડક્ટ્સ ભલામણ કરવામાં આવે છે:",
                "ur": "آپ کی صحت کے مسئلے کے پیش نظر OnlyVeda کی مندرجہ ذیل مصنوعات تجویز کی جاتی ہیں:",
                "kn": "ನಿಮ್ಮ ಆರೋಗ್ಯ ಸಮಸ್ಯೆಗಾಗಿ OnlyVeda ಶಿಫಾರಸು ಮಾಡುವ ಉತ್ಪನ್ನಗಳು:",
                "or": "ଆପଣଙ୍କ ସ୍ୱାସ୍ଥ୍ୟ ସମସ୍ୟା ପାଇଁ OnlyVeda ର ନିମ୍ନଲିଖିତ ଉତ୍ପାଦ ଉପଯୁକ୍ତ:",
                "ml": "നിങ്ങളുടെ ആരോഗ്യ പ്രശ്നത്തിന് OnlyVeda ശുപാർശ ചെയ്യുന്ന ഉൽപ്പന്നങ്ങൾ:"
            }
            response_lines.append(f"### 🌿 {intros.get(lang, intros['en'])}")
            response_lines.append("")

        for idx, prod in enumerate(products, 1):
            ing_str = ", ".join(prod.get("key_ingredients", []))
            prescribed = prod.get("prescribed_dose", prod.get("dosage_and_usage", "1-0-1"))
            price = prod.get("price_inr", "N/A")
            size = prod.get("size", "")

            response_lines.append(f"#### {idx}. **{prod.get('name')}** (₹{price} • {size})")
            response_lines.append(f"- **📋 {h_dose}:** `{prescribed}`")
            response_lines.append(f"- **🌿 {h_ing}:** {ing_str}")
            response_lines.append(f"- **✨ {h_ben}:** {prod.get('benefits', '')}")
            response_lines.append("")

        response_lines.append("---")
        response_lines.append(disclaimer)

        return "\n".join(response_lines)

    def chat(self, user_message: str, selected_lang: Optional[str] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process user query with full persistent multi-turn conversational memory:
        1. Manages persistent SQLite sessions and loads conversation history.
        2. Intelligently decides from user prompt whether to suggest a product or not.
        3. For educational/conceptual questions, explains thoroughly first, and AFTER THIS suggests accurate products.
        4. Matches exact disease protocols from diseases_wise_1.csv.
        5. Saves user and assistant turns to memory.
        """
        clean_msg = user_message.strip()
        session_id = self.memory.get_or_create_session(session_id)
        session_ctx = self.memory.get_session_context(session_id)
        history = self.memory.get_history(session_id, limit=8)

        # Determine language (either user selected or auto-detected)
        detected_lang = self.detect_language(clean_msg)
        if not selected_lang or selected_lang == "auto":
            lang = detected_lang
        elif selected_lang == "en" and detected_lang != "en":
            lang = detected_lang
        else:
            lang = selected_lang

        lang_cfg = SUPPORTED_LANGUAGES.get(lang, SUPPORTED_LANGUAGES["en"])

        # Central Decision Engine
        decision = self.decide_product_suggestion(clean_msg, lang, session_ctx)
        should_suggest = decision["should_suggest"]
        intent = decision["intent"]
        topic = decision["topic"]
        # Deduplicate products by name (keep first occurrence)
        seen_names = set()
        deduped = []
        for p in decision["products"]:
            pname = p.get("name", "")
            if pname not in seen_names:
                seen_names.add(pname)
                deduped.append(p)
        suggested_products = deduped
        disease_protocol = decision["disease_protocol"]



        # 1. CATEGORY: DO NOT SUGGEST PRODUCT (Greetings, Identity, Gratitude, Farewell, Non-Health, Educational)
        if not should_suggest:
            if intent == "educational":
                # Short, crisp educational answer — NO products
                reply = ""
                if self.api_key:
                    edu_prompt = SYSTEM_PROMPT_NUTRACEUTICAL_EXPLANATION.format(
                        language_name=lang_cfg['name'],
                        native_name=lang_cfg['native_name'],
                        clean_msg=clean_msg,
                        catalog_context=""
                    )
                    reply = self._call_gemini_api(edu_prompt, lang, conversation_history=history) or ""
                if not reply:

                    # Offline fallback: pull just first 2 sentences from offline knowledge
                    topic_knowledge = OFFLINE_EDUCATIONAL_KNOWLEDGE.get(topic or "general", OFFLINE_EDUCATIONAL_KNOWLEDGE.get("general", {}))
                    full_text = topic_knowledge.get(lang, topic_knowledge.get("en", ""))
                    if full_text:
                        # Extract just the first plain paragraph (before any heading/bullet)
                        plain_lines = [l.strip() for l in full_text.split("\n") if l.strip() and not l.strip().startswith("#") and not l.strip().startswith("-") and not l.strip().startswith("*") and not l.strip().startswith("####")]
                        short_answer = " ".join(plain_lines[:2]) if plain_lines else full_text[:300]
                    else:
                        short_answer = lang_cfg["greeting"]
                    # Add invite to share personal symptoms
                    invite = {
                        "en": "\n\nIf you are personally experiencing this condition and want OnlyVeda product recommendations, please share your symptoms!",
                        "hi": "\n\nयदि आप स्वयं इस समस्या से पीड़ित हैं और OnlyVeda उत्पाद जानना चाहते हैं, तो कृपया अपने लक्षण बताएं!",
                        "gu": "\n\nજો તમે આ સ્થિતિથી પ્રભાવિત છો અને OnlyVeda ઉત્પાદો જાણવા ઇચ્છો છો, તો કૃપા કરીને તમારા લક્ષણો જણાવો!",
                        "mr": "\n\nजर तुम्हाला स्वतःला ही समस्या आहे आणि OnlyVeda उत्पादने जाणून घ्यायची असतील, तर कृपया तुमची लक्षणे सांगा!",
                        "bn": "\n\nআপনি যদি নিজে এই সমস্যায় ভুগছেন এবং OnlyVeda পণ্যের পরামর্শ চান, তাহলে দয়া করে আপনার উপসর্গ জানান!",
                        "te": "\n\nమీరు స్వయంగా ఈ సమస్యతో బాధపడుతుంటే మరియు OnlyVeda ఉత్పత్తులు తెలుసుకోవాలంటే, దయచేసి మీ లక్షణాలు చెప్పండి!",
                        "ta": "\n\nநீங்கள் தனிப்பட்ட முறையில் இந்த நிலையை அனுபவிக்கிறீர்களா? OnlyVeda தயாரிப்புகள் பெற உங்கள் அறிகுறிகளை பகிர்ந்துகொள்ளுங்கள்!",
                        "kn": "\n\nನೀವು ಈ ಸಮಸ್ಯೆಯಿಂದ ಬಳಲುತ್ತಿದ್ದರೆ ಮತ್ತು OnlyVeda ಉತ್ಪನ್ನಗಳ ಬಗ್ಗೆ ತಿಳಿಯಲು ಬಯಸಿದರೆ, ದಯವಿಟ್ಟು ನಿಮ್ಮ ರೋಗಲಕ್ಷಣಗಳನ್ನು ಹೇಳಿ!",
                        "or": "\n\nଯଦି ଆପଣ ଏହି ସମସ୍ୟାରେ ପୀଡ଼ିତ ଏବଂ OnlyVeda ଉତ୍ପାଦ ଜାଣିବାକୁ ଚାହୁଁଛନ୍ତି, ଆପଣଙ୍କ ଲକ୍ଷଣ ଜଣାନ୍ତୁ!",
                        "ml": "\n\nനിങ്ങൾ ഈ അവസ്ഥ അനുഭവിക്കുന്നുണ്ടെങ്കിൽ, OnlyVeda ഉൽപ്പന്ന ശുപാർശകൾക്ക് നിങ്ങളുടെ ലക്ഷണങ്ങൾ പങ്കിടൂ!",
                        "ur": "\n\nاگر آپ خود اس مسئلے سے پریشان ہیں اور OnlyVeda مصنوعات جاننا چاہتے ہیں، تو اپنی علامات بتائیں!"
                    }
                    reply = short_answer + invite.get(lang, invite["en"])
                if not reply:
                    reply = lang_cfg["greeting"]
            elif intent in CONVERSATIONAL_RESPONSES:
                intent_responses = CONVERSATIONAL_RESPONSES.get(intent, {})
                reply = intent_responses.get(lang, intent_responses.get("en", lang_cfg["greeting"]))
            elif intent == "non_health":
                non_health_replies = {
                    "en": "Namaste! 🙏 I am your **OnlyVeda Ayurvedic & Nutraceutical Wellness Assistant**.\n\nI specialize in natural herbal medicine, Ayurvedic principles, and our clinical wellness formulations (such as solutions for Blood Pressure, Joint Pain, Acidity, Immunity, Diabetes support, and Skin Care).\n\nI am unable to assist with non-health topics. Please feel free to ask me any health or wellness question!",
                    "hi": "नमस्ते! 🙏 मैं आपका **OnlyVeda आयुर्वेदिक और न्यूट्रास्युटिकल सलाहकार** हूँ।\n\nमेरी विशेषज्ञता प्राकृतिक जड़ी-बूटियों, आयुर्वेद और स्वास्थ्य सप्लीमेंट्स (जैसे ब्लड प्रेशर, जोड़ों का दर्द, गैस-एसिडिटी, इम्युनिटी, त्वचा आदि) में है।\n\nमैं गैर-स्वास्थ्य विषयों पर जानकारी देने में असमर्थ हूँ। कृपया बेझिझक अपने स्वास्थ्य से संबंधित कोई भी प्रश्न पूछें!",
                    "gu": "નમસ્તે! 🙏 હું તમારો **OnlyVeda આયુર્વેદિક અને ન્યુટ્રાસ્યુટિકલ સહાયક** છું.\n\nહું કુદરતી આયુર્વેદિક ઉપચારો અને સ્વાસ્થ્ય પ્રોડક્ટ્સ (જેમ કે હાઈ બીપી, સાંધાનો દુખાવો, એસિડિટી, રોગપ્રતિકારક શક્તિ, ત્વચા સંભાળ વગેરે) માટે મદદ કરું છું.\n\nહું બિન-આરોગ્ય વિષયો પર માહિતી આપી શકતો નથી. કૃપા કરીને તમારા સ્વાસ્થ્ય સંબંધી કોઈપણ પ્રશ્ન પૂછો!",
                    "mr": "नमस्कार! 🙏 मी आपला **OnlyVeda आयुर्वेदिक आणि न्यूट्रास्युटिकल वेलनेस असिस्टंट** आहे.\n\nमी आरोग्य, आजार आणि नैसर्गिक सप्लिमेंट्सबद्दल मार्गदर्शन करतो. कृपया आपल्या आरोग्याशी संबंधित प्रश्न विचारा!",
                    "bn": "নমস্কার! 🙏 আমি আপনার **OnlyVeda আয়ুর্বেদিক ও নিউট্রাসিউটিক্যাল স্বাস্থ্য সহকারী**।\n\nআমি কেবল স্বাস্থ্য ও ভেষজ চিকিৎসা সংক্রান্ত বিষয়ে সহায়তা করি। অনুগ্রহ করে আপনার স্বাস্থ্য সমস্যা সম্পর্কে জানান!",
                    "te": "నమస్కారం! 🙏 నేను మీ **OnlyVeda ఆయుర్వేద & న్యూట్రాస్యూటికల్ వెల్నెస్ అసిస్టెంట్**.\n\nనేను ఆరోగ్య సమస్యలు మరియు మూలికా ఉత్పత్తుల గురించి మాత్రమే మార్గదర్శనం చేస్తాను.",
                    "ta": "வணக்கம்! 🙏 நான் உங்கள் **OnlyVeda ஆயுர்வேத மற்றும் நல்வாழ்வு உதவியாளர்**.\n\nநான் உடல்நலம் மற்றும் மூலிகை தயாரிப்புகள் பற்றிய தகவல்களை மட்டுமே வழங்குகிறேன்.",
                    "kn": "ನಮಸ್ಕಾರ! 🙏 ನಾನು ನಿಮ್ಮ **OnlyVeda ಆಯುರ್ವೇದ ಆರೋಗ್ಯ ಸಹಾಯಕ**.\n\nನಾನು ಕೇವಲ ಆರೋಗ್ಯ ಮತ್ತು ಆಯುರ್ವೇದ ಉತ್ಪನ್ನಗಳ ಬಗ್ಗೆ ಮಾರ್ಗದರ್ಶನ ನೀಡುತ್ತೇನೆ.",
                    "or": "ନମସ୍କାର! 🙏 ମୁଁ ଆପଣଙ୍କ **OnlyVeda ଆୟୁର୍ବେଦିକ ସ୍ୱାସ୍ଥ୍ୟ ସହାୟକ**।\n\nମୁଁ କେବଳ ସ୍ୱାସ୍ଥ୍ୟ ଏବଂ ଆୟୁର୍ବେଦିକ ଉତ୍ପାଦ ବିଷୟରେ ପରାମର୍ଶ ଦେଇଥାଏ।",
                    "ml": "നമസ്കാരം! 🙏 ഞാൻ നിങ്ങളുടെ **OnlyVeda ആയുർവേദ വെൽനസ് അസിസ്റ്റന്റാണ്**.\n\nഞാൻ ആരോഗ്യ കാര്യങ്ങളിൽ മാത്രമേ സഹായിക്കുകയുള്ളൂ.",
                    "ur": "السلام علیکم! 🙏 میں آپ کا **OnlyVeda آیورویدک ہیلتھ اسسٹنٹ** ہوں۔\n\nمیں صرف صحت اور قدرتی سپلیمنٹس سے متعلق رہنمائی فراہم کرتا ہوں۔"
                }
                reply = non_health_replies.get(lang, non_health_replies["en"]) + f"\n\n---\n{lang_cfg['disclaimer']}"
            else:
                reply = lang_cfg["greeting"]



            self.memory.add_message(session_id=session_id, role="user", content=clean_msg, language=lang)
            self.memory.add_message(session_id=session_id, role="assistant", content=reply, language=lang)
            return {
                "session_id": session_id,
                "response": reply,
                "language": lang,
                "language_name": lang_cfg["name"],
                "products": [],
                "disease_protocol": None,
                "suggestions": [],
                "has_api_key": bool(self.api_key)
            }

        # 2. CATEGORY: SUGGEST PRODUCT ACCURATELY
        generated_text = None

        # Build catalog summary for LLM context
        catalog_summary = []
        for p in suggested_products:
            catalog_summary.append(
                f"- Product: {p.get('name')}\n"
                f"  Prescribed Dose: {p.get('prescribed_dose')}\n"
                f"  Ingredients: {', '.join(p.get('key_ingredients', []))}\n"
                f"  Benefits: {p.get('benefits')}\n"
                f"  Category: {p.get('category')}\n"
                f"  Price: INR {p.get('price_inr', 499)} ({p.get('size', 'Standard Pack')})"
            )
        catalog_context_str = "\n\n".join(catalog_summary) if catalog_summary else "OnlyVeda standardized herbal extracts and clinical nutraceuticals."

        if self.api_key:
            if intent == "educational":
                prompt = SYSTEM_PROMPT_NUTRACEUTICAL_EXPLANATION.format(
                    language_name=lang_cfg['name'],
                    native_name=lang_cfg['native_name'],
                    clean_msg=clean_msg,
                    catalog_context=catalog_context_str
                )
                generated_text = self._call_gemini_api(prompt, lang, conversation_history=history)
            elif intent == "disease_protocol":
                dis_name = disease_protocol.get("disease", "Clinical Condition") if disease_protocol else "Clinical Condition"
                prompt = (
                    f"{SYSTEM_PROMPT_INDIC_TEMPLATE.format(language_name=lang_cfg['name'], native_name=lang_cfg['native_name'], catalog_context=catalog_context_str)}\n\n"
                    f"Target Condition: {dis_name}\n"
                    f"STRICT INSTRUCTION: Recommend ONLY the OnlyVeda products listed above with their exact prescribed doses. Explain why these products help, how to take them, and relevant Ayurvedic dietary tips.\n\n"
                    f"User ({lang_cfg['name']}): \"{clean_msg}\"\n\n"
                    f"Please reply in {lang_cfg['name']} ({lang_cfg['native_name']}) now:"
                )
                generated_text = self._call_gemini_api(prompt, lang, conversation_history=history)
            elif intent == "followup":
                dis_name = topic or "Prior Condition"
                prompt = (
                    f"{SYSTEM_PROMPT_INDIC_TEMPLATE.format(language_name=lang_cfg['name'], native_name=lang_cfg['native_name'], catalog_context=catalog_context_str)}\n\n"
                    f"Previously prescribed condition: {dis_name}\n"
                    f"STRICT INSTRUCTION: The user is asking a follow-up question regarding their previously prescribed condition/products. Answer their question accurately in {lang_cfg['name']} ({lang_cfg['native_name']}) as OnlyVeda Assistant. Emphasize proper usage of the discussed OnlyVeda products.\n\n"
                    f"User Question ({lang_cfg['name']}): \"{clean_msg}\"\n\n"
                    f"Please reply in {lang_cfg['name']} ({lang_cfg['native_name']}) as OnlyVeda Assistant now:"
                )
                generated_text = self._call_gemini_api(prompt, lang, conversation_history=history)
            else:
                prompt = (
                    f"{SYSTEM_PROMPT_NUTRACEUTICAL_EXPLANATION.format(language_name=lang_cfg['name'], native_name=lang_cfg['native_name'], clean_msg=clean_msg, catalog_context=catalog_context_str)}\n\n"
                    f"Please provide an empathetic, knowledgeable Ayurvedic wellness response in {lang_cfg['name']} ({lang_cfg['native_name']}) concluding with recommending the listed OnlyVeda products:"
                )
                generated_text = self._call_gemini_api(prompt, lang, conversation_history=history)

        # Fallback to local generator if offline, rate limited, or API returned empty
        if not generated_text:
            if intent == "educational":
                generated_text = self._generate_educational_offline_response(clean_msg, lang, topic)
            elif intent == "followup":
                followup_lower = clean_msg.lower()
                primary_prod = suggested_products[0]['name'] if suggested_products else "OnlyVeda Formulation"
                if any(w in followup_lower for w in ["milk", "दूध", "દૂધ", "పాలు", "பால்", "ಹಾಲು", "দুধ", "ଦୁଗ୍ଧ", "دودھ", "പാൽ"]):
                    msg_map = {
                        "en": f"Yes, you can take {primary_prod} with lukewarm milk or warm water, preferably 30 minutes after meals.",
                        "hi": f"हाँ, आप {primary_prod} को गुनगुने दूध या गर्म पानी के साथ ले सकते हैं, भोजन के 30 मिनट बाद लेना सर्वोत्तम है।",
                        "gu": f"હા, તમે {primary_prod} ને નવશેકા દૂધ અથવા ગરમ પાણી સાથે લઈ શકો છો, જમ્યા પછી 30 મિનિટે લેવું હિતાવહ છે.",
                        "mr": f"होय, तुम्ही {primary_prod} कोमट दूध किंवा कोमट पाण्यासोबत जेवणानंतर 30 मिनिटांनी घेऊ शकता.",
                        "te": f"అవును, మీరు {primary_prod} ను గోరువెచ్చని పాలు లేదా నీటితో భోజనం తర్వాత తీసుకోవచ్చు.",
                        "ta": f"ஆம், நீங்கள் {primary_prod} ஐ வெதுவெதுப்பான பால் அல்லது தண்ணீருடன் உணவு உட்கொண்ட பிறகு எடுத்துக்கொள்ளலாம்.",
                        "bn": f"হ্যাঁ, আপনি {primary_prod} হালকা গরম দুধ বা হালকা গরম জলের সাথে খাবারের ৩০ মিনিট পরে নিতে পারেন।",
                        "kn": f"ಹೌದು, ನೀವು {primary_prod} ಅನ್ನು ಬೆಚ್ಚಗಿನ ಹಾಲು ಅಥವಾ ನೀರಿನೊಂದಿಗೆ ಊಟದ ನಂತರ ತೆಗೆದುಕೊಳ್ಳಬಹುದು.",
                        "ur": f"جی ہاں، آپ {primary_prod} نیم گرم دودھ یا پانی کے ساتھ کھانے کے بعد لے سکتے ہیں۔",
                        "or": f"ହଁ, ଆପଣ {primary_prod} କୁ ଉଷୁମ କ୍ଷୀର କିମ୍ବା ପାଣି ସହିତ ଖାଇବା ପରେ ନେଇପାରିବେ។",
                        "ml": f"അതെ, നിങ്ങൾക്ക് {primary_prod} ചെറുചൂടുള്ള പാലിലോ വെള്ളത്തിലോ ഭക്ഷണത്തിന് ശേഷം കഴിക്കാം."
                    }
                    generated_text = msg_map.get(lang, msg_map["en"]) + f"\n\n---\n{lang_cfg['disclaimer']}"
                elif any(w in followup_lower for w in ["side effect", "आडअसर", "આડઅસર", "साइड इफेक्ट", "नुकसान", "సైడ్ ఎఫెక్ట్", "பக்க விளைவு", "ಸೈಡ್ ಎಫೆಕ್ಟ್", "పార్శ్వప్రতিক୍ରિયા", "نقصان"]):
                    se_map = {
                        "en": f"OnlyVeda products like {primary_prod} are 100% natural, herbal, and Ayurvedic formulations with no known adverse side effects when taken at the recommended dose.",
                        "hi": f"OnlyVeda के उत्पाद जैसे {primary_prod} 100% प्राकृतिक और शुद्ध आयुर्वेदिक हैं। निर्धारित खुराक में लेने पर इसका कोई दुष्प्रभाव (side effect) नहीं होता है।",
                        "gu": f"OnlyVeda ની પ્રોડક્ટ્સ જેમ કે {primary_prod} 100% કુદરતી અને આયુર્વેદિક છે. નિયત માત્રામાં લેવાથી કોઈ આડઅસર થતી નથી.",
                        "mr": f"OnlyVeda ची उत्पादने जसे {primary_prod} 100% नैसर्गिक व आयुर्वेदिक आहेत. योग्य प्रमाणात घेतल्यास कोणतेही दुष्परिणाम होत नाहीत.",
                        "te": f"OnlyVeda ఉత్పత్తులు {primary_prod} 100% సహజసిద్ధమైన ఆయుర్వేద మూలికలతో తయారైనవి. సూచించిన మోతాదులో తీసుకుంటే ఎలాంటి సైడ్ ఎఫెక్ట్స్ ఉండవు.",
                        "ta": f"OnlyVeda தயாரிப்புகள் {primary_prod} 100% இயற்கையான மூலிகைகளால் ஆனவை. பரிந்துரைக்கப்பட்ட அளவில் எடுக்கும்போது எந்த பக்கவிளைவுகளும் இல்லை.",
                        "bn": f"OnlyVeda পণ্য যেমন {primary_prod} সম্পূর্ণ প্রাকৃতিক ও আয়ুর্বেদিক। সঠিক মাত্রায় গ্রহণে কোনো পার্শ্বপ্রতিক্রিয়া নেই।",
                        "kn": f"OnlyVeda ಉತ್ಪನ್ನಗಳು {primary_prod} 100% ನೈಸರ್ಗಿಕ ಮತ್ತು ಆಯುರ್ವೇದಿಕವಾಗಿದ್ದು, ನಿಗದಿತ ಪ್ರಮಾಣದಲ್ಲಿ ಯಾವುದೇ ಅಡ್ಡಪರಿಣಾಮಗಳಿಲ್ಲ.",
                        "ur": f"OnlyVeda کی تمام مصنوعات جیسے {primary_prod} 100% قدرتی اور جڑی بوٹیوں سے تیار کردہ ہیں اور ان کا کوئی نقصان دہ سائیڈ ایفیکٹ نہیں ہے۔",
                        "or": f"OnlyVeda ଉତ୍ପାଦ ଯେପରିକି {primary_prod} ସମ୍ପୂର୍ଣ୍ଣ ପ୍ରାକୃତିକ ଏବଂ ଆୟୁର୍ବେଦିକ, ଏହାର କୌଣସି ପାର୍ଶ୍ୱ ପ୍ରତିକ୍ରିୟା ନାହିଁ।",
                        "ml": f"OnlyVeda ഉൽപ്പന്നങ്ങൾ {primary_prod} 100% പ്രകൃതിദത്ത ആയുർവേദ ചേരുവകളാൽ നിർമ്മിതമാണ്. പാർശ്വഫലങ്ങളൊന്നുമില്ല."
                    }
                    generated_text = se_map.get(lang, se_map["en"]) + f"\n\n---\n{lang_cfg['disclaimer']}"
                elif any(w in followup_lower for w in ["how long", "how many days", "कितने दिन", "કેટલા દિવસ", "ఎన్ని రోజులు", "எத்தனை நாட்கள்", "ಎಷ್ಟು ದಿನ", "কত দিন", "କେତେ ଦିନ", "کتنے دن"]):
                    dur_map = {
                        "en": f"For optimal health results, we recommend continuing {primary_prod} consistently for at least 60 to 90 days alongside a balanced Ayurvedic diet.",
                        "hi": f"सर्वोत्तम परिणामों के लिए, संतुलित आहार के साथ कम से कम 60 से 90 दिनों तक {primary_prod} का नियमित सेवन करने की सलाह दी जाती है।",
                        "gu": f"શ્રેષ્ઠ પરિણામ માટે, સંતુલિત આહાર સાથે ઓછામાં ઓછા 60 થી 90 દિવસ સુધી {primary_prod} નું નિયમિત સેવન કરવાની ભલામણ છે.",
                        "mr": f"उत्तम परिणामांसाठी, योग्य आहारासोबत किमान 60 ते 90 दिवस {primary_prod} चे नियमित सेवन करावे.",
                        "te": f"మంచి ఫలితాల కోసం, కనీసం 60 నుండి 90 రోజుల పాటు {primary_prod} ను క్రమం తప్పకుండా తీసుకోవాలని సిఫార్సు చేస్తున్నాము.",
                        "ta": f"சிறந்த பலன்களுக்கு, குறைந்தது 60 முதல் 90 நாட்கள் வரை {primary_prod} ஐ தொடர்ந்து எடுத்துக்கொள்ள பரிந்துரைக்கிறோம்.",
                        "bn": f"সেরা ফলাফলের জন্য, সুষম খাদ্যের সাথে কমপক্ষে ৬০ থেকে ৯০ দিন {primary_prod} নিয়মিত গ্রহণের পরামর্শ দেওয়া হচ্ছে।",
                        "kn": f"ಉತ್ತಮ ಫಲಿತಾಂಶಕ್ಕಾಗಿ, ಕನಿಷ್ಠ 60 ರಿಂದ 90 ದಿನಗಳವರೆಗೆ {primary_prod} ಅನ್ನು ನಿರಂತರವಾಗಿ ಸೇವಿಸಲು ಶಿಫಾರಸು ಮಾಡುತ್ತೇವೆ.",
                        "ur": f"بہترین نتائج کے لیے مناسب غذا کے ساتھ کم از کم 60 سے 90 دن تک {primary_prod} کا باقاعدگی سے استعمال تجویز کیا جاتا ہے۔",
                        "or": f"ସର୍ବୋତ୍ତମ ଫଳାଫଳ ପାଇଁ ଅତି କମରେ ୬୦ ରୁ ୯୦ ଦିନ ପର୍ଯ୍ୟନ୍ତ {primary_prod} ନିୟମିତ ଭାବରେ ସେବନ କରନ୍ତୁ।",
                        "ml": f"മികച്ച ഫലങ്ങൾക്ക്, കുറഞ്ഞത് 60 മുതൽ 90 ദിവസം വരെ {primary_prod} ക്രമമായി കഴിക്കാൻ നിർദ്ദേശിക്കുന്നു."
                    }
                    generated_text = dur_map.get(lang, dur_map["en"]) + f"\n\n---\n{lang_cfg['disclaimer']}"
                else:
                    generated_text = self._generate_localized_template_response(clean_msg, suggested_products, lang, disease_protocol)
            else:
                generated_text = self._generate_localized_template_response(clean_msg, suggested_products, lang, disease_protocol)

        # "AFTER THIS SUGGEST A PRODUCT FROM LIST AND MAKE PROPER AND ACCURATE"
        if suggested_products:
            primary_name = suggested_products[0].get("name", "")
            # If the primary product name is not clearly present in the response text, append the formatted section
            if primary_name.lower() not in generated_text.lower():
                prod_section = self._format_product_recommendation_section(suggested_products, lang)
                disclaimer = lang_cfg["disclaimer"]
                if disclaimer in generated_text:
                    parts = generated_text.rsplit(disclaimer, 1)
                    generated_text = parts[0].strip() + "\n\n" + prod_section + "\n\n---\n" + disclaimer
                else:
                    generated_text = generated_text.strip() + "\n\n" + prod_section + "\n\n---\n" + disclaimer

        # Record turns into SQLite memory
        self.memory.add_message(
            session_id=session_id,
            role="user",
            content=clean_msg,
            language=lang
        )
        self.memory.add_message(
            session_id=session_id,
            role="assistant",
            content=generated_text,
            language=lang,
            products=suggested_products,
            disease_protocol=disease_protocol
        )

        return {
            "session_id": session_id,
            "response": generated_text,
            "language": lang,
            "language_name": lang_cfg["name"],
            "products": suggested_products,
            "disease_protocol": disease_protocol,
            "suggestions": [],
            "has_api_key": bool(self.api_key)
        }
