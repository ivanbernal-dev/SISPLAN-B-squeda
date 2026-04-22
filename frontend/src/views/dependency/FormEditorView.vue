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
        <div class="flex items-center gap-3">
          <StatusBadge v-if="formData?.estado" :status="formData.estado" />
          <!-- Mode toggle: only for new forms -->
          <div v-if="!formId" class="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
            <button
              type="button"
              class="px-3 py-1.5 text-xs font-semibold font-barlow rounded-md transition-all"
              :class="inputMode === 'form' ? 'bg-white text-ubpd-gris shadow-sm' : 'text-gray-500'"
              @click="inputMode = 'form'"
            >
              Formulario
            </button>
            <button
              type="button"
              class="px-3 py-1.5 text-xs font-semibold font-barlow rounded-md transition-all"
              :class="inputMode === 'excel' ? 'bg-white text-ubpd-gris shadow-sm' : 'text-gray-500'"
              @click="inputMode = 'excel'"
            >
              Cargar Excel
            </button>
          </div>
        </div>
      </div>

      <!-- Excel upload mode -->
      <div v-if="inputMode === 'excel'" class="space-y-4">
        <div class="bg-blue-50 border border-blue-200 rounded-xl p-4 space-y-3">
          <div class="flex items-center justify-between gap-3 flex-wrap">
            <div>
              <h3 class="text-sm font-semibold font-montserrat text-blue-800">Carga masiva via Excel</h3>
              <p class="text-xs font-barlow text-blue-600 mt-0.5">Descarga el archivo de ejemplo, rellénalo y súbelo para crear múltiples formularios.</p>
            </div>
            <button
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2 bg-blue-700 text-white font-semibold font-barlow text-sm rounded-lg hover:bg-blue-800 transition-colors"
              :disabled="downloadingExample"
              @click="downloadExcelExample"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 256 256" fill="currentColor"><path d="M224,152v56a16,16,0,0,1-16,16H48a16,16,0,0,1-16-16V152a8,8,0,0,1,16,0v56H208V152a8,8,0,0,1,16,0Zm-101.66,5.66a8,8,0,0,0,11.32,0l40-40a8,8,0,0,0-11.32-11.32L136,132.69V40a8,8,0,0,0-16,0v92.69L93.66,106.34a8,8,0,0,0-11.32,11.32Z"/></svg>
              {{ downloadingExample ? 'Descargando...' : 'Descargar Ejemplo' }}
            </button>
          </div>

          <!-- File picker Excel -->
          <div
            class="border-2 border-dashed border-blue-300 rounded-xl p-6 text-center cursor-pointer hover:bg-blue-100 transition-colors"
            @click="triggerExcelInput"
            @dragover.prevent
            @drop.prevent="onExcelDrop"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 256 256" fill="currentColor" class="mx-auto text-blue-400 mb-2">
              <path d="M213.66,82.34l-56-56A8,8,0,0,0,152,24H56A16,16,0,0,0,40,40V216a16,16,0,0,0,16,16H200a16,16,0,0,0,16-16V88A8,8,0,0,0,213.66,82.34ZM160,51.31,188.69,80H160ZM200,216H56V40h88V88a8,8,0,0,0,8,8h48V216Z"/>
            </svg>
            <p class="text-sm font-barlow text-blue-700">
              {{ excelFile ? excelFile.name : 'Arrastra un archivo .xlsx aquí o haz click para seleccionar' }}
            </p>
            <input ref="excelInputRef" type="file" accept=".xlsx,.xls" class="hidden" @change="onExcelFileSelected" />
          </div>

          <!-- File picker ZIP opcional -->
          <div
            class="border-2 border-dashed border-teal-300 rounded-xl p-5 text-center cursor-pointer hover:bg-teal-50 transition-colors"
            @click="triggerZipInput"
            @dragover.prevent
            @drop.prevent="onZipDrop"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" class="mx-auto text-teal-500 mb-2">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
            <p class="text-sm font-barlow text-teal-700">
              <strong>ZIP con adjuntos (opcional):</strong>
              {{ zipFile ? zipFile.name : 'Arrastra un .zip con las evidencias' }}
            </p>
            <input ref="zipInputRef" type="file" accept=".zip" class="hidden" @change="onZipFileSelected" />
            <button
              v-if="zipFile"
              type="button"
              class="mt-2 text-xs text-red-600 hover:underline font-barlow"
              @click.stop="zipFile = null"
            >
              Quitar ZIP
            </button>
          </div>

          <!-- Ayuda: convención del ZIP -->
          <div class="bg-teal-50/70 border border-teal-200 rounded-xl px-4 py-3 text-xs font-barlow text-teal-800 space-y-1.5">
            <p class="font-semibold">📁 Cómo organizar el ZIP</p>
            <p>
              Cada carpeta se llama con el <strong>número de fila</strong> del Excel
              (la primera fila de datos es la 1):
            </p>
            <pre class="bg-white/80 border border-teal-100 rounded px-2 py-1 text-[11px] leading-relaxed overflow-x-auto">formularios/1/documento.pdf
