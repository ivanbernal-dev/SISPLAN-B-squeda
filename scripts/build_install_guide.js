// Genera docs/INSTALACION.docx — instructivo end-to-end de instalación
// del Sistema UBPD (Windows, Linux y macOS).
//
// Uso:  NODE_PATH=$(npm root -g) node scripts/build_install_guide.js
// Salida: docs/INSTALACION.docx

const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, LevelFormat, PageBreak,
  PageNumber, BorderStyle, WidthType, ShadingType, TabStopType,
  TabStopPosition, TableOfContents, PageOrientation,
} = require('docx');

// ─── Helpers ──────────────────────────────────────────────────────────────
const FONT = 'Arial';
const COLOR_TITLE = '1A3C5E';
const COLOR_ACCENT = '2E75B6';
const COLOR_BG_HEADER = 'D5E8F0';
const COLOR_BG_CODE = 'F1F3F5';

const para = (text, opts = {}) => new Paragraph({
  spacing: { after: 100, ...(opts.spacing || {}) },
  ...opts,
  children: opts.children || [new TextRun({ text, font: FONT, size: 22 })],
});

const heading = (text, level = HeadingLevel.HEADING_1) => new Paragraph({
  heading: level,
  spacing: { before: 280, after: 160 },
  children: [new TextRun({ text, font: FONT, bold: true, color: COLOR_TITLE })],
});

const bullet = (text, level = 0, runs = null) => new Paragraph({
  numbering: { reference: 'bullets', level },
  spacing: { after: 60 },
  children: runs || [new TextRun({ text, font: FONT, size: 22 })],
});

const numbered = (text, runs = null) => new Paragraph({
  numbering: { reference: 'numbers', level: 0 },
  spacing: { after: 80 },
  children: runs || [new TextRun({ text, font: FONT, size: 22 })],
});

// Bloque de código (texto monoespaciado sobre fondo gris claro)
const codeBlock = (code) => {
  return code.split('\n').map((line, i) => new Paragraph({
    spacing: { after: 0, line: 240 },
    shading: { fill: COLOR_BG_CODE, type: ShadingType.CLEAR },
    children: [new TextRun({ text: line || ' ', font: 'Consolas', size: 20 })],
  }));
};

// Tabla simple 2 columnas (clave, valor)
const kvTable = (rows, widths = [3000, 6360]) => new Table({
  width: { size: widths[0] + widths[1], type: WidthType.DXA },
  columnWidths: widths,
  rows: rows.map((r, idx) => new TableRow({
    children: r.map((cell, i) => new TableCell({
      width: { size: widths[i], type: WidthType.DXA },
      shading: idx === 0
        ? { fill: COLOR_BG_HEADER, type: ShadingType.CLEAR }
        : undefined,
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      borders: {
        top:    { style: BorderStyle.SINGLE, size: 4, color: 'BBBBBB' },
        bottom: { style: BorderStyle.SINGLE, size: 4, color: 'BBBBBB' },
        left:   { style: BorderStyle.SINGLE, size: 4, color: 'BBBBBB' },
        right:  { style: BorderStyle.SINGLE, size: 4, color: 'BBBBBB' },
      },
      children: [new Paragraph({
        children: [new TextRun({
          text: cell,
          font: FONT,
          size: 20,
          bold: idx === 0,
        })],
      })],
    })),
  })),
});

// ─── Contenido del documento ──────────────────────────────────────────────

const children = [];

// Portada
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { before: 2000, after: 280 },
  children: [new TextRun({
    text: 'Sistema de Indicadores',
    font: FONT, bold: true, size: 56, color: COLOR_TITLE,
  })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 1600 },
  children: [new TextRun({
    text: 'Guía de Instalación y Puesta en Marcha',
    font: FONT, size: 36, color: COLOR_ACCENT,
  })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  children: [new TextRun({
    text: 'Documento técnico — paso a paso de instalación, configuración y verificación',
    font: FONT, italics: true, size: 22, color: '666666',
  })],
}));
children.push(new Paragraph({ children: [new PageBreak()] }));

// Tabla de contenido
children.push(heading('Tabla de contenido'));
children.push(new TableOfContents('Contenido', { hyperlink: true, headingStyleRange: '1-2' }));
children.push(new Paragraph({ children: [new PageBreak()] }));

