"""Copia o portal web para docs/portal/ com caminhos corrigidos para GitHub Pages.

Uso:
    python scripts/export_static_portal.py

O que faz:
    - Copia apps/portal/{index.html,styles.css,app.js} para docs/portal/ corrigindo
      os caminhos relativos de desenvolvimento (../../docs/assets/, ../../pictures/icons/)
      para caminhos relativos ao site do GitHub Pages (../assets/, ../icons/).
    - Copia apps/portal/data/copamind.json para docs/portal/data/ com a mesma correcao.
    - Copia pictures/icons/ para docs/icons/ (icones dos modelos LLM).
    - Cria docs/.nojekyll se nao existir.

Depois basta:
    git add docs/ && git commit -m "chore: update portal snapshot" && git push
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORTAL_SRC = ROOT / "apps" / "portal"
DOCS = ROOT / "docs"
PORTAL_DST = DOCS / "portal"

# (caminho local dev → caminho GitHub Pages relativo ao portal/)
SUBSTITUTIONS: list[tuple[str, str]] = [
    ("../../docs/assets/", "../assets/"),
    ("../../pictures/icons/", "../icons/"),
]


def fix_content(text: str) -> str:
    for old, new in SUBSTITUTIONS:
        text = text.replace(old, new)
    return text


def main() -> None:
    print("==> Exportando portal para GitHub Pages...")

    # Cria diretorios
    PORTAL_DST.mkdir(parents=True, exist_ok=True)
    (PORTAL_DST / "data").mkdir(exist_ok=True)

    # Arquivos de texto — corrige caminhos
    for filename in ("index.html", "styles.css", "app.js"):
        src = PORTAL_SRC / filename
        if not src.exists():
            print(f"  AVISO: {filename} nao encontrado, pulando.", file=sys.stderr)
            continue
        content = fix_content(src.read_text(encoding="utf-8"))
        dst = PORTAL_DST / filename
        dst.write_text(content, encoding="utf-8")
        print(f"  ok  docs/portal/{filename}")

    # JSON de dados — corrige caminhos de icones locais embutidos
    json_src = PORTAL_SRC / "data" / "copamind.json"
    if json_src.exists():
        content = fix_content(json_src.read_text(encoding="utf-8"))
        (PORTAL_DST / "data" / "copamind.json").write_text(content, encoding="utf-8")
        print("  ok  docs/portal/data/copamind.json")
    else:
        print("  AVISO: apps/portal/data/copamind.json nao encontrado.", file=sys.stderr)
        print("         Rode primeiro: python scripts/export_portal_data.py", file=sys.stderr)

    # Copia icones dos modelos LLM
    icons_src = ROOT / "pictures" / "icons"
    icons_dst = DOCS / "icons"
    if icons_src.exists():
        if icons_dst.exists():
            shutil.rmtree(icons_dst)
        shutil.copytree(icons_src, icons_dst)
        n = len(list(icons_src.iterdir()))
        print(f"  ok  docs/icons/ ({n} icones)")
    else:
        print("  AVISO: pictures/icons/ nao encontrado.", file=sys.stderr)

    # .nojekyll — evita que o GitHub Pages processe com Jekyll
    nojekyll = DOCS / ".nojekyll"
    if not nojekyll.exists():
        nojekyll.touch()
        print("  ok  docs/.nojekyll (criado)")

    print()
    print("Pronto! Estrutura em docs/:")
    print("  docs/portal/index.html   <- portal principal")
    print("  docs/portal/styles.css")
    print("  docs/portal/app.js")
    print("  docs/portal/data/copamind.json")
    print("  docs/icons/              <- icones dos modelos")
    print()
    print("Proximos passos:")
    print("  git add docs/")
    print('  git commit -m "chore: update portal snapshot"')
    print("  git push")
    print()
    print("GitHub Pages URL:")
    print("  https://phemassa.github.io/copamind-2026/portal/")


if __name__ == "__main__":
    main()
