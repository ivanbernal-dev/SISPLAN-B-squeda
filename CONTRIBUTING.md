# Contribución

El proyecto usa GitFlow y pull requests obligatorios.

1. Actualiza `develop` y crea `feature/<descripcion>`.
2. Mantén commits pequeños y descriptivos.
3. No incluyas `.env`, secretos, datos institucionales ni archivos de IDE/SO.
4. Ejecuta las validaciones antes de publicar:

```bash
cd frontend && npm ci && npm run type-check && npm run lint:check && npm run build
cd ../backend && pip install -r requirements.txt -r requirements-test.txt && pytest
```

5. Abre un pull request hacia `develop` usando la plantilla.
6. Para una entrega, abre PR de `develop` a `release` y luego de `release` a `main`.
7. Los hotfix nacen en `main` y deben reintegrarse también a `develop`.

`main` y `release` no aceptan cambios directos ni bypass de políticas.
