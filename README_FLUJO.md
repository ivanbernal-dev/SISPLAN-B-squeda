# UBPD — Recorrido Completo del Dato

Guía paso a paso de cómo viaja un dato desde que un usuario de dependencia lo ingresa hasta que aparece como estadística pública en el panel de indicadores.

---

## Arquitectura general

```
Usuarios               Backend (FastAPI)          Base de datos (PostgreSQL)
──────────             ──────────────────         ──────────────────────────
Dependencia  →  POST /forms             →   Form (estado: draft → submitted)
Validador    →  POST /validation/{id}   →   Form (estado: approved | rejected)
Admin        →  POST /script-pipeline   →   KpiResultado (nivel1, nivel2)
Público      ←  GET /stats/kpis         ←   KpiResultado
```

---

## Flujo paso a paso

### 1. Autenticación

Todos los usuarios se autentican en `POST /api/auth/login` con sus credenciales. El sistema retorna un **JWT** válido por 30 minutos (renovable vía refresh token).

Roles del sistema:
| Rol | Ruta por defecto | Acceso |
|---|---|---|
| `admin` | `/admin` | Gestión total del sistema |
| `validator` | `/validator/inbox` | Revisión y aprobación de formularios |
| `dependency_user` | `/dependencia` | Carga de formularios |

### 2. Gestión de Templates (Admin)

El administrador define los formularios en `/admin/templates`. Un template contiene:
- **Nombre** y código único
- **Campos configurables** (texto, número, fecha, select, textarea, archivo)
- **Plantilla Markdown** para visualización del registro aprobado

Los templates son la "forma" que deben llenar los usuarios de dependencia.

### 3. Carga de Formularios (Usuario de Dependencia)

El usuario de dependencia:
1. Va a `/dependencia/templates` y selecciona un template disponible
2. Completa el formulario en `/dependencia/forms/new/{templateId}`
3. Los datos se guardan como JSONB en la columna `datos_dinamicos` del modelo `Form`
4. El formulario queda en estado `submitted` (enviado para revisión)

**Modelo Form:**
```
Form {
  id, plantilla_id, usuario_id, dependency_id
  datos_dinamicos: JSONB   ← los valores del formulario
  estado: draft | submitted | approved | rejected
  fecha_usuario, fecha_carga, fecha_validacion
}
```

### 4. Validación (Validador)

El validador recibe los formularios en su bandeja de entrada (`/validator/inbox`):
1. Revisa los datos del formulario
2. **Aprueba** (`POST /api/validation/{id}/approve`) → estado pasa a `approved`
3. **Rechaza** (`POST /api/validation/{id}/reject`) con comentario → estado `rejected`

Solo los formularios en estado `approved` alimentan los indicadores.

### 5. Pipeline de Procesamiento (Admin — Script Editor)

El administrador accede a `/admin/script-pipeline` donde puede escribir y ejecutar un script Python personalizado.

**Variables disponibles en el script:**
```python
dfs           # dict: nombre_template → DataFrame de formularios aprobados
template_meta # dict: nombre_template → {id, nombre, codigo}
pd            # pandas
```

Cada fila del DataFrame corresponde a un formulario aprobado, con las columnas siendo los campos del `datos_dinamicos`.

**Contrato de salida esperado:**
```python
resultado = {
    "nivel1": [
        {"key": "kpi_cobertura", "label": "Cobertura", "valor": 75.3, "descripcion": "..."},
        # hasta 5 KPIs de nivel 1
    ],
    "nivel2": {
        "kpi_cobertura": [
            {"key": "kpi_cob_1", "label": "Hallazgos", "valor": 82.1, "template_id": "uuid"},
            # hasta 5 sub-KPIs por KPI padre
        ],
        # resto de KPIs padre...
    }
}
```

**Modos de ejecución:**
- **Test** (`modo: "test"`): Ejecuta el script, captura stdout, NO guarda en BD
- **Producción** (`modo: "produccion"`): Ejecuta y persiste los KPIs en la tabla `kpi_resultados`

