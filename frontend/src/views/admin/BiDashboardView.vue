<template>
  <div class="p-6 space-y-6">
    <!-- Header -->
    <div class="flex items-start justify-between gap-4 flex-wrap">
      <div>
        <h1 class="font-subtitulo font-bold text-2xl text-ubpd-gris">Dashboard BI — Planes Regionales</h1>
        <p class="font-cuerpo text-sm text-gray-500 mt-1">
          Carga el Excel de Metas GITT para actualizar el dashboard público de Planes Regionales de Búsqueda.
        </p>
      </div>
      <RouterLink
        to="/bi"
        target="_blank"
        class="inline-flex items-center gap-2 border border-ubpd-teal text-ubpd-teal font-semibold font-barlow text-sm rounded-xl px-4 py-2 hover:bg-teal-50 transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 256 256" fill="currentColor">
          <path d="M200,64V168a8,8,0,0,1-16,0V83.31L69.66,197.66a8,8,0,0,1-11.32-11.32L172.69,72H88a8,8,0,0,1,0-16H192A8,8,0,0,1,200,64Z"/>
        </svg>
        Ver dashboard público
      </RouterLink>
    </div>

    <!-- Estado actual del dataset -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div class="lg:col-span-2 bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
        <h2 class="font-subtitulo font-semibold text-base text-ubpd-gris mb-3">Estado del dataset</h2>
        <div v-if="loadingStatus" class="grid grid-cols-2 sm:grid-cols-4 gap-3 animate-pulse">
          <div v-for="i in 4" :key="i" class="h-16 bg-gray-100 rounded-xl" />
        </div>
        <div v-else-if="!status?.loaded" class="py-6 text-center">
          <svg class="w-12 h-12 text-gray-300 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p class="font-cuerpo text-sm text-gray-500">No hay datos BI cargados aún.</p>
        </div>
        <div v-else class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div class="bg-gradient-to-br from-ubpd-teal/10 to-ubpd-teal/5 rounded-xl p-4">
            <p class="font-cuerpo text-xs text-ubpd-teal/80 uppercase tracking-wide mb-1">Registros</p>
            <p class="font-subtitulo text-2xl font-bold text-ubpd-teal">{{ status.total_rows }}</p>
          </div>
          <div class="bg-gradient-to-br from-ubpd-verde/10 to-ubpd-verde/5 rounded-xl p-4">
            <p class="font-cuerpo text-xs text-ubpd-verde/80 uppercase tracking-wide mb-1">Planes</p>
            <p class="font-subtitulo text-2xl font-bold text-ubpd-verde">{{ status.total_prb }}</p>
          </div>
          <div class="bg-gradient-to-br from-blue-50 to-blue-100/30 rounded-xl p-4">
            <p class="font-cuerpo text-xs text-blue-700/80 uppercase tracking-wide mb-1">Indicadores</p>
            <p class="font-subtitulo text-2xl font-bold text-blue-700">{{ status.total_indicadores }}</p>
          </div>
          <div class="bg-gradient-to-br from-amber-50 to-amber-100/30 rounded-xl p-4">
            <p class="font-cuerpo text-xs text-amber-700/80 uppercase tracking-wide mb-1">Año</p>
            <p class="font-subtitulo text-2xl font-bold text-amber-700">{{ status.anio ?? '—' }}</p>
          </div>
        </div>
        <div v-if="status?.loaded" class="mt-4 pt-4 border-t border-gray-100 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div>
            <span class="font-cuerpo text-gray-400 block">Archivo</span>
            <span class="font-mono text-ubpd-gris truncate block">{{ status.filename }}</span>
          </div>
          <div>
            <span class="font-cuerpo text-gray-400 block">Cargado por</span>
            <span class="font-cuerpo text-ubpd-gris">{{ status.uploaded_by ?? '—' }}</span>
          </div>
          <div>
            <span class="font-cuerpo text-gray-400 block">Fecha de carga</span>
            <span class="font-cuerpo text-ubpd-gris">{{ formatDate(status.uploaded_at) }}</span>
          </div>
        </div>
      </div>

      <!-- Info estructura requerida -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
        <h2 class="font-subtitulo font-semibold text-base text-ubpd-gris mb-3">Estructura requerida</h2>
        <p class="font-cuerpo text-xs text-gray-500 mb-3">El Excel debe contener 3 hojas:</p>
        <div class="space-y-2">
          <div class="flex items-start gap-2">
            <span class="flex-shrink-0 w-5 h-5 rounded-full bg-ubpd-teal/10 text-ubpd-teal text-xs font-bold font-barlow flex items-center justify-center mt-0.5">1</span>
            <div class="flex-1">
              <p class="font-semibold font-barlow text-xs text-ubpd-gris">PRB</p>
              <p class="font-cuerpo text-xs text-gray-400">COD, PRB, Regional, GITT</p>
            </div>
          </div>
          <div class="flex items-start gap-2">
            <span class="flex-shrink-0 w-5 h-5 rounded-full bg-ubpd-teal/10 text-ubpd-teal text-xs font-bold font-barlow flex items-center justify-center mt-0.5">2</span>
            <div class="flex-1">
              <p class="font-semibold font-barlow text-xs text-ubpd-gris">EstructuraIndicadores</p>
              <p class="font-cuerpo text-xs text-gray-400">Cod_Linea, Linea, Cod_Indicador, Indicador</p>
            </div>
          </div>
          <div class="flex items-start gap-2">
            <span class="flex-shrink-0 w-5 h-5 rounded-full bg-ubpd-teal/10 text-ubpd-teal text-xs font-bold font-barlow flex items-center justify-center mt-0.5">3</span>
            <div class="flex-1">
              <p class="font-semibold font-barlow text-xs text-ubpd-gris">Historico</p>
              <p class="font-cuerpo text-xs text-gray-400">CodPRB, Cod_Indicador, Meta, Mes 1-12, Avance Total, % de Avance, AÑO</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Upload zone -->
    <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
      <h2 class="font-subtitulo font-semibold text-base text-ubpd-gris mb-4">Cargar nuevo Excel</h2>

      <div
        class="border-2 border-dashed rounded-2xl p-10 text-center transition-colors"
        :class="dragging ? 'border-ubpd-teal bg-teal-50/30' : 'border-gray-200 hover:border-ubpd-teal/40 hover:bg-gray-50/50'"
        @dragover.prevent="dragging = true"
        @dragleave.prevent="dragging = false"
        @drop.prevent="onDrop"
      >
        <svg class="w-14 h-14 text-gray-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 0115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <p class="font-barlow text-base text-ubpd-gris mb-1">Arrastra el archivo Excel aquí</p>
        <p class="font-cuerpo text-xs text-gray-400 mb-4">o selecciónalo desde tu equipo (.xlsx)</p>

        <label
          class="inline-flex items-center gap-2 bg-ubpd-teal text-white font-semibold font-barlow text-sm rounded-xl px-5 py-2.5 hover:bg-teal-700 transition-colors cursor-pointer"
          :class="uploading ? 'opacity-60 pointer-events-none' : ''"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 256 256" fill="currentColor">
            <path d="M213.66,82.34l-56-56A8,8,0,0,0,152,24H56A16,16,0,0,0,40,40V216a16,16,0,0,0,16,16H200a16,16,0,0,0,16-16V88A8,8,0,0,0,213.66,82.34ZM160,51.31,188.69,80H160ZM200,216H56V40h88V88a8,8,0,0,0,8,8h48V216Z"/>
          </svg>
          {{ uploading ? 'Procesando...' : 'Seleccionar archivo' }}
          <input type="file" accept=".xlsx,.xls" class="hidden" @change="onFileSelected" :disabled="uploading" />
        </label>

        <div v-if="selectedFile" class="mt-5 inline-flex items-center gap-3 bg-gray-50 rounded-xl px-4 py-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 256 256" fill="currentColor" class="text-ubpd-verde">
            <path d="M213.66,82.34l-56-56A8,8,0,0,0,152,24H56A16,16,0,0,0,40,40V216a16,16,0,0,0,16,16H200a16,16,0,0,0,16-16V88A8,8,0,0,0,213.66,82.34ZM160,51.31,188.69,80H160Z"/>
          </svg>
          <span class="font-cuerpo text-sm text-ubpd-gris">{{ selectedFile.name }}</span>
          <span class="font-cuerpo text-xs text-gray-400">({{ formatSize(selectedFile.size) }})</span>
        </div>
      </div>

      <div v-if="selectedFile" class="mt-4 flex items-center justify-between gap-3 flex-wrap">
        <p class="font-cuerpo text-xs text-amber-700 flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 256 256" fill="currentColor"><path d="M236.8,188.09,149.35,36.22a24.76,24.76,0,0,0-42.7,0L19.2,188.09a23.51,23.51,0,0,0,0,23.72A24.35,24.35,0,0,0,40.55,224h174.9a24.35,24.35,0,0,0,21.33-12.19A23.51,23.51,0,0,0,236.8,188.09ZM120,104a8,8,0,0,1,16,0v40a8,8,0,0,1-16,0Zm8,88a12,12,0,1,1,12-12A12,12,0,0,1,128,192Z"/></svg>
          Cargar un nuevo Excel reemplaza todos los datos BI actuales.
        </p>
        <div class="flex gap-2">
          <button
            type="button"
            class="px-4 py-2 border border-gray-300 text-gray-600 font-semibold font-barlow text-sm rounded-lg hover:bg-gray-50 transition-colors"
            @click="selectedFile = null"
            :disabled="uploading"
          >
            Cancelar
          </button>
          <button
            type="button"
            class="px-5 py-2 bg-ubpd-verde text-white font-semibold font-barlow text-sm rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
            :disabled="uploading"
            @click="uploadFile"
          >
            {{ uploading ? 'Cargando...' : 'Cargar y procesar' }}
          </button>
        </div>
      </div>

      <!-- Resultado de upload -->
      <div v-if="lastResult" class="mt-5 bg-gradient-to-br from-ubpd-verde/10 to-transparent border border-ubpd-verde/20 rounded-xl p-4">
        <p class="font-semibold font-barlow text-sm text-ubpd-verde mb-2 flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 256 256" fill="currentColor"><path d="M229.66,77.66l-128,128a8,8,0,0,1-11.32,0l-56-56a8,8,0,0,1,11.32-11.32L96,188.69,218.34,66.34a8,8,0,0,1,11.32,11.32Z"/></svg>
          Carga exitosa
        </p>
        <p class="font-cuerpo text-xs text-gray-600">{{ lastResult.mensaje }}</p>
      </div>
    </div>

    <!-- Acción peligrosa -->
    <div v-if="status?.loaded" class="bg-white rounded-2xl border border-red-100 shadow-sm p-5">
      <div class="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h3 class="font-subtitulo font-semibold text-sm text-red-700">Limpiar todos los datos BI</h3>
          <p class="font-cuerpo text-xs text-gray-500 mt-0.5">Elimina todos los datos del dashboard BI. Esta acción no se puede deshacer.</p>
        </div>
        <button
          type="button"
          class="px-4 py-2 border border-red-300 text-red-600 font-semibold font-barlow text-sm rounded-lg hover:bg-red-50 transition-colors"
          @click="clearAll"
        >
          Limpiar datos
        </button>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useNotificationsStore } from '@/stores/notifications'

