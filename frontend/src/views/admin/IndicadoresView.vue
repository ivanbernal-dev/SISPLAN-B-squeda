<template>
  <div class="p-6 space-y-5">

    <!-- Header ──────────────────────────────────────────────── -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 flex-wrap">
      <div>
        <h1 class="font-subtitulo font-bold text-2xl text-ubpd-gris">Gestión de Indicadores</h1>
        <p class="font-cuerpo text-sm text-gray-500 mt-1">
          Indicadores KPI conectados al pipeline público
        </p>
      </div>
      <div class="flex items-center gap-2 flex-wrap">
        <!-- Import JSON -->
        <label
          class="inline-flex items-center gap-2 cursor-pointer border border-gray-300 text-gray-600 font-semibold font-barlow text-sm rounded-xl px-4 py-2 hover:bg-gray-50 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 256 256" fill="currentColor">
            <path d="M213.66,82.34l-56-56A8,8,0,0,0,152,24H56A16,16,0,0,0,40,40V216a16,16,0,0,0,16,16H200a16,16,0,0,0,16-16V88A8,8,0,0,0,213.66,82.34ZM160,51.31,188.69,80H160ZM200,216H56V40h88V88a8,8,0,0,0,8,8h48V216Zm-42.34-61.66a8,8,0,0,1,0,11.32l-24,24a8,8,0,0,1-11.32,0l-24-24a8,8,0,0,1,11.32-11.32L120,164.69V120a8,8,0,0,1,16,0v44.69l10.34-10.35A8,8,0,0,1,157.66,154.34Z"/>
          </svg>
          Importar JSON
          <input type="file" accept=".json" class="hidden" @change="importJson" />
        </label>
        <!-- Export JSON -->
        <button
          type="button"
          class="inline-flex items-center gap-2 border border-gray-300 text-gray-600 font-semibold font-barlow text-sm rounded-xl px-4 py-2 hover:bg-gray-50 transition-colors"
          @click="exportJson"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 256 256" fill="currentColor">
            <path d="M213.66,82.34l-56-56A8,8,0,0,0,152,24H56A16,16,0,0,0,40,40V216a16,16,0,0,0,16,16H200a16,16,0,0,0,16-16V88A8,8,0,0,0,213.66,82.34ZM160,51.31,188.69,80H160ZM200,216H56V40h88V88a8,8,0,0,0,8,8h48V216Zm-42.34-77.66a8,8,0,0,1-11.32,11.32L136,139.31V184a8,8,0,0,1-16,0V139.31l-10.34,10.35a8,8,0,0,1-11.32-11.32l24-24a8,8,0,0,1,11.32,0Z"/>
          </svg>
          Exportar JSON
        </button>
        <!-- New N2 -->
        <button
          type="button"
          class="inline-flex items-center gap-2 border border-ubpd-teal text-ubpd-teal font-semibold font-barlow text-sm rounded-xl px-4 py-2 hover:bg-teal-50 transition-colors"
          @click="openModal('nivel2')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 256 256" fill="currentColor"><path d="M228,128a12,12,0,0,1-12,12H140v76a12,12,0,0,1-24,0V140H40a12,12,0,0,1,0-24h76V40a12,12,0,0,1,24,0v76h76A12,12,0,0,1,228,128Z"/></svg>
          Sub-Indicador
        </button>
        <!-- New N1 -->
        <button
          type="button"
          class="inline-flex items-center gap-2 bg-ubpd-teal text-white font-semibold font-barlow text-sm rounded-xl px-4 py-2.5 hover:bg-teal-700 transition-colors"
          @click="openModal('nivel1')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 256 256" fill="currentColor"><path d="M228,128a12,12,0,0,1-12,12H140v76a12,12,0,0,1-24,0V140H40a12,12,0,0,1,0-24h76V40a12,12,0,0,1,24,0v76h76A12,12,0,0,1,228,128Z"/></svg>
          Nuevo Indicador
        </button>
      </div>
    </div>

    <!-- Loading skeleton ──────────────────────────────────────── -->
    <div v-if="loading" class="space-y-3">
      <div v-for="i in 4" :key="i" class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 animate-pulse">
        <div class="flex items-center gap-4">
          <div class="flex-1 h-4 bg-gray-200 rounded" />
          <div class="w-16 h-6 bg-gray-100 rounded-full" />
          <div class="w-20 h-4 bg-gray-100 rounded" />
        </div>
      </div>
    </div>

    <!-- KPI Accordion List ────────────────────────────────────── -->
    <div v-else-if="nivel1Kpis.length > 0" class="space-y-3">
      <div
        v-for="(kpi1, idx) in nivel1Kpis"
        :key="kpi1.kpi_key"
        class="bg-white rounded-2xl border shadow-sm overflow-hidden transition-all"
        :class="kpi1.activo ? 'border-gray-100' : 'border-gray-200 opacity-75'"
      >
        <!-- Nivel 1 Row -->
        <div class="flex items-start gap-3 px-5 py-4 cursor-pointer group" @click="toggleExpand(kpi1.kpi_key)">
          <!-- Expand icon -->
          <button type="button" class="mt-0.5 flex-shrink-0 text-gray-400 hover:text-ubpd-teal transition-colors">
            <svg
              xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 256 256"
              class="transition-transform duration-200"
              :class="expandedKeys.has(kpi1.kpi_key) ? 'rotate-90' : ''"
            >
              <path d="M181.66,133.66l-80,80a8,8,0,0,1-11.32-11.32L164.69,128,90.34,53.66a8,8,0,0,1,11.32-11.32l80,80A8,8,0,0,1,181.66,133.66Z"/>
            </svg>
          </button>

          <!-- Index -->
          <span class="flex-shrink-0 w-6 h-6 rounded-full bg-ubpd-teal/10 text-ubpd-teal text-xs font-bold font-barlow flex items-center justify-center mt-0.5">
            {{ idx + 1 }}
          </span>

          <!-- Labels -->
          <div class="flex-1 min-w-0">
            <p class="font-semibold font-barlow text-sm text-ubpd-gris leading-snug">{{ kpi1.kpi_label }}</p>
            <p v-if="kpi1.descripcion" class="text-xs text-gray-400 font-barlow mt-0.5 line-clamp-1">{{ kpi1.descripcion }}</p>
            <p class="text-xs text-gray-300 font-barlow mt-0.5 font-mono">{{ kpi1.kpi_key }}</p>
          </div>

          <!-- Valor badge -->
          <div class="flex-shrink-0 flex flex-col items-end gap-1.5 ml-2">
            <div
              class="text-sm font-bold font-barlow px-3 py-0.5 rounded-full"
              :class="valorClass(kpi1.valor)"
            >
              {{ kpi1.valor.toFixed(1) }}%
            </div>
            <!-- Active toggle -->
            <button
              type="button"
              class="text-xs font-semibold font-barlow px-2.5 py-0.5 rounded-full border transition-colors"
              :class="kpi1.activo
                ? 'bg-ubpd-verde/10 text-ubpd-verde border-ubpd-verde/20 hover:bg-red-50 hover:text-red-600 hover:border-red-200'
                : 'bg-gray-100 text-gray-500 border-gray-200 hover:bg-green-50 hover:text-green-700 hover:border-green-200'"
              :title="kpi1.activo ? 'Clic para desactivar' : 'Clic para activar'"
              @click.stop="toggleActivo(kpi1)"
            >
              {{ kpi1.activo ? 'Activo' : 'Inactivo' }}
            </button>
          </div>

          <!-- Actions -->
          <div class="flex-shrink-0 flex items-center gap-1 ml-1" @click.stop>
            <button
              type="button"
              title="Editar"
              class="p-1.5 rounded-lg text-gray-400 hover:text-ubpd-teal hover:bg-teal-50 transition-colors"
              @click="editKpi(kpi1)"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 256 256" fill="currentColor">
                <path d="M227.31,73.37,182.63,28.68a16,16,0,0,0-22.63,0L36.69,152A15.86,15.86,0,0,0,32,163.31V208a16,16,0,0,0,16,16H216a8,8,0,0,0,0-16H115.32l112-112A16,16,0,0,0,227.31,73.37ZM92.69,208H48V163.31l88-88L180.69,120ZM192,108.68,147.31,64l24-24L216,84.68Z"/>
              </svg>
            </button>
            <button
              type="button"
              title="Eliminar KPI"
              class="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
              @click="deleteKpi(kpi1.kpi_key, kpi1.kpi_label)"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 256 256" fill="currentColor">
                <path d="M216,48H176V40a24,24,0,0,0-24-24H104A24,24,0,0,0,80,40v8H40a8,8,0,0,0,0,16h8V208a16,16,0,0,0,16,16H192a16,16,0,0,0,16-16V64h8a8,8,0,0,0,0-16ZM96,40a8,8,0,0,1,8-8h48a8,8,0,0,1,8,8v8H96Zm96,168H64V64H192ZM112,104v64a8,8,0,0,1-16,0V104a8,8,0,0,1,16,0Zm48,0v64a8,8,0,0,1-16,0V104a8,8,0,0,1,16,0Z"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Nivel 2 sub-indicators (collapsible) -->
        <div v-if="expandedKeys.has(kpi1.kpi_key)" class="border-t border-gray-50">
          <!-- Sub-indicator rows -->
          <div
            v-for="(kpi2, sidx) in getSubKpis(kpi1.kpi_key)"
            :key="kpi2.kpi_key"
            class="flex items-start gap-3 px-5 py-3 border-b border-gray-50 last:border-0 group hover:bg-gray-50/50 transition-colors"
            :class="kpi2.activo ? '' : 'opacity-60'"
          >
            <div class="w-4 ml-5 flex-shrink-0" />
            <span class="flex-shrink-0 w-5 h-5 rounded-full bg-gray-100 text-gray-500 text-xs font-bold font-barlow flex items-center justify-center mt-0.5">
              {{ sidx + 1 }}
            </span>
            <div class="flex-1 min-w-0">
              <p class="font-medium font-barlow text-sm text-ubpd-gris">{{ kpi2.kpi_label }}</p>
              <p v-if="kpi2.descripcion" class="text-xs text-gray-400 font-barlow mt-0.5 line-clamp-1">{{ kpi2.descripcion }}</p>
              <p class="text-xs text-gray-300 font-barlow mt-0.5 font-mono">{{ kpi2.kpi_key }}</p>
            </div>
            <!-- Valor -->
            <div class="flex-shrink-0 flex flex-col items-end gap-1.5 ml-2">
              <div
                class="text-xs font-bold font-barlow px-2.5 py-0.5 rounded-full"
                :class="valorClass(kpi2.valor)"
              >
                {{ kpi2.valor.toFixed(1) }}%
              </div>
              <button
                type="button"
                class="text-xs font-semibold font-barlow px-2 py-0.5 rounded-full border transition-colors"
                :class="kpi2.activo
                  ? 'bg-ubpd-verde/10 text-ubpd-verde border-ubpd-verde/20 hover:bg-red-50 hover:text-red-600 hover:border-red-200'
                  : 'bg-gray-100 text-gray-500 border-gray-200 hover:bg-green-50 hover:text-green-700 hover:border-green-200'"
                @click="toggleActivo(kpi2)"
              >
                {{ kpi2.activo ? 'Activo' : 'Inactivo' }}
              </button>
            </div>
            <!-- Actions -->
            <div class="flex-shrink-0 flex items-center gap-1">
              <button
                type="button"
                title="Editar"
                class="p-1.5 rounded-lg text-gray-400 hover:text-ubpd-teal hover:bg-teal-50 transition-colors"
                @click="editKpi(kpi2)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 256 256" fill="currentColor">
                  <path d="M227.31,73.37,182.63,28.68a16,16,0,0,0-22.63,0L36.69,152A15.86,15.86,0,0,0,32,163.31V208a16,16,0,0,0,16,16H216a8,8,0,0,0,0-16H115.32l112-112A16,16,0,0,0,227.31,73.37ZM92.69,208H48V163.31l88-88L180.69,120ZM192,108.68,147.31,64l24-24L216,84.68Z"/>
                </svg>
              </button>
              <button
                type="button"
                title="Eliminar sub-indicador"
                class="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                @click="deleteKpi(kpi2.kpi_key, kpi2.kpi_label)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 256 256" fill="currentColor">
                  <path d="M216,48H176V40a24,24,0,0,0-24-24H104A24,24,0,0,0,80,40v8H40a8,8,0,0,0,0,16h8V208a16,16,0,0,0,16,16H192a16,16,0,0,0,16-16V64h8a8,8,0,0,0,0-16ZM96,40a8,8,0,0,1,8-8h48a8,8,0,0,1,8,8v8H96Zm96,168H64V64H192ZM112,104v64a8,8,0,0,1-16,0V104a8,8,0,0,1,16,0Zm48,0v64a8,8,0,0,1-16,0V104a8,8,0,0,1,16,0Z"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- Add sub-indicator shortcut -->
          <div class="px-5 py-2.5 flex items-center gap-2 bg-gray-50/50">
            <div class="w-4 ml-5 flex-shrink-0" />
            <button
              type="button"
              class="inline-flex items-center gap-1.5 text-xs font-semibold font-barlow text-ubpd-teal hover:text-teal-700 transition-colors"
              @click="openSubModal(kpi1.kpi_key)"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 256 256" fill="currentColor"><path d="M228,128a12,12,0,0,1-12,12H140v76a12,12,0,0,1-24,0V140H40a12,12,0,0,1,0-24h76V40a12,12,0,0,1,24,0v76h76A12,12,0,0,1,228,128Z"/></svg>
              Agregar sub-indicador
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="flex flex-col items-center justify-center py-20 text-gray-400">
      <svg class="w-14 h-14 mb-4 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
      <p class="font-barlow text-base">No hay indicadores disponibles.</p>
      <p class="font-barlow text-sm mt-1 text-gray-300">
        Ejecuta el pipeline o crea un indicador manualmente.
      </p>
    </div>

    <!-- ── Modal ────────────────────────────────────────────────── -->
    <div
      v-if="showModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      role="dialog"
      aria-modal="true"
      @click.self="closeModal"
    >
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6 space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-semibold font-montserrat text-ubpd-gris">
            {{ editingKpi ? 'Editar' : 'Nuevo' }}
            {{ modalType === 'nivel1' ? 'Indicador (Nivel 1)' : 'Sub-Indicador (Nivel 2)' }}
          </h2>
          <button type="button" @click="closeModal" class="text-gray-400 hover:text-ubpd-gris">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 256 256" fill="currentColor"><path d="M205.66,194.34a8,8,0,0,1-11.32,11.32L128,139.31,61.66,205.66a8,8,0,0,1-11.32-11.32L116.69,128,50.34,61.66A8,8,0,0,1,61.66,50.34L128,116.69l66.34-66.35a8,8,0,0,1,11.32,11.32L139.31,128Z"/></svg>
          </button>
        </div>

        <div class="space-y-3">
          <!-- Key (only new) -->
          <div v-if="!editingKpi">
            <label class="text-xs font-semibold font-barlow text-gray-500 block mb-1">
              Clave única (kpi_key) *
              <span class="font-normal text-gray-400">Ej: kpi_linea1_sub1</span>
            </label>
            <input
              v-model="form.kpi_key"
              type="text"
              placeholder="kpi_linea1_sub1"
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono focus:outline-none focus:border-ubpd-verde"
            />
          </div>
          <!-- Label -->
          <div>
            <label class="text-xs font-semibold font-barlow text-gray-500 block mb-1">Nombre del indicador *</label>
            <input
              v-model="form.kpi_label"
              type="text"
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-barlow focus:outline-none focus:border-ubpd-verde"
            />
          </div>
          <!-- Descripcion -->
          <div>
            <label class="text-xs font-semibold font-barlow text-gray-500 block mb-1">Subtítulo / descripción</label>
            <textarea
              v-model="form.descripcion"
              rows="2"
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-barlow resize-none focus:outline-none focus:border-ubpd-verde"
            />
          </div>
          <!-- Nivel 1 parent (only nivel 2) -->
          <div v-if="modalType === 'nivel2'">
            <label class="text-xs font-semibold font-barlow text-gray-500 block mb-1">Indicador Nivel 1 padre *</label>
            <select
              v-model="form.nivel1_key"
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-barlow focus:outline-none focus:border-ubpd-verde"
            >
              <option value="" disabled>Seleccionar...</option>
              <option v-for="n1 in nivel1Kpis" :key="n1.kpi_key" :value="n1.kpi_key">{{ n1.kpi_label }}</option>
            </select>
          </div>
          <!-- Activo -->
          <div class="flex items-center gap-2">
            <input type="checkbox" id="activo-chk" v-model="form.activo" class="rounded border-gray-300" />
            <label for="activo-chk" class="text-sm font-barlow text-gray-600">Visible en la vista pública</label>
          </div>
          <!-- Read-only valor (editing) -->
          <div v-if="editingKpi" class="bg-gray-50 rounded-xl px-4 py-3">
            <p class="text-xs font-semibold font-barlow text-gray-400 uppercase tracking-wide mb-1">Valor actual (calculado por pipeline)</p>
            <p class="text-2xl font-bold font-barlow" :class="valorClass(editingKpi.valor)">{{ editingKpi.valor.toFixed(1) }}%</p>
          </div>
        </div>

        <div class="flex gap-3 pt-2">
          <button type="button" @click="closeModal"
            class="flex-1 px-4 py-2 border border-gray-300 text-gray-600 font-semibold font-barlow text-sm rounded-lg hover:bg-gray-50 transition-colors">
            Cancelar
          </button>
          <button type="button" @click="saveKpi" :disabled="saving"
            class="flex-1 px-4 py-2 bg-ubpd-teal text-white font-semibold font-barlow text-sm rounded-lg hover:bg-teal-700 transition-colors disabled:opacity-50">
            {{ saving ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useApi } from '@/composables/useApi'
import { useNotificationsStore } from '@/stores/notifications'

interface KpiItem {
  id: string
  kpi_key: string
  kpi_label: string
  nivel: number
  nivel1_key: string | null
  descripcion: string | null
  template_id: string | null
  valor: number
  activo: boolean
  updated_at: string | null
}

const { get, post, patch, del } = useApi()
const notifications = useNotificationsStore()

const loading = ref(false)
const allKpis = ref<KpiItem[]>([])
const expandedKeys = ref<Set<string>>(new Set())

const nivel1Kpis = computed(() => allKpis.value.filter((k) => k.nivel === 1))

function getSubKpis(nivel1_key: string): KpiItem[] {
  return allKpis.value.filter((k) => k.nivel === 2 && k.nivel1_key === nivel1_key)
}

function valorClass(v: number) {
  if (v >= 70) return 'bg-green-50 text-green-700'
  if (v >= 40) return 'bg-amber-50 text-amber-700'
  if (v > 0) return 'bg-orange-50 text-orange-700'
  return 'bg-gray-100 text-gray-500'
}

function toggleExpand(key: string) {
  if (expandedKeys.value.has(key)) {
    expandedKeys.value.delete(key)
  } else {
    expandedKeys.value.add(key)
  }
}

// ── Modal ──────────────────────────────────────────────────────────────────

const showModal = ref(false)
const modalType = ref<'nivel1' | 'nivel2'>('nivel1')
const editingKpi = ref<KpiItem | null>(null)
const saving = ref(false)
const form = ref<Record<string, any>>({
  kpi_key: '',
  kpi_label: '',
  descripcion: '',
  nivel1_key: '',
  activo: true,
})

function openModal(type: 'nivel1' | 'nivel2') {
  modalType.value = type
  editingKpi.value = null
  form.value = {
    kpi_key: '',
    kpi_label: '',
    descripcion: '',
    nivel1_key: '',
    activo: true,
  }
  showModal.value = true
}

function openSubModal(nivel1Key: string) {
  modalType.value = 'nivel2'
  editingKpi.value = null
  form.value = {
    kpi_key: '',
    kpi_label: '',
    descripcion: '',
    nivel1_key: nivel1Key,
    activo: true,
  }
  showModal.value = true
}

function editKpi(kpi: KpiItem) {
  modalType.value = kpi.nivel === 1 ? 'nivel1' : 'nivel2'
  editingKpi.value = kpi
  form.value = {
    kpi_key: kpi.kpi_key,
    kpi_label: kpi.kpi_label,
    descripcion: kpi.descripcion || '',
    nivel1_key: kpi.nivel1_key || '',
    activo: kpi.activo,
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingKpi.value = null
}

async function saveKpi() {
  if (!form.value.kpi_label?.trim()) {
    notifications.warning('Validación', 'El nombre del indicador es requerido.')
    return
  }
  if (!editingKpi.value && !form.value.kpi_key?.trim()) {
    notifications.warning('Validación', 'La clave única (kpi_key) es requerida.')
    return
  }
  if (modalType.value === 'nivel2' && !form.value.nivel1_key) {
    notifications.warning('Validación', 'Selecciona el Indicador Nivel 1 padre.')
    return
  }

  saving.value = true
  try {
    if (editingKpi.value) {
      // Update
      await patch(`/indicadores/kpis/${editingKpi.value.kpi_key}`, {
        kpi_label: form.value.kpi_label,
        descripcion: form.value.descripcion || null,
        activo: form.value.activo,
      })
      notifications.success('Actualizado', 'Indicador actualizado correctamente.')
    } else {
      // Create
      await post('/indicadores/kpis', {
        kpi_key: form.value.kpi_key,
        kpi_label: form.value.kpi_label,
        nivel: modalType.value === 'nivel1' ? 1 : 2,
        nivel1_key: modalType.value === 'nivel2' ? form.value.nivel1_key : null,
        descripcion: form.value.descripcion || null,
        activo: form.value.activo,
      })
      notifications.success('Creado', 'Indicador creado correctamente.')
      if (modalType.value === 'nivel2' && form.value.nivel1_key) {
        expandedKeys.value.add(form.value.nivel1_key)
      }
    }
    closeModal()
    await loadKpis()
  } catch (err: any) {
    const detail = err?.response?.data?.detail || 'No se pudo guardar el indicador.'
    notifications.error('Error', detail)
  } finally {
    saving.value = false
  }
}

async function toggleActivo(kpi: KpiItem) {
  const newState = !kpi.activo
  try {
    await patch(`/indicadores/kpis/${kpi.kpi_key}`, { activo: newState })
    kpi.activo = newState
    notifications.success(
      newState ? 'Activado' : 'Desactivado',
      `"${kpi.kpi_label}" ahora está ${newState ? 'visible en la vista pública' : 'oculto en la vista pública'}.`,
    )
  } catch {
    notifications.error('Error', 'No se pudo cambiar el estado del indicador.')
  }
}

async function deleteKpi(kpiKey: string, label: string) {
  if (!confirm(`¿Eliminar permanentemente "${label}"?\n\nEsta acción no se puede deshacer.`)) return
  try {
    await del(`/indicadores/kpis/${kpiKey}`)
    notifications.success('Eliminado', `"${label}" eliminado correctamente.`)
    await loadKpis()
  } catch {
    notifications.error('Error', 'No se pudo eliminar el indicador.')
  }
}

// ── JSON Export / Import ───────────────────────────────────────────────────

async function exportJson() {
  try {
    const data = await get<any>('/indicadores/kpis/export')
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
    a.href = url
    a.download = `kpis_config_${ts}.json`
    a.click()
    URL.revokeObjectURL(url)
    notifications.success('Exportado', 'Configuración de indicadores descargada.')
  } catch {
    notifications.error('Error', 'No se pudo exportar la configuración.')
  }
}

async function importJson(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  try {
    const text = await file.text()
    const payload = JSON.parse(text)
    const result = await post<any>('/indicadores/kpis/import', payload)
    notifications.success(
      'Importado',
      result.mensaje || 'Configuración importada correctamente.',
    )
    await loadKpis()
  } catch (err: any) {
    notifications.error('Error', 'No se pudo importar el JSON. Verifica el formato.')
  } finally {
    input.value = ''
  }
}

// ── Data loading ───────────────────────────────────────────────────────────

async function loadKpis() {
  loading.value = true
  try {
    allKpis.value = await get<KpiItem[]>('/indicadores/kpis')
    // Auto-expand all nivel 1 on first load
    if (expandedKeys.value.size === 0) {
      allKpis.value
        .filter((k) => k.nivel === 1)
        .forEach((k) => expandedKeys.value.add(k.kpi_key))
    }
  } catch {
    allKpis.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadKpis)
</script>
