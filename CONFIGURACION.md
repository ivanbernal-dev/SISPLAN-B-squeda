# UBPD — Configuración e Instalación

Guía de configuración inicial, variables de entorno, certificados SSL y preparación
del entorno antes de levantar la aplicación.

> **Ver también:** [`EJECUCION.md`](EJECUCION.md) — cómo correr, desplegar y usar el sistema.

---

## Requisitos

| Componente | Versión mínima | Verificar |
|------------|----------------|-----------|
| Docker Engine | 24+ | `docker --version` |
| Docker Compose plugin | 2.20+ | `docker compose version` |
| OpenSSL | 1.1+ | `openssl version` |
| RAM del servidor | 4 GB | — |
| Disco libre | 20 GB | — |

Para **desarrollo local** (sin Docker) se necesita además:
- Python 3.11+
- Node.js 20+ y npm
- PostgreSQL 15+, Redis 7+, MinIO (o servicios levantados en Docker de forma separada)

---

## Estructura de directorios relevante

```
ubpd-app/
├── .env.example         ← plantilla de variables de entorno
├── .env                 ← ¡crear desde .env.example, NO commitear!
├── docker-compose.yml
├── nginx/
│   ├── certs/           ← certificados SSL (generar con el script)
│   ├── nginx.conf
│   └── conf.d/ubpd.conf
├── logs/                ← logs del sistema (creado automáticamente)
│   ├── nginx/           ← access.log, error.log de Nginx
│   └── backend/         ← app.log, errors.log, access.log, celery_*.log
├── backend/
└── frontend/
```

---

## Paso 1 — Generar certificado SSL autofirmado

```bash
chmod +x scripts/generate-ssl.sh

# Reemplazar con la IP real del servidor en la intranet
./scripts/generate-ssl.sh 192.168.1.100
```

Genera:
- `nginx/certs/server.crt`
- `nginx/certs/server.key`

### Instalar el certificado en clientes Windows

Para evitar la advertencia de seguridad del navegador:

1. Copiar `nginx/certs/server.crt` al equipo cliente
2. Doble clic → **Instalar certificado** → Equipo local
3. **Examinar** → "Entidades de certificación raíz de confianza"
4. Aceptar y reiniciar el navegador

---

## Paso 2 — Crear y configurar el archivo `.env`

```bash
cp .env.example .env
```

### Variables obligatorias a cambiar

```bash
# ── Servidor ──────────────────────────────────────────────────
SERVER_IP=192.168.1.100          # IP real del servidor en la intranet

# ── Seguridad ─────────────────────────────────────────────────
# Generar con: python3 -c "import secrets; print(secrets.token_hex(64))"
SECRET_KEY=CAMBIAR_POR_CLAVE_LARGA_ALEATORIA

# ── Base de datos ──────────────────────────────────────────────
POSTGRES_PASSWORD=contraseña_segura_postgres

# ── Redis ──────────────────────────────────────────────────────
REDIS_PASSWORD=contraseña_segura_redis

# ── MinIO ──────────────────────────────────────────────────────
MINIO_ROOT_PASSWORD=contraseña_minio_8chars   # mínimo 8 caracteres

# ── Administrador inicial ──────────────────────────────────────
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=Admin@UBPD2024!
INITIAL_ADMIN_EMAIL=admin@ubpd.gov.co

# ── CORS (ajustar con la IP del servidor) ──────────────────────
CORS_ORIGINS=https://192.168.1.100,http://localhost:5173,http://localhost:3000
```

### Variables de logging

```bash
# Directorio de logs — en Docker usa /app/logs (volumen montado en ./logs/backend)
# En desarrollo local cambiar a: ./logs/backend
LOG_DIR=/app/logs

# Nivel: DEBUG (dev) | INFO (producción)
LOG_LEVEL=INFO
```

### Variables opcionales

| Variable | Por defecto | Descripción |
|----------|-------------|-------------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Vida del JWT access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Vida del refresh token |
| `MAX_UPLOAD_MB` | 50 | Tamaño máximo de archivos adjuntos |
| `STATS_RECALC_INTERVAL_SECONDS` | 600 | Frecuencia de recálculo de estadísticas |
| `APP_ENV` | production | `development` activa debug y logs SQL |

---

## Paso 3 — Verificar la configuración

```bash
# Sintaxis de docker-compose válida
docker compose config --quiet && echo "OK"

# Variables de entorno cargadas correctamente
docker compose config | grep -E "SECRET_KEY|POSTGRES_PASSWORD|SERVER_IP"
```

---

## Configuración de desarrollo local (sin Docker)

### Backend

Crear `.env` de desarrollo en `backend/`:

```bash
# backend/.env.dev  (o exportar las variables en la terminal)
DATABASE_URL=postgresql+asyncpg://ubpd:password@localhost:5432/ubpd_dev
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_USE_SSL=false
SECRET_KEY=clave-local-desarrollo
APP_ENV=development
LOG_DIR=./logs/backend
LOG_LEVEL=DEBUG
```

### Frontend

El proxy `/api → http://localhost:8000` ya está configurado en `frontend/vite.config.ts`.
No requiere configuración adicional.

---

## Archivos de log generados

| Archivo | Ubicación en host | Contenido |
|---------|-------------------|-----------|
| `access.log` | `logs/nginx/access.log` | Requests HTTP a Nginx |
| `error.log` | `logs/nginx/error.log` | Errores de Nginx |
| `app.log` | `logs/backend/app.log` | Todo INFO+ del backend |
| `errors.log` | `logs/backend/errors.log` | Solo ERROR+ del backend |
| `access.log` | `logs/backend/access.log` | Requests HTTP a FastAPI |
| `celery_worker.log` | `logs/backend/celery_worker.log` | Worker de tareas |
| `celery_tasks.log` | `logs/backend/celery_tasks.log` | Ejecución de tareas |

Los archivos rotan automáticamente (10 MB máx, 7 backups). Los logs de Nginx rotan
con la configuración por defecto del contenedor (`logrotate`).
