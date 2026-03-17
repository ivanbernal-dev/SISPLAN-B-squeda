<template>
  <div class="max-w-4xl mx-auto space-y-6 pb-12">
    <!-- Loading skeleton -->
    <div v-if="loading" class="space-y-4 animate-pulse">
      <div class="h-8 bg-gray-200 rounded w-1/2" />
      <div class="h-4 bg-gray-100 rounded w-1/3" />
      <div class="h-64 bg-gray-100 rounded-xl" />
    </div>

    <template v-else>
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 class="text-xl font-bold font-montserrat text-ubpd-gris leading-tight">
            {{ templateData?.nombre ?? 'Formulario' }}
          </h1>
          <p class="text-sm font-barlow text-gray-500 mt-0.5">{{ dependenciaNombre }}</p>
        </div>
        <StatusBadge v-if="formData?.estado" :status="formData.estado" />
      </div>

      <!-- Rejection banner -->
      <div
        v-if="formData?.estado === 'rejected' && formData.comentario_rechazo"
        class="bg-orange-50 border border-ubpd-naranja rounded-xl p-4"
        role="alert"
      >
        <p class="text-sm font-semibold text-ubpd-naranja font-barlow mb-1">
          ⚠️ Este formulario requiere corrección
        </p>
        <p class="text-sm font-barlow text-ubpd-gris">{{ formData.comentario_rechazo }}</p>
      </div>

      <!-- Date fields row -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 bg-white border border-gray-200 rounded-xl p-5">
        <div class="flex flex-col gap-1">
          <label class="text-xs font-semibold font-barlow text-gray-500 uppercase tracking-wide">
            Fecha de Carga
          </label>
          <input
            type="text"
            :value="formData?.fecha_carga ? formatDate(formData.fecha_carga) : 'Se asignará al guardar'"
            disabled
            class="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-barlow text-gray-500 cursor-not-allowed"
          />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-xs font-semibold font-barlow text-gray-500 uppercase tracking-wide">
            Última Edición
          </label>
          <input
            type="text"
            :value="formData?.fecha_ultima_edicion ? formatDate(formData.fecha_ultima_edicion) : '—'"
            disabled
            class="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-barlow text-gray-500 cursor-not-allowed"
          />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-xs font-semibold font-barlow text-gray-500">
            Fecha de Referencia
          </label>
          <input
            type="date"
            v-model="fechaReferencia"
            :disabled="isReadOnly"
            class="rounded-lg border border-gray-300 px-3 py-2 text-sm font-barlow focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-teal-100"
            :class="isReadOnly ? 'bg-gray-50 cursor-not-allowed' : 'bg-white'"
          />
        </div>
      </div>

      <!-- Dynamic form -->
      <div
        v-if="schema"
        class="bg-white border border-gray-200 rounded-xl p-5 space-y-4"
      >
        <h2 class="text-base font-semibold font-montserrat text-ubpd-gris">Campos del formulario</h2>
        <DynamicFormRenderer
          :schema="schema"
          v-model="dinamicValues"
          :read-only="isReadOnly"
          :highlighted-fields="highlightedFields"
        />
      </div>

      <!-- Informe cualitativo -->
      <div class="bg-white border border-gray-200 rounded-xl p-5 space-y-2">
        <label for="informe_cualitativo" class="text-base font-semibold font-montserrat text-ubpd-gris">
          Informe cualitativo de la búsqueda
          <span class="text-ubpd-naranja">*</span>
        </label>
        <textarea
          id="informe_cualitativo"
          v-model="informeCualitativo"
          :disabled="isReadOnly"
          rows="6"
          placeholder="Describa los hallazgos, procesos y resultados de la búsqueda de manera cualitativa..."
          class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-barlow resize-y focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-teal-100"
          :class="isReadOnly ? 'bg-gray-50 cursor-not-allowed' : 'bg-white'"
        />
      </div>

      <!-- File upload -->
      <div class="bg-white border border-gray-200 rounded-xl p-5 space-y-2">
        <h2 class="text-base font-semibold font-montserrat text-ubpd-gris">Soportes y archivos adjuntos</h2>
        <FileUploadZone
          :form-id="formId ?? undefined"
          :existing-files="formData?.archivos ?? []"
          :read-only="isReadOnly"
          @uploaded="onFileUploaded"
          @removed="onFileRemoved"
        />
      </div>

      <!-- Action buttons -->
      <div v-if="!isReadOnly" class="flex flex-wrap items-center gap-3 pt-2">
        <button
          type="button"
          class="px-6 py-2.5 border-2 border-ubpd-teal text-ubpd-teal font-semibold font-barlow text-sm rounded-lg
                 hover:bg-teal-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="saving"
          @click="saveDraft"
        >
          <span v-if="saving && saveMode === 'draft'">Guardando...</span>
          <span v-else>Guardar Borrador</span>
        </button>
        <button
          type="button"
          class="px-6 py-2.5 bg-ubpd-teal text-white font-semibold font-barlow text-sm rounded-lg
                 hover:bg-teal-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="saving || !canSubmit"
          :title="!canSubmit ? 'Complete todos los campos requeridos para enviar' : ''"
          @click="submitForm"
        >
          <span v-if="saving && saveMode === 'submit'">Enviando...</span>
          <span v-else>Enviar a Revisión</span>
        </button>

        <!-- Auto-save indicator -->
        <span v-if="lastAutoSave" class="text-xs text-gray-400 font-barlow">
          Autoguardado {{ formatTime(lastAutoSave) }}
        </span>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import type { FormData, FormSchema, FileRecord } from '@/types/forms'
