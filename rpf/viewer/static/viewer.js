let DATA = null;
let currentFilter = "all";
let selectedTick = 1;
let statusTimer = null;

const $ = (id) => document.getElementById(id);

const ZH = {
  "locked-in": "锁定",
  "cold-war": "冷战",
  "repair-avoidant": "回避修复",
  fragile: "脆弱",
  low: "低",
  high: "高",
  unstable: "不稳定",
  building: "累积中",
  available: "可用",
  demanding: "持续索取承认",
  withholding: "收回表达",
  careful: "谨慎防御",
  distant: "疏离",
  "direct apology": "直接道歉",
  scene: "场景",
  micro_interaction: "微交互",
  latent: "潜伏",
  material: "物质场",
  binding: "绑定",
  affordance: "可行动空间",
  action: "行动",
  expression: "表达",
  communication: "沟通信号",
  observation: "观察",
  rpp: "关系模式",
  rpp_dynamics: "模式动力学",
  recognition: "承认/误认",
  repair: "修复",
  classification: "关系命名",
  irreversibility: "不可逆",
  memory: "记忆重构",
  aggregation: "聚合",
  projection: "投影",
  diagnostic: "诊断",
  SimulationInitializedEvent: "模拟初始化",
  TickStartedEvent: "Tick 开始",
  FieldPressureEvent: "场压力",
  BindingActivatedEvent: "绑定激活",
  AffordanceSelectionEvent: "可行动空间选择",
  ActionSelectionEvent: "行动选择",
  ActionInhibitionEvent: "行动抑制",
  ActionSubstitutionEvent: "行动替代",
  ExpressionSelectionEvent: "表达选择",
  MicroSignalEvent: "微信号",
  ObservationEvent: "观察",
  SceneCrystallizationEvent: "场景结晶",
  RPPActivationEvent: "关系模式激活",
  StabilizationEvent: "模式稳定化",
  RPPCompositionEvent: "关系模式组合",
  RPPSuppressionEvent: "关系模式抑制",
  RPPDecayEvent: "关系模式衰减",
  RecognitionEvent: "承认结果",
  MisrecognitionEvent: "误认",
  RepairEvent: "修复",
  DisplacementEvent: "转移修复",
  AvoidanceEvent: "回避",
  OperativeClassificationEvent: "操作性命名",
  DownwardConstraintEvent: "向下约束",
  IrreversibilityEvent: "不可逆事件",
  MemoryReconstructionEvent: "记忆重构",
  AggregationEvent: "聚合",
  ProjectionEvent: "投影",
  LatentTimeEvent: "潜伏时间",
  SimulationCompletedEvent: "模拟完成",
  material_pressure_intrusion: "物质压力闯入",
  unacknowledged_contribution_claim: "未被承认的付出索取",
  practical_repair_offer: "实际帮助式修复",
  public_performance: "公开表演",
  care_intervention: "照护介入",
  double_bind_response: "双重束缚回应",
  mediated_delay: "媒介延迟",
  embodied_avoidance: "身体回避",
  direct_enactment: "直接行动",
  inhibited_omission: "被抑制的遗漏",
  practical_substitution: "实际行动替代",
  public_substitution: "公开形式替代",
  recognition_claim: "承认索取",
  enacted: "已行动",
  inhibited: "被抑制",
  substituted: "被替代",
  escalated: "升级",
  plain_speech: "直接说出",
  tightened_tone: "绷紧语气",
  hesitation: "犹豫停顿",
  gesture_displacement: "姿态转移",
  charged_silence: "带电沉默",
  public_mask: "公开面具",
  spoken: "言说",
  tonal_shift: "语气变化",
  timing_distortion: "时机扭曲",
  gesture: "姿态",
  silence: "沉默",
  public_performance: "公开表演",
  delayed_reply: "延迟回应",
  short_answer: "短促回答",
  gaze_avoidance: "回避目光",
  unacknowledged_help: "未被承认的帮助",
  practical_repair: "实际补偿",
  public_politeness: "公开礼貌",
  material_urgency: "物质紧迫",
  granted: "承认成功",
  partial: "部分承认",
  misunderstood: "被误解",
  displaced: "被转移",
  refused: "被拒绝",
  postponed: "被推迟",
  unspeakable: "变得不可说",
  MisrecognitionEvent: "误认",
  RepairEvent: "修复",
  DisplacementEvent: "转移",
  AvoidanceEvent: "回避",
  contribution_debt_loop: "付出-债务循环",
  repair_avoidance: "修复回避",
  recognition_pursuit: "承认追逐",
  pursuit_withdrawal: "追逐-退缩",
  double_bind: "双重束缚",
  public_private_split: "公私分裂",
  silence_interpretation_loop: "沉默解释循环",
  complementary_dependency: "互补依赖",
  face_saving_loop: "保全面子循环",
  debt_lock: "债务锁定",
  recognition_trap: "承认陷阱",
  credit_recognition_lock: "贡献-承认锁定",
  anxious_silence_circuit: "焦虑沉默回路",
  care_bind_double_bind: "照护-束缚回路",
  public_face_split: "公开面子分裂",
  symbolic_debt_lock: "象征债务锁定",
  role_lock: "角色锁定",
  public_reclassification: "公开重分类",
  absence_history: "缺席成为历史",
  identity_mark: "身份标记",
  injury_reconstruction: "受伤式重构",
  defensive_reconstruction: "防御式重构",
  fate_lock: "命运锁定记忆",
  operative_label: "操作性标签",
  "you_make_it_sound_like_i_owe_you": "你让我像欠了你",
  "your_help_is_control": "你的帮助是在控制",
  "we_are_only_fine_in_public": "我们只是在公开场合没事",
  "you_are_never_really_here": "你从来没有真正出现",
  "nothing_i_do_is_right": "我怎么做都不对",
  "the claim is present as avoidance rather than direct action": "要求没有被说出，而是以回避形式出现",
  "practical action substitutes for direct recognition": "用实际行动替代直接承认",
  "publicly safe performance replaces private action": "用公开安全的表现替代私人行动",
  "recognition demand becomes explicit enough to alter the scene": "承认索取变得足够明确，开始改变场景",
  "non-response becomes a relational act": "不回应本身变成一种关系行动",
  "brief co-presence or message-level signal became structurally relevant": "短暂共处或消息层信号变得具有结构意义",
  "latent time passed while pressure accumulated without direct scene": "没有直接场景发生，压力在潜伏时间中累积",
  "field and recognition pressure crystallized into a scene": "场压力与承认压力结晶为一个场景",
  "plain": "平直",
  "controlled": "克制",
  "uncertain": "不确定",
  "indirect": "间接",
  "silent": "沉默",
  "polite": "礼貌",
  "minimal": "最小动作",
  "stillness": "静止",
  "interrupted_movement": "动作中断",
  "looks_away_or_handles_object": "移开目光或摆弄物件",
  "no_answer": "没有回答",
  "social_smile": "社交性微笑",
  "direct": "直接",
  "slight_delay": "轻微延迟",
  "pause_before_response": "回答前停顿",
  "before_speech": "话语之前",
  "absence_extends": "缺席延长",
  "on_time": "按时出现",
};

