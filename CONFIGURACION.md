# UBPD — Configuración, Despliegue y Operación

---

## Requisitos del Servidor

| Componente | Mínimo | Recomendado |
|-----------|--------|-------------|
| CPU | 4 núcleos | 8 núcleos |
| RAM | 8 GB | 16 GB |
| Disco | 100 GB SSD | 500 GB SSD |
| SO | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| Docker Engine | 24+ | 25+ |
| Docker Compose plugin | 2.20+ | 2.24+ |
| OpenSSL | 1.1+ | — |

---

## Instalación inicial (una sola vez)

```bash
chmod +x scripts/*.sh
./scripts/install.sh
```

El script hace automáticamente:
1. Verifica Docker, docker compose y openssl
2. Crea `logs/nginx/`, `logs/backend/`, `nginx/certs/`, `postgres/init/`, `backups/`
3. Copia `.env.example` → `.env`
4. Genera el certificado SSL con la IP configurada en `.env`

Opcionalmente, generar todas las claves y contraseñas automáticamente:

```bash
./scripts/generar-env.sh          # detecta IP local, genera SECRET_KEY y passwords
./scripts/generar-env.sh --write  # igual, escribe en .env directamente
```

Luego **editar `.env`** con las credenciales del administrador inicial:

```bash
nano .env
```

---

## Variables de entorno (`.env`)

### Obligatorias

```bash
SERVER_IP=192.168.1.100        # IP del servidor en la intranet

# Generar con: python3 -c "import secrets; print(secrets.token_hex(64))"
SECRET_KEY=CAMBIAR_POR_CLAVE_LARGA_ALEATORIA

POSTGRES_PASSWORD=contraseña_segura
REDIS_PASSWORD=contraseña_segura      # usada por Valkey
MINIO_ROOT_PASSWORD=min8chars

INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=Admin@UBPD2024!
INITIAL_ADMIN_EMAIL=admin@ubpd.gov.co

CORS_ORIGINS=https://192.168.1.100,http://localhost:5173
```

### Logging

```bash
LOG_DIR=/app/logs   # montado en ./logs/backend del host
LOG_LEVEL=INFO      # DEBUG activa logs SQL y detallados
```

### Opcionales

| Variable | Default | Descripción |
|----------|---------|-------------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Vida del JWT |
| `MAX_UPLOAD_MB` | 50 | Tamaño máximo de archivos |
| `STATS_RECALC_INTERVAL_SECONDS` | 600 | Frecuencia de recálculo (segundos) |
| `APP_ENV` | production | `development` activa logging SQL |
| `ALLOW_DB_RESET` | false | Habilita `reset-db` (solo desarrollo) |

---

## Certificado SSL

Generado automáticamente por `install.sh`. Para regenerar:

```bash
./scripts/generate-ssl.sh 192.168.1.100
```

### Instalar en clientes Windows

1. Copiar `nginx/certs/server.crt` al equipo
2. Doble clic → **Instalar certificado** → Equipo local
3. **Examinar** → "Entidades de certificación raíz de confianza"
4. Aceptar y reiniciar el navegador

### Instalar en Firefox (cualquier SO)

`about:preferences#privacy` → Ver certificados → Importar → seleccionar `server.crt` → "Confiar para sitios web"

### Instalar en macOS

```bash
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain nginx/certs/server.crt
```

---

## Despliegue sin Internet (Air-Gapped)

### En máquina con internet

```bash
# Descargar y empaquetar imágenes Docker
docker pull postgres:16-alpine valkey/valkey:7-alpine nginx:1.25-alpine \
  minio/minio:latest python:3.12-slim node:20-alpine
docker save postgres:16-alpine valkey/valkey:7-alpine nginx:1.25-alpine \
  minio/minio:latest python:3.12-slim node:20-alpine \
  | gzip > ubpd-docker-images.tar.gz

# O usar el script incluido:
./scripts/save-docker-images.sh
```

### Transferir al servidor

```bash
scp ubpd-docker-images.tar.gz usuario@192.168.1.100:/opt/ubpd/
scp -r ubpd-app/ usuario@192.168.1.100:/opt/ubpd/
# Alternativa: copiar por USB
```

### En el servidor sin internet

```bash
cd /opt/ubpd
docker load -i ubpd-docker-images.tar.gz          # importar imágenes
cd ubpd-app
chmod +x scripts/*.sh
./scripts/install.sh                               # configurar
nano .env                                          # editar IP y contraseñas
./scripts/prod.sh start                            # levantar (sin build)
./scripts/prod.sh ps                               # verificar estado
```

---

## Gestión del sistema (`prod.sh`)

Todo se maneja con un único script:

