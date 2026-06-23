<template>
  <div class="p-6 space-y-5" @click="closeMenu">

    <!-- ══ HEADER ═══════════════════════════════════════════════════════════════ -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="font-subtitulo font-bold text-2xl text-ubpd-gris">Mis Trámites</h1>
        <p class="font-cuerpo text-sm text-gray-500 mt-0.5">Gestión de formularios enviados y borradores</p>
      </div>
      <RouterLink
        to="/dependencia/templates"
        class="inline-flex items-center gap-2 bg-ubpd-teal text-white font-cuerpo font-semibold
               text-sm rounded-xl px-5 py-2.5 hover:bg-[#346d7a] transition flex-shrink-0"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nuevo Registro
      </RouterLink>
    </div>

    <!-- ══ TABS ══════════════════════════════════════════════════════════════════ -->
    <div class="flex flex-wrap gap-1 border-b border-gray-200">
      <button
        v-for="tab in TABS"
        :key="tab.key"
        type="button"
        class="relative flex items-center gap-1.5 px-4 py-2.5 font-cuerpo text-sm font-semibold
               rounded-t-lg transition-colors"
        :class="activeTab === tab.key
          ? 'bg-white border border-b-white border-gray-200 text-ubpd-teal -mb-px'
          : 'text-gray-500 hover:text-ubpd-teal'"
        @click.stop="setTab(tab.key)"
      >
        {{ tab.label }}
        <span
          v-if="tabCounts[tab.key] > 0"
          class="inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 rounded-full
                 font-cuerpo text-xs font-bold"
          :class="tab.key === 'rejected'
            ? 'bg-ubpd-naranja/20 text-ubpd-naranja'
            : activeTab === tab.key
              ? 'bg-ubpd-teal/20 text-ubpd-teal'
              : 'bg-gray-200 text-gray-600'"
        >
          {{ tabCounts[tab.key] }}
        </span>
      </button>
    </div>

    <!-- ══ FILTROS (búsqueda + fechas) ══════════════════════════════════════════ -->
    <div class="bg-white rounded-2xl border border-gray-100 shadow-sm px-5 py-4">
      <div class="flex flex-wrap items-end gap-3">
        <!-- Buscador -->
        <div class="flex-1 min-w-[180px]">
          <label class="block font-cuerpo text-xs font-medium text-gray-500 mb-1">Buscar</label>
          <div class="relative">
            <svg
              class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
              fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M21 21l-4.35-4.35M17 11A6 6 0 105 11a6 6 0 0012 0z" />
            </svg>
            <input
              v-model="searchQ"
              type="text"
              placeholder="Buscar por formulario..."
              class="w-full font-cuerpo text-sm border border-gray-300 rounded-lg pl-9 pr-3 py-2
                     focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20 transition"
              @input="onSearchInput"
            />
          </div>
        </div>

        <!-- Desde -->
        <div>
          <label class="block font-cuerpo text-xs font-medium text-gray-500 mb-1">Desde</label>
          <input
            v-model="filterStart"
            type="date"
            class="font-cuerpo text-sm border border-gray-300 rounded-lg px-3 py-2
                   focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20 transition"
            @change="loadForms(1)"
          />
        </div>

        <!-- Hasta -->
        <div>
          <label class="block font-cuerpo text-xs font-medium text-gray-500 mb-1">Hasta</label>
          <input
            v-model="filterEnd"
            type="date"
            class="font-cuerpo text-sm border border-gray-300 rounded-lg px-3 py-2
                   focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20 transition"
            @change="loadForms(1)"
          />
        </div>

        <!-- Limpiar -->
        <button
          v-if="searchQ || filterStart || filterEnd"
          type="button"
          class="font-cuerpo text-sm text-gray-500 border border-gray-300 rounded-lg px-3 py-2
                 hover:bg-gray-50 transition"
          @click="clearFilters"
        >
          Limpiar
        </button>
      </div>
    </div>

    <!-- ══ LISTA DE TRÁMITES ═══════════════════════════════════════════════════ -->
    <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">

      <!-- Loading skeleton -->
      <div v-if="loading" class="divide-y divide-gray-50">
        <div v-for="i in 5" :key="i" class="px-6 py-4 flex items-center gap-4 animate-pulse">
          <div class="w-20 h-6 rounded-full bg-gray-200 flex-shrink-0" />
          <div class="flex-1 space-y-2">
            <div class="w-48 h-4 rounded bg-gray-200" />
            <div class="w-32 h-3 rounded bg-gray-200" />
          </div>
          <div class="w-24 h-4 rounded bg-gray-200 hidden sm:block" />
          <div class="w-8 h-8 rounded-lg bg-gray-200" />
        </div>
      </div>

      <!-- Datos -->
      <div v-else-if="forms.length > 0">
        <!-- Cabecera de tabla (sm+) -->
        <div
          class="hidden sm:grid sm:grid-cols-[140px_1fr_160px_48px] gap-4 px-6 py-3
                 border-b border-gray-100 bg-gray-50/60"
        >
          <span class="font-cuerpo text-xs font-semibold text-gray-500 uppercase tracking-wide">Estado</span>
          <span class="font-cuerpo text-xs font-semibold text-gray-500 uppercase tracking-wide">Formulario</span>
          <span class="font-cuerpo text-xs font-semibold text-gray-500 uppercase tracking-wide">Fecha carga</span>
          <span />
        </div>

        <!-- Filas -->
        <div
          v-for="form in forms"
          :key="form.id"
          class="grid grid-cols-1 sm:grid-cols-[140px_1fr_160px_48px] gap-3 sm:gap-4
                 px-6 py-4 border-b border-gray-50 hover:bg-gray-50/50 transition"
        >
          <!-- Badge estado -->
          <div class="flex items-center">
            <span
              class="inline-flex items-center gap-1.5 font-cuerpo text-xs font-semibold
                     px-2.5 py-1 rounded-full"
              :class="statusBadgeClass(form.estado)"
            >
              <span class="w-1.5 h-1.5 rounded-full" :class="statusDotClass(form.estado)" />
              {{ statusLabel(form.estado) }}
            </span>
          </div>

          <!-- Nombre template -->
          <div class="flex flex-col justify-center min-w-0">
            <p class="font-cuerpo font-medium text-sm text-ubpd-gris truncate">
              {{ form.template_nombre || '—' }}
            </p>
            <p v-if="form.comentario_rechazo" class="font-cuerpo text-xs text-red-400 truncate mt-0.5">
              {{ form.comentario_rechazo }}
            </p>
          </div>

          <!-- Fecha carga -->
          <div class="flex flex-col justify-center">
            <p class="font-cuerpo text-sm text-gray-600">{{ formatDate(form.fecha_carga) }}</p>
            <p class="font-cuerpo text-xs text-gray-400">{{ formatTime(form.fecha_carga) }}</p>
          </div>

          <!-- Menú tres puntos -->
          <div class="flex items-center justify-end">
            <button
              type="button"
              class="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400
                     hover:bg-gray-100 hover:text-ubpd-gris transition"
              :aria-label="`Opciones para ${form.template_nombre}`"
              @click.stop="toggleMenu(form.id, $event)"
            >
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <circle cx="12" cy="5" r="1.5" />
                <circle cx="12" cy="12" r="1.5" />
                <circle cx="12" cy="19" r="1.5" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Paginación -->
        <div v-if="totalPages > 1" class="px-6 py-4 border-t border-gray-100 flex items-center justify-between">
          <p class="font-cuerpo text-sm text-gray-500">
            Página {{ currentPage }} de {{ totalPages }}
            <span class="text-gray-400 ml-1">({{ total }} registros)</span>
          </p>
          <div class="flex items-center gap-1">
            <button
              @click="loadForms(currentPage - 1)"
              :disabled="currentPage === 1"
              class="p-2 rounded-lg border border-gray-200 text-gray-500
                     hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <button
              v-for="p in paginationRange"
              :key="p"
              @click="loadForms(p)"
              class="w-8 h-8 rounded-lg font-cuerpo text-sm transition"
              :class="p === currentPage
                ? 'bg-ubpd-teal text-white'
                : 'border border-gray-200 text-gray-500 hover:bg-gray-50'"
            >
              {{ p }}
            </button>
            <button
              @click="loadForms(currentPage + 1)"
              :disabled="currentPage === totalPages"
              class="p-2 rounded-lg border border-gray-200 text-gray-500
                     hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Sin trámites -->
      <div v-else class="py-16 text-center">
        <div class="w-16 h-16 rounded-2xl bg-ubpd-teal/10 flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8 text-ubpd-teal" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293
                 l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <p class="font-subtitulo font-semibold text-ubpd-gris">No hay trámites</p>
        <p class="font-cuerpo text-sm text-gray-400 mt-1">
          {{ searchQ || filterStart || filterEnd
             ? 'No se encontraron resultados con los filtros aplicados'
             : activeTab !== 'all'
               ? `No tienes trámites en estado "${statusLabel(activeTab)}"`
               : 'Aún no has creado ningún trámite' }}
        </p>
        <RouterLink
          v-if="activeTab === 'all' && !searchQ && !filterStart && !filterEnd"
          to="/dependencia/templates"
          class="mt-4 inline-flex items-center gap-1.5 font-cuerpo text-sm font-medium
                 text-ubpd-teal hover:underline"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Crear mi primer trámite
        </RouterLink>
      </div>
    </div>

    <!-- ══ DROPDOWN MENÚ (Teleport fuera de overflow-hidden) ═══════════════════ -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition ease-out duration-100"
        enter-from-class="opacity-0 scale-95"
        enter-to-class="opacity-100 scale-100"
        leave-active-class="transition ease-in duration-75"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-95"
      >
        <div
          v-if="openMenuId && activeMenuForm"
          :style="{ top: menuStyle.top, left: menuStyle.left }"
          class="fixed z-[9999] w-48 bg-white rounded-xl shadow-xl border border-gray-100 py-1"
          @click.stop
        >
          <!-- Ver detalle -->
          <RouterLink
            :to="`/dependencia/registros/${activeMenuForm.plantilla_id}/${activeMenuForm.id}`"
            class="flex items-center gap-2.5 px-4 py-2.5 font-cuerpo text-sm
                   text-ubpd-gris hover:bg-gray-50 transition"
            @click="openMenuId = null"
          >
            <svg class="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7
                   -1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            Ver detalle
          </RouterLink>

          <!-- Editar (solo draft / rejected) -->
          <RouterLink
            v-if="activeMenuForm.estado === 'draft' || activeMenuForm.estado === 'rejected'"
            :to="`/dependencia/forms/${activeMenuForm.id}`"
            class="flex items-center gap-2.5 px-4 py-2.5 font-cuerpo text-sm
                   text-ubpd-gris hover:bg-gray-50 transition"
            @click="openMenuId = null"
          >
            <svg class="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5
                   m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Editar
          </RouterLink>

          <!-- Separador antes de eliminar -->
          <div v-if="activeMenuForm.estado === 'draft'" class="my-1 border-t border-gray-100" />

          <!-- Eliminar (solo draft) -->
          <button
            v-if="activeMenuForm.estado === 'draft'"
            type="button"
            class="w-full flex items-center gap-2.5 px-4 py-2.5 font-cuerpo text-sm
                   text-red-500 hover:bg-red-50 transition"
            @click="confirmDelete(activeMenuForm)"
          >
            <svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7
                   m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            Eliminar borrador
          </button>
        </div>
      </Transition>
    </Teleport>

    <!-- ══ MODAL CONFIRMAR ELIMINACIÓN ══════════════════════════════════════════ -->
    <ConfirmModal
      :is-open="showDeleteModal"
      title="Eliminar borrador"
      :message="`¿Estás seguro de que quieres eliminar el borrador «${deleteTarget?.template_nombre}»? Esta acción no se puede deshacer.`"
      confirm-text="Eliminar"
      confirm-variant="danger"
      :loading="deleting"
      @confirm="deleteForm"
      @cancel="showDeleteModal = false"
    />

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useNotificationsStore } from '@/stores/notifications'
import ConfirmModal from '@/components/common/ConfirmModal.vue'

