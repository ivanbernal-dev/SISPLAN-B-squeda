<template>
  <div class="p-6 space-y-5">

    <!-- ══ ETAPA 1: Búsqueda de templates ══════════════════════════════════ -->
    <template v-if="stage === 'templates'">
      <!-- Encabezado -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 class="font-subtitulo font-bold text-2xl text-ubpd-gris">Registros</h1>
          <p class="font-cuerpo text-sm text-gray-500 mt-1">
            Selecciona un formulario para ver sus registros
          </p>
        </div>
      </div>

      <!-- Buscador -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm px-5 py-4">
        <div class="max-w-sm">
          <label class="block font-cuerpo text-xs font-medium text-gray-500 mb-1">
            Buscar formulario
          </label>
          <div class="relative">
            <svg
              class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
              fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M21 21l-4.35-4.35M17 11A6 6 0 105 11a6 6 0 0012 0z" />
            </svg>
            <input
              v-model="templateSearch"
              type="text"
              placeholder="Buscar por nombre..."
              class="w-full font-cuerpo text-sm border border-gray-300 rounded-lg pl-9 pr-3 py-2
                     focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20 transition"
            />
          </div>
        </div>
      </div>

      <!-- Grid de cards de templates (loading) -->
      <div v-if="loadingTemplates" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        <div v-for="i in 6" :key="i" class="bg-white rounded-2xl border border-gray-100 p-5 animate-pulse">
          <div class="w-full h-5 rounded bg-gray-200 mb-3" />
          <div class="w-3/4 h-4 rounded bg-gray-200 mb-4" />
          <div class="flex gap-2">
            <div class="w-16 h-5 rounded-full bg-gray-200" />
            <div class="w-20 h-5 rounded-full bg-gray-200" />
          </div>
        </div>
      </div>

      <!-- Grid de cards de templates (datos) -->
      <div
        v-else-if="filteredTemplates.length > 0"
        class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4"
      >
        <div
          v-for="tmpl in filteredTemplates"
          :key="tmpl.id"
          class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 cursor-pointer
                 hover:shadow-md hover:border-ubpd-teal/40 transition group"
          @click="selectTemplate(tmpl)"
        >
          <!-- Nombre y código -->
          <div class="flex items-start justify-between gap-2 mb-2">
            <p class="font-subtitulo font-semibold text-sm text-ubpd-gris
                      group-hover:text-ubpd-teal transition leading-snug">
              {{ tmpl.nombre }}
            </p>
            <span
              v-if="tmpl.codigo"
              class="flex-shrink-0 font-cuerpo text-xs bg-ubpd-teal/10 text-ubpd-teal
                     px-2 py-0.5 rounded-full"
            >
              {{ tmpl.codigo }}
            </span>
          </div>

          <!-- Descripción -->
          <p
            v-if="tmpl.descripcion"
            class="font-cuerpo text-xs text-gray-400 mb-3 line-clamp-2"
          >
            {{ tmpl.descripcion }}
          </p>

          <!-- Meta -->
          <div class="flex flex-wrap items-center gap-2">
            <span class="font-cuerpo text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
              {{ countCampos(tmpl) }} campos
            </span>
            <span
              class="font-cuerpo text-xs px-2 py-0.5 rounded-full"
              :class="tmpl.is_active
                ? 'bg-ubpd-verde/10 text-ubpd-verde'
                : 'bg-gray-100 text-gray-400'"
            >
              {{ tmpl.is_active ? 'Activo' : 'Inactivo' }}
            </span>
          </div>

          <!-- Acciones admin (solo aprobados) + Indicador clickable -->
          <div class="mt-3 flex items-center justify-between gap-2">
            <div v-if="isAdmin" class="flex items-center gap-1.5 flex-wrap" @click.stop>
              <button
                type="button"
                :disabled="downloadingKey === tmpl.id + ':excel'"
                @click.stop="downloadTemplateForms(tmpl, 'excel')"
                class="flex items-center gap-1 text-[11px] font-cuerpo font-medium
                       border border-ubpd-verde/50 text-ubpd-verde rounded-lg px-2 py-1
                       hover:bg-ubpd-verde/10 transition disabled:opacity-50"
                title="Descargar Excel con los formularios APROBADOS"
              >
                <svg v-if="downloadingKey !== tmpl.id + ':excel'" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M9 17v-4a2 2 0 012-2h2a2 2 0 012 2v4M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
                <svg v-else class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25" />
                  <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Excel
              </button>
              <button
                type="button"
                :disabled="downloadingKey === tmpl.id + ':zip'"
                @click.stop="downloadTemplateForms(tmpl, 'zip')"
                class="flex items-center gap-1 text-[11px] font-cuerpo font-medium
                       border border-ubpd-teal/50 text-ubpd-teal rounded-lg px-2 py-1
                       hover:bg-teal-50 transition disabled:opacity-50"
                title="Descargar ZIP (aprobados) con evidencias por formulario"
              >
                <svg v-if="downloadingKey !== tmpl.id + ':zip'" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
                <svg v-else class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25" />
                  <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                ZIP
              </button>
              <button
                type="button"
                :disabled="templateCount(tmpl.id).total === 0"
                @click.stop="confirmDeleteRegistros(tmpl)"
                class="flex items-center gap-1 text-[11px] font-cuerpo font-medium
                       border rounded-lg px-2 py-1 transition"
                :class="templateCount(tmpl.id).total === 0
                  ? 'border-gray-200 text-gray-300 cursor-not-allowed'
                  : 'border-red-300 text-red-600 hover:bg-red-50'"
                :title="templateCount(tmpl.id).total === 0
                  ? 'No hay registros que vaciar'
                  : `Eliminar los ${templateCount(tmpl.id).total} registro(s) de este template`"
              >
                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6M1 7h22M9 7V4a2 2 0 012-2h2a2 2 0 012 2v3" />
                </svg>
                Vaciar
                <span v-if="templateCount(tmpl.id).total > 0" class="ml-0.5">({{ templateCount(tmpl.id).total }})</span>
              </button>
              <button
                type="button"
                :disabled="templateCount(tmpl.id).total > 0"
                @click.stop="confirmDeleteTemplate(tmpl)"
                class="flex items-center gap-1 text-[11px] font-cuerpo font-medium
                       rounded-lg px-2 py-1 transition"
                :class="templateCount(tmpl.id).total > 0
                  ? 'border border-gray-200 text-gray-300 cursor-not-allowed bg-gray-50'
                  : 'border border-red-500 text-white bg-red-500 hover:bg-red-600'"
                :title="templateCount(tmpl.id).total > 0
                  ? `Primero vacía los ${templateCount(tmpl.id).total} registro(s) del template`
                  : 'Eliminar el template'"
              >
                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
                Borrar template
              </button>
            </div>
            <span v-else />

            <span class="font-cuerpo text-xs text-ubpd-teal opacity-0 group-hover:opacity-100 transition flex items-center gap-1">
              Ver registros
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </span>
          </div>
        </div>
      </div>

      <!-- Vacío -->
      <div v-else class="bg-white rounded-2xl border border-gray-100 py-16 text-center">
        <svg class="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
            d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6z" />
        </svg>
        <p class="font-cuerpo text-sm text-gray-500">No se encontraron formularios</p>
        <p class="font-cuerpo text-xs text-gray-400 mt-1">
          {{ templateSearch ? 'Prueba con otro término de búsqueda' : 'No hay formularios disponibles' }}
        </p>
      </div>
    </template>

    <!-- ══ ETAPA 2: Lista de formularios del template ═══════════════════════ -->
    <template v-else-if="stage === 'forms' && selectedTemplate">
      <!-- Breadcrumb + acciones -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <!-- Breadcrumb -->
          <nav class="flex items-center gap-1.5 font-cuerpo text-sm text-gray-400 mb-1">
            <button
              @click="backToTemplates"
              class="hover:text-ubpd-teal transition flex items-center gap-1"
            >
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
              Registros
            </button>
            <svg class="w-3.5 h-3.5 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
            <span class="text-ubpd-gris font-medium truncate max-w-xs">
              {{ selectedTemplate.nombre }}
            </span>
          </nav>
          <h1 class="font-subtitulo font-bold text-2xl text-ubpd-gris">
            {{ selectedTemplate.nombre }}
          </h1>
          <p class="font-cuerpo text-sm text-gray-500 mt-0.5">
            {{ totalForms }} registro{{ totalForms !== 1 ? 's' : '' }} encontrado{{ totalForms !== 1 ? 's' : '' }}
          </p>
        </div>

        <div class="flex items-center gap-2 flex-wrap">
          <!-- Descargas consolidadas (solo admin) -->
          <button
            v-if="isAdmin && selectedTemplate"
            type="button"
            :disabled="downloadingKey === selectedTemplate.id + ':excel'"
            @click="downloadTemplateForms(selectedTemplate, 'excel')"
            class="inline-flex items-center gap-2 border border-ubpd-verde text-ubpd-verde
                   font-cuerpo font-semibold text-sm rounded-xl px-4 py-2.5
                   hover:bg-ubpd-verde/10 transition disabled:opacity-50"
            title="Descargar Excel con todos los formularios respondidos"
          >
            <svg v-if="downloadingKey !== selectedTemplate.id + ':excel'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M9 17v-4a2 2 0 012-2h2a2 2 0 012 2v4M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
            <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25" />
              <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Descargar Excel
          </button>

          <button
            v-if="isAdmin && selectedTemplate"
            type="button"
            :disabled="downloadingKey === selectedTemplate.id + ':zip'"
            @click="downloadTemplateForms(selectedTemplate, 'zip')"
            class="inline-flex items-center gap-2 border border-ubpd-teal text-ubpd-teal
                   font-cuerpo font-semibold text-sm rounded-xl px-4 py-2.5
                   hover:bg-teal-50 transition disabled:opacity-50"
            title="Descargar ZIP con evidencias agrupadas por formulario"
          >
            <svg v-if="downloadingKey !== selectedTemplate.id + ':zip'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
            <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25" />
              <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Descargar ZIP
          </button>

          <!-- Botón Nuevo Registro (solo dependency_user) -->
          <button
            v-if="isDependencyUser"
            @click="goToNewForm"
            class="inline-flex items-center gap-2 bg-ubpd-teal text-white font-cuerpo font-semibold text-sm
                   rounded-xl px-5 py-2.5 hover:bg-[#346d7a] transition flex-shrink-0"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Nuevo Registro
          </button>
        </div>
      </div>

      <!-- Filtro de estado -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm px-5 py-4">
        <div class="flex flex-wrap items-end gap-3">
          <div>
            <label class="block font-cuerpo text-xs font-medium text-gray-500 mb-1">Estado</label>
            <select
              v-model="statusFilter"
              @change="loadForms(1)"
              class="font-cuerpo text-sm border border-gray-300 rounded-lg px-3 py-2
                     focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20 transition"
            >
              <option value="">Todos los estados</option>
              <option v-if="!isValidatorOrAdmin" value="draft">Borrador</option>
              <option value="pending">Pendiente</option>
              <option value="approved">Aprobado</option>
              <option value="rejected">Rechazado</option>
            </select>
          </div>
          <button
            v-if="statusFilter"
            @click="statusFilter = ''; loadForms(1)"
            class="font-cuerpo text-sm text-gray-500 border border-gray-300 rounded-lg px-3 py-2
                   hover:bg-gray-50 transition"
          >
            Limpiar filtro
          </button>
        </div>
      </div>

      <!-- Tabla de formularios -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <!-- Loading skeleton -->
        <div v-if="loadingForms" class="divide-y divide-gray-50">
          <div v-for="i in 5" :key="i" class="px-6 py-4 flex items-center gap-4 animate-pulse">
            <div class="w-20 h-6 rounded-full bg-gray-200 flex-shrink-0" />
            <div class="flex-1 space-y-2">
              <div class="w-40 h-4 rounded bg-gray-200" />
              <div class="w-28 h-3 rounded bg-gray-200" />
            </div>
            <div class="w-24 h-4 rounded bg-gray-200 hidden sm:block" />
            <div class="w-24 h-4 rounded bg-gray-200 hidden md:block" />
            <div class="w-8 h-8 rounded-lg bg-gray-200" />
          </div>
        </div>

        <!-- Tabla con datos -->
        <div v-else-if="forms.length > 0">
          <!-- Cabecera de tabla (solo en sm+) -->
          <div class="hidden sm:grid sm:grid-cols-[140px_1fr_140px_140px_48px] gap-4 px-6 py-3
                      border-b border-gray-100 bg-gray-50/60">
            <span class="font-cuerpo text-xs font-semibold text-gray-500 uppercase tracking-wide">Estado</span>
            <span class="font-cuerpo text-xs font-semibold text-gray-500 uppercase tracking-wide">Dependencia / Usuario</span>
            <span class="font-cuerpo text-xs font-semibold text-gray-500 uppercase tracking-wide">Fecha carga</span>
            <span class="font-cuerpo text-xs font-semibold text-gray-500 uppercase tracking-wide">Fecha validación</span>
            <span />
          </div>

          <!-- Filas -->
          <div
            v-for="form in forms"
            :key="form.id"
            class="grid grid-cols-1 sm:grid-cols-[140px_1fr_140px_140px_48px] gap-3 sm:gap-4
                   px-6 py-4 border-b border-gray-50 hover:bg-gray-50/50 cursor-pointer transition group"
            @click="goToForm(form.id)"
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

            <!-- Dependencia / usuario -->
            <div class="flex flex-col justify-center min-w-0">
              <p class="font-cuerpo text-sm text-ubpd-gris group-hover:text-ubpd-teal transition truncate">
                {{ form.dependencia_nombre || form.usuario_nombre || '—' }}
              </p>
              <p v-if="form.usuario_nombre && form.dependencia_nombre" class="font-cuerpo text-xs text-gray-400 truncate">
                {{ form.usuario_nombre }}
              </p>
            </div>

            <!-- Fecha carga -->
            <div class="flex flex-col justify-center">
              <p class="font-cuerpo text-sm text-gray-600">{{ formatDate(form.fecha_carga) }}</p>
              <p class="font-cuerpo text-xs text-gray-400">{{ formatTime(form.fecha_carga) }}</p>
            </div>

            <!-- Fecha validación -->
            <div class="flex flex-col justify-center">
              <template v-if="form.fecha_validacion">
                <p class="font-cuerpo text-sm text-gray-600">{{ formatDate(form.fecha_validacion) }}</p>
                <p class="font-cuerpo text-xs text-gray-400">{{ formatTime(form.fecha_validacion) }}</p>
              </template>
              <span v-else class="font-cuerpo text-xs text-gray-300">—</span>
            </div>

            <!-- Flecha -->
            <div class="flex items-center justify-end">
              <svg
                class="w-4 h-4 text-gray-300 group-hover:text-ubpd-teal transition"
                fill="none" viewBox="0 0 24 24" stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </div>

          <!-- Paginación -->
          <div v-if="totalPages > 1" class="px-6 py-4 border-t border-gray-100 flex items-center justify-between">
            <p class="font-cuerpo text-sm text-gray-500">
              Página {{ currentPage }} de {{ totalPages }}
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
              <span class="font-cuerpo text-sm text-gray-600 px-3">
                {{ currentPage }} / {{ totalPages }}
              </span>
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

        <!-- Sin registros -->
        <div v-else class="py-16 text-center">
          <div class="w-16 h-16 rounded-2xl bg-gray-100 flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <p class="font-subtitulo font-semibold text-ubpd-gris">Sin registros</p>
          <p class="font-cuerpo text-sm text-gray-400 mt-1">
            {{ statusFilter ? 'No hay registros con ese estado' : 'Aún no hay registros para este formulario' }}
          </p>
          <button
            v-if="isDependencyUser && !statusFilter"
            @click="goToNewForm"
            class="mt-4 inline-flex items-center gap-1.5 font-cuerpo text-sm font-medium
                   text-ubpd-teal hover:underline"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Crear primer registro
          </button>
        </div>
      </div>
    </template>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'

// ─── Tipos ────────────────────────────────────────────────────────────────────

interface FieldConfig {
  name: string
  label: string
  type: string
}

interface Template {
  id: string
  nombre: string
  codigo?: string
  descripcion?: string
  is_active: boolean
  configuracion_campos?: {
    fields?: FieldConfig[]
    campos?: FieldConfig[]
  }
}

interface Form {
  id: string
  estado: 'draft' | 'pending' | 'approved' | 'rejected'
  dependencia_nombre?: string
  usuario_nombre?: string
  fecha_carga: string
  fecha_validacion?: string
}

interface FormsResponse {
  total: number
  page: number
  size: number
  items: Form[]
}

// ─── Setup ────────────────────────────────────────────────────────────────────

const router = useRouter()
const route = useRoute()
const { get } = useApi()
const authStore = useAuthStore()
const notifications = useNotificationsStore()

// ─── Estado ───────────────────────────────────────────────────────────────────

const stage = ref<'templates' | 'forms'>('templates')
const selectedTemplate = ref<Template | null>(null)

// Templates
const templates = ref<Template[]>([])
const loadingTemplates = ref(true)
const templateSearch = ref('')
let debounceTimer: ReturnType<typeof setTimeout> | null = null

// Forms
const forms = ref<Form[]>([])
const loadingForms = ref(false)
const totalForms = ref(0)
const currentPage = ref(1)
const pageSize = 20
const statusFilter = ref('')

// ─── Computed ─────────────────────────────────────────────────────────────────

const isDependencyUser = computed(() => authStore.user?.role === 'dependency_user')
const isAdmin = computed(() => authStore.user?.role === 'admin')
const isValidatorOrAdmin = computed(() =>
  authStore.user?.role === 'validator' || authStore.user?.role === 'admin',
)

// ── Conteos por template (admin) para habilitar acciones destructivas ─────
interface TemplateCount {
  total: number
  approved: number
  pending: number
  draft: number
  rejected: number
}
const templateCounts = ref<Record<string, TemplateCount>>({})

function templateCount(id: string): TemplateCount {
  return templateCounts.value[id] || { total: 0, approved: 0, pending: 0, draft: 0, rejected: 0 }
}

// ── Descarga consolidada por template (admin) ─────────────────────────────
const downloadingKey = ref<string | null>(null)

async function confirmDeleteRegistros(tmpl: Template) {
  const ok = window.confirm(
    `⚠️ ¿Eliminar TODOS los registros del template "${tmpl.nombre}"?\n\n` +
    `Esta acción elimina todos los formularios respondidos (en cualquier estado) ` +
    `junto con sus archivos adjuntos. No se puede deshacer.`,
  )
  if (!ok) return
  try {
    const apiUrl = import.meta.env.VITE_API_URL || '/api'
    const token = localStorage.getItem('ubpd_access_token')
    const resp = await fetch(`${apiUrl}/admin/templates/${tmpl.id}/registros`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const data = await resp.json()
    notifications.success('Registros eliminados', data.mensaje || '')
    await loadTemplates()
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'No se pudo eliminar.'
    notifications.error('Error', msg)
  }
}

async function confirmDeleteTemplate(tmpl: Template) {
  const ok = window.confirm(
    `⚠️ ¿Eliminar el TEMPLATE "${tmpl.nombre}"?\n\n` +
    `Solo se puede borrar si NO tiene registros. Si hay registros, primero usa "Vaciar".`,
  )
  if (!ok) return
  try {
    const apiUrl = import.meta.env.VITE_API_URL || '/api'
    const token = localStorage.getItem('ubpd_access_token')
    const resp = await fetch(`${apiUrl}/admin/templates/${tmpl.id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!resp.ok) {
      if (resp.status === 409) {
        const body = await resp.json().catch(() => ({}))
        throw new Error(body.detail || 'El template aún tiene registros.')
      }
      throw new Error(`HTTP ${resp.status}`)
    }
    const data = await resp.json()
    notifications.success('Template eliminado', data.mensaje || '')
    await loadTemplates()
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'No se pudo eliminar.'
    notifications.error('Error', msg)
  }
}

async function downloadTemplateForms(tmpl: Template, format: 'excel' | 'zip') {
  const key = `${tmpl.id}:${format}`
  downloadingKey.value = key
  try {
    const apiUrl = import.meta.env.VITE_API_URL || '/api'
    const token = localStorage.getItem('ubpd_access_token')
    const endpoint = format === 'excel' ? 'export-excel' : 'export-zip'
    const response = await fetch(`${apiUrl}/admin/templates/${tmpl.id}/${endpoint}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!response.ok) {
      if (response.status === 404) throw new Error('Template no encontrado')
      if (response.status === 403) throw new Error('No tienes permiso para esta descarga')
      throw new Error(`HTTP ${response.status}`)
    }
    const disposition = response.headers.get('Content-Disposition') || ''
    const match = disposition.match(/filename="([^"]+)"/)
    const defaultName = format === 'excel'
      ? `formularios_${tmpl.codigo || tmpl.id}.xlsx`
      : `formularios_${tmpl.codigo || tmpl.id}.zip`
    const filename = match?.[1] || defaultName

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)

    notifications.success(
      'Descarga iniciada',
      format === 'excel'
        ? 'Excel con los formularios respondidos descargado.'
        : 'ZIP con Excel + evidencias por formulario descargado.',
    )
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'No se pudo descargar el archivo.'
    notifications.error('Error al descargar', msg)
  } finally {
    downloadingKey.value = null
  }
}

