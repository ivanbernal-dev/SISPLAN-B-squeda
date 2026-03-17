<template>
  <div class="p-6 space-y-5">
    <!-- Encabezado -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="font-subtitulo font-bold text-2xl text-ubpd-gris">Dependencias</h1>
        <p class="font-cuerpo text-sm text-gray-500 mt-1">Gestión de dependencias e instancias institucionales</p>
      </div>
      <button
        @click="openCreateModal"
        class="inline-flex items-center gap-2 bg-ubpd-teal text-white font-cuerpo font-semibold text-sm
               rounded-xl px-5 py-2.5 hover:bg-[#346d7a] transition"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nueva Dependencia
      </button>
    </div>

    <!-- Buscador -->
    <div class="bg-white rounded-2xl border border-gray-100 shadow-sm px-5 py-4">
      <div class="max-w-xs">
        <label class="block font-cuerpo text-xs font-medium text-gray-500 mb-1">Buscar</label>
        <input
          v-model="search"
          type="text"
          placeholder="Nombre o código..."
          class="w-full font-cuerpo text-sm border border-gray-300 rounded-lg px-3 py-2
                 focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20 transition"
        />
      </div>
    </div>

    <!-- Tabla -->
    <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <!-- Loading skeleton -->
      <div v-if="loading" class="divide-y divide-gray-50">
        <div v-for="i in 4" :key="i" class="px-6 py-4 flex items-center gap-4 animate-pulse">
          <div class="w-10 h-10 rounded-xl bg-gray-200" />
          <div class="flex-1 space-y-2">
            <div class="w-48 h-4 rounded bg-gray-200" />
            <div class="w-24 h-3 rounded bg-gray-200" />
          </div>
          <div class="w-20 h-6 rounded-full bg-gray-200" />
          <div class="flex gap-2">
            <div class="w-8 h-8 rounded-lg bg-gray-200" />
            <div class="w-8 h-8 rounded-lg bg-gray-200" />
          </div>
        </div>
      </div>

      <div v-else-if="filteredDeps.length > 0">
        <table class="w-full">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide">Dependencia</th>
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide">Código</th>
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide hidden md:table-cell">Descripción</th>
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide">Estado</th>
              <th class="px-6 py-3 text-right font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="dep in paginatedDeps" :key="dep.id" class="hover:bg-gray-50/50 transition">
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-xl bg-ubpd-lila/10 flex items-center justify-center flex-shrink-0">
                    <svg class="w-5 h-5 text-ubpd-lila" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                  </div>
                  <p class="font-cuerpo font-medium text-sm text-ubpd-gris">{{ dep.nombre }}</p>
                </div>
              </td>
              <td class="px-6 py-4">
                <span class="font-mono text-sm text-gray-600 bg-gray-100 px-2 py-0.5 rounded">{{ dep.codigo }}</span>
              </td>
              <td class="px-6 py-4 hidden md:table-cell">
                <p class="font-cuerpo text-sm text-gray-500 truncate max-w-[240px]">{{ dep.descripcion || '—' }}</p>
              </td>
              <td class="px-6 py-4">
                <span
                  class="inline-flex items-center gap-1.5 font-cuerpo text-xs font-medium px-2.5 py-1 rounded-full"
                  :class="dep.is_active ? 'bg-ubpd-verde/10 text-ubpd-verde' : 'bg-gray-100 text-gray-500'"
                >
                  <span class="w-1.5 h-1.5 rounded-full" :class="dep.is_active ? 'bg-ubpd-verde' : 'bg-gray-400'" />
                  {{ dep.is_active ? 'Activa' : 'Inactiva' }}
                </span>
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center justify-end gap-1.5">
                  <button
                    @click="openEditModal(dep)"
                    class="p-2 rounded-lg text-gray-400 hover:text-ubpd-teal hover:bg-ubpd-teal/10 transition"
                    title="Editar"
                  >
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    @click="confirmToggle(dep)"
                    class="p-2 rounded-lg transition"
                    :class="dep.is_active ? 'text-gray-400 hover:text-ubpd-naranja hover:bg-orange-50' : 'text-gray-400 hover:text-ubpd-verde hover:bg-ubpd-verde/10'"
                    :title="dep.is_active ? 'Desactivar' : 'Activar'"
                  >
                    <svg v-if="dep.is_active" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                    </svg>
                    <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Paginación -->
        <div v-if="totalPages > 1" class="px-6 py-4 border-t border-gray-100 flex items-center justify-between">
          <p class="font-cuerpo text-sm text-gray-500">
            Mostrando {{ (page - 1) * pageSize + 1 }}–{{ Math.min(page * pageSize, filteredDeps.length) }}
            de {{ filteredDeps.length }}
          </p>
          <div class="flex gap-1">
            <button @click="page--" :disabled="page === 1"
              class="p-2 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <button v-for="p in totalPages" :key="p" @click="page = p"
              class="w-8 h-8 rounded-lg font-cuerpo text-sm transition"
              :class="p === page ? 'bg-ubpd-teal text-white' : 'border border-gray-200 text-gray-500 hover:bg-gray-50'">
              {{ p }}
            </button>
            <button @click="page++" :disabled="page === totalPages"
              class="p-2 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Vacío -->
      <div v-else class="py-16 text-center">
        <svg class="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <p class="font-cuerpo text-sm text-gray-500">No se encontraron dependencias</p>
        <button @click="openCreateModal" class="mt-3 font-cuerpo text-sm text-ubpd-teal hover:underline">
          Registrar la primera dependencia
        </button>
      </div>
    </div>

    <!-- Modales -->
    <DependencyFormModal
      v-model="showDepModal"
      :edit-data="selectedDep"
      @saved="handleDepSaved"
    />

    <ConfirmModal
      v-model="showConfirm"
      :title="confirmData.is_active ? 'Desactivar dependencia' : 'Activar dependencia'"
      :message="`¿Desea ${confirmData.is_active ? 'desactivar' : 'activar'} la dependencia &quot;${confirmData.nombre}&quot;?`"
      :confirm-label="confirmData.is_active ? 'Desactivar' : 'Activar'"
      :variant="confirmData.is_active ? 'warning' : 'confirm'"
      :loading="confirmLoading"
      @confirm="handleToggleDep"
      @cancel="showConfirm = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useApi } from '@/composables/useApi'
import { useNotificationsStore } from '@/stores/notifications'
import DependencyFormModal from '@/components/forms/DependencyFormModal.vue'
import ConfirmModal from '@/components/common/ConfirmModal.vue'

interface Dependency {
  id: string
  nombre: string
  codigo: string
  descripcion: string
  is_active: boolean
}

const { get, patch } = useApi()
const notifications = useNotificationsStore()

const loading = ref(true)
const deps = ref<Dependency[]>([])
const search = ref('')
const page = ref(1)
const pageSize = 15

const showDepModal = ref(false)
const selectedDep = ref<Dependency | null>(null)
const showConfirm = ref(false)
const confirmLoading = ref(false)
const confirmData = reactive({ id: '', nombre: '', is_active: true })

async function loadDeps() {
  loading.value = true
  try {
    deps.value = await get<Dependency[]>('/admin/dependencies')
  } catch {
    notifications.error('No se pudo cargar la lista de dependencias')
  } finally {
    loading.value = false
  }
}

onMounted(loadDeps)
watch(search, () => { page.value = 1 })

const filteredDeps = computed(() =>
  !search.value
    ? deps.value
    : deps.value.filter((d) =>
        d.nombre.toLowerCase().includes(search.value.toLowerCase()) ||
        d.codigo.toLowerCase().includes(search.value.toLowerCase())
      )
)

const totalPages = computed(() => Math.max(1, Math.ceil(filteredDeps.value.length / pageSize)))

const paginatedDeps = computed(() => {
  const start = (page.value - 1) * pageSize
  return filteredDeps.value.slice(start, start + pageSize)
})

function openCreateModal() {
  selectedDep.value = null
  showDepModal.value = true
}

function openEditModal(dep: Dependency) {
  selectedDep.value = dep
  showDepModal.value = true
}

function confirmToggle(dep: Dependency) {
  confirmData.id = dep.id
  confirmData.nombre = dep.nombre
  confirmData.is_active = dep.is_active
  showConfirm.value = true
}

async function handleToggleDep() {
  confirmLoading.value = true
  try {
    await patch(`/admin/dependencies/${confirmData.id}`, { is_active: !confirmData.is_active })
    const idx = deps.value.findIndex((d) => d.id === confirmData.id)
    if (idx !== -1) deps.value[idx].is_active = !confirmData.is_active
    notifications.success(confirmData.is_active ? 'Dependencia desactivada' : 'Dependencia activada')
    showConfirm.value = false
  } catch {
    notifications.error('No se pudo actualizar el estado')
  } finally {
    confirmLoading.value = false
  }
}

function handleDepSaved(saved: Dependency) {
  const idx = deps.value.findIndex((d) => d.id === saved.id)
  if (idx !== -1) deps.value[idx] = saved
  else deps.value.unshift(saved)
}
</script>
