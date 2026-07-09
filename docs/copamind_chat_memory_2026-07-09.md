# Memoria de interacoes - CopaMind 2026

Data: 2026-07-09  
Projeto: CopaMind 2026  
Autor/idealizador: Phellype Flaibam Massarente  
Workspace: `C:\copamind-2026`

## Visao geral do projeto

O CopaMind 2026 nasceu como um portal simples e bem acabado para comparar LLMs locais em previsoes da Copa. A ideia evoluiu para um bolao de IAs: cada modelo local recebe o mesmo pacote estatistico de dados FIFA, gera palpites estruturados por jogo e depois e pontuado conforme os resultados oficiais aparecem.

O foco competitivo foi reduzido para o mata-mata:

- Oitavas de final
- Quartas de final
- Semifinais
- Disputa de 3o lugar
- Final

Grupos e fases anteriores entram como contexto historico, mas o bolao principal roda a partir do mata-mata.

## Dados usados

Foram extraidos e organizados dados FIFA de:

- Estatisticas de equipes: `data/fifa/team_statistics`
- Estatisticas de jogadores: `data/fifa/player_statistics`
- Jogos e resultados oficiais FIFA
- Historico de jogadores
- Fotos de jogadores, bandeiras e assets visuais quando disponiveis

O usuario tambem criou arquivos explicando os campos:

- `Estatisticas Da Equipe.txt`
- `Estatisticas do jogador.txt`

Esses arquivos foram usados como referencia conceitual para entender o significado dos CSVs como uma camada de analytics, e nao apenas como numeros crus.

## Analytics FIFA v2

Foi decidido que as LLMs nao devem receber apenas estatisticas soltas, como "Franca tem 14 gols". Elas devem receber um pacote pre-jogo enxuto e interpretado, com indices derivados.

Indices principais:

- `attack_index`
- `chance_quality_index`
- `finishing_index`
- `defense_index`
- `keeper_index`
- `control_index`
- `pressing_index`
- `transition_index`
- `discipline_risk`
- `physical_load`
- `volatility_index`
- `champion_profile_score`
- `upset_risk_score`

Logica importante:

- Saldo de gols e forte, mas nao decide sozinho.
- xG, chutes no alvo, gols sofridos, clean sheets, controle, ruptura de linhas, risco disciplinar e desgaste fisico tambem entram.
- Jogadores sao avaliados por papel: finalizador, criador, ruptura, pressao defensiva, risco disciplinar e goleiro decisivo.
- Jogadores com poucos minutos devem ser marcados como amostra pequena.
- A camada de ML aqui e deterministica/analitica, baseada em features, normalizacao e heuristicas. Nao foi treinado um modelo supervisionado complexo nesta fase.

## Snapshots de features

Foi criada a ideia/tabela de snapshots:

- `match_feature_snapshots`

Ela guarda por partida:

- `match_id`
- `phase`
- `as_of`
- `features_json`
- `baseline_json`
- `created_at`

Regra importante: evitar vazamento. O snapshot deve usar apenas dados disponiveis ate o momento do jogo/sync.

## Baseline

Cada jogo pode receber um baseline numerico simples, por exemplo:

- Poisson / Dixon-Coles simplificado
- Elo simples quando disponivel
- Probabilidades de casa/empate/fora
- Gols esperados

Esse baseline serve como referencia para a LLM, nao como verdade absoluta.

## Contrato das LLMs

Cada chamada pede uma resposta JSON estruturada.

Campos esperados:

- `winner`
- `prob_home`
- `prob_draw`
- `prob_away`
- `predicted_home_goals`
- `predicted_away_goals`
- `total_goals`
- `goes_to_extra_time`
- `goes_to_penalties`
- `penalty_winner`
- `first_goal_scorer`
- `player_picks`
- `confidence`
- `rationale`
- `evidence_ids`
- `coherence_notes`

Regra importante de mata-mata:

- Se o placar estiver empatado, a LLM precisa informar prorrogação e/ou penaltis.
- Para penaltis, o placar deve deixar claro o vencedor, por exemplo `1 (4) x 1 (3)`.
- Foi explicado que `AET` significa "after extra time", ou seja, apos prorrogacao.

## Como as chamadas funcionam

O fluxo correto documentado no Guia do Projeto:

- A chamada e por modelo + jogo.
- Formula: `jogos da fase x modelos x samples`.
- O padrao atual e `samples = 1`.
- Consenso 3x existe como modo avancado, mas nao e o padrao para rodar cerca de 30 modelos.

Exemplo:

- Quartas com 4 jogos
- 28 modelos
- 1 sample
- Total: 112 chamadas

Cada chamada salva:

