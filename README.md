# UBPD — Sistema de Gestión de Formularios e Indicadores

**Unidad de Búsqueda de Personas Dadas por Desaparecidas**

Sistema para diligenciar, validar y publicar información del **Plan de Acción
Institucional 2026** y de los indicadores institucionales. Funciona en intranet
con un único entorno Docker, sin dependencia de servicios externos.

## Componentes incluidos

### Visores independientes

| Visor | Ruta | Fuente |
|------|------|--------|
| Plan de Acción Institucional 2026 | `/estadisticas` | Formularios PAI aprobados y pipeline oficial |
| Indicadores Comité Directivo | `/comite-directivo` | Catálogo anual y formularios mensuales aprobados |
| Visor BI | `/bi` | Dataset BI cargado por el administrador |

### Módulos de gestión

| Perfil | Ruta principal | Función |
|--------|----------------|---------|
| Administrador | `/admin` | Usuarios, dependencias, templates, pipeline, auditoría y respaldos |
| Validador OAP | `/validator` | Revisión, comentarios OAP, aprobación y rechazo |
| Dependencia | `/dependencia` | Diligenciamiento, soportes y envío de formularios |

Los visores son rutas separadas y de solo lectura. Los módulos de gestión
alimentan la misma base de datos mediante los flujos de aprobación existentes.

---

## Inicio rápido

```bash
# 1. Clonar e instalar
git clone <URL_DEL_REPO> sistema-indicadores
cd sistema-indicadores
chmod +x scripts/*.sh
./scripts/install.sh                 # verifica Docker y crea directorios

# 2. Configurar variables de entorno
cp .env.example .env
nano .env                            # editar contraseñas, SERVER_IP, JWT_SECRET_KEY, RESET_PIN

# 3. Levantar el sistema
./scripts/prod.sh build              # construye imágenes Y las despliega (build + up)
./scripts/prod.sh start
./scripts/prod.sh status             # verifica el estado y muestra URLs + ubicación de logs
```

Abrir `http://127.0.0.1/estadisticas` (PAI 2026),
`http://127.0.0.1/comite-directivo` (Comité Directivo),
`http://127.0.0.1/bi` (BI) y `http://127.0.0.1` (login).
Credenciales iniciales definidas en `.env` (`INITIAL_ADMIN_USERNAME` / `INITIAL_ADMIN_PASSWORD`).

> 📄 **Guía de instalación completa**: [`docs/INSTALACION.docx`](docs/INSTALACION.docx)
> — paso a paso para Windows, Linux y macOS, con variables de entorno, comandos,
> mantenimiento y resolución de problemas.

---

## Stack

| Capa | Tecnología |
|------|-----------|
| Frontend | Vue 3 · Vite · Pinia · ECharts |
| Backend | FastAPI · SQLAlchemy 2.0 async |
| Base de datos | PostgreSQL 16 |
| Archivos | MinIO (S3-compatible) |
| Tareas | Celery + Valkey |
| Proxy | Nginx (HTTP) |
| Contenedores | Docker Compose (8 servicios) |

---

## Comandos de operación

Todos desde la raíz del proyecto con `./scripts/prod.sh <comando>`:

| Comando | Descripción |
|---------|-------------|
| `start` / `up` | Levantar todos los servicios. |
| `stop` / `down` | Detener servicios. |
| `restart [svc]` | Reinicia todo o un servicio (recrea contenedor → aplica imagen nueva). |
| `build [svc]` | Construye imagen y la aplica (`build + up -d`). |
| `rebuild [svc]` | Igual que `build` pero sin caché de Docker. |
| `logs [svc]` | Ver logs en tiempo real. |
| `status` / `ps` | Estado + URLs + ubicación de los logs en disco. |
| `shell [svc]` | Terminal dentro de un contenedor (default: backend). |
| `migrate` | Aplicar migraciones Alembic. |
| `backup` | Backup manual de PostgreSQL → `./backups/`. |
| **`pipeline-reset`** | **Restaurar el pipeline de indicadores a la versión por defecto y ejecutarlo.** Úsalo si los velocímetros no se actualizan. |
| `pipeline-sync [run]` | Sincroniza `scripts/pai_2026/pipeline_pai.py` como script activo en BD. Con `run` también lo ejecuta. |
| `reset-db` | Eliminar y recrear la BD (requiere `ALLOW_DB_RESET=true` en `.env`). |
| `reset-fresh` | Reset TOTAL a estado de instalación (frase `BORRAR TODO` + PIN). |
| `destroy [all]` | Destruir contenedores, imágenes y volúmenes (frase `DESTRUIR TODO` + PIN). |

