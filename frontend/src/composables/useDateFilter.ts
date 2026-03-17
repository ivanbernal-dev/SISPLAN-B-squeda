// ============================================================
// UBPD — Composable useDateFilter
// Expone el store de fechas y prepara los parámetros para la API
// ============================================================

import { computed } from 'vue'
import { useStatsFilterStore, type DatePreset } from '../stores/statsFilter'

export interface DateApiParams {
  start_date: string
  end_date:   string
}

export function useDateFilter() {
  const store = useStatsFilterStore()

  /** Parámetros listos para incluir en las llamadas a la API */
  const dateParams = computed<DateApiParams>(() => ({
    start_date: store.startDate,
    end_date:   store.endDate,
  }))

  /** Texto legible del rango activo, p.ej. "01 ene. 2025 — 17 mar. 2026" */
  const formattedRange = computed(() => store.formattedRange)

  function setRange(start: string, end: string): void {
    store.setRange(start, end)
  }

  function setPreset(preset: DatePreset): void {
    store.setPreset(preset)
  }

  function reset(): void {
    store.reset()
  }

  return {
    startDate: computed(() => store.startDate),
    endDate:   computed(() => store.endDate),
    dateParams,
    formattedRange,
    setRange,
    setPreset,
    reset,
  }
}
