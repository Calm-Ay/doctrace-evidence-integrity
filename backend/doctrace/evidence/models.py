import json
from dataclasses import dataclass, asdict
from typing import Optional

def canonical_json(data: dict) -> bytes:
    """Returns deterministic JSON bytes for cryptographic hashing."""
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")

@dataclass
class Evidence:
    evidence_id: str
    original_filename: str
    file_size: int
    original_hash: str
    collection_timestamp: str
    created_at: str
    updated_at: str
    status: str = 'REGISTERED'
    case_id: Optional[str] = None
    stored_path: Optional[str] = None
    mime_type: Optional[str] = None
    hash_algorithm: str = 'SHA-256'
    collector_id: Optional[str] = None
    collection_device_id: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None

@dataclass
class CustodyEvent:
    event_id: str
    evidence_id: str
    event_type: str
    timestamp: str
    event_hash: str
    created_at: str
    actor_id: Optional[str] = None
    device_id: Optional[str] = None
    recipient_id: Optional[str] = None
    notes: Optional[str] = None
    evidence_hash: Optional[str] = None
    previous_event_hash: Optional[str] = None
    sync_status: str = 'LOCAL'
    
    def compute_hash(self) -> str:
        import hashlib
        # We must exclude event_hash from the payload used to compute the event_hash
        d = asdict(self)
        d.pop('event_hash', None)
        d.pop('sync_status', None) # sync status is a local transmission state, not part of the core immutable ledger
        # d.pop('id', None) # id is not in the dataclass anyway
        payload = canonical_json(d)
        return hashlib.sha256(payload).hexdigest()