**Persistencia:**
Los resultados se guardan en `KpiResultado`:
```
KpiResultado {
  nivel: 1 | 2
  kpi_key: string (único)
  kpi_label: string
  valor: float (0–100)
  nivel1_key: string | null (FK a KPI padre, solo para nivel 2)
  template_id: string | null (UUID del template asociado, para drill-down)
  updated_at: datetime
}
```

### 6. Estadísticas Públicas (Todos — sin autenticación)

La ruta `/estadisticas` es pública y muestra los indicadores en tres niveles de profundidad:

#### Nivel 1 — `/estadisticas`
- Muestra 5 gauges (velocímetros) con los KPIs principales
- Datos: `GET /api/stats/kpis`
- Si no hay datos en BD, los gauges muestran 0%

#### Nivel 2 — `/estadisticas/:kpiKey`
- Muestra los 5 sub-indicadores del KPI seleccionado
- Datos: `GET /api/stats/kpis/{kpiKey}`
- También muestra el gauge resumen del indicador padre

#### Nivel 3 — `/estadisticas/:kpiKey/forms/:subKpiKey`
- Lista paginada de formularios aprobados asociados al sub-indicador
- Datos: `GET /api/stats/kpis/{subKpiKey}/forms`
- El endpoint busca el `template_id` del sub-KPI y retorna los formularios aprobados de ese template
- Columnas: Caso/Nombre, Dependencia, Responsable, Fecha

#### Detalle de Formulario — `/estadisticas/:kpiKey/forms/:subKpiKey/:formId`
- Vista completa de un formulario aprobado
- Datos: `GET /api/forms/{formId}`
- Muestra todos los campos del `datos_dinamicos` como pares clave-valor

---

## Flujo de datos resumido

```
[Template definido por Admin]
         ↓
[Formulario llenado por Dependencia]
         ↓  datos_dinamicos: {campo1: valor1, campo2: valor2, ...}
[Formulario aprobado por Validador]
         ↓  estado = "approved"
[Script Python procesando DataFrames]
         ↓  resultado = {nivel1: [...], nivel2: {...}}
[KPIs guardados en kpi_resultados]
         ↓
[Velocímetros públicos en /estadisticas]
```

---

## Test E2E — Guía de uso

### Requisitos

- El sistema debe estar corriendo: `./scripts/prod.sh start`
- Python 3.9+ con `requests` instalado: `pip install requests`

### Configuración

```bash
export UBPD_BASE_URL="http://localhost:8000/api"   # URL del API
export UBPD_ADMIN_USER="admin"                      # Usuario admin
export UBPD_ADMIN_PASS="Admin@UBPD2024!"            # Contraseña admin
```

### Modos disponibles

```bash
# Verificar estado actual del sistema y datos de prueba
python scripts/e2e_test.py status

# Crear datos de prueba (3 templates + 30 formularios + 2 usuarios)
python scripts/e2e_test.py seed

# Ejecutar el pipeline de procesamiento
python scripts/e2e_test.py run

# Verificar que los KPIs públicos tienen valores correctos
python scripts/e2e_test.py verify

# Eliminar todos los datos de prueba
python scripts/e2e_test.py clean

# Flujo completo automatizado (seed → run → verify → clean)
python scripts/e2e_test.py auto

# Flujo completo SIN limpiar (para inspección manual post-test)
python scripts/e2e_test.py full
```

### Flujo automático completo

```bash
python scripts/e2e_test.py auto
```

El modo `auto` ejecuta estos pasos en secuencia:

