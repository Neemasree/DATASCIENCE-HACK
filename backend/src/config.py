
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data_raw"
CLEAN_DIR = BASE_DIR / "data_clean"
MODEL_DIR = BASE_DIR / "models"
OUTPUT_DIR = BASE_DIR / "outputs"
REPORT_DIR = OUTPUT_DIR / "reports"

RISK_HIGH = 0.70
RISK_MEDIUM = 0.40
OVERSTOCK_MULTIPLIER = 1.50
SAFETY_Z = 1.28
