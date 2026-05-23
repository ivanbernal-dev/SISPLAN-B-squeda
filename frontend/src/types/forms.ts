// ============================================================
// UBPD Frontend — Tipos compartidos para formularios
// ============================================================

export interface FieldConfig {
  name: string
  label: string
  type: 'text' | 'number' | 'date' | 'textarea' | 'select' | 'archivos' | 'computed'
  readonly: boolean
  default: string | number | null
  required?: boolean
  options?: { value: string; label: string }[]
  formula?: string
  /** Si true, sólo lo edita el validador al aprobar (no lo ve la dependencia). */
  validator_only?: boolean
  /** Fórmula de cálculo automático aplicada en frontend y backend.
   *  Valores soportados:
   *    'ratio_alcanzado_proyectado'           → pct_alcanzado / pct_proyectado
   *    'estado_cumplimiento_from_pct_final'   → Cumple/Parcial/No Cumple/No Aplica */
  auto_calculate?: string
}

export interface FormSchema {
  fields: FieldConfig[]
}

export interface FileRecord {
  id: string
  nombre: string
  tamanio: number
  tipo: string
  url?: string
  created_at?: string
}

export type FormStatus = 'draft' | 'pending' | 'rejected' | 'approved'

export interface FormData {
  id: string
  template_id: string
  template_nombre: string
  estado: FormStatus
  fecha_carga: string | null
  fecha_ultima_edicion: string | null
  fecha_referencia: string
  datos_dinamicos: Record<string, unknown>
  informe_cualitativo: string
  comentario_rechazo: string | null
  archivos: FileRecord[]
  dependencia_nombre?: string
}

export const ESTADO_LABELS: Record<FormStatus, string> = {
  draft: 'Borrador',
  pending: 'Enviado para revisión',
  rejected: 'Requiere corrección',
  approved: 'Registro validado',
}

export const ESTADO_COLORS: Record<FormStatus, string> = {
  draft: '#E0E0E0',
  pending: '#3E818F',
  rejected: '#FF6900',
  approved: '#52ABAB',
}
