// ============================================================
// UBPD — Store de Filtros de Estadísticas (Pinia)
// Persiste el rango de fechas al navegar entre los 3 niveles
// ============================================================

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type DatePreset = 'thisMonth' | 'lastQuarter' | 'thisYear'

interface FilterState {
  startDate: string  // YYYY-MM-DD
  endDate: string    // YYYY-MM-DD
}

function toIsoDate(d: Date): string {
  return d.toISOString().split('T')[0]
}

// ─── Store ────────────────────────────────────────────────
export const useStatsFilterStore = defineStore('statsFilter', () => {
  const now = new Date()

  const startDate = ref<string>(toIsoDate(new Date(now.getFullYear(), 0, 1)))
  const endDate   = ref<string>(toIsoDate(now))
  /** Selector temporal de KPIs del PAI: anual | trim1 | trim2 | trim3 | trim4 */
  const periodo   = ref<string>('anual')

  // ─── Getters ──────────────────────────────────────────

  /** Parámetros listos para enviar a la API */
  const apiParams = computed(() => ({
    start_date: startDate.value,
    end_date:   endDate.value,
  }))

  function setPeriodo(p: string): void {
    periodo.value = p
  }

  /** Rango formateado legible */
  const formattedRange = computed(() => {
    const fmt = (s: string) =>
      new Date(s + 'T00:00:00').toLocaleDateString('es-CO', {
        day: '2-digit', month: 'short', year: 'numeric',
      })
    return `${fmt(startDate.value)} — ${fmt(endDate.value)}`
  })

  // ─── Actions ──────────────────────────────────────────

  function setRange(start: string, end: string): void {
    startDate.value = start
    endDate.value   = end
  }

  function setPreset(preset: DatePreset): void {
    const today = new Date()
    const end   = toIsoDate(today)
    let start: string

    switch (preset) {
      case 'thisMonth': {
        start = toIsoDate(new Date(today.getFullYear(), today.getMonth(), 1))
        break
      }
      case 'lastQuarter': {
        const d = new Date(today)
        d.setMonth(d.getMonth() - 3)
        start = toIsoDate(d)
        break
      }
      case 'thisYear':
      default: {
        start = toIsoDate(new Date(today.getFullYear(), 0, 1))
        break
      }
    }

    startDate.value = start
    endDate.value   = end
  }

  function reset(): void {
    const today = new Date()
    startDate.value = toIsoDate(new Date(today.getFullYear(), 0, 1))
    endDate.value   = toIsoDate(today)
  }

  return {
    startDate,
    endDate,
    periodo,
    apiParams,
    formattedRange,
    setRange,
    setPreset,
    setPeriodo,
    reset,
  }
})

// Alias para compatibilidad con código existente que usa useStatsFilter
export { useStatsFilterStore as useStatsFilter }
export type { FilterState }
