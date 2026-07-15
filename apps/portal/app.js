const PHASE_LABELS = {
  group: "Grupos",
  round_of_32: "16 avos",
  round_of_16: "Oitavas",
  quarterfinal: "Quartas",
  semifinal: "Semifinais",
  third_place: "3o lugar",
  final: "Final",
};
const API_BASE = "http://localhost:8000";
const RUN_POLL_MS = 10000;
const PROGRESS_POLL_MS = 2000;
const RUN_TIMEOUT_MS = 15 * 60 * 1000;
const BULK_PHASES = ["round_of_16", "quarterfinal", "semifinal", "third_place", "final"];
const STATIC_ASSETS = [
  "../../docs/assets/banner.png",
  "../../docs/assets/copamind_2026.png",
  "../../docs/assets/fundo_clean1.png",
  "../../docs/assets/fundo_taca.png",
  "../../docs/assets/icon.png",
];

let state = null;
let activePhase = "round_of_16";
let activeView = "home";
let activePlayerTeam = "all";
let activePlayerRanking = "top20";
let activeCapturePhase = null;
let activeTournamentStage = "group";
const runningRuns = new Map();
const recoveredProgressBatches = new Set();
let sequentialBatch = null;
let chatSessionId = localStorage.getItem("copamind_chat_session") || null;
let chatModels = [];
let chatSelectedModels = new Set();
let chatNews = null;
let chatPollTimer = null;

const CHAT_HARDWARE_DETAILS = {
  "mistralai/devstral-small-2-2512":"15,2 GB · muito CPU", "qwen/qwen3.6-27b":"17,5 GB · muito CPU", "google/gemma-4-31b-qat":"18,9 GB · muito lento", "allenai/olmo-3-32b-think":"19,5 GB · lento + raciocínio longo", "google/gemma-4-31b":"19,9 GB · muito lento", "bytedance/seed-oss-36b":"21,8 GB · extremamente pesado",
  "openai/gpt-oss-20b":"12,1 GB · MoE 3,6B ativos · utilizável", "baidu/ernie-4.5-21b-a3b":"13,5 GB · MoE 3B · depende da RAM", "liquid/lfm2-24b-a2b":"14,4 GB · MoE 2B ativos", "google/gemma-4-26b-a4b-qat":"15,6 GB · MoE 4B · moderadamente lento", "zai-org/glm-4.7-flash":"18,1 GB · MoE 3B · CPU pesada", "qwen/qwen3.6-35b-a3b":"22,1 GB · MoE 3B · muita RAM", "nvidia/nemotron-3-nano-omni":"26,1 GB · MoE ~3B · limite de 32 GB",
  "microsoft/phi-4-reasoning-plus":"9,1 GB · ~1/3 na CPU", "microsoft/phi-4":"9,1 GB · CPU parcial", "mistralai/ministral-3-14b-reasoning":"9,1 GB · CPU parcial + reasoning",
  "google/gemma-4-12b-qat":"7,2 GB · pequeno offload", "google/gemma-4-12b":"7,6 GB · offload moderado",
  "qwen/qwen3.5-9b":"6,5 GB · excelente equilíbrio", "mistralai/mistral-nemo-instruct-2407":"6,6 GB · quase toda GPU",
  "microsoft/phi-4-mini-reasoning":"2,5 GB · muito rápido", "nvidia/nemotron-3-nano-4b":"2,8 GB · muito rápido", "ibm/granite-4-h-tiny":"4,2 GB · muito rápido", "google/gemma-4-e2b":"4,4 GB · rápido", "ibm/granite-3.2-8b":"4,9 GB · rápido", "deepseek/deepseek-r1-0528-qwen3-8b":"5,0 GB · rápido, reasoning longo", "essentialai/rnj-1":"5,1 GB · rápido"
};

document.getElementById("refresh-data").addEventListener("click", () => loadData(true));
document.getElementById("open-chat-header")?.addEventListener("click", () => {
  activeView = "chat";
  renderMainNav();
  if (!chatSessionId || !chatModels.length) {
    initializeChat().catch((error) => setChatStatus(`API do chat offline: ${error.message}`));
  }
  document.querySelector('[data-section="chat"]')?.scrollIntoView({ behavior: "smooth", block: "start" });
});
document.getElementById("btn-refresh-scores")?.addEventListener("click", triggerRefreshScores);
document.getElementById("btn-export-linkedin")?.addEventListener("click", exportLinkedInImage);
document.getElementById("btn-export-ranking")?.addEventListener("click", exportRankingImage);
document.getElementById("btn-export-benchmark")?.addEventListener("click", exportBenchmarkImage);
document.getElementById("btn-publish-static")?.addEventListener("click", publishStaticSite);
document.querySelectorAll("[data-export-static]").forEach((button) => {
  button.addEventListener("click", exportStaticSite);
});
document.getElementById("context-note-form")?.addEventListener("submit", saveContextNote);
document.getElementById("btn-extract-url")?.addEventListener("click", extractFromUrl);
document.getElementById("chat-form")?.addEventListener("submit", sendChatQuestion);
document.getElementById("chat-extract-news")?.addEventListener("click", extractChatNews);
document.getElementById("chat-reset")?.addEventListener("click", resetChatSession);
document.getElementById("chat-select-all")?.addEventListener("click", () => selectChatModels(true));
document.getElementById("chat-select-none")?.addEventListener("click", () => selectChatModels(false));
document.getElementById("chat-question")?.addEventListener("input", updateChatSendState);
document.querySelectorAll(".main-nav button").forEach((button) => {
  button.addEventListener("click", () => {
    activeView = button.dataset.view || "bolao";
    renderMainNav();
    if (activeView === "chat" && (!chatSessionId || !chatModels.length)) {
      initializeChat().catch((error) => setChatStatus(`API do chat offline: ${error.message}`));
    }
  });
});
document.querySelectorAll("[data-home-view]").forEach((button) => {
  button.addEventListener("click", () => {
    activeView = button.dataset.homeView || "bolao";
    renderMainNav();
    document.querySelector(`[data-section="${cssEscape(activeView)}"]`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});
loadData();
if (!window.COPAMIND_OFFLINE) {
  initializeChat().catch(() => setChatStatus("API do chat offline."));
}

async function loadData(cacheBust = false) {
  if (window.COPAMIND_EMBEDDED_DATA) {
    state = window.COPAMIND_EMBEDDED_DATA;
    activePhase = (state.phases || []).find((phase) => phase.key === activePhase)?.key
      || state.phases?.[0]?.key
      || "round_of_16";
    activeCapturePhase = activeCapturePhase || defaultCapturePhase();
    reconcileRunningRuns();
    renderAll();
    return;
  }
  const suffix = cacheBust ? `?t=${Date.now()}` : "";
  const response = await fetch(`data/copamind.json${suffix}`);
  if (!response.ok) {
    renderMissingData();
    return;
  }
  state = await response.json();
  activePhase = (state.phases || []).find((phase) => phase.key === activePhase)?.key
    || state.phases?.[0]?.key
    || "round_of_16";
  activeCapturePhase = activeCapturePhase || defaultCapturePhase();
  reconcileRunningRuns();
  renderAll();
  recoverLatestBulkProgress().catch(() => {});
}

// -- Pergunte as IAs -------------------------------------------------------
async function chatFetch(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try { detail = (await response.json()).detail || detail; } catch (_err) { /* noop */ }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return response.json();
}

async function initializeChat() {
  const modelPayload = await chatFetch("/chat/models");
  chatModels = modelPayload.models || [];
  const availableIds = chatModels.filter((item) => item.available).map((item) => item.model_id);
  if (!chatSelectedModels.size) {
    const recommended = chatModels
      .filter((item) => item.available && item.group_id === "fast")
      .map((item) => item.model_id);
    chatSelectedModels = new Set(recommended.length ? recommended : availableIds);
  }
  renderChatModels();
  let payload = null;
  if (chatSessionId) {
    try { payload = await chatFetch(`/chat/sessions/${encodeURIComponent(chatSessionId)}`); }
    catch (_err) { chatSessionId = null; }
  }
  if (!chatSessionId) {
    payload = await chatFetch("/chat/sessions", { method: "POST" });
    chatSessionId = payload.session.session_id;
    localStorage.setItem("copamind_chat_session", chatSessionId);
  }
  hydrateChat(payload);
}

function hydrateChat(payload) {
  renderChatTimeline(payload?.messages || []);
  const news = payload?.news || [];
  if (news.length) {
    chatNews = news[news.length - 1];
    document.getElementById("chat-news-url").value = chatNews.source_url || "";
    document.getElementById("chat-news-title").value = chatNews.title || "";
    document.getElementById("chat-news-summary").value = chatNews.summary || "";
  }
  const batch = payload?.active_batch;
  if (batch && !["completed", "completed_with_errors", "failed"].includes(batch.status)) {
    pollChatBatch(batch.batch_id);
  } else {
    setChatStatus("Pronto para perguntar.");
  }
  updateChatSendState();
}

function renderChatModels() {
  const container = document.getElementById("chat-models");
  if (!container) return;
  const groups = [...new Map(
    chatModels
      .slice()
      .sort((a, b) => (a.group_order || 99) - (b.group_order || 99))
      .map((item) => [item.group_id || "other", {
        id: item.group_id || "other", label: item.group_label || "Outros",
        order: item.group_order || 99,
      }])
  ).values()];
  container.innerHTML = chatModels.length ? groups.map((group) => {
    const models = chatModels.filter((item) => (item.group_id || "other") === group.id);
    const selectedCount = models.filter((item) => chatSelectedModels.has(item.model_id)).length;
    return `<section class="chat-model-group group-${escapeAttr(group.id)}">
      <div class="chat-model-group-head">
        <strong>${escapeHtml(group.label)}</strong><span>${selectedCount}/${models.length}</span>
        <button type="button" data-chat-group-select="${escapeAttr(group.id)}">Selecionar</button>
        <button type="button" data-chat-group-clear="${escapeAttr(group.id)}">Limpar</button>
      </div>
      ${models.map((item) => `
        <label class="chat-model-option ${item.available ? "" : "offline"}">
          <input type="checkbox" data-chat-model="${escapeAttr(item.model_id)}"
            ${chatSelectedModels.has(item.model_id) ? "checked" : ""} ${item.available ? "" : "disabled"} />
          <span><strong>${escapeHtml(item.model_id)}</strong><small>${item.available ? "online" : "offline"} · ${escapeHtml(CHAT_HARDWARE_DETAILS[item.model_id] || "perfil não medido")}</small></span>
        </label>`).join("")}
    </section>`;
  }).join("") : `<span>Nenhum modelo configurado.</span>`;
  container.querySelectorAll("[data-chat-model]").forEach((input) => input.addEventListener("change", () => {
    if (input.checked) chatSelectedModels.add(input.dataset.chatModel);
    else chatSelectedModels.delete(input.dataset.chatModel);
    updateChatSendState();
  }));
  container.querySelectorAll("[data-chat-group-select]").forEach((button) => button.addEventListener("click", () => {
    selectChatModelGroup(button.dataset.chatGroupSelect, true);
  }));
  container.querySelectorAll("[data-chat-group-clear]").forEach((button) => button.addEventListener("click", () => {
    selectChatModelGroup(button.dataset.chatGroupClear, false);
  }));
  updateChatSendState();
}

function selectChatModelGroup(groupId, select) {
  chatModels.filter((item) => item.group_id === groupId && item.available).forEach((item) => {
    if (select) chatSelectedModels.add(item.model_id);
    else chatSelectedModels.delete(item.model_id);
  });
  renderChatModels();
}

function selectChatModels(select) {
  chatSelectedModels = new Set(select ? chatModels.filter((item) => item.available).map((item) => item.model_id) : []);
  renderChatModels();
}

function updateChatSendState() {
  const button = document.getElementById("chat-send");
  if (!button) return;
  button.disabled = !document.getElementById("chat-question")?.value.trim() || !chatSelectedModels.size || Boolean(chatPollTimer);
}

function setChatStatus(message) {
  const element = document.getElementById("chat-status");
  if (element) element.textContent = message;
}

async function extractChatNews() {
  const url = document.getElementById("chat-news-url")?.value.trim();
  const status = document.getElementById("chat-news-status");
  if (!url) { status.textContent = "Informe uma URL valida."; return; }
  if (!chatSessionId) {
    status.textContent = "Reconectando a API do chat...";
    try { await initializeChat(); }
    catch (error) { status.textContent = `API do chat indisponivel: ${error.message}`; return; }
  }
  status.textContent = "Buscando e extraindo noticia...";
  try {
    chatNews = await chatFetch(`/chat/sessions/${encodeURIComponent(chatSessionId)}/news/extract`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url }),
    });
    document.getElementById("chat-news-title").value = chatNews.title || "";
    document.getElementById("chat-news-summary").value = chatNews.summary || "";
    status.textContent = `Fonte adicionada somente a esta conversa: ${chatNews.source}`;
  } catch (error) {
    chatNews = null;
    status.textContent = `Nao foi possivel extrair: ${error.message}. Voce ainda pode perguntar normalmente.`;
  }
}

async function sendChatQuestion(event) {
  event.preventDefault();
  const input = document.getElementById("chat-question");
  const question = input.value.trim();
  if (!chatSessionId || !chatModels.length) {
    try { await initializeChat(); }
    catch (error) { setChatStatus(`API do chat indisponivel: ${error.message}`); return; }
  }
  if (!question || !chatSelectedModels.size || !chatSessionId) return;
  setChatStatus("Enfileirando modelos...");
  try {
    const payload = await chatFetch(`/chat/sessions/${encodeURIComponent(chatSessionId)}/ask`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question, model_ids: [...chatSelectedModels],
        use_memory: Boolean(document.getElementById("chat-use-memory")?.checked),
        news_id: chatNews?.news_id || null,
        news_title: chatNews ? document.getElementById("chat-news-title")?.value.trim() : null,
        news_summary: chatNews ? document.getElementById("chat-news-summary")?.value.trim() : null,
      }),
    });
    input.value = "";
    pollChatBatch(payload.batch_id);
  } catch (error) {
    setChatStatus(`Falha ao enviar: ${error.message}`);
  }
  updateChatSendState();
}

function pollChatBatch(batchId) {
  if (chatPollTimer) clearInterval(chatPollTimer);
  const poll = async () => {
    try {
      const payload = await chatFetch(`/chat/batches/${encodeURIComponent(batchId)}/progress`);
      const batch = payload.batch;
      renderChatTimelineForBatch(payload.messages || [], batch);
      setChatStatus(batch.current_model_id
        ? `${batch.completed_models}/${batch.selected_models.length} concluidos - ${batch.current_model_id}`
        : "Preparando lote...");
      if (["completed", "completed_with_errors", "failed"].includes(batch.status)) {
        clearInterval(chatPollTimer); chatPollTimer = null;
        const session = await chatFetch(`/chat/sessions/${encodeURIComponent(chatSessionId)}`);
        hydrateChat(session);
      }
    } catch (error) {
      clearInterval(chatPollTimer); chatPollTimer = null;
      setChatStatus(`Falha ao acompanhar lote: ${error.message}`);
      updateChatSendState();
    }
  };
  chatPollTimer = setInterval(poll, PROGRESS_POLL_MS);
  poll();
  updateChatSendState();
}

function renderChatTimelineForBatch(messages, batch) {
  const existing = document.querySelector(`[data-chat-batch="${cssEscape(batch.batch_id)}"]`);
  if (existing) existing.remove();
  const wrap = document.createElement("div");
  wrap.dataset.chatBatch = batch.batch_id;
  const answered = new Set(messages.filter((item) => item.model_id).map((item) => item.model_id));
  const pending = (batch.selected_models || []).filter((modelId) => !answered.has(modelId)).map((modelId) => ({
    role: "model", model_id: modelId, content: modelId === batch.current_model_id ? "Modelo respondendo..." : "Aguardando sua vez...",
    status: modelId === batch.current_model_id ? "responding" : "waiting", latency_ms: null,
  }));
  wrap.innerHTML = chatMessagesHtml([...messages, ...pending]);
  document.getElementById("chat-timeline")?.appendChild(wrap);
}

function renderChatTimeline(messages) {
  const container = document.getElementById("chat-timeline");
  if (!container) return;
  container.innerHTML = messages.length ? chatMessagesHtml(messages) : `<div class="chat-empty">Inicie uma conversa sobre a Copa do Mundo.</div>`;
  container.scrollTop = container.scrollHeight;
}

function chatMessagesHtml(messages) {
  return messages.map((message) => {
    const label = message.role === "user" ? "Voce" : message.role === "synthesis" ? "Sintese CopaMind" : message.model_id;
    const meta = message.role === "model" && message.latency_ms != null ? ` - ${Math.round(message.latency_ms)} ms` : "";
    const lists = message.role === "synthesis" ? synthesisListsHtml(message.metadata || {}) : "";
    return `<article class="chat-message role-${escapeAttr(message.role)} status-${escapeAttr(message.status)}">
      <div><strong>${escapeHtml(label || "IA")}</strong><span>${escapeHtml(message.status)}${meta}</span></div>
      <p>${escapeHtml(message.content || "").replaceAll("\n", "<br>")}</p>${lists}</article>`;
  }).join("");
}

function synthesisListsHtml(metadata) {
  return ["consensus", "divergences", "uncertainties", "sources"].map((key) => {
    const values = Array.isArray(metadata[key]) ? metadata[key] : [];
    return values.length ? `<div class="chat-synthesis-list"><strong>${escapeHtml(key)}</strong><ul>${values.map((v) => `<li>${escapeHtml(String(v))}</li>`).join("")}</ul></div>` : "";
  }).join("");
}

async function resetChatSession() {
  if (!chatSessionId || !window.confirm("Resetar somente o historico desta conversa?")) return;
  try {
    await chatFetch(`/chat/sessions/${encodeURIComponent(chatSessionId)}`, { method: "DELETE" });
    localStorage.removeItem("copamind_chat_session");
    chatSessionId = null; chatNews = null;
    document.getElementById("chat-news-url").value = "";
    document.getElementById("chat-news-title").value = "";
    document.getElementById("chat-news-summary").value = "";
    await initializeChat();
  } catch (error) { setChatStatus(`Nao foi possivel resetar: ${error.message}`); }
}

function renderMissingData() {
  document.getElementById("generated-at").textContent = "sem snapshot";
  document.getElementById("phase-tabs").innerHTML = "";
  document.getElementById("matches-list").innerHTML = empty("Snapshot nao encontrado. Rode scripts/export_portal_data.py.");
  document.getElementById("llm-card-grid").innerHTML = "";
}

function renderAll() {
  renderMainNav();
  renderSummary();
  renderPhaseTabs();
  renderPhaseHeader();
  renderMatches();
  renderModels();
  renderRanking();
  renderBenchmark();
  renderLinkedInCaptures();
  renderContextInputs();
  renderTournament();
  renderTeamDashboard();
  renderPlayersDashboard();
  renderGuide();
  renderReferences();
  document.getElementById("generated-at").textContent = `Snapshot: ${formatDateTime(state.generated_at)}`;
}

function renderMainNav() {
  document.querySelectorAll(".main-nav button").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === activeView);
    if (window.COPAMIND_OFFLINE && button.dataset.view === "chat") {
      button.disabled = true;
      button.title = "Chat desativado no modo estático";
    }
  });
  document.querySelectorAll(".view-section").forEach((section) => {
    section.classList.toggle("is-hidden", section.dataset.section !== activeView);
  });
}

function renderSummary() {
  const summary = state.summary || {};
  const sync = state.sync_status || {};
  const modelCount = (state.models || []).filter((model) => !model.is_combo).length;
  const predictions = summary.predictions ?? 0;
  setText("kpi-matches", summary.matches ?? "-");
  setText("kpi-models", modelCount);
  setText("kpi-features", sync.feature_snapshots ?? 0);
  setText("kpi-predictions", predictions);
  setText("kpi-models-home", modelCount);
  setText("kpi-matches-home", summary.matches ?? "-");
  setText("kpi-predictions-home", predictions);
}

function renderPhaseTabs() {
  const phases = state.phases || [];
  document.getElementById("phase-tabs").innerHTML = phases.map((phase) => `
    <button class="${phase.key === activePhase ? "active" : ""}" type="button" data-phase="${escapeAttr(phase.key)}">
      ${escapeHtml(phase.label)}
      <span>${phase.match_count ? phase.match_count + " jogos" : "em breve"}</span>
    </button>
  `).join("");
  document.querySelectorAll("#phase-tabs button").forEach((button) => {
    button.addEventListener("click", () => {
      activePhase = button.dataset.phase;
      renderPhaseTabs();
      renderPhaseHeader();
      renderMatches();
      renderModels();
      recoverLatestBulkProgress().catch(() => {});
    });
  });
}

function renderPhaseHeader() {
  const phase = currentPhase();
  const runOverview = phaseRunOverview(activePhase);
  setText("active-phase-title", phase?.label || phaseLabel(activePhase));
  setText("phase-context", phase?.context || "Dados atuais da FIFA + historico disponivel antes da partida.");
  setText(
    "phase-stats",
    `${phase?.finished_count || 0}/${phase?.match_count || 0} finalizados | `
      + `${phase?.models_count || 0} modelos com palpites`
      + (runOverview ? ` | ${runOverview.valid}/${runOverview.total} LLMs válidas | ${runOverview.invalid} com JSON inválido` : "")
  );
}

function phaseRunOverview(phaseKey) {
  const rows = (state.phase_model_run_status || []).filter((item) => item.phase === phaseKey);
  if (!rows.length) return null;
  return {
    total: rows.length,
    valid: rows.filter((item) => Number(item.valid_runs || 0) > 0).length,
    invalid: rows.filter((item) => Number(item.runs || 0) > 0 && Number(item.valid_runs || 0) === 0).length,
    jsonInvalid: rows.filter((item) => dominantRunIssue(item) === "json_invalid").length,
    lmstudioError: rows.filter((item) => dominantRunIssue(item) === "lmstudio_error").length,
  };
}

function renderMatches() {
  const matches = matchesForPhase(activePhase);
  const featuresByMatch = Object.fromEntries((state.feature_snapshots || []).map((item) => [item.match_id, item]));
  const projected = matches.length ? [] : projectedMatchesForPhase(activePhase, "combo");
  document.getElementById("matches-list").innerHTML = matches.map((match) => matchCard(match, featuresByMatch[match.match_id])).join("")
    || projected.map(projectedMatchCard).join("")
    || empty("Sem jogos cadastrados nesta fase.");
}

function matchCard(match, feature) {
  const score = matchScore(match);
  const markers = matchMarkers(match);
  const baseline = feature?.baseline;
  const baselineText = baseline?.available
    ? `${pct(baseline.prob_home)} / ${pct(baseline.prob_draw)} / ${pct(baseline.prob_away)}`
    : "baseline aguardando historico";
  return `
    <article class="match-card">
      <div class="match-teams">
        ${teamLine(match.home, match.home_flag_url, match.home_score)}
        <div class="versus">${score}</div>
        ${teamLine(match.away, match.away_flag_url, match.away_score)}
      </div>
      <div class="match-meta">
        <span>${formatDateTime(match.date)}</span>
        <span>${statusLabel(match.status)}${markers ? ` | ${escapeHtml(markers)}` : ""}</span>
      </div>
      <div class="baseline-row">
        <span>ML baseline</span>
        <strong>${escapeHtml(baselineText)}</strong>
      </div>
    </article>`;
}

function teamLine(name, flagUrl, score) {
  return `
    <div class="team-line">
      <img src="${escapeAttr(flagUrl || "")}" alt="" />
      <strong>${escapeHtml(name || "A definir")}</strong>
      <span>${score ?? ""}</span>
    </div>`;
}

function renderModels() {
  renderModelActions();
  const scoresByModel = Object.fromEntries(
    (state.phase_model_scores || [])
      .filter((score) => score.phase === activePhase)
      .map((score) => [score.model_id, score])
  );
  const predictionsByModel = Object.fromEntries(
    (state.phase_predictions_by_model || [])
      .filter((item) => item.phase === activePhase)
      .map((item) => [item.model_id, item.predictions || []])
  );
  const runStatusByModel = Object.fromEntries(
    (state.phase_model_run_status || [])
      .filter((item) => item.phase === activePhase)
      .map((item) => [item.model_id, item])
  );
  const cards = (state.models || [])
    .filter((model) => !model.is_combo || scoresByModel[model.model_id] || predictionsByModel[model.model_id])
    .sort((a, b) => {
      const scoreA = scoresByModel[a.model_id] || {};
      const scoreB = scoresByModel[b.model_id] || {};
      return (b.is_combo ? 1 : 0) - (a.is_combo ? 1 : 0)
        || accuracyValue(scoreB) - accuracyValue(scoreA)
        || (scoreB.points || 0) - (scoreA.points || 0)
        || a.display_name.localeCompare(b.display_name);
    });

  // Champion per model (Final predictions)
  const actualChampionId = officialWinnersForPhase("final")[0] ?? null;
  const modelChampionPick = {};
  for (const item of state.phase_predictions_by_model || []) {
    if (item.phase !== "final" || item.model_id === "combo") continue;
    for (const pred of item.predictions || []) {
      const side = predictedSide(pred);
      if (!side) continue;
      const tid = side === "away" ? pred.away_team_id : pred.home_team_id;
      if (tid) modelChampionPick[item.model_id] = tid;
    }
  }

  document.getElementById("llm-card-grid").innerHTML = cards.map((model) => {
    const isChampionHit = actualChampionId != null && modelChampionPick[model.model_id] === actualChampionId;
    return modelCard(
      model,
      scoresByModel[model.model_id],
      modelRowsForPhase(
        activePhase,
        model.model_id,
        predictionsByModel[model.model_id] || [],
        runStatusByModel[model.model_id]
      ),
      runStatusByModel[model.model_id],
      isChampionHit,
    );
  }).join("") || empty("Sem palpites nesta fase. Use o Admin para processar a fase com LLMs e exporte o snapshot.");
  document.querySelectorAll("[data-run-model]").forEach((button) => {
    button.addEventListener("click", () => runModelPhase(button.dataset.runModel));
  });
  document.querySelectorAll("[data-reset-model]").forEach((button) => {
    button.addEventListener("click", () => resetLLMHistory({ phase: activePhase, modelId: button.dataset.resetModel }));
  });
}

function renderModelActions() {
  if (window.COPAMIND_OFFLINE) {
    document.getElementById("model-actions").innerHTML = `
      <div class="model-actions-main offline-notice">
        <span>🔒 Modo estático — controles de execução desativados</span>
      </div>`;
    return;
  }
  const canRunAll = canRunAllModelsForPhase();
  const phase = currentPhase();
  const pendingResults = pendingPhaseMatches(activePhase).length;
  const projected = projectedMatchesForPhase(activePhase, "combo").length;
  const bulkRun = runningRuns.get(runKey(activePhase, "__all__"));
  const runOverview = phaseRunOverview(activePhase);
  const gaps = phaseExecutionGaps(activePhase);
  const isSeq = Boolean(sequentialBatch && !sequentialBatch.aborted && sequentialBatch.phase === activePhase);
  const runButtonLabel = isSeq
    ? `Modelo ${sequentialBatch.current}/${sequentialBatch.total}: ${sequentialBatch.currentModelId || ""}`
    : bulkRun
      ? "Executando fase..."
      : gaps.missingCalls
        ? "Executar LLMs faltantes"
        : runOverview?.invalid
          ? "Tudo processado (há erros)"
        : "Executar todas as LLMs da fase";
  const runHint = canRunAll
    ? gaps.missingCalls
      ? `Executa ${gaps.missingCalls} chamadas ainda nao processadas em ${phase?.label || phaseLabel(activePhase)}.`
      : `Executa todos os modelos ativos para ${phase?.label || phaseLabel(activePhase)}.`
    : runOverview?.invalid
      ? "Tudo ja foi processado. Para tentar novamente os modelos com erro, use Reset modelo ou Reset fase."
      : "Disponivel quando houver jogos oficiais, chamadas faltantes ou chave projetada.";
  const statusBits = [`${pendingResults} jogos sem resultado oficial`, `${projected} projetados`];
  if (gaps.missingCalls) statusBits.push(`${gaps.missingCalls} chamadas nao processadas`);
  if (runOverview) {
    statusBits.push(`${runOverview.valid}/${runOverview.total} LLMs válidas`);
    if (runOverview.jsonInvalid) statusBits.push(`${runOverview.jsonInvalid} com JSON inválido`);
    if (runOverview.lmstudioError) statusBits.push(`${runOverview.lmstudioError} com erro LM Studio`);
  }
  document.getElementById("model-actions").innerHTML = `
    <div class="model-actions-main">
      <div>
        <strong>Controle do agente</strong>
        <span>${escapeHtml(statusBits.join(" | "))}</span>
      </div>
      ${isSeq && sequentialBatch.progress ? bulkProgressPanel(sequentialBatch.progress) : ""}
      ${!isSeq && bulkRun?.progress ? bulkProgressPanel(bulkRun.progress) : ""}
    </div>
    <div class="model-action-buttons">
      <button type="button" id="run-all-models" ${canRunAll && !bulkRun && !isSeq ? "" : "disabled"} title="${escapeAttr(runHint)}">
        ${escapeHtml(runButtonLabel)}
      </button>
      ${isSeq ? `<button type="button" id="cancel-sequential" class="danger-button" title="Interrompe após o modelo atual terminar.">Cancelar</button>` : ""}
      <button type="button" id="reset-phase-history" title="Limpa chamadas e palpites das LLMs nesta fase.">
        Reset fase
      </button>
      <button type="button" id="reset-all-history" class="danger-button" title="Limpa todo o historico de chamadas/palpites das LLMs.">
        Reset geral
      </button>
    </div>`;
  document.getElementById("run-all-models").addEventListener("click", runAllModelsForPhase);
  document.getElementById("cancel-sequential")?.addEventListener("click", cancelSequentialBatch);
  document.getElementById("reset-phase-history").addEventListener("click", () => resetLLMHistory({ phase: activePhase }));
  document.getElementById("reset-all-history").addEventListener("click", () => resetLLMHistory({}));
}

const DISQUALIFIED_MODELS = {
  "mistralai/mistral-7b-instruct-v0.3": "Desclassificado — Channel Error no llama.cpp ao gerar saída estruturada. Sem Structured Output, não obedecia o contrato JSON do bolão. Removido para não contaminar o ranking com dados inválidos.",
};

const STRUCTURED_OUTPUT_MODELS = new Set([
  "glm-4.7-flash",
  "nemotron-3-nano-4b",
  "nemotron-3-nano-omni",
  "olmo-3-32b-think",
  "qwen3.5-9b",
  "qwen3.6-27b",
  "qwen3.6-35b-a3b",
]);

function needsStructuredOutput(modelId) {
  const id = (modelId || "").toLowerCase();
  return [...STRUCTURED_OUTPUT_MODELS].some((key) => id.includes(key));
}

