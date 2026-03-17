// ============================================================
// UBPD Frontend — Configuración Vite
// ============================================================

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],

  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },

  // Servidor de desarrollo (solo para desarrollo local con internet)
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      // Proxy al backend durante desarrollo
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },

  build: {
    outDir: 'dist',
    // Separar vendors para mejor caching
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia', 'axios'],
          charts: ['echarts', 'vue-echarts'],
        },
      },
    },
  },
})
