let DATA = null;
let SCENARIOS = [];
let RUNS = [];
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
  restricted: "受限",
  blocked: "被遮蔽",
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
  viability: "可存续性",
  common_ground: "共同现实",
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
  ConstraintActivationEvent: "约束激活",
  ViabilityRequirementEvent: "可存续性要求",
  AffordanceWidthEvent: "可行动宽度",
  DeformationTraceEvent: "变形追踪",
  FutureConstraintEvent: "未来约束",
  DerivedDramaticTensionEvent: "派生戏剧张力",
  CommonGroundEvent: "共同现实更新",
  WitnessStrategyEvent: "证人策略",
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
  protective_silence: "保护性沉默",
  partial_disclosure: "部分透露",
  probing_counterquestion: "试探性反问",
  refusal_to_confirm: "拒绝确认",
  controlled_detail_release: "控制性透露",
  withholding: "保留细节",
  limited_disclosure: "有限透露",
  testing_the_listener: "测试倾听者",
  denial_boundary: "拒认边界",
  controlled_disclosure: "控制透露",
  night_recovery: "夜间恢复",
  workday_friction: "工作日摩擦",
  meal_or_errand_overlap: "吃饭或杂事重叠",
  commute_overlap: "通勤重叠",
  late_return: "晚归",
  waiting_time: "等待时间",
  recovery_window_loss: "恢复窗口损失",
  repair_window_loss: "修复窗口损失",
  evidence_window_loss: "证据窗口损失",
  social_exposure_cost: "公共暴露成本",
  trust_window_loss: "信任窗口损失",
  ordinary_task_spillover: "日常任务外溢",
  sleep_or_body_recovery: "睡眠或身体恢复",
  clean_repair_opening: "干净修复窗口",
  usable_evidence_or_testimony_timing: "可用证据或证词时机",
  private_resolution_before_public_reading: "被公开解读前的私人解决",
  "low-cost_trust_update": "低成本信任更新",
  ordinary_work_or_errand_completion: "普通工作或杂事完成",
  recoverable: "仍可修复",
  narrowing: "可逆性收窄",
  threshold_crossed: "越过阈值",
  symbolic_only: "只能象征性修复",
  ordinary_repair_still_available: "普通修复仍可用",
  direct_repair_still_possible: "直接修复仍可能",
  repair_requires_extra_cost: "修复需要额外代价",
  repair_requires_explicit_counter_history: "修复需要明确改写历史",
  only_symbolic_acknowledgement_remains: "只剩象征性承认",
  case_knowledge_asymmetry: "案件知情不对称",
  testimony_disclosure_risk: "证词披露风险",
  public_private_knowledge_split: "公私知识分裂",
  unspeakable_fact_boundary: "不可说事实边界",
  open_but_costly: "可说但有代价",
  narrowed: "可说性收窄",
  sealed: "被封闭",
  body_management: "身体管理",
  case_fixation: "案件固着",
  threat_monitoring: "威胁监控",
  repair_opportunity: "修复机会",
  avoidance_route: "回避路径",
  memory_intrusion: "记忆侵入",
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
  shared: "共同现实稳定",
  contested: "共同现实争夺",
  fractured: "共同现实断裂",
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
  material_pressure: "物质压力",
  public_face_risk: "公开面子风险",
  speech_inhibition: "言说抑制",
  historical_repair_debt: "历史修复债",
  memory_load: "记忆负荷",
  future_constraint: "未来约束",
  recognition_access: "承认可达性",
  relation_continuation: "关系延续",
  repair_availability: "修复可达性",
  inhibition: "抑制",
  substitution: "替代",
  expression_distortion: "表达扭曲",
  public_mask: "公开面具",
  indirect_adaptation: "间接适应",
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
  reopened_cold_case: "冷案重启",
  partially_legible: "部分可读",
  inconsistent_records: "记录不一致",
  degraded: "退化",
  institutional_rot: "制度腐蚀",
  public_silence: "公共沉默",
  public_attention: "公众关注",
  procedural_gap: "程序缺口",
  testimony_burden: "证词负担",
  recognition_dependency: "承认依赖",
  pattern_attraction: "模式吸引",
  testimony_gap: "证词断裂",
  reality_anchor_loss: "现实锚点松动",
  memory_trigger: "记忆触发",
  witness_fragility: "证人脆弱性",
  institutional_compromise: "制度妥协",
  memory_contamination: "记忆污染",
  decayed_evidence: "腐坏证物",
  institutional_silence: "制度沉默",
  mildew_pressure: "霉味压力",
  spatial_disorientation: "空间迷失",
  map_inconsistency: "地图不一致",
  visual_distortion: "视觉扭曲",
  procedural_fatigue: "程序疲劳",
  evidence_review_contaminates_relation: "证物审阅污染关系",
  testimony_probe_raises_retraction_pressure: "证词追问提高撤回压力",
  symbol_becomes_speakable_but_unstable: "符号被说出但不稳定",
  case_pressure_sediments: "案件压力沉积",
  institutional_silencing: "制度静默",
  public_exposure_forces_movement: "公共曝光推动调查",
  procedural_force_opens_access: "程序力量打开权限",
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
  await loadScenarios();
  await loadRuns();
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

async function loadScenarios() {
  const res = await fetch("/api/scenarios");
  const payload = await res.json();
  SCENARIOS = payload.scenarios || [];
  renderScenarioOptions(payload.current_output_dir);
}

async function loadRuns() {
  const res = await fetch("/api/runs");
  const payload = await res.json();
  RUNS = payload.runs || [];
  renderRunHistory(payload.current_output_dir);
}

function renderAll() {
  renderOverview();
  renderCaseLedger();
  renderCanon();
  renderStory();
  renderLiveStory();
  renderEvolution();
  renderViabilityDynamics();
  renderTicks();
  renderPatterns();
  renderTraces();
  renderEvents();
  renderRunHistory(DATA.run_dir);
}

