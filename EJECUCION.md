# UBPD — Ejecución y Manual de Usuario

> **Ver también:** [`CONFIGURACION.md`](CONFIGURACION.md) — instalación, `.env` y certificados.

---

## Tabla de Contenidos

1. [Arranque y gestión](#arranque-y-gestión)
2. [Despliegue sin Internet (Air-Gapped)](#despliegue-sin-internet-air-gapped)
3. [Ejecutar Tests](#ejecutar-tests)
4. [Manual de Usuario](#manual-de-usuario)
5. [Operaciones Frecuentes](#operaciones-frecuentes)

---

## Arranque y gestión

Todo se maneja con un único script: `./scripts/prod.sh`

```bash
./scripts/prod.sh start          # levantar todos los servicios
./scripts/prod.sh stop           # detener y eliminar contenedores
./scripts/prod.sh restart        # reiniciar todos los servicios
./scripts/prod.sh restart backend  # reiniciar un servicio específico
./scripts/prod.sh build          # construir imágenes
./scripts/prod.sh rebuild        # reconstruir sin caché y levantar
./scripts/prod.sh logs           # logs en tiempo real (todos)
./scripts/prod.sh logs nginx     # logs de un servicio
./scripts/prod.sh ps             # estado de contenedores + URLs
./scripts/prod.sh shell          # shell en el backend
./scripts/prod.sh shell postgres # shell en otro servicio
./scripts/prod.sh migrate        # aplicar migraciones Alembic
./scripts/prod.sh backup         # backup manual de BD
./scripts/prod.sh test           # ejecutar tests del backend
```

**Primer arranque:**
```bash
./scripts/prod.sh build    # construir todas las imágenes (requiere internet)
./scripts/prod.sh start    # levantar
./scripts/prod.sh ps       # verificar estado y ver URLs
```

**URLs de acceso** (reemplazar con la IP del servidor):

| URL | Descripción |
|-----|-------------|
| `https://192.168.1.100` | Aplicación |
| `https://192.168.1.100/stats` | Dashboard público |
| `https://192.168.1.100/api/docs` | Documentación API |
| `https://192.168.1.100/api/health` | Health check |

**Credenciales iniciales:** definidas en `INITIAL_ADMIN_*` del `.env`.

### Ver logs en disco

```bash
tail -f logs/backend/app.log       # actividad general
tail -f logs/backend/errors.log    # solo errores
tail -f logs/nginx/access.log      # requests HTTP

# Buscar errores recientes
grep -i "error\|exception" logs/backend/app.log | tail -50
```

---

## Despliegue sin Internet (Air-Gapped)

### En una máquina con internet

```bash
./scripts/save-docker-images.sh
# Genera: docker-images-ubpd-YYYYMMDD.tar.gz (~1-2 GB)
```

### Transferir al servidor

```bash
scp docker-images-ubpd-*.tar.gz usuario@192.168.1.100:/opt/ubpd/
# o copiar en USB junto con la carpeta ubpd-app/
```

### En el servidor sin internet

```bash
cd /opt/ubpd
chmod +x ubpd-app/scripts/*.sh
./ubpd-app/scripts/load-docker-images.sh   # importar imágenes

cd ubpd-app
./scripts/install.sh                        # configurar
nano .env                                   # editar IP y contraseñas
./scripts/prod.sh start                     # levantar (sin build)
./scripts/prod.sh ps
```

---

## Ejecutar Tests

```bash
# Desde el contenedor backend
./scripts/prod.sh test

# O con shell interactivo
./scripts/prod.sh shell backend
# dentro del contenedor:
pytest tests/ -v --tb=short
pytest --cov=app --cov-report=term-missing
```

| Archivo | Qué verifica |
|---------|-------------|
| `test_auth_service.py` | Bcrypt, JWT, autenticación |
| `test_template_parser.py` | Markdown → JSON schema, completitud |
| `test_calculators.py` | Fórmulas por tipo de indicador |
| `test_dependencies.py` | Guards JWT, RBAC, extracción de IP |
| `test_auth_router.py` | Endpoints `/api/auth/*` |
| `test_stats_router.py` | Endpoints `/api/stats/*`, health |

---

## Manual de Usuario

### Roles

| Rol | Acceso |
|-----|--------|
| **Administrador** | Gestión completa |
| **Validador** | Aprueba o devuelve formularios |
| **Usuario Dependencia** | Diligencia formularios |
| **Público** | Estadísticas sin autenticación |

---

### Administrador

**Acceso:** URL del sistema → credenciales admin

#### Gestión de usuarios
- Menú → **Usuarios** → **Nuevo usuario**
- Asignar rol + dependencia (para usuarios de dependencia)
- **Desactivar**: preserva historial

#### Plantillas de formularios

Menú → **Plantillas** → **Nueva plantilla** → editor Markdown:

```
| campo          | tipo     | bloqueado | default | requerido | opciones                     |
|----------------|----------|-----------|---------|-----------|------------------------------|
| nombre_victima | text     | no        |         | si        |                              |
| departamento   | select   | no        |         | si        | Cundinamarca,Antioquia,Valle |
| fecha_evento   | date     | no        |         | si        |                              |
| observaciones  | textarea | no        |         | no        |                              |
| numero_caso    | number   | si        | 0       | no        |                              |
```

- Tipos: `text`, `number`, `date`, `select`, `textarea`
- `bloqueado: si` → campo de solo lectura
- `opciones` → para `select`, separados con coma

#### Monitoreo
- **Pipeline** → semáforo de estado (actualiza cada 30s)
- **Auditoría** → log de todas las acciones del sistema

---

### Validador

1. Menú → **Bandeja** → formularios pendientes (contador naranja)
2. **Revisar** → pantalla dividida: datos (60%) + dictamen (40%)
3. **Aprobar** (verde) → entra a estadísticas
4. **Devolver** (naranja) → comentario obligatorio con la corrección

---

### Usuario de Dependencia

**Nuevo formulario:**
1. **Galería** → plantilla → **Diligenciar**
2. Completar campos `*`, adjuntar archivos (PDF/JPEG/PNG/DOCX, máx 50 MB)
3. **Guardar** (borrador) o **Enviar para revisión**

> Guardado automático cada 2 minutos.

**Formulario devuelto:**
1. **Mis Formularios** → **Devueltos** → leer comentario (banner naranja)
2. Corregir → **Reenviar**

| Estado | Color | Significado |
|--------|-------|-------------|
| Borrador | Gris | En edición |
| Pendiente | Amarillo | En revisión |
| Aprobado | Verde | En estadísticas |
| Devuelto | Naranja | Requiere corrección |

---

### Portal Público

URL: `https://IP_SERVIDOR/stats` — sin autenticación

| Nivel | Contenido | Acción |
|-------|-----------|--------|
| 1 | Gauge por indicador | Clic → Nivel 2 |
| 2 | Gauges por plantilla | Clic → Nivel 3 |
| 3 | Tabla de registros | Exportar Excel |

---

## Operaciones Frecuentes

### Backup

```bash
./scripts/prod.sh backup          # manual

# Automático con cron (2 AM diario)
crontab -e
# Agregar:
0 2 * * * /ruta/ubpd-app/scripts/backup.sh >> /var/log/ubpd-backup.log 2>&1
```

### Restaurar backup

```bash
ls -lh backups/
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

### Recálculo forzado de estadísticas

```bash
./scripts/prod.sh restart celery
./scripts/prod.sh restart celery-beat
```

### Consola MinIO (SSH tunnel)

```bash
ssh -L 9001:localhost:9001 usuario@192.168.1.100
# Abrir: http://localhost:9001
```
