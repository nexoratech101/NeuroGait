import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client.js";

export default function Report() {
  const { sessionId } = useParams();
  const [report, setReport] = useState(null);
  const [busy, setBusy] = useState(false);
  const [pdfUrl, setPdfUrl] = useState(null);
  const [error, setError] = useState(null);

  const loadExisting = async () => {
    try {
      setReport(await api.getReport(sessionId));
    } catch {
      setReport(null);
    }
  };

  useEffect(() => { loadExisting(); }, [sessionId]);

  const generate = async () => {
    setBusy(true);
    setError(null);
    try {
      await api.generateReport(sessionId);
      await loadExisting();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const viewPdf = async () => {
    const token = localStorage.getItem("neurogait_token");
    const resp = await fetch(api.reportDownloadUrl(sessionId), {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!resp.ok) {
      setError("Could not load PDF");
      return;
    }
    const blob = await resp.blob();
    setPdfUrl(URL.createObjectURL(blob));
  };

  return (
    <div>
      <h2>Session Report</h2>
      <div className="card">
        {report ? (
          <>
            <p>Report generated: {report.generated_at?.slice(0, 16).replace("T", " ")}</p>
            <button className="primary" onClick={viewPdf}>View PDF</button>{" "}
            <button onClick={generate} disabled={busy}>{busy ? "Regenerating..." : "Regenerate Report"}</button>
          </>
        ) : (
          <button className="primary" onClick={generate} disabled={busy}>
            {busy ? "Generating..." : "Generate Report"}
          </button>
        )}
        {error && <p style={{ color: "crimson" }}>{error}</p>}
      </div>

      {pdfUrl && (
        <div className="card">
          <iframe title="report" src={pdfUrl} style={{ width: "100%", height: "80vh", border: "none" }} />
        </div>
      )}
    </div>
  );
}