// ─── Tipos ────────────────────────────────────────────────────────────────────

interface FormItem {
  id: string
  plantilla_id: string
  estado: 'draft' | 'pending' | 'approved' | 'rejected'
  template_nombre?: string
  fecha_carga: string
  comentario_rechazo?: string
}

interface FormsResponse {
  items: FormItem[]
  total: number
}

// ─── Constantes ───────────────────────────────────────────────────────────────

const PAGE_SIZE = 20

const TABS = [
  { key: 'all',      label: 'Todos'      },
  { key: 'draft',    label: 'Borradores' },
  { key: 'pending',  label: 'En Revisión' },
  { key: 'rejected', label: 'Devueltos'  },
  { key: 'approved', label: 'Aprobados'  },
] as const

type TabKey = (typeof TABS)[number]['key']

// ─── Setup ────────────────────────────────────────────────────────────────────

const { get, del } = useApi()
const notifications = useNotificationsStore()

// ─── Estado ───────────────────────────────────────────────────────────────────

const loading    = ref(true)
const forms      = ref<FormItem[]>([])
const total      = ref(0)
const currentPage = ref(1)
const activeTab  = ref<TabKey>('all')
const filterStart = ref('')
const filterEnd   = ref('')
const searchQ     = ref('')
let   searchTimer: ReturnType<typeof setTimeout> | null = null

