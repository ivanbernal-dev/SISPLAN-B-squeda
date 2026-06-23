# Arquitectura del Sistema UBPD

## Visión General

El sistema opera en una **red Ethernet cerrada (air-gapped)** sin acceso a internet.
Todos los servicios corren como contenedores Docker orquestados con Docker Compose en un único servidor.

```
┌─────────────────────────────────────────────────────────────────┐
│                        RED LOCAL ETHERNET                       │
│                                                                 │
│   ┌──────────┐    ┌─────────────────────────────────────────┐  │
│   │ Clientes │───▶│              NGINX (Reverse Proxy)       │  │
│   │(Browsers)│    │              Puerto 80 (HTTP)              │  │
│   └──────────┘    └────────────┬──────────────┬─────────────┘  │
│                                │              │                 │
│              ┌─────────────────▼──┐    ┌──────▼─────────────┐  │
│              │  FRONTEND (Vue.js) │    │  BACKEND (FastAPI) │  │
│              │   Nginx estático   │    │   Puerto 8000      │  │
│              │   Puerto 3000      │    └──────┬─────────────┘  │
│              └────────────────────┘           │                │
│                                        ┌──────▼──────────────┐ │
│                                        │     SERVICIOS       │ │
│                                        │                     │ │
│                              ┌─────────▼──┐  ┌────────────┐ │ │
│                              │ PostgreSQL  │  │   MinIO    │ │ │
│                              │ Puerto 5432 │  │ Puerto 9000│ │ │
│                              └────────────┘  └────────────┘ │ │
│                                        │                     │ │
│                              ┌─────────▼──┐                 │ │
│                              │   Valkey    │                 │ │
│                              │ Puerto 6379 │                 │ │
│                              └─────────────┘                │ │
│                                        │                     │ │
│                              ┌─────────▼──┐                 │ │
│                              │   Celery   │                 │ │
│                              │  Worker    │                 │ │
│                              └────────────┘                 │ │
│                                        └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Servicios Docker

### 1. `nginx` — Proxy Inverso
- **Imagen**: `nginx:1.25-alpine`
- **Función**: Punto de entrada único. Enruta `/api/` al backend y `/` al frontend.
- **Puertos expuestos**: `80` (HTTP; TLS no configurado en esta versión)

### 2. `frontend` — Aplicación Vue.js
- **Imagen**: Build multistage (Node → Nginx estático)
- **Función**: Sirve el bundle compilado de Vue.js. Todas las dependencias (fuentes, íconos, librerías) embebidas en el build.
- **Puerto interno**: `3000`
- **Nota**: No hace peticiones a CDNs externos.

### 3. `backend` — API FastAPI
- **Imagen**: `python:3.12-slim`
- **Función**: API REST principal. Gestión de autenticación JWT, formularios, pipelines de estadísticas y uploads a MinIO.
- **Puerto interno**: `8000`
- **Workers**: Uvicorn con múltiples workers según carga.

### 4. `postgres` — Base de Datos
- **Imagen**: `postgres:16-alpine`
- **Función**: Almacena usuarios, dependencias, templates (JSONB), formularios, estadísticas precalculadas y auditoría.
- **Puerto**: `5432` (interno, no expuesto al exterior)
- **Persistencia**: Volumen Docker `postgres_data`

### 5. `minio` — Almacenamiento de Archivos
- **Imagen**: `minio/minio:latest`
- **Función**: Almacena los archivos adjuntos de los formularios (PDFs, imágenes, documentos). Compatible con S3 API.
- **Puertos internos**: `9000` (API), `9001` (Consola Web)
- **Persistencia**: Volumen Docker `minio_data`

### 6. `valkey` — Caché y Cola de Tareas
- **Imagen**: `valkey/valkey:7-alpine`
- **Función**: Broker de mensajes para Celery. Caché de resultados de pipelines. Fork open-source de Redis, 100% compatible con el cliente `redis` de Python.
- **Puerto**: `6379` (interno)

### 7. `celery` — Worker de Tareas
- **Imagen**: Misma imagen que `backend`
- **Función**: Ejecuta los pipelines de cálculo de indicadores estadísticos de forma asíncrona tras la aprobación de formularios.
- **Tareas programadas**: Recálculo periódico de tablas materializadas de estadísticas.

## Red Interna Docker

Todos los servicios se comunican a través de la red interna `ubpd_network` (tipo `bridge`).
Ningún servicio excepto `nginx` expone puertos al host por defecto (salvo MinIO console para administración).

## Flujo de Datos General

```
Usuario Dependencia
        │
        ▼
   [Llena formulario]
        │
        ▼
   POST /api/forms/submit
        │
        ▼
   Backend guarda en PostgreSQL (status: pending)
   + archivos en MinIO
        │
        ▼
   Validador recibe notificación
        │
        ├─── RECHAZA ──▶ Status: rejected + comentario
        │                       │
        │               ◀───────┘
        │               (Regresa al usuario de dependencia)
        │
        └─── APRUEBA ─▶ Status: approved
                                │
                                ▼
                       Celery Task disparado
                                │
                                ▼
                    Pipeline calcula indicadores
                    Actualiza `fact_stats` en PostgreSQL
                                │
                                ▼
                    Sitio Público lee `fact_stats`
                    y muestra Gauges (Nivel 1, 2, 3)
```

## Ciclo de Vida del Formulario

```
BORRADOR (draft)
    │
    ▼ [Usuario envía]
PENDIENTE (pending)
    │
    ├── [Validador rechaza] ──▶ DEVUELTO (rejected)
    │                                │
    │                          [Usuario corrige y reenvía]
    │                                │
    │                          PENDIENTE (pending) ◀──┘
    │
    └── [Validador aprueba] ──▶ APROBADO (approved)
                                        │
                                 [Pipeline automático]
                                        │
                                 DATOS EN ESTADÍSTICAS
```

## Consideraciones de Red Local (Air-Gapped)

1. **Sin CDN**: Todas las librerías JS/CSS van en el bundle de Vite.
2. **Fuentes locales**: Barlow, Montserrat, Playfair Display como archivos `.woff2`.
3. **Imágenes Docker**: Pre-descargadas y guardadas como `.tar` para transfer manual.
4. **Tráfico web**: Por ahora corre sobre HTTP en intranet; TLS opcional en despliegues futuros.
5. **NTP local**: Se recomienda configurar servidor de tiempo en la red para sincronía de timestamps.
6. **Backup**: Scripts de backup de volúmenes Docker programables con cron.

## Seguridad

- Autenticación: JWT firmado con `SECRET_KEY` local (HS256)
- Tokens: Access Token (30 min) + Refresh Token (7 días)
- Contraseñas: Hash con `bcrypt` (costo 12)
- Capa de transporte: HTTP en esta configuración; conviene planear TLS cuando el entorno lo exija
- RBAC: Cada endpoint verifica el rol del JWT antes de procesar
- MinIO: Buckets privados, acceso solo via pre-signed URLs del backend
