import duckdb

con = duckdb.connect("data/copamind.duckdb")

print("=== SCHEMA DAS TABELAS DE POOL/LLM ===")
for t in ["llm_phase_batches", "llm_model_runs", "llm_pool_rounds", "pool_prediction_payloads", "llm_model_consensus"]:
    cols = con.execute(f"DESCRIBE {t}").fetchall()
    print(f"\n{t}: {[c[0] for c in cols]}")

print("\n=== DADOS EM llm_phase_batches ===")
rows = con.execute("SELECT * FROM llm_phase_batches ORDER BY created_at DESC LIMIT 5").fetchall()
for r in rows: print(r)

print("\n=== DADOS EM llm_model_runs (recentes) ===")
rows = con.execute("SELECT * FROM llm_model_runs ORDER BY created_at DESC LIMIT 20").fetchall()
for r in rows: print(r)

con.close()