function modelCard(model, score, predictions, runStatus, isChampionHit = false) {
  const telemetry = model.telemetry || {};
  const accuracy = score?.accuracy == null ? null : Math.round(score.accuracy * 100);
  const exactRate = score?.exact_rate == null ? null : score.exact_rate;
  const precision = (accuracy != null && accuracy > 0 && exactRate != null)
    ? Math.round((exactRate / score.accuracy) * 100)
    : null;
  const jsonRate = telemetry.json_rate == null ? "-" : `${Math.round(telemetry.json_rate * 100)}%`;
  const fallbackAvatar = avatarForModel(model);
  const avatar = resolveModelImage(model) || fallbackAvatar;
  const phaseRunLabel = phaseRunSummary(score, predictions, runStatus);
  const disqualifiedReason = DISQUALIFIED_MODELS[model.model_id];
  return `
    <article class="llm-card ${model.is_combo ? "combo-card" : ""} ${disqualifiedReason ? "disqualified-card" : ""} ${isChampionHit ? "llm-card--champion-hit" : ""}">
      ${isChampionHit ? `<div class="champion-banner">🏆 Acertou o campeão!</div>` : ""}
      ${disqualifiedReason ? `<div class="disqualified-banner">🚫 ${escapeHtml(disqualifiedReason)}</div>` : ""}
      <div class="llm-card-head">
        <img class="model-avatar" src="${escapeAttr(avatar)}" alt="" onerror="this.onerror=null;this.src='${escapeAttr(fallbackAvatar)}';" />
        <div class="llm-title">
          <strong title="${escapeAttr(model.model_id)}">${escapeHtml(model.display_name || model.model_id)}</strong>
          <span>${escapeHtml(model.family || "local")} | ${escapeHtml(model.model_class || "chat")} | ${escapeHtml(phaseRunLabel)}</span>
          ${needsStructuredOutput(model.model_id) ? `<span class="struct-output-badge" title="Necessita Structured Output ativado no LM Studio para gerar JSON valido. Menos maleavel — exige mais refinamento de configuracao.">⚠ Struct. Output</span>` : ""}
        </div>
        <div class="accuracy-score">
          <strong>${accuracy == null ? "Aguardando" : `${accuracy}%`}</strong>
          <span>${accuracy == null ? "resultado" : "assertividade"}</span>
          ${precision != null ? `<strong class="precision-score">${precision}%</strong><span>precisao nos acertos</span>` : ""}
        </div>
      </div>
      <div class="llm-metrics">
        <div><span>Pontos</span><strong>${score?.points ?? 0}</strong></div>
        <div><span>LM Studio</span><strong>${model.available === false ? "offline" : "ativo"}</strong></div>
        <div><span>JSON válido</span><strong>${jsonRate}</strong></div>
        <div><span>Lat. média</span><strong>${num(telemetry.avg_latency_ms, 0)} ms</strong></div>
        <div><span>Tokens/s</span><strong>${num(telemetry.avg_tokens_per_second, 1)}</strong></div>
        <div><span>Brier fase</span><strong>${score?.brier_avg == null ? "aguarda" : num(score.brier_avg, 3)}</strong></div>
        <div><span>Rodadas</span><strong>${telemetry.rounds ?? 0}</strong></div>
      </div>
      ${disqualifiedReason
        ? `<div class="disqualified-no-action">Modelo fora da competição — sem execução no pipeline</div>`
        : model.is_combo ? "" : modelActionRow(model)}
      <div class="prediction-list">
        ${model.is_combo
          ? comboConsensusBlock(activePhase, predictions)
          : predictions.map(predictionRow).join("") || emptyPrediction("Sem palpites nesta fase.")}
      </div>
    </article>`;
}

function phaseRunSummary(score, predictions, runStatus) {
  const runs = Number(runStatus?.runs || 0);
  if (runs) {
    const valid = Number(runStatus?.valid_runs || 0);
    const invalid = runIssueSummary(runStatus);
    return `${valid}/${runs} JSON válidos${invalid ? ` | ${invalid}` : ""}`;
  }
  const predicted = Number(score?.predictions || predictions.filter((item) => item.has_prediction !== false).length || 0);
  if (predicted) return `${predicted} palpites`;
  return `${predictions.length || 0} jogos`;
}

function runIssueSummary(runStatus) {
  const counts = runStatus?.error_counts || {};
  const pieces = [];
  if (counts.lmstudio_error) pieces.push(`${counts.lmstudio_error} erro LM Studio`);
  if (counts.json_invalid) pieces.push(`${counts.json_invalid} JSON inválido`);
  if (counts.context_error) pieces.push(`${counts.context_error} contexto/tokens`);
  const other = Number(counts.other_error || 0);
  if (other) pieces.push(`${other} outros erros`);
  return pieces.join(" | ");
}

function dominantRunIssue(runStatus) {
  const counts = runStatus?.error_counts || {};
  const entries = Object.entries(counts).sort((a, b) => Number(b[1]) - Number(a[1]));
  return entries[0]?.[0] || (Number(runStatus?.invalid_runs || 0) ? "json_invalid" : "");
}

function modelActionRow(model) {
  return `
    <div class="card-action-row">
      ${runModelButton(model)}
      <button
        class="reset-model-button"
        type="button"
        data-reset-model="${escapeAttr(model.model_id)}"
        title="Limpa chamadas, rodadas e palpites deste modelo nesta fase."
      >
        Reset modelo
      </button>
    </div>`;
}

function runModelButton(model) {
  const phase = currentPhase();
  const officialMatches = matchesForPhase(activePhase).length;
  const projectedMatches = projectedMatchesForPhase(activePhase, model.model_id).length;
  const canRun = officialMatches > 0 || projectedMatches > 0;
  const running = runningRuns.has(runKey(activePhase, model.model_id));
  const label = running ? "Rodando... atualizando" : canRun ? "Executar IA nesta fase" : "Aguardando chave";
  return `
    <button
      class="run-model-button ${running ? "is-running" : ""}"
      type="button"
      data-run-model="${escapeAttr(model.model_id)}"
      ${canRun && !running ? "" : "disabled"}
      title="${canRun ? "Dispara o agente local via API CopaMind. Em fases sem chave oficial, usa confronto projetado." : "Ainda nao ha dados suficientes para projetar esta fase."}"
    >
      ${escapeHtml(label)}
    </button>`;
}

function renderRanking() {
  if (!state) return;
  renderRankingSummary();
  renderRankingTable();
  renderPhaseScoreboard();
  renderWinnerForecast();
  renderTeamTitleRanking();
}

function renderRankingSummary() {
  const rows = rankingRows();
  const scored = rows.filter((row) => row.scored > 0).length;
  const votes = allValidPredictions().length;
  const best = rows.find((row) => row.scored > 0);
  document.getElementById("ranking-summary").innerHTML = `
    <div><span>Modelos</span><strong>${rows.filter((row) => !row.is_combo).length}</strong></div>
    <div><span>Com score</span><strong>${scored}</strong></div>
    <div><span>Palpites LLM</span><strong>${votes}</strong></div>
    <div><span>Lider</span><strong>${escapeHtml(best?.display_name || "Aguardando")}</strong></div>`;
}

function renderRankingTable() {
  const rows = rankingRows();
  const phases = (state.phases || []).filter((p) => p.key !== "group");
  document.getElementById("ranking-table").innerHTML = `
    <div class="ranking-table">
      <div class="ranking-table-head">
        <span>#</span><span></span><span>Modelo</span><span title="Pontos efetivos = pts brutos − 1pt por cada vencedor errado. Tooltip na célula mostra o detalhe.">Pts Efetivos</span><span>Acerto</span><span>Jogos</span><span>JSON</span><span>Lat.</span><span>Tok/s</span><span>Brier</span>
      </div>
      ${rows.map((row, index) => {
        const imgSrc = escapeAttr(resolveModelImage(row) || avatarForModel(row));
        const fallback = escapeAttr(avatarForModel(row));
        const phaseDetail = phases
          .filter((p) => row.phase_scores[p.key]?.points > 0 || row.phase_scores[p.key]?.scored > 0)
          .map((p) => {
            const s = row.phase_scores[p.key];
            return s ? `<em>${escapeHtml(p.label)}: <b>${s.points}pts</b>${s.scored ? ` ${pct(s.accuracy)}` : ""}</em>` : "";
          }).join("  ");
        return `
        <div class="ranking-table-row ${row.is_combo ? "combo-row" : ""}">
          <span>${index + 1}</span>
          <img class="row-model-icon" src="${imgSrc}" alt="" onerror="this.onerror=null;this.src='${fallback}';" />
          <strong title="${escapeAttr(row.model_id)}">${escapeHtml(row.display_name)}</strong>
          <span class="pts-cell" title="${row.wrong > 0 ? `${row.points} pts brutos − ${row.wrong} erro(s) = ${row.net_score} pts efetivos` : `${row.points} pts — sem erros penalizados`}">
            <b>${row.net_score}</b>
            ${phaseDetail ? `<small class="pts-phases">${phaseDetail}</small>` : ""}
            ${row.wrong > 0 ? `<small class="pts-penalty">−${row.wrong} erro${row.wrong > 1 ? "s" : ""}</small>` : ""}
          </span>
          <span>${row.scored ? pct(row.accuracy) : "aguarda"}</span>
          <span>${row.scored || row.predictions}</span>
          <span>${row.json_rate == null ? "-" : `${Math.round(row.json_rate * 100)}%`}</span>
          <span>${num(row.avg_latency_ms, 0)} ms</span>
          <span>${num(row.avg_tokens_per_second, 1)}</span>
          <span>${row.brier_avg == null ? "-" : num(row.brier_avg, 3)}</span>
        </div>`;
      }).join("")}
    </div>`;
}

function renderPhaseScoreboard() {
  const rows = rankingRows().slice(0, 18);
  const phases = state.phases || [];
  document.getElementById("phase-scoreboard").innerHTML = `
    <div class="phase-score-grid">
      ${rows.map((row) => `
        <article class="phase-score-card">
          <strong title="${escapeAttr(row.model_id)}">${escapeHtml(row.display_name)}</strong>
          <div>
            ${phases.map((phase) => {
              const score = row.phase_scores[phase.key];
              return `
                <span>
                  <em>${escapeHtml(phase.label)}</em>
                  <b>${score ? `${score.points} pts` : "-"}</b>
                  <small>${score?.scored ? pct(score.accuracy) : "aguarda"}</small>
                </span>`;
            }).join("")}
          </div>
        </article>
      `).join("") || empty("Aguardando modelos.")}
    </div>`;
}

function renderWinnerForecast() {
  const phases = ["quarterfinal", "semifinal", "third_place", "final"];
  document.getElementById("winner-forecast").innerHTML = `
    <div class="winner-forecast-list">
      ${phases.map((phase) => forecastPhaseCard(phase)).join("")}
    </div>`;
}

function forecastPhaseCard(phase) {
  const allVotes = winnerVotesForPhase(phase);
  const votes = allVotes.slice(0, 5);
  const voteTotal = allVotes.reduce((sum, row) => sum + row.votes, 0);
  const officialWinners = officialWinnersForPhase(phase);
  return `
    <article class="forecast-card">
      <div>
        <strong>${escapeHtml(phaseLabel(phase))}</strong>
        <span>${officialWinners.length ? `${officialWinners.length} classificados reais` : `top ${votes.length} de ${voteTotal} votos LLM`}</span>
      </div>
      ${votes.map((row) => teamVoteLine(row, officialWinners)).join("") || emptyPrediction("Aguardando palpites da fase.")}
    </article>`;
}

function renderTeamTitleRanking() {
  const rows = teamTitleRows().slice(0, 16);
  document.getElementById("team-title-ranking").innerHTML = `
    <div class="team-title-list">
      ${rows.map((row, index) => `
        <div class="team-title-row ${row.eliminated ? "is-eliminated" : ""}">
          <span>${index + 1}</span>
          <img src="${escapeAttr(row.flag_url || "")}" alt="" />
          <strong>${escapeHtml(row.name)}</strong>
          <em>${escapeHtml(row.status)}</em>
          <b>${pct(row.chance)}</b>
          <small>${row.votes} votos | perfil ${pct(row.profile)}</small>
        </div>
      `).join("")}
    </div>`;
}

function rankingRows() {
  const phaseScores = state.phase_model_scores || [];
  const scoreMap = {};
  for (const score of phaseScores) {
    const id = String(score.model_id);
    scoreMap[id] ||= {};
    scoreMap[id][score.phase] = score;
  }
  return (state.models || [])
    .map((model) => {
      const phases = scoreMap[model.model_id] || {};
      const phaseList = Object.values(phases);
      const scored = phaseList.reduce((sum, item) => sum + Number(item.scored || 0), 0);
      const points = phaseList.reduce((sum, item) => sum + Number(item.points || 0), 0);
      const weightedAccuracy = scored
        ? phaseList.reduce((sum, item) => sum + Number(item.accuracy || 0) * Number(item.scored || 0), 0) / scored
        : null;
      const brierValues = phaseList.map((item) => item.brier_avg).filter((value) => value != null);
      const brier = brierValues.length
        ? brierValues.reduce((sum, value) => sum + Number(value), 0) / brierValues.length
        : null;
      const winnerHits = phaseList.reduce((sum, item) => sum + Number(item.winner_hits || 0), 0);
      const wrong = scored - winnerHits;          // previsões com vencedor errado
      const netScore = points - wrong;             // penalidade: -1pt por erro
      return {
        model_id: model.model_id,
        display_name: model.display_name || model.model_id,
        image_url: model.image_url || "",
        family: model.family || "",
        is_combo: Boolean(model.is_combo),
        points,
        net_score: netScore,
        wrong,
        scored,
        predictions: phaseList.reduce((sum, item) => sum + Number(item.predictions || 0), 0),
        accuracy: weightedAccuracy,
        brier_avg: brier,
        exact: phaseList.reduce((sum, item) => sum + Number(item.exact_hits || 0), 0),
        json_rate: model.telemetry?.json_rate,
        avg_latency_ms: model.telemetry?.avg_latency_ms,
        avg_tokens_per_second: model.telemetry?.avg_tokens_per_second,
        phase_scores: phases,
      };
    })
    .sort((a, b) => (
      Number(b.is_combo) - Number(a.is_combo)
      || accuracySortValue(b.accuracy) - accuracySortValue(a.accuracy)   // acerto% = critério principal
      || (b.net_score || 0) - (a.net_score || 0)                          // pts efetivos (desempate)
      || b.points - a.points
      || b.exact - a.exact
      || brierSortValue(a.brier_avg) - brierSortValue(b.brier_avg)
      || a.display_name.localeCompare(b.display_name)
    ));
}

function allValidPredictions() {
  return (state.phase_predictions_by_model || [])
    .flatMap((item) => (item.predictions || []).map((prediction) => ({
      ...prediction,
      model_id: item.model_id,
    })))
    .filter((prediction) => prediction.has_prediction !== false);
}

function renderBenchmark() {
  if (!state) return;
  const rows = benchmarkRows();
  renderBenchmarkSummary(rows);
  renderBenchmarkTable(rows);
  renderBenchmarkGuidance(rows);
  renderBenchmarkCharts();
}

function renderBenchmarkSummary(rows) {
  const currentRows = rows.filter((row) => !row.archived);
  const runs = currentRows.reduce((sum, row) => sum + row.runs, 0);
  const valid = currentRows.reduce((sum, row) => sum + row.valid_runs, 0);
  const invalid = currentRows.reduce((sum, row) => sum + row.invalid_runs, 0);
  const best = currentRows.find((row) => row.runs > 0);
  const fastest = currentRows
    .filter((row) => row.avg_tokens_per_second != null)
    .sort((a, b) => b.avg_tokens_per_second - a.avg_tokens_per_second)[0];
  document.getElementById("benchmark-summary").innerHTML = `
    <div><span>Modelos atuais</span><strong>${currentRows.length}</strong></div>
    <div><span>Chamadas</span><strong>${runs}</strong></div>
    <div><span>JSON valido</span><strong>${runs ? Math.round(valid / runs * 100) : 0}%</strong></div>
    <div><span>Invalidas</span><strong>${invalid}</strong></div>
    <div><span>Melhor benchmark</span><strong>${escapeHtml(best?.display_name || "Aguardando")}</strong></div>
    <div><span>Mais rapido</span><strong>${escapeHtml(fastest?.display_name || "Aguardando")}</strong></div>`;
}

function renderBenchmarkTable(rows) {
  document.getElementById("benchmark-table").innerHTML = `
    <div class="benchmark-table">
      <div class="benchmark-table-head">
        <span>#</span><span></span><span>Modelo</span><span>Bench</span><span>Bolao</span><span>JSON</span><span>Chamadas</span><span>Lat.</span><span>Tok/s</span><span>Uso</span><span>Orientacao</span>
      </div>
      ${rows.map((row, index) => {
        const imgSrc = escapeAttr(resolveModelImage(row) || avatarForModel(row));
        const fallback = escapeAttr(avatarForModel(row));
        return `
        <div class="benchmark-table-row ${row.archived ? "archived-row" : ""}">
          <span>${index + 1}</span>
          <img class="row-model-icon" src="${imgSrc}" alt="" onerror="this.onerror=null;this.src='${fallback}';" />
          <strong title="${escapeAttr(row.model_id)}">${escapeHtml(row.display_name)}</strong>
          <b>${num(row.benchmark_score, 0)}</b>
          <span>${row.scored ? `${row.points} pts / ${pct(row.accuracy)}` : "sem score"}</span>
          <span>${row.runs ? `${Math.round(row.json_rate * 100)}%` : "-"}</span>
          <span>${row.valid_runs}/${row.runs}</span>
          <span>${num(row.avg_latency_ms, 0)} ms</span>
          <span>${num(row.avg_tokens_per_second, 1)}</span>
          <em>${escapeHtml(row.ease_label)}</em>
          <small>${escapeHtml(row.recommendation)}</small>
        </div>`;
      }).join("") || empty("Sem dados de benchmark ainda. Rode uma fase com LLMs e exporte o snapshot.")}
    </div>`;
}

function renderBenchmarkGuidance(rows) {
  const invalidRows = rows.filter((row) => row.invalid_runs > 0 && !row.archived);
  const jsonInvalid = invalidRows.filter((row) => row.dominant_issue === "json_invalid").length;
  const lmstudioError = invalidRows.filter((row) => row.dominant_issue === "lmstudio_error").length;
  const contextError = invalidRows.filter((row) => row.dominant_issue === "context_error").length;
  document.getElementById("benchmark-guidance").innerHTML = `
    <div class="benchmark-issue-grid">
      <div><span>JSON/schema</span><strong>${jsonInvalid}</strong></div>
      <div><span>LM Studio</span><strong>${lmstudioError}</strong></div>
      <div><span>Contexto</span><strong>${contextError}</strong></div>
    </div>
    <article>
      <h4>Perfil de teste recomendado</h4>
      <p>Para os modelos que nao obedecem JSON: Temperature 0.0-0.2, Top P 0.80-0.90, Top K 10-20, Structured Output ligado quando o modelo aceitar, Preserve Thinking desligado e Reasoning Parsing ligado somente para modelos que usam &lt;think&gt;.</p>
    </article>
    <article>
      <h4>Como comparar de forma justa</h4>
      <p>Rode o mesmo jogo/fase com todos os modelos, samples = 1, mesma temperatura do agente e depois uma rodada retry-invalidos com o perfil JSON. O benchmark final deve guardar a configuracao usada em cada rodada.</p>
    </article>
    <article>
      <h4>O que a nota mede</h4>
      <p>Ela combina score do bolao, taxa de JSON valido, velocidade, latencia e disponibilidade. Assim um modelo pode ser bom no palpite, mas perder pontos se for dificil de operar.</p>
    </article>
    <article class="hardware-method-note">
      <h4>CPU/offload × acurácia</h4>
      <p><strong>CPU afeta diretamente velocidade e latência, não a capacidade lógica do modelo.</strong> A acurácia só pode ser afetada indiretamente quando o limite local provoca timeout, truncamento, contexto menor, quantização diferente ou raciocínio interrompido. Por isso, o ranking não penaliza acertos apenas por um modelo usar CPU.</p>
    </article>`;
}

