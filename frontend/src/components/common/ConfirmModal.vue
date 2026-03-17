<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        role="dialog"
        :aria-labelledby="modalTitleId"
        aria-modal="true"
        @keydown.esc="$emit('cancel')"
      >
        <!-- Overlay -->
        <div
          class="absolute inset-0 bg-black/50 backdrop-blur-sm"
          aria-hidden="true"
          @click="$emit('cancel')"
        />

        <!-- Panel -->
        <div
          class="relative bg-white rounded-2xl shadow-2xl max-w-md w-full mx-auto p-6 z-10
                 ring-1 ring-black/5"
        >
          <!-- Ícono -->
          <div
            class="w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4"
            :class="iconBg"
          >
            <svg v-if="resolvedVariant === 'danger'" class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
            </svg>
            <svg v-else class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>

          <!-- Contenido -->
          <h3 :id="modalTitleId" class="font-semibold text-lg text-ubpd-gris text-center mb-2">
            {{ title }}
          </h3>
          <p v-if="message" class="text-sm text-gray-500 text-center mb-6 leading-relaxed">
            {{ message }}
          </p>
          <!-- Slot para contenido adicional (e.g. textarea de rechazo) -->
          <slot />

          <!-- Acciones -->
          <div class="flex gap-3 justify-end mt-6">
            <button
              type="button"
              class="px-5 py-2.5 rounded-lg font-medium text-sm
                     border border-gray-300 text-ubpd-gris hover:bg-gray-50 transition"
              @click="$emit('cancel')"
            >
              Cancelar
            </button>
            <button
              type="button"
              :disabled="loading"
              class="px-5 py-2.5 rounded-lg font-semibold text-sm text-white transition
                     disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              :class="confirmBtnClass"
              @click="$emit('confirm')"
            >
              <svg v-if="loading" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  /** Controla la visibilidad del modal */
  isOpen:          boolean
  title?:          string
  message?:        string
  confirmText?:    string
  /** 'success' = verde, 'danger' = naranja/rojo */
  confirmVariant?: 'success' | 'danger'
  loading?:        boolean
}

const props = withDefaults(defineProps<Props>(), {
  title:           '¿Confirmar acción?',
  message:         undefined,
  confirmText:     'Confirmar',
  confirmVariant:  'success',
  loading:         false,
})

defineEmits<{
  confirm: []
  cancel:  []
}>()

// Alias interno para claridad
const resolvedVariant = computed(() => props.confirmVariant)

// ID único para aria-labelledby
const modalTitleId = `modal-title-${Math.random().toString(36).substring(2, 9)}`

const iconBg = computed(() =>
  resolvedVariant.value === 'danger' ? 'bg-ubpd-naranja' : 'bg-ubpd-verde',
)

const confirmBtnClass = computed(() =>
  resolvedVariant.value === 'danger'
    ? 'bg-ubpd-naranja hover:bg-orange-600'
    : 'bg-ubpd-verde hover:bg-[#469090]',
)
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s ease;
}
.modal-enter-active .relative,
.modal-leave-active .relative {
  transition: transform 0.25s ease, opacity 0.25s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .relative {
  transform: scale(0.95) translateY(-6px);
  opacity: 0;
}
</style>
