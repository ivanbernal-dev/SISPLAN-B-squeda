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
#   pipeline-sync [run] Sincroniza pipeline_pai.py del repo como script activo
#                       en la BD. 'run' además lo ejecuta en producción.
#   reset-db           Eliminar BD y recrear (requiere ALLOW_DB_RESET=true en .env)
#   reset-fresh        Reset TOTAL a estado de instalación limpia (frase + PIN)
#   destroy [all]      DESTRUIR contenedores, imágenes y volúmenes (frase + PIN).
#                       Añade 'all' para borrar también imágenes 3rd party.
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

# IP “de red” solo desde .env (sin auto-detección: evita IPs equivocadas y simplifica).
read_server_ip() {
    local ip=""
    [ -f .env ] && ip=$(grep -E '^SERVER_IP=' .env 2>/dev/null | cut -d= -f2- | tr -d '\r' | tr -d '"' | tr -d "'" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    [ -n "$ip" ] && { echo "$ip"; return; }
    echo "127.0.0.1"
}

SERVER_IP=$(read_server_ip)

check_prerequisites() {
    local ok=true
    [ ! -f ".env" ] && { echo -e "${RED}[ERROR]${NC} No existe .env — ejecuta: ./scripts/install.sh"; ok=false; }
    if [ "$ok" = false ]; then exit 1; fi
}

show_urls() {
    BOLD='\033[1m'
    local lan="$SERVER_IP"

    echo ""
    echo -e "  ${CYAN}────────────────────────────────────────────${NC}"
    echo -e "  ${BOLD}${GREEN}🌐  Portal de Indicadores (público, sin login)${NC}"
    echo -e "  ${BOLD}${GREEN}    http://127.0.0.1/estadisticas${NC}  ${CYAN}(este equipo)${NC}"
    [ "$lan" != "127.0.0.1" ] && [ -n "$lan" ] && \
        echo -e "  ${BOLD}${GREEN}    http://${lan}/estadisticas${NC}  ${CYAN}(red — misma IP que en .env)${NC}"
    echo -e "  ${CYAN}────────────────────────────────────────────${NC}"
    echo ""
    info "Aplicación (login): http://127.0.0.1"
    info "API Docs:           http://127.0.0.1/api/docs"
    info "Health check:       http://127.0.0.1/api/health"
    if [ "$lan" != "127.0.0.1" ] && [ -n "$lan" ]; then
        info "… vía red LAN:      http://${lan} (requiere http://${lan} en CORS_ORIGINS del .env)"
    fi
    echo ""
}

# Resumen de dónde quedan los archivos de log en disco. Se llama al hacer `start`
# para que el operador sepa exactamente dónde buscar errores sin tener que
# preguntar.
show_log_paths() {
    local base="${ROOT_DIR}/logs"
    echo -e "  ${CYAN}────────────────────────────────────────────${NC}"
    echo -e "  ${BOLD}📁  Logs en disco${NC}"
    echo -e "  ${CYAN}────────────────────────────────────────────${NC}"
    echo -e "  ${BOLD}Backend (app):${NC}"
    echo "    ${base}/backend/app.log              (todo, INFO+)"
    echo "    ${base}/backend/errors.log           (solo ERROR+)"
    echo "    ${base}/backend/access.log           (peticiones HTTP)"
    echo "    ${base}/backend/celery_worker.log    (Celery worker)"
    echo "    ${base}/backend/celery_beat.log      (Celery beat)"
    echo ""
    echo -e "  ${BOLD}${YELLOW}Pipeline de indicadores (datos → KPIs):${NC}"
    echo "    ${base}/backend/pipeline/pipeline.log         (histórico de ejecuciones)"
    echo "    ${base}/backend/pipeline/pipeline_errors.log  (solo errores)"
    echo "    ${base}/backend/pipeline/runs/                (un archivo por ejecución:"
    echo "                                              run_<fecha>_<modo>_<id>.log)"
    echo ""
    echo -e "  ${BOLD}${YELLOW}Cargas de Excel (dependencias):${NC}"
    echo "    ${base}/backend/uploads/upload_<fecha>_<id>.log"
    echo "                          (un archivo por intento de upload-excel,"
    echo "                           con el detalle de fila/columna que falló)"
    echo ""
    echo -e "  ${BOLD}Nginx:${NC}"
    echo "    ${base}/nginx/access.log             (accesos HTTP del proxy)"
    echo "    ${base}/nginx/error.log              (errores del proxy)"
    echo ""
    echo -e "  ${CYAN}Ver logs en vivo:${NC}  ./scripts/prod.sh logs [servicio]"
    echo -e "  ${CYAN}Tail del pipeline:${NC}  tail -f ${base}/backend/pipeline/pipeline.log"
    echo ""
}

case "$CMD" in

    start|up)
        check_prerequisites
        header "Levantando servicios..."
        # Asegurar que la carpeta de logs del pipeline existe antes de arrancar
        # (los volúmenes se montan automáticamente, pero esto evita que el
        # primer arranque escriba en una ruta inexistente en algunos hosts).
        mkdir -p logs/backend/pipeline/runs logs/backend/uploads logs/nginx 2>/dev/null || true
        $COMPOSE up -d $SERVICE
        echo ""
        echo -e "${GREEN}✅  Servicios levantados correctamente.${NC}"
        show_urls
        show_log_paths
        ;;

    stop|down)
        header "Deteniendo servicios..."
        $COMPOSE down $SERVICE
        ;;

    restart)
        header "Reiniciando ${SERVICE:-todos los servicios}..."
        # `restart` solo reinicia el contenedor con la imagen actual; si
        # acabas de hacer `build`, además hay que recrear el contenedor con
        # `up -d` para que tome la imagen nueva. Lo hacemos aquí para que el
        # operador no se pregunte por qué su cambio no aparece.
        $COMPOSE up -d $SERVICE
        info "(usado 'up -d' para garantizar que se aplique cualquier imagen recién construida)"
        ;;

    build)
        header "Construyendo imágenes..."
        $COMPOSE build $SERVICE
        header "Aplicando la imagen nueva (up -d)..."
        # `build` por sí solo NO actualiza el contenedor en ejecución: produce
        # una imagen nueva, pero el contenedor sigue corriendo con la vieja.
        # Hacer `up -d` después es idempotente: si nada cambió no hace nada,
        # si la imagen cambió recrea el contenedor automáticamente. Así un
        # `./scripts/prod.sh build frontend` despliega el cambio de una.
        $COMPOSE up -d $SERVICE
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
        echo ""

        # Lista de servicios esperados
        EXPECTED="nginx frontend backend celery celery-beat postgres valkey minio"

        # Obtener estado de todos los contenedores en JSON
        PS_JSON=$($COMPOSE ps --format json 2>/dev/null)

        running=0; starting=0; failed=0

        for svc in $EXPECTED; do
            # Normalizar guiones a guiones bajos para buscar en el nombre del contenedor
            svc_search=$(echo "$svc" | tr '-' '_')

            # Extraer estado del servicio (compatible con Docker Compose v2)
            STATUS=$(echo "$PS_JSON" | python3 -c "
import sys, json
data = sys.stdin.read().strip()
try:
    rows = json.loads(data) if data.startswith('[') else [json.loads(l) for l in data.splitlines() if l.strip()]
except:
    rows = []
svc = '$svc_search'
for r in rows:
    name = (r.get('Name','') or r.get('Service','')).replace('-','_')
    if svc in name:
        health = r.get('Health','')
        state  = r.get('State','') or r.get('Status','')
        if health:
            print(state + ' (' + health + ')')
        else:
            print(state)
        sys.exit(0)
print('ausente')
" 2>/dev/null)

            # Clasificar y mostrar con color + formato alineado
            case "$STATUS" in
                *exited*|*dead*|*"exit "*|ausente)
                    printf "  ${RED}✗${NC}  %-16s ${RED}%s${NC}\n" "$svc" "$STATUS"
                    failed=$((failed+1))
                    ;;
                *"health: starting"*|*starting*|*created*)
                    printf "  ${YELLOW}◐${NC}  %-16s ${YELLOW}%s${NC}\n" "$svc" "$STATUS"
                    starting=$((starting+1))
                    ;;
                *healthy*|*running*|*up*)
                    printf "  ${GREEN}✓${NC}  %-16s ${GREEN}%s${NC}\n" "$svc" "$STATUS"
                    running=$((running+1))
                    ;;
                *)
                    printf "  ${YELLOW}?${NC}  %-16s ${YELLOW}%s${NC}\n" "$svc" "${STATUS:-desconocido}"
                    starting=$((starting+1))
                    ;;
            esac
        done

        echo ""
        echo -e "  ${GREEN}✓ Activos: ${running}${NC}  ${YELLOW}◐ Iniciando: ${starting}${NC}  ${RED}✗ Fallidos: ${failed}${NC}"

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

    reset-fresh)
        header "Reset TOTAL a estado de instalación..."
        chmod +x scripts/reset-fresh.sh
        ./scripts/reset-fresh.sh
        ;;

    pipeline-sync)
        header "Sincronizando pipeline_pai.py → BD (script activo)..."
        # El backend ya tiene psycopg2 + requests instalados. Copiamos los 2
        # archivos al contenedor y ejecutamos ahí (resuelve postgres por
        # nombre de servicio del compose, no hace falta IP).
        RUN_FLAG=""
        if [ "${SERVICE:-}" = "--run" ] || [ "${SERVICE:-}" = "run" ]; then
            RUN_FLAG="--run"
            info "Modo --run: tras guardar se ejecutará el pipeline en producción."
        fi
        # Crear estructura temporal en el contenedor
        $COMPOSE exec -T backend mkdir -p /tmp/pai_sync || true
        $COMPOSE cp scripts/pai_2026/pipeline_pai.py        backend:/tmp/pai_sync/pipeline_pai.py
        $COMPOSE cp scripts/pai_2026/sync_pipeline_to_db.py backend:/tmp/pai_sync/sync_pipeline_to_db.py
        # Stub del .env adentro del contenedor: las credenciales reales están
        # en las variables de entorno del contenedor; el script las puede leer
        # con os.environ.
        $COMPOSE exec -T \
            -e POSTGRES_HOST=postgres \
            -e POSTGRES_PORT=5432 \
            -e UBPD_BASE_URL=http://nginx \
            backend sh -c "cd /tmp/pai_sync && cp /app/.env . 2>/dev/null || (cat > .env <<EOF
