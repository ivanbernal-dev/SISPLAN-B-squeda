<template>
  <div class="p-6">
    <!-- TODO: Formulario de creación/edición de usuario -->
    <h2 class="text-xl font-semibold text-ubpd-gris">
      {{ isNew ? 'Crear Usuario' : 'Editar Usuario' }}
    </h2>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isNew = computed(() => !route.params.id)
</script>
