import React from "react";
import RiskBadge from "./RiskBadge";

function money(v) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(Number(v || 0));
}

export default function ActionTable({ items = [], compact = false, onSelect }) {
  return (
    <div className="table-wrap">
      <table>
        <thead><tr>
          <th>Product</th><th>Store</th><th>Risk</th><th>Stock-out</th><th>7D Forecast</th><th>Stock</th><th>Reorder</th><th>Action</th>
        </tr></thead>
        <tbody>
          {items.length === 0 ? <tr><td colSpan="8" className="empty">No actions match the current filters.</td></tr> : items.map((item, i) => (
            <tr key={`${item.product_id}-${item.store_id}-${i}`} onClick={() => onSelect?.(item)} className={onSelect ? "clickable" : ""}>
              <td><strong>{item.product_id}</strong><span className="muted">{item.category}</span></td>
              <td><strong>{item.store_id}</strong><span className="muted">{item.city || "—"}</span></td>
              <td><RiskBadge level={item.risk_level} /></td>
              <td><strong>{(Number(item.stockout_probability || 0) * 100).toFixed(0)}%</strong></td>
              <td>{Number(item.forecast_7d || 0).toFixed(0)}</td>
              <td>{Number(item.closing || 0).toFixed(0)}</td>
              <td><strong>{Number(item.reorder_quantity || 0).toFixed(0)}</strong></td>
              <td><span className="action-text">{item.manager_action || "Review"}</span>{!compact && <span className="muted">{money(item.revenue_at_risk)}</span>}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
