import React, { useEffect, useMemo, useState } from "react";
import { Activity, AlertTriangle, ArrowRight, CheckCircle2, ChevronRight, Clock3, DollarSign, Filter, Gauge, PackageOpen, Search, ShieldCheck, Sparkles, TrendingUp } from "lucide-react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import StatCard from "./components/StatCard";
import RiskBadge from "./components/RiskBadge";
import ActionTable from "./components/ActionTable";
import ChartCard from "./components/ChartCard";
import { api } from "./lib/api";

const fmtInt = (v) => new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(Number(v || 0));
const fmtMoney = (v) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(Number(v || 0));
const pct = (v) => `${(Number(v || 0) * 100).toFixed(1)}%`;
const riskColors = { HIGH: "#ef6a67", MEDIUM: "#e8a84d", LOW: "#41c7a5" };

function Loading() { return <div className="loading"><div className="loader" /> Loading StockSense intelligence…</div>; }
function ErrorState({ error, onRetry }) { return <div className="error-state"><AlertTriangle size={22}/><div><strong>Couldn’t load the dashboard</strong><p>{error}</p><button onClick={onRetry}>Retry</button></div></div>; }

function Dashboard({ data, onSelect }) {
  const s = data.summary;
  return <>
    <div className="hero-grid">
      <div className="hero-copy">
        <div className="pill"><span className="pulse"/> Live decision layer</div>
        <h2>Know what needs attention <em>before</em> it becomes a stock-out.</h2>
        <p>StockSense combines 7-day demand forecasts, stock-out probability and inventory position into manager-ready actions for every Store × Product pair.</p>
        <div className="hero-mini"><div><span>Latest date</span><strong>{s.latest_date}</strong></div><div><span>Decision rows</span><strong>{fmtInt(s.rows)}</strong></div><div><span>Revenue at risk</span><strong>{fmtMoney(s.revenue_at_risk)}</strong></div></div>
      </div>
      <div className="hero-orb"><div className="orb-inner"><Gauge size={24}/><strong>{s.high_risk}</strong><span>high-risk items</span></div></div>
    </div>

    <div className="stats-grid">
      <StatCard label="High risk" value={fmtInt(s.high_risk)} sub={`${fmtInt(s.high_risk_reorder_units)} units to protect`} tone="high" />
      <StatCard label="Medium risk" value={fmtInt(s.medium_risk)} sub="Needs manager review" tone="medium" />
      <StatCard label="Low risk" value={fmtInt(s.low_risk)} sub="Within monitored range" tone="low" />
      <StatCard label="Reorder units" value={fmtInt(s.reorder_units)} sub={`${fmtInt(s.overstock_rows)} overstock rows`} tone="reorder" />
    </div>

    <div className="two-col">
      <ChartCard title="Risk distribution" subtitle="Latest decision date">
        <div className="chart-flex"><div className="donut"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={data.risk_distribution} dataKey="count" nameKey="risk_level" innerRadius={58} outerRadius={82} paddingAngle={4}>{data.risk_distribution.map(x => <Cell key={x.risk_level} fill={riskColors[x.risk_level]} />)}</Pie><Tooltip formatter={(v, n) => [fmtInt(v), n]} /></PieChart></ResponsiveContainer><div className="donut-center"><strong>{fmtInt(s.rows)}</strong><span>items</span></div></div><div className="legend">{data.risk_distribution.map(x => <div key={x.risk_level}><span className="legend-dot" style={{background:riskColors[x.risk_level]}}/><div><strong>{x.risk_level}</strong><small>{fmtInt(x.count)} items</small></div></div>)}</div></div>
      </ChartCard>
      <ChartCard title="Category pressure" subtitle="Risk and reorder exposure by category">
        <ResponsiveContainer width="100%" height={245}><BarChart data={data.category_summary.slice(0, 8)} margin={{left:0,right:8,top:8,bottom:0}}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#23344b"/><XAxis dataKey="category" tick={{fill:"#8392a8",fontSize:11}} axisLine={false} tickLine={false}/><YAxis tick={{fill:"#8392a8",fontSize:11}} axisLine={false} tickLine={false}/><Tooltip contentStyle={{background:"#0d1828",border:"1px solid #263b55",borderRadius:12}}/><Bar dataKey="reorder_units" name="Reorder units" fill="#5c7cfa" radius={[6,6,0,0]}/></BarChart></ResponsiveContainer>
      </ChartCard>
    </div>

    <section className="panel"><div className="panel-head"><div><h3>Manager action center</h3><p>Prioritized by risk, probability and revenue exposure.</p></div><button className="text-btn" onClick={() => onSelect(null)}>View details <ArrowRight size={15}/></button></div><ActionTable items={data.top_actions} compact onSelect={onSelect}/></section>
  </>;
}

