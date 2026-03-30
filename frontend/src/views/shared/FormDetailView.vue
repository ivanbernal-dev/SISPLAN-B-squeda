<template>
  <div class="p-6 space-y-5">

    <!-- Loading estado inicial -->
    <div v-if="loadingInitial" class="space-y-5">
      <div class="bg-white rounded-2xl border border-gray-100 p-6 animate-pulse space-y-3">
        <div class="w-64 h-6 rounded bg-gray-200" />
        <div class="w-40 h-4 rounded bg-gray-200" />
      </div>
      <div class="bg-white rounded-2xl border border-gray-100 p-6 animate-pulse space-y-4">
        <div v-for="i in 5" :key="i" class="space-y-1.5">
          <div class="w-32 h-3 rounded bg-gray-200" />
          <div class="w-full h-9 rounded-lg bg-gray-200" />
        </div>
      </div>
    </div>

    <template v-else-if="template && form">

      <!-- ══ HEADER ════════════════════════════════════════════════════════════ -->
      <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div>
          <!-- Breadcrumb -->
          <nav class="flex items-center gap-1.5 font-cuerpo text-sm text-gray-400 mb-1">
            <button
              @click="goBack"
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
            <span class="text-gray-500 truncate max-w-[160px]">{{ template.nombre }}</span>
            <svg class="w-3.5 h-3.5 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
            <span class="text-ubpd-gris font-medium">Detalle</span>
          </nav>

          <!-- Título + badge -->
          <div class="flex items-center gap-3 flex-wrap">
            <h1 class="font-subtitulo font-bold text-2xl text-ubpd-gris">
              {{ template.nombre }}
            </h1>
            <span
              class="inline-flex items-center gap-1.5 font-cuerpo text-xs font-semibold
                     px-2.5 py-1 rounded-full"
              :class="statusBadgeClass(form.estado)"
            >
              <span class="w-1.5 h-1.5 rounded-full" :class="statusDotClass(form.estado)" />
              {{ statusLabel(form.estado) }}
            </span>
          </div>
        </div>
      </div>

      <!-- ══ CAMPOS DEL FORMULARIO ══════════════════════════════════════════════ -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
        <h2 class="font-subtitulo font-semibold text-base text-ubpd-gris mb-4 flex items-center gap-2">
          <svg class="w-4 h-4 text-ubpd-teal" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Datos del registro
        </h2>

        <div v-if="displayFields.length === 0" class="text-center py-8">
          <p class="font-cuerpo text-sm text-gray-400">No hay campos configurados para este formulario</p>
        </div>

        <div v-else class="space-y-4">
          <div v-for="field in displayFields" :key="field.name">
            <label class="block font-cuerpo text-xs font-semibold mb-1.5"
              :class="field.readonly ? 'text-gray-400' : 'text-ubpd-gris'">
              {{ field.label }}
              <span v-if="field.readonly" class="font-normal text-gray-400 ml-1">(solo lectura)</span>
            </label>

            <!-- Select: mostrar valor seleccionado -->
            <div
              v-if="field.type === 'select'"
              class="w-full font-cuerpo text-sm rounded-lg px-3 py-2.5 border min-h-[38px]"
              :class="field.readonly
                ? 'bg-gray-50 border-gray-200 text-gray-400'
                : 'bg-gray-50 border-gray-200 text-ubpd-gris'"
            >
              {{ getFieldValue(field) || '—' }}
            </div>

            <!-- Computed: badge especial -->
            <div
              v-else-if="field.type === 'computed'"
              class="w-full font-cuerpo text-sm rounded-lg px-3 py-2.5 border
                     bg-blue-50 border-blue-200 text-blue-700 flex items-center gap-2"
            >
              <svg class="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 11h.01M12 11h.01M15 11h.01M4 19h16a2 2 0 002-2V7a2 2 0 00-2-2H4a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <span>{{ getFieldValue(field) || 'Calculado automáticamente' }}</span>
            </div>

            <!-- Date: formatear fecha -->
            <div
              v-else-if="field.type === 'date'"
              class="w-full font-cuerpo text-sm rounded-lg px-3 py-2.5 border min-h-[38px]"
              :class="field.readonly
                ? 'bg-gray-50 border-gray-200 text-gray-400'
                : 'bg-gray-50 border-gray-200 text-ubpd-gris'"
            >
              {{ formatFieldDate(getFieldValue(field)) || '—' }}
            </div>

            <!-- Textarea (tipo textarea) con auto-height -->
            <textarea
              v-else-if="field.type === 'textarea'"
              :ref="el => setTextareaRef(el as HTMLTextAreaElement | null, field.name)"
              :value="getFieldValue(field)"
              readonly
              rows="2"
              class="w-full font-cuerpo text-sm rounded-lg px-3 py-2.5 border resize-none
                     cursor-default focus:outline-none min-h-[38px] overflow-hidden leading-relaxed"
              :class="field.readonly
                ? 'bg-gray-50 border-gray-200 text-gray-400'
                : 'bg-gray-50 border-gray-200 text-ubpd-gris'"
            />

            <!-- Text / number / resto: textarea readonly auto-height -->
            <textarea
              v-else
              :ref="el => setTextareaRef(el as HTMLTextAreaElement | null, field.name)"
              :value="getFieldValue(field)"
              readonly
              rows="1"
              class="w-full font-cuerpo text-sm rounded-lg px-3 py-2.5 border resize-none
                     cursor-default focus:outline-none min-h-[38px] overflow-hidden leading-relaxed"
              :class="field.readonly
                ? 'bg-gray-50 border-gray-200 text-gray-400'
                : 'bg-gray-50 border-gray-200 text-ubpd-gris'"
            />
          </div>
        </div>
      </div>

      <!-- ══ QUIÉN LLENÓ EL FORMULARIO (admin / validador) ══════════════════════ -->
      <div v-if="isValidator" class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
        <h2 class="font-subtitulo font-semibold text-base text-ubpd-gris mb-4 flex items-center gap-2">
          <svg class="w-4 h-4 text-ubpd-teal" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          Información del solicitante
        </h2>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div class="flex flex-col gap-1">
            <p class="font-cuerpo text-xs font-semibold text-gray-400 uppercase tracking-wide">Dependencia</p>
            <p class="font-cuerpo text-sm text-ubpd-gris">{{ form.dependencia_nombre || '—' }}</p>
          </div>
          <div class="flex flex-col gap-1">
            <p class="font-cuerpo text-xs font-semibold text-gray-400 uppercase tracking-wide">Usuario</p>
            <p class="font-cuerpo text-sm text-ubpd-gris">{{ form.usuario_nombre || '—' }}</p>
          </div>
          <div class="flex flex-col gap-1">
            <p class="font-cuerpo text-xs font-semibold text-gray-400 uppercase tracking-wide">Fecha de carga</p>
            <p class="font-cuerpo text-sm text-ubpd-gris">{{ form.fecha_carga ? formatDate(form.fecha_carga) : '—' }}</p>
          </div>
        </div>
      </div>

      <!-- ══ SECCIÓN VALIDACIÓN ═════════════════════════════════════════════════ -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
        <h2 class="font-subtitulo font-semibold text-base text-ubpd-gris mb-4 flex items-center gap-2">
          <svg class="w-4 h-4 text-ubpd-teal" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04
                 A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622
                 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          Información de validación
        </h2>

        <!-- Pendiente -->
        <div
          v-if="!form.validador_nombre"
          class="flex items-center gap-3 p-4 rounded-xl bg-gray-50 border border-gray-200"
        >
          <svg class="w-5 h-5 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p class="font-cuerpo text-sm text-gray-400">Pendiente de validación</p>
        </div>

        <!-- Validado (aprobado o rechazado) -->
        <div v-else class="space-y-3">
          <div
            class="flex flex-col sm:flex-row sm:items-center gap-3 p-4 rounded-xl border"
            :class="form.estado === 'approved'
              ? 'bg-ubpd-verde/5 border-ubpd-verde/20'
              : 'bg-orange-50 border-orange-200'"
          >
            <div
              class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
              :class="form.estado === 'approved' ? 'bg-ubpd-verde/10' : 'bg-orange-100'"
            >
              <svg
                class="w-5 h-5"
                :class="form.estado === 'approved' ? 'text-ubpd-verde' : 'text-orange-500'"
                fill="none" viewBox="0 0 24 24" stroke="currentColor"
              >
                <path
                  v-if="form.estado === 'approved'"
                  stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
                <path
                  v-else
                  stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <p class="font-cuerpo font-semibold text-sm"
                :class="form.estado === 'approved' ? 'text-ubpd-verde' : 'text-orange-600'">
                {{ form.validador_nombre }}
              </p>
              <p class="font-cuerpo text-xs text-gray-500 mt-0.5">
                {{ form.validador_correo }}
              </p>
            </div>
            <div class="text-right flex-shrink-0" v-if="form.fecha_validacion">
              <p class="font-cuerpo text-sm text-gray-600">{{ formatDate(form.fecha_validacion) }}</p>
              <p class="font-cuerpo text-xs text-gray-400">{{ formatTime(form.fecha_validacion) }}</p>
            </div>
          </div>

          <!-- Comentario de rechazo -->
          <div
            v-if="form.comentario_rechazo"
            class="p-4 rounded-xl bg-red-50 border border-red-200"
          >
            <p class="font-cuerpo text-xs font-semibold text-red-600 mb-1 flex items-center gap-1.5">
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Motivo de rechazo
            </p>
            <p class="font-cuerpo text-sm text-red-700 leading-relaxed">
              {{ form.comentario_rechazo }}
            </p>
          </div>
        </div>
      </div>

      <!-- ══ SECCIÓN ARCHIVOS ════════════════════════════════════════════════════ -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="font-subtitulo font-semibold text-base text-ubpd-gris flex items-center gap-2">
            <svg class="w-4 h-4 text-ubpd-teal" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585
                   a6 6 0 108.486 8.486L20.5 13" />
            </svg>
            Archivos adjuntos
          </h2>

          <!-- Adjuntar archivo (solo dependency_user en draft o rejected) -->
          <div v-if="canUpload">
            <label
              class="inline-flex items-center gap-1.5 font-cuerpo text-sm font-medium cursor-pointer
                     border border-ubpd-teal text-ubpd-teal rounded-xl px-4 py-2
                     hover:bg-ubpd-teal hover:text-white transition"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              Adjuntar archivo
              <input
                ref="fileInputRef"
                type="file"
                class="hidden"
                multiple
                @change="handleFileUpload"
              />
            </label>
          </div>
        </div>

        <!-- Uploading indicator -->
        <div v-if="uploadingFile" class="mb-3 flex items-center gap-2 text-ubpd-teal font-cuerpo text-sm">
          <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Subiendo archivo...
        </div>

        <!-- Lista de archivos -->
        <div v-if="files.length > 0" class="space-y-2">
          <div
            v-for="file in files"
            :key="file.id"
            class="flex items-center gap-3 p-3 rounded-xl border border-gray-100
                   hover:border-ubpd-teal/20 hover:bg-gray-50/50 transition"
          >
            <!-- Ícono según tipo -->
            <div class="w-9 h-9 rounded-lg bg-ubpd-teal/10 flex items-center justify-center flex-shrink-0">
              <!-- PDF -->
              <svg v-if="file.tipo_mime === 'application/pdf'"
                class="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7
                     a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              <!-- Imagen -->
              <svg v-else-if="file.tipo_mime?.startsWith('image/')"
                class="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14
                     m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <!-- Genérico -->
              <svg v-else class="w-5 h-5 text-ubpd-teal" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293
                     l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>

            <!-- Nombre y tamaño -->
            <div class="flex-1 min-w-0">
              <p class="font-cuerpo text-sm text-ubpd-gris truncate">
                {{ file.nombre || file.nombre_original }}
              </p>
              <p v-if="file.tamanio || file.tamaño_bytes" class="font-cuerpo text-xs text-gray-400">
                {{ formatFileSize(file.tamanio || file.tamaño_bytes || 0) }}
              </p>
            </div>

            <!-- Acciones -->
            <div class="flex items-center gap-2 flex-shrink-0">

              <!-- Ver (solo PDF e imágenes) -->
              <button
                v-if="isViewable(file.tipo_mime)"
                @click="viewFile(file.id, file.tipo_mime)"
                :disabled="activeFileId === file.id"
                class="flex items-center gap-1.5 font-cuerpo text-xs font-medium
                       text-gray-600 border border-gray-200 rounded-lg px-3 py-1.5
                       hover:bg-gray-100 hover:border-gray-300 transition
                       disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg v-if="activeFileId !== file.id || activeFileAction !== 'view'"
                  class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7
                       -1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <svg v-else class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                Ver
              </button>

              <!-- Descargar (siempre) -->
              <button
                @click="downloadFile(file.id, file.nombre || file.nombre_original)"
                :disabled="activeFileId === file.id"
                class="flex items-center gap-1.5 font-cuerpo text-xs font-medium
                       text-ubpd-teal border border-ubpd-teal/30 rounded-lg px-3 py-1.5
                       hover:bg-ubpd-teal hover:text-white hover:border-ubpd-teal transition
                       disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg v-if="activeFileId !== file.id || activeFileAction !== 'download'"
                  class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                <svg v-else class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                Descargar
              </button>
            </div>
          </div>
        </div>

        <!-- Sin archivos -->
        <div v-else class="py-8 text-center">
          <svg class="w-10 h-10 text-gray-200 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
              d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656
                 l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
          </svg>
          <p class="font-cuerpo text-sm text-gray-400">Sin archivos adjuntos</p>
        </div>
      </div>

      <!-- ══ SECCIÓN ACCIONES VALIDADOR ══════════════════════════════════════════ -->
      <div
        v-if="isValidator && form.estado === 'pending'"
        class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6"
      >
        <h2 class="font-subtitulo font-semibold text-base text-ubpd-gris mb-4 flex items-center gap-2">
          <svg class="w-4 h-4 text-ubpd-teal" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5
                 m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          Acciones de validación
        </h2>

        <div class="flex flex-col sm:flex-row gap-3">
          <!-- Aprobar -->
          <button
            @click="approveForm"
            :disabled="actionLoading"
            class="flex-1 flex items-center justify-center gap-2 font-cuerpo text-sm font-semibold
                   bg-ubpd-verde text-white rounded-xl px-5 py-3
                   hover:bg-[#1a7a4d] transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg v-if="!actionLoading" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Aprobar
          </button>

          <!-- Rechazar -->
          <button
            @click="openRejectModal"
            :disabled="actionLoading"
            class="flex-1 flex items-center justify-center gap-2 font-cuerpo text-sm font-semibold
                   border border-red-300 text-red-600 rounded-xl px-5 py-3
                   hover:bg-red-50 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Rechazar
          </button>
        </div>
      </div>

    </template>

    <!-- Error estado -->
    <div v-else-if="!loadingInitial" class="bg-white rounded-2xl border border-gray-100 py-16 text-center">
      <svg class="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4
             c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <p class="font-subtitulo font-semibold text-ubpd-gris">No se pudo cargar el registro</p>
      <p class="font-cuerpo text-sm text-gray-400 mt-1">Verifica que el registro exista</p>
      <button
        @click="goBack"
        class="mt-4 font-cuerpo text-sm text-ubpd-teal hover:underline"
      >
        Volver atrás
      </button>
    </div>

    <!-- ══ MODAL RECHAZO ══════════════════════════════════════════════════════ -->
    <Teleport to="body">
      <Transition name="modal-fade">
        <div
          v-if="showRejectModal"
          class="fixed inset-0 z-50 flex items-center justify-center p-4"
          @click.self="closeRejectModal"
        >
          <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="closeRejectModal" />

          <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-md z-10">
            <!-- Header modal -->
            <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-lg bg-red-100 flex items-center justify-center">
                  <svg class="w-4 h-4 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 class="font-subtitulo font-bold text-base text-ubpd-gris">Rechazar registro</h3>
              </div>
              <button
                @click="closeRejectModal"
                class="text-gray-400 hover:text-gray-600 transition"
              >
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <!-- Body modal -->
            <div class="px-6 py-5">
              <p class="font-cuerpo text-sm text-gray-500 mb-3">
                Indica el motivo de rechazo. Este comentario será visible para el usuario que envió el registro.
              </p>
              <label class="block font-cuerpo text-xs font-semibold text-ubpd-gris mb-1.5">
                Motivo de rechazo <span class="text-ubpd-naranja">*</span>
              </label>
              <textarea
                v-model="rejectComment"
                rows="4"
                placeholder="Describe el motivo de rechazo..."
                class="w-full font-cuerpo text-sm border rounded-xl px-3 py-2.5 resize-none
                       focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-ubpd-verde/20 transition"
                :class="rejectCommentError ? 'border-red-400' : 'border-gray-300'"
              />
              <p v-if="rejectCommentError" class="font-cuerpo text-xs text-red-500 mt-1">
                El motivo de rechazo es obligatorio
              </p>
            </div>

            <!-- Footer modal -->
            <div class="px-6 py-4 border-t border-gray-100 flex gap-3">
              <button
                @click="closeRejectModal"
                class="flex-1 font-cuerpo text-sm font-medium border border-gray-300
                       text-gray-600 rounded-xl px-4 py-2.5 hover:bg-gray-50 transition"
              >
                Cancelar
              </button>
              <button
                @click="rejectForm"
                :disabled="actionLoading"
                class="flex-1 flex items-center justify-center gap-2 font-cuerpo text-sm font-semibold
                       bg-red-600 text-white rounded-xl px-4 py-2.5
                       hover:bg-red-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg v-if="actionLoading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
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
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useApi } from '@/composables/useApi'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'

