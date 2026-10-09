"""
OnlyVedaa AI Coach Modules & Orchestration Engine
Implements the 6 AI Coaches, Medical Safety Engine, Nutritrainer, and Voice Agent Controllers
as specified in 'The concept of Chatbot' document.
"""

import re
from typing import Dict, Any, List, Optional, Tuple

# Red Flag Medical Emergency Keywords across English and Indic languages
EMERGENCY_RED_FLAGS = [
    r'\b(?:chest\s*pain|heart\s*attack|angina|हार्ट\s*अटैक|सीने\s*में\s*दर्द|છાતીમાં\s*દુખાવો|ఛాతీ\s*నొప్పి)\b',
    r'\b(?:severe\s*breathlessness|cannot\s*breathe|choking|सांस\s*फूलना|दम\s*घुटना|શ્વાસ\s*લેવામાં\s*તકલીફ)\b',
    r'\b(?:stroke|paralysis\s*attack|facial\s*droop|slurred\s*speech|लकवा|पक्षाघात|સ્ટ્રોક)\b',
    r'\b(?:loss\s*of\s*consciousness|fainted|unconscious|बेहोश|બેભાન|స్పృహ\s*తప్పడం)\b',
    r'\b(?:heavy\s*bleeding|uncontrolled\s*bleeding|खून\s*बहना|रक्तस्राव|લોહી\s*નીકળવું)\b',
    r'\b(?:suicidal|suicide|kill\s*myself|आत्महत्या|આત્મહત્યા)\b',
    r'\b(?:anaphylaxis|severe\s*allergic\s*reaction|throat\s*swelling|गला\s*फूलना)\b'
]

