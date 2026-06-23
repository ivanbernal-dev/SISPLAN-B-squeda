# Scripts de Reseteo de Datos — UBPD

Documentación de los scripts y comandos de administración para limpiar datos del
sistema de forma controlada. La mayoría se ejecutan a través del CLI unificado
`./scripts/prod.sh <comando>`.

---

## Visión general — niveles de "limpieza"

De menos a más destructivo:

| # | Comando | Borra registros | Borra templates | Borra imágenes | Borra volúmenes | Vuelve a levantar | Requiere PIN |
|---|---------|-----------------|-----------------|----------------|-----------------|-------------------|--------------|
| 1 | `./scripts/prod.sh pipeline-reset` | KPIs y script de pipeline | ❌ | ❌ | ❌ | ❌ (no apaga nada) | ❌ |
| 2 | `./scripts/reset-formularios.sh` | ✅ (forms + adjuntos) | ❌ | ❌ | ❌ | ❌ | ❌ |
| 3 | `./scripts/reset-templates.sh` | ✅ + templates | ✅ | ❌ | ❌ | ❌ | ❌ |
| 4 | `./scripts/reset-users.sh` | usuarios | ❌ | ❌ | ❌ | ❌ | ❌ |
| 5 | `./scripts/reset-all-data.sh` | TODO el contenido | ✅ | ❌ | ❌ | ❌ | frase |
| 6 | `./scripts/prod.sh reset-db` | recrea BD | ✅ | ❌ | ✅ (postgres) | ✅ | flag `.env` |
| 7 | **`./scripts/prod.sh reset-fresh`** | **TODO** | ✅ | ❌ | ✅ (3 volúmenes) | ✅ | **frase + PIN** |
| 8 | **`./scripts/prod.sh destroy [all]`** | **TODO** | ✅ | **✅** | ✅ | ❌ (queda apagado) | **frase + PIN** |

> 🟡 **Los comandos 7 y 8 requieren `RESET_PIN=<pin>` en `.env`**. Sin esa variable
> el script aborta con instrucciones — protección contra borrados accidentales.

---

## Índice

