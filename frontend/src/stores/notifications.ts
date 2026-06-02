// ============================================================
// UBPD — Store de Notificaciones Toast (Pinia)
// ============================================================
//
// API (todas las funciones success/error/warning/info aceptan overloads):
//   notify.error('mensaje simple')
//   notify.error('Título', 'mensaje detallado')
//   notify.error('Título', 'mensaje', { duration: 10000, details: [...] })
//   notify.error('mensaje', { duration: 10000, details: [...] })
//   notify.error({ title, message, details, duration })
//
// `details` se renderiza como lista (útil para mostrar N errores de un
// upload de Excel o todas las validaciones que falló el backend).
// ============================================================

import { defineStore } from 'pinia'
import { ref } from 'vue'

export type NotificationType = 'success' | 'error' | 'warning' | 'info'

export interface NotificationOptions {
  duration?: number
  details?: string[]
}

export interface Notification {
  id: string
  type: NotificationType
  title?: string
  message: string
  details?: string[]
  duration?: number
}

interface NotificationInput {
  type?: NotificationType
  title?: string
  message: string
  details?: string[]
  duration?: number
}

type NotifyArgs =
  | [string]
  | [string, string]
  | [string, string, NotificationOptions]
  | [string, NotificationOptions]
  | [NotificationInput]

/** Normaliza los distintos overloads a un objeto NotificationInput */
function _normalize(args: NotifyArgs): NotificationInput {
  // Objeto completo
  if (args.length === 1 && typeof args[0] === 'object') {
    return args[0] as NotificationInput
  }
  // Un solo argumento string → mensaje
  if (args.length === 1) {
    return { message: args[0] as string }
  }
  // Dos args: (message, opts) ó (title, message)
  if (args.length === 2) {
    const [a, b] = args
    if (typeof b === 'object' && b !== null) {
      return { message: a as string, ...(b as NotificationOptions) }
    }
    return { title: a as string, message: b as string }
  }
  // Tres args: (title, message, opts)
  const [t, m, o] = args
  return { title: t as string, message: m as string, ...(o as NotificationOptions) }
}

export const useNotificationsStore = defineStore('notifications', () => {
  const notifications = ref<Notification[]>([])

  function add(input: NotificationInput): string {
    const id = `notif-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
    // Default duration: errores y warnings duran más para dar tiempo a leer el detalle
    const defaultDuration =
      input.type === 'error' ? 9000
      : input.type === 'warning' ? 6000
      : 4000
    const n: Notification = {
      id,
      type: input.type || 'info',
      title: input.title,
      message: input.message,
      details: input.details,
      duration: input.duration ?? defaultDuration,
    }
    notifications.value.push(n)

    if (n.duration && n.duration > 0) {
      setTimeout(() => remove(id), n.duration)
    }
    return id
  }

  function remove(id: string): void {
    const idx = notifications.value.findIndex((n) => n.id === id)
    if (idx !== -1) notifications.value.splice(idx, 1)
  }

  function clear(): void {
    notifications.value = []
  }

  function success(...args: NotifyArgs): string {
    return add({ type: 'success', ..._normalize(args) })
  }

  function error(...args: NotifyArgs): string {
    return add({ type: 'error', ..._normalize(args) })
  }

  function warning(...args: NotifyArgs): string {
    return add({ type: 'warning', ..._normalize(args) })
  }

  function info(...args: NotifyArgs): string {
    return add({ type: 'info', ..._normalize(args) })
  }

  return {
    notifications,
    add,
    remove,
    clear,
    success,
    error,
    warning,
    info,
  }
})
