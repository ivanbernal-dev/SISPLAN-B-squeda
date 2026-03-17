<template>
  <div class="p-6 space-y-6">
    <!-- Encabezado -->
    <div>
      <h1 class="font-subtitulo font-bold text-2xl text-ubpd-gris">Panel de Administración</h1>
      <p class="font-cuerpo text-sm text-gray-500 mt-1">
        Resumen del estado del sistema — Unidad de Búsqueda
      </p>
    </div>

    <!-- Cards de métricas -->
    <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5">
      <!-- Skeleton loading -->
      <template v-if="loading">
        <div
          v-for="i in 4"
          :key="i"
          class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 animate-pulse"
        >
          <div class="flex items-center justify-between mb-4">
            <div class="w-12 h-12 rounded-xl bg-gray-200" />
            <div class="w-16 h-5 rounded bg-gray-200" />
          </div>
          <div class="w-20 h-8 rounded bg-gray-200 mb-2" />
          <div class="w-32 h-4 rounded bg-gray-200" />
        </div>
      </template>

      <!-- Cards reales -->
      <template v-else>
        <!-- Total Formularios -->
        <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition">
          <div class="flex items-center justify-between mb-4">
            <div class="w-12 h-12 rounded-xl bg-ubpd-lila/10 flex items-center justify-center">
              <svg class="w-6 h-6 text-ubpd-lila" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414A1 1 0 0119 9.414V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <span class="text-xs font-cuerpo font-medium text-ubpd-lila bg-ubpd-lila/10 px-2.5 py-1 rounded-full">
              Formularios
            </span>
          </div>
          <p class="font-subtitulo font-bold text-3xl text-ubpd-gris">{{ stats?.total_formularios ?? 0 }}</p>
          <p class="font-cuerpo text-sm text-gray-500 mt-1">Registros en el sistema</p>
          <!-- Desglose por estado -->
          <div class="mt-3 flex flex-wrap gap-2">
            <span class="text-xs font-cuerpo px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
              {{ stats?.formularios_draft ?? 0 }} borrador
            </span>
            <span class="text-xs font-cuerpo px-2 py-0.5 rounded-full bg-ubpd-teal/10 text-ubpd-teal">
              {{ stats?.formularios_pending ?? 0 }} en revisión
            </span>
            <span class="text-xs font-cuerpo px-2 py-0.5 rounded-full bg-ubpd-verde/10 text-ubpd-verde">
              {{ stats?.formularios_approved ?? 0 }} validados
            </span>
            <span class="text-xs font-cuerpo px-2 py-0.5 rounded-full bg-orange-100 text-ubpd-naranja">
              {{ stats?.formularios_rejected ?? 0 }} devueltos
            </span>
          </div>
        </div>

        <!-- Usuarios activos -->
        <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition">
          <div class="flex items-center justify-between mb-4">
            <div class="w-12 h-12 rounded-xl bg-ubpd-verde/10 flex items-center justify-center">
              <svg class="w-6 h-6 text-ubpd-verde" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <span class="text-xs font-cuerpo font-medium text-ubpd-verde bg-ubpd-verde/10 px-2.5 py-1 rounded-full">
              Usuarios
            </span>
          </div>
          <p class="font-subtitulo font-bold text-3xl text-ubpd-gris">{{ stats?.usuarios_activos ?? 0 }}</p>
          <p class="font-cuerpo text-sm text-gray-500 mt-1">Usuarios activos en el sistema</p>
          <div class="mt-3 flex gap-2">
            <span class="text-xs font-cuerpo px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
              {{ stats?.total_usuarios ?? 0 }} total
            </span>
          </div>
        </div>

        <!-- Templates activos -->
        <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition">
          <div class="flex items-center justify-between mb-4">
            <div class="w-12 h-12 rounded-xl bg-ubpd-teal/10 flex items-center justify-center">
              <svg class="w-6 h-6 text-ubpd-teal" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
              </svg>
            </div>
            <span class="text-xs font-cuerpo font-medium text-ubpd-teal bg-ubpd-teal/10 px-2.5 py-1 rounded-full">
              Templates
            </span>
          </div>
          <p class="font-subtitulo font-bold text-3xl text-ubpd-gris">{{ stats?.templates_activos ?? 0 }}</p>
          <p class="font-cuerpo text-sm text-gray-500 mt-1">Plantillas de formularios activas</p>
          <div class="mt-3">
            <span class="text-xs font-cuerpo px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
              {{ stats?.total_templates ?? 0 }} total
            </span>
          </div>
        </div>

        <!-- Último pipeline -->
        <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition">
          <div class="flex items-center justify-between mb-4">
            <div class="w-12 h-12 rounded-xl bg-orange-50 flex items-center justify-center">
              <svg class="w-6 h-6 text-ubpd-naranja" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </div>
            <span
              class="text-xs font-cuerpo font-medium px-2.5 py-1 rounded-full"
              :class="pipelineBadgeClass"
            >
              {{ pipelineStatusLabel }}
            </span>
          </div>
          <p class="font-subtitulo font-bold text-3xl text-ubpd-gris">
            {{ stats?.pipelines_hoy ?? 0 }}
          </p>
          <p class="font-cuerpo text-sm text-gray-500 mt-1">Pipelines ejecutados hoy</p>
          <div v-if="stats?.ultimo_pipeline" class="mt-3">
            <p class="font-cuerpo text-xs text-gray-400">
              Último: {{ formatDate(stats.ultimo_pipeline.iniciado) }}
            </p>
          </div>
        </div>
      </template>
    </div>

    <!-- Error state -->
    <div
      v-if="error && !loading"
      class="bg-orange-50 border border-ubpd-naranja/30 rounded-xl px-5 py-4 flex items-center gap-3"
    >
      <svg class="w-5 h-5 text-ubpd-naranja flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
      </svg>
      <div>
        <p class="font-cuerpo font-medium text-sm text-ubpd-naranja">No se pudo cargar el resumen del sistema</p>
        <button @click="loadStats" class="font-cuerpo text-xs text-ubpd-teal hover:underline mt-1">
          Intentar de nuevo
        </button>
      </div>
    </div>

    <!-- Sección de accesos rápidos -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
      <RouterLink
        v-for="item in quickActions"
        :key="item.to"
        :to="item.to"
        class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5
               hover:shadow-md hover:border-ubpd-teal/30 transition group flex items-center gap-4"
      >
        <div class="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0" :class="item.iconBg">
          <component :is="item.icon" class="w-5 h-5" :class="item.iconColor" />
        </div>
        <div>
          <p class="font-subtitulo font-semibold text-sm text-ubpd-gris group-hover:text-ubpd-teal transition">
            {{ item.label }}
          </p>
          <p class="font-cuerpo text-xs text-gray-400 mt-0.5">{{ item.description }}</p>
        </div>
        <svg class="w-4 h-4 text-gray-300 ml-auto group-hover:text-ubpd-teal transition" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useNotificationsStore } from '@/stores/notifications'

