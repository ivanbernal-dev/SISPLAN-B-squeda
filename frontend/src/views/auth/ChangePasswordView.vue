<template>
  <div class="min-h-screen bg-ubpd-gris-claro flex flex-col items-center justify-center px-4">
    <div class="w-full max-w-md">
      <!-- Encabezado -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-ubpd-teal rounded-full mb-4">
          <svg class="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
        <h1 class="font-subtitulo font-bold text-2xl text-ubpd-gris">Actualizar Contraseña</h1>
        <p class="font-cuerpo text-sm text-gray-500 mt-2 max-w-xs mx-auto">
          Por seguridad, defina una nueva contraseña para su cuenta institucional
        </p>
      </div>

      <!-- Card -->
      <div class="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
        <div class="bg-ubpd-teal px-6 py-4">
          <p class="font-cuerpo text-white/90 text-sm">
            Complete los campos para establecer su nueva contraseña
          </p>
        </div>

        <form class="px-6 py-6 space-y-5" @submit.prevent="handleSubmit" novalidate>
          <!-- Error general -->
          <div
            v-if="errorMessage"
            class="bg-orange-50 border border-ubpd-naranja/30 rounded-lg px-4 py-3"
            role="alert"
          >
            <p class="font-cuerpo text-sm text-ubpd-naranja">{{ errorMessage }}</p>
          </div>

          <!-- Contraseña actual -->
          <div>
            <label for="current_password" class="block font-cuerpo font-medium text-sm text-ubpd-gris mb-1.5">
              Contraseña actual
            </label>
            <div class="relative">
              <input
                id="current_password"
                v-model="form.current_password"
                :type="showCurrent ? 'text' : 'password'"
                required
                :disabled="loading"
                placeholder="Contraseña temporal"
                class="w-full font-cuerpo text-sm border rounded-lg px-4 py-2.5 pr-11
                       focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20
                       disabled:bg-gray-50 disabled:cursor-not-allowed transition"
                :class="fieldErrors.current_password ? 'border-ubpd-naranja' : 'border-gray-300'"
              />
              <button type="button" @click="showCurrent = !showCurrent"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-ubpd-teal transition"
                :aria-label="showCurrent ? 'Ocultar' : 'Mostrar'">
                <EyeIcon :visible="showCurrent" />
              </button>
            </div>
            <p v-if="fieldErrors.current_password" class="mt-1 font-cuerpo text-xs text-ubpd-naranja">
              {{ fieldErrors.current_password }}
            </p>
          </div>

          <!-- Nueva contraseña -->
          <div>
            <label for="new_password" class="block font-cuerpo font-medium text-sm text-ubpd-gris mb-1.5">
              Nueva contraseña
            </label>
            <div class="relative">
              <input
                id="new_password"
                v-model="form.new_password"
                :type="showNew ? 'text' : 'password'"
                required
                :disabled="loading"
                placeholder="Mínimo 8 caracteres"
                class="w-full font-cuerpo text-sm border rounded-lg px-4 py-2.5 pr-11
                       focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20
                       disabled:bg-gray-50 disabled:cursor-not-allowed transition"
                :class="fieldErrors.new_password ? 'border-ubpd-naranja' : 'border-gray-300'"
              />
              <button type="button" @click="showNew = !showNew"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-ubpd-teal transition"
                :aria-label="showNew ? 'Ocultar' : 'Mostrar'">
                <EyeIcon :visible="showNew" />
              </button>
            </div>
            <!-- Indicador de fortaleza -->
            <div v-if="form.new_password" class="mt-2">
              <div class="flex gap-1 mb-1">
                <div
                  v-for="i in 4"
                  :key="i"
                  class="h-1 flex-1 rounded-full transition-colors"
                  :class="passwordStrength >= i ? strengthColor : 'bg-gray-200'"
                />
              </div>
              <p class="font-cuerpo text-xs" :class="strengthTextColor">{{ strengthLabel }}</p>
            </div>
            <p v-if="fieldErrors.new_password" class="mt-1 font-cuerpo text-xs text-ubpd-naranja">
              {{ fieldErrors.new_password }}
            </p>
          </div>

          <!-- Confirmar contraseña -->
          <div>
            <label for="confirm_password" class="block font-cuerpo font-medium text-sm text-ubpd-gris mb-1.5">
              Confirmar nueva contraseña
            </label>
            <div class="relative">
              <input
                id="confirm_password"
                v-model="form.confirm_password"
                :type="showConfirm ? 'text' : 'password'"
                required
                :disabled="loading"
                placeholder="Repita la nueva contraseña"
                class="w-full font-cuerpo text-sm border rounded-lg px-4 py-2.5 pr-11
                       focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20
                       disabled:bg-gray-50 disabled:cursor-not-allowed transition"
                :class="fieldErrors.confirm_password ? 'border-ubpd-naranja' : 'border-gray-300'"
              />
              <button type="button" @click="showConfirm = !showConfirm"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-ubpd-teal transition"
                :aria-label="showConfirm ? 'Ocultar' : 'Mostrar'">
                <EyeIcon :visible="showConfirm" />
              </button>
            </div>
            <p v-if="fieldErrors.confirm_password" class="mt-1 font-cuerpo text-xs text-ubpd-naranja">
              {{ fieldErrors.confirm_password }}
            </p>
          </div>

          <!-- Botón -->
          <button
            type="submit"
            :disabled="loading"
            class="w-full bg-ubpd-teal text-white font-cuerpo font-semibold text-sm
                   rounded-lg px-4 py-3 hover:bg-[#346d7a] transition
                   disabled:opacity-50 disabled:cursor-not-allowed
                   flex items-center justify-center gap-2"
          >
            <svg v-if="loading" class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span>{{ loading ? 'Actualizando...' : 'Actualizar Contraseña' }}</span>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationsStore } from '@/stores/notifications'
