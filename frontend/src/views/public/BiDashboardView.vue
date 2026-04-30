<template>
  <div class="min-h-screen bg-white">

    <!-- ── Header estilo BI ───────────────────────────────────── -->
    <header class="border-b border-gray-200 bg-white">
      <div class="max-w-[1400px] mx-auto px-6 py-4 flex items-center justify-between gap-4">
        <div class="flex items-center gap-4">
          <img src="/logo-ubpd-placeholder.svg" alt="UBPD" class="h-12 w-auto" />
          <div>
            <h1 class="font-subtitulo font-bold text-base text-[#5B2B5E] tracking-wide">
              UNIDAD DE BÚSQUEDA DE PERSONAS DESAPARECIDAS
            </h1>
            <p class="font-cuerpo italic text-sm text-gray-500 mt-0.5">
              Planes Regionales de Búsqueda
            </p>
          </div>
        </div>
        <div class="text-right">
          <p class="font-cuerpo text-sm text-gray-700">{{ formatDate(status?.uploaded_at) }}</p>
          <p class="font-cuerpo text-xs text-gray-400 italic">Última Actualización</p>
        </div>
      </div>

      <!-- Tabs de página -->
      <nav class="max-w-[1400px] mx-auto px-6 flex items-end gap-1 border-t border-gray-100">
        <button
          v-for="p in pages"
          :key="p.id"
          type="button"
          class="px-5 py-2.5 font-cuerpo text-sm font-semibold border-b-2 transition-colors"
          :class="currentPage === p.id
            ? 'border-[#5B2B5E] text-[#5B2B5E]'
            : 'border-transparent text-gray-400 hover:text-gray-600'"
          @click="currentPage = p.id"
        >
          {{ p.label }}
        </button>
        <div class="ml-auto text-xs text-gray-400 font-cuerpo py-2">
          Página {{ currentPage }} de 2
        </div>
      </nav>
    </header>

    <!-- Empty state -->
    <div v-if="!loading && !filters?.anios?.length" class="max-w-3xl mx-auto px-4 py-16 text-center">
      <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <p class="font-cuerpo text-xl text-ubpd-gris font-semibold mb-2">No hay datos disponibles</p>
      <p class="font-cuerpo text-gray-500">
        Un administrador debe cargar el archivo Excel de metas para que este dashboard muestre información.
      </p>
    </div>

    <!-- ══════════════════════ PÁGINA 1 ══════════════════════ -->
    <main v-else-if="currentPage === 1" class="max-w-[1400px] mx-auto px-6 py-6 space-y-4">

      <!-- Filtros del reporte -->
      <section>
        <h2 class="font-cuerpo italic text-sm text-gray-500 mb-2">Filtros del reporte:</h2>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          <div class="filter-box">
            <label class="filter-label">Año</label>
            <select v-model.number="active.anio" @change="refreshPage1" class="filter-input">
              <option :value="null">Todos</option>
              <option v-for="a in filters?.anios ?? []" :key="a" :value="a">{{ a }}</option>
            </select>
          </div>
          <div class="filter-box">
            <label class="filter-label">Trimestre / Mes</label>
            <select v-model.number="active.mes" @change="refreshPage1" class="filter-input">
              <option :value="null">Todas</option>
              <option v-for="(n, i) in meses" :key="i+1" :value="i+1">{{ n }}</option>
            </select>
          </div>
          <div class="filter-box">
            <label class="filter-label">Regional</label>
            <select v-model="active.regional" @change="onRegionalChange" class="filter-input">
              <option :value="null">Todas</option>
              <option v-for="r in filters?.regionales ?? []" :key="r" :value="r">{{ r }}</option>
            </select>
          </div>
          <div class="filter-box">
            <label class="filter-label">GITT</label>
            <select v-model="active.gitt" @change="onGittChange" class="filter-input">
              <option :value="null">Todos</option>
              <option v-for="g in gittsForActiveRegion" :key="g" :value="g">{{ g }}</option>
            </select>
          </div>
          <div class="filter-box">
            <label class="filter-label">PRB</label>
            <select v-model="active.prb" @change="refreshPage1" class="filter-input">
              <option :value="null">Todos</option>
              <option v-for="p in prbsForActiveRegion" :key="p" :value="p">{{ p }}</option>
            </select>
          </div>
        </div>
        <div class="mt-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <div class="filter-box">
            <label class="filter-label">Nombre del indicador</label>
            <select v-model.number="active.cod_indicador" @change="refreshPage1" class="filter-input">
              <option :value="null">Todas</option>
              <option v-for="i in filters?.indicadores ?? []" :key="i.cod" :value="i.cod">
                {{ i.codigo }} — {{ truncate(i.nombre, 60) }}
              </option>
            </select>
          </div>
          <div v-if="hasActiveFilters" class="self-end">
            <button
              type="button"
              class="h-10 px-4 font-cuerpo text-xs border border-gray-300 rounded text-gray-600 hover:bg-gray-50"
              @click="clearFilters"
            >
              Limpiar filtros
            </button>
          </div>
        </div>
      </section>

      <!-- Indicadores de interés -->
      <section>
        <h2 class="font-cuerpo italic text-sm text-gray-500 mb-3 mt-2">Indicadores de interés</h2>
        <!-- 12 primeros en grid 4xN -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div v-for="card in indicadoresCards.slice(0, 12)" :key="card.cod" class="kpi-card">
            <p class="kpi-title" :title="card.nombre">{{ cardTitle(card) }}</p>
            <div class="flex justify-between items-start mt-2 gap-2">
              <div class="text-center flex-1">
                <p class="kpi-num">{{ formatNum(card.dato_2025) }}</p>
                <p class="kpi-lbl">Dato 2025</p>
              </div>
              <div class="text-center flex-1">
                <p class="kpi-num">{{ formatNum(card.avance) }}</p>
                <p class="kpi-lbl">Avance 2026</p>
              </div>
              <div class="text-center flex-1">
                <p class="kpi-num">{{ formatMeta(card.meta) }}</p>
                <p class="kpi-lbl">Meta 2026</p>
              </div>
            </div>
            <div class="mt-3 h-2 w-full rounded-full bg-gray-200 overflow-hidden">
              <div class="h-full bg-[#5B2B5E] transition-all duration-500"
                   :style="{ width: Math.min(100, card.pct) + '%' }" />
            </div>
            <p class="text-center mt-2 font-subtitulo text-lg font-bold text-gray-800">{{ formatPct(card.pct) }}</p>
            <p class="text-center text-[10px] italic text-gray-400">% Avance 2026</p>
          </div>
        </div>

        <!-- 13ª tarjeta centrada (Cuerpos Recuperados — como en el BI) -->
        <div v-if="indicadoresCards.length > 12" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-3">
          <div /><div />
          <div class="kpi-card">
            <p class="kpi-title" :title="indicadoresCards[12].nombre">{{ cardTitle(indicadoresCards[12]) }}</p>
            <div class="flex justify-between items-start mt-2 gap-2">
              <div class="text-center flex-1">
                <p class="kpi-num">{{ formatNum(indicadoresCards[12].dato_2025) }}</p>
                <p class="kpi-lbl">Dato 2025</p>
              </div>
              <div class="text-center flex-1">
                <p class="kpi-num">{{ formatNum(indicadoresCards[12].avance) }}</p>
                <p class="kpi-lbl">Avance 2026</p>
              </div>
              <div class="text-center flex-1">
                <p class="kpi-num">{{ formatMeta(indicadoresCards[12].meta) }}</p>
                <p class="kpi-lbl">Meta 2026</p>
              </div>
            </div>
            <div class="mt-3 h-2 w-full rounded-full bg-gray-200 overflow-hidden">
              <div class="h-full bg-[#5B2B5E] transition-all duration-500"
                   :style="{ width: Math.min(100, indicadoresCards[12].pct) + '%' }" />
            </div>
            <p class="text-center mt-2 font-subtitulo text-lg font-bold text-gray-800">{{ formatPct(indicadoresCards[12].pct) }}</p>
            <p class="text-center text-[10px] italic text-gray-400">% Avance 2026</p>
          </div>
          <div />
        </div>
      </section>

      <!-- Ejecución chart -->
      <section class="bg-white rounded border border-gray-200 p-4">
        <h3 class="font-subtitulo text-sm font-semibold text-gray-700 mb-3">Ejecución</h3>
        <div class="flex items-center gap-4 text-xs mb-2">
          <span class="flex items-center gap-1.5"><span class="inline-block w-3 h-3 bg-gray-300"></span> Ejecución 2026</span>
          <span class="flex items-center gap-1.5"><span class="inline-block w-3 h-3 rounded-full bg-[#A43F5F]"></span> Dato 2025</span>
        </div>
        <VChart v-if="ejecucionOpt" :option="ejecucionOpt" autoresize class="h-80" />
        <div v-else class="h-80 flex items-center justify-center text-gray-300 font-cuerpo text-sm">Sin datos</div>
      </section>

    </main>

    <!-- ══════════════════════ PÁGINA 2 ══════════════════════ -->
    <main v-else class="max-w-[1400px] mx-auto px-6 py-6 space-y-4">

      <!-- Selectores jerárquicos A / B -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <HierarchicalSelector
          label="REGIONAL A"
          accent="#7C3A5C"
          :nivel="cmpA.tipo"
          :valor="cmpA.valor"
          :options="hierarchyOptions"
          @update="(t, v) => { cmpA.tipo = t; cmpA.valor = v; refreshPage2() }"
        />
        <HierarchicalSelector
          label="REGIONAL B"
          accent="#35678A"
          :nivel="cmpB.tipo"
          :valor="cmpB.valor"
          :options="hierarchyOptions"
          @update="(t, v) => { cmpB.tipo = t; cmpB.valor = v; refreshPage2() }"
        />
      </div>

      <!-- Gráfica comparación divergente -->
      <section class="bg-white rounded border border-gray-200 p-4">
        <VChart v-if="comparisonOpt" :option="comparisonOpt" autoresize class="h-[640px]" />
        <div v-else class="h-[640px] flex items-center justify-center text-gray-300 font-cuerpo text-sm">
          Seleccione ambos grupos para generar la comparación
        </div>
      </section>

      <!-- Resultado de la Comparación -->
      <section>
        <div class="text-center mb-3">
          <h3 class="font-subtitulo font-semibold text-sm text-gray-500 italic">Resultado de la Comparación</h3>
        </div>
        <div v-if="!comparison" class="bg-[#9B5F7E] text-white rounded-lg p-4 text-center font-cuerpo text-sm">
          Seleccione ambos grupos para generar la comparación.
        </div>
        <div v-else class="space-y-3">
          <!-- Banner morado superior con la comparación general -->
          <div class="bg-[#C0A7B8] text-gray-800 rounded p-4 font-cuerpo text-sm leading-relaxed">
            {{ comparison.banner }}
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div class="cmp-box">
              <p class="cmp-lbl">Hallazgo Principal</p>
              <p class="cmp-text">{{ comparison.hallazgo || 'Sin diferencias significativas.' }}</p>
            </div>
            <div class="cmp-box">
              <p class="cmp-lbl">Resumen Desempeño</p>
              <p class="cmp-text">{{ comparison.resumen || '—' }}</p>
            </div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div class="cmp-box">
              <p class="cmp-lbl">Estado Selección Filtro A</p>
              <p class="cmp-text font-semibold">{{ comparison.estado_a }}</p>
              <p class="cmp-text mt-1 text-xs">{{ comparison.estado_a_explicacion }}</p>
            </div>
            <div class="cmp-box">
              <p class="cmp-lbl">Estado Selección Filtro B</p>
              <p class="cmp-text font-semibold">{{ comparison.estado_b }}</p>
              <p class="cmp-text mt-1 text-xs">{{ comparison.estado_b_explicacion }}</p>
            </div>
          </div>
          <div class="cmp-box text-center">
            <p class="cmp-lbl italic">Brecha A vs B</p>
            <p class="cmp-text font-semibold">{{ comparison.brecha }}</p>
          </div>
        </div>
      </section>

    </main>

    <footer class="max-w-[1400px] mx-auto px-6 pb-8 pt-4 text-center text-xs text-gray-400 font-cuerpo border-t border-gray-100 mt-8">
      UBPD · Planes Regionales de Búsqueda
      <span v-if="status?.filename"> · {{ status.filename }}</span>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, defineComponent, h } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, GridComponent, LegendComponent, MarkLineComponent,
} from 'echarts/components'
import { useApi } from '@/composables/useApi'