function svgHBar({ rows, getValue, title, color, unit = "", labelW = 170, barZoneW = 270, barH = 20, gap = 5 }) {
  const n = rows.length;
  if (!n) return `<p class="bench-chart-empty">Sem dados suficientes</p>`;
  const W = labelW + barZoneW + 72;
  const H = 34 + n * (barH + gap);
  const vals = rows.map(getValue).filter((v) => v != null && !isNaN(v));
  const maxV = vals.length ? Math.max(...vals, 0.001) : 1;
  const items = rows.map((row, i) => {
    const v = getValue(row);
    const valid = v != null && !isNaN(v) && v >= 0;
    const bw = valid ? Math.round((v / maxV) * barZoneW) : 0;
    const y = 30 + i * (barH + gap);
    const label = (row.display_name || row.model_id || "").slice(0, 24);
    const valStr = valid ? (v % 1 === 0 ? String(Math.round(v)) : v.toFixed(1)) + unit : "—";
    const op = row.archived ? 0.3 : 1;
    return `
      <text x="${labelW - 6}" y="${y + barH - 5}" text-anchor="end" font-family="system-ui,ui-sans-serif,sans-serif" font-size="11" fill="#9aa8b8" opacity="${op}">${escapeHtml(label)}</text>
      <rect x="${labelW}" y="${y}" width="${Math.max(bw, valid ? 3 : 0)}" height="${barH}" fill="${color}" rx="3" opacity="${op * 0.82}" />
      <text x="${labelW + Math.max(bw, 0) + 7}" y="${y + barH - 5}" font-family="system-ui,ui-sans-serif,sans-serif" font-size="11" font-weight="700" fill="#dce8f5" opacity="${op}">${valStr}</text>`;
  }).join("");
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" style="max-width:100%">
    <text x="${labelW}" y="16" font-family="system-ui,ui-sans-serif,sans-serif" font-size="10" font-weight="900" fill="#6a8aa8" letter-spacing="1.2">${escapeHtml(title.toUpperCase())}</text>
    ${items}
  </svg>`;
}

function metricCell(value, max, { format = (v) => num(v, 0), inverse = false } = {}) {
  if (value == null || Number.isNaN(Number(value))) return `<div class="metric-cell is-empty"><span>—</span></div>`;
  const ratio = Math.max(0, Math.min(1, Number(value) / Math.max(Number(max), 0.001)));
  const quality = inverse ? 1 - ratio : ratio;
  return `<div class="metric-cell" style="--metric:${Math.round(quality * 100)}%">
    <i style="width:${Math.max(4, Math.round(quality * 100))}%"></i><strong>${format(Number(value))}</strong>
  </div>`;
}

function renderBenchmarkCharts() {
  const container = document.getElementById("benchmark-charts");
  if (!container) return;
  const active = benchmarkRows().filter((r) => !r.archived && (r.runs > 0 || r.scored > 0));
  if (!active.length) { container.innerHTML = ""; return; }
  const rows = active.slice().sort((a, b) => b.benchmark_score - a.benchmark_score);
  const maxPoints = Math.max(...rows.map((r) => r.points || 0), 1);
  const maxSpeed = Math.max(...rows.map((r) => r.avg_tokens_per_second || 0), 1);
  const maxBrier = Math.max(...rows.map((r) => r.brier_avg || 0), 1);
  container.innerHTML = `
    <div class="bench-dashboard-head">
      <div class="section-title bench-charts-title">
        <p>Estatisticas de execucao</p>
        <h3>Painel comparativo consolidado</h3>
        <span>${rows.length} modelos avaliados. Barras mais longas indicam melhor desempenho.</span>
      </div>
      <button id="btn-export-benchmark-dashboard" class="btn-export-table" type="button">📸 Exportar quadro completo</button>
    </div>
    <aside class="structured-output-callout">
      <span class="structured-output-icon">{ }</span>
      <div><strong>Structured Output · JSON Schema</strong>
      <p><b>Advanced:</b> you can provide a JSON Schema to enforce a particular output format from the model. Read the documentation to learn more.</p></div>
      <em>${rows.filter((row) => row.invalid_runs > 0).length} modelos exigiram ajuste no LM Studio <span title="Modelos que precisaram de ajuste de configuracao recebem penalizacao de usabilidade no Score do Benchmark (-8 pts). O Ranking das LLMs é independente: pontos do bolao nao sofrem esta penalizacao.">⚠ penaliza benchmark</span></em>
    </aside>
    <div class="benchmark-matrix-wrap"><div class="benchmark-matrix">
      <div class="benchmark-matrix-head"><span>Modelo</span><span title="Usabilidade (JSON+facilidade) 45% · Acertividade 30% · Performance 20% · Disponib. 5% — NÃO inclui pontos do bolão (ver Ranking das LLMs)">Score Benchmark</span><span title="Pontos do Bolão (ver Ranking das LLMs) — referência apenas, NÃO compõe o Score Benchmark">Pontos Bolão ↗</span><span class="json-head">JSON válido<small>Structured Output</small></span><span>Acerto %</span><span>Velocidade</span><span>Brier ↓</span><span>Capacidade</span></div>
      ${rows.map((row, index) => `<div class="benchmark-matrix-row">
        <div class="matrix-model"><b>${index + 1}</b><img src="${escapeAttr(resolveModelImage(row) || avatarForModel(row))}" alt=""><span><strong>${escapeHtml(row.display_name)}</strong><small>${row.runs} execuções</small></span></div>
        ${metricCell(row.benchmark_score, 100)}
        ${metricCell(row.points, maxPoints, { format: (v) => `${num(v, 0)} pts` })}
        <div class="json-metric-wrap">${metricCell(row.json_rate == null ? null : row.json_rate * 100, 100, { format: (v) => `${num(v, 0)}%` })}<small class="schema-status ${row.invalid_runs > 0 ? "was-adjusted" : ""}">${row.invalid_runs > 0 ? `↻ Ajustado no LM Studio · ${row.invalid_runs} falha${row.invalid_runs === 1 ? "" : "s"}` : "✓ Schema aplicado"}</small></div>
        ${metricCell(row.accuracy == null ? null : row.accuracy * 100, 100, { format: (v) => `${num(v, 0)}%` })}
        ${metricCell(row.avg_tokens_per_second, maxSpeed, { format: (v) => `${num(v, 1)} tok/s` })}
        ${metricCell(row.brier_avg, maxBrier, { inverse: true, format: (v) => num(v, 3) })}
        <span class="capability-pill ${/omni|vision|vl/i.test(row.model_id) ? "is-visual" : ""}">${/omni|vision|vl/i.test(row.model_id) ? "◉ Visão" : "Texto"}</span>
      </div>`).join("")}
      <div class="benchmark-matrix-row image-model-row">
        <div class="matrix-model"><b>+</b><span class="image-model-icon">✦</span><span><strong>FLUX.1-dev</strong><small>modelo visual de referência</small></span></div>
        <div class="matrix-na">fora do benchmark</div><div class="matrix-na">—</div><div class="matrix-na">—</div><div class="matrix-na">—</div><div class="matrix-na">—</div><div class="matrix-na">—</div>
        <span class="capability-pill is-generator">✦ Gera imagem</span>
      </div>
    </div></div>`;
  document.getElementById("btn-export-benchmark-dashboard")?.addEventListener("click", exportBenchmarkDashboardImage);
}

function benchmarkRows() {
  const scoreRows = rankingRows().filter((row) => !row.is_combo);
  const scoreByModel = Object.fromEntries(scoreRows.map((row) => [row.model_id, row]));
  const modelById = Object.fromEntries((state.models || [])
    .filter((model) => !model.is_combo)
    .map((model) => [model.model_id, model]));
  const runGroups = {};
  for (const run of state.llm?.runs || []) {
    const modelId = String(run.model_id || "");
    if (!modelId || modelId === "combo") continue;
    const group = runGroups[modelId] ||= {
      runs: 0,
      valid_runs: 0,
      invalid_runs: 0,
      latency_values: [],
      speed_values: [],
      prompt_tokens: [],
      completion_tokens: [],
      errors: {},
    };
    group.runs += 1;
    if (run.valid) group.valid_runs += 1;
    else {
      group.invalid_runs += 1;
      const issue = runErrorType(run.error || "");
      group.errors[issue] = (group.errors[issue] || 0) + 1;
    }
    if (run.latency_ms != null) group.latency_values.push(Number(run.latency_ms));
    if (run.prompt_tokens != null) group.prompt_tokens.push(Number(run.prompt_tokens));
    if (run.completion_tokens != null) {
      group.completion_tokens.push(Number(run.completion_tokens));
      if (Number(run.latency_ms) > 0) {
        group.speed_values.push(Number(run.completion_tokens) / (Number(run.latency_ms) / 1000));
      }
    }
  }
  const ids = new Set([...Object.keys(modelById), ...Object.keys(runGroups), ...Object.keys(scoreByModel)]);
  return [...ids].map((modelId) => {
    const model = modelById[modelId] || {};
    const score = scoreByModel[modelId] || {};
    const runs = runGroups[modelId] || {};
    const validRuns = Number(runs.valid_runs || model.telemetry?.valid_runs || 0);
    const totalRuns = Number(runs.runs || model.telemetry?.runs || 0);
    const invalidRuns = Math.max(0, totalRuns - validRuns);
    const jsonRate = totalRuns ? validRuns / totalRuns : null;
    const speed = avg(runs.speed_values) ?? model.telemetry?.avg_tokens_per_second ?? null;
    const latency = avg(runs.latency_values) ?? model.telemetry?.avg_latency_ms ?? null;
    const dominantIssueValue = dominantIssueFromCounts(runs.errors || {});
    const row = {
      model_id: modelId,
      display_name: model.display_name || score.display_name || modelId,
      image_url: model.image_url || "",
      family: model.family || "",
      archived: !modelById[modelId],
      available: model.available !== false,
      points: Number(score.points || 0),
      scored: Number(score.scored || 0),
      accuracy: score.accuracy ?? null,
      brier_avg: score.brier_avg ?? null,
      runs: totalRuns,
      valid_runs: validRuns,
      invalid_runs: invalidRuns,
      json_rate: jsonRate,
      avg_latency_ms: latency,
      avg_tokens_per_second: speed,
      avg_prompt_tokens: avg(runs.prompt_tokens),
      avg_completion_tokens: avg(runs.completion_tokens),
      dominant_issue: dominantIssueValue,
    };
    row.benchmark_score = benchmarkScore(row);
    row.ease_label = easeLabel(row);
    row.recommendation = recommendationForBenchmark(row);
    return row;
  }).sort((a, b) => (
    b.benchmark_score - a.benchmark_score
    || Number(b.json_rate || 0) - Number(a.json_rate || 0)
    || b.points - a.points
    || a.display_name.localeCompare(b.display_name)
  ));
}

function benchmarkScore(row) {
  if (!row.runs && !row.scored) return 0;

  // ── Usabilidade (0–45) ────────────────────────────────────────────────────
  // JSON válido: 0-30
  const json = row.json_rate == null ? 0 : row.json_rate * 30;
  // Facilidade de configuração: 15 = pronto sem ajuste | 7 = precisou ⚠ ajuste | 0 = instável
  const noAdjust = row.invalid_runs === 0 && row.runs > 0;
  const goodWithAdjust = !noAdjust && (row.json_rate ?? 0) >= 0.7;
  const ease = noAdjust ? 15 : goodWithAdjust ? 7 : 0;

  // ── Acertividade (0–30) ───────────────────────────────────────────────────
  // % de vencedores corretos (accuracy)
  const accuracy = row.accuracy == null ? 0 : row.accuracy * 30;

  // ── Performance técnica (0–20) ────────────────────────────────────────────
  // Velocidade (tok/s): 0-15
  const speed = row.avg_tokens_per_second == null ? 0 : Math.min(15, row.avg_tokens_per_second * 0.75);
  // Latência (inversamente): 0-5
  const latency = row.avg_latency_ms == null ? 0 : Math.max(0, 5 - row.avg_latency_ms / 60000);

  // ── Disponibilidade (0–5) ─────────────────────────────────────────────────
  const available = row.archived || row.available === false ? 0 : 5;

  return Math.max(0, Math.min(100, json + ease + accuracy + speed + latency + available));
  // Distribuição: Usabilidade 45% | Acertividade 30% | Performance 20% | Disponib. 5%
}

function easeLabel(row) {
  if (row.archived) return "fora da lista";
  if (!row.runs) return "sem teste";
  if (row.json_rate >= 0.95 && row.invalid_runs === 0) return "pronto";
  if (row.json_rate >= 0.75 && row.invalid_runs > 0) return "ajuste necessário";
  if (row.json_rate >= 0.75) return "bom com ajuste";
  if (row.dominant_issue === "lmstudio_error") return "corrigir ambiente";
  if (row.dominant_issue === "context_error") return "reduzir contexto";
  if (row.dominant_issue === "json_invalid") return "ajustar JSON";
  return "instavel";
}

function recommendationForBenchmark(row) {
  if (row.archived) return "Modelo com historico, mas fora da lista atual.";
  if (!row.runs) return "Executar uma fase curta antes de comparar.";
  if (row.dominant_issue === "lmstudio_error") return "Ver carregamento, contexto e suporte a response_format/schema.";
  if (row.dominant_issue === "context_error") return "Aumentar Context Length ou usar prompt enxuto.";
  if (row.dominant_issue === "json_invalid") return "Usar perfil producao: temp 0.0-0.2 e Structured Output.";
  if (row.json_rate >= 0.95) return "Config atual serve como baseline.";
  return "Rodar retry-invalidos com perfil JSON.";
}

function dominantIssueFromCounts(counts) {
  const entries = Object.entries(counts || {});
  if (!entries.length) return "none";
  return entries.sort((a, b) => Number(b[1]) - Number(a[1]))[0][0];
}

function runErrorType(error) {
  const lowered = String(error || "").toLowerCase();
  if (lowered.includes("lm studio") || lowered.includes("bad request") || lowered.includes("http")) return "lmstudio_error";
  if (lowered.includes("context") || lowered.includes("token")) return "context_error";
  if (lowered.includes("json")) return "json_invalid";
  return "other_error";
}

// ─── Canvas-based image export (no html2canvas dependency) ──────────────────

function _loadImg(src) {
  return new Promise((resolve) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => resolve(img);
    img.onerror = () => resolve(null);
    img.src = src;
  });
}

// ── Shared canvas helpers ────────────────────────────────────────────────────
function _canvasPalette() {
  return {
    bg: "#161a22", panel: "#1e2433", border: "#2c3347",
    accent: "#38d6a5", gold: "#f2c94c", red: "#fb7185", green: "#2fc76f",
    text: "#e8edf5", muted: "#7080a0", dim: "#404a60",
  };
}

function _canvasTxt(ctx, text, x, y, font, color, align = "left") {
  ctx.textAlign = align;
  ctx.fillStyle = color;
  ctx.font = font;
  ctx.fillText(text, x, y);
  ctx.textAlign = "left";
}

function _canvasF(size, bold = false) {
  return `${bold ? "bold " : ""}${size}px system-ui, ui-sans-serif, sans-serif`;
}

function _canvasDrawIcon(ctx, img, fallbackInitials, x, y, size, r) {
  if (img) {
    ctx.save();
    _roundRect(ctx, x, y, size, size, r);
    ctx.clip();
    ctx.drawImage(img, x, y, size, size);
    ctx.restore();
  } else {
    const C = _canvasPalette();
    ctx.fillStyle = C.accent + "44";
    _roundRect(ctx, x, y, size, size, r);
    ctx.fill();
    _canvasTxt(ctx, (fallbackInitials || "AI").slice(0, 2).toUpperCase(),
      x + size / 2, y + size * 0.67, _canvasF(size * 0.38, true), C.accent, "center");
  }
}

async function _loadIconMap(rows) {
  const urls = rows.map((r) => resolveModelImage(r) || avatarForModel(r));
  const imgs = await Promise.all(urls.map((u) => _loadImg(u)));
  // fallback pass for failed real images
  const resolved = await Promise.all(rows.map(async (r, i) => imgs[i] || await _loadImg(avatarForModel(r))));
  return new Map(rows.map((r, i) => [r.model_id, resolved[i]]));
}

async function _canvasDownload(canvas, filename) {
  if (typeof canvas.toBlob !== "function") {
    const a = document.createElement("a");
    a.download = filename;
    a.href = canvas.toDataURL("image/png");
    document.body.appendChild(a);
    a.click();
    a.remove();
    return;
  }
  await new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (!blob) {
        try {
          const a = document.createElement("a");
          a.download = filename;
          a.href = canvas.toDataURL("image/png");
          document.body.appendChild(a);
          a.click();
          a.remove();
          resolve();
        } catch (error) { reject(error); }
        return;
      }
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.download = filename;
      a.href = url;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(url), 10000);
      resolve();
    }, "image/png");
  });
}

function _canvasHeader(ctx, W, HDR_H, PAD, logo, title, subtitle, C) {
  const hGrad = ctx.createLinearGradient(0, 0, W, HDR_H);
  hGrad.addColorStop(0, "#090e18");
  hGrad.addColorStop(1, "#161a22");
  ctx.fillStyle = hGrad;
  ctx.fillRect(0, 0, W, HDR_H);

  const LOGO = 56;
  const ly = (HDR_H - LOGO) / 2;
  if (logo) {
    ctx.drawImage(logo, PAD, ly, LOGO, LOGO);
  } else {
    ctx.fillStyle = C.accent + "33";
    _roundRect(ctx, PAD, ly, LOGO, LOGO, 8);
    ctx.fill();
    _canvasTxt(ctx, "CM", PAD + LOGO / 2, ly + LOGO * 0.62, _canvasF(18, true), C.accent, "center");
  }
  const tx = PAD + LOGO + 14;
  _canvasTxt(ctx, "COPAMIND 2026", tx, HDR_H / 2 - 12, _canvasF(9, true), C.accent);
  _canvasTxt(ctx, title, tx, HDR_H / 2 + 12, _canvasF(22, true), C.text);
  _canvasTxt(ctx, subtitle, tx, HDR_H / 2 + 28, _canvasF(11), C.muted);

  const dateStr = new Date().toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });
  _canvasTxt(ctx, dateStr, W - PAD, PAD + 12, _canvasF(10), C.muted, "right");

  ctx.fillStyle = C.accent;
  ctx.fillRect(0, HDR_H - 2, W, 2);
}

// ── Ranking canvas ───────────────────────────────────────────────────────────
function buildRankingCanvas(rows, logo, iconMap) {
  const C = _canvasPalette();
  const SCALE = 2;
  const PAD = 20;
  const ROW_H = 52;
  const HDR_H = 88;
  const COL_H = 32;
  const FOOT_H = 36;
  const ICO = 32;

  // columns: #, icon, name, pontos, acerto, jogos, json, lat, tok/s, brier
  const COLS = [
    { label: "#",      w: 40,  align: "center" },
    { label: "",       w: 42,  align: "center" },   // icon
    { label: "Modelo", w: 220, align: "left"   },
    { label: "Pts",    w: 62,  align: "center" },
    { label: "Acerto", w: 72,  align: "center" },
    { label: "Jogos",  w: 58,  align: "center" },
    { label: "JSON",   w: 58,  align: "center" },
    { label: "Lat.",   w: 76,  align: "center" },
    { label: "Tok/s",  w: 68,  align: "center" },
    { label: "Brier",  w: 68,  align: "center" },
  ];

  const totalColW = COLS.reduce((s, c) => s + c.w, 0);
  const W = PAD + totalColW + PAD;
  const H = HDR_H + COL_H + rows.length * ROW_H + FOOT_H;

  const canvas = document.createElement("canvas");
  canvas.width = W * SCALE;
  canvas.height = H * SCALE;
  const ctx = canvas.getContext("2d");
  ctx.scale(SCALE, SCALE);

  ctx.fillStyle = C.bg;
  ctx.fillRect(0, 0, W, H);

  _canvasHeader(ctx, W, HDR_H, PAD, logo, "Ranking das LLMs", "Score geral · Bolao CopaMind 2026", C);

  // Column header
  let cx = PAD;
  COLS.forEach((col) => {
    ctx.fillStyle = C.panel;
    ctx.fillRect(cx, HDR_H, col.w, COL_H);
    if (col.label) {
      _canvasTxt(ctx, col.label.toUpperCase(), cx + col.w / 2, HDR_H + 21,
        _canvasF(9, true), C.muted, "center");
    }
    cx += col.w;
  });
  ctx.fillStyle = C.accent;
  ctx.fillRect(PAD, HDR_H + COL_H - 1, totalColW, 1);

  // Data rows
  rows.forEach((row, ri) => {
    const ry = HDR_H + COL_H + ri * ROW_H;
    const even = ri % 2 === 0;
    ctx.fillStyle = even ? "#1a1f2c" : C.bg;
    ctx.fillRect(PAD, ry, totalColW, ROW_H - 1);

    const vals = [
      { v: String(ri + 1), align: "center", color: C.gold, bold: true },
      null, // icon handled separately
      { v: row.display_name, align: "left",   color: C.text,  bold: false },
      { v: String(row.points), align: "center", color: row.points > 0 ? C.accent : C.muted },
      { v: row.scored ? pct(row.accuracy) : "–", align: "center", color: C.text },
      { v: String(row.scored || row.predictions || 0), align: "center", color: C.text },
      { v: row.json_rate == null ? "–" : `${Math.round(row.json_rate * 100)}%`, align: "center",
        color: row.json_rate == null ? C.muted : row.json_rate >= 0.95 ? C.accent : row.json_rate >= 0.7 ? C.gold : C.red },
      { v: row.avg_latency_ms == null ? "–" : `${Math.round(row.avg_latency_ms)} ms`, align: "center", color: C.muted },
      { v: row.avg_tokens_per_second == null ? "–" : num(row.avg_tokens_per_second, 1), align: "center", color: C.text },
      { v: row.brier_avg == null ? "–" : num(row.brier_avg, 3), align: "center", color: C.muted },
    ];

    let x = PAD;
    COLS.forEach((col, ci) => {
      if (ci === 1) {
        // icon
        const icoX = x + (col.w - ICO) / 2;
        const icoY = ry + (ROW_H - ICO) / 2;
        const modelIcon = iconMap?.get(row.model_id);
        ctx.fillStyle = "#10141c";
        _roundRect(ctx, icoX - 1, icoY - 1, ICO + 2, ICO + 2, 7);
        ctx.fill();
        _canvasDrawIcon(ctx, modelIcon,
          (row.display_name || row.model_id).replace(/^[^/]+\//, ""),
          icoX, icoY, ICO, 6);
      } else {
        const d = vals[ci];
        if (d) {
          // clip long text for name col
          if (ci === 2) {
            ctx.save();
            ctx.beginPath();
            ctx.rect(x + 6, ry, col.w - 8, ROW_H);
            ctx.clip();
          }
          _canvasTxt(ctx, d.v, d.align === "center" ? x + col.w / 2 : x + 6,
            ry + ROW_H / 2 + 5, _canvasF(11, d.bold ?? false), d.color ?? C.text, d.align || "left");
          if (ci === 2) ctx.restore();
        }
      }
      x += col.w;
    });

    // Bottom divider
    ctx.fillStyle = C.border;
    ctx.fillRect(PAD, ry + ROW_H - 1, totalColW, 1);
  });

  // Footer
  const fy = HDR_H + COL_H + rows.length * ROW_H;
  ctx.fillStyle = C.border;
  ctx.fillRect(PAD, fy + 8, totalColW, 1);
  _canvasTxt(ctx, "github.com/Phemassa/copamind-2026  •  IA local · dados oficiais FIFA · benchmark auditavel",
    W / 2, fy + 26, _canvasF(10), C.muted, "center");

  return canvas;
}

// ── Benchmark canvas ─────────────────────────────────────────────────────────
function buildBenchmarkCanvas(rows, logo, iconMap) {
  const C = _canvasPalette();
  const SCALE = 2;
  const PAD = 20;
  const ROW_H = 58;
  const HDR_H = 88;
  const COL_H = 32;
  const FOOT_H = 36;
  const ICO = 34;

  // columns: #, icon, name, bench, bolao (ref), json, chamadas, lat, tok/s, uso, orientacao
  const COLS = [
    { label: "#",            w: 40,  align: "center" },
    { label: "",             w: 44,  align: "center" },
    { label: "Modelo",       w: 210, align: "left"   },
    { label: "Score",        w: 68,  align: "center" },
    { label: "Pts Bolão ↗",  w: 108, align: "center" },
    { label: "JSON",         w: 60,  align: "center" },
    { label: "Chamadas",     w: 80,  align: "center" },
    { label: "Lat.",         w: 80,  align: "center" },
    { label: "Tok/s",        w: 68,  align: "center" },
    { label: "Uso",          w: 100, align: "center" },
    { label: "Orientação",   w: 200, align: "left"   },
  ];

  const totalColW = COLS.reduce((s, c) => s + c.w, 0);
  const W = PAD + totalColW + PAD;
  const H = HDR_H + COL_H + rows.length * ROW_H + FOOT_H;

  const canvas = document.createElement("canvas");
  canvas.width = W * SCALE;
  canvas.height = H * SCALE;
  const ctx = canvas.getContext("2d");
  ctx.scale(SCALE, SCALE);

  ctx.fillStyle = C.bg;
  ctx.fillRect(0, 0, W, H);

  _canvasHeader(ctx, W, HDR_H, PAD, logo, "Benchmark LLMs", "Usabilidade · Acertividade · Performance técnica (independente do Bolão)", C);

  // Column headers
  let cx = PAD;
  COLS.forEach((col) => {
    ctx.fillStyle = C.panel;
    ctx.fillRect(cx, HDR_H, col.w, COL_H);
    if (col.label) {
      _canvasTxt(ctx, col.label.toUpperCase(), cx + col.w / 2, HDR_H + 21,
        _canvasF(9, true), C.muted, "center");
    }
    cx += col.w;
  });
  ctx.fillStyle = C.accent;
  ctx.fillRect(PAD, HDR_H + COL_H - 1, totalColW, 1);

  // Data rows
  rows.forEach((row, ri) => {
    const ry = HDR_H + COL_H + ri * ROW_H;
    const even = ri % 2 === 0;
    ctx.fillStyle = row.archived ? "#191c25" : (even ? "#1a1f2c" : C.bg);
    ctx.fillRect(PAD, ry, totalColW, ROW_H - 1);

    const jsonColor = row.json_rate == null ? C.muted
      : row.json_rate >= 0.95 ? C.accent
      : row.json_rate >= 0.7 ? C.gold : C.red;

    const vals = [
      { v: String(ri + 1), align: "center", color: C.gold, bold: true },
      null, // icon
      { v: row.display_name, align: "left", color: row.archived ? C.muted : C.text },
      { v: num(row.benchmark_score, 0), align: "center", color: C.green, bold: true },
      { v: row.scored ? `${row.points}pts / ${pct(row.accuracy)}` : "sem score", align: "center", color: C.text },
      { v: row.runs ? `${Math.round(row.json_rate * 100)}%` : "–", align: "center", color: jsonColor },
      { v: `${row.valid_runs}/${row.runs}`, align: "center", color: C.text },
      { v: row.avg_latency_ms == null ? "–" : `${Math.round(row.avg_latency_ms)} ms`, align: "center", color: C.muted },
      { v: row.avg_tokens_per_second == null ? "–" : num(row.avg_tokens_per_second, 1), align: "center", color: C.text },
      { v: row.ease_label || "–", align: "center", color: "#dbe8ff" },
      { v: row.recommendation || "–", align: "left", color: C.muted },
    ];

    let x = PAD;
    COLS.forEach((col, ci) => {
      if (ci === 1) {
        const icoX = x + (col.w - ICO) / 2;
        const icoY = ry + (ROW_H - ICO) / 2;
        const modelIcon = iconMap?.get(row.model_id);
        ctx.fillStyle = "#10141c";
        _roundRect(ctx, icoX - 1, icoY - 1, ICO + 2, ICO + 2, 7);
        ctx.fill();
        _canvasDrawIcon(ctx, modelIcon,
          (row.display_name || row.model_id).replace(/^[^/]+\//, ""),
          icoX, icoY, ICO, 6);
      } else {
        const d = vals[ci];
        if (d) {
          ctx.save();
          ctx.beginPath();
          ctx.rect(x + (d.align === "left" ? 6 : 0), ry + 2, col.w - 8, ROW_H - 4);
          ctx.clip();
          _canvasTxt(ctx, d.v,
            d.align === "center" ? x + col.w / 2 : x + 6,
            ry + ROW_H / 2 + 5,
            _canvasF(11, d.bold ?? false), d.color ?? C.text, d.align || "left");
          ctx.restore();
        }
      }
      x += col.w;
    });

    ctx.fillStyle = C.border;
    ctx.fillRect(PAD, ry + ROW_H - 1, totalColW, 1);
  });

  const fy = HDR_H + COL_H + rows.length * ROW_H;
  ctx.fillStyle = C.border;
  ctx.fillRect(PAD, fy + 8, totalColW, 1);
  _canvasTxt(ctx, "github.com/Phemassa/copamind-2026  •  IA local · benchmark auditavel · LM Studio / Ollama",
    W / 2, fy + 26, _canvasF(10), C.muted, "center");

  return canvas;
}

async function exportRankingImage() {
  const rows = rankingRows();
  if (!rows.length) { alert("Sem dados de ranking ainda."); return; }
  const btn = document.getElementById("btn-export-ranking");
  const orig = btn?.textContent;
  if (btn) { btn.textContent = "Gerando..."; btn.disabled = true; }
  try {
    const [logo, iconMap] = await Promise.all([
      _loadImg("../../docs/assets/copamind_2026.png"),
      _loadIconMap(rows),
    ]);
    const canvas = buildRankingCanvas(rows, logo, iconMap);
    const date = new Date().toISOString().slice(0, 10).replace(/-/g, "");
    await _canvasDownload(canvas, `copamind_ranking_${date}.png`);
  } catch (err) {
    console.error("Erro ao exportar ranking:", err);
    alert("Erro ao gerar imagem. Veja o console.");
  } finally {
    if (btn) { btn.textContent = orig; btn.disabled = false; }
  }
}

function buildBenchmarkDashboardCanvas(rows, banner, iconMap) {
  const C = _canvasPalette(), S = 2, PAD = 24, HEADER = 188, HEAD = 38, ROW = 54, FOOT = 40;
  const cols = [250, 105, 105, 105, 105, 125, 105, 135];
  const labels = ["MODELO", "SCORE", "PONTOS", "JSON VÁLIDO", "ACERTO", "VELOCIDADE", "BRIER ↓", "CAPACIDADE"];
  const W = PAD * 2 + cols.reduce((a, b) => a + b, 0);
  const BANNER_H = Math.round(W / 3), BODY_H = HEADER + HEAD + (rows.length + 1) * ROW + FOOT, H = BANNER_H + BODY_H;
  const canvas = document.createElement("canvas"); canvas.width = W * S; canvas.height = H * S;
  const ctx = canvas.getContext("2d"); ctx.scale(S, S); ctx.fillStyle = C.bg; ctx.fillRect(0, 0, W, H);
  if (banner) ctx.drawImage(banner, 0, 0, W, BANNER_H);
  else { ctx.fillStyle = "#090e18"; ctx.fillRect(0, 0, W, BANNER_H); }
  ctx.translate(0, BANNER_H);
  _canvasHeader(ctx, W, 80, PAD, null, "Painel comparativo consolidado", `${rows.length} modelos avaliados · barras maiores indicam melhor desempenho`, C);
  _canvasTxt(ctx, "ESTATÍSTICAS DE EXECUÇÃO", PAD, 101, _canvasF(10, true), C.accent);
  const adjustedCount = rows.filter((row) => row.invalid_runs > 0).length;
  ctx.fillStyle = "#17283a"; _roundRect(ctx, PAD, 116, W - PAD * 2, 60, 10); ctx.fill();
  ctx.strokeStyle = "#57a7ff88"; ctx.lineWidth = 1; _roundRect(ctx, PAD, 116, W - PAD * 2, 60, 10); ctx.stroke();
  ctx.fillStyle = "#57a7ff"; ctx.fillRect(PAD, 116, 4, 60);
  ctx.fillStyle = "#243d58"; _roundRect(ctx, PAD + 14, 127, 38, 38, 8); ctx.fill();
  _canvasTxt(ctx, "{ }", PAD + 33, 151, "bold 13px monospace", "#9dccff", "center");
  _canvasTxt(ctx, "Structured Output · JSON Schema", PAD + 64, 137, _canvasF(12, true), "#dcecff");
  _canvasTxt(ctx, "Advanced: you can provide a JSON Schema to enforce a particular output format from the model. Read the documentation to learn more.", PAD + 64, 158, _canvasF(9), C.muted);
  const badge = `${adjustedCount} modelos exigiram ajuste no LM Studio`;
  ctx.font = _canvasF(9, true); const badgeW = ctx.measureText(badge).width + 22;
  ctx.fillStyle = "#40371f"; _roundRect(ctx, W - PAD - badgeW - 12, 128, badgeW, 28, 14); ctx.fill();
  _canvasTxt(ctx, badge, W - PAD - badgeW / 2 - 12, 147, _canvasF(9, true), C.gold, "center");
  let x = PAD; labels.forEach((label, i) => { ctx.fillStyle = C.panel; ctx.fillRect(x, HEADER, cols[i], HEAD); _canvasTxt(ctx, label, x + (i ? cols[i] / 2 : 8), HEADER + 24, _canvasF(9, true), C.muted, i ? "center" : "left"); x += cols[i]; });
  const maxPoints = Math.max(...rows.map(r => r.points || 0), 1), maxSpeed = Math.max(...rows.map(r => r.avg_tokens_per_second || 0), 1), maxBrier = Math.max(...rows.map(r => r.brier_avg || 0), 1);
  const metric = (value, max, inverse = false) => value == null ? null : (inverse ? 1 - Math.min(1, value / max) : Math.min(1, value / max));
  rows.forEach((r, ri) => {
    const y = HEADER + HEAD + ri * ROW; ctx.fillStyle = ri % 2 ? C.bg : "#1a1f2c"; ctx.fillRect(PAD, y, W - PAD * 2, ROW - 1);
    const img = iconMap?.get(r.model_id); _canvasDrawIcon(ctx, img, r.display_name, PAD + 30, y + 10, 34, 6);
    _canvasTxt(ctx, String(ri + 1), PAD + 14, y + 32, _canvasF(10, true), C.gold, "center");
    _canvasTxt(ctx, (r.display_name || r.model_id).slice(0, 26), PAD + 72, y + 25, _canvasF(11, true), C.text); _canvasTxt(ctx, `${r.runs} execuções`, PAD + 72, y + 41, _canvasF(9), C.muted);
    const values = [
      [r.benchmark_score, 100, num(r.benchmark_score, 0)], [r.points, maxPoints, `${r.points} pts`],
      [r.json_rate == null ? null : r.json_rate * 100, 100, r.json_rate == null ? "—" : `${Math.round(r.json_rate * 100)}%`],
      [r.accuracy == null ? null : r.accuracy * 100, 100, r.accuracy == null ? "—" : `${Math.round(r.accuracy * 100)}%`],
      [r.avg_tokens_per_second, maxSpeed, r.avg_tokens_per_second == null ? "—" : `${num(r.avg_tokens_per_second, 1)} tok/s`],
      [r.brier_avg, maxBrier, r.brier_avg == null ? "—" : num(r.brier_avg, 3), true]
    ];
    let mx = PAD + cols[0]; values.forEach(([v, max, label, inverse], i) => { const q = metric(v, max, inverse); ctx.fillStyle = "#252b38"; _roundRect(ctx, mx + 8, y + 8, cols[i + 1] - 16, i === 2 ? 27 : 34, 6); ctx.fill(); if (q != null) { ctx.fillStyle = C.accent + "88"; _roundRect(ctx, mx + 8, y + 8, Math.max(4, (cols[i + 1] - 16) * q), i === 2 ? 27 : 34, 6); ctx.fill(); } _canvasTxt(ctx, label, mx + cols[i + 1] / 2, y + 29, _canvasF(10, true), C.text, "center"); if (i === 2) _canvasTxt(ctx, r.invalid_runs > 0 ? "AJUSTADO LM STUDIO" : "SCHEMA APLICADO", mx + cols[i + 1] / 2, y + 47, _canvasF(7, true), r.invalid_runs > 0 ? C.gold : C.accent, "center"); mx += cols[i + 1]; });
    const visual = /omni|vision|vl/i.test(r.model_id); _canvasTxt(ctx, visual ? "◉ Visão" : "Texto", mx + cols[7] / 2, y + 32, _canvasF(10, true), visual ? "#9dccff" : C.muted, "center");
  });
  const fy = HEADER + HEAD + rows.length * ROW; ctx.fillStyle = "#251d30"; ctx.fillRect(PAD, fy, W - PAD * 2, ROW - 1); _canvasTxt(ctx, "+", PAD + 14, fy + 32, _canvasF(12, true), "#f0abfc", "center"); _canvasTxt(ctx, "✦  FLUX.1-dev", PAD + 38, fy + 25, _canvasF(11, true), C.text); _canvasTxt(ctx, "modelo visual de referência", PAD + 38, fy + 41, _canvasF(9), C.muted); _canvasTxt(ctx, "fora do benchmark", PAD + cols[0] + cols.slice(1, 7).reduce((a,b)=>a+b,0) / 2, fy + 32, _canvasF(10), C.muted, "center"); _canvasTxt(ctx, "✦ Gera imagem", W - PAD - cols[7] / 2, fy + 32, _canvasF(10, true), "#f0abfc", "center");
  _canvasTxt(ctx, "CopaMind 2026 · Benchmark de LLMs locais", W / 2, BODY_H - 14, _canvasF(10), C.muted, "center"); return canvas;
}

async function exportBenchmarkDashboardImage() {
  const rows = benchmarkRows().filter(r => !r.archived && (r.runs > 0 || r.scored > 0)).sort((a,b) => b.benchmark_score - a.benchmark_score);
  const btn = document.getElementById("btn-export-benchmark-dashboard"), label = btn?.textContent;
  if (!rows.length) { alert("Sem dados de benchmark ainda."); return; }
  if (btn) { btn.textContent = "Gerando PNG..."; btn.disabled = true; }
  try { const [banner, icons] = await Promise.all([_loadImg("../../docs/assets/banner.png"), _loadIconMap(rows)]); await _canvasDownload(buildBenchmarkDashboardCanvas(rows, banner, icons), `copamind_painel_comparativo_${new Date().toISOString().slice(0,10).replace(/-/g,"")}.png`); }
  catch (err) { console.error("Erro ao exportar painel:", err); alert("Erro ao gerar o quadro completo. Veja o console."); }
  finally { if (btn) { btn.textContent = label; btn.disabled = false; } }
}

async function exportBenchmarkImage() {
  const rows = benchmarkRows().filter((row) => !row.archived);
  if (!rows.length) { alert("Sem dados de benchmark ainda."); return; }
  const buttons = [document.getElementById("btn-export-benchmark"), document.getElementById("btn-export-benchmark-dashboard")].filter(Boolean);
  const labels = buttons.map((button) => button.textContent);
  buttons.forEach((button) => { button.textContent = "Gerando PNG..."; button.disabled = true; });
  try {
    const [logo, iconMap] = await Promise.all([
      _loadImg("../../docs/assets/copamind_2026.png"),
      _loadIconMap(rows),
    ]);
    const canvas = buildBenchmarkCanvas(rows, logo, iconMap);
    const date = new Date().toISOString().slice(0, 10).replace(/-/g, "");
    await _canvasDownload(canvas, `copamind_benchmark_${date}.png`);
  } catch (err) {
    console.error("Erro ao exportar benchmark:", err);
    alert("Erro ao gerar imagem. Veja o console.");
  } finally {
    buttons.forEach((button, index) => { button.textContent = labels[index]; button.disabled = false; });
  }
}

function _shortName(name) {
  if (!name) return "?";
  const first = name.trim().split(/\s+/)[0];
  return first.length <= 10 ? first : first.slice(0, 3).toUpperCase();
}

function _nameLines(displayName) {
  // Strip vendor prefix, split on delimiters → up to 4 short lines
  const base = (displayName || "").replace(/^[^/]+\//, "");
  const parts = base.split(/[-_.]/g).filter(Boolean);
  const lines = [];
  let cur = "";
  for (const p of parts) {
    const joined = cur ? `${cur}-${p}` : p;
    if (cur && joined.length > 10) { lines.push(cur); cur = p; }
    else { cur = joined; }
    if (lines.length === 3) { cur = parts.slice(parts.indexOf(p)).join("-"); break; }
  }
  if (cur) lines.push(cur);
  return lines.slice(0, 4);
}

function _roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

function buildLinkedInCanvas(rows, phase, icon, iconMap) {
  const PAD     = 20;
  const MCW     = 130;         // match column width
  const CW      = 64;          // cell width per model
  const ICO     = 32;          // model icon size
  const HDR_H   = 110;         // CopaMind header
  const SUM_H   = 58;          // stats bar
  const MOD_H   = 112;         // model name header row (icon + 4 lines + dot)
  const ROW_H   = 68;          // data row height
  const FOOT_H  = 38;

  // Collect ordered matches — deduplicate by canonical team pair
  // Coleta e deduplica partidas por par de times canônico
  const matchOrderAll = [];
  const seenKeys = new Set();
  rows.forEach((row) => (row.predictions || []).forEach((pred) => {
    const canonical = `${pred.home || pred.home_team_id || ""}×${pred.away || pred.away_team_id || ""}`;
    if (!seenKeys.has(canonical)) { seenKeys.add(canonical); matchOrderAll.push({ ...pred, _key: canonical }); }
  }));
  // Filtra apenas pares de times que correspondem a partidas OFICIAIS da fase (evita projeções erradas)
  const canvasOfficialMatches = (state.matches || []).filter((m) => m.stage === phase);
  const canvasOfficialPairs = new Set(canvasOfficialMatches.map((m) => `${m.home_team_id}|${m.away_team_id}`));
  const matchOrder = canvasOfficialMatches.length > 0
    ? matchOrderAll.filter((m) => {
        const hId = m.home_team_id || "";
        const aId = m.away_team_id || "";
        return hId && aId && canvasOfficialPairs.has(`${hId}|${aId}`);
      })
    : matchOrderAll;

  const _findPred = (preds, canonical) =>
    preds.find((p) => `${p.home || p.home_team_id || ""}×${p.away || p.away_team_id || ""}` === canonical);
  const _findOfficial = (m) => {
    if (!m) return undefined;
    return (state.matches || []).find((mx) =>
      (mx.home_team_id && m.home_team_id && mx.home_team_id === m.home_team_id && mx.away_team_id === m.away_team_id)
      || (m.match_id && mx.match_id === m.match_id),
    );
  };

  // Avg prob per match across models
  const matchStats = {};
  matchOrder.forEach((m) => {
    const preds = rows
      .map((row) => _findPred(row.predictions || [], m._key))
      .filter((p) => p && (p.prob_home || 0) + (p.prob_away || 0) > 0);
    if (preds.length) {
      const avgH = preds.reduce((s, p) => s + p.prob_home / (p.prob_home + p.prob_away), 0) / preds.length;
      matchStats[m._key] = { home: Math.round(avgH * 100), away: Math.round((1 - avgH) * 100) };
    }
  });

  const nM = rows.length;
  const nG = matchOrder.length;
  const W  = PAD + MCW + nM * CW + PAD;
  const TEAMS_H = 110;  // top-4 teams section
  const LEG_H   = 34;   // star legend bar
  const SUMROW_H = 44;  // star count summary row
  const H  = HDR_H + SUM_H + TEAMS_H + MOD_H + SUMROW_H + nG * ROW_H + LEG_H + FOOT_H;

  // Escala adaptativa: retina (2x) para tabelas pequenas, 1x para tabelas largas
  // Limita a ~8192px de largura para compatibilidade com todos os browsers
  const MAX_PX = 8192;
  const SCALE  = Math.min(2, Math.floor(MAX_PX / W)) || 1;

  const canvas = document.createElement("canvas");
  canvas.width  = W * SCALE;
  canvas.height = H * SCALE;
  const ctx = canvas.getContext("2d");
  ctx.scale(SCALE, SCALE);

  // ── Palette ────────────────────────────────────────────────────────────────
  const C = {
    bg:      "#161a22", panel:   "#1e2433", border:  "#2c3347",
    accent:  "#38d6a5", blue:    "#4d8dff", gold:    "#f2c94c",
    red:     "#fb7185", purple:  "#c084fc",
    text:    "#e8edf5", muted:   "#7080a0", dim:     "#404a60",
    cHome:   "#0f231c", cAway:   "#0e1a2e", cDraw:   "#221e0a",
    tHome:   "#38d6a5", tAway:   "#57a7ff", tDraw:   "#f2c94c",
  };

  const F = (size, bold = false) =>
    `${bold ? "bold " : ""}${size}px system-ui, ui-sans-serif, sans-serif`;

  // helper: fill + stroke text
  const txt = (text, x, y, font, color, align = "left") => {
    ctx.textAlign = align;
    ctx.fillStyle = color;
    ctx.font = font;
    ctx.fillText(text, x, y);
    ctx.textAlign = "left";
  };

  // ── Background ─────────────────────────────────────────────────────────────
  ctx.fillStyle = C.bg;
  ctx.fillRect(0, 0, W, H);

  // ── Header ─────────────────────────────────────────────────────────────────
  const hGrad = ctx.createLinearGradient(0, 0, W, HDR_H);
  hGrad.addColorStop(0, "#090e18");
  hGrad.addColorStop(1, "#161a22");
  ctx.fillStyle = hGrad;
  ctx.fillRect(0, 0, W, HDR_H);

  // Icon / logo
  const LOGO = 72;
  if (icon) {
    ctx.drawImage(icon, PAD, (HDR_H - LOGO) / 2, LOGO, LOGO);
  } else {
    ctx.fillStyle = C.accent + "33";
    _roundRect(ctx, PAD, (HDR_H - LOGO) / 2, LOGO, LOGO, 10);
    ctx.fill();
    txt("CM", PAD + LOGO / 2, (HDR_H - LOGO) / 2 + LOGO / 2 + 8, F(22, true), C.accent, "center");
  }

  const tx = PAD + LOGO + 16;
  txt("PREVISÃO DAS LLMS · COPAMIND 2026", tx, HDR_H / 2 - 20, F(10, true), C.accent);
  txt("Previsão das LLMs", tx, HDR_H / 2 + 12, F(30, true), C.text);
  txt("Chances por seleção · mesmos dados · mesma regra JSON · previsões auditáveis", tx, HDR_H / 2 + 30, F(12), C.muted);

  const dateStr = new Date().toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });
  txt(dateStr, W - PAD, PAD + 14, F(11), C.muted, "right");

  // Accent line
  ctx.fillStyle = C.accent;
  ctx.fillRect(0, HDR_H - 2, W, 2);

  // ── Summary bar ────────────────────────────────────────────────────────────
  const phaseInfo = (state.phases || []).find((p) => p.key === phase);
  const phaseLbl  = phaseInfo?.label || phase;
  const validPreds = rows.reduce((s, r) => s + r.predictions.length, 0);
  const best100    = rows.filter((r) => r.json_rate === 1).length;

  ctx.fillStyle = C.panel;
  ctx.fillRect(0, HDR_H, W, SUM_H);

  const sumItems = [
    { label: "FASE",            value: phaseLbl },
    { label: "MODELOS VÁLIDOS", value: String(nM) },
    { label: "PALPITES",        value: String(validPreds) },
    { label: "JSON 100%",       value: String(best100) },
  ];
  const sw = W / sumItems.length;
  sumItems.forEach((item, i) => {
    if (i > 0) { ctx.fillStyle = C.border; ctx.fillRect(i * sw, HDR_H + 8, 1, SUM_H - 16); }
    const cx = i * sw + sw / 2;
    txt(item.label, cx, HDR_H + 20, F(9, true), C.muted, "center");
    txt(item.value, cx, HDR_H + 46, F(20, true), C.text, "center");
  });

  ctx.fillStyle = C.border;
  ctx.fillRect(0, HDR_H + SUM_H - 1, W, 1);

  // ── Top-4 seleções esperadas ───────────────────────────────────────────────
  {
    // Usa apenas partidas OFICIAIS da fase para evitar times de projeções erradas
    const phaseOfficial = (state.matches || []).filter((m) => m.stage === phase);
    const officialPairSet = new Set(phaseOfficial.map((m) => `${m.home_team_id}|${m.away_team_id}`));

    const teamChancesMap = {};
    matchOrder.forEach((m) => {
      const stats = matchStats[m._key];
      if (!stats) return;
      // Se há partidas oficiais, filtra apenas as que correspondem
      if (phaseOfficial.length > 0) {
        const hId = m.home_team_id || "";
        const aId = m.away_team_id || "";
        if (!hId || !aId || !officialPairSet.has(`${hId}|${aId}`)) return;
      }
      const hName = m.home || m.home_team_id || "";
      const aName = m.away || m.away_team_id || "";
      if (hName) teamChancesMap[hName] = { name: hName, prob: stats.home };
      if (aName) teamChancesMap[aName] = { name: aName, prob: stats.away };
    });
    const allTeams = Object.values(teamChancesMap).filter((t) => t.name).sort((a, b) => b.prob - a.prob);
    const top4 = allTeams.slice(0, 4);
    const secY = HDR_H + SUM_H;
    ctx.fillStyle = C.panel;
    ctx.fillRect(0, secY, W, TEAMS_H);
    txt("CHANCES POR SELEÇÃO  —  probabilidade média das LLMs por jogo", PAD, secY + 18, F(9, true), C.accent);
    const barMaxW = Math.min(260, W * 0.30);
    const colW = (W - PAD * 2) / Math.max(1, top4.length);
    top4.forEach((team, i) => {
      const cx = PAD + i * colW;
      const ty = secY + 30;
      txt(`${i + 1}.`, cx + 4, ty + 15, F(10, true), C.gold);
      txt(team.name, cx + 20, ty + 15, F(11, true), C.text);
      txt(`${team.prob}%`, cx + 20, ty + 30, F(13, true), C.accent);
      // bar proporcional à probabilidade (0–100%)
      const bw = Math.round(barMaxW * team.prob / 100);
      ctx.fillStyle = C.border; ctx.fillRect(cx + 20, ty + 38, barMaxW, 8);
      const grad = ctx.createLinearGradient(cx + 20, 0, cx + 20 + bw, 0);
      grad.addColorStop(0, C.accent); grad.addColorStop(1, "#f2c94c");
      ctx.fillStyle = grad; ctx.fillRect(cx + 20, ty + 38, bw, 8);
      const advLbl = phase === "final"       ? "prob. de ser campeã"
        : phase === "third_place"            ? "prob. vencer (3º lugar)"
        : phase === "semifinal"              ? "prob. ir à Final"
        : "prob. de avançar";
      txt(advLbl, cx + 20, ty + 60, F(9), C.muted);
    });
    ctx.fillStyle = C.border;
    ctx.fillRect(0, secY + TEAMS_H - 1, W, 1);
  }

  // ── Model header row ───────────────────────────────────────────────────────
  const tableX = PAD + MCW;
  let sy = HDR_H + SUM_H + TEAMS_H;

  // Empty match-col corner
  ctx.fillStyle = C.panel;
  ctx.fillRect(PAD, sy, MCW, MOD_H);

  rows.forEach((row, ri) => {
    const cx = tableX + ri * CW;
    ctx.fillStyle = ri % 2 === 0 ? "#1c2130" : C.panel;
    ctx.fillRect(cx, sy, CW - 1, MOD_H);

    const cellCx = cx + CW / 2;

    // ── Model icon ──
    const icoX = cx + (CW - ICO) / 2;
    const icoY = sy + 6;
    const modelIcon = iconMap?.get(row.model_id);
    ctx.fillStyle = "#10141c";
    _roundRect(ctx, icoX - 2, icoY - 2, ICO + 4, ICO + 4, 7);
    ctx.fill();
    if (modelIcon) {
      ctx.save();
      _roundRect(ctx, icoX, icoY, ICO, ICO, 6);
      ctx.clip();
      ctx.drawImage(modelIcon, icoX, icoY, ICO, ICO);
      ctx.restore();
    } else {
      // Fallback initials
      const initials = (row.display_name || row.model_id).replace(/^[^/]+\//, "").slice(0, 2).toUpperCase();
      ctx.fillStyle = C.accent + "44";
      _roundRect(ctx, icoX, icoY, ICO, ICO, 6);
      ctx.fill();
      txt(initials, cellCx, icoY + ICO * 0.67, F(12, true), C.accent, "center");
    }

    // ── Model name lines ──
    const lines = _nameLines(row.display_name || row.model_id);
    ctx.textAlign = "center";
    const nameStartY = icoY + ICO + 11;
    lines.forEach((line, li) => {
      ctx.fillStyle = li === 0 ? C.text : C.muted;
      ctx.font = F(li === 0 ? 9 : 8, li === 0);
      ctx.fillText(line, cellCx, nameStartY + li * 12);
    });

    // ── JSON rate dot ──
    const jr = row.json_rate ?? 0;
    const dotColor = jr >= 0.95 ? C.accent : jr >= 0.7 ? C.gold : C.red;
    ctx.fillStyle = dotColor;
    ctx.beginPath();
    ctx.arc(cellCx, sy + MOD_H - 8, 3.5, 0, Math.PI * 2);
    ctx.fill();
    ctx.textAlign = "left";
  });

  // Accent separator below model header
  ctx.fillStyle = C.accent;
  ctx.fillRect(PAD, sy + MOD_H - 2, W - PAD, 2);

  sy += MOD_H;

  // Build match result lookup for correct-prediction highlighting
  const canvasResultMap = {};
  matchOrder.forEach((m) => {
    const official = _findOfficial(m);
    if (official) canvasResultMap[m._key] = actualWinner(official);
  });

  // ── Summary row: acertos por modelo ──────────────────────────────────────
  const canvasFinishedKeys = [];
  matchOrder.forEach((m) => {
    if (canvasResultMap[m._key]) canvasFinishedKeys.push(m._key);
  });
  const canvasStarCounts = {};
  rows.forEach((row) => { canvasStarCounts[row.model_id] = [0, 0, 0, 0, 0, 0]; });
  canvasFinishedKeys.forEach((key) => {
    const m = matchOrder.find((x) => x._key === key);
    if (!m) return;
    const actual = canvasResultMap[key];
    const off = _findOfficial(m);
    rows.forEach((row) => {
      const pred = _findPred(row.predictions || [], key);
      if (!pred) return;
      try {
        const s = pred.star_rating != null
          ? Number(pred.star_rating)
          : starRating(pred, off, actual);
        if (s >= 0 && s <= 5) canvasStarCounts[row.model_id][s]++;
      } catch (_) { /* ignora erros de pontuacao individual */ }
    });
  });

  const nCanvasFinished = canvasFinishedKeys.length;
  ctx.fillStyle = "#1a1e2c";
  ctx.fillRect(PAD, sy, W - PAD, SUMROW_H);
  ctx.fillStyle = C.muted;
  ctx.font = F(9, true);
  ctx.fillText("ACERTOS", PAD + 6, sy + 16);
  ctx.fillText(nCanvasFinished > 0 ? `${nCanvasFinished} jogos` : "aguard.", PAD + 6, sy + 30);
  rows.forEach((row, ri) => {
    const cx = tableX + ri * CW;
    ctx.fillStyle = ri % 2 === 0 ? "#1a1e2c" : "#161b28";
    ctx.fillRect(cx, sy, CW - 1, SUMROW_H);
    if (nCanvasFinished > 0) {
      const sc = canvasStarCounts[row.model_id] || [];
      const correct = [1, 2, 3, 4, 5].reduce((s, n) => s + (sc[n] || 0), 0);
      const topStars = [5, 4, 3, 2, 1].find((n) => sc[n] > 0) || 0;
      const scoreColor = correct === nCanvasFinished ? C.gold : correct > 0 ? "#5af0a0" : C.muted;
      txt(`${correct}/${nCanvasFinished}`, cx + CW / 2, sy + 16, F(12, true), scoreColor, "center");
      if (topStars > 0) {
        const starColor = topStars >= 5 ? C.gold : topStars >= 4 ? "#a8e6c0" : "#5af0a0";
        txt("\u2605".repeat(topStars), cx + CW / 2, sy + 32, F(topStars > 3 ? 7 : 8, true), starColor, "center");
      }
    } else {
      txt("—", cx + CW / 2, sy + SUMROW_H / 2 + 4, F(11), C.dim, "center");
    }
    ctx.fillStyle = C.border;
    ctx.fillRect(cx + CW - 1, sy, 1, SUMROW_H);
  });
  ctx.fillStyle = C.accent + "44";
  ctx.fillRect(PAD, sy + SUMROW_H - 1, W - PAD, 1);

  sy += SUMROW_H;

  // ── Data rows ──────────────────────────────────────────────────────────────
  matchOrder.forEach((m, mi) => {
    const ry = sy + mi * ROW_H;
    const even = mi % 2 === 0;
    const actualSide = canvasResultMap[m._key] ?? null;

    // Match info column
    ctx.fillStyle = even ? "#1a1f2c" : "#161a24";
    ctx.fillRect(PAD, ry, MCW - 2, ROW_H - 1);

    const stats = matchStats[m._key];
    const homeShort = _shortName(m.home);
    const awayShort = _shortName(m.away);
    const mPad = PAD + 8;

    // Home row: dim name if lost, bright if won
    const homeColor = actualSide ? (actualSide === "home" ? C.text : C.muted) : C.text;
    const awayColor = actualSide ? (actualSide === "away" ? C.text : C.muted) : C.text;
    txt(homeShort, mPad, ry + 18, F(11, true), homeColor);
    if (stats) txt(`${stats.home}%`, mPad, ry + 31, F(10, true), C.accent);

    // Actual score or × separator
    const officialMatch = _findOfficial(m);
    if (officialMatch && officialMatch.home_score != null) {
      txt(`${officialMatch.home_score}–${officialMatch.away_score}`, mPad, ry + ROW_H / 2 + 5, F(10, true), C.gold);
    } else {
      txt("×", mPad, ry + ROW_H / 2 + 4, F(10), C.dim);
    }

    txt(awayShort, mPad, ry + ROW_H - 22, F(11, true), awayColor);
    if (stats) txt(`${stats.away}%`, mPad, ry + ROW_H - 9, F(10, true), C.muted);

    ctx.fillStyle = C.border;
    ctx.fillRect(PAD, ry + ROW_H - 1, MCW - 2, 1);

    // Model cells
    rows.forEach((row, ri) => {
      const cx = tableX + ri * CW;
      const pred = _findPred(row.predictions || [], m._key);
      const side = pred ? predictedSide(pred) : null;
      const stars = pred ? (pred.star_rating != null ? Number(pred.star_rating) : starRating(pred, _findOfficial(m), actualSide)) : 0;
      const isWrong = actualSide != null && stars === 0 && !!pred;

      // Cell bg
      const baseBg = even ? "#181d28" : C.bg;
      ctx.fillStyle = isWrong
        ? (side === "home" ? "#0d1a14" : side === "away" ? "#0a1020" : side === "draw" ? "#16140a" : baseBg)
        : (side === "home" ? C.cHome : side === "away" ? C.cAway : side === "draw" ? C.cDraw : baseBg);
      ctx.fillRect(cx, ry, CW - 1, ROW_H - 1);

      // Star-based tint + border
      if (stars >= 5) {
        ctx.fillStyle = "rgba(242,201,76,0.20)"; ctx.fillRect(cx, ry, CW - 1, ROW_H - 1);
        ctx.strokeStyle = "#f2c94ccc"; ctx.lineWidth = 2;
        ctx.strokeRect(cx + 1, ry + 1, CW - 3, ROW_H - 3); ctx.lineWidth = 1;
      } else if (stars >= 4) {
        ctx.fillStyle = "rgba(90,240,160,0.14)"; ctx.fillRect(cx, ry, CW - 1, ROW_H - 1);
        ctx.strokeStyle = "#2fc76fcc"; ctx.lineWidth = 2;
        ctx.strokeRect(cx + 1, ry + 1, CW - 3, ROW_H - 3); ctx.lineWidth = 1;
      } else if (stars >= 3) {
        ctx.fillStyle = "rgba(47,199,111,0.09)"; ctx.fillRect(cx, ry, CW - 1, ROW_H - 1);
        ctx.strokeStyle = "#2fc76f88"; ctx.lineWidth = 1.5;
        ctx.strokeRect(cx + 1, ry + 1, CW - 3, ROW_H - 3); ctx.lineWidth = 1;
      } else if (stars >= 1) {
        ctx.strokeStyle = "#2fc76f44"; ctx.lineWidth = 1;
        ctx.strokeRect(cx, ry, CW - 1, ROW_H - 1); ctx.lineWidth = 1;
      }

      if (!pred) {
        txt("—", cx + CW / 2, ry + ROW_H / 2 + 5, F(12), C.dim, "center");
      } else {
        const isDrawScore = pred.predicted_home_goals != null && pred.predicted_away_goals != null
          && Number(pred.predicted_home_goals) === Number(pred.predicted_away_goals);
        const hasPen = isDrawScore && pred.goes_to_penalties
          && pred.penalty_winner && pred.penalty_winner !== "none";

        const dimFactor = isWrong ? 0.32 : 1;
        const tColor = stars >= 5 ? "#f2c94c" : stars >= 3 ? "#5af0a0" : stars >= 1 ? C.tHome : (side === "home" ? C.tHome : side === "away" ? C.tAway : C.tDraw);
        const scoreStr = `${pred.predicted_home_goals ?? "?"}–${pred.predicted_away_goals ?? "?"}`;
        const penStr = hasPen ? `(${pred.penalty_winner === "home" ? 4 : 3}–${pred.penalty_winner === "away" ? 4 : 3})` : "";

        ctx.globalAlpha = dimFactor;
        txt(scoreStr, cx + CW / 2, ry + (hasPen ? 22 : 26), F(13, true), tColor, "center");
        if (penStr) txt(penStr, cx + CW / 2, ry + 36, F(9), C.muted, "center");
        const winner = side === "home" ? homeShort : side === "away" ? awayShort : "EMP";
        txt(winner.slice(0, 7), cx + CW / 2, ry + ROW_H - 10, F(9, true), stars >= 1 ? "#5af0a0" : C.muted, "center");
        ctx.globalAlpha = 1;

        // Stars badge top-right
        if (stars > 0) {
          const starsStr = "★".repeat(stars);
          const starColor = stars >= 5 ? "#f2c94c" : stars >= 4 ? "#a8e6c0" : "#5af0a0";
          const starFont = stars <= 2 ? F(7, true) : stars <= 3 ? F(8, true) : F(9, true);
          txt(starsStr, cx + CW - 4, ry + 10, starFont, starColor, "right");
        }
      }

      // Right divider
      ctx.fillStyle = C.border;
      ctx.fillRect(cx + CW - 1, ry, 1, ROW_H);
    });

    // Bottom divider
    ctx.fillStyle = C.border;
    ctx.fillRect(PAD, ry + ROW_H - 1, W - PAD, 1);
  });

  sy += nG * ROW_H;

  // ── Star legend bar ────────────────────────────────────────────────────────
  ctx.fillStyle = C.panel;
  ctx.fillRect(0, sy, W, LEG_H);
  ctx.fillStyle = C.border;
  ctx.fillRect(0, sy, W, 1);
  const legendDefs = [
    ["★", "Vencedor"], ["★★", "+1 gol"], ["★★★", "Placar exato"],
    ["★★★★", "+Tempo"], ["★★★★★", "Tudo certo!"],
  ];
  const legSlot = W / legendDefs.length;
  legendDefs.forEach(([stars, label], i) => {
    const lx = i * legSlot + legSlot / 2;
    txt(stars, lx, sy + 14, F(9, true), "#f2c94c", "center");
    txt(label, lx, sy + 28, F(8), C.muted, "center");
  });

  // ── Footer ─────────────────────────────────────────────────────────────────
  sy += LEG_H;
  ctx.fillStyle = C.border;
  ctx.fillRect(PAD, sy + 8, W - PAD * 2, 1);
  txt(
    "github.com/Phemassa/copamind-2026  •  IA local · dados oficiais FIFA · prompt auditavel",
    W / 2, sy + 26, F(11), C.muted, "center",
  );

  return canvas;
}

async function publishStaticSite() {
  const btn = document.getElementById("btn-publish-static");
  if (!btn) return;
  const orig = btn.textContent;
  btn.textContent = "Publicando...";
  btn.disabled = true;
  try {
    const res = await fetch(`${API_BASE}/admin/publish`, { method: "POST" });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || res.statusText);
    const log = (data.log || []).join("\n");
    alert(`✅ Publicado!\n\n${log}\n\nURL: ${data.url || ""}`);
  } catch (err) {
    alert(`❌ Erro ao publicar: ${err.message}\n\nVerifique se a API está rodando (http://localhost:8000) e se o git push está configurado.`);
  } finally {
    btn.textContent = orig;
    btn.disabled = false;
  }
}

