<template>
  <div class="space-y-6">
    <!-- Breadcrumb -->
    <nav class="flex items-center gap-2 text-sm font-barlow text-gray-500" aria-label="Navegación">
      <RouterLink to="/estadisticas" class="hover:text-ubpd-teal transition-colors">
        Estadísticas
      </RouterLink>
      <span aria-hidden="true">›</span>
      <RouterLink
        :to="`/estadisticas/${route.params.indicador_id}`"
        class="hover:text-ubpd-teal transition-colors"
      >
        {{ indicadorNombre || 'Indicador' }}
      </RouterLink>
      <span aria-hidden="true">›</span>
      <span class="text-ubpd-gris font-semibold">{{ templateNombre || 'Template' }}</span>
    </nav>

    <!-- Page header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold font-montserrat text-ubpd-gris">
          {{ templateNombre || 'Detalle de formularios' }}
        </h1>
        <p class="text-sm font-barlow text-gray-500 mt-0.5">
          {{ periodoLabel }}
        </p>
      </div>

      <!-- Export button -->
      <button
        type="button"
        class="inline-flex items-center gap-2 px-5 py-2.5 bg-ubpd-teal text-white font-semibold font-barlow text-sm rounded-lg hover:bg-teal-700 transition-colors shrink-0"
        :disabled="exporting"
        @click="exportExcel"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 256 256" fill="currentColor" aria-hidden="true">
          <path d="M224,152v56a16,16,0,0,1-16,16H48a16,16,0,0,1-16-16V152a8,8,0,0,1,16,0v56H208V152a8,8,0,0,1,16,0Zm-101.66,5.66a8,8,0,0,0,11.32,0l40-40a8,8,0,0,0-11.32-11.32L136,132.69V40a8,8,0,0,0-16,0v92.69L93.66,106.34a8,8,0,0,0-11.32,11.32Z"/>
        </svg>
        <span v-if="exporting">Exportando...</span>
        <span v-else>Exportar a Excel</span>
      </button>
    </div>

    <!-- Selector temporal -->
    <div class="inline-flex bg-gray-100 rounded-xl p-1 gap-1" role="tablist">
      <button
        v-for="opt in periodoOptions"
        :key="opt.value"
        type="button"
        @click="setPeriodo(opt.value)"
        :class="[
          'px-4 py-1.5 rounded-lg text-sm font-cuerpo font-semibold transition-all',
          periodo === opt.value
            ? 'bg-white text-ubpd-teal shadow-sm'
            : 'text-gray-500 hover:text-ubpd-gris',
        ]"
        :aria-pressed="periodo === opt.value"
      >
        {{ opt.label }}
      </button>
    </div>

    <!-- Data table -->
    <DataTable
      :columns="COLUMNS"
      :data="tableRows"
      :loading="loading"
      :searchable="true"
      :total="total"
      :current-page="currentPage"
      :page-size="PAGE_SIZE"
      @search="onSearch"
      @sort="onSort"
      @page-change="onPageChange"
    >
      <!-- Dependencia (clickable) -->
      <template #cell-dependencia="{ row, value }">
        <button
          type="button"
          class="font-medium text-ubpd-gris hover:text-ubpd-teal transition-colors text-left"
          @click="navigateToDetail(row.id as string)"
        >
          {{ value }}
        </button>
      </template>

      <!-- Actividad clave -->
      <template #cell-actividad="{ value }">
        <span class="text-gray-700 text-sm line-clamp-2" :title="String(value)">
          {{ truncate(String(value ?? ''), 120) }}
        </span>
      </template>

      <!-- Trimestre -->
      <template #cell-trimestre="{ value }">
        <span class="text-gray-600 text-sm whitespace-nowrap">{{ value }}</span>
      </template>

      <!-- % Final con barra -->
      <template #cell-pct_final="{ value }">
        <template v-if="value !== null && value !== undefined">
          <div class="flex items-center gap-2">
            <div class="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden min-w-[70px]">
              <div
                class="h-full rounded-full"
                :class="colorBar(Number(value))"
                :style="{ width: `${Math.min(100, Number(value))}%` }"
              />
            </div>
            <span class="text-xs font-bold shrink-0 tabular-nums w-14 text-right"
                  :class="colorText(Number(value))">
              {{ Number(value).toFixed(1) }}%
            </span>
          </div>
        </template>
        <span v-else class="text-gray-400">—</span>
      </template>

      <!-- Estado -->
      <template #cell-estado="{ value }">
        <span
          class="text-xs font-semibold px-2.5 py-1 rounded-full whitespace-nowrap"
          :class="estadoClass(String(value))"
        >
          {{ value || '—' }}
        </span>
      </template>

      <!-- Archivos -->
      <template #cell-archivos="{ row }">
        <button
          v-if="Number(row.archivos_count) > 0"
          type="button"
          class="inline-flex items-center gap-1 text-ubpd-teal hover:text-teal-700 font-barlow text-sm"
          @click="openFiles(row.id as string)"
          :aria-label="`Ver ${row.archivos_count} archivos`"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 256 256" fill="currentColor" aria-hidden="true">
            <path d="M209.66,122.34a8,8,0,0,1,0,11.32l-82.05,82a56,56,0,0,1-79.2-79.21L147.67,36.73a40,40,0,1,1,56.61,56.55L105,192.78a24,24,0,1,1-33.94-33.95l62.56-62.45a8,8,0,0,1,11.31,11.32L82.38,170.15a8,8,0,1,0,11.31,11.31L192.32,81.08a24,24,0,1,0-33.93-33.94L59.18,147.38a40,40,0,1,0,56.55,56.62l82.06-82A8,8,0,0,1,209.66,122.34Z"/>
          </svg>
          {{ row.archivos_count }}
        </button>
        <span v-else class="text-gray-400">—</span>
      </template>
    </DataTable>

    <!-- Files modal -->
    <div
      v-if="showFilesModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Archivos del formulario"
      @click.self="showFilesModal = false"
    >
      <div class="bg-white rounded-xl shadow-xl w-full max-w-lg p-6 space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-semibold font-montserrat text-ubpd-gris">Archivos adjuntos</h2>
          <button
            type="button"
            class="text-gray-400 hover:text-ubpd-gris"
            @click="showFilesModal = false"
            aria-label="Cerrar"
          >
            ✕
          </button>
        </div>
        <div v-if="loadingFiles" class="text-center py-6">
          <span class="inline-block h-6 w-6 border-2 border-ubpd-teal border-t-transparent rounded-full animate-spin" />
        </div>
        <ul v-else class="space-y-2">
          <li
            v-for="file in modalFiles"
            :key="file.id"
            class="flex items-center justify-between gap-3 bg-gray-50 rounded-lg px-4 py-3"
          >
            <span class="text-sm font-barlow text-ubpd-gris truncate">{{ file.nombre }}</span>
            <a
              v-if="file.url"
              :href="file.url"
              target="_blank"
              rel="noopener"
              class="text-xs text-ubpd-teal hover:underline font-barlow shrink-0"
            >
              Abrir
            </a>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useStatsFilterStore } from '@/stores/statsFilter'