// 1. Introducción
children.push(heading('1. Introducción'));
children.push(para(
  'Este documento describe el procedimiento completo para instalar, configurar y ' +
  'poner en marcha el Sistema de Indicadores en un servidor o estación de trabajo. ' +
  'Soporta los sistemas operativos Windows 10 / 11, distribuciones Linux modernas ' +
  '(Ubuntu 22.04+, Debian 12+, RHEL 8+) y macOS 12+.',
));
children.push(para(
  'La arquitectura se basa en contenedores Docker, lo que permite que el procedimiento ' +
  'sea idéntico en cualquier sistema operativo. No es necesario instalar dependencias ' +
  'de Python, Node.js o PostgreSQL directamente en el host: todo corre dentro de los ' +
  'contenedores.',
));
children.push(heading('Componentes del sistema', HeadingLevel.HEADING_2));
[
  'Backend FastAPI (Python 3.12) — API REST, autenticación y lógica de negocio.',
  'Frontend Vue 3 / Vite — interfaz web servida por Nginx.',
  'PostgreSQL 16 — base de datos relacional.',
  'MinIO — almacenamiento de archivos adjuntos (compatible S3).',
  'Valkey (Redis) — caché y colas de tareas en segundo plano.',
  'Celery — worker para tareas asíncronas.',
  'Nginx — proxy inverso que enruta /api al backend y / al frontend.',
].forEach((b) => children.push(bullet(b)));

// 2. Requerimientos
children.push(heading('2. Requerimientos de hardware'));
children.push(kvTable([
  ['Recurso', 'Mínimo recomendado'],
  ['Procesador', '4 núcleos (x86_64 o ARM64)'],
  ['Memoria RAM', '8 GB (16 GB recomendado para uso con muchos formularios)'],
  ['Disco', '20 GB libres en SSD'],
  ['Red', 'Conexión de salida para descargar imágenes Docker la primera vez'],
  ['Puertos libres', '80 (HTTP), opcionalmente 443 (HTTPS)'],
]));

// 3. Software a instalar
children.push(heading('3. Software a instalar'));
children.push(para(
  'Independiente del sistema operativo, solo se requieren dos componentes en el host:',
));
children.push(bullet('Docker Engine versión 24.0 o superior.'));
children.push(bullet('Docker Compose v2 (incluido en Docker Desktop y en el plugin docker-compose-plugin para Linux).'));
children.push(bullet('Git para clonar el repositorio.'));

children.push(heading('3.1. Instalación en Windows', HeadingLevel.HEADING_2));
children.push(numbered('Descargar Docker Desktop desde https://www.docker.com/products/docker-desktop/ y ejecutar el instalador como administrador.'));
children.push(numbered('Habilitar la integración con WSL 2 cuando lo solicite el instalador. Si WSL no está instalado, ejecutar en PowerShell como administrador: wsl --install.'));
children.push(numbered('Reiniciar el equipo si lo solicita.'));
children.push(numbered('Abrir Docker Desktop y aceptar los términos de uso. Esperar a que el ícono indique "Engine running".'));
children.push(numbered('Instalar Git desde https://git-scm.com/download/win con las opciones por defecto.'));
children.push(numbered('Abrir PowerShell o Windows Terminal y verificar:'));
codeBlock('docker --version\ndocker compose version\ngit --version').forEach((p) => children.push(p));

children.push(heading('3.2. Instalación en Linux (Ubuntu / Debian)', HeadingLevel.HEADING_2));
children.push(numbered('Actualizar paquetes:'));
codeBlock('sudo apt update && sudo apt upgrade -y').forEach((p) => children.push(p));
children.push(numbered('Instalar dependencias de soporte:'));
codeBlock('sudo apt install -y ca-certificates curl gnupg git').forEach((p) => children.push(p));
children.push(numbered('Agregar la clave GPG y el repositorio oficial de Docker:'));
codeBlock(
  'sudo install -m 0755 -d /etc/apt/keyrings\n' +
  'curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \\\n' +
  '  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg\n' +
  'sudo chmod a+r /etc/apt/keyrings/docker.gpg\n' +
  'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \\\n' +
  '  https://download.docker.com/linux/ubuntu $(. /etc/os-release; echo $VERSION_CODENAME) stable" | \\\n' +
  '  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null'
).forEach((p) => children.push(p));
children.push(numbered('Instalar Docker y el plugin Compose:'));
codeBlock(
  'sudo apt update\n' +
  'sudo apt install -y docker-ce docker-ce-cli containerd.io \\\n' +
  '  docker-buildx-plugin docker-compose-plugin'
).forEach((p) => children.push(p));
children.push(numbered('Agregar el usuario actual al grupo docker (para no requerir sudo en cada comando):'));
codeBlock('sudo usermod -aG docker $USER\n# Cerrar sesión y volver a entrar para que aplique').forEach((p) => children.push(p));
children.push(numbered('Verificar la instalación:'));
codeBlock('docker --version\ndocker compose version').forEach((p) => children.push(p));

