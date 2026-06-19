const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

export async function fetchDocuments() {
  const res = await fetch(`${API_BASE}/documents`);
  if (!res.ok) throw new Error("Failed to fetch documents.");
  return res.json();
}

export async function deleteDocument(docId) {
  const res = await fetch(`${API_BASE}/documents/${docId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete document.");
  return res.json();
}

export async function uploadDocuments(files) {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }

  const res = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to upload documents.");
  return res.json();
}

export async function askQuestion(query, docIds = null) {
  const res = await fetch(`${API_BASE}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, doc_ids: docIds }),
  });
  if (!res.ok) throw new Error("Failed to process question.");
  return res.json();
}

export async function fetchRisks(docId = null, severity = null) {
  const params = new URLSearchParams();
  if (docId) params.append("doc_id", docId);
  if (severity) params.append("severity", severity);

  const res = await fetch(`${API_BASE}/risks?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch risks.");
  return res.json();
}

export async function detectRisk(text = null, docId = null) {
  const res = await fetch(`${API_BASE}/detect-risk`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, doc_id: docId }),
  });
  if (!res.ok) throw new Error("Failed to run risk detection.");
  return res.json();
}

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error("Failed to fetch health status.");
  return res.json();
}