// Counts separados — no dependen de los items cargados
const tabCounts = ref<Record<string, number>>({
  all: 0, draft: 0, pending: 0, rejected: 0, approved: 0,
})

// Dropdown de acciones (Teleport a body)
const openMenuId   = ref<string | null>(null)
const menuStyle    = ref({ top: '0px', left: '0px' })
const activeMenuForm = computed(() =>
  forms.value.find((f) => f.id === openMenuId.value) ?? null,
)

// Eliminar
const showDeleteModal = ref(false)
const deleteTarget    = ref<FormItem | null>(null)
const deleting        = ref(false)

// ─── Computed ─────────────────────────────────────────────────────────────────

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

const paginationRange = computed(() => {
  const tp = totalPages.value
  const cp = currentPage.value
  if (tp <= 7) return Array.from({ length: tp }, (_, i) => i + 1)
  const pages: number[] = [1]
  if (cp > 3) pages.push(-1)
  for (let p = Math.max(2, cp - 1); p <= Math.min(tp - 1, cp + 1); p++) pages.push(p)
  if (cp < tp - 2) pages.push(-1)
  pages.push(tp)
  return pages
})

// ─── Carga de datos ───────────────────────────────────────────────────────────

async function loadForms(page = 1) {
  loading.value = true
  currentPage.value = page
  try {
    const params = new URLSearchParams({ page: String(page), size: String(PAGE_SIZE) })
    if (activeTab.value !== 'all') params.set('estado', activeTab.value)
    if (filterStart.value) params.set('start_date', filterStart.value)
    if (filterEnd.value)   params.set('end_date', filterEnd.value)
    if (searchQ.value.trim()) params.set('search', searchQ.value.trim())

    const data = await get<FormsResponse>(`/forms?${params}`)
    forms.value  = data.items
    total.value  = data.total
  } catch {
    notifications.error('No se pudieron cargar los trámites')
  } finally {
    loading.value = false
  }
}

