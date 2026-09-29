from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

checks = [
    ("/", 200),
    ("/api/v1/health", 200),
    ("/api/v1/summary", 200),
    ("/api/v1/dashboard", 200),
    ("/api/v1/actions?limit=5", 200),
    ("/api/v1/products", 200),
    ("/api/v1/stores", 200),
    ("/api/v1/categories", 200),
    ("/api/v1/metrics", 200),
    ("/docs", 200),
]

for path, expected in checks:
    response = client.get(path)
    print(f"{path:35} -> {response.status_code}")
    if response.status_code != expected:
        raise SystemExit(f"FAILED: {path}: {response.text}")

print("\nAPI VERIFICATION COMPLETE")
