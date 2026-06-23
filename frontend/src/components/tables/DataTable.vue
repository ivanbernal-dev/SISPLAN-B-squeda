<template>
  <div class="flex flex-col gap-3">
    <!-- Search bar -->
    <div v-if="searchable" class="flex justify-end">
      <div class="relative">
        <input
          type="search"
          :value="searchQuery"
          placeholder="Buscar..."
          class="pl-9 pr-4 py-2 text-sm font-barlow border border-gray-300 rounded-lg focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-teal-100 w-64"
          @input="onSearch"
          aria-label="Buscar en la tabla"
        />
        <svg xmlns="http://www.w3.org/2000/svg" class="absolute left-2.5 top-2.5 text-gray-400" width="16" height="16" viewBox="0 0 256 256" fill="currentColor" aria-hidden="true">
          <path d="M229.66,218.34l-50.07-50.07a88.11,88.11,0,1,0-11.31,11.31l50.06,50.07a8,8,0,0,0,11.32-11.31ZM40,112a72,72,0,1,1,72,72A72.08,72.08,0,0,1,40,112Z"/>
        </svg>
      </div>
    </div>

    <!-- Table wrapper -->
    <div class="w-full overflow-x-auto rounded-xl border border-gray-200 shadow-sm">
      <table class="w-full text-sm font-barlow text-ubpd-gris">
        <!-- Header -->
        <thead class="bg-ubpd-teal text-white">
          <tr>
            <th
              v-for="col in columns"
              :key="col.key"
              :style="col.width ? { width: col.width } : {}"
              class="px-4 py-3 text-left font-semibold whitespace-nowrap"
              :class="col.sortable ? 'cursor-pointer hover:bg-teal-600 select-none' : ''"
              @click="col.sortable ? toggleSort(col.key) : undefined"
              :aria-sort="sortKey === col.key ? (sortDir === 'asc' ? 'ascending' : 'descending') : undefined"
            >
              <span class="flex items-center gap-1">
                {{ col.label }}
                <span v-if="col.sortable" class="flex flex-col text-xs leading-none opacity-70">
                  <svg
                    xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 256 256" fill="currentColor"
                    :class="sortKey === col.key && sortDir === 'asc' ? 'opacity-100' : 'opacity-40'"
                    aria-hidden="true"
                  >
                    <path d="M213.66,165.66a8,8,0,0,1-11.32,0L128,91.31,53.66,165.66a8,8,0,0,1-11.32-11.32l80-80a8,8,0,0,1,11.32,0l80,80A8,8,0,0,1,213.66,165.66Z"/>
                  </svg>
                  <svg
                    xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 256 256" fill="currentColor"
                    :class="sortKey === col.key && sortDir === 'desc' ? 'opacity-100' : 'opacity-40'"
                    aria-hidden="true"
                  >
                    <path d="M213.66,101.66l-80,80a8,8,0,0,1-11.32,0l-80-80A8,8,0,0,1,53.66,90.34L128,164.69l74.34-74.35a8,8,0,0,1,11.32,11.32Z"/>
                  </svg>
                </span>
              </span>
            </th>
          </tr>
        </thead>

        <!-- Body -->
        <tbody>
          <!-- Skeleton rows while loading -->
          <template v-if="loading">
            <tr v-for="n in pageSize ?? 5" :key="`sk-${n}`" class="border-t border-gray-100 animate-pulse">
              <td v-for="col in columns" :key="`sk-${n}-${col.key}`" class="px-4 py-3">
                <div class="h-4 bg-gray-200 rounded w-3/4" />
              </td>
            </tr>
          </template>

          <!-- Actual data rows -->
          <template v-else-if="data.length > 0">
            <tr
              v-for="(row, rowIdx) in data"
              :key="rowIdx"
              class="border-t border-gray-100 hover:bg-gray-50 transition-colors"
            >
              <td
                v-for="col in columns"
                :key="col.key"
                class="px-4 py-3"
              >
                <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">
                  {{ row[col.key] ?? '—' }}
                </slot>
              </td>
            </tr>
          </template>

          <!-- Empty state -->
          <tr v-else>
            <td :colspan="columns.length" class="px-4 py-10 text-center text-gray-400">
              <div class="flex flex-col items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 256 256" fill="currentColor" class="opacity-40" aria-hidden="true">
                  <path d="M213.66,82.34l-56-56A8,8,0,0,0,152,24H56A16,16,0,0,0,40,40V216a16,16,0,0,0,16,16H200a16,16,0,0,0,16-16V88A8,8,0,0,0,213.66,82.34ZM160,51.31,188.69,80H160ZM200,216H56V40h88V88a8,8,0,0,0,8,8h48V216Z"/>
                </svg>
                <span class="text-sm">No hay datos para mostrar</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div
      v-if="total && pageSize && total > pageSize"
      class="flex items-center justify-between text-sm font-barlow text-gray-600"
    >
      <span>
        Mostrando {{ paginationStart }}–{{ paginationEnd }} de {{ total }} registros
      </span>
      <div class="flex items-center gap-1">
        <button
          type="button"
          class="px-3 py-1.5 rounded-lg border border-gray-300 hover:border-ubpd-teal hover:text-ubpd-teal disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          :disabled="(currentPage ?? 1) <= 1"
          @click="emit('page-change', (currentPage ?? 1) - 1)"
          aria-label="Página anterior"
        >
          ‹
        </button>

        <button
          v-for="p in visiblePages"
          :key="p"
          type="button"
          class="px-3 py-1.5 rounded-lg border transition-colors"
          :class="p === (currentPage ?? 1)
            ? 'border-ubpd-teal bg-ubpd-teal text-white'
            : 'border-gray-300 hover:border-ubpd-teal hover:text-ubpd-teal'"
          @click="emit('page-change', p)"
          :aria-current="p === (currentPage ?? 1) ? 'page' : undefined"
        >
          {{ p }}
        </button>

        <button
          type="button"
          class="px-3 py-1.5 rounded-lg border border-gray-300 hover:border-ubpd-teal hover:text-ubpd-teal disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          :disabled="(currentPage ?? 1) >= totalPages"
          @click="emit('page-change', (currentPage ?? 1) + 1)"
          aria-label="Página siguiente"
        >
          ›
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Column {
  key: string
  label: string
  sortable?: boolean
  width?: string
}

