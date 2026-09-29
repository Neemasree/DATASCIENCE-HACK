const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000/api/v1";

async function request(path) {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    let detail = `Request failed: ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch (_) {}
    throw new Error(detail);
  }
  return response.json();
}

export const api = {
  health: () => request("/health"),
  summary: () => request("/summary"),
  dashboard: () => request("/dashboard"),
  actions: ({ risk, storeId, category, limit = 50 } = {}) => {
    const params = new URLSearchParams();
    if (risk) params.set("risk", risk);
    if (storeId) params.set("store_id", storeId);
    if (category) params.set("category", category);
    params.set("limit", String(limit));
    return request(`/actions?${params.toString()}`);
  },
  products: () => request("/products"),
  stores: () => request("/stores"),
  categories: () => request("/categories"),
  product: (productId, storeId = "") => request(`/product/${encodeURIComponent(productId)}${storeId ? `?store_id=${encodeURIComponent(storeId)}` : ""}`),
  store: (storeId) => request(`/store/${encodeURIComponent(storeId)}`),
  trends: ({ storeId, productId, days = 30 } = {}) => {
    const params = new URLSearchParams({ days: String(days) });
    if (storeId) params.set("store_id", storeId);
    if (productId) params.set("product_id", productId);
    return request(`/trends?${params.toString()}`);
  },
  metrics: () => request("/metrics"),
};

export { API_BASE };
