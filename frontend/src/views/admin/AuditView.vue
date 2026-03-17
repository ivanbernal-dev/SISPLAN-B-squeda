<template>
  <div class="p-6 space-y-5">
    <!-- Encabezado -->
    <div>
      <h1 class="font-subtitulo font-bold text-2xl text-ubpd-gris">Registro de Auditoría</h1>
      <p class="font-cuerpo text-sm text-gray-500 mt-1">Historial de actividad del sistema</p>
    </div>

    <!-- Filtros -->
    <div class="bg-white rounded-2xl border border-gray-100 shadow-sm px-5 py-4">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <div>
          <label class="block font-cuerpo text-xs font-medium text-gray-500 mb-1">Usuario</label>
          <input
            v-model="filters.usuario"
            type="text"
            placeholder="Filtrar por usuario..."
            @keyup.enter="applyFilters"
            class="w-full font-cuerpo text-sm border border-gray-300 rounded-lg px-3 py-2
                   focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20 transition"
          />
        </div>
        <div>
          <label class="block font-cuerpo text-xs font-medium text-gray-500 mb-1">Acción</label>
          <select
            v-model="filters.accion"
            @change="applyFilters"
            class="w-full font-cuerpo text-sm border border-gray-300 rounded-lg px-3 py-2
                   focus:outline-none focus:border-ubpd-verde transition"
          >
            <option value="">Todas las acciones</option>
            <option value="login">Inicio de sesión</option>
            <option value="logout">Cierre de sesión</option>
            <option value="create">Crear</option>
            <option value="update">Actualizar</option>
            <option value="delete">Desactivar</option>
            <option value="approve">Aprobar</option>
            <option value="reject">Devolver</option>
          </select>
        </div>
        <div>
          <label class="block font-cuerpo text-xs font-medium text-gray-500 mb-1">Desde</label>
          <input
            v-model="filters.start_date"
            type="date"
            @change="applyFilters"
            class="w-full font-cuerpo text-sm border border-gray-300 rounded-lg px-3 py-2
                   focus:outline-none focus:border-ubpd-verde transition"
          />
        </div>
        <div>
          <label class="block font-cuerpo text-xs font-medium text-gray-500 mb-1">Hasta</label>
          <input
            v-model="filters.end_date"
            type="date"
            @change="applyFilters"
            class="w-full font-cuerpo text-sm border border-gray-300 rounded-lg px-3 py-2
                   focus:outline-none focus:border-ubpd-verde transition"
          />
        </div>
      </div>
      <div class="flex gap-2 mt-3">
        <button
          @click="applyFilters"
          class="font-cuerpo text-sm font-medium text-white bg-ubpd-teal px-4 py-2 rounded-lg hover:bg-[#346d7a] transition"
        >
          Buscar
        </button>
        <button
          @click="clearFilters"
          class="font-cuerpo text-sm font-medium text-ubpd-gris border border-gray-300 px-4 py-2 rounded-lg hover:bg-gray-50 transition"
        >
          Limpiar
        </button>
      </div>
    </div>

    <!-- Tabla -->
    <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <div v-if="loading" class="divide-y divide-gray-50">
        <div v-for="i in 8" :key="i" class="px-6 py-4 flex items-center gap-4 animate-pulse">
          <div class="w-32 h-4 rounded bg-gray-200" />
          <div class="w-24 h-4 rounded bg-gray-200" />
          <div class="w-20 h-6 rounded-full bg-gray-200" />
          <div class="flex-1 h-4 rounded bg-gray-200" />
          <div class="w-24 h-4 rounded bg-gray-200" />
        </div>
      </div>

      <div v-else-if="logs.length > 0">
        <table class="w-full">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide">Fecha y Hora</th>
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide">Usuario</th>
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide">Acción</th>
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide hidden md:table-cell">Entidad</th>
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide hidden lg:table-cell">IP</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="log in logs" :key="log.id" class="hover:bg-gray-50/50 transition">
              <td class="px-6 py-4">
                <div>
                  <p class="font-cuerpo text-sm text-ubpd-gris">{{ formatDate(log.fecha) }}</p>
                  <p class="font-cuerpo text-xs text-gray-400">{{ formatTime(log.fecha) }}</p>
                </div>
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center gap-2">
                  <div class="w-7 h-7 rounded-full bg-ubpd-teal/10 flex items-center justify-center flex-shrink-0">
                    <span class="font-subtitulo text-xs font-bold text-ubpd-teal">
                      {{ (log.usuario ?? '?')[0].toUpperCase() }}
                    </span>
                  </div>
                  <span class="font-cuerpo text-sm text-ubpd-gris">{{ log.usuario }}</span>
                </div>
              </td>
              <td class="px-6 py-4">
                <span
                  class="inline-flex items-center font-cuerpo text-xs font-medium px-2.5 py-1 rounded-full"
                  :class="actionBadgeClass(log.accion)"
                >
                  {{ actionLabel(log.accion) }}
                </span>
              </td>
              <td class="px-6 py-4 hidden md:table-cell">
                <span class="font-cuerpo text-sm text-gray-500">{{ log.entidad ?? '—' }}</span>
              </td>
              <td class="px-6 py-4 hidden lg:table-cell">
                <span class="font-mono text-xs text-gray-400">{{ log.ip ?? '—' }}</span>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Paginación -->
        <div class="px-6 py-4 border-t border-gray-100 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p class="font-cuerpo text-sm text-gray-500">
            Página {{ page }} de {{ totalPages }} &mdash; {{ total }} registros
          </p>
          <div class="flex gap-1">
            <button @click="goToPage(1)" :disabled="page === 1"
              class="px-3 py-2 rounded-lg border border-gray-200 font-cuerpo text-xs text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition">«</button>
            <button @click="goToPage(page - 1)" :disabled="page === 1"
              class="px-3 py-2 rounded-lg border border-gray-200 font-cuerpo text-xs text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition">‹</button>
            <span class="px-3 py-2 rounded-lg bg-ubpd-teal text-white font-cuerpo text-xs font-medium">{{ page }}</span>
            <button @click="goToPage(page + 1)" :disabled="page === totalPages"
              class="px-3 py-2 rounded-lg border border-gray-200 font-cuerpo text-xs text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition">›</button>
            <button @click="goToPage(totalPages)" :disabled="page === totalPages"
              class="px-3 py-2 rounded-lg border border-gray-200 font-cuerpo text-xs text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition">»</button>
          </div>
        </div>
      </div>

      <div v-else class="py-16 text-center">
        <svg class="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
        <p class="font-cuerpo text-sm text-gray-500">No se encontraron registros de auditoría</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useApi } from '@/composables/useApi'