function renderCaseLedger() {
  const target = $("caseLedger");
  if (!target) return;
  const ledger = DATA.case_ledger || {};
  if (!ledger.case_id && !ledger.case_title) {
    target.innerHTML = "<div class=\"panel\"><small>当前运行没有案件账本。</small></div>";
    return;
  }
  const groups = [
    ["已知事实", ledger.known_facts || [], caseText],
    ["证物", ledger.evidence_items || [], evidenceText],
    ["证词", ledger.testimonies || [], testimonyText],
    ["地点", ledger.locations || [], locationText],
    ["矛盾", ledger.contradictions || [], contradictionText],
    ["未证实异常", ledger.unverified_anomalies || [], anomalyText],
  ];
  const inquiry = DATA.inquiry || [];
  target.innerHTML = `
    <div class="panel case-summary">
      <div>
        <h3>${escapeHtml(ledger.case_title || ledger.case_id || "案件")}</h3>
        <p>${escapeHtml(ledger.doctrine || "案件账本限制故事事实边界。")}</p>
      </div>
      <div class="case-stats">
        <span>阶段 <b>${escapeHtml(zh(ledger.case_phase || "-"))}</b></span>
        <span>事实 <b>${(ledger.known_facts || []).length}</b></span>
        <span>证物 <b>${(ledger.evidence_items || []).length}</b></span>
        <span>矛盾 <b>${(ledger.contradictions || []).length}</b></span>
        <span>推进 <b>${inquiry.length}</b></span>
      </div>
    </div>
    <div class="panel case-group">
      <h3>调查推进</h3>
      ${inquiry.length ? inquiry.slice(-6).reverse().map(inquiryText).join("") : "<small>暂无调查推进</small>"}
    </div>
    <div class="case-grid">
      ${groups.map(([title, rows, formatter]) => `
        <div class="panel case-group">
          <h3>${title}</h3>
          ${rows.length ? rows.slice(0, 6).map((item) => formatter(item)).join("") : "<small>暂无记录</small>"}
        </div>
      `).join("")}
    </div>
  `;
}

function inquiryText(item) {
  if (item.event_type === "InstitutionalPressureEvent") {
    return ledgerItem(`Tick ${item.tick} · ${item.focus_id || "institution"}`, item.institutional_effect || item.label || "-", [
      "制度压力",
      `静默 ${fmt(item.silencing_pressure)}`,
      `曝光 ${fmt(item.public_exposure)}`,
      `程序 ${fmt(item.procedural_force)}`,
      `权限 ${fmt(item.permission_width)}`,
    ]);
  }
  if (item.event_type === "WitnessStrategyEvent") {
    const effects = item.effects || {};
    return ledgerItem(`Tick ${item.tick} · ${item.focus_id || "witness"}`, item.label || item.strategy_label || "-", [
      "证人策略",
      zh(item.strategy_id),
      `保护 ${fmt(item.protective_value)}`,
      `透露宽度 ${fmt(item.disclosure_width)}`,
      `确认风险 ${fmt(item.confirmation_risk)}`,
      `可达变化 ${signed(effects.accessibility_delta)}`,
    ]);
  }
  if (item.event_type === "LocationEvidenceCouplingEvent") {
    const after = item.location_after || {};
    const delta = item.location_delta || {};
    return ledgerItem(`Tick ${item.tick} · ${after.location_id || item.focus_id || "location"}`, item.coupling_reason || after.location_label || "-", [
      "地点-证据耦合",
      after.location_label || "-",
      `地点压力 ${fmt(after.location_pressure)} (${signed(delta.pressure)})`,
      `地点污染 ${fmt(after.contamination)} (${signed(delta.contamination)})`,
      `${zh(after.access_status)} / 可达 ${fmt(after.location_accessibility)}`,
    ]);
  }
  if (item.event_type === "EvidenceAccessibilityEvent") {
    const before = item.accessibility_before || {};
    const after = item.accessibility_after || {};
    return ledgerItem(`Tick ${item.tick} · ${item.focus_id || "access"}`, item.label || item.access_reason || "-", [
      "证据可达性",
      `${zh(before.access_status)} → ${zh(after.access_status)}`,
      `可达 ${fmt(after.accessibility)} (${signed(item.accessibility_delta)})`,
      zh(item.access_reason || ""),
    ]);
  }
  const state = item.state_after || {};
  const deltas = item.deltas || {};
  return ledgerItem(`Tick ${item.tick} · ${item.focus_id || item.inquiry_id}`, item.label || item.narrative_boundary || "-", [
    zh(item.movement),
    `进展 ${fmt(state.progress)} (${signed(deltas.progress)})`,
    `污染 ${fmt(state.contamination)} (${signed(deltas.contamination)})`,
    `关系风险 ${fmt(state.relationship_risk)}`,
  ]);
}

function caseText(item) {
  return ledgerItem(item.fact_id, item.text, [
    `可靠度 ${fmt(item.reliability)}`,
    `污染 ${fmt(item.contamination_risk)}`,
    ...(item.pressure_tags || []).slice(0, 3).map(zh),
  ]);
}

function evidenceText(item) {
  return ledgerItem(item.evidence_id, item.label, [
    zh(item.status),
    `可靠度 ${fmt(item.reliability)}`,
    `污染 ${fmt(item.contamination_risk)}`,
    ...(item.pressures || []).slice(0, 3).map(zh),
  ]);
}

function testimonyText(item) {
  return ledgerItem(item.testimony_id, item.statement, [
    `稳定 ${fmt(item.stability)}`,
    `撤回压力 ${fmt(item.pressure_to_retract)}`,
    `污染暴露 ${fmt(item.contamination_exposure)}`,
  ]);
}

function locationText(item) {
  return ledgerItem(item.location_id, item.label, [
    `污染 ${fmt(item.contamination_risk)}`,
    ...(item.field_effects || []).slice(0, 3).map(zh),
  ]);
}

function contradictionText(item) {
  return ledgerItem(item.contradiction_id, item.text, (item.pressure_tags || []).slice(0, 4).map(zh));
}

function anomalyText(item) {
  return ledgerItem(item.anomaly_id, item.text, [
    `模糊度 ${fmt(item.ambiguity)}`,
    item.may_not_be_supernatural ? "不证明超自然" : "未定",
  ]);
}

function ledgerItem(id, body, tags) {
  return `
    <article class="ledger-item">
      <strong>${escapeHtml(id || "-")}</strong>
      <p>${escapeHtml(body || "-")}</p>
      <div class="tags">${(tags || []).filter(Boolean).map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("")}</div>
    </article>
  `;
}

