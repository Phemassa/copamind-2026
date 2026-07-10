"""Verifica progresso salvo do Bolao LLM no DuckDB e progress files."""
import json
import duckdb
from pathlib import Path

# ---- Progress file mais recente ----
progress_dir = Path("data/cache/llm_progress")
files = sorted(progress_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
latest = files[0] if files else None
if latest:
    data = json.loads(latest.read_text(encoding="utf-8"))
    print("=== LATEST PROGRESS FILE ===")
    print(f"File    : {latest.name}")
    print(f"batch_id: {data.get('batch_id')}")
    print(f"phase   : {data.get('phase')}")
    print(f"status  : {data.get('status')}")
    print(f"percent : {data.get('percent')}%")
    print(f"calls   : {data.get('completed_calls')}/{data.get('total_calls')}")
    print(f"match   : {data.get('current_match_index')}/{data.get('total_matches')} - {data.get('current_match_label')}")
    print(f"model   : {data.get('current_model_index')}/{data.get('total_models')} - {data.get('current_model_id')}")
    print(f"updated : {data.get('updated_at')}")

print()

# ---- DuckDB ----
con = duckdb.connect("data/copamind.duckdb", read_only=True)
tables = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
print("Tables:", tables)

if "pool_llm_predictions" in tables:
    total = con.execute("SELECT COUNT(*) FROM pool_llm_predictions").fetchone()[0]
    print(f"\npool_llm_predictions total rows: {total}")
    
    phase_counts = con.execute(
        "SELECT phase, status, COUNT(*) FROM pool_llm_predictions GROUP BY phase, status ORDER BY phase, status"
    ).fetchall()
    print("By phase/status:")
    for row in phase_counts:
        print(f"  {row}")

    print("\nBy model_id (round_of_16):")
    rows = con.execute(
        "SELECT model_id, COUNT(*) as n, COUNT(CASE WHEN status='valid' THEN 1 END) as valid FROM pool_llm_predictions WHERE phase='round_of_16' GROUP BY model_id ORDER BY model_id"
    ).fetchall()
    for row in rows:
        print(f"  {row}")
else:
    print("Table pool_llm_predictions NOT FOUND")

# check pool_predictions or similar
for t in tables:
    if "pool" in t.lower() or "llm" in t.lower():
        cnt = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {cnt} rows")

con.close()
