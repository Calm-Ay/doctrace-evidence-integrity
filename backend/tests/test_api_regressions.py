import hashlib
from concurrent.futures import ThreadPoolExecutor
import pymupdf
import pytest
from fastapi.testclient import TestClient
from api import app
from doctrace.evidence.storage import EvidenceDB
from doctrace.evidence.custody import generate_id
from doctrace.evidence.custody import log_event

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('DOCTRACE_DB', str(tmp_path / 'test.db'))
    monkeypatch.setenv('DOCTRACE_OUTPUT_DIR', str(tmp_path / 'stamped'))
    with TestClient(app) as client:
        yield client

def intake(client, payload=b'synthetic evidence', filename='evidence.txt'):
    response = client.post('/api/evidence/intake', files={'file':(filename,payload)}, data={'collector_id':'DEMO-A','case_id':'CASE-DEMO','notes':'synthetic only'})
    assert response.status_code == 200, response.text
    return response.json()['evidence']['evidence_id']

def pdf():
    with pymupdf.open() as document:
        page = document.new_page()
        page.insert_text((72,72), 'Synthetic Doctrace demonstration only')
        return document.tobytes()

def test_demo_intake_transfer_match_mismatch_report(client):
    evidence_id = intake(client)
    detail = client.get(f'/api/evidence/{evidence_id}').json()
    assert detail['original_filename'] == 'evidence.txt'
    assert detail['notes'] == 'synthetic only'
    assert detail['events'][0]['event_type'] == 'COLLECTED'
    assert detail['status'] == 'REGISTERED'
    response = client.post(f'/api/evidence/{evidence_id}/custody', json={'action':'TRANSFERRED','actor_id':'DEMO-A','recipient_id':'DEMO-B'})
    assert response.status_code == 200
    for content, expected in [(b'synthetic evidence','MATCH'),(b'synthetic evidence changed','MISMATCH')]:
        result = client.post(f'/api/evidence/{evidence_id}/verify', files={'file':('copy.txt',content)}).json()
        assert result['evidence_result'] == expected
        assert result['chain_result'] == 'VALID'
        assert result['actual_hash'] == hashlib.sha256(content).hexdigest()
    detail = client.get(f'/api/evidence/{evidence_id}').json()
    assert detail['current_custodian'] == 'DEMO-B'
    assert detail['status'] == 'MISMATCH'
    assert len(detail['events']) == 2
    report = client.get(f'/api/evidence/{evidence_id}/report').json()['report']
    assert evidence_id in report and 'MISMATCH' in report and 'TRANSFERRED' in report
    assert client.get('/api/cases').json()[0]['evidenceCount'] == 1

@pytest.mark.parametrize('damage', ['notes', 'missing', 'hash'])
def test_corrupted_chain_does_not_crash_or_change_file_result(client, damage):
    evidence_id = intake(client)
    with EvidenceDB()._get_connection() as conn:
        if damage == 'missing': conn.execute('DELETE FROM custody_events')
        elif damage == 'notes': conn.execute("UPDATE custody_events SET notes='tampered'")
        else: conn.execute("UPDATE custody_events SET evidence_hash='tampered'")
    response = client.post(f'/api/evidence/{evidence_id}/verify', files={'file':('original.txt',b'synthetic evidence')})
    assert response.status_code == 200, response.text
    assert response.json()['evidence_result'] == 'MATCH'
    assert response.json()['chain_result'] == 'INVALID'
    assert client.get('/api/evidence').json()[0]['chain_status'] == 'INVALID'

def test_missing_evidence_is_404(client):
    assert client.get('/api/evidence/missing').status_code == 404
    assert client.get('/api/evidence/missing/report').status_code == 404
    assert client.post('/api/evidence/missing/verify', files={'file':('a',b'x')}).status_code == 404
    assert client.post('/api/evidence/missing/custody', json={'action':'TRANSFERRED','actor_id':'a','recipient_id':'b'}).status_code == 404

def test_custody_validation(client):
    evidence_id = intake(client)
    for data in [{'action':'NONSENSE','actor_id':'a'}, {'action':'TRANSFERRED','actor_id':'a'}, {'action':'ACCESSED'}]:
        assert client.post(f'/api/evidence/{evidence_id}/custody', json=data).status_code == 400

def test_filename_cannot_control_temp_path(client):
    evidence_id = intake(client, filename='../../synthetic.txt')
    assert client.get(f'/api/evidence/{evidence_id}').status_code == 200

def test_stamp_download_verify_repeat_and_registry(client):
    original = pdf()
    copies = []
    for recipient in ['DEMO-1','DEMO-1','DEMO-2']:
        response = client.post('/api/provenance/stamp', files={'file':('demo.pdf',original)}, data={'recipient_id':recipient})
        assert response.status_code == 200, response.text
        result = response.json()
        download = client.get(result['download_url'])
        assert download.status_code == 200 and download.content.startswith(b'%PDF')
        copies.append((recipient,download.content,result['copy_id']))
    assert copies[0][2] == copies[1][2] != copies[2][2]
    for recipient, content, copy_id in copies:
        result = client.post('/api/provenance/verify', files={'file':('copy.pdf',content)}).json()
        assert result['status'] == 'VERIFIED'
        assert result['recipient'] == recipient and result['copy_id'] == copy_id
    assert len(client.get('/api/provenance/registry').json()) == 2
    assert client.post('/api/provenance/stamp', files={'file':('stamped.pdf',copies[0][1])}, data={'recipient_id':'DEMO-3'}).status_code == 400
    assert client.post('/api/provenance/verify', files={'file':('original.pdf',original)}).json()['status'] == 'NO_WATERMARK'

@pytest.mark.parametrize('endpoint', ['stamp','verify'])
def test_invalid_pdf_is_client_error(client, endpoint):
    response = client.post(f'/api/provenance/{endpoint}', files={'file':('bad.pdf',b'not a PDF')}, data={'recipient_id':'DEMO'})
    assert response.status_code == 400, response.text

def test_unavailable_features_do_not_fake_success(client):
    intake(client)
    before = client.get('/api/sync/status').json()
    assert client.post('/api/sync').status_code == 501
    assert client.get('/api/sync/status').json() == before
    assert client.post('/api/provenance/identify', files={'file':('photo.png',b'image')}).status_code == 501

def test_identifiers_do_not_collide():
    with ThreadPoolExecutor(max_workers=8) as pool:
        ids = list(pool.map(lambda _: generate_id('EV'), range(10000)))
    assert len(set(ids)) == len(ids)

def test_concurrent_custody_events_form_one_chain(client):
    evidence_id = intake(client)
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda n: log_event(evidence_id, 'ACCESSED', None, actor_id=f'DEMO-{n}'), range(20)))
    detail = client.get(f'/api/evidence/{evidence_id}').json()
    assert detail['chain_status'] == 'VALID'
    assert len(detail['events']) == 21

def test_reject_append_to_corrupted_chain(client):
    evidence_id = intake(client)
    with EvidenceDB()._get_connection() as conn:
        conn.execute("UPDATE custody_events SET notes='tampered'")
    assert client.post(f'/api/evidence/{evidence_id}/custody', json={'action':'ACCESSED','actor_id':'DEMO'}).status_code == 409
