# API Endpoints — UBPD Backend (FastAPI)

Base URL: `http://SERVER_IP/api`

## Convenciones
- Autenticación: `Authorization: Bearer <JWT>` en todos los endpoints protegidos
- Respuestas de error: `{ "detail": "mensaje de error" }`
- Paginación: `?page=1&size=20` en listados
- Filtros de fecha: `?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`

---

## AUTH — Autenticación

| Método | Endpoint | Roles | Descripción |
|--------|----------|-------|-------------|
| POST | `/auth/login` | Público | Login con username/password. Retorna JWT |
| POST | `/auth/refresh` | Autenticado | Renovar access token con refresh token |
| POST | `/auth/logout` | Autenticado | Invalidar sesión actual |
| POST | `/auth/change-password` | Autenticado | Cambiar contraseña (requerido en primer login) |

### POST /auth/login
```json
// Request
{ "username": "jgarcia", "password": "mi_clave" }

// Response 200
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "nombre_completo": "Juan García",
    "role": "admin",
    "dependency_id": null
  }
}
```

---

## ADMIN — Gestión de Usuarios y Dependencias

| Método | Endpoint | Roles | Descripción |
|--------|----------|-------|-------------|
| GET | `/admin/users` | admin | Listar todos los usuarios |
| POST | `/admin/users` | admin | Crear usuario |
| GET | `/admin/users/:id` | admin | Ver detalle de usuario |
| PATCH | `/admin/users/:id` | admin | Editar usuario |
| DELETE | `/admin/users/:id` | admin | Desactivar usuario (soft delete) |
| GET | `/admin/dependencies` | admin | Listar dependencias |
| POST | `/admin/dependencies` | admin | Crear dependencia |
| PATCH | `/admin/dependencies/:id` | admin | Editar dependencia |
| GET | `/admin/pipelines/status` | admin | Estado de los últimos pipelines ejecutados |
| GET | `/admin/audit` | admin | Log de auditoría paginado |
| GET | `/admin/stats/overview` | admin | Métricas del sistema (formularios por estado, usuarios activos) |

### POST /admin/users
```json
// Request
{
  "username": "mrojas",
  "nombre_completo": "María Rojas",
  "email": "mrojas@ubpd.gov.co",
  "role": "dependency_user",
  "dependency_id": "uuid-dependencia"
}

// Response 201
{
  "id": "uuid-nuevo-usuario",
  "username": "mrojas",
  "requires_password_change": true,
  "temp_password": "Ubpd@2024"
}
```

---

## TEMPLATES — Gestión de Plantillas de Formularios

| Método | Endpoint | Roles | Descripción |
|--------|----------|-------|-------------|
| GET | `/templates` | admin, validator | Listar todos los templates |
| POST | `/templates` | admin, validator | Crear template desde Markdown |
| GET | `/templates/:id` | admin, validator, dependency_user | Ver template |
| PATCH | `/templates/:id` | admin, validator | Editar template |
| DELETE | `/templates/:id` | admin | Desactivar template |
| POST | `/templates/preview` | admin, validator | Previsualizar JSONB generado desde Markdown |
| GET | `/templates/by-dependency/:dep_id` | dependency_user | Templates disponibles para una dependencia |

### POST /templates
```json
// Request
{
  "nombre": "Formulario L1-P1-IHE",
  "descripcion": "Indicador de Hallazgos y Evidencias - Primer Periodo",
  "indicador_nivel1_id": 1,
  "codigo_markdown": "## L1-P1-IHE\n\n| Campo | Tipo | Bloqueado | Default |\n|...",
  "configuracion_campos": {
    "fields": [
      { "name": "municipio", "label": "Municipio", "type": "text", "readonly": true, "default": "Bogotá" },
      { "name": "codigo_caso", "label": "Código del Caso", "type": "text", "readonly": false, "default": "" }
    ]
  }
}
```

---

## FORMS — Formularios (Usuario de Dependencia)

