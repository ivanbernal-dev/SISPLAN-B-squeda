<template>
  <div class="flex flex-col gap-2 h-full">
    <!-- Toolbar -->
    <div class="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
      <span class="text-xs font-semibold text-gray-500 uppercase tracking-wide mr-2">Ayuda:</span>
      <button
        type="button"
        class="text-xs font-barlow bg-white border border-gray-300 rounded px-2 py-1 hover:border-ubpd-teal hover:text-ubpd-teal transition-colors"
        @click="insertTableSyntax"
        title="Insertar tabla de campos"
      >
        + Tabla de campos
      </button>
      <button
        type="button"
        class="text-xs font-barlow bg-white border border-gray-300 rounded px-2 py-1 hover:border-ubpd-teal hover:text-ubpd-teal transition-colors"
        @click="insertFieldRow"
        title="Insertar fila de campo"
      >
        + Fila
      </button>
    </div>

    <!-- Two-panel editor -->
    <div class="grid grid-cols-2 gap-4 flex-1 min-h-0">
      <!-- Editor panel -->
      <div class="flex flex-col gap-1">
        <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Editor Markdown</p>
        <textarea
          ref="textareaRef"
          :value="modelValue"
          :disabled="disabled"
          rows="20"
          class="flex-1 w-full font-mono text-sm border border-gray-300 rounded-lg p-3 resize-none focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-teal-100 bg-white text-ubpd-gris"
          :placeholder="PLACEHOLDER"
          @input="onInput"
        />
      </div>

      <!-- Preview panel -->
      <div class="flex flex-col gap-1">
        <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide flex items-center gap-2">
          Preview del Formulario
          <span v-if="isLoadingPreview" class="inline-block h-3 w-3 border-2 border-ubpd-teal border-t-transparent rounded-full animate-spin" aria-label="Cargando preview" />
        </p>
        <div class="flex-1 border border-gray-200 rounded-lg p-4 bg-gray-50 overflow-auto">
          <div v-if="previewSchema && previewSchema.fields.length > 0">
            <DynamicFormRenderer
              :schema="previewSchema"
              :model-value="previewValues"
              :read-only="false"
            />
          </div>
          <div v-else class="text-center py-8 text-gray-400">
            <p class="text-sm font-barlow">Escribe en el editor para ver el preview del formulario</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useApi } from '@/composables/useApi'
import type { FormSchema } from '@/types/forms'
import DynamicFormRenderer from './DynamicFormRenderer.vue'

interface Props {
  modelValue: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const { post } = useApi()
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const previewSchema = ref<FormSchema | null>(null)
const previewValues = ref<Record<string, unknown>>({})
const isLoadingPreview = ref(false)

let debounceTimer: ReturnType<typeof setTimeout> | null = null

const PLACEHOLDER = `## Nombre del Template

| Campo | Tipo | Bloqueado | Default |
|-------|------|-----------|---------|
| municipio | text | true | Bogotá |
| codigo_caso | text | false | |
| num_solicitudes | number | false | 0 |
| fecha_inicio | date | false | |
| estado | select | false | activo |

<!-- Tipos: text, number, date, textarea, select -->
<!-- Bloqueado: true = readonly, false = editable -->
`

function onInput(e: Event) {
  const val = (e.target as HTMLTextAreaElement).value
  emit('update:modelValue', val)

  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => fetchPreview(val), 800)
}

async function fetchPreview(markdown: string) {
  if (!markdown.trim()) {
    previewSchema.value = null
    return
  }
  isLoadingPreview.value = true
  try {
    const result = await post<{ configuracion_campos: FormSchema }>('/templates/preview', {
      codigo_markdown: markdown,
    })
    previewSchema.value = result.configuracion_campos
    // Initialize preview values with defaults
    const vals: Record<string, unknown> = {}
    for (const f of result.configuracion_campos.fields) {
      vals[f.name] = f.default ?? ''
    }
    previewValues.value = vals
  } catch {
    previewSchema.value = null
  } finally {
    isLoadingPreview.value = false
  }
}

function insertTableSyntax() {
  const syntax = `\n| Campo | Tipo | Bloqueado | Default |\n|-------|------|-----------|---------|
| nombre_campo | text | false | |\n`
  emit('update:modelValue', props.modelValue + syntax)
}

function insertFieldRow() {
  const row = `| nuevo_campo | text | false | |\n`
  emit('update:modelValue', props.modelValue + row)
}

watch(() => props.modelValue, (val) => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => fetchPreview(val), 800)
}, { immediate: true })
</script>
