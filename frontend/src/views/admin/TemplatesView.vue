<template>
  <div class="p-6 space-y-5">
    <!-- Encabezado -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="font-subtitulo font-bold text-2xl text-ubpd-gris">Templates de Formularios</h1>
        <p class="font-cuerpo text-sm text-gray-500 mt-1">Plantillas para el registro de información</p>
      </div>
      <RouterLink
        to="/admin/templates/new"
        class="inline-flex items-center gap-2 bg-ubpd-teal text-white font-cuerpo font-semibold text-sm
               rounded-xl px-5 py-2.5 hover:bg-[#346d7a] transition"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nuevo Template
      </RouterLink>
    </div>

    <!-- Buscador -->
    <div class="bg-white rounded-2xl border border-gray-100 shadow-sm px-5 py-4">
      <div class="max-w-xs">
        <input
          v-model="search"
          type="text"
          placeholder="Buscar por nombre o indicador..."
          class="w-full font-cuerpo text-sm border border-gray-300 rounded-lg px-3 py-2
                 focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20 transition"
        />
      </div>
    </div>

    <!-- Grid de cards -->
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <div v-for="i in 6" :key="i" class="bg-white rounded-2xl border border-gray-100 p-5 animate-pulse">
        <div class="w-full h-5 rounded bg-gray-200 mb-3" />
        <div class="w-3/4 h-4 rounded bg-gray-200 mb-4" />
        <div class="flex gap-2">
          <div class="w-16 h-5 rounded-full bg-gray-200" />
          <div class="w-20 h-5 rounded-full bg-gray-200" />
        </div>
      </div>
    </div>

    <div v-else-if="filteredTemplates.length > 0" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <div
        v-for="tmpl in filteredTemplates"
        :key="tmpl.id"
        class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5
               hover:shadow-md hover:border-ubpd-teal/30 transition group"
      >
        <div class="flex items-start justify-between gap-2 mb-3">
          <div class="flex-1">
            <p class="font-subtitulo font-semibold text-sm text-ubpd-gris group-hover:text-ubpd-teal transition leading-snug">
              {{ tmpl.nombre }}
            </p>
            <p class="font-cuerpo text-xs text-gray-400 mt-1">{{ tmpl.indicador_nombre ?? 'Sin indicador asignado' }}</p>
          </div>
          <span
            class="flex-shrink-0 text-xs font-cuerpo font-medium px-2 py-0.5 rounded-full"
            :class="tmpl.is_active ? 'bg-ubpd-verde/10 text-ubpd-verde' : 'bg-gray-100 text-gray-500'"
          >
            {{ tmpl.is_active ? 'Activo' : 'Inactivo' }}
          </span>
        </div>

        <div class="flex flex-wrap gap-2 mb-4">
          <span class="font-cuerpo text-xs bg-ubpd-teal/10 text-ubpd-teal px-2 py-0.5 rounded-full">
            v{{ tmpl.version ?? 1 }}
          </span>
          <span class="font-cuerpo text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
            {{ tmpl.campos_count ?? 0 }} campos
          </span>
          <span class="font-cuerpo text-xs text-gray-400">
            {{ formatDate(tmpl.created_at) }}
          </span>
        </div>

        <div class="flex items-center gap-2">
          <RouterLink
            :to="`/admin/templates/${tmpl.id}`"
            class="flex-1 flex items-center justify-center gap-1.5 text-xs font-cuerpo font-medium
                   border border-ubpd-teal text-ubpd-teal rounded-lg px-3 py-2
                   hover:bg-ubpd-teal hover:text-white transition"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Editar
          </RouterLink>
          <button
            v-if="showDeactivate"
            @click="confirmToggle(tmpl)"
            class="flex items-center justify-center gap-1.5 text-xs font-cuerpo font-medium
                   border rounded-lg px-3 py-2 transition"
            :class="tmpl.is_active
              ? 'border-ubpd-naranja/50 text-ubpd-naranja hover:bg-orange-50'
              : 'border-ubpd-verde/50 text-ubpd-verde hover:bg-ubpd-verde/10'"
            :title="tmpl.is_active ? 'Desactivar' : 'Activar'"
          >
            {{ tmpl.is_active ? 'Desactivar' : 'Activar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Vacío -->
    <div v-else class="bg-white rounded-2xl border border-gray-100 py-16 text-center">
      <svg class="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6z" />
      </svg>
      <p class="font-cuerpo text-sm text-gray-500">No se encontraron templates</p>
      <RouterLink to="/admin/templates/new" class="mt-3 inline-block font-cuerpo text-sm text-ubpd-teal hover:underline">
        Crear el primer template
      </RouterLink>
    </div>

    <ConfirmModal
      v-model="showConfirm"
      :title="confirmData.is_active ? 'Desactivar template' : 'Activar template'"
      :message="`¿Desea ${confirmData.is_active ? 'desactivar' : 'activar'} el template &quot;${confirmData.nombre}&quot;?`"
      :confirm-label="confirmData.is_active ? 'Desactivar' : 'Activar'"
      :variant="confirmData.is_active ? 'warning' : 'confirm'"
      :loading="confirmLoading"
      @confirm="handleToggle"
      @cancel="showConfirm = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useNotificationsStore } from '@/stores/notifications'
import ConfirmModal from '@/components/common/ConfirmModal.vue'

interface Template {
  id: string
  nombre: string
  indicador_nombre?: string
  version?: number
  campos_count?: number
  is_active: boolean
  created_at: string
}

interface Props {
  showDeactivate?: boolean
}

const props = withDefaults(defineProps<Props>(), { showDeactivate: true })

const { get, del } = useApi()
const notifications = useNotificationsStore()

const loading = ref(true)
const templates = ref<Template[]>([])
const search = ref('')

const showConfirm = ref(false)
const confirmLoading = ref(false)
const confirmData = reactive({ id: '', nombre: '', is_active: true })

async function loadTemplates() {
  loading.value = true
  try {
    templates.value = await get<Template[]>('/templates')
  } catch {
    notifications.error('No se pudo cargar los templates')
  } finally {
    loading.value = false
  }
}

onMounted(loadTemplates)
watch(search, () => {})

const filteredTemplates = computed(() =>
  !search.value
    ? templates.value
    : templates.value.filter(
        (t) =>
          t.nombre.toLowerCase().includes(search.value.toLowerCase()) ||
          (t.indicador_nombre ?? '').toLowerCase().includes(search.value.toLowerCase())
      )
)

function formatDate(d: string): string {
  return new Date(d).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}

function confirmToggle(tmpl: Template) {
  confirmData.id = tmpl.id
  confirmData.nombre = tmpl.nombre
  confirmData.is_active = tmpl.is_active
  showConfirm.value = true
}

async function handleToggle() {
  confirmLoading.value = true
  try {
    await del(`/templates/${confirmData.id}`)
    const idx = templates.value.findIndex((t) => t.id === confirmData.id)
    if (idx !== -1) templates.value[idx].is_active = !confirmData.is_active
    notifications.success(confirmData.is_active ? 'Template desactivado' : 'Template activado')
    showConfirm.value = false
  } catch {
    notifications.error('No se pudo actualizar el template')
  } finally {
    confirmLoading.value = false
  }
}
</script>