| Paso | Acción | Qué verifica |
|---|---|---|
| 1 | Health check | Backend responde en `/api/health` |
| 2 | Login admin | JWT válido para el admin |
| 3 | Seed | Crea dependencia, 3 templates, 2 usuarios, 30 formularios |
| 4 | Instalar script | Carga el script de prueba en el editor |
| 5 | Login dep_user | `test_e2e_dep_user` puede autenticarse |
| 6 | Login validador | `test_e2e_validator` puede autenticarse |
| 7 | Check formularios | ≥21 formularios aprobados en BD |
| 8 | Cargar script | Script activo disponible vía API |
| 9 | Ejecutar pipeline | Test mode OK + Producción OK + KPIs guardados |
| 10 | Verificar KPIs | `/stats/kpis` retorna valores > 0 con drill-down |
| 11 | Limpiar | Elimina todos los datos `[TEST_E2E]` |

### Datos de prueba generados

**Usuarios:**
| Usuario | Rol | Contraseña |
|---|---|---|
| `test_e2e_dep_user` | dependency_user | `Test@E2E2024!` |
| `test_e2e_validator` | validator | `Test@E2E2024!` |

**Templates (3):**
- `Hallazgos Humanitarios [TEST_E2E]`
- `Procesos Extrajudiciales [TEST_E2E]`
- `Entrega Digna [TEST_E2E]`

**Formularios por template:** 10 total = 7 aprobados + 3 rechazados

**Campos del formulario de prueba:**
- `nombre_caso` — Texto
- `region` — Texto  
- `valor_numerico` — Número (0–100, usado por el pipeline para calcular KPIs)
- `observaciones` — Área de texto

**Script de prueba instalado:**
El pipeline de prueba lee los 3 templates, calcula la media de `valor_numerico` por template como sub-KPIs de nivel 2, y promedia esos valores para el KPI de nivel 1 `Cobertura`.

### Convenciones de datos de prueba

Los datos de prueba se identifican mediante estas convenciones:
- Nombres con sufijo `[TEST_E2E]`
- Código de dependencia: `TEST_E2E_DEP`
- Códigos de templates: `TEST_E2E_T1`, `TEST_E2E_T2`, `TEST_E2E_T3`
- Nombres de usuario con prefijo `test_e2e_`

El endpoint `DELETE /admin/test-data/clean` busca y elimina exactamente estos patrones, sin afectar datos reales del sistema.

---

## Endpoints relevantes del API

### Autenticación
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/auth/login` | Login, retorna JWT |
| POST | `/api/auth/refresh` | Renovar token |
| GET | `/api/auth/me` | Perfil del usuario actual |

### Templates
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/templates` | Lista de templates |
| POST | `/api/templates` | Crear template (admin) |
| GET | `/api/templates/{id}` | Detalle de template |

### Formularios
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/forms` | Lista de formularios del usuario |
| POST | `/api/forms` | Crear formulario |
| PUT | `/api/forms/{id}` | Actualizar formulario |
| GET | `/api/forms/{id}` | Detalle de formulario |

### Validación
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/validation/inbox` | Bandeja del validador |
| POST | `/api/validation/{id}/approve` | Aprobar formulario |
| POST | `/api/validation/{id}/reject` | Rechazar con comentario |

### Script Pipeline (Admin)
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/admin/script-pipeline/script` | Cargar script activo |
| POST | `/api/admin/script-pipeline/script` | Guardar script |
| POST | `/api/admin/script-pipeline/run` | Ejecutar pipeline |
| GET | `/api/admin/script-pipeline/tables` | Tablas disponibles con estadísticas |

### Estadísticas Públicas
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/stats/kpis` | KPIs nivel 1 |
| GET | `/api/stats/kpis/{key}` | Sub-KPIs de un KPI padre |
| GET | `/api/stats/kpis/{key}/forms` | Formularios de un sub-KPI |

### Test Data (Admin)
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/admin/test-data/status` | Estado de datos de prueba |
| POST | `/api/admin/test-data/seed` | Crear datos de prueba |
| POST | `/api/admin/test-data/install-script` | Instalar script de prueba |
| DELETE | `/api/admin/test-data/clean` | Eliminar datos de prueba |

---

## Documentación interactiva del API

Con el sistema corriendo, accede a:
- **Swagger UI:** `http://localhost:8000/api/docs`
- **ReDoc:** `http://localhost:8000/api/redoc`
