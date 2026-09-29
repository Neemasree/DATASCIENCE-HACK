"""Backward-compatible API entrypoint.

Keeps `uvicorn api:app --reload` working while the real application lives in app/.
"""
from app.main import app

__all__ = ["app"]
