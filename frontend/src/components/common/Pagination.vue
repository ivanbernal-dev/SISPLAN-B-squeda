<template>
  <div
    v-if="totalPages > 1 || totalItems > 0"
    class="flex flex-col sm:flex-row items-center justify-between gap-3 px-1 py-2"
  >
    <!-- Indicador de total -->
    <p class="text-xs text-ubpd-gris/60">
      <span class="font-medium text-ubpd-gris">{{ totalItems }}</span> registros en total
    </p>

    <!-- Controles de paginación -->
    <nav class="flex items-center gap-1" aria-label="Paginación">
      <!-- Anterior -->
      <button
        class="pagination-btn"
        :disabled="currentPage <= 1"
        aria-label="Página anterior"
        @click="$emit('page-change', currentPage - 1)"
      >
        <PhCaretLeft :size="14" aria-hidden="true" />
      </button>

      <!-- Números de página -->
      <template v-for="page in visiblePages" :key="page">
        <!-- Elipsis -->
        <span
          v-if="page === '...'"
          class="px-2 text-ubpd-gris/40 select-none text-sm"
          aria-hidden="true"
        >
          …
        </span>
        <!-- Botón de página -->
        <button
          v-else
          class="pagination-btn"
          :class="{ 'pagination-btn-active': page === currentPage }"
          :aria-label="`Página ${page}`"
          :aria-current="page === currentPage ? 'page' : undefined"
          @click="$emit('page-change', page as number)"
        >
          {{ page }}
        </button>
      </template>

      <!-- Siguiente -->
      <button
        class="pagination-btn"
        :disabled="currentPage >= totalPages"
        aria-label="Página siguiente"
        @click="$emit('page-change', currentPage + 1)"
      >
        <PhCaretRight :size="14" aria-hidden="true" />
      </button>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { PhCaretLeft, PhCaretRight } from '@phosphor-icons/vue'

interface Props {
  currentPage:  number
  totalPages:   number
  totalItems:   number
  /** Cuántos números de página mostrar como máximo (default: 7) */
  maxVisible?:  number
}

const props = withDefaults(defineProps<Props>(), {
  maxVisible: 7,
})

defineEmits<{
  'page-change': [page: number]
}>()

/** Genera el array de páginas visibles con elipsis */
const visiblePages = computed<Array<number | '...'>>(() => {
  const { currentPage: cur, totalPages: total, maxVisible } = props

  if (total <= maxVisible) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }

  const half = Math.floor(maxVisible / 2)
  let start = Math.max(2, cur - half)
  let end   = Math.min(total - 1, cur + half)

  // Ajustar si estamos cerca del inicio o del final
  if (cur <= half + 1) {
    end = Math.min(total - 1, maxVisible - 2)
  } else if (cur >= total - half) {
    start = Math.max(2, total - maxVisible + 3)
  }

  const pages: Array<number | '...'> = [1]

  if (start > 2) pages.push('...')
  for (let p = start; p <= end; p++) pages.push(p)
  if (end < total - 1) pages.push('...')
  pages.push(total)

  return pages
})
</script>

<style scoped>
.pagination-btn {
  @apply inline-flex h-8 min-w-[2rem] items-center justify-center rounded-md border
         border-ubpd-gris-borde bg-white px-1.5 text-sm text-ubpd-gris
         hover:border-ubpd-teal hover:text-ubpd-teal transition-colors
         disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:border-ubpd-gris-borde
         disabled:hover:text-ubpd-gris;
}

.pagination-btn-active {
  @apply border-ubpd-teal bg-ubpd-teal text-white hover:text-white hover:border-ubpd-teal;
}
</style>
