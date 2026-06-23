<template>
  <span :class="['inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium', config.classes]">
    <component :is="config.icon" :size="12" aria-hidden="true" />
    {{ config.label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  PhPencilSimple,
  PhClock,
  PhWarning,
  PhCheckCircle,
} from '@phosphor-icons/vue'

export type FormStatus = 'draft' | 'pending' | 'rejected' | 'approved'

interface Props {
  status: FormStatus
}

const props = defineProps<Props>()

interface StatusConfig {
  label:   string
  classes: string
  icon:    unknown
}

const STATUS_MAP: Record<FormStatus, StatusConfig> = {
  draft: {
    label:   'Borrador',
    classes: 'bg-ubpd-gris-borde text-ubpd-gris',
    icon:    PhPencilSimple,
  },
  pending: {
    label:   'En Revisión',
    classes: 'bg-ubpd-teal text-white',
    icon:    PhClock,
  },
  rejected: {
    label:   'Requiere Corrección',
    classes: 'bg-ubpd-naranja text-white',
    icon:    PhWarning,
  },
  approved: {
    label:   'Aprobado',
    classes: 'bg-ubpd-verde text-white',
    icon:    PhCheckCircle,
  },
}

const config = computed<StatusConfig>(() => STATUS_MAP[props.status] ?? STATUS_MAP.draft)
</script>
