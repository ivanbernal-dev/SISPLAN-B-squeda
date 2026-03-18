#!/usr/bin/env bash
# ============================================================
# UBPD — Gestión del Sistema
# ============================================================
# Uso: ./scripts/prod.sh <comando> [servicio]
#
# Comandos:
#   start    | up      Levantar todos los servicios
#   stop     | down    Detener y eliminar contenedores
#   restart  [svc]     Reiniciar todos o un servicio
#   build    [svc]     Construir/reconstruir imágenes
#   rebuild  [svc]     Reconstruir sin caché y levantar
#   logs     [svc]     Ver logs en tiempo real
#   ps       | status  Estado de los contenedores + URLs
#   shell    [svc]     Shell en un contenedor (default: backend)
#   migrate            Aplicar migraciones de base de datos
#   backup             Backup manual de base de datos
#   test               Ejecutar tests del backend
#   reset-db           Eliminar BD y recrear (requiere ALLOW_DB_RESET=true en .env)
#
# Ejemplos:
#   ./scripts/prod.sh start
#   ./scripts/prod.sh restart backend
#   ./scripts/prod.sh logs nginx
#   ./scripts/prod.sh shell backend
#   ./scripts/prod.sh migrate
# ============================================================
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE="docker compose"
CMD="${1:-status}"
SERVICE="${2:-}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

header() { echo -e "\n${CYAN}▶  $*${NC}"; }
info()   { echo -e "${GREEN}   $*${NC}"; }
warn()   { echo -e "${YELLOW}   $*${NC}"; }

# Leer IP del servidor del .env
SERVER_IP=$(grep -E "^SERVER_IP=" .env 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'" || echo "192.168.1.100")

check_prerequisites() {
    local ok=true
    [ ! -f ".env" ] && { echo -e "${RED}[ERROR]${NC} No existe .env — ejecuta: ./scripts/install.sh"; ok=false; }
    [ ! -f "nginx/certs/server.crt" ] && { echo -e "${RED}[ERROR]${NC} Sin certificado SSL — ejecuta: ./scripts/generate-ssl.sh <IP>"; ok=false; }
    [ "$ok" = false ] && exit 1
}

show_urls() {
    echo ""
    info "Aplicación:   https://${SERVER_IP}"
    info "Estadísticas: https://${SERVER_IP}/stats"
    info "API Docs:     https://${SERVER_IP}/api/docs"
    info "Health:       https://${SERVER_IP}/api/health"
    echo ""
}

case "$CMD" in

    start|up)
        check_prerequisites
        header "Levantando servicios..."
        $COMPOSE up -d $SERVICE
        show_urls
        ;;

    stop|down)
        header "Deteniendo servicios..."
        $COMPOSE down $SERVICE
        ;;

    restart)
        header "Reiniciando ${SERVICE:-todos los servicios}..."
        $COMPOSE restart $SERVICE
        ;;

    build)
        header "Construyendo imágenes..."
        $COMPOSE build $SERVICE
        ;;

    rebuild)
        header "Reconstruyendo sin caché..."
        $COMPOSE build --no-cache $SERVICE
        header "Levantando con imágenes nuevas..."
        $COMPOSE up -d $SERVICE
        ;;

    logs)
        header "Logs${SERVICE:+ de $SERVICE} (Ctrl+C para salir)"
        $COMPOSE logs -f --tail=100 $SERVICE
        ;;

    ps|status)
        header "Estado de los servicios:"
        $COMPOSE ps
        show_urls
        warn "Logs en disco: ./logs/backend/app.log  |  ./logs/nginx/access.log"
        ;;

    shell)
        TARGET="${SERVICE:-backend}"
        header "Shell en $TARGET"
        $COMPOSE exec "$TARGET" sh
        ;;

    migrate)
        header "Aplicando migraciones de base de datos..."
        $COMPOSE exec backend alembic upgrade head
        ;;

    backup)
        header "Ejecutando backup..."
        chmod +x scripts/backup.sh
        ./scripts/backup.sh
        ;;

    test)
        header "Ejecutando tests del backend..."
        $COMPOSE exec backend sh -c "cd /app && pytest tests/ -v --tb=short"
        ;;

    reset-db)
        header "Reset de base de datos..."
        chmod +x scripts/reset-db.sh
        ./scripts/reset-db.sh
        ;;

    help|--help|-h|*)
        echo ""
        echo "Uso: ./scripts/prod.sh <comando> [servicio]"
        echo ""
        echo "  start   | up      Levantar servicios"
        echo "  stop    | down    Detener servicios"
        echo "  restart [svc]     Reiniciar todos o uno"
        echo "  build   [svc]     Construir imágenes"
        echo "  rebuild [svc]     Reconstruir sin caché"
        echo "  logs    [svc]     Logs en tiempo real"
        echo "  ps      | status  Estado + URLs"
        echo "  shell   [svc]     Shell (default: backend)"
        echo "  migrate           Migraciones Alembic"
        echo "  backup            Backup de base de datos"
        echo "  test              Ejecutar tests"
        echo "  reset-db          Resetear BD (requiere ALLOW_DB_RESET=true en .env)"
        echo ""
        echo "Servicios: nginx | backend | frontend | celery | celery-beat | postgres | redis | minio"
        echo ""
        ;;
esac
