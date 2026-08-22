import React, { useState } from "react";
import { api } from "../api/client.js";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.login(email, password);
      localStorage.setItem("neurogait_token", res.access_token);
      localStorage.setItem("neurogait_role", res.role);
      localStorage.setItem("neurogait_name", res.name);
      window.location.href = "/patients";
    } catch (err) {
      setError("Login failed. Check your email and password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", height: "100vh", alignItems: "center", justifyContent: "center", background: "#f6f7fb" }}>
      <form onSubmit={submit} className="card" style={{ width: 340 }}>
        <h2>NeuroGait Platform</h2>
        <p style={{ fontSize: 13, color: "#666" }}>Research prototype -- Western University</p>
        <div style={{ marginBottom: 12 }}>
          <label>Email</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required
                 style={{ width: "100%", padding: 8, marginTop: 4 }} />
        </div>
        <div style={{ marginBottom: 12 }}>
          <label>Password</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required
                 style={{ width: "100%", padding: 8, marginTop: 4 }} />
        </div>
        {error && <p style={{ color: "crimson", fontSize: 13 }}>{error}</p>}
        <button type="submit" className="primary" disabled={loading} style={{ width: "100%" }}>
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </div>
  );
}