use([
  CanvasRenderer, BarChart, LineChart,
  TitleComponent, TooltipComponent, GridComponent, LegendComponent, MarkLineComponent,
])

// ── Selector jerárquico inline (GITT / PRB / Regional con valor opcional) ──
const HierarchicalSelector = defineComponent({
  props: {
    label: { type: String, required: true },
    accent: { type: String, default: '#7C3A5C' },
    nivel: { type: String, default: 'gitt' },
    valor: { type: String as () => string | null, default: null },
    options: { type: Object as () => Record<string, string[]>, required: true },
  },
  emits: ['update'],
  setup(props, { emit }) {
    const open = ref(true)
    const expanded = ref<Record<string, boolean>>({
      gitt: props.nivel === 'gitt',
      prb: props.nivel === 'prb',
      regional: props.nivel === 'regional',
    })
    const currentLabel = computed(() => {
      if (props.valor) return `${props.nivel.toUpperCase()} (Nivel) + ${props.nivel.toUpperCase()} | ${props.valor} (Etiqueta)`
      return `${props.nivel.toUpperCase()} (Nivel)`
    })
    const tipos = ['gitt', 'prb', 'regional'] as const
    return () => h('div', { class: 'flex flex-col' }, [
      h('p', { class: 'font-cuerpo font-semibold text-sm text-gray-600 uppercase tracking-wide mb-1.5' }, props.label),
      h('div', {
        class: 'border border-gray-300 rounded bg-white',
        style: { borderTopColor: props.accent, borderTopWidth: '3px' },
      }, [
        h('button', {
          type: 'button',
          class: 'w-full text-left px-3 py-2 text-sm font-cuerpo text-gray-700 flex items-center justify-between',
          onClick: () => (open.value = !open.value),
        }, [
          h('span', { class: 'truncate' }, currentLabel.value),
          h('span', { class: 'text-gray-400 text-xs ml-2' }, open.value ? '▲' : '▼'),
        ]),
        open.value && h('div', { class: 'border-t border-gray-100 max-h-80 overflow-y-auto py-1' },
          tipos.flatMap((t) => [
            h('div', {
              key: `t-${t}`,
              class: 'flex items-center gap-2 px-3 py-1 hover:bg-gray-50 cursor-pointer select-none',
              onClick: () => { expanded.value[t] = !expanded.value[t] },
            }, [
              h('span', { class: 'text-gray-400 text-xs w-3' }, expanded.value[t] ? '⌄' : '›'),
              h('input', {
                type: 'radio', name: `h-${props.label}`,
                checked: props.nivel === t && !props.valor,
                onClick: (e: Event) => { e.stopPropagation(); emit('update', t, null) },
              }),
              h('span', { class: 'font-cuerpo text-sm' }, t.toUpperCase()),
            ]),
            ...(expanded.value[t] ? (props.options[t] ?? []).map((v) => h('div', {
              key: `${t}-${v}`,
              class: 'flex items-center gap-2 pl-10 pr-3 py-1 cursor-pointer hover:bg-gray-50 select-none',
              onClick: () => emit('update', t, v),
            }, [
              h('input', {
                type: 'radio', name: `h-${props.label}`,
                checked: props.nivel === t && props.valor === v,
                onClick: (e: Event) => e.stopPropagation(),
                readonly: true,
              }),
              h('span', { class: 'font-cuerpo text-sm text-gray-700' }, `${t.toUpperCase()} | ${v}`),
            ])) : []),
          ])
        ),
      ]),
    ])
  },
})

