<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        role="dialog"
        :aria-label="isEditing ? 'Editar dependencia' : 'Nueva dependencia'"
        aria-modal="true"
      >
        <div class="fixed inset-0 bg-black/50 backdrop-blur-sm" @click="handleClose" />

        <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg z-10">
          <!-- Header -->
          <div class="bg-ubpd-teal rounded-t-2xl px-6 py-4 flex items-center justify-between">
            <div>
              <h2 class="font-subtitulo font-bold text-white text-lg">
                {{ isEditing ? 'Editar Dependencia' : 'Nueva Dependencia' }}
              </h2>
              <p class="font-cuerpo text-white/75 text-sm mt-0.5">
                {{ isEditing ? 'Actualice los datos de la dependencia' : 'Registre una nueva dependencia institucional' }}
              </p>
            </div>
            <button @click="handleClose" class="text-white/80 hover:text-white transition" aria-label="Cerrar">
              <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Form -->
          <form class="px-6 py-5 space-y-4" @submit.prevent="handleSubmit" novalidate>
            <!-- Nombre -->
            <div>
              <label for="dep_nombre" class="block font-cuerpo font-medium text-sm text-ubpd-gris mb-1.5">
                Nombre de la dependencia <span class="text-ubpd-naranja">*</span>
              </label>
              <input
                id="dep_nombre"
                v-model="form.nombre"
                type="text"
                placeholder="Ej. Regional Antioquia"
                :disabled="loading"
                class="w-full font-cuerpo text-sm border rounded-lg px-4 py-2.5
                       focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20
                       disabled:bg-gray-50 disabled:cursor-not-allowed transition"
                :class="errors.nombre ? 'border-ubpd-naranja' : 'border-gray-300'"
              />
              <p v-if="errors.nombre" class="mt-1 font-cuerpo text-xs text-ubpd-naranja">{{ errors.nombre }}</p>
            </div>

            <!-- Código -->
            <div>
              <label for="dep_codigo" class="block font-cuerpo font-medium text-sm text-ubpd-gris mb-1.5">
                Código <span class="text-ubpd-naranja">*</span>
              </label>
              <input
                id="dep_codigo"
                v-model="form.codigo"
                type="text"
                placeholder="Ej. REG-ANT-001"
                :disabled="loading"
                class="w-full font-cuerpo text-sm border rounded-lg px-4 py-2.5
                       focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20
                       disabled:bg-gray-50 disabled:cursor-not-allowed transition uppercase"
                :class="errors.codigo ? 'border-ubpd-naranja' : 'border-gray-300'"
              />
              <p v-if="errors.codigo" class="mt-1 font-cuerpo text-xs text-ubpd-naranja">{{ errors.codigo }}</p>
            </div>

            <!-- Descripción -->
            <div>
              <label for="dep_descripcion" class="block font-cuerpo font-medium text-sm text-ubpd-gris mb-1.5">
                Descripción
              </label>
              <textarea
                id="dep_descripcion"
                v-model="form.descripcion"
                rows="3"
                placeholder="Descripción breve de la dependencia..."
                :disabled="loading"
                class="w-full font-cuerpo text-sm border border-gray-300 rounded-lg px-4 py-2.5
                       focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20
                       disabled:bg-gray-50 disabled:cursor-not-allowed transition resize-none"
              />
            </div>

            <!-- Acciones -->
            <div class="flex gap-3 justify-end pt-2">
              <button
                type="button"
                @click="handleClose"
                :disabled="loading"
                class="px-5 py-2.5 rounded-lg font-cuerpo font-medium text-sm
                       border border-gray-300 text-ubpd-gris hover:bg-gray-50 transition disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                :disabled="loading"
                class="px-5 py-2.5 rounded-lg bg-ubpd-teal text-white font-cuerpo font-semibold text-sm
                       hover:bg-[#346d7a] transition disabled:opacity-50 disabled:cursor-not-allowed
                       flex items-center gap-2"
              >
                <svg v-if="loading" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {{ loading ? 'Guardando...' : (isEditing ? 'Actualizar' : 'Crear Dependencia') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { useApi } from '@/composables/useApi'
import { useNotificationsStore } from '@/stores/notifications'

interface DependencyData {
  id?: string
  nombre: string
  codigo: string
  descripcion: string
}

interface Props {
  modelValue: boolean
  editData?: DependencyData | null
}

const props = withDefaults(defineProps<Props>(), { editData: null })

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: [dep: DependencyData]
}>()

const { post, patch } = useApi()
const notifications = useNotificationsStore()

const loading = ref(false)

const form = reactive<DependencyData>({
  nombre: '',
  codigo: '',
  descripcion: '',
})

const errors = reactive({ nombre: '', codigo: '' })

const isEditing = computed(() => !!props.editData?.id)

watch(() => props.editData, (data) => {
  if (data) {
    form.nombre = data.nombre
    form.codigo = data.codigo
    form.descripcion = data.descripcion
  } else {
    resetForm()
  }
}, { immediate: true })

function resetForm() {
  form.nombre = ''
  form.codigo = ''
  form.descripcion = ''
  errors.nombre = ''
  errors.codigo = ''
}

function validate(): boolean {
  errors.nombre = ''
  errors.codigo = ''
  let valid = true
  if (!form.nombre.trim()) { errors.nombre = 'El nombre es obligatorio'; valid = false }
  if (!form.codigo.trim()) { errors.codigo = 'El código es obligatorio'; valid = false }
  return valid
}

async function handleSubmit() {
  if (!validate()) return
  loading.value = true
  try {
    let saved: DependencyData
    if (isEditing.value && props.editData?.id) {
      saved = await patch<DependencyData>(`/admin/dependencies/${props.editData.id}`, { ...form })
      notifications.success('Dependencia actualizada exitosamente')
    } else {
      saved = await post<DependencyData>('/admin/dependencies', { ...form })
      notifications.success('Dependencia creada exitosamente')
    }
    emit('saved', saved)
    handleClose()
  } catch (err: unknown) {
    const axiosErr = err as { response?: { data?: { detail?: string } } }
    notifications.error(axiosErr?.response?.data?.detail || 'Error al guardar la dependencia')
  } finally {
    loading.value = false
  }
}

function handleClose() {
  if (!loading.value) {
    emit('update:modelValue', false)
    resetForm()
  }
}
</script>

<style scoped>
.modal-enter-active, .modal-leave-active { transition: opacity 0.2s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
