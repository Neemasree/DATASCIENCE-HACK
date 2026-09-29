from functools import lru_cache
from pathlib import Path
import json
import pandas as pd
from fastapi import HTTPException

from app.core.config import OUTPUT_DIR, REPORT_DIR, MODEL_DIR, RISK_ORDER

DECISIONS_FILE = OUTPUT_DIR / "stocksense_decisions.csv"


def _json_records(df: pd.DataFrame):
    """Convert a dataframe into JSON-safe records."""
    if df.empty:
        return []
    return json.loads(
        df.where(pd.notna(df), None).to_json(
            orient="records",
            date_format="iso",
        )
    )


@lru_cache(maxsize=1)
def get_decisions() -> pd.DataFrame:
    """Load the scored decision table once per API process."""
    if not DECISIONS_FILE.exists():
        raise HTTPException(
            status_code=503,
            detail="Pipeline outputs are missing. Run 'python run_pipeline.py' first.",
        )

    df = pd.read_csv(DECISIONS_FILE, parse_dates=["date"])

    required = {
        "date", "store_id", "product_id", "category", "risk_level",
        "stockout_probability", "forecast_7d", "closing", "reorder_quantity",
        "overstock_flag", "revenue_at_risk", "manager_action",
        "confidence_level", "recommendation_confidence",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"stocksense_decisions.csv is missing columns: {missing}",
        )

    return df


def refresh_cache() -> None:
    """Clear cached CSV data after the pipeline is rerun."""
    get_decisions.cache_clear()


def latest_date(df: pd.DataFrame):
    return df["date"].max()


def latest_rows(df: pd.DataFrame) -> pd.DataFrame:
    date = latest_date(df)
    return df[df["date"] == date].copy()


def filter_actions(
    df: pd.DataFrame,
    risk: str | None = None,
    store_id: str | None = None,
    category: str | None = None,
    limit: int = 50,
) -> pd.DataFrame:
    view = latest_rows(df)

    if risk:
        view = view[view["risk_level"].str.upper() == risk.upper()]
    if store_id:
        view = view[view["store_id"].astype(str).str.upper() == store_id.upper()]
    if category:
        view = view[view["category"].astype(str).str.lower() == category.lower()]

    view["_risk_rank"] = view["risk_level"].map(RISK_ORDER).fillna(99)
    view = view.sort_values(
        ["_risk_rank", "stockout_probability", "revenue_at_risk"],
        ascending=[True, False, False],
    ).drop(columns="_risk_rank")
    return view.head(limit)


def get_metrics():
    result = {}

    forecast_file = REPORT_DIR / "forecast_model_metrics.csv"
    stockout_file = REPORT_DIR / "stockout_model_metrics.json"

    if forecast_file.exists():
        result["forecast"] = _json_records(pd.read_csv(forecast_file))
    if stockout_file.exists():
        result["stockout"] = json.loads(stockout_file.read_text(encoding="utf-8"))

    return result


def model_status():
    return {
        "demand_forecast_model": (MODEL_DIR / "demand_forecast_xgb.joblib").exists(),
        "stockout_model": (MODEL_DIR / "stockout_xgb.joblib").exists(),
    }


def records(df: pd.DataFrame):
    return _json_records(df)
