// ============================================================
// UBPD Frontend — Punto de Entrada
// Vue 3 + Pinia + Vue Router + ECharts
// ============================================================

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './assets/styles/main.css'

// ─── ECharts (registro de componentes necesarios) ──────────
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { GaugeChart, BarChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
} from 'echarts/components'

use([
  CanvasRenderer,
  GaugeChart,
  BarChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
])

// ─── Bootstrap de la aplicación ───────────────────────────
const pinia = createPinia()
const app = createApp(App)

app.use(pinia)
app.use(router)

// Registrar VChart como componente global
app.component('VChart', VChart)

import { vAutoresize } from './directives/autoresize'
app.directive('autoresize', vAutoresize)

// Cargar tokens del localStorage antes de montar
// (el store se inicializa dentro del plugin pinia, pero necesitamos
//  que la acción loadFromStorage se llame después de que pinia esté activo)
import { useAuthStore } from './stores/auth'
const authStore = useAuthStore()
authStore.loadFromStorage()

app.mount('#app')