function zh(value) {
  if (value === undefined || value === null) return "-";
  const text = String(value);
  return ZH[text] || text;
}

function fmt(value) {
  if (value === undefined || value === null) return "-";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(3);
  return String(value);
}

function short(value, max = 48) {
  const text = fmt(value);
  return text.length > max ? `${text.slice(0, max - 1)}...` : text;
}

async function main() {
  await loadData();
  selectedTick = DATA.scheduler[0]?.tick_index || 1;
  restoreLocalSettings();
  renderAll();
  bindControls();
  await pollSimulationStatus();
  statusTimer = setInterval(pollSimulationStatus, 2000);
}

async function loadData() {
  const res = await fetch("/api/run");
  DATA = await res.json();
}

function renderAll() {
  renderOverview();
  renderCanon();
  renderStory();
  renderTicks();
  renderPatterns();
  renderTraces();
  renderEvents();
}

function renderStory() {
  const frames = DATA.story || [];
  $("storyFrames").innerHTML = frames.map((frame) => {
    const action = frame.action || {};
    const expression = frame.expression || {};
    const recognition = frame.recognition || {};
    const participants = frame.participants || {};
    const names = [participants.source?.name, participants.target?.name].filter(Boolean).join(" → ");
    return `
      <article class="story-card ${frame.phase_changed ? "changed" : ""}">
        <div class="story-head">
          <strong>第 ${frame.tick} 步 · ${zh(frame.tick_type)}</strong>
          <span>${zh(frame.phase)}${frame.phase_changed ? " · 阶段改变" : ""}</span>
        </div>
        ${names ? `<small class="story-participants">${names}</small>` : ""}
        <p>${localizeSentence(frame.summary)}</p>
        <div class="tags">
          ${action.action_id ? `<span class="tag">行动：${zh(action.action_id)}</span>` : ""}
          ${expression.expression_id ? `<span class="tag">表达：${zh(expression.expression_id)}</span>` : ""}
          ${recognition.outcome ? `<span class="tag">承认：${zh(recognition.outcome)}</span>` : ""}
          ${frame.memory_count ? `<span class="tag">记忆重构：${frame.memory_count}</span>` : ""}
          ${frame.fate_count ? `<span class="tag">命运转折：${frame.fate_count}</span>` : ""}
        </div>
      </article>
    `;
  }).join("");

  const last = frames[frames.length - 1] || {};
  const pressure = last.pressure || {};
  $("stateChange").innerHTML = `
    <div class="state-row"><span>当前阶段</span><b>${zh(last.phase)}</b></div>
    <div class="state-row"><span>物质紧迫</span><b>${fmt(pressure.material_urgency)}</b></div>
    <div class="state-row"><span>冲突压力</span><b>${fmt(pressure.conflict_pressure)}</b></div>
    <div class="state-row"><span>修复债</span><b>${fmt(pressure.repair_debt)}</b></div>
    <div class="state-row"><span>记忆压力</span><b>${fmt(pressure.memory_pressure)}</b></div>
    <div class="state-row"><span>承认压力</span><b>${fmt(pressure.recognition_pressure)}</b></div>
  `;
}

