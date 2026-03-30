<template>
  <div class="p-6 space-y-5">
    <!-- Encabezado con contador -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <div class="flex items-center gap-3">
          <h1 class="font-subtitulo font-bold text-2xl text-ubpd-gris">Bandeja de Entrada</h1>
          <span
            v-if="totalPending > 0"
            class="inline-flex items-center justify-center min-w-[28px] h-7 px-2 rounded-full
                   bg-ubpd-naranja text-white font-cuerpo font-bold text-sm"
            aria-live="polite"
            :aria-label="`${totalPending} formularios pendientes de revisión`"
          >
            {{ totalPending }}
          </span>
        </div>
        <p class="font-cuerpo text-sm text-gray-500 mt-1">
          Formularios enviados para revisión y validación
        </p>
      </div>
    </div>

    <!-- Filtros de fecha -->
    <div class="bg-white rounded-2xl border border-gray-100 shadow-sm px-5 py-4">
      <div class="flex flex-wrap items-end gap-3">
        <div>
          <label class="block font-cuerpo text-xs font-medium text-gray-500 mb-1">Desde</label>
          <input
            v-model="filters.start_date"
            type="date"
            @change="applyFilters"
            class="font-cuerpo text-sm border border-gray-300 rounded-lg px-3 py-2
                   focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20 transition"
          />
        </div>
        <div>
          <label class="block font-cuerpo text-xs font-medium text-gray-500 mb-1">Hasta</label>
          <input
            v-model="filters.end_date"
            type="date"
            @change="applyFilters"
            class="font-cuerpo text-sm border border-gray-300 rounded-lg px-3 py-2
                   focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20 transition"
          />
        </div>
        <button
          @click="clearFilters"
          class="font-cuerpo text-sm text-gray-500 border border-gray-300 rounded-lg px-3 py-2 hover:bg-gray-50 transition"
        >
          Limpiar fechas
        </button>
      </div>
    </div>

    <!-- Lista de formularios -->
    <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <!-- Loading -->
      <div v-if="loading" class="divide-y divide-gray-50">
        <div v-for="i in 5" :key="i" class="px-6 py-5 flex items-center gap-4 animate-pulse">
          <div class="flex-1 space-y-2">
            <div class="w-48 h-4 rounded bg-gray-200" />
            <div class="w-32 h-3 rounded bg-gray-200" />
          </div>
          <div class="w-20 h-6 rounded-full bg-gray-200" />
          <div class="w-28 h-4 rounded bg-gray-200" />
          <div class="w-8 h-8 rounded-lg bg-gray-200" />
        </div>
      </div>

      <!-- Datos -->
      <div v-else-if="forms.length > 0">
        <div
          v-for="form in forms"
          :key="form.id"
          class="px-6 py-5 border-b border-gray-50 flex items-center gap-4
                 hover:bg-gray-50/50 cursor-pointer transition group"
          role="row"
          :aria-label="`Revisar formulario de ${form.dependencia_nombre}`"
          @click="goToReview(form.id)"
        >
          <!-- Ícono de formulario -->
          <div class="w-10 h-10 rounded-xl bg-ubpd-teal/10 flex items-center justify-center flex-shrink-0">
            <svg class="w-5 h-5 text-ubpd-teal" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414A1 1 0 0119 9.414V19a2 2 0 01-2 2z" />
            </svg>
          </div>

          <!-- Info -->
          <div class="flex-1 min-w-0">
            <p class="font-cuerpo font-medium text-sm text-ubpd-gris group-hover:text-ubpd-teal transition truncate">
              {{ form.template_nombre }}
            </p>
            <p class="font-cuerpo text-xs text-gray-400 mt-0.5">{{ form.dependencia_nombre }}</p>
          </div>

          <!-- Badge estado -->
          <span class="flex-shrink-0 inline-flex items-center gap-1.5 font-cuerpo text-xs font-medium
                       px-2.5 py-1 rounded-full bg-ubpd-teal/10 text-ubpd-teal">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            En Revisión
          </span>

          <!-- Fecha de envío -->
          <div class="flex-shrink-0 text-right hidden sm:block">
            <p class="font-cuerpo text-sm text-gray-600">{{ formatDate(form.fecha_carga) }}</p>
            <p class="font-cuerpo text-xs text-gray-400">{{ formatTime(form.fecha_carga) }}</p>
          </div>

          <!-- Flecha -->
          <svg class="w-4 h-4 text-gray-300 group-hover:text-ubpd-teal transition flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </div>

        <!-- Paginación -->
        <div v-if="totalPages > 1" class="px-6 py-4 border-t border-gray-100 flex items-center justify-between">
          <p class="font-cuerpo text-sm text-gray-500">
            Página {{ page }} de {{ totalPages }}
          </p>
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

      <!-- Bandeja vacía -->
      <div v-else class="py-16 text-center">
        <div class="w-16 h-16 rounded-2xl bg-ubpd-verde/10 flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8 text-ubpd-verde" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p class="font-subtitulo font-semibold text-ubpd-gris">Bandeja vacía</p>
        <p class="font-cuerpo text-sm text-gray-400 mt-1">
          No hay formularios pendientes de revisión en este momento
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useNotificationsStore } from '@/stores/notifications'

interface PendingForm {
  id: string
  template_nombre: string
  dependencia_nombre: string
  fecha_carga: string
  estado: string
}

interface PendingResponse {
  total: number
  page: number
  items: PendingForm[]
}

const router = useRouter()
const { get } = useApi()
const notifications = useNotificationsStore()

const loading = ref(true)
const forms = ref<PendingForm[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20

const filters = reactive({ start_date: '', end_date: '' })
const totalPending = computed(() => total.value)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

async function loadForms() {
  loading.value = true
  try {
    const params = new URLSearchParams({ page: String(page.value), size: String(pageSize) })
    if (filters.start_date) params.append('start_date', filters.start_date)
    if (filters.end_date) params.append('end_date', filters.end_date)
    const data = await get<PendingResponse>(`/validation/pending?${params.toString()}`)
    forms.value = data.items
    total.value = data.total
  } catch {
    notifications.error('No se pudo cargar la bandeja de entrada')
  } finally {
    loading.value = false
  }
}

onMounted(loadForms)

function applyFilters() { page.value = 1; loadForms() }
function clearFilters() { filters.start_date = ''; filters.end_date = ''; applyFilters() }
function goToPage(p: number) { if (p >= 1 && p <= totalPages.value) { page.value = p; loadForms() } }
function goToReview(id: string) { router.push(`/validator/review/${id}`) }

function formatDate(d: string): string {
  return new Date(d).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}
function formatTime(d: string): string {
  return new Date(d).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })
}
</script>