children.push(heading('3.3. Instalación en macOS', HeadingLevel.HEADING_2));
children.push(numbered('Descargar Docker Desktop para Mac (Apple Silicon o Intel según corresponda) desde https://www.docker.com/products/docker-desktop/.'));
children.push(numbered('Abrir el archivo .dmg y arrastrar Docker.app a Aplicaciones.'));
children.push(numbered('Iniciar Docker y aceptar los permisos.'));
children.push(numbered('Instalar Git si no está disponible: brew install git (requiere Homebrew).'));
children.push(numbered('Verificar:'));
codeBlock('docker --version\ndocker compose version\ngit --version').forEach((p) => children.push(p));

// 4. Clonar repositorio
children.push(heading('4. Obtener el código fuente'));
children.push(para(
  'Clonar el repositorio en la carpeta de trabajo. El comando es idéntico en Windows ' +
  '(PowerShell o Git Bash), Linux y macOS:',
));
codeBlock(
  'cd /ruta/donde/quieres/instalar\n' +
  'git clone <URL_DEL_REPOSITORIO> sistema-indicadores\n' +
  'cd sistema-indicadores'
).forEach((p) => children.push(p));

// 5. Variables de entorno
children.push(heading('5. Configuración de variables de entorno'));
children.push(para(
  'Toda la configuración sensible vive en un archivo .env en la raíz del proyecto. ' +
  'Se incluye un .env.example como plantilla:',
));
codeBlock('cp .env.example .env').forEach((p) => children.push(p));
children.push(para(
  'En Windows PowerShell se usa "copy" en lugar de "cp":',
));
codeBlock('copy .env.example .env').forEach((p) => children.push(p));
children.push(para(
  'Editar el archivo .env con un editor de texto y ajustar como mínimo las siguientes ' +
  'variables. Use contraseñas largas y aleatorias en producción.',
));

children.push(heading('Variables obligatorias', HeadingLevel.HEADING_2));
children.push(kvTable([
  ['Variable', 'Descripción y valor sugerido'],
  ['POSTGRES_USER', 'Usuario de la base de datos. Sugerido: ubpd_user'],
  ['POSTGRES_PASSWORD', 'Contraseña fuerte de PostgreSQL (mínimo 16 caracteres)'],
  ['POSTGRES_DB', 'Nombre de la base. Sugerido: ubpd'],
  ['MINIO_ROOT_USER', 'Usuario administrador de MinIO'],
  ['MINIO_ROOT_PASSWORD', 'Contraseña de MinIO (mínimo 12 caracteres)'],
  ['MINIO_BUCKET_NAME', 'Nombre del bucket donde se guardan adjuntos. Sugerido: ubpd-formularios'],
  ['VALKEY_PASSWORD', 'Contraseña de Valkey (Redis)'],
  ['JWT_SECRET_KEY', 'Cadena aleatoria larga para firmar tokens JWT'],
  ['INITIAL_ADMIN_USERNAME', 'Usuario administrador inicial. Sugerido: admin'],
  ['INITIAL_ADMIN_PASSWORD', 'Contraseña inicial del administrador'],
  ['INITIAL_ADMIN_EMAIL', 'Correo del administrador inicial'],
  ['INITIAL_ADMIN_NOMBRE', 'Nombre legible del administrador'],
  ['SERVER_IP', 'IP del servidor (LAN) para mostrar URLs accesibles desde la red'],
  ['CORS_ORIGINS', 'Lista de orígenes permitidos, separados por coma'],
  ['RESET_PIN', 'PIN numérico personal para autorizar comandos destructivos'],
]));

