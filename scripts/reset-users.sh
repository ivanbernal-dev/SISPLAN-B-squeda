#!/usr/bin/env bash
# ============================================================
# UBPD — Borrar usuarios (conserva administradores)
#
# Elimina todos los usuarios con rol:
#   · validator
#   · dependency_user
#
# Conserva todos los usuarios con rol 'admin'.
#
# En cascada se eliminan también:
#   · Formularios respondidos de esos usuarios
#   · Archivos adjuntos de esos formularios
#   · Audit logs generados por esos usuarios
#   · Archivos físicos en MinIO de sus formularios
#
# Uso: ./scripts/reset-users.sh
#      ./scripts/reset-users.sh --solo-validadores   (solo borra validadores)
#      ./scripts/reset-users.sh --solo-dependencias  (solo borra dep. users)
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
MODO="${1:-}"

case "$MODO" in
  --solo-validadores)
    ROLES_SQL="role = 'validator'"
    ROLES_DESC="validadores"
    ;;
  --solo-dependencias)
    ROLES_SQL="role = 'dependency_user'"
    ROLES_DESC="usuarios de dependencia"
    ;;
  *)
    ROLES_SQL="role IN ('validator', 'dependency_user')"
    ROLES_DESC="validadores y usuarios de dependencia"
    ;;
esac

# ── Cargar variables del .env ────────────────────────────────
if [ ! -f ".env" ]; then
  echo -e "${RED}✗ No se encontró el archivo .env en: $ROOT_DIR${NC}"
  exit 1
fi
set -o allexport
source .env
set +o allexport

# ── Mostrar estado actual ────────────────────────────────────
echo ""

ADMIN_COUNT=$(docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At \
  -c "SELECT COUNT(*) FROM usuarios WHERE role = 'admin';" 2>/dev/null || echo "?")

VALIDATOR_COUNT=$(docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At \
  -c "SELECT COUNT(*) FROM usuarios WHERE role = 'validator';" 2>/dev/null || echo "?")

DEPUSER_COUNT=$(docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At \
  -c "SELECT COUNT(*) FROM usuarios WHERE role = 'dependency_user';" 2>/dev/null || echo "?")

AFFECTED_COUNT=$(docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At \
  -c "SELECT COUNT(*) FROM usuarios WHERE ${ROLES_SQL};" 2>/dev/null || echo "?")

FORMS_AFFECTED=$(docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At \
  -c "SELECT COUNT(*) FROM formularios_respondidos
      WHERE usuario_id IN (SELECT id FROM usuarios WHERE ${ROLES_SQL});" \
  2>/dev/null || echo "?")

echo -e "${YELLOW}${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}${BOLD}║   ⚠  ADVERTENCIA — Borrar usuarios                  ║${NC}"
echo -e "${YELLOW}${BOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Estado actual:"
echo -e "    · Admins:             ${BOLD}${ADMIN_COUNT}${NC} ${GREEN}(se conservan)${NC}"
echo -e "    · Validadores:        ${BOLD}${VALIDATOR_COUNT}${NC}"
echo -e "    · Usuarios dependencia: ${BOLD}${DEPUSER_COUNT}${NC}"
echo ""
echo -e "  Modo seleccionado: ${BOLD}${ROLES_DESC}${NC}"
echo -e "  Usuarios a eliminar: ${BOLD}${AFFECTED_COUNT}${NC}"
echo -e "  Formularios afectados: ${BOLD}${FORMS_AFFECTED}${NC} (se eliminarán en cascada)"
echo ""
echo -e "${GREEN}  Se conservará:${NC}"
echo "    · Todos los administradores"
echo "    · Templates e indicadores"
echo "    · Dependencias"
echo ""
echo -e "${YELLOW}  Modos disponibles:${NC}"
echo "    Sin argumento           → borra validadores + dep. users"
echo "    --solo-validadores      → borra solo validadores"
echo "    --solo-dependencias     → borra solo usuarios de dependencia"
echo ""
read -r -p "  Escribe CONFIRMAR para continuar: " CONFIRM
if [ "$CONFIRM" != "CONFIRMAR" ]; then
  echo -e "${CYAN}  Operación cancelada.${NC}"
  exit 0
fi

echo ""
echo -e "${CYAN}► Obteniendo rutas de archivos en MinIO antes de borrar...${NC}"

# Obtener rutas MinIO de archivos de formularios de estos usuarios
MINIO_PATHS=$(docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At \
  -c "SELECT ruta_minio FROM archivos
      WHERE formulario_id IN (
        SELECT id FROM formularios_respondidos
        WHERE usuario_id IN (SELECT id FROM usuarios WHERE ${ROLES_SQL})
      );" 2>/dev/null || echo "")

echo -e "${CYAN}► Eliminando usuarios y datos en cascada...${NC}"

# Ejecutar el SQL usando variable de shell
docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  -v roles_filter="${ROLES_SQL}" \
  <<SQL
-- 1. Borrar archivos físicos referenciados
DELETE FROM archivos
  WHERE formulario_id IN (
    SELECT id FROM formularios_respondidos
    WHERE usuario_id IN (SELECT id FROM usuarios WHERE ${ROLES_SQL})
  );

-- 2. Borrar formularios
DELETE FROM formularios_respondidos
  WHERE usuario_id IN (SELECT id FROM usuarios WHERE ${ROLES_SQL});

-- 3. Borrar audit logs de estos usuarios
DELETE FROM audit_logs
  WHERE usuario_id IN (SELECT id FROM usuarios WHERE ${ROLES_SQL});

-- 4. Borrar los usuarios
DELETE FROM usuarios WHERE ${ROLES_SQL};
SQL

echo -e "${GREEN}  ✓ Usuarios y datos relacionados eliminados${NC}"

# ── Limpiar archivos físicos en MinIO ────────────────────────
if [ -n "$MINIO_PATHS" ]; then
  echo -e "${CYAN}► Eliminando archivos físicos en MinIO...${NC}"

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
REMAINING=$(docker compose exec -T postgres psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At \
  -c "SELECT role, COUNT(*) FROM usuarios GROUP BY role ORDER BY role;" \
  2>/dev/null || echo "?")

echo -e "${GREEN}${BOLD}✓ Operación completada.${NC}"
echo -e "  Usuarios restantes por rol:"
while IFS='|' read -r ROL CANT; do
  [ -z "$ROL" ] && continue
  echo -e "    · ${ROL}: ${BOLD}${CANT}${NC}"
done <<< "$REMAINING"
echo ""
