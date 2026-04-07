<template>
  <div class="space-y-3">
    <!-- Drop zone -->
    <div
      v-if="!readOnly"
      class="relative border-2 border-dashed rounded-xl p-6 text-center transition-colors duration-200"
      :class="isDragging
        ? 'border-ubpd-verde bg-teal-50'
        : 'border-gray-300 bg-gray-50 hover:border-ubpd-teal hover:bg-teal-50/40'"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="onDrop"
      @click="fileInputRef?.click()"
      role="button"
      aria-label="Zona de carga de archivos"
      tabindex="0"
      @keydown.enter="fileInputRef?.click()"
    >
      <input
        ref="fileInputRef"
        type="file"
        multiple
        class="hidden"
        accept=".pdf,.jpg,.jpeg,.png,.docx,.xlsx,.xls"
        @change="onFileSelected"
      />

      <!-- Icon -->
      <div class="flex justify-center mb-2">
        <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 256 256"
          class="text-ubpd-teal" fill="currentColor" aria-hidden="true">
          <path d="M213.66,82.34l-56-56A8,8,0,0,0,152,24H56A16,16,0,0,0,40,40V216a16,16,0,0,0,16,16H200a16,16,0,0,0,16-16V88A8,8,0,0,0,213.66,82.34ZM160,51.31,188.69,80H160ZM200,216H56V40h88V88a8,8,0,0,0,8,8h48V216Zm-42.34-61.66a8,8,0,0,1-11.32,11.32L136,155.31V184a8,8,0,0,1-16,0V155.31l-10.34,10.35a8,8,0,0,1-11.32-11.32l24-24a8,8,0,0,1,11.32,0Z"/>
        </svg>
      </div>

      <p class="text-sm font-barlow text-gray-600">
        <span class="font-semibold text-ubpd-teal">Arrastra archivos aquí</span> o haz clic para seleccionar
      </p>
      <p class="text-xs text-gray-400 mt-1">PDF, JPG, PNG, DOCX, XLS/XLSX — máx. 50 MB por archivo</p>
    </div>

    <!-- Pending files queue -->
    <div v-if="pendingFiles.length > 0" class="space-y-2">
      <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Archivos pendientes</p>
      <div
        v-for="(pf, idx) in pendingFiles"
        :key="idx"
        class="flex items-center gap-3 bg-white border border-gray-200 rounded-lg p-3"
      >
        <component :is="fileIconComponent(pf.file.name)" class="text-gray-500 shrink-0" aria-hidden="true" />
        <div class="flex-1 min-w-0">
          <p class="text-sm font-barlow truncate text-ubpd-gris">{{ pf.file.name }}</p>
          <p class="text-xs text-gray-400">{{ formatSize(pf.file.size) }}</p>
          <!-- Progress bar -->
          <div class="mt-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div
              class="h-full bg-ubpd-verde transition-all duration-300 rounded-full"
              :style="{ width: pf.progress + '%' }"
            />
          </div>
        </div>
        <button
          type="button"
          class="text-gray-400 hover:text-ubpd-naranja transition-colors"
          :aria-label="`Quitar ${pf.file.name}`"
          @click.stop="removePending(idx)"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 256 256" fill="currentColor" aria-hidden="true">
            <path d="M205.66,194.34a8,8,0,0,1-11.32,11.32L128,139.31,61.66,205.66a8,8,0,0,1-11.32-11.32L116.69,128,50.34,61.66A8,8,0,0,1,61.66,50.34L128,116.69l66.34-66.35a8,8,0,0,1,11.32,11.32L139.31,128Z"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Existing uploaded files -->
    <div v-if="existingFiles && existingFiles.length > 0" class="space-y-2">
      <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Archivos subidos</p>
      <div
        v-for="file in existingFiles"
        :key="file.id"
        class="flex items-center gap-3 bg-white border border-gray-200 rounded-lg p-3"
      >
        <!-- Thumbnail for images -->
        <img
          v-if="isImage(file.tipo)"
          :src="file.url"
          :alt="file.nombre"
          class="w-10 h-10 object-cover rounded"
        />
        <!-- Icon for other types -->
        <span v-else class="text-gray-500">
          <svg v-if="file.tipo === 'application/pdf'" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 256 256" fill="currentColor" aria-hidden="true">
            <path d="M224,152a8,8,0,0,1-8,8H192v16h16a8,8,0,0,1,0,16H192v16a8,8,0,0,1-16,0V144a8,8,0,0,1,8-8h32A8,8,0,0,1,224,152ZM92,172a28,28,0,0,1-28,28H56v8a8,8,0,0,1-16,0V144a8,8,0,0,1,8-8H64A28,28,0,0,1,92,172Zm-16,0a12,12,0,0,0-12-12H56v24h8A12,12,0,0,0,76,172Zm88,8a36,36,0,0,1-36,36H112a8,8,0,0,1-8-8V144a8,8,0,0,1,8-8h16A36,36,0,0,1,164,180Zm-16,0a20,20,0,0,0-20-20h-8v40h8A20,20,0,0,0,148,180ZM40,112V40A16,16,0,0,1,56,24h96a8,8,0,0,1,5.66,2.34l56,56A8,8,0,0,1,216,88v24a8,8,0,0,1-16,0V96H152a8,8,0,0,1-8-8V40H56v72a8,8,0,0,1-16,0ZM160,80h28.69L160,51.31Z"/>
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 256 256" fill="currentColor" aria-hidden="true">
            <path d="M213.66,82.34l-56-56A8,8,0,0,0,152,24H56A16,16,0,0,0,40,40V216a16,16,0,0,0,16,16H200a16,16,0,0,0,16-16V88A8,8,0,0,0,213.66,82.34ZM160,51.31,188.69,80H160ZM200,216H56V40h88V88a8,8,0,0,0,8,8h48V216Z"/>
          </svg>
        </span>

        <div class="flex-1 min-w-0">
          <p class="text-sm font-barlow truncate text-ubpd-gris">{{ file.nombre }}</p>
          <p class="text-xs text-gray-400">{{ formatSize(file.tamanio) }}</p>
        </div>

        <button
          v-if="!readOnly"
          type="button"
          class="text-gray-400 hover:text-ubpd-naranja transition-colors"
          :aria-label="`Eliminar ${file.nombre}`"
          @click.stop="emit('removed', file.id)"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 256 256" fill="currentColor" aria-hidden="true">
            <path d="M216,48H176V40a24,24,0,0,0-24-24H104A24,24,0,0,0,80,40v8H40a8,8,0,0,0,0,16h8V208a16,16,0,0,0,16,16H192a16,16,0,0,0,16-16V64h8a8,8,0,0,0,0-16ZM96,40a8,8,0,0,1,8-8h48a8,8,0,0,1,8,8v8H96Zm96,168H64V64H192ZM112,104v64a8,8,0,0,1-16,0V104a8,8,0,0,1,16,0Zm48,0v64a8,8,0,0,1-16,0V104a8,8,0,0,1,16,0Z"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Error messages -->
    <p
      v-for="(err, i) in errors"
      :key="i"
      class="text-xs text-ubpd-naranja font-barlow"
      role="alert"
    >
      {{ err }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'
import { useNotificationsStore } from '@/stores/notifications'
import type { FileRecord } from '@/types/forms'

defineOptions({ name: 'FileUploadZone' })

const MAX_SIZE_MB = 50
const ACCEPTED_TYPES = [
  'application/pdf',
  'image/jpeg',
  'image/png',
  'image/jpg',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel',
]

interface PendingFile {
  file: File
  progress: number
}

interface Props {
  formId?: string
  existingFiles?: FileRecord[]
  readOnly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  existingFiles: () => [],
  readOnly: false,
})

