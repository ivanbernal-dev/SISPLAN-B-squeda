<template>
  <div class="space-y-6">
    <!-- Breadcrumb -->
    <nav class="flex items-center gap-2 text-sm font-barlow text-gray-500 flex-wrap" aria-label="Navegación">
      <RouterLink to="/estadisticas" class="hover:text-ubpd-teal transition-colors">Plan de Acción Institucional 2026</RouterLink>
      <span aria-hidden="true">›</span>
      <RouterLink
        v-if="route.params.indicador_id"
        :to="`/estadisticas/${route.params.indicador_id}`"
        class="hover:text-ubpd-teal transition-colors"
      >Indicador</RouterLink>
      <span aria-hidden="true">›</span>
      <RouterLink
        v-if="route.params.indicador_id && route.params.template_id"
        :to="`/estadisticas/${route.params.indicador_id}/${route.params.template_id}`"
        class="hover:text-ubpd-teal transition-colors"
      >Formularios</RouterLink>
      <span aria-hidden="true">›</span>
      <span class="text-ubpd-gris font-semibold">Detalle</span>
    </nav>

    <!-- Loading skeleton -->
    <div v-if="loading" class="space-y-4 animate-pulse">
      <div class="h-8 bg-gray-200 rounded w-1/2" />
      <div class="h-4 bg-gray-100 rounded w-1/3" />
      <div class="h-64 bg-gray-100 rounded-xl" />
    </div>

    <template v-else-if="formDetail">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold font-montserrat text-ubpd-gris">
            {{ templateNombre || 'Detalle de Formulario' }}
          </h1>
          <p class="text-sm font-barlow text-gray-500 mt-0.5">
            {{ formDetail.dependencia_nombre }} —
            {{ formDetail.fecha_usuario ? formatDate(formDetail.fecha_usuario) : '—' }}
          </p>
        </div>
        <div class="flex items-center gap-3">
          <span
            class="text-xs font-semibold font-barlow px-3 py-1.5 rounded-full"
            :class="statusClass(formDetail.estado)"
          >
            {{ statusLabel(formDetail.estado) }}
          </span>
          <button
            type="button"
            class="inline-flex items-center gap-2 px-4 py-2 bg-ubpd-teal text-white font-semibold font-barlow text-sm rounded-lg hover:bg-teal-700 transition-colors"
            :disabled="downloadingExcel"
            @click="downloadExcel"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 256 256" fill="currentColor"><path d="M224,152v56a16,16,0,0,1-16,16H48a16,16,0,0,1-16-16V152a8,8,0,0,1,16,0v56H208V152a8,8,0,0,1,16,0Zm-101.66,5.66a8,8,0,0,0,11.32,0l40-40a8,8,0,0,0-11.32-11.32L136,132.69V40a8,8,0,0,0-16,0v92.69L93.66,106.34a8,8,0,0,0-11.32,11.32Z"/></svg>
            {{ downloadingExcel ? 'Descargando...' : 'Excel' }}
          </button>
        </div>
      </div>

      <!-- Metadata card -->
      <div class="bg-white border border-gray-200 rounded-xl p-5 grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div>
          <p class="text-xs font-semibold font-barlow text-gray-400 uppercase tracking-wide">Fecha Carga</p>
          <p class="text-sm font-barlow text-ubpd-gris mt-0.5">{{ formatDateTime(formDetail.fecha_carga) }}</p>
        </div>
        <div>
          <p class="text-xs font-semibold font-barlow text-gray-400 uppercase tracking-wide">Fecha Referencia</p>
          <p class="text-sm font-barlow text-ubpd-gris mt-0.5">{{ formDetail.fecha_usuario ? formatDate(formDetail.fecha_usuario) : '—' }}</p>
        </div>
        <div>
          <p class="text-xs font-semibold font-barlow text-gray-400 uppercase tracking-wide">Dependencia</p>
          <p class="text-sm font-barlow text-ubpd-gris mt-0.5">{{ formDetail.dependencia_nombre || '—' }}</p>
        </div>
        <div>
          <p class="text-xs font-semibold font-barlow text-gray-400 uppercase tracking-wide">Cargado via Excel</p>
          <p class="text-sm font-barlow text-ubpd-gris mt-0.5">{{ formDetail.cargado_via_excel ? 'Sí' : 'No' }}</p>
        </div>
      </div>

      <!-- Dynamic fields -->
      <div v-if="fields.length > 0" class="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
        <h2 class="text-base font-semibold font-montserrat text-ubpd-gris">Campos del formulario</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div
            v-for="field in fields"
            :key="field.name"
            class="flex flex-col gap-1"
            :class="field.tipo === 'textarea' ? 'sm:col-span-2' : ''"
          >
            <label class="text-xs font-semibold font-barlow text-gray-500 uppercase tracking-wide">
              {{ field.label }}
              <span v-if="field.readonly" class="ml-1 text-gray-300 font-normal normal-case">(readonly)</span>
            </label>
            <div
              v-if="field.tipo === 'file'"
              class="text-sm font-barlow text-gray-400 italic"
            >
              Ver archivos adjuntos abajo
            </div>
            <textarea
              v-else-if="field.tipo === 'textarea'"
              v-autoresize
              :value="getFieldValue(field.name)"
              readonly
              class="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-barlow text-gray-700 cursor-default min-h-[60px]"
            />
            <input
              v-else
              :value="getFieldValue(field.name)"
              :type="field.tipo === 'number' ? 'text' : 'text'"
              readonly
              class="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-barlow text-gray-700 cursor-default"
            />
          </div>
        </div>
      </div>

      <!-- Informe cualitativo -->
      <div v-if="formDetail.informe_cualitativo" class="bg-white border border-gray-200 rounded-xl p-5 space-y-2">
        <h2 class="text-base font-semibold font-montserrat text-ubpd-gris">Informe cualitativo</h2>
        <p class="text-sm font-barlow text-gray-700 whitespace-pre-line leading-relaxed">{{ formDetail.informe_cualitativo }}</p>
      </div>

      <!-- File attachments -->
      <div class="bg-white border border-gray-200 rounded-xl p-5 space-y-3">
        <h2 class="text-base font-semibold font-montserrat text-ubpd-gris">Archivos adjuntos</h2>
        <div v-if="loadingFiles" class="text-center py-4">
          <span class="inline-block h-5 w-5 border-2 border-ubpd-teal border-t-transparent rounded-full animate-spin" />
        </div>
        <ul v-else-if="attachments.length > 0" class="space-y-2">
          <li
            v-for="file in attachments"
            :key="file.id"
            class="flex items-center justify-between gap-3 bg-gray-50 rounded-lg px-4 py-3"
          >
            <div class="flex items-center gap-3 min-w-0">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 256 256" fill="currentColor" class="text-gray-400 shrink-0">
                <path d="M213.66,82.34l-56-56A8,8,0,0,0,152,24H56A16,16,0,0,0,40,40V216a16,16,0,0,0,16,16H200a16,16,0,0,0,16-16V88A8,8,0,0,0,213.66,82.34ZM160,51.31,188.69,80H160ZM200,216H56V40h88V88a8,8,0,0,0,8,8h48V216Z"/>
              </svg>
              <span class="text-sm font-barlow text-ubpd-gris truncate">{{ file.nombre }}</span>
            </div>
            <a
              v-if="file.url"
              :href="file.url"
              target="_blank"
              rel="noopener"
              class="text-xs text-ubpd-teal hover:underline font-barlow shrink-0"
            >
              Abrir
            </a>
          </li>
        </ul>
        <p v-else class="text-sm font-barlow text-gray-400">No hay archivos adjuntos.</p>
      </div>
    </template>

    <!-- Error state -->
    <div v-else-if="!loading" class="text-center py-16">
      <p class="text-base font-barlow text-gray-400">No se encontró el formulario solicitado.</p>
      <RouterLink to="/estadisticas" class="text-ubpd-teal hover:underline text-sm font-barlow mt-2 inline-block">
        Volver al Plan de Acción Institucional 2026
      </RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'
