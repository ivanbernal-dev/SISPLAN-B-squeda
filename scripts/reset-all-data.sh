#!/usr/bin/env bash
# ============================================================
# UBPD — Borrar TODOS los datos de todas las tablas
#
# Elimina registros de todas las tablas (formularios, archivos,
# templates, usuarios, dependencias, logs, indicadores, etc.)
# y limpia todos los archivos almacenados en MinIO.
#
# Los contenedores deben estar corriendo.
# El admin inicial se recreará automáticamente al reiniciar el backend.
#
# Uso: ./scripts/reset-all-data.sh
# ============================================================
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# ── Colores ──────────────────────────────────────────────────
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ── Cargar variables del .env ────────────────────────────────
if [ ! -f ".env" ]; then
  echo -e "${RED}✗ No se encontró el archivo .env en: $ROOT_DIR${NC}"
  exit 1
fi
set -o allexport
source .env
set +o allexport

# ── Confirmación doble ───────────────────────────────────────
echo ""
echo -e "${RED}${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}${BOLD}║   ⚠  ADVERTENCIA — OPERACIÓN DESTRUCTIVA TOTAL      ║${NC}"
echo -e "${RED}${BOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}  Esto eliminará TODOS los datos de la base de datos:${NC}"
echo "    · Formularios y archivos adjuntos"
echo "    · Templates y configuraciones"
echo "    · Usuarios (todos, incluyendo admins)"
echo "    · Dependencias, indicadores, audit logs"
echo "    · Archivos físicos en MinIO"
echo ""
echo -e "${YELLOW}  El admin inicial se recreará al reiniciar el backend.${NC}"
echo ""
read -r -p "  Escribe CONFIRMAR para continuar: " CONFIRM
if [ "$CONFIRM" != "CONFIRMAR" ]; then
  echo -e "${CYAN}  Operación cancelada.${NC}"
  exit 0
fi

echo ""
read -r -p "  ¿Seguro? Escribe BORRAR TODO para ejecutar: " CONFIRM2
if [ "$CONFIRM2" != "BORRAR TODO" ]; then
  echo -e "${CYAN}  Operación cancelada.${NC}"
  exit 0
fi

echo ""
echo -e "${CYAN}► Limpiando base de datos...${NC}"

# ── SQL: TRUNCATE en orden correcto con CASCADE ──────────────
docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  <<'SQL'
-- Deshabilitar temporalmente los checks de FK para mayor velocidad
SET session_replication_role = replica;

TRUNCATE TABLE
  archivos,
  formularios_respondidos,
  fact_stats,
  pipeline_ejecuciones,
  pipeline_runs,
  audit_logs,
  templates,
  pipeline_definiciones,
  indicadores_nivel2,
  indicadores_nivel1,
  usuarios,
  dependencias
RESTART IDENTITY CASCADE;

-- Restaurar checks de FK
SET session_replication_role = DEFAULT;
SQL

echo -e "${GREEN}  ✓ Tablas limpiadas${NC}"

# ── Limpiar archivos en MinIO ─────────────────────────────────
echo -e "${CYAN}► Limpiando archivos en MinIO...${NC}"

# Usar mc (MinIO Client) dentro del contenedor minio para borrar el bucket
# y recrearlo vacío
docker compose exec -T minio sh -c "
  mc alias set local http://localhost:9000 '${MINIO_ROOT_USER}' '${MINIO_ROOT_PASSWORD}' --quiet 2>/dev/null || true
  mc rm --recursive --force local/'${MINIO_BUCKET_NAME}' 2>/dev/null || true
  mc mb --ignore-existing local/'${MINIO_BUCKET_NAME}' 2>/dev/null || true
  echo 'MinIO limpiado'
" 2>/dev/null && echo -e "${GREEN}  ✓ Archivos MinIO eliminados${NC}" \
             || echo -e "${YELLOW}  ⚠ No se pudo limpiar MinIO (continúa sin error)${NC}"

echo ""
echo -e "${GREEN}${BOLD}✓ Reseteo completo finalizado.${NC}"
echo -e "  Reinicia el backend para recrear el admin inicial:"
echo -e "  ${CYAN}./scripts/prod.sh restart backend${NC}"
echo ""