| Método | Endpoint | Roles | Descripción |
|--------|----------|-------|-------------|
| GET | `/forms` | dependency_user | Mis formularios (todos los estados) |
| POST | `/forms` | dependency_user | Crear nuevo formulario (draft) |
| GET | `/forms/:id` | dependency_user, validator, admin | Ver formulario |
| PATCH | `/forms/:id` | dependency_user | Actualizar formulario (solo en draft/rejected) |
| POST | `/forms/:id/submit` | dependency_user | Enviar a validación (draft → pending) |
| DELETE | `/forms/:id` | dependency_user | Eliminar borrador (solo draft) |
| GET | `/forms/inbox` | dependency_user | Mis formularios con filtros de estado |

---

## FILES — Archivos Adjuntos

| Método | Endpoint | Roles | Descripción |
|--------|----------|-------|-------------|
| POST | `/files/upload/:form_id` | dependency_user | Subir archivo(s) a formulario |
| GET | `/files/:file_id/url` | dependency_user, validator, admin | Obtener pre-signed URL para descarga |
| DELETE | `/files/:file_id` | dependency_user | Eliminar archivo (solo en draft/rejected) |

### POST /files/upload/:form_id
- Content-Type: `multipart/form-data`
- Máximo por archivo: configurable (`.env`: `MAX_UPLOAD_MB`)
- Formatos aceptados: PDF, JPG, PNG, DOCX (configurable)

---

## VALIDATION — Validación (Validador)

| Método | Endpoint | Roles | Descripción |
|--------|----------|-------|-------------|
| GET | `/validation/pending` | validator | Bandeja de pendientes, filtrable por fecha |
| GET | `/validation/history` | validator | Historial de formularios procesados |
| PATCH | `/validation/:id/approve` | validator | Aprobar formulario → dispara pipeline |
| PATCH | `/validation/:id/reject` | validator | Rechazar formulario (requiere comentario) |

### PATCH /validation/:id/reject
```json
// Request
{
  "comentario": "Falta adjuntar el acta de comité. El código de caso no coincide con el registro interno."
}

// Response 200
{
  "id": "uuid-form",
  "estado": "rejected",
  "comentario_rechazo": "Falta adjuntar..."
}
```

---

## STATS — Estadísticas Públicas

| Método | Endpoint | Roles | Descripción |
|--------|----------|-------|-------------|
| GET | `/stats/global` | Público | Nivel 1: indicadores globales con completitud |
| GET | `/stats/by-template` | Público | Nivel 2: completitud por template para un indicador |
| GET | `/stats/detail` | Público | Nivel 3: lista de formularios validados (tabla) |
| GET | `/stats/export` | Público | Exportar Nivel 3 como Excel (.xlsx) |
| GET | `/stats/indicators` | Público | Lista de indicadores disponibles para el selector |

### GET /stats/global
```
Query params:
  start_date=2024-01-01
  end_date=2024-12-31

Response 200:
[
  {
    "indicador_id": 1,
    "nombre": "Línea Estratégica 1 - Primer Indicador",
    "completitud_promedio": 78.5,
    "total_formularios": 142,
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  }
]
```

### GET /stats/by-template
```
Query params:
  indicador_id=1
  start_date=2024-01-01
  end_date=2024-12-31

Response 200:
[
  {
    "template_id": "uuid",
    "nombre": "L1-P1-IHE",
    "completitud": 82.3,
    "total_formularios": 47
  }
]
```

### GET /stats/detail
```
Query params:
  template_id=uuid
  start_date=2024-01-01
  end_date=2024-12-31
  page=1
  size=20
  search=bogota  (opcional)

Response 200:
{
  "total": 47,
  "page": 1,
  "items": [
    {
      "id": "uuid",
      "fecha_referencia": "2024-03-15",
      "dependencia": "Regional Antioquia",
      "informe_cualitativo": "Se realizó...",
      "datos_dinamicos": { "municipio": "Medellín", ... },
      "archivos_count": 3
    }
  ]
}
```

### GET /stats/export
```
Query params: (mismos que /stats/detail sin paginación)
Response: archivo .xlsx como stream
Content-Disposition: attachment; filename="estadisticas_2024.xlsx"
```

---

## Códigos de Respuesta

| Código | Significado |
|--------|-------------|
| 200 | OK |
| 201 | Creado exitosamente |
| 400 | Datos inválidos en el request |
| 401 | No autenticado |
| 403 | Sin permisos para esta acción |
| 404 | Recurso no encontrado |
| 422 | Error de validación de schema |
| 500 | Error interno del servidor |
