
# StockSense — Backend / ML Pipeline

This package contains the **backend only** for the StockSense hackathon project.

No frontend is included here.

## Pipeline

```text
5 Raw CSVs
   ↓
Data Quality Audit
   ↓
Cleaning + Standardization
   ↓
Master Dataset
(one Date × Store × Product)
   ↓
EDA + Statistical Tests
   ↓
Feature Engineering
   ↓
7-Day Demand Forecast
   ↓
Stock-Out Probability
   ↓
Risk Level
   ↓
Overstock Detection
   ↓
Safety Stock
   ↓
Reorder Quantity
   ↓
Business Explanation
   ↓
Trust-Aware Recommendation
```

## Dataset

The included dataset is synthetic and follows the hackathon's five-file schema:

- transactions.csv
- products.csv
- stores.csv
- inventory.csv
- external_factors.csv

It is **not official organizer data**.

## What gets cleaned

### transactions
- duplicate transaction IDs
- negative quantities

### products
- category case/whitespace inconsistencies
- equivalent category names

### stores
- store ID standardization

### inventory
- opening + received - sold validation
- inventory mismatch flag
- reconciled closing value

### external factors
- missing temperature
- city-median imputation

### integration
- foreign-key validation

## Master dataset

The master dataset is built at:

**one row = one date × one store × one product**

Transactions are aggregated to daily demand before joining.

## ML targets

### Demand forecasting
Predict:

**next 7 days of demand**

### Stock-out classification
Predict:

**whether a stock-out occurs during the next 7 days**

## Risk rules

- probability >= 70% → HIGH
- 40% to <70% → MEDIUM
- <40% → LOW

## Replenishment

```text
Recommended Stock
= Forecast Demand + Safety Stock

Reorder Quantity
= max(
    0,
    Recommended Stock - Current Stock - Incoming Stock
  )
```

## Overstock

Prototype rule:

```text
Current Stock + Incoming Stock
> 1.5 × Forecast Demand
```

## Trust-aware recommendation

Confidence is a transparent decision-support score based on:

- historical coverage
- inventory consistency
- forecast reliability
- feature completeness

It is **not** a calibrated probability of model correctness.

## Run everything

```bash
pip install -r requirements.txt
python run_pipeline.py
```

## Important outputs

### Clean data
`data_clean/`

### Data quality report
`outputs/reports/data_quality_report.csv`

### Master dataset
`data_clean/master_dataset.csv`

### Forecast metrics
`outputs/reports/forecast_model_metrics.csv`

### Stock-out metrics
`outputs/reports/stockout_model_metrics.json`

### Final predictions
`outputs/stocksense_decisions.csv`

### Latest manager actions
`outputs/latest_manager_action_centre.csv`

### Saved models
`models/`

The frontend will later consume these backend outputs/API endpoints.

## API layer (frontend-ready)

The API is separated from the ML pipeline so the future React/Vite frontend can consume stable REST endpoints without changing the training code.

Architecture:

```text
React/Vite Frontend
        │
        │ HTTP GET / JSON
        ▼
FastAPI (app/main.py)
        │
        ├── Dashboard / Actions / Trends
        ├── Product / Store details
        └── Model metrics / Health
        │
        ▼
outputs/stocksense_decisions.csv
outputs/reports/*
models/*.joblib
```

### Start the API

After running the pipeline:

```powershell
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Or:

```powershell
.\run_api.ps1
```

Open:

- `http://127.0.0.1:8000/docs` — Swagger UI
- `http://127.0.0.1:8000/redoc` — ReDoc

### Frontend base URL

The future frontend should use:

```text
http://127.0.0.1:8000/api/v1
```

### Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/health` | API, pipeline and model readiness |
| `GET /api/v1/summary` | Latest inventory/risk KPIs |
| `GET /api/v1/dashboard` | One payload for the main dashboard |
| `GET /api/v1/actions` | Manager actions with risk/store/category filters |
| `GET /api/v1/products` | Product filter data |
| `GET /api/v1/stores` | Store filter data |
| `GET /api/v1/categories` | Category filter data |
| `GET /api/v1/product/{product_id}` | Product history and latest decision |
| `GET /api/v1/store/{store_id}` | Store summary and latest decisions |
| `GET /api/v1/trends` | Time-series data for charts |
| `GET /api/v1/metrics` | Forecast and stock-out model metrics |

`api.py` remains as a compatibility entrypoint, so `uvicorn api:app --reload` also works.

### API verification

```powershell
python verify_api.py
```

The API uses CORS for local React/Vite development on ports 5173 and 3000. Production frontend origins can be added later in `app/core/config.py`.
