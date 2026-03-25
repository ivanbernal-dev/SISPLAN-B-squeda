<template>
  <div class="flex flex-col h-full min-h-screen bg-gray-50">
    <!-- Top bar -->
    <div class="bg-white border-b border-gray-200 px-4 py-3 flex flex-wrap items-center gap-3 shadow-sm z-20">
      <RouterLink to="/admin/pipeline-editor" class="text-gray-400 hover:text-ubpd-gris transition-colors">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 256 256" fill="currentColor"><path d="M165.66,202.34a8,8,0,0,1-11.32,11.32l-80-80a8,8,0,0,1,0-11.32l80-80a8,8,0,0,1,11.32,11.32L91.31,128Z"/></svg>
      </RouterLink>
      <div class="flex-1 min-w-0">
        <input
          v-model="pipelineName"
          class="text-base font-semibold font-montserrat text-ubpd-gris bg-transparent border-none outline-none w-full max-w-xs truncate"
          placeholder="Nombre del pipeline"
        />
      </div>
      <div class="flex items-center gap-2 ml-auto flex-wrap">
        <button type="button" @click="addNode('data_source')"
          class="px-3 py-1.5 text-xs font-semibold font-barlow rounded-lg border border-blue-300 text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors">
          + Fuente
        </button>
        <button type="button" @click="addNode('processor')"
          class="px-3 py-1.5 text-xs font-semibold font-barlow rounded-lg border border-purple-300 text-purple-700 bg-purple-50 hover:bg-purple-100 transition-colors">
          + Procesador
        </button>
        <button type="button" @click="addNode('nivel2_output')"
          class="px-3 py-1.5 text-xs font-semibold font-barlow rounded-lg border border-orange-300 text-orange-700 bg-orange-50 hover:bg-orange-100 transition-colors">
          + Nivel 2
        </button>
        <button type="button" @click="addNode('nivel1_output')"
          class="px-3 py-1.5 text-xs font-semibold font-barlow rounded-lg border border-green-300 text-green-700 bg-green-50 hover:bg-green-100 transition-colors">
          + Nivel 1
        </button>
        <div class="w-px h-6 bg-gray-200 mx-1 hidden sm:block" />
        <button type="button" @click="savePipeline" :disabled="saving"
          class="px-4 py-1.5 text-sm font-semibold font-barlow rounded-lg bg-ubpd-teal text-white hover:bg-teal-700 transition-colors disabled:opacity-50">
          {{ saving ? 'Guardando...' : 'Guardar' }}
        </button>
        <button type="button" @click="executePipeline" :disabled="executing"
          class="px-4 py-1.5 text-sm font-semibold font-barlow rounded-lg bg-ubpd-verde text-white hover:bg-green-700 transition-colors disabled:opacity-50">
          {{ executing ? 'Ejecutando...' : 'Ejecutar' }}
        </button>
        <button type="button" @click="exportPipeline"
          class="px-3 py-1.5 text-xs font-semibold font-barlow rounded-lg border border-gray-300 text-gray-600 hover:border-ubpd-teal hover:text-ubpd-teal transition-colors">
          Exportar
        </button>
        <label class="px-3 py-1.5 text-xs font-semibold font-barlow rounded-lg border border-gray-300 text-gray-600 hover:border-ubpd-teal hover:text-ubpd-teal transition-colors cursor-pointer">
          Importar
          <input type="file" accept=".json" class="hidden" @change="importPipeline" />
        </label>
      </div>
    </div>

    <!-- Main content -->
    <div class="flex flex-1 overflow-hidden">
      <!-- Canvas area -->
      <div class="flex-1 relative overflow-hidden bg-gray-100" ref="canvasRef"
        @mousemove="onCanvasMouseMove"
        @mouseup="onCanvasMouseUp"
      >
        <!-- Simple node canvas (no external library dependency, fully functional) -->
        <svg
          class="absolute inset-0 w-full h-full"
          @click.self="deselectNode"
        >
          <!-- Grid background -->
          <defs>
            <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#e5e7eb" stroke-width="0.5"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />

          <!-- Edges (arrows) -->
          <g v-for="edge in edges" :key="edge.id">
            <line
              :x1="getNodeCenter(edge.source).x"
              :y1="getNodeCenter(edge.source).y"
              :x2="getNodeCenter(edge.target).x"
              :y2="getNodeCenter(edge.target).y"
              stroke="#94a3b8"
              stroke-width="2"
              marker-end="url(#arrowhead)"
              class="cursor-pointer"
              @click="removeEdge(edge.id)"
            />
          </g>
          <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="#94a3b8" />
            </marker>
          </defs>

          <!-- Active connection line -->
          <line
            v-if="connectingFrom"
            :x1="getNodeCenter(connectingFrom).x"
            :y1="getNodeCenter(connectingFrom).y"
            :x2="mousePos.x"
            :y2="mousePos.y"
            stroke="#0d9488"
            stroke-width="2"
            stroke-dasharray="6,3"
          />
        </svg>

        <!-- Nodes (HTML overlay) -->
        <div
          v-for="node in nodes"
          :key="node.id"
          class="absolute rounded-xl shadow-lg border-2 cursor-move select-none min-w-44"
          :style="{
            left: node.position.x + 'px',
            top: node.position.y + 'px',
            borderColor: selectedNodeId === node.id ? '#0d9488' : nodeColors[node.type].border,
            backgroundColor: nodeColors[node.type].bg,
          }"
          @mousedown="startDrag($event, node.id)"
          @click.stop="selectNode(node.id)"
        >
          <!-- Node header -->
          <div
            class="flex items-center justify-between px-3 py-2 rounded-t-xl text-white text-xs font-semibold font-barlow"
            :style="{ backgroundColor: nodeColors[node.type].header }"
          >
            <span class="truncate max-w-32">{{ node.data.nombre || nodeTypeLabel(node.type) }}</span>
            <div class="flex items-center gap-1 ml-2 shrink-0">
              <!-- Connect button -->
              <button
                type="button"
                class="w-5 h-5 rounded bg-white/20 hover:bg-white/40 flex items-center justify-center transition-colors"
                :title="connectingFrom === node.id ? 'Cancelar conexión' : 'Conectar'"
                @click.stop="toggleConnect(node.id)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 256 256" fill="currentColor"><circle cx="128" cy="128" r="96" fill="none" stroke="currentColor" stroke-width="32"/></svg>
              </button>
              <!-- Delete button -->
              <button
                type="button"
                class="w-5 h-5 rounded bg-white/20 hover:bg-red-500/60 flex items-center justify-center transition-colors"
                title="Eliminar nodo"
                @click.stop="removeNode(node.id)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 256 256" fill="currentColor"><path d="M205.66,194.34a8,8,0,0,1-11.32,11.32L128,139.31,61.66,205.66a8,8,0,0,1-11.32-11.32L116.69,128,50.34,61.66A8,8,0,0,1,61.66,50.34L128,116.69l66.34-66.35a8,8,0,0,1,11.32,11.32L139.31,128Z"/></svg>
              </button>
            </div>
          </div>
          <!-- Node body -->
          <div class="px-3 py-2 text-xs font-barlow text-gray-600">
            <div v-if="node.type === 'data_source'" class="truncate max-w-40">
              {{ node.data.template_id ? `Template: ${node.data.template_id.slice(0,8)}…` : 'Sin template' }}
            </div>
            <div v-else-if="node.type === 'processor'" class="truncate max-w-40">
              {{ node.data.codigo_python ? 'Código Python' : 'Sin código' }}
            </div>
            <div v-else-if="node.type === 'nivel2_output'" class="truncate max-w-40">
              {{ node.data.indicador_nivel2_id ? `Indicador N2: ${node.data.indicador_nivel2_id}` : 'Sin indicador' }}
            </div>
            <div v-else-if="node.type === 'nivel1_output'" class="truncate max-w-40">
              {{ node.data.indicador_nivel1_id ? `Indicador N1: ${node.data.indicador_nivel1_id}` : 'Sin indicador' }}
            </div>
          </div>
          <!-- Connection indicator when connecting -->
          <div
            v-if="connectingFrom && connectingFrom !== node.id"
            class="absolute inset-0 rounded-xl border-2 border-teal-500 bg-teal-50/50 flex items-center justify-center cursor-pointer"
            @click.stop="finishConnect(node.id)"
          >
            <span class="text-xs font-semibold text-teal-700 font-barlow">Conectar aquí</span>
          </div>
        </div>

        <!-- Empty state -->
        <div v-if="nodes.length === 0" class="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div class="text-center text-gray-400">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 256 256" fill="currentColor" class="mx-auto mb-3 opacity-40">
              <path d="M230.14,58.87A8,8,0,0,0,224,56H188V48a8,8,0,0,0-8-8H76a8,8,0,0,0-8,8v8H32a8,8,0,0,0-8,8.53l26,176A8,8,0,0,0,58,248H198a8,8,0,0,0,7.92-7.47l26-176A8,8,0,0,0,230.14,58.87ZM84,56H172v8H84Zm105.35,176H66.65L42.7,72H213.3Z"/>
            </svg>
            <p class="font-barlow text-sm">Usa los botones del menú para añadir nodos</p>
            <p class="font-barlow text-xs mt-1">Arrastra para moverlos, haz click en el círculo para conectar</p>
          </div>
        </div>
      </div>

      <!-- Right panel: Node editor -->
      <div v-if="selectedNode" class="w-80 bg-white border-l border-gray-200 flex flex-col overflow-y-auto shadow-lg z-10">
        <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
          <h3 class="text-sm font-semibold font-montserrat text-ubpd-gris">
            {{ nodeTypeLabel(selectedNode.type) }}
          </h3>
          <button type="button" @click="deselectNode" class="text-gray-400 hover:text-ubpd-gris">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 256 256" fill="currentColor"><path d="M205.66,194.34a8,8,0,0,1-11.32,11.32L128,139.31,61.66,205.66a8,8,0,0,1-11.32-11.32L116.69,128,50.34,61.66A8,8,0,0,1,61.66,50.34L128,116.69l66.34-66.35a8,8,0,0,1,11.32,11.32L139.31,128Z"/></svg>
          </button>
        </div>

        <div class="p-4 space-y-4 flex-1">
          <!-- Common: nombre -->
          <div>
            <label class="text-xs font-semibold font-barlow text-gray-500 block mb-1">Nombre del nodo</label>
            <input
              v-model="selectedNode.data.nombre"
              type="text"
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-barlow focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-teal-100"
              placeholder="Nombre descriptivo"
            />
          </div>

          <!-- data_source: template_id -->
          <div v-if="selectedNode.type === 'data_source'">
            <label class="text-xs font-semibold font-barlow text-gray-500 block mb-1">Template ID</label>
            <input
              v-model="selectedNode.data.template_id"
              type="text"
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-teal-100"
              placeholder="UUID del template"
            />
            <p class="text-xs text-gray-400 font-barlow mt-1">Carga formularios aprobados de este template</p>
          </div>

          <!-- processor: codigo_python -->
          <div v-if="selectedNode.type === 'processor'">
            <label class="text-xs font-semibold font-barlow text-gray-500 block mb-1">Código Python</label>
            <textarea
              v-model="selectedNode.data.codigo_python"
              rows="12"
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-xs font-mono resize-y focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-teal-100 bg-gray-50"
              placeholder="# df contiene el DataFrame de entrada
