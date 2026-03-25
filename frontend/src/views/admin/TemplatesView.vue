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
            {{ countCampos(tmpl) }} campos
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

          <!-- Botón Vista Previa -->
          <button
            @click="openPreview(tmpl)"
            class="flex items-center justify-center gap-1.5 text-xs font-cuerpo font-medium
                   border border-gray-300 text-gray-600 rounded-lg px-3 py-2
                   hover:bg-gray-50 hover:border-gray-400 transition"
            title="Vista previa del formulario"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            Previa
          </button>

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

    <!-- Modal Confirmar activar/desactivar -->
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

    <!-- ── Modal Vista Previa del Formulario ─────────────────────────────── -->
    <Teleport to="body">
      <Transition name="modal-fade">
        <div
          v-if="previewTemplate"
          class="fixed inset-0 z-50 flex items-center justify-center p-4"
          @click.self="closePreview"
        >
          <!-- Backdrop -->
          <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="closePreview" />

          <!-- Panel -->
          <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col z-10">
            <!-- Header -->
            <div class="flex items-start justify-between px-6 py-4 border-b border-gray-100">
              <div>
                <div class="flex items-center gap-2 mb-0.5">
                  <span class="inline-flex items-center gap-1 text-xs font-cuerpo font-medium bg-ubpd-teal/10 text-ubpd-teal px-2 py-0.5 rounded-full">
                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    Vista Previa
                  </span>
                  <span
                    class="text-xs font-cuerpo font-medium px-2 py-0.5 rounded-full"
                    :class="previewTemplate.is_active ? 'bg-ubpd-verde/10 text-ubpd-verde' : 'bg-gray-100 text-gray-500'"
                  >
                    {{ previewTemplate.is_active ? 'Activo' : 'Inactivo' }}
                  </span>
                </div>
                <h2 class="font-subtitulo font-bold text-lg text-ubpd-gris leading-snug">
                  {{ previewTemplate.nombre }}
                </h2>
                <p v-if="previewTemplate.indicador_nombre" class="font-cuerpo text-xs text-gray-400 mt-0.5">
                  {{ previewTemplate.indicador_nombre }}
                </p>
              </div>
              <button
                @click="closePreview"
                class="text-gray-400 hover:text-gray-600 transition mt-1"
              >
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <!-- Leyenda -->
            <div class="px-6 py-3 bg-gray-50 border-b border-gray-100 flex flex-wrap gap-4 text-xs font-cuerpo text-gray-500">
              <span class="flex items-center gap-1.5">
                <span class="w-3 h-3 rounded-sm bg-gray-200 border border-gray-300 inline-block" />
                Campo de solo lectura (pre-llenado)
              </span>
              <span class="flex items-center gap-1.5">
                <span class="w-3 h-3 rounded-sm bg-white border border-ubpd-teal inline-block" />
                Campo editable
              </span>
              <span class="flex items-center gap-1.5">
                <span class="text-ubpd-naranja font-bold">*</span>
                Requerido
              </span>
            </div>

            <!-- Formulario preview scrollable -->
            <div class="overflow-y-auto flex-1 px-6 py-5">
              <div v-if="previewFields.length === 0" class="text-center py-12">
                <svg class="w-10 h-10 text-gray-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p class="font-cuerpo text-sm text-gray-400">Este template no tiene campos configurados</p>
              </div>

              <div v-else class="space-y-4">
                <div
                  v-for="field in previewFields"
                  :key="field.name"
                  class="group/field"
                >
                  <label class="block font-cuerpo text-xs font-semibold mb-1.5"
                    :class="field.readonly ? 'text-gray-400' : 'text-ubpd-gris'">
                    {{ field.label }}
                    <span v-if="field.required && !field.readonly" class="text-ubpd-naranja ml-0.5">*</span>
                    <span v-if="field.readonly" class="ml-1.5 text-gray-400 font-normal">(solo lectura)</span>
                  </label>

                  <!-- select -->
                  <select
                    v-if="field.type === 'select'"
                    disabled
                    class="w-full font-cuerpo text-sm rounded-lg px-3 py-2 border appearance-none cursor-not-allowed"
                    :class="field.readonly
                      ? 'bg-gray-100 border-gray-200 text-gray-400'
                      : 'bg-white border-ubpd-teal/40 text-gray-700'"
                  >
                    <option value="" disabled selected>{{ field.default ?? 'Seleccionar…' }}</option>
                    <option v-for="opt in (field.options ?? [])" :key="opt" :value="opt">{{ opt }}</option>
                  </select>

                  <!-- textarea -->
                  <textarea
                    v-else-if="field.type === 'textarea'"
                    v-autoresize
                    disabled
                    :placeholder="field.default ?? `Ingrese ${field.label.toLowerCase()}…`"
                    class="w-full font-cuerpo text-sm rounded-lg px-3 py-2 border resize-none cursor-not-allowed"
                    :class="field.readonly
                      ? 'bg-gray-100 border-gray-200 text-gray-400'
                      : 'bg-white border-ubpd-teal/40 text-gray-700'"
                  />

                  <!-- computed badge -->
                  <div
                    v-else-if="field.type === 'computed'"
                    class="w-full font-cuerpo text-sm rounded-lg px-3 py-2 border bg-blue-50 border-blue-200 text-blue-700 flex items-center gap-2"
                  >
                    <svg class="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 11h.01M12 11h.01M15 11h.01M4 19h16a2 2 0 002-2V7a2 2 0 00-2-2H4a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    <span class="text-xs">Calculado automáticamente</span>
                  </div>

                  <!-- todos los demás tipos: textarea autoresize para mostrar texto completo -->
                  <textarea
                    v-else
                    v-autoresize
                    disabled
                    :placeholder="field.default != null ? String(field.default) : (field.type === 'date' ? 'dd/mm/aaaa' : `Ingrese ${field.label.toLowerCase()}…`)"
                    class="w-full font-cuerpo text-sm rounded-lg px-3 py-2 border cursor-not-allowed leading-snug"
                    :class="field.readonly
                      ? 'bg-gray-100 border-gray-200 text-gray-400'
                      : 'bg-white border-ubpd-teal/40 text-gray-700'"
                  />
                </div>
              </div>
            </div>

            <!-- Footer -->
            <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-between">
              <p class="font-cuerpo text-xs text-gray-400">
                {{ previewFields.filter(f => !f.readonly).length }} editables ·
                {{ previewFields.filter(f => f.readonly).length }} solo lectura ·
                {{ previewFields.length }} total
              </p>
              <div class="flex gap-2">
                <RouterLink
                  :to="`/admin/templates/${previewTemplate.id}`"
                  class="font-cuerpo text-xs font-medium border border-ubpd-teal text-ubpd-teal
                         rounded-lg px-4 py-2 hover:bg-ubpd-teal hover:text-white transition"
                  @click="closePreview"
                >
                  Editar template
                </RouterLink>
                <button
                  @click="closePreview"
                  class="font-cuerpo text-xs font-medium bg-gray-100 text-gray-600
                         rounded-lg px-4 py-2 hover:bg-gray-200 transition"
                >
                  Cerrar
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useNotificationsStore } from '@/stores/notifications'
import ConfirmModal from '@/components/common/ConfirmModal.vue'

