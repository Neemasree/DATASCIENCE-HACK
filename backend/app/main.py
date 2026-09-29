from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import APP_NAME, APP_VERSION, CORS_ORIGINS

app = FastAPI(
    title=APP_NAME,
    description=(
        "StockSense decision-support API for 7-day demand forecasting, "
        "stock-out risk, overstock detection and replenishment recommendations."
    ),
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/", tags=["System"])
def root():
    return {
        "service": APP_NAME,
        "status": "running",
        "version": APP_VERSION,
        "docs": "/docs",
        "api_base": "/api/v1",
    }


app.include_router(router)
