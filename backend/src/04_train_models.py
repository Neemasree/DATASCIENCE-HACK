
import sys, json
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
)
from xgboost import XGBRegressor, XGBClassifier

sys.path.append(str(Path(__file__).resolve().parent))
from config import CLEAN_DIR, MODEL_DIR, REPORT_DIR

MODEL_DIR.mkdir(exist_ok=True)

df = pd.read_csv(CLEAN_DIR/"master_dataset.csv", parse_dates=["date"])
df = df[df.future_7d_complete == 1].copy()

dates = sorted(df.date.unique())
cut1 = dates[int(len(dates)*.70)]
cut2 = dates[int(len(dates)*.85)]

train = df[df.date <= cut1]
valid = df[(df.date > cut1) & (df.date <= cut2)]
test = df[df.date > cut2]

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

def prepare(data):
    x = data[features].copy()
    for c in x.select_dtypes(exclude="object").columns:
        x[c] = x[c].replace([np.inf,-np.inf], np.nan).fillna(0)
    return x

def metrics_reg(y, pred):
    y = np.asarray(y)
    pred = np.asarray(pred)
    # MAPE only on meaningful positive demand to avoid exploding percentage errors at zero.
    mask = y > 0
    mape = np.mean(np.abs((y[mask]-pred[mask])/y[mask]))*100 if mask.any() else np.nan
    return {
        "MAE": float(mean_absolute_error(y,pred)),
        "RMSE": float(np.sqrt(mean_squared_error(y,pred))),
        "MAPE_percent_positive_targets": float(mape),
        "R2": float(r2_score(y,pred))
    }

cat = [c for c in features if df[c].dtype == "object"]
num = [c for c in features if c not in cat]
print("Categorical features:", cat)
print("Numeric features:", len(num))

# Explicit numeric encoding for categorical columns.
# This avoids passing raw strings such as S01/P001 to XGBoost.
pre = ColumnTransformer([
    ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), cat),
    ("num", "passthrough", num)
])

reg = Pipeline([
    ("pre", pre),
    ("model", XGBRegressor(
        n_estimators=250, max_depth=6, learning_rate=.05,
        subsample=.85, colsample_bytree=.85,
        objective="reg:squarederror", random_state=42, n_jobs=4
    ))
])

reg.fit(prepare(train), train.next_7_day_demand)
valid_pred = np.maximum(0, reg.predict(prepare(valid)))
test_pred = np.maximum(0, reg.predict(prepare(test)))

forecast_metrics = pd.DataFrame([
    {"split":"validation", **metrics_reg(valid.next_7_day_demand, valid_pred)},
    {"split":"test", **metrics_reg(test.next_7_day_demand, test_pred)}
])
forecast_metrics.to_csv(REPORT_DIR/"forecast_model_metrics.csv", index=False)
joblib.dump(reg, MODEL_DIR/"demand_forecast_xgb.joblib")

# Stock-out classifier
cls_features = features + ["inventory_mismatch_flag"]
cat2 = [c for c in cls_features if df[c].dtype == "object"]
num2 = [c for c in cls_features if c not in cat2]

pre2 = ColumnTransformer([
    ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), cat2),
    ("num", "passthrough", num2)
])

pos = max(1, int(train.stockout_next_7d.sum()))
neg = max(1, len(train)-pos)

clf = Pipeline([
    ("pre", pre2),
    ("model", XGBClassifier(
        n_estimators=250, max_depth=5, learning_rate=.05,
        subsample=.85, colsample_bytree=.85,
        scale_pos_weight=neg/pos,
        eval_metric="logloss", random_state=42, n_jobs=4
    ))
])

clf.fit(
    train[cls_features].copy().fillna(0),
    train.stockout_next_7d
)
prob = clf.predict_proba(test[cls_features].copy().fillna(0))[:,1]
pred = (prob >= .5).astype(int)

cls_metrics = {
    "accuracy": float(accuracy_score(test.stockout_next_7d,pred)),
    "precision": float(precision_score(test.stockout_next_7d,pred,zero_division=0)),
    "recall": float(recall_score(test.stockout_next_7d,pred,zero_division=0)),
    "f1": float(f1_score(test.stockout_next_7d,pred,zero_division=0)),
    "roc_auc": float(roc_auc_score(test.stockout_next_7d,prob))
}
with open(REPORT_DIR/"stockout_model_metrics.json","w") as f:
    json.dump(cls_metrics,f,indent=2)

joblib.dump(clf, MODEL_DIR/"stockout_xgb.joblib")

print("MODEL TRAINING COMPLETE")
print("\nDemand forecast:")
print(forecast_metrics.to_string(index=False))
print("\nStock-out:")
print(json.dumps(cls_metrics, indent=2))