children.push(heading('Generar contraseñas y secretos seguros', HeadingLevel.HEADING_2));
children.push(para('En Linux y macOS:'));
codeBlock(
  'openssl rand -hex 32              # JWT_SECRET_KEY (64 caracteres)\n' +
  'openssl rand -base64 24           # contraseñas robustas'
).forEach((p) => children.push(p));
children.push(para('En Windows PowerShell:'));
codeBlock(
  '[Convert]::ToBase64String((New-Object byte[] 24 | % { Get-Random -Max 255 }))'
).forEach((p) => children.push(p));

children.push(heading('Notas importantes sobre el .env', HeadingLevel.HEADING_2));
children.push(bullet('NUNCA se debe versionar el archivo .env en Git. Ya está incluido en .gitignore.'));
children.push(bullet('Los valores no llevan comillas ni espacios alrededor del signo igual.'));
children.push(bullet('Si se cambia una contraseña después de la instalación inicial, hay que reiniciar el sistema para que tome efecto.'));
children.push(bullet('El RESET_PIN se requiere para los comandos destructivos: reset-fresh y destroy. Sin él, esos comandos se niegan a ejecutar.'));

// 6. Primer arranque
children.push(heading('6. Primer arranque del sistema'));
children.push(numbered('Desde la raíz del proyecto, ejecutar el script de instalación. En Linux/macOS:'));
codeBlock('./scripts/install.sh').forEach((p) => children.push(p));
children.push(numbered('En Windows usar Git Bash o WSL (no funciona en CMD/PowerShell puros porque el script es Bash).'));
children.push(numbered('El instalador construye las imágenes Docker (puede tardar entre 5 y 15 minutos la primera vez) y crea las carpetas necesarias.'));
children.push(numbered('Levantar todos los servicios:'));
codeBlock('./scripts/prod.sh start').forEach((p) => children.push(p));
children.push(numbered('El comando muestra al final las URL de acceso y la ruta de los logs. Anotarlas.'));
children.push(numbered('Esperar 30 a 60 segundos a que todos los contenedores estén "healthy". Verificar:'));
codeBlock('./scripts/prod.sh status').forEach((p) => children.push(p));

// 7. Verificación
children.push(heading('7. Verificación de la instalación'));
children.push(para(
  'Abrir un navegador en el equipo y entrar a:',
));
children.push(bullet('http://127.0.0.1/estadisticas — Portal público (no requiere login).'));
children.push(bullet('http://127.0.0.1 — Pantalla de inicio de sesión.'));
children.push(bullet('http://127.0.0.1/api/docs — Documentación interactiva de la API (Swagger).'));
children.push(bullet('http://127.0.0.1/api/health — Diagnóstico, debe responder { "status": "ok" }.'));
children.push(para(
  'Para acceder desde la red local de la organización, usar la IP definida en SERVER_IP del .env. ' +
  'Asegurarse de que esa IP esté incluida en CORS_ORIGINS, separada por coma.',
));
children.push(para('Iniciar sesión con el usuario administrador inicial configurado en el .env.'));

// 8. Comandos comunes
children.push(heading('8. Comandos de operación'));
children.push(para(
  'Todos los comandos se ejecutan desde la raíz del proyecto con ./scripts/prod.sh <comando>. ' +
  'Lista completa con ./scripts/prod.sh help.',
));
children.push(kvTable([
  ['Comando', 'Descripción'],
  ['start | up', 'Levantar todos los servicios.'],
  ['stop | down', 'Detener todos los servicios.'],
  ['restart [svc]', 'Reiniciar todos o un servicio específico.'],
  ['build [svc]', 'Construir imagen y aplicarla (build + up -d).'],
  ['rebuild [svc]', 'Igual que build pero sin caché de Docker.'],
  ['logs [svc]', 'Ver logs en tiempo real (Ctrl+C para salir).'],
  ['status | ps', 'Estado de los contenedores y URLs.'],
  ['shell [svc]', 'Abrir terminal dentro de un contenedor (default: backend).'],
  ['migrate', 'Aplicar migraciones de base de datos.'],
  ['backup', 'Backup manual de PostgreSQL.'],
  ['pipeline-reset', 'Restaurar el pipeline de indicadores a la versión por defecto y ejecutarlo.'],
  ['pipeline-sync [run]', 'Sincronizar el script local de pipeline con la BD. Añadir "run" para ejecutarlo.'],
  ['reset-db', 'Eliminar y recrear la base de datos (requiere ALLOW_DB_RESET=true en .env).'],
  ['reset-fresh', 'Reset total a estado de instalación (frase + PIN).'],
  ['destroy [all]', 'Eliminar contenedores, imágenes y volúmenes (frase + PIN).'],
]));