// ─── Tipos ────────────────────────────────────────────────────────────────────

interface FieldConfig {
  name: string
  label: string
  type: 'text' | 'number' | 'date' | 'select' | 'textarea' | 'computed' | 'archivos' | string
  readonly?: boolean
  required?: boolean
  default?: unknown
  options?: string[]
}

interface Template {
  id: string
  nombre: string
  configuracion_campos?: {
    fields?: FieldConfig[]
    campos?: FieldConfig[]
  }
}

interface ArchivoItem {
  id: string
  nombre_original: string
  nombre: string          // alias enviado por el backend
  tamanio: number         // alias enviado por el backend
  tamaño_bytes?: number
  tipo_mime?: string
}

interface FormDetail {
  id: string
  estado: 'draft' | 'pending' | 'approved' | 'rejected'
  datos_dinamicos: Record<string, unknown>
  archivos?: ArchivoItem[]
  validado_por_id?: string
  validador_nombre?: string
  validador_correo?: string
  fecha_validacion?: string
  comentario_rechazo?: string
  // Quién llenó el formulario
  usuario_nombre?: string
  dependencia_nombre?: string
  fecha_carga?: string
}

// ─── Setup ────────────────────────────────────────────────────────────────────

const router = useRouter()
const route = useRoute()
const { get, patch, postForm, client: apiClient } = useApi()
const authStore = useAuthStore()
const notifications = useNotificationsStore()

