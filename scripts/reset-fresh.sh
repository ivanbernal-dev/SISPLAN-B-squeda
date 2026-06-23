#!/usr/bin/env bash
# ============================================================
# UBPD — RESET TOTAL A ESTADO DE INSTALACIÓN
#
# Deja la base de datos, MinIO y Redis (Valkey) exactamente
# como quedaron tras una instalación limpia:
#   - PostgreSQL: vuelve a crearse el esquema y se siembran el
#     admin inicial, templates por defecto y dependencias seed.
#   - MinIO: se borran TODOS los archivos adjuntos.
#   - Valkey (Redis): se vacía el caché y las colas Celery.
#
# Requiere DOBLE confirmación:
#   1) Escribir la frase exacta "BORRAR TODO".
#   2) Ingresar el PIN definido en .env como RESET_PIN.
#
# Si RESET_PIN no está en .env el script se aborta con
# instrucciones (no hay PIN por defecto — evita borrados
# accidentales).
#
# Uso:
#   ./scripts/reset-fresh.sh
#
# Variables de entorno opcionales (para automatización en CI):
#   RESET_AUTO_CONFIRM=yes  — salta los prompts de confirmación
#   RESET_AUTO_PIN=<pin>    — pasa el PIN sin pedirlo interactivamente
# ============================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# ── Colores ──────────────────────────────────────────────────
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

err()  { echo -e "${RED}✗ $*${NC}" >&2; }
warn() { echo -e "${YELLOW}⚠ $*${NC}"; }
ok()   { echo -e "${GREEN}✓ $*${NC}"; }
hdr()  { echo -e "\n${CYAN}▶  $*${NC}"; }

# ── Pre-requisitos ───────────────────────────────────────────
if [ ! -f ".env" ]; then
  err "No existe .env en: $ROOT_DIR"
  echo "  Ejecuta primero ./scripts/install.sh"
  exit 1
fi

# Leer variables específicas del .env (sin `source`, que rompe con
# valores que contienen caracteres especiales como '-' o '!').
read_env() {
  # No falla si la clave no está (grep saldría 1 y romperia set -e).
  local key="$1"
  local raw
  raw=$(grep -E "^${key}=" .env 2>/dev/null | head -1 || true)
  [ -z "$raw" ] && { echo ""; return 0; }
  printf '%s' "$raw" \
    | cut -d= -f2- \
    | tr -d '\r' \
    | sed -e 's/^"//; s/"$//' -e "s/^'//; s/'$//"
}

POSTGRES_USER=$(read_env POSTGRES_USER)
POSTGRES_DB=$(read_env POSTGRES_DB)
INITIAL_ADMIN_USERNAME=$(read_env INITIAL_ADMIN_USERNAME)
INITIAL_ADMIN_EMAIL=$(read_env INITIAL_ADMIN_EMAIL)
INITIAL_ADMIN_PASSWORD=$(read_env INITIAL_ADMIN_PASSWORD)
RESET_PIN=$(read_env RESET_PIN)

if ! command -v docker >/dev/null 2>&1; then
  err "Docker no está disponible en PATH."
  exit 1
fi

# ── Validar PIN configurado ──────────────────────────────────
if [ -z "${RESET_PIN:-}" ]; then
  err "RESET_PIN no está configurado en .env."
  echo ""
  echo "  Para habilitar este comando agrega al final de tu .env una línea:"
  echo ""
  echo -e "      ${BOLD}RESET_PIN=<tu_pin_personal>${NC}    # ej: RESET_PIN=472918"
  echo ""
  echo "  Recomendación: un PIN numérico de 4-8 dígitos que SOLO conozcas tú."
  echo "  No se versiona en git (el .env está en .gitignore)."
  exit 1
fi

# ── Banner de advertencia ────────────────────────────────────
echo ""
echo -e "${RED}${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}${BOLD}║   ⚠   RESET TOTAL — ESTADO DE INSTALACIÓN LIMPIA        ║${NC}"
echo -e "${RED}${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}  Esto va a ELIMINAR DEFINITIVAMENTE:${NC}"
echo "    · PostgreSQL: base de datos completa (volumen ubpd_postgres_data)"
echo "    · MinIO:      todos los archivos adjuntos (volumen ubpd_minio_data)"
echo "    · Valkey:     caché y colas de trabajo (volumen ubpd_valkey_data)"
echo ""
echo -e "${YELLOW}  Después del reset se recrea automáticamente:${NC}"
echo "    · Esquema de tablas (vía Alembic) o models al startup"
echo "    · Usuario admin inicial (INITIAL_ADMIN_USERNAME del .env)"
echo "    · Buckets y carpetas de MinIO"
echo ""
warn "Esta operación NO se puede deshacer."
echo ""

