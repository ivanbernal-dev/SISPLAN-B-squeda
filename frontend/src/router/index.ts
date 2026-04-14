// ============================================================
// UBPD — Vue Router
// Rutas protegidas por rol + guardia global JWT
// ============================================================

import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import type { UserRole } from '../stores/auth'

// ─── Tipos de meta ────────────────────────────────────────
declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    roles?: UserRole[]
  }
}

// ─── Definición de Rutas ──────────────────────────────────
const routes: RouteRecordRaw[] = [

  // ── Raíz: redirect inteligente ─────────────────────────
  {
    path: '/',
    redirect: () => {
      const auth = useAuthStore()
      return auth.isAuthenticated ? auth.getDefaultRoute() : '/login'
    },
  },

  // ── Rutas Públicas ─────────────────────────────────────
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/auth/LoginView.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/change-password',
    name: 'ChangePassword',
    component: () => import('../views/auth/ChangePasswordView.vue'),
    meta: { requiresAuth: true },
  },

  // ── Estadísticas Públicas (sin auth) ───────────────────
  {
    path: '/estadisticas',
    component: () => import('../layouts/PublicLayout.vue'),
    children: [
      {
        path: '',
        name: 'StatsLevel1',
        component: () => import('../views/public/Level1View.vue'),
        meta: { requiresAuth: false },
      },
      {
        path: ':indicadorId',
        name: 'StatsLevel2',
        component: () => import('../views/public/Level2View.vue'),
        meta: { requiresAuth: false },
      },
      {
        path: ':kpiKey/forms/:subKpiKey',
        name: 'KpiLevel3',
        component: () => import('../views/public/Level3KpiView.vue'),
        meta: { requiresAuth: false },
      },
      {
        path: ':kpiKey/forms/:subKpiKey/:formId',
        name: 'KpiFormDetail',
        component: () => import('../views/public/KpiFormDetailView.vue'),
        meta: { requiresAuth: false },
      },
      {
        path: ':indicadorId/:templateId',
        name: 'StatsLevel3',
        component: () => import('../views/public/Level3View.vue'),
        meta: { requiresAuth: false },
      },
      {
        path: ':indicador_id/:template_id/:form_id',
        name: 'FormDetail',
        component: () => import('../views/public/FormDetailView.vue'),
        meta: { requiresAuth: false },
      },
    ],
  },

  // ── Rutas Admin ────────────────────────────────────────
  {
    path: '/admin',
    component: () => import('../layouts/AdminLayout.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: () => import('../views/admin/DashboardView.vue'),
        meta: { requiresAuth: true, roles: ['admin'] },
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('../views/admin/UsersView.vue'),
        meta: { requiresAuth: true, roles: ['admin'] },
      },
      {
        path: 'users/new',
        name: 'AdminUsersNew',
        component: () => import('../views/admin/UserFormView.vue'),
        meta: { requiresAuth: true, roles: ['admin'] },
      },
      {
        path: 'users/:id',
        name: 'AdminUsersEdit',
        component: () => import('../views/admin/UserFormView.vue'),
        meta: { requiresAuth: true, roles: ['admin'] },
      },
      {
        path: 'dependencies',
        name: 'AdminDependencies',
        component: () => import('../views/admin/DependenciesView.vue'),
        meta: { requiresAuth: true, roles: ['admin'] },
      },
      {
        path: 'dependencies/new',
        name: 'AdminDependenciesNew',
        component: () => import('../views/admin/DependencyFormView.vue'),
        meta: { requiresAuth: true, roles: ['admin'] },
      },
      {
        path: 'dependencies/:id',
        name: 'AdminDependenciesEdit',
        component: () => import('../views/admin/DependencyFormView.vue'),
        meta: { requiresAuth: true, roles: ['admin'] },
      },
      {
        path: 'templates',
        name: 'AdminTemplates',
        component: () => import('../views/admin/TemplatesView.vue'),
        meta: { requiresAuth: true, roles: ['admin'] },
      },
      {
        path: 'templates/new',
        name: 'AdminTemplatesNew',
        component: () => import('../views/admin/TemplateEditorView.vue'),
        meta: { requiresAuth: true, roles: ['admin'] },
      },
      {
        path: 'templates/:id',
        name: 'AdminTemplatesEdit',
        component: () => import('../views/admin/TemplateEditorView.vue'),
        meta: { requiresAuth: true, roles: ['admin'] },
      },
      {
        path: 'script-pipeline',
        name: 'AdminScriptPipeline',
        component: () => import('../views/admin/ScriptEditorView.vue'),
        meta: { requiresAuth: true, roles: ['admin'] },
      },
      {
        path: 'pipelines',
        name: 'AdminPipelines',
        component: () => import('../views/admin/PipelinesView.vue'),
        meta: { requiresAuth: true, roles: ['admin'] },
      },
      {
        path: 'pipeline-editor',
        name: 'PipelineEditorNew',
        component: () => import('../views/admin/PipelineEditorView.vue'),
        meta: { requiresAuth: true, roles: ['admin'] },
      },
      {
        path: 'pipeline-editor/:id',
        name: 'PipelineEditor',
        component: () => import('../views/admin/PipelineEditorView.vue'),
        meta: { requiresAuth: true, roles: ['admin'] },
      },
      {
        path: 'indicadores',
        name: 'IndicadoresAdmin',
        component: () => import('../views/admin/IndicadoresView.vue'),
        meta: { requiresAuth: true, roles: ['admin'] },
      },
      {
        path: 'audit',
        name: 'AdminAudit',
        component: () => import('../views/admin/AuditView.vue'),
        meta: { requiresAuth: true, roles: ['admin'] },
      },
      {
        path: 'registros',
        name: 'AdminRegistros',
        component: () => import('../views/shared/FormsBrowserView.vue'),
        meta: { requiresAuth: true, roles: ['admin'] },
      },
      {
        path: 'registros/:templateId',
        name: 'AdminRegistrosTemplate',
        component: () => import('../views/shared/FormsBrowserView.vue'),
        meta: { requiresAuth: true, roles: ['admin'] },
      },
      {
        path: 'registros/:templateId/:formId',
        name: 'AdminRegistrosDetalle',
        component: () => import('../views/shared/FormDetailView.vue'),
        meta: { requiresAuth: true, roles: ['admin'] },
      },
    ],
  },

  // ── Rutas Validador ────────────────────────────────────
  {
    path: '/validator',
    component: () => import('../layouts/ValidatorLayout.vue'),
    meta: { requiresAuth: true, roles: ['validator'] },
    children: [
      {
        path: '',
        redirect: { name: 'ValidatorInbox' },
      },
      {
        path: 'inbox',
        name: 'ValidatorInbox',
        component: () => import('../views/validator/InboxView.vue'),
        meta: { requiresAuth: true, roles: ['validator'] },
      },
      {
        path: 'review/:id',
        name: 'ValidatorReview',
        component: () => import('../views/validator/ReviewView.vue'),
        meta: { requiresAuth: true, roles: ['validator'] },
      },
      {
        path: 'review-batch/:loteId',
        name: 'ValidatorBatchReview',
        component: () => import('../views/validator/BatchReviewView.vue'),
        meta: { requiresAuth: true, roles: ['validator'] },
      },
      {
        path: 'history',
        name: 'ValidatorHistory',
        component: () => import('../views/validator/HistoryView.vue'),
        meta: { requiresAuth: true, roles: ['validator'] },
      },
      {
        path: 'templates/new',
        name: 'ValidatorTemplatesNew',
        component: () => import('../views/validator/TemplateEditorView.vue'),
        meta: { requiresAuth: true, roles: ['validator'] },
      },
      {
        path: 'templates/:id',
        name: 'ValidatorTemplatesEdit',
        component: () => import('../views/validator/TemplateEditorView.vue'),
        meta: { requiresAuth: true, roles: ['validator'] },
      },
      {
        path: 'registros',
        name: 'ValidatorRegistros',
        component: () => import('../views/shared/FormsBrowserView.vue'),
        meta: { requiresAuth: true, roles: ['validator'] },
      },
      {
        path: 'registros/:templateId',
        name: 'ValidatorRegistrosTemplate',
        component: () => import('../views/shared/FormsBrowserView.vue'),
        meta: { requiresAuth: true, roles: ['validator'] },
      },
      {
        path: 'registros/:templateId/:formId',
        name: 'ValidatorRegistrosDetalle',
        component: () => import('../views/shared/FormDetailView.vue'),
        meta: { requiresAuth: true, roles: ['validator'] },
      },
    ],
  },

  // ── Rutas Dependencia ──────────────────────────────────
  {
    path: '/dependencia',
    component: () => import('../layouts/DependencyLayout.vue'),
    meta: { requiresAuth: true, roles: ['dependency_user'] },
    children: [
      {
        path: '',
        name: 'DependenciaDashboard',
        component: () => import('../views/dependency/DashboardView.vue'),
        meta: { requiresAuth: true, roles: ['dependency_user'] },
      },
      {
        path: 'templates',
        name: 'DependenciaTemplates',
        component: () => import('../views/dependency/TemplateGalleryView.vue'),
        meta: { requiresAuth: true, roles: ['dependency_user'] },
      },
      {
        path: 'forms/new/:templateId',
        name: 'DependenciaFormsNew',
        component: () => import('../views/dependency/FormEditorView.vue'),
        meta: { requiresAuth: true, roles: ['dependency_user'] },
      },
      {
        path: 'forms/:id',
        name: 'DependenciaFormsEdit',
        component: () => import('../views/dependency/FormEditorView.vue'),
        meta: { requiresAuth: true, roles: ['dependency_user'] },
      },
      {
        path: 'inbox',
        name: 'DependenciaInbox',
        component: () => import('../views/dependency/InboxView.vue'),
        meta: { requiresAuth: true, roles: ['dependency_user'] },
      },
      {
        path: 'registros',
        name: 'DependenciaRegistros',
        component: () => import('../views/shared/FormsBrowserView.vue'),
        meta: { requiresAuth: true, roles: ['dependency_user'] },
      },
      {
        path: 'registros/:templateId',
        name: 'DependenciaRegistrosTemplate',
        component: () => import('../views/shared/FormsBrowserView.vue'),
        meta: { requiresAuth: true, roles: ['dependency_user'] },
      },
      {
        path: 'registros/:templateId/:formId',
        name: 'DependenciaRegistrosDetalle',
        component: () => import('../views/shared/FormDetailView.vue'),
        meta: { requiresAuth: true, roles: ['dependency_user'] },
      },
    ],
  },

  // ── 404 catch-all ──────────────────────────────────────
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: '/',
  },
]

// ─── Crear Router ─────────────────────────────────────────
const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

// ─── Guardia Global ───────────────────────────────────────
router.beforeEach((to, _from) => {
  const auth = useAuthStore()

  const requiresAuth = to.meta.requiresAuth !== false &&
    (to.meta.requiresAuth === true || to.matched.some((r) => r.meta.requiresAuth))

  // Rutas que no requieren auth
  if (!requiresAuth) {
    // Si ya está autenticado y va a /login, redirigir al home
    if (to.path === '/login' && auth.isAuthenticated) {
      return auth.getDefaultRoute()
    }
    return true
  }

  // Ruta protegida: verificar autenticación
  if (!auth.isAuthenticated) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  // Verificar roles permitidos en la ruta
  const allowedRoles = to.meta.roles
  if (allowedRoles && allowedRoles.length > 0) {
    const userRole = auth.user?.role
    if (!userRole || !allowedRoles.includes(userRole)) {
      // Redirigir al home del rol actual en lugar de 403
      return auth.getDefaultRoute()
    }
  }

  return true
})

export default router
