const API_BASE = "http://localhost:8000/api";

async function jsonOrThrow(res) {
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`);
  return data;
}

export async function fetchCases() {
  const res = await fetch(`${API_BASE}/cases`);
  return res.json();
}

export async function fetchEvidenceList() {
  const res = await fetch(`${API_BASE}/evidence`);
  return res.json();
}

export async function fetchEvidenceDetail(id) {
  const res = await fetch(`${API_BASE}/evidence/${id}`);
  return res.json();
}

export async function intakeEvidence(file, caseId, collectorId, deviceId) {
  const formData = new FormData();
  formData.append("file", file);
  if (caseId) formData.append("case_id", caseId);
  if (collectorId) formData.append("collector_id", collectorId);
  if (deviceId) formData.append("device_id", deviceId);
  
  const res = await fetch(`${API_BASE}/evidence/intake`, {
    method: "POST",
    body: formData
  });
  return res.json();
}

export async function verifyEvidence(id, file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/evidence/${id}/verify`, {
    method: "POST",
    body: formData
  });
  return res.json();
}

export async function logCustody(id, data) {
  const res = await fetch(`${API_BASE}/evidence/${id}/custody`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function getReport(id) {
  const res = await fetch(`${API_BASE}/evidence/${id}/report`);
  return res.json();
}

export async function fetchSyncStatus() {
  const res = await fetch(`${API_BASE}/sync/status`);
  return res.json();
}

export async function triggerSync() {
  const res = await fetch(`${API_BASE}/sync`, { method: "POST" });
  return res.json();
}

export async function fetchRegistry() {
  const res = await fetch(`${API_BASE}/provenance/registry`);
  return res.json();
}

export async function stampDocument(file, recipientId, type="digital") {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("recipient_id", recipientId);
  formData.append("watermark_type", type);
  const res = await fetch(`${API_BASE}/provenance/stamp`, {
    method: "POST",
    body: formData
  });
  return jsonOrThrow(res);
}

export async function verifyDigital(file) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("watermark_type", "digital");
  const res = await fetch(`${API_BASE}/provenance/verify`, {
    method: "POST",
    body: formData
  });
  return jsonOrThrow(res);
}

export function stampedDownloadUrl(path) {
  return path?.startsWith("http") ? path : `http://localhost:8000${path}`;
}

export async function identifyPhoto(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/provenance/identify`, {
    method: "POST",
    body: formData
  });
  return res.json();
}