// ── Tipos ───────────────────────────────────────────────────
interface Filters {
  regionales: string[]
  gitts: string[]
  lineas: Array<{ cod: number; nombre: string }>
  indicadores: Array<{ cod: number; codigo: string; nombre: string }>
  anios: number[]
}
interface IndicadorCard {
  cod: number; codigo: string; nombre: string;
  dato_2025: number; avance: number; meta: number; pct: number
}
interface MonthlyRow {
  mes: number; mes_nombre: string; valor: number;
  acumulado: number; meta_acumulada: number; dato_2025: number
}
interface ComparisonIndicador {
  codigo:       string
  nombre:       string         // etiqueta corta de la página 2 ("SIF (Confirmados…")
  nombre_largo: string         // nombre original del Excel (para tooltip / resumen)
  avance_a:     number; meta_a: number; pct_a: number   // pct = avance/meta (0..1)
  avance_b:     number; meta_b: number; pct_b: number
  base_2025_a:  number; base_2025_b: number
  // legacy (pct * 100)
  a: number; b: number
}
interface ComparisonResp {
  a: { tipo: string; valor: string | null; label: string; total_avance: number; total_meta: number; pct: number }
  b: { tipo: string; valor: string | null; label: string; total_avance: number; total_meta: number; pct: number }
  indicadores: ComparisonIndicador[]
  banner:                string
  hallazgo:              string
  resumen:               string
  estado_a:              string
  estado_b:              string
  estado_a_explicacion:  string
  estado_b_explicacion:  string
  brecha:                string
}

