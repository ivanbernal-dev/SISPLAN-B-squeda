<template>
  <div class="flex h-screen overflow-hidden bg-gray-50">

    <!-- ── Overlay móvil ─────────────────────────────────── -->
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
        'fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-ubpd-teal text-white',
        'transition-transform duration-300',
        sidebarOpen || !isMobile ? 'translate-x-0' : '-translate-x-full',
        !isMobile ? 'relative translate-x-0' : '',
      ]"
      aria-label="Navegación principal administrador"
    >
      <!-- Logo + nombre usuario -->
      <div class="flex flex-col gap-2 px-5 pt-6 pb-4 border-b border-white/20">
        <RouterLink to="/admin" class="block">
          <img
            src="/logo-ubpd-placeholder.svg"
            alt="UBPD — Unidad de Búsqueda"
            class="h-10 w-auto"
          />
        </RouterLink>
        <div class="mt-1">
          <p class="text-xs text-white/60 uppercase tracking-wider">Administrador</p>
          <p class="text-sm font-semibold truncate">{{ auth.user?.nombre_completo ?? '—' }}</p>
        </div>
      </div>

      <!-- Navegación -->
      <nav class="flex-1 overflow-y-auto px-3 py-4 space-y-1" aria-label="Menú administrador">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="sidebar-item"
          :class="{ 'sidebar-item-active': isActive(item.to, item.exact) }"
          :aria-current="isActive(item.to, item.exact) ? 'page' : undefined"
          @click="closeSidebarOnMobile"
        >
          <component :is="item.icon" :size="20" aria-hidden="true" />
          <span>{{ item.label }}</span>
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
          class="text-ubpd-gris hover:text-ubpd-teal transition-colors"
          aria-label="Abrir menú"
          @click="sidebarOpen = !sidebarOpen"
        >
          <PhList :size="24" aria-hidden="true" />
        </button>
        <img src="/logo-ubpd-placeholder.svg" alt="UBPD" class="h-8 w-auto" />
      </header>

      <!-- Contenido de la vista -->
      <main class="flex-1 overflow-hidden flex flex-col">
        <RouterView v-slot="{ Component, route: r }">
          <component
            :is="Component"
            :class="r.name === 'AdminScriptPipeline' ? 'flex-1 overflow-hidden' : 'flex-1 overflow-y-auto p-6'"
          />
        </RouterView>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { RouterView, RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useNotificationsStore } from '../stores/notifications'
import {
  PhGauge,
  PhUsers,
  PhBuildings,
  PhFileText,
  PhClipboardText,
  PhSignOut,
  PhList,
  PhChartBar,
  PhChartLineUp,
  PhFolderOpen,
  PhCode,
} from '@phosphor-icons/vue'

// ─── Nav items ────────────────────────────────────────────
interface NavItem {
  label: string
  to:    string
  icon:  unknown
  exact?: boolean
}

const navItems: NavItem[] = [
  { label: 'Dashboard',    to: '/admin',               icon: PhGauge,         exact: true  },
  { label: 'Usuarios',     to: '/admin/users',         icon: PhUsers                       },
  { label: 'Dependencias', to: '/admin/dependencies',  icon: PhBuildings                   },
  { label: 'Templates',    to: '/admin/templates',     icon: PhFileText                    },
  { label: 'Registros',    to: '/admin/registros',     icon: PhFolderOpen                  },
  { label: 'Script Pipeline',  to: '/admin/script-pipeline',  icon: PhCode                        },
  { label: 'Indicadores',     to: '/admin/indicadores',      icon: PhChartBar                    },
  { label: 'Dashboard BI',    to: '/admin/bi-dashboard',     icon: PhChartLineUp                 },
  { label: 'Auditoría',       to: '/admin/audit',            icon: PhClipboardText               },
]

// ─── State ───────────────────────────────────────────────
const auth          = useAuthStore()
const notifications = useNotificationsStore()
const router        = useRouter()
const route         = useRoute()

const sidebarOpen = ref(true)
const windowWidth = ref(window.innerWidth)
const isMobile    = computed(() => windowWidth.value < 1024)

function isActive(path: string, exact = false): boolean {
  return exact ? route.path === path : route.path.startsWith(path)
}

function handleResize() {
  windowWidth.value = window.innerWidth
  if (!isMobile.value) sidebarOpen.value = true
}

function closeSidebarOnMobile() {
  if (isMobile.value) sidebarOpen.value = false
}

async function handleLogout() {
  try {
    await auth.logout()
    router.push('/login')
  } catch {
    notifications.error('No se pudo cerrar la sesión correctamente.')
  }
}

onMounted(() => window.addEventListener('resize', handleResize))
onUnmounted(() => window.removeEventListener('resize', handleResize))
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }
</style>
