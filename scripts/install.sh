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
command -v openssl  >/dev/null 2>&1 || error "openssl no está instalado."

DOCKER_VERSION=$(docker --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
info "Docker $DOCKER_VERSION detectado."
info "docker compose detectado."
info "openssl detectado."

# ── 2. Crear directorios necesarios ─────────────────────────
step "Creando directorios de logs y datos..."

mkdir -p logs/nginx logs/backend
mkdir -p nginx/certs
mkdir -p postgres/init
mkdir -p backups

info "Directorios creados: logs/nginx, logs/backend, nginx/certs, postgres/init, backups"

# ── 3. Configurar .env ───────────────────────────────────────
step "Configurando variables de entorno..."

if [ -f ".env" ]; then
    warn ".env ya existe — no se sobreescribe. Revisa que esté actualizado con .env.example"
else
    cp .env.example .env
    info ".env creado desde .env.example"
    warn "IMPORTANTE: Edita .env antes de arrancar — especialmente SECRET_KEY y las contraseñas."
fi

# ── 4. Generar certificado SSL ───────────────────────────────
step "Configurando certificado SSL..."

if [ -f "nginx/certs/server.crt" ] && [ -f "nginx/certs/server.key" ]; then
    warn "Certificado SSL ya existe en nginx/certs/ — no se regenera."
    warn "Para regenerar: ./scripts/generate-ssl.sh <IP_SERVIDOR>"
else
    # Obtener SERVER_IP del .env
    SERVER_IP=$(grep -E "^SERVER_IP=" .env 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'")
    SERVER_IP="${SERVER_IP:-192.168.1.100}"

    info "Generando certificado autofirmado para IP: $SERVER_IP"
    chmod +x scripts/generate-ssl.sh
    ./scripts/generate-ssl.sh "$SERVER_IP"
    info "Certificado generado en nginx/certs/"
fi

# ── 5. Resumen ───────────────────────────────────────────────
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
echo "     → App: https://\$(grep SERVER_IP .env | cut -d= -f2)"
echo ""
echo "  Instalar certificado SSL en clientes Windows:"
echo "  → Copiar nginx/certs/server.crt al equipo cliente"
echo "  → Instalar en 'Entidades de certificación raíz de confianza'"
echo ""