function renderScenarioOptions(currentOutputDir) {
  const select = $("scenarioSelect");
  if (!select) return;
  select.innerHTML = SCENARIOS.map((scenario) => `
    <option value="${escapeHtml(scenario.path)}">${escapeHtml(scenario.title || scenario.id)}</option>
  `).join("");
  const current = SCENARIOS.find((scenario) => samePath(scenario.output_dir, currentOutputDir));
  if (current) select.value = current.path;
  $("scenarioStatus").textContent = SCENARIOS.length ? `已发现 ${SCENARIOS.length} 个案例` : "没有发现案例文件";
}

function samePath(left, right) {
  return String(left || "").replaceAll("\\", "/").toLowerCase() === String(right || "").replaceAll("\\", "/").toLowerCase();
}

function renderRunHistory(currentOutputDir) {
  const target = $("runHistory");
  if (!target) return;
  target.innerHTML = RUNS.length
    ? RUNS.slice(0, 12).map((run) => `
      <article class="run-item ${samePath(run.output_dir, currentOutputDir) ? "active" : ""}">
        <strong>${escapeHtml(run.title || run.scenario_id || run.run_id)}</strong>
        <small>${escapeHtml(run.scenario_id || "-")} / ${escapeHtml(run.mode || "-")} / ${escapeHtml(run.storage_backend || "file")} / seed ${escapeHtml(run.seed ?? "-")}</small>
        <small>${escapeHtml(run.created_at || "-")} / Tick ${escapeHtml(run.tick ?? "-")} / 事件 ${escapeHtml(run.event_count ?? "-")} / 阶段 ${escapeHtml(zh(run.phase || "-"))}</small>
        <small>${escapeHtml(run.output_dir || run.run_id || "")}</small>
        <div class="run-actions">
          <button type="button" data-run-dir="${escapeAttr(run.output_dir || "")}" data-run-id="${escapeAttr(run.storage_backend === "postgres" ? run.run_id : "")}">打开</button>
          ${run.output_dir ? `<button type="button" data-compare-dir="${escapeAttr(run.output_dir)}">对比当前</button>` : ""}
        </div>
      </article>
    `).join("")
    : "<div class=\"trace\"><small>暂无运行档案。载入案例或开始持续模拟后会生成。</small></div>";
  target.querySelectorAll("button[data-run-dir]").forEach((button) => {
    button.addEventListener("click", () => openRun(button.dataset.runDir, button.dataset.runId));
  });
  target.querySelectorAll("button[data-compare-dir]").forEach((button) => {
    button.addEventListener("click", () => compareRun(button.dataset.compareDir));
  });
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
          ${frame.attention_drift?.dominant_focus ? `<span class="tag">注意：${zh(frame.attention_drift.dominant_focus)}</span>` : ""}
          ${frame.opportunity_cost?.cost_type ? `<span class="tag">机会成本：${zh(frame.opportunity_cost.cost_type)}</span>` : ""}
          ${frame.reversibility?.threshold_state ? `<span class="tag">可逆性：${zh(frame.reversibility.threshold_state)}</span>` : ""}
          ${frame.epistemic_boundary?.boundary_type ? `<span class="tag">信息边界：${zh(frame.epistemic_boundary.boundary_type)}</span>` : ""}
          ${frame.common_ground?.state ? `<span class="tag">共同现实：${zh(frame.common_ground.state)}</span>` : ""}
          ${frame.daily_ecology?.routine_phase ? `<span class="tag">日常：${zh(frame.daily_ecology.routine_phase)}</span>` : ""}
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
    <div class="state-row"><span>日常压力</span><b>${fmt(pressure.daily_ecology_pressure)}</b></div>
    <div class="state-row"><span>信息边界</span><b>${fmt(pressure.epistemic_pressure)}</b></div>
    <div class="state-row"><span>共同现实</span><b>${fmt(pressure.common_ground_pressure)}</b></div>
    <div class="state-row"><span>机会成本</span><b>${fmt(pressure.opportunity_pressure)}</b></div>
    <div class="state-row"><span>可逆性压力</span><b>${fmt(pressure.reversibility_pressure)}</b></div>
    <div class="state-row"><span>冲突压力</span><b>${fmt(pressure.conflict_pressure)}</b></div>
    <div class="state-row"><span>修复债</span><b>${fmt(pressure.repair_debt)}</b></div>
    <div class="state-row"><span>记忆压力</span><b>${fmt(pressure.memory_pressure)}</b></div>
    <div class="state-row"><span>承认压力</span><b>${fmt(pressure.recognition_pressure)}</b></div>
  `;
}

function renderLiveStory() {
  const stream = DATA.rendered_story_stream || "";
  const target = $("liveStoryStream");
  if (!target) return;
  target.innerHTML = stream
    ? markdownToHtml(stream)
    : "<p>还没有自动渲染内容。选择自动渲染后，持续模拟每完成一个最短剧情生命周期就会追加到这里。</p>";
  if (stream && !$("llmOutput").textContent.trim().startsWith("生成后会显示")) {
    return;
  }
  if (stream) $("llmOutput").innerHTML = markdownToHtml(stream);
}

function renderEvolution() {
  const points = buildEvolutionPoints();
  renderPhaseRail(points);
  renderPressureChart(points);
  renderTurningPoints(points);
  renderEvolutionStats(points);
}

function buildEvolutionPoints() {
  const framesByTick = Object.fromEntries((DATA.story || []).map((frame) => [Number(frame.tick), frame]));
  const recognitionByTick = Object.fromEntries((DATA.recognition || []).map((item) => [Number(item.tick), item]));
  return (DATA.scheduler || []).map((tick) => {
    const tickIndex = Number(tick.tick_index || tick.tick || 0);
    const frame = framesByTick[tickIndex] || {};
    const pressure = tick.input_factors || frame.pressure || {};
    const recognition = recognitionByTick[tickIndex] || frame.recognition || {};
    return {
      tick: tickIndex,
      tick_type: tick.selected_tick_type || frame.tick_type || "unknown",
      phase: frame.phase || "-",
      phase_changed: Boolean(frame.phase_changed),
      summary: frame.summary || "",
      recognition_outcome: recognition.outcome || "",
      memory_count: Number(frame.memory_count || 0),
      fate_count: Number(frame.fate_count || 0),
      material_urgency: numberOrNull(pressure.material_urgency),
      daily_ecology_pressure: numberOrNull(pressure.daily_ecology_pressure),
      conflict_pressure: numberOrNull(pressure.conflict_pressure ?? recognition.conflict_pressure),
      repair_debt: numberOrNull(pressure.repair_debt ?? recognition.repair_debt),
      recognition_pressure: numberOrNull(pressure.recognition_pressure ?? recognition.demand_pressure),
      memory_pressure: numberOrNull(pressure.memory_pressure),
      epistemic_pressure: numberOrNull(pressure.epistemic_pressure),
      common_ground_pressure: numberOrNull(pressure.common_ground_pressure),
      opportunity_pressure: numberOrNull(pressure.opportunity_pressure),
      reversibility_pressure: numberOrNull(pressure.reversibility_pressure),
    };
  }).filter((point) => point.tick > 0);
}

function numberOrNull(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function renderPhaseRail(points) {
  const target = $("phaseRail");
  if (!target) return;
  target.innerHTML = points.length
    ? points.map((point) => `
      <div class="phase-segment ${escapeAttr(point.tick_type)} ${point.phase_changed ? "changed" : ""}" title="${escapeAttr(point.summary)}">
        <strong>${point.tick}</strong>
        <span>${escapeHtml(zh(point.phase))}</span>
      </div>
    `).join("")
    : "<div class=\"trace\"><small>暂无阶段轨迹</small></div>";
}

function renderPressureChart(points) {
  const series = [
    {key: "material_urgency", label: "物质紧迫", color: "#296b63"},
    {key: "daily_ecology_pressure", label: "日常压力", color: "#6d7652"},
    {key: "conflict_pressure", label: "冲突压力", color: "#8a4c32"},
    {key: "repair_debt", label: "修复债", color: "#a45f1b"},
    {key: "recognition_pressure", label: "承认压力", color: "#315f8f"},
    {key: "memory_pressure", label: "记忆压力", color: "#6f5a8f"},
    {key: "epistemic_pressure", label: "信息边界", color: "#46635f"},
    {key: "common_ground_pressure", label: "共同现实", color: "#7b4b64"},
    {key: "opportunity_pressure", label: "机会成本", color: "#7a6a2d"},
    {key: "reversibility_pressure", label: "可逆性压力", color: "#8b3d5b"},
  ];
  const width = Math.max(620, points.length * 26);
  const height = 260;
  const pad = 32;
  const values = points.flatMap((point) => series.map((item) => point[item.key]).filter((value) => value !== null));
  const maxValue = Math.max(1, ...values);
  const x = (index) => points.length <= 1 ? pad : pad + (index / (points.length - 1)) * (width - pad * 2);
  const y = (value) => height - pad - (Math.max(0, value) / maxValue) * (height - pad * 2);
  const grid = [0, 0.25, 0.5, 0.75, 1].map((ratio) => {
    const gy = height - pad - ratio * (height - pad * 2);
    return `<line x1="${pad}" y1="${gy}" x2="${width - pad}" y2="${gy}" stroke="#d8dfda" stroke-width="1" /><text x="6" y="${gy + 4}" fill="#66736d" font-size="11">${(ratio * maxValue).toFixed(2)}</text>`;
  }).join("");
  const lines = series.map((item) => {
    const path = linePath(points, item.key, x, y);
    return path ? `<path d="${path}" fill="none" stroke="${item.color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />` : "";
  }).join("");
  const ticks = points.filter((_, index) => index === 0 || index === points.length - 1 || index % Math.ceil(points.length / 8) === 0)
    .map((point, index, arr) => {
      const originalIndex = points.findIndex((item) => item.tick === point.tick);
      const tx = x(originalIndex);
      return `<text x="${tx}" y="${height - 8}" text-anchor="${index === arr.length - 1 ? "end" : "middle"}" fill="#66736d" font-size="11">${point.tick}</text>`;
    }).join("");
  $("pressureChart").innerHTML = points.length
    ? `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="压力曲线">${grid}${lines}<line x1="${pad}" y1="${height - pad}" x2="${width - pad}" y2="${height - pad}" stroke="#bfc8c2" />${ticks}</svg>`
    : "<div class=\"trace\"><small>暂无压力曲线</small></div>";
  $("pressureLegend").innerHTML = series.map((item) => `
    <span class="legend-item"><i class="legend-line" style="background:${item.color}"></i>${item.label}</span>
  `).join("");
}

