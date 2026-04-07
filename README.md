# UBPD — Sistema de Gestión de Formularios

**Unidad de Búsqueda de Personas Dadas por Desaparecidas**

Sistema para diligenciar, validar y publicar estadísticas de formularios de la
Línea Estratégica No. 1. Funciona en red intranet (air-gapped) con un único entorno Docker.

---

## Inicio rápido

```bash
chmod +x scripts/*.sh
./scripts/install.sh          # verifica Docker y crea directorios
nano .env                     # editar SERVER_IP, SECRET_KEY, contraseñas
./scripts/prod.sh build
./scripts/prod.sh start
./scripts/prod.sh ps          # verificar estado y ver URLs
```

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

## Documentación

| Documento | Contenido |
|-----------|-----------|
| [`CONFIGURACION.md`](CONFIGURACION.md) | Instalación, `.env`, despliegue, operación |
| [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) | Servicios, flujo de datos, seguridad |
| [`docs/FLUJO_USUARIOS.md`](docs/FLUJO_USUARIOS.md) | Flujos por rol: admin, validador, dependencia, público |
