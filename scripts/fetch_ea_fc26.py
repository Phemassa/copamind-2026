"""Busca ratings de jogadores do EA Sports FC 2026 via API pública (drop-api.ea.com).

A API é pública e os dados são usados apenas para fins educacionais e de portfólio.
Referência: https://www.ea.com/pt-br/games/ea-sports-fc/ratings
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import httpx

BASE_URL = "https://drop-api.ea.com/rating/ea-sports-fc-26"
OUT_PATH = Path("data/samples/ea_fc26_players.json")
PAGE_SIZE = 40


def _headers() -> dict[str, str]:
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }


def fetch_all(max_pages: int = 80) -> list[dict]:
    """Busca todos os jogadores da Copa 2026 via API do EA FC 26."""
    players: list[dict] = []
    for page in range(max_pages):
        offset = page * PAGE_SIZE
        url = f"{BASE_URL}?limit={PAGE_SIZE}&offset={offset}&locale=en"
        try:
            r = httpx.get(url, headers=_headers(), timeout=20)
            if r.status_code != 200:
                print(f"  [stop] status {r.status_code} na página {page}")
                break
            data = r.json()
            items = data.get("items") or data.get("players") or (data if isinstance(data, list) else [])
            if not items:
                print(f"  [done] sem itens na página {page}")
                break
            players.extend(items)
            print(f"  página {page}: +{len(items)} jogadores (total: {len(players)})")
            if len(items) < PAGE_SIZE:
                break
            time.sleep(0.3)
        except Exception as exc:
            print(f"  [erro] {exc}")
            break
    return players


def fetch_copa_players() -> list[dict]:
    """Busca jogadores das seleções da Copa 2026 (ordena por overall DESC)."""
    players: list[dict] = []
    for page in range(100):
        offset = page * PAGE_SIZE
        full_url = f"{BASE_URL}?limit={PAGE_SIZE}&offset={offset}&locale=en&sort=overallRating:DESC"
        try:
            r = httpx.get(full_url, headers=_headers(), timeout=20)
            if r.status_code != 200:
                break
            data = r.json()
            # inspecciona chaves na primeira página
            if page == 0:
                print(f"  chaves da resposta: {list(data.keys()) if isinstance(data, dict) else 'lista'}")
            items = data.get("items") or data.get("players") or data.get("data") or (data if isinstance(data, list) else [])
            if not items:
                break
            players.extend(items)
            print(f"  offset={offset}: +{len(items)} (total={len(players)})")
            if len(items) < PAGE_SIZE:
                break
            time.sleep(0.25)
        except Exception as exc:
            print(f"  [erro] {exc}")
            break
    return players


def main() -> None:
    print("Buscando ratings EA FC 26...")
    players = fetch_copa_players()
    if not players:
        print("Nenhum dado obtido. Verifique a conectividade.")
        return
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(players, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Salvo: {OUT_PATH} ({len(players)} jogadores)")
    # Mostra um exemplo
    if players:
        print("Exemplo:", json.dumps(players[0], indent=2, ensure_ascii=False)[:600])


if __name__ == "__main__":
    main()