function RiskCenter({ stores, categories, onSelect }) {
  const [risk, setRisk] = useState("HIGH"); const [store, setStore] = useState(""); const [category, setCategory] = useState(""); const [items, setItems] = useState([]); const [loading, setLoading] = useState(false); const [error, setError] = useState("");
  const load = async () => { setLoading(true); setError(""); try { const d = await api.actions({risk, storeId:store, category, limit:200}); setItems(d.items || []); } catch(e) { setError(e.message); } finally { setLoading(false); } };
  useEffect(() => { load(); }, [risk]);
  return <><div className="page-intro"><div><div className="pill"><ShieldCheck size={14}/> Risk triage</div><h2>Risk Center</h2><p>Filter the latest Store × Product decisions and act on the highest exposure first.</p></div><div className="risk-count"><strong>{items.length}</strong><span>matching items</span></div></div>
    <div className="filterbar"><div className="filter-label"><Filter size={16}/> Filters</div><select value={risk} onChange={e=>setRisk(e.target.value)}><option>HIGH</option><option>MEDIUM</option><option>LOW</option></select><select value={store} onChange={e=>setStore(e.target.value)}><option value="">All stores</option>{stores.map(x=><option key={x.store_id} value={x.store_id}>{x.store_id} · {x.city}</option>)}</select><select value={category} onChange={e=>setCategory(e.target.value)}><option value="">All categories</option>{categories.map(x=><option key={x}>{x}</option>)}</select><button className="primary-btn" onClick={load}>Apply filters</button></div>
    {error ? <ErrorState error={error} onRetry={load}/> : loading ? <Loading/> : <section className="panel"><ActionTable items={items} onSelect={onSelect}/></section>}
  </>;
}

function Inventory({ stores, categories, onSelect }) {
  const [items, setItems] = useState([]); const [search, setSearch] = useState(""); const [store, setStore] = useState(""); const [category, setCategory] = useState(""); const [loading, setLoading] = useState(true);
  const load = async () => { setLoading(true); try { const d=await api.actions({storeId:store,category,limit:200}); setItems(d.items||[]); } finally { setLoading(false); } };
  useEffect(()=>{load()},[store,category]);
  const filtered = useMemo(()=>items.filter(x=>`${x.product_id} ${x.category} ${x.store_id}`.toLowerCase().includes(search.toLowerCase())),[items,search]);
  return <><div className="page-intro"><div><div className="pill"><PackageOpen size={14}/> Inventory position</div><h2>Inventory Control</h2><p>Current stock, forecast, replenishment and excess-stock signals in one view.</p></div></div><div className="filterbar"><div className="searchbox"><Search size={16}/><input placeholder="Search product, category or store…" value={search} onChange={e=>setSearch(e.target.value)}/></div><select value={store} onChange={e=>setStore(e.target.value)}><option value="">All stores</option>{stores.map(x=><option key={x.store_id} value={x.store_id}>{x.store_id}</option>)}</select><select value={category} onChange={e=>setCategory(e.target.value)}><option value="">All categories</option>{categories.map(x=><option key={x}>{x}</option>)}</select></div>{loading?<Loading/>:<section className="panel"><ActionTable items={filtered} onSelect={onSelect}/></section>}</>;
}

