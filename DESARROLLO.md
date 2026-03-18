# UBPD — Guía de Trabajo y Desarrollo

Todo corre en Docker con un único `docker-compose.yml`.
El script `./scripts/prod.sh` es la única herramienta para gestionar el sistema.

---

## Tabla de Contenidos

1. [Ciclo completo de inicio](#1-ciclo-completo-de-inicio)
2. [Arrancar y verificar](#2-arrancar-y-verificar)
3. [Trabajar en el backend](#3-trabajar-en-el-backend)
4. [Trabajar en el frontend](#4-trabajar-en-el-frontend)
5. [Aplicar migraciones de BD](#5-aplicar-migraciones-de-bd)
6. [Detener y reiniciar](#6-detener-y-reiniciar)
7. [Reset de base de datos](#7-reset-de-base-de-datos)
8. [Referencia rápida de comandos](#8-referencia-rápida-de-comandos)

---

## 1. Ciclo completo de inicio

**Solo la primera vez** en una máquina nueva:

```bash
# Dar permisos a los scripts
chmod +x scripts/*.sh

# Instalación: verifica Docker, crea directorios, copia .env, genera SSL
./scripts/install.sh
```

**Generar la configuración del `.env` automáticamente:**

```bash
./scripts/generar-env.sh
```

Este script:
- Detecta la IP local de la máquina automáticamente
- Genera `SECRET_KEY` (64 bytes hex), `POSTGRES_PASSWORD`, `REDIS_PASSWORD` y `MINIO_ROOT_PASSWORD` con valores criptográficamente seguros
- Pregunta si escribe los valores directamente en `.env`

Modos disponibles:

| Modo | Comando | Efecto |
|------|---------|--------|
| Interactivo | `./scripts/generar-env.sh` | Muestra valores, pregunta si escribe |
| Escritura directa | `./scripts/generar-env.sh --write` | Escribe en `.env` sin preguntar |
| Solo mostrar | `./scripts/generar-env.sh --show` | Muestra valores, nunca escribe |

**Editar `.env` para los valores que el script no genera:**

```bash
nano .env
```

Campos que aún debes completar manualmente:

| Variable | Por qué |
|----------|---------|
| `INITIAL_ADMIN_PASSWORD` | Contraseña del primer usuario admin |
| `INITIAL_ADMIN_EMAIL` | Email real del administrador |

**Construir imágenes y levantar** (solo la primera vez o tras cambios en `requirements.txt` / `package.json`):

```bash
./scripts/prod.sh build
./scripts/prod.sh start
./scripts/prod.sh ps        # verificar que todo esté running
```

---

## 2. Arrancar y verificar

```bash
./scripts/prod.sh start
./scripts/prod.sh ps
```

Salida esperada — todos los servicios en `running`:
```
NAME               STATUS
ubpd_nginx         running
ubpd_frontend      running
ubpd_backend       running
ubpd_celery        running
ubpd_celery_beat   running
ubpd_postgres      running
ubpd_redis         running
ubpd_minio         running
```

URLs disponibles (reemplazar con tu IP):
- Aplicación: `https://192.168.1.100`
- API Docs: `https://192.168.1.100/api/docs`
- Health check: `https://192.168.1.100/api/health`

---

## 3. Trabajar en el backend

### Sin hot-reload (comportamiento por defecto)

Cada cambio en el código Python requiere reconstruir la imagen:

```bash
./scripts/prod.sh rebuild backend
# reconstruye la imagen del backend y reinicia el contenedor
```

Usar cuando:
- Cambiaste lógica en `app/routers/`, `app/services/`, `app/models/`, etc.
- Cambiaste cualquier archivo `.py`

### Con hot-reload (cambios se aplican al instante)

Editar `docker-compose.yml` y descomentar los bloques marcados `# [DEV]` en el servicio `backend`:

```yaml
    volumes:
      - ./logs/backend:/app/logs
      - ./backend:/app          # ← descomentar (monta el código)

    # command: >                # ← descomentar todo el bloque
    #   uvicorn app.main:app
    #   --host 0.0.0.0 --port 8000
    #   --reload --log-level debug
```

Luego reiniciar el backend:
```bash
./scripts/prod.sh restart backend
```

A partir de ahí, **cada vez que guardes un archivo `.py`** uvicorn se reinicia solo en el contenedor.

**Para volver al modo normal** (sin hot-reload), volver a comentar esas líneas y:
```bash
./scripts/prod.sh rebuild backend
```

### Actualizar dependencias Python

Si agregaste paquetes a `requirements.txt`:
```bash
./scripts/prod.sh rebuild backend
# también rebuild celery si el paquete lo usa
./scripts/prod.sh rebuild celery
```

### Ver logs del backend en tiempo real

```bash
./scripts/prod.sh logs backend         # salida del contenedor
tail -f logs/backend/app.log           # archivo en disco (INFO+)
tail -f logs/backend/errors.log        # solo errores
```

### Abrir shell para depurar

```bash
./scripts/prod.sh shell backend
# dentro del contenedor:
python -c "from app.config import settings; print(settings.APP_ENV)"
alembic current
pytest tests/test_auth_service.py -v
```

---

## 4. Trabajar en el frontend

El frontend se compila como build estático y lo sirve Nginx. No tiene hot-reload en este entorno.

### Aplicar cambios en el código Vue

Después de modificar archivos en `frontend/src/`:

```bash
./scripts/prod.sh rebuild frontend
```

Esto:
1. Reconstruye la imagen (`npm ci` + `npm run build`)
2. Reinicia el contenedor frontend
3. Nginx empieza a servir el build nuevo

### Cuándo hacer `rebuild` vs `restart`

| Situación | Comando |
|-----------|---------|
| Cambios en código Vue/TypeScript/CSS | `rebuild frontend` |
| Nuevas dependencias en `package.json` | `rebuild frontend` |
| Solo reiniciar el servidor nginx del frontend | `restart frontend` |
| Cambios en `tailwind.config.js` o `vite.config.ts` | `rebuild frontend` |

### Actualizar dependencias npm

Si agregaste paquetes a `package.json`:
```bash
# Instalar localmente primero para actualizar package-lock.json
cd frontend && npm install && cd ..

# Luego reconstruir la imagen
./scripts/prod.sh rebuild frontend
```

> **Nota:** en red intranet sin internet, asegurarse de que los paquetes nuevos
> estén disponibles offline o que el build se haga en una máquina con internet
> y luego se transfieran las imágenes (ver `scripts/save-docker-images.sh`).

---

## 5. Aplicar migraciones de BD

Cuando cambias modelos SQLAlchemy (`app/models/*.py`):

### Generar una nueva migración

```bash
./scripts/prod.sh shell backend
# dentro:
alembic revision --autogenerate -m "descripcion_del_cambio"
exit
```

Esto crea un archivo en `backend/alembic/versions/`.

### Aplicar la migración

```bash
./scripts/prod.sh migrate
```

### Verificar estado actual

```bash
./scripts/prod.sh shell backend
# dentro:
alembic current
alembic history
```

---

## 6. Detener y reiniciar

```bash
# Detener todos los contenedores (los datos se preservan en los volúmenes)
./scripts/prod.sh stop

# Volver a arrancar (usa las imágenes ya construidas, no rebuild)
./scripts/prod.sh start

# Reiniciar todos los servicios sin detener
./scripts/prod.sh restart

# Reiniciar un solo servicio
./scripts/prod.sh restart backend
./scripts/prod.sh restart celery
./scripts/prod.sh restart nginx
```

**Los datos no se pierden** al hacer `stop` / `start`. Los volúmenes Docker
(`ubpd_postgres_data`, `ubpd_minio_data`, `ubpd_redis_data`) persisten.

---

## 7. Reset de base de datos

Para empezar con la base de datos completamente limpia
(útil durante el desarrollo cuando necesitas probar desde cero).

### Paso 1 — Habilitar en `.env`

```bash
nano .env
# Cambiar:
ALLOW_DB_RESET=true
```

### Paso 2 — Ejecutar el reset

```bash
./scripts/prod.sh reset-db
```

El script pedirá confirmación escribiendo `CONFIRMAR`:

```
╔══════════════════════════════════════════════════════╗
║       ADVERTENCIA — OPERACIÓN DESTRUCTIVA            ║
║  Se ELIMINARÁN todos los datos de la base de datos.  ║
╚══════════════════════════════════════════════════════╝

Escribe CONFIRMAR para continuar: CONFIRMAR
```

El proceso:
1. Detiene backend y workers
2. Elimina el volumen `ubpd_postgres_data`
3. Levanta PostgreSQL limpio
4. Aplica todas las migraciones Alembic
5. Levanta el resto de servicios
6. El admin inicial se recrea automáticamente al arrancar

### Paso 3 — Deshabilitar después de usar

```bash
nano .env
# Volver a:
ALLOW_DB_RESET=false
```

> **Importante:** si `ALLOW_DB_RESET=false`, el comando `reset-db` falla con
> un error explicativo y **no toca ningún dato**.

---

## 8. Referencia rápida de comandos

```bash
# ── Configuración inicial ───────────────────────────────────
./scripts/generar-env.sh             # detectar IP + generar claves y contraseñas
./scripts/generar-env.sh --write     # igual, pero escribe en .env directamente
./scripts/generar-env.sh --show      # solo mostrar, sin escribir nada

# ── Ciclo de vida ──────────────────────────────────────────
./scripts/prod.sh start              # levantar
./scripts/prod.sh stop               # detener (datos preservados)
./scripts/prod.sh restart            # reiniciar todo
./scripts/prod.sh restart <servicio> # reiniciar uno solo
./scripts/prod.sh ps                 # estado + URLs

# ── Build / Rebuild ────────────────────────────────────────
./scripts/prod.sh build              # construir todas las imágenes
./scripts/prod.sh build backend      # construir solo el backend
./scripts/prod.sh build frontend     # construir solo el frontend
./scripts/prod.sh rebuild backend    # sin caché + reiniciar
./scripts/prod.sh rebuild frontend   # sin caché + reiniciar

# ── Observabilidad ─────────────────────────────────────────
./scripts/prod.sh logs               # logs en tiempo real (todos)
./scripts/prod.sh logs backend       # logs de un servicio
./scripts/prod.sh logs nginx         # logs de nginx
tail -f logs/backend/app.log         # archivo de log en disco
tail -f logs/backend/errors.log      # solo errores

# ── Base de datos ──────────────────────────────────────────
./scripts/prod.sh migrate            # aplicar migraciones Alembic
./scripts/prod.sh backup             # backup manual
./scripts/prod.sh reset-db           # reset completo (requiere ALLOW_DB_RESET=true)

# ── Depuración ─────────────────────────────────────────────
./scripts/prod.sh shell              # shell en backend
./scripts/prod.sh shell postgres     # shell en postgres
./scripts/prod.sh shell frontend     # shell en frontend
./scripts/prod.sh test               # ejecutar tests del backend
```

### Servicios disponibles para comandos con `[servicio]`

| Servicio | Descripción |
|----------|-------------|
| `nginx` | Reverse proxy y SSL |
| `frontend` | Build estático Vue.js |
| `backend` | API FastAPI |
| `celery` | Worker de tareas |
| `celery-beat` | Scheduler periódico |
| `postgres` | Base de datos |
| `redis` | Broker y caché |
| `minio` | Almacenamiento de archivos |
