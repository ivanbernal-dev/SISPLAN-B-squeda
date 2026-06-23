<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-start justify-center p-4 pt-16 overflow-y-auto"
        role="dialog"
        :aria-label="isEditing ? 'Editar usuario' : 'Nuevo usuario'"
        aria-modal="true"
      >
        <!-- Overlay -->
        <div class="fixed inset-0 bg-black/50 backdrop-blur-sm" @click="handleClose" />

        <!-- Panel -->
        <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg z-10 mb-8">
          <!-- Header -->
          <div class="bg-ubpd-teal rounded-t-2xl px-6 py-4 flex items-center justify-between">
            <div>
              <h2 class="font-subtitulo font-bold text-white text-lg">
                {{ isEditing ? 'Editar Usuario' : (createdPassword ? 'Usuario creado' : 'Nuevo Usuario') }}
              </h2>
              <p class="font-cuerpo text-white/75 text-sm mt-0.5">
                {{ isEditing
                  ? 'Actualice los datos del usuario'
                  : (createdPassword ? 'Guarda la contraseña temporal antes de cerrar' : 'Complete los datos para registrar un nuevo usuario') }}
              </p>
            </div>
            <button @click="handleClose" class="text-white/80 hover:text-white transition" aria-label="Cerrar">
              <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- ── Panel de éxito: contraseña temporal ── -->
          <div v-if="createdPassword" class="px-6 py-5 space-y-4">
            <div class="flex items-start gap-3 bg-green-50 border border-green-200 rounded-xl px-4 py-3">
              <svg class="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p class="font-cuerpo text-xs text-green-800">
                El usuario ha sido creado. Entrega la siguiente contraseña temporal —
                <strong>no podrá recuperarse</strong> después de cerrar esta ventana.
              </p>
            </div>

            <!-- Contraseña -->
            <div>
              <label class="block font-cuerpo font-medium text-sm text-ubpd-gris mb-1.5">
                Contraseña temporal
              </label>
              <div class="flex items-center gap-2 border border-gray-300 rounded-lg px-3 py-2.5 bg-gray-50">
                <code class="flex-1 font-mono text-sm text-ubpd-gris select-all tracking-wide">{{ createdPassword }}</code>
                <button
                  type="button"
                  @click="copyPassword"
                  class="p-1.5 rounded-md text-ubpd-teal hover:bg-ubpd-teal/10 transition"
                  :title="copied ? 'Copiado' : 'Copiar contraseña'"
                >
                  <svg v-if="!copied" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <svg v-else class="w-4 h-4 text-ubpd-verde" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                </button>
              </div>
              <p class="mt-1.5 font-cuerpo text-xs text-gray-500">
                El usuario deberá cambiarla en su primer ingreso al sistema.
              </p>
            </div>

            <div class="pt-1">
              <button
                type="button"
                @click="handleClose"
                class="w-full px-5 py-2.5 rounded-lg bg-ubpd-teal text-white font-cuerpo font-semibold text-sm
                       hover:bg-[#346d7a] transition"
              >
                Cerrar
              </button>
            </div>
          </div>

          <!-- ── Formulario ── -->
          <form v-else class="px-6 py-5 space-y-4" @submit.prevent="handleSubmit" novalidate>
            <!-- Nombre completo -->
            <div>
              <label for="nombre_completo" class="block font-cuerpo font-medium text-sm text-ubpd-gris mb-1.5">
                Nombre completo <span class="text-ubpd-naranja">*</span>
              </label>
              <input
                id="nombre_completo"
                v-model="form.nombre_completo"
                type="text"
                placeholder="Ej. María Alejandra Torres"
                :disabled="loading"
                class="w-full font-cuerpo text-sm border rounded-lg px-4 py-2.5
                       focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20
                       disabled:bg-gray-50 disabled:cursor-not-allowed transition"
                :class="errors.nombre_completo ? 'border-ubpd-naranja' : 'border-gray-300'"
              />
              <p v-if="errors.nombre_completo" class="mt-1 font-cuerpo text-xs text-ubpd-naranja">{{ errors.nombre_completo }}</p>
            </div>

            <!-- Username -->
            <div>
              <label for="username" class="block font-cuerpo font-medium text-sm text-ubpd-gris mb-1.5">
                Nombre de usuario <span class="text-ubpd-naranja">*</span>
              </label>
              <input
                id="username"
                v-model="form.username"
                type="text"
                placeholder="Ej. matorres"
                :disabled="loading || isEditing"
                class="w-full font-cuerpo text-sm border rounded-lg px-4 py-2.5
                       focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20
                       disabled:bg-gray-50 disabled:cursor-not-allowed transition"
                :class="errors.username ? 'border-ubpd-naranja' : 'border-gray-300'"
              />
              <p v-if="isEditing" class="mt-1 font-cuerpo text-xs text-gray-400">El nombre de usuario no puede modificarse</p>
              <p v-if="errors.username" class="mt-1 font-cuerpo text-xs text-ubpd-naranja">{{ errors.username }}</p>
            </div>

            <!-- Email -->
            <div>
              <label for="email" class="block font-cuerpo font-medium text-sm text-ubpd-gris mb-1.5">
                Correo electrónico <span class="text-ubpd-naranja">*</span>
              </label>
              <input
                id="email"
                v-model="form.email"
                type="email"
                placeholder="usuario@ubpd.gov.co"
                :disabled="loading"
                class="w-full font-cuerpo text-sm border rounded-lg px-4 py-2.5
                       focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20
                       disabled:bg-gray-50 disabled:cursor-not-allowed transition"
                :class="errors.email ? 'border-ubpd-naranja' : 'border-gray-300'"
              />
              <p v-if="errors.email" class="mt-1 font-cuerpo text-xs text-ubpd-naranja">{{ errors.email }}</p>
            </div>

            <!-- Rol -->
            <div>
              <label for="role" class="block font-cuerpo font-medium text-sm text-ubpd-gris mb-1.5">
                Rol <span class="text-ubpd-naranja">*</span>
              </label>
              <select
                id="role"
                v-model="form.role"
                :disabled="loading"
                class="w-full font-cuerpo text-sm border rounded-lg px-4 py-2.5
                       focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20
                       disabled:bg-gray-50 disabled:cursor-not-allowed transition"
                :class="errors.role ? 'border-ubpd-naranja' : 'border-gray-300'"
              >
                <option value="">Seleccione un rol</option>
                <option value="admin">Administrador</option>
                <option value="validator">Validador</option>
                <option value="dependency_user">Usuario de Dependencia</option>
              </select>
              <p v-if="errors.role" class="mt-1 font-cuerpo text-xs text-ubpd-naranja">{{ errors.role }}</p>
            </div>

            <!-- Dependencia (solo para dependency_user) -->
            <Transition name="fade">
              <div v-if="form.role === 'dependency_user'">
                <label for="dependency_id" class="block font-cuerpo font-medium text-sm text-ubpd-gris mb-1.5">
                  Dependencia <span class="text-ubpd-naranja">*</span>
                </label>
                <select
                  id="dependency_id"
                  v-model="form.dependency_id"
                  :disabled="loading || loadingDeps"
                  class="w-full font-cuerpo text-sm border rounded-lg px-4 py-2.5
                         focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20
                         disabled:bg-gray-50 disabled:cursor-not-allowed transition"
                  :class="errors.dependency_id ? 'border-ubpd-naranja' : 'border-gray-300'"
                >
                  <option value="">{{ loadingDeps ? 'Cargando dependencias...' : 'Seleccione una dependencia' }}</option>
                  <option
                    v-for="dep in dependencies"
                    :key="dep.id"
                    :value="dep.id"
                  >
                    {{ dep.nombre }}
                  </option>
                </select>
                <p v-if="errors.dependency_id" class="mt-1 font-cuerpo text-xs text-ubpd-naranja">{{ errors.dependency_id }}</p>
              </div>
            </Transition>

            <!-- Info contraseña temporal para nuevos usuarios -->
            <div v-if="!isEditing" class="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 flex gap-2">
              <svg class="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p class="font-cuerpo text-xs text-blue-700">
                Se generará una contraseña temporal. El usuario deberá cambiarla en su primer ingreso.
              </p>
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
                {{ loading ? 'Guardando...' : (isEditing ? 'Actualizar' : 'Crear Usuario') }}
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

interface Dependency {
  id: string
  nombre: string
}

interface UserData {
  id?: string
  nombre_completo: string
  username: string
  email: string
  role: string
  dependency_id: string | null
  activo?: boolean
}

interface UserCreateResponse {
  id: string
  username: string
  requires_password_change: boolean
  temp_password: string
}

interface Props {
  modelValue: boolean
  editData?: UserData | null
}

const props = withDefaults(defineProps<Props>(), {
  editData: null,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: [user: UserData]
}>()

const { get, post, patch } = useApi()
const notifications = useNotificationsStore()

const loading = ref(false)
const loadingDeps = ref(false)
const dependencies = ref<Dependency[]>([])

// Estado del panel de contraseña temporal
const createdPassword = ref<string | null>(null)
const copied = ref(false)

const form = reactive<UserData>({
  nombre_completo: '',
  username: '',
  email: '',
  role: '',
  dependency_id: null,
})

const errors = reactive({
  nombre_completo: '',
  username: '',
  email: '',
  role: '',
  dependency_id: '',
})

const isEditing = computed(() => !!props.editData?.id)

// Cargar dependencias cuando sea necesario
async function loadDependencies() {
  if (dependencies.value.length > 0) return
  loadingDeps.value = true
  try {
    const data = await get<Dependency[]>('/admin/dependencies')
    dependencies.value = data
  } catch {
    notifications.error('No se pudieron cargar las dependencias')
  } finally {
    loadingDeps.value = false
  }
}

watch(() => form.role, (newRole) => {
  if (newRole === 'dependency_user') {
    loadDependencies()
  } else {
    form.dependency_id = null
  }
})

// Poblar form cuando se edita
watch(() => props.editData, (data) => {
  if (data) {
    form.nombre_completo = data.nombre_completo
    form.username = data.username
    form.email = data.email
    form.role = data.role
    form.dependency_id = data.dependency_id
    if (data.role === 'dependency_user') loadDependencies()
  } else {
    resetForm()
  }
}, { immediate: true })

function resetForm() {
  form.nombre_completo = ''
  form.username = ''
  form.email = ''
  form.role = ''
  form.dependency_id = null
  Object.keys(errors).forEach((k) => (errors[k as keyof typeof errors] = ''))
  createdPassword.value = null
  copied.value = false
}

function validate(): boolean {
  let valid = true
  Object.keys(errors).forEach((k) => (errors[k as keyof typeof errors] = ''))

  if (!form.nombre_completo.trim()) {
    errors.nombre_completo = 'El nombre completo es obligatorio'
    valid = false
  }
  if (!isEditing.value && !form.username.trim()) {
    errors.username = 'El nombre de usuario es obligatorio'
    valid = false
  }
  if (!form.email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    errors.email = 'Ingrese un correo electrónico válido'
    valid = false
  }
  if (!form.role) {
    errors.role = 'Seleccione un rol'
    valid = false
  }
  if (form.role === 'dependency_user' && !form.dependency_id) {
    errors.dependency_id = 'Debe seleccionar una dependencia para este rol'
    valid = false
  }
  return valid
}

async function handleSubmit() {
  if (!validate()) return
  loading.value = true

  try {
    if (isEditing.value && props.editData?.id) {
      // Edición: PATCH → retorna UserResponse completo
      const saved = await patch<UserData>(`/admin/users/${props.editData.id}`, {
        nombre_completo: form.nombre_completo,
        email: form.email,
        role: form.role,
        dependency_id: form.dependency_id,
      })
      notifications.success('Usuario actualizado exitosamente')
      emit('saved', saved)
      handleClose()
    } else {
      // Creación: POST → retorna UserCreateResponse (sin datos completos)
      const created = await post<UserCreateResponse>('/admin/users', { ...form })
      // Obtener usuario completo para actualizar la tabla
      const fullUser = await get<UserData>(`/admin/users/${created.id}`)
      emit('saved', fullUser)
      // Mostrar panel con contraseña temporal (no cierra automáticamente)
      createdPassword.value = created.temp_password
    }
  } catch (err: unknown) {
    const axiosErr = err as { response?: { data?: { detail?: string } } }
    notifications.error(axiosErr?.response?.data?.detail || 'Error al guardar el usuario')
  } finally {
    loading.value = false
  }
}

async function copyPassword() {
  if (!createdPassword.value) return
  try {
    await navigator.clipboard.writeText(createdPassword.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    notifications.error('No se pudo copiar al portapapeles')
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
.modal-enter-active,
.modal-leave-active { transition: opacity 0.2s ease; }
.modal-enter-from,
.modal-leave-to { opacity: 0; }
.fade-enter-active,
.fade-leave-active { transition: all 0.2s ease; }
.fade-enter-from,
.fade-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
