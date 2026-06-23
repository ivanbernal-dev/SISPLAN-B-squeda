export interface Periodo {
  key: string
  label: string
}

export interface VariableMes {
  numero: number
  nombre: string
  valor_mes: string | number | null
  valor_acumulado: string | number | null
  acumulado_calculado: boolean
}

export interface ReporteMes {
  label: string
  resultado: string | number | null
  resultado_acumulado?: string | number | null
  display: string
  avance: number | null
  tipo: string
  analisis: string
  logros: string
  observaciones: string
  observacionOap: string
  estadoOap?: string
  variables: VariableMes[]
  fuente?: string
  formulario_id?: string
  fecha_validacion?: string | null
  validado_por?: string | null
}

export interface IndicadorComite {
  uid: string
  vigencia: number
  no: string
  linea: string
  resultado: string
  producto: string
  dependencia: string
  responsables: string
  codigo: string
  nombre: string
  objetivo: string
  definicion: string
  formula: string
  periodicidad: string
  unidad: string
  fuente: string
  lineaBase: string
  metaAnual: string
  estado: string
  meses: Record<string, ReporteMes>
}

export interface ResumenComite {
  total: number
  activos: number
  inactivos: number
  avance_promedio: number
  observaciones_oap: number
}

export interface FiltrosComite {
  lineas: string[]
  dependencias: string[]
  estados: string[]
}

export interface RespuestaComite {
  vigencia: number
  periodos: Periodo[]
  filtros: FiltrosComite
  resumen: ResumenComite
  items: IndicadorComite[]
}
