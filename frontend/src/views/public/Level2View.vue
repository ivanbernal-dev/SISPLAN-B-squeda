<template>
  <div class="min-h-screen bg-gray-50">

    <!-- Encabezado con breadcrumb ────────────────────────────────── -->
    <div class="bg-white border-b border-gray-100 shadow-sm">
      <div class="max-w-6xl mx-auto px-6 py-6">
        <nav class="flex items-center gap-2 text-sm font-barlow text-gray-400 mb-4">
          <RouterLink to="/estadisticas" class="hover:text-ubpd-teal transition-colors">
            Estadísticas
          </RouterLink>
          <span>›</span>
          <span class="text-ubpd-gris font-semibold">{{ kpiLabel }}</span>
        </nav>

        <div class="flex flex-col sm:flex-row items-center sm:items-start gap-6">
          <!-- Gauge resumen padre -->
          <div v-if="parentKpi" class="flex flex-col items-center bg-gray-50 rounded-2xl border border-gray-100 px-6 pt-4 pb-3 shrink-0">
            <GaugeChart
              :value="parentKpi.valor"
              :color="gaugeColor(parentKpi.valor)"
              size="sm"
            />
            <p class="text-xs font-barlow text-gray-400 mt-1 text-center">Avance general</p>
          </div>
          <!-- Título -->
          <div class="flex flex-col justify-center">
            <h1 class="text-2xl font-bold font-montserrat text-ubpd-gris leading-snug">
              {{ kpiLabel }}
            </h1>
            <p class="text-sm font-barlow text-gray-500 mt-1">
              Sub-indicadores del indicador seleccionado
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Grilla de sub-KPIs ───────────────────────────────────────── -->
    <div class="max-w-6xl mx-auto px-6 py-10">

      <!-- Loading -->
      <div v-if="loading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="n in 5" :key="n"
          class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 flex flex-col items-center gap-3 animate-pulse"
        >
          <div class="h-4 bg-gray-200 rounded w-3/4" />
          <div class="w-44 h-28 bg-gray-100 rounded-full mt-2" />
          <div class="h-3 bg-gray-100 rounded w-1/2" />
        </div>
      </div>

      <!-- Gauges nivel 2 -->
      <div v-else-if="subKpis.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="(kpi, idx) in subKpis"
          :key="kpi.key"
          class="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md
                 transition-all duration-200 cursor-pointer group flex flex-col items-center
                 px-6 pt-6 pb-5"
          @click="navigateToForms(kpi)"
          role="button"
          :aria-label="`Ver formularios de ${kpi.label}`"
        >
          <!-- Título -->
          <h3 class="text-sm font-semibold font-montserrat text-ubpd-gris text-center leading-snug min-h-[2.5rem] flex items-center">
            <span class="text-ubpd-teal font-bold mr-1.5">{{ idx + 1 }}.</span>
            {{ kpi.label }}
          </h3>

          <!-- Gauge -->
          <div class="w-full flex justify-center mt-1">
            <GaugeChart
              :value="kpi.valor"
              :color="gaugeColor(kpi.valor)"
              size="md"
            />
          </div>

          <!-- Badge estado -->
          <span
            class="mt-1 text-xs font-cuerpo font-semibold px-2.5 py-0.5 rounded-full"
            :class="scoreClass(kpi.valor)"
          >
            {{ scoreLabel(kpi.valor) }}
          </span>

          <!-- Acción -->
          <p class="mt-3 text-xs font-cuerpo font-semibold text-ubpd-teal opacity-0
                     group-hover:opacity-100 transition-opacity">
            Ver registros →
          </p>
        </div>
      </div>

      <!-- Sin datos -->
      <div v-else class="flex flex-col items-center justify-center py-24 text-gray-400">
        <svg class="w-14 h-14 mb-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
        </svg>
        <p class="text-base font-barlow">No hay sub-indicadores para este KPI.</p>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'
import GaugeChart from '@/components/charts/GaugeChart.vue'
import { useStatsFilterStore } from '@/stores/statsFilter'

interface SubKpi {
  key: string
  label: string
  valor: number
  nivel1_key: string | null
  updated_at: string | null
}

interface ParentKpi {
  key: string
  label: string
  valor: number
}

const route = useRoute()
const router = useRouter()
const { get } = useApi()
const filterStore = useStatsFilterStore()

const loading = ref(true)
const subKpis = ref<SubKpi[]>([])
const parentKpi = ref<ParentKpi | null>(null)

const kpiKey = computed(() => route.params.indicadorId as string)
const kpiLabel = computed(() =>
  parentKpi.value?.label ?? (route.query.label as string) ?? kpiKey.value
)

function gaugeColor(v: number): string {
  if (v >= 70) return '#3e9c45'
  if (v >= 40) return '#f59e0b'
  return '#ef6c00'
}

function scoreClass(v: number) {
  if (v >= 70) return 'bg-green-50 text-green-700'
  if (v >= 40) return 'bg-amber-50 text-amber-700'
  return 'bg-orange-50 text-orange-700'
}

function scoreLabel(v: number) {
  if (v >= 70) return 'Avanzado'
  if (v >= 40) return 'En progreso'
  return 'Inicial'
}

function navigateToForms(kpi: SubKpi) {
  router.push({
    path: `/estadisticas/${kpiKey.value}/forms/${kpi.key}`,
    query: { kpiLabel: kpiLabel.value, subLabel: kpi.label },
  })
}

async function loadData() {
  loading.value = true
  try {
    // Los KPIs nivel 2 siempre muestran el último valor guardado del pipeline
    // El filtro de fecha solo afecta la lista de formularios (nivel 3)
    subKpis.value = await get<SubKpi[]>(`/stats/kpis/${kpiKey.value}`)
    const nivel1 = await get<ParentKpi[]>('/stats/kpis')
    parentKpi.value = nivel1.find((k) => k.key === kpiKey.value) ?? null
  } catch {
    subKpis.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
watch(kpiKey, loadData)
</script>