formularios/1/foto.jpg
formularios/3/informe.pdf</pre>
            <p>
              <strong>Si una fila no tiene archivos adjuntos, simplemente omite la carpeta</strong>
              (no la dejes vacía). El sistema salta ese número y continúa.
            </p>
            <p class="text-teal-700/80">
              💡 También puedes subir el mismo ZIP que se descarga desde
              administración — usa la misma convención.
            </p>
          </div>

          <!-- Preview table -->
          <div v-if="excelPreviewRows.length > 0" class="overflow-x-auto rounded-lg border border-blue-200">
            <table class="w-full text-xs font-barlow">
              <thead>
                <tr class="bg-blue-100">
                  <th v-for="col in excelPreviewHeaders" :key="col" class="px-3 py-2 text-left text-blue-800 font-semibold whitespace-nowrap">{{ col }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in excelPreviewRows.slice(0, 5)" :key="i" class="border-t border-blue-100">
                  <td v-for="col in excelPreviewHeaders" :key="col" class="px-3 py-2 text-gray-600 whitespace-nowrap max-w-32 truncate">{{ row[col] ?? '' }}</td>
                </tr>
              </tbody>
            </table>
            <div v-if="excelPreviewRows.length > 5" class="px-3 py-2 text-xs text-blue-600 font-barlow bg-blue-50">
              ... y {{ excelPreviewRows.length - 5 }} filas más ({{ excelPreviewRows.length }} total)
            </div>
          </div>

          <!-- Upload button -->
          <button
            v-if="excelFile"
            type="button"
            class="w-full py-2.5 bg-ubpd-teal text-white font-semibold font-barlow text-sm rounded-lg hover:bg-teal-700 transition-colors disabled:opacity-50"
            :disabled="uploadingExcel"
            @click="uploadExcel"
          >
            <span v-if="uploadingExcel" class="flex items-center justify-center gap-2">
              <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
              Validando y subiendo...
            </span>
            <span v-else>Subir {{ excelPreviewRows.length }} formulario(s)</span>
          </button>

          <!-- Panel de errores de validación por fila -->
          <div v-if="excelErrors.length > 0" class="rounded-xl border border-red-200 bg-red-50 overflow-hidden">
            <div class="flex items-center gap-2 px-4 py-3 bg-red-100 border-b border-red-200">
              <svg class="w-4 h-4 text-red-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
              </svg>
              <p class="font-barlow text-sm font-semibold text-red-700">
                Se encontraron errores en {{ excelErrors.length }} fila(s) — corrígelos en el archivo y vuelve a cargarlo
              </p>
            </div>
            <div class="divide-y divide-red-100 max-h-64 overflow-y-auto">
              <div
                v-for="rowErr in excelErrors"
                :key="rowErr.fila"
                class="px-4 py-3"
              >
                <p class="font-barlow text-xs font-bold text-red-600 mb-1">
                  Fila {{ rowErr.fila }} del archivo Excel:
                </p>
                <ul class="space-y-0.5">
                  <li
                    v-for="(err, i) in rowErr.errores"
                    :key="i"
                    class="font-barlow text-xs text-red-700 flex items-start gap-1.5"
                  >
                    <span class="mt-0.5 w-1 h-1 rounded-full bg-red-400 flex-shrink-0 mt-1.5" />
                    {{ err }}
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Form fill mode content -->
      <template v-if="inputMode === 'form'">

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
          v-autoresize
          v-model="informeCualitativo"
          :disabled="isReadOnly"
          placeholder="Describa los hallazgos, procesos y resultados de la búsqueda de manera cualitativa..."
          class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-barlow min-h-[120px] focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-teal-100"
          :class="isReadOnly ? 'bg-gray-50 cursor-not-allowed' : 'bg-white'"
        />
      </div>

      <!-- File upload -->
      <div class="bg-white border border-gray-200 rounded-xl p-5 space-y-2">
        <h2 class="text-base font-semibold font-montserrat text-ubpd-gris">Soportes y archivos adjuntos</h2>
        <FileUploadZone
          ref="fileUploadZoneRef"
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
      <!-- End form fill mode content -->

    </template>

    <!-- ── Modal de errores de validación (Excel + ZIP) ─────────────────────── -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="validationModalOpen"
          class="fixed inset-0 z-50 flex items-center justify-center p-4"
          @click.self="validationModalOpen = false"
        >
          <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="validationModalOpen = false" />

          <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col z-10">
            <!-- Header rojo -->
            <div class="flex items-start justify-between gap-4 px-6 py-4 bg-red-50 border-b border-red-200 rounded-t-2xl">
              <div class="flex items-start gap-3">
                <div class="flex-shrink-0 w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                  <svg class="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div>
                  <h2 class="font-subtitulo font-bold text-lg text-red-700">
                    Carga rechazada — se encontraron errores de validación
                  </h2>
                  <p class="font-barlow text-xs text-red-600/80 mt-1">
                    <strong>No se creó ningún registro.</strong>
                    Corrige los errores en el Excel y/o en el ZIP y vuelve a intentarlo.
                  </p>
                </div>
              </div>
              <button
                class="text-red-400 hover:text-red-600 transition"
                @click="validationModalOpen = false"
              >
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <!-- Contenido scrollable -->
            <div class="overflow-y-auto flex-1 px-6 py-5 space-y-5">

              <!-- Estructura general -->
              <section v-if="estructuraErrors.length">
                <h3 class="font-cuerpo font-semibold text-sm text-red-700 mb-2 flex items-center gap-2">
                  <span class="w-5 h-5 bg-red-600 text-white text-[10px] rounded-full flex items-center justify-center font-bold">!</span>
                  Problemas generales ({{ estructuraErrors.length }})
                </h3>
                <ul class="space-y-1 text-sm font-barlow text-red-700 ml-2">
                  <li v-for="(e, i) in estructuraErrors" :key="`est-${i}`" class="flex items-start gap-2">
                    <span class="mt-1.5 w-1 h-1 rounded-full bg-red-400 flex-shrink-0" />
                    <span>{{ e }}</span>
                  </li>
                </ul>
              </section>

              <!-- Errores del ZIP -->
              <section v-if="zipErrors.length">
                <h3 class="font-cuerpo font-semibold text-sm text-teal-700 mb-2 flex items-center gap-2">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                  </svg>
                  Problemas en el ZIP ({{ zipErrors.length }})
                </h3>
                <ul class="space-y-1.5 text-sm font-barlow text-gray-700 ml-2">
                  <li v-for="(e, i) in zipErrors" :key="`zip-${i}`" class="flex items-start gap-2 bg-teal-50 rounded p-2">
                    <span class="mt-1 text-teal-600 flex-shrink-0">📁</span>
                    <span>{{ e }}</span>
                  </li>
                </ul>
                <div class="mt-2 text-xs text-gray-500 font-barlow bg-gray-50 border border-gray-200 rounded p-2">
                  <strong>Recordatorio:</strong> cada carpeta debe llamarse con el número de fila del Excel
                  (<code class="bg-white px-1 rounded">formularios/1/</code>,
                  <code class="bg-white px-1 rounded">formularios/2/</code>…).
                  Las filas sin archivos adjuntos <strong>no</strong> necesitan carpeta (se saltan).
                </div>
              </section>

              <!-- Errores por fila del Excel -->
              <section v-if="excelErrors.length">
                <h3 class="font-cuerpo font-semibold text-sm text-orange-700 mb-2 flex items-center gap-2">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M9 17v-4a2 2 0 012-2h2a2 2 0 012 2v4M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  Problemas en el Excel — {{ excelErrors.length }} fila(s) con errores
                </h3>
                <div class="space-y-2">
                  <div
                    v-for="rowErr in excelErrors"
                    :key="`xl-${rowErr.fila}`"
                    class="border border-orange-200 bg-orange-50 rounded-lg p-3"
                  >
                    <p class="font-barlow text-xs font-bold text-orange-700 mb-1.5">
                      Fila {{ rowErr.fila }}
                    </p>
                    <ul class="space-y-0.5">
                      <li
                        v-for="(err, i) in rowErr.errores"
                        :key="i"
                        class="font-barlow text-xs text-orange-800 flex items-start gap-1.5"
                      >
                        <span class="mt-0.5 w-1 h-1 rounded-full bg-orange-400 flex-shrink-0 mt-1.5" />
                        <span>{{ err }}</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </section>

            </div>

            <!-- Footer -->
            <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-end gap-2 bg-gray-50 rounded-b-2xl">
              <button
                @click="validationModalOpen = false"
                class="px-4 py-2 font-barlow text-sm font-medium bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
              >
                Entendido, corregiré el archivo
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useNotificationsStore } from '@/stores/notifications'
import type { FormData, FormSchema, FieldConfig, FileRecord } from '@/types/forms'
import DynamicFormRenderer from '@/components/forms/DynamicFormRenderer.vue'
import FileUploadZone from '@/components/forms/FileUploadZone.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'

