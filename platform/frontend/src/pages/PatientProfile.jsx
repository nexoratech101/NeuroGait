import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client.js";

const FIELDS = [
  ["full_name", "Full name", "text"],
  ["mobile_number", "Mobile number", "text"],
  ["dob", "Date of birth", "date"],
  ["sex", "Sex", "text"],
  ["ms_phenotype", "MS phenotype", "text"],
  ["year_of_diagnosis", "Year of diagnosis", "number"],
  ["mobility_status", "Mobility status", "text"],
  ["assistive_device", "Assistive device", "text"],
  ["edss_score", "EDSS score", "number"],
  ["edss_date", "EDSS date", "date"],
  ["notes", "Notes", "textarea"],
];

export default function PatientProfile() {
  const { patientId } = useParams();
  const [patient, setPatient] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [form, setForm] = useState({});
  const [saving, setSaving] = useState(false);

  const load = async () => {
    const p = await api.getPatient(patientId);
    setPatient(p);
    setForm(p);
    setSessions(await api.listPatientSessions(patientId));
  };

  useEffect(() => { load(); }, [patientId]);

  const save = async () => {
    setSaving(true);
    try {
      const updated = await api.updatePatient(patientId, form);
      setPatient(updated);
    } finally {
      setSaving(false);
    }
  };

  if (!patient) return <p>Loading...</p>;

  return (
    <div>
      <h2>{patient.full_name} <span style={{ fontSize: 14, color: "#888" }}>({patient.study_id})</span></h2>

      {!patient.consent_recorded && (
        <div className="notice">Consent not yet recorded for this patient (placeholder field -- no workflow enforcement in Phase 1).</div>
      )}

      <div className="card">
        <h3>Patient Information</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          {FIELDS.map(([key, label, type]) => (
            <div key={key}>
              <label style={{ fontSize: 12, color: "#666" }}>{label}</label>
              {type === "textarea" ? (
                <textarea
                  value={form[key] || ""}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                  style={{ width: "100%", padding: 6 }}
                />
              ) : (
                <input
                  type={type}
                  value={form[key] ?? ""}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                  style={{ width: "100%", padding: 6 }}
                />
              )}
            </div>
          ))}
        </div>
        <button className="primary" style={{ marginTop: 12 }} onClick={save} disabled={saving}>
          {saving ? "Saving..." : "Save changes"}
        </button>
      </div>

      <div className="card">
        <h3>Sessions</h3>
        <Link to={`/patients/${patientId}/trend`}>View trend across sessions →</Link>
        <table style={{ marginTop: 12 }}>
          <thead><tr><th>Date</th><th>Test type</th><th>Status</th></tr></thead>
          <tbody>
            {sessions.map((s) => (
              <tr key={s.session_id}>
                <td>{s.assessment_date?.slice(0, 10)}</td>
                <td>{s.test_type || "-"}</td>
                <td><Link to={`/sessions/${s.session_id}`}>{s.status}</Link></td>
              </tr>
            ))}
            {sessions.length === 0 && <tr><td colSpan={3}>No sessions yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
