<template>
  <div class="p-6 space-y-5">
    <!-- Encabezado -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="font-subtitulo font-bold text-2xl text-ubpd-gris">Monitor de Pipelines</h1>
        <p class="font-cuerpo text-sm text-gray-500 mt-1">
          Estado de ejecución de los procesos de datos
          <span v-if="lastRefresh" class="ml-2 text-gray-400">
            — Actualizado {{ formatRelative(lastRefresh) }}
          </span>
        </p>
      </div>
      <div class="flex items-center gap-2">
        <RouterLink
          to="/admin/pipeline-editor"
          class="inline-flex items-center gap-2 bg-ubpd-teal text-white font-cuerpo font-semibold text-sm
                 rounded-xl px-5 py-2.5 hover:bg-[#346d7a] transition"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Nuevo Pipeline
        </RouterLink>
        <button
          @click="loadPipelines"
          :disabled="loading"
          class="inline-flex items-center gap-2 border border-ubpd-teal text-ubpd-teal font-cuerpo font-semibold text-sm
                 rounded-xl px-5 py-2.5 hover:bg-ubpd-teal hover:text-white transition disabled:opacity-50"
        >
          <svg class="w-4 h-4 transition-transform" :class="loading ? 'animate-spin' : ''"
            fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Actualizar
        </button>
      </div>
    </div>

    <!-- Resumen de estados -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <div
        v-for="item in statusSummary"
        :key="item.label"
        class="bg-white rounded-xl border border-gray-100 shadow-sm px-4 py-3 flex items-center gap-3"
      >
        <div class="w-3 h-3 rounded-full flex-shrink-0" :class="item.dot" />
        <div>
          <p class="font-subtitulo font-bold text-xl text-ubpd-gris">{{ item.count }}</p>
          <p class="font-cuerpo text-xs text-gray-400">{{ item.label }}</p>
        </div>
      </div>
    </div>

    <!-- Tabla de pipelines -->
    <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <!-- Loading -->
      <div v-if="loading" class="divide-y divide-gray-50">
        <div v-for="i in 6" :key="i" class="px-6 py-4 flex items-center gap-4 animate-pulse">
          <div class="w-3 h-3 rounded-full bg-gray-200" />
          <div class="w-24 h-4 rounded bg-gray-200" />
          <div class="w-32 h-4 rounded bg-gray-200" />
          <div class="flex-1 h-4 rounded bg-gray-200" />
          <div class="w-20 h-4 rounded bg-gray-200" />
          <div class="w-16 h-4 rounded bg-gray-200" />
        </div>
      </div>

      <!-- Datos -->
      <div v-else-if="pipelines.length > 0">
        <table class="w-full">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide">Estado</th>
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide">Tipo</th>
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide hidden md:table-cell">Formulario</th>
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide">Iniciado</th>
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide hidden lg:table-cell">Terminado</th>
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide hidden lg:table-cell">Duración</th>
              <th class="px-6 py-3"></th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="pipe in pipelines" :key="pipe.id" class="hover:bg-gray-50/50 transition">
              <td class="px-6 py-4">
                <!-- Semáforo de estado -->
                <div class="flex items-center gap-2">
                  <div
                    class="w-3 h-3 rounded-full flex-shrink-0"
                    :class="{
                      'bg-ubpd-verde': pipe.estado === 'success',
                      'bg-red-500': pipe.estado === 'error',
                      'bg-yellow-400 animate-pulse': pipe.estado === 'running',
                      'bg-gray-400': pipe.estado === 'pending',
                    }"
                  />
                  <span
                    class="font-cuerpo text-xs font-medium px-2 py-0.5 rounded-full"
                    :class="{
                      'bg-ubpd-verde/10 text-ubpd-verde': pipe.estado === 'success',
                      'bg-red-100 text-red-600': pipe.estado === 'error',
                      'bg-yellow-100 text-yellow-700': pipe.estado === 'running',
                      'bg-gray-100 text-gray-500': pipe.estado === 'pending',
                    }"
                  >
                    {{ estadoLabel(pipe.estado) }}
                  </span>
                </div>
              </td>
              <td class="px-6 py-4">
                <span class="font-cuerpo text-sm text-ubpd-gris">{{ pipe.tipo }}</span>
              </td>
              <td class="px-6 py-4 hidden md:table-cell">
                <span class="font-mono text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                  {{ pipe.formulario_id ? truncateId(pipe.formulario_id) : '—' }}
                </span>
              </td>
              <td class="px-6 py-4">
                <span class="font-cuerpo text-sm text-gray-600">{{ formatDate(pipe.iniciado) }}</span>
              </td>
              <td class="px-6 py-4 hidden lg:table-cell">
                <span class="font-cuerpo text-sm text-gray-600">
                  {{ pipe.terminado ? formatDate(pipe.terminado) : '—' }}
                </span>
              </td>
              <td class="px-6 py-4 hidden lg:table-cell">
                <span class="font-cuerpo text-sm text-gray-600">
                  {{ pipe.iniciado && pipe.terminado ? calcDuration(pipe.iniciado, pipe.terminado) : '—' }}
                </span>
              </td>
              <td class="px-6 py-4 text-right">
                <RouterLink
                  v-if="pipe.pipeline_id"
                  :to="`/admin/pipeline-editor/${pipe.pipeline_id}`"
                  class="font-cuerpo text-xs font-medium text-ubpd-teal hover:underline"
                >
                  Editar
                </RouterLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Vacío -->
      <div v-else class="py-16 text-center">
        <svg class="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <p class="font-cuerpo text-sm text-gray-500">No hay ejecuciones recientes</p>
      </div>
    </div>

    <!-- Auto-refresh indicator -->
    <p class="font-cuerpo text-xs text-gray-400 text-right">
      Actualización automática cada 30 segundos
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useNotificationsStore } from '@/stores/notifications'