---

## Logs

`./scripts/prod.sh start` imprime al final la ruta exacta de cada log. Los principales:

```
logs/backend/app.log                            # actividad general
logs/backend/errors.log                         # solo errores
logs/backend/access.log                         # peticiones HTTP
logs/backend/pipeline/pipeline.log              # histórico del pipeline de KPIs
logs/backend/pipeline/runs/run_<ts>_<modo>.log  # un archivo por ejecución
logs/backend/uploads/upload_<ts>_<id>.log       # un archivo por intento de cargar Excel
logs/nginx/access.log  /  logs/nginx/error.log
```

---

## Documentación

| Documento | Contenido |
|-----------|-----------|
| [`docs/INSTALACION.docx`](docs/INSTALACION.docx) | **Guía de instalación end-to-end** (Windows / Linux / macOS). |
| [`CONFIGURACION.md`](CONFIGURACION.md) | Instalación, `.env`, despliegue, operación (versión técnica). |
| [`README_FLUJO.md`](README_FLUJO.md) | Recorrido completo del dato — de la dependencia al panel público. |
| [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) | Servicios, flujo de datos, seguridad. |
| [`docs/FLUJO_USUARIOS.md`](docs/FLUJO_USUARIOS.md) | Flujos por rol: admin, validador, dependencia, público. |
| [`docs/FLUJO_TEMPLATES.md`](docs/FLUJO_TEMPLATES.md) | Estructura de templates, campos `validator_only` y `auto_calculate`. |
| [`docs/FLUJO_DATOS_FORMULARIOS.md`](docs/FLUJO_DATOS_FORMULARIOS.md) | Estados del formulario, carga vía Excel, ZIP de adjuntos. |
| [`docs/FLUJO_PIPELINE_PROCESAMIENTO.md`](docs/FLUJO_PIPELINE_PROCESAMIENTO.md) | Cálculo de KPIs nivel 1 / nivel 2 / por trimestre. |
| [`docs/SCRIPTS_RESET.md`](docs/SCRIPTS_RESET.md) | Comandos destructivos (`reset-db`, `reset-fresh`, `destroy`). |
| [`scripts/pai_2026/README.md`](scripts/pai_2026/README.md) | Setup del PAI 2026 (14 templates, 6 líneas). |
| [`docs/ENTREGA_GITHUB_AZURE.md`](docs/ENTREGA_GITHUB_AZURE.md) | Alcance del repositorio y entrega de GitHub a Azure DevOps. |
| [`docs/GOBIERNO_AZURE_DEVOPS.md`](docs/GOBIERNO_AZURE_DEVOPS.md) | GitFlow, permisos, PR, CI/CD, MFA y Seguridad Digital. |

---

## Entrega de GitHub a Azure DevOps

El área de TI puede importar el repositorio directamente desde GitHub o clonarlo
y publicarlo en Azure DevOps:

```bash
git clone https://github.com/<ORGANIZACION>/<REPOSITORIO>.git
cd <REPOSITORIO>
git remote add azure https://dev.azure.com/<ORGANIZACION>/<PROYECTO>/_git/<REPOSITORIO>
git push azure --all
git push azure --tags
```

Antes del primer despliegue se debe crear `.env` desde `.env.example`, asignar
secretos institucionales y ejecutar `./scripts/prod.sh build`. La base de datos,
los respaldos, los archivos cargados y cualquier `.env` están excluidos del
repositorio.
