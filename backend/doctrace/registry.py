import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple

DEFAULT_DB_NAME = "doctrace.db"

class Registry:
    def __init__(self, db_path: Optional[str] = None):
        """
        Initializes the SQLite database.
        If db_path is not specified, it defaults to the local 'doctrace.db' in the CWD.
        """
        if not db_path:
            db_path = os.getenv("DOCTRACE_DB", DEFAULT_DB_NAME)
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Creates the necessary schema if it does not exist."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS copies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_hash TEXT NOT NULL,
                    doc_name TEXT NOT NULL,
                    recipient_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    bitstring TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(doc_hash, recipient_id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_bitstring ON copies(bitstring)
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS layout_maps (
                    doc_hash TEXT PRIMARY KEY,
                    layout_json TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def add_copy(self, doc_hash: str, doc_name: str, recipient_id: str, name: str, email: str, bitstring: str):
        """Adds a new stamped copy to the registry."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO copies (doc_hash, doc_name, recipient_id, name, email, bitstring)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (doc_hash, doc_name, recipient_id, name, email, bitstring))
            conn.commit()

    def get_all_copies(self) -> List[Dict]:
        """Returns all registered copies."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM copies ORDER BY timestamp DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_copies_by_doc(self, doc_hash: str) -> List[Dict]:
        """Returns all copies stamped for a specific original document."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM copies WHERE doc_hash = ?", (doc_hash,))
            return [dict(row) for row in cursor.fetchall()]

    def find_exact_match(self, bitstring: str) -> Optional[Dict]:
        """Looks up a copy by exact bitstring."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM copies WHERE bitstring = ?", (bitstring,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def save_layout_map(self, doc_hash: str, layout_json: str):
        """Saves a document layout map for Layer 2 decoding."""
        secret = os.getenv("DOCTRACE_SECRET_KEY")
        if secret:
            from cryptography.fernet import Fernet
            try:
                f = Fernet(secret.encode())
                layout_json = f.encrypt(layout_json.encode()).decode()
            except Exception as e:
                raise ValueError(f"Failed to encrypt layout_map. Ensure DOCTRACE_SECRET_KEY is a valid Fernet key. Error: {e}")
                
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO layout_maps (doc_hash, layout_json)
                VALUES (?, ?)
            """, (doc_hash, layout_json))
            conn.commit()

    def get_layout_map(self, doc_hash: str) -> Optional[str]:
        """Retrieves a document layout map."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT layout_json FROM layout_maps WHERE doc_hash = ?", (doc_hash,))
            row = cursor.fetchone()
            
            if not row:
                return None
                
            layout_json = row['layout_json']
            
            # Backwards compatibility for plaintext JSON
            if layout_json.startswith('{') or layout_json.startswith('['):
                return layout_json
                
            # If it doesn't start with '{', it's encrypted
            secret = os.getenv("DOCTRACE_SECRET_KEY")
            if not secret:
                raise ValueError("CRITICAL: layout_map is encrypted but DOCTRACE_SECRET_KEY environment variable is not set. Cannot decrypt!")
                
            from cryptography.fernet import Fernet
            try:
                f = Fernet(secret.encode())
                return f.decrypt(layout_json.encode()).decode()
            except Exception as e:
                raise ValueError(f"CRITICAL: Failed to decrypt layout_map. The DOCTRACE_SECRET_KEY may be incorrect, changed, or lost. Data is unreadable! Error: {e}")
