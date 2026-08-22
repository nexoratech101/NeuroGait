import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client.js";

export default function UploadAssessment() {
  const navigate = useNavigate();
  const [files, setFiles] = useState([]);
  const [testType, setTestType] = useState("10m walk");
  const [uploadResult, setUploadResult] = useState(null);
  const [newPatientName, setNewPatientName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const doUpload = async () => {
    if (files.length === 0) return;
    setBusy(true);
    setError(null);
    try {
      const formData = new FormData();
      files.forEach((f) => formData.append("files", f));
      formData.append("test_type", testType);
      const res = await api.uploadSession(formData);
      setUploadResult(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const associateAndAnalyze = async () => {
    if (!uploadResult) return;
    setBusy(true);
    setError(null);
    try {
      await api.associateSession(uploadResult.session_id, {
        new_patient: { full_name: newPatientName },
      });
      navigate(`/sessions/${uploadResult.session_id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <h2>Upload Assessment</h2>
      <div className="card">
        <p>Select 1-3 sensor files (ankle / thigh / hip). Files with the <code>PAT-..._SES-..._POS-..._DEV-...</code>
           naming convention are matched automatically; legacy files with no metadata will prompt for manual patient association.</p>
        <input type="file" multiple accept=".csv" onChange={(e) => setFiles(Array.from(e.target.files))} />
        <div style={{ marginTop: 10 }}>
          <label style={{ fontSize: 12, color: "#666" }}>Test type</label><br />
          <input value={testType} onChange={(e) => setTestType(e.target.value)} style={{ padding: 6 }} />
        </div>
        <button className="primary" style={{ marginTop: 12 }} disabled={busy || files.length === 0} onClick={doUpload}>
          {busy ? "Uploading..." : "Upload & Validate"}
        </button>
        {error && <p style={{ color: "crimson" }}>{error}</p>}
      </div>

      {uploadResult && (
        <div className="card">
          <h3>Validation Checklist</h3>
          <table>
            <thead><tr><th>File</th><th>Valid</th><th>Detected position</th><th>Association</th></tr></thead>
            <tbody>
              {uploadResult.files.map((f, i) => (
                <tr key={i}>
                  <td>{f.filename}</td>
                  <td>{f.valid ? "✓" : `✗ ${f.errors.join("; ")}`}</td>
                  <td>{f.detected_position || "unknown"}</td>
                  <td>{f.association_reason}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {uploadResult.needs_association ? (
            <div style={{ marginTop: 14 }}>
              <p className="badge-warning">
                {uploadResult.legacy_no_metadata
                  ? "No filename metadata detected -- this looks like a legacy upload. Select or create a patient to continue."
                  : "Could not automatically match a patient. Select or create a patient to continue."}
              </p>
              <label style={{ fontSize: 12, color: "#666" }}>New patient full name</label><br />
              <input value={newPatientName} onChange={(e) => setNewPatientName(e.target.value)} style={{ padding: 6, width: 260 }} />
              <br />
              <button className="primary" style={{ marginTop: 10 }} disabled={busy || !newPatientName} onClick={associateAndAnalyze}>
                Create Patient & Start Analysis
              </button>
            </div>
          ) : (
            <div style={{ marginTop: 14 }}>
              <p>Patient matched automatically. Analysis starting...</p>
              <button className="primary" onClick={() => navigate(`/sessions/${uploadResult.session_id}`)}>
                View Session
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
