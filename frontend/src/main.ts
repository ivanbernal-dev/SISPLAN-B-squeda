// ============================================================
// UBPD Frontend — Punto de Entrada Vue.js
// TODO: Implementar en pasos posteriores
// ============================================================

// Estructura de módulos planificada:
//
// src/
// ├── main.ts                    ← Este archivo (entry point)
// ├── App.vue                    ← Componente raíz
// │
// ├── assets/
// │   ├── fonts/                 ← Fuentes locales: Barlow, Montserrat, Playfair Display
// │   ├── images/
// │   │   └── logo-ubpd.svg
// │   └── styles/
// │       ├── main.css           ← Variables CSS + @font-face
// │       └── tailwind.css       ← Directivas Tailwind
// │
// ├── router/
// │   └── index.ts               ← Vue Router + guardias por rol
// │
// ├── stores/                    ← Pinia stores
// │   ├── auth.ts                ← Estado de autenticación + JWT
// │   ├── stats-filter.ts        ← Filtro de fechas global (persiste entre niveles)
// │   └── notifications.ts
// │
// ├── composables/               ← Composables reutilizables
// │   ├── useApi.ts              ← Axios con interceptores JWT
// │   └── useDateFilter.ts
// │
// ├── layouts/
// │   ├── AdminLayout.vue        ← Shell con sidebar teal #3E818F
// │   ├── ValidatorLayout.vue
// │   ├── DependencyLayout.vue
// │   └── PublicLayout.vue       ← Sin auth, solo header con logo
// │
// ├── views/
// │   ├── auth/
// │   │   ├── LoginView.vue
// │   │   └── ChangePasswordView.vue
// │   │
// │   ├── admin/
// │   │   ├── DashboardView.vue
// │   │   ├── UsersView.vue
// │   │   ├── DependenciesView.vue
// │   │   ├── TemplatesView.vue
// │   │   ├── TemplateEditorView.vue  ← Editor Markdown + Preview
// │   │   ├── PipelinesView.vue
// │   │   └── AuditView.vue
// │   │
// │   ├── validator/
// │   │   ├── InboxView.vue
// │   │   ├── ReviewView.vue         ← Split screen datos + archivos
// │   │   ├── HistoryView.vue
// │   │   └── TemplatesView.vue
// │   │
// │   ├── dependency/
// │   │   ├── DashboardView.vue
// │   │   ├── TemplateGalleryView.vue
// │   │   ├── FormEditorView.vue     ← Renderizador dinámico desde JSONB
// │   │   └── InboxView.vue
// │   │
// │   └── public/
// │       ├── Level1View.vue         ← Gauges globales por indicador
// │       ├── Level2View.vue         ← Gauges por template
// │       └── Level3View.vue         ← Tabla detallada + exportar Excel
// │
// └── components/
//     ├── common/
//     │   ├── UbpdHeader.vue         ← Logo + área de reserva
//     │   ├── DateRangePicker.vue    ← Filtro global de fechas
//     │   ├── StatusBadge.vue        ← Badge de estado de formulario
//     │   └── ConfirmModal.vue
//     ├── charts/
//     │   ├── GaugeChart.vue         ← Velocímetro ECharts
//     │   └── IndicatorCard.vue
//     ├── forms/
//     │   ├── DynamicFormRenderer.vue ← Lee JSONB y renderiza campos
//     │   ├── FileUploadZone.vue     ← Drag & Drop con barra de progreso
//     │   └── MarkdownEditor.vue     ← Editor + Preview tiempo real
//     └── tables/
//         └── DataTable.vue          ← Tabla con búsqueda, filtros y export
