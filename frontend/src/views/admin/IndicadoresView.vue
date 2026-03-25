<template>
  <div class="p-6 space-y-5">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="font-subtitulo font-bold text-2xl text-ubpd-gris">Gestión de Indicadores</h1>
        <p class="font-cuerpo text-sm text-gray-500 mt-1">Administra los indicadores de Nivel 1 y Nivel 2</p>
      </div>
      <button
        v-if="activeTab === 'nivel1'"
        type="button"
        class="inline-flex items-center gap-2 bg-ubpd-teal text-white font-semibold font-barlow text-sm rounded-xl px-5 py-2.5 hover:bg-teal-700 transition-colors"
        @click="openModal('nivel1')"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 256 256" fill="currentColor"><path d="M228,128a12,12,0,0,1-12,12H140v76a12,12,0,0,1-24,0V140H40a12,12,0,0,1,0-24h76V40a12,12,0,0,1,24,0v76h76A12,12,0,0,1,228,128Z"/></svg>
        Nuevo Indicador N1
      </button>
      <button
        v-else
        type="button"
        class="inline-flex items-center gap-2 bg-ubpd-teal text-white font-semibold font-barlow text-sm rounded-xl px-5 py-2.5 hover:bg-teal-700 transition-colors"
        @click="openModal('nivel2')"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 256 256" fill="currentColor"><path d="M228,128a12,12,0,0,1-12,12H140v76a12,12,0,0,1-24,0V140H40a12,12,0,0,1,0-24h76V40a12,12,0,0,1,24,0v76h76A12,12,0,0,1,228,128Z"/></svg>
        Nuevo Indicador N2
      </button>
    </div>

    <!-- Tabs -->
    <div class="flex gap-1 bg-gray-100 rounded-xl p-1 w-fit">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        type="button"
        class="px-5 py-2 text-sm font-semibold font-barlow rounded-lg transition-all"
        :class="activeTab === tab.key
          ? 'bg-white text-ubpd-gris shadow-sm'
          : 'text-gray-500 hover:text-ubpd-gris'"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Nivel 1 Table -->
    <div v-if="activeTab === 'nivel1'" class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <div v-if="loadingN1" class="divide-y divide-gray-50">
        <div v-for="i in 4" :key="i" class="px-6 py-4 flex items-center gap-4 animate-pulse">
          <div class="flex-1 h-4 rounded bg-gray-200" />
          <div class="w-24 h-4 rounded bg-gray-200" />
          <div class="w-16 h-4 rounded bg-gray-200" />
        </div>
      </div>
      <table v-else-if="nivel1List.length > 0" class="w-full">
        <thead>
          <tr class="bg-gray-50 border-b border-gray-100">
            <th class="px-6 py-3 text-left font-barlow font-semibold text-xs text-gray-500 uppercase tracking-wide">Nombre</th>
            <th class="px-6 py-3 text-left font-barlow font-semibold text-xs text-gray-500 uppercase tracking-wide hidden md:table-cell">Fórmula</th>
            <th class="px-6 py-3 text-center font-barlow font-semibold text-xs text-gray-500 uppercase tracking-wide">N2</th>
            <th class="px-6 py-3 text-center font-barlow font-semibold text-xs text-gray-500 uppercase tracking-wide">Templates</th>
            <th class="px-6 py-3 text-center font-barlow font-semibold text-xs text-gray-500 uppercase tracking-wide">Estado</th>
            <th class="px-6 py-3 text-center font-barlow font-semibold text-xs text-gray-500 uppercase tracking-wide">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="item in nivel1List" :key="item.id" class="hover:bg-gray-50/50 transition">
            <td class="px-6 py-4">
              <div>
                <p class="font-semibold font-barlow text-sm text-ubpd-gris">{{ item.nombre }}</p>
                <p v-if="item.descripcion" class="text-xs text-gray-400 font-barlow mt-0.5 truncate max-w-xs">{{ item.descripcion }}</p>
              </div>
            </td>
            <td class="px-6 py-4 hidden md:table-cell">
              <span class="text-xs bg-gray-100 text-gray-600 font-barlow px-2 py-0.5 rounded-full">{{ item.formula_tipo }}</span>
            </td>
            <td class="px-6 py-4 text-center">
              <span class="font-semibold font-barlow text-sm text-ubpd-gris">{{ item.total_nivel2 }}</span>
            </td>
            <td class="px-6 py-4 text-center">
              <span class="font-semibold font-barlow text-sm text-ubpd-gris">{{ item.total_templates }}</span>
            </td>
            <td class="px-6 py-4 text-center">
              <span
                class="text-xs font-semibold font-barlow px-2.5 py-1 rounded-full"
                :class="item.activo ? 'bg-ubpd-verde/10 text-ubpd-verde' : 'bg-gray-100 text-gray-500'"
              >
                {{ item.activo ? 'Activo' : 'Inactivo' }}
              </span>
            </td>
            <td class="px-6 py-4 text-center">
              <div class="flex items-center justify-center gap-2">
                <button
                  type="button"
                  class="text-xs font-barlow text-ubpd-teal hover:text-teal-700 font-semibold"
                  @click="editNivel1(item)"
                >
                  Editar
                </button>
                <button
                  type="button"
                  class="text-xs font-barlow text-ubpd-naranja hover:text-orange-700 font-semibold"
                  @click="deleteNivel1(item.id)"
                >
                  Desactivar
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="py-16 text-center">
        <p class="text-sm font-barlow text-gray-400">No hay indicadores de Nivel 1 creados.</p>
      </div>
    </div>

    <!-- Nivel 2 Table -->
    <div v-if="activeTab === 'nivel2'" class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <!-- Filter by nivel1 -->
      <div class="px-4 py-3 border-b border-gray-100 flex items-center gap-3 flex-wrap">
        <label class="text-xs font-semibold font-barlow text-gray-500">Filtrar por Nivel 1:</label>
        <select
          v-model="filterNivel1Id"
          class="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-barlow focus:outline-none focus:border-ubpd-verde"
        >
          <option :value="null">Todos</option>
          <option v-for="n1 in nivel1List" :key="n1.id" :value="n1.id">{{ n1.nombre }}</option>
        </select>
      </div>

      <div v-if="loadingN2" class="divide-y divide-gray-50">
        <div v-for="i in 4" :key="i" class="px-6 py-4 flex items-center gap-4 animate-pulse">
          <div class="flex-1 h-4 rounded bg-gray-200" />
          <div class="w-32 h-4 rounded bg-gray-200" />
          <div class="w-16 h-4 rounded bg-gray-200" />
        </div>
      </div>
      <table v-else-if="filteredNivel2List.length > 0" class="w-full">
        <thead>
          <tr class="bg-gray-50 border-b border-gray-100">
            <th class="px-6 py-3 text-left font-barlow font-semibold text-xs text-gray-500 uppercase tracking-wide">Nombre</th>
            <th class="px-6 py-3 text-left font-barlow font-semibold text-xs text-gray-500 uppercase tracking-wide hidden md:table-cell">Nivel 1</th>
            <th class="px-6 py-3 text-center font-barlow font-semibold text-xs text-gray-500 uppercase tracking-wide">Templates</th>
            <th class="px-6 py-3 text-center font-barlow font-semibold text-xs text-gray-500 uppercase tracking-wide">Estado</th>
            <th class="px-6 py-3 text-center font-barlow font-semibold text-xs text-gray-500 uppercase tracking-wide">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="item in filteredNivel2List" :key="item.id" class="hover:bg-gray-50/50 transition">
            <td class="px-6 py-4">
              <div>
                <p class="font-semibold font-barlow text-sm text-ubpd-gris">{{ item.nombre }}</p>
                <p v-if="item.descripcion" class="text-xs text-gray-400 font-barlow mt-0.5 truncate max-w-xs">{{ item.descripcion }}</p>
              </div>
            </td>
            <td class="px-6 py-4 hidden md:table-cell">
              <span class="text-xs bg-blue-50 text-blue-700 font-barlow px-2 py-0.5 rounded-full">{{ item.indicador_nivel1_nombre }}</span>
            </td>
            <td class="px-6 py-4 text-center">
              <span class="font-semibold font-barlow text-sm text-ubpd-gris">{{ item.total_templates }}</span>
            </td>
            <td class="px-6 py-4 text-center">
              <span
                class="text-xs font-semibold font-barlow px-2.5 py-1 rounded-full"
                :class="item.activo ? 'bg-ubpd-verde/10 text-ubpd-verde' : 'bg-gray-100 text-gray-500'"
              >
                {{ item.activo ? 'Activo' : 'Inactivo' }}
              </span>
            </td>
            <td class="px-6 py-4 text-center">
              <div class="flex items-center justify-center gap-2">
                <button type="button" class="text-xs font-barlow text-ubpd-teal hover:text-teal-700 font-semibold" @click="editNivel2(item)">Editar</button>
                <button type="button" class="text-xs font-barlow text-ubpd-naranja hover:text-orange-700 font-semibold" @click="deleteNivel2(item.id)">Desactivar</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="py-16 text-center">
        <p class="text-sm font-barlow text-gray-400">No hay indicadores de Nivel 2 creados.</p>
      </div>
    </div>

    <!-- Modal -->
    <div
      v-if="showModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      role="dialog"
      aria-modal="true"
      @click.self="closeModal"
    >
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-semibold font-montserrat text-ubpd-gris">
            {{ editingItem ? 'Editar' : 'Nuevo' }} Indicador {{ modalType === 'nivel1' ? 'Nivel 1' : 'Nivel 2' }}
          </h2>
          <button type="button" @click="closeModal" class="text-gray-400 hover:text-ubpd-gris">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 256 256" fill="currentColor"><path d="M205.66,194.34a8,8,0,0,1-11.32,11.32L128,139.31,61.66,205.66a8,8,0,0,1-11.32-11.32L116.69,128,50.34,61.66A8,8,0,0,1,61.66,50.34L128,116.69l66.34-66.35a8,8,0,0,1,11.32,11.32L139.31,128Z"/></svg>
          </button>
        </div>

        <div class="space-y-3">
          <div>
            <label class="text-xs font-semibold font-barlow text-gray-500 block mb-1">Nombre *</label>
            <input v-model="form.nombre" type="text" class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-barlow focus:outline-none focus:border-ubpd-verde" />
          </div>
          <div>
            <label class="text-xs font-semibold font-barlow text-gray-500 block mb-1">Descripción</label>
            <textarea v-model="form.descripcion" rows="3" class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-barlow resize-none focus:outline-none focus:border-ubpd-verde" />
          </div>
          <div v-if="modalType === 'nivel1'">
            <label class="text-xs font-semibold font-barlow text-gray-500 block mb-1">Tipo de Fórmula</label>
            <select v-model="form.formula_tipo" class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-barlow focus:outline-none focus:border-ubpd-verde">
              <option value="promedio_simple">Promedio Simple</option>
              <option value="promedio_ponderado">Promedio Ponderado</option>
              <option value="conteo">Conteo</option>
              <option value="personalizado">Personalizado</option>
            </select>
          </div>
          <div v-if="modalType === 'nivel2'">
            <label class="text-xs font-semibold font-barlow text-gray-500 block mb-1">Indicador Nivel 1 *</label>
            <select v-model="form.indicador_nivel1_id" class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-barlow focus:outline-none focus:border-ubpd-verde">
              <option :value="null" disabled>Seleccionar...</option>
              <option v-for="n1 in nivel1List" :key="n1.id" :value="n1.id">{{ n1.nombre }}</option>
            </select>
          </div>
          <div class="flex items-center gap-2">
            <input type="checkbox" id="activo-chk" v-model="form.activo" class="rounded border-gray-300" />
            <label for="activo-chk" class="text-sm font-barlow text-gray-600">Activo</label>
          </div>
        </div>

        <div class="flex gap-3 pt-2">
          <button type="button" @click="closeModal"
            class="flex-1 px-4 py-2 border border-gray-300 text-gray-600 font-semibold font-barlow text-sm rounded-lg hover:bg-gray-50 transition-colors">
            Cancelar
          </button>
          <button type="button" @click="saveItem" :disabled="saving"
            class="flex-1 px-4 py-2 bg-ubpd-teal text-white font-semibold font-barlow text-sm rounded-lg hover:bg-teal-700 transition-colors disabled:opacity-50">
            {{ saving ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useApi } from '@/composables/useApi'
import { useNotificationsStore } from '@/stores/notifications'

interface Nivel1Item {
  id: number
  nombre: string
  descripcion?: string
  formula_tipo: string
  peso: number
  activo: boolean
  total_nivel2: number
  total_templates: number
}

interface Nivel2Item {
  id: number
  nombre: string
  descripcion?: string
  indicador_nivel1_id: number
  indicador_nivel1_nombre?: string
  activo: boolean
  total_templates: number
}

const { get, post, put } = useApi()
const notifications = useNotificationsStore()

const activeTab = ref<'nivel1' | 'nivel2'>('nivel1')
const tabs = [
  { key: 'nivel1', label: 'Indicadores Nivel 1' },
  { key: 'nivel2', label: 'Indicadores Nivel 2' },
]

const nivel1List = ref<Nivel1Item[]>([])
const nivel2List = ref<Nivel2Item[]>([])
const loadingN1 = ref(false)
const loadingN2 = ref(false)
const filterNivel1Id = ref<number | null>(null)

const filteredNivel2List = computed(() => {
  if (!filterNivel1Id.value) return nivel2List.value
  return nivel2List.value.filter((n) => n.indicador_nivel1_id === filterNivel1Id.value)
})

// Modal state
const showModal = ref(false)
const modalType = ref<'nivel1' | 'nivel2'>('nivel1')
const editingItem = ref<Nivel1Item | Nivel2Item | null>(null)
const saving = ref(false)
const form = ref<Record<string, unknown>>({
  nombre: '',
  descripcion: '',
  formula_tipo: 'promedio_simple',
  indicador_nivel1_id: null,
  activo: true,
})

function openModal(type: 'nivel1' | 'nivel2') {
  modalType.value = type
  editingItem.value = null
  form.value = {
    nombre: '',
    descripcion: '',
    formula_tipo: 'promedio_simple',
    indicador_nivel1_id: filterNivel1Id.value,
    activo: true,
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingItem.value = null
}

function editNivel1(item: Nivel1Item) {
  modalType.value = 'nivel1'
  editingItem.value = item
  form.value = { ...item }
  showModal.value = true
}

function editNivel2(item: Nivel2Item) {
  modalType.value = 'nivel2'
  editingItem.value = item
  form.value = { ...item }
  showModal.value = true
}

async function saveItem() {
  if (!form.value.nombre) {
    notifications.warning('Validación', 'El nombre es requerido.')
    return
  }
  saving.value = true
  try {
    if (modalType.value === 'nivel1') {
      if (editingItem.value) {
        await put(`/indicadores/nivel1/${editingItem.value.id}`, form.value)
        notifications.success('Actualizado', 'Indicador Nivel 1 actualizado.')
      } else {
        await post('/indicadores/nivel1', form.value)
        notifications.success('Creado', 'Indicador Nivel 1 creado.')
      }
      await loadNivel1()
    } else {
      if (!form.value.indicador_nivel1_id) {
        notifications.warning('Validación', 'Selecciona un Indicador Nivel 1.')
        return
      }
      if (editingItem.value) {
        await put(`/indicadores/nivel2/${editingItem.value.id}`, form.value)
        notifications.success('Actualizado', 'Indicador Nivel 2 actualizado.')
      } else {
        await post('/indicadores/nivel2', form.value)
        notifications.success('Creado', 'Indicador Nivel 2 creado.')
      }
      await loadNivel2()
    }
    closeModal()
  } catch {
    notifications.error('Error', 'No se pudo guardar el indicador.')
  } finally {
    saving.value = false
  }
}

async function deleteNivel1(id: number) {
  if (!confirm('¿Desactivar este indicador Nivel 1?')) return
  try {
    const { del } = useApi()
    await del(`/indicadores/nivel1/${id}`)
    notifications.success('Desactivado', 'Indicador Nivel 1 desactivado.')
    await loadNivel1()
  } catch {
    notifications.error('Error', 'No se pudo desactivar el indicador.')
  }
}

async function deleteNivel2(id: number) {
  if (!confirm('¿Desactivar este indicador Nivel 2?')) return
  try {
    const { del } = useApi()
    await del(`/indicadores/nivel2/${id}`)
    notifications.success('Desactivado', 'Indicador Nivel 2 desactivado.')
    await loadNivel2()
  } catch {
    notifications.error('Error', 'No se pudo desactivar el indicador.')
  }
}

async function loadNivel1() {
  loadingN1.value = true
  try {
    nivel1List.value = await get<Nivel1Item[]>('/indicadores/nivel1')
  } catch {
    nivel1List.value = []
  } finally {
    loadingN1.value = false
  }
}

async function loadNivel2() {
  loadingN2.value = true
  try {
    nivel2List.value = await get<Nivel2Item[]>('/indicadores/nivel2')
  } catch {
    nivel2List.value = []
  } finally {
    loadingN2.value = false
  }
}

onMounted(async () => {
  await loadNivel1()
  await loadNivel2()
})

watch(activeTab, (tab) => {
  if (tab === 'nivel2' && nivel2List.value.length === 0) loadNivel2()
})
</script>