async function loadCounts() {
  try {
    const estados: TabKey[] = ['draft', 'pending', 'rejected', 'approved']
    const results = await Promise.all(
      estados.map((e) =>
        get<FormsResponse>(`/forms?page=1&size=1&estado=${e}`)
          .then((r) => ({ estado: e, count: r.total }))
          .catch(() => ({ estado: e, count: 0 })),
      ),
    )
    let totalAll = 0
    for (const { estado, count } of results) {
      tabCounts.value[estado] = count
      totalAll += count
    }
    tabCounts.value['all'] = totalAll
  } catch {
    // no crítico
  }
}

// ─── Acciones ─────────────────────────────────────────────────────────────────

function setTab(tab: TabKey) {
  activeTab.value = tab
  currentPage.value = 1
  loadForms(1)
}

function clearFilters() {
  searchQ.value = ''
  filterStart.value = ''
  filterEnd.value = ''
  loadForms(1)
}

function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => loadForms(1), 350)
}

function toggleMenu(id: string, event: MouseEvent) {
  if (openMenuId.value === id) {
    openMenuId.value = null
    return
  }
  const btn  = event.currentTarget as HTMLElement
  const rect = btn.getBoundingClientRect()
  const dropdownWidth = 192  // w-48
  const margin = 8           // margen mínimo del borde de pantalla

  // Posición ideal: alineado a la derecha del botón
  const idealLeft = rect.right - dropdownWidth

  // Clampear para que nunca salga por ninguno de los dos bordes
  const clampedLeft = Math.max(margin, Math.min(idealLeft, window.innerWidth - dropdownWidth - margin))

  menuStyle.value = {
    top:  `${rect.bottom + window.scrollY + 4}px`,
    left: `${clampedLeft}px`,
  }
  openMenuId.value = id
}