import type { FileRecord } from '@/types/forms'
import DataTable from '@/components/tables/DataTable.vue'

interface DetailItem {
  id: string
  fecha_referencia: string
  dependencia: string
  informe_cualitativo: string
  datos_dinamicos: Record<string, unknown>
  archivos_count: number
}

const PAGE_SIZE = 20

const COLUMNS = [
  { key: 'dependencia', label: 'Dependencia', sortable: true },
  { key: 'actividad', label: 'Actividad clave', sortable: false },
  { key: 'trimestre', label: 'Trimestre', sortable: false, width: '110px' },
  { key: 'pct_final', label: '% Final', sortable: false, width: '160px' },
  { key: 'estado', label: 'Estado', sortable: false, width: '160px' },
  { key: 'archivos', label: 'Archivos', sortable: false, width: '90px' },
]

const periodoOptions = [
  { value: 'anual', label: 'Anual' },
  { value: 'trim1', label: 'Trim 1' },
  { value: 'trim2', label: 'Trim 2' },
  { value: 'trim3', label: 'Trim 3' },
  { value: 'trim4', label: 'Trim 4' },
]

const route = useRoute()
const router = useRouter()
const { get } = useApi()
const filterStore = useStatsFilterStore()

const loading = ref(true)
const exporting = ref(false)
const items = ref<DetailItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const searchQ = ref('')
const indicadorNombre = ref('')
const templateNombre = ref('')
const periodo = ref<string>(
  (route.query.periodo as string) || filterStore.periodo || 'anual',
)

const showFilesModal = ref(false)
const loadingFiles = ref(false)
const modalFiles = ref<FileRecord[]>([])

const templateId = computed(() => route.params.template_id as string)

const periodoLabel = computed(() =>
  periodoOptions.find((o) => o.value === periodo.value)?.label ?? 'Anual',
)

function toNum(v: any): number | null {
  if (v === null || v === undefined || v === '') return null
  const n = parseFloat(String(v).replace(',', '.'))
  return isNaN(n) ? null : n
}

