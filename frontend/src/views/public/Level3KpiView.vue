<template>
  <div class="min-h-screen bg-gray-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-6">

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

    <!-- Header con resumen ───────────────────────────────────── -->
    <div class="bg-white rounded-2xl border border-gray-100 shadow-sm px-6 py-5 flex flex-col sm:flex-row sm:items-center gap-5">
      <div class="flex-1">
        <h1 class="text-xl font-bold font-montserrat text-ubpd-gris leading-snug">{{ pageTitle }}</h1>
        <p class="text-sm font-barlow text-gray-500 mt-0.5">
          Actividades reportadas — periodo
          <span class="font-semibold text-ubpd-gris">{{ periodoLabel }}</span>
          <span v-if="!loading" class="font-semibold text-ubpd-gris">— {{ total }} registros</span>
        </p>

        <!-- Selector temporal -->
        <div class="mt-3 inline-flex bg-gray-100 rounded-xl p-1 gap-1" role="tablist">
          <button
            v-for="opt in periodoOptions"
            :key="opt.value"
            type="button"
            @click="setPeriodo(opt.value)"
            :class="[
              'px-3 py-1 rounded-lg text-xs font-cuerpo font-semibold transition-all',
              periodo === opt.value
                ? 'bg-white text-ubpd-teal shadow-sm'
                : 'text-gray-500 hover:text-ubpd-gris',
            ]"
          >
            {{ opt.label }}
          </button>
        </div>

        <!-- Barra de avance promedio -->
        <div v-if="!loading && promedioFinal !== null" class="mt-4">
          <div class="flex items-center justify-between mb-1">
            <span class="font-cuerpo text-xs text-gray-500 uppercase tracking-wide">% Avance final promedio</span>
            <span class="font-cuerpo text-sm font-bold" :class="colorText(promedioFinal)">
              {{ promedioFinal.toFixed(1) }}%
            </span>
          </div>
          <div class="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-700"
              :class="colorBar(promedioFinal)"
              :style="{ width: `${Math.min(100, promedioFinal)}%` }"
            />
          </div>
          <p class="mt-1 text-xs font-cuerpo" :class="colorText(promedioFinal)">
            {{ scoreLabel(promedioFinal) }}
          </p>
        </div>
      </div>
      <!-- Badge estado -->
      <div v-if="!loading && promedioFinal !== null"
        class="shrink-0 flex flex-col items-center justify-center
               w-24 h-24 rounded-2xl border-2"
        :class="colorBadgeBg(promedioFinal)">
        <span class="font-montserrat text-2xl font-bold" :class="colorText(promedioFinal)">
          {{ promedioFinal.toFixed(0) }}<span class="text-base">%</span>
        </span>
        <span class="font-cuerpo text-xs mt-0.5" :class="colorText(promedioFinal)">avance</span>
      </div>
    </div>

    <!-- Skeleton ─────────────────────────────────────────────── -->
    <div v-if="loading" class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden animate-pulse">
      <div class="px-6 py-4 border-b border-gray-100 bg-gray-50 flex gap-4">
        <div class="h-4 w-40 bg-gray-200 rounded" />
        <div class="h-4 w-28 bg-gray-200 rounded" />
        <div class="h-4 w-24 bg-gray-200 rounded" />
      </div>
      <div v-for="n in 5" :key="n" class="px-6 py-5 border-b border-gray-50 flex gap-6 items-center">
        <div class="h-4 w-48 bg-gray-100 rounded" />
        <div class="h-4 w-32 bg-gray-100 rounded" />
        <div class="h-3 w-24 bg-gray-100 rounded-full ml-auto" />
      </div>
    </div>

    <!-- Tabla de registros ───────────────────────────────────── -->
    <div v-else-if="items.length > 0" class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">

      <!-- Cabecera de tabla -->
      <div class="grid grid-cols-12 gap-3 px-6 py-3 bg-ubpd-gris/5 border-b border-gray-100 text-xs font-semibold text-gray-500 uppercase tracking-wide font-cuerpo">
        <div class="col-span-4">Actividad clave</div>
        <div class="col-span-2 hidden md:block">Dependencia / Trim</div>
        <div class="col-span-1 text-right">Proyec.</div>
        <div class="col-span-1 text-right">Alcanz.</div>
        <div class="col-span-2">% Final</div>
        <div class="col-span-2 text-center">Estado</div>
      </div>

      <!-- Filas -->
      <div
        v-for="item in items"
        :key="item.id"
        class="grid grid-cols-12 gap-3 px-6 py-4 border-b border-gray-50
               hover:bg-ubpd-teal/5 transition cursor-pointer items-center text-sm font-cuerpo"
        @click="viewDetail(item.id)"
      >
        <!-- Actividad -->
        <div class="col-span-4">
          <p class="font-medium text-ubpd-gris leading-snug line-clamp-2">
            {{ getActividad(item.datos_dinamicos) }}
          </p>
          <p class="text-xs text-gray-400 mt-0.5 md:hidden">
            {{ item.dependency || '—' }} · {{ getTrimestre(item.datos_dinamicos) }}
          </p>
        </div>

        <!-- Dependencia + trimestre -->
        <div class="col-span-2 hidden md:block">
          <p class="text-gray-700 truncate">{{ item.dependency || '—' }}</p>
          <p class="text-xs text-gray-400">{{ getTrimestre(item.datos_dinamicos) }}</p>
        </div>

        <!-- Proyectado (con decimales) -->
        <div class="col-span-1 text-right text-gray-700 tabular-nums">
          {{ formatPct(item.datos_dinamicos?.pct_avance_proyectado) }}
        </div>

        <!-- Alcanzado (con decimales) -->
        <div class="col-span-1 text-right text-gray-700 tabular-nums">
          {{ formatPct(item.datos_dinamicos?.pct_avance_alcanzado) }}
        </div>

        <!-- % Avance final con barra:
             - Calculado AL VUELO desde alcanzado/proyectado (no depende del
               valor guardado en datos_dinamicos, que puede estar stale).
             - La barra muestra alcanzado SOBRE proyectado (el 100% del
               ancho representa el proyectado). 100% = se cumplió la meta. -->
        <div class="col-span-2">
          <template v-if="getPctFinalLive(item.datos_dinamicos) !== null">
            <div class="flex items-center gap-2">
              <div class="relative flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full"
                  :class="colorBar(getPctFinalLive(item.datos_dinamicos)!)"
                  :style="{ width: `${Math.min(100, getPctFinalLive(item.datos_dinamicos)!)}%` }"
                />
              </div>
              <span class="text-xs font-bold shrink-0 w-14 text-right tabular-nums"
                    :class="colorText(getPctFinalLive(item.datos_dinamicos)!)">
                {{ getPctFinalLive(item.datos_dinamicos)!.toFixed(1) }}%
              </span>
            </div>
          </template>
          <span v-else class="text-xs text-gray-400">—</span>
        </div>

        <!-- Estado -->
        <div class="col-span-2 flex items-center justify-center gap-2">
          <span
            class="text-xs font-semibold px-2.5 py-1 rounded-full"
            :class="estadoClass(getEstado(item.datos_dinamicos))"
          >
            {{ getEstado(item.datos_dinamicos) || '—' }}
          </span>
          <button
            class="p-1 rounded text-gray-300 hover:text-ubpd-teal transition"
            @click.stop="viewDetail(item.id)"
            title="Ver detalle"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Paginación ─────────────────────────────────────────── -->
      <div v-if="totalPages > 1" class="px-6 py-4 border-t border-gray-100 flex items-center justify-between">
        <p class="font-cuerpo text-sm text-gray-500">
          Página {{ page }} de {{ totalPages }} · {{ total }} registros
        </p>
        <div class="flex gap-1.5">
          <button
            :disabled="page <= 1"
            @click="changePage(page - 1)"
            class="px-3 py-1.5 rounded-lg border border-gray-200 font-cuerpo text-sm text-gray-500
                   hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            ← Anterior
          </button>
          <button
            :disabled="page >= totalPages"
            @click="changePage(page + 1)"
            class="px-3 py-1.5 rounded-lg border border-gray-200 font-cuerpo text-sm text-gray-500
                   hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            Siguiente →
          </button>
        </div>
      </div>
    </div>

    <!-- Sin datos ────────────────────────────────────────────── -->
    <div v-else class="bg-white rounded-2xl border border-gray-100 shadow-sm text-center py-20 text-gray-400">
      <svg class="w-12 h-12 mx-auto mb-4 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
      </svg>
      <p class="font-barlow text-base">No hay formularios aprobados para este indicador.</p>
      <p class="font-barlow text-sm mt-1 text-gray-300">El indicador puede no tener un template asociado aún.</p>
    </div>

  </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useStatsFilterStore } from '@/stores/statsFilter'

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
const total = ref(0)
const page = ref(1)
const pageSize = 20
const items = ref<FormItem[]>([])
const kpiLabel = ref('')
const templateNombre = ref<string | null>(null)
const templateId = ref<string | null>(null)
const periodo = ref<string>(filterStore.periodo || 'anual')

