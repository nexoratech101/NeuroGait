import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client.js";

export default function PatientList() {
  const [patients, setPatients] = useState([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async (query = "") => {
    setLoading(true);
    const data = await api.listPatients(query);
    setPatients(data);
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  return (
    <div>
      <h2>Patients</h2>
      <div className="card">
        <input
          placeholder="Search by name..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && load(q)}
          style={{ padding: 8, width: 260 }}
        />
        <button className="primary" style={{ marginLeft: 8 }} onClick={() => load(q)}>Search</button>
      </div>
      <div className="card">
        {loading ? (
          <p>Loading...</p>
        ) : (
          <table>
            <thead>
              <tr><th>Study ID</th><th>Name</th><th>Phenotype</th><th>Enrolled</th></tr>
            </thead>
            <tbody>
              {patients.map((p) => (
                <tr key={p.patient_id}>
                  <td>{p.study_id}</td>
                  <td><Link to={`/patients/${p.patient_id}`}>{p.full_name}</Link></td>
                  <td>{p.ms_phenotype || "-"}</td>
                  <td>{p.enrollment_date || "-"}</td>
                </tr>
              ))}
              {patients.length === 0 && (
                <tr><td colSpan={4}>No patients yet. Upload an assessment to create one.</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
