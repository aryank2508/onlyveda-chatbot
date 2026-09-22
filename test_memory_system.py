"""
Test Suite for Persistent Multi-turn Memory System in OnlyVeda Chatbot.
Verifies SQLite storage, contextual follow-up recall, history retrieval,
and session reset across multiple turns and languages.
"""

import os
import sys
import unittest
import tempfile
import json

from src.data_manager import ProductDataManager
from src.memory_manager import ConversationMemory
from src.bot_engine import OnlyVedaChatbot


class TestMemorySystem(unittest.TestCase):
    def setUp(self):
        # Use a temporary database for test isolation
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.memory = ConversationMemory(db_path=self.temp_db.name)
        self.dm = ProductDataManager()
        self.chatbot = OnlyVedaChatbot(data_manager=self.dm, memory=self.memory)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            try:
                os.remove(self.temp_db.name)
            except Exception:
                pass

    def test_session_creation_and_persistence(self):
        """Test that sessions and messages persist to SQLite."""
        session_id = self.memory.get_or_create_session(title="Test Consultation")
        self.assertTrue(session_id.startswith("session_") or session_id.startswith("sess_"))

        # Add message
        self.memory.add_message(
            session_id=session_id,
            role="user",
            content="मुझे हाई बीपी है",
            language="hi"
        )
        self.memory.add_message(
            session_id=session_id,
            role="assistant",
            content="Linopress Tablet लें",
            language="hi",
            products=[{"name": "Linopress Tablet", "prescribed_dose": "1-0-1"}],
            disease_protocol={"disease": "High Blood Pressure"}
        )

        # Retrieve history
        hist = self.memory.get_history(session_id)
        self.assertEqual(len(hist), 2)
        self.assertEqual(hist[0]["role"], "user")
        self.assertEqual(hist[0]["content"], "मुझे हाई बीपी है")
        self.assertEqual(hist[1]["role"], "assistant")
        self.assertEqual(hist[1]["products"][0]["name"], "Linopress Tablet")

        # Check context
        ctx = self.memory.get_session_context(session_id)
        self.assertEqual(ctx["last_disease"], "High Blood Pressure")
        self.assertEqual(ctx["last_products"][0]["name"], "Linopress Tablet")

    def test_multi_turn_contextual_recall(self):
        """Test multi-turn conversation where follow-up references prior prescription."""
        session_id = "test_sess_turn_1"

        # Turn 1: User inquires about High Blood Pressure
        turn1 = self.chatbot.chat("मुझे हाई ब्लड प्रेशर की शिकायत है", session_id=session_id)
        self.assertEqual(turn1["session_id"], session_id)
        self.assertIsNotNone(turn1["disease_protocol"])
        self.assertIn("blood pres", turn1["disease_protocol"]["disease"].lower())
        prod_names = [p["name"] for p in turn1["products"]]
        self.assertTrue(any("linopress" in p.lower() for p in prod_names))

        # Verify context stored in memory
        ctx = self.memory.get_session_context(session_id)
        self.assertIn("blood pres", ctx["last_disease"].lower())
        self.assertTrue(any("linopress" in p["name"].lower() for p in ctx["last_products"]))

        # Turn 2: Follow-up question about milk (no disease mentioned!)
        turn2 = self.chatbot.chat("क्या इसे दूध के साथ ले सकते हैं?", session_id=session_id)
        self.assertEqual(turn2["session_id"], session_id)
        # Verify that the response mentions the product Linopress
        self.assertTrue("linopress" in turn2["response"].lower())
        self.assertTrue("दूध" in turn2["response"] or "milk" in turn2["response"].lower())

        # Turn 3: Follow-up question about how many days (duration)
        turn3 = self.chatbot.chat("कितने दिन तक लेना चाहिए?", session_id=session_id)
        self.assertTrue("linopress" in turn3["response"].lower())
        self.assertTrue("दिन" in turn3["response"] or "days" in turn3["response"].lower())

        # Verify history has all 6 messages (3 user + 3 assistant)
        hist = self.memory.get_history(session_id)
        self.assertEqual(len(hist), 6)

    def test_multi_turn_gujarati_context(self):
        """Test multi-turn memory in Gujarati language."""
        session_id = "test_sess_gu"

        # Turn 1: User inquires about Acne / Pimples in Gujarati
        turn1 = self.chatbot.chat("મારા ચહેરા પર ખૂબ ખીલ અને પિમ્પલ્સ છે", session_id=session_id)
        self.assertEqual(turn1["session_id"], session_id)
        self.assertEqual(turn1["disease_protocol"]["disease"], "acne")
        prod_names = [p["name"] for p in turn1["products"]]
        self.assertTrue(any("active 365" in p.lower() or "xemma" in p.lower() for p in prod_names))

        # Turn 2: Follow-up regarding side effects in Gujarati
        turn2 = self.chatbot.chat("કોઈ આડઅસર છે?", session_id=session_id)
        self.assertTrue(any(p["name"].lower() in turn2["response"].lower() for p in turn1["products"]))
        self.assertTrue("આડઅસર" in turn2["response"] or "side effect" in turn2["response"].lower())

    def test_session_clear(self):
        """Test clearing a session."""
        session_id = "test_sess_clear"
        self.chatbot.chat("Hello, I have acidity", session_id=session_id)
        hist = self.memory.get_history(session_id)
        self.assertGreater(len(hist), 0)

        # Clear session
        cleared = self.memory.clear_session(session_id)
        self.assertTrue(cleared)
        hist_after = self.memory.get_history(session_id)
        self.assertEqual(len(hist_after), 0)

    def test_educational_inquiries_pain_and_heart(self):
        """Test that educational queries like 'what is pain' and 'which are heart dieses' are explained thoroughly."""
        # 1. "what is pain"
        res_pain = self.chatbot.chat("what is pain", session_id="test_edu_1")
        self.assertIsNone(res_pain["disease_protocol"])
        self.assertGreater(len(res_pain["response"]), 150)
        self.assertTrue("pain" in res_pain["response"].lower() or "vata" in res_pain["response"].lower())
        self.assertTrue(any("strenus" in p["name"].lower() or "serronil" in p["name"].lower() for p in res_pain["products"]))

        # 2. "which are heart dieses"
        res_heart = self.chatbot.chat("which are heart dieses", session_id="test_edu_2")
        self.assertIsNone(res_heart["disease_protocol"])
        self.assertGreater(len(res_heart["response"]), 150)
        heart_response_lower = res_heart["response"].lower()
        self.assertTrue(
            "coronary" in heart_response_lower or 
            "hypertension" in heart_response_lower or 
            "blood pressure" in heart_response_lower or 
            "arrhythmia" in heart_response_lower or
            "cardiovascular" in heart_response_lower
        )
        self.assertTrue(any("linopress" in p["name"].lower() or "arjuna" in p["name"].lower() for p in res_heart["products"]))


if __name__ == "__main__":
    unittest.main()