interface Pipeline {
  id: string
  tipo: string
  estado: 'success' | 'error' | 'running' | 'pending'
  formulario_id?: string
  iniciado: string
  terminado?: string
}

const { get } = useApi()
const notifications = useNotificationsStore()

const loading = ref(true)
const pipelines = ref<Pipeline[]>([])
const lastRefresh = ref<Date | null>(null)

let autoRefreshTimer: ReturnType<typeof setInterval> | null = null

async function loadPipelines() {
  loading.value = true
  try {
    pipelines.value = await get<Pipeline[]>('/admin/pipelines/status')
    lastRefresh.value = new Date()
  } catch {
    notifications.error('No se pudo cargar el estado de los pipelines')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadPipelines()
  autoRefreshTimer = setInterval(loadPipelines, 30000)
})

onUnmounted(() => {
  if (autoRefreshTimer) clearInterval(autoRefreshTimer)
})

const statusSummary = computed(() => {
  const success = pipelines.value.filter((p) => p.estado === 'success').length
  const error = pipelines.value.filter((p) => p.estado === 'error').length
  const running = pipelines.value.filter((p) => p.estado === 'running').length
  const pending = pipelines.value.filter((p) => p.estado === 'pending').length
  return [
    { label: 'Exitosos', count: success, dot: 'bg-ubpd-verde' },
    { label: 'En ejecución', count: running, dot: 'bg-yellow-400' },
    { label: 'Con error', count: error, dot: 'bg-red-500' },
    { label: 'Pendientes', count: pending, dot: 'bg-gray-400' },
  ]
})

function estadoLabel(estado: string): string {
  const map: Record<string, string> = {
    success: 'Exitoso',
    error: 'Error',
    running: 'En ejecución',
    pending: 'Pendiente',
  }
  return map[estado] ?? estado
}

function formatDate(d: string): string {
  return new Date(d).toLocaleString('es-CO', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  })
}

function formatRelative(date: Date): string {
  const diff = Math.floor((Date.now() - date.getTime()) / 1000)
  if (diff < 60) return `hace ${diff}s`
  if (diff < 3600) return `hace ${Math.floor(diff / 60)}min`
  return formatDate(date.toISOString())
}

function truncateId(id: string): string {
  return id.length > 8 ? `${id.slice(0, 8)}...` : id
}

function calcDuration(start: string, end: string): string {
  const ms = new Date(end).getTime() - new Date(start).getTime()
  const s = Math.floor(ms / 1000)
  if (s < 60) return `${s}s`
  const m = Math.floor(s / 60)
  const rem = s % 60
  return `${m}m ${rem}s`
}
</script>
