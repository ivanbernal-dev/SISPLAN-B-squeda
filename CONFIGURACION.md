# UBPD — Configuración e Instalación

> **Ver también:** [`EJECUCION.md`](EJECUCION.md) — arrancar, operar y usar el sistema.

---

## Requisitos

| Componente | Versión mínima | Verificar |
|------------|----------------|-----------|
| Docker Engine | 24+ | `docker --version` |
| Docker Compose plugin | 2.20+ | `docker compose version` |
| OpenSSL | 1.1+ | `openssl version` |
| RAM | 4 GB | — |
| Disco libre | 20 GB | — |

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

Después, **editar `.env`**:

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
REDIS_PASSWORD=contraseña_segura
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
| `STATS_RECALC_INTERVAL_SECONDS` | 600 | Frecuencia de recálculo |
| `APP_ENV` | production | `development` activa logging SQL |

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

---

## Ajustes de trabajo en el `docker-compose.yml`

El archivo contiene bloques comentados marcados con `# [DEV]` para activar
funcionalidades durante el trabajo en el código. Descomentar y reiniciar el servicio.

### Hot-reload del backend (cambios sin rebuild)

En `docker-compose.yml`, dentro del servicio `backend`:

```yaml
    volumes:
      - ./logs/backend:/app/logs
      # [DEV] Descomentar para hot-reload:
      - ./backend:/app                    # ← descomentar esta línea

    # [DEV] Descomentar para hot-reload:
    # command: >
    #   uvicorn app.main:app
    #   --host 0.0.0.0 --port 8000
    #   --reload --log-level debug
```

Después de descomentar:
```bash
./scripts/prod.sh restart backend
```

### Exponer puertos para herramientas locales

```yaml
# Acceso directo a la API (Postman, curl, etc.)
backend:
  ports:
    - "8000:8000"    # ← descomentar

# Acceso a PostgreSQL desde TablePlus / DBeaver
postgres:
  ports:
    - "5432:5432"    # ← descomentar

# API de MinIO accesible desde el host
minio:
  ports:
    - "9000:9000"    # ← descomentar
```

Después de cualquier cambio en `docker-compose.yml`:
```bash
./scripts/prod.sh restart          # reinicia todos los servicios afectados
```

---

## Logs del sistema

Los logs se guardan fuera del contenedor en `./logs/`:

```
logs/
├── nginx/
│   ├── access.log        ← Requests HTTP recibidos por Nginx
│   └── error.log         ← Errores de Nginx
└── backend/
    ├── app.log           ← Actividad general del backend (INFO+)
    ├── errors.log        ← Solo errores (ERROR+)
    ├── access.log        ← Requests HTTP a FastAPI
    ├── celery_worker.log ← Worker de tareas
    └── celery_tasks.log  ← Ejecución de tareas individuales
```

Rotación automática: 10 MB máx, 7 copias de respaldo.
