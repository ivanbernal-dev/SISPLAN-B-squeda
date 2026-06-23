<template>
  <div class="p-6 space-y-6">

    <!-- ══ HEADER ═══════════════════════════════════════════════════════════════ -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-ubpd-teal/10 flex items-center justify-center flex-shrink-0">
          <svg class="w-5 h-5 text-ubpd-teal" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293
                 l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <div>
          <h1 class="font-subtitulo font-bold text-xl text-ubpd-gris leading-tight">
            Formularios disponibles
          </h1>
          <p class="font-cuerpo text-sm text-gray-400 mt-0.5">
            Selecciona un formulario para iniciar un nuevo registro
          </p>
        </div>
      </div>

      <!-- Contador total -->
      <div v-if="!loading && templates.length > 0"
        class="flex-shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5
               bg-ubpd-teal/8 border border-ubpd-teal/20 rounded-xl">
        <span class="font-cuerpo text-xs font-semibold text-ubpd-teal">
          {{ templates.length }}
        </span>
        <span class="font-cuerpo text-xs text-gray-500">
          {{ templates.length === 1 ? 'formulario' : 'formularios' }}
        </span>
      </div>
    </div>

    <!-- ══ BUSCADOR ══════════════════════════════════════════════════════════════ -->
    <div v-if="!loading && templates.length > 0" class="relative">
      <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5">
        <svg class="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Buscar formulario por nombre o descripción..."
        class="w-full pl-10 pr-4 py-2.5 font-cuerpo text-sm border border-gray-200 rounded-xl
               bg-white text-ubpd-gris placeholder-gray-400
               focus:outline-none focus:border-ubpd-teal focus:ring-2 focus:ring-ubpd-teal/20
               transition-all duration-200"
      />
      <!-- Limpiar búsqueda -->
      <button
        v-if="searchQuery"
        type="button"
        class="absolute inset-y-0 right-0 flex items-center pr-3.5 text-gray-400
               hover:text-gray-600 transition-colors"
        @click="searchQuery = ''"
        aria-label="Limpiar búsqueda"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- ══ SKELETON ══════════════════════════════════════════════════════════════ -->
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <div
        v-for="n in 6"
        :key="n"
        class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden animate-pulse"
      >
        <div class="h-1.5 bg-gray-200 w-full" />
        <div class="p-5 space-y-3">
          <div class="h-4 bg-gray-200 rounded-full w-1/3" />
          <div class="h-5 bg-gray-200 rounded w-3/4 mt-1" />
          <div class="h-3.5 bg-gray-100 rounded w-full" />
          <div class="h-3.5 bg-gray-100 rounded w-5/6" />
          <div class="h-3.5 bg-gray-100 rounded w-4/6" />
          <div class="h-9 bg-gray-200 rounded-xl mt-4" />
        </div>
      </div>
    </div>

    <!-- ══ GRID DE FORMULARIOS ════════════════════════════════════════════════ -->
    <div
      v-else-if="filteredTemplates.length > 0"
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"
    >
      <div
        v-for="tmpl in filteredTemplates"
        :key="tmpl.id"
        class="group bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden
               flex flex-col hover:shadow-md hover:border-ubpd-teal/30 transition-all duration-200"
      >
        <!-- Barra de acento superior -->
        <div class="h-1.5 bg-gradient-to-r from-ubpd-teal to-teal-400 w-full" />

        <div class="p-5 flex flex-col gap-3 flex-1">

          <!-- Badge indicador -->
          <div class="flex items-center gap-2">
            <span
              class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full
                     font-cuerpo text-xs font-semibold bg-purple-50 text-ubpd-morado border border-purple-100"
            >
              <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9
                     a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5
                     a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              {{ tmpl.indicador_nombre ?? 'Indicador' }}
            </span>
          </div>

          <!-- Nombre -->
          <h2 class="font-subtitulo font-bold text-base text-ubpd-gris leading-snug">
            {{ tmpl.nombre }}
          </h2>

          <!-- Descripción -->
          <p class="font-cuerpo text-sm text-gray-500 leading-relaxed flex-1 line-clamp-3">
            {{ tmpl.descripcion ?? 'Sin descripción disponible.' }}
          </p>

          <!-- Separador -->
          <div class="border-t border-gray-100 pt-3 mt-auto">
            <button
              type="button"
              class="w-full flex items-center justify-center gap-2 py-2.5
                     bg-ubpd-teal text-white font-cuerpo font-semibold text-sm rounded-xl
                     hover:bg-teal-700 active:scale-[0.98] transition-all duration-150"
              @click="startForm(tmpl.id)"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M12 4v16m8-8H4" />
              </svg>
              Iniciar Formulario
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ══ SIN RESULTADOS DE BÚSQUEDA ════════════════════════════════════════ -->
    <div
      v-else-if="!loading && templates.length > 0 && filteredTemplates.length === 0"
      class="bg-white rounded-2xl border border-gray-100 shadow-sm py-16 text-center"
    >
      <div class="w-14 h-14 rounded-2xl bg-gray-100 flex items-center justify-center mx-auto mb-4">
        <svg class="w-7 h-7 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
      <p class="font-subtitulo font-semibold text-ubpd-gris">Sin resultados</p>
      <p class="font-cuerpo text-sm text-gray-400 mt-1">
        No se encontraron formularios que coincidan con
        <span class="font-medium text-ubpd-gris">"{{ searchQuery }}"</span>
      </p>
      <button
        type="button"
        class="mt-4 font-cuerpo text-sm text-ubpd-teal hover:underline"
        @click="searchQuery = ''"
      >
        Limpiar búsqueda
      </button>
    </div>

    <!-- ══ ESTADO VACÍO (sin formularios asignados) ════════════════════════ -->
    <div
      v-else-if="!loading && templates.length === 0"
      class="bg-white rounded-2xl border border-gray-100 shadow-sm py-20 text-center"
    >
      <div class="w-16 h-16 rounded-2xl bg-gray-100 flex items-center justify-center mx-auto mb-4">
        <svg class="w-8 h-8 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293
               l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <p class="font-subtitulo font-semibold text-ubpd-gris">
        No hay formularios disponibles
      </p>
      <p class="font-cuerpo text-sm text-gray-400 mt-1 max-w-xs mx-auto">
        Tu dependencia aún no tiene formularios asignados. Contacta al administrador para obtener acceso.
      </p>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'

interface Template {
  id: string
  nombre: string
  descripcion: string | null
  indicador_nivel1_id: number
  indicador_nombre?: string
}

const { get } = useApi()
const authStore = useAuthStore()
const notifications = useNotificationsStore()
const router = useRouter()

const loading = ref(true)
const templates = ref<Template[]>([])
const searchQuery = ref('')

const filteredTemplates = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return templates.value
  return templates.value.filter(
    (t) =>
      t.nombre.toLowerCase().includes(q) ||
      (t.descripcion ?? '').toLowerCase().includes(q) ||
      (t.indicador_nombre ?? '').toLowerCase().includes(q),
  )
})

async function loadTemplates() {
  loading.value = true
  const depId = authStore.user?.dependency_id
  if (!depId) {
    notifications.warning('Sin dependencia', 'Tu usuario no tiene una dependencia asignada.')
    loading.value = false
    return
  }
  try {
    templates.value = await get<Template[]>(`/templates/by-dependency/${depId}`)
  } catch {
    notifications.error('Error', 'No se pudieron cargar los formularios disponibles.')
  } finally {
    loading.value = false
  }
}

function startForm(templateId: string) {
  router.push(`/dependencia/forms/new/${templateId}`)
}

onMounted(loadTemplates)
</script>