function linePath(points, key, x, y) {
  let path = "";
  let open = false;
  points.forEach((point, index) => {
    const value = point[key];
    if (value === null) {
      open = false;
      return;
    }
    path += `${open ? "L" : "M"} ${x(index).toFixed(2)} ${y(value).toFixed(2)} `;
    open = true;
  });
  return path.trim();
}

function renderTurningPoints(points) {
  const turns = points.filter((point) =>
    point.phase_changed ||
    point.fate_count > 0 ||
    point.memory_count > 0 ||
    point.recognition_outcome
  );
  $("turningPoints").innerHTML = turns.length
    ? turns.slice(-24).reverse().map((point) => `
      <article class="turning-item">
        <strong>第 ${point.tick} 步 · ${zh(point.tick_type)}</strong>
        <small>${[
          point.phase_changed ? `阶段：${zh(point.phase)}` : "",
          point.recognition_outcome ? `承认：${zh(point.recognition_outcome)}` : "",
          point.memory_count ? `记忆重构 ${point.memory_count}` : "",
          point.fate_count ? `命运转折 ${point.fate_count}` : "",
        ].filter(Boolean).join(" / ")}</small>
        <p>${escapeHtml(localizeSentence(point.summary))}</p>
      </article>
    `).join("")
    : "<div class=\"trace\"><small>暂无关键转折</small></div>";
}

function renderEvolutionStats(points) {
  const last = points[points.length - 1] || {};
  const previous = points[Math.max(0, points.length - 6)] || {};
  const rows = [
    ["物质紧迫", trend(last.material_urgency, previous.material_urgency)],
    ["日常压力", trend(last.daily_ecology_pressure, previous.daily_ecology_pressure)],
    ["冲突压力", trend(last.conflict_pressure, previous.conflict_pressure)],
    ["修复债", trend(last.repair_debt, previous.repair_debt)],
    ["承认压力", trend(last.recognition_pressure, previous.recognition_pressure)],
    ["记忆压力", trend(last.memory_pressure, previous.memory_pressure)],
    ["信息边界", trend(last.epistemic_pressure, previous.epistemic_pressure)],
    ["共同现实", trend(last.common_ground_pressure, previous.common_ground_pressure)],
    ["机会成本", trend(last.opportunity_pressure, previous.opportunity_pressure)],
    ["可逆性压力", trend(last.reversibility_pressure, previous.reversibility_pressure)],
  ];
  $("evolutionStats").innerHTML = rows.map(([label, value]) => `
    <div class="state-row"><span>${label}</span><b>${value}</b></div>
  `).join("");
}

