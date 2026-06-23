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

    <!-- Metadatos -->
    <div class="bg-white rounded-2xl border border-gray-100 shadow-sm px-5 py-4 flex-shrink-0">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
        <div>
          <label class="block font-cuerpo font-medium text-sm text-ubpd-gris mb-1.5">Indicador de Nivel 1</label>
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

    <!-- Editor principal — 2 columnas -->
    <div class="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-2 gap-5">

      <!-- ── Columna izquierda: Editor (tabbed) ────────────────────────── -->
      <div class="flex flex-col bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">

        <!-- Tabs -->
        <div class="flex items-center border-b border-gray-100 px-1 pt-1 flex-shrink-0">
          <button
            @click="setMode('visual')"
            class="flex items-center gap-1.5 px-4 py-2.5 text-xs font-cuerpo font-medium rounded-t-lg transition border-b-2"
            :class="editorMode === 'visual'
              ? 'border-ubpd-verde text-ubpd-verde bg-ubpd-verde/5'
              : 'border-transparent text-gray-500 hover:text-ubpd-gris'"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M4 6h16M4 10h16M4 14h16M4 18h16" />
            </svg>
            Editor Visual
          </button>
          <button
            @click="setMode('markdown')"
            class="flex items-center gap-1.5 px-4 py-2.5 text-xs font-cuerpo font-medium rounded-t-lg transition border-b-2"
            :class="editorMode === 'markdown'
              ? 'border-ubpd-teal text-ubpd-teal bg-ubpd-teal/5'
              : 'border-transparent text-gray-500 hover:text-ubpd-gris'"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
            </svg>
            Markdown
          </button>
          <div class="ml-auto pr-3 flex items-center gap-2">
            <span v-if="syncing" class="font-cuerpo text-xs text-ubpd-teal flex items-center gap-1">
              <svg class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Sincronizando…
            </span>
          </div>
        </div>

        <!-- ── Tab Markdown ── -->
        <div v-show="editorMode === 'markdown'" class="flex-1 flex flex-col overflow-hidden">
          <div class="flex-1 overflow-hidden">
            <textarea
              v-model="form.codigo_markdown"
              @input="onMarkdownInput"
              placeholder="# Nombre del Formulario&#10;&#10;## Campos&#10;&#10;| campo | label | tipo | bloqueado | default | requerido | opciones |&#10;|-------|-------|------|-----------|---------|-----------|---------|&#10;| municipio | Municipio | text | true | Bogotá | true | |"
              class="w-full h-full font-mono text-sm border-0 focus:ring-0 outline-none resize-none p-5
                     text-ubpd-gris bg-white placeholder-gray-300"
              spellcheck="false"
            />
          </div>
          <div class="px-5 py-2.5 border-t border-gray-100 bg-gray-50 flex-shrink-0">
            <p class="font-cuerpo text-xs text-gray-400">
              <strong class="text-gray-500">Columnas:</strong>
              campo · label · tipo · bloqueado · default · requerido · opciones
            </p>
          </div>
        </div>

        <!-- ── Tab Editor Visual ── -->
        <div v-show="editorMode === 'visual'" class="flex-1 flex flex-col overflow-hidden">
          <!-- Barra de acciones -->
          <div class="px-4 py-2.5 border-b border-gray-100 bg-gray-50 flex items-center justify-between flex-shrink-0">
            <span class="font-cuerpo text-xs text-gray-500">
              {{ visualFields.length }} campo{{ visualFields.length !== 1 ? 's' : '' }}
            </span>
            <button
              @click="addField"
              class="inline-flex items-center gap-1.5 text-xs font-cuerpo font-semibold
                     bg-ubpd-verde text-white px-3 py-1.5 rounded-lg hover:bg-[#3a7d4a] transition"
            >
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
              Agregar campo
            </button>
          </div>

          <!-- Lista de campos -->
          <div class="flex-1 overflow-y-auto p-4 space-y-3">
            <div v-if="visualFields.length === 0" class="flex flex-col items-center justify-center h-full py-12 text-center">
              <svg class="w-10 h-10 text-gray-200 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p class="font-cuerpo text-sm text-gray-400">No hay campos. Agrega uno con el botón.</p>
            </div>

            <div
              v-for="(field, idx) in visualFields"
              :key="field.id"
              draggable="true"
              @dragstart="onDragStart(idx, $event)"
              @dragover.prevent="onDragOver(idx)"
              @dragend="onDragEnd"
              class="border rounded-xl p-3.5 space-y-3 transition select-none"
              :class="[
                field.readonly ? 'bg-gray-50 border-gray-200' : 'bg-white border-ubpd-teal/30 shadow-sm',
                dragOverIdx === idx && dragIdx !== idx ? 'ring-2 ring-ubpd-teal ring-offset-1' : '',
                dragIdx === idx ? 'opacity-50' : '',
              ]"
            >
              <!-- Fila 1: handle, nombre, label, tipo, acciones -->
              <div class="grid grid-cols-12 gap-2 items-end">
                <!-- Drag handle -->
                <div class="col-span-1 flex items-end pb-1.5">
                  <div
                    class="cursor-grab active:cursor-grabbing text-gray-300 hover:text-gray-500 transition flex flex-col gap-0.5 px-0.5"
                    title="Arrastrar para reordenar"
                  >
                    <span class="block w-4 h-0.5 bg-current rounded" />
                    <span class="block w-4 h-0.5 bg-current rounded" />
                    <span class="block w-4 h-0.5 bg-current rounded" />
                  </div>
                </div>
                <div class="col-span-3">
                  <label class="block font-cuerpo text-xs text-gray-500 mb-1">Nombre <span class="text-ubpd-naranja">*</span></label>
                  <input
                    v-model="field.name"
                    @input="onVisualChange"
                    type="text"
                    placeholder="nombre_campo"
                    class="w-full font-mono text-xs border border-gray-300 rounded-lg px-2 py-1.5
                           focus:outline-none focus:border-ubpd-teal focus:ring-1 focus:ring-ubpd-teal/30 transition"
                  />
                </div>
                <div class="col-span-4">
                  <label class="block font-cuerpo text-xs text-gray-500 mb-1">Etiqueta (label)</label>
                  <input
                    v-model="field.label"
                    @input="onVisualChange"
                    type="text"
                    placeholder="Nombre visible"
                    class="w-full font-cuerpo text-xs border border-gray-300 rounded-lg px-2 py-1.5
                           focus:outline-none focus:border-ubpd-teal focus:ring-1 focus:ring-ubpd-teal/30 transition"
                  />
                </div>
                <div class="col-span-2">
                  <label class="block font-cuerpo text-xs text-gray-500 mb-1">Tipo</label>
                  <select
                    v-model="field.type"
                    @change="onVisualChange"
                    class="w-full font-cuerpo text-xs border border-gray-300 rounded-lg px-2 py-1.5
                           focus:outline-none focus:border-ubpd-teal transition"
                  >
                    <option value="text">Texto</option>
                    <option value="number">Número</option>
                    <option value="date">Fecha</option>
                    <option value="textarea">Área texto</option>
                    <option value="select">Selector</option>
                    <option value="computed">Calculado</option>
                    <option value="archivos">Archivos adjuntos</option>
                  </select>
                </div>
                <div class="col-span-2 flex justify-end items-end gap-1 pb-0.5">
                  <button
                    @click="removeField(idx)"
                    class="p-1.5 rounded-lg text-ubpd-naranja hover:bg-orange-50 transition"
                    title="Eliminar campo"
                  >
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>

              <!-- Fila 2: default + toggles -->
              <div class="grid grid-cols-12 gap-2 items-center">
                <div class="col-span-4">
                  <label class="block font-cuerpo text-xs text-gray-500 mb-1">Valor por defecto</label>
                  <input
                    v-model="field.default"
                    @input="onVisualChange"
                    type="text"
                    placeholder="Vacío"
                    class="w-full font-cuerpo text-xs border border-gray-300 rounded-lg px-2 py-1.5
                           focus:outline-none focus:border-ubpd-teal transition"
                  />
                </div>
                <div class="col-span-8 flex items-center gap-4 pt-4 flex-wrap">
                  <!-- Toggle readonly -->
                  <label class="flex items-center gap-2 cursor-pointer select-none">
                    <button
                      type="button"
                      @click="field.readonly = !field.readonly; onVisualChange()"
                      class="relative flex-shrink-0 rounded-full transition-colors duration-200"
                      :class="field.readonly ? 'bg-ubpd-teal' : 'bg-gray-300'"
                      style="width:36px;height:20px;"
                    >
                      <span
                        class="absolute bg-white rounded-full shadow transition-transform duration-200"
                        :style="{
                          width: '16px', height: '16px',
                          top: '2px', left: '2px',
                          transform: field.readonly ? 'translateX(16px)' : 'translateX(0)',
                        }"
                      />
                    </button>
                    <span class="font-cuerpo text-xs" :class="field.readonly ? 'text-ubpd-teal font-medium' : 'text-gray-500'">
                      Solo lectura
                    </span>
                  </label>

                  <!-- Toggle required -->
                  <label class="flex items-center gap-2 cursor-pointer select-none">
                    <button
                      type="button"
                      @click="field.required = !field.required; onVisualChange()"
                      class="relative flex-shrink-0 rounded-full transition-colors duration-200"
                      :class="field.required ? 'bg-ubpd-naranja' : 'bg-gray-300'"
                      style="width:36px;height:20px;"
                    >
                      <span
                        class="absolute bg-white rounded-full shadow transition-transform duration-200"
                        :style="{
                          width: '16px', height: '16px',
                          top: '2px', left: '2px',
                          transform: field.required ? 'translateX(16px)' : 'translateX(0)',
                        }"
                      />
                    </button>
                    <span class="font-cuerpo text-xs" :class="field.required ? 'text-ubpd-naranja font-medium' : 'text-gray-500'">
                      Requerido
                    </span>
                  </label>
                </div>
              </div>

              <!-- Fila 3: opciones (solo para select) -->
              <div v-if="field.type === 'select'" class="pt-1 border-t border-gray-100">
                <label class="block font-cuerpo text-xs text-gray-500 mb-2">Opciones del selector</label>
                <div class="flex flex-wrap gap-1.5 mb-2">
                  <span
                    v-for="(opt, oi) in field.options"
                    :key="oi"
                    class="inline-flex items-center gap-1 bg-ubpd-teal/10 text-ubpd-teal
                           text-xs font-cuerpo px-2 py-0.5 rounded-full"
                  >
                    {{ opt }}
                    <button
                      @click="removeOption(field, oi)"
                      class="text-ubpd-teal/60 hover:text-ubpd-naranja transition"
                    >×</button>
                  </span>
                  <span v-if="field.options.length === 0" class="text-xs text-gray-400 italic">Sin opciones</span>
                </div>
                <div class="flex gap-2">
                  <input
                    v-model="field.newOption"
                    @keydown.enter.prevent="addOption(field)"
                    type="text"
                    placeholder="Nueva opción…"
                    class="flex-1 font-cuerpo text-xs border border-gray-300 rounded-lg px-2 py-1.5
                           focus:outline-none focus:border-ubpd-verde transition"
                  />
                  <button
                    @click="addOption(field)"
                    :disabled="!field.newOption.trim()"
                    class="font-cuerpo text-xs font-medium bg-ubpd-verde text-white px-3 py-1.5
                           rounded-lg hover:bg-[#3a7d4a] disabled:opacity-40 transition"
                  >
                    Agregar
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Columna derecha: Preview del formulario ───────────────────── -->
      <div class="flex flex-col bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div class="flex items-center gap-2 px-5 py-3 border-b border-gray-100 flex-shrink-0">
          <div class="w-2 h-2 rounded-full bg-ubpd-verde" />
          <span class="font-subtitulo font-semibold text-sm text-ubpd-gris">Vista Previa del Formulario</span>
          <span v-if="previewLoading" class="ml-auto font-cuerpo text-xs text-ubpd-teal flex items-center gap-1">
            <svg class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Actualizando…
          </span>
        </div>

        <div v-if="!previewFields.length && !previewLoading"
             class="flex-1 flex flex-col items-center justify-center p-8 text-center">
          <svg class="w-12 h-12 text-gray-200 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
              d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
          <p class="font-cuerpo text-sm text-gray-400">Agrega campos para ver la vista previa</p>
        </div>

        <div v-else class="flex-1 overflow-y-auto p-5 space-y-4">
          <div v-for="field in previewFields" :key="field.name" class="space-y-1">
            <div class="flex items-center gap-2">
              <label class="font-cuerpo font-medium text-sm text-ubpd-gris">
                {{ field.label ?? field.name }}
                <span v-if="field.required" class="text-ubpd-naranja ml-0.5">*</span>
              </label>
              <span
                class="inline-flex items-center gap-1 text-xs font-cuerpo px-1.5 py-0.5 rounded"
                :class="field.readonly ? 'bg-gray-100 text-gray-500' : 'bg-ubpd-verde/10 text-ubpd-verde'"
              >
                <svg v-if="field.readonly" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <svg v-else class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
                {{ field.readonly ? 'Bloqueado' : 'Editable' }}
              </span>
            </div>

            <select v-if="field.type === 'select'" :disabled="field.readonly"
              class="w-full font-cuerpo text-sm border rounded-lg px-4 py-2.5 transition"
              :class="field.readonly ? 'bg-gray-100 border-gray-200 text-gray-500 cursor-not-allowed' : 'bg-white border-gray-300'">
              <option value="" disabled selected>Seleccionar…</option>
              <option v-for="opt in (field.options ?? [])" :key="opt">{{ opt }}</option>
            </select>
            <textarea v-else-if="field.type === 'textarea'" v-autoresize :value="field.default ?? ''" :disabled="field.readonly"
              class="w-full font-cuerpo text-sm border rounded-lg px-4 py-2.5 transition min-h-[80px]"
              :class="field.readonly ? 'bg-gray-100 border-gray-200 text-gray-500 cursor-not-allowed' : 'bg-white border-gray-300'" />
            <div v-else-if="field.type === 'computed'"
              class="w-full font-cuerpo text-sm rounded-lg px-4 py-2.5 border bg-blue-50 border-blue-200 text-blue-700 text-xs">
              Calculado automáticamente
            </div>
            <textarea v-else
              v-autoresize
              :value="field.default ?? ''" :disabled="field.readonly"
              class="w-full font-cuerpo text-sm border rounded-lg px-4 py-2.5 transition leading-snug"
              :class="field.readonly ? 'bg-gray-100 border-gray-200 text-gray-500 cursor-not-allowed' : 'bg-white border-gray-300'"
            />
          </div>
        </div>

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

type FieldType = 'text' | 'number' | 'date' | 'textarea' | 'select' | 'computed' | 'archivos'

interface Indicator {
  indicador_id: number
  nombre: string
}

interface PreviewField {
  name: string
  label?: string
  type: FieldType
  readonly: boolean
  required?: boolean
  default?: any
  options?: string[]
}

interface VisualField extends PreviewField {
  id: string
  options: string[]
  newOption: string
}

const route = useRoute()
const router = useRouter()
const { get, post, patch } = useApi()
const notifications = useNotificationsStore()

const templateId = computed(() => route.params.id as string | undefined)
const isEditing = computed(() => !!templateId.value && templateId.value !== 'new')

const saving = ref(false)
const syncing = ref(false)
const loadingIndicators = ref(true)
const previewLoading = ref(false)
const previewError = ref('')
const previewFields = ref<PreviewField[]>([])
const indicators = ref<Indicator[]>([])
const editorMode = ref<'markdown' | 'visual'>('visual')
const visualFields = ref<VisualField[]>([])

// ── Drag & drop state ─────────────────────────────────────────────────────────
const dragIdx = ref<number | null>(null)
const dragOverIdx = ref<number | null>(null)

let debounceTimer: ReturnType<typeof setTimeout> | null = null

const form = reactive({
  nombre: '',
  descripcion: '',
  indicador_nivel1_id: null as number | null,
  codigo_markdown: `# Nombre del Formulario

## Campos

| campo | label | tipo | bloqueado | default | requerido | opciones |
|-------|-------|------|-----------|---------|-----------|---------|
| municipio | Municipio | text | true | Bogotá | true | |
| codigo_caso | Código de caso | text | false | | true | |
| fecha_hecho | Fecha del hecho | date | false | | true | |
| num_personas | Número de personas | number | false | 1 | true | |
`,
})

// ── Modo ──────────────────────────────────────────────────────────────────────

async function setMode(mode: 'markdown' | 'visual') {
  if (mode === editorMode.value) return
  syncing.value = true
  try {
    if (mode === 'visual') {
      // Markdown → Visual: parsear via API
      await syncMarkdownToVisual()
    } else {
      // Visual → Markdown: generar markdown desde campos
      syncVisualToMarkdown()
      await updatePreview()
    }
    editorMode.value = mode
  } finally {
    syncing.value = false
  }
}

async function syncMarkdownToVisual() {
  if (!form.codigo_markdown.trim()) {
    visualFields.value = []
    return
  }
  try {
    const resp = await post<{ configuracion_campos?: { fields?: PreviewField[] } }>(
      '/templates/preview',
      { codigo_markdown: form.codigo_markdown }
    )
    const fields = resp.configuracion_campos?.fields ?? []
    visualFields.value = fields.map((f) => fieldToVisual(f))
  } catch {
    // Si falla, mantener los campos visuales actuales
  }
}

function syncVisualToMarkdown() {
  form.codigo_markdown = visualFieldsToMarkdown()
}

// ── Markdown helpers ──────────────────────────────────────────────────────────

function visualFieldsToMarkdown(): string {
  const header = `# ${form.nombre || 'Formulario'}

## Campos

| campo | label | tipo | bloqueado | default | requerido | opciones |
|-------|-------|------|-----------|---------|-----------|---------|`
  const rows = visualFields.value.map((f) => {
    const def = f.default != null ? String(f.default) : ''
    const opts = f.options.join(',')
    return `| ${f.name} | ${f.label} | ${f.type} | ${f.readonly ? 'true' : 'false'} | ${def} | ${f.required !== false ? 'true' : 'false'} | ${opts} |`
  })
  return [header, ...rows].join('\n') + '\n'
}

function fieldToVisual(f: PreviewField): VisualField {
  return {
    id: crypto.randomUUID(),
    name: f.name ?? '',
    label: f.label ?? f.name?.replace(/_/g, ' ') ?? '',
    type: (f.type as FieldType) ?? 'text',
    readonly: f.readonly ?? false,
    required: f.required !== false,
    default: f.default ?? '',
    options: (f.options ?? []).slice(),
    newOption: '',
  }
}

// ── Eventos de cambio ─────────────────────────────────────────────────────────

function onMarkdownInput() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(updatePreview, 700)
}