function renderCanon() {
  const canon = DATA.render_canon || {};
  const cast = canon.cast || {};
  const setting = canon.setting || {};
  const narration = canon.narration || {};
  const people = Object.entries(cast).map(([pid, person]) => `
    <div class="canon-person">
      <strong>${person.name || pid}</strong>
      <small>${person.gender || "-"} / ${person.age_band || "-"} / ${person.surface_role || "-"}</small>
    </div>
  `).join("");
  const forbidden = (narration.forbidden || []).slice(0, 6).map((item) => `<span class="tag">${zh(item)}</span>`).join("");
  $("renderCanon").innerHTML = `
    <div class="canon-title">${canon.title || "未配置叙事圣经"}</div>
    <small>${setting.place || "-"} / ${setting.period || "-"} / ${narration.style || "-"}</small>
    <div class="canon-people">${people || "<small>暂无人物显现配置</small>"}</div>
    <div class="tags">${forbidden}</div>
  `;
}

function localizeSentence(text) {
  if (!text) return "";
  let output = String(text);
  Object.keys(ZH)
    .sort((a, b) => b.length - a.length)
    .forEach((key) => {
      output = output.split(key).join(ZH[key]);
    });
  return output;
}

function renderOverview() {
  $("runDir").textContent = DATA.run_dir;
  $("eventCount").textContent = `${DATA.summary.event_count} 个事件`;
  $("phase").textContent = zh(DATA.summary.phase);
  $("trust").textContent = `${fmt(DATA.summary.trust.score)} / ${zh(DATA.summary.trust.state)}`;
  $("resentment").textContent = `${fmt(DATA.summary.resentment.score)} / ${zh(DATA.summary.resentment.state)}`;
  $("repair").textContent = `${fmt(DATA.summary.repair.score)} / ${zh(DATA.summary.repair.state)}`;

  const people = DATA.derived_views.person_views || {};
  $("personViews").innerHTML = Object.values(people)
    .map((person) => `
      <div class="person">
        <strong>${person.process_id}</strong>
        <div class="tags">${(person.apparent_labels || []).map((label) => `<span class="tag">${zh(label)}</span>`).join("") || "<span class=\"tag\">暂无标签</span>"}</div>
        <small>不可用行动：${(person.unavailable_actions || []).map(zh).join("，") || "-"}</small>
      </div>
    `)
    .join("");

  const records = DATA.irreversibility.records || [];
  $("irreversibles").innerHTML = records.length
    ? records.map((record) => `
      <div class="trace">
        <strong>${zh(record.category)}</strong>
        <small>${zh(record.description)}</small>
        <div class="tags">${(record.future_constraints || []).map((item) => `<span class="tag">${zh(item)}</span>`).join("")}</div>
      </div>
    `).join("")
    : "<div class=\"trace\"><small>暂无不可逆记录</small></div>";
}

