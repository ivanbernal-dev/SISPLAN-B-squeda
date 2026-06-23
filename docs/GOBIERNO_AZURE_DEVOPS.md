# Gobierno del proyecto en Azure DevOps

## Estructura organizacional acordada

- Organización: **UPD** (la URL definitiva debe ser confirmada por TI).
- Proyecto: **SysPlan**.
- Repositorio: **SISPLAN-BUSQUEDA**.
- Repos relacionados: **Cisplan** ya se encuentra administrado en Azure DevOps.
- Identidad: Azure Portal y directorio activo institucional con MFA.

El código puede publicarse primero en GitHub para su entrega, pero después de la
importación cada entorno local debe apuntar al remoto de Azure DevOps. GitHub no
debe continuar como fuente operativa paralela sin autorización de TI.

## Estrategia GitFlow

| Rama | Propósito | Entrada permitida | Despliegue sugerido |
|------|-----------|------------------|---------------------|
| `main` | Producción estable | PR desde `release` o `hotfix/*` | Producción |
| `develop` | Integración continua | PR desde `feature/*` y retorno de hotfix | Desarrollo |
| `release` / `release/*` | Preparación y estabilización | PR desde `develop` | Staging |
| `hotfix/*` | Corrección urgente | Se crea desde `main`; vuelve a `main` y `develop` | Producción controlada |
| `feature/*` | Cambio funcional acotado | Se crea desde `develop` | Sin despliegue directo |

No se realizan commits directos sobre `main` ni `release`. Los cambios deben ser
pequeños, descriptivos y preferiblemente seguir el formato:

```text
feat(comite): agregar filtro por dependencia
fix(pai): promediar avance real de todos los productos
docs(azure): documentar política de ramas
```

## Políticas de rama en Azure DevOps

Configurar como mínimo en `main` y `release`:

1. Requerir pull request; bloquear pushes directos y force-push.
2. Mínimo dos aprobaciones.
3. Cristian como revisor técnico obligatorio.
4. Iván como aprobador funcional obligatorio.
5. Invalidar aprobaciones cuando aparezcan commits nuevos.
6. Resolver todos los comentarios antes de completar.
7. Ejecutar `azure-pipelines.yml` como Build Validation obligatoria.
8. Exigir que la rama origen esté actualizada y sin conflictos.
9. Vincular work item cuando la metodología del proyecto lo requiera.

En `develop` se recomienda PR, una aprobación y la misma validación automática.

## Permisos sugeridos

| Grupo | Permisos |
|-------|----------|
| Administradores del proyecto TI | Configurar proyecto, repos, pipelines, agentes y service connections |
| Desarrolladores | Crear ramas y pull requests; sin bypass de políticas |
| Aprobadores técnicos | Revisar código, arquitectura, Docker y CI/CD |
| Aprobadores funcionales | Validar reglas de negocio y evidencia funcional |
| Seguridad Digital | Revisar aplicaciones públicas, dependencias, secretos y hallazgos |
| Build Service | Leer repositorio, publicar artefactos y usar conexiones expresamente autorizadas |

El acceso humano debe usar directorio activo y MFA. Para automatización deben
preferirse service connections o identidades administradas; no se almacenan PAT,
contraseñas ni credenciales personales en YAML o Git.

## Flujo de pull request

1. Crear `feature/*` desde `develop` o `hotfix/*` desde `main`.
2. Realizar commits pequeños y ejecutar pruebas locales.
3. Abrir PR usando la plantilla de `.azuredevops`.
4. Esperar pruebas unitarias, análisis estático, seguridad y compilación Docker.
5. Obtener revisión técnica y aprobación funcional.
6. Solicitar revisión de Seguridad Digital cuando aplique.
7. Completar el PR sin omitir políticas.
8. Promover `develop` a `release` y luego `release` a `main` mediante PR.

## CI/CD y ambientes

`azure-pipelines.yml` valida backend y frontend, publica el artefacto web y
construye imágenes Docker para `main`, `release/*` y `hotfix/*`. TI debe completar:

- Pool y registro de agentes locales.
- Azure Container Registry u otro registro institucional.
- Service connections con privilegio mínimo.
- Grupos de variables secretos o Azure Key Vault.
- Azure DevOps Environments: desarrollo, staging y producción.
- Aprobaciones previas al despliegue y estrategia de reversión.
- Manifiestos o conexión Kubernetes para las aplicaciones que lo requieran.

## Pruebas y seguridad

La Build Validation incluye pruebas unitarias, TypeScript, lint, auditoría de
dependencias y análisis de código. Test Plans puede incorporarse para trazabilidad
entre pruebas, bugs, commits y requisitos, sujeto a la licencia disponible.

Antes de publicar un visor en internet o promover un cambio con controles
adicionales, debe obtenerse concepto del equipo de Seguridad Digital.

## Pendientes de TI

- Compartir la URL definitiva de organización, proyecto y repositorio.
- Confirmar nombres de pools, environments y service connections.
- Confirmar registro de contenedores y destino de despliegue.
- Aplicar las políticas de rama, ya que no pueden imponerse solo desde Git.