function onVisualChange() {
  // Actualizar preview desde los campos visuales directamente
  previewFields.value = visualFields.value.map((f) => ({ ...f }))
  // Sync en background al markdown (sin debounce para mantener consistencia)
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    syncVisualToMarkdown()
  }, 500)
}

// ── Drag & Drop ───────────────────────────────────────────────────────────────

function onDragStart(idx: number, e: DragEvent) {
  dragIdx.value = idx
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
    // payload mínimo requerido por algunos navegadores
    e.dataTransfer.setData('text/plain', String(idx))
  }
}

function onDragOver(idx: number) {
  if (dragIdx.value === null || dragIdx.value === idx) return
  dragOverIdx.value = idx
  // Reordenar en tiempo real para feedback visual inmediato
  const arr = visualFields.value
  const from = dragIdx.value
  const item = arr.splice(from, 1)[0]
  arr.splice(idx, 0, item)
  dragIdx.value = idx
}

function onDragEnd() {
  dragIdx.value = null
  dragOverIdx.value = null
  onVisualChange()
}

// ── Campo CRUD ────────────────────────────────────────────────────────────────

function addField() {
  const idx = visualFields.value.length + 1
  visualFields.value.push({
    id: crypto.randomUUID(),
    name: `campo_${idx}`,
    label: `Campo ${idx}`,
    type: 'text',
    readonly: false,
    required: true,
    default: '',
    options: [],
    newOption: '',
  })
  onVisualChange()
}

