import React from "react";
export default function ChartCard({ title, subtitle, children, className = "" }) {
  return <section className={`panel chart-panel ${className}`}><div className="panel-head"><div><h3>{title}</h3>{subtitle && <p>{subtitle}</p>}</div></div>{children}</section>;
}