function renderTicks() {
  const ticks = DATA.scheduler.filter((tick) => currentFilter === "all" || tick.selected_tick_type === currentFilter);
  $("tickStrip").innerHTML = ticks.map((tick) => `
    <button class="tick ${tick.selected_tick_type} ${tick.tick_index === selectedTick ? "active" : ""}" data-tick="${tick.tick_index}">
      ${tick.tick_index}
    </button>
  `).join("");
  document.querySelectorAll(".tick").forEach((button) => {
    button.addEventListener("click", () => {
      selectedTick = Number(button.dataset.tick);
      renderTicks();
      renderTickDetail();
    });
  });
  renderTickDetail();
}

function renderTickDetail() {
  const tick = DATA.scheduler.find((item) => item.tick_index === selectedTick);
  const projection = DATA.projection.find((item) => item.tick === selectedTick);
  const action = DATA.action.find((item) => item.tick === selectedTick)?.selected_action;
  const expression = DATA.expression.find((item) => item.tick === selectedTick)?.selected_expression;
  const recognition = DATA.recognition.find((item) => item.tick === selectedTick);
  $("tickDetail").innerHTML = `
    <div class="detail-block">
      <b>第 ${selectedTick} 步</b>
      <code>${tick ? JSON.stringify({
        类型: zh(tick.selected_tick_type),
        模拟秒数: tick.simulated_time_delta_seconds,
        原因: zh(tick.time_mapping_reason),
      }, null, 2) : "暂无调度记录"}</code>
    </div>
    <div class="detail-block">
      <b>行动 / 表达</b>
      <code>${JSON.stringify({
        行动: zh(action?.action_id),
        行动模式: zh(action?.action_mode),
        表达: zh(expression?.expression_id),
        表达模式: zh(expression?.expression_mode),
        表层信号: zh(expression?.surface_signal),
      }, null, 2)}</code>
    </div>
    <div class="detail-block">
      <b>投影 / 承认</b>
      <code>${JSON.stringify({
        关系阶段: zh(projection?.relationship_phase),
        承认结果: zh(recognition?.outcome),
        修复事件: zh(recognition?.repair_event_type),
      }, null, 2)}</code>
    </div>
  `;
}

function renderPatterns() {
  renderBars("rppBars", DATA.summary.top_rpps);
  renderBars("compositionBars", DATA.summary.top_compositions);
  renderBars("eventBars", DATA.summary.top_events);
}

function renderBars(id, rows) {
  const max = Math.max(...rows.map((row) => Number(row.value)), 1);
  $(id).innerHTML = rows.map((row) => `
    <div class="bar">
      <div class="bar-label" title="${row.key}">${short(zh(row.key), 28)}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${(Number(row.value) / max) * 100}%"></div></div>
      <div class="bar-value">${fmt(Number(row.value))}</div>
    </div>
  `).join("");
}

function renderTraces() {
  $("actionTrace").innerHTML = traceRows(DATA.action, (item) => {
    const selected = item.selected_action;
    return {
      tick: item.tick,
      title: `${zh(selected.action_id)} / ${zh(selected.action_mode)}`,
      body: zh(selected.relation_claim),
      tags: [zh(selected.signal_type), `分数 ${fmt(selected.score)}`],
    };
  });
  $("expressionTrace").innerHTML = traceRows(DATA.expression, (item) => {
    const selected = item.selected_expression;
    return {
      tick: item.tick,
      title: `${zh(selected.expression_id)} / ${zh(selected.expression_mode)}`,
      body: `${zh(selected.surface_signal)}；${zh(selected.tone)}；${zh(selected.timing)}`,
      tags: [zh(selected.gesture), `强度 ${fmt(selected.intensity)}`],
    };
  });
  $("recognitionTrace").innerHTML = traceRows(DATA.recognition, (item) => ({
    tick: item.tick,
    title: zh(item.outcome),
    body: zh(item.repair_event_type),
    tags: [`修复债 ${fmt(item.repair_debt)}`, `压力 ${fmt(item.demand_pressure)}`],
  }));
  $("memoryTrace").innerHTML = traceRows(DATA.memory.slice(-40), (item) => ({
    tick: item.tick,
    title: `${item.owner_process_id}：${zhMemory(item.remembered_as)}`,
    body: zh(item.source_event_type),
    tags: (item.reconstruction_biases || []).map(zh),
  }));
}

