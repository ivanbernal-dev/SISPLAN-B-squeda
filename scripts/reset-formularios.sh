#!/usr/bin/env bash
# ============================================================
# UBPD — Borrar todos los formularios y archivos adjuntos
#
# Elimina todos los datos generados por el llenado de formularios:
#   · Formularios respondidos (todos los estados)
#   · Archivos adjuntos de esos formularios
#   · Estadísticas calculadas (fact_stats)
#   · Archivos físicos en MinIO
#
# Conserva: templates, usuarios, dependencias, indicadores,
#           pipelines, audit logs.
#
# Uso: ./scripts/reset-formularios.sh
#      ./scripts/reset-formularios.sh --template-id <uuid>   (solo un template)
#      ./scripts/reset-formularios.sh --estado draft         (solo un estado)
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

# ── Argumentos ───────────────────────────────────────────────
TEMPLATE_ID=""
ESTADO=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --template-id)
      TEMPLATE_ID="$2"
      shift 2
      ;;
    --estado)
      ESTADO="$2"
      shift 2
      ;;
    *)
      echo -e "${RED}✗ Argumento desconocido: $1${NC}"
      echo "  Uso: $0 [--template-id <uuid>] [--estado draft|pending|approved|rejected]"
      exit 1
      ;;
  esac
done

# Validar estado si se pasó
if [ -n "$ESTADO" ]; then
  case "$ESTADO" in
    draft|pending|approved|rejected) ;;
    *)
      echo -e "${RED}✗ Estado inválido: '$ESTADO'${NC}"
      echo "  Estados válidos: draft, pending, approved, rejected"
      exit 1
      ;;
  esac
fi

# ── Cargar variables del .env ────────────────────────────────
if [ ! -f ".env" ]; then
  echo -e "${RED}✗ No se encontró el archivo .env en: $ROOT_DIR${NC}"
  exit 1
fi
set -o allexport
source .env
set +o allexport

# ── Construir filtro SQL ──────────────────────────────────────
WHERE_CLAUSE="1=1"
SCOPE_DESC="todos los formularios"

if [ -n "$TEMPLATE_ID" ]; then
  WHERE_CLAUSE="${WHERE_CLAUSE} AND plantilla_id = '${TEMPLATE_ID}'"
  TEMPLATE_NAME=$(docker compose exec -T postgres psql \
    -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At \
    -c "SELECT nombre FROM templates WHERE id = '${TEMPLATE_ID}';" 2>/dev/null || echo "?")
  SCOPE_DESC="formularios del template '${TEMPLATE_NAME}'"
fi

if [ -n "$ESTADO" ]; then
  WHERE_CLAUSE="${WHERE_CLAUSE} AND estado = '${ESTADO}'"
  SCOPE_DESC="${SCOPE_DESC} en estado '${ESTADO}'"
fi

# ── Consultar estado actual ───────────────────────────────────
echo ""

FORM_TOTAL=$(docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At \
  -c "SELECT COUNT(*) FROM formularios_respondidos WHERE ${WHERE_CLAUSE};" \
  2>/dev/null || echo "?")