const { get } = useApi()

// ── Estado ──────────────────────────────────────────────────
const currentPage = ref<1 | 2>(1)
const pages = [
  { id: 1 as const, label: 'Dashboard Principal' },
  { id: 2 as const, label: 'Comparación A vs B' },
]
const loading = ref(true)
const filters = ref<Filters | null>(null)
const prbMap = ref<Array<{ prb: string; regional: string | null; gitt: string | null }>>([])
const status = ref<any>(null)
const indicadoresCards = ref<IndicadorCard[]>([])
const monthly = ref<MonthlyRow[]>([])
const comparison = ref<ComparisonResp | null>(null)
const meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

const active = reactive<{
  anio: number | null; mes: number | null;
  regional: string | null; gitt: string | null; prb: string | null;
  cod_indicador: number | null;
}>({
  anio: null, mes: null, regional: null, gitt: null, prb: null, cod_indicador: null,
})

const cmpA = reactive<{ tipo: string; valor: string | null }>({ tipo: 'gitt', valor: null })
const cmpB = reactive<{ tipo: string; valor: string | null }>({ tipo: 'gitt', valor: null })

const hierarchyOptions = reactive<Record<string, string[]>>({ gitt: [], prb: [], regional: [] })

const gittsForActiveRegion = computed(() => {
  if (!active.regional) return filters.value?.gitts ?? []
  const set = new Set(prbMap.value.filter((p) => p.regional === active.regional).map((p) => p.gitt).filter(Boolean) as string[])
  return Array.from(set).sort()
})
const prbsForActiveRegion = computed(() => {
  let list = prbMap.value
  if (active.regional) list = list.filter((p) => p.regional === active.regional)
  if (active.gitt) list = list.filter((p) => p.gitt === active.gitt)
  return list.map((p) => p.prb).sort()
})
const hasActiveFilters = computed(() =>
  !!(active.regional || active.gitt || active.prb || active.cod_indicador || active.mes),
)

