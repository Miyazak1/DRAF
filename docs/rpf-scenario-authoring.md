# RPF Scenario Authoring Guide

## 0. Purpose

This document defines how to author RPF scenarios.

An RPF scenario must not start from fixed characters with personality traits.

It must start from:

```text
field conditions
process positions
bindings
recognition demands
habitus tendencies
RPP susceptibilities
irreversible history
```

The goal is not to write a plot. The goal is to configure a generative relational field.

---

## 1. Scenario Package

A scenario package contains:

```text
scenario.yaml
field.yaml
processes.yaml
bindings.yaml
recognition.yaml
history.yaml
rpp_overrides.yaml optional
runtime_config.yaml
render_canon.yaml optional
```

---

## 2. Forbidden Scenario Inputs

Do not write:

```text
A is avoidant.
B is anxious.
They trust each other 0.6.
Their relationship is toxic.
The plot is that A betrays B.
```

Instead write:

```text
A has high speech inhibition under dependency claims.
B has high relevance weight for delayed replies.
Their shared housing raises exit cost.
A previous unacknowledged sacrifice remains unresolved.
Silence has repeatedly been interpreted as withdrawal.
```

---

## 3. scenario.yaml

```yaml
id: shared_apartment_unresolved_sacrifice
name: Shared Apartment, Unresolved Sacrifice
description: >
  Two process positions remain materially and narratively bound after
  one absorbed a major cost that the other has never recognized.
steps: 100
seed: 42
initial_tick: 0
```

---

## 4. field.yaml

Define the field as constraints and affordances.

```yaml
material_conditions:
  resources:
    rent:
      amount_due: 1800
      due_in_ticks: 3
      controlled_by: [p1, p2]
  labor_obligations:
    - id: labor_001
      kind: household
      assigned_to: p1
      visibility: low
      recovery_cost: 0.6

institutional_orders:
  - id: lease
    domain: market
    recognized_roles: [co_tenant]
    sanctions:
      - late_fee
      - eviction_risk

spatial_arrangements:
  shared_spaces: [kitchen, bedroom, entryway]
  private_spaces:
    p1: desk_corner
    p2: balcony

audience_network:
  imagined_audiences:
    - id: mutual_friends
      relevance: 0.5
```

---

## 5. processes.yaml

Define process positions, not complete people.

```yaml
processes:
  - id: p1
    display_name: A
    body_position:
      fatigue_level: 0.7
      recovery_need: 0.8
    field_positions:
      - field_name: work
        economic_capital: 0.4
        symbolic_capital: 0.5
        sanction_exposure: 0.6
    embodied_habitus:
      speech_inhibition:
        direct_need: 0.7
        anger: 0.6
      shame_threshold:
        being_needy: 0.4
      threat_sensitivity:
        being_used: 0.8
    relevance_landscape:
      symbolic_triggers:
        unacknowledged_help: 0.9
        delayed_reply: 0.5

  - id: p2
    display_name: B
    body_position:
      fatigue_level: 0.5
    embodied_habitus:
      speech_inhibition:
        apology: 0.8
        dependency_admission: 0.7
      threat_sensitivity:
        being_controlled: 0.8
    relevance_landscape:
      symbolic_triggers:
        repeated_questions: 0.8
```

---

## 6. bindings.yaml

Bindings explain continued co-presence.

```yaml
bindings:
  - id: bind_lease
    type: material
    process_ids: [p1, p2]
    strength: 0.9
    exit_cost:
      p1: 0.8
      p2: 0.6

  - id: bind_unrecognized_contribution
    type: recognition
    process_ids: [p1, p2]
    strength: 0.75
    asymmetry:
      p1: 0.9
      p2: 0.4
```

---

## 7. recognition.yaml

Recognition demands are central.

```yaml
recognition_demands:
  - id: rec_001
    holder_process_id: p1
    demanded_from: p2
    recognition_type: admit_what_happened
    explicitness: 0.2
    vulnerability_cost: 0.8
    threat_if_denied: 0.9
    identity_dependency: 0.7

  - id: rec_002
    holder_process_id: p2
    demanded_from: p1
    recognition_type: allow_nonchange
    explicitness: 0.1
    vulnerability_cost: 0.6
    threat_if_denied: 0.7
```