// Ref al componente FileUploadZone para poder llamar triggerUploadAll
const fileUploadZoneRef = ref<InstanceType<typeof FileUploadZone> | null>(null)

interface Template {
  id: string
  nombre: string
  descripcion: string | null
  configuracion_campos: FormSchema
}

const route = useRoute()
const router = useRouter()
const { get, post, patch } = useApi()
const notifications = useNotificationsStore()

// Route params — la ruta define :templateId (camelCase) y :id
const templateId = computed(() =>
  (route.params.templateId ?? route.params.template_id ?? '') as string
)
const formId = ref<string | null>((route.params.id as string) || null)

// Excel mode
const inputMode = ref<'form' | 'excel'>('form')
const excelFile = ref<File | null>(null)
const zipFile = ref<File | null>(null)
const excelPreviewHeaders = ref<string[]>([])
const excelPreviewRows = ref<Record<string, unknown>[]>([])
const downloadingExample = ref(false)
const uploadingExcel = ref(false)
const excelInputRef = ref<HTMLInputElement | null>(null)
const zipInputRef = ref<HTMLInputElement | null>(null)

interface ExcelRowError {
  fila: number
  errores: string[]
}
const excelErrors = ref<ExcelRowError[]>([])
const zipErrors = ref<string[]>([])
const estructuraErrors = ref<string[]>([])
const validationModalOpen = ref(false)

