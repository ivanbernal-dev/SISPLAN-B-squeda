# UBPD — Sistema de Gestión de Formularios

**Unidad de Búsqueda de Personas Dadas por Desaparecidas**

Sistema para diligenciar, validar y publicar estadísticas de formularios de la Línea Estratégica No. 1.
Diseñado para funcionar exclusivamente en **red intranet** (sin acceso a internet).

---

## Tabla de Contenidos

1. [Requisitos](#requisitos)
2. [Configuración Inicial](#configuración-inicial)
3. [Levantar en Intranet (Docker)](#levantar-en-intranet-docker)
4. [Transferir sin Internet (Air-Gapped)](#transferir-sin-internet-air-gapped)
5. [Desarrollo Local (sin Docker)](#desarrollo-local-sin-docker)
6. [Ejecutar Tests](#ejecutar-tests)
7. [Manual de Usuario](#manual-de-usuario)
8. [Operaciones Frecuentes](#operaciones-frecuentes)

---

## Requisitos

| Componente | Versión | Verificar |
|------------|---------|-----------|
| Docker Engine | 24+ | `docker --version` |
| Docker Compose | 2.20+ (plugin) | `docker compose version` |
| OpenSSL | 1.1+ | `openssl version` |
| RAM | 4 GB mínimo | — |
| Disco libre | 20 GB | — |

> Para **desarrollo local** sin Docker se necesita además: Python 3.11+, Node.js 20+, PostgreSQL 15+, Redis 7+.

---

## Configuración Inicial

### 1. Generar certificado SSL

```bash
chmod +x scripts/generate-ssl.sh

# Reemplazar con la IP real del servidor en la intranet
./scripts/generate-ssl.sh 192.168.1.100
```

Genera `nginx/certs/server.crt` y `nginx/certs/server.key`.

### 2. Crear el archivo `.env`

```bash
cp .env.example .env
```

Editar `.env` y cambiar **obligatoriamente**:

```bash
# IP del servidor en la intranet
SERVER_IP=192.168.1.100

# Clave secreta JWT — generarla con:
# python3 -c "import secrets; print(secrets.token_hex(64))"
SECRET_KEY=CAMBIAR_POR_CLAVE_LARGA_ALEATORIA

# Contraseñas
POSTGRES_PASSWORD=contraseña_segura_postgres
REDIS_PASSWORD=contraseña_segura_redis
MINIO_ROOT_PASSWORD=contraseña_minio_8chars

# Credenciales del primer administrador
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=Admin@UBPD2024!
INITIAL_ADMIN_EMAIL=admin@ubpd.gov.co

# Origins CORS: ajustar con la IP real del servidor
CORS_ORIGINS=https://192.168.1.100,http://localhost:5173,http://localhost:3000
```

### 3. Instalar el certificado en los clientes Windows

Para que el navegador no muestre advertencia de seguridad:

1. Copiar `nginx/certs/server.crt` al equipo cliente
2. Doble clic → **Instalar certificado** → Equipo local
3. **Examinar** → "Entidades de certificación raíz de confianza"
4. Aceptar y reiniciar el navegador

---

## Levantar en Intranet (Docker)

```bash
# Primera vez: construir imágenes
# (esta operación requiere internet; ver sección Air-Gapped si no hay internet)
docker compose build

# Iniciar todos los servicios
docker compose up -d

# Verificar que todos estén corriendo
docker compose ps
```

**Salida esperada:**
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

**Acceso:**

| URL | Descripción |
|-----|-------------|
| `https://192.168.1.100` | Aplicación (reemplazar IP) |
| `https://192.168.1.100/stats` | Dashboard público |
| `https://192.168.1.100/api/docs` | Documentación API |
| `https://192.168.1.100/api/health` | Estado del sistema |

**Credenciales iniciales:** las definidas en `INITIAL_ADMIN_*` del `.env`.
Cambiar la contraseña del admin en el primer acceso.

### Comandos de gestión

```bash
# Detener
docker compose down

# Reiniciar un servicio (ej. tras cambiar .env)
docker compose restart backend

# Ver logs en tiempo real
docker compose logs -f

# Ver logs de un servicio específico
docker compose logs -f backend
docker compose logs -f celery
```

---

## Transferir sin Internet (Air-Gapped)

Cuando el servidor de producción **no tiene internet**, exportar las imágenes desde otra máquina que sí tenga.

### En la máquina con internet

```bash
chmod +x scripts/save-docker-images.sh
./scripts/save-docker-images.sh
# Genera: docker-images-ubpd-YYYYMMDD.tar.gz  (~1-2 GB)
```

### Transferir al servidor

```bash
# Por red local
scp docker-images-ubpd-*.tar.gz usuario@192.168.1.100:/opt/ubpd/

# O copiar por USB junto con la carpeta ubpd-app/
```

### En el servidor sin internet

```bash
cd /opt/ubpd

chmod +x ubpd-app/scripts/load-docker-images.sh
./ubpd-app/scripts/load-docker-images.sh   # importa las imágenes

cd ubpd-app
./scripts/generate-ssl.sh 192.168.1.100
cp .env.example .env && nano .env           # editar variables

docker compose up -d                        # NO requiere build
docker compose ps
```

---

## Desarrollo Local (sin Docker)

### Backend

```bash
cd backend

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# Variables mínimas para desarrollo
export DATABASE_URL="postgresql+asyncpg://ubpd:password@localhost:5432/ubpd_dev"
export REDIS_URL="redis://localhost:6379/0"
export SECRET_KEY="clave-local-solo-desarrollo"
export APP_ENV="development"
export MINIO_ENDPOINT="localhost:9000"
export MINIO_ACCESS_KEY="minioadmin"
export MINIO_SECRET_KEY="minioadmin"
export MINIO_USE_SSL="false"

# Aplicar migraciones
alembic upgrade head

# Iniciar servidor con auto-reload
uvicorn app.main:app --reload --port 8000
```

En terminales separadas:

```bash
# Worker Celery
celery -A app.celery_app worker --loglevel=info

# Scheduler Celery Beat
celery -A app.celery_app beat --loglevel=info
```

### Frontend

```bash
cd frontend

npm install
npm run dev   # disponible en http://localhost:5173
```

El proxy `/api → http://localhost:8000` está configurado en `vite.config.ts`.

---

## Ejecutar Tests

```bash
cd backend

pip install -r requirements-test.txt

# Todos los tests
pytest

# Solo tests unitarios (no requieren servicios externos)
pytest tests/test_auth_service.py tests/test_template_parser.py \
       tests/test_calculators.py tests/test_dependencies.py -v

# Tests de integración de routers
pytest tests/test_auth_router.py tests/test_stats_router.py -v

# Con reporte de cobertura
pytest --cov=app --cov-report=term-missing
```

**Suite de tests incluida:**

| Archivo | Qué prueba |
|---------|------------|
| `test_auth_service.py` | Hash bcrypt, creación/decodificación JWT, autenticación |
| `test_template_parser.py` | Parseo Markdown → schema, cálculo de completitud |
| `test_calculators.py` | Calculadoras por tipo de fórmula (simple, ponderado, conteo) |
| `test_dependencies.py` | Guards JWT, RBAC por rol, extracción de IP |
| `test_auth_router.py` | Endpoints `/api/auth/*` (login, refresh, logout, cambio de contraseña) |
| `test_stats_router.py` | Endpoints `/api/stats/*` y `/api/health` |

---

## Manual de Usuario

### Administrador

**Acceso:** `https://IP_SERVIDOR` → credenciales admin

| Tarea | Ruta en la app |
|-------|----------------|
| Crear/desactivar usuarios | Menú → Usuarios |
| Crear dependencias | Menú → Dependencias |
| Crear plantillas de formularios | Menú → Plantillas |
| Monitorear pipeline | Menú → Pipeline |
| Ver auditoría | Menú → Auditoría |

**Crear plantilla:** usar tabla Markdown en el editor:

```
| campo          | tipo     | bloqueado | default | requerido | opciones                     |
|----------------|----------|-----------|---------|-----------|------------------------------|
| nombre_victima | text     | no        |         | si        |                              |
| departamento   | select   | no        |         | si        | Cundinamarca,Antioquia,Valle |
| fecha_evento   | date     | no        |         | si        |                              |
| observaciones  | textarea | no        |         | no        |                              |
| numero_caso    | number   | si        | 0       | no        |                              |
```

- Tipos válidos: `text`, `number`, `date`, `select`, `textarea`
- `bloqueado: si` → campo de solo lectura (se rellena automáticamente)
- La columna `opciones` solo aplica para tipo `select` (separar con coma)

---

### Validador

**Flujo:**
1. Menú → **Bandeja** — ver formularios pendientes (contador naranja)
2. Clic en **Revisar** → pantalla dividida: datos (izq.) + dictamen (der.)
3. **Aprobar** (botón verde) — el formulario entra a las estadísticas
4. **Devolver** (botón naranja) — escribir comentario obligatorio con la corrección solicitada

---

### Usuario de Dependencia

**Diligenciar un formulario:**
1. Menú → **Galería** — seleccionar plantilla → **Diligenciar**
2. Completar campos requeridos (*), adjuntar archivos (PDF / JPEG / PNG / DOCX, máx. 50 MB)
3. **Guardar** (deja en borrador) o **Enviar para revisión**

**Formulario devuelto:**
1. Menú → **Mis Formularios** → pestaña **Devueltos**
2. Leer el comentario del validador (banner naranja)
3. Corregir → **Reenviar**

> El sistema guarda automáticamente cada 2 minutos mientras se edita.

**Estados:**

| Estado | Color | Significado |
|--------|-------|-------------|
| Borrador | Gris | En edición, no enviado |
| Pendiente | Amarillo | Esperando revisión |
| Aprobado | Verde | Validado, en estadísticas |
| Devuelto | Naranja | Requiere corrección |

---

### Portal Público de Estadísticas

No requiere autenticación. URL: `https://IP_SERVIDOR/stats`

- **Nivel 1:** gauges por indicador (completitud global)
- **Nivel 2:** clic en indicador → gauges por plantilla
- **Nivel 3:** clic en plantilla → tabla de registros + exportar Excel

Filtros de fecha disponibles en todos los niveles.

---

## Operaciones Frecuentes

### Backup

```bash
chmod +x scripts/backup.sh
./scripts/backup.sh
# Guarda en ./backups/ con retención de 30 días
```

Cron job para backup automático diario a las 2 AM:
```bash
crontab -e
# Agregar la línea:
0 2 * * * /ruta/completa/a/ubpd-app/scripts/backup.sh >> /var/log/ubpd-backup.log 2>&1
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

La consola MinIO solo escucha en `localhost` del servidor. Para acceder remotamente:

```bash
# Desde la máquina del administrador (SSH tunnel)
ssh -L 9001:localhost:9001 usuario@192.168.1.100
# Luego abrir: http://localhost:9001
```

### Ver logs de errores

```bash
docker compose logs --since 1h backend | grep -i error
docker compose logs --since 1h celery | grep -i error
```
