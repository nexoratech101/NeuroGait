import React from "react";
import { Link } from "react-router-dom";

export default function Sidebar() {
  const logout = () => {
    localStorage.removeItem("neurogait_token");
    window.location.href = "/login";
  };

  return (
    <div className="sidebar">
      <h1>NeuroGait Platform</h1>
      <Link to="/patients">Patients</Link>
      <Link to="/upload">Upload Assessment</Link>
      <span className="disabled" title="Future placeholder">Turning Analysis (coming soon)</span>
      <span className="disabled" title="Future placeholder">Fatigue Analysis (coming soon)</span>
      <span className="disabled" title="Future placeholder">Research Mode (coming soon)</span>
      <span className="disabled" title="Future placeholder">Multi-patient Comparison (coming soon)</span>
      <span className="disabled" title="Future placeholder">Alerts (coming soon)</span>
      <div style={{ marginTop: 24 }}>
        <a href="#" onClick={(e) => { e.preventDefault(); logout(); }}>Log out</a>
      </div>
    </div>
  );
}
