#!/usr/bin/env bash
# ============================================================
# UBPD — Reset de Base de Datos
# ============================================================
# Elimina TODOS los datos y vuelve a crear la BD desde cero.
# Solo funciona si ALLOW_DB_RESET=true en el .env.
#
# Llamado desde: ./scripts/prod.sh reset-db
# ============================================================
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

# ── Verificar que ALLOW_DB_RESET=true en .env ────────────────
if [ ! -f ".env" ]; then
    echo -e "${RED}[ERROR]${NC} No existe .env"
    exit 1
fi

ALLOW=$(grep -E "^ALLOW_DB_RESET=" .env 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'" | tr '[:upper:]' '[:lower:]')

if [ "$ALLOW" != "true" ]; then
    echo ""
    echo -e "${RED}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  Reset bloqueado — ALLOW_DB_RESET no está habilitado ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "  Para habilitar el reset, editar .env:"
    echo ""
    echo "    ALLOW_DB_RESET=true"
    echo ""
    echo "  ADVERTENCIA: esto eliminará TODOS los datos de la base de datos."
    echo "  Volver a false cuando termines."
    echo ""
    exit 1
fi

# ── Confirmación obligatoria ─────────────────────────────────
echo ""
echo -e "${YELLOW}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║       ADVERTENCIA — OPERACIÓN DESTRUCTIVA            ║${NC}"
echo -e "${YELLOW}╠══════════════════════════════════════════════════════╣${NC}"
echo -e "${YELLOW}║  Se ELIMINARÁN todos los datos de la base de datos.  ║${NC}"
echo -e "${YELLOW}║  Esta operación NO se puede deshacer.                ║${NC}"
echo -e "${YELLOW}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -n "  Escribe CONFIRMAR para continuar: "
read -r CONFIRM

if [ "$CONFIRM" != "CONFIRMAR" ]; then
    echo ""
    echo "  Operación cancelada."
    echo ""
    exit 0
fi

echo ""
echo -e "${CYAN}▶  Iniciando reset de base de datos...${NC}"

# ── Leer variables de postgres desde .env ───────────────────
POSTGRES_USER=$(grep -E "^POSTGRES_USER=" .env | cut -d= -f2 | tr -d '"')
POSTGRES_DB=$(grep -E "^POSTGRES_DB=" .env | cut -d= -f2 | tr -d '"')

# ── 1. Detener backend y celery (siguen necesitando BD) ──────
echo "  [1/5] Deteniendo backend y workers..."
docker compose stop backend celery celery-beat 2>/dev/null || true

# ── 2. Eliminar el volumen de postgres ──────────────────────
echo "  [2/5] Eliminando volumen de datos de PostgreSQL..."
docker compose rm -f postgres 2>/dev/null || true
docker volume rm ubpd_postgres_data 2>/dev/null || true

# ── 3. Levantar postgres limpio ──────────────────────────────
echo "  [3/5] Iniciando PostgreSQL limpio..."
docker compose up -d postgres
echo "       Esperando que PostgreSQL esté listo..."
sleep 5
# Esperar hasta que healthcheck pase
for i in $(seq 1 20); do
    if docker compose exec -T postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
        echo "       PostgreSQL listo."
        break
    fi
    sleep 2
done

# ── 4. Aplicar migraciones en la BD nueva ───────────────────
echo "  [4/5] Aplicando migraciones..."
docker compose up -d backend
sleep 5
docker compose exec -T backend alembic upgrade head

# ── 5. Levantar el resto ─────────────────────────────────────
echo "  [5/5] Levantando todos los servicios..."
docker compose up -d

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Base de datos reiniciada correctamente              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  El usuario admin inicial se recreará automáticamente."
echo "  Usuario: $(grep -E '^INITIAL_ADMIN_USERNAME=' .env | cut -d= -f2)"
echo ""
echo -e "${YELLOW}  RECUERDA: volver a poner ALLOW_DB_RESET=false en .env${NC}"
echo ""
