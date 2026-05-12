"""
Inserta indicadores Nivel 2 (productos) y templates en la base de datos
desde el JSON ya generado, usando la sesión SQLAlchemy directa del backend.

Uso desde el host:
    docker cp scripts/pai_2026/data/pai_templates.json ubpd_backend:/tmp/
    docker cp scripts/pai_2026/load_pai.py             ubpd_backend:/tmp/
    docker exec ubpd_backend python3 /tmp/load_pai.py
"""
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, "/app")

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.indicator import Indicator
from app.models.indicador_nivel2 import IndicadorNivel2
from app.models.template import Template


async def main():
    # Busca el JSON tanto en el path por defecto del contenedor como junto al script
    candidates = [
        Path("/tmp/pai_templates.json"),
        Path(__file__).parent / "data" / "pai_templates.json",
    ]
    json_path = next((p for p in candidates if p.exists()), candidates[0])
    payload = json.loads(json_path.read_text())
    print(f"Templates a procesar: {len(payload)}")

    async with AsyncSessionLocal() as db:
        # Mapa Nivel 1 (id=1..6 ya creados)
        n1_rows = (await db.execute(
            select(Indicator).order_by(Indicator.id)
        )).scalars().all()
        n1_by_num = {int(i.id): i for i in n1_rows}
        print("Nivel 1:", {k: v.nombre[:40] for k, v in n1_by_num.items()})

        # Crear Nivel 2 (un producto por template)
        n2_by_codigo: dict[str, IndicadorNivel2] = {}
        for t in payload:
            linea = t["linea_num"]
            n1 = n1_by_num.get(linea)
            if not n1:
                print(f"⚠️  No hay Nivel 1 para línea {linea} — salto template {t['codigo']}")
                continue

            n2 = IndicadorNivel2(
                nombre=t["codigo"],   # ej "L1-P1-DPE-2026"
                descripcion=t["producto_full"][:500],
                indicador_nivel1_id=n1.id,
                activo=True,
            )
            db.add(n2)
            await db.flush()
            n2_by_codigo[t["codigo"]] = n2
            print(f"  + N2 id={n2.id:>3}  L{linea}/{t['codigo']}")

        # Crear Templates
        for t in payload:
            n2 = n2_by_codigo.get(t["codigo"])
            tpl = Template(
                nombre=t["nombre"][:255],
                descripcion=t["descripcion"][:500] if t["descripcion"] else None,
                codigo=t["codigo"][:100],
                indicador_nivel1_id=n2.indicador_nivel1_id if n2 else None,
                indicador_nivel2_id=n2.id if n2 else None,
                codigo_markdown=t["codigo_markdown"],
                configuracion_campos=t["configuracion_campos"],
                version=1,
                activo=True,
            )
            db.add(tpl)
            await db.flush()
            print(f"  + TPL {tpl.codigo:25s} id={tpl.id}")

        await db.commit()
        print("\n✓ Commit OK")


asyncio.run(main())
