<template>
  <div
    class="min-h-screen bg-white flex flex-col items-center justify-center px-4"
    :style="topoStyle"
  >
    <!-- Logo UBPD con área de reserva -->
    <div class="mb-8 flex flex-col items-center">
      <div class="w-48 h-20 flex items-center justify-center">
        <!-- Área de reserva del logo: ningún elemento invade este espacio -->
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-full bg-ubpd-teal flex items-center justify-center flex-shrink-0">
            <span class="text-white font-subtitulo font-bold text-xl">U</span>
          </div>
          <div>
            <p class="font-subtitulo font-bold text-ubpd-teal text-sm leading-tight">Unidad de Búsqueda</p>
            <p class="font-subtitulo font-bold text-ubpd-gris text-xs leading-tight">de Personas dadas por Desaparecidas</p>
          </div>
        </div>
      </div>
      <h1 class="mt-4 font-subtitulo font-bold text-2xl text-ubpd-gris tracking-wide">
        Sistema de Formularios
      </h1>
      <p class="font-cuerpo text-sm text-gray-500 mt-1">Plataforma Institucional UBPD</p>
    </div>

    <!-- Card de Login -->
    <div class="w-full max-w-md bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
      <div class="bg-ubpd-teal px-8 py-5">
        <h2 class="font-subtitulo font-semibold text-white text-lg">Iniciar Sesión</h2>
        <p class="font-cuerpo text-white/80 text-sm mt-1">Ingrese sus credenciales institucionales</p>
      </div>

      <form class="px-8 py-6 space-y-5" @submit.prevent="handleLogin" novalidate>
        <!-- Error general -->
        <div
          v-if="errorMessage"
          class="bg-orange-50 border border-ubpd-naranja/30 rounded-lg px-4 py-3 flex items-start gap-3"
          role="alert"
          aria-live="assertive"
        >
          <svg class="w-5 h-5 text-ubpd-naranja flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
          </svg>
          <p class="font-cuerpo text-sm text-ubpd-naranja">{{ errorMessage }}</p>
        </div>

        <!-- Username -->
        <div>
          <label for="username" class="block font-cuerpo font-medium text-sm text-ubpd-gris mb-1.5">
            Usuario
          </label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            autocomplete="username"
            placeholder="Nombre de usuario institucional"
            required
            :disabled="loading"
            class="w-full font-cuerpo text-sm border border-gray-300 rounded-lg px-4 py-2.5
                   focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20
                   disabled:bg-gray-50 disabled:cursor-not-allowed transition"
          />
        </div>

        <!-- Password -->
        <div>
          <label for="password" class="block font-cuerpo font-medium text-sm text-ubpd-gris mb-1.5">
            Contraseña
          </label>
          <div class="relative">
            <input
              id="password"
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="current-password"
              placeholder="Contraseña"
              required
              :disabled="loading"
              class="w-full font-cuerpo text-sm border border-gray-300 rounded-lg px-4 py-2.5 pr-11
                     focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20
                     disabled:bg-gray-50 disabled:cursor-not-allowed transition"
            />
            <button
              type="button"
              @click="showPassword = !showPassword"
              :aria-label="showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-ubpd-teal transition"
            >
              <svg v-if="!showPassword" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Botón Ingresar -->
        <button
          type="submit"
          :disabled="loading || !form.username || !form.password"
          class="w-full bg-ubpd-teal text-white font-cuerpo font-semibold text-sm
                 rounded-lg px-4 py-3 hover:bg-[#346d7a] transition
                 disabled:opacity-50 disabled:cursor-not-allowed
                 flex items-center justify-center gap-2"
        >
          <svg
            v-if="loading"
            class="animate-spin w-5 h-5"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span>{{ loading ? 'Verificando...' : 'Ingresar' }}</span>
        </button>
      </form>
    </div>

    <!-- Footer -->
    <p class="mt-8 font-cuerpo text-xs text-gray-400 text-center">
      Unidad de Búsqueda de Personas dadas por Desaparecidas &mdash; Sistema Institucional
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationsStore } from '@/stores/notifications'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const notifications = useNotificationsStore()
const authStore = useAuthStore()

const loading = ref(false)
const showPassword = ref(false)
const errorMessage = ref('')

const form = reactive({
  username: '',
  password: '',
})

// Patrón topográfico SVG sutil como fondo
const topoStyle = {
  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400'%3E%3Cg fill='none' stroke='%233E818F' stroke-width='0.5' opacity='0.08'%3E%3Cellipse cx='200' cy='200' rx='180' ry='100'/%3E%3Cellipse cx='200' cy='200' rx='150' ry='80'/%3E%3Cellipse cx='200' cy='200' rx='120' ry='60'/%3E%3Cellipse cx='200' cy='200' rx='90' ry='45'/%3E%3Cellipse cx='200' cy='200' rx='60' ry='30'/%3E%3Cellipse cx='200' cy='200' rx='30' ry='15'/%3E%3Cellipse cx='50' cy='50' rx='80' ry='50'/%3E%3Cellipse cx='350' cy='350' rx='80' ry='50'/%3E%3Cellipse cx='50' cy='350' rx='70' ry='40'/%3E%3Cellipse cx='350' cy='50' rx='70' ry='40'/%3E%3C/g%3E%3C/svg%3E")`,
  backgroundSize: '400px 400px',
}

async function handleLogin() {
  if (loading.value) return
  errorMessage.value = ''
  loading.value = true

  try {
    const { requiresPasswordChange } = await authStore.login(form.username, form.password)

    notifications.success(`Bienvenido/a, ${authStore.user?.nombre_completo ?? ''}`)

    if (requiresPasswordChange) {
      router.push('/change-password')
      return
    }

    router.push(authStore.getDefaultRoute())
  } catch (err: unknown) {
    const axiosErr = err as { response?: { status?: number } }
    if (axiosErr?.response?.status === 401 || axiosErr?.response?.status === 400) {
      errorMessage.value = 'Usuario o contraseña incorrectos. Verifique sus credenciales.'
    } else if (axiosErr?.response?.status === 403) {
      errorMessage.value = 'Su cuenta se encuentra inactiva. Comuníquese con el administrador.'
    } else {
      errorMessage.value = 'No fue posible conectar con el servidor. Intente nuevamente.'
    }
  } finally {
    loading.value = false
  }
}
</script>
