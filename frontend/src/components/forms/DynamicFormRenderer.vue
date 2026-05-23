<template>
  <div class="space-y-4">
    <div
      v-for="field in visibleFields"
      :key="field.name"
      class="flex flex-col gap-1"
    >
      <!-- Label -->
      <label
        :for="`field-${field.name}`"
        class="text-sm font-medium font-barlow flex items-center gap-1"
        :class="isHighlighted(field.name) ? 'text-ubpd-naranja' : 'text-ubpd-gris'"
      >
        {{ field.label }}
        <span v-if="field.required && !isReadonlyField(field)" class="text-ubpd-naranja">*</span>
        <span
          v-if="isAutoCalculated(field)"
          class="ml-1 inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full
                 bg-blue-50 text-blue-700 text-[10px] font-semibold uppercase tracking-wide
                 border border-blue-200"
          title="Campo calculado automáticamente"
        >
          ƒ Auto
        </span>
        <span
          v-else-if="isReadonlyField(field)"
          class="inline-flex items-center text-gray-400"
          aria-label="Campo bloqueado"
        >
          <!-- Lock icon (inline SVG for LockSimple from Phosphor) -->
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 256 256" fill="currentColor" aria-hidden="true">
            <path d="M208,80H176V56a48,48,0,0,0-96,0V80H48A16,16,0,0,0,32,96V208a16,16,0,0,0,16,16H208a16,16,0,0,0,16-16V96A16,16,0,0,0,208,80ZM96,56a32,32,0,0,1,64,0V80H96ZM208,208H48V96H208Z"/>
          </svg>
        </span>
      </label>

      <!-- textarea -->
      <textarea
        v-if="field.type === 'textarea'"
        v-autoresize
        :id="`field-${field.name}`"
        :name="field.name"
        :value="String(modelValue[field.name] ?? field.default ?? '')"
        :readonly="isReadonlyField(field)"
        :disabled="isReadonlyField(field)"
        :required="field.required && !isReadonlyField(field)"
        class="w-full rounded-lg border px-3 py-2 text-sm font-barlow resize-none transition-all duration-150 focus:outline-none"
        :class="fieldClass(field)"
        @input="onInput(field.name, ($event.target as HTMLTextAreaElement).value)"
      />

      <!-- select -->
      <select
        v-else-if="field.type === 'select'"
        :id="`field-${field.name}`"
        :name="field.name"
        :value="String(modelValue[field.name] ?? field.default ?? '')"
        :disabled="isReadonlyField(field)"
        :required="field.required && !isReadonlyField(field)"
        class="w-full rounded-lg border px-3 py-2 text-sm font-barlow transition-all duration-150 focus:outline-none"
        :class="fieldClass(field)"
        @change="onInput(field.name, ($event.target as HTMLSelectElement).value)"
      >
        <option value="">-- Seleccionar --</option>
        <option
          v-for="opt in field.options"
          :key="opt.value"
          :value="opt.value"
        >
          {{ opt.label }}
        </option>
      </select>

      <!-- computed (read-only calculated value) -->
      <div
        v-else-if="field.type === 'computed'"
        :id="`field-${field.name}`"
        class="w-full rounded-lg border px-3 py-2 text-sm font-barlow bg-gray-50 border-gray-200 text-gray-600 min-h-[38px] flex items-center"
      >
        {{ computedValue(field) }}
      </div>

      <!-- archivos — shown as a note (FileUploadZone handles actual upload at the parent) -->
      <div
        v-else-if="field.type === 'archivos'"
        class="text-xs text-gray-400 font-barlow italic"
      >
        Los archivos adjuntos se gestionan en la sección «Soportes y archivos adjuntos».
      </div>

      <!-- number / date / text -->
      <input
        v-else
        :id="`field-${field.name}`"
        :name="field.name"
        :type="field.type"
        :value="modelValue[field.name] ?? field.default ?? ''"
        :readonly="isReadonlyField(field)"
        :disabled="isReadonlyField(field)"
        :required="field.required && !isReadonlyField(field)"
        class="w-full rounded-lg border px-3 py-2 text-sm font-barlow transition-all duration-150 focus:outline-none"
        :class="fieldClass(field)"
        @input="onInput(field.name, ($event.target as HTMLInputElement).value)"
      />

      <!-- Highlighted hint -->
      <p
        v-if="isHighlighted(field.name)"
        class="text-xs text-ubpd-naranja font-barlow"
        role="alert"
      >
        Este campo requiere corrección.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import type { FormSchema, FieldConfig } from '@/types/forms'

