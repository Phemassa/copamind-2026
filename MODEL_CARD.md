# MODEL_CARD — CopaMind 2026

> Cartão de modelo dos componentes preditivos. As probabilidades são
> **experimentais e educacionais** e não representam garantia de resultado.

## Visão geral

O CopaMind produz probabilidades de partidas e do torneio a partir de um
conjunto de modelos estatísticos/ML **calibrados**. Um LLM local interpreta e
explica, mas **não** produz as probabilidades.

## Componentes

| Modelo | Papel | Entradas | Saídas |
| --- | --- | --- | --- |
| **Elo** | Rating de força | resultados, mando, importância, diferença de gols | rating, prob. esperada |
| **Poisson / Dixon-Coles** | Gols esperados | forças ataque/defesa | matriz de placares, 1x2, over/under |
| **Ensemble** | Combinação | probabilidades Elo + Poisson | 1x2 combinado |
| **Calibração (isotônica)** | Ajuste | probabilidades + resultados | probabilidades calibradas |
| **Simulação Monte Carlo** | Torneio | probabilidades por confronto | chances por fase/título |

## Dados

- Dataset de amostra **sintético e fictício** (não representa dados reais).
- Fontes reais previstas: OpenFootball `worldcup.json`, StatsBomb Open Data,
  football-data.org, API-Football, Zafronix (ver `config/sources.example.yaml`).
- Toda linha carrega linhagem (`source`, `collected_at`, `available_at`, `snapshot_id`).

## Avaliação

- Métricas: Brier score, Log-Loss, Expected Calibration Error (ECE), curva de
  confiabilidade. Bolão de IAs registra desempenho por preditor ao longo do tempo.

## Prevenção de vazamento temporal

- Features e previsões usam apenas dados disponíveis antes da partida
  (`available_at` / `as_of`). Palpites do bolão são imutáveis após travados.

## Limitações

- Com dataset pequeno, modelos de gradient boosting (CatBoost/XGBoost) e SHAP
  ainda não são treinados — dependem de dados reais.
- Elo/Poisson são baselines; a qualidade depende da cobertura e atualidade dos dados.

## Uso pretendido

Educacional, exploratório e de portfólio. **Não** deve ser usado para apostas.
