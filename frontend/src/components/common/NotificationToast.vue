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

          <!-- Botón cerrar -->
          <button
            class="ml-1 mt-0.5 text-ubpd-gris/40 hover:text-ubpd-gris transition-colors shrink-0"
            :aria-label="`Cerrar notificación: ${n.title || n.message}`"
            @click="store.remove(n.id)"
          >
            <PhX :size="14" aria-hidden="true" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { useNotificationsStore, type NotificationType } from '../../stores/notifications'
import {
  PhCheckCircle,
  PhWarningCircle,
  PhWarning,
  PhInfo,
  PhX,
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
</script>

<style scoped>
.toast-enter-active { transition: all 0.3s ease; }
.toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from   { opacity: 0; transform: translateX(100%) scale(0.95); }
.toast-leave-to     { opacity: 0; transform: translateX(100%) scale(0.95); }
.toast-move         { transition: transform 0.2s ease; }
</style>