function renderViabilityDynamics() {
  const points = buildViabilityPoints();
  renderViabilityChart(points);
  renderViabilityTickStats(points);
  renderViabilityChain(points);
  renderViabilityConstraints();
}

function buildViabilityPoints() {
  const schedulerByTick = Object.fromEntries((DATA.scheduler || []).map((item) => [Number(item.tick_index || item.tick), item]));
  const actionByTick = Object.fromEntries((DATA.action || []).map((item) => [Number(item.tick), item]));
  const expressionByTick = Object.fromEntries((DATA.expression || []).map((item) => [Number(item.tick), item]));
  const recognitionByTick = Object.fromEntries((DATA.recognition || []).map((item) => [Number(item.tick), item]));
  return (DATA.viability || []).map((trace) => {
    const tick = Number(trace.tick);
    const widths = trace.affordance_widths || [];
    const deformations = trace.deformations || [];
    const requirements = trace.requirements || [];
    const constraints = trace.constraints || [];
    const minWidth = minMetric(widths, "width", 1);
    const directCost = maxMetric(widths, "direct_response_cost");
    const requirementPressure = maxMetric(requirements, "urgency");
    const constraintPressure = maxMetric(constraints, "intensity");
    const deformationDistance = maxMetric(deformations, "deformation_distance");
    const scheduler = schedulerByTick[tick] || {};
    const rhythm = scheduler.viability_rhythm || {};
    return {
      tick,
      tick_type: trace.tick_type || scheduler.selected_tick_type || "unknown",
      viability_pressure: numberOrNull(rhythm.viability_pressure ?? requirementPressure),
      requirement_pressure: numberOrNull(requirementPressure),
      constraint_pressure: numberOrNull(constraintPressure),
      affordance_width: numberOrNull(minWidth),
      affordance_narrowing: numberOrNull(1 - minWidth),
      direct_response_cost: numberOrNull(directCost),
      deformation_distance: numberOrNull(deformationDistance),
      dramatic_tension: numberOrNull(trace.dramatic_tension),
      scene_readiness: numberOrNull(rhythm.scene_readiness),
      action: actionByTick[tick]?.selected_action || {},
      expression: expressionByTick[tick]?.selected_expression || {},
      recognition: recognitionByTick[tick] || {},
      trace,
    };
  }).filter((point) => point.tick > 0);
}

function maxMetric(rows, key, fallback = 0) {
  const values = (rows || []).map((row) => Number(row[key])).filter(Number.isFinite);
  return values.length ? Math.max(...values) : fallback;
}

function minMetric(rows, key, fallback = 0) {
  const values = (rows || []).map((row) => Number(row[key])).filter(Number.isFinite);
  return values.length ? Math.min(...values) : fallback;
}

function renderViabilityChart(points) {
  const series = [
    {key: "viability_pressure", label: "可存续性压力", color: "#225f73"},
    {key: "affordance_narrowing", label: "可行动收窄", color: "#9a5d23"},
    {key: "direct_response_cost", label: "直接回应成本", color: "#7c4f8f"},
    {key: "deformation_distance", label: "变形距离", color: "#8a3f3f"},
    {key: "dramatic_tension", label: "派生张力", color: "#2b6b43"},
  ];
  const width = Math.max(620, points.length * 26);
  const height = 260;
  const pad = 32;
  const x = (index) => points.length <= 1 ? pad : pad + (index / (points.length - 1)) * (width - pad * 2);
  const y = (value) => height - pad - Math.max(0, value) * (height - pad * 2);
  const grid = [0, 0.25, 0.5, 0.75, 1].map((ratio) => {
    const gy = y(ratio);
    return `<line x1="${pad}" y1="${gy}" x2="${width - pad}" y2="${gy}" stroke="#d8dfda" stroke-width="1" /><text x="6" y="${gy + 4}" fill="#66736d" font-size="11">${ratio.toFixed(2)}</text>`;
  }).join("");
  const lines = series.map((item) => {
    const path = linePath(points, item.key, x, y);
    return path ? `<path d="${path}" fill="none" stroke="${item.color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />` : "";
  }).join("");
  const markers = points.map((point, index) => {
    if (!point.recognition?.outcome && !point.deformation_distance) return "";
    return `<circle cx="${x(index)}" cy="${y(point.dramatic_tension || 0)}" r="3.5" fill="#26342f"><title>Tick ${point.tick} ${zh(point.recognition?.outcome || point.tick_type)}</title></circle>`;
  }).join("");
  const ticks = points.filter((_, index) => index === 0 || index === points.length - 1 || index % Math.ceil(points.length / 8) === 0)
    .map((point, index, arr) => {
      const originalIndex = points.findIndex((item) => item.tick === point.tick);
      const tx = x(originalIndex);
      return `<text x="${tx}" y="${height - 8}" text-anchor="${index === arr.length - 1 ? "end" : "middle"}" fill="#66736d" font-size="11">${point.tick}</text>`;
    }).join("");
  $("viabilityChart").innerHTML = points.length
    ? `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="底层动力学曲线">${grid}${lines}${markers}<line x1="${pad}" y1="${height - pad}" x2="${width - pad}" y2="${height - pad}" stroke="#bfc8c2" />${ticks}</svg>`
    : "<div class=\"trace\"><small>暂无底层动力学曲线</small></div>";
  $("viabilityLegend").innerHTML = series.map((item) => `
    <span class="legend-item"><i class="legend-line" style="background:${item.color}"></i>${item.label}</span>
  `).join("");
}

function renderViabilityTickStats(points) {
  const point = points.find((item) => item.tick === selectedTick) || points[points.length - 1] || {};
  $("viabilityTickStats").innerHTML = [
    ["Tick", point.tick || "-"],
    ["类型", zh(point.tick_type || "-")],
    ["可存续性压力", fmt(point.viability_pressure)],
    ["可行动宽度", fmt(point.affordance_width)],
    ["直接回应成本", fmt(point.direct_response_cost)],
    ["变形距离", fmt(point.deformation_distance)],
    ["派生张力", fmt(point.dramatic_tension)],
    ["场景就绪", fmt(point.scene_readiness)],
  ].map(([label, value]) => `<div class="state-row"><span>${label}</span><b>${value}</b></div>`).join("");
}

