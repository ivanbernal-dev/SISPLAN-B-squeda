# Flujo de Templates — UBPD

## 1. Qué es un Template

Un **template** es la estructura de un formulario. Define:
- Los campos que el usuario debe llenar (`configuracion_campos` en JSONB).
- El indicador de Nivel 1 al que pertenece.
- El indicador de Nivel 2 (sub-indicador agrupador).
- Un código único (e.g. `L1-P1-DPE-2026`).
- Texto markdown descriptivo (`codigo_markdown`).

Modelo: `templates` table → `Template` SQLAlchemy model.

---

## 2. Jerarquía de Indicadores

```
Indicador Nivel 1  (indicadores_nivel1)
  └── Indicador Nivel 2  (indicadores_nivel2)
        └── Template  (templates)
              └── Formularios Respondidos  (formularios_respondidos)
```

- **Nivel 1**: Indicadores estratégicos globales (e.g. "Línea Estratégica de IHE").
- **Nivel 2**: Sub-indicadores que agrupan templates relacionados.
- **Template**: Define la estructura del formulario. Cada sheet de Excel corresponde a un template.

---

## 3. Estructura de Campos (configuracion_campos)

El campo JSONB `configuracion_campos` tiene la siguiente estructura:

```json
{
  "fields": [
    {
      "name": "nombre_campo",
      "label": "Etiqueta visible",
      "tipo": "text|textarea|number|date|file",
      "readonly": false,
      "requerido": true,
      "default": null
    }
  ]
}
```

### Tipos de campo

| Tipo       | Descripción                                          |
|------------|------------------------------------------------------|
| `text`     | Texto de una sola línea                              |
| `textarea` | Texto multilínea                                     |
| `number`   | Valor numérico (entero o decimal)                    |
| `date`     | Fecha en formato ISO (YYYY-MM-DD)                    |
| `file`     | Adjunto de archivo (manejado por `archivos` table)   |

### Campos readonly vs editables

- **readonly: true** → El valor está fijado en `default` y el usuario no puede cambiarlo. Se autocompleta al crear el formulario.
- **readonly: false** → El usuario debe llenar el campo.
- **requerido: true** → El formulario no puede enviarse a revisión si el campo está vacío.

---

## 4. Los 6 Templates de Excel

Cada hoja del archivo Excel UBPD 2026 corresponde a un template:

| Código           | Producto                                                   | Entregables |
|------------------|------------------------------------------------------------|-------------|
| L1-P1-DPE-2026   | Modelo operativo descentralizado de búsqueda humanitaria   | 2           |
| L1-P1-IHE-2026   | Estrategia para la planificación de la IHE                 | 1           |
| L1-P2-IHE-2026   | Sistema SIM Busquemos versión 2.0                          | 3           |
| L1-P3-IHE-2026   | Estrategia de Gestión Integral del Dato                    | 4           |
| L1-P4-IHE-2026   | Estrategia Aportantes Consolidada                          | 1           |
| L1-P5-IHE-2026   | Estrategia Misión identificación                           | 1           |

Todos comparten los mismos campos base readonly (Línea estratégica, Código del Producto, Producto, etc.)
y los mismos campos cuantitativos editables (Variable 1, Variable 2, Calculo formula, etc.).

---

## 5. Creación de Templates (Admin/Validator)

### Via UI (Template Editor)

1. Navegar a `/admin/templates/new` o `/validator/templates/new`.
2. Definir nombre, descripción, Indicador Nivel 1, Indicador Nivel 2, y código único.
3. Usar el editor de campos para agregar/configurar cada campo.
4. Guardar.

### Via Seed Script

```bash
cd backend
python scripts/seed_templates_excel.py
```

El script:
1. Usa el primer Indicador Nivel 1 existente (o lo crea).
2. Crea 6 IndicadorNivel2, uno por template.
3. Crea los 6 templates con toda su configuracion_campos.

---

## 6. Exportar / Importar Templates

Los templates se pueden exportar/importar via los endpoints REST:

- `GET /api/templates` — lista todos los templates activos.
- `GET /api/templates/{id}` — obtiene un template con su configuración completa.
- `POST /api/templates` — crea un nuevo template (requiere rol admin o validator).
- `PUT /api/templates/{id}` — actualiza un template.

---

## 7. Relación con Estadísticas

Cuando un formulario es aprobado, el pipeline de procesamiento puede leer los datos del formulario
usando el `template_id` para calcular los indicadores de Nivel 2 y Nivel 1.

Ver: `FLUJO_PIPELINE_PROCESAMIENTO.md`
