"""Copia o portal web para docs/ (raiz) com caminhos corrigidos para GitHub Pages.

O servidor local serve apps/portal/ na raiz (porta 8601).
O GitHub Pages serve docs/ na raiz (https://phemassa.github.io/copamind-2026/).
Este script faz a copia fiel, corrigindo apenas os caminhos relativos de assets.

Uso:
    python scripts/export_static_portal.py

O que faz:
    - Remove docs/portal/ (subpasta legada, se existir).
    - Copia os arquivos do portal e o catalogo ingles para docs/.
      os caminhos relativos de desenvolvimento:
        ../../docs/assets/  ->  assets/
        ../../pictures/icons/  ->  icons/
    - Copia apps/portal/data/copamind.json para docs/data/ com a mesma correcao.
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

# (caminho local dev → caminho GitHub Pages relativo a docs/)
SUBSTITUTIONS: list[tuple[str, str]] = [
    ("../../docs/assets/", "assets/"),
    ("../../pictures/icons/", "icons/"),
    # API local — substitui por string vazia para evitar o dialogo de
    # "Local Network Access" do Edge/Chrome ao abrir o site estatico HTTPS.
    # fetch("" + "/rota") vira URL relativa que retorna 404 sem acionar permissao.
    (
        'const API_BASE = "http://localhost:8000";',
        'const API_BASE = ""; // static mode — API local nao disponivel',
    ),
    # Botao Admin aponta para localhost — desativa no site estatico
    (
        '<a href="http://localhost:8501" target="_blank" rel="noreferrer">Admin</a>',
        '<a aria-disabled="true" title="Disponivel apenas no servidor local" style="opacity:.35;pointer-events:none;cursor:default">Admin</a>',
    ),
]

OFFLINE_HEAD = """<script>window.COPAMIND_OFFLINE = true;</script>
<style>
/* modo offline: oculta controles locais */
.header-actions { display: none !important; }
#btn-refresh-scores, #run-all-models, #reset-phase-history, #reset-all-history,
#cancel-sequential, .model-action-buttons, .context-note-form, #chat-form, #chat-reset,
#btn-extract-url, .chat-controls, [data-section="chat"] { display: none !important; }
.offline-notice { display: flex !important; }
.language-switch { position: fixed; right: 18px; bottom: 18px; z-index: 1000;
  display: flex; gap: 4px; padding: 4px; border: 1px solid rgba(120,180,255,.3);
  border-radius: 999px; background: rgba(5,15,30,.9); backdrop-filter: blur(10px); }
.language-switch a { padding: 7px 10px; border-radius: 999px; color: #a9c8e8;
  font: 700 12px/1 system-ui,sans-serif; text-decoration: none; }
.language-switch a[aria-current="page"] { color: #06101e; background: #67e8f9; }
</style>"""


def static_html(text: str, *, english: bool = False) -> str:
    """Prepara uma pagina sem controles locais e com seletor de idioma."""
    text = fix_content(text)
    text = text.replace("</head>", f"{OFFLINE_HEAD}\n</head>", 1)
    switch = (
        '<nav class="language-switch" aria-label="Language">'
        f'<a href="./"'
        f'{" " if english else " aria-current=\"page\""}>PT</a>'
        f'<a href="en/"'
        f'{" aria-current=\"page\"" if english else ""}>EN</a></nav>'
    )
    text = text.replace("</body>", f"{switch}\n</body>", 1)
    if english:
        text = text.replace('<html lang="pt-BR">', '<html lang="en">', 1)
        text = text.replace("<head>", '<head>\n  <base href="../" />', 1)
        text = text.replace(
            "<title>CopaMind 2026 | Bolao das LLMs</title>",
            "<title>CopaMind 2026 | LLM Prediction Pool</title>",
            1,
        )
        text = text.replace(
            '<script src="app.js"></script>',
            '<script src="en-translations.js"></script>\n'
            '  <script src="app.js"></script>\n'
            '  <script src="en.js"></script>',
            1,
        )
    return text


def fix_content(text: str) -> str:
    for old, new in SUBSTITUTIONS:
        text = text.replace(old, new)
    return text


def main() -> None:
    print("==> Exportando portal para GitHub Pages (raiz docs/)...")

    # Remove subpasta legada docs/portal/ se existir
    legacy = DOCS / "portal"
    if legacy.exists():
        shutil.rmtree(legacy)
        print("  rm  docs/portal/ (subpasta legada removida)")

    # Cria docs/data/
    (DOCS / "data").mkdir(parents=True, exist_ok=True)

    # Arquivos de texto — corrige caminhos
    for filename in ("index.html", "styles.css", "app.js", "en.js", "en-translations.js"):
        src = PORTAL_SRC / filename
        if not src.exists():
            print(f"  AVISO: {filename} nao encontrado, pulando.", file=sys.stderr)
            continue
        content = src.read_text(encoding="utf-8")
        if filename == "index.html":
            content = static_html(content)
        else:
            content = fix_content(content)
        (DOCS / filename).write_text(content, encoding="utf-8")
        print(f"  ok  docs/{filename}")

    # Versao inglesa reutiliza CSS, JS, imagens e snapshot da raiz.
    en_dir = DOCS / "en"
    en_dir.mkdir(parents=True, exist_ok=True)
    index_src = PORTAL_SRC / "index.html"
    if index_src.exists():
        content = static_html(index_src.read_text(encoding="utf-8"), english=True)
        (en_dir / "index.html").write_text(content, encoding="utf-8")
        print("  ok  docs/en/index.html")

    # JSON de dados — corrige caminhos de icones locais embutidos
    json_src = PORTAL_SRC / "data" / "copamind.json"
    if json_src.exists():
        content = fix_content(json_src.read_text(encoding="utf-8"))
        (DOCS / "data" / "copamind.json").write_text(content, encoding="utf-8")
        print("  ok  docs/data/copamind.json")
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
    print("  docs/index.html          <- portal (raiz do site)")
    print("  docs/styles.css")
    print("  docs/app.js")
    print("  docs/en.js")
    print("  docs/en-translations.js")
    print("  docs/en/index.html      <- English version")
    print("  docs/data/copamind.json")
    print("  docs/assets/             <- imagens (icon, banner, fundos)")
    print("  docs/icons/              <- icones dos modelos")
    print()
    print("Proximos passos:")
    print("  git add docs/")
    print('  git commit -m "chore: update portal snapshot"')
    print("  git push")
    print()
    print("GitHub Pages URL:")
    print("  PT: https://phemassa.github.io/copamind-2026/")
    print("  EN: https://phemassa.github.io/copamind-2026/en/")


if __name__ == "__main__":
    main()
