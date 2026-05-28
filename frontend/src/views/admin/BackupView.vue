<template>
  <div class="p-6 space-y-6 max-w-5xl">
    <!-- Encabezado -->
    <div>
      <h1 class="font-subtitulo font-bold text-2xl text-ubpd-gris">Backup &amp; Restauración</h1>
      <p class="font-cuerpo text-sm text-gray-500 mt-1">
        Descarga toda la base (templates + formularios + adjuntos) en un único ZIP,
        restáurala desde un ZIP, o limpia la base por completo. <span class="text-ubpd-naranja font-semibold">Cada acción requiere confirmación.</span>
      </p>
    </div>

    <!-- Tarjeta 1: Exportar -->
    <section class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
      <div class="flex items-start gap-4">
        <div class="w-12 h-12 rounded-xl bg-ubpd-teal/10 flex items-center justify-center shrink-0">
          <svg class="w-6 h-6 text-ubpd-teal" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5 5-5M12 15V3" />
          </svg>
        </div>
        <div class="flex-1">
          <h2 class="font-subtitulo font-semibold text-lg text-ubpd-gris">1 · Descargar backup completo</h2>
          <p class="font-cuerpo text-sm text-gray-500 mt-1">
            Genera un archivo <code class="text-xs bg-gray-100 px-1.5 rounded">ubpd_backup_*.zip</code> con
            todos los templates, todos los formularios respondidos (cualquier estado) y todos los adjuntos
            almacenados en MinIO. Sirve como respaldo y permite restaurar en otra instalación.
          </p>
          <button
            @click="confirmExport"
            :disabled="exporting"
            class="mt-4 inline-flex items-center gap-2 bg-ubpd-teal text-white font-cuerpo font-semibold
                   text-sm rounded-xl px-5 py-2.5 hover:bg-[#346d7a] disabled:opacity-60 transition"
          >
            <span v-if="exporting" class="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5 5-5M12 15V3" />
            </svg>
            {{ exporting ? 'Generando ZIP...' : 'Descargar backup ZIP' }}
          </button>
        </div>
      </div>
    </section>

    <!-- Tarjeta 2: Importar -->
    <section class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
      <div class="flex items-start gap-4">
        <div class="w-12 h-12 rounded-xl bg-ubpd-verde/10 flex items-center justify-center shrink-0">
          <svg class="w-6 h-6 text-ubpd-verde" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M17 8l-5-5-5 5M12 3v12" />
          </svg>
        </div>
        <div class="flex-1">
          <h2 class="font-subtitulo font-semibold text-lg text-ubpd-gris">2 · Restaurar desde un backup</h2>
          <p class="font-cuerpo text-sm text-gray-500 mt-1">
            Selecciona un <code class="text-xs bg-gray-100 px-1.5 rounded">ubpd_backup_*.zip</code> previamente
            generado. Por defecto se hace <strong>upsert</strong> (se crean los que faltan y se actualizan los que ya existen
            por id). Marca <em>Reemplazar</em> para borrar la base actual antes de cargar.
          </p>

          <label class="mt-3 flex items-center gap-2 cursor-pointer select-none">
            <input v-model="importReplace" type="checkbox" class="rounded border-gray-300 text-ubpd-naranja focus:ring-ubpd-naranja" />
            <span class="font-cuerpo text-sm text-gray-700">
              Reemplazar (borra templates+forms+archivos antes de importar)
            </span>
          </label>

          <div class="mt-4 flex items-center gap-3">
            <label
              :class="[
                'inline-flex items-center gap-2 font-cuerpo font-semibold text-sm rounded-xl px-5 py-2.5 transition cursor-pointer',
                importing
                  ? 'opacity-50 cursor-not-allowed bg-gray-100 text-gray-400'
                  : 'bg-white border border-gray-200 text-ubpd-gris hover:border-ubpd-verde hover:text-ubpd-verde',
              ]"
            >
              <svg v-if="!importing" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M17 8l-5-5-5 5M12 3v12" />
              </svg>
              <span v-else class="inline-block w-4 h-4 border-2 border-ubpd-gris border-t-transparent rounded-full animate-spin" />
              {{ importing ? 'Restaurando...' : 'Seleccionar archivo ZIP' }}
              <input
                ref="fileInput"
                type="file"
                accept=".zip,application/zip,application/x-zip-compressed"
                class="hidden"
                :disabled="importing"
                @change="onFileSelected"
              />
            </label>
          </div>

          <!-- Resultado del último import -->
          <div v-if="lastImportResult" class="mt-4 p-4 bg-gray-50 rounded-xl border border-gray-100 text-sm font-cuerpo space-y-1">
            <p><strong>Templates:</strong> {{ lastImportResult.templates.creados }} creados, {{ lastImportResult.templates.actualizados }} actualizados</p>
            <p><strong>Formularios:</strong> {{ lastImportResult.forms.creados }} creados, {{ lastImportResult.forms.actualizados }} actualizados, {{ lastImportResult.forms.omitidos }} omitidos</p>
            <p><strong>Archivos:</strong> {{ lastImportResult.archivos.creados }} creados, {{ lastImportResult.archivos.actualizados }} actualizados, {{ lastImportResult.archivos.minio_ok }} subidos a MinIO ({{ lastImportResult.archivos.minio_fail }} fallidos)</p>
            <p v-if="lastImportResult.replace" class="text-ubpd-naranja">
              <strong>Reemplazo activo:</strong> se borraron antes
              {{ lastImportResult.borrados_previos.forms }} forms,
              {{ lastImportResult.borrados_previos.archivos }} archivos,
              {{ lastImportResult.borrados_previos.templates }} templates.
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Tarjeta 3: Wipe -->
    <section class="bg-white rounded-2xl border-2 border-red-200 shadow-sm p-6">
      <div class="flex items-start gap-4">
        <div class="w-12 h-12 rounded-xl bg-red-100 flex items-center justify-center shrink-0">
          <svg class="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div class="flex-1">
          <h2 class="font-subtitulo font-semibold text-lg text-red-700">3 · Zona peligrosa — Limpiar base de datos</h2>
          <p class="font-cuerpo text-sm text-gray-600 mt-1">
            Elimina todos los formularios respondidos y sus adjuntos en MinIO.
            Opcionalmente también borra todos los templates. <strong class="text-red-700">Esta acción no se puede deshacer.</strong>
            Te recomendamos descargar el backup antes.
          </p>

          <label class="mt-3 flex items-center gap-2 cursor-pointer select-none">
            <input v-model="wipeIncludeTemplates" type="checkbox" class="rounded border-gray-300 text-red-600 focus:ring-red-500" />
            <span class="font-cuerpo text-sm text-gray-700">
              También borrar templates (no solo los registros)
            </span>
          </label>

          <div class="mt-4">
            <label class="block font-cuerpo text-xs font-medium text-gray-500 mb-1">
              Para habilitar el botón, escribe exactamente: <code class="text-red-700">{{ WIPE_TOKEN }}</code>
            </label>
            <input
              v-model="wipeToken"
              type="text"
              placeholder="Escribe el texto de confirmación..."
              class="w-full max-w-sm font-mono text-sm border border-gray-300 rounded-lg px-3 py-2
                     focus:outline-none focus:border-red-500 focus:ring-2 focus:ring-red-200 transition"
            />
          </div>

          <button
            @click="confirmWipe"
            :disabled="wiping || wipeToken !== WIPE_TOKEN"
            class="mt-4 inline-flex items-center gap-2 bg-red-600 text-white font-cuerpo font-semibold
                   text-sm rounded-xl px-5 py-2.5 hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            <span v-if="wiping" class="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6M1 7h22M9 7V4a1 1 0 011-1h4a1 1 0 011 1v3" />
            </svg>
            {{ wiping ? 'Borrando...' : (wipeIncludeTemplates ? 'BORRAR TODA LA BASE (templates + registros)' : 'BORRAR todos los registros') }}
          </button>

          <div v-if="lastWipeResult" class="mt-4 p-4 bg-red-50 rounded-xl border border-red-200 text-sm font-cuerpo space-y-1 text-red-900">
            <p><strong>Eliminados:</strong>
              {{ lastWipeResult.deleted_forms }} formularios,
              {{ lastWipeResult.deleted_archivos }} archivos,
              {{ lastWipeResult.deleted_templates }} templates.</p>
            <p>MinIO: {{ lastWipeResult.minio_ok }} OK, {{ lastWipeResult.minio_fail }} con fallo.</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useApi } from '@/composables/useApi'
