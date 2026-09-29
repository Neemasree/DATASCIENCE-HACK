import React from "react";
import { CalendarDays, RefreshCw } from "lucide-react";

export default function Topbar({ title, date, onRefresh, loading }) {
  return (
    <header className="topbar">
      <div><p className="eyebrow">NOVA MART / INVENTORY CONTROL</p><h1>{title}</h1></div>
      <div className="topbar-actions">
        {date && <span className="date-chip"><CalendarDays size={15} /> {date}</span>}
        <button className="refresh-btn" onClick={onRefresh} disabled={loading}><RefreshCw size={16} className={loading ? "spin" : ""} /> Refresh</button>
      </div>
    </header>
  );
}