function closeMenu() {
  openMenuId.value = null
}

function confirmDelete(form: FormItem) {
  deleteTarget.value  = form
  showDeleteModal.value = true
  openMenuId.value    = null
}

async function deleteForm() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await del(`/forms/${deleteTarget.value.id}`)
    notifications.success('Borrador eliminado correctamente')
    showDeleteModal.value = false
    deleteTarget.value    = null
    await Promise.all([loadForms(currentPage.value), loadCounts()])
  } catch {
    notifications.error('No se pudo eliminar el borrador')
  } finally {
    deleting.value = false
  }
}

// ─── Helpers visuales ─────────────────────────────────────────────────────────

function formatDate(d: string): string {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}
function formatTime(d: string): string {
  if (!d) return ''
  return new Date(d).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })
}

function statusLabel(estado: string): string {
  const map: Record<string, string> = {
    draft:    'Borrador',
    pending:  'En Revisión',
    approved: 'Aprobado',
    rejected: 'Devuelto',
  }
  return map[estado] ?? estado
}

function statusBadgeClass(estado: string): string {
  const map: Record<string, string> = {
    draft:    'bg-gray-100 text-gray-600',
    pending:  'bg-yellow-50 text-yellow-700',
    approved: 'bg-ubpd-verde/10 text-ubpd-verde',
    rejected: 'bg-red-50 text-red-600',
  }
  return map[estado] ?? 'bg-gray-100 text-gray-500'
}

function statusDotClass(estado: string): string {
  const map: Record<string, string> = {
    draft:    'bg-gray-400',
    pending:  'bg-yellow-500',
    approved: 'bg-ubpd-verde',
    rejected: 'bg-red-500',
  }
  return map[estado] ?? 'bg-gray-400'
}

// ─── Init ─────────────────────────────────────────────────────────────────────

onMounted(async () => {
  await Promise.all([loadForms(1), loadCounts()])
  window.addEventListener('scroll', closeMenu, { passive: true })
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', closeMenu)
})
</script>
