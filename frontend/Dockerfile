# ============================================================
# UBPD Frontend — Vue.js 3 + Vite
# Build multistage: Node (build) → Nginx (serve)
# ============================================================

# ──────────────────────────────────────────────
# STAGE 1: Build
# ──────────────────────────────────────────────
FROM node:20-alpine AS builder

ARG VITE_API_BASE_URL=/api

WORKDIR /app

# Copiar archivos de dependencias primero (caché de Docker)
COPY package.json package-lock.json ./

# Instalar dependencias
# En modo air-gapped: node_modules ya viene copiado o se usa npm ci --offline
RUN npm ci

# Copiar el resto del código
COPY . .

# Variables de entorno para el build de Vite
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Construir la aplicación para producción
# Todas las fuentes, íconos y librerías quedan embebidas en /app/dist
RUN npm run build

# ──────────────────────────────────────────────
# STAGE 2: Serve con Nginx
# ──────────────────────────────────────────────
FROM nginx:1.25-alpine AS production

LABEL maintainer="UBPD Dev Team"
LABEL description="Frontend Vue.js para UBPD"

# Copiar el build de Vite
COPY --from=builder /app/dist /usr/share/nginx/html

# Copiar configuración de Nginx para SPA (Vue Router history mode)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Puerto interno
EXPOSE 3000

# Nginx en primer plano
CMD ["nginx", "-g", "daemon off;"]
