"""Fundos e assets visuais do dashboard (base64 para injeção via CSS)."""

from __future__ import annotations

import base64
from pathlib import Path


def _b64(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    data = p.read_bytes()
    ext = p.suffix.lstrip(".")
    mime = "jpeg" if ext in ("jpg", "jpeg") else "png"
    return f"data:image/{mime};base64,{base64.b64encode(data).decode()}"


def home_bg_css() -> str:
    """CSS com fundo_taca para a tela Home."""
    src = _b64("docs/assets/fundo_taca.png")
    if not src:
        return ""
    return f"""
<style>
[data-testid="stApp"] {{
    background-image: url("{src}") !important;
    background-size: cover !important;
    background-position: center top !important;
    background-attachment: fixed !important;
}}
[data-testid="stApp"]::before {{
    content:"";
    position:fixed;inset:0;
    background: linear-gradient(180deg,
        rgba(5,12,10,.55) 0%,
        rgba(5,12,10,.85) 60%,
        rgba(5,12,10,.97) 100%);
    pointer-events:none;
    z-index:0;
}}
</style>"""


def page_bg_css(variant: int = 2) -> str:
    """CSS com fundo_clean1/2 para páginas internas.

    ``variant`` = 1 → fundo_clean1 (luminoso); 2 → fundo_clean2 (estádio escuro).
    """
    src = _b64(f"docs/assets/fundo_clean{variant}.png")
    if not src:
        return ""
    return f"""
<style>
[data-testid="stApp"] {{
    background-image: url("{src}") !important;
    background-size: cover !important;
    background-position: center center !important;
    background-attachment: fixed !important;
}}
[data-testid="stApp"]::before {{
    content:"";
    position:fixed;inset:0;
    background: linear-gradient(180deg,
        rgba(4,8,18,.70) 0%,
        rgba(4,8,18,.88) 50%,
        rgba(4,8,18,.97) 100%);
    pointer-events:none;
    z-index:0;
}}
</style>"""


def clear_bg_css() -> str:
    """Remove background customizado (usa cor sólida do tema)."""
    return """
<style>
[data-testid="stApp"] {
    background-image: none !important;
    background: #07100f !important;
}
[data-testid="stApp"]::before { display:none; }
</style>"""