interface BiStatus {
  loaded: boolean
  filename?: string
  uploaded_by?: string
  uploaded_at?: string
  total_rows?: number
  total_prb?: number
  total_indicadores?: number
  anio?: number
}

const { get, postForm, del } = useApi()
const notifications = useNotificationsStore()

const status = ref<BiStatus | null>(null)
const loadingStatus = ref(true)
const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const dragging = ref(false)
const lastResult = ref<any>(null)

async function loadStatus() {
  loadingStatus.value = true
  try {
    status.value = await get<BiStatus>('/admin/bi/status')
  } catch {
    status.value = { loaded: false }
  } finally {
    loadingStatus.value = false
  }
}

function onFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  const f = input.files?.[0]
  if (f) selectedFile.value = f
}

function onDrop(e: DragEvent) {
  dragging.value = false
  const f = e.dataTransfer?.files?.[0]
  if (f && /\.(xlsx|xls)$/i.test(f.name)) {
    selectedFile.value = f
  } else {
    notifications.warning('Archivo inválido', 'Debe ser un archivo .xlsx o .xls')
  }
}

async function uploadFile() {
  if (!selectedFile.value) return
  uploading.value = true
  lastResult.value = null
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    const result = await postForm<any>('/admin/bi/upload', formData)
    lastResult.value = result
    notifications.success('Carga exitosa', result.mensaje || 'Datos BI actualizados.')
    selectedFile.value = null
    await loadStatus()
  } catch (err: any) {
    const detail = err?.response?.data?.detail || 'No se pudo cargar el Excel.'
    notifications.error('Error', typeof detail === 'string' ? detail : JSON.stringify(detail))
  } finally {
    uploading.value = false
  }
}

async function clearAll() {
  if (!confirm('¿Eliminar TODOS los datos BI? Esta acción no se puede deshacer.')) return
  try {
    await del('/admin/bi')
    notifications.success('Eliminado', 'Datos BI eliminados.')
    lastResult.value = null
    await loadStatus()
  } catch {
    notifications.error('Error', 'No se pudieron eliminar los datos BI.')
  }
}

function formatDate(iso?: string) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('es-CO', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

onMounted(loadStatus)
</script>