# Asigna el resultado a: result
# Ejemplo:
result = df['calculo_formula'].mean()"
            />
            <p class="text-xs text-gray-400 font-barlow mt-1">Variables disponibles: <code class="bg-gray-100 px-1 rounded">df</code>, <code class="bg-gray-100 px-1 rounded">pd</code></p>
          </div>

          <!-- nivel2_output -->
          <div v-if="selectedNode.type === 'nivel2_output'">
            <label class="text-xs font-semibold font-barlow text-gray-500 block mb-1">ID Indicador Nivel 2</label>
            <input
              v-model.number="selectedNode.data.indicador_nivel2_id"
              type="number"
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-barlow focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-teal-100"
              placeholder="ID del indicador nivel 2"
            />
            <label class="text-xs font-semibold font-barlow text-gray-500 block mb-1 mt-3">Agregación por defecto</label>
            <select v-model="selectedNode.data.aggregation"
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-barlow focus:outline-none focus:border-ubpd-verde">
              <option value="mean">Promedio (mean)</option>
              <option value="sum">Suma (sum)</option>
              <option value="count">Conteo (count)</option>
            </select>
            <label class="text-xs font-semibold font-barlow text-gray-500 block mb-1 mt-3">Código Python personalizado (opcional)</label>
            <textarea
              v-model="selectedNode.data.codigo_python"
              rows="6"
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-xs font-mono resize-y focus:outline-none focus:border-ubpd-verde bg-gray-50"
              placeholder="# Opcional: calcula el valor escalar
