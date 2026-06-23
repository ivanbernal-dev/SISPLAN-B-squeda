# Flujos de Usuario — UBPD

## 1. Usuario Administrador

### Navegación
```
/admin
├── /admin/dashboard          ← Panel principal con métricas del sistema
├── /admin/users              ← Lista de usuarios (CRUD)
│   ├── /admin/users/new      ← Crear usuario
│   └── /admin/users/:id      ← Editar usuario
├── /admin/dependencies       ← Gestión de dependencias
│   ├── /admin/dependencies/new
│   └── /admin/dependencies/:id
├── /admin/templates          ← Gestión de templates de formularios
│   ├── /admin/templates/new  ← Editor Markdown + Preview
│   └── /admin/templates/:id  ← Editar template
├── /admin/pipelines          ← Monitor de estado de pipelines
└── /admin/audit              ← Log de auditoría
```

### Flujo: Crear Template
```
1. Navegar a /admin/templates/new
2. Escribir Markdown en el editor (lado izquierdo)
3. Ver preview del formulario en tiempo real (lado derecho)
4. Definir qué campos son readonly y sus valores por defecto
5. Asignar al indicador del Nivel 1 correspondiente
6. Guardar → Backend parsea Markdown → Genera JSONB → Almacena en BD
```

### Flujo: Crear Usuario
```
1. Navegar a /admin/users/new
2. Completar: nombre, username, email, role
3. Si role = dependency_user → seleccionar dependencia obligatoriamente
4. Sistema genera contraseña temporal (el usuario debe cambiarla al primer login)
5. Guardar → Usuario creado activo
```

---

## 2. Usuario Validador

### Navegación
```
/validator
├── /validator/inbox          ← Bandeja de entrada (formularios pendientes)
│   └── /validator/review/:id ← Vista de revisión (split screen)
├── /validator/history        ← Historial de formularios procesados
└── /validator/templates      ← Crear/editar templates (igual que admin)
    ├── /validator/templates/new
    └── /validator/templates/:id
```

### Flujo: Validar un Formulario
```
1. Entrar a /validator/inbox
2. Ver lista paginada ordenada por fecha de envío
3. Filtrar por rango de fechas si es necesario
4. Hacer clic en un formulario → Ir a /validator/review/:id
5. Vista dividida:
   - Izquierda: datos del formulario (lectura)
   - Derecha: visor de archivos adjuntos (PDF/imagen embebido)
6. Revisar Informe Cualitativo
7. Decisión:
   ├── APROBAR → Confirmación modal → Estado: approved → Celery task disparado
   └── RECHAZAR → Textarea obligatoria con observaciones → Estado: rejected
8. Volver a la bandeja de entrada
```

---

## 3. Usuario de Dependencia

### Navegación
```
/dependencia
├── /dependencia/dashboard    ← Resumen: mis trámites por estado
├── /dependencia/templates    ← Galería de templates disponibles para su dependencia
├── /dependencia/forms/new/:template_id  ← Llenar nuevo formulario
├── /dependencia/forms/:id    ← Ver/editar formulario (si es draft o rejected)
└── /dependencia/inbox        ← Bandeja: Borrador | Enviado | Devuelto | Aprobado
```

### Flujo: Llenar y Enviar Formulario
```
1. Entrar a /dependencia/templates
2. Ver galería de tarjetas con los templates disponibles
3. Seleccionar template → Sistema auto-llena campos con valores por defecto
4. Formulario renderizado dinámicamente desde JSONB del template:
   - Campos editables: input normal con borde verde (#52ABAB al focus)
   - Campos readonly: fondo gris, cursor no-allowed, muestra valor por defecto
5. Fechas gestionadas:
   - "Fecha de Carga": campo deshabilitado, muestra fecha/hora actual (se confirma al guardar)
   - "Fecha de Última Edición": campo deshabilitado, automático
   - "Fecha de Referencia": date picker, iniciado en hoy, editable
6. Sección "Informe Cualitativo": textarea obligatorio
7. Sección "Soportes": drag & drop de archivos
   - Validación de tamaño antes de upload
   - Barra de progreso por archivo
   - Miniatura si imagen, icono si PDF
8. Opciones:
   ├── "Guardar Borrador" → Estado: draft
   └── "Enviar a Validación" → Estado: pending → Aparece en bandeja del validador
```

