<template>
  <div class="flex flex-col h-full">

    <!-- ── Toolbar ─────────────────────────────────────────────── -->
    <div class="flex flex-wrap items-center gap-2 px-4 py-3 bg-white border-b border-gray-200 flex-shrink-0">
      <h1 class="font-subtitulo font-bold text-lg text-ubpd-gris mr-2">Editor de Pipeline</h1>

      <!-- Run test -->
      <button
        @click="runScript('test')"
        :disabled="running"
        class="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-cuerpo font-semibold
               bg-ubpd-teal text-white hover:opacity-90 disabled:opacity-50 transition"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/>
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        Ejecutar prueba
      </button>

      <!-- Run produccion -->
      <button
        @click="confirmProduccion = true"
        :disabled="running"
        class="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-cuerpo font-semibold
               bg-ubpd-naranja text-white hover:opacity-90 disabled:opacity-50 transition"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3l14 9-14 9V3z"/>
        </svg>
        Ejecutar en producción
      </button>

      <div class="h-6 w-px bg-gray-200 mx-1 hidden sm:block" />

      <!-- Save -->
      <button
        @click="saveScript"
        :disabled="saving"
        class="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-cuerpo font-medium
               border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"/>
        </svg>
        Guardar
      </button>

      <!-- Download -->
      <button
        @click="downloadScript"
        class="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-cuerpo font-medium
               border border-gray-300 text-gray-700 hover:bg-gray-50 transition"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
        </svg>
        Descargar .py
      </button>

      <!-- Upload -->
      <label
        class="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-cuerpo font-medium
               border border-gray-300 text-gray-700 hover:bg-gray-50 transition cursor-pointer"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
        </svg>
        Cargar .py
        <input type="file" accept=".py,.txt" class="sr-only" @change="loadFile" />
      </label>

      <!-- Running indicator -->
      <div v-if="running" class="flex items-center gap-1.5 ml-auto text-sm font-cuerpo text-ubpd-teal">
        <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
        Ejecutando...
      </div>
    </div>

    <!-- ── Cuerpo principal ─────────────────────────────────────── -->
    <div class="flex flex-1 overflow-hidden">

      <!-- Panel izquierdo: tablas ──────────────────────────────── -->
      <aside class="w-56 flex-shrink-0 border-r border-gray-200 bg-[#1a1a2e] flex flex-col">
        <div class="px-3 py-2.5 border-b border-white/10">
          <p class="font-cuerpo text-xs font-semibold text-white/50 uppercase tracking-wide">Tablas BD</p>
        </div>
        <div class="flex-1 overflow-y-auto py-1">
          <div v-if="loadingTables" class="px-3 py-4 text-xs text-white/40 font-cuerpo">Cargando...</div>
          <button
            v-for="t in tables"
            :key="t.tabla"
            class="w-full text-left px-3 py-1.5 hover:bg-white/5 transition group"
            @click="insertTableName(t.tabla)"
            :title="`${t.filas} filas — ${t.tamaño}`"
          >
            <p class="font-mono text-xs text-[#9cdcfe] truncate group-hover:text-white">{{ t.tabla }}</p>
            <p class="font-cuerpo text-[10px] text-white/30 group-hover:text-white/50">
              {{ t.filas.toLocaleString() }} filas · {{ t.tamaño }}
            </p>
          </button>
        </div>
      </aside>

      <!-- Editor + consola ─────────────────────────────────────── -->
      <div class="flex-1 flex flex-col overflow-hidden">

        <!-- Editor de código con CodeMirror ────────────────────── -->
        <div class="flex-1 overflow-hidden relative bg-[#282c34]">
          <CodeMirrorEditor v-model="code" />
        </div>

        <!-- Consola de salida ─────────────────────────────────── -->
        <div
          class="border-t border-gray-200 bg-[#0d1117] flex flex-col"
          :style="{ height: consoleHeight + 'px' }"
        >
          <!-- Consola header -->
          <div class="flex items-center gap-3 px-4 py-2 border-b border-white/10 flex-shrink-0">
            <p class="font-cuerpo text-xs font-semibold text-white/50 uppercase tracking-wide">Consola</p>
            <div v-if="lastRun" class="flex items-center gap-2 ml-auto">
              <span
                class="inline-flex items-center gap-1 font-cuerpo text-xs px-2 py-0.5 rounded-full"
                :class="lastRun.ok ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'"
              >
                <span class="w-1.5 h-1.5 rounded-full" :class="lastRun.ok ? 'bg-green-400' : 'bg-red-400'" />
                {{ lastRun.ok ? 'OK' : 'Error' }}
              </span>
              <span class="font-cuerpo text-xs text-white/30">
                {{ lastRun.modo === 'produccion' ? '▶ Producción' : '◎ Prueba' }} · {{ lastRun.time }}
              </span>
            </div>
            <button
              @click="clearConsole"
              class="ml-2 font-cuerpo text-xs text-white/30 hover:text-white/60 transition"
            >
              Limpiar
            </button>
          </div>
          <!-- Consola output -->
          <pre
            ref="consoleRef"
            class="flex-1 overflow-y-auto px-4 py-3 font-mono text-xs leading-5 text-[#c9d1d9] whitespace-pre-wrap"
          >{{ consoleOutput || '> Ejecuta el script para ver la salida aquí...' }}</pre>
        </div>

        <!-- Resize handle -->
        <div
          class="h-1 bg-gray-300 hover:bg-ubpd-teal cursor-ns-resize flex-shrink-0 transition-colors"
          @mousedown="startResize"
        />
      </div>
    </div>

    <!-- ── Modal: confirmar producción ─────────────────────────── -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="confirmProduccion"
          class="fixed inset-0 z-50 flex items-center justify-center p-4"
          role="dialog"
        >
          <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="confirmProduccion = false" />
          <div class="relative bg-white rounded-2xl shadow-2xl max-w-sm w-full z-10 p-6 space-y-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center">
                <svg class="w-5 h-5 text-orange-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
                </svg>
              </div>
              <div>
                <h3 class="font-subtitulo font-bold text-ubpd-gris">Ejecutar en producción</h3>
                <p class="font-cuerpo text-sm text-gray-500">Los resultados se guardarán en la base de datos y actualizarán la vista pública de estadísticas.</p>
              </div>
            </div>
            <div class="flex gap-3 pt-2">
              <button
                @click="confirmProduccion = false"
                class="flex-1 px-4 py-2 rounded-lg border border-gray-300 text-sm font-cuerpo text-gray-600 hover:bg-gray-50 transition"
              >
                Cancelar
              </button>
              <button
                @click="confirmProduccion = false; runScript('produccion')"
                class="flex-1 px-4 py-2 rounded-lg bg-ubpd-naranja text-white text-sm font-cuerpo font-semibold hover:opacity-90 transition"
              >
                Ejecutar ahora
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useApi } from '@/composables/useApi'
import { useNotificationsStore } from '@/stores/notifications'
import CodeMirrorEditor from '@/components/editor/CodeMirrorEditor.vue'