import { useAuthStore } from '@/stores/auth'

// Pequeño componente inline para el icono de ojo
const EyeIcon = {
  props: ['visible'],
  template: `
    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <template v-if="!visible">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
      </template>
      <template v-else>
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
      </template>
    </svg>
  `,
}

const router = useRouter()
const notifications = useNotificationsStore()
const authStore = useAuthStore()

const loading = ref(false)
const showCurrent = ref(false)
const showNew = ref(false)
const showConfirm = ref(false)
const errorMessage = ref('')

const form = reactive({
  current_password: '',
  new_password: '',
  confirm_password: '',
})

const fieldErrors = reactive({
  current_password: '',
  new_password: '',
  confirm_password: '',
})

// Indicador de fortaleza de contraseña
const passwordStrength = computed(() => {
  const p = form.new_password
  if (!p) return 0
  let score = 0
  if (p.length >= 8) score++
  if (/[A-Z]/.test(p)) score++
  if (/[0-9]/.test(p)) score++
  if (/[^A-Za-z0-9]/.test(p)) score++
  return score
})

const strengthColor = computed(() => {
  if (passwordStrength.value <= 1) return 'bg-ubpd-naranja'
  if (passwordStrength.value === 2) return 'bg-yellow-400'
  if (passwordStrength.value === 3) return 'bg-ubpd-verde'
  return 'bg-green-600'
})

const strengthTextColor = computed(() => {
  if (passwordStrength.value <= 1) return 'text-ubpd-naranja'
  if (passwordStrength.value === 2) return 'text-yellow-600'
  return 'text-ubpd-verde'
})

const strengthLabel = computed(() => {
  if (passwordStrength.value <= 1) return 'Contraseña débil'
  if (passwordStrength.value === 2) return 'Contraseña regular'
  if (passwordStrength.value === 3) return 'Contraseña buena'
  return 'Contraseña segura'
})

function validate(): boolean {
  let valid = true
  fieldErrors.current_password = ''
  fieldErrors.new_password = ''
  fieldErrors.confirm_password = ''

  if (!form.current_password) {
    fieldErrors.current_password = 'Ingrese su contraseña actual'
    valid = false
  }
  if (form.new_password.length < 8) {
    fieldErrors.new_password = 'La contraseña debe tener mínimo 8 caracteres'
    valid = false
  }
  if (form.new_password !== form.confirm_password) {
    fieldErrors.confirm_password = 'Las contraseñas no coinciden'
    valid = false
  }
  return valid
}

async function handleSubmit() {
  if (!validate()) return
  errorMessage.value = ''
  loading.value = true

  try {
    await authStore.changePassword(form.current_password, form.new_password)
    notifications.success('Su contraseña fue actualizada exitosamente')
    router.push(authStore.getDefaultRoute())
  } catch (err: unknown) {
    const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } }
    if (axiosErr?.response?.status === 400) {
      errorMessage.value = axiosErr.response?.data?.detail || 'La contraseña actual no es correcta'
    } else {
      errorMessage.value = 'Ocurrió un error al actualizar. Intente de nuevo.'
    }
  } finally {
    loading.value = false
  }
}
</script>