function renderViabilityChain(points) {
  const point = points.find((item) => item.tick === selectedTick) || points[points.length - 1] || {};
  if (!point.tick) {
    $("viabilityChain").innerHTML = "<div class=\"trace\"><small>暂无因果链</small></div>";
    return;
  }
  const trace = point.trace || {};
  const strongestConstraint = maxBy(trace.constraints || [], "intensity");
  const strongestRequirement = maxBy(trace.requirements || [], "urgency");
  const deformation = (trace.deformations || [])[0] || {};
  const chain = [
    {label: "约束", value: strongestConstraint ? `${zh(strongestConstraint.constraint_type)} ${fmt(strongestConstraint.intensity)}` : "暂无"},
    {label: "要求", value: strongestRequirement ? `${zh(strongestRequirement.requirement_type)} ${fmt(strongestRequirement.urgency)}` : "暂无"},
    {label: "行动", value: point.action?.action_id ? `${zh(point.action.action_id)} / ${zh(point.action.action_mode)}` : "未发生"},
    {label: "表达", value: point.expression?.expression_id ? `${zh(point.expression.expression_id)} / ${zh(point.expression.expression_mode)}` : "未发生"},
    {label: "变形", value: deformation.deformation_type ? `${zh(deformation.deformation_type)} ${fmt(deformation.deformation_distance)}` : "无明显变形"},
    {label: "承认", value: point.recognition?.outcome ? `${zh(point.recognition.outcome)} / ${zh(point.recognition.repair_event_type)}` : "未进入承认评估"},
  ];
  $("viabilityChain").innerHTML = chain.map((item, index) => `
    <div class="chain-node">
      <small>${index + 1}</small>
      <strong>${item.label}</strong>
      <span>${escapeHtml(item.value)}</span>
    </div>
  `).join("");
}

function renderViabilityConstraints() {
  const traces = DATA.viability || [];
  const trace = traces.find((item) => Number(item.tick) === selectedTick) || traces[traces.length - 1];
  if (!trace) {
    $("viabilityConstraints").innerHTML = "<div class=\"trace\"><small>暂无约束记录</small></div>";
    return;
  }
  const rows = [
    ...(trace.constraints || []).slice(0, 4).map((item) => ({
      tick: trace.tick,
      title: zh(item.constraint_type),
      body: zh(item.activation_condition),
      tags: [`强度 ${fmt(item.intensity)}`, ...(item.affected_requirements || []).slice(0, 3).map(zh)],
    })),
    ...(trace.requirements || []).slice(0, 3).map((item) => ({
      tick: trace.tick,
      title: zh(item.requirement_type),
      body: zh(item.minimum_satisfaction_condition),
      tags: [`紧迫 ${fmt(item.urgency)}`, `失败代价 ${fmt(item.failure_cost)}`],
    })),
  ];
  $("viabilityConstraints").innerHTML = traceRows(rows, (item) => item);
}

function maxBy(rows, key) {
  const values = (rows || []).filter((row) => Number.isFinite(Number(row[key])));
  if (!values.length) return null;
  return values.reduce((best, item) => Number(item[key]) > Number(best[key]) ? item : best, values[0]);
}

function trend(current, previous) {
  if (current === null || current === undefined) return "-";
  if (previous === null || previous === undefined) return fmt(current);
  const delta = current - previous;
  const arrow = delta > 0.01 ? "↑" : delta < -0.01 ? "↓" : "→";
  return `${fmt(current)} ${arrow} ${delta >= 0 ? "+" : ""}${delta.toFixed(3)}`;
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
  renderCanonEditor(canon);
}

function renderCanonEditor(canon) {
  const setting = canon.setting || {};
  const narration = canon.narration || {};
  $("canonTitle").value = canon.title || "";
  $("canonPlace").value = setting.place || "";
  $("canonPeriod").value = setting.period || "";
  $("canonAtmosphere").value = setting.atmosphere || "";
  $("canonObjects").value = (setting.material_objects || []).join("\n");
  $("canonStyle").value = narration.style || "";
  $("canonPerspective").value = narration.perspective || "";
  $("canonInteriority").value = narration.interiority_level || "";
  $("canonMetaphor").value = narration.metaphor_level || "";
  $("canonRhythm").value = narration.sentence_rhythm || "";
  $("canonForbidden").value = (narration.forbidden || []).join("\n");
  const cast = canon.cast || {};
  $("castEditor").innerHTML = Object.entries(cast).map(([pid, person]) => `
    <div class="cast-person" data-pid="${escapeAttr(pid)}">
      <h4>${escapeHtml(pid)} · ${escapeHtml(person.name || pid)}</h4>
      <div class="cast-grid">
        <label>姓名<input data-field="name" value="${escapeAttr(person.name || pid)}" /></label>
        <label>性别<input data-field="gender" value="${escapeAttr(person.gender || "")}" /></label>
        <label>代词<input data-field="pronoun" value="${escapeAttr(person.pronoun || "")}" /></label>
        <label>年龄段<input data-field="age_band" value="${escapeAttr(person.age_band || "")}" /></label>
      </div>
      <label>表层位置<input data-field="surface_role" value="${escapeAttr(person.surface_role || "")}" /></label>
      <label>言说风格<input data-field="speech_style" value="${escapeAttr(person.speech_style || "")}" /></label>
      <label>内心描写边界<input data-field="allowed_interiority" value="${escapeAttr(person.allowed_interiority || "")}" /></label>
    </div>
  `).join("");
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
      renderViabilityDynamics();
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
    common_ground_id: "共同现实编号",
    mutual_legibility: "互相可读性",
    interpretive_gap: "解释裂缝",
    shared_definition_width: "共同定义宽度",
    repair_handle_width: "修复抓手宽度",
    dominant_frame: "主导框架",
    contested_fact: "争夺事实",
    consequence: "后果",
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
  $("saveCanon").addEventListener("click", saveCanon);
  $("generateReport").addEventListener("click", generateReport);
  $("exportBundle").addEventListener("click", exportBundle);
  $("refreshRuns").addEventListener("click", refreshRuns);
  $("createScenario").addEventListener("click", createScenario);
  $("loadScenario").addEventListener("click", loadSelectedScenario);
  $("startSimulation").addEventListener("click", startSimulation);
  $("stopSimulation").addEventListener("click", stopSimulation);
  $("saveLlmKey").addEventListener("click", saveKey);
  $("clearLlmKey").addEventListener("click", clearKey);
  $("llmApiKey").addEventListener("input", markKeyDirty);
  $("llmModel").addEventListener("change", saveLocalSettings);
  $("llmThinking").addEventListener("change", saveLocalSettings);
  $("simRenderMode").addEventListener("change", saveLocalSettings);
}

