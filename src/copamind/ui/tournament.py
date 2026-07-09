"""Bracket dinamico da Copa 2026 para o portal Streamlit."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from html import escape

from copamind.data.fifa_stats import flag_url, team_label
from copamind.data.schemas import Match, MatchStatus

KNOCKOUT_STAGES = (
    "round_of_32",
    "round_of_16",
    "quarterfinal",
    "semifinal",
    "third_place",
    "final",
)

STAGE_LABELS = {
    "round_of_32": "32 avos",
    "round_of_16": "Oitavas",
    "quarterfinal": "Quartas",
    "semifinal": "Semifinal",
    "third_place": "3o lugar",
    "final": "Final",
}

EXPECTED_SLOTS = {
    "round_of_32": 16,
    "round_of_16": 8,
    "quarterfinal": 4,
    "semifinal": 2,
    "third_place": 1,
    "final": 1,
}


def build_bracket_html(
    matches: Iterable[Match] | None = None,
    *,
    consensus_by_match: Mapping[str, str] | None = None,
) -> str:
    """Gera uma chave mata-mata baseada nas partidas locais."""
    grouped: dict[str, list[Match]] = {stage: [] for stage in KNOCKOUT_STAGES}
    for match in matches or []:
        stage = str(match.stage)
        if stage in grouped:
            grouped[stage].append(match)
    for items in grouped.values():
        items.sort(key=lambda item: (item.match_date, item.match_id))

    columns = [
        _column(stage, grouped[stage], consensus_by_match or {})
        for stage in KNOCKOUT_STAGES
        if grouped[stage] or stage in {"round_of_32", "round_of_16", "quarterfinal", "semifinal", "final"}
    ]
    return f"""
<style>
  .cm-bracket {{
    background:#071018;
    border:1px solid #1b3240;
    border-radius:8px;
    color:#e8f4f1;
    font-family:Inter,system-ui,-apple-system,Segoe UI,sans-serif;
    padding:18px;
  }}
  .cm-bracket-head {{
    display:flex;
    justify-content:space-between;
    gap:14px;
    align-items:flex-end;
    margin-bottom:16px;
  }}
  .cm-bracket-title {{font-size:20px;font-weight:800;line-height:1.2}}
  .cm-bracket-sub {{color:#94a8b3;font-size:13px;margin-top:4px}}
  .cm-bracket-flow {{
    display:flex;
    gap:16px;
    overflow-x:auto;
    padding-bottom:6px;
  }}
  .cm-bracket-col {{
    min-width:232px;
    display:flex;
    flex-direction:column;
    gap:10px;
  }}
  .cm-bracket-col h3 {{
    color:#38d6a5;
    font-size:12px;
    letter-spacing:0;
    margin:0 0 2px;
    text-transform:uppercase;
  }}
  .cm-bracket-card {{
    background:#0d1a24;
    border:1px solid #203747;
    border-radius:8px;
    padding:10px;
    min-height:124px;
  }}
  .cm-bracket-card.finished {{border-color:#38d6a5}}
  .cm-bracket-card.scheduled {{border-color:#57a7ff}}
  .cm-bracket-team {{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:8px;
    color:#edf7f4;
    font-size:14px;
    min-height:28px;
  }}
  .cm-bracket-team span:first-child {{
    display:flex;
    align-items:center;
    gap:7px;
    min-width:0;
  }}
  .cm-bracket-team b {{
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
    max-width:148px;
  }}
  .cm-bracket-team img {{width:22px;height:22px;border-radius:50%;object-fit:cover}}
  .cm-bracket-score {{font-weight:800;color:#38d6a5}}
  .cm-bracket-meta {{
    border-top:1px solid #203747;
    color:#94a8b3;
    font-size:12px;
    margin-top:8px;
    padding-top:8px;
    display:flex;
    flex-direction:column;
    gap:3px;
  }}
  .cm-bracket-empty {{color:#536775}}
</style>
<div class="cm-bracket">
  <div class="cm-bracket-head">
    <div>
      <div class="cm-bracket-title">Chave mata-mata CopaMind</div>
      <div class="cm-bracket-sub">Dados locais sincronizados da FIFA, com consenso das LLMs quando houver.</div>
    </div>
  </div>
  <div class="cm-bracket-flow">{"".join(columns)}</div>
</div>
"""


def _column(stage: str, matches: list[Match], consensus_by_match: Mapping[str, str]) -> str:
    slots = max(EXPECTED_SLOTS.get(stage, len(matches)), len(matches))
    cards = [
        _match_card(matches[index], consensus_by_match)
        if index < len(matches)
        else _empty_card(stage, index)
        for index in range(slots)
    ]
    return f"""
<section class="cm-bracket-col">
  <h3>{escape(STAGE_LABELS.get(stage, stage))}</h3>
  {"".join(cards)}
</section>
"""


def _match_card(match: Match, consensus_by_match: Mapping[str, str]) -> str:
    status_class = "finished" if match.status is MatchStatus.finished else "scheduled"
    consensus = consensus_by_match.get(match.match_id)
    meta = [_date_label(match.match_date), f"Status: {_status_label(match)}"]
    if consensus:
        meta.append(f"LLM: {consensus}")
    return f"""
<article class="cm-bracket-card {status_class}">
  {_team_row(match.home_team_id, match.home_score)}
  {_team_row(match.away_team_id, match.away_score)}
  <div class="cm-bracket-meta">{"".join(f"<span>{escape(item)}</span>" for item in meta)}</div>
</article>
"""


def _empty_card(stage: str, index: int) -> str:
    return f"""
<article class="cm-bracket-card">
  <div class="cm-bracket-team cm-bracket-empty"><span>A definir</span><span>-</span></div>
  <div class="cm-bracket-team cm-bracket-empty"><span>A definir</span><span>-</span></div>
  <div class="cm-bracket-meta"><span>{escape(STAGE_LABELS.get(stage, stage))} #{index + 1}</span></div>
</article>
"""


def _team_row(team_id: str, score: int | None) -> str:
    score_html = "-" if score is None else str(score)
    return f"""
<div class="cm-bracket-team">
  <span><img src="{escape(flag_url(team_id))}" alt="" /><b>{escape(team_label(team_id))}</b></span>
  <span class="cm-bracket-score">{escape(score_html)}</span>
</div>
"""


def _date_label(value: datetime) -> str:
    return value.strftime("%d/%m/%Y %H:%M") if value else "Data a definir"


def _status_label(match: Match) -> str:
    if match.status is MatchStatus.finished:
        return "finalizado"
    if match.status is MatchStatus.cancelled:
        return "cancelado"
    return "agendado"
