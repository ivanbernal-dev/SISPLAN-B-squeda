<template>
  <div
    class="bg-white rounded-xl shadow-sm border border-gray-200 p-4 flex flex-col items-center gap-2 cursor-pointer
           hover:shadow-md hover:border-ubpd-lila transition-all duration-200 select-none"
    :class="{ 'ring-2 ring-ubpd-lila': active }"
    @click="handleClick"
    role="button"
    :aria-label="`Ver detalle de ${nombre}`"
    tabindex="0"
    @keydown.enter="handleClick"
    @keydown.space.prevent="handleClick"
  >
    <GaugeChart
      :value="completitud"
      :title="nombre"
      :subtitle="`${totalFormularios} formularios`"
      :size="size"
      :variant="variant"
      @click="handleClick"
    />

    <div class="text-center mt-1">
      <p class="text-xs font-barlow text-gray-500">
        {{ totalFormularios }} formulario{{ totalFormularios !== 1 ? 's' : '' }} en el período
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import GaugeChart from './GaugeChart.vue'

interface Props {
  indicadorId: string | number
  nombre: string
  completitud: number
  totalFormularios: number
  variant?: 'primary' | 'secondary'
  size?: 'sm' | 'md' | 'lg'
  active?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  active: false,
})

const emit = defineEmits<{
  click: [indicadorId: string | number]
}>()

function handleClick() {
  emit('click', props.indicadorId)
}
</script>
