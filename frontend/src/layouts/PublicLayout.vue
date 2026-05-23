<template>
  <div class="flex min-h-screen flex-col bg-white">

    <!-- ── Header público ────────────────────────────────── -->
    <header class="sticky top-0 z-20 bg-white border-b border-ubpd-gris-borde shadow-sm">
      <div class="mx-auto flex max-w-7xl items-center gap-4 px-4 py-4 sm:px-6">

        <!-- Logo + título -->
        <router-link to="/estadisticas" class="shrink-0">
          <img
            src="/logo-ubpd-placeholder.svg"
            alt="UBPD — Unidad de Búsqueda"
            class="h-10 w-auto"
          />
        </router-link>
        <div class="border-l border-ubpd-gris-borde pl-4">
          <h1 class="text-base font-bold text-ubpd-gris leading-tight">
            Sistema de Estadísticas
          </h1>
          <p class="text-xs text-ubpd-gris/60">Unidad de Búsqueda de Personas dadas por Desaparecidas</p>
        </div>
      </div>
    </header>

    <!-- ── Contenido de la vista (3 niveles) ─────────────── -->
    <main class="flex-1">
      <RouterView />
    </main>

    <!-- ── Footer ─────────────────────────────────────────── -->
    <footer class="bg-ubpd-gris text-white/70 py-6 mt-auto">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs">
        <span>© {{ currentYear }} Unidad de Búsqueda de Personas dadas por Desaparecidas — UBPD</span>
        <span class="text-white/40">Sistema de Gestión de Formularios y Estadísticas</span>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'

const currentYear = new Date().getFullYear()
</script>