import DynamicFormRenderer from '@/components/forms/DynamicFormRenderer.vue'
import FileUploadZone from '@/components/forms/FileUploadZone.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'

interface Template {
  id: string
  nombre: string
  descripcion: string | null
  configuracion_campos: FormSchema
}

const route = useRoute()
const router = useRouter()
const { get, post, patch } = useApi()
const authStore = useAuthStore()
const notifications = useNotificationsStore()

// Route params
const templateId = computed(() => route.params.template_id as string | undefined)
const formId = ref<string | null>((route.params.id as string) || null)

// State
const loading = ref(true)
const saving = ref(false)
const saveMode = ref<'draft' | 'submit'>('draft')

const templateData = ref<Template | null>(null)
const formData = ref<FormData | null>(null)
const schema = computed<FormSchema | null>(() => templateData.value?.configuracion_campos ?? null)

const dependenciaNombre = ref('')
const dinamicValues = ref<Record<string, unknown>>({})
const informeCualitativo = ref('')
const fechaReferencia = ref(new Date().toISOString().split('T')[0])
const highlightedFields = ref<string[]>([])
const lastAutoSave = ref<Date | null>(null)
let autoSaveInterval: ReturnType<typeof setInterval> | null = null
let hasChanges = false

const isReadOnly = computed(() =>
  formData.value?.estado === 'approved' || formData.value?.estado === 'pending',
)

const canSubmit = computed(() => {
  if (!schema.value) return false
  const required = schema.value.fields.filter((f) => f.required && !f.readonly)
  return required.every((f) => {
    const val = dinamicValues.value[f.name]
    return val !== undefined && val !== null && val !== ''
  }) && informeCualitativo.value.trim().length > 0
})

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' })
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })
}

async function loadTemplate(id: string) {
  templateData.value = await get<Template>(`/templates/${id}`)
  // Pre-fill defaults
  const vals: Record<string, unknown> = {}
  for (const f of templateData.value.configuracion_campos.fields) {
    vals[f.name] = f.default ?? ''
  }
  dinamicValues.value = vals
}

async function loadForm(id: string) {
  formData.value = await get<FormData>(`/forms/${id}`)
  templateData.value = await get<Template>(`/templates/${formData.value.template_id}`)
  dinamicValues.value = formData.value.datos_dinamicos as Record<string, unknown>
  informeCualitativo.value = formData.value.informe_cualitativo ?? ''
  fechaReferencia.value = formData.value.fecha_referencia ?? new Date().toISOString().split('T')[0]
  dependenciaNombre.value = formData.value.dependencia_nombre ?? ''
}

async function loadData() {
  loading.value = true
  try {
    if (formId.value) {
      await loadForm(formId.value)
    } else if (templateId.value) {
      await loadTemplate(templateId.value)
    }
  } catch {
    notifications.error('Error', 'No se pudo cargar el formulario.')
    router.push('/dependencia/inbox')
  } finally {
    loading.value = false
  }
}

function buildPayload() {
  return {
    template_id: templateData.value?.id,
    fecha_referencia: fechaReferencia.value,
    datos_dinamicos: dinamicValues.value,
    informe_cualitativo: informeCualitativo.value,
  }
}

async function saveDraft() {
  saving.value = true
  saveMode.value = 'draft'
  try {
    if (formId.value) {
      await patch(`/forms/${formId.value}`, buildPayload())
    } else {
      const created = await post<FormData>('/forms', buildPayload())
      formId.value = created.id
      formData.value = created
      router.replace(`/dependencia/forms/${created.id}`)
    }
    hasChanges = false
    lastAutoSave.value = new Date()
    notifications.success('Guardado', 'El borrador ha sido guardado correctamente.')
  } catch {
    notifications.error('Error al guardar', 'No se pudo guardar el borrador.')
  } finally {
    saving.value = false
  }
}

async function submitForm() {
  saving.value = true
  saveMode.value = 'submit'
  try {
    // Save first, then submit
    if (formId.value) {
      await patch(`/forms/${formId.value}`, buildPayload())
      await post(`/forms/${formId.value}/submit`, {})
    } else {
      const created = await post<FormData>('/forms', buildPayload())
      formId.value = created.id
      await post(`/forms/${created.id}/submit`, {})
      router.replace(`/dependencia/forms/${created.id}`)
    }
    hasChanges = false
    notifications.success('Enviado', 'El formulario ha sido enviado a revisión.')
    await loadForm(formId.value!)
  } catch {
    notifications.error('Error al enviar', 'No se pudo enviar el formulario a revisión.')
  } finally {
    saving.value = false
  }
}

function onFileUploaded(file: FileRecord) {
  if (formData.value) {
    formData.value.archivos = [...(formData.value.archivos ?? []), file]
  }
}

async function onFileRemoved(fileId: string) {
  const { del } = useApi()
  try {
    await del(`/files/${fileId}`)
    if (formData.value) {
      formData.value.archivos = formData.value.archivos.filter((f) => f.id !== fileId)
    }
  } catch {
    notifications.error('Error', 'No se pudo eliminar el archivo.')
  }
}

// Auto-save every 2 minutes if there are changes
watch([dinamicValues, informeCualitativo, fechaReferencia], () => {
  hasChanges = true
}, { deep: true })

onMounted(() => {
  loadData()
  autoSaveInterval = setInterval(() => {
    if (hasChanges && !isReadOnly.value && !saving.value) {
      saveDraft()
    }
  }, 2 * 60 * 1000)
})

onUnmounted(() => {
  if (autoSaveInterval) clearInterval(autoSaveInterval)
})
</script>
