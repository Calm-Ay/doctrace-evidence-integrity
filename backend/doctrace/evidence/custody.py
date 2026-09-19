import os
import time
from datetime import datetime, timezone
from typing import Optional, Tuple
from doctrace.evidence.models import Evidence, CustodyEvent
from doctrace.evidence.storage import EvidenceDB
from doctrace.evidence.hashing import stream_hash

def generate_id(prefix: str) -> str:
    """Generates an ID like EV-2026-123456"""
    year = datetime.now(timezone.utc).strftime("%Y")
    # unique suffix using timestamp
    unique_suffix = f"{int(time.time() * 1000) % 1000000:06d}"
    return f"{prefix}-{year}-{unique_suffix}"

def intake_evidence(filepath: str, db_path: str, collector_id: Optional[str] = None,
                   device_id: Optional[str] = None, case_id: Optional[str] = None,
                   original_filename: Optional[str] = None) -> Tuple[Evidence, CustodyEvent]:
    db = EvidenceDB(db_path)
    
    file_size = os.path.getsize(filepath)
    file_hash = stream_hash(filepath)
    
    now = datetime.now(timezone.utc).isoformat()
    evidence_id = generate_id("EV")
    
    evidence = Evidence(
        evidence_id=evidence_id,
        original_filename=original_filename or os.path.basename(filepath),
        file_size=file_size,
        original_hash=file_hash,
        collection_timestamp=now,
        created_at=now,
        updated_at=now,
        case_id=case_id,
        collector_id=collector_id,
        collection_device_id=device_id
    )
    
    import dataclasses
    db.insert_evidence(dataclasses.asdict(evidence))
    
    # First custody event
    event = CustodyEvent(
        event_id=generate_id("EVT"),
        evidence_id=evidence_id,
        event_type="COLLECTED",
        timestamp=now,
        created_at=now,
        actor_id=collector_id,
        device_id=device_id,
        evidence_hash=file_hash,
        previous_event_hash=None,
        event_hash=""
    )
    event.event_hash = event.compute_hash()
    db.insert_custody_event(dataclasses.asdict(event))
    
    # Stub sync queue entry
    with db._get_connection() as conn:
        import json
        conn.execute("INSERT INTO sync_queue (event_id, payload, created_at) VALUES (?, ?, ?)",
                     (event.event_id, json.dumps(dataclasses.asdict(event)), now))
        conn.commit()
    
    return evidence, event

def log_event(evidence_id: str, action: str, db_path: str, actor_id: Optional[str] = None,
              recipient_id: Optional[str] = None, notes: Optional[str] = None, 
              device_id: Optional[str] = None) -> CustodyEvent:
    db = EvidenceDB(db_path)
    latest_event = db.get_latest_event(evidence_id)
    if not latest_event:
        raise ValueError(f"Evidence {evidence_id} not found or no genesis event.")
    
    now = datetime.now(timezone.utc).isoformat()
    
    event = CustodyEvent(
        event_id=generate_id("EVT"),
        evidence_id=evidence_id,
        event_type=action,
        timestamp=now,
        created_at=now,
        actor_id=actor_id,
        device_id=device_id,
        recipient_id=recipient_id,
        notes=notes,
        evidence_hash=latest_event['evidence_hash'], # Assumed unchanged without specific verification
        previous_event_hash=latest_event['event_hash'],
        event_hash=""
    )
    event.event_hash = event.compute_hash()
    import dataclasses
    db.insert_custody_event(dataclasses.asdict(event))
    
    # Stub sync queue entry
    with db._get_connection() as conn:
        import json
        conn.execute("INSERT INTO sync_queue (event_id, payload, created_at) VALUES (?, ?, ?)",
                     (event.event_id, json.dumps(dataclasses.asdict(event)), now))
        conn.commit()
        
    return event
