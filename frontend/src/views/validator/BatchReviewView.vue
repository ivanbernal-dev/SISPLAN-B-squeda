<template>
  <div class="p-6 space-y-5">

    <!-- Breadcrumb -->
    <nav class="flex items-center gap-2 text-sm font-barlow text-gray-400">
      <RouterLink to="/validator/inbox" class="hover:text-ubpd-teal transition-colors">Bandeja</RouterLink>
      <span>›</span>
      <span class="text-ubpd-gris font-semibold">Revisión de carga Excel</span>
    </nav>

    <!-- Loading -->
    <div v-if="loading" class="space-y-4">
      <div class="bg-white rounded-2xl border border-gray-100 p-6 animate-pulse">
        <div class="h-5 bg-gray-200 rounded w-1/3 mb-3" />
        <div class="h-4 bg-gray-100 rounded w-1/4" />
      </div>
      <div class="bg-white rounded-2xl border border-gray-100 p-6 animate-pulse h-48" />
    </div>

    <template v-else-if="lote">

      <!-- Info del lote -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div class="space-y-1">
            <h1 class="font-montserrat font-bold text-xl text-ubpd-gris">
              {{ lote.template_nombre }}
            </h1>
            <p class="font-barlow text-sm text-gray-500">
              <span class="font-medium text-ubpd-gris">Dependencia:</span> {{ lote.dependencia_nombre }}
              &nbsp;·&nbsp;
              <span class="font-medium text-ubpd-gris">Cargado por:</span> {{ lote.usuario_nombre }}
              &nbsp;·&nbsp;
              {{ formatDate(lote.fecha_carga) }}
            </p>
          </div>
          <div class="flex items-center gap-2">
            <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full
                         bg-ubpd-teal/10 text-ubpd-teal font-cuerpo text-sm font-semibold">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414A1 1 0 0119 9.414V19a2 2 0 01-2 2z"/>
              </svg>
              {{ lote.total_registros }} registros
            </span>
          </div>
        </div>
      </div>

      <!-- Tabla de registros -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div class="px-5 py-3 border-b border-gray-100 flex items-center gap-2">
          <svg class="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M3 10h18M3 14h18M10 6h4M10 18h4"/>
          </svg>
          <p class="font-cuerpo text-sm font-semibold text-ubpd-gris">
            Registros del lote
          </p>
          <span class="ml-auto font-cuerpo text-xs text-gray-400">
            Revisa cada fila antes de validar
          </span>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-sm font-cuerpo">
            <thead>
              <tr class="bg-gray-50 border-b border-gray-100">
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide w-10">#</th>
                <th
                  v-for="campo in columnasMostrar"
                  :key="campo.key"
                  class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap"
                >
                  {{ campo.label }}
                </th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Informe</th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Fecha ref.</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr
                v-for="(reg, idx) in lote.registros"
                :key="reg._id"
                class="hover:bg-gray-50/50 transition"
                :class="reg._estado === 'approved' ? 'bg-green-50/30' : reg._estado === 'rejected' ? 'bg-red-50/30' : ''"
              >
                <td class="px-4 py-3 text-gray-400 font-mono text-xs">{{ idx + 1 }}</td>
                <td
                  v-for="campo in columnasMostrar"
                  :key="campo.key"
                  class="px-4 py-3 text-gray-700 max-w-[200px]"
                >
                  <span class="line-clamp-2">{{ reg[campo.key] ?? '—' }}</span>
                </td>
                <td class="px-4 py-3 text-gray-600 max-w-[220px]">
                  <span class="line-clamp-2 text-xs">{{ reg.informe_cualitativo || '—' }}</span>
                </td>
                <td class="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">
                  {{ reg.fecha_referencia || '—' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Botones de acción -->
      <div v-if="pendingCount > 0" class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
        <p class="font-cuerpo text-sm text-gray-500 mb-4">
          <strong class="text-ubpd-gris">{{ pendingCount }}</strong> registro(s) pendientes de validación.
          La acción se aplicará a todos a la vez.
        </p>
        <div class="flex flex-wrap gap-3">
          <button
            @click="doApprove"
            :disabled="actionLoading"
            class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-ubpd-verde text-white
                   font-cuerpo font-semibold text-sm hover:opacity-90 disabled:opacity-50 transition"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
            Aprobar todos ({{ pendingCount }})
          </button>
          <button
            @click="showRejectModal = true"
            :disabled="actionLoading"
            class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-red-500 text-white
                   font-cuerpo font-semibold text-sm hover:opacity-90 disabled:opacity-50 transition"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
            Rechazar lote
          </button>
        </div>
      </div>

      <!-- Ya procesado -->
      <div v-else class="bg-green-50 border border-green-100 rounded-2xl p-5 flex items-center gap-3">
        <svg class="w-6 h-6 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <p class="font-cuerpo text-sm text-green-800 font-medium">Este lote ya fue procesado.</p>
      </div>

    </template>

    <!-- Modal rechazar -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showRejectModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="showRejectModal = false" />
          <div class="relative bg-white rounded-2xl shadow-2xl max-w-md w-full z-10 p-6 space-y-4">
            <h3 class="font-montserrat font-bold text-ubpd-gris text-lg">Rechazar lote completo</h3>
            <p class="font-cuerpo text-sm text-gray-500">
              Indica el motivo del rechazo. El usuario podrá ver este comentario.
            </p>
            <textarea
              v-model="rejectComentario"
              rows="4"
              placeholder="Explica el motivo del rechazo (mínimo 10 caracteres)..."
              class="w-full border border-gray-300 rounded-xl px-4 py-3 font-cuerpo text-sm
                     focus:outline-none focus:border-ubpd-teal focus:ring-2 focus:ring-ubpd-teal/20
                     resize-none transition"
            />
            <div class="flex gap-3 pt-1">
              <button
                @click="showRejectModal = false"
                class="flex-1 px-4 py-2.5 rounded-xl border border-gray-300 font-cuerpo text-sm text-gray-600 hover:bg-gray-50 transition"
              >
                Cancelar
              </button>
              <button
                @click="doReject"
                :disabled="rejectComentario.trim().length < 10 || actionLoading"
                class="flex-1 px-4 py-2.5 rounded-xl bg-red-500 text-white font-cuerpo font-semibold text-sm
                       hover:opacity-90 disabled:opacity-50 transition"
              >
                Confirmar rechazo
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useNotificationsStore } from '@/stores/notifications'

interface LoteDetalle {
  lote_id: string
  template_nombre: string
  dependencia_nombre: string
  usuario_nombre: string
  fecha_carga: string
  total_registros: number
  campos: string[]
  registros: Record<string, any>[]
}

const route = useRoute()
const router = useRouter()
const { get, post } = useApi()
const notifications = useNotificationsStore()

const loteId = computed(() => route.params.loteId as string)
const loading = ref(true)
const actionLoading = ref(false)
const lote = ref<LoteDetalle | null>(null)
const showRejectModal = ref(false)
const rejectComentario = ref('')

// Columnas a mostrar: hasta 5 campos del template (excluir metadatos internos)
const columnasMostrar = computed(() => {
  if (!lote.value) return []
  const primeros = lote.value.campos.slice(0, 5)
  // Intentar extraer las keys del primer registro
  const primeraFila = lote.value.registros[0] || {}
  const keys = Object.keys(primeraFila).filter(k => !k.startsWith('_') && k !== 'informe_cualitativo' && k !== 'fecha_referencia')
  return primeros.map((label, i) => ({
    label,
    key: keys[i] || label,
  })).filter(c => c.key)
})

const pendingCount = computed(() =>
  (lote.value?.registros || []).filter(r => r._estado === 'pending').length
)

async function loadLote() {
  loading.value = true
  try {
    lote.value = await get<LoteDetalle>(`/validation/lotes/${loteId.value}`)
  } catch {
    notifications.error('No se pudo cargar el lote')
    router.push('/validator/inbox')
  } finally {
    loading.value = false
  }
}

async function doApprove() {
  actionLoading.value = true
  try {
    const res = await post<{ aprobados: number; mensaje: string }>(
      `/validation/lotes/${loteId.value}/approve`, {}
    )
    notifications.success(res.mensaje)
    await loadLote()
  } catch (e: any) {
    notifications.error(e?.message ?? 'Error al aprobar el lote')
  } finally {
    actionLoading.value = false
  }
}

async function doReject() {
  if (rejectComentario.value.trim().length < 10) return
  actionLoading.value = true
  showRejectModal.value = false
  try {
    const res = await post<{ rechazados: number; mensaje: string }>(
      `/validation/lotes/${loteId.value}/reject`,
      { comentario: rejectComentario.value.trim() }
    )
    notifications.success(res.mensaje)
    rejectComentario.value = ''
    await loadLote()
  } catch (e: any) {
    notifications.error(e?.message ?? 'Error al rechazar el lote')
  } finally {
    actionLoading.value = false
  }
}

function formatDate(d: string): string {
  return new Date(d).toLocaleDateString('es-CO', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

onMounted(loadLote)
</script>

<style scoped>
.modal-enter-active, .modal-leave-active { transition: opacity 0.2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
