// Thin fetch wrapper (MASTER PRD §5 Step 4.4) -- every API call in the app goes through
// here so error handling and the base path are defined in exactly one place.
const BASE = "/api/v1";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.error ? JSON.stringify(body.error) : detail;
    } catch {
      // response wasn't JSON -- keep statusText
    }
    throw new Error(`${res.status} ${detail}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  listProducts: () => request("/products"),
  getProduct: (id) => request(`/products/${id}`),
  createProduct: (data) => request("/products", { method: "POST", body: JSON.stringify(data) }),
  updateProduct: (id, data) => request(`/products/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  getProductStrategy: (id) => request(`/products/${id}/strategy`),
  addStrategyQueries: (id, queries) =>
    request(`/products/${id}/strategy/queries`, {
      method: "POST",
      body: JSON.stringify({ search_queries: queries }),
    }),

  listLeads: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/leads${qs ? `?${qs}` : ""}`);
  },
  getLead: (id) => request(`/leads/${id}`),
  patchLeadStatus: (id, status) =>
    request(`/leads/${id}/status`, { method: "PATCH", body: JSON.stringify({ status }) }),
  triggerOutreach: (id) => request(`/leads/${id}/outreach`, { method: "POST" }),

  listAlerts: () => request("/alerts"),

  getSettings: () => request("/settings"),
  patchSettings: (data) => request("/settings", { method: "PATCH", body: JSON.stringify(data) }),
};
