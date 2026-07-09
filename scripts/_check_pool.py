import duckdb

con = duckdb.connect("data/copamind.duckdb")

print("=== FASES DISPONÍVEIS ===")
print(con.execute("SELECT DISTINCT phase FROM pool_llm_predictions ORDER BY phase").fetchall())

print("\n=== STATUS POR MODELO (fase atual) ===")
rows = con.execute("""
SELECT model_id, COUNT(*) as total,
       SUM(CASE WHEN raw_response IS NOT NULL THEN 1 ELSE 0 END) as com_resposta
FROM pool_llm_predictions
WHERE phase = (SELECT MAX(phase) FROM pool_llm_predictions)
GROUP BY model_id ORDER BY model_id
""").fetchall()
for r in rows:
    print(r)

print("\n=== JOGOS NA FASE ATUAL ===")
phase = con.execute("SELECT MAX(phase) FROM pool_llm_predictions").fetchone()[0]
print("Fase:", phase)
matches = con.execute(f"SELECT DISTINCT match_id FROM pool_llm_predictions WHERE phase='{phase}'").fetchall()
print("Jogos:", [m[0] for m in matches])

print("\n=== MODELOS SEM RESPOSTA (incompletos) ===")
rows = con.execute(f"""
SELECT model_id, match_id, raw_response IS NULL as sem_resposta
FROM pool_llm_predictions
WHERE phase='{phase}' AND raw_response IS NULL
ORDER BY model_id, match_id
""").fetchall()
for r in rows:
    print(r)

con.close()
