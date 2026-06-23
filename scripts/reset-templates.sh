#!/usr/bin/env bash
# ============================================================
# UBPD — Borrar todos los Templates
#
# Elimina todos los templates y en cascada:
#   · Formularios respondidos vinculados
#   · Archivos adjuntos de esos formularios
#   · Estadísticas (fact_stats) de esos templates
#   · Archivos físicos en MinIO de los formularios eliminados
#
# Conserva: usuarios, dependencias, indicadores, logs.
#
# Uso: ./scripts/reset-templates.sh
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

# ── Mostrar cuántos templates hay antes de borrar ────────────
echo ""
TEMPLATE_COUNT=$(docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At \
  -c "SELECT COUNT(*) FROM templates;" 2>/dev/null || echo "?")

FORM_COUNT=$(docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At \
  -c "SELECT COUNT(*) FROM formularios_respondidos;" 2>/dev/null || echo "?")

echo -e "${YELLOW}${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}${BOLD}║   ⚠  ADVERTENCIA — Borrar Templates                 ║${NC}"
echo -e "${YELLOW}${BOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Estado actual:"
echo -e "    · Templates:    ${BOLD}${TEMPLATE_COUNT}${NC}"
echo -e "    · Formularios:  ${BOLD}${FORM_COUNT}${NC} (se eliminarán también)"
echo ""
echo -e "${YELLOW}  Se eliminará en cascada:${NC}"
echo "    · Todos los templates"
echo "    · Todos los formularios respondidos"
echo "    · Todos los archivos adjuntos"
echo "    · Todas las estadísticas fact_stats"
echo "    · Archivos físicos en MinIO"
echo ""
echo -e "${GREEN}  Se conservará:${NC}"
echo "    · Usuarios y dependencias"
echo "    · Indicadores de nivel 1 y 2"
echo "    · Definiciones de pipelines"
echo "    · Audit logs"
echo ""
read -r -p "  Escribe CONFIRMAR para continuar: " CONFIRM
if [ "$CONFIRM" != "CONFIRMAR" ]; then
  echo -e "${CYAN}  Operación cancelada.${NC}"
  exit 0
fi

echo ""
echo -e "${CYAN}► Obteniendo rutas de archivos en MinIO antes de borrar...${NC}"

# Obtener las rutas de MinIO de los archivos vinculados a templates
MINIO_PATHS=$(docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At \
  -c "SELECT ruta_minio FROM archivos WHERE formulario_id IN (
        SELECT id FROM formularios_respondidos WHERE plantilla_id IN (
          SELECT id FROM templates
        )
      );" 2>/dev/null || echo "")

echo -e "${CYAN}► Eliminando templates y datos en cascada...${NC}"

docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  <<'SQL'
-- Borrar en orden de dependencias (CASCADE se encarga del resto)
DELETE FROM fact_stats
  WHERE template_id IN (SELECT id FROM templates);

DELETE FROM archivos
  WHERE formulario_id IN (
    SELECT id FROM formularios_respondidos
    WHERE plantilla_id IN (SELECT id FROM templates)
  );

DELETE FROM formularios_respondidos
  WHERE plantilla_id IN (SELECT id FROM templates);

DELETE FROM templates;
SQL

echo -e "${GREEN}  ✓ Templates y datos relacionados eliminados${NC}"

# ── Limpiar archivos físicos en MinIO ────────────────────────
if [ -n "$MINIO_PATHS" ]; then
  echo -e "${CYAN}► Eliminando archivos físicos en MinIO...${NC}"

  # Configurar alias mc y borrar cada objeto
  docker compose exec -T minio sh -c "
    mc alias set local http://localhost:9000 '${MINIO_ROOT_USER}' '${MINIO_ROOT_PASSWORD}' --quiet 2>/dev/null || true
  " 2>/dev/null || true

  while IFS= read -r RUTA; do
    [ -z "$RUTA" ] && continue
    docker compose exec -T minio sh -c "
      mc rm 'local/${MINIO_BUCKET_NAME}/${RUTA}' --quiet 2>/dev/null || true
    " 2>/dev/null || true
  done <<< "$MINIO_PATHS"

  echo -e "${GREEN}  ✓ Archivos físicos eliminados de MinIO${NC}"
else
  echo -e "${CYAN}  (No había archivos físicos en MinIO asociados)${NC}"
fi

# ── Resumen final ────────────────────────────────────────────
echo ""
NEW_TEMPLATE_COUNT=$(docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At \
  -c "SELECT COUNT(*) FROM templates;" 2>/dev/null || echo "?")

echo -e "${GREEN}${BOLD}✓ Operación completada.${NC}"
echo -e "  Templates restantes: ${BOLD}${NEW_TEMPLATE_COUNT}${NC}"
echo ""
