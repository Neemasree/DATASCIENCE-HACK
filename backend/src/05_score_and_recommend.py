
import sys, json
from pathlib import Path
import pandas as pd
import numpy as np
import joblib

sys.path.append(str(Path(__file__).resolve().parent))
from config import CLEAN_DIR, MODEL_DIR, OUTPUT_DIR, REPORT_DIR, RISK_HIGH, RISK_MEDIUM, OVERSTOCK_MULTIPLIER, SAFETY_Z

df = pd.read_csv(CLEAN_DIR/"master_dataset.csv", parse_dates=["date"])
reg = joblib.load(MODEL_DIR/"demand_forecast_xgb.joblib")
clf = joblib.load(MODEL_DIR/"stockout_xgb.joblib")

features = [
    "store_id","product_id","category","store_type","city",
    "avg_daily_customers","floor_area_sqft","mrp","cost_price",
    "shelf_life_days","lead_days","reorder_lvl","opening","closing",
    "received","demand","avg_discount_pct","promotion_flag","temp_c",
    "rain_mm","holiday","festival","weekend","local_event",
    "day_of_week","month","week_of_year","lag_1","lag_7","lag_14",
    "rolling_mean_7","rolling_mean_14","rolling_mean_28",
    "rolling_std_7","rolling_std_14","rolling_std_28"
]
x = df[features].copy()
for c in x.select_dtypes(exclude="object").columns:
    x[c] = x[c].replace([np.inf,-np.inf],np.nan).fillna(0)

df["forecast_7d"] = np.maximum(0, reg.predict(x))

cls_features = features + ["inventory_mismatch_flag"]
xc = df[cls_features].copy().fillna(0)
df["stockout_probability"] = clf.predict_proba(xc)[:,1]

df["risk_level"] = np.select(
    [
        df.stockout_probability >= RISK_HIGH,
        df.stockout_probability >= RISK_MEDIUM
    ],
    ["HIGH","MEDIUM"],
    default="LOW"
)

df["demand_volatility"] = (
    df.rolling_std_28.fillna(df.rolling_std_14)
      .fillna(df.rolling_std_7).fillna(0)
)

df["safety_stock"] = (
    SAFETY_Z * df.demand_volatility * np.sqrt(np.maximum(df.lead_days,1))
).clip(lower=0)

df["recommended_stock"] = df.forecast_7d + df.safety_stock

df["reorder_quantity"] = np.maximum(
    0,
    np.ceil(df.recommended_stock - df.closing - df.received)
).astype(int)

df["overstock_flag"] = (
    (df.forecast_7d > 0) &
    ((df.closing + df.received) > OVERSTOCK_MULTIPLIER * df.forecast_7d)
).astype(int)

df["excess_units"] = np.maximum(
    0,
    np.floor(df.closing + df.received - df.forecast_7d)
).astype(int)

df["revenue_at_risk"] = (
    np.maximum(0, df.forecast_7d - df.closing - df.received)
    * df.avg_selling_price.fillna(df.mrp)
)

# Trust-aware score: transparent decision-support confidence, not calibrated probability.
hist_days = df.groupby(["store_id","product_id"]).date.transform("count")
history_score = np.clip(hist_days/90,0,1)
inventory_score = 1 - df.inventory_mismatch_flag.clip(0,1)

report = pd.read_csv(REPORT_DIR/"forecast_model_metrics.csv")
mape = float(report.loc[report.split=="test","MAPE_percent_positive_targets"].iloc[0])
forecast_reliability = np.clip(1 - mape/100, 0, 1)

feature_completeness = df[
    ["lag_1","lag_7","lag_14","rolling_mean_7","rolling_mean_14"]
].notna().mean(axis=1)

df["recommendation_confidence"] = (
    .30*history_score +
    .25*inventory_score +
    .25*forecast_reliability +
    .20*feature_completeness
).clip(0,1)

df["confidence_level"] = np.select(
    [
        df.recommendation_confidence >= .90,
        df.recommendation_confidence >= .70
    ],
    ["HIGH","MEDIUM"],
    default="LOW"
)

def action(r):
    if r.risk_level == "HIGH" and r.confidence_level == "HIGH":
        return "ACT NOW — place replenishment order"
    if r.risk_level == "HIGH":
        return "VERIFY DATA — high risk, review before ordering"
    if r.overstock_flag:
        return "DO NOT REORDER — excess inventory"
    if r.risk_level == "MEDIUM":
        return "MONITOR — prepare replenishment"
    return "NO ACTION — continue monitoring"

df["manager_action"] = df.apply(action, axis=1)

def explain(r):
    reasons = []
    if r.closing <= r.reorder_lvl:
        reasons.append("stock at/below reorder level")
    if pd.notna(r.rolling_mean_7) and r.rolling_mean_7 > 0 and r.lag_1 > 1.15*r.rolling_mean_7:
        reasons.append("recent demand rising")
    if r.promotion_flag:
        reasons.append("promotion active")
    if r.weekend:
        reasons.append("weekend effect")
    if r.festival:
        reasons.append("festival effect")
    if r.local_event:
        reasons.append("local event")
    if r.lead_days >= 4:
        reasons.append("long supplier lead time")
    if r.overstock_flag:
        reasons.append("available stock above forecast")
    if r.inventory_mismatch_flag:
        reasons.append("inventory mismatch lowers confidence")
    return "; ".join(reasons[:4]) or "combined demand, inventory, store/product and external-factor signals"

df["business_explanation"] = df.apply(explain, axis=1)

cols = [
    "date","store_id","city","product_id","category","sub_category",
    "forecast_7d","closing","received","stockout_probability","risk_level",
    "overstock_flag","excess_units","safety_stock","recommended_stock",
    "reorder_quantity","revenue_at_risk","recommendation_confidence",
    "confidence_level","business_explanation","manager_action"
]
df[cols].to_csv(OUTPUT_DIR/"stocksense_decisions.csv", index=False)

latest_date = df.date.max()
df[df.date == latest_date][cols].to_csv(
    OUTPUT_DIR/"latest_manager_action_centre.csv", index=False
)

df.to_csv(OUTPUT_DIR/"scored_master_dataset.csv", index=False)

print("SCORING + RECOMMENDATIONS COMPLETE")
print("Latest date:", latest_date.date())
print("High risk:", int((df[df.date==latest_date].risk_level=="HIGH").sum()))
print("Medium risk:", int((df[df.date==latest_date].risk_level=="MEDIUM").sum()))
print("Low risk:", int((df[df.date==latest_date].risk_level=="LOW").sum()))
print("Reorder units:", int(df[df.date==latest_date].reorder_quantity.sum()))
