import os

def generate_report(evidence_id: str, db_path: str, out_path: str = None) -> str:
    if not db_path:
        db_path = os.getenv("DOCTRACE_DB", "doctrace.db")
    from doctrace.evidence.storage import EvidenceDB
    db = EvidenceDB(db_path)
    
    with db._get_connection() as conn:
        cursor = conn.execute("SELECT * FROM evidence WHERE evidence_id = ?", (evidence_id,))
        ev_row = cursor.fetchone()
        if not ev_row:
            raise ValueError(f"Evidence {evidence_id} not found.")
        evidence = dict(ev_row)
        
        cursor = conn.execute("SELECT * FROM custody_events WHERE evidence_id = ? ORDER BY id ASC", (evidence_id,))
        events = [dict(row) for row in cursor.fetchall()]
        cursor = conn.execute("SELECT * FROM verification_events WHERE evidence_id = ? ORDER BY id DESC LIMIT 1", (evidence_id,))
        verification_row = cursor.fetchone()
        verification = dict(verification_row) if verification_row else None
        
    report = []
    report.append("DOCTRACE EVIDENCE INTEGRITY REPORT")
    report.append("=" * 40)
    report.append(f"\nCase: {evidence.get('case_id') or 'N/A'}")
    report.append(f"Evidence ID: {evidence_id}")
    report.append(f"File: {evidence['original_filename']}")
    report.append(f"Collected: {evidence['collection_timestamp']} by {evidence.get('collector_id') or 'Unknown'} on {evidence.get('collection_device_id') or 'Unknown'}")
    
    report.append(f"\nIntegrity Result: {verification['evidence_result'] if verification else 'PENDING VERIFICATION'}")
    report.append(f"Original fingerprint: {evidence['original_hash']}")
    from doctrace.evidence.verification import check_chain
    report.append(f"Current custody-chain check: {check_chain(events, evidence['original_hash'])}")
    if verification:
        report.append(f"Current fingerprint: {verification['observed_hash']}")
        report.append(f"Custody chain at last file verification: {verification['chain_result']}")
        report.append(f"Verified: {verification['timestamp']}")
    
    report.append("\nCustody Timeline:")
    for e in events:
        actor = e.get('actor_id') or "Unknown"
        recipient = e.get('recipient_id')
        action = e['event_type']
        ts = e['timestamp']
        if recipient:
            report.append(f"{ts}  {action} by {actor} to {recipient}")
        else:
            report.append(f"{ts}  {action} by {actor}")
            
    report.append("\nFinal Finding:")
    report.append("This report lists the registered custody history.")
    report.append("The system uses cryptographic fingerprints to track changes.")
    report.append("To mathematically verify that the file currently presented matches this registered history, please run `doctrace evidence verify`.")
    
    report.append("\n" + "-" * 40)
    report.append("Technical Appendix:")
    report.append(f"Hash Algorithm: {evidence['hash_algorithm']}")
    report.append("Cryptographic Ledger:")
    for e in events:
        report.append(f"Event: {e['event_id']}")
        report.append(f"  Prev Hash: {e.get('previous_event_hash') or 'None'}")
        report.append(f"  Event Hash: {e['event_hash']}")
        
    output = "\n".join(report)
    
    if out_path:
        with open(out_path, 'w') as f:
            f.write(output)
    return output
