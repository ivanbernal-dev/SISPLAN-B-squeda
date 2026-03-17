<template>
  <div class="space-y-8">
    <!-- Breadcrumb -->
    <nav class="flex items-center gap-2 text-sm font-barlow text-gray-500" aria-label="Navegación">
      <RouterLink to="/estadisticas" class="hover:text-ubpd-teal transition-colors">
        Estadísticas
      </RouterLink>
      <span aria-hidden="true">›</span>
      <span class="text-ubpd-gris font-semibold">{{ indicadorNombre || 'Indicador' }}</span>
    </nav>

    <!-- Page header -->
    <div>
      <h1 class="text-2xl font-bold font-montserrat text-ubpd-gris">
        {{ indicadorNombre || 'Cargando...' }}
      </h1>
      <p class="text-sm font-barlow text-gray-500 mt-0.5">
        Desagregación por formulario — {{ statsFilter.startDate }} a {{ statsFilter.endDate }}
      </p>
    </div>

    <!-- Date filter bar (same as Level1) -->
    <div class="bg-white border border-gray-200 rounded-xl p-4 flex flex-wrap items-center gap-4 shadow-sm">
      <span class="text-sm font-semibold font-barlow text-gray-600">Período:</span>
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

    <!-- Total badge -->
    <p v-if="!loading && templates.length > 0" class="text-sm font-barlow text-gray-600">
      <span class="font-semibold text-ubpd-gris">{{ totalFormularios }}</span>
      formularios encontrados en este período
    </p>

    <!-- Gauge grid -->
    <div>
      <!-- Skeleton -->
      <div v-if="loading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="n in 4"
          :key="n"
          class="bg-white rounded-xl border border-gray-200 shadow-sm p-6 flex flex-col items-center gap-3 animate-pulse"
        >
          <div class="w-48 h-44 bg-gray-200 rounded" />
          <div class="h-4 bg-gray-200 rounded w-3/4" />
        </div>
      </div>

      <div v-else-if="templates.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <IndicatorCard
          v-for="tmpl in templates"
          :key="tmpl.template_id"
          :indicador-id="tmpl.template_id"
          :nombre="tmpl.nombre"
          :completitud="tmpl.completitud"
          :total-formularios="tmpl.total_formularios"
          variant="secondary"
          size="md"
          @click="navigateToLevel3"
        />
      </div>

      <div v-else class="text-center py-16 text-gray-400">
        <p class="text-base font-barlow">No hay datos para este indicador en el período seleccionado.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useStatsFilter } from '@/stores/statsFilter'
import IndicatorCard from '@/components/charts/IndicatorCard.vue'

interface TemplateStats {
  template_id: string
  nombre: string
  completitud: number
  total_formularios: number
}

type PresetKey = 'this_month' | 'last_quarter' | 'this_year'

const PRESETS: { key: PresetKey; label: string }[] = [
  { key: 'this_month', label: 'Este mes' },
  { key: 'last_quarter', label: 'Último trimestre' },
  { key: 'this_year', label: 'Año actual' },
]

const route = useRoute()
const router = useRouter()
const { get } = useApi()
const statsFilter = useStatsFilter()

const loading = ref(true)
const templates = ref<TemplateStats[]>([])
const indicadorNombre = ref('')
const activePreset = ref<PresetKey | null>(null)

const indicadorId = computed(() => route.params.indicador_id as string)

const totalFormularios = computed(() =>
  templates.value.reduce((sum, t) => sum + t.total_formularios, 0),
)

function onStartDateChange(e: Event) {
  statsFilter.setDates((e.target as HTMLInputElement).value, statsFilter.endDate)
  activePreset.value = null
  loadStats()
}

function onEndDateChange(e: Event) {
  statsFilter.setDates(statsFilter.startDate, (e.target as HTMLInputElement).value)
  activePreset.value = null
  loadStats()
}

function applyPreset(preset: PresetKey) {
  statsFilter.setPreset(preset)
  activePreset.value = preset
  loadStats()
}

function navigateToLevel3(templateId: string | number) {
  router.push({
    path: `/estadisticas/${indicadorId.value}/${templateId}`,
    query: statsFilter.queryParams,
  })
}

async function loadStats() {
  loading.value = true
  try {
    const data = await get<TemplateStats[]>('/stats/by-template', {
      params: {
        indicador_id: indicadorId.value,
        ...statsFilter.queryParams,
      },
    })
    templates.value = data
    // Set indicador name from route state or first result meta
    if (route.query.nombre) {
      indicadorNombre.value = String(route.query.nombre)
    }
  } catch {
    templates.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // Sync URL dates to store if present
  if (route.query.start_date) statsFilter.setDates(String(route.query.start_date), String(route.query.end_date ?? statsFilter.endDate))
  loadStats()
})

watch(indicadorId, loadStats)
</script>
