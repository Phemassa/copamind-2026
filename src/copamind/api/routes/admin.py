"""Endpoint de publicação do portal estático (localhost only)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.requests import Request

router = APIRouter(tags=["admin"], prefix="/admin")

_ROOT = Path(__file__).parent.parent.parent.parent.parent  # raiz do repo


def _localhost_only(request: Request) -> None:
    host = request.client.host if request.client else ""
    if host not in ("127.0.0.1", "::1", "localhost"):
        raise HTTPException(status_code=403, detail="Endpoint disponivel apenas em localhost.")


@router.post("/publish")
def publish_static(request: Request) -> dict[str, object]:
    """Exporta dados, sincroniza docs/ e faz git commit + push.

    Só aceita chamadas de localhost para evitar execução remota acidental.
    """
    _localhost_only(request)

    log: list[str] = []

    # 1. Exportar dados do portal
    try:
        result = subprocess.run(
            [sys.executable, str(_ROOT / "scripts" / "export_portal_data.py")],
            cwd=str(_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
        log.append(f"export: {'ok' if result.returncode == 0 else 'aviso'} — {result.stdout.strip().splitlines()[-1] if result.stdout.strip() else 'sem output'}")
    except subprocess.TimeoutExpired:
        log.append("export: timeout (120s)")

    # 2. Sincronizar docs/
    docs = _ROOT / "docs"
    portal = _ROOT / "apps" / "portal"
    docs_data = docs / "data"
    docs_icons = docs / "icons"
    docs_data.mkdir(parents=True, exist_ok=True)
    docs_icons.mkdir(parents=True, exist_ok=True)

    import re

    _OFFLINE_INJECT = (
        '<script>window.COPAMIND_OFFLINE = true;</script>\n'
        '<style>\n'
        '/* modo offline: oculta controles locais */\n'
        '.header-actions { display: none !important; }\n'
        '#btn-refresh-scores, #run-all-models, #reset-phase-history, #reset-all-history,\n'
        '#cancel-sequential, .model-action-buttons, .context-note-form, #chat-form, #chat-reset,\n'
        '#btn-extract-url, .chat-controls, [data-section="chat"] { display: none !important; }\n'
        '.offline-notice { display: flex !important; }\n'
        '</style>\n'
    )

    def _strip_local_controls(html: str) -> str:
        """Remove botoes de controle local e injeta modo offline."""
        patterns = [
            r'<button[^>]+id="refresh-data"[^>]*>.*?</button>',
            r'<button[^>]+data-export-static[^>]*>.*?</button>',
            r'<button[^>]+id="btn-publish-static"[^>]*>.*?</button>',
            r'<button[^>]+id="open-chat-header"[^>]*>.*?</button>',
            r'<a[^>]+href="http://localhost:8501"[^>]*>.*?</a>',
            r'<div[^>]+class="header-actions"[^>]*>\s*</div>',
        ]
        for pat in patterns:
            html = re.sub(pat, "", html, flags=re.DOTALL)
        # Injeta flag offline antes de </head>
        html = html.replace("</head>", f"{_OFFLINE_INJECT}</head>", 1)
        return html

    for fname in ("index.html", "app.js", "styles.css"):
        src = portal / fname
        if src.exists():
            content = src.read_text(encoding="utf-8")
            if fname == "index.html":
                content = _strip_local_controls(content)
            (docs / fname).write_text(content, encoding="utf-8")
    src_json = portal / "data" / "copamind.json"
    if src_json.exists():
        shutil.copy2(src_json, docs_data / "copamind.json")
    for icon in (_ROOT / "pictures" / "icons").glob("*.png"):
        shutil.copy2(icon, docs_icons / icon.name)
    log.append("sync: ok — index.html, app.js, styles.css, copamind.json, icons")

    # 3. Git add
    subprocess.run(["git", "add", "docs/", "apps/portal/data/copamind.json",
                    "apps/portal/app.js", "apps/portal/styles.css"],
                   cwd=str(_ROOT), capture_output=True)
    log.append("git add: ok")

    # 4. Git commit
    stamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    commit = subprocess.run(
        ["git", "commit", "-m", f"chore(pages): atualiza portal estatico {stamp}"],
        cwd=str(_ROOT), capture_output=True, text=True,
    )
    if commit.returncode == 0:
        log.append(f"git commit: ok — {commit.stdout.strip().splitlines()[0]}")
    else:
        log.append("git commit: nada a commitar (sem mudancas)")

    # 5. Git push
    push = subprocess.run(
        ["git", "push", "origin", "main"],
        cwd=str(_ROOT), capture_output=True, text=True, timeout=60,
    )
    if push.returncode == 0:
        log.append("git push: ok")
    else:
        log.append(f"git push: ERRO — {push.stderr.strip()[:200]}")
        raise HTTPException(status_code=500, detail="\n".join(log))

    return {
        "status": "published",
        "timestamp": stamp,
        "log": log,
        "url": "https://phemassa.github.io/copamind-2026/",
    }