- [Requisitos previos](#requisitos-previos)
- [prod.sh pipeline-reset — Restaurar pipeline](#prodsh-pipeline-reset--restaurar-pipeline)
- [reset-formularios.sh — Borrar formularios](#reset-formulariossh--borrar-formularios)
- [reset-templates.sh — Borrar templates](#reset-templatessh--borrar-templates)
- [reset-users.sh — Borrar usuarios](#reset-userssh--borrar-usuarios)
- [reset-all-data.sh — Borrar todo (sin tocar contenedores)](#reset-all-datash--borrar-todo)
- [prod.sh reset-fresh — Reset a instalación limpia](#prodsh-reset-fresh--reset-a-instalación-limpia)
- [prod.sh destroy — Destruir Docker del proyecto](#prodsh-destroy--destruir-docker-del-proyecto)
- [Qué se elimina en cada script](#qué-se-elimina-en-cada-script)
- [Orden de ejecución recomendado](#orden-de-ejecución-recomendado)
- [Solución de problemas](#solución-de-problemas)

---

## Requisitos previos

Antes de ejecutar cualquier script:

1. **Los contenedores deben estar corriendo:**
   ```bash
   ./scripts/prod.sh start
   ./scripts/prod.sh ps   # verificar que postgres y minio estén "healthy"
   ```

2. **El archivo `.env` debe existir** en la raíz del proyecto con las credenciales de base de datos y MinIO.

3. **Ejecutar desde la raíz del proyecto** (donde está el `docker-compose.yml`):
   ```bash
   cd /ruta/al/proyecto/ubpd-app
   ```

---

## `reset-formularios.sh` — Borrar formularios

**Ubicación:** `scripts/reset-formularios.sh`

Elimina todos los formularios respondidos y sus archivos adjuntos **sin tocar los templates**. Los templates quedan intactos y disponibles para seguir siendo usados.

### Uso

```bash
# Borrar TODOS los formularios del sistema
./scripts/reset-formularios.sh

# Borrar solo los formularios de un template específico
./scripts/reset-formularios.sh --template-id <uuid-del-template>

# Borrar solo formularios en un estado concreto
./scripts/reset-formularios.sh --estado draft
./scripts/reset-formularios.sh --estado pending
./scripts/reset-formularios.sh --estado approved
./scripts/reset-formularios.sh --estado rejected

# Combinar filtros: solo borradores de un template específico
./scripts/reset-formularios.sh --template-id <uuid> --estado draft
```

### Qué elimina

| Elemento | Detalle |
|---|---|
| Formularios respondidos | Los que coincidan con el filtro (todos si no hay filtro) |
| Archivos adjuntos (BD) | Registros de archivos vinculados a esos formularios |
| Estadísticas (`fact_stats`) | Estadísticas calculadas de esos formularios |
| Archivos físicos (MinIO) | Archivos subidos en esos formularios |

### Qué conserva

- **Templates** y su configuración de campos
- Usuarios (admins, validadores, usuarios de dependencia)
- Dependencias
- Indicadores nivel 1 y nivel 2
- Definiciones de pipelines
- Audit logs

### Información mostrada antes de ejecutar

El script muestra el desglose por estado antes de pedir confirmación:

```
Alcance: todos los formularios

Formularios a eliminar: 104
  · Borradores:   23
  · Pendientes:   41
  · Aprobados:    35
  · Rechazados:    5
Archivos adjuntos: 87
```

Si no hay formularios que coincidan con el filtro, el script termina sin hacer nada ni pedir confirmación.

### Resumen final

```
✓ Operación completada.
  Formularios restantes en el sistema: 0
  Templates intactos:                  12
```

---

## `reset-templates.sh` — Borrar templates

**Ubicación:** `scripts/reset-templates.sh`

Elimina todos los templates y, en cascada, todos los datos que dependen de ellos. Los usuarios, dependencias e indicadores **no se ven afectados**.

### Uso

```bash
./scripts/reset-templates.sh
```

### Qué elimina

| Elemento | Detalle |
|---|---|
| Templates | Todos los templates activos e inactivos |
| Formularios respondidos | Todos los formularios de todos los templates |
| Archivos adjuntos (BD) | Registros de archivos vinculados a esos formularios |
| Estadísticas (`fact_stats`) | Estadísticas calculadas de esos templates |
| Archivos físicos (MinIO) | Archivos subidos en formularios de esos templates |

### Qué conserva

- Usuarios (admins, validadores, usuarios de dependencia)
- Dependencias
- Indicadores nivel 1 y nivel 2
- Definiciones de pipelines
- Audit logs

### Información mostrada antes de ejecutar

```
Estado actual:
  · Templates:    12
  · Formularios:  87  (se eliminarán también)
```

---

## `reset-users.sh` — Borrar usuarios

**Ubicación:** `scripts/reset-users.sh`

Elimina usuarios del sistema **conservando siempre los administradores**. Soporta tres modos de operación.

### Uso

```bash
# Borrar validadores Y usuarios de dependencia
./scripts/reset-users.sh

# Borrar solo validadores
./scripts/reset-users.sh --solo-validadores

# Borrar solo usuarios de dependencia
./scripts/reset-users.sh --solo-dependencias
```

### Modos disponibles

| Comando | Roles eliminados | Roles conservados |
|---|---|---|
| Sin argumento | `validator`, `dependency_user` | `admin` |
| `--solo-validadores` | `validator` | `admin`, `dependency_user` |
| `--solo-dependencias` | `dependency_user` | `admin`, `validator` |

### Qué elimina en cascada

Al borrar un usuario se eliminan también todos sus datos asociados:

| Elemento | Detalle |
|---|---|
| Formularios respondidos | Todos los formularios enviados por el usuario |
| Archivos adjuntos (BD) | Registros de archivos en esos formularios |
| Audit logs | Registros de actividad del usuario |
| Archivos físicos (MinIO) | Archivos subidos por el usuario |

### Información mostrada antes de ejecutar

```
Estado actual:
  · Admins:               2  (se conservan)
  · Validadores:          5
  · Usuarios dependencia: 18

Modo seleccionado: validadores y usuarios de dependencia
Usuarios a eliminar: 23
Formularios afectados: 104 (se eliminarán en cascada)
```

### Resumen final

```
✓ Operación completada.
  Usuarios restantes por rol:
    · admin: 2
```

---

## `reset-all-data.sh` — Borrar todo

**Ubicación:** `scripts/reset-all-data.sh`

Elimina **absolutamente todos los datos** de todas las tablas de la base de datos y borra todos los archivos almacenados en MinIO. Es el reseteo más completo del sistema.

### Uso

```bash
./scripts/reset-all-data.sh
```

### Qué elimina

| Tabla | Contenido eliminado |
|---|---|
| `formularios_respondidos` | Todos los formularios (cualquier estado) |
| `archivos` | Todos los registros de archivos adjuntos |
| `templates` | Todos los templates de formularios |
| `usuarios` | Todos los usuarios (incluyendo admins) |
| `dependencias` | Todas las dependencias registradas |
| `indicadores_nivel1` | Indicadores de la Línea Estratégica 1 |
| `indicadores_nivel2` | Indicadores de nivel 2 |
| `fact_stats` | Estadísticas calculadas |
| `pipeline_definiciones` | Definiciones de pipelines |
| `pipeline_ejecuciones` | Historial de ejecuciones de pipelines |
| `pipeline_runs` | Runs de pipelines |
| `audit_logs` | Registro de auditoría |
| **MinIO** | Todos los archivos físicos del bucket |

Los IDs de todas las tablas se reinician (`RESTART IDENTITY`).

### Confirmación requerida

El script exige **dos confirmaciones** escritas para evitar ejecuciones accidentales:

```
Escribe CONFIRMAR para continuar: CONFIRMAR
¿Seguro? Escribe BORRAR TODO para ejecutar: BORRAR TODO
```

### Recuperación tras el reseteo

Al reiniciar el backend, el sistema recrea automáticamente:
- El usuario administrador inicial (credenciales definidas en `.env`)
- Los indicadores de la Línea Estratégica 1

```bash
./scripts/prod.sh restart backend
```

---

## `prod.sh pipeline-reset` — Restaurar pipeline

**Comando:** `./scripts/prod.sh pipeline-reset`

Reinstala el pipeline de cálculo de KPIs a la versión por defecto y lo ejecuta.
Es **no destructivo para los formularios y templates** — solo regenera la tabla
`kpi_resultados` y el script activo en `pipeline_scripts`.

### Cuándo usarlo

- Los velocímetros de `/estadisticas` muestran valores incorrectos o desactualizados.
- Aparecen KPIs viejos que ya no corresponden al PAI 2026.
- Después de cargar formularios nuevos y querer refrescar los indicadores.

### Qué hace internamente

1. Borra TODOS los `pipeline_scripts` e inserta el seed `backend/app/seeds/pipeline_pai_default.py` como único activo.
2. Borra TODOS los `kpi_resultados`.
3. Ejecuta el seed in-process (sin pasar por el editor).
4. Imprime los KPIs recién guardados con sus valores y labels para verificación.

### Salida típica

```
✅ Reset OK
   Seed: /app/app/seeds/pipeline_pai_default.py (8123 chars)
   Scripts viejos borrados: 3
   KPIs viejos borrados:    11

📊 KPIs nivel-1 guardados:
   L1   valor=  0.00  label=Línea 1 — Investigación Humanitaria y Extrajudicial
   ...
   L6   valor=  5.93  label=Línea 6 — Soporte Estratégico y Operativo

📊 KPIs nivel-2 guardados:
   L6-P2-DPE-2026  valor= 23.70  label=L6-P2-DPE-2026 — SISPLAN - BÚSQUEDA: ...
```

---

## `prod.sh reset-fresh` — Reset a instalación limpia

**Comando:** `./scripts/prod.sh reset-fresh`

Devuelve el sistema al estado de "recién instalado": **borra todos los datos, archivos
y caché**, recrea el esquema y siembra el admin inicial automáticamente.

### Requisitos

- `RESET_PIN=<pin>` definido en `.env` (PIN numérico de 4-8 dígitos).
- Sin esa variable el comando aborta con instrucciones.

### Confirmación triple

1. Escribir literalmente: `BORRAR TODO`
2. Confirmar el alcance escribiendo: `si`
3. Ingresar el PIN (oculto, como `sudo`)

### Qué hace

1. Hace **backup preventivo** automático (`pg_dump` → `backups/pre-reset/`).
2. `docker compose down --remove-orphans`.
3. Borra los 3 volúmenes: `ubpd_postgres_data`, `ubpd_minio_data`, `ubpd_valkey_data`.
4. Levanta `postgres + minio + valkey` limpios.
5. Levanta `backend` → recrea esquema, siembra admin inicial y pipeline PAI.
6. Levanta el resto de servicios.

### Modo automatizado (CI)

```bash
RESET_AUTO_CONFIRM=yes RESET_AUTO_PIN=472918 ./scripts/prod.sh reset-fresh
```

---

## `prod.sh destroy` — Destruir Docker del proyecto

**Comando:** `./scripts/prod.sh destroy [all]`

Elimina del entorno Docker **todo lo asociado al proyecto** (scope acotado, no
afecta otros proyectos en la misma máquina). A diferencia de `reset-fresh`, **no
vuelve a levantar el sistema** — para volver a usarlo hay que reconstruir.

### Qué borra

| Recurso | Modo normal | Modo `all` |
|---------|-------------|------------|
| Contenedores del compose + `ubpd_*` huérfanos | ✅ | ✅ |
| Imágenes locales `ubpd-app-backend`, `ubpd-app-frontend` | ✅ | ✅ |
| Volúmenes `ubpd_postgres_data`, `ubpd_minio_data`, `ubpd_valkey_data` | ✅ | ✅ |
| Red `ubpd_network` | ✅ | ✅ |
| Imágenes 3rd party (postgres, nginx, minio, valkey) | ❌ | ✅ |

### Triple confirmación

1. Escribir literalmente: `DESTRUIR TODO`
2. Confirmar alcance escribiendo: `si`
3. Ingresar el PIN

### Para volver a levantarlo

```bash
./scripts/prod.sh build && ./scripts/prod.sh start
```

### Modo automatizado (CI)

```bash
DESTROY_AUTO_CONFIRM=yes DESTROY_AUTO_PIN=472918 DESTROY_INCLUDE_3RD=yes \
  ./scripts/prod.sh destroy all
```

---

## Qué se elimina en cada script

Tabla resumen comparativa:

| Dato | reset-formularios | reset-templates | reset-users | reset-all-data |
|---|:---:|:---:|:---:|:---:|
| Formularios respondidos | ✅ | ✅ | ✅ (del usuario) | ✅ |
| Archivos adjuntos | ✅ | ✅ | ✅ (del usuario) | ✅ |
| Archivos MinIO | ✅ | ✅ | ✅ (del usuario) | ✅ |
| Estadísticas | ✅ | ✅ | ❌ | ✅ |
| Templates | ❌ | ✅ | ❌ | ✅ |
| Usuarios (no admin) | ❌ | ❌ | ✅ | ✅ |
| Administradores | ❌ | ❌ | ❌ | ✅ |
| Dependencias | ❌ | ❌ | ❌ | ✅ |
| Indicadores | ❌ | ❌ | ❌ | ✅ |
| Pipelines | ❌ | ❌ | ❌ | ✅ |
| Audit logs | ❌ | ❌ | ✅ (del usuario) | ✅ |

---

## Orden de ejecución recomendado

### Limpiar solo registros para pruebas (conservar estructura)

```bash
# Borra todos los formularios pero deja los templates listos para usarse
./scripts/reset-formularios.sh
```

### Limpiar registros de un estado específico

```bash
# Ejemplo: borrar solo los borradores
./scripts/reset-formularios.sh --estado draft

# Ejemplo: borrar solo los formularios de un template en pruebas
./scripts/reset-formularios.sh --template-id <uuid>
```

### Reseteo total por etapas

```bash
# 1. Borrar formularios
./scripts/reset-formularios.sh

# 2. Borrar templates
./scripts/reset-templates.sh

# 3. Borrar usuarios (excepto admins)
./scripts/reset-users.sh

# 4. Reiniciar backend para recrear admin e indicadores
./scripts/prod.sh restart backend
```

### Reseteo total directo

```bash
./scripts/reset-all-data.sh
./scripts/prod.sh restart backend
```

---

## Solución de problemas

### "No se encontró el archivo .env"
El script no encuentra el archivo de configuración. Asegúrate de ejecutarlo desde la raíz del proyecto:
```bash
cd /ruta/al/ubpd-app
./scripts/reset-formularios.sh
```

### "Error: could not connect to server"
El contenedor de PostgreSQL no está corriendo o no está healthy:
```bash
./scripts/prod.sh ps
./scripts/prod.sh start
```

### Los archivos de MinIO no se eliminaron
Si el contenedor de MinIO no tiene el cliente `mc` instalado o hubo un error de red, el script continúa sin error pero muestra una advertencia:
```
⚠ No se pudo limpiar MinIO (continúa sin error)
```
En ese caso, puedes limpiar manualmente desde la consola de MinIO en `http://localhost:9001` (requiere túnel SSH si el servidor es remoto).

### El admin no se recreó tras el reseteo
Si el backend no recrea el admin inicial, reinícialo manualmente:
```bash
./scripts/prod.sh restart backend
./scripts/prod.sh logs backend   # verificar que el lifespan corrió
```
El admin se crea con las credenciales definidas en `.env` bajo `INITIAL_ADMIN_*`.
