"""
sync_pipeline_to_db.py — Sube el contenido de scripts/pai_2026/pipeline_pai.py
a la tabla `pipeline_scripts` como el script ACTIVO del pipeline de KPIs.

Por qué existe:
  El pipeline que se ejecuta cuando alguien pulsa "Ejecutar" en la UI
  vive en la BD (tabla pipeline_scripts). Editar pipeline_pai.py en el
  repo NO basta — hay que cargarlo a la BD. Este script automatiza ese
  paso para evitar que el equipo se quede con una versión antigua que,
  por ejemplo, no tenga Línea 6 o las correcciones de cálculo recientes.

Qué hace:
  1. Lee scripts/pai_2026/pipeline_pai.py del repo.
  2. Conecta a PostgreSQL con las credenciales del .env.
  3. Desactiva el script activo actual (activo = false).
  4. Inserta una nueva fila con el contenido del archivo y activo = true.
  5. Opcionalmente (--run) ejecuta el pipeline en modo producción para
     refrescar los KPIs visibles en /estadisticas.

Uso:
    python3 scripts/pai_2026/sync_pipeline_to_db.py          # solo guarda
    python3 scripts/pai_2026/sync_pipeline_to_db.py --run    # guarda + ejecuta
    ./scripts/prod.sh pipeline-sync                          # vía CLI
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIPELINE_FILE = ROOT / "scripts" / "pai_2026" / "pipeline_pai.py"
ENV_FILE = ROOT / ".env"


def read_env(key: str, default: str = "") -> str:
    if not ENV_FILE.exists():
        return default
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        m = re.match(rf"^{re.escape(key)}=(.*)$", line)
        if m:
            v = m.group(1).strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            return v
    return default


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true",
                        help="Tras guardar, ejecutar el pipeline en modo producción.")
    parser.add_argument("--name", default="Pipeline PAI 2026 (sync)",
                        help="Nombre que se le da al script al guardarlo.")
    args = parser.parse_args()

    if not PIPELINE_FILE.exists():
        print(f"✗ No existe {PIPELINE_FILE}", file=sys.stderr)
        return 1

    codigo = PIPELINE_FILE.read_text(encoding="utf-8")
    print(f"📄 Leído pipeline_pai.py: {len(codigo)} caracteres, "
          f"{len(codigo.splitlines())} líneas")

    # Pre-validar que compile como Python
    try:
        compile(codigo, "<pipeline_pai>", "exec")
        print("✅ El archivo compila como Python válido")
    except SyntaxError as e:
        print(f"✗ SyntaxError en {PIPELINE_FILE}:{e.lineno} → {e.msg}", file=sys.stderr)
        return 1

    # ── Conexión a Postgres ─────────────────────────────────────────────────
    try:
        import psycopg2
    except ImportError:
        print("✗ Falta psycopg2. Instálalo:  pip install psycopg2-binary",
              file=sys.stderr)
        return 1

    pg_user = read_env("POSTGRES_USER", "ubpd_user")
    pg_pass = read_env("POSTGRES_PASSWORD", "")
    pg_db   = read_env("POSTGRES_DB", "ubpd")
    pg_host = os.environ.get("POSTGRES_HOST", "127.0.0.1")
    pg_port = os.environ.get("POSTGRES_PORT", "5432")

    print(f"🔌 Conectando a postgres://{pg_user}@{pg_host}:{pg_port}/{pg_db}...")
    try:
        conn = psycopg2.connect(
            host=pg_host, port=pg_port,
            user=pg_user, password=pg_pass, dbname=pg_db,
        )
    except Exception as e:
        print(f"✗ No se pudo conectar a Postgres: {e}", file=sys.stderr)
        print("  Sugerencia: ¿está corriendo el contenedor postgres?", file=sys.stderr)
        print("  ./scripts/prod.sh ps", file=sys.stderr)
        return 1

    try:
        with conn:
            with conn.cursor() as cur:
                # 1. Inspección previa
                cur.execute("SELECT id, nombre, length(codigo), activo FROM pipeline_scripts ORDER BY updated_at DESC")
                rows = cur.fetchall()
                print(f"\n📋 Scripts actuales en BD: {len(rows)}")
                for (sid, nom, ln, act) in rows:
                    flag = "● ACTIVO" if act else "  inactivo"
                    print(f"   {flag}  {nom!r:42s}  {ln} chars  id={sid}")

                # 2. Desactivar todos los activos
                cur.execute("UPDATE pipeline_scripts SET activo = false WHERE activo = true")
                print(f"\n🔕 Desactivados {cur.rowcount} script(s) activo(s) previo(s)")

                # 3. Insertar el nuevo activo
                new_id = str(uuid.uuid4())
                now = datetime.now(timezone.utc)
                cur.execute(
                    """INSERT INTO pipeline_scripts (id, nombre, codigo, activo, created_at, updated_at)
                       VALUES (%s, %s, %s, true, %s, %s)""",
                    (new_id, args.name, codigo, now, now),
                )
                print(f"💾 Insertado nuevo script ACTIVO: id={new_id}, nombre={args.name!r}")

        # 4. Confirmar
        with conn.cursor() as cur:
            cur.execute("SELECT id, nombre, length(codigo), updated_at FROM pipeline_scripts WHERE activo = true")
            r = cur.fetchone()
            if r:
                print(f"\n✅ Script ACTIVO ahora: {r[1]!r} ({r[2]} chars, actualizado {r[3]})")
            else:
                print("\n✗ Algo salió mal: no quedó ningún script activo", file=sys.stderr)
                return 1

    finally:
        conn.close()

    # 5. Ejecutar pipeline (opcional)
    if args.run:
        print("\n▶  Ejecutando pipeline en modo PRODUCCIÓN...")
        # Hacemos login y POST /admin/script-pipeline/run vía requests
        try:
            import requests
        except ImportError:
            print("  ⚠️  requests no instalado — ejecuta manualmente desde la UI:")
            print("      Admin → Script Pipeline → Ejecutar")
            return 0
        admin_user = read_env("INITIAL_ADMIN_USERNAME", "admin")
        admin_pass = read_env("INITIAL_ADMIN_PASSWORD", "")
        base = os.environ.get("UBPD_BASE_URL", "http://localhost")
        try:
            tok_r = requests.post(
                f"{base}/api/auth/login",
                json={"username": admin_user, "password": admin_pass},
                timeout=10,
            )
            tok_r.raise_for_status()
            token = tok_r.json()["access_token"]
            run_r = requests.post(
                f"{base}/api/admin/script-pipeline/run",
                headers={"Authorization": f"Bearer {token}"},
                json={"codigo": codigo, "modo": "produccion"},
                timeout=120,
            )
            data = run_r.json()
            if data.get("ok"):
                print(f"  ✅ Ejecutado correctamente. {(data.get('stdout') or '').strip().splitlines()[-1] if data.get('stdout') else ''}")
            else:
                print(f"  ✗ Falló: {data.get('stderr','(sin detalle)')[:500]}")
        except Exception as e:
            print(f"  ⚠️  No se pudo ejecutar vía API ({e}). Hazlo desde la UI:")
            print("      Admin → Script Pipeline → Ejecutar")

    print("\n💡 Próximos pasos:")
    print("   1. Abre Admin → Script Pipeline y verifica que el script cargado")
    print("      es 'Pipeline PAI 2026 (sync)' con todas las líneas L1..L6.")
    print("   2. Pulsa 'Ejecutar' (modo producción) si no usaste --run.")
    print("   3. Ve a /estadisticas — deberías ver las 6 líneas (incl. L6).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
