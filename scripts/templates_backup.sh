#!/usr/bin/env bash
# =============================================================================
# templates_backup.sh — Exportar e importar templates de UBPD
# =============================================================================
# Uso:
#   ./scripts/templates_backup.sh export              → guarda templates_backup_FECHA.json
#   ./scripts/templates_backup.sh export mi_backup.json
#   ./scripts/templates_backup.sh import mi_backup.json
# =============================================================================

set -euo pipefail

# ── Configuración ─────────────────────────────────────────────────────────────
API_URL="${UBPD_API_URL:-http://localhost/api}"
DEFAULT_FILE="templates_backup_$(date +%Y%m%d_%H%M%S).json"

ACTION="${1:-help}"
FILE="${2:-$DEFAULT_FILE}"

# ── Colores ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅  $*${NC}"; }
err()  { echo -e "${RED}❌  $*${NC}";  }
info() { echo -e "${YELLOW}ℹ️   $*${NC}"; }

# ── Ayuda ─────────────────────────────────────────────────────────────────────
if [ "$ACTION" = "help" ] || [ "$ACTION" = "-h" ] || [ "$ACTION" = "--help" ]; then
  echo ""
  echo "  UBPD — Respaldo de Templates"
  echo "  ─────────────────────────────────────────────────────"
  echo "  Exportar  →  $0 export [archivo.json]"
  echo "  Importar  →  $0 import <archivo.json>"
  echo ""
  echo "  Variable de entorno opcional:"
  echo "    UBPD_API_URL  (por defecto: http://localhost/api)"
  echo ""
  exit 0
fi

# ── Credenciales ──────────────────────────────────────────────────────────────
echo ""
info "Conectando a: $API_URL"
echo ""
read -rp "  Email administrador: " EMAIL
read -rsp "  Contraseña:          " PASSWORD
echo ""

# ── Login ─────────────────────────────────────────────────────────────────────
info "Autenticando..."
TOKEN=$(curl -sf -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token',''))" 2>/dev/null || true)

if [ -z "$TOKEN" ]; then
  err "No se pudo autenticar. Verifique email y contraseña."
  exit 1
fi
ok "Autenticado correctamente."
echo ""

# ── Exportar ──────────────────────────────────────────────────────────────────
if [ "$ACTION" = "export" ]; then
  info "Exportando templates a: $FILE"

  HTTP_CODE=$(curl -s -o "$FILE" -w "%{http_code}" \
    "$API_URL/templates/export" \
    -H "Authorization: Bearer $TOKEN")

  if [ "$HTTP_CODE" != "200" ]; then
    err "Error HTTP $HTTP_CODE al exportar."
    rm -f "$FILE"
    exit 1
  fi

  # Formatear JSON
  python3 -m json.tool "$FILE" > "${FILE}.tmp" && mv "${FILE}.tmp" "$FILE"

  TOTAL=$(python3 -c "import json; d=json.load(open('$FILE')); print(len(d))" 2>/dev/null || echo "?")
  ok "Exportación completada: $TOTAL template(s) → $FILE"

# ── Importar ──────────────────────────────────────────────────────────────────
elif [ "$ACTION" = "import" ]; then
  if [ ! -f "$FILE" ]; then
    err "Archivo no encontrado: $FILE"
    exit 1
  fi

  TOTAL=$(python3 -c "import json; d=json.load(open('$FILE')); print(len(d))" 2>/dev/null || echo "?")
  info "Importando $TOTAL template(s) desde: $FILE"
  echo ""
  read -rp "  ¿Confirma la importación? [s/N]: " CONFIRM
  if [[ ! "$CONFIRM" =~ ^[sS]$ ]]; then
    info "Operación cancelada."
    exit 0
  fi
  echo ""

  RESULT=$(curl -sf -X POST "$API_URL/templates/import" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    --data-binary "@$FILE" 2>/dev/null || true)

  if [ -z "$RESULT" ]; then
    err "No se recibió respuesta del servidor."
    exit 1
  fi

  MENSAJE=$(python3 -c "import json,sys; d=json.loads('$RESULT'); print(d.get('mensaje',''))" 2>/dev/null || echo "$RESULT")
  ok "$MENSAJE"

else
  err "Acción desconocida: '$ACTION'. Use export o import."
  exit 1
fi

echo ""