```bash
# ── Ciclo de vida ──────────────────────────────────────────
./scripts/prod.sh start              # levantar todos los servicios
./scripts/prod.sh stop               # detener (datos preservados en volúmenes)
./scripts/prod.sh restart            # reiniciar todo
./scripts/prod.sh restart <servicio> # reiniciar uno solo
./scripts/prod.sh ps                 # estado de contenedores + URLs

# ── Build / Rebuild ────────────────────────────────────────
./scripts/prod.sh build              # construir todas las imágenes
./scripts/prod.sh rebuild backend    # reconstruir sin caché y reiniciar
./scripts/prod.sh rebuild frontend   # reconstruir sin caché y reiniciar

# ── Observabilidad ─────────────────────────────────────────
./scripts/prod.sh logs               # logs en tiempo real (todos)
./scripts/prod.sh logs <servicio>    # logs de un servicio específico

# ── Base de datos ──────────────────────────────────────────
./scripts/prod.sh migrate            # aplicar migraciones Alembic
./scripts/prod.sh backup             # backup manual de BD
./scripts/prod.sh reset-db           # reset completo (requiere ALLOW_DB_RESET=true)

# ── Depuración ─────────────────────────────────────────────
./scripts/prod.sh shell              # shell en el backend
./scripts/prod.sh shell <servicio>   # shell en otro servicio
./scripts/prod.sh test               # ejecutar tests del backend
```

**URLs de acceso** (reemplazar con la IP del servidor):

| URL | Descripción |
|-----|-------------|
| `https://192.168.1.100` | Aplicación |
| `https://192.168.1.100/stats` | Dashboard público |
| `https://192.168.1.100/api/docs` | Documentación API |
| `https://192.168.1.100/api/health` | Health check |

**Credenciales iniciales:** definidas en `INITIAL_ADMIN_*` del `.env`.

---

## Desarrollo (hot-reload y herramientas locales)

En `docker-compose.yml`, descomentar los bloques marcados con `# [DEV]`.

### Hot-reload del backend

```yaml
backend:
  volumes:
    - ./logs/backend:/app/logs
    - ./backend:/app          # ← descomentar
  # command: >                # ← descomentar todo el bloque
  #   uvicorn app.main:app
  #   --host 0.0.0.0 --port 8000
  #   --reload --log-level debug
```

### Exponer puertos para herramientas locales

```yaml
backend:   ports: ["8000:8000"]   # Postman, curl, /api/docs directo
postgres:  ports: ["5432:5432"]   # TablePlus, DBeaver
minio:     ports: ["9000:9000"]   # API MinIO
```

Después de cualquier cambio en `docker-compose.yml`:

```bash
./scripts/prod.sh restart <servicio>
```

### Migraciones de base de datos

```bash
./scripts/prod.sh shell backend
# dentro del contenedor:
alembic revision --autogenerate -m "descripcion_del_cambio"
exit
./scripts/prod.sh migrate
```

---

## Operaciones frecuentes

### Logs en disco

```bash
tail -f logs/backend/app.log       # actividad general
tail -f logs/backend/errors.log    # solo errores
tail -f logs/nginx/access.log      # requests HTTP
```

Estructura de logs (rotación automática: 10 MB máx, 7 copias):

```
logs/
├── nginx/
│   ├── access.log
│   └── error.log
└── backend/
    ├── app.log
    ├── errors.log
    ├── access.log
    ├── celery_worker.log
    └── celery_tasks.log
```

### Backup y restauración

```bash
# Backup manual
./scripts/prod.sh backup

# Automático con cron (2 AM diario)
crontab -e
# Agregar:
0 2 * * * /ruta/ubpd-app/scripts/backup.sh >> /var/log/ubpd-backup.log 2>&1

# Restaurar
gunzip -c backups/ubpd_db_YYYYMMDD_HHMMSS.sql.gz | \
  docker compose exec -T postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
```

### Crear administrador adicional

```bash
./scripts/prod.sh shell backend
# dentro:
python scripts/create_admin.py \
  --username nuevo_admin \
  --password ContraseñaSegura! \
  --email correo@ubpd.gov.co \
  --nombre "Nombre Completo"
```

### Consola MinIO (SSH tunnel)

```bash
ssh -L 9001:localhost:9001 usuario@192.168.1.100
# Abrir en el navegador local: http://localhost:9001
```

### Recálculo forzado de estadísticas

```bash
./scripts/prod.sh restart celery
./scripts/prod.sh restart celery-beat
```

### Reset de base de datos (solo desarrollo)

```bash
# 1. Habilitar en .env:
ALLOW_DB_RESET=true

# 2. Ejecutar (pide confirmación escribiendo "CONFIRMAR"):
./scripts/prod.sh reset-db

# 3. Deshabilitar después de usar:
ALLOW_DB_RESET=false
```

### Actualizar el sistema

```bash
# Reconstruir solo los servicios afectados
./scripts/prod.sh rebuild backend
./scripts/prod.sh rebuild frontend

# Aplicar migraciones si las hay
./scripts/prod.sh migrate
```

---

## IP estática en Ubuntu (recomendado)

```yaml
# /etc/netplan/00-installer-config.yaml
network:
  ethernets:
    ens3:
      dhcp4: no
      addresses: [192.168.1.100/24]
      gateway4: 192.168.1.1
      nameservers:
        addresses: [192.168.1.1]
  version: 2
```

```bash
sudo netplan apply
```
