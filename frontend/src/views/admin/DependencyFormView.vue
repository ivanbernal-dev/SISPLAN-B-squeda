<template>
  <div class="p-6">
    <!-- TODO: Formulario de creación/edición de dependencia -->
    <h2 class="text-xl font-semibold text-ubpd-gris">
      {{ isNew ? 'Crear Dependencia' : 'Editar Dependencia' }}
    </h2>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isNew = computed(() => !route.params.id)
</script>
