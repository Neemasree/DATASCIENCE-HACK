
import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.append(str(Path(__file__).resolve().parent))
from config import RAW_DIR, CLEAN_DIR, REPORT_DIR

CLEAN_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

tx = pd.read_csv(RAW_DIR / "transactions.csv", parse_dates=["date"])
products = pd.read_csv(RAW_DIR / "products.csv")
stores = pd.read_csv(RAW_DIR / "stores.csv")
inventory = pd.read_csv(RAW_DIR / "inventory.csv", parse_dates=["date"])
external = pd.read_csv(RAW_DIR / "external_factors.csv", parse_dates=["date"])

audit = []

def add(dataset, issue, count, action, reason):
    audit.append({
        "dataset": dataset,
        "issue": issue,
        "count": int(count),
        "action": action,
        "justification": reason
    })

# ---------- TRANSACTIONS ----------
duplicates = tx.duplicated(subset=["transaction_id"]).sum()
add("transactions", "Duplicate transaction IDs", duplicates,
    "Remove duplicate transaction_id rows; keep first",
    "Duplicate IDs can double-count demand.")

negative_qty = (tx["quantity"] < 0).sum()
add("transactions", "Negative quantity", negative_qty,
    "Remove invalid negative sales quantities",
    "Normal sales quantities cannot be negative.")

tx = tx.drop_duplicates(subset=["transaction_id"], keep="first")
tx = tx[tx["quantity"] >= 0].copy()

# ---------- PRODUCTS ----------
products["category_raw"] = products["category"]
products["category"] = products["category"].astype(str).str.strip().str.title()
products["category"] = products["category"].replace({"Beverage": "Beverages"})

category_changes = (products["category_raw"].astype(str).str.strip() != products["category"]).sum()
add("products", "Category inconsistencies", category_changes,
    "Strip whitespace, normalize case and map equivalent labels",
    "One canonical category is required for grouping and modeling.")

# ---------- STORES ----------
stores["store_id"] = stores["store_id"].astype(str).str.strip().str.upper()

# ---------- INVENTORY ----------
inventory["store"] = inventory["store"].astype(str).str.strip().str.upper()
inventory["product"] = inventory["product"].astype(str).str.strip().str.upper()

inventory["expected_closing"] = (
    inventory["opening"] + inventory["received"] - inventory["sold"]
)
inventory["inventory_mismatch_flag"] = (
    inventory["closing"] != inventory["expected_closing"]
).astype(int)

mismatches = inventory["inventory_mismatch_flag"].sum()
add("inventory", "Inventory arithmetic mismatch", mismatches,
    "Preserve source closing; add mismatch flag and reconciled value",
    "Source values should remain auditable rather than being silently overwritten.")

inventory["closing_reconciled"] = inventory["expected_closing"]

# ---------- EXTERNAL FACTORS ----------
missing_temp = external["temp_c"].isna().sum()
add("external_factors", "Missing temperature", missing_temp,
    "Impute using city median temperature",
    "City-level median is appropriate for a small number of missing continuous values.")

external["city"] = external["city"].astype(str).str.strip().str.title()
external["temp_c_raw"] = external["temp_c"]
external["temp_c"] = external.groupby("city")["temp_c"].transform(
    lambda s: s.fillna(s.median())
)

# ---------- FOREIGN KEYS ----------
checks = [
    ("transactions", "Invalid store IDs",
     (~tx["store_id"].isin(stores["store_id"])).sum(),
     "Stop/flag integration if non-zero",
     "Every transaction store must exist in stores."),
    ("transactions", "Invalid product IDs",
     (~tx["product_id"].isin(products["product_id"])).sum(),
     "Stop/flag integration if non-zero",
     "Every transaction product must exist in products."),
    ("inventory", "Invalid store IDs",
     (~inventory["store"].isin(stores["store_id"])).sum(),
     "Stop/flag integration if non-zero",
     "Every inventory store must exist in stores."),
    ("inventory", "Invalid product IDs",
     (~inventory["product"].isin(products["product_id"])).sum(),
     "Stop/flag integration if non-zero",
     "Every inventory product must exist in products.")
]

for dataset, issue, count, action, reason in checks:
    add(dataset, issue, count, action, reason)

# Save
tx.to_csv(CLEAN_DIR / "transactions_clean.csv", index=False)
products.drop(columns=["category_raw"]).to_csv(CLEAN_DIR / "products_clean.csv", index=False)
stores.to_csv(CLEAN_DIR / "stores_clean.csv", index=False)
inventory.to_csv(CLEAN_DIR / "inventory_clean.csv", index=False)
external.to_csv(CLEAN_DIR / "external_factors_clean.csv", index=False)

audit_df = pd.DataFrame(audit)
audit_df.to_csv(REPORT_DIR / "data_quality_report.csv", index=False)

summary = {
    "transactions_raw": len(pd.read_csv(RAW_DIR / "transactions.csv")),
    "transactions_clean": len(tx),
    "products": len(products),
    "stores": len(stores),
    "inventory": len(inventory),
    "external_factors": len(external),
    "duplicate_transaction_ids": int(duplicates),
    "negative_quantities": int(negative_qty),
    "inventory_mismatches": int(mismatches),
    "missing_temperature": int(missing_temp),
    "invalid_foreign_keys": int(sum(x[2] for x in checks))
}
pd.DataFrame([summary]).to_json(
    REPORT_DIR / "cleaning_summary.json", orient="records", indent=2
)

print("DATA CLEANING COMPLETE")
print(pd.DataFrame(audit).to_string(index=False))
