# Requerimientos Funcionales por Rol — UBPD

## Contexto

Sistema para la **Unidad de Búsqueda de Personas Dadas por Desaparecidas (UBPD)**.
Gestiona formularios de la **Línea Estratégica No. 1** organizados por indicadores.
Operable en **red local sin internet**.

---

## RF-INF — Infraestructura y Despliegue

| ID | Requerimiento |
|----|---------------|
| RF-INF-01 | El sistema debe arrancar con un solo comando: `docker compose up -d` |
| RF-INF-02 | Todas las librerías JS, fuentes y assets deben estar embebidos en el build (sin CDN) |
| RF-INF-03 | Los datos deben persistir en volúmenes Docker ante reinicios del servidor |
| RF-INF-04 | El sistema debe funcionar con HTTPS usando certificados autofirmados en intranet |
| RF-INF-05 | Las imágenes Docker deben poder exportarse/importarse sin internet (`docker save/load`) |
| RF-INF-06 | La aplicación debe soportar al menos 50 usuarios concurrentes en una red Ethernet |

---

## RF-AUTH — Autenticación y Autorización

| ID | Requerimiento |
|----|---------------|
| RF-AUTH-01 | Autenticación mediante usuario y contraseña con JWT (sin proveedores externos) |
| RF-AUTH-02 | Contraseñas almacenadas como hash `bcrypt` (nunca texto plano) |
| RF-AUTH-03 | El token JWT debe contener `user_id`, `role` y `dependency_id` |
| RF-AUTH-04 | Access Token: 30 minutos. Refresh Token: 7 días |
| RF-AUTH-05 | El sistema debe implementar RBAC con los roles: `admin`, `validator`, `dependency_user` |
| RF-AUTH-06 | Las rutas de la API deben estar protegidas según el rol requerido |
| RF-AUTH-07 | El sitio público de estadísticas NO requiere autenticación |

---

## RF-ADM — Usuario Administrador

| ID | Requerimiento |
|----|---------------|
| RF-ADM-01 | Crear, editar y desactivar cuentas de `validator` y `dependency_user` |
| RF-ADM-02 | Asignar a cada usuario la dependencia a la que pertenece |
| RF-ADM-03 | Crear y editar dependencias (áreas/unidades organizativas) |
| RF-ADM-04 | Crear templates de formularios usando sintaxis Markdown extendida |
| RF-ADM-05 | Definir qué campos del template son `readonly` (bloqueados) y sus valores por defecto |
| RF-ADM-06 | Asignar cada template a un indicador del Nivel 1 de estadísticas |
| RF-ADM-07 | Visualizar el estado de los pipelines de cálculo de estadísticas (activo/error) |
| RF-ADM-08 | Consultar logs de auditoría: quién cargó qué y cuándo |
| RF-ADM-09 | Ver métricas básicas del sistema (formularios por estado, usuarios activos) |

---

## RF-VAL — Usuario Validador

| ID | Requerimiento |
|----|---------------|
| RF-VAL-01 | Crear templates de formularios (igual que el administrador) |
| RF-VAL-02 | Visualizar bandeja de entrada con formularios en estado `pending`, filtrable por fecha |
| RF-VAL-03 | Ver los datos del formulario en modo lectura (vista dividida: datos + archivos) |
| RF-VAL-04 | Descargar o previsualizar los archivos adjuntos al formulario |
| RF-VAL-05 | **Aprobar** un formulario: cambia estado a `approved` y dispara pipeline de estadísticas |
| RF-VAL-06 | **Rechazar** un formulario: requiere comentario obligatorio; cambia estado a `rejected` |
| RF-VAL-07 | Consultar historial de formularios que ya procesó, con filtro por fecha |
| RF-VAL-08 | El sistema debe indicar claramente el número de formularios pendientes en el menú |

---

## RF-DEP — Usuario de Dependencia

| ID | Requerimiento |
|----|---------------|
| RF-DEP-01 | Ver solo los templates de formularios asignados a su dependencia |
| RF-DEP-02 | Iniciar un nuevo formulario a partir de un template (con auto-llenado de campos por defecto) |
| RF-DEP-03 | Los campos marcados como `readonly` en el template deben mostrarse pero no editarse |
| RF-DEP-04 | Gestionar tres fechas por formulario: carga (automática), última edición (automática), fecha de referencia (manual, por defecto hoy) |
| RF-DEP-05 | Adjuntar múltiples archivos por formulario (carga a MinIO) con barra de progreso |
| RF-DEP-06 | Incluir un campo de **Informe Cualitativo** (textarea) en cada formulario |
| RF-DEP-07 | Guardar formularios en estado `draft` antes de enviar a validación |
| RF-DEP-08 | Enviar formulario a validación (cambia estado a `pending`) |
| RF-DEP-09 | Ver bandeja de trámites con sus estados: Borrador, Enviado, Devuelto, Aprobado |
| RF-DEP-10 | Si el formulario es devuelto, ver el comentario del validador y poder corregirlo y reenviarlo |
| RF-DEP-11 | No puede editar formularios ya aprobados |

