-- ============================================================
-- UBPD — Extensiones PostgreSQL requeridas
-- Este script se ejecuta automáticamente al crear el contenedor
-- ============================================================

-- Soporte para UUID nativo (gen_random_uuid())
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Para búsqueda de texto completo en español (informe cualitativo)
CREATE EXTENSION IF NOT EXISTS "unaccent";
