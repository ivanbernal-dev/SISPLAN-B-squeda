# Identidad Visual — Manual UBPD aplicado al Frontend

> Basado en el **Manual de Identidad UBPD V4 (17-12-2024)**

---

## Paleta de Colores

### Colores Primarios Institucionales

| Nombre | HEX | Uso Principal |
|--------|-----|---------------|
| Lila Institucional | `#A97CC9` | Branding principal, Gauges Nivel 1, encabezados |
| Verde Institucional | `#52ABAB` | Éxito, campos activos, botón Aprobar, esperanza |
| Blanco | `#FFFFFF` | Fondo principal para máxima legibilidad |

### Colores para Interfaz Web

| Nombre | HEX | Uso |
|--------|-----|-----|
| Teal Oscuro | `#3E818F` | Sidebar admin, headers, botones de acción primaria |
| Morado Web | `#8351CC` | Links, interacciones secundarias |
| Naranja Alerta | `#FF6900` | Estado Devuelto/Rechazado, alertas críticas, CTA |
| Gris Oscuro | `#323232` | Texto de cuerpo, tablas, alta legibilidad |
| Gris Claro | `#F5F5F5` | Campos readonly, fondos de sección |
| Gris Medio | `#E0E0E0` | Bordes, separadores |

### Configuración Tailwind CSS (`tailwind.config.js`)

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        ubpd: {
          lila:    '#A97CC9',
          verde:   '#52ABAB',
          teal:    '#3E818F',
          morado:  '#8351CC',
          naranja: '#FF6900',
          gris:    '#323232',
        }
      }
    }
  }
}
```

### Variables CSS (`main.css`)

```css
:root {
  --color-primary:     #A97CC9;
  --color-success:     #52ABAB;
  --color-action:      #3E818F;
  --color-link:        #8351CC;
  --color-warning:     #FF6900;
  --color-text:        #323232;
  --color-bg:          #FFFFFF;
  --color-bg-readonly: #F5F5F5;
  --color-border:      #E0E0E0;
}
```

---

## Tipografía

### Jerarquía de Fuentes

| Uso | Fuente | Peso | Tamaño |
|-----|--------|------|--------|
| Títulos H1-H3 | Playfair Display o Montserrat | 700 | 2xl - 4xl |
| Subtítulos H4-H6 | Montserrat | 600 | lg - xl |
| Cuerpo de texto | Barlow | 400 | base (16px) |
| Formularios e inputs | Barlow | 400 | sm-base |
| Tablas de datos | Barlow | 400 | sm |
| Botones | Barlow | 600 | sm |
| Labels | Barlow | 500 | xs-sm |

### Archivos de Fuentes (Instalación Local)

Las fuentes deben instalarse **vía npm** o como archivos `.woff2` locales. **Prohibido usar Google Fonts CDN**.

```bash
# Opción 1: npm (recomendado para Vite)
npm install @fontsource/barlow @fontsource/montserrat @fontsource/playfair-display

# Opción 2: Archivos locales (air-gapped)
# Descargar .woff2 y colocar en /frontend/src/assets/fonts/
```

```css
/* Si se usan archivos locales */
@font-face {
  font-family: 'Barlow';
  src: url('@/assets/fonts/barlow-regular.woff2') format('woff2');
  font-weight: 400;
  font-style: normal;
}
```

---

## Logo y Área de Reserva

- El logo de la Unidad de Búsqueda debe ubicarse en el **Header** de todas las vistas.
- Área de reserva mínima: espacio equivalente al **alto de la letra "U"** del identificador en todos los costados.
- Ningún elemento puede invadir ese espacio alrededor del logo.
- En el header, el logo va a la izquierda con su área de reserva respetada.

---

## Componentes por Estado

### Estados de Formulario

| Estado | Color | Label | Icono |
|--------|-------|-------|-------|
| Borrador (`draft`) | `#E0E0E0` gris | "Borrador" | lápiz |
| Enviado (`pending`) | `#3E818F` teal | "En Revisión" | reloj |
| Devuelto (`rejected`) | `#FF6900` naranja | "Requiere Corrección" | alerta |
| Aprobado (`approved`) | `#52ABAB` verde | "Aprobado" | check |