function paramsFor(): Record<string, any> {
  const p: Record<string, any> = {}
  if (active.anio) p.anio = active.anio
  if (active.regional) p.regional = active.regional
  if (active.gitt) p.gitt = active.gitt
  if (active.cod_indicador) p.cod_indicador = active.cod_indicador
  return p
}

async function loadAllFilters() {
  filters.value = await get<Filters>('/bi/filters')
  if (filters.value?.anios?.length === 1 && !active.anio) active.anio = filters.value.anios[0]
  const [gitts, prbs, regionales] = await Promise.all([
    get<string[]>('/bi/hierarchy-values', { params: { tipo: 'gitt' } }),
    get<string[]>('/bi/hierarchy-values', { params: { tipo: 'prb' } }),
    get<string[]>('/bi/hierarchy-values', { params: { tipo: 'regional' } }),
  ])
  hierarchyOptions.gitt = gitts
  hierarchyOptions.prb = prbs
  hierarchyOptions.regional = regionales
  // Cargar mapping prb → regional/gitt para filtros encadenados
  try {
    const resp = await get<any>('/bi/data', { params: { page: 1, size: 200 } })
    const seen = new Set<string>()
    const list: typeof prbMap.value = []
    for (const item of resp.items as any[]) {
      if (item.prb && !seen.has(item.prb)) {
        seen.add(item.prb)
        list.push({ prb: item.prb, regional: item.regional, gitt: item.gitt })
      }
    }
    // Posiblemente haya más PRBs en otras páginas — iterar
    let page = 2
    const total = resp.total as number
    const size = resp.size as number
    while ((page - 1) * size < total && page < 20) {
      const extra = await get<any>('/bi/data', { params: { page, size } })
      for (const item of extra.items as any[]) {
        if (item.prb && !seen.has(item.prb)) {
          seen.add(item.prb)
          list.push({ prb: item.prb, regional: item.regional, gitt: item.gitt })
        }
      }
      page += 1
    }
    prbMap.value = list
  } catch { /* noop */ }
}

