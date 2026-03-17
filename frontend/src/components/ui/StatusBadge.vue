<template>
  <span
    class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold font-barlow whitespace-nowrap"
    :style="{ backgroundColor: bgColor, color: textColor }"
  >
    <span :style="{ color: textColor }" aria-hidden="true">{{ icon }}</span>
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { FormStatus } from '@/types/forms'

interface Props {
  status: FormStatus
}

const props = defineProps<Props>()

const CONFIG: Record<FormStatus, { label: string; bg: string; text: string; icon: string }> = {
  draft:    { label: 'Borrador',              bg: '#F5F5F5', text: '#666666', icon: '✏️' },
  pending:  { label: 'En Revisión',           bg: '#E6F4F6', text: '#3E818F', icon: '🕐' },
  rejected: { label: 'Requiere corrección',   bg: '#FFF1E6', text: '#FF6900', icon: '⚠️' },
  approved: { label: 'Registro validado',     bg: '#E6F7F7', text: '#52ABAB', icon: '✓' },
}

const bgColor = computed(() => CONFIG[props.status]?.bg ?? '#F5F5F5')
const textColor = computed(() => CONFIG[props.status]?.text ?? '#323232')
const label = computed(() => CONFIG[props.status]?.label ?? props.status)
const icon = computed(() => CONFIG[props.status]?.icon ?? '')
</script>
