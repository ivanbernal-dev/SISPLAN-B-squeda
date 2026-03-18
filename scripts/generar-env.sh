#!/usr/bin/env bash
# ============================================================
# UBPD — Generador de configuración para .env
# ============================================================
# Detecta la IP local, genera claves y contraseñas seguras,
# y opcionalmente las escribe directamente en el .env.
#
# Uso:
#   ./scripts/generar-env.sh           → muestra valores, pregunta si escribe
#   ./scripts/generar-env.sh --write   → escribe en .env sin preguntar
#   ./scripts/generar-env.sh --show    → solo muestra, nunca escribe
# ============================================================
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

MODE="${1:-ask}"   # ask | --write | --show

# ── Utilidades de generación ─────────────────────────────────

gen_secret_key() {
    python3 -c "import secrets; print(secrets.token_hex(64))" 2>/dev/null || \
    openssl rand -hex 64
}

gen_password() {
    local length="${1:-20}"
    # Letras + dígitos + caracteres seguros para contraseñas (evita comillas y $)
    python3 -c "
import secrets, string
chars = string.ascii_letters + string.digits + '@#%!_'
# Asegurar al menos 1 mayúscula, 1 minúscula, 1 número, 1 especial
pwd = [
    secrets.choice(string.ascii_uppercase),
    secrets.choice(string.ascii_lowercase),
    secrets.choice(string.digits),
    secrets.choice('@#%!_'),
]
pwd += [secrets.choice(chars) for _ in range($length - 4)]
secrets.SystemRandom().shuffle(pwd)
print(''.join(pwd))
" 2>/dev/null || openssl rand -base64 "$length" | tr -d '=/+\n' | head -c "$length"
}

# ── Detectar IP local ─────────────────────────────────────────

detect_local_ip() {
    local ip=""

    # Linux: ip route
    ip=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' | head -1)

    # Linux fallback: hostname -I
    if [ -z "$ip" ]; then
        ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    fi

    # macOS: route get
    if [ -z "$ip" ]; then
        local iface
        iface=$(route get default 2>/dev/null | grep interface | awk '{print $2}')
        if [ -n "$iface" ]; then
            ip=$(ipconfig getifaddr "$iface" 2>/dev/null)
        fi
    fi

    # macOS fallback: ifconfig
    if [ -z "$ip" ]; then
        ip=$(ifconfig 2>/dev/null | grep "inet " | grep -v "127.0.0.1" | awk '{print $2}' | head -1)
    fi

    # Último recurso
    if [ -z "$ip" ]; then
        ip="127.0.0.1"
        echo -e "${YELLOW}[WARN]${NC} No se detectó IP de red — usando 127.0.0.1 (cambia SERVER_IP manualmente si el servidor está en otra IP)" >&2
    fi

    echo "$ip"
}

# ── Generar todos los valores ─────────────────────────────────

echo ""
echo -e "${CYAN}${BOLD}Detectando configuración...${NC}"
echo ""

SERVER_IP=$(detect_local_ip)
SECRET_KEY=$(gen_secret_key)
POSTGRES_PASSWORD=$(gen_password 22)
REDIS_PASSWORD=$(gen_password 20)
MINIO_ROOT_PASSWORD=$(gen_password 18)

# ── Mostrar resultado ─────────────────────────────────────────

echo -e "${BOLD}┌─────────────────────────────────────────────────────────┐${NC}"
echo -e "${BOLD}│         Valores generados para .env                     │${NC}"
echo -e "${BOLD}└─────────────────────────────────────────────────────────┘${NC}"
echo ""
echo -e "${CYAN}# IP detectada en esta máquina:${NC}"
echo -e "  ${GREEN}SERVER_IP${NC}=${YELLOW}${SERVER_IP}${NC}"
echo ""
echo -e "${CYAN}# Clave secreta JWT (64 bytes hex):${NC}"
echo -e "  ${GREEN}SECRET_KEY${NC}=${YELLOW}${SECRET_KEY}${NC}"
echo ""
echo -e "${CYAN}# Contraseñas de servicios:${NC}"
echo -e "  ${GREEN}POSTGRES_PASSWORD${NC}=${YELLOW}${POSTGRES_PASSWORD}${NC}"
echo -e "  ${GREEN}REDIS_PASSWORD${NC}=${YELLOW}${REDIS_PASSWORD}${NC}"
echo -e "  ${GREEN}MINIO_ROOT_PASSWORD${NC}=${YELLOW}${MINIO_ROOT_PASSWORD}${NC}"
echo ""
echo -e "${YELLOW}  ─── Fijan manualmente en .env ────────────────────${NC}"
echo -e "  ${GREEN}INITIAL_ADMIN_PASSWORD${NC}=  (elige una contraseña segura)"
echo -e "  ${GREEN}INITIAL_ADMIN_EMAIL${NC}=     (email real del administrador)"
echo ""

# ── Decidir si escribir ───────────────────────────────────────

WRITE=false

if [ "$MODE" = "--write" ]; then
    WRITE=true
elif [ "$MODE" = "--show" ]; then
    WRITE=false
else
    # Modo interactivo
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}No existe .env — se creará desde .env.example${NC}"
    fi
    echo -n "¿Escribir estos valores en .env? [s/N]: "
    read -r RESP
    [[ "$RESP" =~ ^[sS]$ ]] && WRITE=true
fi

if [ "$WRITE" = false ]; then
    echo ""
    echo "  Valores no escritos. Copia los que necesites manualmente."
    echo "  O ejecuta: ./scripts/generar-env.sh --write"
    echo ""
    exit 0
fi

# ── Escribir en .env ──────────────────────────────────────────

# Crear .env desde .env.example si no existe
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}[OK]${NC} .env creado desde .env.example"
fi

# Reemplazar valores usando Python para mayor fiabilidad
python3 << PYEOF
import re

with open(".env", "r", encoding="utf-8") as f:
    content = f.read()

replacements = {
    "SERVER_IP":           "${SERVER_IP}",
    "SECRET_KEY":          "${SECRET_KEY}",
    "POSTGRES_PASSWORD":   "${POSTGRES_PASSWORD}",
    "REDIS_PASSWORD":      "${REDIS_PASSWORD}",
    "MINIO_ROOT_PASSWORD": "${MINIO_ROOT_PASSWORD}",
}

for key, value in replacements.items():
    # Reemplaza KEY=<cualquier cosa> por KEY=nuevo_valor
    pattern = rf'^({re.escape(key)}=).*$'
    replacement = rf'\g<1>{re.escape(value)}'
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    if new_content != content:
        content = new_content
    else:
        # La clave no existe aún, agregarla al final
        content += f"\n{key}={value}"

with open(".env", "w", encoding="utf-8") as f:
    f.write(content)

print("OK")
PYEOF

echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║  .env actualizado correctamente                      ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  Valores escritos:"
echo -e "  ${GREEN}✓${NC} SERVER_IP, SECRET_KEY"
echo -e "  ${GREEN}✓${NC} POSTGRES_PASSWORD, REDIS_PASSWORD, MINIO_ROOT_PASSWORD"
echo ""
echo -e "  ${YELLOW}Todavía debes ajustar manualmente en .env:${NC}"
echo "    INITIAL_ADMIN_PASSWORD   (contraseña del primer admin)"
echo "    INITIAL_ADMIN_EMAIL      (email del primer admin)"
echo ""
echo "  Editar:"
echo "    nano .env"
echo ""
echo "  Luego arrancar:"
echo "    ./scripts/prod.sh build"
echo "    ./scripts/prod.sh start"
echo ""
