# StockSense Frontend

React + Vite dashboard for the NovaMart StockSense backend.

## Architecture

React/Vite -> FastAPI -> StockSense ML pipeline -> saved decisions/reports/models

Backend base URL:
`http://127.0.0.1:8000/api/v1`

## Requirements

- Node.js 18+ recommended
- StockSense FastAPI backend running on port 8000

## Setup

```powershell
npm install
copy .env.example .env
npm run dev
```

Open the Vite URL shown in the terminal, normally:
`http://localhost:5173`

## API contract used

- GET `/api/v1/health`
- GET `/api/v1/summary`
- GET `/api/v1/dashboard`
- GET `/api/v1/actions`
- GET `/api/v1/products`
- GET `/api/v1/stores`
- GET `/api/v1/categories`
- GET `/api/v1/product/{product_id}`
- GET `/api/v1/store/{store_id}`
- GET `/api/v1/trends`
- GET `/api/v1/metrics`

## Pages

- Operations Dashboard
- Risk Center
- Inventory Control
- Analytics & Models
- Product/store decision drawer

The UI reads data from the API only; it does not read CSVs or model files directly.
