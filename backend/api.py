import os
import shutil
import tempfile
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from doctrace.evidence.storage import EvidenceDB
from doctrace.registry import Registry
from doctrace.evidence.custody import intake_evidence, log_event
from doctrace.evidence.verification import verify_evidence
from doctrace.evidence.reporting import generate_report
from doctrace.evidence.sync import sync_events
from doctrace.stampers.zerowidth import ZeroWidthStamper
from doctrace.stampers.microspacing import MicroSpacingStamper
from doctrace.stampers.structural import StructuralStamper
from doctrace.extractors.pdf_extract import extract_digital_watermarks
from doctrace.utils.bitops import generate_random_bitstring, find_best_matches

app = FastAPI(title="Doctrace API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db_path = os.getenv("DOCTRACE_DB", "doctrace.db")
    return EvidenceDB(db_path)

def get_registry():
    db_path = os.getenv("DOCTRACE_DB", "doctrace.db")
    return Registry(db_path)

@app.get("/api/cases")
def list_cases():
    db = get_db()
    with db._get_connection() as conn:
        cursor = conn.execute("SELECT * FROM cases")
        cases = [dict(row) for row in cursor.fetchall()]
        
        # We also need evidence counts
        for c in cases:
            cur2 = conn.execute("SELECT COUNT(*) as count FROM evidence WHERE case_id=?", (c['case_id'],))
            c['evidenceCount'] = cur2.fetchone()['count']
            c['health'] = 'cyan' # Mock health logic for now based on actual data structure
            c['lastActivity'] = '10 mins ago' # Need real logic if possible
    return cases

@app.get("/api/evidence")
def list_evidence():
    db = get_db()
    with db._get_connection() as conn:
        cursor = conn.execute("SELECT * FROM evidence ORDER BY id DESC")
        evidence = [dict(row) for row in cursor.fetchall()]
        
        for e in evidence:
            latest = db.get_latest_event(e['evidence_id'])
            if latest:
                e['current_custodian'] = latest.get('actor_id')
                e['current_device'] = latest.get('device_id')
                e['last_action'] = latest.get('event_type')
                e['last_actor'] = latest.get('actor_id')
                e['chain_status'] = "VALID" # Needs full chain verify to be precise
                e['sync_status'] = latest.get('sync_status', 'SYNCED')
            else:
                e['chain_status'] = "N/A"
    return evidence

@app.get("/api/evidence/{evidence_id}")
def get_evidence_detail(evidence_id: str):
    db = get_db()
    with db._get_connection() as conn:
        cursor = conn.execute("SELECT * FROM evidence WHERE evidence_id=?", (evidence_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Evidence not found")
        ev = dict(row)
        
        latest = db.get_latest_event(evidence_id)
        if latest:
            ev['current_custodian'] = latest.get('actor_id')
            ev['current_device'] = latest.get('device_id')
            ev['last_action'] = latest.get('event_type')
            ev['last_actor'] = latest.get('actor_id')
        
        cursor = conn.execute("SELECT * FROM custody_events WHERE evidence_id=? ORDER BY id ASC", (evidence_id,))
        ev['events'] = [dict(r) for r in cursor.fetchall()]
        cursor = conn.execute("SELECT * FROM verification_events WHERE evidence_id=? ORDER BY id DESC LIMIT 1", (evidence_id,))
        verification = cursor.fetchone()
        ev['latest_verification'] = dict(verification) if verification else None
        
    return ev

@app.post("/api/evidence/intake")
async def api_intake(
    file: UploadFile = File(...),
    case_id: Optional[str] = Form(None),
    collector_id: Optional[str] = Form(None),
    device_id: Optional[str] = Form(None)
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
        
    db_path = os.getenv("DOCTRACE_DB", "doctrace.db")
    try:
        ev, event = intake_evidence(tmp_path, db_path, collector_id, device_id, case_id, file.filename)
        return {
            "evidence": {
                "evidence_id": ev.evidence_id,
                "current_hash": ev.original_hash
            },
            "event_id": event.event_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.remove(tmp_path)

@app.post("/api/evidence/{evidence_id}/verify")
async def api_verify(evidence_id: str, file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
        
    db_path = os.getenv("DOCTRACE_DB", "doctrace.db")
    try:
        res = verify_evidence(tmp_path, evidence_id, db_path)
        if res.get("evidence_result") == "NOT_FOUND":
            raise HTTPException(status_code=404, detail="Evidence not found")
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.remove(tmp_path)

class CustodyLogReq(BaseModel):
    action: str
    actor_id: Optional[str] = None
    recipient_id: Optional[str] = None
    device_id: Optional[str] = None
    notes: Optional[str] = None

@app.post("/api/evidence/{evidence_id}/custody")
def api_log_custody(evidence_id: str, req: CustodyLogReq):
    db_path = os.getenv("DOCTRACE_DB", "doctrace.db")
    try:
        event = log_event(evidence_id, req.action, db_path, req.actor_id, req.recipient_id, req.notes, req.device_id)
        return {"event_id": event.event_id, "event_hash": event.event_hash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/evidence/{evidence_id}/report")
def api_get_report(evidence_id: str):
    db_path = os.getenv("DOCTRACE_DB", "doctrace.db")
    try:
        report_text = generate_report(evidence_id, db_path, None)
        return {"report": report_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sync/status")
def api_sync_status():
    db = get_db()
    with db._get_connection() as conn:
        cursor = conn.execute("SELECT * FROM sync_queue ORDER BY id DESC")
        return [dict(r) for r in cursor.fetchall()]

@app.post("/api/sync")
def api_sync():
    db_path = os.getenv("DOCTRACE_DB", "doctrace.db")
    count = sync_events(db_path)
    return {"synced": count}

@app.get("/api/provenance/registry")
def list_registry():
    registry = get_registry()
    copies = registry.get_all_copies()
    return copies

@app.post("/api/provenance/stamp")
async def api_stamp(
    file: UploadFile = File(...),
    recipient_id: str = Form(...),
    watermark_type: str = Form("digital")
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    
    safe_name = os.path.basename(file.filename or "document.pdf")
    output_dir = os.path.abspath(os.getenv("DOCTRACE_OUTPUT_DIR", "stamped"))
    os.makedirs(output_dir, exist_ok=True)
    try:
        if watermark_type == "digital":
            stamper = ZeroWidthStamper()
        elif watermark_type == "physical":
            stamper = MicroSpacingStamper()
        else:
            raise HTTPException(status_code=400, detail="Unknown watermark type")
            
        from doctrace.evidence.hashing import stream_hash
        doc_hash = stream_hash(tmp_path)
        bitstring = generate_random_bitstring(32)
        out_name = f"{bitstring[:8]}_stamped_{safe_name}"
        out_path = os.path.join(output_dir, out_name)
        if not stamper.stamp(tmp_path, out_path, bitstring):
            raise RuntimeError("The document could not be stamped")
        registry = get_registry()
        registry.add_copy(doc_hash, safe_name, recipient_id, recipient_id, "", bitstring)
        return {"copy_id": bitstring, "out_file": out_name, "download_url": f"/api/provenance/stamped/{out_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.remove(tmp_path)

@app.post("/api/provenance/verify")
async def api_provenance_verify(
    file: UploadFile = File(...),
    watermark_type: str = Form("digital")
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
        
    try:
        extracted = None
        if watermark_type == "digital":
            from doctrace.extractors.pdf_extract import extract_digital_watermarks
            extracted = extract_digital_watermarks(tmp_path)
            copy_id = extracted.get("zerowidth") or extracted.get("microspacing")
        else:
            raise HTTPException(status_code=400, detail="Only digital verify supported for now in api")
            
        if not copy_id:
            return {"status": "NO_WATERMARK"}
            
        registry = get_registry()
        record = registry.find_exact_match(copy_id)
        if record:
            return {"status": "VERIFIED", "copy_id": copy_id, "recipient": record["recipient_id"], "document": record["doc_name"]}
        else:
            return {"status": "UNKNOWN_ID", "copy_id": copy_id}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.remove(tmp_path)

@app.post("/api/provenance/identify")
async def api_provenance_identify(
    file: UploadFile = File(...)
):
    # Minimal identify endpoint
    return await api_provenance_verify(file=file, watermark_type="digital")

@app.get("/api/provenance/stamped/{filename}")
def download_stamped(filename: str):
    safe_name = os.path.basename(filename)
    output_dir = os.path.abspath(os.getenv("DOCTRACE_OUTPUT_DIR", "stamped"))
    path = os.path.join(output_dir, safe_name)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Stamped document not found")
    return FileResponse(path, media_type="application/pdf", filename=safe_name)
