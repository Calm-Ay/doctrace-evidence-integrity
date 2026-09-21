import os
import shutil
import tempfile
from uuid import uuid4
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from doctrace.evidence.storage import EvidenceDB
from doctrace.registry import Registry
from doctrace.evidence.custody import intake_evidence, log_event
from doctrace.evidence.verification import verify_evidence, check_chain
from doctrace.evidence.reporting import generate_report
from doctrace.stampers.zerowidth import ZeroWidthStamper
from doctrace.extractors.pdf_extract import extract_digital_watermarks
from doctrace.utils.bitops import generate_random_bitstring

app = FastAPI(title="Doctrace API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("DOCTRACE_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db_path = os.getenv("DOCTRACE_DB", "doctrace.db")
    return EvidenceDB(db_path)

def get_registry():
    db_path = os.getenv("DOCTRACE_DB", "doctrace.db")
    return Registry(db_path)

def enrich_evidence(ev, db):
    with db._get_connection() as conn:
        events = [dict(r) for r in conn.execute("SELECT * FROM custody_events WHERE evidence_id=? ORDER BY id", (ev['evidence_id'],))]
        row = conn.execute("SELECT * FROM verification_events WHERE evidence_id=? ORDER BY id DESC LIMIT 1", (ev['evidence_id'],)).fetchone()
    ev['events'] = events
    ev['latest_verification'] = dict(row) if row else None
    ev['status'] = row['evidence_result'] if row else 'REGISTERED'
    ev['current_hash'] = row['observed_hash'] if row else None
    ev['chain_status'] = check_chain(events, ev['original_hash'])
    ev['current_custodian'] = ev.get('collector_id')
    for event in events:
        if event['event_type'] == 'TRANSFERRED':
            ev['current_custodian'] = event['recipient_id']
    if events:
        latest = events[-1]
        ev.update(current_device=latest['device_id'], last_action=latest['event_type'],
                  last_actor=latest['actor_id'], sync_status=latest['sync_status'])
    return ev

def require_pdf(path):
    import pymupdf
    try:
        with pymupdf.open(path) as document:
            if not document.is_pdf or document.needs_pass or not len(document):
                raise ValueError()
    except Exception:
        raise HTTPException(400, 'Upload a valid, unencrypted PDF with at least one page')

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
            c['health'] = 'Not assessed'
            c['lastActivity'] = c['updated_at']
    return cases

@app.get("/api/evidence")
def list_evidence():
    db = get_db()
    with db._get_connection() as conn:
        cursor = conn.execute("SELECT * FROM evidence ORDER BY id DESC")
        evidence = [dict(row) for row in cursor.fetchall()]
        
    return [enrich_evidence(e, db) for e in evidence]

@app.get("/api/evidence/{evidence_id}")
def get_evidence_detail(evidence_id: str):
    db = get_db()
    with db._get_connection() as conn:
        cursor = conn.execute("SELECT * FROM evidence WHERE evidence_id=?", (evidence_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Evidence not found")
        ev = dict(row)
        
        
    return enrich_evidence(ev, db)

@app.post("/api/evidence/intake")
async def api_intake(
    file: UploadFile = File(...),
    case_id: Optional[str] = Form(None),
    collector_id: Optional[str] = Form(None),
    device_id: Optional[str] = Form(None),
    notes: Optional[str] = Form(None)
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".upload") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
        
    db_path = os.getenv("DOCTRACE_DB", "doctrace.db")
    try:
        ev, event = intake_evidence(tmp_path, db_path, collector_id, device_id, case_id, file.filename, notes)
        return {
            "evidence": {
                "evidence_id": ev.evidence_id,
                "original_filename": ev.original_filename,
                "current_hash": ev.original_hash
            },
            "event_id": event.event_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.remove(tmp_path)

@app.post("/api/evidence/{evidence_id}/verify")
async def api_verify(evidence_id: str, file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".upload") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
        
    db_path = os.getenv("DOCTRACE_DB", "doctrace.db")
    try:
        res = verify_evidence(tmp_path, evidence_id, db_path)
        if res.get("evidence_result") == "NOT_FOUND":
            raise HTTPException(status_code=404, detail="Evidence not found")
        return res
    except HTTPException:
        raise
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
    get_evidence_detail(evidence_id)
    if req.action not in {'TRANSFERRED', 'ACCESSED', 'STORED', 'RELEASED'}:
        raise HTTPException(400, 'Unsupported custody action')
    if not req.actor_id or not req.actor_id.strip():
        raise HTTPException(400, 'Actor is required')
    if req.action == 'TRANSFERRED' and not (req.recipient_id or '').strip():
        raise HTTPException(400, 'Recipient is required for a transfer')
    db_path = os.getenv("DOCTRACE_DB", "doctrace.db")
    try:
        event = log_event(evidence_id, req.action, db_path, req.actor_id, req.recipient_id, req.notes, req.device_id)
        return {"event_id": event.event_id, "event_hash": event.event_hash}
    except ValueError as e:
        raise HTTPException(409, str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/evidence/{evidence_id}/report")
def api_get_report(evidence_id: str):
    get_evidence_detail(evidence_id)
    db_path = os.getenv("DOCTRACE_DB", "doctrace.db")
    try:
        report_text = generate_report(evidence_id, db_path, None)
        return {"report": report_text}
    except HTTPException:
        raise
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
    raise HTTPException(501, 'Remote synchronization is not configured. Events remain local.')

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
    with tempfile.NamedTemporaryFile(delete=False, suffix=".upload") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    
    safe_name = os.path.basename(file.filename or "document.pdf")
    output_dir = os.path.abspath(os.getenv("DOCTRACE_OUTPUT_DIR", "stamped"))
    os.makedirs(output_dir, exist_ok=True)
    try:
        require_pdf(tmp_path)
        if not recipient_id.strip():
            raise HTTPException(400, 'Recipient ID is required')
        if extract_digital_watermarks(tmp_path).get('zerowidth'):
            raise HTTPException(400, 'This PDF already contains a watermark; use the original PDF')
        if watermark_type == "digital":
            stamper = ZeroWidthStamper()
        elif watermark_type == "physical":
            raise HTTPException(501, 'Physical watermarking is experimental and unavailable in this demo')
        else:
            raise HTTPException(status_code=400, detail="Unknown watermark type")
            
        from doctrace.evidence.hashing import stream_hash
        doc_hash = stream_hash(tmp_path)
        registry = get_registry()
        existing = next((r for r in registry.get_copies_by_doc(doc_hash) if r['recipient_id'] == recipient_id), None)
        bitstring = existing['bitstring'] if existing else generate_random_bitstring(128)
        out_name = f"{uuid4().hex}_stamped.pdf"
        out_path = os.path.join(output_dir, out_name)
        if not stamper.stamp(tmp_path, out_path, bitstring):
            raise RuntimeError("The document could not be stamped")
        if stamper.extract(out_path) != bitstring:
            os.remove(out_path)
            raise HTTPException(422, 'The PDF layout cannot preserve the complete watermark. Try a standard-size PDF.')
        registry = get_registry()
        if not existing:
            registry.add_copy(doc_hash, safe_name, recipient_id, recipient_id, "", bitstring)
        return {"copy_id": bitstring, "out_file": out_name, "download_url": f"/api/provenance/stamped/{out_name}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.remove(tmp_path)

@app.post("/api/provenance/verify")
async def api_provenance_verify(
    file: UploadFile = File(...),
    watermark_type: str = Form("digital")
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".upload") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
        
    try:
        require_pdf(tmp_path)
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
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.remove(tmp_path)

@app.post("/api/provenance/identify")
async def api_provenance_identify(
    file: UploadFile = File(...)
):
    raise HTTPException(501, 'Photo identification is experimental and not available in this demo. Use digital PDF verification.')

@app.get("/api/provenance/stamped/{filename}")
def download_stamped(filename: str):
    safe_name = os.path.basename(filename)
    output_dir = os.path.abspath(os.getenv("DOCTRACE_OUTPUT_DIR", "stamped"))
    path = os.path.join(output_dir, safe_name)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Stamped document not found")
    return FileResponse(path, media_type="application/pdf", filename=safe_name)
