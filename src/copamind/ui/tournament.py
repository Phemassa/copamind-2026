"""Bracket visual da Copa 2026 em HTML (tema escuro/verde-ciano)."""

from __future__ import annotations

from copamind.data.connectors.flags import TEAMS

# ── resultados R16 conhecidos (06/07/2026) ──────────────────────────────────
R16_RESULTS = {
    89: ("T-MAR", "T-CAN", "3-0"),
    90: ("T-FRA", "T-PAR", "1-0"),
    91: ("T-NOR", "T-BRA", "2-1"),
    92: ("T-ENG", "T-MEX", "3-2"),
    93: None,  # hoje 15:00
    94: None,  # hoje 20:00
    95: None,  # amanhã
    96: None,  # amanhã
}

# quartas confirmadas
QF_CONFIRMED = {
    97: ("T-FRA", "T-MAR"),
    99: ("T-NOR", "T-ENG"),
}


def _flag_img(team_id: str, w: int = 24) -> str:
    iso = TEAMS.get(team_id, {}).get("iso2", "")
    if not iso:
        return ""
    return f'<img src="https://flagcdn.com/w{w}/{iso}.png" width="{w}" style="vertical-align:middle;border-radius:2px" />'


def _name(team_id: str) -> str:
    t = TEAMS.get(team_id)
    if t is None:
        return "A definir"
    return t["name_pt"]


def _match_cell(
    home_id: str | None, away_id: str | None, result: str | None = None, highlight: str = ""
) -> str:
    if home_id is None:
        home_html = '<span style="color:#4e6080">A definir</span>'
    else:
        home_html = f"{_flag_img(home_id)} <strong>{_name(home_id)}</strong>"

    if away_id is None:
        away_html = '<span style="color:#4e6080">A definir</span>'
    else:
        away_html = f"{_flag_img(away_id)} <strong>{_name(away_id)}</strong>"

    score_html = (
        f'<span style="color:#19e3c2;font-weight:700;font-size:18px">{result}</span>'
        if result
        else '<span style="color:#4e6080;font-size:13px">Aguardando</span>'
    )
    border = f"border-color:{highlight}" if highlight else "border-color:#1f2f42"
    return f"""
      <div style="background:#0f1826;{border};border-width:1px;border-style:solid;border-radius:10px;padding:10px 14px;min-width:210px;margin:4px 0">
        <div style="color:#e8f0f8;margin-bottom:4px">{home_html}</div>
        <div style="text-align:center;margin:4px 0">{score_html}</div>
        <div style="color:#e8f0f8">{away_html}</div>
      </div>"""


def build_bracket_html() -> str:
    """Gera o HTML completo do bracket da Copa 2026."""

    # R16 — lado superior (MAR, FRA, NOR, ENG avançaram; POR/ESP, USA/BEL pendentes)
    r16_upper = [
        _match_cell("T-CAN", "T-MAR", "0-3"),
        _match_cell("T-PAR", "T-FRA", "0-1"),
        _match_cell("T-BRA", "T-NOR", "1-2"),
        _match_cell("T-MEX", "T-ENG", "2-3"),
    ]
    r16_lower = [
        _match_cell("T-POR", "T-ESP", None, "#2f6bff"),
        _match_cell("T-USA", "T-BEL", None, "#2f6bff"),
        _match_cell("T-ARG", "T-EGY", None, "#e5a020"),
        _match_cell("T-SUI", "T-COL", None, "#e5a020"),
    ]

    # QF
    qf1 = _match_cell("T-FRA", "T-MAR", None)
    qf2_home = _match_cell(None, None)  # POR/ESP
    qf3 = _match_cell("T-NOR", "T-ENG", None)
    qf4_home = _match_cell(None, None)  # ARG/EGY ou SUI/COL

    # Legend
    def legend_item(color: str, text: str) -> str:
        return f'<span style="display:inline-flex;align-items:center;gap:6px;margin-right:16px"><span style="width:12px;height:12px;background:{color};border-radius:3px;flex-shrink:0"></span>{text}</span>'

    legend = (
        legend_item("#19e3c2", "Resultado confirmado")
        + legend_item("#2f6bff", "Hoje")
        + legend_item("#e5a020", "Amanhã")
    )

    def col(title: str, *cells: str) -> str:
        return f"""
        <div style="display:flex;flex-direction:column;gap:4px;min-width:240px">
          <div style="color:#19e3c2;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;text-align:center">{title}</div>
          {"".join(cells)}
        </div>"""

    return f"""
<style>
  .bracket-root {{
    background: #070b12;
    color: #e8f0f8;
    font-family: system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
    font-size: 14px;
    padding: 20px;
    border-radius: 12px;
  }}
  .bracket-title {{ font-size: 20px; font-weight: 700; margin-bottom: 6px; }}
  .bracket-legend {{ color: #8fa3bd; font-size: 13px; margin-bottom: 20px; }}
  .bracket-flow {{ display: flex; gap: 24px; align-items: flex-start; overflow-x: auto; }}
</style>
<div class="bracket-root">
  <div class="bracket-title">⚽ Copa do Mundo 2026 — Bracket</div>
  <div class="bracket-legend">{legend}</div>
  <div class="bracket-flow">
    {col("Oitavas (sup.)", *r16_upper)}
    {col("Quartas (sup.)", qf1, "<br>", qf3)}
    {col("Oitavas (inf.)", *r16_lower)}
    {col("Quartas (inf.)", qf2_home, "<br>", qf4_home)}
    {col("Semi / Final", _match_cell(None, None), "<br>", _match_cell(None, None), "<br><br>", _match_cell(None, None))}
  </div>
</div>"""