interface Props {
  columns: Column[]
  data: Record<string, unknown>[]
  loading?: boolean
  searchable?: boolean
  total?: number
  currentPage?: number
  pageSize?: number
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  searchable: false,
  currentPage: 1,
  pageSize: 20,
})

const emit = defineEmits<{
  search: [query: string]
  sort: [key: string, dir: 'asc' | 'desc']
  'page-change': [page: number]
}>()

const searchQuery = ref('')
const sortKey = ref<string | null>(null)
const sortDir = ref<'asc' | 'desc'>('asc')

const totalPages = computed(() =>
  props.total && props.pageSize ? Math.ceil(props.total / props.pageSize) : 1,
)

const paginationStart = computed(() =>
  ((props.currentPage ?? 1) - 1) * (props.pageSize ?? 20) + 1,
)
const paginationEnd = computed(() =>
  Math.min((props.currentPage ?? 1) * (props.pageSize ?? 20), props.total ?? 0),
)

const visiblePages = computed(() => {
  const current = props.currentPage ?? 1
  const total = totalPages.value
  const pages: number[] = []
  const start = Math.max(1, current - 2)
  const end = Math.min(total, current + 2)
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

function onSearch(e: Event) {
  searchQuery.value = (e.target as HTMLInputElement).value
  emit('search', searchQuery.value)
}

function toggleSort(key: string) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'asc'
  }
  emit('sort', sortKey.value, sortDir.value)
}
</script>
