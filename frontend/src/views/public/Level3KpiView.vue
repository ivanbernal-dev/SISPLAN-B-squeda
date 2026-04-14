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
      <!-- Barra de avance general -->
      <div class="flex-1">
        <h1 class="text-xl font-bold font-montserrat text-ubpd-gris leading-snug">{{ pageTitle }}</h1>
        <p class="text-sm font-barlow text-gray-500 mt-0.5">
          Formularios aprobados asociados a este indicador
          <span v-if="!loading" class="font-semibold text-ubpd-gris">— {{ total }} registros</span>
        </p>
        <!-- Barra de avance promedio -->
        <div v-if="!loading && promedioVar1 !== null" class="mt-4">
          <div class="flex items-center justify-between mb-1">
            <span class="font-cuerpo text-xs text-gray-500 uppercase tracking-wide">Avance promedio (Variable 1)</span>
            <span class="font-cuerpo text-sm font-bold" :class="colorText(promedioVar1)">
              {{ promedioVar1.toFixed(1) }}%
            </span>
          </div>
          <div class="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-700"
              :class="colorBar(promedioVar1)"
              :style="{ width: `${Math.min(100, promedioVar1)}%` }"
            />
          </div>
          <p class="mt-1 text-xs font-cuerpo" :class="colorText(promedioVar1)">
            {{ scoreLabel(promedioVar1) }}
          </p>
        </div>
      </div>
      <!-- Badge estado -->
      <div v-if="!loading && promedioVar1 !== null"
        class="shrink-0 flex flex-col items-center justify-center
               w-24 h-24 rounded-2xl border-2"
        :class="colorBadgeBg(promedioVar1)">
        <span class="font-montserrat text-2xl font-bold" :class="colorText(promedioVar1)">
          {{ promedioVar1.toFixed(0) }}<span class="text-base">%</span>
        </span>
        <span class="font-cuerpo text-xs mt-0.5" :class="colorText(promedioVar1)">avance</span>
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
      <div class="grid grid-cols-12 gap-4 px-6 py-3 bg-ubpd-gris/5 border-b border-gray-100">
        <div class="col-span-4 font-cuerpo text-xs font-semibold text-gray-500 uppercase tracking-wide">
          Informe / Descripción
        </div>
        <div class="col-span-2 font-cuerpo text-xs font-semibold text-gray-500 uppercase tracking-wide hidden sm:block">
          Dependencia
        </div>
        <div class="col-span-2 font-cuerpo text-xs font-semibold text-gray-500 uppercase tracking-wide hidden md:block">
          Fecha
        </div>
        <div class="col-span-3 font-cuerpo text-xs font-semibold text-gray-500 uppercase tracking-wide">
          Avance (Var. 1)
        </div>
        <div class="col-span-1 font-cuerpo text-xs font-semibold text-gray-500 uppercase tracking-wide text-right">
          &nbsp;
        </div>
      </div>

      <!-- Filas -->
      <div
        v-for="item in items"
        :key="item.id"
        class="grid grid-cols-12 gap-4 px-6 py-4 border-b border-gray-50
               hover:bg-ubpd-teal/5 transition cursor-pointer items-center"
        @click="viewDetail(item.id)"
      >
        <!-- Informe cualitativo -->
        <div class="col-span-4">
          <p class="font-cuerpo text-sm font-medium text-ubpd-gris leading-snug line-clamp-2">
            {{ getInforme(item.datos_dinamicos) }}
          </p>
          <p v-if="item.datos_dinamicos?.fecha_referencia" class="font-cuerpo text-xs text-gray-400 mt-0.5 sm:hidden">
            {{ formatDate(item.datos_dinamicos.fecha_referencia) }}
          </p>
        </div>

        <!-- Dependencia -->
        <div class="col-span-2 hidden sm:block">
          <span class="font-cuerpo text-sm text-gray-600 truncate block">{{ item.dependency || '—' }}</span>
        </div>

        <!-- Fecha -->
        <div class="col-span-2 hidden md:block">
          <span class="font-cuerpo text-sm text-gray-500">
            {{ formatDate(item.datos_dinamicos?.fecha_referencia || item.fecha_usuario || item.fecha_carga) }}
          </span>
        </div>

        <!-- Barra de avance var1 -->
        <div class="col-span-3">
          <template v-if="getVar1(item.datos_dinamicos) !== null">
            <div class="flex items-center gap-2">
              <div class="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full"
                  :class="colorBar(getVar1(item.datos_dinamicos)! * 100)"
                  :style="{ width: `${Math.min(100, getVar1(item.datos_dinamicos)! * 100)}%` }"
                />
              </div>
              <span class="font-cuerpo text-xs font-bold shrink-0 w-10 text-right"
                    :class="colorText(getVar1(item.datos_dinamicos)! * 100)">
                {{ (getVar1(item.datos_dinamicos)! * 100).toFixed(0) }}%
              </span>
            </div>
          </template>
          <span v-else class="font-cuerpo text-xs text-gray-400">—</span>
        </div>

        <!-- Acción -->
        <div class="col-span-1 flex justify-end">
          <button
            class="p-1.5 rounded-lg text-gray-400 hover:text-ubpd-teal hover:bg-ubpd-teal/10 transition"
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