# ── Confirmación 1: frase ────────────────────────────────────
AUTO_CONFIRM="${RESET_AUTO_CONFIRM:-}"
if [ "$AUTO_CONFIRM" != "yes" ]; then
  echo -e "${BOLD}Escribe la frase exacta para continuar: ${RED}BORRAR TODO${NC}"
  printf "  > "
  read -r FRASE
  if [ "$FRASE" != "BORRAR TODO" ]; then
    echo ""
    echo "  Operación cancelada (la frase no coincide)."
    exit 0
  fi
fi

# ── Confirmación 2: PIN ──────────────────────────────────────
INPUT_PIN="${RESET_AUTO_PIN:-}"
if [ -z "$INPUT_PIN" ]; then
  echo ""
  echo -e "${BOLD}Ingresa el PIN definido en .env (RESET_PIN):${NC}"
  printf "  > "
  # -s = oculta lo que se escribe
  read -rs INPUT_PIN
  echo ""
fi

if [ "$INPUT_PIN" != "$RESET_PIN" ]; then
  err "PIN incorrecto. Operación cancelada."
  exit 1
fi
ok "PIN aceptado."

# ── Hacer backup automático antes de borrar (best-effort) ────
hdr "Backup preventivo (best-effort) antes del reset..."
mkdir -p backups/pre-reset
TS=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backups/pre-reset/pre_reset_${TS}.sql.gz"
if docker compose ps --status running --services 2>/dev/null | grep -q '^postgres$'; then
  if docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" 2>/dev/null | gzip > "$BACKUP_FILE" 2>/dev/null; then
    ok "Backup guardado en $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"
  else
    warn "No se pudo generar backup automático (postgres no respondió). Continúa el reset."
    rm -f "$BACKUP_FILE"
  fi
else
  warn "PostgreSQL no está corriendo — se omite backup preventivo."
fi

# ── 1. Detener servicios dependientes ────────────────────────
hdr "[1/6] Deteniendo servicios..."
docker compose down --remove-orphans 2>&1 | tail -3 || true

# ── 2. Eliminar volúmenes de datos ───────────────────────────
hdr "[2/6] Eliminando volúmenes (postgres + minio + valkey)..."
for vol in ubpd_postgres_data ubpd_minio_data ubpd_valkey_data; do
  if docker volume inspect "$vol" >/dev/null 2>&1; then
    docker volume rm "$vol" >/dev/null && ok "Volumen $vol eliminado"
  else
    warn "Volumen $vol no existía"
  fi
done

# ── 3. Levantar infraestructura limpia ───────────────────────
hdr "[3/6] Levantando PostgreSQL, MinIO y Valkey limpios..."
docker compose up -d postgres minio valkey
echo "       Esperando a que PostgreSQL esté listo..."
for i in $(seq 1 30); do
  if docker compose exec -T postgres pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" >/dev/null 2>&1; then
    ok "PostgreSQL listo"
    break
  fi
  sleep 2
  [ "$i" -eq 30 ] && { err "PostgreSQL no respondió en 60s"; exit 1; }
done

# ── 4. Aplicar migraciones / crear esquema ───────────────────
hdr "[4/6] Levantando backend (crea esquema y siembra admin inicial)..."
docker compose up -d backend
echo "       Esperando a que el backend reporte health OK..."
for i in $(seq 1 30); do
  if curl -fsS http://localhost/api/health >/dev/null 2>&1; then
    ok "Backend OK"
    break
  fi
  sleep 2
  [ "$i" -eq 30 ] && warn "El backend no respondió a /api/health (puede tardar un poco más)"
done

# Intentar aplicar migraciones explícitamente (idempotente)
docker compose exec -T backend alembic upgrade head 2>/dev/null \
  && ok "Migraciones Alembic aplicadas" \
  || warn "Alembic no ejecutó (puede ser que el backend ya creó las tablas por modelos)"

# ── 5. Levantar el resto de servicios ────────────────────────
hdr "[5/6] Levantando resto de servicios (nginx, frontend, celery, ...)"
docker compose up -d

# ── 6. Resumen ───────────────────────────────────────────────
hdr "[6/6] Listo."
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║  ✓  Base reiniciada a estado de instalación limpia       ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  Credenciales del admin inicial (.env):"
echo "    Usuario:  ${INITIAL_ADMIN_USERNAME:-admin}"
echo "    Email:    ${INITIAL_ADMIN_EMAIL:-admin@ubpd.gov.co}"
echo "    Password: ${INITIAL_ADMIN_PASSWORD:-(la del .env)}"
echo ""
if [ -f "$BACKUP_FILE" ]; then
  echo "  Backup pre-reset: $BACKUP_FILE"
fi
echo ""