import apiClient from '@/composables/useApi'
import { useNotificationsStore } from '@/stores/notifications'

interface ImportResult {
  ok: boolean
  replace: boolean
  templates: { creados: number; actualizados: number }
  forms: { creados: number; actualizados: number; omitidos: number }
  archivos: {
    creados: number; actualizados: number; omitidos: number
    minio_ok: number; minio_fail: number
  }
  borrados_previos: { forms: number; archivos: number; templates: number }
}

interface WipeResult {
  ok: boolean
  deleted_forms: number
  deleted_archivos: number
  deleted_templates: number
  minio_ok: number
  minio_fail: number
}

const WIPE_TOKEN = 'BORRAR TODO'

const { post } = useApi()
const notifications = useNotificationsStore()

const exporting = ref(false)
const importing = ref(false)
const wiping = ref(false)

const importReplace = ref(false)
const wipeIncludeTemplates = ref(false)
const wipeToken = ref('')
const fileInput = ref<HTMLInputElement | null>(null)

const lastImportResult = ref<ImportResult | null>(null)
const lastWipeResult = ref<WipeResult | null>(null)

function confirmExport() {
  if (!window.confirm(
    'Se generará un ZIP con TODOS los templates, formularios y adjuntos. ' +
    'Puede tardar varios segundos.\n\n¿Continuar?',
  )) return
  exportBackup()
}