async function loadStatus() {
  try { status.value = await get<any>('/admin/bi/status') } catch { status.value = null }
}

async function refreshPage1() {
  const [cards, ev] = await Promise.all([
    get<IndicadorCard[]>('/bi/indicadores-summary', { params: paramsFor() }),
    get<MonthlyRow[]>('/bi/monthly-evolution', { params: paramsFor() }),
  ])
  indicadoresCards.value = cards
  monthly.value = ev
}

async function refreshPage2() {
  if (!cmpA.valor && cmpA.tipo !== 'meta') { comparison.value = null; return }
  if (!cmpB.valor && cmpB.tipo !== 'meta') { comparison.value = null; return }
  comparison.value = await get<ComparisonResp>('/bi/comparison', {
    params: {
      a_tipo: cmpA.tipo, a_valor: cmpA.valor,
      b_tipo: cmpB.tipo, b_valor: cmpB.valor,
      anio: active.anio,
    },
  })
}

function onRegionalChange() {
  active.gitt = null
  active.prb = null
  refreshPage1()
}
function onGittChange() {
  active.prb = null
  refreshPage1()
}
function clearFilters() {
  active.regional = null; active.gitt = null; active.prb = null
  active.cod_indicador = null; active.mes = null
  refreshPage1()
}

// ── Etiquetas y orden canónicos del BI oficial ──────────────────────────
// El backend ya devuelve los indicadores en este orden y con estos nombres
// (ver BI_DISPLAY_ORDER y BI_SHORT_LABELS en bi_dashboard.py). Mantenemos
// SHORT_LABELS aquí solo como respaldo para etiquetas de gráficas/tooltips.
const SHORT_LABELS: Record<string, string> = {
  'L1P-002':     'PDD con solictud de búsqueda',
  'L1A-021':     'SB Mejoradas Pendientes',
  'L1A-020a':    'PDD con muestra biológica asociada',
  'L1P-010':     'No. de lugares de IF caracterizados',
  'L1R-006-007': 'SIF (confirmados y descartados)',
  'L1R-001':     'PEV PRB Asignado',
  'L1R-005':     'Entrega Digna GITT asignada PDD',
  'L1A-022':     'Postulados Búsq Inversa para Verificación',
  'L1R-004':     'Personas con contacto exitosos o reencuentro',
  'L1R-003':     'Informes de lo acaecido entregados',
  'L1P-006':     'Planes de trabajo formulados con aportantes',
  'L1P-008-009': 'Informe de Investigación con Hipótesis',
  'L1R-008':     'Cuerpos Recuperados',
}
function cardTitle(c: IndicadorCard) {
  // El backend ya envía 'nombre' como la etiqueta canónica del BI.
  return c.nombre || SHORT_LABELS[c.codigo] || ''
}

// ── Formatters ─────────────────────────────────────────────
function formatNum(n: number) {
  if (n == null) return '0'
  return new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 }).format(n)
}
function formatMeta(n: number) {
  if (n == null) return '0'
  if (Number.isInteger(n)) return new Intl.NumberFormat('es-CO').format(n) + '.'
  return new Intl.NumberFormat('es-CO', { maximumFractionDigits: 1 }).format(n)
}
function formatPct(n: number) { return (n ?? 0).toFixed(1).replace('.', ',') + ' %' }
function formatDate(iso?: string) {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (x: number) => String(x).padStart(2, '0')
  const hh = d.getHours() % 12 || 12
  return `${pad(d.getDate())}/${pad(d.getMonth()+1)}/${d.getFullYear()} ${pad(hh)}:${pad(d.getMinutes())}:${pad(d.getSeconds())} ${d.getHours() >= 12 ? 'p.m.' : 'a.m.'}`
}
function truncate(s: string | null | undefined, n: number) {
  if (!s) return ''
  return s.length > n ? s.slice(0, n) + '…' : s
}