EMERGENCY_DISCLAIMER_MAP = {
    "en": "🚨 **URGENT MEDICAL ATTENTION REQUIRED**\n\nThis symptom may indicate an acute or critical medical emergency. Please **seek immediate professional emergency medical care or visit the nearest hospital** right away. Onlyvedaa AI is an educational wellness guide and cannot provide emergency diagnosis or medical intervention.",
    "hi": "🚨 **आपातकालीन चिकित्सकीय सहायता आवश्यक है**\n\nयह लक्षण किसी गंभीर चिकित्सकीय आपातकाल का संकेत हो सकता है। कृपया तुरंत **नजदीकी अस्पताल या डॉक्टर से आपातकालीन सहायता लें**। Onlyvedaa AI केवल शैक्षणिक स्वास्थ्य गाइड है और आपातकालीन चिकित्सा का विकल्प नहीं है।",
    "gu": "🚨 **તાત્કાલિક તબીબી સારવારની જરૂર છે**\n\nઆ લક્ષણ ગંભીર તબીબી કટોકટી સૂચવી શકે છે. કૃપા કરીને તરત જ **નજીકની હોસ્પિટલ અથવા કટોકટી તબીબી સેવાનો સંપર્ક કરો**। Onlyvedaa AI એક શૈક્ષણિક વેલનેસ માર્ગદર્શક છે અને કટોકટીની સારવાર માટે નથી.",
    "mr": "🚨 **तातडीने वैद्यकीय मदतीची आवश्यकता आहे**\n\nहे लक्षण गंभीर वैद्यकीय समस्येचे असू शकते. कृपया त्वरित **जवळच्या रुग्णालयात किंवा आपत्कालीन वैद्यकीय कक्षात जावे**.",
    "bn": "🚨 **জরুরি চিকিৎসা সহায়তা প্রয়োজন**\n\nএই লক্ষণটি একটি গুরুতর স্বাস্থ্য সংক্রান্ত জরুরি অবস্থা নির্দেশ করতে পারে। অনুগ্রহ করে অবিলম্বে **নিকটস্থ হাসপাতালে যান বা জরুরি চিকিৎসা নিন**।",
    "te": "🚨 **తక్షణ వైద్య సహాయం అవసరం**\n\nఈ లక్షణం తీవ్రమైన అత్యవసర వైద్య పరిస్థితిని సూచించవచ్చు. దయచేసి వెంటనే **సమీప ఆసుపత్రికి లేదా అత్యవసర విభాగానికి వెళ్లండి**.",
    "ta": "🚨 **அவசர மருத்துவ உதவி தேவை**\n\nஇந்த அறிகுறி தீவிர மருத்துவ அவசரநிலையைக் குறிக்கலாம். தயவுசெய்து உடனடியாக **அருகிலுள்ள மருத்துவமனைக்குச் செல்லுங்கள்**.",
    "kn": "🚨 **ತುರ್ತು ವೈದ್ಯಕೀಯ ನೆರವು ಅಗತ್ಯವಿದೆ**\n\nಈ ಲಕ್ಷಣವು ಗಂಭೀರ ವೈದ್ಯಕೀಯ ಸಮಸ್ಯೆಯನ್ನು ಸೂಚಿಸಬಹುದು. ದಯವಿಟ್ಟು ತಕ್ಷಣವೇ **ಹತ್ತಿರದ ಆಸ್ಪತ್ರೆಗೆ ಭೇಟಿ ನೀಡಿ**.",
    "or": "🚨 **ଜରୁରୀକାଳୀନ ଚିକିତ୍ସା ସହାୟତା ଆବଶ୍ୟକ**\n\nଏହି ଲକ୍ଷଣ ଏକ ଗୁରୁତର ଡାକ୍ତରୀ ଜରୁରୀ ପରିସ୍ଥିତି ହୋଇପାରେ। ଦୟାକରି ତୁରନ୍ତ **ନିକଟସ୍ଥ ଡାକ୍ତରଖାନାକୁ ଯାଆନ୍ତୁ**.",
    "ml": "🚨 **അടിയന്തര വൈദ്യസഹായം ആവശ്യമാണ്**\n\nഈ ലക്ഷണം ഗുരുതരമായ ഒരു മെഡിക്കൽ അടിയന്തരാവസ്ഥയെ സൂചിപ്പിക്കാം. ദയവായി ഉടൻ തന്നെ **അടുത്തുള്ള ആശുപത്രി സന്ദർശിക്കുക**.",
    "ur": "🚨 **فوری طبی امداد کی ضرورت ہے**\n\nیہ علامت کسی سنگین طبی ایمرجنسی کی نشاندہی کر سکتی ہے۔ براہ کرم فوری طور پر **قریبی ہسپتال یا ایمرجنسی روم سے رجوع کریں**۔"
}


class MedicalSafetyEngine:
    """Detects acute medical emergencies and returns protective safety warnings."""
    @staticmethod
    def check_red_flags(query: str, lang: str = "en") -> Optional[str]:
        cleaned = query.strip().lower()
        for pattern in EMERGENCY_RED_FLAGS:
            if re.search(pattern, cleaned):
                return EMERGENCY_DISCLAIMER_MAP.get(lang, EMERGENCY_DISCLAIMER_MAP["en"])
        return None


class CoachModule:
    BODY = "body"
    NUTRITION = "nutrition"
    HEALTH = "health"
    PRODUCT = "product"
    CAREER = "career"
    NUTRITRAINER = "nutritrainer"
    DISCOVERY = "discovery"
    ORCHESTRATOR = "orchestrator"


