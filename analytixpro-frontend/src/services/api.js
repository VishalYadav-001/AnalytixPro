import axios from "axios"

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
})

// ── Request interceptor: attach JWT ──────────────────────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token")
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// ── Response interceptor: auto-refresh on 401 ────────────────
let isRefreshing = false
let failedQueue = []

function processQueue(error, token = null) {
  failedQueue.forEach((prom) => {
    if (error) prom.reject(error)
    else prom.resolve(token)
  })
  failedQueue = []
}

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config

    // Only attempt refresh on 401, and not on the refresh endpoint itself
    if (
      error.response?.status === 401 &&
      !original._retry &&
      !original.url?.includes("/auth/token/refresh/")
    ) {
      if (isRefreshing) {
        // Queue the request until refresh completes
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            original.headers.Authorization = `Bearer ${token}`
            return api(original)
          })
          .catch((err) => Promise.reject(err))
      }

      original._retry = true
      isRefreshing = true

      const refresh = localStorage.getItem("refresh_token")

      if (!refresh) {
        isRefreshing = false
        localStorage.removeItem("access_token")
        localStorage.removeItem("refresh_token")
        window.location.href = "/auth/login"
        return Promise.reject(error)
      }

      try {
        // Use plain axios (not api instance) to avoid interceptor loop
        const { data } = await axios.post("/api/auth/token/refresh/", { refresh })
        const newAccess = data.access

        localStorage.setItem("access_token", newAccess)
        api.defaults.headers.common.Authorization = `Bearer ${newAccess}`

        processQueue(null, newAccess)

        original.headers.Authorization = `Bearer ${newAccess}`
        return api(original)
      } catch (refreshError) {
        processQueue(refreshError, null)
        localStorage.removeItem("access_token")
        localStorage.removeItem("refresh_token")
        window.location.href = "/auth/login"
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

// ── Auth ─────────────────────────────────────────────────────
export const authService = {
  register:       (data) => api.post("/auth/register/", data),
  login:          (data) => api.post("/auth/login/", data),
  me:             ()     => api.get("/auth/me/"),
  updateMe:       (data) => api.patch("/auth/me/", data),
  changePassword: (data) => api.post("/auth/me/change-password/", data),
}

// ── Datasets ─────────────────────────────────────────────────
export const datasetService = {
  list:   ()        => api.get("/datasets/"),
  get:    (id)      => api.get(`/datasets/${id}/`),
  upload: (payload) => {
    const form = new FormData()
    form.append("file", payload.file)
    form.append("name", payload.name)
    return api.post("/datasets/", form, {
      headers: { "Content-Type": "multipart/form-data" },
    })
  },
  delete:      (id)       => api.delete(`/datasets/${id}/`),
  runAnalysis: (id, data) => api.post(`/datasets/${id}/run-analysis/`, data),
}

// ── Chat ─────────────────────────────────────────────────────
export const chatService = {
  list:        ()         => api.get("/chat-sessions/"),
  create:      (data)     => api.post("/chat-sessions/", data),
  get:         (id)       => api.get(`/chat-sessions/${id}/`),
  update:      (id, data) => api.patch(`/chat-sessions/${id}/`, data),
  delete:      (id)       => api.delete(`/chat-sessions/${id}/`),
  sendMessage: (id, data) => api.post(`/chat-sessions/${id}/send-message/`, data),
  messages:    (id)       => api.get(`/chat-sessions/${id}/messages/`),
}

// ── Analyses ─────────────────────────────────────────────────
export const analysisService = {
  list: ()   => api.get("/analyses/"),
  get:  (id) => api.get(`/analyses/${id}/`),
}

// ── Dashboards ───────────────────────────────────────────────
export const dashboardService = {
  list:     ()           => api.get("/dashboards/"),
  get:      (id)         => api.get(`/dashboards/${id}/`),
  generate: (analysisId) => api.post("/dashboards/generate/", { analysis_id: analysisId }),
  delete:   (id)         => api.delete(`/dashboards/${id}/`),
  export:   (id, fmt)    => api.post(`/dashboards/${id}/export/`, { format: fmt }),
  exports:  (id)         => api.get(`/dashboards/${id}/exports/`),
}

// ── Exported Reports ─────────────────────────────────────────
export const exportService = {
  list: ()   => api.get("/exports/"),
  get:  (id) => api.get(`/exports/${id}/`),
}

export default api