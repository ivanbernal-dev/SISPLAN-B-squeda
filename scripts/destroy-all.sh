#!/usr/bin/env bash
# ============================================================
# UBPD — DESTRUCCIÓN TOTAL DE DOCKER (scope del proyecto)
#
# Borra del entorno Docker TODO lo asociado al proyecto UBPD:
#   - Contenedores (los del compose + cualquier ubpd_* huérfano)
#   - Imágenes (las construidas localmente: ubpd-app-*  +  las
#     descargadas para servicios del compose si --pull-images)
#   - Volúmenes nombrados (ubpd_postgres_data, ubpd_minio_data,
#     ubpd_valkey_data y cualquier otro ubpd_*)
#   - Redes del compose
#
# Diferencia con reset-fresh.sh:
#   reset-fresh = limpia DATOS pero deja imágenes y vuelve a levantar.
#   destroy-all = borra imágenes y volúmenes, NO vuelve a levantar.
#                 Para volver a usar el sistema toca:
#                     ./scripts/prod.sh build && ./scripts/prod.sh start
#
# Requiere TRIPLE confirmación:
#   1) Escribir la frase exacta "DESTRUIR TODO"
#   2) Aceptar el alcance (con o sin --all-images)
#   3) Ingresar el PIN definido en .env como RESET_PIN
#
# Variables opcionales (CI / automatización):
#   DESTROY_AUTO_CONFIRM=yes  — salta los prompts
#   DESTROY_AUTO_PIN=<pin>    — pasa el PIN sin pedirlo
#   DESTROY_INCLUDE_3RD=yes   — además borra imágenes 3rd party
#                                (postgres, nginx, minio, valkey)
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
[ -f ".env" ] || { err "No existe .env en: $ROOT_DIR"; exit 1; }

read_env() {
  local key="$1"
  local raw
  raw=$(grep -E "^${key}=" .env 2>/dev/null | head -1 || true)
  [ -z "$raw" ] && { echo ""; return 0; }
  printf '%s' "$raw" | cut -d= -f2- | tr -d '\r' \
    | sed -e 's/^"//; s/"$//' -e "s/^'//; s/'$//"
}

RESET_PIN=$(read_env RESET_PIN)
command -v docker >/dev/null 2>&1 || { err "Docker no está en PATH."; exit 1; }

if [ -z "${RESET_PIN:-}" ]; then
  err "RESET_PIN no está configurado en .env."
  echo "  Agrega al .env:   RESET_PIN=<pin>    (mismo PIN que usa reset-fresh)"
  exit 1
fi

INCLUDE_3RD="${DESTROY_INCLUDE_3RD:-no}"

# ── Banner ───────────────────────────────────────────────────
echo ""
echo -e "${RED}${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}${BOLD}║   ☠   DESTRUCCIÓN TOTAL DE DOCKER (UBPD)                ║${NC}"
echo -e "${RED}${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}  Esto eliminará del entorno Docker:${NC}"
echo "    · Todos los contenedores del compose (y cualquier ubpd_* huérfano)"
echo "    · Imágenes construidas localmente: ubpd-app-backend, ubpd-app-frontend"
echo "    · Volúmenes ubpd_postgres_data, ubpd_minio_data, ubpd_valkey_data"
echo "    · Red ubpd_network"
if [ "$INCLUDE_3RD" = "yes" ]; then
  echo -e "${YELLOW}  + Imágenes 3rd party del compose:${NC}"
  echo "    · postgres:16-alpine, nginx:1.25-alpine,"
  echo "      minio/minio:latest, valkey/valkey:7-alpine"
fi
echo ""
warn "Esta operación NO se puede deshacer."
warn "El sistema NO queda levantado al terminar. Para volver a usarlo:"
echo "    ./scripts/prod.sh build && ./scripts/prod.sh start"
echo ""

# ── Confirmación 1: frase ────────────────────────────────────
AUTO_CONFIRM="${DESTROY_AUTO_CONFIRM:-}"
if [ "$AUTO_CONFIRM" != "yes" ]; then
  echo -e "${BOLD}Escribe la frase exacta para continuar: ${RED}DESTRUIR TODO${NC}"
  printf "  > "
  read -r FRASE
  [ "$FRASE" = "DESTRUIR TODO" ] || { echo "  Operación cancelada (frase no coincide)."; exit 0; }

  # Confirmación 2: alcance
  echo ""
  if [ "$INCLUDE_3RD" = "yes" ]; then
    echo -e "${BOLD}Confirmar: ¿borrar TAMBIÉN imágenes 3rd party? (escribe 'si')${NC}"
  else
    echo -e "${BOLD}Confirmar alcance (solo proyecto, NO 3rd party). Escribe 'si' para continuar:${NC}"
  fi
  printf "  > "
  read -r ALCANCE
  [ "$ALCANCE" = "si" ] || { echo "  Operación cancelada (alcance no confirmado)."; exit 0; }
