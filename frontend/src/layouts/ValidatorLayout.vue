<template>
  <div class="flex h-screen overflow-hidden bg-gray-50">

    <!-- Overlay móvil -->
    <Transition name="fade">
      <div
        v-if="sidebarOpen && isMobile"
        class="fixed inset-0 z-20 bg-black/50"
        aria-hidden="true"
        @click="sidebarOpen = false"
      />
    </Transition>

    <!-- ── Sidebar ───────────────────────────────────────── -->
    <aside
      :class="[
        'fixed inset-y-0 left-0 z-30 flex w-60 flex-col bg-ubpd-teal text-white',
        'transition-transform duration-300',
        sidebarOpen || !isMobile ? 'translate-x-0' : '-translate-x-full',
        !isMobile ? 'relative translate-x-0' : '',
      ]"
      aria-label="Navegación validador"
    >
      <!-- Logo + nombre -->
      <div class="flex flex-col gap-2 px-5 pt-6 pb-4 border-b border-white/20">
        <router-link to="/validator/inbox" class="block">
          <img
            src="/logo-ubpd.png"
            alt="UBPD — Unidad de Búsqueda"
            class="h-auto w-full rounded-lg bg-white p-2 object-contain"
          />
        </router-link>
        <div class="mt-1">
          <p class="text-xs text-white/60 uppercase tracking-wider">Validador</p>
          <p class="text-sm font-semibold truncate">{{ auth.user?.nombre_completo ?? '—' }}</p>
        </div>
      </div>

      <!-- Navegación -->
      <nav class="flex-1 overflow-y-auto px-3 py-4 space-y-1" aria-label="Menú validador">

        <!-- Bandeja con contador de pendientes -->
        <RouterLink
          to="/validator/inbox"
          class="sidebar-item"
          :class="{ 'sidebar-item-active': isActive('/validator/inbox') }"
          aria-current-value="page"
        >
          <PhTray :size="20" aria-hidden="true" />
          <span class="flex-1">Bandeja de Entrada</span>
          <span
            v-if="pendingCount > 0"
            class="ml-auto flex h-5 min-w-[1.25rem] items-center justify-center
                   rounded-full bg-ubpd-naranja px-1.5 text-xs font-bold"
            :aria-label="`${pendingCount} formularios pendientes`"
          >
            {{ pendingCount > 99 ? '99+' : pendingCount }}
          </span>
        </RouterLink>

        <RouterLink
          to="/validator/history"
          class="sidebar-item"
          :class="{ 'sidebar-item-active': isActive('/validator/history') }"
        >
          <PhClockCounterClockwise :size="20" aria-hidden="true" />
          <span>Historial</span>
        </RouterLink>

        <RouterLink
          to="/validator/registros"
          class="sidebar-item"
          :class="{ 'sidebar-item-active': isActive('/validator/registros') }"
        >
          <PhFolderOpen :size="20" aria-hidden="true" />
          <span>Registros</span>
        </RouterLink>
      </nav>

      <!-- Cerrar sesión -->
      <div class="px-3 pb-5 border-t border-white/20 pt-3">
        <button
          class="sidebar-item w-full text-left text-white/70 hover:text-white"
          aria-label="Cerrar sesión"
          @click="handleLogout"
        >
          <PhSignOut :size="20" aria-hidden="true" />
          <span>Cerrar Sesión</span>
        </button>
      </div>
    </aside>

    <!-- ── Área principal ─────────────────────────────────── -->
    <div class="flex flex-1 flex-col min-w-0 overflow-hidden">

      <!-- Topbar móvil -->
      <header
        v-if="isMobile"
        class="flex items-center gap-4 border-b border-ubpd-gris-borde bg-white px-4 py-3"
      >
        <button
          class="text-ubpd-gris"
          aria-label="Abrir menú"
          @click="sidebarOpen = !sidebarOpen"
        >
          <PhList :size="24" aria-hidden="true" />
        </button>
        <img src="/logo-ubpd.png" alt="UBPD" class="h-8 w-auto" />
      </header>

      <main class="flex-1 overflow-y-auto">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { RouterView, RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useNotificationsStore } from '../stores/notifications'
import { apiGet } from '../composables/useApi'
import {
  PhTray,
  PhClockCounterClockwise,
  PhSignOut,
  PhList,
  PhFolderOpen,
} from '@phosphor-icons/vue'

const auth          = useAuthStore()
const notifications = useNotificationsStore()
const router        = useRouter()
const route         = useRoute()

const sidebarOpen = ref(true)
const windowWidth = ref(window.innerWidth)
const pendingCount = ref(0)

const isMobile = computed(() => windowWidth.value < 1024)

function isActive(path: string): boolean {
  return route.path.startsWith(path)
}

function handleResize() {
  windowWidth.value = window.innerWidth
  if (!isMobile.value) sidebarOpen.value = true
}

async function handleLogout() {
  try {
    await auth.logout()
    router.push('/login')
  } catch {
    notifications.error('No se pudo cerrar la sesión correctamente.')
  }
}

// ─── Polling contador de pendientes ───────────────────────
async function fetchPendingCount() {
  try {
    const data = await apiGet<{ total: number }>('/validation/pending?size=1')
    pendingCount.value = data.total ?? 0
  } catch {
    // Silencioso: no interrumpir la UI por un error de polling
  }
}

let pollingInterval: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  window.addEventListener('resize', handleResize)
  fetchPendingCount()
  pollingInterval = setInterval(fetchPendingCount, 30_000)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (pollingInterval) clearInterval(pollingInterval)
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }
</style>