function zhMemory(value) {
  if (!value) return "-";
  const parts = String(value).split(":");
  return parts.map(zh).join("：");
}

function traceRows(rows, mapper) {
  return rows.length
    ? rows.map((row) => {
      const item = mapper(row);
      return `
        <div class="trace">
          <small>第 ${item.tick} 步</small>
          <strong>${item.title}</strong>
          <small>${item.body || ""}</small>
          <div class="tags">${(item.tags || []).map((tag) => `<span class="tag">${tag}</span>`).join("")}</div>
        </div>
      `;
    }).join("")
    : "<div class=\"trace\"><small>暂无记录</small></div>";
}

function renderEvents() {
  const query = ($("eventSearch")?.value || "").toLowerCase();
  const events = DATA.timeline
    .filter((event) => !query || JSON.stringify(event).toLowerCase().includes(query))
    .slice(-220)
    .reverse();
  $("eventList").innerHTML = events.map((event) => `
    <div class="event">
      <small>第 ${event.tick} 步 / ${zh(event.source_layer)}</small>
      <strong>${zh(event.event_type)}</strong>
      <code>${JSON.stringify(localizePayload(event.payload), null, 2)}</code>
    </div>
  `).join("");
}

function localizePayload(value) {
  if (Array.isArray(value)) return value.map(localizePayload);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [zhKey(key), localizePayload(item)]));
  }
  return typeof value === "string" ? zhMemory(value) : value;
}

function zhKey(key) {
  const keys = {
    tick_type: "tick 类型",
    signal_type: "信号类型",
    source_process: "来源过程",
    target_process: "目标过程",
    affordance_id: "可行动空间",
    action_id: "行动",
    action_mode: "行动模式",
    expression_id: "表达",
    expression_mode: "表达模式",
    surface_signal: "表层信号",
    relation_claim: "关系主张",
    recognition_pressure: "承认压力",
    repair_debt: "修复债",
    memory_pressure: "记忆压力",
    injury_memory: "受伤记忆",
    defensive_memory: "防御记忆",
    fate_memory: "命运记忆",
    speech_block: "言说阻塞",
    outcome_scores: "结果评分",
    evidence: "证据",
    result: "结果",
    category: "类别",
    description: "描述",
    future_constraints: "未来约束",
    lost_alternatives: "失去的可能性",
  };
  return keys[key] || key;
}

function bindControls() {
  document.querySelectorAll(".toolbar button").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".toolbar button").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      currentFilter = button.dataset.filter;
      const first = DATA.scheduler.find((tick) => currentFilter === "all" || tick.selected_tick_type === currentFilter);
      if (first) selectedTick = first.tick_index;
      renderTicks();
    });
  });
  $("eventSearch").addEventListener("input", renderEvents);
  $("renderLlm").addEventListener("click", () => renderMarkdownStory(true));
  $("renderDeterministic").addEventListener("click", () => renderMarkdownStory(false));
  $("startSimulation").addEventListener("click", startSimulation);
  $("stopSimulation").addEventListener("click", stopSimulation);
  $("saveLlmKey").addEventListener("click", saveKey);
  $("clearLlmKey").addEventListener("click", clearKey);
  $("llmApiKey").addEventListener("input", markKeyDirty);
  $("llmModel").addEventListener("change", saveLocalSettings);
  $("llmThinking").addEventListener("change", saveLocalSettings);
  $("simRenderMode").addEventListener("change", saveLocalSettings);
}

function restoreLocalSettings() {
  const saved = JSON.parse(localStorage.getItem("rpfViewerSettings") || "{}");
  if (saved.apiKey) $("llmApiKey").value = saved.apiKey;
  if (saved.model) $("llmModel").value = saved.model;
  if (saved.thinking) $("llmThinking").value = saved.thinking;
  if (saved.renderMode) $("simRenderMode").value = saved.renderMode;
  updateKeyStatus(Boolean(saved.apiKey));
}