interface StatsOverview {
  total_formularios: number
  formularios_draft: number
  formularios_pending: number
  formularios_approved: number
  formularios_rejected: number
  usuarios_activos: number
  total_usuarios: number
  templates_activos: number
  total_templates: number
  pipelines_hoy: number
  ultimo_pipeline?: {
    estado: 'success' | 'error' | 'running'
    iniciado: string
  }
}

const { get } = useApi()
const notifications = useNotificationsStore()

const loading = ref(true)
const error = ref(false)
const stats = ref<StatsOverview | null>(null)

async function loadStats() {
  loading.value = true
  error.value = false
  try {
    stats.value = await get<StatsOverview>('/admin/stats/overview')
  } catch {
    error.value = true
    notifications.error('No se pudo cargar el resumen del sistema')
  } finally {
    loading.value = false
  }
}

onMounted(loadStats)

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString('es-CO', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  })
}

const pipelineBadgeClass = computed(() => {
  const estado = stats.value?.ultimo_pipeline?.estado
  if (estado === 'success') return 'bg-ubpd-verde/10 text-ubpd-verde'
  if (estado === 'error') return 'bg-red-100 text-red-600'
  if (estado === 'running') return 'bg-yellow-100 text-yellow-700'
  return 'bg-gray-100 text-gray-500'
})

const pipelineStatusLabel = computed(() => {
  const estado = stats.value?.ultimo_pipeline?.estado
  if (estado === 'success') return 'Exitoso'
  if (estado === 'error') return 'Con error'
  if (estado === 'running') return 'En ejecución'
  return 'Sin datos'
})

// Íconos como componentes inline
const UsersIcon = { template: `<svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/></svg>` }
const TemplateIcon = { template: `<svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6z"/></svg>` }
const AuditIcon = { template: `<svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/></svg>` }

const quickActions = [
  { to: '/admin/users', label: 'Gestionar Usuarios', description: 'Crear, editar y desactivar usuarios', iconBg: 'bg-ubpd-verde/10', iconColor: 'text-ubpd-verde', icon: UsersIcon },
  { to: '/admin/templates', label: 'Templates de Formularios', description: 'Crear y editar plantillas Markdown', iconBg: 'bg-ubpd-teal/10', iconColor: 'text-ubpd-teal', icon: TemplateIcon },
  { to: '/admin/audit', label: 'Log de Auditoría', description: 'Revisar el historial de actividad', iconBg: 'bg-ubpd-lila/10', iconColor: 'text-ubpd-lila', icon: AuditIcon },
]
</script>