function removeField(idx: number) {
  visualFields.value.splice(idx, 1)
  onVisualChange()
}


function addOption(field: VisualField) {
  const opt = field.newOption.trim()
  if (!opt || field.options.includes(opt)) return
  field.options.push(opt)
  field.newOption = ''
  onVisualChange()
}

function removeOption(field: VisualField, idx: number) {
  field.options.splice(idx, 1)
  onVisualChange()
}

// ── Preview via API (para modo Markdown) ─────────────────────────────────────

async function updatePreview() {
  if (!form.codigo_markdown.trim()) {
    previewFields.value = []
    previewError.value = ''
    return
  }
  previewLoading.value = true
  previewError.value = ''
  try {
    const resp = await post<{ configuracion_campos?: { fields?: PreviewField[] }; fields?: PreviewField[] }>(
      '/templates/preview',
      { codigo_markdown: form.codigo_markdown }
    )
    previewFields.value = resp.configuracion_campos?.fields ?? resp.fields ?? []
  } catch {
    previewError.value = 'No se pudo generar el preview. Verifique la sintaxis del Markdown.'
    previewFields.value = []
  } finally {
    previewLoading.value = false
  }
}

// ── Helpers para markdown generado desde campos existentes ────────────────────

function fieldsToMarkdown(tmplNombre: string, fields: PreviewField[]): string {
  const rows = fields.map((f) => {
    const def = f.default != null ? String(f.default) : ''
    const opts = Array.isArray(f.options) ? f.options.join(',') : ''
    return `| ${f.name} | ${f.label ?? f.name} | ${f.type} | ${f.readonly ? 'true' : 'false'} | ${def} | ${f.required !== false ? 'true' : 'false'} | ${opts} |`
  })
  return `# ${tmplNombre}

## Campos

| campo | label | tipo | bloqueado | default | requerido | opciones |
|-------|-------|------|-----------|---------|-----------|---------|
${rows.join('\n')}
`
}