interface Props {
  schema: FormSchema
  modelValue: Record<string, unknown>
  readOnly?: boolean
  highlightedFields?: string[]
  /** Si true, muestra TODOS los campos (incluyendo validator_only).
   *  Útil para la vista del validador al aprobar. */
  showValidatorFields?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  readOnly: false,
  highlightedFields: () => [],
  showValidatorFields: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: Record<string, unknown>]
}>()

// Esconde los campos validator_only de la vista por defecto (los ve solo el validador)
const visibleFields = computed(() =>
  props.schema.fields.filter((f) => props.showValidatorFields || !(f as any).validator_only),
)

function isReadonlyField(field: { readonly: boolean }) {
  return props.readOnly || field.readonly
}

function isAutoCalculated(field: FieldConfig): boolean {
  return !!(field as any).auto_calculate
}

function isHighlighted(fieldName: string) {
  return props.highlightedFields.includes(fieldName)
}

function fieldClass(field: { name: string; readonly: boolean }) {
  const readonly = isReadonlyField(field)
  const highlighted = isHighlighted(field.name)

  if (readonly) {
    return 'bg-gray-100 border-gray-200 text-gray-500 cursor-not-allowed'
  }
  if (highlighted) {
    return 'border-ubpd-naranja bg-orange-50 focus:ring-2 focus:ring-orange-200'
  }
  return 'border-gray-300 bg-white focus:border-ubpd-verde focus:ring-2 focus:ring-teal-100'
}

function computedValue(field: FieldConfig): string {
  if (!field.formula) return '—'
  // formula is like "var1 / var2" — evaluate simple arithmetic from modelValue
  try {
    const parts = field.formula.split('/')
    if (parts.length === 2) {
      const a = parseFloat(String(props.modelValue[parts[0].trim()] ?? 0))
      const b = parseFloat(String(props.modelValue[parts[1].trim()] ?? 0))
      if (!isNaN(a) && !isNaN(b) && b !== 0) {
        return (a / b * 100).toFixed(2) + '%'
      }
    }
  } catch { /* ignore */ }
  return '—'
}

// ── Auto-cálculo de campos con `auto_calculate` ──────────────────────────
// Las mismas reglas que aplica el backend (services/auto_calc.py).
function toNum(v: unknown): number | null {
  if (v === null || v === undefined || v === '') return null
  const n = Number(String(v).replace(',', '.'))
  return Number.isFinite(n) ? n : null
}

function applyAutoCalculate(values: Record<string, unknown>): Record<string, unknown> {
  const next = { ...values }
  const fields = props.schema.fields as Array<FieldConfig & { auto_calculate?: string }>

  // Paso 1: ratio alcanzado / proyectado → pct_avance_final
  for (const f of fields) {
    if (f.auto_calculate !== 'ratio_alcanzado_proyectado') continue
    const proj = toNum(next['pct_avance_proyectado'])
    const alc  = toNum(next['pct_avance_alcanzado'])
    if (proj === null || alc === null || proj <= 0) {
      next[f.name] = null
    } else {
      next[f.name] = Number((alc / proj).toFixed(4))
    }
  }

  // Paso 2: estado cumplimiento desde pct_avance_final
  for (const f of fields) {
    if (f.auto_calculate !== 'estado_cumplimiento_from_pct_final') continue
    const pctF = toNum(next['pct_avance_final'])
    if (pctF === null) {
      next[f.name] = 'No Aplica'
    } else {
      const pct = pctF * 100
      if      (pct >= 90) next[f.name] = 'Cumple'
      else if (pct >= 70) next[f.name] = 'Cumple Parcialmente'
      else if (pct >  0)  next[f.name] = 'No Cumple'
      else                next[f.name] = 'No Aplica'
    }
  }
  return next
}

function onInput(fieldName: string, value: unknown) {
  if (props.readOnly) return
  // Recalcular siempre — los campos auto_calculate se sobreescriben
  const updated = applyAutoCalculate({ ...props.modelValue, [fieldName]: value })
  emit('update:modelValue', updated)
}

// Recalcular al cargar el form la primera vez (sincroniza valores guardados)
watch(
  () => props.schema?.fields?.length,
  () => {
    if (props.readOnly) return
    const recalc = applyAutoCalculate(props.modelValue)
    // Solo emitir si efectivamente cambia algo
    const changed = Object.keys(recalc).some((k) => recalc[k] !== props.modelValue[k])
    if (changed) emit('update:modelValue', recalc)
  },
  { immediate: true },
)
</script>
