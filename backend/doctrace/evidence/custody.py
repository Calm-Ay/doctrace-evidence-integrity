import os
import json
from dataclasses import asdict
from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional, Tuple
from doctrace.evidence.models import Evidence, CustodyEvent
from doctrace.evidence.storage import EvidenceDB
from doctrace.evidence.hashing import stream_hash
from doctrace.evidence.verification import check_chain

def generate_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now(timezone.utc).year}-{uuid4().hex.upper()}"

def _insert(conn, table, record):
    keys = ', '.join(record)
    placeholders = ', '.join('?' for _ in record)
    conn.execute(f'INSERT INTO {table} ({keys}) VALUES ({placeholders})', list(record.values()))

def _record_event(conn, event):
    record = asdict(event)
    _insert(conn, 'custody_events', record)
    conn.execute('INSERT INTO sync_queue (event_id,payload,created_at) VALUES (?,?,?)',
                 (event.event_id, json.dumps(record), event.created_at))

def intake_evidence(filepath: str, db_path: str, collector_id: Optional[str] = None,
                    device_id: Optional[str] = None, case_id: Optional[str] = None,
                    original_filename: Optional[str] = None, notes: Optional[str] = None) -> Tuple[Evidence, CustodyEvent]:
    db = EvidenceDB(db_path)
    now = datetime.now(timezone.utc).isoformat()
    fingerprint = stream_hash(filepath)
    evidence = Evidence(evidence_id=generate_id('EV'),
        original_filename=os.path.basename((original_filename or filepath).replace('\\', '/')),
        file_size=os.path.getsize(filepath), original_hash=fingerprint,
        collection_timestamp=now, created_at=now, updated_at=now,
        case_id=case_id, collector_id=collector_id, collection_device_id=device_id, notes=notes)
    event = CustodyEvent(event_id=generate_id('EVT'), evidence_id=evidence.evidence_id,
        event_type='COLLECTED', timestamp=now, created_at=now, actor_id=collector_id,
        device_id=device_id, evidence_hash=fingerprint, previous_event_hash=None, event_hash='')
    event.event_hash = event.compute_hash()
    with db._get_connection() as conn:
        conn.execute('BEGIN IMMEDIATE')
        _insert(conn, 'evidence', asdict(evidence))
        _record_event(conn, event)
        if case_id:
            conn.execute('INSERT INTO cases (case_id,title,created_at,updated_at) VALUES (?,?,?,?) ON CONFLICT(case_id) DO UPDATE SET updated_at=excluded.updated_at', (case_id, case_id, now, now))
    return evidence, event

def log_event(evidence_id: str, action: str, db_path: str, actor_id: Optional[str] = None,
              recipient_id: Optional[str] = None, notes: Optional[str] = None,
              device_id: Optional[str] = None) -> CustodyEvent:
    if action not in {'TRANSFERRED', 'ACCESSED', 'STORED', 'RELEASED'}:
        raise ValueError('Unsupported custody action')
    if not (actor_id or '').strip():
        raise ValueError('Actor is required')
    if action == 'TRANSFERRED' and not (recipient_id or '').strip():
        raise ValueError('Recipient is required for a transfer')
    db = EvidenceDB(db_path)
    with db._get_connection() as conn:
        # Serialize chain append so concurrent requests cannot share the same parent.
        conn.execute('BEGIN IMMEDIATE')
        evidence = conn.execute('SELECT * FROM evidence WHERE evidence_id=?', (evidence_id,)).fetchone()
        if evidence is None:
            raise ValueError('Evidence not found')
        events = [dict(r) for r in conn.execute('SELECT * FROM custody_events WHERE evidence_id=? ORDER BY id', (evidence_id,))]
        if check_chain(events, evidence['original_hash']) != 'VALID':
            raise ValueError('Cannot append to an invalid custody chain')
        now = datetime.now(timezone.utc).isoformat()
        event = CustodyEvent(event_id=generate_id('EVT'), evidence_id=evidence_id,
            event_type=action, timestamp=now, created_at=now, actor_id=actor_id,
            device_id=device_id, recipient_id=recipient_id, notes=notes,
            evidence_hash=evidence['original_hash'], previous_event_hash=events[-1]['event_hash'], event_hash='')
        event.event_hash = event.compute_hash()
        _record_event(conn, event)
        conn.execute('UPDATE evidence SET updated_at=? WHERE evidence_id=?', (now, evidence_id))
        conn.execute('UPDATE cases SET updated_at=? WHERE case_id=?', (now, evidence['case_id']))
    return event