// 9. Logs
children.push(heading('9. Ubicación de los logs'));
children.push(para(
  'Todos los logs se escriben dentro de la carpeta ./logs del proyecto. El comando ' +
  '"./scripts/prod.sh start" imprime un resumen completo de las rutas. Las principales son:',
));
children.push(bullet('logs/backend/app.log — Toda la actividad del backend (INFO+).'));
children.push(bullet('logs/backend/errors.log — Solo errores del backend.'));
children.push(bullet('logs/backend/access.log — Peticiones HTTP recibidas.'));
children.push(bullet('logs/backend/celery_worker.log — Tareas en segundo plano.'));
children.push(bullet('logs/backend/pipeline/pipeline.log — Histórico de ejecuciones del pipeline de indicadores.'));
children.push(bullet('logs/backend/pipeline/runs/ — Un archivo por cada ejecución del pipeline.'));
children.push(bullet('logs/backend/uploads/ — Un archivo por cada intento de cargar un Excel.'));
children.push(bullet('logs/nginx/access.log y logs/nginx/error.log — Tráfico y errores del proxy.'));
children.push(para('Para ver logs en vivo:'));
codeBlock(
  '# Backend\n' +
  './scripts/prod.sh logs backend\n\n' +
  '# Pipeline de indicadores\n' +
  'tail -f logs/backend/pipeline/pipeline.log'
).forEach((p) => children.push(p));

// 10. Mantenimiento
children.push(heading('10. Mantenimiento'));
children.push(heading('Backups', HeadingLevel.HEADING_2));
children.push(para(
  'Para crear un respaldo manual de la base de datos:',
));
codeBlock('./scripts/prod.sh backup').forEach((p) => children.push(p));
children.push(para(
  'El backup queda en ./backups/. Se recomienda automatizarlo con cron (Linux/macOS) ' +
  'o Programador de Tareas (Windows) ejecutando el comando diariamente.',
));

children.push(heading('Actualización del código', HeadingLevel.HEADING_2));
codeBlock(
  'git pull\n' +
  './scripts/prod.sh build backend\n' +
  './scripts/prod.sh build frontend'
).forEach((p) => children.push(p));

children.push(heading('Restaurar el pipeline de indicadores', HeadingLevel.HEADING_2));
children.push(para(
  'Si los velocímetros del módulo de estadísticas no muestran los valores esperados, ' +
  'ejecutar:',
));
codeBlock('./scripts/prod.sh pipeline-reset').forEach((p) => children.push(p));
children.push(para(
  'Este comando carga la versión por defecto del pipeline desde la imagen del backend, ' +
  'limpia los KPIs viejos, ejecuta el pipeline y devuelve los valores recalculados.',
));

// 11. Resolución de problemas
children.push(heading('11. Resolución de problemas comunes'));
children.push(heading('Los contenedores no levantan', HeadingLevel.HEADING_2));
children.push(bullet('Verificar que Docker esté corriendo: docker ps debe responder sin error.'));
children.push(bullet('Comprobar que los puertos 80 y opcionalmente 443 estén libres. En Windows: netstat -ano | findstr :80'));
children.push(bullet('Revisar logs de inicio: ./scripts/prod.sh logs'));

children.push(heading('No puedo entrar al sistema', HeadingLevel.HEADING_2));
children.push(bullet('Confirmar que se completó el arranque con ./scripts/prod.sh status — todos en verde.'));
children.push(bullet('Usar el INITIAL_ADMIN_USERNAME e INITIAL_ADMIN_PASSWORD definidos en el .env.'));
children.push(bullet('Si la contraseña se modificó después del primer arranque, hay que entrar con el valor anterior y cambiarla desde la UI.'));