# result = df['calculo_formula'].mean()"
            />
          </div>

          <!-- nivel1_output -->
          <div v-if="selectedNode.type === 'nivel1_output'">
            <label class="text-xs font-semibold font-barlow text-gray-500 block mb-1">ID Indicador Nivel 1</label>
            <input
              v-model.number="selectedNode.data.indicador_nivel1_id"
              type="number"
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-barlow focus:outline-none focus:border-ubpd-verde focus:ring-2 focus:ring-teal-100"
              placeholder="ID del indicador nivel 1"
            />
            <label class="text-xs font-semibold font-barlow text-gray-500 block mb-1 mt-3">Código Python personalizado (opcional)</label>
            <textarea
              v-model="selectedNode.data.codigo_python"
              rows="8"
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-xs font-mono resize-y focus:outline-none focus:border-ubpd-verde bg-gray-50"
              placeholder="# nivel2_outputs contiene {nivel2_id: valor}
# result = sum(nivel2_outputs.values()) / len(nivel2_outputs)"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Debug log panel (bottom) -->
    <div
      v-if="showDebug"
      class="bg-gray-900 text-green-400 font-mono text-xs p-4 max-h-48 overflow-y-auto border-t border-gray-700 relative"
    >
      <div class="flex items-center justify-between mb-2">
        <span class="text-gray-400 font-semibold">Log de ejecución</span>
        <button type="button" @click="showDebug = false" class="text-gray-500 hover:text-white transition-colors">✕</button>
      </div>
      <pre class="whitespace-pre-wrap">{{ debugLog || 'Sin logs disponibles.' }}</pre>
    </div>

    <!-- Status bar -->
    <div class="bg-white border-t border-gray-200 px-4 py-2 flex items-center justify-between text-xs font-barlow text-gray-500">
      <span>{{ nodes.length }} nodo(s) — {{ edges.length }} conexión(es)</span>
      <span v-if="lastSaved">Guardado {{ formatTime(lastSaved) }}</span>
      <button type="button" v-if="lastExecution" @click="showDebug = !showDebug"
        class="text-ubpd-teal hover:underline">
        {{ showDebug ? 'Ocultar log' : 'Ver log' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'

const canvasRef = ref<HTMLDivElement | null>(null)
import { useApi } from '@/composables/useApi'
import { useNotificationsStore } from '@/stores/notifications'

interface NodeData {
  nombre?: string
  template_id?: string
  codigo_python?: string
  indicador_nivel2_id?: number
  indicador_nivel1_id?: number
  aggregation?: string
  [key: string]: unknown
}

interface PipelineNode {
  id: string
  type: string
  position: { x: number; y: number }
  data: NodeData
}

interface PipelineEdge {
  id: string
  source: string
  target: string
}

interface Pipeline {
  id: string
  nombre: string
  descripcion?: string
  grafo: { nodes: PipelineNode[]; edges: PipelineEdge[] }
  activo: boolean
}

const route = useRoute()
const { get, post, put } = useApi()
const notifications = useNotificationsStore()

const pipelineId = computed(() => route.params.id as string | undefined)
const pipelineName = ref('Nuevo Pipeline')
const nodes = ref<PipelineNode[]>([])
const edges = ref<PipelineEdge[]>([])
const selectedNodeId = ref<string | null>(null)
const connectingFrom = ref<string | null>(null)
const mousePos = ref({ x: 0, y: 0 })
const saving = ref(false)
const executing = ref(false)
const lastSaved = ref<Date | null>(null)
const debugLog = ref('')
const showDebug = ref(false)
const lastExecution = ref<unknown>(null)

const selectedNode = computed(() =>
  selectedNodeId.value ? nodes.value.find((n) => n.id === selectedNodeId.value) ?? null : null
)

const nodeColors: Record<string, { border: string; bg: string; header: string }> = {
  data_source: { border: '#3b82f6', bg: '#eff6ff', header: '#2563eb' },
  processor: { border: '#8b5cf6', bg: '#f5f3ff', header: '#7c3aed' },
  nivel2_output: { border: '#f97316', bg: '#fff7ed', header: '#ea580c' },
  nivel1_output: { border: '#22c55e', bg: '#f0fdf4', header: '#16a34a' },
}

function nodeTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    data_source: 'Fuente de Datos',
    processor: 'Procesador',
    nivel2_output: 'Salida Nivel 2',
    nivel1_output: 'Salida Nivel 1',
  }
  return labels[type] ?? type
}

