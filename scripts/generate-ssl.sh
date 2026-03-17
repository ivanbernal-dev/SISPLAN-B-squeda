#!/bin/bash
# ============================================================
# UBPD — Generar Certificados SSL Autofirmados
# Ejecutar ANTES del primer `docker compose up`
# ============================================================

set -e

SERVER_IP="${1:-192.168.1.100}"
CERTS_DIR="$(dirname "$0")/../nginx/certs"

mkdir -p "$CERTS_DIR"

echo "🔐 Generando certificado SSL autofirmado para IP: $SERVER_IP"

openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout "$CERTS_DIR/server.key" \
  -out "$CERTS_DIR/server.crt" \
  -subj "/C=CO/ST=Bogota/L=Bogota/O=UBPD/OU=IT/CN=$SERVER_IP" \
  -addext "subjectAltName=IP:$SERVER_IP,DNS:ubpd.local"

echo ""
echo "✅ Certificados generados en $CERTS_DIR/"
echo "   - server.crt (certificado público — distribuir a clientes)"
echo "   - server.key (clave privada — NUNCA compartir)"
echo ""
echo "Para instalar en Windows (clientes):"
echo "  1. Copiar server.crt al cliente"
echo "  2. Doble clic → Instalar → 'Entidades de certificación raíz de confianza'"
