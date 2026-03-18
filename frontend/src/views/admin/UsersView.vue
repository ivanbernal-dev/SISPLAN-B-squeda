<template>
  <div class="p-6 space-y-5">
    <!-- Encabezado -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="font-subtitulo font-bold text-2xl text-ubpd-gris">Usuarios</h1>
        <p class="font-cuerpo text-sm text-gray-500 mt-1">Gestión de cuentas de acceso al sistema</p>
      </div>
      <button
        @click="openCreateModal"
        class="inline-flex items-center gap-2 bg-ubpd-teal text-white font-cuerpo font-semibold text-sm
               rounded-xl px-5 py-2.5 hover:bg-[#346d7a] transition"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nuevo Usuario
      </button>
    </div>

    <!-- Filtros -->
    <div class="bg-white rounded-2xl border border-gray-100 shadow-sm px-5 py-4 flex flex-wrap gap-3">
      <div class="flex-1 min-w-[180px]">
        <label class="block font-cuerpo text-xs font-medium text-gray-500 mb-1">Buscar</label>
        <input
          v-model="filters.search"
          type="text"
          placeholder="Nombre o usuario..."
          class="w-full font-cuerpo text-sm border border-gray-300 rounded-lg px-3 py-2
                 focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20 transition"
        />
      </div>
      <div class="min-w-[150px]">
        <label class="block font-cuerpo text-xs font-medium text-gray-500 mb-1">Rol</label>
        <select
          v-model="filters.role"
          class="w-full font-cuerpo text-sm border border-gray-300 rounded-lg px-3 py-2
                 focus:outline-none focus:border-ubpd-verde transition"
        >
          <option value="">Todos los roles</option>
          <option value="admin">Administrador</option>
          <option value="validator">Validador</option>
          <option value="dependency_user">Usuario Dependencia</option>
        </select>
      </div>
      <div class="min-w-[140px]">
        <label class="block font-cuerpo text-xs font-medium text-gray-500 mb-1">Estado</label>
        <select
          v-model="filters.status"
          class="w-full font-cuerpo text-sm border border-gray-300 rounded-lg px-3 py-2
                 focus:outline-none focus:border-ubpd-verde transition"
        >
          <option value="">Todos</option>
          <option value="active">Activo</option>
          <option value="inactive">Inactivo</option>
        </select>
      </div>
    </div>

    <!-- Tabla -->
    <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <!-- Loading skeleton -->
      <div v-if="loading" class="divide-y divide-gray-50">
        <div v-for="i in 5" :key="i" class="px-6 py-4 flex items-center gap-4 animate-pulse">
          <div class="w-9 h-9 rounded-full bg-gray-200" />
          <div class="flex-1 space-y-2">
            <div class="w-40 h-4 rounded bg-gray-200" />
            <div class="w-28 h-3 rounded bg-gray-200" />
          </div>
          <div class="w-20 h-6 rounded-full bg-gray-200" />
          <div class="w-24 h-4 rounded bg-gray-200" />
          <div class="w-16 h-6 rounded-full bg-gray-200" />
          <div class="flex gap-2">
            <div class="w-8 h-8 rounded-lg bg-gray-200" />
            <div class="w-8 h-8 rounded-lg bg-gray-200" />
          </div>
        </div>
      </div>

      <!-- Datos -->
      <div v-else-if="filteredUsers.length > 0">
        <table class="w-full">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide">Persona</th>
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide">Usuario</th>
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide">Rol</th>
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide hidden md:table-cell">Dependencia</th>
              <th class="px-6 py-3 text-left font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide">Estado</th>
              <th class="px-6 py-3 text-right font-cuerpo font-medium text-xs text-gray-500 uppercase tracking-wide">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr
              v-for="user in paginatedUsers"
              :key="user.id"
              class="hover:bg-gray-50/50 transition"
            >
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <div class="w-9 h-9 rounded-full bg-ubpd-teal/10 flex items-center justify-center flex-shrink-0">
                    <span class="font-subtitulo font-semibold text-sm text-ubpd-teal">
                      {{ initials(user.nombre_completo) }}
                    </span>
                  </div>
                  <div>
                    <p class="font-cuerpo font-medium text-sm text-ubpd-gris">{{ user.nombre_completo }}</p>
                    <p class="font-cuerpo text-xs text-gray-400">{{ user.email }}</p>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4">
                <span class="font-cuerpo text-sm text-gray-600 font-mono">{{ user.username }}</span>
              </td>
              <td class="px-6 py-4">
                <span class="inline-flex items-center font-cuerpo text-xs font-medium px-2.5 py-1 rounded-full"
                  :class="roleBadgeClass(user.role)">
                  {{ roleLabel(user.role) }}
                </span>
              </td>
              <td class="px-6 py-4 hidden md:table-cell">
                <span class="font-cuerpo text-sm text-gray-400">—</span>
              </td>
              <td class="px-6 py-4">
                <span
                  class="inline-flex items-center gap-1.5 font-cuerpo text-xs font-medium px-2.5 py-1 rounded-full"
                  :class="user.activo ? 'bg-ubpd-verde/10 text-ubpd-verde' : 'bg-gray-100 text-gray-500'"
                >
                  <span class="w-1.5 h-1.5 rounded-full" :class="user.activo ? 'bg-ubpd-verde' : 'bg-gray-400'" />
                  {{ user.activo ? 'Activo' : 'Inactivo' }}
                </span>
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center justify-end gap-1.5">
                  <button
                    @click="openEditModal(user)"
                    class="p-2 rounded-lg text-gray-400 hover:text-ubpd-teal hover:bg-ubpd-teal/10 transition"
                    :aria-label="`Editar ${user.nombre_completo}`"
                    title="Editar"
                  >
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    @click="confirmToggle(user)"
                    class="p-2 rounded-lg transition"
                    :class="user.activo
                      ? 'text-gray-400 hover:text-ubpd-naranja hover:bg-orange-50'
                      : 'text-gray-400 hover:text-ubpd-verde hover:bg-ubpd-verde/10'"
                    :aria-label="user.activo ? `Desactivar ${user.nombre_completo}` : `Activar ${user.nombre_completo}`"
                    :title="user.activo ? 'Desactivar' : 'Activar'"
                  >
                    <svg v-if="user.activo" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                    </svg>
                    <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Paginación -->
        <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-between">
          <p class="font-cuerpo text-sm text-gray-500">
            Mostrando {{ paginationInfo.from }}–{{ paginationInfo.to }} de {{ filteredUsers.length }}
          </p>
          <div class="flex gap-1">
            <button
              @click="page--"
              :disabled="page === 1"
              class="p-2 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <button
              v-for="p in totalPages"
              :key="p"
              @click="page = p"
              class="w-8 h-8 rounded-lg font-cuerpo text-sm transition"
              :class="p === page ? 'bg-ubpd-teal text-white' : 'border border-gray-200 text-gray-500 hover:bg-gray-50'"
            >
              {{ p }}
            </button>
            <button
              @click="page++"
              :disabled="page === totalPages"
              class="p-2 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Estado vacío -->
      <div v-else class="py-16 text-center">
        <svg class="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <p class="font-cuerpo text-sm text-gray-500">No se encontraron usuarios</p>
        <button @click="openCreateModal" class="mt-3 font-cuerpo text-sm text-ubpd-teal hover:underline">
          Crear el primer usuario
        </button>
      </div>
    </div>

    <!-- Modales -->
    <UserFormModal
      v-model="showUserModal"
      :edit-data="selectedUser"
      @saved="handleUserSaved"
    />

    <ConfirmModal
      v-model="showConfirm"
      :title="confirmData.activo ? 'Desactivar usuario' : 'Activar usuario'"
      :message="confirmData.activo
        ? `¿Desea desactivar la cuenta de ${confirmData.nombre}? El usuario no podrá ingresar al sistema.`
        : `¿Desea activar la cuenta de ${confirmData.nombre}?`"
      :confirm-label="confirmData.activo ? 'Desactivar' : 'Activar'"
      :variant="confirmData.activo ? 'danger' : 'confirm'"
      :loading="confirmLoading"
      @confirm="handleToggleUser"
      @cancel="showConfirm = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useApi } from '@/composables/useApi'
import { useNotificationsStore } from '@/stores/notifications'
import UserFormModal from '@/components/forms/UserFormModal.vue'
import ConfirmModal from '@/components/common/ConfirmModal.vue'

interface User {
  id: string
  nombre_completo: string
  username: string
  email: string
  role: string
  dependency_id: string | null
  activo: boolean
}

interface UserListResponse {
  total: number
  page: number
  size: number
  items: User[]
}

const { get, del, patch } = useApi()
const notifications = useNotificationsStore()

const loading = ref(true)
const users = ref<User[]>([])
const page = ref(1)
const pageSize = 15

const filters = reactive({ search: '', role: '', status: '' })

const showUserModal = ref(false)
const selectedUser = ref<User | null>(null)

const showConfirm = ref(false)
const confirmLoading = ref(false)
const confirmData = reactive({ id: '', nombre: '', activo: true })

async function loadUsers() {
  loading.value = true
  try {
    const data = await get<UserListResponse>('/admin/users')
    users.value = data.items
  } catch {
    notifications.error('No se pudo cargar la lista de usuarios')
  } finally {
    loading.value = false
  }
}

onMounted(loadUsers)

// Filtros: resetear página cuando cambian
watch(filters, () => { page.value = 1 })

const filteredUsers = computed(() => {
  return users.value.filter((u) => {
    const matchSearch = !filters.search
      || u.nombre_completo.toLowerCase().includes(filters.search.toLowerCase())
      || u.username.toLowerCase().includes(filters.search.toLowerCase())
    const matchRole = !filters.role || u.role === filters.role
    const matchStatus = !filters.status
      || (filters.status === 'active' && u.activo)
      || (filters.status === 'inactive' && !u.activo)
    return matchSearch && matchRole && matchStatus
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredUsers.value.length / pageSize)))

const paginatedUsers = computed(() => {
  const start = (page.value - 1) * pageSize
  return filteredUsers.value.slice(start, start + pageSize)
})

const paginationInfo = computed(() => {
  const from = filteredUsers.value.length === 0 ? 0 : (page.value - 1) * pageSize + 1
  const to = Math.min(page.value * pageSize, filteredUsers.value.length)
  return { from, to }
})

function initials(name: string): string {
  return name.split(' ').slice(0, 2).map((n) => n[0]).join('').toUpperCase()
}

function roleLabel(role: string): string {
  const map: Record<string, string> = {
    admin: 'Administrador',
    validator: 'Validador',
    dependency_user: 'Dependencia',
  }
  return map[role] ?? role
}

function roleBadgeClass(role: string): string {
  const map: Record<string, string> = {
    admin: 'bg-ubpd-lila/10 text-ubpd-lila',
    validator: 'bg-ubpd-teal/10 text-ubpd-teal',
    dependency_user: 'bg-ubpd-verde/10 text-ubpd-verde',
  }
  return map[role] ?? 'bg-gray-100 text-gray-500'
}

function openCreateModal() {
  selectedUser.value = null
  showUserModal.value = true
}

function openEditModal(user: User) {
  selectedUser.value = user
  showUserModal.value = true
}

function confirmToggle(user: User) {
  confirmData.id = user.id
  confirmData.nombre = user.nombre_completo
  confirmData.activo = user.activo
  showConfirm.value = true
}

async function handleToggleUser() {
  confirmLoading.value = true
  try {
    if (confirmData.activo) {
      // Desactivar: DELETE /admin/users/{id}
      await del(`/admin/users/${confirmData.id}`)
    } else {
      // Reactivar: PATCH /admin/users/{id} con activo: true
      await patch(`/admin/users/${confirmData.id}`, { activo: true })
    }
    const idx = users.value.findIndex((u) => u.id === confirmData.id)
    if (idx !== -1) users.value[idx].activo = !confirmData.activo
    notifications.success(
      confirmData.activo ? 'Usuario desactivado' : 'Usuario activado'
    )
    showConfirm.value = false
  } catch {
    notifications.error('No se pudo actualizar el estado del usuario')
  } finally {
    confirmLoading.value = false
  }
}

function handleUserSaved(savedUser: User) {
  const idx = users.value.findIndex((u) => u.id === savedUser.id)
  if (idx !== -1) {
    users.value[idx] = savedUser
  } else {
    users.value.unshift(savedUser)
  }
}
</script>
