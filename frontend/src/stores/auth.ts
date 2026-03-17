// ============================================================
// UBPD — Store de Autenticación (Pinia)
// Gestiona JWT, roles y estado de sesión
// ============================================================

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

// ─── Tipos ────────────────────────────────────────────────
export type UserRole = 'admin' | 'validator' | 'dependency_user'

export interface AuthUser {
  id: string
  username: string
  nombre_completo: string
  role: UserRole
  dependency_id: string | null
}

interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: {
    id: string
    nombre_completo: string
    role: string
    dependency_id: string | null
  }
}

/** Decodifica el payload de un JWT sin verificar firma (solo lectura de claims en frontend) */
function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const payload = token.split('.')[1]
    const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
    return JSON.parse(decoded) as Record<string, unknown>
  } catch {
    return null
  }
}

const LS_ACCESS  = 'ubpd_access_token'
const LS_REFRESH = 'ubpd_refresh_token'
const LS_USER    = 'ubpd_user'

// ─── Store ────────────────────────────────────────────────
export const useAuthStore = defineStore('auth', () => {
  // State
  const user         = ref<AuthUser | null>(null)
  const accessToken  = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)
  const isAdmin         = computed(() => user.value?.role === 'admin')
  const isValidator     = computed(() => user.value?.role === 'validator')
  const isDependencyUser = computed(() => user.value?.role === 'dependency_user')

  function hasRole(role: UserRole): boolean {
    return user.value?.role === role
  }

  /** Ruta home según rol activo */
  function getDefaultRoute(): string {
    if (!user.value) return '/login'
    switch (user.value.role) {
      case 'admin':           return '/admin'
      case 'validator':       return '/validator/inbox'
      case 'dependency_user': return '/dependencia'
      default:                return '/login'
    }
  }

  // ─── Actions ──────────────────────────────────────────

  /** Cargar tokens persistidos en localStorage al iniciar la app */
  function loadFromStorage(): void {
    const storedAccess  = localStorage.getItem(LS_ACCESS)
    const storedRefresh = localStorage.getItem(LS_REFRESH)
    const storedUser    = localStorage.getItem(LS_USER)

    if (!storedAccess) return

    // Verificar expiración del JWT
    const payload = decodeJwtPayload(storedAccess)
    const exp = payload?.['exp'] as number | undefined
    if (exp && Date.now() / 1000 > exp) {
      _clearStorage()
      return
    }

    accessToken.value  = storedAccess
    refreshToken.value = storedRefresh

    if (storedUser) {
      try {
        user.value = JSON.parse(storedUser) as AuthUser
      } catch {
        _clearStorage()
      }
    }
  }

  /** Iniciar sesión con username y password */
  async function login(
    username: string,
    password: string,
  ): Promise<{ requiresPasswordChange: boolean }> {
    const apiBase = import.meta.env.VITE_API_BASE_URL || '/api'
    const { data } = await axios.post<LoginResponse>(`${apiBase}/auth/login`, {
      username,
      password,
    })

    accessToken.value  = data.access_token
    refreshToken.value = data.refresh_token

    const jwtPayload = decodeJwtPayload(data.access_token)

    const authUser: AuthUser = {
      id:              data.user.id,
      username:        String(jwtPayload?.['username'] ?? username),
      nombre_completo: data.user.nombre_completo,
      role:            data.user.role as UserRole,
      dependency_id:   data.user.dependency_id,
    }
    user.value = authUser

    // Persistir
    localStorage.setItem(LS_ACCESS,  data.access_token)
    localStorage.setItem(LS_REFRESH, data.refresh_token)
    localStorage.setItem(LS_USER,    JSON.stringify(authUser))

    const requiresPasswordChange = Boolean(jwtPayload?.['requires_password_change'])
    return { requiresPasswordChange }
  }

  /** Cerrar sesión */
  async function logout(): Promise<void> {
    try {
      if (accessToken.value) {
        const apiBase = import.meta.env.VITE_API_BASE_URL || '/api'
        await axios.post(
          `${apiBase}/auth/logout`,
          {},
          { headers: { Authorization: `Bearer ${accessToken.value}` } },
        )
      }
    } finally {
      _clearState()
    }
  }

  /** Renovar access token usando el refresh token */
  async function refreshTokens(): Promise<void> {
    if (!refreshToken.value) throw new Error('No refresh token available')

    const apiBase = import.meta.env.VITE_API_BASE_URL || '/api'
    const { data } = await axios.post<{ access_token: string; refresh_token: string }>(
      `${apiBase}/auth/refresh`,
      { refresh_token: refreshToken.value },
    )

    accessToken.value  = data.access_token
    refreshToken.value = data.refresh_token

    localStorage.setItem(LS_ACCESS,  data.access_token)
    localStorage.setItem(LS_REFRESH, data.refresh_token)
  }

  /** Cambiar contraseña del usuario autenticado */
  async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
    const apiBase = import.meta.env.VITE_API_BASE_URL || '/api'
    await axios.post(
      `${apiBase}/auth/change-password`,
      { old_password: oldPassword, new_password: newPassword },
      { headers: { Authorization: `Bearer ${accessToken.value}` } },
    )
  }

  // ─── Helpers privados ─────────────────────────────────

  function _clearStorage(): void {
    localStorage.removeItem(LS_ACCESS)
    localStorage.removeItem(LS_REFRESH)
    localStorage.removeItem(LS_USER)
  }

  function _clearState(): void {
    user.value         = null
    accessToken.value  = null
    refreshToken.value = null
    _clearStorage()
  }

  return {
    // State (readonly desde componentes)
    user,
    accessToken,
    refreshToken,
    // Getters
    isAuthenticated,
    isAdmin,
    isValidator,
    isDependencyUser,
    hasRole,
    getDefaultRoute,
    // Actions
    loadFromStorage,
    login,
    logout,
    refreshTokens,
    changePassword,
  }
})