// ── ECharts: Ejecución bar + 2025 line ─────────────────────
const ejecucionOpt = computed(() => {
  if (!monthly.value?.length) return null
  const dato2025 = monthly.value[0]?.dato_2025 ?? 0
  const monthNamesLong = ['January','February','March','April','May','June','July','August','September','October','November','December']
  return {
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => formatNum(v) },
    grid: { left: 70, right: 30, top: 30, bottom: 50 },
    xAxis: {
      type: 'category',
      data: monthNamesLong,
      axisLabel: { fontSize: 11, color: '#666' },
      name: 'Month', nameLocation: 'middle', nameGap: 30,
    },
    yAxis: {
      type: 'value',
      name: 'Ejecución 2026', nameLocation: 'middle', nameGap: 50,
      axisLabel: { show: false }, splitLine: { show: false },
    },
    series: [
      {
        name: 'Ejecución 2026', type: 'bar',
        data: monthly.value.map((m) => m.valor),
        itemStyle: { color: '#D1D5DB' },
        label: { show: true, position: 'top', formatter: (p: any) => p.value > 0 ? formatNum(p.value) : '', fontSize: 10, color: '#555' },
        barWidth: 24,
      },
      {
        name: 'Dato 2025', type: 'line',
        data: Array(12).fill(dato2025),
        lineStyle: { color: '#A43F5F', width: 2 },
        itemStyle: { color: '#A43F5F' },
        symbol: 'circle', symbolSize: 6,
        label: { show: true, formatter: () => formatNum(dato2025), color: '#A43F5F', fontSize: 10, position: 'top' },
      },
    ],
  }
})

