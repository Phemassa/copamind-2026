/* English UI layer for the static portal.
 * Keeps a single application/data snapshot and translates both initial markup
 * and content rendered later by app.js.
 */
(() => {
  "use strict";

  document.documentElement.lang = "en";

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
    "Nenhum resultado": "No results"
  }));

  const replacements = [
    [/\bBolao\b/gi, "Pool"], [/\bbolão\b/gi, "pool"], [/\bPalpites\b/gi, "Predictions"],
    [/\bprevisoes\b/gi, "predictions"], [/\bprevisões\b/gi, "predictions"],
    [/\bJogos\b/g, "Matches"], [/\bjogos\b/g, "matches"],
    [/\bPontos\b/g, "Points"], [/\bpontos\b/g, "points"],
    [/\bSelecoes\b/g, "Teams"], [/\bSeleções\b/g, "Teams"], [/\bselecao\b/gi, "team"],
    [/\bJogadores\b/g, "Players"], [/\bjogadores\b/g, "players"],
    [/\bVencedor\b/g, "Winner"], [/\bvencedor\b/g, "winner"],
    [/\bAcuracia\b/gi, "Accuracy"], [/\bAcurácia\b/gi, "Accuracy"],
    [/\bRodada\b/gi, "Round"], [/\bFase\b/g, "Stage"], [/\bfase\b/g, "stage"],
    [/\bcarregando\b/gi, "loading"], [/\bgerando\b/gi, "generating"],
    [/\bNenhum\b/g, "No"], [/\bnenhum\b/g, "no"], [/\bSem\b/g, "No"],
    [/\bvalido\b/gi, "valid"], [/\bválido\b/gi, "valid"],
    [/\bmodelo\b/gi, "model"], [/\bmodelos\b/gi, "models"],
    [/\bgeral\b/gi, "overall"], [/\bhistorico\b/gi, "history"], [/\bhistórico\b/gi, "history"]
  ];

  function translateText(value) {
    const trimmed = value.trim();
    if (!trimmed) return value;
    let translated = exact.get(trimmed);
    if (!translated) {
      translated = trimmed;
      for (const [pattern, replacement] of replacements) {
        translated = translated.replace(pattern, replacement);
      }
    }
    if (translated === trimmed) return value;
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
