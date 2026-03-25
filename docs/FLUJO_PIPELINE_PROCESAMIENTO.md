# Flujo del Pipeline de Procesamiento — UBPD

## 1. Qué es el Pipeline Visual

El sistema incluye un **motor de pipelines visual** que permite a los administradores
definir cómo se procesan los datos de los formularios para calcular los indicadores.

Los pipelines se definen visualmente en el editor (`/admin/pipeline-editor/:id`)
y se ejecutan para calcular valores de Nivel 2 y Nivel 1.

---

## 2. Tipos de Nodos

| Tipo              | Color    | Descripción                                                     |
|-------------------|----------|-----------------------------------------------------------------|
| `data_source`     | Azul     | Lee formularios aprobados de un template → DataFrame            |
| `processor`       | Púrpura  | Ejecuta código Python/pandas para transformar el DataFrame      |
| `nivel2_output`   | Naranja  | Agrega el DataFrame → genera valor escalar para un Indicador N2 |
| `nivel1_output`   | Verde    | Agrega valores N2 → valor final del Indicador N1                |

---

## 3. Estructura del Grafo (JSONB)

El campo `grafo` en `pipeline_definiciones` tiene la forma:

```json
{
  "nodes": [
    {
      "id": "n1",
      "type": "data_source",
      "position": {"x": 100, "y": 100},
      "data": {
        "nombre": "Formularios L1-P1-DPE",
        "template_id": "uuid-del-template"
      }
    },
    {
      "id": "n2",
      "type": "processor",
      "position": {"x": 350, "y": 100},
      "data": {
        "nombre": "Calcular promedio",
        "codigo_python": "result = df['calculo_formula'].mean()"
      }
    },
    {
      "id": "n3",
      "type": "nivel2_output",
      "position": {"x": 600, "y": 100},
      "data": {
        "nombre": "Salida N2 — DPE",
        "indicador_nivel2_id": 1,
        "aggregation": "mean"
      }
    },
    {
      "id": "n4",
      "type": "nivel1_output",
      "position": {"x": 850, "y": 100},
      "data": {
        "nombre": "Indicador Línea 1",
        "indicador_nivel1_id": 1
      }
    }
  ],
  "edges": [
    {"id": "e1", "source": "n1", "target": "n2"},
    {"id": "e2", "source": "n2", "target": "n3"},
    {"id": "e3", "source": "n3", "target": "n4"}
  ]
}
```

---

## 4. Cómo Escribir Código en Nodos `processor`

El código se ejecuta en un sandbox restringido con:
- **`df`**: DataFrame de pandas con los datos de entrada (del nodo anterior).
- **`pd`**: librería pandas.
- **`result`**: variable donde se debe guardar el resultado.

### Ejemplo: calcular promedio de una columna

```python
# Filtrar filas con datos válidos
df_clean = df[df['calculo_formula'].notna()]
# Convertir a numérico
valores = pd.to_numeric(df_clean['calculo_formula'], errors='coerce').dropna()
# Calcular promedio
result = valores.mean() if len(valores) > 0 else 0.0
```

### Ejemplo: filtrar por mes

```python
import datetime
# Filtrar por año actual
df['_fecha'] = pd.to_datetime(df['_fecha_usuario'], errors='coerce')
df_2026 = df[df['_fecha'].dt.year == 2026]
result = df_2026['calculo_formula'].mean()
```

### Variables disponibles en `df`

Los formularios aprobados se cargan con estas columnas meta:
- `_form_id`: UUID del formulario.
- `_fecha_usuario`: fecha de referencia del formulario.
- `_dependency_id`: UUID de la dependencia.
- `_informe_cualitativo`: texto del informe.
- Todas las columnas del `datos_dinamicos` del formulario (campos del template).

### Funciones builtins disponibles en el sandbox

`len`, `range`, `enumerate`, `zip`, `list`, `dict`, `str`, `int`, `float`, `bool`,
`round`, `sum`, `min`, `max`, `abs`, `print`, `isinstance`, `type`.

---

## 5. Nodo `nivel2_output`

- Si tiene `codigo_python`, lo ejecuta para calcular el valor escalar.
- Si no tiene código, usa la agregación por defecto sobre la columna `calculo_formula`:
  - `mean` (promedio) — por defecto.
  - `sum` (suma).
  - `count` (conteo de valores no nulos).
- El valor resultante se asocia al `indicador_nivel2_id`.

---

## 6. Nodo `nivel1_output`

- Recibe todos los valores de Nivel 2 calculados en la ejecución.
- Si tiene `codigo_python`, puede acceder a `nivel2_outputs` (dict `{nivel2_id: valor}`).
- Si no tiene código, calcula el promedio de todos los valores de Nivel 2.

### Ejemplo de código en nivel1_output

```python
# Promedio ponderado manual
pesos = {1: 0.4, 2: 0.3, 3: 0.3}
total = sum(nivel2_outputs.get(k, 0) * v for k, v in pesos.items())
result = total / sum(pesos.values())
```

---

## 7. Ejecución del Pipeline

### Via API

```
POST /api/pipeline-definitions/{id}/execute
Authorization: Bearer <token_admin>
```

Respuesta:
```json
{
  "id": "uuid-ejecucion",
  "pipeline_id": "uuid-pipeline",
  "estado": "success",
  "resultado": {
    "nivel2_1": 75.3,
    "nivel2_2": 82.1,
    "nivel1_1": 78.7,
    "valor_final": 78.7,
    "nivel2_outputs": {"1": 75.3, "2": 82.1}
  },
  "log_debug": "...",
  "iniciado_en": "...",
  "terminado_en": "..."
}
```

### Via Editor Visual

En el editor `/admin/pipeline-editor/:id`, hacer click en **"Ejecutar"**.
El log de ejecución aparece en el panel inferior.

---

## 8. Historial de Ejecuciones

```
GET /api/pipeline-definitions/{id}/executions
```

Retorna las últimas 50 ejecuciones con estado, log y resultado.

---

## 9. Exportar / Importar Pipelines

### Exportar todos:
```
GET /api/pipeline-definitions/export-all
```
Descarga un JSON con todos los pipelines.

### Importar:
```
POST /api/pipeline-definitions/import
Body: [{nombre, grafo, activo}, ...]
```

También puede hacerse desde el editor visual con los botones "Exportar" / "Importar".

---

## 10. Flujo Completo de Datos

```
Templates (configuracion_campos)
    ↓ (define estructura)
Formularios llenados (datos_dinamicos)
    ↓ (aprobados por validador)
Pipeline: nodo data_source
    ↓ (DataFrame con todas las filas aprobadas)
Pipeline: nodo processor (transformaciones Python/pandas)
    ↓ (DataFrame transformado)
Pipeline: nodo nivel2_output
    ↓ (valor escalar por Indicador N2)
Pipeline: nodo nivel1_output
    ↓ (valor final del Indicador N1)
Estadísticas públicas (/estadisticas)
```

---

## 11. Seguridad del Sandbox

El código Python se ejecuta en un sandbox restringido:
- No hay acceso a `import`, `open`, `os`, `sys`, ni otras funciones peligrosas.
- Solo están disponibles las funciones builtins básicas listadas arriba.
- `pandas` (`pd`) está disponible para manipulación de datos.
- Si el código lanza una excepción, la ejecución del pipeline falla con estado `error`
  y el detalle se registra en `log_debug`.