// ─── Estado ───────────────────────────────────────────────────────────────────

const loadingInitial = ref(true)
const template = ref<Template | null>(null)
const form = ref<FormDetail | null>(null)
const files = ref<ArchivoItem[]>([])

// Acciones
const actionLoading = ref(false)
const showRejectModal = ref(false)
const rejectComment = ref('')
const rejectCommentError = ref(false)

// Archivos
const fileInputRef = ref<HTMLInputElement | null>(null)
const uploadingFile = ref(false)
// Estado compartido para ver/descargar
const activeFileId     = ref<string | null>(null)
const activeFileAction = ref<'view' | 'download' | null>(null)

// Refs para textareas auto-height
const textareaRefs = ref<Map<string, HTMLTextAreaElement>>(new Map())

// ─── Computed ─────────────────────────────────────────────────────────────────

const isValidator = computed(() =>
  authStore.user?.role === 'validator' || authStore.user?.role === 'admin',
)

const isDependencyUser = computed(() => authStore.user?.role === 'dependency_user')

const canUpload = computed(() =>
  isDependencyUser.value &&
  form.value &&
  (form.value.estado === 'draft' || form.value.estado === 'rejected'),
)

/** Campos visibles: excluir tipo 'archivos' */
const displayFields = computed<FieldConfig[]>(() => {
  if (!template.value) return []
  const cfg = template.value.configuracion_campos ?? {}
  const campos = (cfg.fields ?? cfg.campos ?? []) as FieldConfig[]
  return campos.filter((f) => f.type !== 'archivos')
})

