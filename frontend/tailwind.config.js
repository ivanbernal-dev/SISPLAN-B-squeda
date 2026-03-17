/** ============================================================
 * UBPD Frontend — Configuración Tailwind CSS
 * Paleta UBPD según Manual de Identidad V4
 * ============================================================ */

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // ─── Colores Institucionales UBPD ─────────────────
        ubpd: {
          lila:          '#A97CC9',  // Identidad principal, Gauges Nivel 1
          verde:         '#52ABAB',  // Éxito, campo activo, botón Aprobar
          teal:          '#3E818F',  // Sidebar, header, acción primaria
          morado:        '#8351CC',  // Links, interacciones
          naranja:       '#FF6900',  // Alertas, Devuelto, CTA
          gris:          '#323232',  // Texto cuerpo
          'gris-claro':  '#F5F5F5',  // Campos readonly
          'gris-borde':  '#E0E0E0',  // Bordes
        },
      },

      fontFamily: {
        // Tipografía UBPD — instalada localmente vía npm @fontsource
        titulo:    ['Playfair Display', 'Montserrat', 'serif'],
        subtitulo: ['Montserrat', 'sans-serif'],
        cuerpo:    ['Barlow', 'sans-serif'],
        // Fuente de sistema como fallback
        sans:      ['Barlow', 'system-ui', 'sans-serif'],
      },

      // Animaciones suaves para los gauges
      transitionDuration: {
        '400': '400ms',
        '600': '600ms',
      },
    },
  },

  plugins: [
    require('@tailwindcss/forms'),
  ],
}