COACH_METADATA = {
    CoachModule.BODY: {
        "title": "🧬 Body Coach (Know Your Body™)",
        "badge": "Anatomy & Physiology",
        "description": "Explains how your cells, organs, digestion, and metabolic systems function."
    },
    CoachModule.NUTRITION: {
        "title": "🥗 Nutrition Coach",
        "badge": "Nutrients & Diet",
        "description": "Guides you through protein, hydration, micronutrients, and healthy eating patterns."
    },
    CoachModule.HEALTH: {
        "title": "🩺 Health Educator",
        "badge": "Physiology & Prevention",
        "description": "Clear, non-diagnostic explanations of common health conditions and lifestyle principles."
    },
    CoachModule.PRODUCT: {
        "title": "🌿 Onlyvedaa Wellness & Product Guide",
        "badge": "Product Brain",
        "description": "Scientific, evidence-informed guidance on Onlyvedaa formulations, mechanisms, and usage."
    },
    CoachModule.CAREER: {
        "title": "🚀 Onlyvedaa Career Coach",
        "badge": "Community Commerce",
        "description": "Explores Why Onlyvedaa, ethical wellness entrepreneurship, leadership, and earning pathways."
    },
    CoachModule.NUTRITRAINER: {
        "title": "🎓 Nutritrainer AI Academy",
        "badge": "Interactive Learning",
        "description": "Structured curriculum, adaptive coaching (Explain → Ask → Check → Advance), and quizzes."
    },
    CoachModule.DISCOVERY: {
        "title": "📋 Personal Wellness Discovery",
        "badge": "Health Journey",
        "description": "Comprehensive assessment creating your Personal Wellness Snapshot and 30-Day Plan."
    }
}


class OrchestratorEngine:
    """Classifies user intent and routes to the appropriate coach."""
    @staticmethod
    def classify_intent(query: str, explicit_module: Optional[str] = None) -> str:
        if explicit_module and explicit_module in COACH_METADATA:
            return explicit_module

        cleaned = query.strip().lower()

        # Career / Business intent
        career_keywords = [
            "career", "business", "earning", "income", "opportunity", "distributor", "entrepreneur",
            "why onlyveda", "why onlyvedaa", "business model", "join onlyveda", "direct selling",
            "commission", "leader", "community commerce", "franchise", "पार्टनर", "कमाई", "बिज़नेस", "રોજગાર"
        ]
        if any(w in cleaned for w in career_keywords):
            return CoachModule.CAREER

        # Nutritrainer / Quiz / Academy intent
        nutri_keywords = [
            "quiz", "test me", "nutritrainer", "certificate", "exam", "lesson", "level 1", "level 2",
            "teach me step by step", "academy", "training", "क्विज", "परीक्षा", "શીખવો"
        ]
        if any(w in cleaned for w in nutri_keywords):
            return CoachModule.NUTRITRAINER

        # Discovery session intent
        discovery_keywords = [
            "discovery", "assessment", "my profile", "snapshot", "30-day journey", "wellness plan",
            "analyze me", "evaluate my health"
        ]
        if any(w in cleaned for w in discovery_keywords):
            return CoachModule.DISCOVERY

        # Body Coach (Know Your Body) intent
        body_keywords = [
            "cell", "tissue", "organ", "physiology", "how digestion works", "digestive system",
            "how liver works", "how kidney works", "how heart works", "brain function",
            "nervous system", "gut microbiome", "sleep physiology", "metabolism works",
            "शरीर कैसे काम करता है", "पाचन क्रिया", "શરીર વિજ્ઞાન"
        ]
        if any(w in cleaned for w in body_keywords):
            return CoachModule.BODY

        # Nutrition Coach intent
        nutrition_keywords = [
            "protein", "macronutrient", "micronutrient", "fiber", "fibre", "calorie", "hydration",
            "water intake", "carbohydrate", "fats", "vitamins", "minerals", "diet chart",
            "food choices", "डाइट", "पोषण", "ખોરાક"
        ]
        if any(w in cleaned for w in nutrition_keywords):
            return CoachModule.NUTRITION

        # Default to Orchestrator (combines Health Educator & Wellness Guide)
        return CoachModule.ORCHESTRATOR