const kpiKey = computed(() => route.params.kpiKey as string)
const subKpiKey = computed(() => route.params.subKpiKey as string)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

const pageTitle = computed(() =>
  kpiLabel.value || (route.query.subLabel as string) || subKpiKey.value
)

// Promedio de var1 (0-1) → % para mostrar en la barra del header
const promedioVar1 = computed<number | null>(() => {
  if (items.value.length === 0) return null
  const vals = items.value
    .map((i) => getVar1(i.datos_dinamicos))
    .filter((v): v is number => v !== null)
  if (vals.length === 0) return null
  return (vals.reduce((a, b) => a + b, 0) / vals.length) * 100
})

// ── Helpers de datos ──────────────────────────────────────────
function getVar1(dd: Record<string, any> | null): number | null {
  if (!dd) return null
  const raw = dd['reporte_cuantitativo_variable_1']
  const n = parseFloat(raw)
  return isNaN(n) ? null : n
}

function getInforme(dd: Record<string, any> | null): string {
  if (!dd) return '—'
  return (
    dd['informe_cualitativo'] ||
    dd['nombre_caso'] ||
    dd['nombre'] ||
    dd['eje_tematico'] ||
    '—'
  )
}

// ── Helpers de color ──────────────────────────────────────────
function colorBar(pct: number) {
  if (pct >= 70) return 'bg-ubpd-verde'
  if (pct >= 40) return 'bg-amber-400'
  return 'bg-orange-500'
}

function colorText(pct: number) {
  if (pct >= 70) return 'text-ubpd-verde'
  if (pct >= 40) return 'text-amber-600'
  return 'text-orange-600'
}

function colorBadgeBg(pct: number) {
  if (pct >= 70) return 'border-ubpd-verde/30 bg-green-50'
  if (pct >= 40) return 'border-amber-300 bg-amber-50'
  return 'border-orange-300 bg-orange-50'
}

function scoreLabel(pct: number) {
  if (pct >= 70) return 'Avanzado'
  if (pct >= 40) return 'En progreso'
  return 'Inicial'
}

function formatDate(s: string | null | undefined): string {
  if (!s) return '—'
  try {
    return new Date(s).toLocaleDateString('es-CO', { day: 'numeric', month: 'short', year: 'numeric' })
  } catch { return s }
}

function viewDetail(formId: string) {
  router.push({
    path: `/estadisticas/${kpiKey.value}/forms/${subKpiKey.value}/${formId}`,
    query: {
      kpiLabel: route.query.kpiLabel,
      subLabel: kpiLabel.value,
      templateNombre: templateNombre.value ?? undefined,
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
    const params: Record<string, string | number> = { page: page.value, size: pageSize }
    if (filterStore.startDate) params.start_date = filterStore.startDate
    if (filterStore.endDate) params.end_date = filterStore.endDate
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
watch(() => [filterStore.startDate, filterStore.endDate], () => { page.value = 1; loadForms() })
</script>
