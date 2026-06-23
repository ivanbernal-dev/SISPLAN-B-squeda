// ============================================================
// UBPD — Composable useApi
// Instancia Axios con interceptores JWT y refresh automático
// ============================================================

import axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

// ─── Instancia Axios ──────────────────────────────────────
const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
})

// ─── Interceptor de Request: inyectar Bearer token ────────
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('ubpd_access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: unknown) => Promise.reject(error),
)

// Bandera para evitar bucles infinitos de refresh
let _isRefreshing = false
let _pendingQueue: Array<{
  resolve: (token: string) => void
  reject: (err: unknown) => void
}> = []

function _processQueue(error: unknown, token: string | null = null): void {
  _pendingQueue.forEach((p) => {
    if (error) p.reject(error)
    else p.resolve(token as string)
  })
  _pendingQueue = []
}

// ─── Interceptor de Response: refresh automático en 401 ───
apiClient.interceptors.response.use(
  (response) => response,
  async (error: unknown) => {
    if (!axios.isAxiosError(error)) return Promise.reject(error)

    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (_isRefreshing) {
        // Encolar mientras se está refrescando
        return new Promise((resolve, reject) => {
          _pendingQueue.push({ resolve, reject })
        }).then((token) => {
          if (originalRequest.headers)
            originalRequest.headers.Authorization = `Bearer ${token}`
          return apiClient(originalRequest)
        })
      }

      originalRequest._retry = true
      _isRefreshing = true

      const storedRefresh = localStorage.getItem('ubpd_refresh_token')

      if (!storedRefresh) {
        _processQueue(error, null)
        _isRefreshing = false
        _redirectToLogin()
        return Promise.reject(error)
      }

      try {
        const { data } = await axios.post<{ access_token: string; refresh_token: string }>(
          `${BASE_URL}/auth/refresh`,
          { refresh_token: storedRefresh },
        )
        localStorage.setItem('ubpd_access_token', data.access_token)
        localStorage.setItem('ubpd_refresh_token', data.refresh_token)

        apiClient.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
        _processQueue(null, data.access_token)

        if (originalRequest.headers)
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`

        return apiClient(originalRequest)
      } catch (refreshError) {
        _processQueue(refreshError, null)
        _redirectToLogin()
        return Promise.reject(refreshError)
      } finally {
        _isRefreshing = false
      }
    }

    return Promise.reject(error)
  },
)

function _redirectToLogin(): void {
  localStorage.removeItem('ubpd_access_token')
  localStorage.removeItem('ubpd_refresh_token')
  localStorage.removeItem('ubpd_user')
  // Evitar bucle si ya estamos en login
  if (!window.location.pathname.includes('/login')) {
    window.location.href = '/login'
  }
}

// ─── Funciones tipadas de alto nivel ─────────────────────

export async function apiGet<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const res: AxiosResponse<T> = await apiClient.get(url, config)
  return res.data
}

export async function apiPost<T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig,
): Promise<T> {
  const res: AxiosResponse<T> = await apiClient.post(url, data, config)
  return res.data
}

export async function apiPatch<T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig,
): Promise<T> {
  const res: AxiosResponse<T> = await apiClient.patch(url, data, config)
  return res.data
}

export async function apiDelete<T = void>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const res: AxiosResponse<T> = await apiClient.delete(url, config)
  return res.data
}

/** Enviar multipart/form-data (subida de archivos) */
export async function apiPostForm<T>(url: string, formData: FormData): Promise<T> {
  const res: AxiosResponse<T> = await apiClient.post(url, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

// ─── Composable ───────────────────────────────────────────
export function useApi() {
  return {
    get:      apiGet,
    post:     apiPost,
    patch:    apiPatch,
    del:      apiDelete,   // 'delete' es palabra reservada; usar 'del' como alias
    postForm: apiPostForm,
    client:   apiClient,
  }
}

export default apiClient