function getNodeCenter(nodeId: string): { x: number; y: number } {
  const node = nodes.value.find((n) => n.id === nodeId)
  if (!node) return { x: 0, y: 0 }
  return { x: node.position.x + 88, y: node.position.y + 32 }
}

let nodeCounter = 0
function addNode(type: string) {
  nodeCounter++
  const id = `node_${Date.now()}_${nodeCounter}`
  const baseX = 100 + (nodes.value.length % 4) * 220
  const baseY = 100 + Math.floor(nodes.value.length / 4) * 150
  nodes.value.push({
    id,
    type,
    position: { x: baseX, y: baseY },
    data: { nombre: nodeTypeLabel(type) },
  })
}

function removeNode(nodeId: string) {
  nodes.value = nodes.value.filter((n) => n.id !== nodeId)
  edges.value = edges.value.filter((e) => e.source !== nodeId && e.target !== nodeId)
  if (selectedNodeId.value === nodeId) selectedNodeId.value = null
}

function removeEdge(edgeId: string) {
  edges.value = edges.value.filter((e) => e.id !== edgeId)
}

function selectNode(nodeId: string) {
  if (connectingFrom.value) {
    finishConnect(nodeId)
    return
  }
  selectedNodeId.value = nodeId
}

function deselectNode() {
  selectedNodeId.value = null
  connectingFrom.value = null
}

