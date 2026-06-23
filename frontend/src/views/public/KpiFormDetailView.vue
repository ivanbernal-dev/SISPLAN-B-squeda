<template>
  <div class="min-h-screen bg-gray-50">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6">

    <!-- Breadcrumb ───────────────────────────────────────────── -->
    <nav class="flex items-center gap-2 text-sm font-barlow text-gray-500 flex-wrap">
      <RouterLink to="/estadisticas" class="hover:text-ubpd-teal transition-colors">Plan de Acción Institucional 2026</RouterLink>
      <span>›</span>
      <RouterLink :to="`/estadisticas/${kpiKey}`" class="hover:text-ubpd-teal transition-colors">
        {{ route.query.kpiLabel || kpiKey }}
      </RouterLink>
      <span>›</span>
      <RouterLink
        :to="`/estadisticas/${kpiKey}/forms/${subKpiKey}`"
        class="hover:text-ubpd-teal transition-colors"
      >
        {{ route.query.subLabel || subKpiKey }}
      </RouterLink>
      <span>›</span>
      <span class="text-ubpd-gris font-semibold">Detalle</span>
    </nav>

    <!-- Loading ──────────────────────────────────────────────── -->
    <div v-if="loading" class="space-y-4 animate-pulse">
      <div class="h-8 bg-gray-200 rounded w-1/2" />
      <div class="h-4 bg-gray-100 rounded w-1/3" />
      <div class="h-64 bg-gray-100 rounded-xl" />
    </div>

    <!-- Detalle ─────────────────────────────────────────────── -->
    <template v-else-if="form">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold font-montserrat text-ubpd-gris">
            {{ route.query.templateNombre || 'Detalle de Formulario' }}
          </h1>
          <p class="text-sm font-barlow text-gray-500 mt-0.5">
            {{ form.dependency }} — {{ formatDate(form.fecha_usuario) }}
          </p>
        </div>
        <span class="inline-flex items-center gap-1.5 font-barlow text-xs font-semibold px-3 py-1.5 rounded-full
                     bg-ubpd-verde/10 text-ubpd-verde">
          <span class="w-1.5 h-1.5 rounded-full bg-ubpd-verde" />
          Aprobado
        </span>
      </div>

      <!-- Metadata card ───────────────────────────────────────── -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
        <h2 class="font-subtitulo font-semibold text-sm text-ubpd-gris mb-3">Información del registro</h2>
        <dl class="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <div>
            <dt class="font-cuerpo text-xs text-gray-400 uppercase tracking-wide">Dependencia</dt>
            <dd class="font-cuerpo text-sm font-medium text-ubpd-gris mt-0.5">{{ form.dependency }}</dd>
          </div>
          <div>
            <dt class="font-cuerpo text-xs text-gray-400 uppercase tracking-wide">Responsable</dt>
            <dd class="font-cuerpo text-sm font-medium text-ubpd-gris mt-0.5">{{ form.usuario }}</dd>
          </div>
          <div>
            <dt class="font-cuerpo text-xs text-gray-400 uppercase tracking-wide">Fecha registro</dt>
            <dd class="font-cuerpo text-sm font-medium text-ubpd-gris mt-0.5">{{ formatDate(form.fecha_usuario) }}</dd>
          </div>
          <div>
            <dt class="font-cuerpo text-xs text-gray-400 uppercase tracking-wide">Fecha carga</dt>
            <dd class="font-cuerpo text-sm font-medium text-ubpd-gris mt-0.5">{{ formatDate(form.fecha_carga) }}</dd>
          </div>
        </dl>
      </div>

      <!-- Datos dinámicos ──────────────────────────────────────── -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
        <h2 class="font-subtitulo font-semibold text-sm text-ubpd-gris mb-4">Campos del formulario</h2>
        <dl class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div
            v-for="(val, key) in form.datos_dinamicos"
            :key="key"
            class="bg-gray-50 rounded-xl px-4 py-3"
          >
            <dt class="font-cuerpo text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
              {{ formatKey(String(key)) }}
            </dt>
            <dd class="font-cuerpo text-sm text-ubpd-gris break-words">
              {{ val !== null && val !== '' ? val : '—' }}
            </dd>
          </div>
        </dl>
      </div>
    </template>

    <!-- Error / no encontrado ────────────────────────────────── -->
    <div v-else class="text-center py-20 text-gray-400">
      <p class="font-barlow text-base">Formulario no encontrado.</p>
      <RouterLink
        :to="`/estadisticas/${kpiKey}/forms/${subKpiKey}`"
        class="mt-3 inline-block font-barlow text-sm text-ubpd-teal hover:underline"
      >
        ← Volver a la lista
      </RouterLink>
    </div>

  </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useApi } from '@/composables/useApi'

interface FormDetail {
  id: string
  dependency: string
  usuario: string
  fecha_carga: string | null
  fecha_usuario: string | null
  datos_dinamicos: Record<string, any>
  estado: string
}

const route = useRoute()
const { get } = useApi()

const loading = ref(true)
const form = ref<FormDetail | null>(null)

const kpiKey = computed(() => route.params.kpiKey as string)
const subKpiKey = computed(() => route.params.subKpiKey as string)
const formId = computed(() => route.params.formId as string)

function formatDate(s: string | null | undefined): string {
  if (!s) return '—'
  try {
    return new Date(s).toLocaleDateString('es-CO', { day: 'numeric', month: 'long', year: 'numeric' })
  } catch { return s }
}

function formatKey(k: string): string {
  return k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

onMounted(async () => {
  loading.value = true
  try {
    const data = await get<any>(`/forms/${formId.value}`)
    // Normalizar respuesta del endpoint existente
    form.value = {
      id: data.id,
      dependency: data.dependencia_nombre ?? data.dependency?.nombre ?? '—',
      usuario: data.usuario_nombre ?? data.usuario?.nombre_completo ?? '—',
      fecha_carga: data.fecha_carga,
      fecha_usuario: data.fecha_usuario,
      datos_dinamicos: data.datos_dinamicos ?? {},
      estado: data.estado,
    }
  } catch {
    form.value = null
  } finally {
    loading.value = false
  }
})
</script>