function saveLocalSettings(options = {}) {
  const previous = JSON.parse(localStorage.getItem("rpfViewerSettings") || "{}");
  const next = {
    ...previous,
    model: $("llmModel").value,
    thinking: $("llmThinking").value,
    renderMode: $("simRenderMode").value,
  };
  if (options.includeKey) {
    next.apiKey = $("llmApiKey").value.trim();
  }
  localStorage.setItem("rpfViewerSettings", JSON.stringify(next));
  updateKeyStatus(Boolean(next.apiKey));
}

function saveKey() {
  const key = $("llmApiKey").value.trim();
  if (!key) {
    $("keySaveStatus").textContent = "请先填写 Key";
    return;
  }
  saveLocalSettings({includeKey: true});
  $("keySaveStatus").textContent = "已保存到本机浏览器";
}

function clearKey() {
  const saved = JSON.parse(localStorage.getItem("rpfViewerSettings") || "{}");
  delete saved.apiKey;
  localStorage.setItem("rpfViewerSettings", JSON.stringify(saved));
  $("llmApiKey").value = "";
  updateKeyStatus(false);
}

function updateKeyStatus(saved) {
  const status = $("keySaveStatus");
  if (status) status.textContent = saved ? "已保存" : "未保存";
}

function markKeyDirty() {
  const saved = JSON.parse(localStorage.getItem("rpfViewerSettings") || "{}");
  const current = $("llmApiKey").value.trim();
  if (current && current !== (saved.apiKey || "")) {
    $("keySaveStatus").textContent = "有未保存修改";
  } else {
    updateKeyStatus(Boolean(saved.apiKey));
  }
}

async function startSimulation() {
  saveLocalSettings();
  const renderMode = $("simRenderMode").value;
  const apiKey = $("llmApiKey").value.trim();
  if (renderMode === "llm" && !apiKey) {
    $("simulationStatus").textContent = "自动 LLM 渲染需要先填写 DeepSeek API Key。";
    return;
  }
  setSimulationButtons(false);
  $("simulationStatus").textContent = "正在启动持续模拟...";
  try {
    const res = await fetch("/api/simulate/start", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        duration_value: $("simDurationValue").value,
        duration_unit: $("simDurationUnit").value,
        seed: $("simSeed").value,
        tick_interval_seconds: $("simTickInterval").value,
        render_mode: renderMode,
        render_every_ticks: $("simRenderEvery").value,
        segment_max_ticks: $("simRenderEvery").value,
        segment_micro_count: $("segmentMicroCount").value,
        segment_latent_hours: $("segmentLatentHours").value,
        segment_max_days: $("segmentMaxDays").value,
        max_steps: $("simMaxSteps").value,
        api_key: apiKey,
        model: $("llmModel").value,
        thinking: $("llmThinking").value,
        reasoning_effort: "high",
      }),
    });
    const payload = await res.json();
    if (!res.ok || payload.error) throw new Error(payload.error || `请求失败：${res.status}`);
    renderSimulationStatus(payload);
  } catch (error) {
    $("simulationStatus").textContent = `启动失败：${error.message}`;
    setSimulationButtons(true);
  }
}

async function stopSimulation() {
  $("simulationStatus").textContent = "正在请求停止...";
  await fetch("/api/simulate/stop", {method: "POST"});
  await pollSimulationStatus();
}

async function pollSimulationStatus() {
  try {
    const res = await fetch("/api/simulate/status");
    const status = await res.json();
    renderSimulationStatus(status);
    if (["running", "completed", "stopped"].includes(status.state)) {
      await loadData();
      renderAll();
    }
    if (status.last_render_text) {
      $("llmOutput").innerHTML = markdownToHtml(status.last_render_text);
      $("llmStatus").textContent = status.last_render_error
        ? `自动渲染失败：${status.last_render_error}`
        : `自动渲染：${status.last_render_output || "-"}`;
    }
  } catch (error) {
    $("simulationStatus").textContent = `状态刷新失败：${error.message}`;
  }
}