// ─── Ruta base ────────────────────────────────────────────────────────────────

function getBaseRoute(): string {
  const path = route.path
  if (path.startsWith('/admin')) return '/admin/registros'
  if (path.startsWith('/validator')) return '/validator/registros'
  return '/dependency/registros'
}

// ─── Carga de datos ───────────────────────────────────────────────────────────

async function loadData() {
  const templateId = route.params.templateId as string
  const formId = route.params.formId as string

  loadingInitial.value = true
  try {
    const [tmpl, frm] = await Promise.all([
      get<Template>(`/templates/${templateId}`),
      get<FormDetail>(`/forms/${formId}`),
    ])
    template.value = tmpl
    form.value = frm
    files.value = frm.archivos ?? []
  } catch {
    notifications.error('No se pudo cargar el registro')
  } finally {
    loadingInitial.value = false
    // Ajustar alturas de textareas tras render
    nextTick(() => adjustAllTextareas())
  }
}

// ─── Helpers de campo ─────────────────────────────────────────────────────────

function getFieldValue(field: FieldConfig): string {
  if (!form.value) return ''
  const val = form.value.datos_dinamicos[field.name]
  if (val !== undefined && val !== null) return String(val)
  if (field.default !== undefined && field.default !== null && field.readonly) {
    return String(field.default)
  }
  return ''
}

