import sqlite3
from typing import Dict, Optional
from doctrace.registry import Registry

class EvidenceDB(Registry):
    def _init_db(self):
        super()._init_db() # Call the original registry initialization to ensure copies/layout_maps exist
        
        with self._get_connection() as conn:
            # cases
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id TEXT UNIQUE NOT NULL,
                    title TEXT,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # evidence
            conn.execute("""
                CREATE TABLE IF NOT EXISTS evidence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    evidence_id TEXT UNIQUE NOT NULL,
                    case_id TEXT,
                    original_filename TEXT NOT NULL,
                    stored_path TEXT,
                    file_size INTEGER NOT NULL,
                    mime_type TEXT,
                    hash_algorithm TEXT NOT NULL DEFAULT 'SHA-256',
                    original_hash TEXT NOT NULL,
                    collector_id TEXT,
                    collection_device_id TEXT,
                    collection_timestamp TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'REGISTERED',
                    description TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # custody_events
            conn.execute("""
                CREATE TABLE IF NOT EXISTS custody_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    evidence_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    actor_id TEXT,
                    device_id TEXT,
                    recipient_id TEXT,
                    timestamp TEXT NOT NULL,
                    notes TEXT,
                    evidence_hash TEXT,
                    previous_event_hash TEXT,
                    event_hash TEXT NOT NULL,
                    sync_status TEXT DEFAULT 'LOCAL',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (evidence_id) REFERENCES evidence(evidence_id)
                )
            """)
            
            # verification_events
            conn.execute("""
                CREATE TABLE IF NOT EXISTS verification_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    verification_id TEXT UNIQUE NOT NULL,
                    evidence_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    actor_id TEXT,
                    device_id TEXT,
                    expected_hash TEXT NOT NULL,
                    observed_hash TEXT NOT NULL,
                    evidence_result TEXT NOT NULL,
                    chain_result TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            
            # actors
            conn.execute("""
                CREATE TABLE IF NOT EXISTS actors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    actor_id TEXT UNIQUE NOT NULL,
                    display_name TEXT,
                    role TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            
            # devices
            conn.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT UNIQUE NOT NULL,
                    display_name TEXT,
                    device_type TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            
            # sync_queue
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT DEFAULT 'PENDING',
                    created_at TEXT NOT NULL,
                    synced_at TEXT
                )
            """)
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_evidence_id ON custody_events(evidence_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_prev_hash ON custody_events(previous_event_hash)")
            conn.commit()

    def get_latest_event(self, evidence_id: str) -> Optional[Dict]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM custody_events WHERE evidence_id = ? ORDER BY id DESC LIMIT 1", (evidence_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
            
    def insert_evidence(self, ev_dict: Dict):
        with self._get_connection() as conn:
            keys = ", ".join(ev_dict.keys())
            placeholders = ", ".join(["?"] * len(ev_dict))
            conn.execute(f"INSERT INTO evidence ({keys}) VALUES ({placeholders})", list(ev_dict.values()))
            conn.commit()
            
    def insert_custody_event(self, event_dict: Dict):
        with self._get_connection() as conn:
            keys = ", ".join(event_dict.keys())
            placeholders = ", ".join(["?"] * len(event_dict))
            conn.execute(f"INSERT INTO custody_events ({keys}) VALUES ({placeholders})", list(event_dict.values()))
            conn.commit()

    def insert_verification_event(self, event_dict: Dict):
        with self._get_connection() as conn:
            keys = ", ".join(event_dict.keys())
            placeholders = ", ".join(["?"] * len(event_dict))
            conn.execute(f"INSERT INTO verification_events ({keys}) VALUES ({placeholders})", list(event_dict.values()))
            conn.commit()