import type { FileRecord } from '@/types/forms'

interface FormDetail {
  id: string
  template_id?: string
  plantilla_id?: string
  estado: string
  fecha_carga: string
  fecha_usuario?: string
  informe_cualitativo?: string
  datos_dinamicos: Record<string, unknown>
  dependencia_nombre?: string
  cargado_via_excel?: boolean
  archivos?: FileRecord[]
}

interface FieldDef {
  name: string
  label: string
  tipo: string
  readonly: boolean
}

const route = useRoute()
const { get } = useApi()

const loading = ref(true)
const loadingFiles = ref(false)
const formDetail = ref<FormDetail | null>(null)
const fields = ref<FieldDef[]>([])
const attachments = ref<(FileRecord & { url?: string })[]>([])
const templateNombre = ref('')
const downloadingExcel = ref(false)

const formId = computed(() => route.params.form_id as string)

function getFieldValue(fieldName: string): string {
  if (!formDetail.value) return ''
  const val = formDetail.value.datos_dinamicos?.[fieldName]
  if (val === null || val === undefined) return ''
  return String(val)
}

function formatDate(dateStr: string): string {
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('es-CO', {
    day: 'numeric', month: 'long', year: 'numeric',
  })
}

function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' })
}

function statusLabel(estado: string): string {
  const map: Record<string, string> = {
    draft: 'Borrador', pending: 'En revisión', approved: 'Aprobado', rejected: 'Rechazado',
  }
  return map[estado] ?? estado
}

function statusClass(estado: string): string {
  const map: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-600',
    pending: 'bg-yellow-100 text-yellow-700',
    approved: 'bg-ubpd-verde/10 text-ubpd-verde',
    rejected: 'bg-orange-100 text-ubpd-naranja',
  }
  return map[estado] ?? 'bg-gray-100 text-gray-600'
}

async function downloadExcel() {
  downloadingExcel.value = true
  try {
    window.open(`${import.meta.env.VITE_API_URL || '/api'}/forms/${formId.value}/excel`, '_blank')
  } finally {
    downloadingExcel.value = false
  }
}

async function loadAttachments() {
  if (!formDetail.value) return
  loadingFiles.value = true
  try {
    const archivos = formDetail.value.archivos ?? []
    const withUrls = await Promise.all(
      archivos.map(async (f) => {
        try {
          const { url } = await get<{ url: string }>(`/files/${f.id}/url`)
          return { ...f, url }
        } catch {
          return f
        }
      })
    )
    attachments.value = withUrls
  } finally {
    loadingFiles.value = false
  }
}

async function loadTemplate(templateId: string) {
  try {
    const t = await get<{ nombre: string; configuracion_campos: { fields: FieldDef[] } }>(`/templates/${templateId}`)
    templateNombre.value = t.nombre
    fields.value = t.configuracion_campos.fields ?? []
  } catch {
    // ignore
  }
}

onMounted(async () => {
  loading.value = true
  try {
    formDetail.value = await get<FormDetail>(`/forms/${formId.value}`)
    const templateId = formDetail.value.template_id ?? formDetail.value.plantilla_id
    if (templateId) await loadTemplate(templateId)
    await loadAttachments()
  } catch {
    formDetail.value = null
  } finally {
    loading.value = false
  }
})
</script>
