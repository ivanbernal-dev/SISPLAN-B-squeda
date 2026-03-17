/// <reference types="vite/client" />

// Definición de variables de entorno tipadas para UBPD
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
