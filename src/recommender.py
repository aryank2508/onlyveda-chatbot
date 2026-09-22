"""
Multilingual Nutraceutical Recommendation Engine for OnlyVeda
Performs exact disease protocol matching from diseases_wise_1.csv
combined with hybrid semantic search across 10 Indic languages.
"""

import os
import re
import json
import unicodedata
from typing import List, Dict, Any, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from src.config import MULTILINGUAL_HEALTH_TAXONOMY, SUPPORTED_LANGUAGES
from src.data_manager import ProductDataManager

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
PROTOCOLS_FILE = os.path.join(DATA_DIR, "disease_protocols.json")
TAXONOMY_FILE = os.path.join(DATA_DIR, "disease_taxonomy.json")


INDIC_HALANTS = '\u094d\u09cd\u0a4d\u0acd\u0b4d\u0bcd\u0c4d\u0ccd\u0d4d'

STOP_PARTICLES = {
    # Hindi / Urdu
    'का', 'के', 'की', 'को', 'में', 'से', 'पर', 'और', 'या', 'है', 'हैं', 'था', 'थी', 'मुझे', 'मेरा', 'मेरी', 'बहुत', 'ज्यादा', 'شدید', 'شدت',
    'میں', 'کے', 'کی', 'کا', 'کو', 'سے', 'پر', 'اور', 'یا', 'ہے', 'ہیں', 'تھا', 'تھی', 'مجھے', 'میرا', 'میری', 'بہت', 'زیادہ',
    # Bengali
    'র', 'এর', 'তে', 'এ', 'য়', 'য়ে', 'ও', 'এবং', 'আমার', 'খুব', 'হচ্ছে', 'আছে',
    # Marathi
    'त', 'मध्ये', 'च्या', 'ची', 'चे', 'ला', 'ने', 'आणि', 'माझे', 'खूप', 'आहे', 'आहेत',
    # Telugu
    'లో', 'కి', 'కు', 'తో', 'మరియు', 'నాకు', 'ఉంది', 'చాలా',
    # Tamil
    'இல்', 'க்கு', 'உடைய', 'மற்றும்', 'எனக்கு', 'உள்ளது', 'அதிகமாக',
    # Gujarati
    'માં', 'નો', 'ની', 'નું', 'ના', 'થી', 'અને', 'મારા', 'ખૂબ', 'છે',
    # Kannada
    'ಅಲ್ಲಿ', 'ಗೆ', 'ಮತ್ತು', 'ನನಗೆ', 'ಇದೆ', 'ತುಂಬಾ',
    # Odia
    'ରେ', 'ର', 'ଏବଂ', 'ମୋର', 'ବହୁତ', 'ଅଛି',
    # Malayalam
    'ൽ', 'இல்', 'ന്', 'ന്റെ', 'ആണ്', 'എനിക്ക്', 'വളരെ',
    # English
    'in', 'of', 'the', 'a', 'an', 'and', 'or', 'for', 'with', 'is', 'are', 'have', 'severe', 'acute', 'my', 'i', 'to'
}


