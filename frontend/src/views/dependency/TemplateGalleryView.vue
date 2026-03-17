<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold font-montserrat text-ubpd-gris">Formularios disponibles</h1>
      <p class="text-sm font-barlow text-gray-500 mt-0.5">
        Selecciona un template para iniciar un nuevo formulario
      </p>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <div
        v-for="n in 6"
        :key="n"
        class="bg-white rounded-xl border border-gray-200 shadow-sm p-5 space-y-3 animate-pulse"
      >
        <div class="h-5 bg-gray-200 rounded w-3/4" />
        <div class="h-4 bg-gray-100 rounded w-full" />
        <div class="h-4 bg-gray-100 rounded w-5/6" />
        <div class="h-8 bg-gray-200 rounded mt-4 w-1/3" />
      </div>
    </div>

    <!-- Template grid -->
    <div v-else-if="templates.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <div
        v-for="tmpl in templates"
        :key="tmpl.id"
        class="bg-white rounded-xl border border-gray-200 shadow-sm p-5 flex flex-col gap-3
               hover:shadow-md hover:border-ubpd-teal transition-all duration-200"
      >
        <!-- Indicator tag -->
        <span class="inline-flex w-fit items-center px-2 py-0.5 rounded-full text-xs font-semibold font-barlow bg-purple-100 text-ubpd-morado">
          {{ tmpl.indicador_nombre ?? 'Indicador' }}
        </span>

        <!-- Name & description -->
        <h2 class="text-base font-semibold font-montserrat text-ubpd-gris leading-snug">
          {{ tmpl.nombre }}
        </h2>
        <p class="text-sm font-barlow text-gray-500 flex-1 line-clamp-3">
          {{ tmpl.descripcion ?? 'Sin descripción disponible.' }}
        </p>

        <!-- CTA -->
        <button
          type="button"
          class="mt-2 w-full py-2 bg-ubpd-teal text-white font-semibold font-barlow text-sm rounded-lg
                 hover:bg-teal-700 transition-colors"
          @click="startForm(tmpl.id)"
        >
          Iniciar Formulario
        </button>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="text-center py-16 text-gray-400">
      <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 256 256" fill="currentColor" class="mx-auto mb-3 opacity-40" aria-hidden="true">
        <path d="M213.66,82.34l-56-56A8,8,0,0,0,152,24H56A16,16,0,0,0,40,40V216a16,16,0,0,0,16,16H200a16,16,0,0,0,16-16V88A8,8,0,0,0,213.66,82.34ZM160,51.31,188.69,80H160ZM200,216H56V40h88V88a8,8,0,0,0,8,8h48V216Z"/>
      </svg>
      <p class="text-base font-barlow">No hay formularios disponibles para tu dependencia.</p>
      <p class="text-sm mt-1">Contacta al administrador para obtener acceso.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'

interface Template {
  id: string
  nombre: string
  descripcion: string | null
  indicador_nivel1_id: number
  indicador_nombre?: string
}

const { get } = useApi()
const authStore = useAuthStore()
const notifications = useNotificationsStore()
const router = useRouter()

const loading = ref(true)
const templates = ref<Template[]>([])

async function loadTemplates() {
  loading.value = true
  const depId = authStore.user?.dependency_id
  if (!depId) {
    notifications.warning('Sin dependencia', 'Tu usuario no tiene una dependencia asignada.')
    loading.value = false
    return
  }
  try {
    templates.value = await get<Template[]>(`/templates/by-dependency/${depId}`)
  } catch {
    notifications.error('Error', 'No se pudieron cargar los formularios disponibles.')
  } finally {
    loading.value = false
  }
}

function startForm(templateId: string) {
  router.push(`/dependencia/forms/new/${templateId}`)
}

onMounted(loadTemplates)
</script>