### Campos de Formulario

```css
/* Campo editable activo */
.input-field:focus {
  border-color: #52ABAB;       /* Verde institucional */
  box-shadow: 0 0 0 2px rgba(82, 171, 171, 0.2);
}

/* Campo readonly */
.input-readonly {
  background-color: #F5F5F5;
  cursor: not-allowed;
  color: #666;
  border-color: #E0E0E0;
}
```

### Botones

| Tipo | Color Fondo | Color Texto | Uso |
|------|-------------|-------------|-----|
| Primario / Enviar | `#3E818F` Teal | Blanco | Enviar a validación, guardar |
| Éxito / Aprobar | `#52ABAB` Verde | Blanco | Aprobar formulario |
| Alerta / Rechazar | `#FF6900` Naranja | Blanco | Rechazar formulario |
| Secundario | Transparente | `#3E818F` | Acciones secundarias |
| Peligro | `#C0392B` | Blanco | Eliminar (con confirmación) |

---

## Gráficos Gauge (Velocímetros)

### Nivel 1 — Indicadores Globales

```javascript
// Configuración ECharts para Gauge Nivel 1
{
  type: 'gauge',
  axisLine: {
    lineStyle: {
      width: 20,
      color: [
        [0.3, '#FF6900'],    // 0-30%: Naranja (alerta)
        [0.7, '#A97CC9'],    // 30-70%: Lila institucional
        [1,   '#52ABAB'],    // 70-100%: Verde (logro)
      ]
    }
  },
  title: { fontFamily: 'Playfair Display', fontSize: 14 },
  detail: { fontFamily: 'Barlow', fontSize: 20, fontWeight: 600 }
}
```

### Nivel 2 — Completitud por Template

```javascript
// Mismo gauge pero con colores secundarios de la paleta
{
  axisLine: {
    lineStyle: {
      color: [
        [0.4, '#FF6900'],
        [0.75, '#3E818F'],
        [1,   '#52ABAB'],
      ]
    }
  }
}
```

---

## Texturas e Ilustraciones

- Se puede usar la **trama topográfica (curvas de nivel)** del manual UBPD como fondo sutil en el dashboard.
- Implementar como patrón SVG o imagen PNG con baja opacidad (`opacity: 0.05`).
- Usar en el header del dashboard público y en la página de login.

---

## Lenguaje y Nomenclatura

### En Interfaces Públicas

| ❌ No usar | ✅ Usar en su lugar |
|-----------|------------------|
| "UBPD" solo | "Unidad de Búsqueda" |
| "Víctimas" | "Personas dadas por desaparecidas" |
| "Capturado" | "Registrado" |
| "Rechazado" | "Requiere corrección" / "Devuelto" |
| "Inválido" | "Pendiente de ajuste" |

### Mensajes de Estado (Lenguaje Humanitario)

```javascript
const ESTADO_LABELS = {
  draft:    'Borrador',
  pending:  'Enviado para revisión',
  rejected: 'Requiere corrección',
  approved: 'Registro validado',
};

const ESTADO_MESSAGES = {
  rejected: 'Este registro ha sido devuelto con observaciones para su ajuste.',
  approved: 'Este registro ha sido validado y hace parte del reporte oficial.',
};
```

---

## Imágenes y Multimedia

- **Fotografías**: Naturales, sinceras, personas en acción y empoderamiento.
- **Prohibido**: Armas de fuego, personas heridas, violencia explícita.
- **Privacidad**: Si hay riesgo, usar ilustraciones o efecto blur narrativo.
- **Videos**: Full HD (1920×1080), formato H.264-MP4. Servidos desde MinIO.

---

## Accesibilidad

- Contraste mínimo WCAG AA (4.5:1) para texto sobre fondo.
- Los combos `#323232` sobre `#FFFFFF` y `#FFFFFF` sobre `#3E818F` cumplen este estándar.
- `aria-label` obligatorio en iconos sin texto visible.
- `role` y `aria-live` en bandejas de entrada para lectores de pantalla.
