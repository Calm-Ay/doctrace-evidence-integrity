import os
from datetime import datetime, timezone
from uuid import uuid4
from typing import Dict, Any, Tuple
from doctrace.evidence.storage import EvidenceDB
from doctrace.evidence.hashing import stream_hash

def verify_evidence(filepath: str, evidence_id: str, db_path: str) -> Dict[str, Any]:
    if not db_path:
        db_path = os.getenv("DOCTRACE_DB", "doctrace.db")
    db = EvidenceDB(db_path)
    
    with db._get_connection() as conn:
        cursor = conn.execute("SELECT * FROM custody_events WHERE evidence_id = ? ORDER BY id ASC", (evidence_id,))
        events = [dict(row) for row in cursor.fetchall()]
        
    if not events:
        return {
            "evidence_result": "NOT_FOUND",
            "chain_result": "INVALID",
            "message": f"No custody events found for evidence {evidence_id}",
            "expected_hash": None,
            "actual_hash": None
        }
        
    chain_result = "VALID"
    expected_hash = None
    
    # Walk the chain to verify hashes
    prev_hash = None
    for event_dict in events:
        from doctrace.evidence.models import CustodyEvent
        # Reconstruct event for hashing
        ev = CustodyEvent(**{k: v for k, v in event_dict.items() if k != 'id'})
        computed_hash = ev.compute_hash()
        
        if computed_hash != event_dict['event_hash']:
            chain_result = "INVALID"
            break
        if event_dict['previous_event_hash'] != prev_hash:
            chain_result = "INVALID"
            break
            
        prev_hash = computed_hash
        expected_hash = event_dict['evidence_hash']

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
