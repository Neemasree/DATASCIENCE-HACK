
import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.append(str(Path(__file__).resolve().parent))
from config import CLEAN_DIR, REPORT_DIR

tx = pd.read_csv(CLEAN_DIR / "transactions_clean.csv", parse_dates=["date"])
products = pd.read_csv(CLEAN_DIR / "products_clean.csv")
stores = pd.read_csv(CLEAN_DIR / "stores_clean.csv")
inventory = pd.read_csv(CLEAN_DIR / "inventory_clean.csv", parse_dates=["date"])
external = pd.read_csv(CLEAN_DIR / "external_factors_clean.csv", parse_dates=["date"])

# Daily Store × Product demand
daily = (
    tx.groupby(["date", "store_id", "product_id"], as_index=False)
      .agg(
          demand=("quantity", "sum"),
          avg_selling_price=("selling_price", "mean"),
          avg_discount_pct=("discount_pct", "mean"),
          promotion_flag=("promotion_flag", "max"),
          transaction_count=("transaction_id", "nunique"),
          customer_count=("customer_id", "nunique")
      )
)

# Inventory is the backbone because it has one row per Date × Store × Product
master = (
    inventory.rename(columns={"store": "store_id", "product": "product_id"})
    .merge(daily, on=["date", "store_id", "product_id"], how="left")
    .merge(products, on="product_id", how="left")
    .merge(stores, on="store_id", how="left")
    .merge(external, on=["date", "city"], how="left")
)

for c in ["demand", "transaction_count", "customer_count", "avg_discount_pct", "promotion_flag"]:
    master[c] = master[c].fillna(0)

master["revenue"] = master["demand"] * master["avg_selling_price"]
master["gross_margin"] = (
    master["demand"] * (master["avg_selling_price"] - master["cost_price"])
)

master["stockout_today"] = (master["closing"] <= 0).astype(int)
master["days_of_inventory"] = (
    master["closing"] / master["demand"].replace(0, np.nan)
).replace([np.inf, -np.inf], np.nan).fillna(999)

master["day_of_week"] = master["date"].dt.dayofweek
master["month"] = master["date"].dt.month
master["week_of_year"] = master["date"].dt.isocalendar().week.astype(int)

master = master.sort_values(["store_id", "product_id", "date"]).reset_index(drop=True)
group = master.groupby(["store_id", "product_id"], group_keys=False)

for lag in [1, 7, 14]:
    master[f"lag_{lag}"] = group["demand"].shift(lag)

for window in [7, 14, 28]:
    shifted = group["demand"].shift(1)
    master[f"rolling_mean_{window}"] = (
        shifted.groupby([master["store_id"], master["product_id"]])
        .rolling(window, min_periods=3).mean()
        .reset_index(level=[0, 1], drop=True)
    )
    master[f"rolling_std_{window}"] = (
        shifted.groupby([master["store_id"], master["product_id"]])
        .rolling(window, min_periods=3).std()
        .reset_index(level=[0, 1], drop=True)
    )

# Future 7-day target
future_demand = group["demand"].transform(
    lambda s: s.shift(-1)[::-1].rolling(7, min_periods=7).sum()[::-1]
)
master["next_7_day_demand"] = future_demand

future_min_stock = group["closing"].transform(
    lambda s: s.shift(-1)[::-1].rolling(7, min_periods=7).min()[::-1]
)
future_count = group["closing"].transform(
    lambda s: s.shift(-1)[::-1].rolling(7, min_periods=7).count()[::-1]
)

master["future_7d_complete"] = (future_count == 7).astype(int)
master["stockout_next_7d"] = (
    (future_min_stock <= 0) & (master["future_7d_complete"] == 1)
).astype(int)

master["overstock_flag"] = (
    (master["closing"] > 1.5 * master["next_7_day_demand"]) &
    (master["next_7_day_demand"] > 0)
).astype(int)

out = CLEAN_DIR / "master_dataset.csv"
master.to_csv(out, index=False)

# Master validation
expected_rows = (
    master["date"].nunique()
    * master["store_id"].nunique()
    * master["product_id"].nunique()
)

report = {
    "rows": len(master),
    "expected_full_grid_rows": expected_rows,
    "date_start": str(master.date.min().date()),
    "date_end": str(master.date.max().date()),
    "stores": int(master.store_id.nunique()),
    "products": int(master.product_id.nunique()),
    "duplicate_grain_rows": int(master.duplicated(["date","store_id","product_id"]).sum()),
    "missing_product_attributes": int(master["category"].isna().sum()),
    "missing_store_attributes": int(master["city"].isna().sum()),
    "missing_external_weather": int(master["temp_c"].isna().sum())
}
pd.DataFrame([report]).to_json(REPORT_DIR / "master_validation.json", orient="records", indent=2)

print("MASTER DATASET COMPLETE")
print(report)