POSTGRES_USER=\$POSTGRES_USER
POSTGRES_PASSWORD=\$POSTGRES_PASSWORD
POSTGRES_DB=\$POSTGRES_DB
INITIAL_ADMIN_USERNAME=\$INITIAL_ADMIN_USERNAME
INITIAL_ADMIN_PASSWORD=\$INITIAL_ADMIN_PASSWORD
EOF
) && mkdir -p ./scripts/pai_2026 && cp pipeline_pai.py ./scripts/pai_2026/ && python sync_pipeline_to_db.py $RUN_FLAG"
        ;;

    destroy|nuke)
        header "DESTRUCCIÓN TOTAL de Docker (UBPD)..."
        chmod +x scripts/destroy-all.sh
        # Permitir pasar bandera al script:
        #   ./scripts/prod.sh destroy --all-images
        if [ "${SERVICE:-}" = "--all-images" ] || [ "${SERVICE:-}" = "all" ]; then
            DESTROY_INCLUDE_3RD=yes ./scripts/destroy-all.sh
        else
            ./scripts/destroy-all.sh
        fi
        ;;

    help|--help|-h|*)
        echo ""
        echo "Uso: ./scripts/prod.sh <comando> [servicio]"
        echo ""
        echo "  start   | up      Levantar servicios"
        echo "  stop    | down    Detener servicios"
        echo "  restart [svc]     Reiniciar (recrea contenedor → aplica imagen nueva)"
        echo "  build   [svc]     Construir imagen y aplicarla (build + up -d)"
        echo "  rebuild [svc]     Igual que build pero SIN caché de Docker"
        echo "  logs    [svc]     Logs en tiempo real"
        echo "  ps      | status  Estado + URLs"
        echo "  shell   [svc]     Shell (default: backend)"
        echo "  migrate           Migraciones Alembic"
        echo "  backup            Backup de base de datos"
        echo "  test              Ejecutar tests"
        echo "  reset-db          Resetear BD (requiere ALLOW_DB_RESET=true en .env)"
        echo "  pipeline-sync [run]"
        echo "                    Sincroniza scripts/pai_2026/pipeline_pai.py"
        echo "                    como el script ACTIVO del pipeline en BD."
        echo "                    Añade 'run' para además ejecutarlo en producción"
        echo "                    (refresca los KPIs visibles en /estadisticas)."
        echo "  reset-fresh       Reset TOTAL a estado de instalación limpia"
        echo "                    (pide frase 'BORRAR TODO' + PIN definido en .env"
        echo "                     como RESET_PIN; borra postgres + minio + valkey)"
        echo "  destroy [all]     DESTRUIR contenedores, imágenes locales y volúmenes"
        echo "                    del proyecto. Frase 'DESTRUIR TODO' + 'si' + PIN."
        echo "                    Añade 'all' (o --all-images) para borrar también"
        echo "                    las imágenes 3rd party (postgres, nginx, minio,…)"
        echo ""
        echo "Servicios: nginx | backend | frontend | celery | celery-beat | postgres | valkey | minio"
        echo ""
        ;;
esac