function toggleConnect(nodeId: string) {
  if (connectingFrom.value === nodeId) {
    connectingFrom.value = null
  } else {
    connectingFrom.value = nodeId
  }
}

function finishConnect(targetId: string) {
  if (!connectingFrom.value || connectingFrom.value === targetId) {
    connectingFrom.value = null
    return
  }
  // Check if edge already exists
  const exists = edges.value.some(
    (e) => e.source === connectingFrom.value && e.target === targetId
  )
  if (!exists) {
    edges.value.push({
      id: `edge_${Date.now()}`,
      source: connectingFrom.value,
      target: targetId,
    })
  }
  connectingFrom.value = null
}

// Drag support
let draggingNodeId: string | null = null
let dragOffset = { x: 0, y: 0 }

function startDrag(event: MouseEvent, nodeId: string) {
  event.preventDefault()
  draggingNodeId = nodeId
  const node = nodes.value.find((n) => n.id === nodeId)!
  const canvasRect = canvasRef.value?.getBoundingClientRect() ?? { left: 0, top: 0 }
  dragOffset = {
    x: event.clientX - canvasRect.left - node.position.x,
    y: event.clientY - canvasRect.top - node.position.y,
  }
}

function onCanvasMouseMove(event: MouseEvent) {
  const canvasRect = canvasRef.value?.getBoundingClientRect() ?? { left: 0, top: 0 }
  mousePos.value = {
    x: event.clientX - canvasRect.left,
    y: event.clientY - canvasRect.top,
  }
  if (draggingNodeId) {
    const node = nodes.value.find((n) => n.id === draggingNodeId)
    if (node) {
      node.position.x = Math.max(0, event.clientX - canvasRect.left - dragOffset.x)
      node.position.y = Math.max(0, event.clientY - canvasRect.top - dragOffset.y)
    }
  }
}