async function refreshRuns() {
  await loadRuns();
  renderRunHistory(DATA?.run_dir);
}

async function createScenario() {
  $("createScenarioStatus").textContent = "正在创建案例并生成预演...";
  $("createScenario").disabled = true;
  try {
    const res = await fetch("/api/scenarios/create", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(collectScenarioDraft()),
    });
    const payload = await res.json();
    if (!res.ok || payload.error) throw new Error(payload.error || `请求失败：${res.status}`);
    DATA = payload.payload;
    SCENARIOS = payload.scenarios || SCENARIOS;
    selectedTick = DATA.scheduler[0]?.tick_index || 1;
    $("createScenarioStatus").textContent = `已创建：${payload.scenario_path}`;
    $("scenarioStatus").textContent = `已载入自定义案例：${DATA.render_canon?.title || "-"}`;
    renderScenarioOptions(DATA.run_dir);
    await loadRuns();
    renderAll();
    await pollSimulationStatus();
  } catch (error) {
    $("createScenarioStatus").textContent = `创建失败：${error.message}`;
  } finally {
    $("createScenario").disabled = false;
  }
}

function collectScenarioDraft() {
  return {
    title: $("newTitle").value,
    place: $("newPlace").value,
    period: $("newPeriod").value,
    bootstrap_steps: $("newBootstrapSteps").value,
    seed: $("simSeed").value,
    p1_name: $("newP1Name").value,
    p2_name: $("newP2Name").value,
    p1_role: $("newP1Role").value,
    p2_role: $("newP2Role").value,
    binding_label: $("newBindingLabel").value,
    recognition_label: $("newRecognitionLabel").value,
    material_urgency: $("newMaterialUrgency").value,
    binding_strength: $("newBindingStrength").value,
    unrecognized_contribution: $("newUnrecognizedContribution").value,
    recognition_pressure: $("newRecognitionPressure").value,
    conflict_pressure: $("newConflictPressure").value,
    repair_debt: $("newRepairDebt").value,
    style: $("newStyle").value,
    atmosphere: $("newAtmosphere").value,
    material_objects: lines($("newObjects").value),
    forbidden: lines($("newForbidden").value),
  };
}

async function openRun(outputDir, runId = "") {
  $("scenarioStatus").textContent = "正在打开历史运行...";
  try {
    const res = await fetch("/api/runs/open", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(runId ? {run_id: runId} : {output_dir: outputDir}),
    });
    const payload = await res.json();
    if (!res.ok || payload.error) throw new Error(payload.error || `请求失败：${res.status}`);
    DATA = payload.payload;
    selectedTick = DATA.scheduler[0]?.tick_index || 1;
    $("scenarioStatus").textContent = `已打开：${DATA.render_canon?.title || outputDir || runId}`;
    await loadRuns();
    renderAll();
    await pollSimulationStatus();
  } catch (error) {
    $("scenarioStatus").textContent = `打开失败：${error.message}`;
  }
}

async function compareRun(outputDir) {
  const target = $("runComparison");
  target.innerHTML = "<div class=\"trace\"><small>正在对比运行...</small></div>";
  try {
    const res = await fetch("/api/runs/compare", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({output_dir: outputDir}),
    });
    const payload = await res.json();
    if (!res.ok || payload.error) throw new Error(payload.error || `请求失败：${res.status}`);
    renderRunComparison(payload);
  } catch (error) {
    target.innerHTML = `<div class="trace"><small>对比失败：${escapeHtml(error.message)}</small></div>`;
  }
}

async function generateReport() {
  const target = $("reportStatus");
  target.innerHTML = "<div class=\"trace\"><small>正在生成运行报告...</small></div>";
  $("generateReport").disabled = true;
  try {
    const res = await fetch("/api/report", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: "{}",
    });
    const payload = await res.json();
    if (!res.ok || payload.error) throw new Error(payload.error || `请求失败：${res.status}`);
    const preview = previewMarkdown(payload.text || "", 1800);
    target.innerHTML = `
      <div class="trace">
        <strong>已生成运行报告</strong>
        <small>${escapeHtml(payload.output || "-")}</small>
      </div>
      <div class="markdown-output compact-output">${markdownToHtml(preview)}</div>
    `;
  } catch (error) {
    target.innerHTML = `<div class="trace"><small>报告生成失败：${escapeHtml(error.message)}</small></div>`;
  } finally {
    $("generateReport").disabled = false;
  }
}

async function exportBundle() {
  const target = $("exportStatus");
  target.innerHTML = "<div class=\"trace\"><small>正在导出运行包...</small></div>";
  $("exportBundle").disabled = true;
  try {
    const res = await fetch("/api/export", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: "{}",
    });
    const payload = await res.json();
    if (!res.ok || payload.error) throw new Error(payload.error || `请求失败：${res.status}`);
    target.innerHTML = `
      <div class="trace">
        <strong>已导出运行包</strong>
        <small>${escapeHtml(payload.output || "-")}</small>
        <div class="tags">${(payload.files || []).slice(0, 12).map((file) => `<span class="tag">${escapeHtml(file)}</span>`).join("")}</div>
        ${(payload.files || []).length > 12 ? `<small>另有 ${(payload.files || []).length - 12} 个文件已打包。</small>` : ""}
      </div>
    `;
  } catch (error) {
    target.innerHTML = `<div class="trace"><small>导出失败：${escapeHtml(error.message)}</small></div>`;
  } finally {
    $("exportBundle").disabled = false;
  }
}

