<template>
  <div class="min-h-screen bg-gray-50">

    <!-- Encabezado ───────────────────────────────────────────────── -->
    <div class="bg-white border-b border-gray-100 shadow-sm">
      <div class="max-w-6xl mx-auto px-6 py-8 text-center">
        <h1 class="text-3xl font-bold font-montserrat text-ubpd-gris">
          Plan de Acción Institucional 2026
        </h1>
        <p class="text-sm font-barlow text-gray-500 mt-2">
          Avance de las líneas estratégicas y sus productos
          <span v-if="updatedAt" class="ml-2 text-gray-400">— Actualizado: {{ updatedAt }}</span>
        </p>

        <!-- Selector temporal -->
        <div class="mt-5 inline-flex bg-gray-100 rounded-xl p-1 gap-1" role="tablist">
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
      </div>
    </div>

    <!-- Contenido ────────────────────────────────────────────────── -->
    <div class="max-w-6xl mx-auto px-6 py-10">

      <!-- Loading skeleton -->
      <div v-if="loading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="n in 5" :key="n"
          class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 flex flex-col items-center gap-3 animate-pulse"
        >
          <div class="h-4 bg-gray-200 rounded w-3/4" />
          <div class="w-48 h-28 bg-gray-100 rounded-full mt-2" />
          <div class="h-3 bg-gray-100 rounded w-1/2 mt-1" />
        </div>
      </div>

      <!-- Gauges nivel 1 -->
      <div v-else-if="kpis.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="(kpi, idx) in kpis"
          :key="kpi.key"
          class="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md
                 transition-all duration-200 cursor-pointer group flex flex-col items-center
                 px-6 pt-6 pb-5"
          @click="navigateToLevel2(kpi.key, kpi.label)"
          role="button"
          :aria-label="`Ver detalle de ${kpi.label}`"
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

          <!-- Descripción / subtítulo -->
          <p class="text-xs font-barlow text-gray-400 text-center mt-1 min-h-[1.25rem]">
            {{ kpi.descripcion ?? '' }}
          </p>

          <!-- Acción -->
          <p class="mt-3 text-xs font-cuerpo font-semibold text-ubpd-teal opacity-0
                     group-hover:opacity-100 transition-opacity">
            Ver detalle →
          </p>
        </div>
      </div>

      <!-- Sin datos -->
      <div v-else class="flex flex-col items-center justify-center py-24 text-gray-400">
        <svg class="w-14 h-14 mb-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
        </svg>
        <p class="text-base font-barlow">No hay indicadores disponibles.</p>
        <p class="text-sm font-barlow mt-1 text-gray-300">El pipeline aún no ha sido ejecutado.</p>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'
import GaugeChart from '@/components/charts/GaugeChart.vue'
import { useStatsFilterStore } from '@/stores/statsFilter'

interface KpiNivel1 {
  key: string
  label: string
  valor: number
  descripcion: string | null
  updated_at: string | null
  periodo?: string
}

const router = useRouter()
const { get } = useApi()
const filterStore = useStatsFilterStore()

const loading = ref(true)
const kpis = ref<KpiNivel1[]>([])
const updatedAt = ref<string | null>(null)
const periodo = ref<string>(filterStore.periodo || 'anual')

const periodoOptions = [
  { value: 'anual', label: 'Anual' },
  { value: 'trim1', label: 'Trim 1' },
  { value: 'trim2', label: 'Trim 2' },
  { value: 'trim3', label: 'Trim 3' },
  { value: 'trim4', label: 'Trim 4' },
]

function setPeriodo(p: string) {
  periodo.value = p
  filterStore.setPeriodo(p)
  loadKpis()
}

function gaugeColor(v: number): string {
  if (v >= 70) return '#3e9c45'
  if (v >= 40) return '#f59e0b'
  return '#ef6c00'
}

function navigateToLevel2(kpiKey: string, label: string) {
  router.push({ path: `/estadisticas/${kpiKey}`, query: { label, periodo: periodo.value } })
}

async function loadKpis() {
  loading.value = true
  try {
    const data = await get<KpiNivel1[]>('/stats/kpis', { params: { periodo: periodo.value } })
    kpis.value = data
    const last = data.find((k) => k.updated_at)?.updated_at
    if (last) {
      updatedAt.value = new Date(last).toLocaleString('es-CO', {
        day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
      })
    }
  } catch {
    kpis.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadKpis)
</script>
