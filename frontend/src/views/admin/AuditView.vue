<template>
  <div class="p-6 space-y-5">
    <!-- Encabezado -->
    <div>
      <h1 class="font-subtitulo font-bold text-2xl text-ubpd-gris">Registro de Auditoría</h1>
      <p class="font-cuerpo text-sm text-gray-500 mt-1">Historial completo de actividad del sistema</p>
    </div>

    <!-- Filtros -->
    <div class="bg-white rounded-2xl border border-gray-100 shadow-sm px-5 py-4">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <div>
          <label class="block font-cuerpo text-xs font-medium text-gray-500 mb-1">Usuario</label>
          <input
            v-model="filters.usuario"
            type="text"
            placeholder="Nombre o correo..."
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
            <option value="LOGIN">Inicio de sesión</option>
            <option value="LOGOUT">Cierre de sesión</option>
            <option value="USER_CREATE">Crear usuario</option>
            <option value="USER_UPDATE">Actualizar usuario</option>
            <option value="USER_DEACTIVATE">Desactivar usuario</option>
            <option value="USER_RESET_PASSWORD">Resetear contraseña</option>
            <option value="FORM_CREATE">Crear formulario</option>
            <option value="FORM_APPROVE">Aprobar formulario</option>
            <option value="FORM_REJECT">Rechazar formulario</option>
            <option value="FORM_DELETE">Eliminar formulario</option>
            <option value="TEMPLATE_UPDATE">Actualizar template</option>
            <option value="DEPENDENCY_CREATE">Crear dependencia</option>
            <option value="DEPENDENCY_UPDATE">Actualizar dependencia</option>
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
      <!-- Skeleton -->
      <div v-if="loading" class="divide-y divide-gray-50">
        <div v-for="i in 8" :key="i" class="px-6 py-4 flex items-center gap-4 animate-pulse">
          <div class="w-32 h-4 rounded bg-gray-200" />
          <div class="w-28 h-4 rounded bg-gray-200" />
          <div class="w-24 h-6 rounded-full bg-gray-200" />
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
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide hidden lg:table-cell">Detalle</th>
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide hidden xl:table-cell">IP</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr
              v-for="log in logs"
              :key="log.id"
              class="hover:bg-gray-50/50 transition cursor-pointer"
              @click="selectedLog = log"
            >
              <!-- Fecha -->
              <td class="px-6 py-4 whitespace-nowrap">
                <p class="font-cuerpo text-sm text-ubpd-gris">{{ formatDate(log.fecha) }}</p>
                <p class="font-cuerpo text-xs text-gray-400">{{ formatTime(log.fecha) }}</p>
              </td>

              <!-- Usuario -->
              <td class="px-6 py-4">
                <div class="flex items-center gap-2">
                  <div class="w-7 h-7 rounded-full bg-ubpd-teal/10 flex items-center justify-center flex-shrink-0">
                    <span class="font-subtitulo text-xs font-bold text-ubpd-teal">
                      {{ initials(log.usuario) }}
                    </span>
                  </div>
                  <div>
                    <p class="font-cuerpo text-sm text-ubpd-gris leading-tight">{{ log.usuario }}</p>
                    <p v-if="log.usuario_email" class="font-cuerpo text-xs text-gray-400 leading-tight">{{ log.usuario_email }}</p>
                  </div>
                </div>
              </td>

              <!-- Acción -->
              <td class="px-6 py-4 whitespace-nowrap">
                <span
                  class="inline-flex items-center font-cuerpo text-xs font-semibold px-2.5 py-1 rounded-full"
                  :class="actionBadgeClass(log.accion)"
                >
                  {{ actionLabel(log.accion) }}
                </span>
              </td>

              <!-- Entidad -->
              <td class="px-6 py-4 hidden md:table-cell">
                <span class="font-cuerpo text-sm text-gray-500">{{ log.entidad || '—' }}</span>
              </td>

              <!-- Detalle -->
              <td class="px-6 py-4 hidden lg:table-cell max-w-xs">
                <span class="font-mono text-xs text-gray-400 truncate block max-w-[200px]">
                  {{ detalleResumen(log.detalle) }}
                </span>
              </td>

              <!-- IP -->
              <td class="px-6 py-4 hidden xl:table-cell whitespace-nowrap">
                <span class="font-mono text-xs text-gray-400">{{ log.ip || '—' }}</span>
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
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
        <p class="font-cuerpo text-sm text-gray-500">No se encontraron registros de auditoría</p>
      </div>
    </div>

    <!-- Modal detalle -->
    <div
      v-if="selectedLog"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      @click.self="selectedLog = null"
    >
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6 space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-semibold font-montserrat text-ubpd-gris">Detalle del evento</h2>
          <button type="button" @click="selectedLog = null" class="text-gray-400 hover:text-ubpd-gris">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 256 256" fill="currentColor">
              <path d="M205.66,194.34a8,8,0,0,1-11.32,11.32L128,139.31,61.66,205.66a8,8,0,0,1-11.32-11.32L116.69,128,50.34,61.66A8,8,0,0,1,61.66,50.34L128,116.69l66.34-66.35a8,8,0,0,1,11.32,11.32L139.31,128Z"/>
            </svg>
          </button>
        </div>

        <dl class="grid grid-cols-2 gap-3 text-sm">
          <div class="col-span-2">
            <dt class="font-cuerpo text-xs text-gray-400 uppercase tracking-wide mb-0.5">Fecha y hora</dt>
            <dd class="font-cuerpo text-ubpd-gris font-medium">
              {{ formatDate(selectedLog.fecha) }} {{ formatTime(selectedLog.fecha) }}
            </dd>
          </div>
          <div>
            <dt class="font-cuerpo text-xs text-gray-400 uppercase tracking-wide mb-0.5">Usuario</dt>
            <dd class="font-cuerpo text-ubpd-gris font-medium">{{ selectedLog.usuario }}</dd>
            <dd class="font-cuerpo text-xs text-gray-400">{{ selectedLog.usuario_email || '' }}</dd>
          </div>
          <div>
            <dt class="font-cuerpo text-xs text-gray-400 uppercase tracking-wide mb-0.5">Acción</dt>
            <dd>
              <span class="inline-flex items-center font-cuerpo text-xs font-semibold px-2.5 py-1 rounded-full" :class="actionBadgeClass(selectedLog.accion)">
                {{ actionLabel(selectedLog.accion) }}
              </span>
            </dd>
          </div>
          <div v-if="selectedLog.entidad">
            <dt class="font-cuerpo text-xs text-gray-400 uppercase tracking-wide mb-0.5">Entidad</dt>
            <dd class="font-cuerpo text-ubpd-gris">{{ selectedLog.entidad }}</dd>
          </div>
          <div v-if="selectedLog.ip">
            <dt class="font-cuerpo text-xs text-gray-400 uppercase tracking-wide mb-0.5">Dirección IP</dt>
            <dd class="font-mono text-sm text-gray-600">{{ selectedLog.ip }}</dd>
          </div>
          <div v-if="selectedLog.detalle && Object.keys(selectedLog.detalle).length > 0" class="col-span-2">
            <dt class="font-cuerpo text-xs text-gray-400 uppercase tracking-wide mb-1">Datos adicionales</dt>
            <dd class="bg-gray-50 rounded-xl p-3 font-mono text-xs text-gray-600 overflow-auto max-h-40 whitespace-pre-wrap">{{ JSON.stringify(selectedLog.detalle, null, 2) }}</dd>
          </div>
        </dl>
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
  usuario_email: string | null
  accion: string
  entidad: string | null
  entidad_tipo: string | null
  detalle: Record<string, any>
  ip: string | null
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
const selectedLog = ref<AuditLog | null>(null)

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
    notifications.error('Error', 'No se pudo cargar el registro de auditoría.')
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
  if (!d) return '—'
  return new Date(d).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}
