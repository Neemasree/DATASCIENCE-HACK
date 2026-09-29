import React from "react";
import { ArrowDownRight, ArrowUpRight, Boxes, CircleAlert, PackageCheck, ShieldAlert } from "lucide-react";

const icons = { high: ShieldAlert, medium: CircleAlert, low: PackageCheck, reorder: Boxes };

export default function StatCard({ label, value, sub, tone = "neutral", trend }) {
  const Icon = icons[tone] || Boxes;
  return (
    <div className={`stat-card ${tone}`}>
      <div className="stat-icon"><Icon size={19} /></div>
      <div className="stat-copy">
        <span>{label}</span>
        <strong>{value}</strong>
        {sub && <small>{sub}</small>}
      </div>
      {trend && <div className={`trend ${trend > 0 ? "up" : "down"}`}>{trend > 0 ? <ArrowUpRight size={15} /> : <ArrowDownRight size={15} />}{Math.abs(trend)}%</div>}
    </div>
  );
}