const { get, post } = useApi()
const notifications = useNotificationsStore()

// ── Estado ────────────────────────────────────────────────────
const code = ref('')
const running = ref(false)
const saving = ref(false)
const loadingTables = ref(true)
const consoleOutput = ref('')
const consoleHeight = ref(220)
const confirmProduccion = ref(false)
const consoleRef = ref<HTMLPreElement | null>(null)

interface TableInfo { tabla: string; filas: number; tamaño: string }
const tables = ref<TableInfo[]>([])

interface LastRun { ok: boolean; modo: string; time: string }
const lastRun = ref<LastRun | null>(null)

// ── Cargar datos iniciales ────────────────────────────────────
onMounted(async () => {
  try {
    const data = await get<{ codigo: string; nombre: string }>('/admin/script-pipeline')
    code.value = data.codigo
  } catch {
    notifications.error('No se pudo cargar el script')
  }
  try {
    tables.value = await get<TableInfo[]>('/admin/script-pipeline/tables')
  } catch {
    tables.value = []
  } finally {
    loadingTables.value = false
  }
})

// ── Funciones del editor ──────────────────────────────────────
function insertTableName(name: string) {
  code.value += `\ndfs.get('${name}', pd.DataFrame())`
}

// ── Guardar script ────────────────────────────────────────────
async function saveScript() {
  saving.value = true
  try {
    await post('/admin/script-pipeline/save', { codigo: code.value, nombre: 'Pipeline Principal' })
    notifications.success('Script guardado')
  } catch {
    notifications.error('No se pudo guardar el script')
  } finally {
    saving.value = false
  }
}

// ── Descargar script ──────────────────────────────────────────
function downloadScript() {
  const blob = new Blob([code.value], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'pipeline_ubpd.py'
  a.click()
  URL.revokeObjectURL(url)
}

// ── Cargar archivo .py ────────────────────────────────────────
function loadFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => {
    code.value = ev.target?.result as string ?? ''
    notifications.success(`Archivo "${file.name}" cargado`)
  }
  reader.readAsText(file)
}

// ── Ejecutar script ───────────────────────────────────────────
async function runScript(modo: 'test' | 'produccion') {
  running.value = true
  consoleOutput.value = `> Ejecutando en modo ${modo === 'produccion' ? 'PRODUCCIÓN' : 'prueba'}...\n`

  try {
    const result = await post<{
      ok: boolean
      stdout: string
      stderr: string | null
      modo: string
      guardado: boolean
    }>('/admin/script-pipeline/run', { codigo: code.value, modo })

    let output = ''
    if (result.stdout) output += result.stdout
    if (result.stderr) output += `\n\n⚠️ ERROR:\n${result.stderr}`

    consoleOutput.value = output || '(sin salida)'
    lastRun.value = {
      ok: result.ok,
      modo: result.modo,
      time: new Date().toLocaleTimeString('es-CO'),
    }

    if (result.ok && modo === 'produccion' && result.guardado) {
      notifications.success('Resultados guardados — la vista pública se actualizó')
    } else if (!result.ok) {
      notifications.error('El script terminó con errores — revisa la consola')
    }
  } catch (err: any) {
    consoleOutput.value = `> Error de comunicación: ${err?.message ?? err}`
    lastRun.value = { ok: false, modo, time: new Date().toLocaleTimeString('es-CO') }
  } finally {
    running.value = false
    nextTick(() => {
      if (consoleRef.value) consoleRef.value.scrollTop = consoleRef.value.scrollHeight
    })
  }
}

function clearConsole() {
  consoleOutput.value = ''
  lastRun.value = null
}

// ── Resize consola ────────────────────────────────────────────
function startResize(e: MouseEvent) {
  const startY = e.clientY
  const startH = consoleHeight.value

  function onMove(ev: MouseEvent) {
    const delta = startY - ev.clientY
    consoleHeight.value = Math.max(80, Math.min(600, startH + delta))
  }
  function onUp() {
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
  }
  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}
</script>

<style scoped>
.modal-enter-active, .modal-leave-active { transition: opacity 0.2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