// ── Normalizar campo de BD (claves español) → PreviewField (claves inglés) ────

function normalizeCampo(c: Record<string, unknown>): PreviewField {
  const rawOpts = (c.opciones ?? c.options) as unknown[]
  return {
    name:     String(c.name ?? ''),
    label:    String(c.label ?? c.name ?? ''),
    type:     String(c.tipo ?? c.type ?? 'text') as FieldType,
    readonly: Boolean(c.readonly ?? c.bloqueado ?? false),
    required: Boolean(c.requerido ?? c.required ?? false),
    default:  c.default ?? null,
    options:  Array.isArray(rawOpts)
      ? rawOpts.map((o) => (typeof o === 'string' ? o : String(o)))
      : [],
  }
}

// ── Carga inicial ─────────────────────────────────────────────────────────────

async function loadIndicators() {
  loadingIndicators.value = true
  try {
    indicators.value = await get<Indicator[]>('/stats/indicators')
  } catch {
    // no crítico
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
      configuracion_campos?: Record<string, unknown>
    }>(`/templates/${templateId.value}`)

    form.nombre = data.nombre
    form.descripcion = data.descripcion ?? ''
    form.indicador_nivel1_id = data.indicador_nivel1_id ?? null

    const cfg = data.configuracion_campos ?? {}
    const rawCampos = ((cfg.campos ?? cfg.fields ?? []) as Record<string, unknown>[])
    // Normalizar siempre a claves en inglés
    const campos: PreviewField[] = rawCampos.map(normalizeCampo)

    if (data.codigo_markdown?.trim()) {
      form.codigo_markdown = data.codigo_markdown
    } else if (campos.length) {
      form.codigo_markdown = fieldsToMarkdown(data.nombre, campos)
    }

    // Poblar directamente el editor visual y el preview sin llamada extra a la API
    visualFields.value = campos.map(fieldToVisual)
    previewFields.value = campos.slice()
  } catch {
    notifications.error('No se pudo cargar el template')
  }
}

onMounted(async () => {
  await loadIndicators()
  await loadTemplate()
  // Si arrancamos en modo markdown, actualizar el preview renderizado
  if (editorMode.value === 'markdown') {
    await updatePreview()
  }
})

// ── Guardar ───────────────────────────────────────────────────────────────────

async function handleSave() {
  if (!form.nombre.trim()) {
    notifications.error('El nombre del template es obligatorio')
    return
  }
  // Si está en modo visual, sincronizar primero al markdown
  if (editorMode.value === 'visual') {
    syncVisualToMarkdown()
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