---

## RF-PUB — Sitio Público de Estadísticas

| ID | Requerimiento |
|----|---------------|
| RF-PUB-01 | Acceso sin autenticación |
| RF-PUB-02 | Filtro global de rango de fechas que afecta los 3 niveles simultáneamente |
| RF-PUB-03 | Presets rápidos de fecha: Este mes, Último trimestre, Año actual |
| RF-PUB-04 | **Nivel 1**: Gráficos Gauge (velocímetro) por grupo de indicadores; cálculo: promedio ponderado de los indicadores del Nivel 2 |
| RF-PUB-05 | **Nivel 2**: Al hacer clic en un indicador del Nivel 1, mostrar Gauges de completitud por template; fórmula: `C = (campos_llenos / campos_totales_editables) × 100` |
| RF-PUB-06 | **Nivel 3**: Al hacer clic en un template del Nivel 2, mostrar tabla detallada de formularios validados con Informe Cualitativo y enlace a soportes |
| RF-PUB-07 | La tabla del Nivel 3 debe permitir búsqueda y filtrado por columna |
| RF-PUB-08 | El botón "Exportar a Excel" en Nivel 3 debe respetar el filtro de fechas activo |
| RF-PUB-09 | El filtro de fechas debe persistir al navegar entre niveles (Pinia / URL params) |
| RF-PUB-10 | El sitio debe verse correctamente en tablets (responsive) |

---

## RF-TEMP — Sistema de Templates (Markdown)

| ID | Requerimiento |
|----|---------------|
| RF-TEMP-01 | Admin y Validador pueden crear templates desde un editor Markdown con preview en tiempo real |
| RF-TEMP-02 | El Markdown define: nombre del campo, tipo (texto/número/fecha/select), si es `readonly`, valor por defecto |
| RF-TEMP-03 | Todo formulario tiene automáticamente: campo "Informe Cualitativo" y sección de carga de archivos |
| RF-TEMP-04 | El backend parsea el Markdown y genera un esquema JSONB almacenado en PostgreSQL |
| RF-TEMP-05 | El template puede asignarse a un indicador del Nivel 1 |
| RF-TEMP-06 | El template puede ser editado sin afectar formularios ya respondidos |
| RF-TEMP-07 | Deben poder crearse nuevos templates para futuros indicadores |

---

## RF-PIPE — Pipelines de Cálculo

| ID | Requerimiento |
|----|---------------|
| RF-PIPE-01 | Al aprobarse un formulario, se dispara automáticamente una tarea Celery |
| RF-PIPE-02 | La tarea extrae los datos del formulario y actualiza la tabla `fact_stats` |
| RF-PIPE-03 | Los indicadores del Nivel 1 y 2 se calculan sobre la tabla `fact_stats` (no en tiempo real) |
| RF-PIPE-04 | Los cálculos NO son siempre promedios simples; cada indicador tiene su propia lógica en `services/calculators/` |
| RF-PIPE-05 | Debe existir un recálculo periódico programado (cada 10 minutos) como respaldo |
| RF-PIPE-06 | El Admin puede ver el estado del último pipeline ejecutado (éxito/error/timestamp) |

---

## RF-FILE — Gestión de Archivos

| ID | Requerimiento |
|----|---------------|
| RF-FILE-01 | Los archivos se almacenan en MinIO (S3-compatible local) |
| RF-FILE-02 | El backend genera pre-signed URLs para acceso temporal a los archivos |
| RF-FILE-03 | El frontend debe mostrar miniatura si es imagen, icono si es PDF u otro formato |
| RF-FILE-04 | El frontend debe validar el tamaño máximo antes de subir (configurable en `.env`) |
| RF-FILE-05 | Los archivos se organizan en MinIO bajo: `bucket/{dependency_id}/{form_id}/` |
| RF-FILE-06 | El validador puede previsualizar archivos sin descargarlos (visor embebido para PDF e imágenes) |
