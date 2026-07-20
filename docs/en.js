/* English UI layer for the static portal.
 * Keeps a single application/data snapshot and translates both initial markup
 * and content rendered later by app.js.
 */
(() => {
  "use strict";

  document.documentElement.lang = "en";
  const catalog = window.COPAMIND_EN_TRANSLATIONS || {};

  const exact = new Map(Object.entries({
    "Bolao das LLMs": "LLM Prediction Pool",
    "Pergunte as IAs": "Ask the AIs",
    "Recarregar": "Reload",
    "Exportar HTML": "Export HTML",
    "Publicar": "Publish",
    "Navegacao principal": "Main navigation",
    "Ranking das LLMs": "LLM Ranking",
    "Análise": "Analysis",
    "Analise": "Analysis",
    "Resumo": "Overview",
    "Tabela e jogos": "Standings & matches",
    "Dashboard das selecoes": "Team dashboard",
    "Dashboard dos jogadores": "Player dashboard",
    "Guia do projeto": "Project guide",
    "Referencias": "References",
    "Referências": "References",
    "modelos locais": "local models",
    "jogos pontuados": "scored matches",
    "registros no histórico": "historical records",
    "Registros de previsão": "Prediction records",
    "Jogos mata-mata": "Knockout matches",
    "Modelos LLM": "LLM models",
    "Features ML": "ML features",
    "Mata-mata": "Knockout stage",
    "Classificacao": "Qualification",
    "Classificação": "Qualification",
    "Jogos da fase": "Stage matches",
    "Partidas": "Matches",
    "Score por IA": "Score by AI",
    "Cards das LLMs": "LLM cards",
    "Quem esta liderando o bolao?": "Who is leading the pool?",
    "Quem está liderando o bolão?": "Who is leading the pool?",
    "Vencedores": "Winners",
    "Ranking geral": "Overall ranking",
    "Pontuacao por fase": "Score by stage",
    "Pontuação por fase": "Score by stage",
    "Selecoes com mais chance de titulo": "Teams most likely to win",
    "Seleções com mais chance de título": "Teams most likely to win",
    "Painel comparativo": "Comparison dashboard",
    "Benchmark de LLMs locais": "Local LLM benchmark",
    "Resumo geral": "Overall summary",
    "Fase": "Stage",
    "Fases": "Stages",
    "Modelo": "Model",
    "Modelos": "Models",
    "Todos": "All",
    "Limpar": "Clear",
    "Tipo de gráfico": "Chart type",
    "Exportar gráfico": "Export chart",
    "Exportar todos": "Export all",
    "Exportar carta": "Export card",
    "Exportar todas": "Export all",
    "Tabela da Copa": "World Cup standings",
    "Selecao": "Team",
    "Seleção": "Team",
    "Jogadores": "Players",
    "Carregando snapshot": "Loading snapshot",
    "carregando snapshot": "loading snapshot",
    "Oitavas": "Round of 16",
    "Quartas": "Quarterfinals",
    "Semifinal": "Semifinal",
    "Terceiro lugar": "Third place",
    "Final": "Final",
    "Campeao": "Champion",
    "Campeão": "Champion",
    "Campea": "Champion",
    "Campeã": "Champion",
    "Pontos": "Points",
    "Jogos": "Matches",
    "Acerto": "Accuracy",
    "Aceite": "Acceptance",
    "Saidas": "Outputs",
    "Saídas": "Outputs",
    "Velocidade": "Speed",
    "Capacidade": "Capacity",
    "Orientacao": "Guidance",
    "Orientação": "Guidance",
    "Desclassificados": "Disqualified",
    "Fontes principais": "Primary sources",
    "Sobre o autor": "About the author",
    "Como funciona": "How it works",
    "Arquitetura": "Architecture",
    "Dados e metodologia": "Data and methodology",
    "Atualizado": "Updated",
    "Concluido": "Completed",
    "Concluído": "Completed",
    "Sem dados": "No data",
    "Nenhum resultado": "No results",
    "Consenso Geral": "Overall Consensus",
    "Referência agregada — fora da classificação": "Aggregate reference — not ranked"
    ,"Um experimento de benchmark com LLMs locais rodando em hardware proprio. Cada modelo percorre a mesma estrutura de tarefa e o mesmo contrato JSON. Os pacotes usam indices FIFA, analytics derivados e evidencias de jogadores disponiveis em cada execucao. O score e calculado fase a fase conforme os resultados oficiais chegam.": "A benchmark experiment with local LLMs running on local hardware. Every model follows the same task structure and JSON contract. The input packages use FIFA indexes, derived analytics, and player evidence available at run time. Scores are calculated stage by stage as official results arrive."
    ,"O CopaMind transforma dados de seleções, partidas e jogadores em um pacote estatístico enxuto. Esse pacote alimenta os modelos locais no LM Studio, e cada resposta vira um palpite auditável com telemetria, pontuação e acurácia por fase.": "CopaMind turns team, match, and player data into a compact statistical package. This package feeds local models in LM Studio, and every response becomes an auditable prediction with telemetry, scoring, and stage-by-stage accuracy."
    ,"Ataque combina produção real, xG, chutes no alvo e eficiência. Defesa combina gols sofridos, clean sheets, pressão, recuperações e exposição do goleiro. Controle mede posse, circulação, precisão e ruptura de linhas. Disciplina e físico entram como risco, não como prova isolada.": "Attack combines actual output, xG, shots on target, and efficiency. Defense combines goals conceded, clean sheets, pressing, recoveries, and goalkeeper exposure. Control measures possession, ball circulation, accuracy, and line-breaking ability. Discipline and physical metrics are treated as risk factors, not standalone proof."
    ,"Jogadores são avaliados por impacto por minuto/per90, papel provável e confiança da amostra. Um atleta com poucos minutos pode aparecer, mas marcado como amostra pequena.": "Players are evaluated by per-minute and per-90 impact, likely role, and sample confidence. A player with limited minutes may still appear, but is flagged as a small sample."
    ,"A chamada envia um resumo do confronto, índices das duas seleções, diferenças relativas, jogadores-chave, evidências, baseline estatístico e incertezas. O modelo não recebe a planilha inteira; recebe um pacote desenhado para raciocinar sem estourar contexto.": "The request sends a matchup summary, indexes for both teams, relative differences, key players, evidence, a statistical baseline, and uncertainties. The model does not receive the full spreadsheet; it receives a compact package designed for reasoning within the context window."
    ,"O projeto separa operacao, dados, agente e publicacao. Assim o bolao roda localmente, preserva historico em DuckDB e publica uma versao estatica para compartilhamento.": "The project separates operations, data, agent orchestration, and publishing. This allows the pool to run locally, preserve its history in DuckDB, and publish a static version for sharing."
    ,"Os dados crus viram indices normalizados. O objetivo nao e mandar planilhas enormes para a IA, mas um pacote enxuto com sinais comparaveis e evidencias rastreaveis.": "Raw data is converted into normalized indexes. The goal is not to send huge spreadsheets to the AI, but a compact package with comparable signals and traceable evidence."
    ,"CopaMind 2026 nasceu como um laboratorio divertido e serio ao mesmo tempo: usar dados da Copa, modelos locais e scoring transparente para descobrir quais IAs chutam melhor quando cada modelo percorre a mesma estrutura de tarefa e o mesmo contrato.": "CopaMind 2026 began as a project that is both fun and rigorous: using World Cup data, local models, and transparent scoring to discover which AIs predict best when every model follows the same task structure and contract."
    ,"Os CSVs não vão crus para a IA. Eles viram índices comparáveis por percentil/rank para evitar misturar escala de passes, gols, distância e cartões.": "Raw CSV files are not sent directly to the AI. They are converted into comparable percentile/rank indexes so that passing, goals, distance, and cards are not mixed on incompatible scales."
    ,"Ela combina score do bolao, taxa de JSON valido, velocidade, latencia e disponibilidade. Assim um modelo pode ser bom no palpite, mas perder pontos se for dificil de operar.": "It combines pool score, valid-JSON rate, speed, latency, and availability. A model may make strong predictions but still lose points when it is difficult to operate."
    ,"No mata-mata nao existe empate final. Se a LLM prever 1-1, o sistema exige prorrogacao ou penaltis e um classificado. Quando necessario, o palpite e normalizado para marcar decisao por penaltis.": "There are no final draws in the knockout stage. If an LLM predicts 1–1, the system requires extra time or penalties and a team to advance. When necessary, the prediction is normalized to record a penalty-shootout decision."
  }));

  const phrasePairs = [
    ["Base FIFA, classificacao e historico anterior entram no contexto pre-jogo.", "The pre-match context includes FIFA data, qualification, and prior history."],
    ["Modo estático — controles de execução desativados", "Static mode — run controls disabled"],
    ["Stage ainda não confirmada", "Stage not confirmed yet"],
    ["Fase ainda não confirmada", "Stage not confirmed yet"],
    ["LLMs projetaram chaves diferentes com base em seus palpites", "LLMs projected different brackets based on their predictions"],
    ["Cada bloco mostra quantos modelos previu aquela partida", "Each block shows how many models predicted that matchup"],
    ["Score geral, desempenho por fase, votos de vencedores e selecoes com mais chance", "Overall score, performance by stage, winner votes, and teams with the best chances"],
    ["Qualidade, velocidade e facilidade de uso", "Quality, speed, and ease of use"],
    ["Config atual serve como baseline.", "The current configuration serves as the baseline."],
    ["Ver carregamento, contexto e suporte a response_format/schema.", "Review loading, context, and response_format/schema support."],
    ["modelo com historico, mas fora da lista atual.", "Model with history, but outside the current list."],
    ["Para os modelos que nao obedecem JSON", "For models that do not follow the JSON contract"],
    ["Como comparar de forma justa", "How to compare models fairly"],
    ["O que a nota mede", "What the score measures"],
    ["CPU afeta diretamente velocidade e latência, não a capacidade lógica do modelo.", "CPU directly affects speed and latency, not the model's reasoning ability."],
    ["Barras mais longas indicam melhor desempenho.", "Longer bars indicate better performance."],
    ["Selecione a fase e exporte o quadro para redes sociais", "Select a stage and export the board for social media"],
    ["Mesma estrutura de tarefa, uma regra JSON, previsoes rastreaveis e ranking multidimensional.", "Same task structure, one JSON contract, traceable predictions, and multidimensional ranking."],
    ["Caracteristicas das selecoes", "Team characteristics"],
    ["Contexto manual controlado", "Controlled manual context"],
    ["Inputs das selecoes por fase", "Team inputs by stage"],
    ["Como entra na LLM", "How it enters the LLM"],
    ["A nota vira evidencia estruturada no contexto do jogo.", "The note becomes structured evidence in the match context."],
    ["Ela nao vira instrucao de sistema", "It does not become a system instruction"],
    ["so entra se estava disponivel antes da partida prevista", "and is only included if it was available before the predicted match"],
    ["Da FIFA ao palpite: o caminho completo", "From FIFA data to predictions: the complete pipeline"],
    ["O portal sincroniza partidas, placares, estatísticas de equipe e estatísticas de jogador", "The portal synchronizes matches, scores, team statistics, and player statistics"],
    ["Os CSVs não vão crus para a IA.", "Raw CSV files are not sent directly to the AI."],
    ["Eles viram índices comparáveis por percentil/rank", "They are converted into comparable percentile/rank indexes"],
    ["Para cada partida de mata-mata, o sistema cria um snapshot", "For every knockout match, the system creates a snapshot"],
    ["somente o que estava disponível antes do jogo", "containing only what was available before the match"],
    ["O agente monta um prompt compacto e igual para todos os modelos.", "The agent builds the same compact prompt for every model."],
    ["Cada modelo precisa responder JSON estruturado.", "Every model must return structured JSON."],
    ["Se vier texto solto ou formato inválido", "If it returns free-form text or an invalid format"],
    ["o agente tenta reparar a resposta uma vez", "the agent attempts to repair the response once"],
    ["Quando o resultado oficial chega, o palpite é pontuado.", "When the official result arrives, the prediction is scored."],
    ["Como os dados viram estatística", "How data becomes statistics"],
    ["O que vai no prompt", "What goes into the prompt"],
    ["Como executar no portal", "How to run models in the portal"],
    ["Como o portal funciona por baixo", "How the portal works under the hood"],
    ["Este diagrama mostra o caminho principal", "This diagram shows the main pipeline"],
    ["Partidas, placares, estatisticas de selecoes e estatisticas de jogadores", "Matches, scores, team statistics, and player statistics"],
    ["O DuckDB guarda a verdade operacional", "DuckDB stores the operational source of truth"],
    ["O agente monta a mesma chamada para todos os modelos locais", "The agent builds the same request for every local model"],
    ["Quando o placar oficial chega, o sistema calcula pontos e metricas", "When the official score arrives, the system calculates points and metrics"],
    ["O Streamlit fica como console tecnico.", "Streamlit remains the technical console."],
    ["Sobre o projeto", "About the project"],
    ["Autor / idealizador", "Author / creator"],
    ["Hardware local", "Local hardware"],
    ["Fontes e tecnologia", "Sources and technology"],
    ["O portal publico e estatico.", "The public portal is static."],
    ["Perfis que exigiram ajuste no ambiente", "Profiles that required environment tuning"],
    ["Durante a configuracao", "During setup"],
    ["Esta lista descreve setup", "This list describes setup"],
    ["nao equivale a falhas finais do contrato", "and does not represent final contract failures"],
    ["Os demais 20 modelos da coorte usaram o perfil-base.", "The other 20 cohort models used the baseline profile."],
    ["Exportar para compartilhar", "Export for sharing"],
    ["Gere um HTML unico com CSS, JavaScript, imagens e dados embutidos.", "Generate a single HTML file with embedded CSS, JavaScript, images, and data."],
    ["Ele pode ser publicado em qualquer hospedagem simples de arquivo estatico.", "It can be published on any basic static file host."],
    ["Palpite gerado em", "Prediction generated on"],
    ["jogo em", "match on"],
    ["acertou o campeão", "predicted the champion"],
    ["acertou o vencedor", "picked the winner"],
    ["acertou winner", "picked the winner"],
    ["placar exato", "exact score"],
    ["Prorr. Pênaltis", "Extra time · Penalties"],
    ["nos pênaltis", "on penalties"],
    ["primeiro gol", "first goal"],
    ["1º gol", "first goal"],
    ["pressao defensiva", "defensive pressing"],
    ["profundidade e quebras de linha", "depth and line-breaking runs"],
    ["gols, xG e chutes no alvo", "goals, xG, and shots on target"],
    ["chutes no alvo", "shots on target"],
    ["gols sofridos", "goals conceded"],
    ["risco disciplinar", "disciplinary risk"],
    ["amarelos", "yellow cards"],
    ["vermelhos", "red cards"],
    ["ataque em percentil", "attack percentile"],
    ["passes, 90% de acerto", "passes, 90% accuracy"],
    ["passes, 91% de acerto", "passes, 91% accuracy"],
    ["passes, 89% de acerto", "passes, 89% accuracy"],
    ["passes, 87% de acerto", "passes, 87% accuracy"],
    ["Chuteira de Ouro - gols", "Golden Boot — goals"],
    ["selecoes da fase", "teams in the stage"],
    ["selecoes da stage", "teams in the stage"],
    ["finalizador", "finisher"],
    ["ruptura", "line breaker"],
    ["pressão", "pressing"],
    ["Equipe", "Team"],
    ["Tecnico", "Coach"],
    ["Disponivel", "Available"],
    ["Fonte", "Source"]
  ];

  const replacements = [
    [/\bSemifinais\b/gi, "Semifinals"], [/\b3o lugar\b/gi, "Third place"],
    [/\bGrupos\b/gi, "Groups"], [/\bOitavas\b/gi, "Round of 16"], [/\bQuartas\b/gi, "Quarterfinals"],
    [/\bAlemanha\b/g, "Germany"], [/\bArgélia\b/g, "Algeria"], [/\bBélgica\b/g, "Belgium"],
    [/\bBrasil\b/g, "Brazil"], [/\bCanadá\b/g, "Canada"], [/\bColômbia\b/g, "Colombia"],
    [/\bCoreia do Sul\b/g, "South Korea"], [/\bCosta do Marfim\b/g, "Ivory Coast"],
    [/\bEgito\b/g, "Egypt"], [/\bEspanha\b/g, "Spain"], [/\bEstados Unidos\b/g, "United States"],
    [/\bFrança\b/g, "France"], [/\bInglaterra\b/g, "England"], [/\bJapão\b/g, "Japan"],
    [/\bMarrocos\b/g, "Morocco"], [/\bMéxico\b/g, "Mexico"], [/\bNoruega\b/g, "Norway"],
    [/\bPaíses Baixos\b/g, "Netherlands"], [/\bParaguai\b/g, "Paraguay"], [/\bSuíça\b/g, "Switzerland"],
    [/\bArábia Saudita\b/g, "Saudi Arabia"], [/\bÁfrica do Sul\b/g, "South Africa"],
    [/\bBolao\b/gi, "Pool"], [/\bbolão\b/gi, "pool"], [/\bPalpites\b/gi, "Predictions"],
    [/\bprevisoes\b/gi, "predictions"], [/\bprevisões\b/gi, "predictions"],
    [/\bJogos\b/g, "Matches"], [/\bjogos\b/g, "matches"],
    [/\bPontos\b/g, "Points"], [/\bpontos\b/g, "points"],
    [/\bSelecoes\b/g, "Teams"], [/\bSeleções\b/g, "Teams"], [/\bselecao\b/gi, "team"],
    [/\bJogadores\b/g, "Players"], [/\bjogadores\b/g, "players"],
    [/\bVencedor\b/g, "Winner"], [/\bvencedor\b/g, "winner"],
    [/\bAcuracia\b/gi, "Accuracy"], [/\bAcurácia\b/gi, "Accuracy"],
    [/\bRodada\b/gi, "Round"], [/\bFase\b/g, "Stage"], [/\bfase\b/g, "stage"],
    [/\bcarregando\b/gi, "loading"], [/\bgerando\b/gi, "generating"], [/\bgerados\b/gi, "generated"],
    [/\bNenhum\b/g, "No"], [/\bnenhum\b/g, "no"], [/\bSem\b/g, "No"],
    [/\bvalido\b/gi, "valid"], [/\bválido\b/gi, "valid"],
    [/\bmodelo\b/gi, "model"], [/\bmodelos\b/gi, "models"],
    [/\bgeral\b/gi, "overall"], [/\bhistorico\b/gi, "history"], [/\bhistórico\b/gi, "history"],
    [/\bfinalizado\b/gi, "finished"], [/\bválidas\b/gi, "valid"], [/\bválidos\b/gi, "valid"],
    [/\binválido\b/gi, "invalid"], [/\bRodadas\b/gi, "Runs"], [/\bmédia\b/gi, "average"],
    [/\bAcertos\b/gi, "Correct picks"], [/\bPrecisao\b/gi, "Precision"], [/\bPrecisão\b/gi, "Precision"],
    [/\bAssertividade\b/gi, "Accuracy"], [/\bPrevisao\b/gi, "Prediction"], [/\bPrevisão\b/gi, "Prediction"],
    [/\bvotos\b/gi, "votes"], [/\bperfil\b/gi, "profile"], [/\btitulo\b/gi, "title"], [/\btítulo\b/gi, "title"],
    [/\bClassificacao\b/gi, "Ranking"], [/\bClassificação\b/gi, "Ranking"],
    [/\bMelhor\b/gi, "Best"], [/\bEstatisticas\b/gi, "Statistics"], [/\bEstatísticas\b/gi, "Statistics"],
    [/\bExecucao\b/gi, "Runs"], [/\bExecução\b/gi, "Runs"], [/\bComparativo\b/gi, "Comparison"],
    [/\bDados\b/gi, "Data"], [/\bFontes\b/gi, "Sources"], [/\bProjeto\b/gi, "Project"],
    [/\bPartidas\b/gi, "Matches"], [/\bplacares\b/gi, "scores"], [/\bplacar\b/gi, "score"],
    [/\bequipe\b/gi, "team"], [/\bjogador\b/gi, "player"], [/\bseleções\b/gi, "teams"],
    [/\bgols\b/gi, "goals"], [/\bDefesa\b/gi, "Defense"], [/\bAtaque\b/gi, "Attack"],
    [/\bChance\b/gi, "Chance"], [/\bChutes alvo\b/gi, "Shots on target"],
    [/\bconf\.\b/gi, "conf."], [/\bativo\b/gi, "active"], [/\boffline\b/gi, "offline"],
    [/\berrou\b/gi, "missed"], [/\breal\b/gi, "actual"], [/\bde 27 modelos\b/gi, "of 27 models"],
    [/\bde 27 models\b/gi, "of 27 models"], [/\btempo\b/gi, "time"], [/\bnormal\b/gi, "regulation"]
  ];

  function translateText(value) {
    const trimmed = value.trim();
    if (!trimmed) return value;
    const normalized = trimmed.replace(/\s+/g, " ");
    let translated = exact.get(normalized) || catalog[normalized];
    if (!translated) {
      translated = normalized;
      for (const [source, target] of phrasePairs) {
        translated = translated.replace(new RegExp(source.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi"), target);
      }
      for (const [pattern, replacement] of replacements) {
        translated = translated.replace(pattern, replacement);
      }
    }
    translated = translated
      .replace(/\blottery\b/gi, "pool")
      .replace(/\bguesses\b/gi, "predictions")
      .replace(/\bguess\b/gi, "prediction")
      .replace(/\bselections\b/gi, "teams")
      .replace(/\bProrr\.\s*/gi, "Extra time · ")
      .replace(/\bcorrect shots\b/gi, "shots on target")
      .replace(/\ba classified\b/gi, "a team to advance")
      .replace(/\bfirst goals scorer\b/gi, "first goalscorer");
    if (translated === normalized) return value;
    return value.replace(trimmed, translated);
  }

  function translateElement(root) {
    if (root.nodeType === Node.TEXT_NODE) {
      const parent = root.parentElement;
      if (parent && !["SCRIPT", "STYLE", "TEXTAREA"].includes(parent.tagName)) {
        root.nodeValue = translateText(root.nodeValue);
      }
      return;
    }
    if (root.nodeType !== Node.ELEMENT_NODE && root.nodeType !== Node.DOCUMENT_NODE) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(translateElement);
    if (root.nodeType === Node.ELEMENT_NODE) {
      for (const attr of ["title", "aria-label", "placeholder"]) {
        if (root.hasAttribute(attr)) root.setAttribute(attr, translateText(root.getAttribute(attr)));
      }
    }
  }

  const observerOptions = { childList: true, subtree: true, characterData: true };
  const observer = new MutationObserver((mutations) => {
    // Disconnect while translating: changing text nodes would otherwise make
    // the observer enqueue its own mutations indefinitely.
    observer.disconnect();
    try {
      for (const mutation of mutations) {
        mutation.addedNodes.forEach(translateElement);
        if (mutation.type === "characterData") translateElement(mutation.target);
      }
    } finally {
      observer.observe(document.body, observerOptions);
    }
  });

  translateElement(document.body);
  observer.observe(document.body, observerOptions);
})();