const emit = defineEmits<{
  uploaded: [file: FileRecord]
  removed: [fileId: string]
}>()

const { client: axiosInstance } = useApi()
const notifications = useNotificationsStore()

const fileInputRef = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)
const pendingFiles = ref<PendingFile[]>([])
const errors = ref<string[]>([])

function isImage(tipo: string) {
  return tipo.startsWith('image/')
}

function fileIconComponent(_filename: string) {
  // Returns a fallback — actual icon differentiation is inline in template
  return 'span'
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function isAcceptedUpload(file: File): boolean {
  if (file.type && ACCEPTED_TYPES.includes(file.type)) return true
  // Al arrastrar, a veces viene tipo vacío u "application/octet-stream"
  const n = file.name.toLowerCase()
  return /\.(pdf|jpe?g|png|docx|xlsx|xls)$/i.test(n)
}

function validateFile(file: File): string | null {
  if (!isAcceptedUpload(file)) {
    return `${file.name}: tipo no permitido (PDF, JPG, PNG, DOCX, XLS, XLSX)`
  }
  if (file.size > MAX_SIZE_MB * 1024 * 1024) {
    return `${file.name}: supera el límite de ${MAX_SIZE_MB} MB`
  }
  return null
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  const files = Array.from(e.dataTransfer?.files ?? [])
  processFiles(files)
}

function onFileSelected(e: Event) {
  const files = Array.from((e.target as HTMLInputElement).files ?? [])
  processFiles(files)
  if (fileInputRef.value) fileInputRef.value.value = ''
}

function processFiles(files: File[]) {
  errors.value = []
  for (const file of files) {
    const err = validateFile(file)
    if (err) {
      errors.value.push(err)
    } else {
      const pf: PendingFile = { file, progress: 0 }
      pendingFiles.value.push(pf)
      if (props.formId) {
        uploadFile(pf)
      }
    }
  }
}

async function uploadFile(pf: PendingFile) {
  if (!props.formId) return

  const formData = new FormData()
  formData.append('file', pf.file)

  try {
    const response = await axiosInstance.post<FileRecord>(
      `/files/upload/${props.formId}`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          if (e.total) {
            pf.progress = Math.round((e.loaded / e.total) * 100)
          }
        },
      },
    )
    emit('uploaded', response.data)
    const idx = pendingFiles.value.indexOf(pf)
    if (idx !== -1) pendingFiles.value.splice(idx, 1)
  } catch {
    notifications.error('Error al subir archivo', `No se pudo subir ${pf.file.name}`)
    const idx = pendingFiles.value.indexOf(pf)
    if (idx !== -1) pendingFiles.value.splice(idx, 1)
  }
}