- run individual em `llm_model_runs`
- consenso em `llm_model_consensus`
- palpite oficial em `pool_predictions`
- payload em `pool_prediction_payloads`

## Runner das LLMs

Foi implementado/planejado o fluxo `model-first`:

Modelo -> todos os jogos da fase -> unload -> proximo modelo

Isso substitui o fluxo menos eficiente:

Jogo -> todos os modelos -> proximo jogo

Vantagens:

- Reduz reload de modelos.
- Aproveita modelo quente na memoria.
- Ajuda LM Studio a processar em sequencia.
- Telemetria fica mais clara: Modelo X/Y, Jogo A/B, Chamada 1/1.

O runner deve pular pares `modelo + jogo` ja salvos, a menos que haja reset/reprocessamento.

## Progresso ao vivo

Foi pedido e implementado/planejado progresso real durante execucao:

- `batch_id`
- fase
- status
- total de jogos
- total de modelos
- total de chamadas
- jogo atual
- modelo atual
- sample atual
- chamadas concluidas
- percentual
- tempo decorrido
- ETA

Endpoints:

- `POST /pool/llm/phase/run`
- `GET /pool/llm/phase/progress?batch_id=...`

## Portal

Portal local:

- `http://localhost:8601/apps/portal/`

API local:

- `http://localhost:8000`

O portal estatico fica em:

- `apps/portal/index.html`
- `apps/portal/app.js`
- `apps/portal/styles.css`
- `apps/portal/data/copamind.json`

O Streamlit segue como console operacional:

- `http://localhost:8501`

## Estrutura de telas do portal

Telas principais:

- Home
- Bolao das LLMs
- Ranking das LLMs
- Dashboard das selecoes
- Dashboard dos jogadores
- Guia do projeto
- Referencias

Home:

- Usa `fundo_taca.png` / arte da taca.
- Removeu cards sobre a taca para deixar o visual limpo.
- Mantem texto principal e navegacao abaixo.

Ranking das LLMs:

- Score geral
- Score por fase
- Previsoes agregadas de vencedores
- Ranking das selecoes com mais chance
- Usa `fundo_taca.png`, preservando a taca no lado direito.

Dashboard das selecoes:

- Mostra indices derivados do analytics FIFA v2.

Dashboard dos jogadores:

- Deve permitir selecionar por selecao.
- Deve mostrar ranking top 20.
- Deve permitir ranking por fase, mas apenas fases com dados reais concluídos devem ficar habilitadas.

Guia do Projeto:

- Explica extracao dos dados.
- Explica analytics/ML deterministico.
- Explica como o prompt das LLMs e montado.
- Explica o contrato JSON.
- Explica persistencia, scoring e arquitetura.
- Deve conter diagrama Mermaid da arquitetura.

Referencias:

- Deve conter apenas autor, sobre o projeto e link do LinkedIn.
- Arquitetura e detalhes tecnicos foram movidos para Guia do Projeto.

Autor:

- Phellype Flaibam Massarente
- LinkedIn: `www.linkedin.com/in/phellype-massarente-13739810a`

## Assets visuais

Assets mencionados:

- `banner.png`
- `icon.png`
- `fundo_clean1.png`
- `fundo_taca.png`
- `sample pagina web.png`
- `docs/copamind_modelos_llm_locais.html`

Pedidos visuais importantes:

- `banner.png` deve aparecer maior, mostrando a taca toda.
- `2026` no titulo deve usar cores semelhantes ao banner.
- Nome dos modelos deve aparecer completo em uma linha quando possivel.
- Nome das equipes nos cards deve aparecer completo em uma linha quando possivel.
- Cards devem evitar textos truncados e informacoes extras mal formatadas.

## Export HTML estatico

Foi pedido um botao `Exportar HTML`:

- Gera um `.html` estatico com todos os dados fixos.
- Serve para publicar em hospedagem gratuita de HTML e compartilhar como site.
- Deve incluir as explicacoes do Guia e dados atuais do snapshot.

## Reset e reprocessamento

Foram pedidos:

- Reset de fase
- Reset geral
- Limpeza real do historico de chamadas das LLMs para permitir novas rodadas de teste

Ponto importante:

- Reset precisa limpar runs, consensos, palpites e payloads associados.
- Sem reset, o runner tende a completar apenas o que falta e nao repetir chamadas ja registradas.

## Estado recente das Quartas

Quartas informadas pelo usuario:

- Franca x Marrocos
- Espanha x Belgica
- Noruega x Inglaterra
- Argentina x Suica

O usuario informou que Suica x Colombia acabou e pediu atualizar para formar as Quartas.

Durante uma execucao das Quartas:

