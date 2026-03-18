# UBPD — Ejecución, Despliegue y Manual de Usuario

> **Ver también:** [`CONFIGURACION.md`](CONFIGURACION.md) — configuración inicial, variables de entorno y certificados.

---

## Tabla de Contenidos

1. [Levantar en Intranet (Docker)](#levantar-en-intranet-docker)
2. [Desarrollo Local (sin Docker)](#desarrollo-local-sin-docker)
3. [Despliegue sin Internet (Air-Gapped)](#despliegue-sin-internet-air-gapped)
4. [Ejecutar Tests](#ejecutar-tests)
5. [Manual de Usuario](#manual-de-usuario)
6. [Operaciones Frecuentes](#operaciones-frecuentes)

---

## Levantar en Intranet (Docker)

> Prerequisito: completar [`CONFIGURACION.md`](CONFIGURACION.md) (SSL + `.env`).

```bash
# Construir imágenes (requiere internet en la máquina de build)
docker compose build

# Levantar todos los servicios en segundo plano
docker compose up -d

# Verificar que todos estén corriendo
docker compose ps
```

**Salida esperada:**
```
NAME               STATUS          PORTS
ubpd_nginx         running         0.0.0.0:80->80, 0.0.0.0:443->443
ubpd_frontend      running
ubpd_backend       running
ubpd_celery        running
ubpd_celery_beat   running
ubpd_postgres      running
ubpd_redis         running
ubpd_minio         running
```

**URLs de acceso** (reemplazar con la IP del servidor):

| URL | Descripción | Requiere auth |
|-----|-------------|---------------|
| `https://192.168.1.100` | Aplicación principal | Sí (según rol) |
| `https://192.168.1.100/stats` | Dashboard público | No |
| `https://192.168.1.100/api/docs` | Documentación API | No |
| `https://192.168.1.100/api/health` | Estado del sistema | No |

**Primer acceso:** usar las credenciales `INITIAL_ADMIN_*` del `.env`. Cambiar contraseña al ingresar.

### Comandos de gestión

```bash
# Detener todos los servicios (preserva datos)
docker compose down

# Reiniciar un servicio (útil tras cambiar .env)
docker compose restart backend

# Ver logs en tiempo real de todos los servicios
docker compose logs -f

# Ver logs de un servicio específico
docker compose logs -f backend
docker compose logs -f celery

# Ver solo errores de los últimas 2 horas
docker compose logs --since 2h backend | grep -i "error\|exception"
```

### Ver logs en disco (fuera del contenedor)

```bash
# Logs de Nginx
tail -f logs/nginx/access.log
tail -f logs/nginx/error.log

# Logs del backend
tail -f logs/backend/app.log
tail -f logs/backend/errors.log     # solo errores
tail -f logs/backend/access.log     # requests HTTP
tail -f logs/backend/celery_worker.log
tail -f logs/backend/celery_tasks.log

# Buscar errores en las últimas 500 líneas
grep -i "error\|exception" logs/backend/app.log | tail -50
```

---

## Desarrollo Local (sin Docker)

> Prerequisito: tener PostgreSQL, Redis y MinIO corriendo localmente (o como contenedores individuales).

### Backend

```bash
cd backend

python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# Variables de entorno mínimas para desarrollo
export DATABASE_URL="postgresql+asyncpg://ubpd:password@localhost:5432/ubpd_dev"
export REDIS_URL="redis://localhost:6379/0"
export SECRET_KEY="clave-local-solo-desarrollo"
export APP_ENV="development"
export LOG_DIR="./logs/backend"
export LOG_LEVEL="DEBUG"
export MINIO_ENDPOINT="localhost:9000"
export MINIO_ACCESS_KEY="minioadmin"
export MINIO_SECRET_KEY="minioadmin"
export MINIO_USE_SSL="false"

# Aplicar migraciones
alembic upgrade head

# Servidor con auto-reload
uvicorn app.main:app --reload --port 8000
```

En terminales separadas:

```bash
# Worker Celery
celery -A app.celery_app worker --loglevel=debug

# Scheduler Beat
celery -A app.celery_app beat --loglevel=info
```

### Frontend

```bash
cd frontend

npm install
npm run dev       # http://localhost:5173
```

El proxy `/api → http://localhost:8000` está preconfigurado en `vite.config.ts`.

---

## Despliegue sin Internet (Air-Gapped)

Cuando el servidor de producción **no tiene acceso a internet**.

### En la máquina con internet (una sola vez)

```bash
chmod +x scripts/save-docker-images.sh
./scripts/save-docker-images.sh
# Produce: docker-images-ubpd-YYYYMMDD.tar.gz (~1-2 GB)
```

### Transferir al servidor

```bash
# Por red local
scp docker-images-ubpd-*.tar.gz usuario@192.168.1.100:/opt/ubpd/

# O copiar junto con la carpeta ubpd-app/ en un USB
```

### En el servidor sin internet

```bash
cd /opt/ubpd

# Importar imágenes Docker
chmod +x ubpd-app/scripts/load-docker-images.sh
./ubpd-app/scripts/load-docker-images.sh

cd ubpd-app

# Configurar
./scripts/generate-ssl.sh 192.168.1.100
cp .env.example .env
nano .env                # editar variables obligatorias

# Levantar (sin build, usa imágenes importadas)
docker compose up -d
docker compose ps
```

---

## Ejecutar Tests

```bash
cd backend

pip install -r requirements-test.txt

# Suite completa
pytest

# Solo tests unitarios (sin servicios externos)
pytest tests/test_auth_service.py tests/test_template_parser.py \
       tests/test_calculators.py tests/test_dependencies.py -v

# Tests de integración de routers
pytest tests/test_auth_router.py tests/test_stats_router.py -v

# Con reporte de cobertura
pytest --cov=app --cov-report=term-missing
```

| Archivo | Qué verifica |
|---------|-------------|
| `test_auth_service.py` | Bcrypt, JWT, autenticación de usuarios |
| `test_template_parser.py` | Markdown → JSON schema, completitud |
| `test_calculators.py` | Fórmulas: simple, ponderado, conteo |
| `test_dependencies.py` | Guards JWT, RBAC, extracción de IP |
| `test_auth_router.py` | `POST /api/auth/login`, refresh, logout, cambio de contraseña |
| `test_stats_router.py` | `GET /api/stats/*`, health check |

---

## Manual de Usuario

### Roles del sistema

| Rol | Acceso |
|-----|--------|
| **Administrador** | Gestión completa: usuarios, dependencias, plantillas, auditoría |
| **Validador** | Revisar, aprobar o devolver formularios enviados |
| **Usuario de Dependencia** | Diligenciar y enviar formularios de su dependencia |
| **Público** | Ver estadísticas sin autenticación |

---

### Administrador

**Acceso:** `https://IP_SERVIDOR` → credenciales admin

#### Gestión de usuarios
- Menú → **Usuarios** → botón **Nuevo usuario**
- Asignar rol: `admin`, `validator` o `dependency_user`
- Para usuarios de dependencia, seleccionar la dependencia asignada
- **Desactivar** usuario: ícono en la fila (no elimina, preserva historial)

#### Gestión de plantillas
- Menú → **Plantillas** → **Nueva plantilla**
- Usar el editor Markdown para definir los campos:

```
| campo          | tipo     | bloqueado | default | requerido | opciones                     |
|----------------|----------|-----------|---------|-----------|------------------------------|
| nombre_victima | text     | no        |         | si        |                              |
| departamento   | select   | no        |         | si        | Cundinamarca,Antioquia,Valle |
| fecha_evento   | date     | no        |         | si        |                              |
| observaciones  | textarea | no        |         | no        |                              |
| numero_caso    | number   | si        | 0       | no        |                              |
```

- **Tipos:** `text`, `number`, `date`, `select`, `textarea`
- **`bloqueado: si`** → campo de solo lectura (relleno automático)
- **`opciones`** → solo para `select`, separar con coma

#### Monitoreo
- **Pipeline** → semáforo de estado del procesamiento (verde=ok, rojo=error)
  - Se actualiza cada 30 segundos automáticamente
- **Auditoría** → log de todas las acciones del sistema con filtros por usuario, acción y fecha

---

### Validador

#### Bandeja de entrada
1. Menú → **Bandeja** — lista de formularios pendientes
2. El contador naranja indica la cantidad de formularios sin revisar
3. Filtrar por rango de fechas si hay muchos pendientes

#### Revisar un formulario
1. Clic en **Revisar** → pantalla dividida:
   - **Izquierda (60%):** datos del formulario y archivos adjuntos
   - **Derecha (40%):** panel de dictamen
2. Hacer clic en miniaturas para ver imágenes; en íconos para descargar PDFs/DOCX
3. Tomar decisión:
   - **Aprobar** (verde) → el formulario entra al cálculo de estadísticas
   - **Devolver** (naranja) → escribir comentario obligatorio indicando qué corregir

#### Historial
- Menú → **Historial** → formularios ya revisados con filtros por estado y fecha

---

### Usuario de Dependencia

#### Diligenciar un nuevo formulario
1. Menú → **Galería** → seleccionar plantilla → **Diligenciar**
2. Completar todos los campos marcados con `*` (requeridos)
3. Adjuntar archivos si corresponde (PDF, JPEG, PNG, DOCX — máx. 50 MB por archivo)
4. Opciones:
   - **Guardar** → queda en borrador (editable)
   - **Enviar para revisión** → pasa al validador

> El sistema guarda automáticamente cada 2 minutos mientras se edita.

#### Formulario devuelto
1. Menú → **Mis Formularios** → pestaña **Devueltos**
2. Leer el comentario del validador (banner naranja en la parte superior)
3. Hacer las correcciones indicadas
4. **Reenviar para revisión**

#### Estados de los formularios

| Estado | Color | Significado |
|--------|-------|-------------|
| Borrador | Gris | En edición, no enviado |
| Pendiente | Amarillo | En espera de revisión |
| Aprobado | Verde | Validado, incluido en estadísticas |
| Devuelto | Naranja | Requiere corrección |

---

### Portal Público de Estadísticas

URL: `https://IP_SERVIDOR/stats` — sin autenticación requerida.

| Nivel | Qué muestra | Navegación |
|-------|-------------|------------|
| **Nivel 1** | Gauge por indicador (completitud global) | Clic en gauge → Nivel 2 |
| **Nivel 2** | Gauges por plantilla del indicador | Clic en gauge → Nivel 3 |
| **Nivel 3** | Tabla de registros aprobados | Botón exportar → Excel |

- Filtro de fechas disponible en todos los niveles (presets: última semana, mes, año)
- El dashboard refleja solo formularios **aprobados**

---

## Operaciones Frecuentes

### Backup

```bash
chmod +x scripts/backup.sh
./scripts/backup.sh
# Genera backups en ./backups/ con retención de 30 días
```

Automatizar con cron (backup diario a las 2 AM):
```bash
crontab -e
# Agregar:
0 2 * * * /ruta/completa/ubpd-app/scripts/backup.sh >> /var/log/ubpd-backup.log 2>&1
```

### Restaurar backup de base de datos

```bash
# Listar backups disponibles
ls -lh backups/

# Restaurar
gunzip -c backups/ubpd_db_YYYYMMDD_HHMMSS.sql.gz | \
  docker compose exec -T postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
```

### Crear administrador adicional

```bash
docker compose exec backend python scripts/create_admin.py \
  --username nuevo_admin \
  --password ContraseñaSegura! \
  --email correo@ubpd.gov.co \
  --nombre "Nombre Completo"
```

### Aplicar migraciones de base de datos

```bash
docker compose exec backend alembic upgrade head
```

### Forzar recálculo de estadísticas

```bash
docker compose restart celery celery-beat
```

### Acceder a la consola de MinIO

La consola MinIO solo escucha en `localhost` del servidor:

```bash
# SSH tunnel desde la máquina del administrador
ssh -L 9001:localhost:9001 usuario@192.168.1.100
# Luego abrir: http://localhost:9001
# Credenciales: MINIO_ROOT_USER / MINIO_ROOT_PASSWORD del .env
```

### Ver logs de errores recientes

```bash
# Errores del backend (archivo en disco)
tail -100 logs/backend/errors.log

# Errores de Nginx
tail -100 logs/nginx/error.log

# Logs en tiempo real de todos los servicios
docker compose logs -f --tail=50

# Buscar un error específico
grep "ValidationError\|500\|CRITICAL" logs/backend/app.log | tail -20
```
