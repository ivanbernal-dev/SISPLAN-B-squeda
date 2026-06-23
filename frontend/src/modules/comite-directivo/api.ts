import { apiGet } from '@/composables/useApi'
import type { RespuestaComite } from './types'

export function obtenerIndicadoresComite(vigencia = 2026): Promise<RespuestaComite> {
  return apiGet<RespuestaComite>('/comite-directivo/indicadores', {
    params: { vigencia },
  })
}
