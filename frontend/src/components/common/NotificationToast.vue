<template>
  <!-- Portal al body para estar siempre sobre el resto del contenido -->
  <Teleport to="body">
    <div
      class="pointer-events-none fixed top-4 right-4 z-[100] flex flex-col gap-2"
      aria-live="assertive"
      aria-atomic="false"
    >
      <TransitionGroup name="toast">
        <div
          v-for="n in store.notifications"
          :key="n.id"
          class="pointer-events-auto flex w-96 max-w-md items-start gap-3 rounded-xl bg-white
                 px-4 py-3 shadow-lg ring-1 ring-black/8"
          :class="ringColor(n.type)"
          role="alert"
        >
          <!-- Icono -->
          <div
            class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full"
            :class="iconBg(n.type)"
          >
            <component :is="iconFor(n.type)" :size="15" class="text-white" aria-hidden="true" />
          </div>

          <!-- Contenido (título + mensaje + detalles) -->
          <div class="flex-1 min-w-0 pt-0.5 space-y-1">
            <p
              v-if="n.title"
              class="text-sm font-semibold text-ubpd-gris leading-snug"
            >
              {{ n.title }}
            </p>
            <p
              class="text-sm text-ubpd-gris/90 leading-snug whitespace-pre-wrap break-words"
              :class="n.title ? 'text-xs' : ''"
            >
              {{ n.message }}
            </p>

            <!-- Detalles colapsables (lista de líneas, ideal para errores
                 de validación masivos del backend) -->
            <details
              v-if="n.details && n.details.length"
              class="mt-1.5 group"
            >
              <summary
                class="text-xs font-medium text-ubpd-teal cursor-pointer select-none
                       hover:underline"
              >
                Ver {{ n.details.length }} detalle{{ n.details.length === 1 ? '' : 's' }}
              </summary>
              <ul
                class="mt-1.5 max-h-48 overflow-y-auto pl-4 list-disc text-xs
                       text-ubpd-gris/80 space-y-0.5 border-l-2 border-gray-100 pl-3 ml-1"
              >
                <li
                  v-for="(d, i) in n.details"
                  :key="i"
                  class="break-words"
                >{{ d }}</li>
              </ul>
            </details>
          </div>

          <!-- Acciones (copiar + cerrar) -->
          <div class="flex items-start gap-1 shrink-0 ml-1">
            <!-- Copiar al portapapeles (título + mensaje + detalles) -->
            <button
              class="mt-0.5 text-ubpd-gris/40 hover:text-ubpd-teal transition-colors
                     relative px-1 py-0.5 rounded hover:bg-ubpd-teal/10"
              :aria-label="`Copiar notificación: ${n.title || n.message}`"
              :title="copiedId === n.id ? '¡Copiado!' : 'Copiar texto'"
              @click="copyToClipboard(n)"
            >
              <PhCheck v-if="copiedId === n.id" :size="14" class="text-ubpd-verde" aria-hidden="true" />
              <PhCopy v-else :size="14" aria-hidden="true" />
              <span
                v-if="copiedId === n.id"
                class="absolute -bottom-5 right-0 text-[10px] font-medium text-ubpd-verde
                       bg-white rounded px-1.5 py-0.5 shadow-sm whitespace-nowrap"
              >
                Copiado
              </span>
            </button>

            <!-- Botón cerrar -->
            <button
              class="mt-0.5 text-ubpd-gris/40 hover:text-ubpd-gris transition-colors
                     px-1 py-0.5 rounded hover:bg-gray-100"
              :aria-label="`Cerrar notificación: ${n.title || n.message}`"
              @click="store.remove(n.id)"
            >
              <PhX :size="14" aria-hidden="true" />
            </button>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useNotificationsStore, type Notification, type NotificationType } from '../../stores/notifications'
import {
  PhCheckCircle,
  PhWarningCircle,
  PhWarning,
  PhInfo,
  PhX,
  PhCopy,
  PhCheck,
} from '@phosphor-icons/vue'

const store = useNotificationsStore()

const iconComponents: Record<NotificationType, unknown> = {
  success: PhCheckCircle,
  error:   PhWarningCircle,
  warning: PhWarning,
  info:    PhInfo,
}

function iconFor(type: NotificationType) {
  return iconComponents[type]
}

const bgMap: Record<NotificationType, string> = {
  success: 'bg-ubpd-verde',
  error:   'bg-ubpd-naranja',
  warning: 'bg-yellow-500',
  info:    'bg-ubpd-teal',
}
function iconBg(type: NotificationType): string {
  return bgMap[type]
}

const ringMap: Record<NotificationType, string> = {
  success: 'ring-ubpd-verde/20',
  error:   'ring-ubpd-naranja/30',
  warning: 'ring-yellow-300',
  info:    'ring-ubpd-teal/20',
}
function ringColor(type: NotificationType): string {
  return ringMap[type]
}

// ─── Copiar al portapapeles ──────────────────────────────────────────────────
const copiedId = ref<string | null>(null)

/** Compone un texto plano con TODO el contenido de la notificación. */
function _formatForClipboard(n: Notification): string {
  const parts: string[] = []
  if (n.title) parts.push(n.title)
  if (n.message) parts.push(n.message)
  if (n.details && n.details.length) {
    parts.push('')
    parts.push('Detalles:')
    for (const d of n.details) parts.push(`  - ${d}`)
  }
  return parts.join('\n')
}

/** Copia el texto con fallback para navegadores sin Clipboard API
 *  (HTTP plano, contexts no-seguros, etc.). */
async function _writeText(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
      return true
    }
  } catch { /* fallback */ }
  try {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.focus(); ta.select()
    const ok = document.execCommand('copy')
    document.body.removeChild(ta)
    return ok
  } catch {
    return false
  }
}

async function copyToClipboard(n: Notification): Promise<void> {
  const ok = await _writeText(_formatForClipboard(n))
  if (ok) {
    copiedId.value = n.id
    setTimeout(() => { if (copiedId.value === n.id) copiedId.value = null }, 1800)
  }
}
</script>

<style scoped>
.toast-enter-active { transition: all 0.3s ease; }
.toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from   { opacity: 0; transform: translateX(100%) scale(0.95); }
.toast-leave-to     { opacity: 0; transform: translateX(100%) scale(0.95); }
.toast-move         { transition: transform 0.2s ease; }
</style>