### Flujo: Corregir Formulario Devuelto
```
1. Ver notificación en /dependencia/inbox (estado: rejected, resaltado naranja)
2. Abrir formulario → Ver comentario del validador resaltado
3. Los campos indicados en el comentario están disponibles para editar
4. Corregir y volver a enviar → Estado: pending
```

---

## 4. Sitio Público (Sin Login)

### Navegación
```
/estadisticas
├── /estadisticas             ← Nivel 1: Dashboard Global (Gauges por indicador)
├── /estadisticas/:indicador_id      ← Nivel 2: Desagregación por template
└── /estadisticas/:indicador_id/:template_id  ← Nivel 3: Tabla detallada
```

### Flujo: Explorar Estadísticas
```
1. Entrar a /estadisticas
2. Barra de filtros global:
   - DateRangePicker (inicio y fin)
   - Presets: "Este mes" | "Último trimestre" | "Año actual"
3. Ver Nivel 1:
   - Gauges (velocímetros) por grupo de indicadores
   - Lila (#A97CC9) como color principal de los gauges
   - Cada gauge muestra: nombre del indicador + porcentaje de completitud
4. Hacer clic en un gauge → Navegar a Nivel 2 (fechas se mantienen en URL)
5. Ver Nivel 2:
   - Gauges de completitud por cada template del indicador seleccionado
   - Etiqueta: "X formularios encontrados en este rango"
6. Hacer clic en un gauge de template → Navegar a Nivel 3
7. Ver Nivel 3:
   - Tabla con búsqueda y filtros por columna
   - Columnas: Dependencia, Fecha, Informe Cualitativo (truncado), Soportes
   - Botón "Exportar a Excel" (respeta filtros activos)
```

---

## 5. Autenticación (Todos los Roles)

### Flujo: Login
```
1. Navegar a /login (redirigido automáticamente si no hay token)
2. Ingresar username y password
3. POST /api/auth/login
4. Backend verifica credenciales y genera JWT
5. Frontend almacena token en localStorage (o cookie httpOnly recomendado)
6. Vue Router redirige según el rol:
   ├── admin        → /admin/dashboard
   ├── validator    → /validator/inbox
   └── dependency_user → /dependencia/dashboard
```

### Flujo: Primer Login (Contraseña Temporal)
```
1. Usuario ingresa con contraseña temporal asignada por admin
2. Backend detecta flag `requires_password_change: true`
3. Frontend redirige a /change-password (forzado, no puede salir)
4. Usuario define nueva contraseña
5. Redirigido a su dashboard
```

### Guardias de Ruta (Vue Router)
```
Ruta /admin/*     → Solo role: admin
Ruta /validator/* → Solo role: validator
Ruta /dependencia/* → Solo role: dependency_user
Ruta /estadisticas/* → Pública, sin guardia
```

---

## 6. Estructura de Vistas por Rol

### Sidebar del Administrador
```
┌─────────────────────────┐
│  [Logo UBPD]            │
│  Admin: Juan García     │
├─────────────────────────┤
│  📊 Dashboard           │
│  👥 Usuarios            │
│  🏢 Dependencias        │
│  📋 Templates           │
│  ⚙️  Pipelines          │
│  📜 Auditoría           │
├─────────────────────────┤
│  🚪 Cerrar Sesión       │
└─────────────────────────┘
Color sidebar: Teal Oscuro #3E818F
```

### Sidebar del Validador
```
┌─────────────────────────┐
│  [Logo UBPD]            │
│  Validador: M. Torres   │
├─────────────────────────┤
│  📥 Bandeja (12)        │ ← contador de pendientes
│  📋 Crear Template      │
│  🗂️  Historial          │
├─────────────────────────┤
│  🚪 Cerrar Sesión       │
└─────────────────────────┘
```

### Navbar del Usuario de Dependencia
```
┌──────────────────────────────────────────────────────┐
│ [Logo UBPD]   Dep. Antioquia     Mis Trámites  Salir │
└──────────────────────────────────────────────────────┘
```