// ── Scatter chart: Acurácia × Pontos Efetivos ────────────────────────────────

function scatterRows() {
  return rankingRows().filter((r) => !r.is_combo && r.scored > 0);
}

function renderScatterChart() {
  const rows = scatterRows();
  document.getElementById("linkedin-summary").innerHTML = `
    <div><span>Modelos</span><strong>${rows.length}</strong></div>
    <div><span>Eixo X</span><strong>Pts Efetivos</strong></div>
    <div><span>Eixo Y</span><strong>Acurácia %</strong></div>
    <div><span>Tamanho</span><strong>Jogos pontuados</strong></div>`;
  document.getElementById("linkedin-team-ranking").innerHTML = "";
  const canvas = buildScatterCanvas(rows, null);
  const wrap = document.createElement("div");
  wrap.style.cssText = "padding:12px 0;";
  canvas.style.cssText = "width:100%;max-width:900px;border-radius:12px;display:block;margin:0 auto;";
  wrap.appendChild(canvas);
  document.getElementById("linkedin-capture-grid").innerHTML = "";
  document.getElementById("linkedin-capture-grid").appendChild(wrap);
}

function buildScatterCanvas(rows, logo) {
  /* ── layout ─────────────────────────────────────────── */
  const S = 2;
  const W = 1000, H = 620;
  const ML = 90, MR = 40, MT = 100, MB = 70;
  const PW = W - ML - MR, PH = H - MT - MB;

  const canvas = document.createElement("canvas");
  canvas.width = W * S; canvas.height = H * S;
  const ctx = canvas.getContext("2d");
  ctx.scale(S, S);

  const F = (sz, bold = false) => `${bold ? "bold " : ""}${sz}px system-ui,sans-serif`;

  /* ── fundo ───────────────────────────────────────────── */
  const bg = ctx.createLinearGradient(0, 0, 0, H);
  bg.addColorStop(0, "#0d1525"); bg.addColorStop(1, "#111827");
  ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);

  /* ── escala ─────────────────────────────────────────── */
  const netPts = rows.map((r) => r.net_score ?? 0);
  const xMin = Math.min(0, ...netPts);
  const xMax = Math.max(...netPts) + 2;
  const yMin = 0.58, yMax = 1.02;

  const toX = (v) => ML + ((v - xMin) / (xMax - xMin)) * PW;
  const toY = (v) => MT + (1 - (v - yMin) / (yMax - yMin)) * PH;

  /* ── grid ────────────────────────────────────────────── */
  ctx.strokeStyle = "#ffffff0e"; ctx.lineWidth = 1;
  const yTicks = [0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0];
  yTicks.forEach((v) => {
    const y = toY(v);
    ctx.beginPath(); ctx.moveTo(ML, y); ctx.lineTo(ML + PW, y); ctx.stroke();
    ctx.fillStyle = "#8090a8"; ctx.font = F(11); ctx.textAlign = "right";
    ctx.fillText(`${Math.round(v * 100)}%`, ML - 10, y + 4);
  });
  const xStep = Math.ceil((xMax - xMin) / 7);
  for (let v = Math.ceil(xMin / xStep) * xStep; v <= xMax; v += xStep) {
    const x = toX(v);
    ctx.beginPath(); ctx.moveTo(x, MT); ctx.lineTo(x, MT + PH); ctx.stroke();
    ctx.fillStyle = "#8090a8"; ctx.font = F(11); ctx.textAlign = "center";
    ctx.fillText(v, x, MT + PH + 20);
  }

  /* ── quadrante "melhor" ─────────────────────────────── */
  const qx = toX((xMin + xMax) / 2), qy = toY((yMin + yMax) / 2);
  ctx.fillStyle = "rgba(56,214,165,0.04)";
  ctx.fillRect(qx, MT, ML + PW - qx, qy - MT);
  ctx.fillStyle = "rgba(56,214,165,0.22)"; ctx.font = F(11, true); ctx.textAlign = "right";
  ctx.fillText("✦ melhor zona", ML + PW - 8, MT + 16);

  /* ── eixos ────────────────────────────────────────────── */
  ctx.strokeStyle = "#ffffff22"; ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.moveTo(ML, MT); ctx.lineTo(ML, MT + PH);
  ctx.lineTo(ML + PW, MT + PH); ctx.stroke();

  /* ── título ──────────────────────────────────────────── */
  ctx.fillStyle = "#e8edf5"; ctx.textAlign = "center"; ctx.font = F(26, true);
  ctx.fillText("Acurácia × Pontos Efetivos", W / 2, 38);
  ctx.fillStyle = "#6070a0"; ctx.font = F(13);
  ctx.fillText("Acurácia = % de vencedores corretos  •  Pts Efetivos = pontos − penalidade por erro", W / 2, 62);

  /* ── rótulos de eixo ─────────────────────────────────── */
  ctx.fillStyle = "#8090a8"; ctx.font = F(12); ctx.textAlign = "center";
  ctx.fillText("Pontos Efetivos →", ML + PW / 2, H - 12);
  ctx.save(); ctx.translate(18, MT + PH / 2);
  ctx.rotate(-Math.PI / 2); ctx.fillText("Acurácia %", 0, 0); ctx.restore();

  /* ── cor por família ─────────────────────────────────── */
  const FAM_COL = {
    gemma:"#4285f4", qwen:"#2dca8c", phi:"#0ea5e9", mistral:"#fa520f",
    deepseek:"#818cf8", granite:"#60a5fa", ernie:"#f472b6",
    glm:"#a78bfa", nemotron:"#84cc16", openai:"#34d399", rnj:"#fb923c",
    olmo:"#f97316", seed:"#fbbf24", lfm:"#38bdf8", liquid:"#38bdf8",
  };
  const getCol = (r) => {
    const f = (r.family || r.model_id || "").toLowerCase();
    for (const [k, c] of Object.entries(FAM_COL)) if (f.includes(k)) return c;
    return "#38d6a5";
  };

  /* ── bolhas ──────────────────────────────────────────── */
  const sorted = [...rows].sort((a, b) => (a.net_score ?? 0) - (b.net_score ?? 0));
  sorted.forEach((r) => {
    const x = toX(r.net_score ?? 0), y = toY(r.accuracy ?? 0);
    const rad = 6 + Math.min(10, (r.scored || 0) * 0.7);
    const col = getCol(r);
    ctx.fillStyle = col + "33";
    ctx.beginPath(); ctx.arc(x, y, rad + 3, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = col + "cc";
    ctx.beginPath(); ctx.arc(x, y, rad, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = col; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.arc(x, y, rad, 0, Math.PI * 2); ctx.stroke();
  });

  /* ── seleciona quem rotular ──────────────────────────── */
  // top-5 pts, top-3 accuracy, 1 "rápido" (menor latência com scored>0)
  const byPts  = [...rows].sort((a, b) => (b.net_score ?? 0) - (a.net_score ?? 0));
  const byAcc  = [...rows].sort((a, b) => (b.accuracy ?? 0) - (a.accuracy ?? 0));
  const byLat  = [...rows].filter((r) => r.avg_latency_ms).sort((a, b) => a.avg_latency_ms - b.avg_latency_ms);
  const toLabel = new Map();
  [...byPts.slice(0, 5), ...byAcc.slice(0, 3), ...byLat.slice(0, 1)].forEach((r) => {
    if (!toLabel.has(r.model_id)) toLabel.set(r.model_id, r);
  });

  /* ── rótulos com linha guia ──────────────────────────── */
  [...toLabel.values()].forEach((r, i) => {
    const x = toX(r.net_score ?? 0), y = toY(r.accuracy ?? 0);
    const rad = 6 + Math.min(10, (r.scored || 0) * 0.7);
    const col = getCol(r);
    // posição do label: alterna direita/esquerda/cima
    const offsets = [[24,-20],[24,16],[-24,-20],[-24,16],[0,-28],[0,28],[30,0],[-30,0]];
    const [ox, oy] = offsets[i % offsets.length];
    const lx = x + ox * 2.4, ly = y + oy * 2.4;
    // linha guia
    ctx.strokeStyle = col + "88"; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(x + (ox > 0 ? rad : -rad), y); ctx.lineTo(lx, ly); ctx.stroke();
    // caixa do rótulo
    const name = (r.display_name || r.model_id).replace(/^[^/]+\//, "");
    const tag  = `${r.net_score ?? "?"}pts · ${Math.round((r.accuracy ?? 0) * 100)}%`;
    ctx.font = F(11, true);
    const nw = ctx.measureText(name).width;
    ctx.font = F(10);
    const tw = Math.max(nw, ctx.measureText(tag).width) + 14;
    const th = 34, bx = lx - (ox >= 0 ? 0 : tw), by = ly - (oy >= 0 ? 0 : th);
    ctx.fillStyle = "#0d1525ee";
    _roundRect(ctx, bx - 2, by - 2, tw + 4, th + 4, 6); ctx.fill();
    ctx.strokeStyle = col + "66"; ctx.lineWidth = 1;
    ctx.strokeRect(bx - 2, by - 2, tw + 4, th + 4);
    ctx.fillStyle = "#e8edf5"; ctx.font = F(11, true); ctx.textAlign = "left";
    ctx.fillText(name, bx + 6, by + 14);
    ctx.fillStyle = col; ctx.font = F(10);
    ctx.fillText(tag, bx + 6, by + 28);
  });

  /* ── legenda de tamanho ──────────────────────────────── */
  ctx.fillStyle = "#8090a8"; ctx.font = F(10); ctx.textAlign = "left";
  ctx.fillText("○ tamanho = jogos pontuados", ML, MT + PH + 46);

  /* ── rodapé ──────────────────────────────────────────── */
  ctx.fillStyle = "#404a60"; ctx.font = F(10); ctx.textAlign = "center";
  ctx.fillText("github.com/Phemassa/copamind-2026  •  CopaMind 2026  •  dados oficiais FIFA", W / 2, H - 4);

  return canvas;
}

async function exportLinkedInImage() {
  const phase = activeCapturePhase || defaultCapturePhase();

  // Gráfico de dispersão
  if (phase === "__scatter__") {
    const btn = document.getElementById("btn-export-linkedin");
    const origText = btn.textContent;
    btn.textContent = "Gerando..."; btn.disabled = true;
    try {
      const logo = await _loadImg("../../docs/assets/copamind_2026.png");
      const canvas = buildScatterCanvas(scatterRows(), logo);
      const date = new Date().toISOString().slice(0, 10).replace(/-/g, "");
      await _canvasDownload(canvas, `copamind_scatter_${date}.png`);
    } catch (err) {
      console.error(err); alert(`Erro ao exportar gráfico: ${err?.message || err}`);
    } finally { btn.textContent = origText; btn.disabled = false; }
    return;
  }
  const rows  = linkedInRows(phase);
  if (!rows.length) {
    alert("Sem palpites validos para exportar nesta fase. Processe os modelos primeiro.");
    return;
  }
  const btn = document.getElementById("btn-export-linkedin");
  const origText = btn.textContent;
  btn.textContent = "Gerando...";
  btn.disabled = true;
  try {
    // Load banner icon and all model icons in parallel
    const modelUrls = rows.map((row) => resolveModelImage(row) || avatarForModel(row));
    const [icon, ...rawIcons] = await Promise.all([
      _loadImg("../../docs/assets/copamind_2026.png"),
      ...modelUrls.map((url) => _loadImg(url)),
    ]);
    // Fallback to SVG avatar if real image failed
    const modelIcons = await Promise.all(
      rows.map(async (row, i) => rawIcons[i] || await _loadImg(avatarForModel(row))),
    );
    const iconMap = new Map(rows.map((row, i) => [row.model_id, modelIcons[i]]));

    const canvas = buildLinkedInCanvas(rows, phase, icon, iconMap);
    const date = new Date().toISOString().slice(0, 10).replace(/-/g, "");
    const filename = `copamind_resumo_${phase}_${date}.png`;
    // toBlob é mais confiável que toDataURL para canvas grandes (sem limite de tamanho da data-URL)
    await new Promise((resolve, reject) => {
      canvas.toBlob((blob) => {
        if (!blob) { reject(new Error("canvas.toBlob retornou null — canvas muito grande ou bloqueado")); return; }
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.download = filename;
        link.href = url;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        setTimeout(() => URL.revokeObjectURL(url), 10000);
        resolve();
      }, "image/png");
    });
  } catch (err) {
    console.error(`[exportLinkedInImage] fase=${phase} rows=${rows.length} erro:`, err);
    alert(`Erro ao gerar imagem (${phase}): ${err?.message || err}`);
  } finally {
    btn.textContent = origText;
    btn.disabled = false;
  }
}

function renderLinkedInCaptures() {
  if (!state) return;
  const phase = currentCapturePhase();
  renderLinkedInPhaseTabs(phase);

  // ── Gráfico de dispersão acurácia × pontos ────────────────────────────────
  if (phase === "__scatter__") {
    renderScatterChart();
    return;
  }
  renderLinkedInPhaseTabs(phase);
  const rows = linkedInRows(phase);
  const phaseInfo = (state.phases || []).find((item) => item.key === phase);
  const validPredictions = rows.reduce((sum, r) => sum + r.predictions.length, 0);
  const bestJson = rows.filter((r) => r.json_rate === 1).length;
  document.getElementById("linkedin-summary").innerHTML = `
    <div><span>Fase</span><strong>${escapeHtml(phaseInfo?.label || phaseLabel(phase))}</strong></div>
    <div><span>Modelos validos</span><strong>${rows.length}</strong></div>
    <div><span>Palpites</span><strong>${validPredictions}</strong></div>
    <div><span>JSON 100%</span><strong>${bestJson}</strong></div>`;
  if (!rows.length) {
    document.getElementById("linkedin-capture-grid").innerHTML = empty("Nenhum palpite valido nesta fase ainda. Rode os modelos e exporte o snapshot.");
    return;
  }
  // Collect match order — deduplicate by team pair (home×away) to avoid
  // duplicate rows when different models used different match_id formats.
  const matchOrder = [];
  const seen = new Set();
  rows.forEach((row) => row.predictions.forEach((pred) => {
    const canonical = `${pred.home || pred.home_team_id || ""}×${pred.away || pred.away_team_id || ""}`;
    if (!seen.has(canonical)) {
      seen.add(canonical);
      matchOrder.push({ ...pred, _key: canonical });
    }
  }));
  // Helper: find a prediction for a canonical key
  const findPred = (preds, canonical) =>
    preds.find((p) => `${p.home || p.home_team_id || ""}×${p.away || p.away_team_id || ""}` === canonical);
  // Helper: find official match by team IDs (also tries match_id as fallback)
  const findOfficial = (m) =>
    (state.matches || []).find((mx) =>
      (mx.home_team_id && mx.home_team_id === m.home_team_id && mx.away_team_id === m.away_team_id)
      || mx.match_id === m.match_id,
    );
  // Compute avg win % per match across all LLMs
  const matchStats = {};
  matchOrder.forEach((m) => {
    const preds = rows
      .map((row) => findPred(row.predictions || [], m._key))
      .filter((p) => p && (p.prob_home || 0) + (p.prob_away || 0) > 0);
    if (preds.length) {
      const avgHome = preds.reduce((s, p) => s + p.prob_home / (p.prob_home + p.prob_away), 0) / preds.length;
      const home = Math.round(avgHome * 100);
      matchStats[m._key] = { home, away: 100 - home };
    }
  });
  // Ranking de equipes: avanco + campea
  renderLinkedInTeamRanking(phase, matchOrder, matchStats);

  // Mapa de resultados reais: match_key → "home"|"away"|null
  const matchResultMap = {};
  matchOrder.forEach((m) => {
    const official = findOfficial(m);
    if (official) matchResultMap[m._key] = actualWinner(official);
  });

  // Campea real (Final) e previsões por modelo
  const actualChampionId = officialWinnersForPhase("final")[0] ?? null;
  const modelChampionMap = {};
  for (const item of state.phase_predictions_by_model || []) {
    if (item.phase !== "final" || item.model_id === "combo") continue;
    for (const pred of item.predictions || []) {
      const side = predictedSide(pred);
      if (!side) continue;
      const tid = side === "away" ? pred.away_team_id : pred.home_team_id;
      if (tid) modelChampionMap[item.model_id] = tid;
    }
  }

  // Compute star counts per model (only for finished matches)
  const finishedMatchKeys = matchOrder.filter((m) => matchResultMap[m._key]).map((m) => m._key);
  const modelStarCounts = {};
  rows.forEach((row) => { modelStarCounts[row.model_id] = [0, 0, 0, 0, 0, 0]; }); // idx 0-5
  finishedMatchKeys.forEach((key) => {
    const m = matchOrder.find((x) => x._key === key);
    const actual = matchResultMap[key];
    const offMatch = findOfficial(m);
    rows.forEach((row) => {
      const pred = findPred(row.predictions || [], key);
      if (!pred) return;
      const s = starRating(pred, offMatch, actual);
      modelStarCounts[row.model_id][s]++;
    });
  });

  // Header: jogo | modelo1 | modelo2 | ...
  const modelHead = rows.map((row) => {
    const hitChampion = actualChampionId && modelChampionMap[row.model_id] === actualChampionId;
    return `
    <th class="resumo-model-header-th${hitChampion ? " resumo-champion-hit" : ""}">
      <img src="${escapeAttr(resolveModelImage(row) || avatarForModel(row))}" alt="" onerror="this.onerror=null;this.src='${avatarForModel(row)}';" />
      <div class="resumo-model-name">${escapeHtml(row.display_name)}</div>
    </th>`;
  }).join("");
  // Summary row: star counts per model
  const nFinished = finishedMatchKeys.length;
  const summaryRow = nFinished > 0 ? `<tr class="resumo-summary-row">
    <td class="resumo-match-td resumo-summary-label">
      <small>Acertos</small><b>${nFinished} jog.</b>
    </td>
    ${rows.map((row) => {
      const sc = modelStarCounts[row.model_id] || [];
      const correct = [1,2,3,4,5].reduce((s, n) => s + (sc[n] || 0), 0);
      const breakdown = [5,4,3,2,1].filter((n) => sc[n] > 0)
        .map((n) => `<span class="sc sc-${n}">${"★".repeat(n)}<i>${sc[n]}</i></span>`).join("");
      return `<td class="resumo-cell resumo-summary-cell">
        <b class="sc-total">${correct}/${nFinished}</b>${breakdown}
      </td>`;
    }).join("")}
  </tr>` : "";
  // Teams already eliminated by official results (losers of finished matches)
  const eliminatedIds = eliminatedTeamIds();

  // Body: one row per match
  const body = matchOrder.map((m) => {
    const actual = matchResultMap[m._key] ?? null;  // "home"|"away"|null
    const officialMatch = findOfficial(m);
    // Mark row as impossible if the match has no official result yet
    // but at least one team is already eliminated from the tournament
    const homeElim = m.home_team_id && eliminatedIds.has(m.home_team_id);
    const awayElim = m.away_team_id && eliminatedIds.has(m.away_team_id);
    const isImpossible = !actual && (homeElim || awayElim);
    const hasScore = officialMatch && officialMatch.home_score != null;
    const scoreDisplay = hasScore ? `${officialMatch.home_score}–${officialMatch.away_score}` : null;
    const cells = rows.map((row) => {
      const pred = findPred(row.predictions || [], m._key);
      if (!pred) return `<td class="resumo-cell resumo-empty">—</td>`;
      const side = predictedSide(pred);
      const stars = pred.star_rating != null
        ? Number(pred.star_rating)
        : starRating(pred, officialMatch, actual);
      const isWrong = actual !== null && actual !== undefined && stars === 0 && side !== actual;
      const starsStr = stars > 0 ? "★".repeat(stars) : "";
      const baseScore = `${pred.predicted_home_goals ?? "?"}–${pred.predicted_away_goals ?? "?"}`;
      let penLine = "";
      let ext = "";
      const isDrawScore = pred.predicted_home_goals != null && pred.predicted_away_goals != null
        && Number(pred.predicted_home_goals) === Number(pred.predicted_away_goals);
      if (isDrawScore && pred.goes_to_penalties && pred.penalty_winner && pred.penalty_winner !== "none") {
        const hp = pred.penalty_winner === "home" ? 4 : 3;
        const ap = pred.penalty_winner === "away" ? 4 : 3;
        penLine = `<small class="resumo-pen">(${hp}–${ap})</small>`;
      } else if (isDrawScore && pred.goes_to_extra_time) {
        ext = " ET";
      }
      const total = (pred.prob_home || 0) + (pred.prob_away || 0);
      const homeProb = total > 0 ? Math.round(pred.prob_home / total * 100) : null;
      const awayProb = total > 0 ? 100 - homeProb : null;
      return `<td class="resumo-cell resumo-${escapeAttr(side)}${stars > 0 ? ` resumo-stars-${stars}` : ""}${isWrong ? " resumo-wrong" : ""}">
        ${starsStr ? `<span class="resumo-stars-badge">${escapeHtml(starsStr)}</span>` : ""}
        <span class="resumo-cell-team${side === "home" ? " is-predicted" : ""}">
          <b>${escapeHtml(shortTeamName(m.home))}</b>${homeProb != null ? `<em>${homeProb}%</em>` : ""}
        </span>
        <b class="resumo-cell-score">${escapeHtml(baseScore)}${ext}</b>${penLine}
        <span class="resumo-cell-team${side === "away" ? " is-predicted" : ""}">
          <b>${escapeHtml(shortTeamName(m.away))}</b>${awayProb != null ? `<em>${awayProb}%</em>` : ""}
        </span>
      </td>`;
    }).join("");
    return `<tr${isImpossible ? ' class="resumo-impossible"' : ''}>
      <td class="resumo-match-td">
        <div class="resumo-match-inline">
          <span class="resumo-match-team${actual === "home" ? " is-winner" : ""}">
            <b>${escapeHtml(shortTeamName(m.home))}</b>
          </span>
          ${scoreDisplay
            ? `<span class="resumo-match-score">${scoreDisplay}</span>`
            : `<span class="resumo-match-vs">×</span>`}
          <span class="resumo-match-team${actual === "away" ? " is-winner" : ""}">
            <b>${escapeHtml(shortTeamName(m.away))}</b>
          </span>
        </div>
      </td>
      ${cells}
    </tr>`;
  }).join("");
  const legendItems = [
    ["★",     "Acertou o vencedor"],
    ["★★",    "+ 1 gol certo"],
    ["★★★",   "Placar exato"],
    ["★★★★",  "+ Tempo (normal/ET/pen)"],
    ["★★★★★", "Tudo certo!"],
  ];
  const legendHtml = legendItems.map(([s, l]) =>
    `<span class="resumo-star-legend-item"><span>${s}</span>${escapeHtml(l)}</span>`,
  ).join("");
  document.getElementById("linkedin-capture-grid").innerHTML = `
    <div class="resumo-table-wrapper">
      <table class="resumo-table">
        <thead><tr><th class="resumo-game-header-th"></th>${modelHead}</tr></thead>
        <tbody>${summaryRow}${body}</tbody>
      </table>
    </div>
    <div class="resumo-star-legend">${legendHtml}</div>`;
}

function shortTeamName(name) {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  return parts[0].length <= 8 ? parts[0] : parts[0].slice(0, 3).toUpperCase();
}

function renderLinkedInTeamRanking(phase, matchOrder, matchStats) {
  const container = document.getElementById("linkedin-team-ranking");
  if (!container) return;
  if (!matchOrder.length) { container.innerHTML = ""; return; }

  const isFinal = phase === "final";
  const isThirdPlace = phase === "third_place";
  const isSemifinal = phase === "semifinal";

  // Label da coluna de avanco (proxima fase / campea / 3o lugar / final)
  const advanceLabel = isFinal
    ? "Vencer final = Campeã"
    : isThirdPlace
      ? "Vencer = 3º lugar"
      : isSemifinal
        ? "→ Final"
        : "Próxima fase";
  const advanceTooltip = isFinal
    ? "% dos modelos que prevêm esta seleção vencendo a Final (soma 100%)"
    : isThirdPlace
      ? "Probabilidade média dos modelos de vencer a disputa pelo 3º lugar"
      : isSemifinal
        ? "Probabilidade média dos modelos de esta seleção VENCER a semifinal e ir à Final. Quem perder disputa o 3º lugar."
        : "Probabilidade média dos modelos de avançar (vencer esta partida)";

  // Monta mapa team_id → { advance (média), name, flag_url }
  // Filtra apenas partidas que correspondem a matches OFICIAIS da fase
  const phaseOfficialMatches = (state.matches || []).filter((m) => m.stage === phase);
  const officialTeamPairs = new Set(phaseOfficialMatches.map((m) => `${m.home_team_id}|${m.away_team_id}`));
  const advanceAccum = {}; // team_id → { sumAdv, count, name, flag_url }
  matchOrder.forEach((m) => {
    const stats = matchStats[m._key];
    if (!stats) return;
    // Se há partidas oficiais, pula projeções com times que não fazem parte delas
    if (phaseOfficialMatches.length > 0) {
      const hId = m.home_team_id || "";
      const aId = m.away_team_id || "";
      if (!hId || !aId || !officialTeamPairs.has(`${hId}|${aId}`)) return;
    }
    const addSide = (teamId, name, flagUrl, pct) => {
      if (!teamId) return;
      if (!advanceAccum[teamId]) advanceAccum[teamId] = { sumAdv: 0, count: 0, name: name || teamId, flag_url: flagUrl || "" };
      advanceAccum[teamId].sumAdv += pct / 100;
      advanceAccum[teamId].count += 1;
    };
    addSide(m.home_team_id, m.home, m.home_flag_url, stats.home);
    addSide(m.away_team_id, m.away, m.away_flag_url, stats.away);
  });
  const advanceByTeam = Object.fromEntries(
    Object.entries(advanceAccum).map(([id, d]) => [id, { name: d.name, flag_url: d.flag_url, advance: d.sumAdv / d.count }])
  );

  // ── Final: usa votos de campeão (share de "vence a final") ──────────────────
  // Cada modelo tem 1 voto → porcentagem real, soma 100%, Noruega some se nenhum modelo a elegeu.
  // ── Outras fases: usa média de win% por partida projetada ────────────────────
  let rankRows;
  let maxAdvance;
  if (isFinal) {
    const finalVoteRows = winnerVotesForPhase("final");
    rankRows = finalVoteRows
      .filter((r) => r.votes > 0)
      .map((r) => ({ team_id: r.team_id, name: r.name, flag_url: r.flag_url, advance: r.share, champion: null }));
    maxAdvance = 1;
  } else {
    // Champion probability: prefer final phase votes over accumulated title score.
    const finalVoteRows = winnerVotesForPhase("final");
    const totalFinalVotes = finalVoteRows.reduce((s, r) => s + r.votes, 0);
    const finalChampionMap = totalFinalVotes > 0
      ? Object.fromEntries(finalVoteRows.map((r) => [r.team_id, r.votes / totalFinalVotes]))
      : null;

    const titleMap = Object.fromEntries(teamTitleRows().map((r) => [r.team_id, r]));

    rankRows = Object.entries(advanceByTeam)
      .map(([teamId, info]) => {
        const title = titleMap[teamId] || {};
        const champion = isThirdPlace
          ? null
          : finalChampionMap
            ? (finalChampionMap[teamId] ?? 0)
            : (title.chance ?? 0);
        return {
          team_id: teamId,
          name: title.name || info.name,
          flag_url: title.flag_url || info.flag_url,
          advance: info.advance,
          champion,
        };
      })
      .sort((a, b) =>
        isThirdPlace
          ? b.advance - a.advance
          : (b.champion ?? 0) - (a.champion ?? 0) || b.advance - a.advance
      );
    maxAdvance = Math.max(...rankRows.map((r) => r.advance), 0.01);
  }

  const finalVoteRowsForLabel = winnerVotesForPhase("final");
  const hasFinalVotes = finalVoteRowsForLabel.some((r) => r.votes > 0);
  const championSourceLabel = hasFinalVotes
    ? "% dos modelos que prevêm esta seleção campeã (votos na Final)"
    : "Score combinado: votos LLM em todas as fases + perfil estatístico";
  const maxChampion = Math.max(...rankRows.map((r) => r.champion ?? 0), 0.01);
  const showChampion = !isFinal && !isThirdPlace;

  container.innerHTML = `
    <div class="team-phase-ranking">
      <div class="team-ranking-header">
        <p>Previsão das LLMs</p>
        <h3>Chances por seleção</h3>
      </div>
      <div class="team-ranking-grid ${showChampion ? "" : "team-ranking-grid--single"}">
        <div class="team-ranking-head">
          <span>#</span>
          <span>Seleção</span>
          <span title="${escapeAttr(advanceTooltip)}">${escapeHtml(advanceLabel)}</span>
          ${showChampion ? `<span title="${escapeAttr(championSourceLabel)}">Campeã${hasFinalVotes ? " (via Final)" : " (acum.)*"}</span>` : ""}
        </div>
        ${rankRows.map((row, i) => `
          <div class="team-ranking-row">
            <span class="team-ranking-pos">${i + 1}</span>
            <div class="team-ranking-id">
              <img src="${escapeAttr(row.flag_url)}" alt="" />
              <strong>${escapeHtml(row.name)}</strong>
            </div>
            <div class="team-ranking-advance">
              <span>${pct(row.advance)}</span>
              <div class="team-ranking-bar"><div style="width:${Math.round(row.advance / maxAdvance * 100)}%"></div></div>
            </div>
            ${showChampion ? `
            <div class="team-ranking-champion">
              <b>${pct(row.champion ?? 0)}</b>
              <div class="team-ranking-bar team-ranking-bar--gold"><div style="width:${Math.round((row.champion ?? 0) / maxChampion * 100)}%"></div></div>
            </div>` : ""}
          </div>`).join("")}
      </div>
      ${!hasFinalVotes && showChampion ? `<p class="team-ranking-note">* Sem previsões da Final ainda. Campeã calculado por votos acumulados em todas as fases + perfil estatístico.</p>` : ""}
    </div>`;
}

function renderLinkedInPhaseTabs(selectedPhase) {
  const phases = (state.phases || []).filter((phase) => linkedInRows(phase.key).length > 0);
  const scatterActive = selectedPhase === "__scatter__";
  document.getElementById("linkedin-phase-tabs").innerHTML = phases.map((phase) => `
    <button class="${phase.key === selectedPhase ? "active" : ""}" type="button" data-linkedin-phase="${escapeAttr(phase.key)}">
      ${escapeHtml(phase.label)}
    </button>
  `).join("") + `<button class="${scatterActive ? "active" : ""}" type="button" data-linkedin-phase="__scatter__">📊 Acurácia × Pts</button>`;
  document.querySelectorAll("[data-linkedin-phase]").forEach((button) => {
    button.addEventListener("click", () => {
      activeCapturePhase = button.dataset.linkedinPhase;
      renderLinkedInCaptures();
    });
  });
}

function linkedInRows(phase) {
  const scoreByModel = Object.fromEntries(
    (state.phase_model_scores || [])
      .filter((item) => item.phase === phase)
      .map((item) => [item.model_id, item])
  );
  const statusByModel = Object.fromEntries(
    (state.phase_model_run_status || [])
      .filter((item) => item.phase === phase)
      .map((item) => [item.model_id, item])
  );
  const modelById = Object.fromEntries((state.models || []).map((model) => [model.model_id, model]));
  return (state.phase_predictions_by_model || [])
    .filter((item) => item.phase === phase && item.model_id !== "combo")
    .map((item) => {
      const predictions = (item.predictions || []).filter(isValidPrediction);
      if (!predictions.length) return null;
      const score = scoreByModel[item.model_id] || {};
      const status = statusByModel[item.model_id] || {};
      const model = modelById[item.model_id] || {};
      const runs = Number(status.runs || model.telemetry?.runs || predictions.length || 0);
      const validRuns = Number(status.valid_runs || predictions.length || 0);
      return {
        model_id: item.model_id,
        display_name: model.display_name || item.display_name || item.model_id,
        family: model.family || "",
        image_url: model.image_url || "",
        predictions,
        points: Number(score.points || 0),
        scored: Number(score.scored || 0),
        accuracy: score.accuracy ?? null,
        json_rate: runs ? validRuns / runs : 1,
        avg_latency_ms: model.telemetry?.avg_latency_ms,
        avg_tokens_per_second: model.telemetry?.avg_tokens_per_second,
      };
    })
    .filter(Boolean)
    .sort((a, b) => (
      b.points - a.points
      || Number(b.json_rate || 0) - Number(a.json_rate || 0)
      || Number(b.avg_tokens_per_second || 0) - Number(a.avg_tokens_per_second || 0)
      || a.display_name.localeCompare(b.display_name)
    ));
}

function linkedInModelCard(row) {
  return `
    <article class="linkedin-model-card">
      <div class="linkedin-model-head">
        <img src="${escapeAttr(resolveModelImage(row) || avatarForModel(row))}" alt="" onerror="this.onerror=null;this.src='${avatarForModel(row)}';" />
        <div>
          <span>${escapeHtml(row.family || "modelo local")}</span>
          <strong title="${escapeAttr(row.model_id)}">${escapeHtml(row.display_name)}</strong>
        </div>
        <em>${row.scored ? `${row.points} pts` : "previsao"}</em>
      </div>
      <div class="linkedin-model-metrics">
        <span>JSON ${pct(row.json_rate)}</span>
        <span>${row.scored ? `Acerto ${pct(row.accuracy)}` : `${row.predictions.length} palpites`}</span>
        <span>${num(row.avg_tokens_per_second, 1)} tok/s</span>
      </div>
      <div class="linkedin-predictions">
        ${row.predictions.map(linkedInPredictionLine).join("")}
      </div>
    </article>`;
}

function linkedInPredictionLine(prediction) {
  const winner = predictedWinnerLabel(prediction);
  const confidence = prediction.confidence == null ? "" : ` | conf. ${pct(prediction.confidence)}`;
  const markers = [
    prediction.goes_to_extra_time ? "prorrogacao" : "",
    prediction.goes_to_penalties ? "penaltis" : "",
  ].filter(Boolean).join(" + ");
  return `
    <div class="linkedin-prediction-line">
      <div>
        <strong>${escapeHtml(prediction.home)} x ${escapeHtml(prediction.away)}</strong>
        <span>${escapeHtml(winner)}${confidence}</span>
      </div>
      <b>${predictionScore(prediction)}</b>
      ${markers ? `<em>${escapeHtml(markers)}</em>` : ""}
    </div>`;
}

function isValidPrediction(prediction) {
  return prediction
    && prediction.has_prediction !== false
    && prediction.predicted_home_goals != null
    && prediction.predicted_away_goals != null
    && prediction.status !== "invalid";
}

function predictedWinnerLabel(prediction) {
  const side = predictedSide(prediction);
  if (side === "home") return prediction.home || "Mandante";
  if (side === "away") return prediction.away || "Visitante";
  return "Empate no tempo normal";
}

function predictionScore(prediction) {
  const home = prediction.predicted_home_goals ?? "-";
  const away = prediction.predicted_away_goals ?? "-";
  const isDrawScore = prediction.predicted_home_goals != null && prediction.predicted_away_goals != null
    && Number(prediction.predicted_home_goals) === Number(prediction.predicted_away_goals);
  if (isDrawScore && prediction.goes_to_penalties && prediction.penalty_winner && prediction.penalty_winner !== "none") {
    const homePen = prediction.penalty_winner === "home" ? 4 : 3;
    const awayPen = prediction.penalty_winner === "away" ? 4 : 3;
    return `${home} (${homePen}) - ${away} (${awayPen})`;
  }
  return `${home} - ${away}`;
}

function currentCapturePhase() {
  const phase = activeCapturePhase || defaultCapturePhase();
  activeCapturePhase = phase;
  return phase;
}

function defaultCapturePhase() {
  const phases = state?.phases || [];
  const withPredictions = phases.find((phase) => (
    (state.phase_predictions_by_model || []).some((item) => (
      item.phase === phase.key
      && item.model_id !== "combo"
      && (item.predictions || []).some(isValidPrediction)
    ))
  ));
  return withPredictions?.key || activePhase || phases[0]?.key || "quarterfinal";
}

function renderContextInputs() {
  if (!state) return;
  renderContextInputOptions();
  renderContextNotesList();
}

function renderContextInputOptions() {
  const phaseSelect = document.getElementById("note-phase");
  const teamSelect = document.getElementById("note-team");
  const availableInput = document.getElementById("note-available-at");
  if (!phaseSelect || !teamSelect) return;
  const phaseOptions = (state.phases || []).map((phase) => `
    <option value="${escapeAttr(phase.key)}">${escapeHtml(phase.label)}</option>
  `).join("");
  const teamOptions = (state.teams || [])
    .slice()
    .sort((a, b) => String(a.name).localeCompare(String(b.name)))
    .map((team) => `<option value="${escapeAttr(team.team_id)}">${escapeHtml(team.name)}</option>`)
    .join("");
  if (phaseSelect.dataset.rendered !== phaseOptions) {
    phaseSelect.innerHTML = phaseOptions;
    phaseSelect.value = activePhase;
    phaseSelect.dataset.rendered = phaseOptions;
  }
  if (teamSelect.dataset.rendered !== teamOptions) {
    teamSelect.innerHTML = teamOptions;
    teamSelect.dataset.rendered = teamOptions;
  }
  if (availableInput && !availableInput.value) {
    availableInput.value = localDateTimeValue(new Date());
  }
}

function renderContextNotesList() {
  const container = document.getElementById("context-notes-list");
  if (!container) return;
  const notes = (state.context_notes || []).slice().sort((a, b) => (
    Number(Boolean(b.active)) - Number(Boolean(a.active))
    || String(b.available_at || "").localeCompare(String(a.available_at || ""))
  ));
  container.innerHTML = notes.map((note) => `
    <article class="context-note-card ${note.active ? "" : "is-inactive"}">
      <div>
        <span>${escapeHtml(note.phase_label || phaseLabel(note.phase))} | ${escapeHtml(note.team_name || note.team_id)}</span>
        <strong>${escapeHtml(note.title)}</strong>
        <p>${escapeHtml(note.note_text)}</p>
      </div>
      <dl>
        <div><dt>Tipo</dt><dd>${escapeHtml(noteTypeLabel(note.note_type))}</dd></div>
        <div><dt>Impacto</dt><dd>${escapeHtml(impactLabel(Object.keys(note.impact || {})[0]))}</dd></div>
        <div><dt>Disponivel</dt><dd>${formatDateTime(note.available_at)}</dd></div>
        <div><dt>Peso</dt><dd>${pct(note.weight)}</dd></div>
      </dl>
      <div class="context-note-actions">
        <span>${note.active ? "ativa" : "inativa"} | fonte: ${escapeHtml(note.source || "manual")}</span>
        ${note.active ? `<button type="button" data-delete-context-note="${escapeAttr(note.note_id)}">Desativar</button>` : ""}
      </div>
    </article>
  `).join("") || empty("Nenhum input contextual cadastrado ainda.");
  document.querySelectorAll("[data-delete-context-note]").forEach((button) => {
    button.addEventListener("click", () => deactivateContextNote(button.dataset.deleteContextNote));
  });
}

async function extractFromUrl() {
  const url = document.getElementById("note-source-url")?.value.trim();
  const phase = document.getElementById("note-phase")?.value;
  const teamId = document.getElementById("note-team")?.value;
  if (!url) { setContextNoteStatus("Cole uma URL no campo antes de extrair."); return; }
  if (!phase || !teamId) { setContextNoteStatus("Selecione fase e selecao antes de extrair."); return; }
  const btn = document.getElementById("btn-extract-url");
  if (btn) { btn.disabled = true; btn.textContent = "Extraindo..."; }
  setContextNoteStatus("Buscando URL e chamando LLM...");
  try {
    const response = await fetch(`${API_BASE}/pool/context-notes/extract`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, phase, team_id: teamId }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }
    const data = await response.json();
    if (data.note_type) document.getElementById("note-type").value = data.note_type;
    if (data.title) document.getElementById("note-title").value = data.title;
    if (data.note_text) document.getElementById("note-text").value = data.note_text;
    if (data.impact_key) document.getElementById("note-impact").value = data.impact_key;
    if (data.confidence != null) document.getElementById("note-confidence").value = data.confidence;
    if (data.weight != null) document.getElementById("note-weight").value = data.weight;
    if (data.source) document.getElementById("note-source").value = data.source;
    if (data.available_at) {
      try { document.getElementById("note-available-at").value = localDateTimeValue(new Date(data.available_at)); } catch (_) {}
    }
    setContextNoteStatus("Formulario preenchido pela LLM. Revise e salve.");
  } catch (error) {
    setContextNoteStatus(`Erro na extracao: ${error.message}`);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = "Extrair de URL"; }
  }
}