function triggerExcelInput() {
  excelInputRef.value?.click()
}

function onExcelDrop(event: DragEvent) {
  const file = event.dataTransfer?.files?.[0]
  if (file) handleExcelFile(file)
}

function onExcelFileSelected(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) handleExcelFile(file)
}

function triggerZipInput() {
  zipInputRef.value?.click()
}

function onZipDrop(event: DragEvent) {
  const file = event.dataTransfer?.files?.[0]
  if (file && /\.zip$/i.test(file.name)) zipFile.value = file
  else notifications.warning('Archivo inválido', 'Debe ser un archivo .zip')
}

function onZipFileSelected(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) zipFile.value = file
}

async function handleExcelFile(file: File) {
  excelFile.value = file
  excelPreviewHeaders.value = []
  excelPreviewRows.value = []
  excelErrors.value = []

  try {
    // Use the xlsx library that's already in dependencies
    const XLSX = await import('xlsx')
    const buffer = await file.arrayBuffer()
    const wb = XLSX.read(buffer, { type: 'array' })
    const ws = wb.Sheets[wb.SheetNames[0]]
    const rawData = XLSX.utils.sheet_to_json<Record<string, unknown>>(ws, { header: 1 })

    if (rawData.length < 1) return
    const headers = (rawData[0] as unknown[]).map((h) => String(h ?? ''))
    excelPreviewHeaders.value = headers

    const rows = rawData.slice(1).map((row) => {
      const obj: Record<string, unknown> = {}
      ;(row as unknown[]).forEach((cell, i) => {
        obj[headers[i]] = cell
      })
      return obj
    })
    excelPreviewRows.value = rows.filter((r) => Object.values(r).some((v) => v !== undefined && v !== ''))
  } catch {
    notifications.error('Error', 'No se pudo leer el archivo Excel.')
  }
}

async function downloadExcelExample() {
  if (!templateId.value) return
  downloadingExample.value = true
  try {
    const apiUrl = import.meta.env.VITE_API_URL || '/api'
    const token = localStorage.getItem('ubpd_access_token')
    const response = await fetch(`${apiUrl}/templates/${templateId.value}/excel-example`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!response.ok) throw new Error('Error descargando')
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ejemplo_${templateId.value}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    notifications.error('Error', 'No se pudo descargar el ejemplo.')
  } finally {
    downloadingExample.value = false
  }
}

