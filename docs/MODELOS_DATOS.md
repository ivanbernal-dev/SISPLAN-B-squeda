# Modelos de Datos — UBPD

## Esquema General de PostgreSQL

```
┌──────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│  dependencias │    │     usuarios     │    │      templates      │
│──────────────│    │──────────────────│    │─────────────────────│
│ id (UUID PK) │◄───│ dependency_id FK │    │ id (UUID PK)        │
│ nombre       │    │ id (UUID PK)     │    │ nombre              │
│ codigo       │    │ username         │    │ descripcion         │
│ descripcion  │    │ password_hash    │    │ indicador_nivel1_id │──▶ indicadores_nivel1
│ activa       │    │ nombre_completo  │    │ codigo_markdown     │
│ created_at   │    │ email            │    │ configuracion JSONB │
└──────────────┘    │ role (enum)      │    │ version             │
                    │ activo           │    │ created_by_id FK    │──▶ usuarios
                    │ created_at       │    │ created_at          │
                    │ updated_at       │    │ updated_at          │
                    │ last_login       │    └─────────────────────┘
                    └──────────────────┘

┌───────────────────────┐    ┌─────────────────────────────┐
│  indicadores_nivel1   │    │    formularios_respondidos  │
│───────────────────────│    │─────────────────────────────│
│ id (INT PK)           │    │ id (UUID PK)                │
│ nombre                │◄───│ plantilla_id FK             │
│ descripcion           │    │ usuario_id FK               │──▶ usuarios
│ formula_tipo (enum)   │    │ dependency_id FK            │──▶ dependencias
│ peso                  │    │ datos_dinamicos JSONB       │
│ activo                │    │ informe_cualitativo TEXT    │
└───────────────────────┘    │ fecha_usuario DATE          │
                             │ fecha_carga TIMESTAMP       │
                             │ fecha_edicion TIMESTAMP     │
                             │ estado (enum)               │
                             │ comentario_rechazo TEXT     │
                             │ validado_por_id FK          │──▶ usuarios
                             │ fecha_validacion TIMESTAMP  │
                             └─────────────────────────────┘
                                          │
                             ┌────────────▼────────────────┐
                             │        archivos             │
                             │─────────────────────────────│
                             │ id (UUID PK)                │
                             │ formulario_id FK            │
                             │ nombre_original             │
                             │ nombre_minio                │
                             │ bucket                      │
                             │ ruta_minio                  │
                             │ tipo_mime                   │
                             │ tamaño_bytes                │
                             │ uploaded_at                 │
                             └─────────────────────────────┘

┌──────────────────────┐    ┌──────────────────────────────┐
│     fact_stats       │    │        audit_logs            │
│──────────────────────│    │──────────────────────────────│
│ id (UUID PK)         │    │ id (UUID PK)                 │
│ formulario_id FK     │    │ usuario_id FK                │
│ template_id FK       │    │ accion                       │
│ indicador_id FK      │    │ entidad_tipo                 │
│ dependency_id FK     │    │ entidad_id                   │
│ campos_llenos INT    │    │ detalle JSONB                │
│ campos_totales INT   │    │ ip_address                   │
│ completitud DECIMAL  │    │ created_at                   │
│ fecha_referencia     │    └──────────────────────────────┘
│ fecha_aprobacion     │
│ calculado_en         │    ┌──────────────────────────────┐
└──────────────────────┘    │     pipeline_runs            │
                            │──────────────────────────────│
                            │ id (UUID PK)                 │
                            │ tipo                         │
                            │ estado (enum)                │
                            │ formulario_id FK (nullable)  │
                            │ detalles JSONB               │
                            │ iniciado_en                  │
                            │ terminado_en                 │
                            └──────────────────────────────┘
```

---

## Tablas Detalladas

### `dependencias`
```sql
CREATE TABLE dependencias (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre      VARCHAR(255) NOT NULL,
    codigo      VARCHAR(50) UNIQUE NOT NULL,
    descripcion TEXT,
    activa      BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);
```

