<template>
  <!-- Componente raíz: sólo el outlet de rutas.
       Toda la lógica de layout se gestiona en los layouts dedicados. -->
  <RouterView />

  <!-- Toast de notificaciones globales -->
  <NotificationToast />
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import NotificationToast from './components/common/NotificationToast.vue'
</script>
