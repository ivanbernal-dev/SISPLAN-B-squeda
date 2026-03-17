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
          class="pointer-events-auto flex w-80 max-w-sm items-start gap-3 rounded-xl bg-white
                 px-4 py-3 shadow-lg ring-1 ring-black/8"
          role="alert"
        >
          <!-- Icono -->
          <div
            class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full"
            :class="iconBg(n.type)"
          >
            <component :is="iconFor(n.type)" :size="15" class="text-white" aria-hidden="true" />
          </div>

          <!-- Mensaje -->
          <p class="flex-1 text-sm text-ubpd-gris leading-snug pt-0.5">
            {{ n.message }}
          </p>

          <!-- Botón cerrar -->
          <button
            class="ml-1 mt-0.5 text-ubpd-gris/40 hover:text-ubpd-gris transition-colors shrink-0"
            :aria-label="`Cerrar notificación: ${n.message}`"
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
</script>

<style scoped>
.toast-enter-active {
  transition: all 0.3s ease;
}
.toast-leave-active {
  transition: all 0.25s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(100%) scale(0.95);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(100%) scale(0.95);
}
.toast-move {
  transition: transform 0.2s ease;
}
</style>
