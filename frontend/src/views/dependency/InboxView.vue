<template>
  <div class="space-y-5">
    <div>
      <h1 class="text-2xl font-bold font-montserrat text-ubpd-gris">Mis Trámites</h1>
      <p class="text-sm font-barlow text-gray-500 mt-0.5">Gestión de formularios enviados y borradores</p>
    </div>

    <!-- Tabs -->
    <div class="flex flex-wrap gap-1 border-b border-gray-200">
      <button
        v-for="tab in TABS"
        :key="tab.key"
        type="button"
        class="px-4 py-2.5 text-sm font-semibold font-barlow rounded-t-lg transition-colors"
        :class="activeTab === tab.key
          ? 'bg-white border border-b-white border-gray-200 text-ubpd-teal -mb-px'
          : 'text-gray-500 hover:text-ubpd-teal'"
        @click="setTab(tab.key)"
      >
        {{ tab.label }}
        <span
          v-if="tabCounts[tab.key] !== undefined && tabCounts[tab.key] > 0"
          class="ml-1.5 inline-flex items-center justify-center w-5 h-5 rounded-full text-xs"
          :class="tab.key === 'rejected' ? 'bg-ubpd-naranja text-white' : 'bg-ubpd-teal text-white'"
        >
          {{ tabCounts[tab.key] }}
        </span>
      </button>
    </div>

    <!-- Date filter -->
    <div class="flex flex-wrap items-center gap-3">
      <div class="flex items-center gap-2">
        <label class="text-xs font-semibold font-barlow text-gray-500">Desde</label>
        <input
          type="date"
          v-model="filterStart"
          class="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-barlow focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-teal-100"
          @change="loadForms"
        />
      </div>
      <div class="flex items-center gap-2">
        <label class="text-xs font-semibold font-barlow text-gray-500">Hasta</label>
        <input
          type="date"
          v-model="filterEnd"
          class="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-barlow focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-teal-100"
          @change="loadForms"
        />
      </div>
      <button
        type="button"
        class="text-xs text-ubpd-teal font-barlow hover:underline"
        @click="clearFilters"
      >
        Limpiar filtros
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
      <!-- Template column -->
      <template #cell-template_nombre="{ row }">
        <span class="font-medium text-ubpd-gris">{{ row.template_nombre }}</span>
      </template>

      <!-- Date column -->
      <template #cell-fecha_referencia="{ row }">
        <span class="text-gray-600">{{ formatDate(String(row.fecha_referencia)) }}</span>
      </template>

      <!-- Status column -->
      <template #cell-estado="{ row }">
        <StatusBadge :status="(row.estado as 'draft' | 'pending' | 'rejected' | 'approved')" />
      </template>

      <!-- Actions column -->
      <template #cell-acciones="{ row }">
        <RouterLink
          :to="`/dependencia/forms/${row.id}`"
          class="inline-flex items-center gap-1 text-sm font-barlow text-ubpd-teal hover:text-teal-700 font-semibold"
        >
          <span v-if="row.estado === 'draft' || row.estado === 'rejected'">Editar</span>
          <span v-else>Ver</span>
        </RouterLink>
      </template>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useNotificationsStore } from '@/stores/notifications'
import type { FormData, FormStatus } from '@/types/forms'
import DataTable from '@/components/tables/DataTable.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'

const PAGE_SIZE = 20

const TABS = [
  { key: 'all', label: 'Todos' },
  { key: 'draft', label: 'Borradores' },
  { key: 'pending', label: 'En Revisión' },
  { key: 'rejected', label: 'Devueltos' },
  { key: 'approved', label: 'Aprobados' },
] as const

type TabKey = (typeof TABS)[number]['key']

const COLUMNS = [
  { key: 'template_nombre', label: 'Formulario', sortable: true },
  { key: 'fecha_referencia', label: 'Fecha Referencia', sortable: true },
  { key: 'estado', label: 'Estado', sortable: false },
  { key: 'acciones', label: 'Acciones', sortable: false, width: '120px' },
]

const { get } = useApi()
const notifications = useNotificationsStore()

const loading = ref(true)
const allForms = ref<FormData[]>([])
const total = ref(0)
const currentPage = ref(1)
const activeTab = ref<TabKey>('all')
const filterStart = ref('')
const filterEnd = ref('')
const searchQ = ref('')
const sortKey = ref('fecha_referencia')
const sortDir = ref<'asc' | 'desc'>('desc')

const tabCounts = computed(() => {
  const counts: Record<string, number> = {}
  for (const f of allForms.value) {
    counts[f.estado] = (counts[f.estado] ?? 0) + 1
  }
  counts['all'] = allForms.value.length
  return counts
})

const tableRows = computed(() =>
  allForms.value.map((f) => ({
    id: f.id,
    template_nombre: f.template_nombre,
    fecha_referencia: f.fecha_referencia,
    estado: f.estado,
    acciones: null,
  })),
)

function formatDate(dateStr: string): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('es-CO', { day: 'numeric', month: 'short', year: 'numeric' })
}

function setTab(tab: TabKey) {
  activeTab.value = tab
  currentPage.value = 1
  loadForms()
}

function clearFilters() {
  filterStart.value = ''
  filterEnd.value = ''
  loadForms()
}

function onSearch(q: string) {
  searchQ.value = q
  currentPage.value = 1
  loadForms()
}

function onSort(key: string, dir: 'asc' | 'desc') {
  sortKey.value = key
  sortDir.value = dir
  loadForms()
}

function onPageChange(page: number) {
  currentPage.value = page
  loadForms()
}

async function loadForms() {
  loading.value = true
  try {
    const params = new URLSearchParams({
      page: String(currentPage.value),
      size: String(PAGE_SIZE),
    })
    if (activeTab.value !== 'all') params.set('estado', activeTab.value)
    if (filterStart.value) params.set('start_date', filterStart.value)
    if (filterEnd.value) params.set('end_date', filterEnd.value)
    if (searchQ.value) params.set('search', searchQ.value)

    const result = await get<{ items: FormData[]; total: number }>(`/forms/inbox?${params}`)
    allForms.value = result.items
    total.value = result.total
  } catch {
    notifications.error('Error', 'No se pudieron cargar los trámites.')
  } finally {
    loading.value = false
  }
}

onMounted(loadForms)
</script>
