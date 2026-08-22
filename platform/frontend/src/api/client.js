const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

function authHeaders() {
  const token = localStorage.getItem("neurogait_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(path, options = {}) {
  const resp = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(options.body && !(options.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
      ...authHeaders(),
      ...(options.headers || {}),
    },
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || `Request failed: ${resp.status}`);
  }
  if (resp.status === 204) return null;
  return resp.json();
}

export const api = {
  login: (email, password) =>
    request("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  listPatients: (q = "") => request(`/patients?q=${encodeURIComponent(q)}`),
  createPatient: (payload) => request("/patients", { method: "POST", body: JSON.stringify(payload) }),
  getPatient: (id) => request(`/patients/${id}`),
  updatePatient: (id, payload) => request(`/patients/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  listPatientSessions: (id) => request(`/patients/${id}/sessions`),
  getPatientTrend: (id) => request(`/patients/${id}/trend`),
  uploadSession: (formData) => request("/sessions/upload", { method: "POST", body: formData }),
  associateSession: (id, payload) =>
    request(`/sessions/${id}/associate`, { method: "POST", body: JSON.stringify(payload) }),
  getSession: (id) => request(`/sessions/${id}`),
  getSessionStatus: (id) => request(`/sessions/${id}/status`),
  getAnalysis: (id) => request(`/sessions/${id}/analysis`),
  getQuality: (id) => request(`/sessions/${id}/quality`),
  getRaw: (sessionId, recordingId) => request(`/sessions/${sessionId}/raw/${recordingId}`),
  listNotes: (id) => request(`/sessions/${id}/notes`),
  createNote: (id, payload) => request(`/sessions/${id}/notes`, { method: "POST", body: JSON.stringify(payload) }),
  generateReport: (id) => request(`/sessions/${id}/report`, { method: "POST" }),
  getReport: (id) => request(`/sessions/${id}/report`),
  reportDownloadUrl: (id) => `${API_BASE}/sessions/${id}/report/download`,
};
