import React from "react";
import { BarChart3, Boxes, LayoutDashboard, ShieldAlert, Sparkles } from "lucide-react";

const items = [
  ["dashboard", "Dashboard", LayoutDashboard],
  ["risk", "Risk Center", ShieldAlert],
  ["inventory", "Inventory", Boxes],
  ["analytics", "Analytics", BarChart3],
];

export default function Sidebar({ page, setPage }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark"><Sparkles size={18} /></div>
        <div><strong>StockSense</strong><span>NovaMart Intelligence</span></div>
      </div>
      <nav>
        <div className="nav-label">Workspace</div>
        {items.map(([id, label, Icon]) => (
          <button key={id} className={`nav-item ${page === id ? "active" : ""}`} onClick={() => setPage(id)}>
            <Icon size={18} />{label}
          </button>
        ))}
      </nav>
      <div className="sidebar-bottom">
        <div className="live-dot"><span /> API connected</div>
        <small>Decision support v1.0</small>
      </div>
    </aside>
  );
}
