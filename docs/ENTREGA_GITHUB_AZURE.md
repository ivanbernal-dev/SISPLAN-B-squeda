# Entrega técnica: GitHub a Azure DevOps

## Alcance del repositorio

Este repositorio contiene una sola solución Docker con los siguientes módulos:

- Visor Plan de Acción Institucional 2026: `/estadisticas`.
- Visor de Indicadores Comité Directivo: `/comite-directivo`.
- Visor BI: `/bi`.
- Administración: `/admin`.
- Validación OAP: `/validator`.
- Diligenciamiento de dependencias: `/dependencia`.

Los tres visores son independientes en navegación, pero consumen la misma API
y la misma base de datos institucional. Comité Directivo es de solo lectura y
no modifica la lógica del PAI ni del BI.

## Contenido que no viaja en Git

Por seguridad y portabilidad no se versionan:

- `.env` ni secretos.
- Volúmenes o copias de PostgreSQL, MinIO y Valkey.
- Backups, logs y archivos cargados por usuarios.
- `node_modules`, entornos Python ni compilaciones locales.
- Excel institucionales usados como fuente de carga.

## Importación recomendada en Azure DevOps

Azure DevOps permite importar directamente un repositorio GitHub desde
**Repos > Import repository**. Como alternativa:

```bash
git clone https://github.com/<ORGANIZACION>/<REPOSITORIO>.git
cd <REPOSITORIO>
git remote add azure https://dev.azure.com/<ORGANIZACION>/<PROYECTO>/_git/<REPOSITORIO>
git push azure --all
git push azure --tags
```

La organización informada es **UPD** y el proyecto **SysPlan**; la URL exacta
del repositorio permanece pendiente de confirmación por TI. Después de importar,
los entornos locales deben cambiar su remoto operativo a Azure DevOps.

La estrategia de ramas, permisos, aprobaciones de Cristian e Iván, MFA y
controles de Seguridad Digital se documentan en
[`GOBIERNO_AZURE_DEVOPS.md`](GOBIERNO_AZURE_DEVOPS.md).

## Primer despliegue

1. Copiar `.env.example` a `.env`.
2. Asignar contraseñas y secretos administrados por TI.
3. Ejecutar `./scripts/install.sh`.
4. Ejecutar `./scripts/prod.sh build`.
5. Crear o restaurar los datos institucionales autorizados.
6. Ejecutar `./scripts/prod.sh pipeline-reset` para instalar la fórmula oficial
   del PAI 2026 y recalcular los velocímetros.
7. Validar `/api/health` y las seis rutas indicadas en Alcance.

## Regla del velocímetro PAI 2026

El avance de un producto es la suma de sus porcentajes alcanzados aplicables.
El avance de una línea estratégica es el promedio del avance real de **todos**
sus productos; los productos sin reporte cuentan como cero.

Ejemplo Línea 6: si solamente `L6-P2-DPE-2026` tiene un avance de `23,7%` y la
línea contiene cuatro productos, el velocímetro de la línea muestra
`23,7 / 4 = 5,925%` (aproximadamente `5,9%`). El `87,8%` corresponde al
cumplimiento del producto frente a su proyección (`23,7 / 27`) y no debe usarse
como avance del producto ni de la línea.

## Validaciones antes de promover

```bash
cd frontend
npm ci
npm run type-check
npm run build

cd ../backend
pip install -r requirements.txt -r requirements-test.txt
pytest
```

La promoción a ambientes institucionales debe ejecutarse con secretos de
Azure DevOps y revisión del área de TI de la UBPD.