- O processo avancou ate cerca de 74%.
- Havia 4 jogos e aproximadamente 29 modelos antes da remocao de um modelo.
- Depois, o portal/API precisaram ser subidos novamente apos reset do PC.

## Modelos locais

O usuario tem cerca de 30 modelos no LM Studio.

Modelos citados:

- `microsoft/phi-4-reasoning-plus`
- `mistralai/mistral-7b-instruct-v0.3`
- `zai-org/glm-4.7-flash`
- `qwen/qwen3.6-27b`
- `qwen/qwen3.6-35b-a3b`
- `qwen/qwen3.5-9b`
- `allenai/olmo-3-32b-think`
- `nvidia/nemotron-3-nano-4b`
- `nvidia/nemotron-3-nano-omni`
- `google/gemma-4-12b-qat`
- `gemma-4-e4b-it-qat`

`gemma-4-e4b-it-qat` apresentou erro de carregamento no LM Studio e o usuario decidiu remover do projeto.

Regra:

- Modelos embedding, OCR, reranker ou vision-only nao participam do bolao.
- Somente modelos chat/reasoning compativeis devem participar.

## JSON invalido

O usuario observou que, de 28 modelos, 9 estavam com JSON invalido.

Interpretacao:

- As chamadas foram efetuadas e registradas quando aparecem como invalidas.
- `0/4 JSON validos | 4 invalidos` significa que houve 4 tentativas para os 4 jogos, mas nenhuma virou palpite aproveitavel.
- Algumas falhas sao erro do LM Studio: modelo nao carregou, erro 400, contexto grande demais ou channel error.
- Outras falhas sao respostas em texto natural, sem JSON parseavel.
- Sem JSON valido, nao ha consenso nem palpite oficial para ranking.

Ponto atual:

- O runner considera uma chamada invalida como processada, para evitar loop infinito.
- Para tentar de novo, e necessario resetar o modelo/fase ou implementar um modo `retry-invalid`.

## Problemas encontrados

Principais problemas:

- Prompts muito grandes para alguns modelos: exemplo de erro com request de 20270 tokens excedendo contexto 8192.
- Alguns modelos nao obedecem JSON mesmo com instrucao.
- Alguns modelos retornam texto explicativo fora do schema.
- Alguns modelos falham ao carregar no LM Studio.
- Brier aparecia como `-` quando nao havia probabilidade valida ou resultado real para calcular.
- Portal podia mostrar progresso antigo/stale como se ainda estivesse rodando.
- Alguns cards tinham informacoes de jogadores mal formatadas ou duplicadas.
- Final estava contando jogos demais por incluir disputa de 3o lugar e outros jogos incorretamente.

## Scoring

Pontuacoes/metricas desejadas:

- Acerto do vencedor
- Placar exato
- Erro absoluto de gols
- Acerto de total de gols
- Acerto de prorrogacao
- Acerto de penaltis
- Acerto do vencedor nos penaltis
- Brier score das probabilidades
- Pontos totais do bolao

Agregado por modelo:

- Score por fase
- Score geral do mata-mata
- JSON valido
- Latencia media
- Tokens/s
- Rodadas executadas
- Acuracia evolutiva apos cada atualizacao FIFA

## Chuteira de Ouro / jogadores

O usuario informou que havia erro no dado de gols de Mbappe.

Top 5 informado:

- Lionel Messi: 8 gols
- Kylian Mbappe: 7 gols
- Erling Haaland: 7 gols
- Harry Kane: 6 gols
- Vini Jr.: 4 gols

Isso precisa ser levado em conta no dashboard dos jogadores e na leitura correta dos CSVs/dados atualizados.

## Como abrir

Portal:

```powershell
cd C:\copamind-2026
python -m http.server 8601
```

Abrir:

```text
http://localhost:8601/apps/portal/
```

API:

```powershell
cd C:\copamind-2026
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

Streamlit:

```powershell
cd C:\copamind-2026
streamlit run apps/streamlit/app.py
```

Abrir:

```text
http://localhost:8501
```

## Proximos passos provaveis

- Responder ao usuario sobre os 9 modelos com JSON invalido.
- Verificar se os invalidos foram chamadas reais ou erros LM Studio por tipo.
- Melhorar UI para separar:
  - executado valido
  - executado invalido
  - erro LM Studio
  - pendente
- Criar botao ou modo `retry invalidos`.
- Garantir que reset de fase/geral limpe todo historico necessario.
- Ajustar Dashboard dos jogadores com gols corretos.
- Confirmar que `gemma-4-e4b-it-qat` nao aparece mais.
- Validar que o portal mostra todos os 28 modelos atuais.
- Reprocessar apenas faltantes/invalidos quando solicitado, sem apagar resultados bons.