function formatFieldDate(value: string): string {
  if (!value) return ''
  try {
    const d = new Date(value)
    if (isNaN(d.getTime())) return value
    return d.toLocaleDateString('es-CO', { day: '2-digit', month: '2-digit', year: 'numeric' })
  } catch {
    return value
  }
}

// ─── Auto-height textareas ────────────────────────────────────────────────────

function setTextareaRef(el: HTMLTextAreaElement | null, name: string) {
  if (el) {
    textareaRefs.value.set(name, el)
  } else {
    textareaRefs.value.delete(name)
  }
}

function adjustTextarea(el: HTMLTextAreaElement) {
  el.style.height = 'auto'
  el.style.height = `${el.scrollHeight}px`
}

function adjustAllTextareas() {
  textareaRefs.value.forEach((el) => adjustTextarea(el))
}

// Cuando cambian los datos del formulario, re-ajustar
watch(
  () => form.value?.datos_dinamicos,
  () => nextTick(() => adjustAllTextareas()),
  { deep: true },
)

// ─── Navegación ───────────────────────────────────────────────────────────────

function goBack() {
  const templateId = route.params.templateId as string
  router.push(`${getBaseRoute()}/${templateId}`)
}

// ─── Acciones de validación ───────────────────────────────────────────────────

async function approveForm() {
  if (!form.value) return
  actionLoading.value = true
  try {
    await patch(`/validation/${form.value.id}/approve`, {})
    notifications.success('Registro aprobado correctamente')
    await loadData()
  } catch {
    notifications.error('No se pudo aprobar el registro')
  } finally {
    actionLoading.value = false
  }
}

