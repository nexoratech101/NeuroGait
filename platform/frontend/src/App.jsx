import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Sidebar from "./components/Sidebar.jsx";
import Login from "./pages/Login.jsx";
import PatientList from "./pages/PatientList.jsx";
import PatientProfile from "./pages/PatientProfile.jsx";
import UploadAssessment from "./pages/UploadAssessment.jsx";
import SessionDashboard from "./pages/SessionDashboard.jsx";
import TrendView from "./pages/TrendView.jsx";
import Report from "./pages/Report.jsx";

function isAuthed() {
  return !!localStorage.getItem("neurogait_token");
}

function RequireAuth({ children }) {
  if (!isAuthed()) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  if (!isAuthed()) {
    return (
      <Routes>
        <Route path="*" element={<Login />} />
      </Routes>
    );
  }

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-content">
        <Routes>
          <Route path="/" element={<Navigate to="/patients" replace />} />
          <Route path="/login" element={<Navigate to="/patients" replace />} />
          <Route path="/patients" element={<RequireAuth><PatientList /></RequireAuth>} />
          <Route path="/patients/:patientId" element={<RequireAuth><PatientProfile /></RequireAuth>} />
          <Route path="/patients/:patientId/trend" element={<RequireAuth><TrendView /></RequireAuth>} />
          <Route path="/upload" element={<RequireAuth><UploadAssessment /></RequireAuth>} />
          <Route path="/sessions/:sessionId" element={<RequireAuth><SessionDashboard /></RequireAuth>} />
          <Route path="/sessions/:sessionId/report" element={<RequireAuth><Report /></RequireAuth>} />
        </Routes>
      </div>
    </div>
  );
}
