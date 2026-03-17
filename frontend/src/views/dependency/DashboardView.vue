<template>
  <div class="space-y-8">
    <!-- Welcome header -->
    <div>
      <h1 class="text-2xl font-bold font-montserrat text-ubpd-gris">
        Bienvenido, {{ user?.nombre_completo?.split(' ')[0] ?? 'Usuario' }}
      </h1>
      <p class="text-sm font-barlow text-gray-500 mt-0.5">
        {{ dependenciaNombre }} — Panel de gestión de formularios
      </p>
    </div>

    <!-- Status summary cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- Borradores -->
      <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-5 flex flex-col gap-2">
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold font-barlow text-gray-500 uppercase tracking-wide">Borradores</span>
          <span class="text-gray-300">✏️</span>
        </div>
        <p class="text-3xl font-bold font-barlow text-ubpd-gris">
          {{ loading ? '—' : counts.draft }}
        </p>
      </div>

      <!-- En Revisión -->
      <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-5 flex flex-col gap-2">
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold font-barlow text-gray-500 uppercase tracking-wide">En Revisión</span>
          <span class="text-ubpd-teal">🕐</span>
        </div>
        <p class="text-3xl font-bold font-barlow text-ubpd-teal">
          {{ loading ? '—' : counts.pending }}
        </p>
      </div>

      <!-- Devueltos -->
      <div
        class="bg-white rounded-xl border shadow-sm p-5 flex flex-col gap-2"
        :class="counts.rejected > 0 ? 'border-ubpd-naranja bg-orange-50' : 'border-gray-200'"
      >
        <div class="flex items-center justify-between">
          <span
            class="text-xs font-semibold font-barlow uppercase tracking-wide"
            :class="counts.rejected > 0 ? 'text-ubpd-naranja' : 'text-gray-500'"
          >
            Devueltos
          </span>
          <span :class="counts.rejected > 0 ? 'text-ubpd-naranja' : 'text-gray-300'">⚠️</span>
        </div>
        <p
          class="text-3xl font-bold font-barlow"
          :class="counts.rejected > 0 ? 'text-ubpd-naranja' : 'text-ubpd-gris'"
        >
          {{ loading ? '—' : counts.rejected }}
        </p>
        <p v-if="counts.rejected > 0" class="text-xs text-ubpd-naranja font-barlow">
          Requieren corrección
        </p>
      </div>

      <!-- Aprobados -->
      <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-5 flex flex-col gap-2">
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold font-barlow text-gray-500 uppercase tracking-wide">Aprobados</span>
          <span class="text-ubpd-verde">✓</span>
        </div>
        <p class="text-3xl font-bold font-barlow text-ubpd-verde">
          {{ loading ? '—' : counts.approved }}
        </p>
      </div>
    </div>

    <!-- Recently returned forms -->
    <div v-if="rejectedForms.length > 0">
      <h2 class="text-lg font-semibold font-montserrat text-ubpd-gris mb-3">
        Formularios devueltos recientes
      </h2>
      <div class="space-y-3">
        <div
          v-for="form in rejectedForms"
          :key="form.id"
          class="bg-orange-50 border border-ubpd-naranja rounded-xl p-4 flex items-start justify-between gap-4"
        >
          <div class="flex-1 min-w-0">
            <p class="font-semibold text-ubpd-gris font-barlow truncate">{{ form.template_nombre }}</p>
            <p class="text-xs text-gray-500 font-barlow mt-0.5">
              Devuelto el {{ formatDate(form.fecha_ultima_edicion) }}
            </p>
            <p v-if="form.comentario_rechazo" class="text-sm text-ubpd-naranja font-barlow mt-1 line-clamp-2">
              {{ form.comentario_rechazo }}
            </p>
          </div>
          <RouterLink
            :to="`/dependencia/forms/${form.id}`"
            class="shrink-0 px-4 py-2 bg-ubpd-naranja text-white text-sm font-semibold font-barlow rounded-lg hover:bg-orange-600 transition-colors"
          >
            Revisar
          </RouterLink>
        </div>
      </div>
    </div>

    <!-- Quick actions -->
    <div>
      <h2 class="text-lg font-semibold font-montserrat text-ubpd-gris mb-3">Acciones rápidas</h2>
      <div class="flex flex-wrap gap-3">
        <RouterLink
          to="/dependencia/templates"
          class="px-5 py-2.5 bg-ubpd-teal text-white font-semibold font-barlow text-sm rounded-lg hover:bg-teal-700 transition-colors"
        >
          + Nuevo Formulario
        </RouterLink>
        <RouterLink
          to="/dependencia/inbox"
          class="px-5 py-2.5 border border-ubpd-teal text-ubpd-teal font-semibold font-barlow text-sm rounded-lg hover:bg-teal-50 transition-colors"
        >
          Ver mis trámites
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import type { FormData, FormStatus } from '@/types/forms'

const { get } = useApi()
const authStore = useAuthStore()
const notifications = useNotificationsStore()

const user = computed(() => authStore.user)

const loading = ref(true)
const dependenciaNombre = ref('')
const allForms = ref<FormData[]>([])

const counts = computed(() => {
  const result: Record<FormStatus, number> = { draft: 0, pending: 0, rejected: 0, approved: 0 }
  for (const f of allForms.value) {
    if (f.estado in result) result[f.estado]++
  }
  return result
})

const rejectedForms = computed(() =>
  allForms.value
    .filter((f) => f.estado === 'rejected')
    .slice(0, 5),
)

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('es-CO', { day: 'numeric', month: 'long', year: 'numeric' })
}

async function loadData() {
  loading.value = true
  try {
    const forms = await get<FormData[]>('/forms?group_by_status')
    allForms.value = forms

    // Try to get dependency name from the first form or from user context
    if (forms.length > 0 && forms[0].dependencia_nombre) {
      dependenciaNombre.value = forms[0].dependencia_nombre
    }
  } catch (err) {
    notifications.error('Error al cargar el dashboard', 'No se pudieron obtener los datos de tus formularios.')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>