async function uploadExcel() {
  if (!excelFile.value || !templateId.value) return
  uploadingExcel.value = true
  excelErrors.value = []
  zipErrors.value = []
  estructuraErrors.value = []
  try {
    const fd = new FormData()
    fd.append('file', excelFile.value)
    if (zipFile.value) {
      fd.append('archivos_zip', zipFile.value)
    }
    const apiUrl = import.meta.env.VITE_API_URL || '/api'
    const token = localStorage.getItem('ubpd_access_token')
    // Endpoint unificado que acepta Excel + ZIP opcional
    const endpoint = zipFile.value
      ? `${apiUrl}/forms/upload-excel-zip/${templateId.value}`
      : `${apiUrl}/forms/upload-excel/${templateId.value}`
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: fd,
    })

    if (response.status === 422 || (response.status === 400 && zipFile.value)) {
      const body = await response.json()
      const detail = body.detail
      if (detail && typeof detail === 'object') {
        // Nuevo formato con excel_errors / zip_errors / estructura_errors
        if ('excel_errors' in detail || 'zip_errors' in detail || 'estructura_errors' in detail) {
          excelErrors.value = (detail.excel_errors || []) as ExcelRowError[]
          zipErrors.value = (detail.zip_errors || []) as string[]
          estructuraErrors.value = (detail.estructura_errors || []) as string[]
          validationModalOpen.value = true
          return
        }
        // Formato legacy: errores_por_fila
        if (detail.errores_por_fila) {
          excelErrors.value = detail.errores_por_fila as ExcelRowError[]
          validationModalOpen.value = true
          notifications.error(
            'Errores en el archivo',
            `Se encontraron errores en ${excelErrors.value.length} fila(s).`,
          )
          return
        }
      }
      notifications.error('Error de validación', typeof detail === 'string' ? detail : 'Revisa el archivo.')
      return
    }

    if (!response.ok) {
      const err = await response.json()
      const msg = typeof err.detail === 'string' ? err.detail : 'Error al subir el archivo.'
      notifications.error('Error', msg)
      return
    }

    const result = await response.json()
    notifications.success('¡Cargado!', result.mensaje ?? `${result.created} formulario(s) creado(s).`)
    router.push('/dependencia/inbox')
  } catch {
    notifications.error('Error', 'No se pudo conectar con el servidor. Intenta de nuevo.')
  } finally {
    uploadingExcel.value = false
  }
}

// State
const loading = ref(true)
const saving = ref(false)
const saveMode = ref<'draft' | 'submit'>('draft')

const templateData = ref<Template | null>(null)
const formData = ref<FormData | null>(null)
/** Normaliza configuracion_campos sin importar si viene con claves en español o inglés */
function normalizeSchema(raw: Record<string, unknown> | null | undefined): FormSchema | null {
  if (!raw) return null
  const rawFields = (raw.campos ?? raw.fields ?? []) as Record<string, unknown>[]
  const fields: FormSchema['fields'] = rawFields.map((f) => ({
    name:     String(f.name     ?? ''),
    label:    String(f.label    ?? f.name ?? ''),
    type:     String(f.tipo     ?? f.type ?? 'text') as FieldConfig['type'],
    readonly: Boolean(f.readonly ?? f.bloqueado ?? false),
    required: Boolean(f.requerido ?? f.required ?? false),
    default:  (f.default ?? null) as string | number | null,
    options:  Array.isArray(f.opciones ?? f.options)
      ? ((f.opciones ?? f.options) as unknown[]).map((o) =>
          typeof o === 'string' ? { value: o, label: o } : (o as { value: string; label: string })
        )
      : undefined,
    formula: f.formula ? String(f.formula) : undefined,
  }))
  return { fields }
}

const schema = computed<FormSchema | null>(() =>
  normalizeSchema(templateData.value?.configuracion_campos as Record<string, unknown> | null)
)

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
  // Pre-fill defaults usando la schema normalizada
  const vals: Record<string, unknown> = {}
  const normalized = normalizeSchema(templateData.value.configuracion_campos as Record<string, unknown>)
  for (const f of normalized?.fields ?? []) {
    vals[f.name] = f.default ?? ''
  }
  dinamicValues.value = vals
}

async function loadForm(id: string) {
  formData.value = await get<FormData>(`/forms/${id}`)
  // El backend devuelve plantilla_id (no template_id)
  const tmplId = (formData.value as unknown as Record<string, string>).plantilla_id
    ?? formData.value.template_id
  templateData.value = await get<Template>(`/templates/${tmplId}`)
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
    plantilla_id: templateData.value?.id,   // el backend usa plantilla_id
    fecha_usuario: fechaReferencia.value,   // el backend usa fecha_usuario
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
      // Subir archivos pendientes ANTES de navegar al nuevo formulario
      if (fileUploadZoneRef.value) {
        await fileUploadZoneRef.value.triggerUploadAll(created.id)
      }
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
      // Subir archivos pendientes antes de enviar a revisión
      if (fileUploadZoneRef.value) {
        await fileUploadZoneRef.value.triggerUploadAll(created.id)
      }
      await post(`/forms/${created.id}/submit`, {})
    }
    hasChanges = false
    notifications.success('Enviado', 'El formulario ha sido enviado a revisión.')
    router.push('/dependencia/inbox')
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
