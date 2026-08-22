import React, { useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";
import { api } from "../api/client.js";
import MetricTile from "../components/MetricTile.jsx";

export default function SessionDashboard() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [quality, setQuality] = useState(null);
  const [notes, setNotes] = useState([]);
  const [noteText, setNoteText] = useState("");
  const [rawSignal, setRawSignal] = useState(null);
  const [showResearch, setShowResearch] = useState(false);
  const [error, setError] = useState(null);

  const load = async () => {
    const s = await api.getSession(sessionId);
    setSession(s);
    setNotes(await api.listNotes(sessionId));
    if (s.status === "complete") {
      try {
        setAnalysis(await api.getAnalysis(sessionId));
        setQuality(await api.getQuality(sessionId));
        if (s.recordings.length > 0) {
          setRawSignal(await api.getRaw(sessionId, s.recordings[0].recording_id));
        }
      } catch (e) {
        setError(e.message);
      }
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(async () => {
      const st = await api.getSessionStatus(sessionId);
      if (st.status === "complete" || st.status === "failed") {
        clearInterval(interval);
        load();
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [sessionId]);

  const addNote = async () => {
    if (!noteText.trim()) return;
    await api.createNote(sessionId, { note_text: noteText });
    setNoteText("");
    setNotes(await api.listNotes(sessionId));
  };

  const chartData = rawSignal
    ? rawSignal.data.timestamp_ms.map((t, i) => ({
        t,
        accel_x: rawSignal.data.accel_x[i],
        accel_y: rawSignal.data.accel_y[i],
        accel_z: rawSignal.data.accel_z[i],
      }))
    : [];

  if (!session) return <p>Loading...</p>;

  return (
    <div>
      <h2>Session Dashboard</h2>
      <p style={{ fontSize: 13, color: "#666" }}>
        Assessment date: {session.assessment_date?.slice(0, 10)} · Status: <strong>{session.status}</strong>
      </p>

      {session.status !== "complete" && (
        <div className="notice">
          {session.status === "processing" && "Analysis in progress..."}
          {session.status === "uploaded" && "Waiting for processing to start."}
          {session.status === "failed" && "Analysis failed. Please check the raw file and re-upload if needed."}
        </div>
      )}

      {quality && (
        <div className="card">
          <h3>Data Quality</h3>
          <p>Score: <strong>{quality.quality_score}</strong> / 100</p>
          <ul>
            {quality.flags.length === 0 && <li>No quality issues flagged</li>}
            {quality.flags.map((f, i) => <li key={i} className="badge-warning">{f}</li>)}
          </ul>
        </div>
      )}

      {analysis && (
        <div className="card">
          <h3>Gait Summary</h3>
          <div className="metric-grid">
            <MetricTile label="Cadence" {...analysis.metrics.cadence_spm} />
            <MetricTile label="Step time" {...analysis.metrics.step_time_s} />
            <MetricTile label="Step time CV" {...analysis.metrics.step_time_cv_pct} />
            <MetricTile label="Stride time" {...analysis.metrics.stride_time_s} />
            <MetricTile label="Gait regularity index" {...analysis.metrics.gait_regularity_index} />
          </div>
          <p style={{ marginTop: 12 }}>
            Walking bouts detected: {analysis.n_walking_bouts} · Walking duration: {analysis.walking_duration_s}s
          </p>

          <label style={{ fontSize: 12, marginTop: 10, display: "block" }}>
            <input type="checkbox" checked={showResearch} onChange={(e) => setShowResearch(e.target.checked)} />
            {" "}Show research metrics (estimated, not yet validated)
          </label>
          {showResearch && (
            <div className="metric-grid" style={{ marginTop: 10 }}>
              <MetricTile label="Walking speed" {...analysis.metrics.speed_mps} />
            </div>
          )}
        </div>
      )}

      {rawSignal && (
        <div className="card">
          <h3>Raw Sensor Signal (accelerometer, downsampled)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="t" tick={false} />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="accel_x" stroke="#3452e1" dot={false} />
              <Line type="monotone" dataKey="accel_y" stroke="#e13456" dot={false} />
              <Line type="monotone" dataKey="accel_z" stroke="#34a856" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="card">
        <h3>Clinical Notes</h3>
        <textarea value={noteText} onChange={(e) => setNoteText(e.target.value)} style={{ width: "100%", padding: 8 }} rows={3} />
        <button className="primary" style={{ marginTop: 8 }} onClick={addNote}>Add Note</button>
        <ul style={{ marginTop: 12 }}>
          {notes.map((n) => (
            <li key={n.note_id}><strong>{n.created_at?.slice(0, 16).replace("T", " ")}:</strong> {n.note_text}</li>
          ))}
        </ul>
      </div>

      <div className="card">
        <Link to={`/patients/${session.patient_id}/trend`}>View trend for this patient →</Link>
        <br /><br />
        <button className="primary" disabled={session.status !== "complete"} onClick={() => navigate(`/sessions/${sessionId}/report`)}>
          Generate / View Report
        </button>
      </div>

      {error && <p style={{ color: "crimson" }}>{error}</p>}
    </div>
  );
}