async function saveContextNote(event) {
  event.preventDefault();
  const status = document.getElementById("context-note-status");
  setContextNoteStatus("Salvando input...");
  const impactKey = document.getElementById("note-impact")?.value || "manual_context";
  const availableAt = document.getElementById("note-available-at")?.value;
  const payload = {
    phase: document.getElementById("note-phase")?.value,
    team_id: document.getElementById("note-team")?.value,
    note_type: document.getElementById("note-type")?.value || "team_news",
    title: document.getElementById("note-title")?.value.trim(),
    note_text: document.getElementById("note-text")?.value.trim(),
    impact: {
      [impactKey]: true,
      label: impactLabel(impactKey),
    },
    source: document.getElementById("note-source")?.value.trim() || "manual",
    source_url: document.getElementById("note-source-url")?.value.trim() || null,
    confidence: Number(document.getElementById("note-confidence")?.value || 0.75),
    weight: Number(document.getElementById("note-weight")?.value || 0.7),
    available_at: availableAt ? new Date(availableAt).toISOString() : null,
  };
  if (!payload.phase || !payload.team_id || !payload.title || !payload.note_text) {
    setContextNoteStatus("Preencha fase, selecao, titulo e nota.");
    return;
  }
  try {
    const response = await fetch(`${API_BASE}/pool/context-notes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    document.getElementById("note-title").value = "";
    document.getElementById("note-text").value = "";
    document.getElementById("note-source-url").value = "";
    setContextNoteStatus("Input salvo e exportacao do portal solicitada.");
    setTimeout(() => loadData(true).catch(() => {}), 1200);
  } catch (error) {
    console.error(error);
    if (status) status.textContent = "Nao consegui salvar. Confirme se a API esta ativa.";
  }
}

async function deactivateContextNote(noteId) {
  if (!noteId) return;
  setContextNoteStatus("Desativando input...");
  try {
    const response = await fetch(`${API_BASE}/pool/context-notes/${encodeURIComponent(noteId)}`, {
      method: "DELETE",
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    setContextNoteStatus("Input desativado.");
    setTimeout(() => loadData(true).catch(() => {}), 1200);
  } catch (error) {
    console.error(error);
    setContextNoteStatus("Nao consegui desativar. Confirme se a API esta ativa.");
  }
}

function setContextNoteStatus(message) {
  const status = document.getElementById("context-note-status");
  if (status) status.textContent = message;
}

function noteTypeLabel(value) {
  return {
    team_news: "Noticia",
    rotation: "Rotacao",
    injury: "Lesao",
    tactical: "Tatica",
    morale: "Moral",
    travel: "Desgaste/viagem",
  }[value] || value || "-";
}

function impactLabel(value) {
  return {
    recent_form_downweight: "Reduz peso da forma recente",
    physical_load_positive: "Melhora leitura de desgaste",
    injury_negative: "Impacto negativo por lesao",
    tactical_positive: "Impacto tatico positivo",
    volatility_up: "Aumenta incerteza",
  }[value] || value || "Contexto manual";
}

function renderTournament() {
  const container = document.getElementById("tournament-dashboard");
  if (!container || !state) return;
  const tournament = state.tournament || {};
  const matches = tournament.matches || state.matches || [];
  const stageOrder = (tournament.stage_order || ["group", "round_of_32", "round_of_16", "quarterfinal"])
    .filter((stage) => stage === "group" || matches.some((match) => match.stage === stage));
  if (!stageOrder.includes(activeTournamentStage)) {
    activeTournamentStage = stageOrder[0] || "group";
  }
  const stageMatches = matches
    .filter((match) => activeTournamentStage === "group" ? match.stage === "group" : match.stage === activeTournamentStage)
    .sort((a, b) => new Date(a.date || 0) - new Date(b.date || 0));
  container.innerHTML = `
    <div class="tournament-tabs">
      ${stageOrder.map((stage) => `
        <button class="${stage === activeTournamentStage ? "active" : ""}" type="button" data-tournament-stage="${escapeAttr(stage)}">
          ${escapeHtml(tournamentStageLabel(stage))}
        </button>
      `).join("")}
    </div>
    ${activeTournamentStage === "group" ? tournamentGroupsView(tournament.groups || []) : ""}
    <div class="section-title tournament-match-title">
      <p>${escapeHtml(tournamentStageLabel(activeTournamentStage))}</p>
      <h3>Partidas</h3>
    </div>
    <div class="tournament-match-grid">
      ${stageMatches.map(tournamentMatchCard).join("") || empty("Sem partidas cadastradas para esta etapa.")}
    </div>`;
  document.querySelectorAll("[data-tournament-stage]").forEach((button) => {
    button.addEventListener("click", () => {
      activeTournamentStage = button.dataset.tournamentStage || "group";
      renderTournament();
    });
  });
}

function tournamentGroupsView(groups) {
  if (!groups.length) return empty("Classificacao de grupos ainda nao exportada.");
  return `
    <div class="groups-grid">
      ${groups.map((group) => `
        <article class="group-table-card">
          <h4>${escapeHtml(group.label || `Grupo ${group.group}`)}</h4>
          <div class="group-table">
            <div class="group-table-head">
              <span>#</span><span>Selecao</span><span>Pts</span><span>PJ</span><span>SG</span><span>GM</span>
            </div>
            ${(group.rows || []).map((row) => `
              <div class="group-table-row ${Number(row.rank) <= 2 ? "qualified-row" : ""}">
                <span>${row.rank}</span>
                <span><img src="${escapeAttr(row.flag_url || "")}" alt="" />${escapeHtml(row.team)}</span>
                <strong>${row.pts}</strong>
                <span>${row.pj}</span>
                <span>${row.sg}</span>
                <span>${row.gm}</span>
              </div>
            `).join("")}
          </div>
        </article>
      `).join("")}
    </div>`;
}

function tournamentMatchCard(match) {
  const score = matchScore(match);
  const markers = matchMarkers(match);
  return `
    <article class="tournament-match-card">
      <div class="match-teams">
        ${teamLine(match.home, match.home_flag_url, match.home_score)}
        <div class="versus">${score}</div>
        ${teamLine(match.away, match.away_flag_url, match.away_score)}
      </div>
      <div class="match-meta">
        <span>${formatDateTime(match.date)}</span>
        <span>${escapeHtml(statusLabel(match.status))}${markers ? ` | ${escapeHtml(markers)}` : ""}</span>
      </div>
    </article>`;
}

function tournamentStageLabel(stage) {
  return (state.tournament?.stage_labels || {})[stage] || phaseLabel(stage);
}

function winnerVotesForPhase(phase) {
  const votes = {};
  for (const prediction of allValidPredictions().filter((item) => item.phase === phase)) {
    const side = predictedSide(prediction);
    const teamId = side === "away" ? prediction.away_team_id : prediction.home_team_id;
    if (!teamId) continue;
    votes[teamId] ||= { team_id: teamId, votes: 0 };
    votes[teamId].votes += 1;
  }
  const total = Object.values(votes).reduce((sum, row) => sum + row.votes, 0);
  return Object.values(votes)
    .map((row) => ({ ...teamRef(row.team_id), votes: row.votes, share: total ? row.votes / total : 0 }))
    .sort((a, b) => b.votes - a.votes || teamProfile(b) - teamProfile(a));
}

function officialWinnersForPhase(phase) {
  return matchesForPhase(phase)
    .map((match) => {
      const winner = actualWinner(match);
      if (!winner) return null;
      return winner === "home" ? match.home_team_id : match.away_team_id;
    })
    .filter(Boolean);
}

function teamVoteLine(row, officialWinners) {
  const official = officialWinners.includes(row.team_id);
  return `
    <div class="team-vote-line ${official ? "is-official" : ""}">
      <img src="${escapeAttr(row.flag_url || "")}" alt="" />
      <span>${escapeHtml(row.name)}</span>
      <strong>${row.votes} votos</strong>
      <em>${pct(row.share)}</em>
    </div>`;
}

function teamTitleRows() {
  const teamVotes = {};
  for (const phase of ["quarterfinal", "semifinal", "third_place", "final"]) {
    for (const row of winnerVotesForPhase(phase)) {
      teamVotes[row.team_id] = (teamVotes[row.team_id] || 0) + row.votes;
    }
  }
  const eliminated = eliminatedTeamIds();
  const maxVotes = Math.max(1, ...Object.values(teamVotes));
  return (state.teams || [])
    .map((team) => {
      const profile = Number(team.analytics?.indexes?.champion_profile_score || 0);
      const votes = teamVotes[team.team_id] || 0;
      const isEliminated = eliminated.has(team.team_id);
      const voteScore = votes / maxVotes;
      const chance = isEliminated ? profile * 0.08 : Math.min(1, voteScore * 0.68 + profile * 0.32);
      return {
        team_id: team.team_id,
        name: team.name,
        flag_url: team.flag_url,
        votes,
        profile,
        chance,
        eliminated: isEliminated,
        status: isEliminated ? "eliminada" : teamStatus(team.team_id),
      };
    })
    .sort((a, b) => Number(a.eliminated) - Number(b.eliminated) || b.chance - a.chance || b.votes - a.votes || b.profile - a.profile);
}

function eliminatedTeamIds() {
  const ids = new Set();
  for (const match of state.matches || []) {
    const winner = actualWinner(match);
    if (!winner) continue;
    ids.add(winner === "home" ? match.away_team_id : match.home_team_id);
  }
  return ids;
}

function teamStatus(teamId) {
  const next = (state.matches || []).find((match) => (
    (match.home_team_id === teamId || match.away_team_id === teamId)
    && (match.status !== "finished" || match.home_score == null || match.away_score == null)
  ));
  return next ? phaseLabel(next.stage) : "viva / projetada";
}

function teamProfile(team) {
  return Number(team?.analytics?.indexes?.champion_profile_score || 0);
}

function accuracySortValue(value) {
  return value == null ? -1 : Number(value);
}

function brierSortValue(value) {
  return value == null ? 999 : Number(value);
}

async function runModelPhase(modelId) {
  const phase = activePhase;
  const key = runKey(phase, modelId);
  const previousPredictionCount = countModelPhasePredictions(phase, modelId);
  const previousSnapshot = state?.generated_at || "";
  runningRuns.set(key, {
    phase,
    modelId,
    previousPredictionCount,
    previousSnapshot,
    startedAt: Date.now(),
    timer: null,
  });
  renderModels();
  const button = document.querySelector(`[data-run-model="${cssEscape(modelId)}"]`);
  if (button) {
    button.disabled = true;
    button.textContent = "Iniciando...";
  }
  try {
    const response = await fetch(`${API_BASE}/pool/llm/phase/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        phase,
        model_id: modelId,
        samples: 1,
        include_heavy: true,
        finished_only: false,
      }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    startRunPolling(key);
    if (button) button.textContent = "Rodando... atualizando";
  } catch (error) {
    stopRunPolling(key);
    if (button) {
      button.disabled = false;
      button.textContent = "API offline";
      button.title = "Inicie a API: uvicorn copamind.api.app:app --reload --port 8000";
    }
  }
}

