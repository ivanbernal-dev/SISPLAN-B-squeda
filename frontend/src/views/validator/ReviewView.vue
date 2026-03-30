<template>
  <div class="h-full flex flex-col">
    <!-- Barra superior -->
    <div class="bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between flex-shrink-0">
      <div class="flex items-center gap-3">
        <RouterLink
          to="/validator/inbox"
          class="p-2 rounded-lg text-gray-400 hover:text-ubpd-teal hover:bg-ubpd-teal/10 transition"
          aria-label="Volver a la bandeja de entrada"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </RouterLink>
        <div>
          <p class="font-subtitulo font-bold text-ubpd-gris">Revisión de Formulario</p>
          <p v-if="formData" class="font-cuerpo text-xs text-gray-400">
            {{ formData.template_nombre }} · {{ formData.dependencia_nombre }}
          </p>
        </div>
      </div>
      <span class="font-cuerpo text-xs font-medium px-3 py-1 rounded-full bg-ubpd-teal/10 text-ubpd-teal">
        En Revisión
      </span>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading" class="flex-1 flex gap-0 overflow-hidden">
      <div class="flex-1 p-6 space-y-4 animate-pulse">
        <div class="w-full h-6 rounded bg-gray-200" />
        <div class="w-3/4 h-4 rounded bg-gray-200" />
        <div class="w-full h-32 rounded bg-gray-200" />
        <div class="w-full h-32 rounded bg-gray-200" />
      </div>
      <div class="w-80 border-l border-gray-100 p-4 space-y-3 animate-pulse">
        <div class="w-full h-20 rounded bg-gray-200" />
        <div class="w-full h-20 rounded bg-gray-200" />
      </div>
    </div>

    <!-- Contenido split screen -->
    <div v-else-if="formData" class="flex-1 flex overflow-hidden">

      <!-- Panel izquierdo (60%): Datos del formulario -->
      <div class="flex-1 overflow-y-auto p-6 space-y-5" style="flex: 0 0 60%;">

        <!-- Info general -->
        <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 space-y-3">
          <h2 class="font-subtitulo font-bold text-lg text-ubpd-gris">{{ formData.template_nombre }}</h2>
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span class="font-cuerpo text-xs text-gray-400 block">Dependencia</span>
              <span class="font-cuerpo font-medium text-ubpd-gris">{{ formData.dependencia_nombre }}</span>
            </div>
            <div>
              <span class="font-cuerpo text-xs text-gray-400 block">Registrado por</span>
              <span class="font-cuerpo font-medium text-ubpd-gris">{{ formData.usuario_nombre }}</span>
            </div>
            <div>
              <span class="font-cuerpo text-xs text-gray-400 block">Fecha de carga</span>
              <span class="font-cuerpo text-ubpd-gris">{{ formatDate(formData.fecha_carga) }}</span>
            </div>
            <div>
              <span class="font-cuerpo text-xs text-gray-400 block">Última edición</span>
              <span class="font-cuerpo text-ubpd-gris">{{ formatDate(formData.fecha_edicion) }}</span>
            </div>
            <div>
              <span class="font-cuerpo text-xs text-gray-400 block">Fecha de referencia</span>
              <span class="font-cuerpo text-ubpd-gris">{{ formatDate(formData.fecha_usuario) }}</span>
            </div>
          </div>
        </div>

        <!-- Campos dinámicos -->
        <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 space-y-4">
          <h3 class="font-subtitulo font-semibold text-ubpd-gris mb-3">Datos del Registro</h3>
          <div
            v-for="(value, key) in formData.datos_dinamicos"
            :key="String(key)"
            class="space-y-1"
          >
            <label class="font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide">
              {{ formatFieldName(String(key)) }}
            </label>
            <div class="w-full font-cuerpo text-sm bg-gray-50 border border-gray-200
                        rounded-lg px-4 py-2.5 text-gray-600">
              {{ value ?? '—' }}
            </div>
          </div>
        </div>

        <!-- Informe Cualitativo -->
        <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
          <h3 class="font-subtitulo font-semibold text-ubpd-gris mb-3">Informe Cualitativo</h3>
          <textarea
            v-autoresize
            :value="formData.informe_cualitativo ?? '—'"
            disabled
            class="w-full font-cuerpo text-sm bg-gray-50 border border-gray-200
                   rounded-lg px-4 py-3 text-gray-600 cursor-not-allowed min-h-[100px]"
          />
        </div>
      </div>

      <!-- Panel derecho (40%): Archivos adjuntos + Dictamen -->
      <div class="border-l border-gray-100 overflow-y-auto flex flex-col" style="flex: 0 0 40%;">

        <!-- ── Archivos adjuntos ──────────────────────────────── -->
        <div class="p-5 flex-1">
          <h3 class="font-subtitulo font-semibold text-ubpd-gris mb-4 flex items-center gap-2">
            <svg class="w-5 h-5 text-ubpd-teal" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586
                   a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
            </svg>
            Documentos Soporte
            <span class="ml-auto font-cuerpo text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">
              {{ formData.archivos?.length ?? 0 }}
            </span>
          </h3>

          <div v-if="formData.archivos?.length" class="space-y-3">
            <div
              v-for="archivo in formData.archivos"
              :key="archivo.id"
              class="bg-white rounded-xl border border-gray-100 shadow-sm p-4"
            >
              <div class="flex items-start gap-3">
                <!-- Ícono según MIME -->
                <div
                  class="flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center"
                  :class="mimeIconBg(archivo.tipo_mime)"
                >
                  <!-- Imagen: miniatura -->
                  <img
                    v-if="isImage(archivo.tipo_mime)"
                    :src="thumbCache[archivo.id]"
                    :alt="archivo.nombre"
                    class="w-12 h-12 object-cover rounded-xl"
                  />
                  <!-- PDF -->
                  <svg v-else-if="archivo.tipo_mime === 'application/pdf'"
                    class="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                      d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414
                         A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  <!-- Word -->
                  <svg v-else
                    class="w-6 h-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586
                         a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>

                <!-- Info -->
                <div class="flex-1 min-w-0">
                  <p class="font-cuerpo font-medium text-sm text-ubpd-gris truncate">
                    {{ archivo.nombre || archivo.nombre_original }}
                  </p>
                  <p class="font-cuerpo text-xs text-gray-400 mt-0.5">
                    {{ mimeLabel(archivo.tipo_mime) }} · {{ formatSize(archivo.tamanio) }}
                  </p>

                  <!-- Acciones -->
                  <div class="flex items-center gap-2 mt-2.5">
                    <!-- Ver (PDF e imágenes) -->
                    <button
                      v-if="isViewable(archivo.tipo_mime)"
                      @click="viewFile(archivo.id)"
                      :disabled="activeFileId === archivo.id"
                      class="inline-flex items-center gap-1 font-cuerpo text-xs font-medium
                             text-gray-600 border border-gray-200 rounded-lg px-2.5 py-1.5
                             hover:bg-gray-100 hover:border-gray-300 transition
                             disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <svg v-if="activeFileId !== archivo.id || activeFileAction !== 'view'"
                        class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943
                             9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                      <svg v-else class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                      </svg>
                      Ver
                    </button>

                    <!-- Descargar (siempre) -->
                    <button
                      @click="downloadFile(archivo.id, archivo.nombre || archivo.nombre_original)"
                      :disabled="activeFileId === archivo.id"
                      class="inline-flex items-center gap-1 font-cuerpo text-xs font-medium
                             text-ubpd-teal border border-ubpd-teal/30 rounded-lg px-2.5 py-1.5
                             hover:bg-ubpd-teal hover:text-white hover:border-ubpd-teal transition
                             disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <svg v-if="activeFileId !== archivo.id || activeFileAction !== 'download'"
                        class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      <svg v-else class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                      </svg>
                      Descargar
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="text-center py-10">
            <div class="w-12 h-12 rounded-2xl bg-gray-100 flex items-center justify-center mx-auto mb-3">
              <svg class="w-6 h-6 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                  d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586
                     a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
              </svg>
            </div>
            <p class="font-cuerpo text-sm text-gray-400">Sin documentos adjuntos</p>
          </div>
        </div>

        <!-- ── Panel de Dictamen ──────────────────────────────── -->
        <div class="border-t border-gray-100 bg-gray-50 p-5 space-y-4 flex-shrink-0">
          <h3 class="font-subtitulo font-semibold text-ubpd-gris">Dictamen</h3>

          <!-- Área de rechazo -->
          <Transition name="slide">
            <div v-if="showRejectionForm" class="space-y-2">
              <label class="block font-cuerpo font-medium text-sm text-ubpd-gris">
                Observaciones <span class="text-ubpd-naranja">*</span>
              </label>
              <textarea
                v-autoresize
                v-model="rejectionComment"
                placeholder="Indique los ajustes requeridos de forma clara y precisa..."
                class="w-full font-cuerpo text-sm border border-gray-300 rounded-lg px-4 py-3
                       min-h-[90px] focus:outline-none focus:border-ubpd-naranja
                       focus:ring-2 focus:ring-ubpd-naranja/20 transition"
                :class="rejectionComment.trim() ? 'border-ubpd-naranja/50' : ''"
              />
              <p class="font-cuerpo text-xs text-gray-400">
                {{ rejectionComment.length }} caracteres — mínimo recomendado: 20
              </p>
            </div>
          </Transition>

          <!-- Botones de acción -->
          <div class="flex gap-3">
            <button
              v-if="!showRejectionForm"
              @click="showApproveConfirm = true"
              :disabled="actionLoading"
              class="flex-1 flex items-center justify-center gap-2
                     bg-ubpd-verde text-white font-cuerpo font-semibold text-sm
                     rounded-xl px-4 py-3 hover:bg-[#469090] transition
                     disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Aprobar
            </button>

            <button
              v-if="!showRejectionForm"
              @click="showRejectionForm = true"
              :disabled="actionLoading"
              class="flex-1 flex items-center justify-center gap-2
                     bg-ubpd-naranja text-white font-cuerpo font-semibold text-sm
                     rounded-xl px-4 py-3 hover:bg-orange-600 transition
                     disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94
                     a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
              </svg>
              Devolver
            </button>

            <template v-if="showRejectionForm">
              <button
                @click="showRejectionForm = false; rejectionComment = ''"
                class="flex-shrink-0 border border-gray-300 text-ubpd-gris font-cuerpo
                       font-medium text-sm rounded-xl px-4 py-3 hover:bg-gray-100 transition"
              >
                Cancelar
              </button>
              <button
                @click="handleReject"
                :disabled="!rejectionComment.trim() || actionLoading"
                class="flex-1 flex items-center justify-center gap-2
                       bg-ubpd-naranja text-white font-cuerpo font-semibold text-sm
                       rounded-xl px-4 py-3 hover:bg-orange-600 transition
                       disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg v-if="actionLoading" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                Enviar Observaciones
              </button>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- Confirmación aprobación -->
    <ConfirmModal
      :is-open="showApproveConfirm"
      title="Aprobar registro"
      message="¿Confirma que este registro cumple con los criterios de validación?"
      confirm-text="Confirmar aprobación"
      confirm-variant="success"
      :loading="actionLoading"
      @confirm="handleApprove"
      @cancel="showApproveConfirm = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useNotificationsStore } from '@/stores/notifications'
import ConfirmModal from '@/components/common/ConfirmModal.vue'

// ─── Tipos ────────────────────────────────────────────────────────────────────

interface Archivo {
  id: string
  nombre_original: string
  nombre: string       // alias del backend
  tipo_mime?: string
  tamanio: number      // alias del backend
  tamaño_bytes?: number
}

interface FormData {
  id: string
  template_nombre: string
  dependencia_nombre: string
  usuario_nombre: string
  fecha_carga: string
  fecha_edicion: string
  fecha_usuario: string
  datos_dinamicos: Record<string, unknown>
  informe_cualitativo: string | null
  archivos: Archivo[]
}

// ─── Setup ────────────────────────────────────────────────────────────────────

const route  = useRoute()
const router = useRouter()
const { get, patch, client: apiClient } = useApi()
const notifications = useNotificationsStore()

const formId = route.params.id as string

const loading       = ref(true)
const actionLoading = ref(false)
const formData      = ref<FormData | null>(null)

const showApproveConfirm = ref(false)
const showRejectionForm  = ref(false)
const rejectionComment   = ref('')

// Estado para botones de archivo
const activeFileId     = ref<string | null>(null)
const activeFileAction = ref<'view' | 'download' | null>(null)

// Cache de thumbnails para imágenes
const thumbCache = ref<Record<string, string>>({})

// ─── Carga ────────────────────────────────────────────────────────────────────

async function loadForm() {
  loading.value = true
  try {
    formData.value = await get<FormData>(`/forms/${formId}`)
    // Pre-cargar thumbnails de imágenes en background (no bloqueante)
    if (formData.value?.archivos?.length) {
      loadImageThumbs(formData.value.archivos)
    }
  } catch {
    notifications.error('No se pudo cargar el formulario')
    router.push('/validator/inbox')
  } finally {
    loading.value = false
  }
}

async function loadImageThumbs(archivos: Archivo[]) {
  for (const a of archivos) {
    if (isImage(a.tipo_mime)) {
      try {
        const res = await apiClient.get(`/files/${a.id}/download`, { responseType: 'blob' })
        const blob = new Blob([res.data as BlobPart], { type: a.tipo_mime || 'image/jpeg' })
        thumbCache.value[a.id] = URL.createObjectURL(blob)
      } catch {
        // Miniatura no crítica — no mostrar error
      }
    }
  }
}

onMounted(loadForm)

// ─── Helpers de archivo ───────────────────────────────────────────────────────

function isImage(mime?: string): boolean {
  return !!mime?.startsWith('image/')
}

function isViewable(mime?: string): boolean {
  return !!mime && (mime.startsWith('image/') || mime === 'application/pdf')
}

function mimeLabel(mime?: string): string {
  if (!mime) return 'Archivo'
  if (mime === 'application/pdf') return 'PDF'
  if (mime.startsWith('image/')) return mime.split('/')[1].toUpperCase()
  if (mime.includes('wordprocessingml')) return 'DOCX'
  return mime.split('/')[1]?.toUpperCase() ?? 'Archivo'
}

function mimeIconBg(mime?: string): string {
  if (mime === 'application/pdf') return 'bg-red-50 border border-red-100'
  if (mime?.startsWith('image/'))  return 'bg-blue-50 border border-blue-100 overflow-hidden'
  return 'bg-gray-50 border border-gray-100'
}

async function _fetchBlob(fileId: string): Promise<Blob> {
  const res = await apiClient.get(`/files/${fileId}/download`, { responseType: 'blob' })
  return new Blob([res.data as BlobPart], {
    type: (res.headers['content-type'] as string) || 'application/octet-stream',
  })
}

async function viewFile(fileId: string) {
  activeFileId.value     = fileId
  activeFileAction.value = 'view'
  try {
    const blob   = await _fetchBlob(fileId)
    const url    = URL.createObjectURL(blob)
    const win    = window.open(url, '_blank', 'noopener,noreferrer')
    if (win) setTimeout(() => URL.revokeObjectURL(url), 60_000)
    else     URL.revokeObjectURL(url)
  } catch {
    notifications.error('No se pudo abrir el archivo')
  } finally {
    activeFileId.value     = null
    activeFileAction.value = null
  }
}

async function downloadFile(fileId: string, nombre?: string) {
  activeFileId.value     = fileId
  activeFileAction.value = 'download'
  try {
    const blob = await _fetchBlob(fileId)
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = nombre || 'archivo'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch {
    notifications.error('No se pudo descargar el archivo')
  } finally {
    activeFileId.value     = null
    activeFileAction.value = null
  }
}

// ─── Acciones de validación ───────────────────────────────────────────────────

async function handleApprove() {
  actionLoading.value = true
  try {
    await patch(`/validation/${formId}/approve`, {})
    notifications.success('Registro validado', 'El registro ha sido aprobado.')
    router.push('/validator/inbox')
  } catch {
    notifications.error('No se pudo aprobar el registro')
  } finally {
    actionLoading.value     = false
    showApproveConfirm.value = false
  }
}

async function handleReject() {
  if (!rejectionComment.value.trim()) return
  actionLoading.value = true
  try {
    await patch(`/validation/${formId}/reject`, { comentario: rejectionComment.value })
    notifications.success('Registro devuelto', 'El registro fue devuelto con las observaciones.')
    router.push('/validator/inbox')
  } catch {
    notifications.error('No se pudo devolver el registro')
  } finally {
    actionLoading.value = false
  }
}

// ─── Helpers visuales ─────────────────────────────────────────────────────────

function formatDate(d?: string): string {
  if (!d) return '—'
  return new Date(d).toLocaleString('es-CO', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function formatSize(bytes?: number): string {
  if (!bytes) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatFieldName(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}
</script>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}
.slide-enter-from,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-8px);
}
.slide-enter-to,
.slide-leave-from {
  max-height: 300px;
  opacity: 1;
  transform: translateY(0);
}
</style>
