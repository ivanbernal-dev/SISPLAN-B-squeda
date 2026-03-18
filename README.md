# UBPD — Sistema de Gestión de Formularios

**Unidad de Búsqueda de Personas Dadas por Desaparecidas**

Sistema para diligenciar, validar y publicar estadísticas de formularios de la
Línea Estratégica No. 1. Funciona exclusivamente en **red intranet** (sin internet).

---

## Documentación

| Documento | Contenido |
|-----------|-----------|
| [`CONFIGURACION.md`](CONFIGURACION.md) | Requisitos, certificados SSL, variables `.env`, logging |
| [`EJECUCION.md`](EJECUCION.md) | Levantar con Docker, desarrollo local, air-gapped, tests, manual de usuario, operaciones |

---

## Inicio rápido

```bash
# 1. Generar certificado SSL con la IP del servidor
./scripts/generate-ssl.sh 192.168.1.100

# 2. Configurar variables de entorno
cp .env.example .env && nano .env

# 3. Construir y levantar
docker compose build
docker compose up -d

# 4. Verificar
docker compose ps
curl -k https://192.168.1.100/api/health
```

---

## Tecnologías

| Capa | Tecnología |
|------|-----------|
| Frontend | Vue 3 + Vite + Pinia + ECharts |
| Backend | FastAPI + SQLAlchemy 2.0 async |
| Base de datos | PostgreSQL 16 (JSONB para formularios dinámicos) |
| Archivos | MinIO (S3-compatible) |
| Tareas | Celery + Redis |
| Proxy | Nginx con SSL autofirmado |
| Contenedores | Docker Compose (8 servicios) |

## Roles

| Rol | Descripción |
|-----|-------------|
| `admin` | Gestión completa del sistema |
| `validator` | Aprueba o devuelve formularios |
| `dependency_user` | Diligencia formularios de su dependencia |
| Público | Ve estadísticas sin autenticarse |
