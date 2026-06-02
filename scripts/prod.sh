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
        # Estrategia (sin depender de psycopg2 dentro del backend):
        #   1. Generamos un SQL con dollar-quoting de Postgres ($pipeline$...$pipeline$)
        #      que mete el contenido del .py como literal sin escapado.
        #   2. Lo ejecutamos con `psql` desde el contenedor postgres (que lo
        #      tiene nativo). Esto desactiva los scripts activos previos y
        #      crea uno nuevo activo.
        #   3. Si el usuario pasa 'run' como 2º arg, hacemos login como admin
        #      y POST al endpoint /run vía curl para refrescar los KPIs.

        PG_USER=$(grep -E '^POSTGRES_USER=' .env | cut -d= -f2- | tr -d '"' | tr -d "'")
        PG_DB=$(grep -E '^POSTGRES_DB=' .env | cut -d= -f2- | tr -d '"' | tr -d "'")
        [ -z "$PG_USER" ] && { err "POSTGRES_USER no está en .env"; exit 1; }
        [ -z "$PG_DB" ]   && { err "POSTGRES_DB no está en .env"; exit 1; }
        if [ ! -f "scripts/pai_2026/pipeline_pai.py" ]; then
            err "No encuentro scripts/pai_2026/pipeline_pai.py"; exit 1
        fi

        # 1) Compilar SQL con dollar quoting
        #    - desactiva scripts activos previos
        #    - inserta el PAI como nuevo activo
        #    - LIMPIA kpi_resultados de KPIs huérfanos del script ejemplo
        #      (kpi_cobertura, kpi_completitud, kpi_calidad, kpi_gestion,
        #       kpi_oportunidad y todos sus sub-KPIs kpi_cob_*, kpi_comp_*,…)
        #      para que al re-ejecutar el pipeline PAI no se mezclen con
        #      los L1..L6 / L1-P1..L6-P2.
        SQL_FILE=$(mktemp)
        # shellcheck disable=SC2046
        {
            echo "BEGIN;"
            echo "UPDATE pipeline_scripts SET activo = false WHERE activo = true;"
            echo "INSERT INTO pipeline_scripts (id, nombre, codigo, activo, created_at, updated_at)"
            echo "VALUES (gen_random_uuid(), 'Pipeline PAI 2026 (sync)', \$pipeline\$"
            cat scripts/pai_2026/pipeline_pai.py
            echo ""
            echo "\$pipeline\$, true, now(), now());"
            echo "-- Limpieza total: borra TODOS los kpi_resultados (script ejemplo,"
            echo "-- runs viejos, KPIs huérfanos, todo). El PAI los reconstruye al"
            echo "-- correr con 'pipeline-sync run'. Si no se pasa run, el endpoint"
            echo "-- /stats/kpis devuelve los 6 defaults L1..L6 en 0% (sin datos)."
            echo "DELETE FROM kpi_resultados;"
            echo
            echo "-- Backfill: pct_avance_final ahora se guarda como PORCENTAJE (0..100),"
            echo "-- no fracción (0..1). Recalcula los formularios existentes y actualiza"
            echo "-- estado_actividad coherente. Usa una CTE para no repetir el ratio."
            echo "WITH r AS ("
            echo "  SELECT id,"
            echo "         COALESCE(NULLIF(datos_dinamicos->>'pct_avance_proyectado','')::float, 0) AS proy,"
            echo "         COALESCE(NULLIF(datos_dinamicos->>'pct_avance_alcanzado','')::float, 0)  AS alc"
            echo "  FROM formularios_respondidos"
            echo "  WHERE datos_dinamicos ? 'pct_avance_proyectado'"
            echo "), calc AS ("
            echo "  SELECT id, proy, alc,"
            echo "         CASE WHEN proy > 0 THEN round((alc / proy * 100)::numeric, 2) END AS pct_final"
            echo "  FROM r"
            echo ")"
            echo "UPDATE formularios_respondidos f SET datos_dinamicos ="
            echo "  jsonb_set(jsonb_set(f.datos_dinamicos,"
            echo "    '{pct_avance_final}',"
            echo "    CASE WHEN c.pct_final IS NULL THEN 'null'::jsonb ELSE to_jsonb(c.pct_final) END),"
            echo "    '{estado_actividad}',"
            echo "    to_jsonb(CASE"
            echo "      WHEN c.pct_final IS NULL    THEN 'No Aplica'"
            echo "      WHEN c.pct_final >= 90      THEN 'Cumple'"
            echo "      WHEN c.pct_final >= 70      THEN 'Cumple Parcialmente'"
            echo "      WHEN c.pct_final >  0       THEN 'No Cumple'"
            echo "      ELSE 'No Aplica' END))"
            echo "FROM calc c WHERE c.id = f.id;"
            echo "COMMIT;"
            echo "SELECT 'Scripts:' AS info; SELECT id, nombre, length(codigo) AS chars, activo, updated_at FROM pipeline_scripts ORDER BY updated_at DESC LIMIT 5;"
            echo "SELECT 'KPIs restantes:' AS info; SELECT nivel, kpi_key, valor FROM kpi_resultados ORDER BY nivel, kpi_key;"
        } > "$SQL_FILE"

        # 2) Copiar al contenedor postgres y ejecutar
        info "Aplicando SQL en postgres (desactiva activo + inserta PAI + limpia KPIs huérfanos)..."
        $COMPOSE cp "$SQL_FILE" postgres:/tmp/sync_pipeline.sql
        $COMPOSE exec -T postgres psql -U "$PG_USER" -d "$PG_DB" -f /tmp/sync_pipeline.sql
        $COMPOSE exec -T postgres rm -f /tmp/sync_pipeline.sql 2>/dev/null || true
        rm -f "$SQL_FILE"
        ok "Script PAI cargado como activo. Tabla kpi_resultados limpia (0 filas)."

        # 3) Si pidió 'run', ejecutar el pipeline vía API
        if [ "${SERVICE:-}" = "--run" ] || [ "${SERVICE:-}" = "run" ]; then
            header "Ejecutando pipeline en modo producción (refresca /estadisticas)..."
            ADMIN_USER=$(grep -E '^INITIAL_ADMIN_USERNAME=' .env | cut -d= -f2- | tr -d '"' | tr -d "'")
            ADMIN_PASS=$(grep -E '^INITIAL_ADMIN_PASSWORD=' .env | cut -d= -f2- | tr -d '"' | tr -d "'")
            TOKEN=$(curl -s -X POST http://localhost/api/auth/login \
                -H "Content-Type: application/json" \
                -d "{\"username\":\"$ADMIN_USER\",\"password\":\"$ADMIN_PASS\"}" \
                | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token',''))" 2>/dev/null)
            if [ -z "$TOKEN" ]; then
                warn "No se pudo obtener token de admin para ejecutar. Hazlo manual:"
                warn "  → Admin → Script Pipeline → Ejecutar (modo producción)"
            else
                # Construir body { codigo: <python>, modo: "produccion" }
                BODY=$(python3 -c "
import json
print(json.dumps({'codigo': open('scripts/pai_2026/pipeline_pai.py').read(), 'modo':'produccion'}))
")
                RESP=$(curl -s -X POST http://localhost/api/admin/script-pipeline/run \
                    -H "Authorization: Bearer $TOKEN" \
                    -H "Content-Type: application/json" \
                    -d "$BODY")
                OK=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('ok',False))" 2>/dev/null)
                if [ "$OK" = "True" ]; then
                    ok "Pipeline ejecutado y KPIs guardados en BD"
                    echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print('  '+(d.get('stdout') or '').strip().split(chr(10))[-1])" 2>/dev/null || true
                else
                    warn "Ejecución no fue exitosa. Respuesta:"
                    echo "$RESP" | head -c 400
                fi
            fi
        else
            info "Para refrescar los KPIs ejecuta:  ./scripts/prod.sh pipeline-sync run"
        fi
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
