from pathlib import Path
import pandas as pd
import json

BASE = Path(__file__).resolve().parent
required = [
    "data_raw/transactions.csv",
    "data_raw/products.csv",
    "data_raw/stores.csv",
    "data_raw/inventory.csv",
    "data_raw/external_factors.csv",
    "data_clean/master_dataset.csv",
    "models/demand_forecast_xgb.joblib",
    "models/stockout_xgb.joblib",
    "outputs/stocksense_decisions.csv",
    "outputs/latest_manager_action_centre.csv",
    "outputs/reports/data_quality_report.csv",
    "outputs/reports/forecast_model_metrics.csv",
    "outputs/reports/stockout_model_metrics.json",
]
missing = [p for p in required if not (BASE/p).exists()]
if missing:
    raise SystemExit("Missing required outputs:\n" + "\n".join(missing))

master = pd.read_csv(BASE/"data_clean/master_dataset.csv")
decisions = pd.read_csv(BASE/"outputs/stocksense_decisions.csv")
metrics = pd.read_csv(BASE/"outputs/reports/forecast_model_metrics.csv")

assert len(master) == 38400, len(master)
assert master.duplicated(["date","store_id","product_id"]).sum() == 0
assert set(decisions.risk_level.unique()) <= {"LOW","MEDIUM","HIGH"}
assert decisions.stockout_probability.between(0,1).all()
assert (decisions.reorder_quantity >= 0).all()
assert (decisions.recommendation_confidence.between(0,1)).all()
assert len(metrics) == 2

print("ALL BACKEND VALIDATION CHECKS PASSED")
print(f"Master rows: {len(master):,}")
print(f"Decision rows: {len(decisions):,}")
print(f"Latest date: {decisions.date.max()}")
print(f"Forecast test R2: {metrics.loc[metrics.split=='test','R2'].iloc[0]:.4f}")
