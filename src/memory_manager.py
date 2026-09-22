"""
Conversation Memory Manager for OnlyVeda Chatbot
Provides persistent SQLite storage for multi-turn chat sessions,
contextual recall, and conversation history across restarts.
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DEFAULT_DB_PATH = os.path.join(DATA_DIR, "memory.db")


class ConversationMemory:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Create sessions and messages tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_disease TEXT,
                    last_products_json TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    language TEXT DEFAULT 'en',
                    products_json TEXT,
                    disease_protocol_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, id)
            """)
            conn.commit()

    def get_or_create_session(self, session_id: Optional[str] = None, title: Optional[str] = None) -> str:
        """Ensure session exists or create a new one."""
        if not session_id:
            session_id = f"session_{int(datetime.now().timestamp())}_{os.urandom(3).hex()}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT session_id FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if not row:
                sess_title = title or "Wellness Consultation"
                cursor.execute("""
                    INSERT INTO sessions (session_id, title, created_at, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (session_id, sess_title))
                conn.commit()
        return session_id

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        language: str = "en",
        products: Optional[List[Dict[str, Any]]] = None,
        disease_protocol: Optional[Dict[str, Any]] = None
    ):
        """Save a message to persistent storage and update session context."""
        session_id = self.get_or_create_session(session_id)
        prods_json = json.dumps(products, ensure_ascii=False) if products else None
        proto_json = json.dumps(disease_protocol, ensure_ascii=False) if disease_protocol else None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO messages (session_id, role, content, language, products_json, disease_protocol_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (session_id, role, content, language, prods_json, proto_json))

            # Update session context if products or disease were identified
            last_dis = disease_protocol.get("disease") if disease_protocol else None
            if last_dis or products:
                cursor.execute("""
                    UPDATE sessions
                    SET updated_at = CURRENT_TIMESTAMP,
                        last_disease = COALESCE(?, last_disease),
                        last_products_json = COALESCE(?, last_products_json)
                    WHERE session_id = ?
                """, (last_dis, prods_json, session_id))
            else:
                cursor.execute("""
                    UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?
                """, (session_id,))

            conn.commit()

    def get_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent messages for a session formatted for chat and LLM context."""
        if not session_id:
            return []

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT role, content, language, products_json, disease_protocol_json, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY id ASC
            """, (session_id,))
            rows = cursor.fetchall()

            history = []
            for r in rows[-limit:]:
                prods = json.loads(r["products_json"]) if r["products_json"] else []
                proto = json.loads(r["disease_protocol_json"]) if r["disease_protocol_json"] else None
                history.append({
                    "role": r["role"],
                    "content": r["content"],
                    "language": r["language"],
                    "products": prods,
                    "disease_protocol": proto,
                    "created_at": r["created_at"]
                })
            return history

    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get the active health context (last discussed disease/products) from memory."""
        if not session_id:
            return {}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT last_disease, last_products_json, updated_at
                FROM sessions
                WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()
            if row:
                prods = json.loads(row["last_products_json"]) if row["last_products_json"] else []
                return {
                    "last_disease": row["last_disease"],
                    "last_products": prods,
                    "updated_at": row["updated_at"]
                }
        return {}

    def clear_session(self, session_id: str) -> bool:
        """Clear memory for a given session."""
        if not session_id:
            return False

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            return True

    def get_all_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List active sessions sorted by recency."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.session_id, s.title, s.created_at, s.updated_at, s.last_disease,
                       COUNT(m.id) as message_count
                FROM sessions s
                LEFT JOIN messages m ON s.session_id = m.session_id
                GROUP BY s.session_id
                ORDER BY s.updated_at DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