function removePending(idx: number) {
  pendingFiles.value.splice(idx, 1)
}

/**
 * Llamado desde el padre cuando un formulario recién creado obtiene su ID.
 * Sube todos los archivos pendientes que quedaron en cola sin formId.
 */
async function triggerUploadAll(newFormId: string) {
  const toUpload = [...pendingFiles.value]
  for (const pf of toUpload) {
    if (pf.progress === 0) {
      // Temporalmente inyectar el formId a la instancia del archivo
      await uploadFileWithId(pf, newFormId)
    }
  }
}

async function uploadFileWithId(pf: PendingFile, targetFormId: string) {
  const formData = new FormData()
  formData.append('file', pf.file)
  try {
    const response = await axiosInstance.post<FileRecord>(
      `/files/upload/${targetFormId}`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          if (e.total) pf.progress = Math.round((e.loaded / e.total) * 100)
        },
      },
    )
    emit('uploaded', response.data)
    const idx = pendingFiles.value.indexOf(pf)
    if (idx !== -1) pendingFiles.value.splice(idx, 1)
  } catch {
    notifications.error('Error al subir archivo', `No se pudo subir ${pf.file.name}`)
    const idx = pendingFiles.value.indexOf(pf)
    if (idx !== -1) pendingFiles.value.splice(idx, 1)
  }
}

defineExpose({ triggerUploadAll })
</script>
