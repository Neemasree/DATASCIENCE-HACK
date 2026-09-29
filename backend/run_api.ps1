# Start the StockSense FastAPI backend from the project root.
# Activate the virtual environment first if needed:
# .\venv\Scripts\Activate.ps1

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
