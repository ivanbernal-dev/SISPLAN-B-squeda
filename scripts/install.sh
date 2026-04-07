#!/usr/bin/env bash
# ============================================================
# UBPD — Script de Instalación Inicial
# Ejecutar UNA sola vez antes del primer arranque.
# ============================================================
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }
step()    { echo -e "\n${YELLOW}▶  $*${NC}"; }

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║          UBPD — Instalación Inicial                  ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── 1. Verificar dependencias ────────────────────────────────
step "Verificando dependencias..."

command -v docker   >/dev/null 2>&1 || error "Docker no está instalado."
docker compose version >/dev/null 2>&1 || error "Plugin 'docker compose' no está disponible."

DOCKER_VERSION=$(docker --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
info "Docker $DOCKER_VERSION detectado."
info "docker compose detectado."

# ── 2. Crear directorios necesarios ─────────────────────────
step "Creando directorios de logs y datos..."

mkdir -p logs/nginx logs/backend
mkdir -p postgres/init
mkdir -p backups

info "Directorios creados: logs/nginx, logs/backend, postgres/init, backups"

# ── 3. Configurar .env ───────────────────────────────────────
step "Configurando variables de entorno..."

if [ -f ".env" ]; then
    warn ".env ya existe — no se sobreescribe. Revisa que esté actualizado con .env.example"
else
    cp .env.example .env
    info ".env creado desde .env.example"
    warn "IMPORTANTE: Edita .env antes de arrancar — especialmente SECRET_KEY y las contraseñas."
fi

# ── 4. Resumen ───────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║          Instalación completada                      ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "  Próximos pasos:"
echo ""
echo "  1. Editar .env con tus valores reales:"
echo "     nano .env"
echo "     (cambiar obligatoriamente: SERVER_IP, SECRET_KEY, contraseñas)"
echo ""
echo "  2. Construir y arrancar:"
echo "     ./scripts/prod.sh build"
echo "     ./scripts/prod.sh start"
echo ""
echo "  3. Verificar estado:"
echo "     ./scripts/prod.sh status"
echo "     → App: http://\$(grep SERVER_IP .env | cut -d= -f2)"
echo ""