const filteredTemplates = computed(() => {
  const q = templateSearch.value.trim().toLowerCase()
  if (!q) return templates.value
  return templates.value.filter(
    (t) =>
      t.nombre.toLowerCase().includes(q) ||
      (t.codigo ?? '').toLowerCase().includes(q) ||
      (t.descripcion ?? '').toLowerCase().includes(q),
  )
})

const totalPages = computed(() => Math.max(1, Math.ceil(totalForms.value / pageSize)))

// ─── Ruta base según prefijo del path ─────────────────────────────────────────

function getBaseRoute(): string {
  const path = route.path
  if (path.startsWith('/admin')) return '/admin/registros'
  if (path.startsWith('/validator')) return '/validator/registros'
  return '/dependency/registros'
}

// ─── Búsqueda de templates con debounce ───────────────────────────────────────

watch(templateSearch, () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    loadTemplates()
  }, 300)
})

async function loadTemplates() {
  loadingTemplates.value = true
  try {
    const q = templateSearch.value.trim()
    const url = q ? `/templates?search=${encodeURIComponent(q)}` : '/templates'
    templates.value = await get<Template[]>(url)
  } catch {
    notifications.error('No se pudo cargar los formularios')
  } finally {
    loadingTemplates.value = false
  }
  // Cargar conteos por template (solo admin) para habilitar/deshabilitar acciones
  if (isAdmin.value) {
    try {
      templateCounts.value = await get<Record<string, TemplateCount>>('/admin/templates/counts')
    } catch {
      templateCounts.value = {}
    }
  }
}