function previewMarkdown(markdown, maxLength) {
  const text = String(markdown || "");
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength)}\n\n- 报告较长，完整内容已写入文件。`;
}

function renderRunComparison(payload) {
  const current = payload.current || {};
  const other = payload.other || {};
  const delta = payload.delta || {};
  $("runComparison").innerHTML = `
    <div class="comparison-grid">
      ${comparisonCard("当前运行", current, false)}
      ${comparisonCard("对照运行", other, false)}
      ${comparisonDeltaCard(delta)}
    </div>
  `;
}

function comparisonCard(title, run) {
  return `
    <section class="comparison-card">
      <h4>${escapeHtml(title)}</h4>
      <div class="comparison-row"><span>标题</span><b>${escapeHtml(run.title || "-")}</b></div>
      <div class="comparison-row"><span>阶段</span><b>${escapeHtml(zh(run.phase || "-"))}</b></div>
      <div class="comparison-row"><span>Tick</span><b>${fmt(run.tick_count)}</b></div>
      <div class="comparison-row"><span>事件</span><b>${fmt(run.event_count)}</b></div>
      <div class="comparison-row"><span>信任</span><b>${fmt(run.trust_score)}</b></div>
      <div class="comparison-row"><span>怨恨</span><b>${fmt(run.resentment_score)}</b></div>
      <div class="comparison-row"><span>修复</span><b>${fmt(run.repair_score)}</b></div>
      <div class="comparison-row"><span>关键转折</span><b>${fmt(run.turning_point_count)}</b></div>
    </section>
  `;
}

function comparisonDeltaCard(delta) {
  const pressure = delta.pressure || {};
  return `
    <section class="comparison-card">
      <h4>差异：当前 - 对照</h4>
      <div class="comparison-row"><span>阶段是否不同</span><b>${delta.phase_changed ? "是" : "否"}</b></div>
      <div class="comparison-row"><span>Tick</span><b>${signed(delta.tick_count)}</b></div>
      <div class="comparison-row"><span>事件</span><b>${signed(delta.event_count)}</b></div>
      <div class="comparison-row"><span>信任</span><b>${signed(delta.trust_score)}</b></div>
      <div class="comparison-row"><span>怨恨</span><b>${signed(delta.resentment_score)}</b></div>
      <div class="comparison-row"><span>修复</span><b>${signed(delta.repair_score)}</b></div>
      <div class="comparison-row"><span>修复债</span><b>${signed(pressure.repair_debt)}</b></div>
      <div class="comparison-row"><span>承认压力</span><b>${signed(pressure.recognition_pressure)}</b></div>
      <div class="comparison-row"><span>当前独有模式</span><b>${escapeHtml((delta.current_only_top_rpps || []).map(zh).join("，") || "-")}</b></div>
      <div class="comparison-row"><span>对照独有模式</span><b>${escapeHtml((delta.other_only_top_rpps || []).map(zh).join("，") || "-")}</b></div>
    </section>
  `;
}

function signed(value) {
  if (value === null || value === undefined) return "-";
  const number = Number(value);
  if (!Number.isFinite(number)) return String(value);
  return `${number > 0 ? "+" : ""}${Number.isInteger(number) ? number : number.toFixed(3)}`;
}

async function saveCanon() {
  const canon = collectCanon();
  $("canonStatus").textContent = "正在保存叙事控制...";
  $("saveCanon").disabled = true;
  try {
    const res = await fetch("/api/canon", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({render_canon: canon}),
    });
    const payload = await res.json();
    if (!res.ok || payload.error) throw new Error(payload.error || `请求失败：${res.status}`);
    $("canonStatus").textContent = `已保存：${payload.output}`;
    await loadData();
    renderAll();
    $("canonStatus").textContent = `已保存：${payload.output}`;
  } catch (error) {
    $("canonStatus").textContent = `保存失败：${error.message}`;
  } finally {
    $("saveCanon").disabled = false;
  }
}

function collectCanon() {
  const cast = {};
  document.querySelectorAll(".cast-person").forEach((node) => {
    const pid = node.dataset.pid;
    cast[pid] = {};
    node.querySelectorAll("[data-field]").forEach((input) => {
      cast[pid][input.dataset.field] = input.value.trim();
    });
  });
  return {
    title: $("canonTitle").value.trim(),
    setting: {
      place: $("canonPlace").value.trim(),
      period: $("canonPeriod").value.trim(),
      atmosphere: $("canonAtmosphere").value.trim(),
      material_objects: lines($("canonObjects").value),
    },
    cast,
    narration: {
      language: "中文",
      tense: "过去时",
      perspective: $("canonPerspective").value.trim(),
      style: $("canonStyle").value.trim(),
      interiority_level: $("canonInteriority").value.trim(),
      metaphor_level: $("canonMetaphor").value.trim(),
      sentence_rhythm: $("canonRhythm").value.trim(),
      forbidden: lines($("canonForbidden").value),
    },
  };
}

function lines(value) {
  return String(value || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

async function loadSelectedScenario() {
  const scenarioPath = $("scenarioSelect").value;
  const bootstrapSteps = $("bootstrapSteps").value;
  $("scenarioStatus").textContent = "正在载入案例并生成初始运行...";
  $("loadScenario").disabled = true;
  try {
    const res = await fetch("/api/scenarios/select", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        scenario_path: scenarioPath,
        bootstrap_steps: bootstrapSteps,
        seed: $("simSeed").value,
      }),
    });
    const payload = await res.json();
    if (!res.ok || payload.error) throw new Error(payload.error || `请求失败：${res.status}`);
    DATA = payload.payload;
    selectedTick = DATA.scheduler[0]?.tick_index || 1;
    $("scenarioStatus").textContent = `已载入：${DATA.render_canon?.title || DATA.manifest?.scenario_path || "-"}`;
    $("llmOutput").textContent = "生成后会显示在这里。";
    await loadRuns();
    renderAll();
    await pollSimulationStatus();
  } catch (error) {
    $("scenarioStatus").textContent = `载入失败：${error.message}`;
  } finally {
    $("loadScenario").disabled = false;
  }
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
      if (["completed", "stopped"].includes(status.state)) await loadRuns();
      renderAll();
    }
    if (status.last_render_text) {
      $("llmOutput").innerHTML = markdownToHtml(status.last_render_text);
      if (!DATA?.rendered_story_stream) $("liveStoryStream").innerHTML = markdownToHtml(status.last_render_text);
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

function escapeAttr(text) {
  return escapeHtml(text).replaceAll("`", "&#096;");
}

main().catch((error) => {
  document.body.innerHTML = `<pre>${error.stack || error}</pre>`;
});
