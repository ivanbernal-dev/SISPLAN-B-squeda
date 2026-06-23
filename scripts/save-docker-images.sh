#!/bin/bash
# ============================================================
# UBPD — Guardar imágenes Docker para transferencia air-gapped
# Ejecutar en máquina CON internet antes de instalar en servidor
# ============================================================

set -e

OUTPUT_FILE="ubpd-docker-images-$(date +%Y%m%d).tar.gz"

echo "📦 Descargando imágenes Docker para UBPD..."

docker pull postgres:16-alpine
docker pull valkey/valkey:7-alpine
docker pull nginx:1.25-alpine
docker pull minio/minio:latest
docker pull python:3.12-slim
docker pull node:20-alpine

echo "💾 Guardando imágenes en $OUTPUT_FILE ..."

docker save \
  postgres:16-alpine \
  valkey/valkey:7-alpine \
  nginx:1.25-alpine \
  minio/minio:latest \
  python:3.12-slim \
  node:20-alpine \
  | gzip > "$OUTPUT_FILE"

echo "✅ Listo: $OUTPUT_FILE ($(du -sh $OUTPUT_FILE | cut -f1))"
echo ""
echo "Transferir al servidor con:"
echo "  scp $OUTPUT_FILE usuario@SERVER_IP:/opt/ubpd/"