function renderSimulationStatus(status) {
  const elapsed = Number(status.elapsed_seconds || 0);
  const target = Number(status.target_seconds || 0);
  const pct = target > 0 ? Math.min(100, (elapsed / target) * 100) : 0;
  $("simulationStatus").textContent = `${stateText(status.state)}：${status.message || "-"}`;
  $("simulationProgress").innerHTML = `
    <div class="state-row"><span>状态</span><b>${stateText(status.state)}</b></div>
    <div class="state-row"><span>Tick</span><b>${fmt(status.tick || 0)}</b></div>
    <div class="state-row"><span>真实运行时间</span><b>${formatDuration(elapsed)} / ${formatDuration(target)}</b></div>
    <div class="progress-track"><div class="progress-fill" style="width:${pct}%"></div></div>
    <div class="state-row"><span>事件数</span><b>${fmt(status.event_count)}</b></div>
    <div class="state-row"><span>自动渲染</span><b>${status.render_mode || "-"}</b></div>
    <div class="state-row"><span>最近段落</span><b>${segmentLabel(status.last_render_segment)}</b></div>
    <div class="state-row"><span>闭合原因</span><b>${escapeHtml(status.last_render_segment?.boundary_reason || "-")}</b></div>
    <div class="state-row"><span>最近输出</span><b>${status.last_render_output || "-"}</b></div>
    ${status.last_render_error ? `<div class="state-row"><span>渲染错误</span><b>${escapeHtml(status.last_render_error)}</b></div>` : ""}
  `;
  setSimulationButtons(!["running", "stopping"].includes(status.state));
}

function segmentLabel(segment) {
  if (!segment) return "-";
  return `${segment.segment_id || "-"}：${segment.tick_start || "-"}-${segment.tick_end || "-"}`;
}

function setSimulationButtons(enabled) {
  $("startSimulation").disabled = !enabled;
  $("stopSimulation").disabled = enabled;
}

function stateText(state) {
  return {
    idle: "空闲",
    running: "运行中",
    stopping: "停止中",
    stopped: "已停止",
    completed: "已完成",
    error: "错误",
  }[state] || state || "-";
}

function formatDuration(seconds) {
  if (!seconds) return "0 分钟";
  if (seconds >= 86400) return `${(seconds / 86400).toFixed(2)} 天`;
  if (seconds >= 3600) return `${(seconds / 3600).toFixed(2)} 小时`;
  return `${Math.round(seconds / 60)} 分钟`;
}

async function renderMarkdownStory(useLlm) {
  const status = $("llmStatus");
  const output = $("llmOutput");
  const apiKey = $("llmApiKey").value.trim();
  const maxFrames = $("llmMaxFrames").value.trim();
  if (useLlm && !apiKey) {
    status.textContent = "请先填写 DeepSeek API Key。";
    return;
  }
  saveLocalSettings();
  status.textContent = useLlm ? "正在请求 DeepSeek 渲染..." : "正在生成确定性故事...";
  output.textContent = "生成中...";
  setRenderButtons(false);
  try {
    const res = await fetch("/api/render", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        use_llm: useLlm,
        provider: useLlm ? "deepseek" : null,
        api_key: useLlm ? apiKey : null,
        model: useLlm ? $("llmModel").value : null,
        thinking: useLlm ? $("llmThinking").value : null,
        reasoning_effort: "high",
        max_frames: maxFrames || null,
      }),
    });
    const payload = await res.json();
    if (!res.ok || payload.error) {
      throw new Error(payload.error || `请求失败：${res.status}`);
    }
    status.textContent = `已生成：${payload.output}`;
    output.innerHTML = markdownToHtml(payload.text || "");
  } catch (error) {
    status.textContent = `生成失败：${error.message}`;
    output.textContent = "";
  } finally {
    setRenderButtons(true);
  }
}

function setRenderButtons(enabled) {
  $("renderLlm").disabled = !enabled;
  $("renderDeterministic").disabled = !enabled;
}

function markdownToHtml(markdown) {
  return String(markdown || "")
    .split(/\n{2,}/)
    .map((block) => {
      const text = block.trim();
      if (!text) return "";
      if (text.startsWith("### ")) return `<h4>${escapeHtml(text.slice(4))}</h4>`;
      if (text.startsWith("## ")) return `<h3>${escapeHtml(text.slice(3))}</h3>`;
      if (text.startsWith("# ")) return `<h2>${escapeHtml(text.slice(2))}</h2>`;
      if (text.startsWith("- ")) {
        return text
          .split("\n")
          .map((line) => `<p class="md-li">${escapeHtml(line.replace(/^- /, ""))}</p>`)
          .join("");
      }
      return `<p>${escapeHtml(text).replace(/\n/g, "<br>")}</p>`;
    })
    .join("");
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

main().catch((error) => {
  document.body.innerHTML = `<pre>${error.stack || error}</pre>`;
});