// ─── Selección de template ────────────────────────────────────────────────────

function selectTemplate(tmpl: Template) {
  selectedTemplate.value = tmpl
  stage.value = 'forms'
  statusFilter.value = ''
  currentPage.value = 1
  // Actualizar URL con templateId
  router.replace(`${getBaseRoute()}/${tmpl.id}`)
  loadForms(1)
}

function backToTemplates() {
  stage.value = 'templates'
  selectedTemplate.value = null
  forms.value = []
  router.replace(getBaseRoute())
}

// ─── Carga de formularios ─────────────────────────────────────────────────────

async function loadForms(page: number) {
  if (!selectedTemplate.value) return
  loadingForms.value = true
  currentPage.value = page
  try {
    const params = new URLSearchParams({
      page: String(page),
      size: String(pageSize),
    })
    if (statusFilter.value) params.append('estado', statusFilter.value)

    const data = await get<FormsResponse>(
      `/templates/${selectedTemplate.value.id}/forms?${params.toString()}`,
    )
    forms.value = data.items
    totalForms.value = data.total
  } catch {
    notifications.error('No se pudo cargar los registros')
  } finally {
    loadingForms.value = false
  }
}

// ─── Navegación ───────────────────────────────────────────────────────────────

function goToForm(formId: string) {
  if (!selectedTemplate.value) return
  router.push(`${getBaseRoute()}/${selectedTemplate.value.id}/${formId}`)
}