async function runAllModelsForPhase() {
  if (!canRunAllModelsForPhase()) return;
  if (runningRuns.has(runKey(activePhase, "__all__"))) return;

  const phase = activePhase;
  try {
    const response = await fetch(`${API_BASE}/pool/llm/phase/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      // Sem model_id → servidor roda todos os modelos pendentes num unico subprocess.
      // Resiliente a reload de pagina: recoverLatestBulkProgress retoma automaticamente.
      body: JSON.stringify({ phase, samples: 1, include_heavy: true, finished_only: false }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    const batchId = payload.batch_id;
    if (!batchId) return;
    startBulkPolling(phase, batchId);
  } catch (_err) {
    const btn = document.getElementById("run-all-models");
    if (btn) {
      btn.disabled = false;
      btn.textContent = "API offline";
      btn.title = "Inicie a API: copamind api serve";
    }
  }
}

function cancelSequentialBatch() {
  if (sequentialBatch) sequentialBatch.aborted = true;
}

async function runOneModelAndWait(modelId, phase) {
  try {
    const response = await fetch(`${API_BASE}/pool/llm/phase/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phase, model_id: modelId, samples: 1, include_heavy: true, finished_only: false }),
    });
    if (!response.ok) return;
    const payload = await response.json();
    const batchId = payload.batch_id;
    if (!batchId) return;
    await pollProgressUntilDone(batchId);
  } catch (_err) { /* pula modelo com erro */ }
}

