<template>
  <div class="space-y-5">
    <header class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.2em] text-ubpd-teal">Visor institucional</p>
        <h1 class="mt-1 text-3xl font-bold text-gray-900">Indicadores Comité Directivo</h1>
        <p class="mt-1 text-sm text-gray-500">
          Consulta ejecutiva de información aprobada. Este módulo no modifica formularios ni resultados.
        </p>
      </div>
      <div class="flex gap-2">
        <button class="secondary-button" :disabled="cargando" @click="cargar">
          {{ cargando ? 'Actualizando…' : 'Actualizar' }}
        </button>
        <button class="primary-button" :disabled="!indicadoresFiltrados.length" @click="exportarExcel">
          Exportar Excel
        </button>
      </div>
    </header>

    <section class="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      <article v-for="card in tarjetas" :key="card.label" class="summary-card">
        <p class="text-xs font-medium uppercase tracking-wide text-gray-500">{{ card.label }}</p>
        <p class="mt-2 text-3xl font-bold text-gray-900">{{ card.value }}</p>
        <p class="mt-1 text-xs" :class="card.color">{{ card.note }}</p>
      </article>
    </section>

    <section class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      <div class="grid gap-0 border-b border-gray-200 lg:grid-cols-[1.4fr_1fr_0.65fr_0.9fr]">
        <label class="filter-cell">
          <span>Línea estratégica</span>
          <select v-model="lineaSeleccionada">
            <option value="Todas">Todas las líneas</option>
            <option v-for="linea in lineas" :key="linea" :value="linea">{{ linea }}</option>
          </select>
        </label>
        <label class="filter-cell lg:border-l">
          <span>Dependencia</span>
          <select v-model="dependenciaSeleccionada">
            <option value="Todas">Todas las dependencias</option>
            <option v-for="dependencia in dependenciasDisponibles" :key="dependencia" :value="dependencia">
              {{ dependencia }}
            </option>
          </select>
        </label>
        <label class="filter-cell lg:border-l">
          <span>Estado del indicador</span>
          <select v-model="estadoSeleccionado">
            <option value="Todos">Todos</option>
            <option v-for="estado in estados" :key="estado" :value="estado">{{ estado }}</option>
          </select>
        </label>
        <label class="filter-cell lg:border-l">
          <span>Buscar</span>
          <input v-model.trim="busqueda" placeholder="Código o nombre…" />
        </label>
      </div>

      <div v-if="error" class="m-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        {{ error }}
      </div>

      <div v-if="cargando" class="flex min-h-80 items-center justify-center text-sm text-gray-500">
        Cargando indicadores aprobados…
      </div>

      <template v-else>
        <div class="flex items-center justify-between gap-4 px-4 py-3">
          <div>
            <h2 class="font-semibold text-gray-900">Tabla de indicadores</h2>
            <p class="text-xs text-gray-500">{{ indicadoresFiltrados.length }} indicadores en esta selección</p>
          </div>
          <span class="rounded-full bg-teal-50 px-3 py-1 text-xs font-semibold text-ubpd-teal">Vigencia 2026</span>
        </div>

        <div class="table-scroll">
          <table class="indicator-table">
            <thead>
              <tr>
                <th class="sticky-col w-32">N.º indicador</th>
                <th class="sticky-name min-w-64">Nombre del indicador</th>
                <th class="min-w-52">Dependencia</th>
                <th class="min-w-48">Fórmula</th>
                <th class="min-w-28">Unidad</th>
                <th class="min-w-24">Meta anual</th>
                <th class="min-w-24">Estado</th>
                <th class="min-w-24">Visual</th>
                <th v-for="periodo in periodos" :key="periodo.key" class="min-w-24 text-center">
                  {{ periodo.label }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="indicador in paginaActual" :key="indicador.uid">
                <td class="sticky-col font-semibold text-gray-700">{{ indicador.codigo }}</td>
                <td class="sticky-name">
                  <button class="indicator-link" @click="abrirDetalle(indicador)">{{ indicador.nombre }}</button>
                </td>
                <td>{{ indicador.dependencia || '—' }}</td>
                <td>{{ indicador.formula || '—' }}</td>
                <td>{{ indicador.unidad || '—' }}</td>
                <td class="font-semibold">{{ indicador.metaAnual || '—' }}</td>
                <td>
                  <span class="status-pill" :class="claseEstado(indicador.estado)">{{ indicador.estado }}</span>
                </td>
                <td class="text-center">
                  <div class="progress-ring" :style="{ '--progress': `${avanceActual(indicador)}%` }">
                    <span>{{ Math.round(avanceActual(indicador)) }}%</span>
                  </div>
                </td>
                <td v-for="periodo in periodos" :key="`${indicador.uid}-${periodo.key}`" class="text-center">
                  <button
                    class="month-button"
                    :class="tieneReporte(indicador.meses[periodo.key]) ? 'month-button-active' : 'month-button-empty'"
                    :disabled="!tieneReporte(indicador.meses[periodo.key])"
                    @click="abrirMes(indicador, periodo.key)"
                  >
                    {{ indicador.meses[periodo.key]?.display || '—' }}
                  </button>
                  <span
                    v-if="indicador.meses[periodo.key]?.observacionOap"
                    class="mt-1 block text-base text-red-500"
                    title="Existe comentario OAP"
                  >⚑</span>
                  <span v-else class="mt-1 block text-base text-gray-400" title="Sin comentario OAP">⚐</span>
                </td>
              </tr>
              <tr v-if="!paginaActual.length">
                <td :colspan="8 + periodos.length" class="py-14 text-center text-gray-500">
                  No hay indicadores para esta combinación de filtros.
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <footer class="flex flex-col gap-3 border-t border-gray-200 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <p class="text-xs text-gray-500">
            Mostrando {{ rangoInicio }}–{{ rangoFin }} de {{ indicadoresFiltrados.length }}
          </p>
          <div class="flex items-center gap-2">
            <select v-model.number="porPagina" class="page-size">
              <option :value="5">5 por página</option>
              <option :value="10">10 por página</option>
              <option :value="20">20 por página</option>
              <option :value="50">50 por página</option>
            </select>
            <button class="page-button" :disabled="pagina <= 1" @click="pagina--">‹</button>
            <span class="min-w-20 text-center text-xs text-gray-600">{{ pagina }} / {{ totalPaginas }}</span>
            <button class="page-button" :disabled="pagina >= totalPaginas" @click="pagina++">›</button>
          </div>
        </footer>
      </template>
    </section>

    <Teleport to="body">
      <div v-if="indicadorDetalle" class="modal-backdrop z-50" @click.self="cerrarDetalle">
        <section class="detail-modal">
          <header class="modal-header">
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-ubpd-teal">Detalle del indicador</p>
              <h2 class="mt-1 text-xl font-bold text-gray-900">
                {{ indicadorDetalle.codigo }}. {{ indicadorDetalle.nombre }}
              </h2>
            </div>
            <button class="close-button" aria-label="Cerrar" @click="cerrarDetalle">×</button>
          </header>

          <div class="grid gap-3 border-b border-gray-200 px-6 py-4 md:grid-cols-4">
            <InfoBox label="Fórmula" :value="indicadorDetalle.formula" />
            <InfoBox label="Unidad" :value="indicadorDetalle.unidad" />
            <InfoBox label="Meta anual" :value="indicadorDetalle.metaAnual" />
            <InfoBox label="Dependencia" :value="indicadorDetalle.dependencia" />
          </div>

          <div class="modal-body space-y-5">
            <div class="grid gap-4 lg:grid-cols-2">
              <TextBox label="Objetivo" :value="indicadorDetalle.objetivo" />
              <TextBox label="Definición" :value="indicadorDetalle.definicion" />
              <TextBox label="Responsables" :value="indicadorDetalle.responsables" />
              <TextBox label="Fuente" :value="indicadorDetalle.fuente" />
            </div>

            <div>
              <h3 class="mb-2 font-semibold text-gray-900">Resultados por periodo</h3>
              <div class="overflow-x-auto rounded-lg border border-gray-200">
                <table class="detail-table">
                  <thead>
                    <tr>
                      <th>Periodo</th>
                      <th>Resultado</th>
                      <th>Análisis cualitativo</th>
                      <th>Logros y dificultades</th>
                      <th>Observaciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="periodo in periodos" :key="periodo.key">
                      <td class="font-semibold">{{ periodo.label }}</td>
                      <td>
                        <button
                          v-if="tieneReporte(indicadorDetalle.meses[periodo.key])"
                          class="indicator-link"
                          @click="abrirMes(indicadorDetalle, periodo.key)"
                        >
                          {{ indicadorDetalle.meses[periodo.key].display }}
                        </button>
                        <span v-else>Sin reporte</span>
                      </td>
                      <td>{{ indicadorDetalle.meses[periodo.key]?.analisis || '—' }}</td>
                      <td>{{ indicadorDetalle.meses[periodo.key]?.logros || '—' }}</td>
                      <td>{{ indicadorDetalle.meses[periodo.key]?.observaciones || '—' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>
      </div>

      <div v-if="reporteSeleccionado && indicadorMes" class="modal-backdrop z-[60]" @click.self="cerrarMes">
        <section class="month-modal">
          <header class="modal-header">
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-ubpd-teal">Detalle del periodo</p>
              <h2 class="mt-1 text-xl font-bold text-gray-900">{{ reporteSeleccionado.label }}</h2>
              <p class="mt-1 text-sm text-gray-500">{{ indicadorMes.codigo }} · {{ indicadorMes.nombre }}</p>
            </div>
            <button class="close-button" aria-label="Cerrar" @click="cerrarMes">×</button>
          </header>

          <div class="modal-body space-y-5">
            <div class="grid gap-3 sm:grid-cols-2">
              <InfoBox label="Resultado del periodo" :value="valor(reporteSeleccionado.resultado)" emphasized />
              <InfoBox label="Resultado acumulado reportado" :value="valor(reporteSeleccionado.resultado_acumulado)" />
            </div>

            <section>
              <h3 class="mb-2 font-semibold text-gray-900">Comportamiento de las variables</h3>
              <div v-if="reporteSeleccionado.variables?.length" class="overflow-hidden rounded-lg border border-gray-200">
                <table class="detail-table">
                  <thead><tr><th>Variable</th><th>Dato del periodo</th><th>Acumulado al periodo</th></tr></thead>
                  <tbody>
                    <tr v-for="variable in reporteSeleccionado.variables" :key="variable.numero">
                      <td><strong>V{{ variable.numero }}.</strong> {{ variable.nombre }}</td>
                      <td class="font-semibold">{{ valor(variable.valor_mes) }}</td>
                      <td class="font-semibold">
                        {{ valor(variable.valor_acumulado) }}
                        <span v-if="variable.acumulado_calculado" class="block text-[11px] font-normal text-amber-600">
                          Suma calculada de periodos aprobados
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p v-else class="rounded-lg bg-gray-50 p-4 text-sm text-gray-500">
                Este reporte no contiene valores desagregados por variable.
              </p>
            </section>

            <div class="grid gap-4 lg:grid-cols-3">
              <TextBox label="Análisis cualitativo" :value="reporteSeleccionado.analisis" />
              <TextBox label="Logros y dificultades" :value="reporteSeleccionado.logros" />
              <TextBox label="Observaciones" :value="reporteSeleccionado.observaciones" />
            </div>

            <section v-if="reporteSeleccionado.observacionOap" class="rounded-lg border border-red-200 bg-red-50 p-4">
              <div class="flex items-start justify-between gap-4">
                <div>
                  <h3 class="font-semibold text-red-700">Comentario de la OAP</h3>
                  <p class="mt-2 whitespace-pre-line text-sm text-red-800">{{ reporteSeleccionado.observacionOap }}</p>
                </div>
                <span class="rounded-full bg-white px-3 py-1 text-xs font-semibold text-red-700">
                  {{ reporteSeleccionado.estadoOap || 'Pendiente' }}
                </span>
              </div>
              <p v-if="reporteSeleccionado.validado_por" class="mt-3 text-xs text-red-600">
                Validado por {{ reporteSeleccionado.validado_por }}
              </p>
            </section>
          </div>
        </section>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, ref, watch } from 'vue'
import { obtenerIndicadoresComite } from './api'
import type { IndicadorComite, Periodo, ReporteMes, RespuestaComite } from './types'

const InfoBox = defineComponent({
  props: { label: String, value: [String, Number], emphasized: Boolean },
  setup: (props) => () => h('div', { class: ['info-box', props.emphasized ? 'ring-1 ring-ubpd-teal' : ''] }, [
    h('p', { class: 'text-[11px] font-medium uppercase tracking-wide text-gray-500' }, props.label),
    h('p', { class: ['mt-1', props.emphasized ? 'text-xl font-bold text-ubpd-teal' : 'text-sm font-semibold text-gray-800'] }, props.value || '—'),
  ]),
})

const TextBox = defineComponent({
  props: { label: String, value: String },
  setup: (props) => () => h('section', { class: 'rounded-lg border border-gray-200 bg-gray-50 p-4' }, [
    h('h3', { class: 'text-sm font-semibold text-gray-900' }, props.label),
    h('p', { class: 'mt-2 whitespace-pre-line text-sm leading-6 text-gray-600' }, props.value || 'Sin información'),
  ]),
})

const respuesta = ref<RespuestaComite | null>(null)
const cargando = ref(false)
const error = ref('')
const lineaSeleccionada = ref('Todas')
const dependenciaSeleccionada = ref('Todas')
const estadoSeleccionado = ref('Todos')
const busqueda = ref('')
const pagina = ref(1)
const porPagina = ref(10)
const indicadorDetalle = ref<IndicadorComite | null>(null)
const indicadorMes = ref<IndicadorComite | null>(null)
const reporteSeleccionado = ref<ReporteMes | null>(null)

const periodos = computed<Periodo[]>(() => respuesta.value?.periodos || [])
const lineas = computed(() => respuesta.value?.filtros.lineas || [])
const estados = computed(() => respuesta.value?.filtros.estados || [])
const indicadores = computed(() => respuesta.value?.items || [])

const dependenciasDisponibles = computed(() => {
  const source = lineaSeleccionada.value === 'Todas'
    ? indicadores.value
    : indicadores.value.filter((item) => item.linea === lineaSeleccionada.value)
  return [...new Set(source.map((item) => item.dependencia).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'es'))
})

function normalizar(value: string): string {
  return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es')
}

const indicadoresFiltrados = computed(() => {
  const needle = normalizar(busqueda.value)
  return indicadores.value.filter((item) => {
    if (lineaSeleccionada.value !== 'Todas' && item.linea !== lineaSeleccionada.value) return false
    if (dependenciaSeleccionada.value !== 'Todas' && item.dependencia !== dependenciaSeleccionada.value) return false
    if (estadoSeleccionado.value !== 'Todos' && item.estado !== estadoSeleccionado.value) return false
    return !needle || normalizar(`${item.codigo} ${item.nombre} ${item.dependencia}`).includes(needle)
  })
})

const totalPaginas = computed(() => Math.max(1, Math.ceil(indicadoresFiltrados.value.length / porPagina.value)))
const paginaActual = computed(() => {
  const start = (pagina.value - 1) * porPagina.value
  return indicadoresFiltrados.value.slice(start, start + porPagina.value)
})
const rangoInicio = computed(() => indicadoresFiltrados.value.length ? (pagina.value - 1) * porPagina.value + 1 : 0)
const rangoFin = computed(() => Math.min(pagina.value * porPagina.value, indicadoresFiltrados.value.length))

const resumenFiltrado = computed(() => {
  const items = indicadoresFiltrados.value
  const avances = items.map(avanceActual).filter((value) => value > 0)
  return {
    total: items.length,
    activos: items.filter((item) => normalizar(item.estado) === 'activo').length,
    inactivos: items.filter((item) => normalizar(item.estado) === 'inactivo').length,
    avance: avances.length ? Math.round(avances.reduce((sum, value) => sum + value, 0) / avances.length) : 0,
    oap: items.reduce((count, item) => count + Object.values(item.meses).filter((month) => month.observacionOap).length, 0),
  }
})

const tarjetas = computed(() => [
  { label: 'Indicadores', value: resumenFiltrado.value.total, note: 'Selección actual', color: 'text-blue-600' },
  { label: 'Activos', value: resumenFiltrado.value.activos, note: 'En seguimiento', color: 'text-green-600' },
  { label: 'Inactivos', value: resumenFiltrado.value.inactivos, note: 'Histórico', color: 'text-gray-500' },
  { label: 'Avance promedio', value: `${resumenFiltrado.value.avance}%`, note: 'Último periodo reportado', color: 'text-ubpd-teal' },
  { label: 'Comentarios OAP', value: resumenFiltrado.value.oap, note: 'Periodos con observación', color: 'text-red-600' },
])

watch([lineaSeleccionada, estadoSeleccionado, busqueda, porPagina], () => { pagina.value = 1 })
watch(lineaSeleccionada, () => {
  if (!dependenciasDisponibles.value.includes(dependenciaSeleccionada.value)) dependenciaSeleccionada.value = 'Todas'
})
watch(dependenciaSeleccionada, () => { pagina.value = 1 })
watch(totalPaginas, () => { if (pagina.value > totalPaginas.value) pagina.value = totalPaginas.value })

async function cargar() {
  cargando.value = true
  error.value = ''
  try {
    respuesta.value = await obtenerIndicadoresComite(2026)
  } catch (cause) {
    console.error(cause)
    error.value = 'No fue posible cargar el visor. Verifica que el backend esté actualizado y vuelve a intentar.'
  } finally {
    cargando.value = false
  }
}

function tieneReporte(report?: ReporteMes): boolean {
  return Boolean(report && (
    report.resultado !== null && report.resultado !== ''
    || report.analisis || report.logros || report.observaciones || report.variables?.length
  ))
}

function avanceActual(indicator: IndicadorComite): number {
  for (const period of [...periodos.value].reverse()) {
    const value = indicator.meses[period.key]?.avance
    if (typeof value === 'number' && Number.isFinite(value)) return Math.max(0, Math.min(100, value))
  }
  return 0
}

function claseEstado(status: string): string {
  const value = normalizar(status)
  if (value === 'activo') return 'bg-green-100 text-green-700'
  if (value === 'inactivo') return 'bg-gray-100 text-gray-600'
  return 'bg-blue-100 text-blue-700'
}

function abrirDetalle(indicator: IndicadorComite) { indicadorDetalle.value = indicator }
function cerrarDetalle() { indicadorDetalle.value = null }
function abrirMes(indicator: IndicadorComite, periodKey: string) {
  indicadorMes.value = indicator
  reporteSeleccionado.value = indicator.meses[periodKey]
}
function cerrarMes() {
  indicadorMes.value = null
  reporteSeleccionado.value = null
}

function valor(value: string | number | null | undefined): string {
  return value === null || value === undefined || value === '' ? 'No reportado' : String(value)
}

async function exportarExcel() {
  const XLSX = await import('xlsx')
  const rows = indicadoresFiltrados.value.map((indicator) => {
    const row: Record<string, string | number> = {
      Código: indicator.codigo,
      Indicador: indicator.nombre,
      Línea: indicator.linea,
      Dependencia: indicator.dependencia,
      Fórmula: indicator.formula,
      Unidad: indicator.unidad,
      'Meta anual': indicator.metaAnual,
      Estado: indicator.estado,
    }
    periodos.value.forEach((period) => { row[period.label] = indicator.meses[period.key]?.display || 'Sin reporte' })
    return row
  })
  const workbook = XLSX.utils.book_new()
  const worksheet = XLSX.utils.json_to_sheet(rows)
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Indicadores 2026')
  XLSX.writeFile(workbook, 'Indicadores_Comite_Directivo_2026.xlsx')
}

onMounted(cargar)
</script>

<style scoped>
.primary-button, .secondary-button {
  @apply rounded-lg px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50;
}
.primary-button { @apply bg-ubpd-teal text-white hover:brightness-95; }
.secondary-button { @apply border border-gray-300 bg-white text-gray-700 hover:bg-gray-50; }
.summary-card { @apply rounded-xl border border-gray-200 bg-white p-4 shadow-sm; }
.filter-cell { @apply flex min-w-0 flex-col gap-1 border-gray-200 px-4 py-3; }
.filter-cell span { @apply text-[11px] font-semibold uppercase tracking-wide text-gray-500; }
.filter-cell select, .filter-cell input { @apply w-full border-0 bg-transparent p-0 text-sm font-semibold text-gray-800 focus:ring-0; }
.table-scroll { @apply max-h-[62vh] overflow-auto border-t border-gray-200; }
.indicator-table { @apply min-w-full border-separate border-spacing-0 text-xs text-gray-600; }
.indicator-table th { @apply sticky top-0 z-20 border-b border-r border-gray-200 bg-gray-50 px-3 py-3 text-left font-semibold text-gray-700; }
.indicator-table td { @apply border-b border-r border-gray-200 bg-white px-3 py-3 align-middle; }
.indicator-table tbody tr:hover td { @apply bg-teal-50/40; }
.sticky-col { @apply sticky left-0 z-10; }
.sticky-name { @apply sticky left-32 z-10; }
thead .sticky-col, thead .sticky-name { @apply z-30; }
.indicator-link { @apply text-left font-semibold text-ubpd-teal underline decoration-dotted underline-offset-4 hover:text-teal-700; }
.status-pill { @apply inline-flex rounded-full px-2.5 py-1 text-[11px] font-semibold; }
.progress-ring {
  @apply relative mx-auto grid h-12 w-12 place-items-center rounded-full text-[10px] font-bold text-gray-700;
  background: conic-gradient(#0e9f6e var(--progress), #e5e7eb 0);
}
.progress-ring::after { content: ''; @apply absolute inset-[5px] rounded-full bg-white; }
.progress-ring span { @apply relative z-10; }
.month-button { @apply min-w-14 rounded-md px-2 py-1 text-[11px] font-semibold; }
.month-button-active { @apply bg-teal-50 text-ubpd-teal underline decoration-dotted underline-offset-2 hover:bg-teal-100; }
.month-button-empty { @apply cursor-default bg-transparent text-gray-400; }
.page-size { @apply rounded-lg border-gray-300 py-1.5 pl-3 pr-8 text-xs focus:border-ubpd-teal focus:ring-ubpd-teal; }
.page-button { @apply grid h-8 w-8 place-items-center rounded-lg border border-gray-300 bg-white text-lg text-gray-700 disabled:opacity-40; }
.modal-backdrop { @apply fixed inset-0 flex items-center justify-center bg-slate-900/50 p-3 backdrop-blur-[1px]; }
.detail-modal { @apply flex h-[92vh] w-[96vw] max-w-[1700px] flex-col overflow-hidden rounded-2xl bg-white shadow-2xl; }
.month-modal { @apply flex max-h-[90vh] w-[94vw] max-w-6xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl; }
.modal-header { @apply flex items-start justify-between gap-4 border-b border-gray-200 px-6 py-4; }
.modal-body { @apply overflow-y-auto p-6; }
.close-button { @apply grid h-9 w-9 shrink-0 place-items-center rounded-full text-2xl text-gray-500 hover:bg-gray-100 hover:text-gray-900; }
.info-box { @apply rounded-lg border border-gray-200 bg-white p-3; }
.detail-table { @apply min-w-full text-left text-xs text-gray-600; }
.detail-table th { @apply border-b border-gray-200 bg-gray-50 px-3 py-3 font-semibold text-gray-700; }
.detail-table td { @apply max-w-md border-b border-gray-200 px-3 py-3 align-top leading-5; }
</style>
