# UBPD — Sistema de Gestión de Formularios

**Unidad de Búsqueda de Personas Dadas por Desaparecidas**

Sistema para diligenciar, validar y publicar estadísticas de formularios de la
Línea Estratégica No. 1. Funciona en red intranet con un único entorno Docker.

---

## Documentación

| Documento | Contenido |
|-----------|-----------|
| [`CONFIGURACION.md`](CONFIGURACION.md) | Instalación, `.env`, SSL, logging, opciones de trabajo |
| [`EJECUCION.md`](EJECUCION.md) | Comandos del script, despliegue, manual de usuario, operaciones |

---

## Inicio rápido

```bash
# 1. Instalar (una sola vez)
chmod +x scripts/*.sh
./scripts/install.sh
nano .env                     # editar SERVER_IP, SECRET_KEY, contraseñas

# 2. Construir y arrancar
./scripts/prod.sh build
./scripts/prod.sh start

# 3. Verificar
./scripts/prod.sh status
```

---

## Script de gestión

```bash
./scripts/prod.sh [start|stop|restart|build|rebuild|logs|ps|shell|migrate|backup|test]
```

---

## Stack

| Capa | Tecnología |
|------|-----------|
| Frontend | Vue 3 · Vite · Pinia · ECharts |
| Backend | FastAPI · SQLAlchemy 2.0 async |
| Base de datos | PostgreSQL 16 |
| Archivos | MinIO (S3-compatible) |
| Tareas | Celery + Redis |
| Proxy | Nginx · SSL autofirmado |
| Contenedores | Docker Compose (8 servicios) |
