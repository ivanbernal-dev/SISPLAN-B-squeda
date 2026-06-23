<template>
  <div class="p-6 space-y-5">
    <!-- Encabezado -->
    <div>
      <h1 class="font-subtitulo font-bold text-2xl text-ubpd-gris">Historial de Validaciones</h1>
      <p class="font-cuerpo text-sm text-gray-500 mt-1">Registros procesados — aprobados y devueltos</p>
    </div>

    <!-- Filtros -->
    <div class="bg-white rounded-2xl border border-gray-100 shadow-sm px-5 py-4">
      <div class="flex flex-wrap items-end gap-3">
        <div>
          <label class="block font-cuerpo text-xs font-medium text-gray-500 mb-1">Estado</label>
          <select
            v-model="filters.estado"
            @change="applyFilters"
            class="font-cuerpo text-sm border border-gray-300 rounded-lg px-3 py-2
                   focus:outline-none focus:border-ubpd-verde transition"
          >
            <option value="">Todos los estados</option>
            <option value="approved">Validados</option>
            <option value="rejected">Devueltos</option>
          </select>
        </div>
        <div>
          <label class="block font-cuerpo text-xs font-medium text-gray-500 mb-1">Desde</label>
          <input
            v-model="filters.start_date"
            type="date"
            @change="applyFilters"
            class="font-cuerpo text-sm border border-gray-300 rounded-lg px-3 py-2
                   focus:outline-none focus:border-ubpd-verde transition"
          />
        </div>
        <div>
          <label class="block font-cuerpo text-xs font-medium text-gray-500 mb-1">Hasta</label>
          <input
            v-model="filters.end_date"
            type="date"
            @change="applyFilters"
            class="font-cuerpo text-sm border border-gray-300 rounded-lg px-3 py-2
                   focus:outline-none focus:border-ubpd-verde transition"
          />
        </div>
        <button
          @click="clearFilters"
          class="font-cuerpo text-sm text-gray-500 border border-gray-300 rounded-lg px-3 py-2 hover:bg-gray-50 transition"
        >
          Limpiar
        </button>
      </div>
    </div>

    <!-- Tabla -->
    <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <!-- Loading -->
      <div v-if="loading" class="divide-y divide-gray-50">
        <div v-for="i in 6" :key="i" class="px-6 py-4 flex items-center gap-4 animate-pulse">
          <div class="flex-1 space-y-2">
            <div class="w-40 h-4 rounded bg-gray-200" />
            <div class="w-28 h-3 rounded bg-gray-200" />
          </div>
          <div class="w-20 h-6 rounded-full bg-gray-200" />
          <div class="w-28 h-4 rounded bg-gray-200" />
          <div class="w-32 h-4 rounded bg-gray-200 hidden md:block" />
        </div>
      </div>

      <!-- Datos -->
      <div v-else-if="items.length > 0">
        <table class="w-full">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide">Template</th>
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide">Dependencia</th>
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide">Estado</th>
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide">Fecha</th>
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide hidden md:table-cell">Comentario</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="item in items" :key="item.id" class="hover:bg-gray-50/50 transition">
              <td class="px-6 py-4">
                <p class="font-cuerpo font-medium text-sm text-ubpd-gris">{{ item.template_nombre }}</p>
              </td>
              <td class="px-6 py-4">
                <p class="font-cuerpo text-sm text-gray-600">{{ item.dependencia_nombre }}</p>
              </td>
              <td class="px-6 py-4">
                <span
                  class="inline-flex items-center gap-1.5 font-cuerpo text-xs font-medium px-2.5 py-1 rounded-full"
                  :class="item.estado === 'approved'
                    ? 'bg-ubpd-verde/10 text-ubpd-verde'
                    : 'bg-orange-100 text-ubpd-naranja'"
                >
                  <svg v-if="item.estado === 'approved'" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                  </svg>
                  {{ item.estado === 'approved' ? 'Registro validado' : 'Requiere corrección' }}
                </span>
              </td>
              <td class="px-6 py-4">
                <p class="font-cuerpo text-sm text-gray-600">{{ formatDate(item.fecha_validacion) }}</p>
              </td>
              <td class="px-6 py-4 hidden md:table-cell">
                <p
                  v-if="item.comentario"
                  class="font-cuerpo text-sm text-gray-500 max-w-xs truncate"
                  :title="item.comentario"
                >
                  {{ item.comentario }}
                </p>
                <span v-else class="font-cuerpo text-xs text-gray-300">—</span>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Paginación -->
        <div v-if="totalPages > 1" class="px-6 py-4 border-t border-gray-100 flex items-center justify-between">
          <p class="font-cuerpo text-sm text-gray-500">Página {{ page }} de {{ totalPages }}</p>
          <div class="flex gap-1">
            <button @click="goToPage(page - 1)" :disabled="page === 1"
              class="p-2 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <button v-for="p in totalPages" :key="p" @click="goToPage(p)"
              class="w-8 h-8 rounded-lg font-cuerpo text-sm transition"
              :class="p === page ? 'bg-ubpd-teal text-white' : 'border border-gray-200 text-gray-500 hover:bg-gray-50'">
              {{ p }}
            </button>
            <button @click="goToPage(page + 1)" :disabled="page === totalPages"
              class="p-2 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Vacío -->
      <div v-else class="py-16 text-center">
        <svg class="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
        <p class="font-cuerpo text-sm text-gray-500">No se encontraron registros</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useApi } from '@/composables/useApi'
import { useNotificationsStore } from '@/stores/notifications'

interface HistoryItem {
  id: string
  template_nombre: string
  dependencia_nombre: string
  estado: 'approved' | 'rejected'
  fecha_validacion: string
  comentario?: string
}

interface HistoryResponse {
  total: number
  page: number
  items: HistoryItem[]
}

const { get } = useApi()
const notifications = useNotificationsStore()

const loading = ref(true)
const items = ref<HistoryItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20

const filters = reactive({ estado: '', start_date: '', end_date: '' })
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

async function loadHistory() {
  loading.value = true
  try {
    const params = new URLSearchParams({ page: String(page.value), size: String(pageSize) })
    if (filters.estado) params.append('estado', filters.estado)
    if (filters.start_date) params.append('start_date', filters.start_date)
    if (filters.end_date) params.append('end_date', filters.end_date)
    const data = await get<HistoryResponse>(`/validation/history?${params.toString()}`)
    items.value = data.items
    total.value = data.total
  } catch {
    notifications.error('No se pudo cargar el historial')
  } finally {
    loading.value = false
  }
}

onMounted(loadHistory)

function applyFilters() { page.value = 1; loadHistory() }
function clearFilters() { filters.estado = ''; filters.start_date = ''; filters.end_date = ''; applyFilters() }
function goToPage(p: number) { if (p >= 1 && p <= totalPages.value) { page.value = p; loadHistory() } }

function formatDate(d: string): string {
  return new Date(d).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}
</script>