interface FieldConfig {
  name: string
  label: string
  type: 'text' | 'number' | 'date' | 'select' | 'textarea' | 'computed'
  readonly: boolean
  required: boolean
  default?: any
  options?: string[]
}

interface Template {
  id: string
  nombre: string
  indicador_nombre?: string
  version?: number
  campos_count?: number
  is_active: boolean
  created_at: string
  configuracion_campos?: {
    fields?: FieldConfig[]
    campos?: FieldConfig[]
  }
}

interface Props {
  showDeactivate?: boolean
}

const props = withDefaults(defineProps<Props>(), { showDeactivate: true })

const { get, patch, del } = useApi()
const notifications = useNotificationsStore()

const loading = ref(true)
const templates = ref<Template[]>([])
const search = ref('')

const showConfirm = ref(false)
const confirmLoading = ref(false)
const confirmData = reactive({ id: '', nombre: '', is_active: true })

// ── Vista Previa ──────────────────────────────────────────────────────────────
const previewTemplate = ref<Template | null>(null)

const previewFields = computed<FieldConfig[]>(() => {
  if (!previewTemplate.value) return []
  const cfg = previewTemplate.value.configuracion_campos ?? {}
  return (cfg.fields ?? cfg.campos ?? []) as FieldConfig[]
})

function openPreview(tmpl: Template) {
  previewTemplate.value = tmpl
}

function closePreview() {
  previewTemplate.value = null
}

function countCampos(tmpl: Template): number {
  const cfg = tmpl.configuracion_campos ?? {}
  return (cfg.fields ?? cfg.campos ?? []).length
}

async function loadTemplates() {
  loading.value = true
  try {
    templates.value = await get<Template[]>('/templates?all=true')
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
    await patch(`/templates/${confirmData.id}`, { activo: !confirmData.is_active })
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

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
.modal-fade-enter-active .relative,
.modal-fade-leave-active .relative {
  transition: transform 0.2s ease;
}
.modal-fade-enter-from .relative,
.modal-fade-leave-to .relative {
  transform: scale(0.96) translateY(8px);
}
</style>