function formatTime(d: string): string {
  if (!d) return ''
  return new Date(d).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}
function initials(name: string): string {
  if (!name) return '?'
  return name.split(' ').map((w) => w[0]).slice(0, 2).join('').toUpperCase()
}

function actionLabel(accion: string): string {
  const map: Record<string, string> = {
    LOGIN: 'Inicio de sesión',
    LOGOUT: 'Cierre de sesión',
    USER_CREATE: 'Crear usuario',
    USER_UPDATE: 'Actualizar usuario',
    USER_DEACTIVATE: 'Desactivar usuario',
    USER_RESET_PASSWORD: 'Resetear contraseña',
    FORM_CREATE: 'Crear formulario',
    FORM_APPROVE: 'Aprobar formulario',
    FORM_REJECT: 'Rechazar formulario',
    FORM_DELETE: 'Eliminar formulario',
    TEMPLATE_CREATE: 'Crear template',
    TEMPLATE_UPDATE: 'Actualizar template',
    DEPENDENCY_CREATE: 'Crear dependencia',
    DEPENDENCY_UPDATE: 'Actualizar dependencia',
  }
  return map[accion] ?? accion
}

function actionBadgeClass(accion: string): string {
  if (accion === 'LOGIN') return 'bg-ubpd-teal/10 text-ubpd-teal'
  if (accion === 'LOGOUT') return 'bg-gray-100 text-gray-500'
  if (accion.includes('CREATE')) return 'bg-ubpd-verde/10 text-ubpd-verde'
  if (accion.includes('UPDATE') || accion.includes('RESET')) return 'bg-blue-100 text-blue-600'
  if (accion.includes('APPROVE')) return 'bg-green-100 text-green-700'
  if (accion.includes('REJECT') || accion.includes('DELETE') || accion.includes('DEACTIVATE')) return 'bg-orange-100 text-ubpd-naranja'
  return 'bg-gray-100 text-gray-500'
}

function detalleResumen(detalle: Record<string, any>): string {
  if (!detalle || Object.keys(detalle).length === 0) return '—'
  const entries = Object.entries(detalle).slice(0, 2)
  return entries.map(([k, v]) => `${k}: ${v}`).join(' | ')
}
</script>
