# Guía de Despliegue — UBPD (Red Local Air-Gapped)

## Requisitos del Servidor

| Componente | Mínimo | Recomendado |
|-----------|--------|-------------|
| CPU | 4 núcleos | 8 núcleos |
| RAM | 8 GB | 16 GB |
| Disco | 100 GB SSD | 500 GB SSD |
| SO | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| Docker | 24+ | 25+ |
| Docker Compose | v2.20+ | v2.24+ |

---

## Fase 1: Preparación (Máquina con Internet)

### 1.1 Descargar imágenes Docker

```bash
# En una máquina con acceso a internet:
docker pull postgres:16-alpine
docker pull redis:7-alpine
docker pull nginx:1.25-alpine
docker pull minio/minio:latest
docker pull python:3.12-slim
docker pull node:20-alpine

# Guardar todas las imágenes en un archivo comprimido
docker save \
  postgres:16-alpine \
  redis:7-alpine \
  nginx:1.25-alpine \
  minio/minio:latest \
  python:3.12-slim \
  node:20-alpine \
  | gzip > ubpd-docker-images.tar.gz
```

### 1.2 Descargar dependencias npm (frontend)

```bash
# Con internet, instalar dependencias y guardar node_modules
cd frontend/
npm install
# Los node_modules ya quedan locales para el build
```

### 1.3 Descargar dependencias Python (backend)

```bash
# Con internet, descargar wheels para instalación offline
pip download -r backend/requirements.txt -d ./vendor/python-wheels/
```

---

## Fase 2: Instalación en Servidor Local

### 2.1 Transferir archivos al servidor

```bash
# Copiar por USB o transferencia de red local (scp, rsync)
scp ubpd-docker-images.tar.gz usuario@SERVER_IP:/opt/ubpd/
scp -r ubpd-app/ usuario@SERVER_IP:/opt/ubpd/
```

### 2.2 Cargar imágenes Docker en el servidor

```bash
ssh usuario@SERVER_IP
cd /opt/ubpd/
docker load -i ubpd-docker-images.tar.gz
# Verificar que las imágenes están cargadas:
docker images
```

### 2.3 Configurar variables de entorno

```bash
cd /opt/ubpd/ubpd-app/
cp .env.example .env
nano .env   # Editar con los valores del servidor
```

Variables **obligatorias** a cambiar:

```env
SERVER_IP=192.168.1.100      # IP del servidor en la red local
SECRET_KEY=cambiar-por-clave-muy-larga-y-aleatoria
POSTGRES_PASSWORD=cambiar-por-password-seguro
MINIO_ROOT_PASSWORD=cambiar-por-password-seguro
```

### 2.4 Generar Certificados SSL Autofirmados

```bash
# En el servidor:
mkdir -p /opt/ubpd/ubpd-app/nginx/certs/

openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout /opt/ubpd/ubpd-app/nginx/certs/server.key \
  -out /opt/ubpd/ubpd-app/nginx/certs/server.crt \
  -subj "/C=CO/ST=Bogota/L=Bogota/O=UBPD/CN=192.168.1.100" \
  -addext "subjectAltName=IP:192.168.1.100"
```

### 2.5 Levantar el sistema

```bash
cd /opt/ubpd/ubpd-app/

# Construir imágenes custom (frontend + backend)
docker compose build

# Iniciar todos los servicios
docker compose up -d

# Verificar que todos los servicios están corriendo
docker compose ps

# Ver logs en tiempo real
docker compose logs -f
```

### 2.6 Inicialización de la base de datos

```bash
# Las migraciones se ejecutan automáticamente al iniciar el backend
# Pero se puede ejecutar manualmente:
docker compose exec backend alembic upgrade head

# Crear usuario administrador inicial:
docker compose exec backend python scripts/create_admin.py \
  --username admin \
  --password "Admin@2024!" \
  --nombre "Administrador UBPD"
```

---

## Fase 3: Configuración de Clientes

### 3.1 Instalar certificado SSL en los navegadores

Para que los clientes no vean advertencia de seguridad:

**Windows (todos los navegadores excepto Firefox):**
1. Copiar `server.crt` al equipo cliente
2. Doble clic → Instalar certificado → Almacén: "Entidades de certificación raíz de confianza"

**Firefox (cualquier SO):**
1. `about:preferences#privacy` → Ver certificados → Importar
2. Seleccionar `server.crt` → Marcar "Confiar para sitios web"

**macOS:**
```bash
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain server.crt
```

### 3.2 Acceder al sistema

- **Aplicación**: `https://192.168.1.100`
- **API docs** (desarrollo): `https://192.168.1.100/api/docs`
- **MinIO Console**: `https://192.168.1.100:9001`

---

## Comandos de Administración

### Estado del sistema

```bash
# Ver estado de todos los servicios
docker compose ps

# Ver uso de recursos
docker stats

# Ver logs de un servicio específico
docker compose logs -f backend
docker compose logs -f celery
```

### Backup de datos

```bash
# Backup de PostgreSQL
docker compose exec postgres pg_dump -U ubpd_user ubpd_db \
  | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Backup de MinIO (archivos subidos)
docker run --rm \
  -v ubpd_minio_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/minio_$(date +%Y%m%d).tar.gz /data
```

### Restaurar backup

```bash
# Restaurar PostgreSQL
gunzip -c backup_20240101_120000.sql.gz \
  | docker compose exec -T postgres psql -U ubpd_user ubpd_db
```

### Actualizar el sistema

```bash
# 1. Descargar nueva versión del código (por USB o red local)
# 2. Reconstruir solo las imágenes afectadas
docker compose build backend
docker compose build frontend

# 3. Reiniciar sin bajar todos los servicios
docker compose up -d --no-deps backend frontend

# 4. Aplicar migraciones si las hay
docker compose exec backend alembic upgrade head
```

### Reiniciar servicios

```bash
# Reiniciar un servicio específico
docker compose restart backend

# Reiniciar todo el stack
docker compose restart

# Apagar todo (los datos persisten en volúmenes)
docker compose down

# Apagar y BORRAR VOLÚMENES (¡destructivo! — solo para reinstalación)
docker compose down -v
```

---

## Configuración de Red

### IP del Servidor (Estática Recomendada)

Configurar IP estática en el servidor Ubuntu:

```yaml
# /etc/netplan/00-installer-config.yaml
network:
  ethernets:
    ens3:
      dhcp4: no
      addresses: [192.168.1.100/24]
      gateway4: 192.168.1.1
      nameservers:
        addresses: [192.168.1.1]
  version: 2
```

```bash
sudo netplan apply
```

### Sincronización de Tiempo (NTP Local)

Si la red tiene un servidor NTP interno:

```bash
# En Ubuntu del servidor
sudo timedatectl set-ntp true
sudo nano /etc/systemd/timesyncd.conf
# Agregar: NTP=192.168.1.1
sudo systemctl restart systemd-timesyncd
```

---

## Monitoreo y Alertas

### Health Checks (incluidos en docker-compose.yml)

- `backend`: GET `/api/health` cada 30s
- `postgres`: `pg_isready` cada 30s
- `redis`: `redis-cli ping` cada 30s
- `minio`: GET `/minio/health/live` cada 30s

### Ver métricas en el panel de Admin

El panel de Admin en `/admin/pipelines` muestra:
- Estado del último pipeline de cálculo
- Timestamp del último cálculo exitoso
- Errores recientes en los pipelines
