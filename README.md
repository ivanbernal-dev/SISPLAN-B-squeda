# UBPD — Sistema de Gestión de Formularios y Estadísticas

> Plataforma interna de la **Unidad de Búsqueda de Personas Dadas por Desaparecidas (UBPD)**
> para la gestión, validación y visualización de formularios de la Línea Estratégica No. 1.

---

## Descripción General

Sistema web desplegado **100% en red local (air-gapped)** sin dependencia de internet.
Gestiona el ciclo de vida completo de formularios humanitarios: desde la carga por parte de dependencias, la validación por parte de revisores, hasta la visualización pública de indicadores estadísticos de 3 niveles.

## Stack Tecnológico

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Frontend | Vue.js 3 + Vite + Pinia + Vue Router | 3.x |
| Estilos | Tailwind CSS | 3.x |
| Gráficos | ECharts | 5.x |
| Backend | FastAPI (Python) | 0.110+ |
| ORM | SQLAlchemy + Alembic | 2.x |
| Base de Datos | PostgreSQL | 16 |
| Almacenamiento | MinIO (S3-compatible) | Latest |
| Caché/Queue | Redis | 7 |
| Workers | Celery | 5.x |
| Proxy | Nginx | 1.25 |
| Orquestación | Docker Compose | v2 |

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [ARQUITECTURA.md](docs/ARQUITECTURA.md) | Visión general de la arquitectura y servicios |
| [REQUERIMIENTOS.md](docs/REQUERIMIENTOS.md) | Requerimientos funcionales por rol |
| [MODELOS_DATOS.md](docs/MODELOS_DATOS.md) | Esquema de base de datos y JSONB |
| [FLUJO_USUARIOS.md](docs/FLUJO_USUARIOS.md) | Flujos de trabajo por perfil de usuario |
| [API_ENDPOINTS.md](docs/API_ENDPOINTS.md) | Definición de endpoints REST |
| [IDENTIDAD_VISUAL.md](docs/IDENTIDAD_VISUAL.md) | Paleta de colores, tipografía y branding UBPD |
| [DESPLIEGUE.md](docs/DESPLIEGUE.md) | Guía de instalación y despliegue en red local |

## Levantar el Proyecto

```bash
# 1. Copiar variables de entorno
cp .env.example .env

# 2. Levantar todos los servicios
docker compose up -d

# 3. Verificar estado
docker compose ps
```

## Roles de Usuario

| Rol | Descripción |
|-----|-------------|
| `admin` | Gestión total: usuarios, templates, auditoría |
| `validator` | Revisión y aprobación/rechazo de formularios |
| `dependency_user` | Carga de formularios y seguimiento de trámites |
| `public` | Consulta pública de estadísticas (sin login) |

## Acceso por Defecto

| Servicio | URL Local | Puerto |
|----------|-----------|--------|
| Aplicación Web | `http://SERVER_IP` | 80 / 443 |
| API Backend | `http://SERVER_IP/api` | 80 (proxy) |
| MinIO Console | `http://SERVER_IP:9001` | 9001 |
| PostgreSQL | `SERVER_IP:5432` | 5432 |
| Redis | `SERVER_IP:6379` | 6379 |
