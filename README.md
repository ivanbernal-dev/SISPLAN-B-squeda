# UBPD — Sistema de Gestión de Formularios

**Unidad de Búsqueda de Personas Dadas por Desaparecidas**
Sistema de gestión de formularios para la Línea Estratégica No. 1

---

## Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Arquitectura](#arquitectura)
3. [Requisitos Previos](#requisitos-previos)
4. [Instalación y Configuración](#instalación-y-configuración)
5. [Despliegue con Docker](#despliegue-con-docker)
6. [Despliegue sin Internet (Air-Gapped)](#despliegue-sin-internet-air-gapped)
7. [Modo Desarrollo (sin Docker)](#modo-desarrollo-sin-docker)
8. [Manual de Usuario](#manual-de-usuario)
9. [Gestión y Operaciones](#gestión-y-operaciones)
10. [Solución de Problemas](#solución-de-problemas)
11. [Estructura del Proyecto](#estructura-del-proyecto)

---

## Descripción General

El sistema UBPD permite a las dependencias de la organización diligenciar formularios digitales estructurados, someterlos a un proceso de validación interna y publicar estadísticas agregadas de completitud en un portal público.

### Funcionalidades Principales

| Módulo | Descripción |
|--------|-------------|
| **Gestión de Usuarios** | CRUD de usuarios con roles diferenciados (admin, validador, dependencia) |
| **Plantillas de Formularios** | Editor Markdown que genera esquemas JSONB dinámicos |
| **Diligenciamiento** | Formularios dinámicos con carga de archivos adjuntos (PDF, imágenes, DOCX) |
| **Validación** | Flujo de revisión con aprobación o devolución con comentario |
| **Estadísticas Públicas** | Dashboard de 3 niveles con indicadores de completitud tipo velocímetro |
| **Exportación Excel** | Descarga de registros aprobados filtrados por fecha |
| **Pipeline de Datos** | Recálculo periódico automático de estadísticas vía Celery |

### Roles del Sistema

```
admin           → Gestión total: usuarios, dependencias, plantillas, auditoría
validator       → Revisión y dictamen de formularios enviados
dependency_user → Diligenciamiento y envío de formularios propios
público         → Consulta de estadísticas sin autenticación
```

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLIENTE                                 │
│              Navegador Web (Chrome / Edge)                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS :443
┌──────────────────────────▼──────────────────────────────────────┐
│                       NGINX (Proxy)                              │
│         SSL Termination  │  Gzip  │  Static Files                │
└──────┬───────────────────┴──────────────────────────────────────┘
       │ /api/*                              │ /*
┌──────▼────────────┐              ┌─────────▼─────────┐
│  FastAPI Backend  │              │  Vue 3 Frontend   │
│  (Uvicorn :8000)  │              │  (Nginx :80)      │
│                   │              │  SPA + Tailwind   │
│  ├─ Auth (JWT)    │              │  ├─ Admin Panel   │
│  ├─ Forms API     │              │  ├─ Validator     │
│  ├─ Stats API     │              │  ├─ Dependency    │
│  └─ Files API     │              │  └─ Public Stats  │
└──────┬────────────┘              └───────────────────┘
       │
┌──────▼──────────────────────────────────────────────┐
│              Capa de Persistencia                    │
│                                                      │
│  ┌─────────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ PostgreSQL  │  │  Redis   │  │     MinIO      │  │
│  │   :5432     │  │  :6379   │  │  :9000/:9001   │  │
│  │  Datos ORM  │  │ Cache/   │  │  Archivos S3   │  │
│  │  + JSONB    │  │ Celery   │  │  compatible    │  │
│  └─────────────┘  └──────────┘  └────────────────┘  │
└──────────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────┐
│           Workers Asíncronos             │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │   Celery    │  │  Celery Beat    │   │
│  │   Worker    │  │  (Scheduler)    │   │
│  │ Procesa     │  │ Recálculo cada  │   │
│  │ aprobaciones│  │ 10 min (conf.)  │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────┘
```

### Estados de un Formulario

```
BORRADOR (draft)
    │
    │  [submit]
    ▼
PENDIENTE (pending)
    │
    ├── [aprobar]  ──► APROBADO (approved)  ──► entra en estadísticas
    │
    └── [devolver] ──► DEVUELTO (rejected)
                         │
                         │  [editar + reenviar]
                         └────────────────────► PENDIENTE
```

---

## Requisitos Previos

### Máquina Servidor

| Componente | Versión mínima | Notas |
|------------|----------------|-------|
| Sistema Operativo | Linux (Ubuntu 20.04+) | Recomendado |
| Docker Engine | 24.0+ | `docker --version` |
| Docker Compose | 2.20+ (plugin) | `docker compose version` |
| RAM disponible | 4 GB | 8 GB recomendado |
| Disco libre | 20 GB | Para datos, imágenes, backups |
| CPU | 2 núcleos | 4 recomendado |
| OpenSSL | 1.1+ | Para certificados SSL |

### Instalar Docker en Ubuntu

```bash
# Actualizar índice de paquetes
sudo apt-get update

# Instalar dependencias
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Agregar clave GPG oficial de Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Agregar repositorio
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker Engine y Compose plugin
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Agregar usuario actual al grupo docker (evita usar sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verificar instalación
docker --version
docker compose version
```

---

## Instalación y Configuración

### Paso 1 — Obtener el Código

```bash
# Copiar el directorio ubpd-app al servidor
# (vía SCP, USB, o cualquier medio disponible)

# O clonar si tiene acceso al repositorio:
# git clone <URL_REPOSITORIO> ubpd-app

cd ubpd-app
```

### Paso 2 — Generar Certificado SSL

El sistema requiere SSL para funcionar de forma segura en red local. Ejecute el script con la **IP real del servidor**:

```bash
# Dar permisos de ejecución
chmod +x scripts/generate-ssl.sh

# Generar certificado (reemplazar con la IP real del servidor)
./scripts/generate-ssl.sh 192.168.1.100
```

Esto genera dos archivos en `nginx/certs/`:
- `server.crt` — Certificado público (distribuir a los clientes)
- `server.key` — Clave privada (¡nunca compartir!)

> **Importante:** La IP en el certificado debe coincidir exactamente con la IP que usarán los clientes para acceder. Si la IP cambia, regenerar el certificado.

### Paso 3 — Configurar Variables de Entorno

```bash
# Copiar la plantilla
cp .env.example .env

# Editar con un editor de texto
nano .env   # o: vi .env
```

**Variables obligatorias a cambiar:**

```bash
# ── Servidor ───────────────────────────────────────────────
SERVER_IP=192.168.1.100          # ← IP real del servidor

# ── Seguridad (CAMBIAR EN PRODUCCIÓN) ─────────────────────
SECRET_KEY=cambia_esto_por_una_clave_secreta_larga_y_aleatoria

# ── Base de Datos ──────────────────────────────────────────
POSTGRES_PASSWORD=una_contraseña_segura_para_postgres

# ── Redis ──────────────────────────────────────────────────
REDIS_PASSWORD=contraseña_segura_para_redis

# ── MinIO (almacenamiento de archivos) ─────────────────────
MINIO_ACCESS_KEY=usuario_minio_seguro
MINIO_SECRET_KEY=contraseña_minio_muy_segura

# ── Administrador Inicial ──────────────────────────────────
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=Admin2024!   # Cambiar inmediatamente al primer inicio
INITIAL_ADMIN_EMAIL=admin@ubpd.gov.co
INITIAL_ADMIN_NOMBRE=Administrador UBPD
```

**Variables opcionales:**

```bash
# Tamaño máximo de archivos adjuntos (en MB)
MAX_UPLOAD_MB=50

# Intervalo de recálculo de estadísticas (en segundos)
STATS_RECALC_INTERVAL_SECONDS=600   # 10 minutos

# Entorno de la aplicación
APP_ENV=production
```

> **Generación de SECRET_KEY segura:**
> ```bash
> python3 -c "import secrets; print(secrets.token_hex(32))"
> ```

---

## Despliegue con Docker

### Primera Ejecución

```bash
# Desde el directorio ubpd-app/
cd ubpd-app

# Construir imágenes (requiere internet la primera vez)
docker compose build

# Iniciar todos los servicios
docker compose up -d

# Verificar que todos los contenedores estén corriendo
docker compose ps
```

**Salida esperada de `docker compose ps`:**
```
NAME                    STATUS          PORTS
ubpd-nginx              running         0.0.0.0:443->443/tcp, 0.0.0.0:80->80/tcp
ubpd-frontend           running
ubpd-backend            running
ubpd-celery             running
ubpd-celery-beat        running
ubpd-postgres           running         5432/tcp
ubpd-redis              running         6379/tcp
ubpd-minio              running         9000/tcp, 9001/tcp
```

### Verificar el Sistema

```bash
# 1. Estado de salud del backend
curl -k https://192.168.1.100/api/health

# Respuesta esperada:
# {"status":"ok","app":"UBPD","version":"1.0.0","env":"production"}

# 2. Ver logs en tiempo real
docker compose logs -f

# 3. Ver logs de un servicio específico
docker compose logs -f backend
docker compose logs -f celery
```

### Acceso Inicial

Una vez levantado el sistema:

| URL | Descripción |
|-----|-------------|
| `https://192.168.1.100` | Aplicación principal (reemplazar IP) |
| `https://192.168.1.100/stats` | Dashboard público de estadísticas |
| `https://192.168.1.100/api/docs` | Documentación API interactiva (Swagger) |
| `https://192.168.1.100/api/health` | Estado del servicio |

**Primer acceso:**
- Usuario: valor de `INITIAL_ADMIN_USERNAME` en `.env`
- Contraseña: valor de `INITIAL_ADMIN_PASSWORD` en `.env`
- **Se recomienda cambiar la contraseña inmediatamente**

### Instalar Certificado en Clientes Windows

Para que el navegador confíe en el certificado autofirmado:

1. Copiar `nginx/certs/server.crt` a cada equipo cliente
2. Hacer doble clic en el archivo `.crt`
3. Clic en **"Instalar certificado"**
4. Seleccionar **"Equipo local"** → Siguiente
5. Seleccionar **"Colocar todos los certificados en el siguiente almacén"**
6. Clic en **"Examinar"** → seleccionar **"Entidades de certificación raíz de confianza"**
7. Aceptar y finalizar
8. Reiniciar el navegador

### Gestión de Servicios

```bash
# Detener todos los servicios
docker compose down

# Reiniciar un servicio específico (ej: después de cambiar .env)
docker compose restart backend

# Reiniciar todos
docker compose restart

# Ver uso de recursos
docker stats

# Actualizar solo el backend (después de cambios en el código)
docker compose build backend
docker compose up -d backend
```

---

## Despliegue sin Internet (Air-Gapped)

Para entornos sin acceso a internet, las imágenes Docker deben exportarse desde una máquina con internet e importarse en el servidor.

### Máquina con Internet (exportar imágenes)

```bash
# Dar permisos
chmod +x scripts/save-docker-images.sh

# Descargar y empaquetar todas las imágenes
./scripts/save-docker-images.sh

# Se genera: docker-images-ubpd-YYYYMMDD.tar.gz (≈ 1-2 GB)
```

### Transferir al Servidor

```bash
# Opción 1: SCP (red)
scp docker-images-ubpd-*.tar.gz usuario@192.168.1.100:/opt/ubpd/

# Opción 2: USB / Medio físico
# Copiar el .tar.gz y el directorio ubpd-app al dispositivo

# Opción 3: rsync
rsync -avz --progress docker-images-ubpd-*.tar.gz usuario@192.168.1.100:/opt/ubpd/
```

### Servidor sin Internet (importar y ejecutar)

```bash
# En el servidor, ir al directorio con los archivos
cd /opt/ubpd

# Dar permisos
chmod +x ubpd-app/scripts/load-docker-images.sh

# Importar imágenes al Docker local
./ubpd-app/scripts/load-docker-images.sh

# Entrar al directorio del proyecto
cd ubpd-app

# Generar SSL (sin internet, usa openssl local)
./scripts/generate-ssl.sh 192.168.1.100

# Configurar .env
cp .env.example .env
nano .env   # editar variables

# Iniciar (NO requiere docker compose build en air-gapped)
docker compose up -d

# Verificar
docker compose ps
```

---

## Modo Desarrollo (sin Docker)

Para desarrollo local en la máquina del desarrollador.

### Backend (FastAPI)

**Requisitos:** Python 3.11+, PostgreSQL 15+, Redis 7+

```bash
cd ubpd-app/backend

# Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno para desarrollo
export DATABASE_URL="postgresql+asyncpg://ubpd:password@localhost:5432/ubpd_dev"
export REDIS_URL="redis://localhost:6379/0"
export SECRET_KEY="clave-local-para-desarrollo"
export APP_ENV="development"
export MINIO_ENDPOINT="localhost:9000"
export MINIO_ACCESS_KEY="minioadmin"
export MINIO_SECRET_KEY="minioadmin"
export MINIO_USE_SSL="false"

# Ejecutar migraciones
alembic upgrade head

# Iniciar servidor de desarrollo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# (En otra terminal) Iniciar worker Celery
celery -A app.celery_app worker --loglevel=info

# (En otra terminal) Iniciar Celery Beat
celery -A app.celery_app beat --loglevel=info
```

### Ejecutar Tests del Backend

```bash
cd ubpd-app/backend

# Instalar dependencias de test
pip install -r requirements-test.txt

# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=app --cov-report=html

# Solo tests unitarios (sin integración)
pytest tests/test_auth_service.py tests/test_template_parser.py tests/test_calculators.py tests/test_dependencies.py -v

# Solo tests de integración de routers
pytest tests/test_auth_router.py tests/test_stats_router.py -v

# Ver reporte de cobertura HTML
open htmlcov/index.html   # macOS
xdg-open htmlcov/index.html   # Linux
```

### Frontend (Vue 3)

**Requisitos:** Node.js 20+, npm 10+

```bash
cd ubpd-app/frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
# (El proxy /api → http://localhost:8000 está configurado en vite.config.ts)
npm run dev

# Build de producción
npm run build

# Preview del build
npm run preview
```

La aplicación estará disponible en `http://localhost:5173`

---

## Manual de Usuario

### Rol: Administrador

El administrador tiene acceso total al sistema.

#### Acceso
1. Ingresar a `https://IP_SERVIDOR`
2. Introducir credenciales de administrador
3. El sistema redirige al **Panel de Administración**

#### Gestión de Usuarios
1. Menú lateral → **"Usuarios"**
2. **Crear usuario:**
   - Clic en **"+ Nuevo Usuario"**
   - Completar: nombre, nombre de usuario, correo, rol, dependencia (si aplica)
   - La contraseña temporal se asigna automáticamente
   - El usuario debe cambiarla en su primer acceso
3. **Desactivar usuario:** Clic en el ícono de candado en la fila correspondiente
4. **Editar usuario:** Clic en el ícono de lápiz

#### Gestión de Dependencias
1. Menú lateral → **"Dependencias"**
2. Crear dependencias antes de asignar usuarios del rol `dependency_user`
3. El nombre de la dependencia aparece en los reportes públicos

#### Gestión de Plantillas
1. Menú lateral → **"Plantillas"**
2. **Crear plantilla:**
   - Clic en **"+ Nueva Plantilla"**
   - Asignar nombre, indicador asociado (Nivel 1)
   - Editar el Markdown de la tabla de campos
3. **Formato de la tabla Markdown:**
   ```markdown
   | campo | tipo | bloqueado | default | requerido | opciones |
   |-------|------|-----------|---------|-----------|----------|
   | nombre_victima | text | no | | si | |
   | departamento | select | no | | si | Cundinamarca,Antioquia,Valle |
   | fecha_evento | date | no | | si | |
   | numero_caso | number | si | 0 | no | |
   | observaciones | textarea | no | | no | |
   ```
   - **tipos válidos:** `text`, `number`, `date`, `select`, `textarea`
   - **bloqueado `si`:** el campo es de solo lectura (relleno automático)
   - La columna **opciones** solo aplica para tipo `select` (separar con coma)
4. El panel derecho muestra vista previa en tiempo real

#### Monitoreo del Pipeline
1. Menú lateral → **"Pipeline"**
2. El semáforo indica el estado del último proceso:
   - Verde: último proceso exitoso
   - Amarillo: en progreso
   - Rojo: error (revisar logs)
3. Se actualiza automáticamente cada 30 segundos

#### Auditoría
1. Menú lateral → **"Auditoría"**
2. Filtre por usuario, tipo de acción o rango de fechas
3. Cada acción registra: usuario, IP, timestamp, descripción

---

### Rol: Validador

El validador revisa y aprueba o devuelve formularios enviados por las dependencias.

#### Bandeja de Entrada
1. Ingresar al sistema con credenciales de validador
2. El sistema muestra la **Bandeja de Entrada**
3. El contador naranja en el menú indica formularios pendientes
4. Usar los filtros de fecha para acotar la búsqueda

#### Revisar un Formulario
1. Clic en **"Revisar"** en la fila del formulario
2. La pantalla muestra:
   - **Izquierda (60%):** Datos del formulario (solo lectura)
     - Campos dinámicos con sus valores
     - Archivos adjuntos con vista previa
   - **Derecha (40%):** Panel de dictamen
3. **Aprobar:**
   - Verificar que los datos sean correctos y completos
   - Clic en **"Aprobar"** (botón verde)
   - El formulario entra al pipeline de estadísticas
4. **Devolver:**
   - Identificar el problema o información faltante
   - Escribir un comentario obligatorio en el campo de texto
   - Clic en **"Devolver"** (botón naranja)
   - El formulario regresa al usuario con el comentario visible

#### Gestión de Plantillas (Validador)
- Los validadores pueden **crear y editar** plantillas
- No pueden desactivar plantillas (solo el administrador)
- Acceso por menú lateral → **"Plantillas"**

---

### Rol: Usuario de Dependencia

Los usuarios de dependencia diligencian y envían formularios.

#### Panel Principal
Al ingresar, el usuario ve:
- **4 indicadores** con conteo de formularios por estado
- **Últimos formularios devueltos** con el motivo de devolución

#### Diligenciar un Nuevo Formulario
1. Menú superior → **"Galería de Formularios"**
2. Seleccionar el formulario (plantilla) a diligenciar
3. Clic en **"Diligenciar"**
4. Completar todos los campos requeridos (marcados con *)
5. **Adjuntar archivos:** arrastrar y soltar o hacer clic en la zona de carga
   - Formatos permitidos: PDF, JPEG, PNG, DOCX
   - Tamaño máximo por archivo: 50 MB
6. Completar el **informe cualitativo** si aplica
7. Seleccionar la **fecha de referencia** del formulario
8. **Guardar borrador:** clic en **"Guardar"** (el formulario queda en estado *Borrador*)
9. **Enviar a validación:** clic en **"Enviar para Revisión"**

> El sistema guarda automáticamente cada 2 minutos mientras se edita.

#### Gestionar Formularios Devueltos
1. Menú superior → **"Mis Formularios"** → pestaña **"Devueltos"**
2. Ver el comentario del validador en el banner naranja
3. Clic en **"Editar"** para corregir los datos señalados
4. Realizar las correcciones necesarias
5. Clic en **"Reenviar"** para someterlo nuevamente a validación

#### Estados de mis Formularios

| Estado | Color | Significado |
|--------|-------|-------------|
| Borrador | Gris | En edición, no enviado |
| Pendiente | Amarillo | Enviado, esperando revisión |
| Aprobado | Verde | Validado, en estadísticas |
| Devuelto | Naranja | Requiere corrección |

---

### Portal Público de Estadísticas

El portal de estadísticas no requiere autenticación.

#### Nivel 1 — Indicadores Globales
- URL: `https://IP_SERVIDOR/stats`
- Muestra los indicadores de la Línea Estratégica No. 1
- Cada indicador se representa como un **velocímetro (gauge)**
- El porcentaje indica el nivel de completitud promedio

#### Nivel 2 — Por Plantilla
- Clic en cualquier indicador del Nivel 1
- Muestra los formularios (plantillas) que componen el indicador
- Cada plantilla tiene su propio gauge de completitud

#### Nivel 3 — Detalle de Registros
- Clic en cualquier plantilla del Nivel 2
- Tabla con todos los formularios aprobados
- Permite buscar por dependencia, usuario o datos del formulario
- **Exportar Excel:** clic en **"Exportar Excel"** para descargar los registros

#### Filtro por Fechas
- Disponible en todos los niveles
- Presets disponibles: Hoy, Esta semana, Este mes, Este año, Últimos 30/90 días
- Rango personalizado mediante selector de fechas

---

## Gestión y Operaciones

### Backups Automáticos

El script de backup genera:
- Dump completo de PostgreSQL (formato pg_dump)
- Compresión del directorio de MinIO (archivos adjuntos)
- Retención de 30 días

```bash
# Configurar cron job para backup diario a las 2 AM
chmod +x scripts/backup.sh
crontab -e

# Agregar la línea:
0 2 * * * /ruta/completa/a/ubpd-app/scripts/backup.sh >> /var/log/ubpd-backup.log 2>&1
```

### Ejecución Manual de Backup

```bash
./scripts/backup.sh
```

Los backups se guardan en `./backups/` con nombres como:
- `ubpd_postgres_YYYYMMDD_HHMMSS.sql.gz`
- `ubpd_minio_YYYYMMDD_HHMMSS.tar.gz`

### Restaurar Backup

```bash
# Restaurar PostgreSQL
docker compose exec -T postgres psql -U ubpd ubpd < backup.sql

# Restaurar MinIO (detener minio primero)
docker compose stop minio
tar -xzf ubpd_minio_FECHA.tar.gz -C /ruta/volumen/minio/
docker compose start minio
```

### Crear Usuario Administrador Adicional

```bash
docker compose exec backend python scripts/create_admin.py \
  --username nuevo_admin \
  --password ContraseñaSegura123! \
  --email nuevo@ubpd.gov.co \
  --nombre "Nombre Completo"
```

### Ejecutar Migraciones de Base de Datos

```bash
# Aplicar migraciones pendientes
docker compose exec backend alembic upgrade head

# Ver estado de migraciones
docker compose exec backend alembic current

# Crear nueva migración (después de modificar modelos)
docker compose exec backend alembic revision --autogenerate -m "descripcion_cambio"
```

### Ver Logs

```bash
# Todos los servicios
docker compose logs -f

# Solo backend (útil para depurar)
docker compose logs -f backend

# Solo errores del último minuto
docker compose logs --since 1m backend | grep ERROR

# Guardar logs a archivo
docker compose logs backend > backend_$(date +%Y%m%d).log
```

---

## Solución de Problemas

### El navegador muestra "No es privado" al ingresar

**Causa:** El certificado SSL autofirmado no está instalado en el navegador del cliente.

**Solución:**
1. Copiar `nginx/certs/server.crt` al equipo cliente
2. Seguir los pasos de [Instalar Certificado en Clientes Windows](#instalar-certificado-en-clientes-windows)
3. Reiniciar el navegador

---

### Los contenedores no inician / `docker compose ps` muestra `Exit`

```bash
# Ver el motivo del error
docker compose logs <nombre_servicio>

# Ejemplo para backend:
docker compose logs backend
```

**Causas comunes:**
- Variables de entorno incorrectas en `.env`
- Puerto ocupado (`Error: bind: address already in use`)
- Certificados SSL no generados

---

### El backend muestra error de conexión a la base de datos

```bash
# Verificar que PostgreSQL esté corriendo
docker compose ps postgres

# Ver logs de PostgreSQL
docker compose logs postgres

# Verificar credenciales en .env
grep POSTGRES .env
```

---

### Archivos adjuntos no se cargan (error 413)

**Causa:** El archivo supera el límite configurado.

**Solución:** Verificar `MAX_UPLOAD_MB` en `.env` y `client_max_body_size` en `nginx/nginx.conf`.

---

### Las estadísticas no se actualizan

**Causa:** El worker de Celery puede estar caído.

```bash
# Verificar estado de Celery
docker compose ps celery celery-beat

# Reiniciar workers
docker compose restart celery celery-beat

# Forzar recálculo manual
docker compose exec backend python -c "
from app.celery_app import celery_app
celery_app.send_task('app.tasks.pipeline_tasks.scheduled_recalculation')
print('Tarea enviada')
"
```

---

### Error al ejecutar `docker compose build`

```bash
# Limpiar caché de Docker y reconstruir
docker compose build --no-cache

# Ver detalles del error
docker compose build --progress=plain 2>&1 | tail -50
```

---

### Restablecer contraseña de administrador

```bash
docker compose exec backend python scripts/create_admin.py \
  --username admin \
  --password NuevaContraseña123! \
  --reset-password
```

---

### Liberar espacio en disco

```bash
# Ver uso de espacio Docker
docker system df

# Limpiar imágenes y contenedores no usados
docker system prune -f

# Limpiar volúmenes huérfanos (¡cuidado con datos!)
docker volume prune -f
```

---

## Estructura del Proyecto

```
ubpd-app/
├── .env.example                  # Plantilla de variables de entorno
├── .gitignore
├── docker-compose.yml            # Orquestación de 7 servicios
│
├── nginx/
│   ├── nginx.conf                # Configuración principal Nginx
│   ├── conf.d/
│   │   └── ubpd.conf             # Virtual host HTTPS + proxy
│   └── certs/                    # Certificados SSL (generados)
│       ├── server.crt
│       └── server.key
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt          # Dependencias Python
│   ├── requirements-test.txt     # Dependencias de testing
│   ├── pytest.ini                # Configuración pytest
│   ├── alembic.ini
│   ├── alembic/
│   │   └── env.py                # Configuración async de migraciones
│   ├── scripts/
│   │   └── create_admin.py       # CLI para crear admins
│   ├── tests/                    # Suite de tests
│   │   ├── conftest.py           # Fixtures compartidos
│   │   ├── test_auth_service.py  # Tests de autenticación
│   │   ├── test_template_parser.py
│   │   ├── test_calculators.py
│   │   ├── test_auth_router.py
│   │   ├── test_stats_router.py
│   │   └── test_dependencies.py
│   └── app/
│       ├── main.py               # Punto de entrada FastAPI
│       ├── config.py             # Configuración (pydantic-settings)
│       ├── database.py           # Motor async SQLAlchemy
│       ├── dependencies.py       # Inyección de dependencias (JWT/RBAC)
│       ├── celery_app.py         # Configuración Celery + Beat
│       ├── models/               # Modelos ORM (9 modelos)
│       ├── schemas/              # Schemas Pydantic (I/O)
│       ├── routers/              # Endpoints REST (7 routers)
│       ├── services/             # Lógica de negocio
│       │   ├── auth_service.py
│       │   ├── template_parser.py
│       │   ├── minio_service.py
│       │   ├── pipeline_service.py
│       │   └── calculators/
│       └── tasks/
│           └── pipeline_tasks.py # Tareas Celery
│
├── frontend/
│   ├── Dockerfile                # Multi-stage build
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js        # Paleta UBPD
│   ├── index.html
│   └── src/
│       ├── main.ts               # Bootstrap Vue + ECharts
│       ├── App.vue
│       ├── router/               # Vue Router con guards RBAC
│       ├── stores/               # Pinia (auth, notifications, statsFilter)
│       ├── composables/          # useApi, useDateFilter
│       ├── types/                # TypeScript interfaces
│       ├── assets/styles/        # Tailwind + CSS vars
│       ├── components/           # Componentes reutilizables
│       │   ├── common/           # Header, StatusBadge, Modals, etc.
│       │   ├── charts/           # GaugeChart, IndicatorCard
│       │   └── forms/            # DynamicFormRenderer, FileUploadZone
│       ├── layouts/              # AdminLayout, ValidatorLayout, etc.
│       └── views/                # Vistas por rol
│           ├── auth/
│           ├── admin/
│           ├── validator/
│           ├── dependency/
│           └── public/
│
├── scripts/
│   ├── generate-ssl.sh           # Generar certificados autofirmados
│   ├── save-docker-images.sh     # Exportar imágenes (air-gapped)
│   ├── load-docker-images.sh     # Importar imágenes (air-gapped)
│   └── backup.sh                 # Backup PostgreSQL + MinIO
│
└── docs/
    ├── ARQUITECTURA.md
    ├── REQUERIMIENTOS.md
    ├── MODELOS_DATOS.md
    ├── FLUJO_USUARIOS.md
    ├── API_ENDPOINTS.md
    ├── IDENTIDAD_VISUAL.md
    └── DESPLIEGUE.md
```

---

## Información del Proyecto

| Elemento | Detalle |
|----------|---------|
| **Stack Backend** | Python 3.11 · FastAPI 0.110 · SQLAlchemy 2.0 · PostgreSQL 16 |
| **Stack Frontend** | Vue 3 · TypeScript · Vite 5 · Tailwind CSS · ECharts |
| **Infraestructura** | Docker Compose · Nginx · MinIO · Redis · Celery |
| **Autenticación** | JWT (HS256) · Bcrypt · RBAC por roles |
| **Versión** | 1.0.0 |