async function exportBackup() {
  exporting.value = true
  try {
    const res = await apiClient.get('/admin/backup/export-zip', { responseType: 'blob' })
    const blob = res.data as Blob
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const cd = (res.headers['content-disposition'] || '') as string
    const match = cd.match(/filename="?([^";]+)"?/i)
    const ts = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14)
    a.download = match?.[1] || `ubpd_backup_${ts}.zip`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
    const tCount = res.headers['x-backup-templates']
    const fCount = res.headers['x-backup-forms']
    const aCount = res.headers['x-backup-archivos-ok']
    notifications.success(
      'Backup descargado',
      `Incluye ${tCount} templates, ${fCount} formularios y ${aCount} archivos.`,
    )
  } catch (err) {
    notifications.error('No se pudo generar el backup', String(err))
  } finally {
    exporting.value = false
  }
}

async function onFileSelected(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  target.value = ''  // permite re-seleccionar el mismo archivo

  const mode = importReplace.value
    ? 'REEMPLAZAR (se borrará la base actual antes de cargar)'
    : 'UPSERT (solo crear/actualizar)'

  if (!window.confirm(
    `Vas a restaurar desde "${file.name}".\n\n` +
    `Modo: ${mode}\n\n` +
    (importReplace.value
      ? 'Esta acción ELIMINARÁ todos los templates, formularios y adjuntos actuales antes de cargar el ZIP. NO se puede deshacer.\n\n'
      : '') +
    '¿Continuar?',
  )) return

  importing.value = true
  try {
    const fd = new FormData()
    fd.append('file', file)
    // No fijamos Content-Type: axios añade el boundary multipart automáticamente.
    // Timeout amplio porque un backup con adjuntos puede tardar.
    const res = await apiClient.post(
      `/admin/backup/import-zip?replace=${importReplace.value ? 'true' : 'false'}`,
      fd,
      { timeout: 600_000 },
    )
    const result = res.data as ImportResult
    lastImportResult.value = result
    notifications.success(
      'Restauración completada',
      `${result.templates.creados + result.templates.actualizados} templates · ` +
      `${result.forms.creados + result.forms.actualizados} forms · ` +
      `${result.archivos.minio_ok} archivos a MinIO`,
    )
  } catch (err: any) {
    const msg = err?.response?.data?.detail || err?.message || 'Error desconocido'
    notifications.error('No se pudo restaurar el backup', String(msg))
  } finally {
    importing.value = false
  }
}

function confirmWipe() {
  if (wipeToken.value !== WIPE_TOKEN) return
  const subject = wipeIncludeTemplates.value
    ? 'TODOS los templates + TODOS los formularios + TODOS los adjuntos'
    : 'TODOS los formularios + TODOS los adjuntos (los templates se conservan)'
  if (!window.confirm(
    `¿SEGURO que quieres eliminar ${subject}?\n\n` +
    'Esta acción NO se puede deshacer.\n' +
    'Te recomendamos descargar el backup antes.',
  )) return
  if (!window.confirm('Última confirmación. Pulsa OK para BORRAR.')) return
  runWipe()
}

async function runWipe() {
  wiping.value = true
  try {
    const result = await post<WipeResult>('/admin/backup/wipe', {
      confirm_token: WIPE_TOKEN,
      include_templates: wipeIncludeTemplates.value,
    })
    lastWipeResult.value = result
    wipeToken.value = ''
    wipeIncludeTemplates.value = false
    notifications.success(
      'Base limpiada',
      `${result.deleted_forms} forms, ${result.deleted_archivos} archivos, ${result.deleted_templates} templates eliminados.`,
    )
  } catch (err: any) {
    const msg = err?.response?.data?.detail || err?.message || 'Error desconocido'
    notifications.error('No se pudo limpiar la base', String(msg))
  } finally {
    wiping.value = false
  }
}
</script>