class NutraceuticalRecommender:
    def __init__(self, data_manager: ProductDataManager):
        self.data_manager = data_manager
        self.products = self.data_manager.get_all_products()
        self.disease_protocols = {}
        self.disease_taxonomy = {}
        self.localized_disease_names = {}
        self.vectorizer = None
        self.tfidf_matrix = None

        self._load_disease_data()
        self._build_search_index()

    def _load_disease_data(self):
        """Load disease protocols and multilingual taxonomy."""
        if os.path.exists(PROTOCOLS_FILE):
            with open(PROTOCOLS_FILE, "r", encoding="utf-8") as f:
                self.disease_protocols = json.load(f)

        if os.path.exists(TAXONOMY_FILE):
            with open(TAXONOMY_FILE, "r", encoding="utf-8") as f:
                tax_data = json.load(f)
                self.disease_taxonomy = tax_data.get("taxonomy", {})
                self.localized_disease_names = tax_data.get("localized_names", {})

    def _build_search_index(self):
        """Index all products into a rich multilingual searchable corpus."""
        self.products = self.data_manager.get_all_products()
        if not self.products:
            return

        corpus = []
        for p in self.products:
            ingredients_str = " ".join(p.get("key_ingredients", []))
            concerns_str = " ".join(p.get("health_concerns", []))
            tags_str = " ".join(p.get("tags", []))
            doc = f"{p.get('name', '')} {p.get('category', '')} {p.get('benefits', '')} {ingredients_str} {concerns_str} {tags_str}"
            corpus.append(doc.lower())

        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 5),
            sublinear_tf=True
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def clean_query(self, text: str) -> str:
        """Strip punctuation marks safely without removing Indic vowel marks/halants."""
        return ''.join(ch for ch in text if not unicodedata.category(ch).startswith('P')).strip().lower()

    def _word_match(self, token: str, query_words: List[str]) -> bool:
        """Matches a keyword token against query words considering Indic agglutination/inflections."""
        token_clean = self.clean_query(token)
        if not token_clean:
            return False
        if token_clean in query_words:
            return True

        is_indic = any(ord(c) > 127 for c in token_clean)
        if is_indic:
            base = token_clean.rstrip(INDIC_HALANTS)
            for qw in query_words:
                qw_clean = qw.rstrip(INDIC_HALANTS)
                if qw == token_clean or qw_clean == base:
                    return True
                if len(base) >= 4 and (qw.startswith(base) or base.startswith(qw_clean)):
                    return True
                # Stem prefix matching for Indic inflections (e.g. दुखणे vs दुखतात, నొప్పి vs నొప్పులు)
                cp = 0
                while cp < len(token_clean) and cp < len(qw) and token_clean[cp] == qw[cp]:
                    cp += 1
                min_len = min(len(token_clean), len(qw))
                if cp >= 4 and cp >= min_len * 0.75:
                    return True
        else:
            for qw in query_words:
                if qw == token_clean or qw == token_clean + 's' or qw == token_clean + 'es' or token_clean == qw + 's':
                    return True
        return False

    def detect_disease_protocol(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Detects if the query mentions any of the 31 specific conditions from diseases_wise_1.csv
        across English, Hindi, Bengali, Marathi, Telugu, Tamil, Gujarati, Urdu, Kannada, Odia, Malayalam.
        Supports exact phrase matching and agglutinative/particle-separated constituent matching.
        """
        cleaned = self.clean_query(query)
        if not cleaned:
            return None

        q_tokens = [w for w in cleaned.split() if w]
        candidates = []

        for disease_name, lang_dict in self.disease_taxonomy.items():
            for lang, keywords in lang_dict.items():
                for kw in keywords:
                    kw_clean = self.clean_query(kw)
                    if not kw_clean:
                        continue

                    # 1. Exact phrase/substring match
                    if kw_clean in cleaned:
                        score = len(kw_clean) * 10
                        candidates.append({
                            "disease": disease_name,
                            "score": score,
                            "matched_keyword": kw,
                            "matched_lang": lang,
                            "protocol": self.disease_protocols.get(disease_name)
                        })
                        continue

                    # 2. Token-level constituent matching
                    kw_tokens = [w for w in kw_clean.split() if w and w not in STOP_PARTICLES]
                    if not kw_tokens:
                        continue

                    if len(kw_tokens) == 1:
                        if self._word_match(kw_tokens[0], q_tokens):
                            score = len(kw_tokens[0]) * 8
                            candidates.append({
                                "disease": disease_name,
                                "score": score,
                                "matched_keyword": kw,
                                "matched_lang": lang,
                                "protocol": self.disease_protocols.get(disease_name)
                            })
                        continue

                    # Multi-token: all content tokens must be present in query
                    all_matched = True
                    matched_chars = 0
                    for kt in kw_tokens:
                        if self._word_match(kt, q_tokens):
                            matched_chars += len(kt)
                        else:
                            all_matched = False
                            break

                    if all_matched:
                        score = matched_chars * 5 + len(kw_tokens) * 4
                        candidates.append({
                            "disease": disease_name,
                            "score": score,
                            "matched_keyword": kw,
                            "matched_lang": lang,
                            "protocol": self.disease_protocols.get(disease_name)
                        })

        if not candidates:
            return None

        candidates.sort(key=lambda x: x["score"], reverse=True)
        best = candidates[0]
        return {
            "disease": best["disease"],
            "matched_keyword": best["matched_keyword"],
            "matched_lang": best["matched_lang"],
            "protocol": best["protocol"]
        }

    def detect_category_from_query(self, query: str) -> List[str]:
        """Detect general health categories mentioned in query using taxonomy."""
        query_lower = self.clean_query(query)
        matched_categories = []

        for category, keywords in MULTILINGUAL_HEALTH_TAXONOMY.items():
            for kw in keywords:
                if self.clean_query(kw) in query_lower:
                    if category not in matched_categories:
                        matched_categories.append(category)
                    break

        return matched_categories

    def _find_product_by_name(self, supp_name: str) -> Optional[Dict[str, Any]]:
        """Find matching product in catalog for supplement name from CSV."""
        supp_clean = supp_name.lower().strip()

        # Direct match on raw_name or name
        for p in self.products:
            if p.get("raw_name", "").lower() == supp_clean:
                return dict(p)
            if p.get("name", "").lower() == supp_clean:
                return dict(p)
            if supp_clean in p.get("name", "").lower():
                return dict(p)

        # Fallback aliases
        alias_map = {
            "calciumus": "calciumus",
            "calcimus": "calcimus",
            "hadjoj": "hadjoj",
            "wal d3": "wal d3",
            "vitamin d3": "vitamin d3",
            "vitamin c": "vitamin c",
            "liver detox": "liver detox",
            "strenus caps": "strenus caps",
            "strenus oil": "strenus oil",
            "hepatreat tablet": "hepatreat tablet",
            "hepatreat": "hepatreat",
            "prowal": "prowal",
            "ashyuka plus": "ashyuka plus",
            "immuferin": "immuferin",
            "serronil": "serronil",
            "multi vitamin men/women": "multivitamin men/women",
            "multivitamin for men/women": "multivitamin men/women",
            "multivitamin men/ women": "multivitamin men/women",
            "active 365`": "active 365"
        }

        mapped_key = alias_map.get(supp_clean)
        if mapped_key:
            for p in self.products:
                if p.get("raw_name", "").lower() == mapped_key.lower():
                    return dict(p)

        return None

    def recommend(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Recommends OnlyVeda products based on query:
        1. Exact disease protocol from diseases_wise_1.csv (if a specific condition is named).
        2. General semantic retrieval of OnlyVeda products.
        Returns:
            {
                "disease_protocol": {...} or None,
                "products": [list of OnlyVeda products with prescribed doses]
            }
        """
        if not self.products:
            self._build_search_index()
            if not self.products:
                return {"disease_protocol": None, "products": []}

        query_clean = self.clean_query(query)

        # 1. Check for exact disease protocol match from diseases_wise_1.csv
        disease_match = self.detect_disease_protocol(query_clean)
        if disease_match and disease_match.get("protocol"):
            protocol = disease_match["protocol"]
            disease_name = disease_match["disease"]
            protocol_supps = protocol.get("supplements", [])

            protocol_products = []
            for item in protocol_supps:
                supp_name = item.get("name", "")
                dose = item.get("dose", "")
                prod = self._find_product_by_name(supp_name)
                if prod:
                    prod["prescribed_dose"] = dose
                    prod["disease_indicated"] = disease_name
                    prod["is_protocol_product"] = True
                    protocol_products.append(prod)
                else:
                    # Synthetic entry from protocol if not in products
                    protocol_products.append({
                        "product_id": f"OV-{supp_name.upper()[:6]}",
                        "name": f"OnlyVeda {supp_name.title()}",
                        "category": protocol.get("category", "General Care"),
                        "key_ingredients": [supp_name],
                        "benefits": f"Specifically indicated for {disease_name}.",
                        "dosage_and_usage": dose,
                        "prescribed_dose": dose,
                        "disease_indicated": disease_name,
                        "is_protocol_product": True,
                        "price_inr": 499,
                        "size": "Standard Pack",
                        "in_stock": True
                    })

            return {
                "disease_protocol": {
                    "disease": disease_name,
                    "category": protocol.get("category"),
                    "matched_keyword": disease_match.get("matched_keyword"),
                    "localized_names": self.localized_disease_names.get(disease_name, {})
                },
                "products": protocol_products
            }

        # 2. General semantic matching across OnlyVeda catalog
        scores = np.zeros(len(self.products))
        detected_categories = self.detect_category_from_query(query_clean)

        for idx, prod in enumerate(self.products):
            if prod.get("category") in detected_categories:
                scores[idx] += 4.0

            tags = [t.lower() for t in prod.get("tags", [])]
            concerns = [c.lower() for c in prod.get("health_concerns", [])]
            ingredients = [i.lower() for i in prod.get("key_ingredients", [])]

            for tag in tags:
                if tag in query_clean:
                    scores[idx] += 2.5
            for concern in concerns:
                if concern in query_clean:
                    scores[idx] += 2.0
            for ing in ingredients:
                if ing in query_clean:
                    scores[idx] += 1.5

        if self.vectorizer is not None and self.tfidf_matrix is not None:
            try:
                query_vec = self.vectorizer.transform([query_clean])
                cosine_sims = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
                scores += cosine_sims * 3.0
            except Exception as e:
                print(f"Error in vector similarity: {e}")

        ranked_indices = np.argsort(scores)[::-1]
        results = []
        for idx in ranked_indices:
            score = float(scores[idx])
            if score >= 1.5:
                prod = dict(self.products[idx])
                prod["relevance_score"] = round(score, 2)
                raw_dose = prod.get("dosage_and_usage", "1 tablet twice daily")
                if " | " in raw_dose:
                    first_part = raw_dose.split(" | ")[0]
                    if ":" in first_part:
                        first_part = first_part.split(":", 1)[1].strip()
                    prod["prescribed_dose"] = first_part
                else:
                    prod["prescribed_dose"] = raw_dose
                results.append(prod)
            if len(results) >= top_k:
                break

        return {
            "disease_protocol": None,
            "products": results
        }