### `usuarios`
```sql
CREATE TYPE user_role AS ENUM ('admin', 'validator', 'dependency_user');

CREATE TABLE usuarios (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username        VARCHAR(100) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,       -- bcrypt hash
    nombre_completo VARCHAR(255) NOT NULL,
    email           VARCHAR(255) UNIQUE,
    role            user_role NOT NULL,
    dependency_id   UUID REFERENCES dependencias(id),  -- NULL para admin/validator
    activo          BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),
    last_login      TIMESTAMP
);
```

### `indicadores_nivel1`
```sql
CREATE TYPE formula_tipo AS ENUM ('promedio_simple', 'promedio_ponderado', 'conteo', 'personalizado');

CREATE TABLE indicadores_nivel1 (
    id            SERIAL PRIMARY KEY,
    nombre        VARCHAR(255) NOT NULL,
    descripcion   TEXT,
    formula_tipo  formula_tipo DEFAULT 'promedio_simple',
    peso          DECIMAL(5,2) DEFAULT 1.0,
    activo        BOOLEAN DEFAULT TRUE
);
```

### `templates`
```sql
CREATE TABLE templates (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre                VARCHAR(255) NOT NULL,
    descripcion           TEXT,
    indicador_nivel1_id   INT REFERENCES indicadores_nivel1(id),
    codigo_markdown       TEXT NOT NULL,
    -- JSONB: { "fields": [{ "name": "...", "type": "text|number|date|select", "readonly": true, "default": "..." }] }
    configuracion_campos  JSONB NOT NULL DEFAULT '{}',
    version               INT DEFAULT 1,
    activo                BOOLEAN DEFAULT TRUE,
    created_by_id         UUID REFERENCES usuarios(id),
    created_at            TIMESTAMP DEFAULT NOW(),
    updated_at            TIMESTAMP DEFAULT NOW()
);
```

#### Ejemplo de `configuracion_campos` JSONB
```json
{
  "fields": [
    {
      "name": "municipio",
      "label": "Municipio",
      "type": "text",
      "readonly": true,
      "default": "Bogotá D.C.",
      "required": true
    },
    {
      "name": "codigo_caso",
      "label": "Código del Caso",
      "type": "text",
      "readonly": false,
      "default": "",
      "required": true
    },
    {
      "name": "fecha_hecho",
      "label": "Fecha del Hecho",
      "type": "date",
      "readonly": false,
      "default": null,
      "required": true
    },
    {
      "name": "numero_personas",
      "label": "Número de Personas",
      "type": "number",
      "readonly": false,
      "default": null,
      "required": true
    }
  ]
}
```

### `formularios_respondidos`
```sql
CREATE TYPE form_status AS ENUM ('draft', 'pending', 'approved', 'rejected');

CREATE TABLE formularios_respondidos (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plantilla_id         UUID NOT NULL REFERENCES templates(id),
    usuario_id           UUID NOT NULL REFERENCES usuarios(id),
    dependency_id        UUID NOT NULL REFERENCES dependencias(id),
    -- JSONB: { "municipio": "Bogotá", "codigo_caso": "2024-001", ... }
    datos_dinamicos      JSONB NOT NULL DEFAULT '{}',
    informe_cualitativo  TEXT,
    fecha_usuario        DATE DEFAULT CURRENT_DATE,
    fecha_carga          TIMESTAMP DEFAULT NOW(),
    fecha_edicion        TIMESTAMP DEFAULT NOW(),
    estado               form_status DEFAULT 'draft',
    comentario_rechazo   TEXT,
    validado_por_id      UUID REFERENCES usuarios(id),
    fecha_validacion     TIMESTAMP,
    CONSTRAINT chk_rechazo CHECK (
        estado != 'rejected' OR comentario_rechazo IS NOT NULL
    )
);
```

### `archivos`
```sql
CREATE TABLE archivos (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    formulario_id    UUID NOT NULL REFERENCES formularios_respondidos(id) ON DELETE CASCADE,
    nombre_original  VARCHAR(500) NOT NULL,
    nombre_minio     VARCHAR(500) NOT NULL,    -- nombre único en MinIO
    bucket           VARCHAR(100) NOT NULL DEFAULT 'ubpd-formularios',
    ruta_minio       VARCHAR(1000) NOT NULL,   -- {dependency_id}/{form_id}/{filename}
    tipo_mime        VARCHAR(100),
    tamaño_bytes     BIGINT,
    uploaded_at      TIMESTAMP DEFAULT NOW()
);
```

