#!/bin/bash
# ============================================================
# UBPD — Script de Backup de Datos
# Recomendado: ejecutar diariamente via cron en el servidor
# Cron: 0 2 * * * /opt/ubpd/ubpd-app/scripts/backup.sh
# ============================================================

set -e

BACKUP_DIR="/opt/ubpd/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# ─── Backup PostgreSQL ────────────────────────────────────
echo "📦 Backup de PostgreSQL..."
docker compose -f /opt/ubpd/ubpd-app/docker-compose.yml \
  exec -T postgres \
  pg_dump -U ubpd_user ubpd_db \
  | gzip > "$BACKUP_DIR/postgres_$DATE.sql.gz"

echo "✅ BD guardada: $BACKUP_DIR/postgres_$DATE.sql.gz"

# ─── Backup MinIO (archivos) ─────────────────────────────
echo "📦 Backup de archivos MinIO..."
docker run --rm \
  -v ubpd_minio_data:/data \
  -v "$BACKUP_DIR":/backup \
  alpine tar czf "/backup/minio_$DATE.tar.gz" /data

echo "✅ Archivos guardados: $BACKUP_DIR/minio_$DATE.tar.gz"

# ─── Limpiar backups de más de 30 días ───────────────────
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete
echo "🗑️  Backups antiguos eliminados"

echo ""
echo "✅ Backup completado: $DATE"
