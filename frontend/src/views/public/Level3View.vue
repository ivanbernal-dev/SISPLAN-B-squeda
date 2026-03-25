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
          {{ statsFilter.startDate }} — {{ statsFilter.endDate }}
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

    <!-- Filters row -->
    <div class="flex flex-wrap items-center gap-3 bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
      <div class="flex items-center gap-2">
        <label class="text-xs font-barlow text-gray-500">Desde</label>
        <input
          type="date"
          :value="statsFilter.startDate"
          class="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-barlow focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-teal-100"
          @change="onStartDateChange"
        />
      </div>
      <div class="flex items-center gap-2">
        <label class="text-xs font-barlow text-gray-500">Hasta</label>
        <input
          type="date"
          :value="statsFilter.endDate"
          class="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-barlow focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-teal-100"
          @change="onEndDateChange"
        />
      </div>
      <div class="flex flex-wrap gap-2 ml-auto">
        <button
          v-for="preset in PRESETS"
          :key="preset.key"
          type="button"
          class="px-3 py-1.5 text-xs font-semibold font-barlow rounded-lg border transition-colors"
          :class="activePreset === preset.key
            ? 'bg-ubpd-teal text-white border-ubpd-teal'
            : 'border-gray-300 text-gray-600 hover:border-ubpd-teal hover:text-ubpd-teal'"
          @click="applyPreset(preset.key)"
        >
          {{ preset.label }}
        </button>
      </div>
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

      <!-- Fecha referencia -->
      <template #cell-fecha_referencia="{ value }">
        <span class="text-gray-600 whitespace-nowrap">{{ formatDate(String(value)) }}</span>
      </template>

      <!-- Campos completados -->
      <template #cell-campos_completados="{ row }">
        <span
          class="font-semibold"
          :class="Number(row.campos_completados_pct) >= 70 ? 'text-ubpd-verde' : Number(row.campos_completados_pct) >= 30 ? 'text-ubpd-lila' : 'text-ubpd-naranja'"
        >
          {{ row.campos_completados }}
        </span>
      </template>

      <!-- Informe cualitativo (truncated with tooltip) -->
      <template #cell-informe_cualitativo="{ value }">
        <div class="relative group max-w-xs">
          <span class="text-gray-600 text-sm truncate block cursor-help" :title="String(value)">
            {{ truncate(String(value ?? ''), 100) }}
          </span>
        </div>
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
import { useStatsFilter } from '@/stores/statsFilter'
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

type PresetKey = 'this_month' | 'last_quarter' | 'this_year'

const PRESETS: { key: PresetKey; label: string }[] = [
  { key: 'this_month', label: 'Este mes' },
  { key: 'last_quarter', label: 'Último trimestre' },
  { key: 'this_year', label: 'Año actual' },
]

const PAGE_SIZE = 20

const COLUMNS = [
  { key: 'dependencia', label: 'Dependencia', sortable: true },
  { key: 'fecha_referencia', label: 'Fecha Referencia', sortable: true },
  { key: 'campos_completados', label: 'Campos completados', sortable: false },
  { key: 'informe_cualitativo', label: 'Informe cualitativo', sortable: false },
  { key: 'archivos', label: 'Archivos', sortable: false, width: '100px' },
]

const route = useRoute()
const router = useRouter()
const { get } = useApi()
const statsFilter = useStatsFilter()

const loading = ref(true)
const exporting = ref(false)
const items = ref<DetailItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const searchQ = ref('')
const activePreset = ref<PresetKey | null>(null)
const indicadorNombre = ref('')
const templateNombre = ref('')

const showFilesModal = ref(false)
const loadingFiles = ref(false)
const modalFiles = ref<FileRecord[]>([])

const templateId = computed(() => route.params.template_id as string)

const tableRows = computed(() =>
  items.value.map((item) => {
    const totalFields = Object.keys(item.datos_dinamicos ?? {}).length
    const filledFields = Object.values(item.datos_dinamicos ?? {}).filter(
      (v) => v !== null && v !== undefined && v !== '',
    ).length
    const pct = totalFields > 0 ? Math.round((filledFields / totalFields) * 100) : 0
    return {
      id: item.id,
      dependencia: item.dependencia,
      fecha_referencia: item.fecha_referencia,
      campos_completados: `${filledFields}/${totalFields} campos`,
      campos_completados_pct: pct,
      informe_cualitativo: item.informe_cualitativo,
      archivos_count: item.archivos_count,
    }
  }),
)

function truncate(str: string, max: number): string {
  if (!str) return '—'
  return str.length > max ? str.slice(0, max) + '…' : str
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '—'
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('es-CO', {
    day: 'numeric', month: 'short', year: 'numeric',
  })
}

function onStartDateChange(e: Event) {
  statsFilter.setDates((e.target as HTMLInputElement).value, statsFilter.endDate)
  activePreset.value = null
  loadData()
}

function onEndDateChange(e: Event) {
  statsFilter.setDates(statsFilter.startDate, (e.target as HTMLInputElement).value)
  activePreset.value = null
  loadData()
}

function applyPreset(preset: PresetKey) {
  statsFilter.setPreset(preset)
  activePreset.value = preset
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
  const templateId = route.params.template_id as string
  router.push({
    name: 'FormDetail',
    params: { indicador_id: indicadorId, template_id: templateId, form_id: formId },
    query: statsFilter.queryParams,
  })
}

async function openFiles(formId: string) {
  showFilesModal.value = true
  loadingFiles.value = true
  try {
    const form = await get<{ archivos: FileRecord[] }>(`/forms/${formId}`)
    // Get signed URLs for each file
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
      ...statsFilter.queryParams,
      ...(searchQ.value ? { search: searchQ.value } : {}),
    })
    // Use window.open to trigger download
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
      ...statsFilter.queryParams,
      page: String(currentPage.value),
      size: String(PAGE_SIZE),
    })
    if (searchQ.value) params.set('search', searchQ.value)

    const result = await get<{ total: number; page: number; items: DetailItem[] }>(`/stats/detail?${params}`)
    items.value = result.items
    total.value = result.total

    // Set names from route query
    if (route.query.indicador_nombre) indicadorNombre.value = String(route.query.indicador_nombre)
    if (route.query.template_nombre) templateNombre.value = String(route.query.template_nombre)
  } catch {
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (route.query.start_date) {
    statsFilter.setDates(String(route.query.start_date), String(route.query.end_date ?? statsFilter.endDate))
  }
  loadData()
})

watch(templateId, () => {
  currentPage.value = 1
  loadData()
})
</script>