fi

# ── Confirmación 3: PIN ──────────────────────────────────────
INPUT_PIN="${DESTROY_AUTO_PIN:-}"
if [ -z "$INPUT_PIN" ]; then
  echo ""
  echo -e "${BOLD}Ingresa el PIN definido en .env (RESET_PIN):${NC}"
  printf "  > "
  read -rs INPUT_PIN
  echo ""
fi
[ "$INPUT_PIN" = "$RESET_PIN" ] || { err "PIN incorrecto. Operación cancelada."; exit 1; }
ok "PIN aceptado."

# ── Backup preventivo (best-effort) ──────────────────────────
hdr "Backup preventivo (best-effort)..."
POSTGRES_USER=$(read_env POSTGRES_USER)
POSTGRES_DB=$(read_env POSTGRES_DB)
mkdir -p backups/pre-destroy
TS=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backups/pre-destroy/pre_destroy_${TS}.sql.gz"
if docker compose ps --status running --services 2>/dev/null | grep -q '^postgres$'; then
  if docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" 2>/dev/null | gzip > "$BACKUP_FILE" 2>/dev/null; then
    ok "Backup guardado en $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"
  else
    warn "No se pudo generar backup (postgres no respondió). Continúa la destrucción."
    rm -f "$BACKUP_FILE"
  fi
else
  warn "PostgreSQL no está corriendo — se omite backup preventivo."
fi

# ── 1. Bajar todo con compose ────────────────────────────────
hdr "[1/5] docker compose down -v --rmi local --remove-orphans..."
docker compose down -v --rmi local --remove-orphans 2>&1 | tail -10 || true

# ── 2. Eliminar contenedores ubpd_* huérfanos ────────────────
hdr "[2/5] Eliminando contenedores ubpd_* sobrantes..."
ORPHAN_CT=$(docker ps -a --filter "name=^ubpd_" --format '{{.ID}}')
if [ -n "$ORPHAN_CT" ]; then
  echo "$ORPHAN_CT" | xargs -r docker rm -f >/dev/null
  ok "Contenedores ubpd_* eliminados"
else
  ok "No quedaban contenedores ubpd_* huérfanos"
fi

# ── 3. Eliminar imágenes ubpd-app-* ──────────────────────────
hdr "[3/5] Eliminando imágenes locales ubpd-app-*..."
LOCAL_IMGS=$(docker images --filter "reference=ubpd-app-*" --format '{{.ID}}' | sort -u)
if [ -n "$LOCAL_IMGS" ]; then
  echo "$LOCAL_IMGS" | xargs -r docker rmi -f >/dev/null 2>&1 || true
  ok "Imágenes ubpd-app-* eliminadas"
else
  ok "No había imágenes ubpd-app-* locales"
fi

# ── 4. Eliminar imágenes 3rd party (opcional) ────────────────
if [ "$INCLUDE_3RD" = "yes" ]; then
  hdr "[4/5] Eliminando imágenes 3rd party del compose..."
  for img in \
      "postgres:16-alpine" \
      "nginx:1.25-alpine" \
      "minio/minio:latest" \
      "valkey/valkey:7-alpine"; do
    if docker image inspect "$img" >/dev/null 2>&1; then
      docker rmi -f "$img" >/dev/null 2>&1 && ok "  borrada: $img" || warn "  no se pudo borrar: $img"
    fi
  done
else
  hdr "[4/5] (Se conservan imágenes 3rd party — usa DESTROY_INCLUDE_3RD=yes para borrarlas)"
fi

# ── 5. Eliminar volúmenes ubpd_* y la red del proyecto ───────
hdr "[5/5] Eliminando volúmenes ubpd_* y red ubpd_network..."
for vol in $(docker volume ls --format '{{.Name}}' | grep -E '^ubpd_' || true); do
  docker volume rm "$vol" >/dev/null 2>&1 && ok "  volumen borrado: $vol" || warn "  no se pudo borrar: $vol"
done
if docker network ls --format '{{.Name}}' | grep -q '^ubpd_network$'; then
  docker network rm ubpd_network >/dev/null 2>&1 && ok "  red borrada: ubpd_network" || true
fi

# ── Resumen ──────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║  ✓  Docker quedó limpio (scope UBPD)                     ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  Para volver a levantar el sistema desde cero:"
echo "      ./scripts/prod.sh build && ./scripts/prod.sh start"
echo ""
if [ -f "$BACKUP_FILE" ]; then
  echo "  Backup pre-destroy: $BACKUP_FILE"
fi
echo ""
