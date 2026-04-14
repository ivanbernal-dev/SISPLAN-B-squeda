<template>
  <div class="space-y-6">

    <!-- Breadcrumb ───────────────────────────────────────────── -->
    <nav class="flex items-center gap-2 text-sm font-barlow text-gray-500 flex-wrap" aria-label="Navegación">
      <RouterLink to="/estadisticas" class="hover:text-ubpd-teal transition-colors">Estadísticas</RouterLink>
      <span>›</span>
      <RouterLink :to="`/estadisticas/${kpiKey}`" class="hover:text-ubpd-teal transition-colors">
        {{ route.query.kpiLabel || kpiKey }}
      </RouterLink>
      <span>›</span>
      <span class="text-ubpd-gris font-semibold">{{ pageTitle }}</span>
    </nav>

    <!-- Header ──────────────────────────────────────────────── -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold font-montserrat text-ubpd-gris">{{ pageTitle }}</h1>
        <p class="text-sm font-barlow text-gray-500 mt-0.5">
          Formularios aprobados asociados a este indicador
          <span v-if="!loading" class="ml-1 font-semibold text-ubpd-gris">— {{ total }} registros</span>
        </p>
      </div>
    </div>

    <!-- Skeleton ─────────────────────────────────────────────── -->
    <div v-if="loading" class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden animate-pulse">
      <div class="px-6 py-4 border-b border-gray-100 flex gap-4">
        <div class="h-5 w-40 bg-gray-200 rounded" />
        <div class="h-5 w-28 bg-gray-200 rounded" />
        <div class="h-5 w-24 bg-gray-200 rounded" />
      </div>
      <div v-for="n in 5" :key="n" class="px-6 py-4 border-b border-gray-50 flex gap-6">
        <div class="h-4 w-48 bg-gray-100 rounded" />
        <div class="h-4 w-32 bg-gray-100 rounded" />
        <div class="h-4 w-24 bg-gray-100 rounded" />
        <div class="h-4 w-20 bg-gray-100 rounded ml-auto" />
      </div>
    </div>

    <!-- Tabla ───────────────────────────────────────────────── -->
    <div v-else-if="items.length > 0" class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <table class="w-full">
        <thead>
          <tr class="bg-gray-50 border-b border-gray-100">
            <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide">Caso / Nombre</th>
            <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide hidden sm:table-cell">Dependencia</th>
            <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide hidden md:table-cell">Responsable</th>
            <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide hidden lg:table-cell">Fecha</th>
            <th class="px-6 py-3 text-right font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr
            v-for="item in items"
            :key="item.id"
            class="hover:bg-gray-50/50 transition cursor-pointer"
            @click="viewDetail(item.id)"
          >
            <td class="px-6 py-4">
              <p class="font-cuerpo font-medium text-sm text-ubpd-gris truncate max-w-xs">
                {{ item.datos_dinamicos?.nombre_caso || item.datos_dinamicos?.nombre || `Registro ${item.id.slice(0, 8)}` }}
              </p>
              <p v-if="item.datos_dinamicos?.region" class="font-cuerpo text-xs text-gray-400 mt-0.5">
                {{ item.datos_dinamicos.region }}
              </p>
            </td>
            <td class="px-6 py-4 hidden sm:table-cell">
              <span class="font-cuerpo text-sm text-gray-600">{{ item.dependency }}</span>
            </td>
            <td class="px-6 py-4 hidden md:table-cell">
              <span class="font-cuerpo text-sm text-gray-600">{{ item.usuario }}</span>
            </td>
            <td class="px-6 py-4 hidden lg:table-cell">
              <span class="font-cuerpo text-sm text-gray-500">{{ formatDate(item.fecha_usuario || item.fecha_carga) }}</span>
            </td>
            <td class="px-6 py-4 text-right">
              <button
                class="inline-flex items-center gap-1 font-cuerpo text-xs font-semibold
                       text-ubpd-teal hover:text-ubpd-verde transition"
                @click.stop="viewDetail(item.id)"
              >
                Ver detalle
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Paginación ─────────────────────────────────────────── -->
      <div v-if="totalPages > 1" class="px-6 py-4 border-t border-gray-100 flex items-center justify-between">
        <p class="font-cuerpo text-sm text-gray-500">
          Página {{ page }} de {{ totalPages }} · {{ total }} registros
        </p>
        <div class="flex gap-1">
          <button
            :disabled="page <= 1"
            @click="changePage(page - 1)"
            class="p-2 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50
                   disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
            </svg>
          </button>
          <button
            :disabled="page >= totalPages"
            @click="changePage(page + 1)"
            class="p-2 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50
                   disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Sin datos ────────────────────────────────────────────── -->
    <div v-else class="text-center py-20 text-gray-400">
      <svg class="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
      </svg>
      <p class="font-barlow text-base">No hay formularios aprobados para este indicador.</p>
      <p class="font-barlow text-sm mt-1 text-gray-300">El indicador puede no tener un template asociado aún.</p>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'

interface FormItem {
  id: string
  dependency: string
  usuario: string
  fecha_carga: string | null
  fecha_usuario: string | null
  datos_dinamicos: Record<string, any>
  estado: string
}

interface KpiForms {
  total: number
  page: number
  size: number
  kpi_label: string
  template_nombre: string | null
  template_id: string | null
  items: FormItem[]
}

const route = useRoute()
const router = useRouter()
const { get } = useApi()

const loading = ref(true)
const total = ref(0)
const page = ref(1)
const pageSize = 20
const items = ref<FormItem[]>([])
const kpiLabel = ref('')
const templateNombre = ref<string | null>(null)
const templateId = ref<string | null>(null)

const kpiKey = computed(() => route.params.kpiKey as string)
const subKpiKey = computed(() => route.params.subKpiKey as string)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

const pageTitle = computed(() =>
  kpiLabel.value || (route.query.subLabel as string) || subKpiKey.value
)

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '—'
  try {
    return new Date(dateStr).toLocaleDateString('es-CO', {
      day: 'numeric', month: 'short', year: 'numeric',
    })
  } catch { return dateStr }
}

function viewDetail(formId: string) {
  router.push({
    path: `/estadisticas/${kpiKey.value}/forms/${subKpiKey.value}/${formId}`,
    query: {
      kpiLabel: route.query.kpiLabel,
      subLabel: kpiLabel.value,
      templateNombre: templateNombre.value ?? undefined,
    },
  })
}

function changePage(p: number) {
  page.value = p
  loadForms()
}

async function loadForms() {
  loading.value = true
  try {
    const data = await get<KpiForms>(`/stats/kpis/${subKpiKey.value}/forms`, {
      params: { page: page.value, size: pageSize },
    })
    total.value = data.total
    items.value = data.items
    kpiLabel.value = data.kpi_label
    templateNombre.value = data.template_nombre
    templateId.value = data.template_id
  } catch {
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

onMounted(loadForms)
watch(subKpiKey, () => { page.value = 1; loadForms() })
</script>
