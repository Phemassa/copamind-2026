"""
Captura automatica de screenshots para o video do CopaMind 2026.
Usa o portal estatico (localhost:8601) — visual premium — para todas as cenas
de interface, mais docs/architecture.html e GitHub para as cenas restantes.

Dependencias:
    pip install playwright requests
    playwright install chromium

Requisitos:
    - Portal rodando em localhost:8601 (ex: python -m http.server 8601 na raiz)
    - Acesso a internet para capturar a pagina do GitHub

Uso:
    & "c:\\copamind-2026\\.venv\\Scripts\\python.exe" scripts\\capture_scenes.py

Saidas em pictures/google_flow/:
    cena_01_gancho.png        Cena 1  — Portal: view "bolao" (Quartas de final)
    cena_02_ranking.png       Cena 2  — Portal: view "ranking" (tabela de modelos)
    cena_04_arquitetura.png   Cenas 4/5 — docs/architecture.html
    cena_06_llms.png          Cena 6  — Portal: view "bolao", scroll ate cards LLM
    cena_08_github.png        Cena 8  — GitHub repo
    portal_home.png           Extra   — Portal: view "home" (hero + KPIs)
    portal_benchmark.png      Extra   — Portal: view "benchmark"

Imagens existentes que nao precisam de recaptura:
    pictures/video/02_probabilidades_titulo.png  (backup Cena 2)
    pictures/video/04_bolao_ias.png              (backup Cena 6)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
OUTPUT_DIR = WORKSPACE / "pictures" / "google_flow"
PORTAL_URL = "http://localhost:8601/apps/portal/"
GITHUB_URL = "https://github.com/Phemassa/copamind-2026"
ARCHITECTURE_HTML = WORKSPACE / "docs" / "architecture.html"

# Viewport padrao para o video (16:9 - 1440x900)
VP = {"width": 1440, "height": 900}

SCENES: list[dict] = [
    {
        "name": "cena_01_gancho",
        "description": "Cena 1 — Portal: Bolao das LLMs (match cards)",
        "type": "portal",
        "view": "bolao",
        "scroll_to": None,
        "clip": None,
        "viewport": VP,
        "wait_ms": 2500,
        "full_page": False,
    },
    {
        "name": "cena_02_ranking",
        "description": "Cena 2 — Portal: Ranking das LLMs",
        "type": "portal",
        "view": "ranking",
        "scroll_to": None,
        "clip": None,
        "viewport": VP,
        "wait_ms": 2000,
        "full_page": False,
    },
    {
        "name": "cena_04_arquitetura",
        "description": "Cenas 4 e 5 — Arquitetura (docs/architecture.html)",
        "type": "local_html",
        "path": ARCHITECTURE_HTML,
        "viewport": VP,
        "wait_ms": 1500,
        "full_page": True,
    },
    {
        "name": "cena_06_llms",
        "description": "Cena 6 — Portal: Bolao das LLMs (scroll ate cards dos modelos)",
        "type": "portal",
        "view": "bolao",
        "scroll_to": ".llm-card-grid, .model-grid, #llm-card-grid",
        "clip": None,
        "viewport": VP,
        "wait_ms": 2500,
        "full_page": False,
    },
    {
        "name": "cena_08_github",
        "description": "Cena 8 — Repositorio GitHub",
        "type": "url",
        "url": GITHUB_URL,
        "viewport": VP,
        "wait_ms": 3000,
        "full_page": False,
    },
    {
        "name": "portal_home",
        "description": "Extra — Portal: Home (hero + KPIs)",
        "type": "portal",
        "view": "home",
        "scroll_to": None,
        "clip": None,
        "viewport": VP,
        "wait_ms": 2000,
        "full_page": False,
    },
    {
        "name": "portal_benchmark",
        "description": "Extra — Portal: Benchmark LLMs",
        "type": "portal",
        "view": "benchmark",
        "scroll_to": None,
        "clip": None,
        "viewport": VP,
        "wait_ms": 2000,
        "full_page": False,
    },
]


def _check_portal() -> bool:
    try:
        import requests  # noqa: PLC0415
        r = requests.get(PORTAL_URL, timeout=5)
        return r.status_code < 500
    except Exception:
        return False


def _navigate_portal_view(page, view: str) -> None:
    """Click the portal nav button for the given data-view value."""
    try:
        btn = page.locator(f'.main-nav button[data-view="{view}"]')
        btn.wait_for(state="visible", timeout=8000)
        btn.click()
        time.sleep(1.5)
    except Exception:
        pass


def _scroll_to_selector(page, selector: str) -> None:
    """Scroll to first matching element if it exists."""
    try:
        for sel in selector.split(","):
            sel = sel.strip()
            el = page.locator(sel).first
            if el.count():
                el.scroll_into_view_if_needed()
                time.sleep(0.8)
                return
    except Exception:
        pass


def capture_all() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    needs_portal = any(s.get("type") == "portal" for s in SCENES)
    if needs_portal and not _check_portal():
        print(
            "\n[AVISO] Portal nao detectado em http://localhost:8601/apps/portal/\n"
            "Inicie o servidor de arquivos estaticos antes de capturar:\n"
            "  python -m http.server 8601  (na raiz do projeto)\n"
            "As cenas 'local_html' e 'url' serao capturadas normalmente.\n"
        )

    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415
    except ImportError:
        print(
            "[ERRO] playwright nao instalado.\n"
            "Execute:  pip install playwright && playwright install chromium"
        )
        sys.exit(1)

    results: list[tuple[str, str, str]] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            color_scheme="dark",
            locale="pt-BR",
        )

        # Pre-load portal once and reuse for all portal scenes
        portal_page = None
        portal_loaded = False

        for scene in SCENES:
            name: str = scene["name"]
            desc: str = scene["description"]
            output_path = OUTPUT_DIR / f"{name}.png"

            try:
                if scene["type"] == "portal":
                    if not _check_portal():
                        results.append((name, desc, "PULADO — portal offline"))
                        continue
                    # Load portal on first portal scene, reuse for subsequent
                    if not portal_loaded or portal_page is None:
                        portal_page = context.new_page()
                        portal_page.set_viewport_size(scene["viewport"])
                        portal_page.goto(PORTAL_URL, wait_until="networkidle", timeout=30000)
                        time.sleep(2.5)
                        portal_loaded = True
                    else:
                        portal_page.set_viewport_size(scene["viewport"])

                    _navigate_portal_view(portal_page, scene["view"])
                    time.sleep(scene.get("wait_ms", 2000) / 1000)

                    if scene.get("scroll_to"):
                        _scroll_to_selector(portal_page, scene["scroll_to"])

                    portal_page.screenshot(
                        path=str(output_path),
                        full_page=scene.get("full_page", False),
                    )
                    results.append((name, desc, f"OK  ->  {output_path.relative_to(WORKSPACE)}"))

                elif scene["type"] == "local_html":
                    if not scene["path"].exists():
                        results.append((name, desc, f"PULADO — nao encontrado: {scene['path'].name}"))
                        continue
                    page = context.new_page()
                    page.set_viewport_size(scene["viewport"])
                    page.goto(scene["path"].as_uri(), wait_until="domcontentloaded", timeout=15000)
                    time.sleep(scene.get("wait_ms", 1500) / 1000)
                    page.screenshot(path=str(output_path), full_page=scene.get("full_page", False))
                    results.append((name, desc, f"OK  ->  {output_path.relative_to(WORKSPACE)}"))
                    page.close()

                elif scene["type"] == "url":
                    page = context.new_page()
                    page.set_viewport_size(scene["viewport"])
                    page.goto(scene["url"], wait_until="networkidle", timeout=30000)
                    time.sleep(scene.get("wait_ms", 3000) / 1000)
                    page.screenshot(path=str(output_path), full_page=scene.get("full_page", False))
                    results.append((name, desc, f"OK  ->  {output_path.relative_to(WORKSPACE)}"))
                    page.close()

            except Exception as exc:
                results.append((name, desc, f"ERRO — {exc}"))

        if portal_page:
            try:
                portal_page.close()
            except Exception:
                pass
        browser.close()

    # Summary
    print("\n" + "=" * 60)
    print("CAPTURAS FINALIZADAS")
    print("=" * 60)
    for name, desc, status in results:
        mark = "✓" if status.startswith("OK") else "✗"
        print(f"  {mark}  {name:<28}  {status}")
    print()
    print("Backup existente (nao recapturado):")
    print("  pictures/video/02_probabilidades_titulo.png  ->  Cena 2 (Streamlit)")
    print("  pictures/video/04_bolao_ias.png              ->  Cena 6 (Streamlit)")
    print()
    print(f"Saida: {OUTPUT_DIR}")


if __name__ == "__main__":
    capture_all()
