<!-- frontend/src/layouts/AdminLayout.vue -->
<!-- Agregar al menú, sin reemplazar el acceso al Dashboard BI. -->

<RouterLink
  v-if="puedeVer(['ADMIN', 'OAP', 'DIRECTIVO', 'CONSULTA'])"
  to="/admin/comite-directivo"
  class="sidebar-link"
  active-class="sidebar-link-active"
>
  <ChartBarSquareIcon class="h-5 w-5" />
  <span>Comité Directivo</span>
</RouterLink>
