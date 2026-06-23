<template>
  <div class="min-h-screen bg-slate-50">
    <header class="sticky top-0 z-40 border-b border-gray-200 bg-white shadow-sm">
      <div class="mx-auto flex max-w-[1800px] items-center gap-4 px-4 py-3 sm:px-6">
        <RouterLink to="/comite-directivo" class="shrink-0">
          <img
            src="/logo-ubpd.png"
            alt="UBPD - Unidad de Búsqueda de Personas dadas por Desaparecidas"
            class="h-12 w-auto object-contain"
          />
        </RouterLink>
        <div class="border-l border-gray-200 pl-4">
          <h1 class="text-base font-bold leading-tight text-gray-900">Visor de Indicadores Comité Directivo</h1>
          <p class="text-xs text-gray-500">Unidad de Búsqueda de Personas dadas por Desaparecidas</p>
        </div>
        <nav class="ml-auto hidden items-center gap-2 text-xs font-semibold text-gray-500 md:flex">
          <RouterLink to="/estadisticas" class="rounded-lg px-3 py-2 hover:bg-gray-100">PAI 2026</RouterLink>
          <RouterLink to="/bi" class="rounded-lg px-3 py-2 hover:bg-gray-100">Visor BI</RouterLink>
        </nav>
      </div>
    </header>
    <main class="mx-auto max-w-[1800px] p-4 sm:p-6">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>
