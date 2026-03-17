<template>
  <div class="flex min-h-screen flex-col bg-white">

    <!-- ── Header público ────────────────────────────────── -->
    <header class="sticky top-0 z-20 bg-white border-b border-ubpd-gris-borde shadow-sm">
      <div class="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 sm:px-6 md:flex-row md:items-center">

        <!-- Logo + título -->
        <div class="flex items-center gap-4">
          <router-link to="/estadisticas" class="shrink-0">
            <img
              src="/logo-ubpd-placeholder.svg"
              alt="UBPD — Unidad de Búsqueda"
              class="h-10 w-auto"
            />
          </router-link>
          <div class="border-l border-ubpd-gris-borde pl-4">
            <h1 class="text-base font-bold text-ubpd-gris leading-tight">
              Sistema de Estadísticas
            </h1>
            <p class="text-xs text-ubpd-gris/60">Unidad de Búsqueda de Personas dadas por Desaparecidas</p>
          </div>
        </div>

        <!-- DateRangePicker global -->
        <div class="md:ml-auto flex flex-wrap items-center gap-2">

          <!-- Presets rápidos -->
          <div class="flex gap-1 flex-wrap">
            <button
              v-for="preset in presets"
              :key="preset.value"
              class="rounded-full border px-3 py-1 text-xs font-medium transition-colors"
              :class="activePreset === preset.value
                ? 'border-ubpd-teal bg-ubpd-teal text-white'
                : 'border-ubpd-gris-borde text-ubpd-gris/70 hover:border-ubpd-teal hover:text-ubpd-teal'"
              @click="applyPreset(preset.value as DatePreset)"
            >
              {{ preset.label }}
            </button>
          </div>

          <!-- Inputs de fecha -->
          <div class="flex items-center gap-1 rounded-lg border border-ubpd-gris-borde px-2 py-1">
            <PhCalendar :size="16" class="text-ubpd-gris/50 shrink-0" aria-hidden="true" />
            <input
              type="date"
              :value="filter.startDate"
              class="w-32 border-none bg-transparent text-xs text-ubpd-gris outline-none"
              aria-label="Fecha de inicio"
              @change="onStartChange"
            />
            <span class="text-ubpd-gris/40">—</span>
            <input
              type="date"
              :value="filter.endDate"
              class="w-32 border-none bg-transparent text-xs text-ubpd-gris outline-none"
              aria-label="Fecha de fin"
              @change="onEndChange"
            />
          </div>
        </div>
      </div>
    </header>

    <!-- ── Contenido de la vista (3 niveles) ─────────────── -->
    <main class="flex-1">
      <RouterView />
    </main>

    <!-- ── Footer ─────────────────────────────────────────── -->
    <footer class="bg-ubpd-gris text-white/70 py-6 mt-auto">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs">
        <span>© {{ currentYear }} Unidad de Búsqueda de Personas dadas por Desaparecidas — UBPD</span>
        <span class="text-white/40">Sistema de Gestión de Formularios y Estadísticas</span>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterView } from 'vue-router'
import { useStatsFilterStore } from '../stores/statsFilter'
import type { DatePreset } from '../stores/statsFilter'
import { PhCalendar } from '@phosphor-icons/vue'

const filter = useStatsFilterStore()

const currentYear = new Date().getFullYear()
const activePreset = ref<DatePreset | null>('thisYear')

const presets: Array<{ label: string; value: DatePreset }> = [
  { label: 'Este mes',         value: 'thisMonth'    },
  { label: 'Último trimestre', value: 'lastQuarter'  },
  { label: 'Año actual',       value: 'thisYear'     },
]

function applyPreset(preset: DatePreset) {
  activePreset.value = preset
  filter.setPreset(preset)
}

function onStartChange(e: Event) {
  activePreset.value = null
  const val = (e.target as HTMLInputElement).value
  filter.setRange(val, filter.endDate)
}

function onEndChange(e: Event) {
  activePreset.value = null
  const val = (e.target as HTMLInputElement).value
  filter.setRange(filter.startDate, val)
}
</script>
