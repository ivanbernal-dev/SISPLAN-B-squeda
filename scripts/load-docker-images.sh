#!/bin/bash
# ============================================================
# UBPD — Cargar imágenes Docker en el servidor local (air-gapped)
# Ejecutar en el SERVIDOR de la red local
# ============================================================

set -e

IMAGE_FILE="${1:-ubpd-docker-images.tar.gz}"

if [ ! -f "$IMAGE_FILE" ]; then
  echo "❌ Archivo no encontrado: $IMAGE_FILE"
  echo "Uso: ./load-docker-images.sh [ruta-al-archivo.tar.gz]"
  exit 1
fi

echo "📦 Cargando imágenes Docker desde $IMAGE_FILE ..."
docker load -i "$IMAGE_FILE"

echo ""
echo "✅ Imágenes cargadas:"
docker images | grep -E "postgres|valkey|nginx|minio|python|node"
