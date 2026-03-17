<template>
  <div class="p-6 space-y-5 h-full flex flex-col">
    <!-- Encabezado -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 flex-shrink-0">
      <div>
        <div class="flex items-center gap-2 text-sm font-cuerpo text-gray-400 mb-1">
          <RouterLink to="/admin/templates" class="hover:text-ubpd-teal transition">Templates</RouterLink>
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
          <span class="text-ubpd-gris">{{ isEditing ? 'Editar Template' : 'Nuevo Template' }}</span>
        </div>
        <h1 class="font-subtitulo font-bold text-2xl text-ubpd-gris">
          {{ isEditing ? 'Editar Template' : 'Nuevo Template' }}
        </h1>
      </div>
      <button
        @click="handleSave"
        :disabled="saving || !form.nombre"
        class="inline-flex items-center gap-2 bg-ubpd-teal text-white font-cuerpo font-semibold text-sm
               rounded-xl px-5 py-2.5 hover:bg-[#346d7a] transition disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <svg v-if="saving" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
        {{ saving ? 'Guardando...' : (isEditing ? 'Actualizar Template' : 'Guardar Template') }}
      </button>
    </div>

    <!-- Metadatos del template -->
    <div class="bg-white rounded-2xl border border-gray-100 shadow-sm px-5 py-4 flex-shrink-0">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <!-- Nombre -->
        <div>
          <label class="block font-cuerpo font-medium text-sm text-ubpd-gris mb-1.5">
            Nombre del template <span class="text-ubpd-naranja">*</span>
          </label>
          <input
            v-model="form.nombre"
            type="text"
            placeholder="Ej. Formulario L1-P1-IHE"
            class="w-full font-cuerpo text-sm border border-gray-300 rounded-lg px-4 py-2.5
                   focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20 transition"
          />
        </div>

        <!-- Indicador -->
        <div>
          <label class="block font-cuerpo font-medium text-sm text-ubpd-gris mb-1.5">
            Indicador de Nivel 1
          </label>
          <select
            v-model="form.indicador_nivel1_id"
            :disabled="loadingIndicators"
            class="w-full font-cuerpo text-sm border border-gray-300 rounded-lg px-4 py-2.5
                   focus:outline-none focus:border-ubpd-verde transition disabled:bg-gray-50"
          >
            <option :value="null">{{ loadingIndicators ? 'Cargando...' : 'Seleccione un indicador' }}</option>
            <option v-for="ind in indicators" :key="ind.indicador_id" :value="ind.indicador_id">
              {{ ind.nombre }}
            </option>
          </select>
        </div>

        <!-- Descripción -->
        <div class="sm:col-span-2">
          <label class="block font-cuerpo font-medium text-sm text-ubpd-gris mb-1.5">Descripción</label>
          <input
            v-model="form.descripcion"
            type="text"
            placeholder="Descripción breve del template..."
            class="w-full font-cuerpo text-sm border border-gray-300 rounded-lg px-4 py-2.5
                   focus:outline-none focus:border-ubpd-verde transition"
          />
        </div>
      </div>
    </div>

    <!-- Editor principal - 2 columnas -->
    <div class="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-2 gap-5">
      <!-- Columna izquierda: Editor Markdown -->
      <div class="flex flex-col bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div class="flex items-center justify-between px-5 py-3 border-b border-gray-100 flex-shrink-0">
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-ubpd-teal" />
            <span class="font-subtitulo font-semibold text-sm text-ubpd-gris">Editor Markdown</span>
          </div>
          <div class="flex items-center gap-2">
            <span v-if="previewLoading" class="font-cuerpo text-xs text-ubpd-teal flex items-center gap-1">
              <svg class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Actualizando preview...
            </span>
          </div>
        </div>
        <div class="flex-1 overflow-hidden">
          <textarea
            v-model="form.codigo_markdown"
            @input="debouncedPreview"
            placeholder="# Nombre del Formulario&#10;&#10;## Campos&#10;&#10;| campo | tipo | bloqueado | default | requerido |&#10;|-------|------|-----------|---------|-----------|&#10;| municipio | text | true | Bogotá | true |"
            class="w-full h-full font-mono text-sm border-0 focus:ring-0 outline-none resize-none p-5
                   text-ubpd-gris bg-white placeholder-gray-300"
            spellcheck="false"
          />
        </div>

        <!-- Ayuda del formato -->
        <div class="px-5 py-3 border-t border-gray-100 bg-gray-50 flex-shrink-0">
          <p class="font-cuerpo text-xs text-gray-400">
            <strong class="text-gray-500">Tipos:</strong> text, number, date, textarea, select —
            <strong class="text-gray-500">bloqueado: true</strong> hace el campo readonly
          </p>
        </div>
      </div>

      <!-- Columna derecha: Preview del formulario -->
      <div class="flex flex-col bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div class="flex items-center gap-2 px-5 py-3 border-b border-gray-100 flex-shrink-0">
          <div class="w-2 h-2 rounded-full bg-ubpd-verde" />
          <span class="font-subtitulo font-semibold text-sm text-ubpd-gris">Vista Previa del Formulario</span>
        </div>

        <!-- Estado vacío del preview -->
        <div v-if="!previewFields.length && !previewLoading" class="flex-1 flex flex-col items-center justify-center p-8 text-center">
          <svg class="w-12 h-12 text-gray-200 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
          <p class="font-cuerpo text-sm text-gray-400">Escriba el Markdown para ver la vista previa</p>
        </div>

        <!-- Campos del preview -->
        <div v-else class="flex-1 overflow-y-auto p-5 space-y-4">
          <div
            v-for="field in previewFields"
            :key="field.name"
            class="space-y-1"
          >
            <div class="flex items-center gap-2">
              <label class="font-cuerpo font-medium text-sm text-ubpd-gris">
                {{ field.label ?? field.name }}
                <span v-if="field.requerido" class="text-ubpd-naranja ml-0.5">*</span>
              </label>
              <!-- Indicador: readonly vs editable -->
              <span
                class="inline-flex items-center gap-1 text-xs font-cuerpo px-1.5 py-0.5 rounded"
                :class="field.readonly ? 'bg-gray-100 text-gray-500' : 'bg-ubpd-verde/10 text-ubpd-verde'"
                :title="field.readonly ? 'Campo bloqueado (solo lectura)' : 'Campo editable'"
              >
                <!-- Candado si readonly -->
                <svg v-if="field.readonly" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <!-- Lápiz si editable -->
                <svg v-else class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
                {{ field.readonly ? 'Bloqueado' : 'Editable' }}
              </span>
            </div>

            <!-- Textarea -->
            <textarea
              v-if="field.tipo === 'textarea'"
              :value="field.default ?? ''"
              :disabled="field.readonly"
              rows="3"
              class="w-full font-cuerpo text-sm border rounded-lg px-4 py-2.5 transition resize-none"
              :class="field.readonly
                ? 'bg-ubpd-gris-claro border-ubpd-gris-borde text-gray-500 cursor-not-allowed'
                : 'bg-white border-gray-300 focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20 focus:outline-none'"
            />
            <!-- Date -->
            <input
              v-else-if="field.tipo === 'date'"
              type="date"
              :value="field.default ?? ''"
              :disabled="field.readonly"
              class="w-full font-cuerpo text-sm border rounded-lg px-4 py-2.5 transition"
              :class="field.readonly
                ? 'bg-ubpd-gris-claro border-ubpd-gris-borde text-gray-500 cursor-not-allowed'
                : 'bg-white border-gray-300 focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20 focus:outline-none'"
            />
            <!-- Number -->
            <input
              v-else-if="field.tipo === 'number'"
              type="number"
              :value="field.default ?? ''"
              :disabled="field.readonly"
              class="w-full font-cuerpo text-sm border rounded-lg px-4 py-2.5 transition"
              :class="field.readonly
                ? 'bg-ubpd-gris-claro border-ubpd-gris-borde text-gray-500 cursor-not-allowed'
                : 'bg-white border-gray-300 focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20 focus:outline-none'"
            />
            <!-- Text (default) -->
            <input
              v-else
              type="text"
              :value="field.default ?? ''"
              :disabled="field.readonly"
              class="w-full font-cuerpo text-sm border rounded-lg px-4 py-2.5 transition"
              :class="field.readonly
                ? 'bg-ubpd-gris-claro border-ubpd-gris-borde text-gray-500 cursor-not-allowed'
                : 'bg-white border-gray-300 focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20 focus:outline-none'"
            />
          </div>
        </div>

        <!-- Error de preview -->
        <div v-if="previewError" class="px-5 py-3 border-t border-orange-100 bg-orange-50 flex-shrink-0">
          <p class="font-cuerpo text-xs text-ubpd-naranja">{{ previewError }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useNotificationsStore } from '@/stores/notifications'

interface Indicator {
  indicador_id: number
  nombre: string
}

interface PreviewField {
  name: string
  label?: string
  tipo: string
  readonly: boolean
  default?: string
  requerido?: boolean
}

interface PreviewResponse {
  fields: PreviewField[]
  error?: string
}

const route = useRoute()
const router = useRouter()
const { get, post, patch } = useApi()
const notifications = useNotificationsStore()

const templateId = computed(() => route.params.id as string | undefined)
const isEditing = computed(() => !!templateId.value && templateId.value !== 'new')

const saving = ref(false)
const loadingIndicators = ref(true)
const previewLoading = ref(false)
const previewError = ref('')
const previewFields = ref<PreviewField[]>([])
const indicators = ref<Indicator[]>([])

let previewDebounceTimer: ReturnType<typeof setTimeout> | null = null

const form = reactive({
  nombre: '',
  descripcion: '',
  indicador_nivel1_id: null as number | null,
  codigo_markdown: `# Nombre del Formulario

## Campos

| campo | tipo | bloqueado | default | requerido |
|-------|------|-----------|---------|-----------|
| municipio | text | true | Bogotá | true |
| codigo_caso | text | false | | true |
| fecha_hecho | date | false | | true |
| num_personas | number | false | 1 | true |
`,
})

async function loadIndicators() {
  loadingIndicators.value = true
  try {
    const data = await get<Indicator[]>('/stats/indicators')
    indicators.value = data
  } catch {
    // Indicadores no críticos para el editor
  } finally {
    loadingIndicators.value = false
  }
}

async function loadTemplate() {
  if (!isEditing.value) return
  try {
    const data = await get<{
      nombre: string
      descripcion?: string
      indicador_nivel1_id?: number
      codigo_markdown?: string
    }>(`/templates/${templateId.value}`)
    form.nombre = data.nombre
    form.descripcion = data.descripcion ?? ''
    form.indicador_nivel1_id = data.indicador_nivel1_id ?? null
    form.codigo_markdown = data.codigo_markdown ?? form.codigo_markdown
    await updatePreview()
  } catch {
    notifications.error('No se pudo cargar el template')
  }
}

onMounted(async () => {
  await loadIndicators()
  await loadTemplate()
  if (!isEditing.value) {
    await updatePreview()
  }
})

async function updatePreview() {
  if (!form.codigo_markdown.trim()) {
    previewFields.value = []
    previewError.value = ''
    return
  }
  previewLoading.value = true
  previewError.value = ''
  try {
    const response = await post<PreviewResponse>('/templates/preview', {
      codigo_markdown: form.codigo_markdown,
    })
    previewFields.value = response.fields ?? []
    if (response.error) previewError.value = response.error
  } catch {
    previewError.value = 'No se pudo generar el preview. Verifique la sintaxis del Markdown.'
    previewFields.value = []
  } finally {
    previewLoading.value = false
  }
}

function debouncedPreview() {
  if (previewDebounceTimer) clearTimeout(previewDebounceTimer)
  previewDebounceTimer = setTimeout(updatePreview, 800)
}

async function handleSave() {
  if (!form.nombre.trim()) {
    notifications.error('El nombre del template es obligatorio')
    return
  }
  saving.value = true
  try {
    const payload = {
      nombre: form.nombre,
      descripcion: form.descripcion,
      indicador_nivel1_id: form.indicador_nivel1_id,
      codigo_markdown: form.codigo_markdown,
    }
    if (isEditing.value) {
      await patch(`/templates/${templateId.value}`, payload)
      notifications.success('Template actualizado exitosamente')
    } else {
      await post('/templates', payload)
      notifications.success('Template creado exitosamente')
      router.push('/admin/templates')
    }
  } catch (err: unknown) {
    const axiosErr = err as { response?: { data?: { detail?: string } } }
    notifications.error(axiosErr?.response?.data?.detail || 'Error al guardar el template')
  } finally {
    saving.value = false
  }
}
</script>
