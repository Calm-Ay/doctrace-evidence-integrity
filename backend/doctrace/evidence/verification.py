import os
from datetime import datetime, timezone
from uuid import uuid4
from typing import Dict, Any, Tuple
from doctrace.evidence.storage import EvidenceDB
from doctrace.evidence.hashing import stream_hash

def check_chain(events, original_hash):
    """Check recorded links independently of the file being verified."""
    from doctrace.evidence.models import CustodyEvent
    if not events or events[0]['event_type'] != 'COLLECTED':
        return 'INVALID'
    previous = None
    for row in events:
        event = CustodyEvent(**{k: v for k, v in row.items() if k != 'id'})
        if (event.compute_hash() != event.event_hash or
                event.previous_event_hash != previous or event.evidence_hash != original_hash):
            return 'INVALID'
        previous = event.event_hash
    return 'VALID'

def verify_evidence(filepath: str, evidence_id: str, db_path: str) -> Dict[str, Any]:
    if not db_path:
        db_path = os.getenv("DOCTRACE_DB", "doctrace.db")
    db = EvidenceDB(db_path)
    
    with db._get_connection() as conn:
        evidence = conn.execute("SELECT original_hash FROM evidence WHERE evidence_id=?", (evidence_id,)).fetchone()
        cursor = conn.execute("SELECT * FROM custody_events WHERE evidence_id = ? ORDER BY id ASC", (evidence_id,))
        events = [dict(row) for row in cursor.fetchall()]
        
    if not evidence:
        return {
            "evidence_result": "NOT_FOUND",
            "chain_result": "INVALID",
            "message": f"No custody events found for evidence {evidence_id}",
            "expected_hash": None,
            "actual_hash": None
        }
        
    expected_hash = evidence['original_hash']
    chain_result = check_chain(events, expected_hash)
    
    # Walk the chain to verify hashes

    # Verify file integrity
    actual_hash = None
    if os.path.exists(filepath):
        actual_hash = stream_hash(filepath)
        
    if actual_hash and actual_hash == expected_hash:
        evidence_result = "MATCH"
    else:
        evidence_result = "MISMATCH"
        
    result = {
        "evidence_result": evidence_result,
        "chain_result": chain_result,
        "expected_hash": expected_hash,
        "actual_hash": actual_hash,
        "events": events
    }
    now = datetime.now(timezone.utc).isoformat()
    db.insert_verification_event({
        "verification_id": f"VER-{uuid4().hex[:12].upper()}",
        "evidence_id": evidence_id,
        "timestamp": now,
        "actor_id": None,
        "device_id": None,
        "expected_hash": expected_hash,
        "observed_hash": actual_hash or "",
        "evidence_result": evidence_result,
        "chain_result": chain_result,
        "created_at": now,
    })
    return result
