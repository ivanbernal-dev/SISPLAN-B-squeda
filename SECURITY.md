# Seguridad

No reportes vulnerabilidades, credenciales o datos institucionales mediante un
issue público. Comunícalos por el canal privado definido por el equipo de
Seguridad Digital de la UBPD.

Toda aplicación pública o cambio con requisitos de control adicionales debe pasar
análisis de Seguridad Digital antes de su despliegue. El repositorio no debe
contener `.env`, contraseñas, tokens, certificados, backups ni información cargada
por usuarios.

Las credenciales de CI/CD se administran mediante service connections, grupos de
variables secretos o Azure Key Vault. Los accesos humanos usan directorio activo
institucional y autenticación multifactor.
