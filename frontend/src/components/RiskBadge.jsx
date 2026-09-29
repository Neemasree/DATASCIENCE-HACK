import React from "react";
export default function RiskBadge({ level }) {
  return <span className={`risk-badge ${(level || "LOW").toLowerCase()}`}>{level || "LOW"}</span>;
}
