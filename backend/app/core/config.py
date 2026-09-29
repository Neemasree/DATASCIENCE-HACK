from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = BASE_DIR / "outputs"
REPORT_DIR = OUTPUT_DIR / "reports"
MODEL_DIR = BASE_DIR / "models"

APP_NAME = "StockSense Backend API"
APP_VERSION = "1.0.0"
API_PREFIX = "/api/v1"

# Local React/Vite development origins.
# Add production frontend domains here later.
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

RISK_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
