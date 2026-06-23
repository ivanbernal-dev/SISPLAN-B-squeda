<template>
  <!-- Área de reserva mínima: padding equivalente al alto de la "U" del logo (10px aprox) -->
  <div
    class="flex items-center gap-3"
    :class="containerClass"
    style="padding: 10px;"
  >
    <img
      src="/logo-ubpd.png"
      alt="UBPD — Unidad de Búsqueda de Personas dadas por Desaparecidas"
      class="h-10 w-auto object-contain"
    />
    <div v-if="showTitle" class="border-l border-current/20 pl-3">
      <slot>
        <span class="text-base font-bold leading-tight">Sistema de Gestión</span>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  /** Mostrar el texto de título a la derecha del logo */
  showTitle?: boolean
  /** Clases adicionales para el contenedor */
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  showTitle: false,
  class: '',
})

const containerClass = computed(() => props.class)
</script>
