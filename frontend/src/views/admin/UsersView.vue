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
                    <div class="flex items-center gap-1">
                      <p class="font-cuerpo text-xs text-gray-400">{{ user.email ?? '—' }}</p>
                      <button
                        v-if="user.email"
                        @click.stop="copyEmail(user.email)"
                        :title="copiedEmail === user.email ? 'Copiado!' : 'Copiar correo'"
                        class="text-gray-300 hover:text-ubpd-teal transition-colors"
                      >
                        <svg v-if="copiedEmail === user.email" class="w-3 h-3 text-ubpd-verde" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
                        </svg>
                        <svg v-else class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center gap-1">
                  <span class="font-cuerpo text-sm text-gray-600 font-mono">{{ user.username }}</span>
                  <button
                    @click.stop="copyUsername(user.username)"
                    :title="copiedUsername === user.username ? 'Copiado!' : 'Copiar usuario'"
                    class="text-gray-300 hover:text-ubpd-teal transition-colors"
                  >
                    <svg v-if="copiedUsername === user.username" class="w-3 h-3 text-ubpd-verde" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
                    </svg>
                    <svg v-else class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </button>
                </div>
              </td>
              <td class="px-6 py-4">
                <span class="inline-flex items-center font-cuerpo text-xs font-medium px-2.5 py-1 rounded-full"
                  :class="roleBadgeClass(user.role)">
                  {{ roleLabel(user.role) }}
                </span>
              </td>
              <td class="px-6 py-4 hidden md:table-cell">
                <span class="font-cuerpo text-sm" :class="user.dependency_id ? 'text-ubpd-gris' : 'text-gray-400'">
                  {{ dependencyName(user.dependency_id) }}
                </span>
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
                  <!-- Editar -->
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
                  <!-- Resetear contraseña -->
                  <button
                    @click="confirmReset(user)"
                    class="p-2 rounded-lg text-gray-400 hover:text-ubpd-lila hover:bg-ubpd-lila/10 transition"
                    :aria-label="`Resetear contraseña de ${user.nombre_completo}`"
                    title="Resetear contraseña"
                  >
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                    </svg>
                  </button>
                  <!-- Activar / Desactivar -->
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
                  <!-- Eliminar permanente -->
                  <button
                    @click="openHardDelete(user)"
                    class="p-2 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition"
                    :aria-label="`Eliminar permanentemente ${user.nombre_completo}`"
                    title="Eliminar permanentemente"
                  >
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6M1 7h22M9 7V4a2 2 0 012-2h2a2 2 0 012 2v3" />
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

    <!-- Modal: confirmar activar/desactivar -->
    <ConfirmModal
      :is-open="showConfirm"
      :title="confirmData.activo ? 'Desactivar usuario' : 'Activar usuario'"
      :message="confirmData.activo
        ? `¿Desea desactivar la cuenta de ${confirmData.nombre}? El usuario no podrá ingresar al sistema.`
        : `¿Desea activar la cuenta de ${confirmData.nombre}?`"
      :confirm-text="confirmData.activo ? 'Desactivar' : 'Activar'"
      :confirm-variant="confirmData.activo ? 'danger' : 'success'"
      :loading="confirmLoading"
      @confirm="handleToggleUser"
      @cancel="showConfirm = false"
    />

    <!-- Modal: confirmar reset de contraseña -->
    <ConfirmModal
      :is-open="showResetConfirm"
      title="Resetear contraseña"
      :message="`¿Generar una nueva contraseña temporal para ${resetData.nombre}? La contraseña actual quedará inválida.`"
      confirm-text="Resetear"
      confirm-variant="danger"
      :loading="resetLoading"
      @confirm="handleResetPassword"
      @cancel="showResetConfirm = false"
    />

    <!-- Modal: eliminar permanentemente usuario -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showHardDelete"
          class="fixed inset-0 z-50 flex items-center justify-center p-4"
          role="dialog" aria-modal="true"
        >
          <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="closeHardDelete" />
          <div class="relative bg-white rounded-2xl shadow-2xl max-w-lg w-full z-10 overflow-hidden">
            <div class="bg-red-600 px-6 py-4">
              <h2 class="font-subtitulo font-bold text-white text-lg flex items-center gap-2">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                Eliminar usuario permanentemente
              </h2>
              <p class="font-cuerpo text-white/85 text-sm mt-0.5">Esta acción NO se puede deshacer</p>
            </div>

            <div class="px-6 py-5 space-y-4">
              <p class="font-cuerpo text-sm text-gray-700">
                Vas a eliminar de forma permanente a
                <strong class="text-ubpd-gris">{{ hardDeleteData.nombre }}</strong>
                (<code class="bg-gray-100 px-1.5 py-0.5 rounded text-xs">{{ hardDeleteData.username }}</code>).
              </p>

              <div v-if="hardDeleteError" class="bg-amber-50 border border-amber-300 rounded-lg p-3">
                <p class="font-cuerpo text-xs text-amber-800">
                  <strong>⚠️ {{ hardDeleteError }}</strong>
                </p>
                <label class="mt-3 flex items-start gap-2 cursor-pointer">
                  <input v-model="hardDeleteForce" type="checkbox" class="mt-1" />
                  <span class="font-cuerpo text-xs text-gray-700">
                    Sí, quiero eliminar TAMBIÉN los formularios y archivos asociados.
                    Entiendo que esta acción es irreversible.
                  </span>
                </label>
              </div>

              <div class="bg-red-50 border border-red-200 rounded-lg p-3 space-y-1">
                <p class="font-cuerpo text-xs text-red-800 font-semibold">Se eliminarán:</p>
                <ul class="font-cuerpo text-xs text-red-700 ml-4 list-disc space-y-0.5">
                  <li>La cuenta del usuario (registros de login, permisos, etc.)</li>
                  <li v-if="hardDeleteForce">Todos los formularios creados por este usuario</li>
                  <li v-if="hardDeleteForce">Todos los archivos adjuntos asociados (MinIO)</li>
                </ul>
                <p class="font-cuerpo text-xs text-gray-600 mt-2">
                  Los registros de auditoría se mantienen (el historial se preserva con la referencia al usuario en null).
                </p>
              </div>
            </div>

            <div class="px-6 py-4 bg-gray-50 flex justify-end gap-2">
              <button
                @click="closeHardDelete"
                class="px-4 py-2 text-sm font-cuerpo font-medium border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-100 transition"
              >
                Cancelar
              </button>
              <button
                @click="handleHardDelete"
                :disabled="hardDeleteLoading"
                class="px-4 py-2 text-sm font-cuerpo font-bold text-white bg-red-600 rounded-lg hover:bg-red-700 transition disabled:opacity-50 flex items-center gap-2"
              >
                <svg v-if="hardDeleteLoading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25" />
                  <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {{ hardDeleteLoading ? 'Eliminando…' : 'Eliminar definitivamente' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Modal: mostrar nueva contraseña temporal -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showResetResult"
          class="fixed inset-0 z-50 flex items-center justify-center p-4"
          role="dialog"
          aria-modal="true"
        >
          <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="showResetResult = false" />
          <div class="relative bg-white rounded-2xl shadow-2xl max-w-md w-full z-10 overflow-hidden">
            <!-- Header -->
            <div class="bg-ubpd-lila px-6 py-4">
              <h2 class="font-subtitulo font-bold text-white text-lg">Nueva contraseña temporal</h2>
              <p class="font-cuerpo text-white/75 text-sm mt-0.5">Guárdala antes de cerrar esta ventana</p>
            </div>
            <!-- Cuerpo -->
            <div class="px-6 py-5 space-y-4">
              <div class="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
                <svg class="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                </svg>
                <p class="font-cuerpo text-xs text-amber-800">
                  Entrega esta contraseña al usuario <strong>{{ resetData.nombre }}</strong>.
                  No podrá recuperarse después de cerrar.
                </p>
              </div>
              <div>
                <label class="block font-cuerpo font-medium text-sm text-ubpd-gris mb-1.5">Contraseña temporal</label>
                <div class="flex items-center gap-2 border border-gray-300 rounded-lg px-3 py-2.5 bg-gray-50">
                  <code class="flex-1 font-mono text-sm text-ubpd-gris select-all tracking-wide">{{ resetData.newPassword }}</code>
                  <button
                    type="button"
                    @click="copyResetPassword"
                    class="p-1.5 rounded-md text-ubpd-lila hover:bg-ubpd-lila/10 transition"
                    :title="resetCopied ? 'Copiado' : 'Copiar'"
                  >
                    <svg v-if="!resetCopied" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    <svg v-else class="w-4 h-4 text-ubpd-verde" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    </svg>
                  </button>
                </div>
                <p class="mt-1.5 font-cuerpo text-xs text-gray-500">El usuario deberá cambiarla en su próximo ingreso.</p>
              </div>
              <button
                type="button"
                @click="showResetResult = false"
                class="w-full px-5 py-2.5 rounded-lg bg-ubpd-lila text-white font-cuerpo font-semibold text-sm
                       hover:opacity-90 transition"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
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

interface Dependency {
  id: string
  nombre: string
  codigo: string
}

const { get, post, del, patch } = useApi()
const notifications = useNotificationsStore()

const loading = ref(true)
const users = ref<User[]>([])
const dependencies = ref<Dependency[]>([])
const page = ref(1)
const pageSize = 15

const filters = reactive({ search: '', role: '', status: '' })

const showUserModal = ref(false)
const selectedUser = ref<User | null>(null)

const showConfirm = ref(false)
const confirmLoading = ref(false)
const confirmData = reactive({ id: '', nombre: '', activo: true })

// Reset de contraseña
const showResetConfirm = ref(false)
const showResetResult = ref(false)
const resetLoading = ref(false)
const resetCopied = ref(false)
const resetData = reactive({ id: '', nombre: '', newPassword: '' })
const copiedEmail = ref<string | null>(null)
const copiedUsername = ref<string | null>(null)

async function loadUsers() {
  loading.value = true
  try {
    const [usersData, depsData] = await Promise.all([
      get<UserListResponse>('/admin/users'),
      get<Dependency[]>('/admin/dependencies').catch(() => [] as Dependency[]),
    ])
    users.value = usersData.items
    dependencies.value = depsData
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

function dependencyName(id: string | null): string {
  if (!id) return '—'
  const dep = dependencies.value.find((d) => d.id === id)
  return dep ? dep.nombre : '—'
}

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

function confirmReset(user: User) {
  resetData.id = user.id
  resetData.nombre = user.nombre_completo
  resetData.newPassword = ''
  showResetConfirm.value = true
}

async function handleResetPassword() {
  resetLoading.value = true
  try {
    interface ResetResponse { id: string; username: string; temp_password: string }
    const result = await post<ResetResponse>(`/admin/users/${resetData.id}/reset-password`, {})
    resetData.newPassword = result.temp_password
    showResetConfirm.value = false
    showResetResult.value = true
    resetCopied.value = false
  } catch {
    notifications.error('No se pudo resetear la contraseña')
  } finally {
    resetLoading.value = false
  }
}

// ── Hard delete (eliminar usuario permanentemente) ──────────────────────────
const showHardDelete = ref(false)
const hardDeleteLoading = ref(false)
const hardDeleteError = ref<string | null>(null)
const hardDeleteForce = ref(false)
const hardDeleteData = reactive({ id: '', nombre: '', username: '' })

function openHardDelete(user: User) {
  hardDeleteData.id = user.id
  hardDeleteData.nombre = user.nombre_completo
  hardDeleteData.username = user.username
  hardDeleteError.value = null
  hardDeleteForce.value = false
  showHardDelete.value = true
}

function closeHardDelete() {
  showHardDelete.value = false
  hardDeleteError.value = null
  hardDeleteForce.value = false
}

async function handleHardDelete() {
  hardDeleteLoading.value = true
  try {
    const apiUrl = import.meta.env.VITE_API_URL || '/api'
    const token = localStorage.getItem('ubpd_access_token')
    const url = `${apiUrl}/admin/users/${hardDeleteData.id}/hard${hardDeleteForce.value ? '?force=true' : ''}`
    const resp = await fetch(url, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    })
    const data = await resp.json().catch(() => ({}))

    if (resp.status === 409) {
      // Tiene forms → mostrar confirmación de force
      hardDeleteError.value = typeof data.detail === 'string'
        ? data.detail
        : 'El usuario tiene datos asociados.'
      return
    }
    if (!resp.ok) {
      notifications.error('Error', typeof data.detail === 'string' ? data.detail : 'No se pudo eliminar.')
      return
    }

    notifications.success('Usuario eliminado', data.mensaje || 'Eliminación completada.')
    // Remover de la lista local
    users.value = users.value.filter((u) => u.id !== hardDeleteData.id)
    closeHardDelete()
  } catch {
    notifications.error('Error', 'No se pudo conectar con el servidor.')
  } finally {
    hardDeleteLoading.value = false
  }
}

async function copyEmail(email: string) {
  try {
    await navigator.clipboard.writeText(email)
    copiedEmail.value = email
    setTimeout(() => { copiedEmail.value = null }, 2000)
  } catch {
    notifications.error('No se pudo copiar al portapapeles')
  }
}

async function copyUsername(username: string) {
  try {
    await navigator.clipboard.writeText(username)
    copiedUsername.value = username
    setTimeout(() => { copiedUsername.value = null }, 2000)
  } catch {
    notifications.error('No se pudo copiar al portapapeles')
  }
}

async function copyResetPassword() {
  try {
    await navigator.clipboard.writeText(resetData.newPassword)
    resetCopied.value = true
    setTimeout(() => { resetCopied.value = false }, 2000)
  } catch {
    notifications.error('No se pudo copiar al portapapeles')
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