function openRejectModal() {
  rejectComment.value = ''
  rejectCommentError.value = false
  showRejectModal.value = true
}

function closeRejectModal() {
  showRejectModal.value = false
}

async function rejectForm() {
  if (!form.value) return
  if (!rejectComment.value.trim()) {
    rejectCommentError.value = true
    return
  }
  rejectCommentError.value = false
  actionLoading.value = true
  try {
    await patch(`/validation/${form.value.id}/reject`, {
      comentario: rejectComment.value.trim(),
    })
    notifications.success('Registro rechazado')
    closeRejectModal()
    await loadData()
  } catch {
    notifications.error('No se pudo rechazar el registro')
  } finally {
    actionLoading.value = false
  }
}

// ─── Manejo de archivos ───────────────────────────────────────────────────────

async function handleFileUpload(event: Event) {
  if (!form.value) return
  const input = event.target as HTMLInputElement
  const selectedFiles = input.files
  if (!selectedFiles || selectedFiles.length === 0) return

  uploadingFile.value = true
  try {
    for (const file of Array.from(selectedFiles)) {
      const fd = new FormData()
      fd.append('file', file)
      const uploaded = await postForm<ArchivoItem>(`/files/upload/${form.value.id}`, fd)
      files.value.push(uploaded)
    }
    notifications.success('Archivo(s) adjuntado(s) correctamente')
  } catch {
    notifications.error('No se pudo subir el archivo')
  } finally {
    uploadingFile.value = false
    // Limpiar input para permitir volver a seleccionar el mismo archivo
    if (fileInputRef.value) fileInputRef.value.value = ''
  }
}