const kpiKey = computed(() => route.params.kpiKey as string)
const subKpiKey = computed(() => route.params.subKpiKey as string)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

const pageTitle = computed(() =>
  kpiLabel.value || (route.query.subLabel as string) || subKpiKey.value
)

const periodoLabel = computed(() =>
  periodoOptions.find((o) => o.value === periodo.value)?.label ?? 'Anual',
)

// Promedio de pct_avance_final (0-100)
// Avance del PRODUCTO = Σ alcanzado / Σ proyectado × 100
// (mismo número que el velocímetro de nivel 2). NO es el promedio de los
// pct_avance_final por fila — esa fórmula daría "promedio de porcentajes"
// que es estadísticamente distinto y subestima/sobrestima cuando las
// actividades tienen pesos distintos.
const promedioFinal = computed<number | null>(() => {
  if (items.value.length === 0) return null
  let sumProy = 0
  let sumAlc  = 0
  let aplica  = 0
  for (const i of items.value) {
    const proy = toNum(i.datos_dinamicos?.['pct_avance_proyectado'])
    const alc  = toNum(i.datos_dinamicos?.['pct_avance_alcanzado'])
    if (proy === null || proy <= 0) continue   // actividad no aplica este periodo
    sumProy += proy
    sumAlc  += (alc ?? 0)
    aplica  += 1
  }
  if (aplica === 0 || sumProy <= 0) return null
  return (sumAlc / sumProy) * 100
})

