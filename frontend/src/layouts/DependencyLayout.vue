<template>
  <div class="flex min-h-screen flex-col bg-gray-50">

    <!-- ── Navbar horizontal ──────────────────────────────── -->
    <header class="sticky top-0 z-20 bg-white border-b border-ubpd-gris-borde shadow-sm">
      <div class="mx-auto flex max-w-7xl items-center gap-6 px-4 py-3 sm:px-6">

        <!-- Logo UBPD (área de reserva respetada) -->
        <router-link to="/dependencia" class="shrink-0 flex items-center">
          <img
            src="/logo-ubpd.png"
            alt="UBPD — Unidad de Búsqueda"
            class="h-10 w-auto"
          />
        </router-link>

        <!-- Nombre de la dependencia -->
        <span
          v-if="auth.user?.dependency_id"
          class="hidden sm:block text-sm font-medium text-ubpd-gris/70 truncate max-w-[180px]"
          :title="auth.user.nombre_completo"
        >
          {{ auth.user.nombre_completo }}
        </span>

        <!-- Separador flexible -->
        <div class="flex-1" />

        <!-- Links de navegación -->
        <nav class="flex items-center gap-1" aria-label="Menú usuario dependencia">
          <RouterLink
            to="/dependencia/inbox"
            class="nav-link"
            :class="{ 'nav-link-active': isActive('/dependencia/inbox') || isActive('/dependencia/forms') }"
          >
            <PhTray :size="18" aria-hidden="true" class="shrink-0" />
            <span class="hidden sm:inline">Mis Trámites</span>
          </RouterLink>

          <RouterLink
            to="/dependencia/templates"
            class="nav-link"
            :class="{ 'nav-link-active': isActive('/dependencia/templates') }"
          >
            <PhGridFour :size="18" aria-hidden="true" class="shrink-0" />
            <span class="hidden sm:inline">Formularios Disponibles</span>
          </RouterLink>

        </nav>

        <!-- Botón cerrar sesión -->
        <button
          class="btn-secondary ml-2 !px-3 !py-1.5 text-sm hidden sm:inline-flex"
          aria-label="Cerrar sesión"
          @click="handleLogout"
        >
          <PhSignOut :size="16" aria-hidden="true" />
          <span>Salir</span>
        </button>

        <!-- Menú móvil -->
        <button
          class="sm:hidden text-ubpd-gris"
          aria-label="Abrir menú"
          @click="mobileMenuOpen = !mobileMenuOpen"
        >
          <PhList :size="24" aria-hidden="true" />
        </button>
      </div>

      <!-- Dropdown móvil -->
      <Transition name="slide-down">
        <div
          v-if="mobileMenuOpen"
          class="sm:hidden border-t border-ubpd-gris-borde bg-white px-4 pb-3 space-y-1"
        >
          <RouterLink
            to="/dependencia/inbox"
            class="flex items-center gap-2 py-2 text-sm text-ubpd-gris"
            @click="mobileMenuOpen = false"
          >
            <PhTray :size="18" />Mis Trámites
          </RouterLink>
          <RouterLink
            to="/dependencia/templates"
            class="flex items-center gap-2 py-2 text-sm text-ubpd-gris"
            @click="mobileMenuOpen = false"
          >
            <PhGridFour :size="18" />Formularios Disponibles
          </RouterLink>
          <button
            class="flex items-center gap-2 py-2 text-sm text-ubpd-naranja w-full text-left"
            @click="handleLogout"
          >
            <PhSignOut :size="18" />Cerrar Sesión
          </button>
        </div>
      </Transition>
    </header>

    <!-- ── Contenido ─────────────────────────────────────── -->
    <main class="flex-1">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterView, RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useNotificationsStore } from '../stores/notifications'
import {
  PhTray,
  PhGridFour,
  PhSignOut,
  PhList,
} from '@phosphor-icons/vue'

const auth          = useAuthStore()
const notifications = useNotificationsStore()
const router        = useRouter()
const route         = useRoute()

const mobileMenuOpen = ref(false)

function isActive(path: string): boolean {
  return route.path.startsWith(path)
}

async function handleLogout() {
  try {
    await auth.logout()
    router.push('/login')
  } catch {
    notifications.error('No se pudo cerrar la sesión correctamente.')
  }
}
</script>

<style scoped>
.nav-link {
  @apply flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium
         text-ubpd-gris/70 hover:text-ubpd-teal hover:bg-ubpd-teal/5 transition-colors;
}
.nav-link-active {
  @apply text-ubpd-teal bg-ubpd-teal/10;
}

.slide-down-enter-active,
.slide-down-leave-active { transition: all 0.2s ease; }
.slide-down-enter-from,
.slide-down-leave-to { opacity: 0; transform: translateY(-8px); }
</style>
