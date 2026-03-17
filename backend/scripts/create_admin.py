#!/usr/bin/env python3
"""
scripts/create_admin.py — Script CLI para crear el usuario administrador inicial.

Uso:
    cd /path/to/backend
    python scripts/create_admin.py
    python scripts/create_admin.py --username miadmin --password MiClave@2024 --email admin@ubpd.gov.co
"""
import argparse
import asyncio
import sys
import os

# Asegurar que el paquete app sea encontrable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def create_admin(
    username: str,
    password: str,
    nombre_completo: str,
    email: str,
) -> None:
    from sqlalchemy import select
    from app.database import AsyncSessionLocal, init_db
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password

    print(f"Inicializando base de datos...")
    await init_db()

    async with AsyncSessionLocal() as db:
        # Verificar si ya existe
        result = await db.execute(select(User).where(User.username == username))
        existing = result.scalar_one_or_none()
        if existing:
            print(f"[!] El usuario '{username}' ya existe (role: {existing.role.value}).")
            if existing.role != UserRole.admin:
                existing.role = UserRole.admin
                existing.activo = True
                await db.commit()
                print(f"[+] Role actualizado a 'admin'.")
            return

        admin = User(
            username=username,
            nombre_completo=nombre_completo,
            email=email,
            role=UserRole.admin,
            password_hash=hash_password(password),
            requires_password_change=False,
            activo=True,
        )
        db.add(admin)
        await db.commit()
        print(f"[+] Administrador creado exitosamente:")
        print(f"    Username: {username}")
        print(f"    Email:    {email}")
        print(f"    Role:     admin")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Crea el usuario administrador inicial de UBPD."
    )
    parser.add_argument(
        "--username", default="admin", help="Nombre de usuario (default: admin)"
    )
    parser.add_argument(
        "--password",
        default="Admin@UBPD2024",
        help="Contraseña (default: Admin@UBPD2024)",
    )
    parser.add_argument(
        "--nombre",
        default="Administrador UBPD",
        help="Nombre completo (default: 'Administrador UBPD')",
    )
    parser.add_argument(
        "--email",
        default="admin@ubpd.gov.co",
        help="Email (default: admin@ubpd.gov.co)",
    )
    args = parser.parse_args()

    asyncio.run(
        create_admin(
            username=args.username,
            password=args.password,
            nombre_completo=args.nombre,
            email=args.email,
        )
    )


if __name__ == "__main__":
    main()
