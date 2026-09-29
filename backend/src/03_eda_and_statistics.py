
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from scipy.stats import ttest_ind, f_oneway, chi2_contingency

sys.path.append(str(Path(__file__).resolve().parent))
from config import CLEAN_DIR, REPORT_DIR

df = pd.read_csv(CLEAN_DIR / "master_dataset.csv", parse_dates=["date"])

# Business summaries
df.groupby("category", as_index=False).agg(
    units=("demand","sum"), revenue=("revenue","sum")
).sort_values("revenue", ascending=False).to_csv(
    REPORT_DIR/"revenue_by_category.csv", index=False
)

df.groupby(["store_id","city"], as_index=False).agg(
    units=("demand","sum"), revenue=("revenue","sum")
).sort_values("revenue", ascending=False).to_csv(
    REPORT_DIR/"revenue_by_store.csv", index=False
)

df.groupby("promotion_flag", as_index=False).agg(
    avg_demand=("demand","mean"), avg_revenue=("revenue","mean")
).to_csv(REPORT_DIR/"promotion_analysis.csv", index=False)

df.groupby("day_of_week", as_index=False).agg(
    avg_demand=("demand","mean"), avg_revenue=("revenue","mean")
).to_csv(REPORT_DIR/"weekday_analysis.csv", index=False)

# Three statistical tests
rows = []

p0 = df.loc[df.promotion_flag == 0, "demand"]
p1 = df.loc[df.promotion_flag == 1, "demand"]
stat, p = ttest_ind(p1, p0, equal_var=False)
rows.append([
    "Promotion vs demand", "Welch t-test", float(p),
    "Reject H0 at 0.05" if p < .05 else "Do not reject H0 at 0.05",
    float(p1.mean()), float(p0.mean())
])

samples = [g["demand"].values for _, g in df.groupby("store_type")]
stat, p = f_oneway(*samples)
rows.append([
    "Store type vs demand", "One-way ANOVA", float(p),
    "Reject H0 at 0.05" if p < .05 else "Do not reject H0 at 0.05",
    np.nan, np.nan
])

table = pd.crosstab(df.promotion_flag, df.stockout_today)
chi2, p, dof, expected = chi2_contingency(table)
rows.append([
    "Promotion vs stock-out", "Chi-square test", float(p),
    "Reject H0 at 0.05" if p < .05 else "Do not reject H0 at 0.05",
    np.nan, np.nan
])

pd.DataFrame(rows, columns=[
    "question","test","p_value","decision_at_0_05",
    "group1_mean_demand","group0_mean_demand"
]).to_csv(REPORT_DIR/"statistical_tests.csv", index=False)

# EDA KPI summary
summary = {
    "total_units": int(df.demand.sum()),
    "total_revenue": float(df.revenue.sum()),
    "stockout_rows": int(df.stockout_today.sum()),
    "inventory_mismatch_rows": int(df.inventory_mismatch_flag.sum()),
    "overstock_rows": int(df.overstock_flag.sum())
}
pd.DataFrame([summary]).to_json(REPORT_DIR/"eda_summary.json", orient="records", indent=2)

print("EDA + STATISTICS COMPLETE")
print(summary)