// ── ECharts: Comparación — dos barras espejadas con labels al centro ──
// IMPORTANTE: las barras representan pct = avance/meta (fracción 0..1) tal
// como hace el BI oficial. El tooltip muestra Avance, Meta y Base 2025.
const comparisonOpt = computed(() => {
  if (!comparison.value) return null
  const inds = [...comparison.value.indicadores]
  // Etiqueta del eje Y = etiqueta corta de Página 2 (viene en `nombre`)
  const nombres = inds.map((i) => i.nombre || truncate(i.nombre_largo || i.codigo, 45))
  const valoresA = inds.map((i) => i.pct_a)
  const valoresB = inds.map((i) => i.pct_b)
  const maxAbs = Math.max(0.05, ...inds.map((i) => Math.max(i.pct_a, i.pct_b)))
  return {
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'shadow' },
      formatter: (params: any[]) => {
        const idx = params[0]?.dataIndex ?? 0
        const row = inds[idx]
        if (!row) return ''
        const pa = (row.pct_a * 100).toFixed(1)
        const pb = (row.pct_b * 100).toFixed(1)
        return `<b>${row.nombre_largo || row.codigo}</b><br/>` +
          `<b>Grupo A:</b> ${row.pct_a.toFixed(2)} &nbsp; (Avance ${formatNum(row.avance_a)}, Meta ${formatNum(row.meta_a)}, Base 2025 ${formatNum(row.base_2025_a)})<br/>` +
          `<b>Grupo B:</b> ${row.pct_b.toFixed(2)} &nbsp; (Avance ${formatNum(row.avance_b)}, Meta ${formatNum(row.meta_b)}, Base 2025 ${formatNum(row.base_2025_b)})<br/>` +
          `<i>${pa}% vs ${pb}%</i>`
      },
    },
    legend: {
      top: 5, left: 'center',
      data: [
        { name: 'Grupo A', itemStyle: { color: '#9B5F7E' } },
        { name: 'Grupo B', itemStyle: { color: '#35678A' } },
      ],
      textStyle: { fontSize: 12, color: '#555' },
    },
    // Distribución simétrica:
    // A chart:       3% → 38%   (35% ancho)
    // pasillo label: 38% → 62%  (24% ancho, centro en 50%)
    // B chart:       62% → 97%  (35% ancho)
    grid: [
      { left: '3%', right: '62%', top: 50, bottom: 55, containLabel: false },
      { left: '62%', right: '3%', top: 50, bottom: 55, containLabel: false },
    ],
    xAxis: [
      {
        gridIndex: 0, type: 'value', inverse: true, min: 0, max: maxAbs,
        axisLabel: { formatter: (v: number) => v.toFixed(2), fontSize: 10, color: '#888' },
        splitLine: { lineStyle: { type: 'dashed', color: '#EEE' } },
        axisLine: { show: false }, axisTick: { show: false },
      },
      {
        gridIndex: 1, type: 'value', min: 0, max: maxAbs,
        axisLabel: { formatter: (v: number) => v.toFixed(2), fontSize: 10, color: '#888' },
        splitLine: { lineStyle: { type: 'dashed', color: '#EEE' } },
        axisLine: { show: false }, axisTick: { show: false },
      },
    ],
    yAxis: [
      // Eje del grid izquierdo: labels al lado DERECHO (pasillo central)
      // inverse:true → primer indicador (SIF) ARRIBA, último (Cuerpos Recuperados) ABAJO,
      // igual que el BI oficial.
      {
        gridIndex: 0, type: 'category', data: nombres, position: 'right',
        inverse: true,
        axisLabel: {
          fontSize: 11, color: '#333',
          width: 180, overflow: 'break',
          align: 'center',
          margin: 160,
          lineHeight: 14,
        },
        axisLine: { show: false }, axisTick: { show: false },
      },
      // Eje del grid derecho: sin labels, pero con mismas categorías para alinear
      {
        gridIndex: 1, type: 'category', data: nombres, position: 'left',
        inverse: true,
        axisLabel: { show: false },
        axisLine: { show: false }, axisTick: { show: false },
      },
    ],
    series: [
      {
        name: 'Grupo A', type: 'bar',
        xAxisIndex: 0, yAxisIndex: 0,
        data: valoresA,
        itemStyle: { color: '#9B5F7E', borderRadius: [4, 0, 0, 4] },
        barWidth: 12,
        label: {
          show: true, position: 'left',
          formatter: (p: any) => (p.value > 0 ? p.value.toFixed(2) : ''),
          fontSize: 10, color: '#666',
        },
      },
      {
        name: 'Grupo B', type: 'bar',
        xAxisIndex: 1, yAxisIndex: 1,
        data: valoresB,
        itemStyle: { color: '#35678A', borderRadius: [0, 4, 4, 0] },
        barWidth: 12,
        label: {
          show: true, position: 'right',
          formatter: (p: any) => (p.value > 0 ? p.value.toFixed(2) : ''),
          fontSize: 10, color: '#666',
        },
      },
    ],
  }
})

// ── Lifecycle ──────────────────────────────────────────────
onMounted(async () => {
  loading.value = true
  try {
    await loadStatus()
    await loadAllFilters()
    await refreshPage1()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.filter-box { @apply flex flex-col; }
.filter-label { @apply font-cuerpo text-xs text-gray-500 mb-1; }
.filter-input {
  @apply w-full h-10 font-cuerpo text-sm border border-gray-300 rounded px-3 bg-white
         focus:outline-none focus:border-[#5B2B5E] focus:ring-1 focus:ring-[#5B2B5E]/30;
}

.kpi-card {
  @apply bg-white rounded border border-gray-200 p-3 hover:shadow-md transition-shadow;
}
.kpi-title { @apply font-cuerpo text-xs text-center text-gray-700 min-h-[32px] leading-tight; }
.kpi-num   { @apply font-subtitulo text-lg font-bold text-gray-800 leading-none; }
.kpi-lbl   { @apply font-cuerpo text-[10px] italic text-gray-500 mt-0.5; }

.cmp-box  { @apply bg-white border border-gray-200 rounded p-3; }
.cmp-lbl  { @apply font-cuerpo text-xs text-gray-500 italic text-center mb-1; }
.cmp-text { @apply font-cuerpo text-sm text-gray-700 leading-relaxed; }
</style>