// ─── Helpers de archivos ──────────────────────────────────────────────────────

function isViewable(mime?: string): boolean {
  if (!mime) return false
  return mime.startsWith('image/') || mime === 'application/pdf'
}

async function _fetchBlob(fileId: string): Promise<{ blob: Blob; contentType: string }> {
  const response = await apiClient.get(`/files/${fileId}/download`, { responseType: 'blob' })
  const contentType = (response.headers['content-type'] as string) || 'application/octet-stream'
  return { blob: new Blob([response.data as BlobPart], { type: contentType }), contentType }
}

async function viewFile(fileId: string, tipoMime?: string) {
  activeFileId.value     = fileId
  activeFileAction.value = 'view'
  try {
    const { blob } = await _fetchBlob(fileId)
    const blobUrl = URL.createObjectURL(blob)
    const win = window.open(blobUrl, '_blank', 'noopener,noreferrer')
    if (win) setTimeout(() => URL.revokeObjectURL(blobUrl), 60_000)
    else URL.revokeObjectURL(blobUrl) // popup bloqueado
  } catch {
    notifications.error('No se pudo abrir el archivo')
  } finally {
    activeFileId.value     = null
    activeFileAction.value = null
  }
}

async function downloadFile(fileId: string, nombre?: string) {
  activeFileId.value     = fileId
  activeFileAction.value = 'download'
  try {
    const { blob } = await _fetchBlob(fileId)
    const blobUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href     = blobUrl
    a.download = nombre || 'archivo'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(blobUrl)
  } catch {
    notifications.error('No se pudo descargar el archivo')
  } finally {
    activeFileId.value     = null
    activeFileAction.value = null
  }
}

// ─── Helpers visuales ─────────────────────────────────────────────────────────

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

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
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

// ─── Init ─────────────────────────────────────────────────────────────────────

onMounted(loadData)
</script>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
.modal-fade-enter-active .relative,
.modal-fade-leave-active .relative {
  transition: transform 0.2s ease;
}
.modal-fade-enter-from .relative,
.modal-fade-leave-to .relative {
  transform: scale(0.96) translateY(8px);
}
</style>
