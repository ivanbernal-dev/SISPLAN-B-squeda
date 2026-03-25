# Flujo de Datos de Formularios — UBPD

## 1. Estados de un Formulario

```
draft  →  pending  →  approved
                  ↘  rejected  →  draft (editable de nuevo)
```

| Estado     | Descripción                                              | Editable |
|------------|----------------------------------------------------------|----------|
| `draft`    | Borrador, visible solo para el usuario creador           | Sí       |
| `pending`  | Enviado a revisión, en espera del validador              | No       |
| `approved` | Aprobado por el validador, cuenta en estadísticas        | No       |
| `rejected` | Rechazado con comentario, el usuario puede corregir      | Sí       |

---

## 2. Llenar un Formulario (modo UI)

### Ruta: `/dependencia/forms/new/:templateId`

1. El usuario de dependencia selecciona un template desde la galería.
2. El frontend carga `GET /api/templates/{id}` para obtener la estructura de campos.
3. Los campos readonly se autocompletan con sus valores `default`.
4. El usuario llena los campos editables.
5. **Guardar Borrador**: `POST /api/forms` → crea formulario en estado `draft`.
6. **Autoguardado**: cada 2 minutos, si hay cambios → `PATCH /api/forms/{id}`.
7. **Enviar a Revisión**: `PATCH /api/forms/{id}` + `POST /api/forms/{id}/submit` → cambia a `pending`.

### Validaciones antes de enviar

- Todos los campos con `requerido: true` deben tener valor.
- El `informe_cualitativo` no puede estar vacío.

---

## 3. Carga via Excel (modo bulk)

### Ruta: `/dependencia/forms/new/:templateId` → toggle "Cargar Excel"

#### Paso 1: Descargar ejemplo
```
GET /api/templates/{template_id}/excel-example
```
Genera un `.xlsx` con:
- Fila 1: encabezados (labels de los campos).
- Fila 2: valores de ejemplo con defaults.
- Celdas grises = readonly. Celdas verdes = editables.

#### Paso 2: Llenar el Excel
- El usuario llena las filas de datos (una fila = un formulario).
- Las columnas readonly pueden dejarse con los defaults o modificarse (se ignorarán al cargar).
- La columna "Mes de Reporte" determina la `fecha_usuario`.
- La columna "Informe cualitativo" se mapea al campo `informe_cualitativo`.

#### Paso 3: Subir el Excel
```
POST /api/forms/upload-excel/{template_id}
Content-Type: multipart/form-data
file: <archivo.xlsx>
```

El backend:
1. Lee la primera hoja del Excel con `openpyxl`.
2. Mapea los encabezados a los campos del template por `label`.
3. Crea un `Form` en estado `draft` por cada fila de datos.
4. Marca `cargado_via_excel = true`.
5. Retorna `{"created": N, "form_ids": [...]}`.

---

## 4. Flujo de Validación

### Bandeja del Validador: `/validator/inbox`

El validador ve todos los formularios en estado `pending`.

#### Aprobar:
```
POST /api/validation/{form_id}/approve
```
- Cambia estado a `approved`.
- Registra `validado_por_id` y `fecha_validacion`.
- Puede disparar ejecución del pipeline.

#### Rechazar:
```
POST /api/validation/{form_id}/reject
Body: {"comentario_rechazo": "..."}
```
- Cambia estado a `rejected`.
- El usuario de dependencia recibe el comentario y puede corregir.

---

## 5. Archivos Adjuntos

Los formularios pueden tener archivos adjuntos (campo tipo `file`).

- **Subir archivo**: `POST /api/files/upload` con `form_id` y archivo.
- Los archivos se almacenan en **MinIO** (S3-compatible).
- **Obtener URL firmada**: `GET /api/files/{file_id}/url` → URL temporal para descarga.
- **Eliminar**: `DELETE /api/files/{file_id}`.

Modelo: tabla `archivos`, FK a `formularios_respondidos`.

---

## 6. Descargar Formulario como Excel

Un formulario individual puede descargarse como Excel:

```
GET /api/forms/{form_id}/excel
```

Genera un `.xlsx` con:
- Hoja 1: todos los campos del formulario con sus valores.
- Hoja 2: metadata (ID, template, estado, fecha carga, etc.).

---

## 7. Validación de Formularios cargados via Excel

Los formularios creados vía Excel siguen el mismo flujo de validación:
- Aparecen en la bandeja del validador con la etiqueta "Cargado via Excel".
- El validador puede aprobar o rechazar individualmente.
- Al aprobar, el formulario cuenta en las estadísticas normalmente.

---

## 8. Autocompletado de Campos Readonly

Al crear un formulario (via UI o Excel), el backend autocompleta automáticamente los campos con `readonly: true`:

```python
for field in template.configuracion_campos.get("fields", []):
    if field.get("readonly") and field.get("default") is not None:
        datos.setdefault(field["name"], field["default"])
```

Esto garantiza que campos como "Línea estratégica" o "Código del Producto" siempre tengan los valores correctos.