// ── Helpers de datos PAI ──────────────────────────────────────
function toNum(v: any): number | null {
  if (v === null || v === undefined || v === '') return null
  const n = parseFloat(String(v).replace(',', '.'))
  return isNaN(n) ? null : n
}

function getActividad(dd: Record<string, any> | null): string {
  if (!dd) return '—'
  return (
    dd['actividad_clave'] ||
    dd['indicador'] ||
    dd['entregable_trimestre'] ||
    dd['entregable_total'] ||
    '—'
  )
}

function getTrimestre(dd: Record<string, any> | null): string {
  if (!dd) return ''
  return dd['periodo_reporte'] || dd['trimestre'] || ''
}

// Lee el pct_avance_final guardado (puede ser fracción 0..1 de versiones
// viejas, o porcentaje 0..100 de la versión nueva). NO se usa para mostrar
// — se mantiene solo por compatibilidad.
function getPctFinal(dd: Record<string, any> | null): number | null {
  return toNum(dd?.['pct_avance_final'])
}

// Versión LIVE: siempre calcula desde alcanzado/proyectado. Devuelve el
// porcentaje 0..100 (puede ser >100 si superó la meta). Devuelve null si
// proyectado es 0 o no aplica ("actividad no aplica este periodo").
function getPctFinalLive(dd: Record<string, any> | null): number | null {
  if (!dd) return null
  const proy = toNum(dd['pct_avance_proyectado'])
  const alc  = toNum(dd['pct_avance_alcanzado'])
  if (proy === null || proy <= 0) return null
  return (alc ?? 0) / proy * 100
}

// Estado derivado de getPctFinalLive (consistente con la barra y la
// fórmula nueva, no depende de estado_actividad que puede estar stale).
function getEstadoLive(dd: Record<string, any> | null): string {
  const pct = getPctFinalLive(dd)
  if (pct === null) return 'No Aplica'
  if (pct >= 90) return 'Cumple'
  if (pct >= 70) return 'Cumple Parcialmente'
  if (pct >  0)  return 'No Cumple'
  return 'No Aplica'
}

function getEstado(dd: Record<string, any> | null): string {
  // Mantenido por compatibilidad — ahora usa la versión live.
  return getEstadoLive(dd)
}

// Formatea con 2 decimales por defecto (los valores reportados suelen
// venir con decimales que se pierden si se redondea a entero).
function formatPct(v: any, digits = 2): string {
  const n = toNum(v)
  if (n === null) return '—'
  return `${n.toFixed(digits)}%`
}

// ── Helpers de color ──────────────────────────────────────────
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

function colorBadgeBg(pct: number) {
  if (pct >= 90) return 'border-ubpd-verde/30 bg-green-50'
  if (pct >= 60) return 'border-amber-300 bg-amber-50'
  return 'border-orange-300 bg-orange-50'
}

function scoreLabel(pct: number) {
  if (pct >= 90) return 'Cumple'
  if (pct >= 60) return 'Cumple parcialmente'
  if (pct >= 1) return 'No cumple'
  return 'Sin avance'
}

function estadoClass(estado: string): string {
  const s = (estado || '').toLowerCase()
  if (s.includes('cumple parcial')) return 'bg-amber-50 text-amber-700'
  if (s === 'cumple') return 'bg-green-50 text-green-700'
  if (s.includes('no cumple')) return 'bg-orange-50 text-orange-700'
  if (s.includes('no aplica')) return 'bg-gray-100 text-gray-500'
  return 'bg-gray-50 text-gray-400'
}

function setPeriodo(p: string) {
  periodo.value = p
  filterStore.setPeriodo(p)
  page.value = 1
  loadForms()
}

function viewDetail(formId: string) {
  router.push({
    path: `/estadisticas/${kpiKey.value}/forms/${subKpiKey.value}/${formId}`,
    query: {
      kpiLabel: route.query.kpiLabel,
      subLabel: kpiLabel.value,
      templateNombre: templateNombre.value ?? undefined,
      periodo: periodo.value,
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
    const params: Record<string, string | number> = {
      page: page.value,
      size: pageSize,
      periodo: periodo.value,
    }
    const data = await get<KpiForms>(`/stats/kpis/${subKpiKey.value}/forms`, { params })
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
