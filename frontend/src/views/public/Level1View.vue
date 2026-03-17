<template>
  <div class="space-y-8">
    <!-- Page header -->
    <div>
      <h1 class="text-3xl font-bold font-montserrat text-ubpd-gris leading-tight">
        Sistema de Estadísticas de la Unidad de Búsqueda
      </h1>
      <p class="text-sm font-barlow text-gray-500 mt-1">
        Período: {{ formatDate(statsFilter.startDate) }} — {{ formatDate(statsFilter.endDate) }}
      </p>
    </div>

    <!-- Date filter bar -->
    <div class="bg-white border border-gray-200 rounded-xl p-4 flex flex-wrap items-center gap-4 shadow-sm">
      <span class="text-sm font-semibold font-barlow text-gray-600">Filtrar por período:</span>

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

      <!-- Presets -->
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

    <!-- Gauge grid -->
    <div>
      <!-- Skeleton -->
      <div v-if="loading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="n in 6"
          :key="n"
          class="bg-white rounded-xl border border-gray-200 shadow-sm p-6 flex flex-col items-center gap-3 animate-pulse"
        >
          <div class="w-48 h-44 bg-gray-200 rounded-full" />
          <div class="h-4 bg-gray-200 rounded w-3/4" />
          <div class="h-3 bg-gray-100 rounded w-1/2" />
        </div>
      </div>

      <!-- Actual gauges -->
      <div v-else-if="indicators.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="ind in indicators"
          :key="ind.indicador_id"
          class="flex flex-col gap-2"
        >
          <IndicatorCard
            :indicador-id="ind.indicador_id"
            :nombre="ind.nombre"
            :completitud="ind.completitud_promedio"
            :total-formularios="ind.total_formularios"
            variant="primary"
            size="md"
            @click="navigateToLevel2"
          />

          <!-- Summary card below gauge -->
          <div class="bg-white border border-gray-100 rounded-lg px-4 py-3 shadow-sm text-sm font-barlow">
            <div class="flex justify-between text-gray-500">
              <span>Total formularios</span>
              <span class="font-semibold text-ubpd-gris">{{ ind.total_formularios }}</span>
            </div>
            <div class="flex justify-between text-gray-500 mt-1">
              <span>Último dato</span>
              <span class="font-semibold text-ubpd-gris">{{ formatDate(ind.end_date) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-else class="text-center py-16 text-gray-400">
        <p class="text-base font-barlow">No hay indicadores disponibles para el período seleccionado.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useStatsFilter } from '@/stores/statsFilter'
import IndicatorCard from '@/components/charts/IndicatorCard.vue'

interface GlobalIndicator {
  indicador_id: number
  nombre: string
  completitud_promedio: number
  total_formularios: number
  start_date: string
  end_date: string
}

type PresetKey = 'this_month' | 'last_quarter' | 'this_year'

const PRESETS: { key: PresetKey; label: string }[] = [
  { key: 'this_month', label: 'Este mes' },
  { key: 'last_quarter', label: 'Último trimestre' },
  { key: 'this_year', label: 'Año actual' },
]

const router = useRouter()
const { get } = useApi()
const statsFilter = useStatsFilter()

const loading = ref(true)
const indicators = ref<GlobalIndicator[]>([])
const activePreset = ref<PresetKey | null>('this_year')

function formatDate(dateStr: string): string {
  if (!dateStr) return '—'
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('es-CO', {
    day: 'numeric', month: 'long', year: 'numeric',
  })
}

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

function navigateToLevel2(indicadorId: string | number) {
  router.push({
    path: `/estadisticas/${indicadorId}`,
    query: statsFilter.queryParams,
  })
}

async function loadStats() {
  loading.value = true
  try {
    indicators.value = await get<GlobalIndicator[]>('/stats/global', {
      params: statsFilter.queryParams,
    })
  } catch {
    // Keep existing data, silent fail for public page
    indicators.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadStats)
</script>