### `fact_stats` (Tabla de Hechos para Estadísticas)
```sql
CREATE TABLE fact_stats (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    formulario_id     UUID NOT NULL REFERENCES formularios_respondidos(id),
    template_id       UUID NOT NULL REFERENCES templates(id),
    indicador_id      INT NOT NULL REFERENCES indicadores_nivel1(id),
    dependency_id     UUID NOT NULL REFERENCES dependencias(id),
    campos_llenos     INT NOT NULL,
    campos_totales    INT NOT NULL,
    completitud       DECIMAL(5,2) NOT NULL,  -- porcentaje 0-100
    fecha_referencia  DATE NOT NULL,
    fecha_aprobacion  TIMESTAMP NOT NULL,
    calculado_en      TIMESTAMP DEFAULT NOW()
);

-- Índices para consultas de estadísticas por rango de fechas
CREATE INDEX idx_fact_stats_fecha ON fact_stats(fecha_aprobacion);
CREATE INDEX idx_fact_stats_indicador ON fact_stats(indicador_id);
CREATE INDEX idx_fact_stats_template ON fact_stats(template_id);
```

### `audit_logs`
```sql
CREATE TABLE audit_logs (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id   UUID REFERENCES usuarios(id),
    accion       VARCHAR(100) NOT NULL,  -- 'LOGIN', 'FORM_SUBMIT', 'FORM_APPROVE', etc.
    entidad_tipo VARCHAR(50),            -- 'formulario', 'usuario', 'template'
    entidad_id   UUID,
    detalle      JSONB DEFAULT '{}',
    ip_address   INET,
    created_at   TIMESTAMP DEFAULT NOW()
);
```

### `pipeline_runs`
```sql
CREATE TYPE pipeline_status AS ENUM ('running', 'success', 'error');

CREATE TABLE pipeline_runs (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo           VARCHAR(100) NOT NULL,    -- 'form_approved', 'scheduled_recalc'
    estado         pipeline_status DEFAULT 'running',
    formulario_id  UUID REFERENCES formularios_respondidos(id),
    detalles       JSONB DEFAULT '{}',       -- errores, estadísticas de la ejecución
    iniciado_en    TIMESTAMP DEFAULT NOW(),
    terminado_en   TIMESTAMP
);
```

---

## Estrategia de Consultas para Estadísticas

### Nivel 1 — Indicadores Globales
```sql
-- Completitud promedio por indicador en un rango de fechas
SELECT
    i.id,
    i.nombre,
    AVG(fs.completitud) AS completitud_promedio,
    COUNT(fs.id) AS total_formularios
FROM fact_stats fs
JOIN indicadores_nivel1 i ON fs.indicador_id = i.id
WHERE fs.fecha_aprobacion BETWEEN :start_date AND :end_date
GROUP BY i.id, i.nombre;
```

### Nivel 2 — Desagregación por Template
```sql
-- Completitud por template para un indicador en un rango de fechas
SELECT
    t.id,
    t.nombre,
    AVG(fs.completitud) AS completitud,
    COUNT(fs.id) AS total_formularios
FROM fact_stats fs
JOIN templates t ON fs.template_id = t.id
WHERE fs.indicador_id = :indicador_id
  AND fs.fecha_aprobacion BETWEEN :start_date AND :end_date
GROUP BY t.id, t.nombre;
```

### Nivel 3 — Detalle Operativo
```sql
-- Lista de formularios validados por template
SELECT
    fr.id,
    fr.fecha_usuario,
    fr.fecha_carga,
    fr.datos_dinamicos,
    fr.informe_cualitativo,
    d.nombre AS dependencia,
    u.nombre_completo AS usuario
FROM formularios_respondidos fr
JOIN dependencias d ON fr.dependency_id = d.id
JOIN usuarios u ON fr.usuario_id = u.id
WHERE fr.plantilla_id = :template_id
  AND fr.estado = 'approved'
  AND fr.fecha_validacion BETWEEN :start_date AND :end_date
ORDER BY fr.fecha_validacion DESC;
```