// Calcula pct_avance_final SIEMPRE al vuelo desde alcanzado/proyectado.
// Así no depende del valor guardado en datos_dinamicos (que en datos
// viejos venía como fracción 0..1 y rompía la UI). Devuelve null si la
// actividad no aplica este periodo (proyectado vacío o 0).
function liveFinal(dd: Record<string, unknown>): number | null {
  const proy = toNum(dd['pct_avance_proyectado'])
  const alc  = toNum(dd['pct_avance_alcanzado'])
  if (proy === null || proy <= 0) return null
  return (alc ?? 0) / proy * 100
}
function liveEstado(pct: number | null): string {
  if (pct === null) return 'No Aplica'
  if (pct >= 90) return 'Cumple'
  if (pct >= 70) return 'Cumple Parcialmente'
  if (pct >  0)  return 'No Cumple'
  return 'No Aplica'
}

const tableRows = computed(() =>
  items.value.map((item) => {
    const dd = (item.datos_dinamicos ?? {}) as Record<string, unknown>
    const pctFinal = liveFinal(dd)
    return {
      id: item.id,
      dependencia: item.dependencia,
      actividad: (dd['actividad_clave'] as string) || (dd['indicador'] as string) || (dd['entregable_trimestre'] as string) || '—',
      trimestre: (dd['periodo_reporte'] as string) || (dd['trimestre'] as string) || '—',
      pct_final: pctFinal,
      estado: liveEstado(pctFinal),
      archivos_count: item.archivos_count,
    }
  }),
)

function colorBar(pct: number) {
  if (pct >= 90) return 'bg-ubpd-verde'
  if (pct >= 60) return 'bg-amber-400'
  return 'bg-orange-500'
}
function colorText(pct: number) {
  if (pct >= 90) return 'text-ubpd-verde'
  if (pct >= 60) return 'text-amber-600'
  return 'text-orange-600'
}
function estadoClass(estado: string): string {
  const s = (estado || '').toLowerCase()
  if (s.includes('cumple parcial')) return 'bg-amber-50 text-amber-700'
  if (s === 'cumple') return 'bg-green-50 text-green-700'
  if (s.includes('no cumple')) return 'bg-orange-50 text-orange-700'
  if (s.includes('no aplica')) return 'bg-gray-100 text-gray-500'
  return 'bg-gray-50 text-gray-400'
}

function truncate(str: string, max: number): string {
  if (!str) return '—'
  return str.length > max ? str.slice(0, max) + '…' : str
}

function setPeriodo(p: string) {
  periodo.value = p
  filterStore.setPeriodo(p)
  currentPage.value = 1
  loadData()
}

function onSearch(q: string) {
  searchQ.value = q
  currentPage.value = 1
  loadData()
}

function onSort(_key: string, _dir: 'asc' | 'desc') {
  loadData()
}

function onPageChange(page: number) {
  currentPage.value = page
  loadData()
}

function navigateToDetail(formId: string) {
  const indicadorId = route.params.indicador_id as string
  const tplId = route.params.template_id as string
  router.push({
    name: 'FormDetail',
    params: { indicador_id: indicadorId, template_id: tplId, form_id: formId },
    query: { periodo: periodo.value },
  })
}

async function openFiles(formId: string) {
  showFilesModal.value = true
  loadingFiles.value = true
  try {
    const form = await get<{ archivos: FileRecord[] }>(`/forms/${formId}`)
    const filesWithUrls = await Promise.all(
      (form.archivos ?? []).map(async (f) => {
        try {
          const { url } = await get<{ url: string }>(`/files/${f.id}/url`)
          return { ...f, url }
        } catch {
          return f
        }
      }),
    )
    modalFiles.value = filesWithUrls
  } catch {
    modalFiles.value = []
  } finally {
    loadingFiles.value = false
  }
}

async function exportExcel() {
  exporting.value = true
  try {
    const params = new URLSearchParams({
      template_id: templateId.value,
      periodo: periodo.value,
      ...(searchQ.value ? { search: searchQ.value } : {}),
    })
    window.open(`${import.meta.env.VITE_API_URL || '/api'}/stats/export?${params}`, '_blank')
  } finally {
    exporting.value = false
  }
}

async function loadData() {
  loading.value = true
  try {
    const params = new URLSearchParams({
      template_id: templateId.value,
      periodo: periodo.value,
      page: String(currentPage.value),
      size: String(PAGE_SIZE),
    })
    if (searchQ.value) params.set('search', searchQ.value)

    const result = await get<{ total: number; page: number; items: DetailItem[] }>(`/stats/detail?${params}`)
    items.value = result.items
    total.value = result.total

    if (route.query.indicador_nombre) indicadorNombre.value = String(route.query.indicador_nombre)
    if (route.query.template_nombre) templateNombre.value = String(route.query.template_nombre)
  } catch {
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

onMounted(loadData)

watch(templateId, () => {
  currentPage.value = 1
  loadData()
})
</script>