async function pollProgressUntilDone(batchId) {
  return new Promise((resolve) => {
    const timer = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/pool/llm/phase/progress?batch_id=${encodeURIComponent(batchId)}`);
        if (!res.ok) { clearInterval(timer); resolve(); return; }
        const progress = await res.json();
        if (sequentialBatch) {
          sequentialBatch.progress = progress;
          renderModelActions();
        }
        if (isTerminalProgress(progress.status) || isStaleProgress(progress)) {
          clearInterval(timer);
          resolve();
        }
      } catch (_err) { clearInterval(timer); resolve(); }
    }, PROGRESS_POLL_MS);
    setTimeout(() => { clearInterval(timer); resolve(); }, RUN_TIMEOUT_MS);
  });
}

async function resetLLMHistory({ phase = null, modelId = null }) {
  const scope = modelId ? "este modelo nesta fase" : phase ? "esta fase" : "todo o historico das LLMs";
  if (!window.confirm(`Resetar ${scope}?`)) return;
  const previousSnapshot = state?.generated_at || "";
  try {
    const response = await fetch(`${API_BASE}/pool/llm/reset`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phase, model_id: modelId }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    await loadData(true);
    pollSnapshotAfterReset(previousSnapshot);
  } catch (error) {
    window.alert("Nao consegui resetar. Confirme se a API esta ativa na porta 8000.");
  }
}

function pollSnapshotAfterReset(previousSnapshot) {
  let attempts = 0;
  const timer = setInterval(async () => {
    attempts += 1;
    try {
      await loadData(true);
      const changed = String(state?.generated_at || "") !== String(previousSnapshot || "");
      if (changed || attempts >= 12) clearInterval(timer);
    } catch (_error) {
      if (attempts >= 12) clearInterval(timer);
    }
  }, 1000);
}

function modelRowsForPhase(phase, modelId, predictions, runStatus) {
  const hasInvalidRuns = Number(runStatus?.invalid_runs || 0) > 0;
  const issue = dominantRunIssue(runStatus);
  if (predictions.length) {
    return predictions.map((prediction) => {
      if (prediction.has_prediction !== false || !hasInvalidRuns) return prediction;
      return {
        ...prediction,
        status: issue === "lmstudio_error" ? "lmstudio_error" : "invalid_prediction",
        projection_note: issue === "lmstudio_error"
          ? "LM Studio nao carregou/aceitou o modelo"
          : "executou, mas retornou JSON invalido",
      };
    });
  }
  const projected = projectedMatchesForPhase(phase, modelId);
  const rows = projected.length ? projected : matchesForPhase(phase);
  const invalidOnly = Number(runStatus?.runs || 0) > 0 && Number(runStatus?.valid_runs || 0) === 0;
  return rows.map((match) => ({
    has_prediction: false,
    is_projection: Boolean(match.status === "projected"),
    home: match.home,
    away: match.away,
    match_date: match.date,
    status: invalidOnly ? issue === "lmstudio_error" ? "lmstudio_error" : "invalid_prediction" : "missing_prediction",
    projection_note: invalidOnly
      ? issue === "lmstudio_error"
        ? "LM Studio nao carregou/aceitou o modelo"
        : "executou, mas retornou JSON invalido"
      : match.note || "jogo oficial sem palpite deste modelo",
  }));
}

function renderTeamDashboard() {
  const teams = (state.teams || [])
    .filter((team) => team.analytics?.indexes)
    .sort((a, b) => {
      const scoreA = a.analytics?.indexes?.champion_profile_score ?? 0;
      const scoreB = b.analytics?.indexes?.champion_profile_score ?? 0;
      return scoreB - scoreA || String(a.name).localeCompare(String(b.name));
    });
  document.getElementById("teams-dashboard").innerHTML = teams.map(teamCard).join("")
    || empty("Sem analytics de seleções. Exporte o snapshot novamente.");
}

function renderPlayersDashboard() {
  renderPlayerControls();
  const rows = filteredPlayers().slice(0, 20);
  document.getElementById("players-dashboard").innerHTML = rows.map(playerCard).join("")
    || empty("Sem jogadores para este filtro. Atualize/exporte os dados FIFA.");
}

function renderPlayerControls() {
  const teamSelect = document.getElementById("player-team-filter");
  const rankingSelect = document.getElementById("player-ranking-filter");
  if (!teamSelect || !rankingSelect) return;
  const teams = [...(state.teams || [])].sort((a, b) => String(a.name).localeCompare(String(b.name)));
  const phaseOptions = (state.phases || []).map((phase) => ({
    key: `phase:${phase.key}`,
    label: `${phase.label} - selecoes da fase`,
    disabled: phaseTeams(phase.key).size === 0,
  }));
  const teamOptions = [
    `<option value="all">Todas as selecoes</option>`,
    ...teams.map((team) => `<option value="${escapeAttr(team.team_id)}">${escapeHtml(team.name)}</option>`),
  ].join("");
  const rankingOptions = [
    `<option value="top20">Top 20 geral</option>`,
    `<option value="golden_boot">Chuteira de Ouro - gols</option>`,
    ...phaseOptions.map((phase) => `
      <option value="${escapeAttr(phase.key)}" ${phase.disabled ? "disabled" : ""}>
        ${escapeHtml(phase.label)}${phase.disabled ? " (aguardando jogos)" : ""}
      </option>`),
  ].join("");
  if (teamSelect.dataset.rendered !== teamOptions) {
    teamSelect.innerHTML = teamOptions;
    teamSelect.dataset.rendered = teamOptions;
  }
  if (rankingSelect.dataset.rendered !== rankingOptions) {
    rankingSelect.innerHTML = rankingOptions;
    rankingSelect.dataset.rendered = rankingOptions;
  }
  if (![...teamSelect.options].some((option) => option.value === activePlayerTeam)) activePlayerTeam = "all";
  if (![...rankingSelect.options].some((option) => option.value === activePlayerRanking && !option.disabled)) {
    activePlayerRanking = "top20";
  }
  teamSelect.value = activePlayerTeam;
  rankingSelect.value = activePlayerRanking;
  teamSelect.onchange = () => {
    activePlayerTeam = teamSelect.value;
    renderPlayersDashboard();
  };
  rankingSelect.onchange = () => {
    activePlayerRanking = rankingSelect.value;
    renderPlayersDashboard();
  };
}

function filteredPlayers() {
  let rows = [...(state.players || [])];
  if (activePlayerTeam !== "all") {
    rows = rows.filter((player) => player.team_id === activePlayerTeam);
  }
  if (activePlayerRanking.startsWith("phase:")) {
    const phase = activePlayerRanking.split(":", 2)[1];
    const allowedTeams = phaseTeams(phase);
    rows = rows.filter((player) => allowedTeams.has(player.team_id));
  }
  return rows.sort(playerSort);
}

function phaseTeams(phase) {
  const ids = new Set();
  for (const match of matchesForPhase(phase)) {
    if (match.home_team_id) ids.add(match.home_team_id);
    if (match.away_team_id) ids.add(match.away_team_id);
  }
  return ids;
}

function playerImpact(player) {
  return Number(player.impact_score ?? player.metric_value ?? player.goals ?? 0);
}

function playerSort(a, b) {
  if (activePlayerRanking === "golden_boot") {
    return Number(b.goals || 0) - Number(a.goals || 0)
      || Number(b.assists || 0) - Number(a.assists || 0)
      || Number(a.minutes || 999999) - Number(b.minutes || 999999)
      || String(a.name).localeCompare(String(b.name));
  }
  return playerImpact(b) - playerImpact(a) || String(a.name).localeCompare(String(b.name));
}

function playerCard(player, index) {
  const per90 = player.per90 || {};
  const score = playerImpact(player);
  return `
    <article class="player-card">
      <div class="player-rank">${index + 1}</div>
      <img class="player-photo" src="${escapeAttr(player.image_url || player.flag_url || "")}" alt="" />
      <div class="player-main">
        <div class="player-title">
          <strong>${escapeHtml(player.name || "-")}</strong>
          <span>
            <img src="${escapeAttr(player.flag_url || "")}" alt="" />
            ${escapeHtml(player.team || teamRef(player.team_id).name || "-")} | ${escapeHtml(player.position || "-")}
          </span>
        </div>
        <div class="player-tags">
          <em>${escapeHtml(roleLabel(player.role))}</em>
          <em>${escapeHtml(player.reason || "impacto FIFA")}</em>
          <em>amostra ${escapeHtml(player.sample || "-")}</em>
        </div>
      </div>
      <div class="player-score">
        <strong>${num(score, 1)}</strong>
        <span>impacto</span>
      </div>
      <div class="player-stats">
        <span><b>${num(player.minutes, 0)}</b>min</span>
        <span><b>${num(player.goals, 0)}</b>gols</span>
        <span><b>${num(player.assists, 0)}</b>assist.</span>
        <span><b>${pct(player.confidence)}</b>conf.</span>
        <span><b>${num(per90.goals, 2)}</b>g/90</span>
        <span><b>${num(per90.assists, 2)}</b>a/90</span>
      </div>
    </article>`;
}

const MODEL_DESCRIPTIONS = {
  "gemma-4-e2b":              "Google Gemma 4 · 2B · instruct leve · baixo consumo de VRAM",
  "gemma-4-12b-qat":          "Google Gemma 4 · 12B · QAT · bom equilibrio qualidade/velocidade",
  "gemma-4-26b-a4b-qat":      "Google Gemma 4 · 26B MoE · QAT · alta qualidade com activation sparse",
  "gemma-4-31b-qat":          "Google Gemma 4 · 31B · QAT · modelo pesado de referencia",
  "qwen3.5-9b":               "Alibaba Qwen 3.5 · 9B · instruct · requer Structured Output",
  "qwen3.6-27b":              "Alibaba Qwen 3.6 · 27B · instruct · modelo pesado · requer Structured Output",
  "qwen3.6-35b-a3b":          "Alibaba Qwen 3.6 · 35B MoE · 3B ativos · modelo pesado · requer Structured Output",
  "phi-4-mini-reasoning":     "Microsoft Phi-4 Mini · 4B · reasoning · eficiente em raciocinio",
  "phi-4-reasoning-plus":     "Microsoft Phi-4 Reasoning Plus · 14B · chain-of-thought avancado",
  "phi-4":                    "Microsoft Phi-4 · 14B · instruct balanceado",
  "mistral-7b-instruct-v0.3": "Mistral 7B · instruct v0.3 · modelo base de referencia · requer Structured Output",
  "mistral-nemo-instruct-2407":"Mistral NeMo · 12B · instruct · contexto longo",
  "ministral-3-14b":          "Mistral Ministral · 14B · reasoning compacto",
  "devstral-small":           "Mistral Devstral Small · orientado a codigo e instrucao",
  "nemotron-3-nano-4b":       "NVIDIA Nemotron 3 Nano · 4B · ultra leve · requer Structured Output",
  "nemotron-3-nano-omni":     "NVIDIA Nemotron 3 Nano Omni · multimodal compacto · requer Structured Output",
  "olmo-3-32b-think":         "AllenAI OLMo 3 · 32B · chain-of-thought aberto · requer Structured Output",
  "glm-4.7-flash":            "ZAI GLM 4.7 Flash · 9B · instruct rapido · requer Structured Output",
  "ernie-4.5-21b-a3b":        "Baidu ERNIE 4.5 · 21B MoE · 3B ativos · modelo chines de producao",
  "lfm2-24b-a2b":             "Liquid AI LFM2 · 24B MoE · 2B ativos · arquitetura hybrid attention",
  "gpt-oss-20b":              "OpenAI GPT OSS · 20B · modelo open-source de referencia",
  "granite-4-h-tiny":         "IBM Granite 4 · tiny · instruct compacto · orientado a enterprise",
  "granite-3.2-8b":           "IBM Granite 3.2 · 8B · instruct · eficiente e confiavel",
  "deepseek-r1-0528-qwen3-8b":"DeepSeek R1 · 8B Qwen3 base · reasoning com chain-of-thought",
  "rnj-1":                    "Essential AI RNJ-1 · instruct experimental",
  "seed-oss-36b":             "ByteDance Seed OSS · 36B · modelo pesado open-source",
};

function modelDesc(modelId) {
  const id = (modelId || "").toLowerCase();
  const key = Object.keys(MODEL_DESCRIPTIONS).find((k) => id.includes(k));
  return key ? MODEL_DESCRIPTIONS[key] : null;
}

function renderReferences() {
  const container = document.getElementById("ref-models-table");
  if (!container) return;
  const models = (state?.models || []).filter((m) => !m.is_combo && m.model_class !== "embedding");
  if (!models.length) { container.innerHTML = ""; return; }
  const rows = models.map((m) => {
    const avatar = resolveModelImage(m) || avatarForModel(m);
    const fallback = avatarForModel(m);
    const desc = modelDesc(m.model_id) || `${m.family || "Local"} · ${m.model_class || "chat"}`;
    const disqualReason = DISQUALIFIED_MODELS[m.model_id];
    const badge = disqualReason
      ? `<span class="disqualified-badge" title="${escapeAttr(disqualReason)}">🚫 Desclassificado</span>`
      : needsStructuredOutput(m.model_id)
        ? `<span class="struct-output-badge" title="Necessita Structured Output no LM Studio">⚠ Struct. Output</span>`
        : "";
    return `<tr class="ref-model-row ${disqualReason ? "ref-model-disqualified" : ""}">
      <td class="ref-model-id">
        <img src="${escapeAttr(avatar)}" alt="" onerror="this.onerror=null;this.src='${escapeAttr(fallback)}';" />
        <div>
          <strong>${escapeHtml(m.display_name || m.model_id)}</strong>
          <small>${escapeHtml(m.model_id)}</small>
        </div>
      </td>
      <td class="ref-model-desc">${escapeHtml(desc)}${badge}</td>
    </tr>`;
  }).join("");
  container.innerHTML = `
    <div class="section-title" style="margin-top:18px">
      <p>Participantes do bolao</p>
      <h3>Modelos utilizados (${models.length})</h3>
    </div>
    <div class="ref-models-table-wrap">
      <table class="ref-models-tbl">
        <thead><tr><th>Modelo</th><th>Descritivo</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
}

function renderGuide() {
  const summary = state?.summary || {};
  const sync = state?.sync_status || {};
  const phases = state?.phases || [];
  const knockoutMatches = phases.reduce((total, phase) => total + Number(phase.match_count || 0), 0);
  const guide = document.getElementById("guide-dashboard");
  if (!guide) return;
  guide.innerHTML = `
    <div class="guide-hero">
      <div>
        <span>Tutor do projeto</span>
        <h2>Da FIFA ao palpite: o caminho completo</h2>
        <p>
          O CopaMind transforma dados de seleções, partidas e jogadores em um pacote estatístico enxuto.
          Esse pacote alimenta os modelos locais no LM Studio, e cada resposta vira um palpite auditável
          com telemetria, pontuação e acurácia por fase.
        </p>
      </div>
      <div class="guide-snapshot">
        <div><span>Times</span><strong>${summary.teams ?? "-"}</strong></div>
        <div><span>Jogos mata-mata</span><strong>${knockoutMatches}</strong></div>
        <div><span>Features ML</span><strong>${sync.feature_snapshots ?? 0}</strong></div>
        <div><span>Modelos</span><strong>${(state.models || []).filter((model) => !model.is_combo).length}</strong></div>
      </div>
    </div>

    <div class="guide-flow">
      ${guideStep("1", "Extração FIFA", "O portal sincroniza partidas, placares, estatísticas de equipe e estatísticas de jogador a partir da base FIFA local/atualizada.", [
        `${summary.team_tabs ?? 0} abas de equipe`,
        `${summary.player_tabs ?? 0} abas de jogador`,
        `${summary.team_rows ?? 0} linhas de seleções`,
        `${summary.player_rows ?? 0} linhas de jogadores`,
      ])}
      ${guideStep("2", "Normalização analytics", "Os CSVs não vão crus para a IA. Eles viram índices comparáveis por percentil/rank para evitar misturar escala de passes, gols, distância e cartões.", [
        "attack_index e chance_quality_index",
        "defense_index e keeper_index",
        "control_index e transition_index",
        "discipline_risk e volatility_index",
      ])}
      ${guideStep("3", "Features por jogo", "Para cada partida de mata-mata, o sistema cria um snapshot com somente o que estava disponível antes do jogo ou no momento do sync.", [
        "fixture, fase e neutralidade",
        "forma recente sem vazamento temporal",
        "jogadores-chave por papel",
        "baseline Poisson/Elo quando há histórico",
      ])}
      ${guideStep("4", "Pacote para LLM", "O agente monta um prompt compacto e igual para todos os modelos. A LLM recebe evidências, diferenças entre times e regras do bolão.", [
        "deltas home_minus_away",
        "top evidências com evidence_ids",
        "alertas de imprevisibilidade",
        "contrato JSON obrigatório",
      ])}
      ${guideStep("5", "Resposta e reparo", "Cada modelo precisa responder JSON estruturado. Se vier texto solto ou formato inválido, o agente tenta reparar a resposta uma vez.", [
        "vencedor e probabilidades",
        "placar, prorrogação e pênaltis",
        "primeiro gol e mercados de jogador",
        "confiança, rationale e coerência",
      ])}
      ${guideStep("6", "Scoring e ranking", "Quando o resultado oficial chega, o palpite é pontuado. Em mata-mata, empate no placar precisa declarar classificado por prorrogação ou pênaltis.", [
        "pontos do bolão",
        "acerto de classificado",
        "placar exato",
        "Brier score probabilístico",
      ])}
    </div>

    <div class="guide-details">
      <article>
        <h3>Como os dados viram estatística</h3>
        <p>
          Ataque combina produção real, xG, chutes no alvo e eficiência. Defesa combina gols sofridos,
          clean sheets, pressão, recuperações e exposição do goleiro. Controle mede posse, circulação,
          precisão e ruptura de linhas. Disciplina e físico entram como risco, não como prova isolada.
        </p>
        <p>
          Jogadores são avaliados por impacto por minuto/per90, papel provável e confiança da amostra.
          Um atleta com poucos minutos pode aparecer, mas marcado como amostra pequena.
        </p>
      </article>
      <article>
        <h3>O que vai no prompt</h3>
        <p>
          A chamada envia um resumo do confronto, índices das duas seleções, diferenças relativas,
          jogadores-chave, evidências, baseline estatístico e incertezas. O modelo não recebe a planilha
          inteira; recebe um pacote desenhado para raciocinar sem estourar contexto.
        </p>
        <p>
          A saída exigida inclui vencedor, probabilidades, gols, prorrogação, pênaltis, vencedor nos
          pênaltis, primeiro goleador, mercados de jogador, confiança e justificativa com evidence_ids.
        </p>
      </article>
      <article>
        <h3>Como executar no portal</h3>
        <p>
          Em Oitavas, Quartas, Semifinais, 3º lugar e Final, use “Executar todas as LLMs da fase” para rodar
          todos os modelos ativos. Em cada card, “Executar IA nesta fase” roda só aquele modelo.
        </p>
        <p>
          “Reset modelo”, “Reset fase” e “Reset geral” limpam apenas histórico das LLMs. Jogos,
          placares oficiais, estatísticas FIFA e jogadores continuam preservados.
        </p>
      </article>
    </div>

    <div class="architecture-guide" aria-label="Arquitetura do projeto">
      <div class="architecture-head">
        <p>Arquitetura CopaMind</p>
        <h3>Como o portal funciona por baixo</h3>
        <span>
          O projeto separa operacao, dados, agente e publicacao. Assim o bolao roda localmente,
          preserva historico em DuckDB e publica uma versao estatica para compartilhamento.
        </span>
      </div>

      <div class="architecture-mermaid">
        <div>
          <h4>Diagrama Mermaid</h4>
          <p>
            Este diagrama mostra o caminho principal: dados FIFA entram, viram features,
            alimentam o agente das LLMs, sao pontuados e aparecem no portal/export.
          </p>
        </div>
        <pre class="mermaid">flowchart LR
  FIFA["FIFA / cache local"] --> REFRESH["Sync de jogos, equipes e jogadores"]
  REFRESH --> DUCKDB["DuckDB local"]
  DUCKDB --> FEATURES["Features ML por partida"]
  FEATURES --> PROMPT["Prompt compacto por jogo"]
  PROMPT --> LMSTUDIO["LM Studio: modelos locais"]
  LMSTUDIO --> RUNS["llm_model_runs"]
  RUNS --> CONSENSUS["llm_model_consensus"]
  CONSENSUS --> PRED["pool_predictions"]
  DUCKDB --> SCORE["Scoring e telemetria"]
  PRED --> SCORE
  SCORE --> EXPORT["copamind.json"]
  EXPORT --> PORTAL["Portal estatico"]
  PORTAL --> HTML["Export HTML unico"]</pre>
      </div>

      <div class="architecture-map">
        <article>
          <span>01</span>
          <h4>Fontes FIFA</h4>
          <p>
            Partidas, placares, estatisticas de selecoes e estatisticas de jogadores entram pelos
            conectores e scripts de refresh. Quando a FIFA falha ou limita acesso, o app preserva
            o cache local.
          </p>
          <ul>
            <li>Jogos e status oficial</li>
            <li>CSVs de equipes por aba</li>
            <li>CSVs de jogadores por aba</li>
            <li>Fotos, bandeiras e IDs externos</li>
          </ul>
        </article>

        <article>
          <span>02</span>
          <h4>Base local DuckDB</h4>
          <p>
            O DuckDB guarda a verdade operacional: jogos, resultados, snapshots de features,
            rodadas das LLMs, chamadas individuais, consensos, payloads e pontuacao.
          </p>
          <ul>
            <li>matches e pool_results</li>
            <li>match_feature_snapshots</li>
            <li>llm_pool_rounds e llm_model_runs</li>
            <li>pool_predictions versionados</li>
          </ul>
        </article>

        <article>
          <span>03</span>
          <h4>Analytics ML</h4>
          <p>
            Os dados crus viram indices normalizados. O objetivo nao e mandar planilhas enormes
            para a IA, mas um pacote enxuto com sinais comparaveis e evidencias rastreaveis.
          </p>
          <ul>
            <li>Ataque, chance e finalizacao</li>
            <li>Defesa, goleiro e controle</li>
            <li>Disciplina, fisico e volatilidade</li>
            <li>Jogadores-chave por papel</li>
          </ul>
        </article>

        <article>
          <span>04</span>
          <h4>Agente das LLMs</h4>
          <p>
            O agente monta a mesma chamada para todos os modelos locais compativeis com chat no
            LM Studio. Cada modelo responde em JSON estruturado para permitir comparacao justa.
          </p>
          <ul>
            <li>Contexto pre-jogo sem vazamento</li>
            <li>Probabilidades e placar</li>
            <li>Prorrogacao e penaltis</li>
            <li>Telemetria de tokens e latencia</li>
          </ul>
        </article>

        <article>
          <span>05</span>
          <h4>Scoring do bolao</h4>
          <p>
            Quando o placar oficial chega, o sistema calcula pontos e metricas: vencedor correto,
            placar exato, erro de gols, total de gols, Brier, prorrogacao e penaltis.
          </p>
          <ul>
            <li>Score por fase</li>
            <li>Acuracia por modelo</li>
            <li>JSON valido e estabilidade</li>
            <li>Ranking evolutivo</li>
          </ul>
        </article>

        <article>
          <span>06</span>
          <h4>Portal e export</h4>
          <p>
            O Streamlit fica como console tecnico. O portal em HTML/CSS/JS consome o snapshot
            exportado e pode gerar um HTML unico com dados e assets embutidos.
          </p>
          <ul>
            <li>Portal publico em 8601</li>
            <li>Admin Streamlit em 8501</li>
            <li>API local em 8000</li>
            <li>HTML estatico para publicar</li>
          </ul>
        </article>
      </div>

      <div class="ml-guide" aria-label="Features ML em detalhes">
        <div class="ml-guide-head">
          <p>Features ML em detalhes</p>
          <h3>O que foi feito, qual modelo foi usado e como funciona</h3>
          <span>
            No CopaMind, "Features ML" nao significa uma rede neural treinada em segredo.
            Significa transformar muitos numeros soltos da FIFA em sinais simples, comparaveis
            e explicaveis para alimentar as LLMs locais.
          </span>
        </div>

        <div class="ml-explain-grid">
          <article>
            <h4>1. O que sao features?</h4>
            <p>
              Feature e uma caracteristica numerica que ajuda a explicar um time ou um jogo.
              Em vez de dizer apenas "Franca fez 10 gols", o sistema pergunta: esses gols vieram
              de boas chances? Foram muitos chutes certos? O time tambem defende bem?
            </p>
            <p>
              Para leigos: e como transformar uma planilha gigante em notas de boletim. Ataque,
              defesa, controle, risco e jogadores-chave viram notas de 0% a 100%.
            </p>
          </article>

          <article>
            <h4>2. Qual modelo foi utilizado?</h4>
            <p>
              Existem duas partes. A primeira e uma camada de engenharia de atributos, feita com
              regras estatisticas transparentes: percentis, pesos e comparacoes entre selecoes.
            </p>
            <p>
              A segunda e um baseline chamado <strong>Poisson/Dixon-Coles</strong>. Ele estima
              gols esperados e probabilidades de vitoria, empate e derrota a partir do historico
              de partidas finalizadas disponivel antes do jogo.
            </p>
          </article>

          <article>
            <h4>3. Como os dados crus viram indices?</h4>
            <p>
              Cada metrica da FIFA e comparada com todas as selecoes. Se uma equipe esta entre
              as melhores em xG, chutes no alvo ou clean sheets, ela recebe percentil alto nessas
              dimensoes.
            </p>
            <p>
              Depois os percentis sao combinados com pesos. Por exemplo: ataque pesa xG, chutes
              no alvo, gols e volume de finalizacoes. Defesa pesa gols sofridos, clean sheets,
              recuperacoes e tempo para recuperar a bola.
            </p>
          </article>

          <article>
            <h4>4. Por que usar percentil?</h4>
            <p>
              Porque cada estatistica tem escala diferente. Passes podem estar na casa dos
              milhares, gols na casa das dezenas e cartoes em unidades. Comparar tudo cru
              confundiria a analise.
            </p>
            <p>
              Percentil responde uma pergunta simples: "em relacao aos outros times, este time
              esta acima ou abaixo?". Assim 80% quer dizer que a selecao esta melhor que a maior
              parte das outras naquele sinal.
            </p>
          </article>

          <article>
            <h4>5. Como o Poisson/Dixon-Coles funciona?</h4>
            <p>
              Futebol tem poucos gols. Modelos de Poisson sao muito usados para estimar quantos
              gols cada lado pode marcar em uma partida. O modelo olha o historico disponivel,
              calcula forca ofensiva e defensiva e gera gols esperados para cada equipe.
            </p>
            <p>
              A parte Dixon-Coles e um ajuste classico para partidas de futebol, especialmente
              placares baixos como 0-0, 1-0, 1-1 e 0-1. O resultado vira uma referencia numerica,
              nao uma verdade absoluta.
            </p>
          </article>

          <article>
            <h4>6. Como isso chega na LLM?</h4>
            <p>
              A LLM nao recebe todos os CSVs. Ela recebe um pacote pequeno: resumo do confronto,
              indices dos dois times, diferencas entre eles, jogadores-chave, evidencias, baseline
              Poisson e alertas de incerteza.
            </p>
            <p>
              Isso ajuda o modelo a raciocinar com contexto limpo. Em vez de se perder em uma
              tabela enorme, ele ve sinais como "time A cria chances melhores, mas time B tem
              goleiro em alta e risco de zebra alto".
            </p>
          </article>
        </div>

        <div class="ml-index-list">
          <article>
            <h4>Indices gerados</h4>
            <dl>
              <div><dt>attack_index</dt><dd>Forca ofensiva geral: xG, gols, chutes e chutes no alvo.</dd></div>
              <div><dt>chance_quality_index</dt><dd>Qualidade das chances criadas, separando chance boa de chute sem perigo.</dd></div>
              <div><dt>finishing_index</dt><dd>Capacidade de converter chances em gols, com cuidado para nao supervalorizar sorte.</dd></div>
              <div><dt>defense_index</dt><dd>Solidez defensiva: poucos gols sofridos, clean sheets e recuperacao.</dd></div>
              <div><dt>keeper_index</dt><dd>Momento e impacto do goleiro: defesas, gols sofridos e clean sheets.</dd></div>
              <div><dt>control_index</dt><dd>Controle de jogo: posse, passes, precisao e inversoes.</dd></div>
              <div><dt>pressing_index</dt><dd>Pressao e recuperacao: roubadas forcadas, pressoes e tempo para recuperar.</dd></div>
              <div><dt>transition_index</dt><dd>Capacidade de quebrar linhas e atacar profundidade.</dd></div>
              <div><dt>discipline_risk</dt><dd>Risco de faltas, cartoes e expulsao atrapalharem o jogo.</dd></div>
              <div><dt>physical_load</dt><dd>Carga fisica: distancia, sprints e corridas intensas; usado como contexto de desgaste.</dd></div>
              <div><dt>volatility_index</dt><dd>Risco de jogo estranho: overperformance, cartoes, dependencia do goleiro e eficiencia instavel.</dd></div>
              <div><dt>champion_profile_score</dt><dd>Perfil de time campeao: combina defesa, chance real, ataque, controle e baixo risco disciplinar.</dd></div>
            </dl>
          </article>

          <article>
            <h4>Exemplo simples</h4>
            <p>
              Imagine duas selecoes. A primeira chuta muito, mas quase nao acerta o gol. A segunda
              chuta menos, mas tem xG alto e muitos chutes no alvo. No dado cru, a primeira parece
              dominante. Nas features, a segunda pode aparecer melhor em qualidade de chance.
            </p>
            <p>
              Esse e o ponto: separar volume de qualidade, eficiencia de sorte, posse de perigo
              real, defesa forte de goleiro sobrecarregado. Depois a LLM recebe essas pistas e
              precisa justificar o palpite usando evidencias.
            </p>
          </article>

          <article>
            <h4>O que isso nao faz</h4>
            <p>
              Nao garante o vencedor. Copa tem lesao, expulsao, bola desviada, penaltis e contexto
              emocional. Por isso tambem existe o <strong>upset_risk_score</strong>, que avisa
              quando o confronto e equilibrado ou imprevisivel.
            </p>
            <p>
              A ideia nao e substituir a LLM, e dar a ela um mapa melhor. Todas recebem o mesmo
              mapa; vence a IA que interpretar melhor esse contexto ao longo das fases.
            </p>
          </article>
        </div>
      </div>

      <div class="architecture-flow">
        <strong>Fluxo resumido</strong>
        <span>FIFA/cache</span>
        <i></i>
        <span>DuckDB</span>
        <i></i>
        <span>Features ML</span>
        <i></i>
        <span>Agente LLM</span>
        <i></i>
        <span>Scoring</span>
        <i></i>
        <span>Portal/export</span>
      </div>
    </div>

    <div class="llm-call-guide">
      <div class="llm-call-head">
        <span>Chamada da IA</span>
        <h3>O que a LLM recebe para prever um resultado</h3>
        <p>
          A chamada continua sendo feita por jogo e por modelo. O sistema nao pede para uma LLM
          prever a fase inteira em uma unica resposta; ele entrega um dossie compacto de uma partida
          e exige um JSON padrao para comparar todos os modelos com a mesma regra.
        </p>
      </div>

      <div class="llm-call-formula">
        <strong>Total de chamadas</strong>
        <code>jogos da fase x modelos participantes x samples</code>
        <span>Hoje o portal usa samples = 1. O modo consenso 3x so acontece quando samples = 3.</span>
      </div>

      <div class="llm-call-grid">
        <article>
          <h4>1. O botao dispara a fase</h4>
          <p>
            "Executar todas as LLMs da fase" chama a API local em /pool/llm/phase/run com a fase
            ativa, samples=1, modelos pesados incluidos e finished_only=false.
          </p>
          <p>
            O backend inicia o runner em background. Ele busca os jogos oficiais da fase, lista os
            modelos compativeis do LM Studio e cria um batch para registrar a rodada.
          </p>
        </article>
        <article>
          <h4>2. A execucao e model-first</h4>
          <p>
            Para cada jogo, o runner cria uma rodada versionada, mas a ordem de processamento e por
            modelo: carrega uma LLM, roda todos os jogos pendentes da fase, salva cada resposta e so
            entao descarrega o modelo. Quartas com 4 jogos e 29 modelos continuam virando 116
            chamadas, mas com menos troca de modelo.
          </p>
          <p>
            Cada chamada recebe somente uma partida, por exemplo Franca x Marrocos, com dados das
            duas selecoes. Isso reduz confusao e evita prompts gigantes.
          </p>
        </article>
        <article>
          <h4>3. O prompt tem duas mensagens</h4>
          <p>
            A mensagem system define a regra: competir no Bolao CopaMind, usar apenas o JSON de
            contexto, responder somente JSON valido e pensar em prorrogacao/penaltis no mata-mata.
          </p>
          <p>
            A mensagem user traz a tarefa, o contrato de saida e o contexto compacto com jogo,
            baseline, comparativo dos times, forma recente e jogadores-chave.
          </p>
        </article>
      </div>

      <div class="llm-payload-grid">
        <article>
          <h4>O que vai em context.match</h4>
          <ul>
            <li>match_id, fase e data do jogo</li>
            <li>campo neutro ou nao</li>
            <li>time da esquerda e time da direita</li>
            <li>bandeiras e IDs internos das selecoes</li>
          </ul>
        </article>
        <article>
          <h4>O que vai em context.baseline</h4>
          <ul>
            <li>modelo Poisson/Dixon-Coles quando existe historico suficiente</li>
            <li>probabilidade de casa, empate e fora</li>
            <li>gols esperados para cada lado</li>
            <li>placar mais provavel pelo baseline</li>
          </ul>
        </article>
        <article>
          <h4>O que vai em context.matchup</h4>
          <ul>
            <li>resumo do confronto</li>
            <li>deltas entre as selecoes nos indices ML</li>
            <li>upset_risk_score, o risco de zebra</li>
            <li>principais evidencias usadas no raciocinio</li>
          </ul>
        </article>
        <article>
          <h4>O que vai em home e away</h4>
          <ul>
            <li>indices: ataque, defesa, controle, volatilidade e perfil campeao</li>
            <li>metricas centrais: gols, xG, chutes, clean sheets e cartoes</li>
            <li>ultimos jogos disponiveis antes da partida</li>
            <li>jogadores-chave com papel, motivo, confianca e per90</li>
          </ul>
        </article>
      </div>

      <div class="llm-json-examples">
        <article>
          <h4>Exemplo compacto do contexto enviado</h4>
          <pre>{
  "task": "Prever o bolao da partida",
  "context": {
    "match": {"stage": "quarterfinal", "home_team": "Franca", "away_team": "Marrocos"},
    "baseline": {"prob_home": 0.45, "prob_draw": 0.27, "prob_away": 0.28},
    "matchup": {"upset_risk_score": 0.61, "deltas": {"attack_index": 0.12}},
    "home": {"indexes": {"attack_index": 0.82}, "key_players": ["Kylian Mbappe"]},
    "away": {"indexes": {"defense_index": 0.74}, "key_players": ["Achraf Hakimi"]}
  }
}</pre>
        </article>
        <article>
          <h4>Exemplo da resposta esperada</h4>
          <pre>{
  "winner": "home",
  "prob_home": 0.48,
  "prob_draw": 0.27,
  "prob_away": 0.25,
  "predicted_home_goals": 1,
  "predicted_away_goals": 1,
  "goes_to_extra_time": true,
  "goes_to_penalties": true,
  "penalty_winner": "home",
  "first_goal_scorer": "Kylian Mbappe",
  "player_picks": [{"market": "gol", "player_name": "Kylian Mbappe"}],
  "confidence": 0.58,
  "evidence_ids": ["matchup.analytics", "home.key_players"]
}</pre>
        </article>
      </div>

      <div class="llm-postprocess">
        <article>
          <h4>Como o JSON e validado</h4>
          <p>
            A primeira tentativa usa response_format=json_schema, com schema estrito. Se o modelo
            nao aceitar, o cliente tenta json_object. Se ainda vier texto livre, o agente tenta
            extrair e reparar o JSON para salvar uma resposta valida.
          </p>
        </article>
        <article>
          <h4>Onde a resposta fica salva</h4>
          <p>
            A chamada individual vai para llm_model_runs. A palavra final do modelo vai para
            llm_model_consensus. O palpite oficial versionado vai para pool_predictions, e o payload
            completo fica em pool_prediction_payloads para auditoria.
          </p>
        </article>
        <article>
          <h4>O que acontece com empate</h4>
          <p>
            No mata-mata nao existe empate final. Se a LLM prever 1-1, o sistema exige prorrogacao
            ou penaltis e um classificado. Quando necessario, o palpite e normalizado para marcar
            decisao por penaltis.
          </p>
        </article>
      </div>
    </div>

    <div class="guide-contract">
      <div>
        <h3>Exemplo do contrato esperado</h3>
        <p>Todos os modelos competem respondendo no mesmo formato, para o portal comparar maçã com maçã.</p>
      </div>
      <pre>{
  "winner": "home",
  "prob_home": 0.46,
  "prob_draw": 0.27,
  "prob_away": 0.27,
  "predicted_home_goals": 1,
  "predicted_away_goals": 1,
  "goes_to_extra_time": true,
  "goes_to_penalties": true,
  "penalty_winner": "home",
  "first_goal_scorer": "Kylian Mbappe",
  "player_picks": [
    {"market": "gol", "player_name": "Kylian Mbappe", "team": "França", "confidence": 0.62}
  ],
  "evidence_ids": ["matchup.analytics", "home.key_players"]
}</pre>
    </div>`;
}

function guideStep(number, title, body, facts) {
  return `
    <article class="guide-step">
      <div class="step-number">${escapeHtml(number)}</div>
      <h3>${escapeHtml(title)}</h3>
      <p>${escapeHtml(body)}</p>
      <ul>
        ${facts.map((fact) => `<li>${escapeHtml(fact)}</li>`).join("")}
      </ul>
    </article>`;
}

function teamCard(team) {
  const analytics = team.analytics || {};
  const indexes = analytics.indexes || {};
  const metrics = analytics.core_metrics || {};
  const players = team.key_players || [];
  const notes = teamContextNotes(team.team_id).slice(0, 3);
  return `
    <article class="team-card">
      <div class="team-card-head">
        <img src="${escapeAttr(team.flag_url || "")}" alt="" />
        <div>
          <strong>${escapeHtml(team.name)}</strong>
          <span>${escapeHtml(team.group ? `Grupo ${team.group}` : team.fifa_code || "")}</span>
        </div>
        <div class="champion-score">
          <strong>${pct(indexes.champion_profile_score)}</strong>
          <span>perfil campeão</span>
        </div>
      </div>
      <div class="team-index-grid">
        ${indexBar("Ataque", indexes.attack_index)}
        ${indexBar("Chance", indexes.chance_quality_index)}
        ${indexBar("Finalização", indexes.finishing_index)}
        ${indexBar("Defesa", indexes.defense_index)}
        ${indexBar("Goleiro", indexes.keeper_index)}
        ${indexBar("Controle", indexes.control_index)}
        ${indexBar("Pressão", indexes.pressing_index)}
        ${indexBar("Transição", indexes.transition_index)}
        ${indexBar("Risco disc.", indexes.discipline_risk, true)}
        ${indexBar("Volatilidade", indexes.volatility_index, true)}
      </div>
      <div class="team-facts">
        <div><span>Gols</span><strong>${num(metrics.goals, 0)}</strong></div>
        <div><span>xG</span><strong>${num(metrics.xg, 2)}</strong></div>
        <div><span>Chutes alvo</span><strong>${num(metrics.shots_on_target, 0)}</strong></div>
        <div><span>Gols sofridos</span><strong>${num(metrics.goals_conceded, 0)}</strong></div>
        <div><span>Clean sheets</span><strong>${num(metrics.clean_sheets, 0)}</strong></div>
      </div>
      <div class="team-evidence">
        ${(analytics.evidence || []).slice(0, 3).map((item) => `
          <span>${escapeHtml(item.text)}</span>
        `).join("")}
      </div>
      ${notes.length ? `
        <div class="team-context-notes">
          ${notes.map((note) => `
            <span>${escapeHtml(noteTypeLabel(note.note_type))} | ${escapeHtml(note.phase_label || phaseLabel(note.phase))}: ${escapeHtml(note.title)}</span>
          `).join("")}
        </div>` : ""}
      <div class="team-players">
        ${players.slice(0, 5).map(playerPill).join("") || "<span>Jogadores-chave aguardando dados.</span>"}
      </div>
    </article>`;
}

function teamContextNotes(teamId) {
  return (state.context_notes || [])
    .filter((note) => note.active !== false && note.team_id === teamId)
    .sort((a, b) => Number(b.weight || 0) - Number(a.weight || 0));
}

function indexBar(label, value, inverse = false) {
  const normalized = Number(value ?? 0);
  const width = Math.max(0, Math.min(100, Math.round(normalized * 100)));
  const tone = inverse && normalized >= 0.6 ? "danger" : normalized >= 0.72 ? "good" : "neutral";
  return `
    <div class="index-bar ${tone}">
      <div>
        <span>${escapeHtml(label)}</span>
        <strong>${pct(normalized)}</strong>
      </div>
      <i style="--w:${width}%"></i>
    </div>`;
}

function playerPill(player) {
  return `
    <div class="player-pill">
      <img src="${escapeAttr(player.image_url || player.flag_url || "")}" alt="" />
      <div>
        <strong>${escapeHtml(player.name || "-")}</strong>
        <span>${escapeHtml(roleLabel(player.role))} | conf. ${pct(player.confidence)}</span>
      </div>
    </div>`;
}

function comboConsensusBlock(phase, comboMatches) {
  const valid = comboMatches.filter((m) => m.has_prediction !== false);
  const pending = comboMatches.filter((m) => m.has_prediction === false);
  if (!valid.length && !pending.length) return emptyPrediction("Sem palpites nesta fase.");

  // Unique matches from combo predictions (home|||away key, latest combo pred per match)
  const matchDefs = new Map();
  valid.forEach((match) => {
    const key = `${match.home}|||${match.away}`;
    if (!matchDefs.has(key)) matchDefs.set(key, { home: match.home, away: match.away, latestCombo: match });
    else matchDefs.get(key).latestCombo = match; // keep latest
  });

  // Individual (non-combo) model predictions for this phase
  const allModelPreds = (state.phase_predictions_by_model || [])
    .filter((item) => item.phase === phase && item.model_id !== "combo");

  const totalModelsInPhase = allModelPreds.length;
  // Multiple distinct matchups = projected phase (LLMs predicted different bracket outcomes)
  const isProjected = matchDefs.size > 1;

  const blocks = [...matchDefs.values()].flatMap(({ home, away, latestCombo }) => {
    // One vote per model: latest valid prediction for this match
    const modelVotes = allModelPreds
      .map((item) => {
        const preds = (item.predictions || []).filter(
          (p) => p.home === home && p.away === away && p.has_prediction !== false
        );
        return preds.length ? preds[preds.length - 1] : null;
      })
      .filter(Boolean);

    // Skip solo-minority projected matchups (< 2 models) when phase has multiple matchups
    if (isProjected && modelVotes.length < 2) return [];

    // Primary: individual model votes; fallback: combo's own rounds
    const comboRounds = valid.filter((m) => m.home === home && m.away === away);
    const votes = modelVotes.length > 0 ? modelVotes : comboRounds;
    const sourceLabel = modelVotes.length > 0
      ? (totalModelsInPhase > 0
          ? `${votes.length} de ${totalModelsInPhase} modelos`
          : `${votes.length} modelo${votes.length !== 1 ? "s" : ""}`)
      : `${votes.length} rodada${votes.length !== 1 ? "s" : ""}`;

    const total = votes.length;
    const homeCount = votes.filter((v) => predictedSide(v) === "home").length;
    const awayCount = votes.filter((v) => predictedSide(v) === "away").length;
    const drawCount = total - homeCount - awayCount;
    const homePct = Math.round(homeCount / total * 100);
    const awayPct = Math.round(awayCount / total * 100);
    const drawPct = 100 - homePct - awayPct;
    const pts = latestCombo.points == null
      ? "Aguardando resultado"
      : `${latestCombo.points} pts | real ${actualScore(latestCombo)}`;
    const drawRow = drawCount > 0 ? `
      <div class="combo-vote-row">
        <span class="combo-team-name">Empate</span>
        <div class="combo-bar"><div class="combo-bar-fill combo-bar-draw" style="width:${drawPct}%"></div></div>
        <span class="combo-vote-pct">${drawPct}% <small>(${drawCount})</small></span>
      </div>` : "";
    return `
      <div class="prediction-item combo-consensus-item">
        <div class="combo-match-label">
          <b>${escapeHtml(home)} \u00d7 ${escapeHtml(away)}</b>
          <span>${escapeHtml(sourceLabel)}</span>
        </div>
        <div class="combo-vote-bars">
          <div class="combo-vote-row">
            <span class="combo-team-name">${escapeHtml(shortTeamName(home))}</span>
            <div class="combo-bar"><div class="combo-bar-fill combo-bar-home" style="width:${homePct}%"></div></div>
            <span class="combo-vote-pct">${homePct}% <small>(${homeCount})</small></span>
          </div>
          ${drawRow}
          <div class="combo-vote-row">
            <span class="combo-team-name">${escapeHtml(shortTeamName(away))}</span>
            <div class="combo-bar"><div class="combo-bar-fill combo-bar-away" style="width:${awayPct}%"></div></div>
            <span class="combo-vote-pct">${awayPct}% <small>(${awayCount})</small></span>
          </div>
        </div>
        <div class="combo-result-pts"><span>${escapeHtml(pts)}</span></div>
      </div>`;
  });
  const projectedNote = isProjected
    ? `<div class="combo-projected-note">⚡ Fase ainda não confirmada — LLMs projetaram chaves diferentes com base em seus palpites das QFs. Cada bloco mostra quantos modelos previu aquela partida.</div>`
    : "";
  return projectedNote + blocks.join("") + pending.map(predictionRow).join("") || emptyPrediction("Sem palpites nesta fase.");
}

function predictionRow(prediction) {
  if (prediction.is_projection) {
    return `
      <div class="prediction-item prediction-item--pending">
        <div>
          <b>${escapeHtml(prediction.home)} x ${escapeHtml(prediction.away)}</b>
          <span>${escapeHtml(prediction.projection_note || "projeção por chave")}</span>
        </div>
        <div class="prediction-result">
          <strong>proj.</strong>
          <span>Aguardando execução</span>
        </div>
      </div>`;
  }
  if (prediction.has_prediction === false) {
    const invalid = prediction.status === "invalid_prediction";
    const lmstudioError = prediction.status === "lmstudio_error";
    const failed = invalid || lmstudioError;
    return `
      <div class="prediction-item prediction-item--pending ${failed ? "prediction-item--invalid" : ""}">
        <div>
          <b>${escapeHtml(prediction.home)} x ${escapeHtml(prediction.away)}</b>
          <span>${formatDateTime(prediction.match_date)} | ${failed ? escapeHtml(prediction.projection_note || "execução sem palpite válido") : "aguardando execução"}</span>
        </div>
        <div class="prediction-result">
          <strong>${lmstudioError ? "LM" : invalid ? "JSON" : "-"}</strong>
          <span>${lmstudioError ? "Erro LM Studio" : invalid ? "Resposta inválida" : "Sem palpite ainda"}</span>
        </div>
      </div>`;
  }
  const predictionMarkers = predictionBadges(prediction);
  const playerText = playerPicksText(prediction);
  const points = prediction.points == null
    ? "Aguardando resultado"
    : `${prediction.points} pts | real ${actualScore(prediction)}`;
  const hitBadge = prediction.exact_score
    ? `<span class="pred-hit-badge pred-exact">⭐ placar exato</span>`
    : prediction.winner_hit === true
      ? `<span class="pred-hit-badge pred-winner">✓ acertou vencedor</span>`
      : prediction.winner_hit === false
        ? `<span class="pred-hit-badge pred-miss">✗ errou</span>`
        : "";
  return `
    <div class="prediction-item${prediction.exact_score ? " pred-item--exact" : prediction.winner_hit ? " pred-item--winner" : ""}">
      <div>
        <b>${escapeHtml(prediction.home)} x ${escapeHtml(prediction.away)}</b>
        <span class="prediction-meta">${formatDateTime(prediction.match_date)} | ${escapeHtml(shortRound(prediction.predictor_name))}</span>
      </div>
      <div class="prediction-result">
        <strong>${escapeHtml(predictedScoreText(prediction))}</strong>
        ${predictionMarkers ? `<em>${escapeHtml(predictionMarkers)}</em>` : ""}
        <span>${escapeHtml(points)}</span>
        ${hitBadge}
        ${playerText ? `<span class="player-picks-line">${escapeHtml(playerText)}</span>` : ""}
      </div>
    </div>`;
}

function predictedScoreText(prediction) {
  const score = `${prediction.predicted_home_goals}-${prediction.predicted_away_goals}`;
  const isDrawScore = prediction.predicted_home_goals != null && prediction.predicted_away_goals != null
    && Number(prediction.predicted_home_goals) === Number(prediction.predicted_away_goals);
  if (!isDrawScore || !prediction.goes_to_penalties) return score;
  if (prediction.penalty_winner === "home") return `${score} (${prediction.home} nos pênaltis)`;
  if (prediction.penalty_winner === "away") return `${score} (${prediction.away} nos pênaltis)`;
  return `${score} (pênaltis)`;
}

function matchScore(match) {
  if (match.home_score == null) return "vs";
  if (match.went_to_penalties) {
    return `${match.home_score} (${match.home_penalty_score}) - ${match.away_score} (${match.away_penalty_score})`;
  }
  return `${match.home_score}-${match.away_score}`;
}

function actualScore(prediction) {
  if (prediction.actual_home_goals == null) return "-";
  if (prediction.actual_penalties) {
    return `${prediction.actual_home_goals} (${prediction.actual_home_penalty_score})-${prediction.actual_away_goals} (${prediction.actual_away_penalty_score})`;
  }
  if (prediction.actual_extra_time) {
    return `${prediction.actual_home_goals}-${prediction.actual_away_goals} PROR`;
  }
  return `${prediction.actual_home_goals}-${prediction.actual_away_goals}`;
}

function matchMarkers(match) {
  const parts = [];
  if (match.went_to_extra_time) parts.push("PROR");
  if (match.went_to_penalties) parts.push("PEN");
  return parts.join(" ");
}

function predictionBadges(prediction) {
  const parts = [];
  const isDrawScore = prediction.predicted_home_goals != null && prediction.predicted_away_goals != null
    && Number(prediction.predicted_home_goals) === Number(prediction.predicted_away_goals);
  if (isDrawScore && prediction.goes_to_extra_time) parts.push("Prorr.");
  if (isDrawScore && prediction.goes_to_penalties) {
    const winner = prediction.penalty_winner === "home"
      ? prediction.home
      : prediction.penalty_winner === "away"
        ? prediction.away
        : "";
    parts.push(winner ? `Pênaltis: ${winner}` : "Pênaltis");
  }
  return parts.join(" ");
}

function playerPicksText(prediction) {
  const parts = [];
  const seen = new Set();
  if (prediction.first_goal_scorer) {
    parts.push(`1º gol: ${prediction.first_goal_scorer}`);
    seen.add(`first_goal:${normalizeText(prediction.first_goal_scorer)}`);
  }
  for (const pick of (prediction.player_picks || [])) {
    if (!pick?.player_name) continue;
    const market = marketLabel(pick.market);
    const name = String(pick.player_name).trim();
    const key = `${market}:${normalizeText(name)}`;
    const firstGoalKey = `first_goal:${normalizeText(name)}`;
    if (seen.has(key) || (market === "1º gol" && seen.has(firstGoalKey))) continue;
    seen.add(key);
    parts.push(`${market}: ${name}`);
    if (parts.length >= 3) break;
  }
  return parts.join(" | ");
}

function marketLabel(value) {
  const market = normalizeText(value || "");
  if (["gol", "gols", "goal", "goals", "scorer", "goalscorer", "goleador"].includes(market)) return "Gol";
  if (["assist", "assists", "assistencia", "assistencias", "assistência", "assistências"].includes(market)) return "Assist.";
  if (["first_goal", "first_goal_scorer", "primeiro_gol", "1_gol", "1o_gol"].includes(market)) return "1º gol";
  if (["card", "cards", "cartao", "cartoes", "cartão", "cartões"].includes(market)) return "Cartão";
  if (["save", "saves", "defesa", "defesas", "clean_sheet"].includes(market)) return "Defesa";
  if (["betting", "pick", "destaque", "key_player"].includes(market)) return "Destaque";
  return value ? String(value).replaceAll("_", " ") : "Jogador";
}

function normalizeText(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function bulkProgressPanel(progress) {
  const percent = Math.max(0, Math.min(100, Number(progress.percent || 0)));
  const status = progressStatusLabel(progress.status);
  const matchText = progress.total_matches
    ? `Jogo ${progress.current_match_index || 0}/${progress.total_matches}: ${progress.current_match_label || "preparando"}`
    : "Mapeando jogos da fase";
  const modelText = progress.total_models
    ? `Modelo ${progress.current_model_index || 0}/${progress.total_models}: ${progress.current_model_id || "preparando"}`
    : "Mapeando modelos locais";
  const sampleText = progress.total_samples
    ? `Chamada ${progress.current_sample_index || 0}/${progress.total_samples}`
    : "Chamada aguardando";
  const callsText = progress.total_calls
    ? `${progress.completed_calls || 0}/${progress.total_calls} chamadas`
    : "chamadas aguardando";
  return `
    <div class="bulk-progress" aria-live="polite">
      <div class="bulk-progress-head">
        <strong>${escapeHtml(status)}</strong>
        <span>${num(percent, 1)}%</span>
      </div>
      <div class="bulk-progress-bar">
        <i style="--w:${percent}%"></i>
      </div>
      <div class="bulk-progress-grid">
        <span>${escapeHtml(matchText)}</span>
        <span>${escapeHtml(modelText)}</span>
        <span>${escapeHtml(sampleText)}</span>
        <span>${escapeHtml(callsText)}</span>
        <span>Tempo ${formatDuration(progress.elapsed_seconds)}</span>
        <span>ETA ${formatDuration(progress.eta_seconds)}</span>
      </div>
      ${progress.message ? `<em>${escapeHtml(progress.message)}</em>` : ""}
    </div>`;
}

function progressStatusLabel(status) {
  const labels = {
    starting: "Iniciando",
    running: "Rodando",
    completed: "Finalizado",
    completed_with_errors: "Finalizado com erros",
    failed: "Falhou",
    interrupted: "Interrompido",
    idle: "Aguardando",
  };
  return labels[status] || status || "Iniciando";
}

function isTerminalProgress(status) {
  return ["completed", "completed_with_errors", "failed", "interrupted"].includes(status);
}

function isStaleProgress(progress) {
  const updatedAt = progress?.updated_at ? Date.parse(progress.updated_at) : 0;
  const ageMs = updatedAt ? Date.now() - updatedAt : Number.POSITIVE_INFINITY;
  if (progress?.status === "starting") return ageMs > 90 * 1000;
  if (progress?.status === "running") return ageMs > 20 * 60 * 1000;
  return false;
}

function startRunPolling(key) {
  const item = runningRuns.get(key);
  if (!item) return;
  if (item.timer) clearInterval(item.timer);
  item.timer = setInterval(() => {
    loadData(true).catch(() => {});
  }, RUN_POLL_MS);
  runningRuns.set(key, item);
}

function startBulkPolling(phase, batchId) {
  const key = runKey(phase, "__all__");
  runningRuns.set(key, {
    phase,
    modelId: "__all__",
    batchId,
    previousPredictionCount: countPhasePredictions(phase),
    previousSnapshot: state?.generated_at || "",
    startedAt: Date.now(),
    progress: {
      batch_id: batchId,
      phase,
      status: "starting",
      message: "Aguardando runner das LLMs iniciar.",
      percent: 0,
      completed_calls: 0,
      total_calls: 0,
    },
    timer: null,
  });
  startBulkProgressPolling(key);
  renderModelActions();
}

async function recoverLatestBulkProgress() {
  if (window.COPAMIND_EMBEDDED_DATA) return;
  const phase = activePhase;
  const response = await fetch(`${API_BASE}/pool/llm/phase/progress/latest?phase=${encodeURIComponent(phase)}`);
  if (!response.ok) return;
  const progress = await response.json();
  if (!progress?.batch_id || progress.phase !== phase) return;
  if (recoveredProgressBatches.has(progress.batch_id)) return;

  if (isTerminalProgress(progress.status)) return;
  if (isStaleProgress(progress)) return;

  const modelId = Number(progress.total_models || 0) === 1 && progress.current_model_id
    ? progress.current_model_id
    : "__all__";
  const key = runKey(phase, modelId);
  if (runningRuns.has(key)) return;
  recoveredProgressBatches.add(progress.batch_id);
  runningRuns.set(key, {
    phase,
    modelId,
    batchId: progress.batch_id,
    previousPredictionCount: modelId === "__all__"
      ? countPhasePredictions(phase)
      : countModelPhasePredictions(phase, modelId),
    previousSnapshot: state?.generated_at || "",
    startedAt: Date.now(),
    progress,
    timer: null,
  });
  startBulkProgressPolling(key);
  renderModelActions();
}

function startBulkProgressPolling(key) {
  const item = runningRuns.get(key);
  if (!item) return;
  if (item.timer) clearInterval(item.timer);
  pollBulkProgress(key).catch(() => {});
  item.timer = setInterval(() => {
    pollBulkProgress(key).catch(() => {});
  }, PROGRESS_POLL_MS);
  runningRuns.set(key, item);
}

async function pollBulkProgress(key) {
  const item = runningRuns.get(key);
  if (!item?.batchId) return;
  const response = await fetch(`${API_BASE}/pool/llm/phase/progress?batch_id=${encodeURIComponent(item.batchId)}`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const progress = await response.json();
  if (isStaleProgress(progress)) {
    stopRunPolling(key);
    renderModelActions();
    return;
  }
  item.progress = progress;
  runningRuns.set(key, item);
  renderModelActions();
  if (isTerminalProgress(progress.status)) {
    if (item.timer) clearInterval(item.timer);
    item.timer = null;
    runningRuns.set(key, item);
    setTimeout(() => {
      stopRunPolling(key);
      loadData(true).catch(() => {});
    }, 1800);
  }
}

function stopRunPolling(key) {
  const item = runningRuns.get(key);
  if (item?.timer) clearInterval(item.timer);
  runningRuns.delete(key);
}

function reconcileRunningRuns() {
  for (const [key, item] of runningRuns.entries()) {
    if (item.batchId) continue;
    const currentCount = item.modelId === "__all__"
      ? countPhasePredictions(item.phase)
      : countModelPhasePredictions(item.phase, item.modelId);
    const snapshotChanged = String(state?.generated_at || "") !== String(item.previousSnapshot || "");
    const predictionChanged = currentCount > item.previousPredictionCount;
    const timedOut = Date.now() - item.startedAt > RUN_TIMEOUT_MS;
    if (predictionChanged || snapshotChanged || timedOut) {
      stopRunPolling(key);
    }
  }
}

function countModelPhasePredictions(phase, modelId) {
  return (state?.phase_predictions_by_model || [])
    .filter((item) => item.phase === phase && item.model_id === modelId)
    .flatMap((item) => item.predictions || [])
    .filter((prediction) => prediction.has_prediction !== false)
    .length;
}

function countPhasePredictions(phase) {
  return (state?.phase_predictions_by_model || [])
    .filter((item) => item.phase === phase)
    .flatMap((item) => item.predictions || [])
    .filter((prediction) => prediction.has_prediction !== false)
    .length;
}

function canRunAllModelsForPhase() {
  if (!BULK_PHASES.includes(activePhase)) return false;
  return phaseExecutionGaps(activePhase).missingCalls > 0 || projectedMatchesForPhase(activePhase, "combo").length > 0;
}

function pendingPhaseMatches(phase) {
  return matchesForPhase(phase).filter((match) => match.status !== "finished" || match.home_score == null || match.away_score == null);
}

function phaseExecutionGaps(phase) {
  const matchCount = matchesForPhase(phase).length || projectedMatchesForPhase(phase, "combo").length;
  if (!matchCount) return { missingCalls: 0, missingModels: 0 };
  const statusByModel = Object.fromEntries(
    (state.phase_model_run_status || [])
      .filter((item) => item.phase === phase)
      .map((item) => [item.model_id, item])
  );
  let missingCalls = 0;
  let missingModels = 0;
  for (const model of runnableModels()) {
    const runs = Number(statusByModel[model.model_id]?.runs || 0);
    const missing = Math.max(0, matchCount - runs);
    if (missing) {
      missingCalls += missing;
      missingModels += 1;
    }
  }
  return { missingCalls, missingModels };
}

function runnableModels() {
  return (state.models || []).filter((model) => (
    !model.is_combo
    && model.model_class !== "embedding"
    && model.model_class !== "unsupported"
    && model.available !== false
  ));
}

function runKey(phase, modelId) {
  return `${phase}::${modelId}`;
}

function currentPhase() {
  return (state.phases || []).find((phase) => phase.key === activePhase);
}

function matchesForPhase(phase) {
  return (state.matches || [])
    .filter((match) => match.stage === phase)
    .sort((a, b) => new Date(a.date) - new Date(b.date));
}

function projectedMatchesForPhase(phase, modelId) {
  if (matchesForPhase(phase).length) return [];
  if (phase === "semifinal") {
    return pairProjectedWinners("quarterfinal", modelId, "Semifinal projetada");
  }
  if (phase === "third_place") {
    const semis = projectedMatchesForPhase("semifinal", modelId);
    const losers = semis.map((match) => projectedLoser(match, modelId)).filter(Boolean);
    return pairTeams(losers, phase, "3o lugar projetado");
  }
  if (phase === "final") {
    const semis = projectedMatchesForPhase("semifinal", modelId);
    const winners = semis.map((match) => projectedWinner(match, modelId)).filter(Boolean);
    return pairTeams(winners, phase, "Final projetada");
  }
  return [];
}

function pairProjectedWinners(previousPhase, modelId, note) {
  const winners = matchesForPhase(previousPhase).map((match) => winnerFromMatch(match, modelId)).filter(Boolean);
  return pairTeams(winners, "semifinal", note);
}

function pairTeams(teams, phase, note) {
  const rows = [];
  for (let index = 0; index + 1 < teams.length; index += 2) {
    rows.push({
      match_id: `projected:${phase}:${index / 2}`,
      stage: phase,
      home_team_id: teams[index].team_id,
      away_team_id: teams[index + 1].team_id,
      home: teams[index].name,
      away: teams[index + 1].name,
      home_flag_url: teams[index].flag_url,
      away_flag_url: teams[index + 1].flag_url,
      date: null,
      status: "projected",
      note,
    });
  }
  return rows;
}

function winnerFromMatch(match, modelId) {
  const actual = actualWinner(match);
  if (actual) return teamRef(actual === "home" ? match.home_team_id : match.away_team_id);
  const prediction = predictionForMatch(modelId, match.match_id);
  if (prediction) {
    return teamRef(predictedSide(prediction) === "home" ? match.home_team_id : match.away_team_id);
  }
  return strongerTeam(match.home_team_id, match.away_team_id);
}

function projectedWinner(match, modelId) {
  const side = predictedSide(predictionForProjected(match, modelId));
  if (side === "away") return teamRef(match.away_team_id);
  if (side === "home") return teamRef(match.home_team_id);
  return strongerTeam(match.home_team_id, match.away_team_id);
}

function projectedLoser(match, modelId) {
  const winner = projectedWinner(match, modelId);
  if (!winner) return null;
  return winner.team_id === match.home_team_id ? teamRef(match.away_team_id) : teamRef(match.home_team_id);
}

function actualWinner(match) {
  if (match.home_score == null || match.away_score == null) return null;
  if (match.home_score > match.away_score) return "home";
  if (match.away_score > match.home_score) return "away";
  return match.winner_side || null;
}

function predictionForMatch(modelId, matchId) {
  const row = (state.phase_predictions_by_model || []).find((item) => (
    item.model_id === modelId
    && (item.predictions || []).some((prediction) => prediction.match_id === matchId)
  ));
  return (row?.predictions || []).find((prediction) => prediction.match_id === matchId && prediction.has_prediction !== false);
}

function predictionForProjected(_match, _modelId) {
  return null;
}

/**
 * 0 = wrong winner / no result yet
 * 1 = correct winner
 * 2 = winner + one goal count right
 * 3 = winner + exact score (both goals)
 * 4 = above + correct time format (normal / ET / pens)
 * 5 = above + correct penalty winner (or normal-time perfect = max)
 */
function starRating(pred, officialMatch, actual) {
  if (!actual || !officialMatch || officialMatch.home_score == null) return 0;
  const side = predictedSide(pred);
  if (!side || side !== actual) return 0;

  let stars = 1;

  const ph = pred.predicted_home_goals != null ? Number(pred.predicted_home_goals) : null;
  const pa = pred.predicted_away_goals != null ? Number(pred.predicted_away_goals) : null;
  const oh = officialMatch.home_score;
  const oa = officialMatch.away_score;
  const homeRight = ph != null && ph === oh;
  const awayRight = pa != null && pa === oa;
  if (homeRight || awayRight) stars = 2;
  if (homeRight && awayRight) stars = 3;

  if (stars >= 3) {
    // In knockout, equal final score → went to ET/pens
    const wentToET = oh === oa;
    const predET  = pred.goes_to_extra_time === true;
    const predPens = pred.goes_to_penalties === true;
    const timeRight = wentToET ? (predET || predPens) : (!predET && !predPens);
    if (timeRight) stars = 4;
  }

  if (stars >= 4) {
    const wentToET = officialMatch.home_score === officialMatch.away_score;
    if (wentToET && pred.goes_to_penalties) {
      // 5★ only if penalty winner also correct
      const pw = pred.penalty_winner;
      if (pw && pw !== "none" && pw === actual) stars = 5;
    } else {
      // Normal-time or ET (no pens): 4★ = perfect
      stars = 5;
    }
  }

  return stars;
}

function predictedSide(prediction) {
  if (!prediction) return null;
  if (prediction.goes_to_penalties && prediction.penalty_winner !== "none") return prediction.penalty_winner;
  if (prediction.predicted_home_goals > prediction.predicted_away_goals) return "home";
  if (prediction.predicted_away_goals > prediction.predicted_home_goals) return "away";
  return prediction.prob_home >= prediction.prob_away ? "home" : "away";
}

function strongerTeam(homeTeamId, awayTeamId) {
  const home = teamRef(homeTeamId);
  const away = teamRef(awayTeamId);
  const homeScore = home?.analytics?.indexes?.champion_profile_score ?? 0;
  const awayScore = away?.analytics?.indexes?.champion_profile_score ?? 0;
  return homeScore >= awayScore ? home : away;
}

function teamRef(teamId) {
  return (state.teams || []).find((team) => team.team_id === teamId)
    || { team_id: teamId, name: teamId, flag_url: "" };
}

function projectedMatchCard(match) {
  return `
    <article class="match-card match-card--projected">
      <div class="match-teams">
        ${teamLine(match.home, match.home_flag_url, null)}
        <div class="versus">proj.</div>
        ${teamLine(match.away, match.away_flag_url, null)}
      </div>
      <div class="match-meta">
        <span>${escapeHtml(match.note || "projeção")}</span>
        <span>sem chave oficial</span>
      </div>
    </article>`;
}

function emptyPrediction(message) {
  return `<div class="prediction-item muted-row"><div><b>${escapeHtml(message)}</b></div></div>`;
}

function empty(message) {
  return `<div class="empty-state">${escapeHtml(message)}</div>`;
}

function setText(id, value) {
  const element = document.getElementById(id);
  if (element) element.textContent = value;
}

function phaseLabel(phase) {
  return PHASE_LABELS[phase] || phase || "-";
}

function statusLabel(status) {
  return { scheduled: "agendado", finished: "finalizado", cancelled: "cancelado" }[status] || status || "-";
}

function accuracyValue(item) {
  return item?.accuracy == null ? -1 : item.accuracy;
}

function shortRound(value) {
  const text = String(value || "");
  if (!text.includes(":round:")) return text;
  return `rodada ${text.split(":round:", 2)[1]}`;
}

function pct(value) {
  return value == null ? "-" : `${Math.round(Number(value) * 100)}%`;
}

function roleLabel(role) {
  return {
    finalizador: "finalizador",
    criador: "criador",
    ruptura: "ruptura",
    pressao_defensiva: "pressão",
    risco_disciplinar: "risco disc.",
    goleiro_decisivo: "goleiro",
  }[role] || role || "-";
}

function num(value, digits = 0) {
  if (value == null || Number.isNaN(Number(value))) return "-";
  return Number(value).toFixed(digits);
}

function avg(values) {
  const items = (values || []).map(Number).filter((value) => Number.isFinite(value));
  if (!items.length) return null;
  return items.reduce((sum, value) => sum + value, 0) / items.length;
}

function formatDateTime(value) {
  if (!value) return "A definir";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function localDateTimeValue(date) {
  const offsetMs = date.getTimezoneOffset() * 60000;
  return new Date(date.getTime() - offsetMs).toISOString().slice(0, 16);
}

function formatDuration(value) {
  if (value == null || Number.isNaN(Number(value))) return "-";
  const total = Math.max(0, Math.round(Number(value)));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const seconds = total % 60;
  if (hours) return `${hours}h ${String(minutes).padStart(2, "0")}m`;
  if (minutes) return `${minutes}m ${String(seconds).padStart(2, "0")}s`;
  return `${seconds}s`;
}

// ── Sincronizar dados (refresh scores sem chamada LLM) ────────────────────────

let _refreshScoresTimer = null;

async function triggerRefreshScores() {
  const btn = document.getElementById("btn-refresh-scores");
  if (!btn || btn.disabled) return;
  btn.disabled = true;
  btn.textContent = "Atualizando...";
  try {
    const res = await fetch(`${API_BASE}/pool/refresh-scores`, { method: "POST" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    _pollRefreshScores();
  } catch (_err) {
    btn.disabled = false;
    btn.textContent = "API offline";
    setTimeout(() => { if (btn) btn.textContent = "Sincronizar dados"; }, 3000);
  }
}

function _pollRefreshScores() {
  if (_refreshScoresTimer) clearInterval(_refreshScoresTimer);
  _refreshScoresTimer = setInterval(async () => {
    try {
      const res = await fetch(`${API_BASE}/pool/refresh-scores/status`);
      if (!res.ok) return;
      const data = await res.json();
      const btn = document.getElementById("btn-refresh-scores");
      if (!btn) { clearInterval(_refreshScoresTimer); return; }
      const STEP_LABELS = ["Ingerindo resultados...", "Calculando scores...", "Exportando portal..."];
      if (data.status === "running") {
        btn.textContent = STEP_LABELS[data.step] || "Atualizando...";
      } else if (data.status === "completed") {
        clearInterval(_refreshScoresTimer);
        btn.disabled = false;
        btn.textContent = "✓ " + (data.message || "Atualizado");
        setTimeout(async () => {
          if (btn) btn.textContent = "Sincronizar dados";
          await loadData(true);
        }, 2500);
      } else if (data.status === "failed") {
        clearInterval(_refreshScoresTimer);
        btn.disabled = false;
        btn.textContent = "Erro — tentar novamente";
        btn.title = data.message || "Falha no refresh";
        setTimeout(() => { if (btn) { btn.textContent = "Sincronizar dados"; btn.title = ""; } }, 5000);
      }
    } catch (_err) { /* continua polling */ }
  }, 1500);
}

// Official icon per provider — keyed by family name and model_id provider prefix.
// Used as fallback when image_url is empty or known-bad.
const MODEL_IMAGE_OVERRIDES = {
  // Google
  "gemma":       "https://cdn.simpleicons.org/googlegemini/4285F4",
  "google":      "https://cdn.simpleicons.org/googlegemini/4285F4",
  // Alibaba / Qwen
  "qwen":        "https://qwenlm.github.io/img/logo.png",
  // Mistral AI
  "mistral":     "https://cdn.simpleicons.org/mistralai/FA520F",
  "mistralai":   "https://cdn.simpleicons.org/mistralai/FA520F",
  // Microsoft
  "phi":         "../../pictures/icons/phi.png",
  "microsoft":   "../../pictures/icons/phi.png",
  // Zhipu AI / ZAI
  "glm":         "../../pictures/icons/glm.png",
  "zai-org":     "../../pictures/icons/glm.png",
  // Meta
  "llama":       "https://cdn.simpleicons.org/meta/0081FB",
  "meta-llama":  "https://cdn.simpleicons.org/meta/0081FB",
  // NVIDIA
  "nvidia":      "https://cdn.simpleicons.org/nvidia/76B900",
  "nemotron":    "https://cdn.simpleicons.org/nvidia/76B900",
  // OpenAI
  "openai":      "../../pictures/icons/gpt.png",
  // DeepSeek
  "deepseek":    "https://cdn.simpleicons.org/deepseek/4D6BFF",
  // IBM
  "ibm":         "../../pictures/icons/granite.png",
  "granite":     "../../pictures/icons/granite.png",
  // Baidu
  "baidu":       "https://cdn.simpleicons.org/baidu/2932E1",
  "ernie":       "https://cdn.simpleicons.org/baidu/2932E1",
  // AllenAI
  "allenai":     "../../pictures/icons/olm.png",
  "olmo":        "../../pictures/icons/olm.png",
  // ByteDance
  "bytedance":   "../../pictures/icons/oss.png",
  "seed":        "../../pictures/icons/oss.png",
  // Essential AI
  "essentialai": "https://essential.ai/favicon.ico",
  "rnj":         "https://essential.ai/favicon.ico",
  // Liquid AI
  "liquid":      "../../pictures/icons/lfm2.png",
  "lfm":         "../../pictures/icons/lfm2.png",
};

function resolveModelImage(model) {
  const url = model.image_url || "";
  // Reject known-bad banner images
  if (!url || url.includes("gemma4_banner")) {
    const family = (model.family || "").toLowerCase();
    const provider = (model.model_id || "").split("/")[0].toLowerCase();
    return MODEL_IMAGE_OVERRIDES[family] || MODEL_IMAGE_OVERRIDES[provider] || null;
  }
  return url;
}

function avatarForModel(model) {
  const family = String(model.family || model.display_name || "IA").slice(0, 2).toUpperCase();
  const hue = hashHue(model.model_id || model.display_name);
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="124" height="124" viewBox="0 0 124 124">
      <rect width="124" height="124" rx="24" fill="#151923"/>
      <circle cx="92" cy="28" r="38" fill="hsl(${hue}, 82%, 58%)" opacity=".35"/>
      <circle cx="30" cy="96" r="46" fill="hsl(${(hue + 80) % 360}, 72%, 48%)" opacity=".24"/>
      <text x="62" y="72" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-size="34" font-weight="900" fill="#f7fafc">${family}</text>
    </svg>`;
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

function hashHue(value) {
  let hash = 0;
  for (const char of String(value || "")) hash = (hash * 31 + char.charCodeAt(0)) % 360;
  return hash;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value);
}

function cssEscape(value) {
  if (window.CSS?.escape) return CSS.escape(value);
  return String(value).replaceAll('"', '\\"');
}

async function exportStaticSite() {
  setExportStatus("Coletando arquivos...");
  try {
    const [html, css, js, data] = await Promise.all([
      fetchText("index.html"),
      fetchText("styles.css"),
      fetchText("app.js"),
      window.COPAMIND_EMBEDDED_DATA || fetchJson("data/copamind.json"),
    ]);
    const localAssetMap = await loadStaticAssetMap();
    const externalUrls = collectExternalImageUrls(data, js);
    setExportStatus(`Baixando ${externalUrls.size} imagens externas (bandeiras e logos)...`);
    const externalAssetMap = await loadExternalAssetMap(externalUrls);
    const assetMap = { ...localAssetMap, ...externalAssetMap };
    const embeddedData = replaceUrlsInData(data, externalAssetMap);
    const offlineFlag = `<script>window.COPAMIND_OFFLINE = true;<\/script>\n`;
    const offlineCss = `<style>
/* modo offline: oculta controles locais */
.header-actions { display: none !important; }
#btn-refresh-scores, #run-all-models, #reset-phase-history, #reset-all-history,
#cancel-sequential, .model-action-buttons, .context-note-form, #chat-form, #chat-reset,
#btn-extract-url, .chat-controls, [data-section="chat"] { display: none !important; }
.offline-notice { display: flex !important; }
<\/style>\n`;
    let outputCss = replaceAssets(css, assetMap);
    let outputJs = replaceAssets(js, assetMap).replaceAll("</script>", "<\\/script>");
    let outputHtml = replaceAssets(html, assetMap);
    // Remove botoes de controle local (nao fazem sentido no HTML exportado)
    outputHtml = outputHtml
      .replace(/<button[^>]+id="refresh-data"[^>]*>.*?<\/button>/s, "")
      .replace(/<button[^>]+data-export-static[^>]*>.*?<\/button>/gs, "")
      .replace(/<button[^>]+id="btn-publish-static"[^>]*>.*?<\/button>/s, "")
      .replace(/<a[^>]+href="http:\/\/localhost:8501"[^>]*>.*?<\/a>/s, "")
      .replace(/<button[^>]+id="open-chat-header"[^>]*>.*?<\/button>/s, "")
      .replace(/<div[^>]+class="header-actions"[^>]*>\s*<\/div>/s, "");
    outputHtml = outputHtml.replace(
      '<link rel="stylesheet" href="styles.css" />',
      `<style>\n${outputCss}\n</style>`
    );
    outputHtml = outputHtml.replace(
      '<script src="app.js"></script>',
      `${offlineFlag}${offlineCss}<script>window.COPAMIND_EMBEDDED_DATA=${safeJson(embeddedData)};<\/script>\n<script>\n${outputJs}\n<\/script>`
    );
    downloadFile(
      `copamind-2026-portal-${new Date().toISOString().slice(0, 10)}.html`,
      outputHtml,
      "text/html;charset=utf-8"
    );
    setExportStatus("HTML gerado para download.");
  } catch (error) {
    console.error(error);
    setExportStatus("Nao consegui exportar. Abra pelo servidor local e tente novamente.");
  }
}

async function fetchText(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`Falha ao carregar ${path}`);
  return response.text();
}

async function fetchJson(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`Falha ao carregar ${path}`);
  return response.json();
}

async function loadStaticAssetMap() {
  const entries = await Promise.all(
    STATIC_ASSETS.map(async (path) => {
      try {
        return [path, await assetAsDataUrl(path)];
      } catch (_error) {
        return [path, path];
      }
    })
  );
  return Object.fromEntries(entries);
}

async function assetAsDataUrl(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`Falha ao carregar ${path}`);
  const blob = await response.blob();
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

function collectExternalImageUrls(data, jsText) {
  const urls = new Set();
  function walk(obj) {
    if (Array.isArray(obj)) { obj.forEach(walk); return; }
    if (!obj || typeof obj !== "object") return;
    for (const [key, val] of Object.entries(obj)) {
      if ((key === "flag_url" || key === "image_url") && typeof val === "string" && val.startsWith("http")) {
        urls.add(val);
      } else {
        walk(val);
      }
    }
  }
  walk(data);
  const urlPattern = /["'](https?:\/\/[^\s"'\\]+)["']/g;
  let m;
  while ((m = urlPattern.exec(jsText)) !== null) {
    const url = m[1];
    if (
      url.includes("cdn.simpleicons.org") ||
      url.includes("qwenlm.github.io") ||
      url.includes("favicon.ico") ||
      /\.(png|jpg|jpeg|webp|svg)(\?|$)/i.test(url)
    ) {
      urls.add(url);
    }
  }
  return urls;
}

async function loadExternalAssetMap(urls) {
  const entries = await Promise.all(
    [...urls].map(async (url) => {
      try {
        return [url, await urlAsDataUrl(url)];
      } catch (_err) {
        console.warn(`Nao foi possivel embutir: ${url}`);
        return [url, url];
      }
    })
  );
  return Object.fromEntries(entries);
}

async function urlAsDataUrl(url) {
  const resp = await fetch(url, { mode: "cors" });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  const blob = await resp.blob();
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

function replaceUrlsInData(data, urlMap) {
  if (Array.isArray(data)) return data.map((item) => replaceUrlsInData(item, urlMap));
  if (data && typeof data === "object") {
    const result = {};
    for (const [key, val] of Object.entries(data)) {
      if ((key === "flag_url" || key === "image_url") && typeof val === "string" && urlMap[val] && urlMap[val] !== val) {
        result[key] = urlMap[val];
      } else {
        result[key] = replaceUrlsInData(val, urlMap);
      }
    }
    return result;
  }
  return data;
}

function replaceAssets(text, assetMap) {
  return Object.entries(assetMap).reduce((current, [path, dataUrl]) => (
    current.replaceAll(path, dataUrl)
  ), text);
}

function safeJson(value) {
  return JSON.stringify(value)
    .replaceAll("<", "\\u003c")
    .replaceAll(">", "\\u003e")
    .replaceAll("&", "\\u0026");
}

function downloadFile(filename, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function setExportStatus(message) {
  const status = document.getElementById("export-status");
  if (status) status.textContent = message;
}
