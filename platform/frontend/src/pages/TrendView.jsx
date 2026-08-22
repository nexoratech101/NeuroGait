import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";
import { api } from "../api/client.js";

const CORE_METRICS = [
  ["cadence_spm", "Cadence (steps/min)"],
  ["step_time_s", "Step time (s)"],
  ["stride_time_s", "Stride time (s)"],
  ["gait_regularity_index", "Gait regularity index"],
];

export default function TrendView() {
  const { patientId } = useParams();
  const [trend, setTrend] = useState(null);

  useEffect(() => {
    api.getPatientTrend(patientId).then(setTrend);
  }, [patientId]);

  if (!trend) return <p>Loading...</p>;

  if (trend.n_sessions === 0) {
    return <p>No completed sessions yet for this patient.</p>;
  }

  return (
    <div>
      <h2>Trend View</h2>
      <p style={{ fontSize: 13, color: "#666" }}>{trend.n_sessions} session(s) with completed analysis.</p>

      {CORE_METRICS.map(([field, label]) => {
        const series = trend.trends[field];
        if (!series) return null;
        const comp = series.comparison;
        const chartData = series.series.map((p) => ({ date: p.assessment_date?.slice(0, 10), value: p.value }));

        return (
          <div className="card" key={field}>
            <h3>{label}</h3>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis domain={["auto", "auto"]} />
                <Tooltip />
                <Line type="monotone" dataKey="value" stroke="#3452e1" />
              </LineChart>
            </ResponsiveContainer>
            <p style={{ fontSize: 13 }}>
              Current: {comp.current ?? "-"} · Previous: {comp.previous ?? "-"}
              {comp.change_vs_previous_pct !== null && comp.change_vs_previous_pct !== undefined && (
                <> ({comp.change_vs_previous_pct > 0 ? "+" : ""}{comp.change_vs_previous_pct}% vs previous)</>
              )}
              {" · "}Baseline: {comp.baseline ?? "-"}
              {comp.change_vs_baseline_pct !== null && comp.change_vs_baseline_pct !== undefined && (
                <> ({comp.change_vs_baseline_pct > 0 ? "+" : ""}{comp.change_vs_baseline_pct}% vs baseline)</>
              )}
            </p>
          </div>
        );
      })}
    </div>
  );
}