function onCanvasMouseUp() {
  draggingNodeId = null
}

async function savePipeline() {
  saving.value = true
  try {
    const grafo = {
      nodes: nodes.value,
      edges: edges.value,
    }
    const payload = {
      nombre: pipelineName.value,
      grafo,
      activo: true,
    }

    if (pipelineId.value && pipelineId.value !== 'new') {
      await put(`/pipeline-definitions/${pipelineId.value}`, payload)
    } else {
      const created = await post<Pipeline>('/pipeline-definitions', payload)
      // Navigate to edit URL without reload
      history.replaceState(null, '', `/admin/pipeline-editor/${created.id}`)
    }
    lastSaved.value = new Date()
    notifications.success('Guardado', 'El pipeline ha sido guardado.')
  } catch {
    notifications.error('Error', 'No se pudo guardar el pipeline.')
  } finally {
    saving.value = false
  }
}

async function executePipeline() {
  if (!pipelineId.value || pipelineId.value === 'new') {
    notifications.warning('Guardar primero', 'Guarda el pipeline antes de ejecutarlo.')
    return
  }
  executing.value = true
  try {
    interface ExecResult { estado: string; log_debug?: string; resultado?: Record<string, unknown> }
    const result = await post<ExecResult>(`/pipeline-definitions/${pipelineId.value}/execute`, {})
    lastExecution.value = result
    debugLog.value = result.log_debug ?? 'Sin log.'
    showDebug.value = true
    if (result.estado === 'success') {
      notifications.success('Ejecutado', 'Pipeline ejecutado exitosamente.')
    } else {
      notifications.error('Error en pipeline', 'La ejecución terminó con errores. Ver log.')
    }
  } catch {
    notifications.error('Error', 'No se pudo ejecutar el pipeline.')
  } finally {
    executing.value = false
  }
}

function exportPipeline() {
  const data = JSON.stringify(
    [{ nombre: pipelineName.value, grafo: { nodes: nodes.value, edges: edges.value }, activo: true }],
    null,
    2
  )
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `pipeline_${pipelineName.value.replace(/\s+/g, '_')}.json`
  a.click()
  URL.revokeObjectURL(url)
}

function importPipeline(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = JSON.parse(e.target?.result as string)
      const pipeline = Array.isArray(data) ? data[0] : data
      if (pipeline.grafo) {
        nodes.value = pipeline.grafo.nodes ?? []
        edges.value = pipeline.grafo.edges ?? []
        pipelineName.value = pipeline.nombre ?? 'Pipeline importado'
        notifications.success('Importado', 'Pipeline importado correctamente.')
      }
    } catch {
      notifications.error('Error', 'No se pudo parsear el archivo JSON.')
    }
  }
  reader.readAsText(file)
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })
}

async function loadPipeline(id: string) {
  try {
    const pipeline = await get<Pipeline>(`/pipeline-definitions/${id}`)
    pipelineName.value = pipeline.nombre
    nodes.value = pipeline.grafo.nodes ?? []
    edges.value = pipeline.grafo.edges ?? []
  } catch {
    notifications.error('Error', 'No se pudo cargar el pipeline.')
  }
}

onMounted(() => {
  if (pipelineId.value && pipelineId.value !== 'new') {
    loadPipeline(pipelineId.value)
  }
})
</script>
