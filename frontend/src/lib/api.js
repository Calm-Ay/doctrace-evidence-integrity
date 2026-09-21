const API_BASE = (import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api').replace(/\/$/, '');
async function request(path, options) {
  const res = await fetch(`${API_BASE}${path}`, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail) || `Request failed (${res.status})`);
  return data;
}
function upload(path, file, fields = {}) {
  const body = new FormData(); body.append('file', file);
  for (const [key, value] of Object.entries(fields)) if (value) body.append(key, value);
  return request(path, { method: 'POST', body });
}
export const fetchCases = () => request('/cases');
export const fetchEvidenceList = () => request('/evidence');
export const fetchEvidenceDetail = id => request(`/evidence/${encodeURIComponent(id)}`);
export const intakeEvidence = (file, caseId, collectorId, deviceId, notes) => upload('/evidence/intake', file, {case_id:caseId, collector_id:collectorId, device_id:deviceId, notes});
export const verifyEvidence = (id, file) => upload(`/evidence/${encodeURIComponent(id)}/verify`, file);
export const logCustody = (id, data) => request(`/evidence/${encodeURIComponent(id)}/custody`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
export const getReport = id => request(`/evidence/${encodeURIComponent(id)}/report`);
export const fetchSyncStatus = () => request('/sync/status');
export const triggerSync = () => request('/sync', {method:'POST'});
export const fetchRegistry = () => request('/provenance/registry');
export const stampDocument = (file, recipientId, type='digital') => upload('/provenance/stamp', file, {recipient_id:recipientId, watermark_type:type});
export const verifyDigital = file => upload('/provenance/verify', file, {watermark_type:'digital'});
export const identifyPhoto = file => upload('/provenance/identify', file);
export const stampedDownloadUrl = path => new URL(path, new URL(API_BASE, window.location.href)).href;
export function downloadText(text, filename, type='text/plain') {
  const url = URL.createObjectURL(new Blob([text], {type}));
  const link = document.createElement('a'); link.href = url; link.download = filename; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