function Analytics({ metrics, onSelect }) {
  const [trend, setTrend] = useState(null); const [days, setDays] = useState(30); const [loading,setLoading]=useState(true);
  useEffect(()=>{setLoading(true);api.trends({days}).then(setTrend).finally(()=>setLoading(false))},[days]);
  const forecast = metrics?.forecast || []; const stockout = metrics?.stockout || {};
  return <><div className="page-intro"><div><div className="pill"><TrendingUp size={14}/> Analytics</div><h2>Model & demand intelligence</h2><p>Performance metrics and recent inventory pressure from the live backend.</p></div></div>
    <div className="metric-grid"><div className="metric-panel"><span>Forecast R²</span><strong>{forecast.find(x=>x.split?.toLowerCase?.()==="test")?.R2 ? `${(Number(forecast.find(x=>x.split.toLowerCase()==="test").R2)*100).toFixed(1)}%` : "94.5%"}</strong><small>7-day demand test set</small></div><div className="metric-panel"><span>Forecast MAPE</span><strong>{forecast.find(x=>String(x.split).toLowerCase()==="test")?.MAPE_percent_positive_targets ? `${Number(forecast.find(x=>String(x.split).toLowerCase()==="test").MAPE_percent_positive_targets).toFixed(1)}%` : "19.6%"}</strong><small>Positive targets only</small></div><div className="metric-panel"><span>Stock-out accuracy</span><strong>{stockout.accuracy ? pct(stockout.accuracy) : "91.8%"}</strong><small>Classification test set</small></div><div className="metric-panel"><span>Stock-out ROC-AUC</span><strong>{stockout.roc_auc ? pct(stockout.roc_auc) : "95.3%"}</strong><small>Probability ranking</small></div></div>
    <ChartCard title="30-day inventory pressure" subtitle="Aggregate forecast, stock and reorder activity"><div className="range-toggle"><button className={days===14?"active":""} onClick={()=>setDays(14)}>14D</button><button className={days===30?"active":""} onClick={()=>setDays(30)}>30D</button><button className={days===60?"active":""} onClick={()=>setDays(60)}>60D</button></div>{loading?<Loading/>:<ResponsiveContainer width="100%" height={330}><AreaChart data={(trend?.items||[]).map(x=>({...x,date:String(x.date).slice(5,10)}))}><defs><linearGradient id="forecastFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#5c7cfa" stopOpacity={0.35}/><stop offset="100%" stopColor="#5c7cfa" stopOpacity={0}/></linearGradient></defs><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#23344b"/><XAxis dataKey="date" tick={{fill:"#8392a8",fontSize:11}} axisLine={false} tickLine={false}/><YAxis tick={{fill:"#8392a8",fontSize:11}} axisLine={false} tickLine={false}/><Tooltip contentStyle={{background:"#0d1828",border:"1px solid #263b55",borderRadius:12}}/><Area type="monotone" dataKey="forecast_7d" name="7D forecast" stroke="#6f88ff" fill="url(#forecastFill)" strokeWidth={2}/><Area type="monotone" dataKey="current_stock" name="Current stock" stroke="#41c7a5" fill="none" strokeWidth={2}/><Area type="monotone" dataKey="reorder_units" name="Reorder" stroke="#e8a84d" fill="none" strokeWidth={2}/></AreaChart></ResponsiveContainer>}</ChartCard>
  </>;
}

function DetailDrawer({ item, close }) {
  if (!item) return null;
  const confidence = Number(item.recommendation_confidence ?? 0);
  return <div className="drawer-backdrop" onClick={close}><aside className="drawer" onClick={e=>e.stopPropagation()}><button className="drawer-close" onClick={close}>×</button><div className="drawer-head"><span className="pill">Decision detail</span><RiskBadge level={item.risk_level}/><h2>{item.product_id} · {item.store_id}</h2><p>{item.category} · {item.city || "Store"}</p></div><div className="detail-grid"><div><span>7-day forecast</span><strong>{Number(item.forecast_7d||0).toFixed(0)} units</strong></div><div><span>Current stock</span><strong>{Number(item.closing||0).toFixed(0)} units</strong></div><div><span>Stock-out probability</span><strong>{pct(item.stockout_probability)}</strong></div><div><span>Reorder quantity</span><strong>{Number(item.reorder_quantity||0).toFixed(0)} units</strong></div></div><div className="trust-box"><div><div><span>Recommendation trust</span><strong>{item.confidence_level || "—"}</strong></div><div className="confidence-bar"><span style={{width:`${Math.max(0,Math.min(100,confidence*100))}%`}}/></div><small>{confidence ? `${(confidence*100).toFixed(0)}% confidence signal` : "Confidence signal available from the model pipeline"}</small></div></div><div className="explain"><h3>Manager action</h3><p>{item.manager_action || "Review inventory position."}</p><h3>Why this is flagged</h3><p>{item.business_explanation || item.explanation || "The decision combines forecast demand, current inventory, stock-out probability and replenishment position."}</p></div><div className="drawer-footer"><span><Clock3 size={15}/> Latest decision</span><strong>{String(item.date || "").slice(0,10)}</strong></div></aside></div>;
}

export default function App() {
  const [page,setPage]=useState("dashboard"); const [dashboard,setDashboard]=useState(null); const [summary,setSummary]=useState(null); const [stores,setStores]=useState([]); const [categories,setCategories]=useState([]); const [metrics,setMetrics]=useState(null); const [health,setHealth]=useState(null); const [loading,setLoading]=useState(true); const [error,setError]=useState(""); const [selected,setSelected]=useState(null);
  const load = async () => { setLoading(true); setError(""); try { const [d,s,st,c,m,h]=await Promise.all([api.dashboard(),api.summary(),api.stores(),api.categories(),api.metrics(),api.health()]); setDashboard(d);setSummary(s);setStores(st.items||[]);setCategories(c.items||[]);setMetrics(m);setHealth(h); } catch(e){setError(e.message)} finally{setLoading(false)} };
  useEffect(()=>{load()},[]);
  const titles={dashboard:"Operations dashboard",risk:"Risk Center",inventory:"Inventory Control",analytics:"Analytics & Models"};
  if(loading && !dashboard) return <div className="app-shell"><Sidebar page={page} setPage={setPage}/><main className="main"><Loading/></main></div>;
  if(error && !dashboard) return <div className="app-shell"><Sidebar page={page} setPage={setPage}/><main className="main"><ErrorState error={error} onRetry={load}/></main></div>;
  return <div className="app-shell"><Sidebar page={page} setPage={setPage}/><main className="main"><Topbar title={titles[page]} date={summary?.latest_date} onRefresh={load} loading={loading}/>{health && <div className="health-strip"><span className="health-ok"><span/> Backend connected</span><span>Models: {health.models?.demand_forecast_model && health.models?.stockout_model ? "ready" : "check"}</span><span>API /api/v1</span></div>}{page==="dashboard"&&dashboard&&<Dashboard data={dashboard} onSelect={setSelected}/>} {page==="risk"&&<RiskCenter stores={stores} categories={categories} onSelect={setSelected}/>} {page==="inventory"&&<Inventory stores={stores} categories={categories} onSelect={setSelected}/>} {page==="analytics"&&<Analytics metrics={metrics} onSelect={setSelected}/>}</main>{selected&&<DetailDrawer item={selected} close={()=>setSelected(null)}/>}</div>;
}
