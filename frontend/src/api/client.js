// Thin fetch wrapper (MASTER PRD §5 Step 4.4) -- every API call in the app goes through
// here so error handling and the base path are defined in exactly one place.
const BASE = "/api/v1";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    credentials: "include", // send/receive the login session cookie
    ...options,
  });
  if (!res.ok) {
    // A 401 on anything other than the login attempt itself means the session expired
    // (or the server restarted with a new SECRET_KEY, invalidating old cookies) mid-use
    // -- reload so App.jsx's getMe() check runs fresh and drops back to the login
    // screen, instead of leaving every open page silently broken.
    if (res.status === 401 && !path.startsWith("/auth/login")) {
      window.location.reload();
      return new Promise(() => {}); // reload is in flight; don't let callers race it
    }
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
  login: (username, password) =>
    request("/auth/login", { method: "POST", body: JSON.stringify({ username, password }) }),
  logout: () => request("/auth/logout", { method: "POST" }),
  getMe: () => request("/auth/me"),

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
  getLeadTimeline: (id) => request(`/leads/${id}/timeline`),
  getCrossChannelCopy: (id, platform) => request(`/leads/${id}/cross-channel-copy?platform=${platform}`),
  getAdjacentLead: (id, params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/leads/${id}/adjacent${qs ? `?${qs}` : ""}`);
  },
  updateLead: (id, data) => request(`/leads/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  patchLeadStatus: (id, status) =>
    request(`/leads/${id}/status`, { method: "PATCH", body: JSON.stringify({ status }) }),
  triggerOutreach: (id, { force = false } = {}) =>
    request(`/leads/${id}/outreach`, { method: "POST", body: JSON.stringify({ force }) }),
  getRecentReplies: (limit = 8) => request(`/leads/recent-replies?limit=${limit}`),
  markReplyRead: (conversationId) => request(`/inbound/${conversationId}/read`, { method: "PATCH" }),

  listMessageFormats: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/message-formats${qs ? `?${qs}` : ""}`);
  },
  createMessageFormat: (data) => request("/message-formats", { method: "POST", body: JSON.stringify(data) }),
  deactivateMessageFormat: (id) => request(`/message-formats/${id}`, { method: "DELETE" }),

  listContentAssets: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/content-assets${qs ? `?${qs}` : ""}`);
  },
  createContentAsset: (data) => request("/content-assets", { method: "POST", body: JSON.stringify(data) }),
  updateContentAsset: (id, data) => request(`/content-assets/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteContentAsset: (id) => request(`/content-assets/${id}`, { method: "DELETE" }),

  listKnowledgeBaseItems: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/knowledge-base${qs ? `?${qs}` : ""}`);
  },
  createKnowledgeBaseItem: (data) => request("/knowledge-base", { method: "POST", body: JSON.stringify(data) }),
  updateKnowledgeBaseItem: (id, data) => request(`/knowledge-base/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteKnowledgeBaseItem: (id) => request(`/knowledge-base/${id}`, { method: "DELETE" }),

  listCampaigns: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/campaigns${qs ? `?${qs}` : ""}`);
  },
  getCampaign: (id) => request(`/campaigns/${id}`),
  createCampaign: (data) => request("/campaigns", { method: "POST", body: JSON.stringify(data) }),
  updateCampaign: (id, data) => request(`/campaigns/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteCampaign: (id) => request(`/campaigns/${id}`, { method: "DELETE" }),
  getCampaignDailyReview: (id) => request(`/campaigns/${id}/daily-review`),
  clearCampaignWatchdogAlert: (id) => request(`/campaigns/${id}/watchdog/clear`, { method: "POST" }),

  // Phase 21 -- the unified AI to-do inbox. listTodos() returns every PENDING item across
  // every campaign/product; submitTodoFeedback/approveTodoItem/dismissTodoItem act on ONE
  // item at a time (replaces the old whole-day approveCampaignToday and the separate
  // listCampaignSuggestions -- both scopes now live in this one queue).
  listTodos: () => request("/todos"),
  submitTodoFeedback: (todoId, instruction) =>
    request(`/todos/${todoId}/feedback`, { method: "POST", body: JSON.stringify({ instruction }) }),
  approveTodoItem: (todoId) => request(`/todos/${todoId}/approve`, { method: "POST" }),
  dismissTodoItem: (todoId) => request(`/todos/${todoId}/dismiss`, { method: "POST" }),
  reviseKickoffDraft: (campaignId, instruction, currentDraft = null) =>
    request(`/campaigns/${campaignId}/kickoff-draft/revise`, {
      method: "POST",
      body: JSON.stringify({ instruction, current_draft: currentDraft }),
    }),
  setCampaignEmailRenderMode: (id, mode) =>
    request(`/campaigns/${id}/email-render-mode`, {
      method: "POST",
      body: JSON.stringify({ mode }),
    }),
  listStrategyInsights: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/strategy-insights${qs ? `?${qs}` : ""}`);
  },
  reviseOutreachDraft: (leadId, instruction, currentDraft = null) =>
    request(`/leads/${leadId}/outreach/revise-draft`, {
      method: "POST",
      body: JSON.stringify({ instruction, current_draft: currentDraft }),
    }),

  listBuiltinWhatsappTemplates: () => request("/whatsapp-templates/builtin"),
  listWhatsappTemplates: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/whatsapp-templates${qs ? `?${qs}` : ""}`);
  },
  createWhatsappTemplate: (data) => request("/whatsapp-templates", { method: "POST", body: JSON.stringify(data) }),
  updateWhatsappTemplate: (id, data) => request(`/whatsapp-templates/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  refreshWhatsappTemplate: (id) => request(`/whatsapp-templates/${id}/refresh`, { method: "POST" }),
  proposeWhatsappTemplate: (purpose, followupLevel, productId) => request("/whatsapp-templates/propose", {
    method: "POST",
    body: JSON.stringify(purpose ? {
      purpose,
      ...(followupLevel ? { followup_level: followupLevel } : {}),
      ...(productId ? { product_id: productId } : {}),
    } : {}),
  }),
  approveWhatsappTemplate: (id) => request(`/whatsapp-templates/${id}/approve`, { method: "POST" }),
  rejectWhatsappTemplate: (id) => request(`/whatsapp-templates/${id}/reject`, { method: "POST" }),
  deleteWhatsappTemplate: (id) => request(`/whatsapp-templates/${id}`, { method: "DELETE" }),

  listSocialQueue: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/social-queue${qs ? `?${qs}` : ""}`);
  },
  draftSocialMessage: (leadId, platform) =>
    request("/social-queue/draft", { method: "POST", body: JSON.stringify({ lead_id: leadId, platform }) }),
  markSocialSent: (id) => request(`/social-queue/${id}/sent`, { method: "POST" }),
  dismissSocialDraft: (id) => request(`/social-queue/${id}/dismiss`, { method: "POST" }),

  searchProspects: (data) => request("/prospects/search", { method: "POST", body: JSON.stringify(data) }),
  listProspects: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/prospects${qs ? `?${qs}` : ""}`);
  },
  listProspectSearches: () => request("/prospects/searches"),
  enrichProspect: (id) => request(`/prospects/${id}/enrich`, { method: "POST" }),

  listAlerts: () => request("/alerts"),

  getSystemLive: () => request("/system/live"),

  getDashboardWidgets: () => request("/dashboard/widgets"),
  saveDashboardWidgets: (widgets) =>
    request("/dashboard/widgets", { method: "PUT", body: JSON.stringify({ widgets }) }),

  getSettings: () => request("/settings"),
  patchSettings: (data) => request("/settings", { method: "PATCH", body: JSON.stringify(data) }),

  getEnvSettings: () => request("/env-settings"),
  patchEnvSettings: (data) => request("/env-settings", { method: "PATCH", body: JSON.stringify(data) }),

  getFunnel: () => request("/analytics/funnel"),
  getChannelPerformance: () => request("/analytics/channel-performance"),
  getTrend: (granularity, periods) => request(`/analytics/trend?granularity=${granularity}&periods=${periods}`),
  getByProduct: () => request("/analytics/by-product"),
  getOutreachFunnel: (start, end) => {
    const params = new URLSearchParams();
    if (start) params.set("start", start);
    if (end) params.set("end", end);
    const qs = params.toString();
    return request(`/analytics/outreach-funnel${qs ? `?${qs}` : ""}`);
  },
};
