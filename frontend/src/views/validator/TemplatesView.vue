<!-- Templates del validador: reutiliza el componente de admin sin la opción de desactivar -->
<template>
  <AdminTemplatesView :show-deactivate="false" />
</template>

<script setup lang="ts">
import AdminTemplatesView from '@/views/admin/TemplatesView.vue'
</script>
