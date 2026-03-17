<template>
  <div class="space-y-4">
    <div
      v-for="field in schema.fields"
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
          v-if="isReadonlyField(field)"
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
        :id="`field-${field.name}`"
        :name="field.name"
        :value="String(modelValue[field.name] ?? field.default ?? '')"
        :readonly="isReadonlyField(field)"
        :disabled="isReadonlyField(field)"
        :required="field.required && !isReadonlyField(field)"
        rows="3"
        class="w-full rounded-lg border px-3 py-2 text-sm font-barlow resize-y transition-all duration-150 focus:outline-none"
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
import type { FormSchema } from '@/types/forms'

interface Props {
  schema: FormSchema
  modelValue: Record<string, unknown>
  readOnly?: boolean
  highlightedFields?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  readOnly: false,
  highlightedFields: () => [],
})

const emit = defineEmits<{
  'update:modelValue': [value: Record<string, unknown>]
}>()

function isReadonlyField(field: { readonly: boolean }) {
  return props.readOnly || field.readonly
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

function onInput(fieldName: string, value: unknown) {
  if (props.readOnly) return
  emit('update:modelValue', {
    ...props.modelValue,
    [fieldName]: value,
  })
}
</script>