FILES_TOTAL=$(docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At \
  -c "SELECT COUNT(*) FROM archivos
      WHERE formulario_id IN (
        SELECT id FROM formularios_respondidos WHERE ${WHERE_CLAUSE}
      );" 2>/dev/null || echo "?")

# Desglose por estado
DRAFT_COUNT=$(docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At \
  -c "SELECT COUNT(*) FROM formularios_respondidos
      WHERE ${WHERE_CLAUSE} AND estado = 'draft';" 2>/dev/null || echo "0")

PENDING_COUNT=$(docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At \
  -c "SELECT COUNT(*) FROM formularios_respondidos
      WHERE ${WHERE_CLAUSE} AND estado = 'pending';" 2>/dev/null || echo "0")

APPROVED_COUNT=$(docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At \
  -c "SELECT COUNT(*) FROM formularios_respondidos
      WHERE ${WHERE_CLAUSE} AND estado = 'approved';" 2>/dev/null || echo "0")

REJECTED_COUNT=$(docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At \
  -c "SELECT COUNT(*) FROM formularios_respondidos
      WHERE ${WHERE_CLAUSE} AND estado = 'rejected';" 2>/dev/null || echo "0")

echo -e "${YELLOW}${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}${BOLD}║   ⚠  ADVERTENCIA — Borrar Formularios               ║${NC}"
echo -e "${YELLOW}${BOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Alcance: ${BOLD}${SCOPE_DESC}${NC}"
echo ""
echo -e "  Formularios a eliminar: ${BOLD}${FORM_TOTAL}${NC}"
echo "    · Borradores:   ${DRAFT_COUNT}"
echo "    · Pendientes:   ${PENDING_COUNT}"
echo "    · Aprobados:    ${APPROVED_COUNT}"
echo "    · Rechazados:   ${REJECTED_COUNT}"
echo -e "  Archivos adjuntos:      ${BOLD}${FILES_TOTAL}${NC}"
echo ""
echo -e "${GREEN}  Se conservará:${NC}"
echo "    · Templates y su configuración"
echo "    · Usuarios y dependencias"
echo "    · Indicadores y pipelines"
echo "    · Audit logs"
echo ""

if [ "$FORM_TOTAL" = "0" ]; then
  echo -e "${CYAN}  No hay formularios que coincidan con el filtro. Nada que hacer.${NC}"
  echo ""
  exit 0
fi

read -r -p "  Escribe CONFIRMAR para continuar: " CONFIRM
if [ "$CONFIRM" != "CONFIRMAR" ]; then
  echo -e "${CYAN}  Operación cancelada.${NC}"
  exit 0
fi

echo ""
echo -e "${CYAN}► Obteniendo rutas de archivos en MinIO antes de borrar...${NC}"

MINIO_PATHS=$(docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At \
  -c "SELECT ruta_minio FROM archivos
      WHERE formulario_id IN (
        SELECT id FROM formularios_respondidos WHERE ${WHERE_CLAUSE}
      );" 2>/dev/null || echo "")

echo -e "${CYAN}► Eliminando formularios y archivos...${NC}"

docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  <<SQL
-- 1. Borrar estadísticas vinculadas
DELETE FROM fact_stats
  WHERE form_id IN (
    SELECT id FROM formularios_respondidos WHERE ${WHERE_CLAUSE}
  );

-- 2. Borrar archivos adjuntos
DELETE FROM archivos
  WHERE formulario_id IN (
    SELECT id FROM formularios_respondidos WHERE ${WHERE_CLAUSE}
  );

-- 3. Borrar los formularios
DELETE FROM formularios_respondidos WHERE ${WHERE_CLAUSE};
SQL

echo -e "${GREEN}  ✓ Formularios y archivos eliminados${NC}"

# ── Limpiar archivos físicos en MinIO ─────────────────────────
if [ -n "$MINIO_PATHS" ]; then
  echo -e "${CYAN}► Eliminando archivos físicos en MinIO...${NC}"

  docker compose exec -T minio sh -c "
    mc alias set local http://localhost:9000 '${MINIO_ROOT_USER}' '${MINIO_ROOT_PASSWORD}' --quiet 2>/dev/null || true
  " 2>/dev/null || true

  DELETED=0
  while IFS= read -r RUTA; do
    [ -z "$RUTA" ] && continue
    docker compose exec -T minio sh -c "
      mc rm 'local/${MINIO_BUCKET_NAME}/${RUTA}' --quiet 2>/dev/null || true
    " 2>/dev/null || true
    DELETED=$((DELETED + 1))
  done <<< "$MINIO_PATHS"

  echo -e "${GREEN}  ✓ ${DELETED} archivo(s) físico(s) eliminados de MinIO${NC}"
else
  echo -e "${CYAN}  (No había archivos físicos en MinIO asociados)${NC}"
fi

# ── Resumen final ─────────────────────────────────────────────
echo ""
REMAINING=$(docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At \
  -c "SELECT COUNT(*) FROM formularios_respondidos;" 2>/dev/null || echo "?")

TEMPLATES_OK=$(docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At \
  -c "SELECT COUNT(*) FROM templates;" 2>/dev/null || echo "?")

echo -e "${GREEN}${BOLD}✓ Operación completada.${NC}"
echo -e "  Formularios restantes en el sistema: ${BOLD}${REMAINING}${NC}"
echo -e "  Templates intactos:                  ${BOLD}${TEMPLATES_OK}${NC}"
echo ""