children.push(heading('Acceso desde la red local falla', HeadingLevel.HEADING_2));
children.push(bullet('Verificar que SERVER_IP en .env coincida con la IP real del servidor.'));
children.push(bullet('Añadir esa IP a CORS_ORIGINS, p.ej. CORS_ORIGINS=http://127.0.0.1,http://192.168.1.50'));
children.push(bullet('Reiniciar: ./scripts/prod.sh restart backend'));
children.push(bullet('Confirmar que el firewall del host permite el puerto 80.'));

children.push(heading('Caché del navegador', HeadingLevel.HEADING_2));
children.push(para(
  'Después de actualizar el frontend con ./scripts/prod.sh build frontend, el navegador ' +
  'puede mostrar la versión vieja. Recargar sin caché con:',
));
children.push(bullet('Windows / Linux: Ctrl + Shift + R'));
children.push(bullet('macOS: Cmd + Shift + R'));

children.push(heading('Comando destructivo: empezar de cero', HeadingLevel.HEADING_2));
children.push(para(
  'Si se requiere borrar todo (datos, archivos adjuntos y caché) y dejar el sistema ' +
  'como recién instalado, configurar primero RESET_PIN en el .env y ejecutar:',
));
codeBlock('./scripts/prod.sh reset-fresh').forEach((p) => children.push(p));
children.push(para(
  'El comando solicita escribir la frase "BORRAR TODO" y el PIN antes de proceder. ' +
  'Realiza un backup automático en ./backups/pre-reset/ por seguridad.',
));

// 12. Apéndice
children.push(heading('12. Apéndice — Puertos y servicios internos'));
children.push(kvTable([
  ['Servicio', 'Puerto interno / acceso'],
  ['Nginx (frontal)', 'Puerto 80 del host — único expuesto al exterior.'],
  ['Backend FastAPI', 'Puerto 8000 (solo dentro de la red Docker).'],
  ['Frontend Vue', 'Puerto 3000 (solo dentro de la red Docker).'],
  ['PostgreSQL', 'Puerto 5432 (solo dentro de la red Docker).'],
  ['MinIO', 'Puertos 9000 (API) y 9001 (consola web), accesibles vía Nginx.'],
  ['Valkey (Redis)', 'Puerto 6379 (solo dentro de la red Docker).'],
]));

children.push(heading('Fin del documento', HeadingLevel.HEADING_2));
children.push(para(
  'Si después de seguir todos los pasos el sistema no funciona, revisar los logs ' +
  'detallados (sección 9) y compartirlos con el equipo técnico para diagnóstico.',
));

// ─── Construir el documento ───────────────────────────────────────────────

const doc = new Document({
  creator: 'Equipo Técnico',
  title: 'Sistema de Indicadores — Guía de Instalación',
  description: 'Procedimiento de instalación, configuración y verificación.',
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal',
        quickFormat: true,
        run: { size: 32, bold: true, color: COLOR_TITLE, font: FONT },
        paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal',
        quickFormat: true,
        run: { size: 26, bold: true, color: COLOR_ACCENT, font: FONT },
        paragraph: { spacing: { before: 180, after: 100 }, outlineLevel: 1 } },
    ],
  },
  numbering: {
    config: [
      { reference: 'bullets',
        levels: [
          { level: 0, format: LevelFormat.BULLET, text: '•',
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
          { level: 1, format: LevelFormat.BULLET, text: '◦',
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 1440, hanging: 360 } } } },
        ] },
      { reference: 'numbers',
        levels: [
          { level: 0, format: LevelFormat.DECIMAL, text: '%1.',
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
        ] },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },                // US Letter
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({
            text: 'Sistema de Indicadores — Guía de Instalación',
            font: FONT, italics: true, size: 18, color: '888888',
          })],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: 'Página ', font: FONT, size: 18, color: '888888' }),
            new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: '888888' }),
            new TextRun({ text: ' de ', font: FONT, size: 18, color: '888888' }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES], font: FONT, size: 18, color: '888888' }),
          ],
        })],
      }),
    },
    children,
  }],
});

// ─── Guardar ──────────────────────────────────────────────────────────────
const outDir = path.join(__dirname, '..', 'docs');
fs.mkdirSync(outDir, { recursive: true });
const outPath = path.join(outDir, 'INSTALACION.docx');
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(outPath, buf);
  console.log(`✓ Documento generado: ${outPath} (${(buf.length / 1024).toFixed(1)} KB)`);
});
