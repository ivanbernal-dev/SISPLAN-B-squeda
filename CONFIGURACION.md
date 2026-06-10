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

---

## Instalación inicial (una sola vez)

```bash
chmod +x scripts/*.sh
./scripts/install.sh
```

El script hace automáticamente:
1. Verifica Docker y docker compose
2. Crea `logs/nginx/`, `logs/backend/`, `postgres/init/`, `backups/`
3. Copia `.env.example` → `.env`

El acceso a la aplicación es por **HTTP** (puerto **80**); no se genera certificado en la instalación.

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

# Base de datos
POSTGRES_USER=ubpd_user
POSTGRES_PASSWORD=<contraseña_robusta_min_16>
POSTGRES_DB=ubpd

# MinIO (almacenamiento de archivos)
MINIO_ROOT_USER=ubpd_minio_admin
MINIO_ROOT_PASSWORD=<contraseña_min_12>
MINIO_BUCKET_NAME=ubpd-formularios

# Valkey (Redis) — caché y colas Celery
VALKEY_PASSWORD=<contraseña_robusta>

# Seguridad
# Generar con: python3 -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=<cadena_aleatoria_64_caracteres>

# Admin inicial (se crea automáticamente en el primer arranque)
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=<contraseña_admin>
INITIAL_ADMIN_EMAIL=admin@ubpd.gov.co
INITIAL_ADMIN_NOMBRE=Administrador UBPD

# CORS — agregar TODA IP/dominio desde el que se acceda
CORS_ORIGINS=http://127.0.0.1,http://localhost,http://192.168.1.100

# PIN para autorizar comandos destructivos (reset-fresh, destroy)
# 4-8 dígitos. Sin esta variable, esos comandos se niegan a ejecutar.
RESET_PIN=<pin_numerico>
```

### Generar secretos seguros

Linux / macOS:
```bash
openssl rand -hex 32         # JWT_SECRET_KEY (64 caracteres)
openssl rand -base64 24      # contraseñas robustas
```

Windows (PowerShell):
```powershell
[Convert]::ToBase64String((New-Object byte[] 24 | % { Get-Random -Max 255 }))
```

### Logging

```bash
LOG_DIR=/app/logs   # se monta en ./logs/backend del host
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
| `RESET_PIN` | _(sin valor)_ | Obligatorio para `reset-fresh` y `destroy`. Sin él, esos comandos abortan. |

---

## HTTPS / certificados (opcional, no activo)

En esta versión Nginx solo escucha **HTTP**. El script `scripts/generate-ssl.sh` y la carpeta `nginx/certs/` pueden usarse en el futuro si se vuelve a configurar TLS en `nginx/conf.d/` y en `docker-compose.yml`.

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
./scripts/prod.sh restart [svc]      # reinicia y recrea contenedor (aplica imagen nueva)
./scripts/prod.sh status             # estado de contenedores + URLs + rutas de logs

# ── Build (construye Y aplica) ─────────────────────────────
./scripts/prod.sh build              # build + up -d (despliega imagen nueva)
./scripts/prod.sh build backend      # solo el backend
./scripts/prod.sh build frontend     # solo el frontend
./scripts/prod.sh rebuild [svc]      # igual que build pero sin caché de Docker

# ── Observabilidad ─────────────────────────────────────────
./scripts/prod.sh logs               # logs en tiempo real (todos)
./scripts/prod.sh logs <servicio>    # logs de un servicio específico

# ── Base de datos ──────────────────────────────────────────
./scripts/prod.sh migrate            # aplicar migraciones Alembic
./scripts/prod.sh backup             # backup manual de BD → ./backups/

# ── Pipeline de indicadores (KPIs) ─────────────────────────
./scripts/prod.sh pipeline-reset     # restaura el pipeline al seed oficial + ejecuta
                                     # (úsalo si los velocímetros no se actualizan)
./scripts/prod.sh pipeline-sync run  # carga scripts/pai_2026/pipeline_pai.py + ejecuta

# ── Comandos destructivos (requieren RESET_PIN en .env) ────
./scripts/prod.sh reset-db           # eliminar y recrear BD (necesita ALLOW_DB_RESET=true)
./scripts/prod.sh reset-fresh        # reset TOTAL a instalación limpia (frase + PIN)
./scripts/prod.sh destroy            # destruye contenedores+imagenes+volumenes (frase + PIN)
./scripts/prod.sh destroy all        # incluso imágenes 3rd party (postgres, nginx, ...)

# ── Depuración ─────────────────────────────────────────────
./scripts/prod.sh shell              # shell en el backend
./scripts/prod.sh shell <servicio>   # shell en otro servicio
./scripts/prod.sh test               # ejecutar tests del backend
./scripts/prod.sh help               # lista completa de comandos
```

**URLs de acceso** (reemplazar con la IP del servidor):

| URL | Descripción |
|-----|-------------|
| `http://192.168.1.100` | Aplicación |
| `http://192.168.1.100/estadisticas` | Portal público de indicadores (sin login) |
| `http://192.168.1.100/api/docs` | Documentación API |
| `http://192.168.1.100/api/health` | Health check |

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
