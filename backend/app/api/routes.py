from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.services.data_service import (
    filter_actions,
    get_decisions,
    get_metrics,
    latest_date,
    latest_rows,
    model_status,
    records,
)
from app.core.config import API_PREFIX

router = APIRouter(prefix=API_PREFIX)


@router.get("/health", tags=["System"])
def health():
    """Return API, pipeline and saved-model availability."""
    df_ready = True
    try:
        df = get_decisions()
        rows = len(df)
    except HTTPException:
        df_ready = False
        rows = 0

    models = model_status()
    return {
        "api": "ok",
        "pipeline_outputs_available": df_ready,
        "decision_rows": rows,
        "models": models,
        "ready_for_frontend": df_ready and all(models.values()),
    }


@router.get("/summary", tags=["Dashboard"])
def summary():
    df = get_decisions()
    view = latest_rows(df)

    return {
        "latest_date": latest_date(df).date().isoformat(),
        "rows": int(len(view)),
        "high_risk": int((view["risk_level"] == "HIGH").sum()),
        "medium_risk": int((view["risk_level"] == "MEDIUM").sum()),
        "low_risk": int((view["risk_level"] == "LOW").sum()),
        "overstock_rows": int(view["overstock_flag"].sum()),
        "reorder_units": int(view["reorder_quantity"].sum()),
        "revenue_at_risk": float(view["revenue_at_risk"].sum()),
        "high_risk_reorder_units": int(
            view.loc[view["risk_level"] == "HIGH", "reorder_quantity"].sum()
        ),
    }


@router.get("/dashboard", tags=["Dashboard"])
def dashboard():
    """Single frontend-friendly payload for the main dashboard."""
    df = get_decisions()
    latest = latest_rows(df)

    risk_distribution = (
        latest["risk_level"].value_counts()
        .reindex(["HIGH", "MEDIUM", "LOW"], fill_value=0)
        .rename_axis("risk_level")
        .reset_index(name="count")
    )

    category_summary = (
        latest.groupby("category", dropna=False)
        .agg(
            products=("product_id", "count"),
            high_risk=("risk_level", lambda x: int((x == "HIGH").sum())),
            medium_risk=("risk_level", lambda x: int((x == "MEDIUM").sum())),
            reorder_units=("reorder_quantity", "sum"),
            revenue_at_risk=("revenue_at_risk", "sum"),
        )
        .reset_index()
        .sort_values("high_risk", ascending=False)
    )

    return {
        "summary": summary(),
        "risk_distribution": records(risk_distribution),
        "category_summary": records(category_summary),
        "top_actions": records(filter_actions(df, limit=10)),
    }


@router.get("/actions", tags=["Actions"])
def actions(
    risk: Optional[str] = Query(default=None, pattern="^(HIGH|MEDIUM|LOW)$"),
    store_id: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=500),
):
    df = get_decisions()
    view = filter_actions(df, risk=risk, store_id=store_id, category=category, limit=limit)

    return {
        "latest_date": latest_date(df).date().isoformat(),
        "count": int(len(view)),
        "filters": {"risk": risk, "store_id": store_id, "category": category},
        "items": records(view),
    }


@router.get("/products", tags=["Reference Data"])
def products():
    df = latest_rows(get_decisions())
    result = (
        df[["product_id", "category", "sub_category"]]
        .drop_duplicates()
        .sort_values("product_id")
    )
    return {"count": len(result), "items": records(result)}


@router.get("/stores", tags=["Reference Data"])
def stores():
    df = latest_rows(get_decisions())
    cols = [c for c in ["store_id", "city", "store_type", "region"] if c in df.columns]
    result = df[cols].drop_duplicates().sort_values("store_id")
    return {"count": len(result), "items": records(result)}


@router.get("/categories", tags=["Reference Data"])
def categories():
    df = latest_rows(get_decisions())
    values = sorted(df["category"].dropna().astype(str).unique().tolist())
    return {"count": len(values), "items": values}


@router.get("/product/{product_id}", tags=["Products"])
def product(product_id: str, store_id: Optional[str] = None):
    df = get_decisions()
    view = df[df["product_id"].astype(str).str.upper() == product_id.upper()].copy()

    if store_id:
        view = view[view["store_id"].astype(str).str.upper() == store_id.upper()]

    if view.empty:
        raise HTTPException(status_code=404, detail="Product/store combination not found")

    latest = view["date"].max()
    return {
        "product_id": product_id,
        "store_id": store_id,
        "latest_date": latest.date().isoformat(),
        "latest": records(view[view["date"] == latest]),
        "history": records(view.sort_values("date")),
    }


@router.get("/store/{store_id}", tags=["Stores"])
def store(store_id: str):
    df = get_decisions()
    view = df[df["store_id"].astype(str).str.upper() == store_id.upper()].copy()

    if view.empty:
        raise HTTPException(status_code=404, detail="Store not found")

    latest = view["date"].max()
    latest_view = view[view["date"] == latest]

    return {
        "store_id": store_id,
        "latest_date": latest.date().isoformat(),
        "summary": {
            "high_risk": int((latest_view["risk_level"] == "HIGH").sum()),
            "medium_risk": int((latest_view["risk_level"] == "MEDIUM").sum()),
            "low_risk": int((latest_view["risk_level"] == "LOW").sum()),
            "reorder_units": int(latest_view["reorder_quantity"].sum()),
            "overstock_rows": int(latest_view["overstock_flag"].sum()),
            "revenue_at_risk": float(latest_view["revenue_at_risk"].sum()),
        },
        "items": records(latest_view),
    }


@router.get("/trends", tags=["Analytics"])
def trends(
    store_id: Optional[str] = None,
    product_id: Optional[str] = None,
    days: int = Query(default=30, ge=7, le=120),
):
    df = get_decisions().copy()

    if store_id:
        df = df[df["store_id"].astype(str).str.upper() == store_id.upper()]
    if product_id:
        df = df[df["product_id"].astype(str).str.upper() == product_id.upper()]

    if df.empty:
        raise HTTPException(status_code=404, detail="No trend data found for the selected filters")

    max_date = df["date"].max()
    min_date = max_date - pd.Timedelta(days=days - 1)
    view = df[df["date"] >= min_date]

    daily = (
        view.groupby("date", as_index=False)
        .agg(
            forecast_7d=("forecast_7d", "sum"),
            current_stock=("closing", "sum"),
            reorder_units=("reorder_quantity", "sum"),
            revenue_at_risk=("revenue_at_risk", "sum"),
        )
        .sort_values("date")
    )

    return {
        "from_date": min_date.date().isoformat(),
        "to_date": max_date.date().isoformat(),
        "filters": {"store_id": store_id, "product_id": product_id},
        "items": records(daily),
    }


@router.get("/metrics", tags=["Models"])
def metrics():
    return get_metrics()