class WellnessDiscoveryEngine:
    """Processes user profile inputs and builds Personal Wellness Snapshot & 30-Day Journey."""
    @staticmethod
    def build_snapshot(profile: Dict[str, Any], lang: str = "en") -> Dict[str, Any]:
        age = profile.get("age", 35)
        gender = profile.get("gender", "Not specified")
        diet = profile.get("diet", "Vegetarian")
        goal = profile.get("goal", "Overall Vitality & Energy")
        sleep = profile.get("sleep", "6-7 hours")
        activity = profile.get("activity", "Moderate")
        concern = profile.get("concern", "General Wellness")

        snapshot = {
            "title": "🌿 Your Personal Wellness Snapshot™",
            "profile_summary": f"Age: {age} • Gender: {gender} • Diet: {diet} • Activity: {activity} • Sleep: {sleep}",
            "primary_goal": goal,
            "primary_concern": concern,
            "focus_areas": [
                {"area": "Metabolic Energy & Nutrition", "status": "Optimization Needed", "tip": "Focus on high-quality morning protein and hydration pacing."},
                {"area": "Digestive & Gut Microbiome", "status": "Fundamental Foundation", "tip": "Introduce prebiotic fiber and warm herbal digestive support."},
                {"area": "Rest & Cellular Recovery", "status": "Sleep Hygiene", "tip": f"Target 7.5 hours consistent sleep to regulate circadian cortisol."}
            ],
            "journey_plan_30_days": {
                "days_1_10": "Phase 1 (Awaken & Cleanse): Rebalance hydration, eliminate inflammatory processed sugars, and support gut flora.",
                "days_11_20": "Phase 2 (Nourish & Balance): Introduce core herbal micronutrients and adaptogens for metabolic efficiency.",
                "days_21_30": "Phase 3 (Sustain & Thrive): Consolidate positive daily habits, activity benchmarks, and long-term vitality protocols."
            }
        }
        return snapshot


class NutritrainerCurriculum:
    """Structured levels and interactive quiz questions for distributor and customer wellness mastery."""
    CURRICULUM = [
        {
            "level": 1,
            "title": "Nutrition Fundamentals",
            "description": "Macronutrients, Micronutrients, Fiber, Protein requirements, and Hydration pacing.",
            "quiz": [
                {
                    "question": "What is the primary structural role of protein in the human body?",
                    "options": ["A. Quick burst energy only", "B. Muscle repair, cellular enzymes, and neurotransmitter synthesis", "C. Long-term fat storage"],
                    "correct": "B",
                    "explanation": "Protein provides essential amino acids needed to build and repair tissues, produce enzymes, and support immune antibodies."
                },
                {
                    "question": "Why is soluble prebiotic fiber critical for digestive wellness?",
                    "options": ["A. It feeds beneficial gut bacteria and forms short-chain fatty acids", "B. It prevents water absorption", "C. It increases acidity in stomach"],
                    "correct": "A",
                    "explanation": "Prebiotic fiber acts as nourishment for healthy gut microbes, producing SCFAs like butyrate which protect the gut lining."
                }
            ]
        },
        {
            "level": 2,
            "title": "Human Physiology & Organs",
            "description": "Understanding the liver, kidneys, cardiovascular system, and the gut-brain axis.",
            "quiz": [
                {
                    "question": "Which organ is primarily responsible for bile production and filtering metabolic wastes from the blood?",
                    "options": ["A. Spleen", "B. Liver", "C. Pancreas"],
                    "correct": "B",
                    "explanation": "The liver produces bile to emulsify dietary fats and processes all nutrients absorbed from the digestive tract."
                }
            ]
        },
        {
            "level": 3,
            "title": "Onlyvedaa Product Science & Mechanisms",
            "description": "Evidence-based phytomedicine, bioavailability, synergistic formulation, and approved claims.",
            "quiz": [
                {
                    "question": "What is Onlyvedaa's core philosophical rule regarding product recommendations?",
                    "options": ["A. Pitch products immediately on first contact", "B. Knowledge Before Recommendation: Understand and educate first", "C. Prescribe treatments for all medical diseases"],
                    "correct": "B",
                    "explanation": "Onlyvedaa champions 'Knowledge Before Recommendation'—empowering users to understand their physiology before introducing wellness supplements."
                }
            ]
        }
    ]
