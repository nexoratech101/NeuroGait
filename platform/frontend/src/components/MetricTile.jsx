import React from "react";

// Every derived gait metric must carry a measured/estimated/derived tag, visible
// wherever the metric is shown (spec section 0.2) -- never render a bare value.
export default function MetricTile({ label, value, unit, status }) {
  const display = value === null || value === undefined ? "not available" : `${value} ${unit || ""}`.trim();
  return (
    <div className="metric-tile">
      <div className="value">{display}</div>
      <div className="label">
        {label}
        {status && <span className={`tag tag-${status}`}>{status}</span>}
      </div>
    </div>
  );
}
