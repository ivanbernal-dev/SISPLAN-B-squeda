// ============================================================
// UBPD — Store de Notificaciones Toast (Pinia)
// ============================================================

import { defineStore } from 'pinia'
import { ref } from 'vue'

export type NotificationType = 'success' | 'error' | 'warning' | 'info'

export interface Notification {
  id: string
  type: NotificationType
  message: string
  duration?: number
}

export const useNotificationsStore = defineStore('notifications', () => {
  const notifications = ref<Notification[]>([])

  function add(notification: Omit<Notification, 'id'>): string {
    const id = `notif-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
    const n: Notification = {
      id,
      duration: 4000,
      ...notification,
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

  function success(message: string, duration = 4000): string {
    return add({ type: 'success', message, duration })
  }

  function error(message: string, duration = 6000): string {
    return add({ type: 'error', message, duration })
  }

  function warning(message: string, duration = 5000): string {
    return add({ type: 'warning', message, duration })
  }

  function info(message: string, duration = 4000): string {
    return add({ type: 'info', message, duration })
  }

  return {
    notifications,
    add,
    remove,
    success,
    error,
    warning,
    info,
  }
})