import { useNotificationsStore } from '@/stores/notifications'

interface AuditLog {
  id: string
  fecha: string
  usuario: string
  accion: string
  entidad?: string
  ip?: string
}

interface AuditResponse {
  total: number
  page: number
  items: AuditLog[]
}

const { get } = useApi()
const notifications = useNotificationsStore()

const loading = ref(true)
const logs = ref<AuditLog[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20

const filters = reactive({ usuario: '', accion: '', start_date: '', end_date: '' })
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

async function loadLogs() {
  loading.value = true
  try {
    const params = new URLSearchParams({ page: String(page.value), size: String(pageSize) })
    if (filters.usuario) params.append('usuario', filters.usuario)
    if (filters.accion) params.append('accion', filters.accion)
    if (filters.start_date) params.append('start_date', filters.start_date)
    if (filters.end_date) params.append('end_date', filters.end_date)
    const data = await get<AuditResponse>(`/admin/audit?${params.toString()}`)
    logs.value = data.items
    total.value = data.total
  } catch {
    notifications.error('No se pudo cargar el registro de auditoría')
  } finally {
    loading.value = false
  }
}

onMounted(loadLogs)

function applyFilters() { page.value = 1; loadLogs() }
function clearFilters() {
  filters.usuario = ''
  filters.accion = ''
  filters.start_date = ''
  filters.end_date = ''
  page.value = 1
  loadLogs()
}
function goToPage(p: number) {
  if (p < 1 || p > totalPages.value) return
  page.value = p
  loadLogs()
}

function formatDate(d: string): string {
  return new Date(d).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}
function formatTime(d: string): string {
  return new Date(d).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })
}
function actionLabel(accion: string): string {
  const map: Record<string, string> = {
    login: 'Inicio de sesión', logout: 'Cierre de sesión',
    create: 'Crear', update: 'Actualizar', delete: 'Desactivar',
    approve: 'Aprobar', reject: 'Devolver',
  }
  return map[accion] ?? accion
}
function actionBadgeClass(accion: string): string {
  const map: Record<string, string> = {
    login: 'bg-ubpd-teal/10 text-ubpd-teal', logout: 'bg-gray-100 text-gray-500',
    create: 'bg-ubpd-verde/10 text-ubpd-verde', update: 'bg-blue-100 text-blue-600',
    delete: 'bg-orange-100 text-ubpd-naranja', approve: 'bg-ubpd-verde/10 text-ubpd-verde',
    reject: 'bg-orange-100 text-ubpd-naranja',
  }
  return map[accion] ?? 'bg-gray-100 text-gray-500'
}
</script>