---

## 8. history.yaml

History should encode irreversible or potentially reclassified events.

```yaml
historical_events:
  - id: hist_001
    type: sacrifice
    summary: A paid several months of rent when B could not.
    public: false
    recognized_by:
      p1: true
      p2: partial
    current_interpretations:
      p1: unacknowledged_sacrifice
      p2: temporary_help
    irreversible_potential: high

  - id: hist_002
    type: repair_avoidance
    summary: B cooked dinner after an argument but did not apologize.
    current_interpretations:
      p1: apology_substitute
      p2: repair_attempt
```

---

## 9. rpp_overrides.yaml

Use this only to tune the RPP library for the scenario.

```yaml
rpp_overrides:
  pursuit_withdrawal:
    activation_modifiers:
      unacknowledged_sacrifice: 0.2
  contribution_debt_loop:
    activation_threshold: 0.45
```

Do not create plot outcomes here.

---

## 10. runtime_config.yaml

```yaml
runtime:
  max_ticks: 100
  snapshot_interval: 5
  llm_rendering: optional
  deterministic_replay: true
  scene_threshold: 0.55
  random_seed: 42
```

---

## 11. render_canon.yaml

`render_canon` defines surface reality for rendering.

It does not define personality.

It does not decide plot.

It exists because literary prose needs concrete names, pronouns, setting texture, and style limits, while the simulator must remain the causal authority.

Example:

```yaml
render_canon:
  title: 共享公寓：未解决的牺牲
  setting:
    place: 共享公寓
    period: 当代城市
    atmosphere: 克制、逼仄、日常压力持续存在
    material_objects:
      - 电费单
      - 房租转账记录
      - 厨房水槽
      - 玄关鞋柜
  cast:
    p1:
      name: 许知遥
      gender: 女
      pronoun: 她
      age_band: 二十多岁后段
      surface_role: 更常承担日常事务和费用垫付的人
      speech_style: 克制、短句、很少直接索取
      allowed_interiority: 只允许从行为、停顿、语气和选择中推断
    p2:
      name: 沈砚
      gender: 男
      pronoun: 他
      age_band: 三十岁出头
      surface_role: 更常回避确认与承认的人
      speech_style: 解释多于承认，倾向拖延或转移
      allowed_interiority: 只允许写可观察到的迟疑、回避和言语选择
  narration:
    language: 中文
    tense: 过去时
    perspective: 第三人称限制视角
    style: 克制的现实主义文学
    interiority_level: 低
    metaphor_level: 低到中
    forbidden:
      - 新增亲属关系
      - 新增职业
      - 新增外部地点
      - 新增童年回忆
      - 新增未来预告
```

Allowed:

- names
- pronouns
- surface roles
- style constraints
- sensory vocabulary bounds
- forbidden invention list

Forbidden:

- fixed personality traits
- guaranteed outcomes
- hidden motives
- future plot
- causal state changes

Rule:

```text
processes define relational positions
render_canon defines literary appearance
events define what happened
LLM only renders their intersection
```

---

## 12. Scenario Quality Checklist

A valid scenario answers:

- Why do these process positions continue to encounter each other?
- What field pressures make avoidance costly?
- Which recognition demands are latent?
- Which micro signals are likely to become meaningful?
- Which RPPs are plausible?
- What past events may be reclassified?
- What actions are unavailable to each position?
- What would count as repair?
- What would count as irreversibility?

---

## 13. Bad Scenario Example

Invalid:

```yaml
A:
  personality: avoidant
B:
  personality: anxious
relationship:
  trust: 0.6
plot:
  - B confronts A
  - A leaves
```

Valid replacement:

```yaml
processes:
  p1:
    speech_inhibition:
      direct_dependency: 0.8
    threat_sensitivity:
      being_controlled: 0.9
  p2:
    relevance_triggers:
      delayed_reply: 0.9
bindings:
  shared_work_project:
    exit_cost:
      p1: 0.7
      p2: 0.7
history:
  unrepaired_departure:
    interpretation_gap:
      p1: needed_space
      p2: abandonment
```

---

## 14. Authoring Principle

Do not write what will happen.

Write the conditions under which some things become more likely, more costly, more meaningful, or more impossible.