function goToNewForm() {
  if (!selectedTemplate.value) return
  router.push(`${getBaseRoute()}/${selectedTemplate.value.id}/nuevo`)
}

// ─── Helpers visuales ─────────────────────────────────────────────────────────

function countCampos(tmpl: Template): number {
  const cfg = tmpl.configuracion_campos ?? {}
  return (cfg.fields ?? cfg.campos ?? []).length
}

function formatDate(d: string): string {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('es-CO', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function formatTime(d: string): string {
  if (!d) return ''
  return new Date(d).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })
}

function statusLabel(estado: string): string {
  const map: Record<string, string> = {
    draft: 'Borrador',
    pending: 'Pendiente',
    approved: 'Aprobado',
    rejected: 'Rechazado',
  }
  return map[estado] ?? estado
}

function statusBadgeClass(estado: string): string {
  const map: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-500',
    pending: 'bg-yellow-50 text-yellow-700',
    approved: 'bg-ubpd-verde/10 text-ubpd-verde',
    rejected: 'bg-red-50 text-red-600',
  }
  return map[estado] ?? 'bg-gray-100 text-gray-500'
}

function statusDotClass(estado: string): string {
  const map: Record<string, string> = {
    draft: 'bg-gray-400',
    pending: 'bg-yellow-500',
    approved: 'bg-ubpd-verde',
    rejected: 'bg-red-500',
  }
  return map[estado] ?? 'bg-gray-400'
}

// ─── Init: detectar si hay templateId en la URL ───────────────────────────────

onMounted(async () => {
  await loadTemplates()

  // Detectar templateId en la ruta actual
  const templateId = route.params.templateId as string | undefined
  if (templateId && templates.value.length > 0) {
    const found = templates.value.find((t) => t.id === templateId)
    if (found) {
      selectTemplate(found)
    }
  } else if (templateId && !templates.value.length) {
    // Si se cargó directo con templateId pero no se encontró el template,
    // intentar cargar el template individual
    try {
      const tmpl = await get<Template>(`/templates/${templateId}`)
      if (tmpl) {
        selectedTemplate.value = tmpl
        stage.value = 'forms'
        loadForms(1)
      }
    } catch {
      // No encontrado, quedarse en etapa 1
    }
  }
})
</script>
