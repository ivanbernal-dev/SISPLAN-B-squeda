#!/usr/bin/env python3
"""
scripts/e2e_test.py — Test E2E del sistema UBPD

Modos de uso:
  python scripts/e2e_test.py seed          # Crea datos de prueba + instala script
  python scripts/e2e_test.py run           # Ejecuta el pipeline en producción
  python scripts/e2e_test.py verify        # Verifica que los KPIs tengan valores > 0
  python scripts/e2e_test.py status        # Muestra el estado actual de los datos de prueba
  python scripts/e2e_test.py clean         # Elimina todos los datos de prueba
  python scripts/e2e_test.py auto          # Ejecuta todo el flujo y limpia al final
  python scripts/e2e_test.py full          # Como auto pero NO limpia (para inspección manual)

Variables de entorno:
  UBPD_BASE_URL   URL base del API (default: http://localhost:8000/api)
  UBPD_ADMIN_USER Usuario administrador (default: admin)
  UBPD_ADMIN_PASS Contraseña del administrador (default: Admin@UBPD2024!)
"""

import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

# ── Dependencia: requests ──────────────────────────────────────────────────────
try:
    import requests
except ImportError:
    print("ERROR: Instala la dependencia: pip install requests")
    sys.exit(1)

# ── Configuración ──────────────────────────────────────────────────────────────
BASE_URL = os.getenv("UBPD_BASE_URL", "http://localhost:8000/api")
ADMIN_USER = os.getenv("UBPD_ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("UBPD_ADMIN_PASS", "Admin@UBPD2024!")

# ── Colores ANSI ───────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg: str)   -> None: print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg: str) -> None: print(f"  {RED}✗{RESET} {msg}")
def info(msg: str) -> None: print(f"  {CYAN}→{RESET} {msg}")
def warn(msg: str) -> None: print(f"  {YELLOW}⚠{RESET} {msg}")
def header(msg: str) -> None: print(f"\n{BOLD}{CYAN}{'─'*60}{RESET}\n{BOLD}{msg}{RESET}")


class E2EClient:
    """Cliente HTTP para el test E2E."""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.token: Optional[str] = None

    # ── Autenticación ──────────────────────────────────────────────────────────

    def login(self, username: str = ADMIN_USER, password: str = ADMIN_PASS) -> bool:
        """Autentica y almacena el JWT."""
        try:
            r = self.session.post(
                f"{BASE_URL}/auth/login",
                json={"username": username, "password": password},
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                return True
            return False
        except requests.ConnectionError:
            return False

    # ── Helpers ────────────────────────────────────────────────────────────────

    def get(self, path: str, **kwargs) -> requests.Response:
        return self.session.get(f"{BASE_URL}{path}", timeout=30, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        return self.session.post(f"{BASE_URL}{path}", timeout=60, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self.session.delete(f"{BASE_URL}{path}", timeout=30, **kwargs)

    def json_or_raise(self, r: requests.Response) -> Any:
        try:
            return r.json()
        except Exception:
            r.raise_for_status()
            raise


# ── Pasos del flujo E2E ────────────────────────────────────────────────────────

def step_health(client: E2EClient) -> bool:
    """1. Verificar que el backend responde."""
    header("PASO 1 — Health check")
    try:
        r = client.get("/health")
        if r.status_code == 200:
            data = r.json()
            ok(f"Backend activo — versión {data.get('version', '?')} [{data.get('env', '?')}]")
            return True
        fail(f"Health check falló: HTTP {r.status_code}")
        return False
    except requests.ConnectionError:
        fail(f"No se puede conectar a {BASE_URL}")
        info("¿Está el sistema corriendo? Ejecuta: ./scripts/prod.sh start")
        return False


def step_login(client: E2EClient) -> bool:
    """2. Login como administrador."""
    header("PASO 2 — Autenticación admin")
    ok_result = client.login()
    if ok_result:
        ok(f"Login exitoso como '{ADMIN_USER}'")
        return True
    fail(f"Login fallido para '{ADMIN_USER}' — verifica UBPD_ADMIN_USER y UBPD_ADMIN_PASS")
    return False


def step_seed(client: E2EClient) -> Optional[Dict[str, Any]]:
    """3. Crear datos de prueba."""
    header("PASO 3 — Seed de datos de prueba")

    # Verificar estado previo
    r = client.get("/admin/test-data/status")
    if r.status_code == 200:
        status_data = r.json()
        if status_data.get("tiene_datos"):
            warn("Ya existen datos de prueba:")
            info(f"  Templates: {status_data.get('templates', [])}")
            info(f"  Formularios: {status_data.get('formularios', 0)}")
            warn("Usa 'clean' primero para partir de cero, o continúa con estos datos.")
            return status_data

    r = client.post("/admin/test-data/seed")
    if r.status_code == 200:
        data = r.json()
        ok(f"Dependencia creada: {data.get('dependencia_id', '')[:8]}...")
        ok(f"Templates creados: {len(data.get('template_ids', []))}")
        ok(f"Formularios creados: {data.get('formularios_creados', 0)} "
           f"({data.get('formularios_aprobados', 0)} aprobados, "
           f"{data.get('formularios_rechazados', 0)} rechazados)")
        ok(f"Usuario dependencia: {data.get('dep_user')} / {data.get('dep_password')}")
        ok(f"Validador: {data.get('validator')} / {data.get('validator_password')}")
        return data
    elif r.status_code == 409:
        warn("Datos de prueba ya existen (409). Continúa con el flujo.")
        return {"ya_existian": True}
    else:
        fail(f"Seed falló: HTTP {r.status_code} — {r.text[:200]}")
        return None


def step_install_script(client: E2EClient) -> bool:
    """4. Instalar el script de pipeline de prueba."""
    header("PASO 4 — Instalar script de pipeline")
    r = client.post("/admin/test-data/install-script")
    if r.status_code == 200:
        ok("Script de prueba instalado en el editor de pipeline")
        return True
    fail(f"Instalación del script falló: HTTP {r.status_code} — {r.text[:200]}")
    return False


def step_login_dep_user(client: E2EClient) -> bool:
    """5. Verificar login de usuario de dependencia."""
    header("PASO 5 — Login usuario de dependencia")
    temp_client = E2EClient()
    result = temp_client.login("test_e2e_dep_user", "Test@E2E2024!")
    if result:
        ok("Login de usuario de dependencia: OK")

        # Verificar que puede ver sus templates
        r = temp_client.get("/templates")
        if r.status_code == 200:
            templates = r.json()
            test_templates = [t for t in templates if "[TEST_E2E]" in t.get("nombre", "")]
            ok(f"Templates visibles para la dependencia: {len(test_templates)} de prueba")
        return True
    fail("Login de usuario de dependencia falló")
    return False


def step_login_validator(client: E2EClient) -> bool:
    """6. Verificar login de validador."""
    header("PASO 6 — Login validador")
    temp_client = E2EClient()
    result = temp_client.login("test_e2e_validator", "Test@E2E2024!")
    if result:
        ok("Login de validador: OK")

        # Verificar inbox del validador
        r = temp_client.get("/validation/inbox")
        if r.status_code == 200:
            items = r.json()
            count = len(items) if isinstance(items, list) else items.get("total", "?")
            ok(f"Inbox del validador accesible ({count} ítems)")
        return True
    fail("Login de validador falló")
    return False


def step_check_forms(client: E2EClient) -> bool:
    """7. Verificar formularios aprobados en la BD."""
    header("PASO 7 — Verificar formularios aprobados")
    r = client.get("/admin/test-data/status")
    if r.status_code != 200:
        fail(f"No se pudo obtener status: HTTP {r.status_code}")
        return False

    data = r.json()
    total = data.get("formularios", 0)
    if total >= 21:  # 3 templates × 7 aprobados = 21
        ok(f"Formularios en BD: {total} (≥21 esperados)")
        return True
    warn(f"Formularios encontrados: {total} (se esperaban ≥21)")
    return total > 0


def step_get_script(client: E2EClient) -> Optional[str]:
    """8. Obtener el script activo del editor."""
    header("PASO 8 — Cargar script del editor")
    r = client.get("/admin/script-pipeline")
    if r.status_code == 200:
        data = r.json()
        codigo = data.get("codigo", "")
        if codigo:
            ok(f"Script cargado ({len(codigo)} caracteres)")
            if "TEST_E2E" in codigo:
                ok("Script contiene referencias TEST_E2E — es el script de prueba")
            return codigo
        warn("Script vacío")
        return None
    fail(f"No se pudo cargar el script: HTTP {r.status_code}")
    return None


def step_run_pipeline(client: E2EClient, codigo: str) -> bool:
    """9. Ejecutar el pipeline en modo producción."""
    header("PASO 9 — Ejecutar pipeline (modo producción)")

    # Primero ejecutar en modo test para verificar
    info("Ejecutando en modo TEST para verificar...")
    r = client.post("/admin/script-pipeline/run", json={"codigo": codigo, "modo": "test"})
    if r.status_code == 200:
        data = r.json()
        if data.get("error"):
            fail(f"Error en modo test: {data['error']}")
            if data.get("stdout"):
                info("Salida del script:")
                for line in data["stdout"].splitlines()[:20]:
                    print(f"    {line}")
            return False
        ok("Modo TEST exitoso")
        if data.get("stdout"):
            info("Salida:")
            for line in data["stdout"].splitlines()[:10]:
                print(f"    {line}")

    # Ahora ejecutar en producción
    info("Ejecutando en modo PRODUCCIÓN...")
    r = client.post("/admin/script-pipeline/run", json={"codigo": codigo, "modo": "produccion"})
    if r.status_code == 200:
        data = r.json()
        if data.get("error"):
            fail(f"Error en producción: {data['error']}")
            return False
        saved = data.get("kpis_guardados", 0)
        ok(f"Pipeline ejecutado — {saved} KPIs guardados en BD")
        return True
    fail(f"Pipeline falló: HTTP {r.status_code} — {r.text[:200]}")
    return False


def step_verify_kpis(client: E2EClient) -> bool:
    """10. Verificar KPIs públicos resultantes."""
    header("PASO 10 — Verificar KPIs públicos")

    # Nivel 1
    r = client.get("/stats/kpis")
    if r.status_code != 200:
        fail(f"No se pudo obtener KPIs nivel 1: HTTP {r.status_code}")
        return False

    kpis_n1 = r.json()
    if not kpis_n1:
        fail("No hay KPIs nivel 1 disponibles")
        return False

    ok(f"KPIs nivel 1: {len(kpis_n1)} encontrados")
    non_zero = [k for k in kpis_n1 if k.get("valor", 0) > 0]
    if non_zero:
        ok(f"KPIs con valor > 0: {len(non_zero)}")
        for kpi in non_zero:
            info(f"  {kpi['label']}: {kpi['valor']}%")
    else:
        warn("Todos los KPIs nivel 1 tienen valor 0.0")

    # Nivel 2 para el primer KPI con valor
    if non_zero:
        parent_key = non_zero[0]["key"]
        r2 = client.get(f"/stats/kpis/{parent_key}")
        if r2.status_code == 200:
            sub_kpis = r2.json()
            ok(f"Sub-KPIs para '{parent_key}': {len(sub_kpis)} encontrados")
            sub_non_zero = [k for k in sub_kpis if k.get("valor", 0) > 0]
            if sub_non_zero:
                ok(f"Sub-KPIs con valor > 0: {len(sub_non_zero)}")
                for kpi in sub_non_zero:
                    info(f"  {kpi['label']}: {kpi['valor']}%")

                # Nivel 3: formularios del primer sub-KPI
                sub_key = sub_non_zero[0]["key"]
                r3 = client.get(f"/stats/kpis/{sub_key}/forms")
                if r3.status_code == 200:
                    forms_data = r3.json()
                    total_forms = forms_data.get("total", 0)
                    ok(f"Formularios públicos para sub-KPI '{sub_key}': {total_forms}")
                    return total_forms > 0
                else:
                    warn(f"No se pudo obtener formularios del sub-KPI: HTTP {r3.status_code}")
            else:
                warn("Sub-KPIs con valor 0 — el pipeline puede no haber asociado template_id")

    return len(non_zero) > 0


def step_clean(client: E2EClient) -> bool:
    """11. Limpiar datos de prueba."""
    header("PASO 11 — Limpieza de datos de prueba")
    r = client.delete("/admin/test-data/clean")
    if r.status_code == 200:
        data = r.json()
        ok(f"Formularios eliminados: {data.get('formularios_eliminados', 0)}")
        ok(f"Usuarios eliminados:    {data.get('usuarios_eliminados', 0)}")
        ok(f"Templates eliminados:   {data.get('templates_eliminados', 0)}")
        ok(f"Dependencias eliminadas:{data.get('dependencias_eliminadas', 0)}")
        return True
    fail(f"Limpieza falló: HTTP {r.status_code} — {r.text[:200]}")
    return False


# ── Modos de ejecución ─────────────────────────────────────────────────────────

def run_status(client: E2EClient) -> None:
    """Muestra el estado actual de datos de prueba."""
    header("Estado de datos de prueba E2E")
    r = client.get("/admin/test-data/status")
    if r.status_code != 200:
        fail(f"HTTP {r.status_code} — {r.text[:200]}")
        return

    data = r.json()
    if data.get("tiene_datos"):
        ok("Datos de prueba PRESENTES")
        info(f"Dependencia:  {data.get('dependencia', '—')}")
        info(f"Usuarios:     {data.get('usuarios', [])}")
        info(f"Templates:    {len(data.get('templates', []))}")
        info(f"Formularios:  {data.get('formularios', 0)}")
        print()
        for t in data.get("templates", []):
            print(f"    • {t}")
    else:
        info("No hay datos de prueba en el sistema.")

    # También mostrar KPIs actuales
    r2 = client.get("/stats/kpis")
    if r2.status_code == 200:
        kpis = r2.json()
        if kpis:
            print()
            info(f"KPIs actuales en BD ({len(kpis)}):")
            for k in kpis:
                bar = "█" * int(k.get("valor", 0) / 10)
                print(f"    {k['label'][:30]:<30} {k.get('valor', 0):5.1f}%  {bar}")


def run_seed(client: E2EClient) -> None:
    if not step_health(client): sys.exit(1)
    if not step_login(client): sys.exit(1)
    seed_data = step_seed(client)
    if seed_data is None: sys.exit(1)
    step_install_script(client)


def run_run(client: E2EClient) -> None:
    if not step_health(client): sys.exit(1)
    if not step_login(client): sys.exit(1)
    codigo = step_get_script(client)
    if not codigo: sys.exit(1)
    if not step_run_pipeline(client, codigo): sys.exit(1)


def run_verify(client: E2EClient) -> None:
    if not step_health(client): sys.exit(1)
    if not step_login(client): sys.exit(1)
    passed = step_verify_kpis(client)
    if not passed:
        print(f"\n{RED}{BOLD}VERIFICACIÓN FALLIDA{RESET}")
        sys.exit(1)
    print(f"\n{GREEN}{BOLD}VERIFICACIÓN EXITOSA{RESET}")


def run_clean(client: E2EClient) -> None:
    if not step_health(client): sys.exit(1)
    if not step_login(client): sys.exit(1)
    if not step_clean(client): sys.exit(1)


def run_auto(client: E2EClient, keep_data: bool = False) -> None:
    """Flujo completo: seed → run → verify → clean."""
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}   UBPD — Test E2E Automatizado{RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}")

    results: Dict[str, bool] = {}
    start_time = time.time()

    def record(name: str, passed: bool) -> bool:
        results[name] = passed
        return passed

    # Flujo completo
    if not record("health",    step_health(client)):   sys.exit(1)
    if not record("login",     step_login(client)):    sys.exit(1)

    seed_data = step_seed(client)
    record("seed", seed_data is not None)
    if seed_data is None: sys.exit(1)

    record("install_script", step_install_script(client))
    record("login_dep_user", step_login_dep_user(client))
    record("login_validator", step_login_validator(client))
    record("check_forms",    step_check_forms(client))

    codigo = step_get_script(client)
    record("get_script", codigo is not None)
    if not codigo:
        sys.exit(1)

    record("run_pipeline", step_run_pipeline(client, codigo))
    record("verify_kpis",  step_verify_kpis(client))

    if not keep_data:
        record("clean", step_clean(client))
    else:
        warn("Datos de prueba conservados para inspección manual.")
        info("Usa 'python scripts/e2e_test.py clean' para eliminarlos.")

    # ── Resumen ───────────────────────────────────────────────────────────────
    elapsed = time.time() - start_time
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}   RESUMEN DEL TEST E2E{RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}")

    all_passed = True
    for step_name, passed in results.items():
        status_str = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
        label = step_name.replace("_", " ").title()
        print(f"  {status_str}  {label}")
        if not passed:
            all_passed = False

    print(f"\n  Tiempo total: {elapsed:.1f}s")
    print()

    if all_passed:
        print(f"{GREEN}{BOLD}  ✓ TODOS LOS TESTS PASARON{RESET}")
        sys.exit(0)
    else:
        failed = [k for k, v in results.items() if not v]
        print(f"{RED}{BOLD}  ✗ TESTS FALLIDOS: {', '.join(failed)}{RESET}")
        sys.exit(1)


# ── Entrada principal ──────────────────────────────────────────────────────────

MODES = {
    "seed":    "Crea datos de prueba e instala el script de pipeline",
    "run":     "Ejecuta el pipeline (test + producción)",
    "verify":  "Verifica KPIs públicos resultantes",
    "status":  "Muestra el estado actual de datos de prueba",
    "clean":   "Elimina todos los datos de prueba",
    "auto":    "Flujo completo + limpieza automática al final",
    "full":    "Flujo completo SIN limpiar (para inspección manual)",
}


def print_help() -> None:
    print(f"\n{BOLD}UBPD — Test E2E{RESET}\n")
    print("Uso: python scripts/e2e_test.py <modo>\n")
    print("Modos disponibles:")
    for mode, desc in MODES.items():
        print(f"  {CYAN}{mode:<10}{RESET}  {desc}")
    print()
    print("Variables de entorno:")
    print(f"  UBPD_BASE_URL   URL del API  (actual: {BASE_URL})")
    print(f"  UBPD_ADMIN_USER Usuario admin (actual: {ADMIN_USER})")
    print(f"  UBPD_ADMIN_PASS Contraseña    (actual: {'*' * len(ADMIN_PASS)})")
    print()


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print_help()
        sys.exit(0)

    mode = sys.argv[1].lower()
    if mode not in MODES:
        print(f"{RED}Modo desconocido: '{mode}'{RESET}")
        print_help()
        sys.exit(1)

    client = E2EClient()

    # Para 'status' no se necesita login de admin previo
    if mode == "status":
        if not step_health(client):
            sys.exit(1)
        if not step_login(client):
            sys.exit(1)
        run_status(client)
        return

    dispatch = {
        "seed":   lambda: run_seed(client),
        "run":    lambda: run_run(client),
        "verify": lambda: run_verify(client),
        "clean":  lambda: run_clean(client),
        "auto":   lambda: run_auto(client, keep_data=False),
        "full":   lambda: run_auto(client, keep_data=True),
    }

    dispatch[mode]()


if __name__ == "__main__":
    main()
