from __future__ import annotations

from collections import Counter, defaultdict

from rpf.core.events import Event


def compute_metrics(events: list[Event]) -> dict[str, int | dict[str, int] | dict[str, float]]:
    counts = Counter(e.event_type for e in events)
    affordance_counts = Counter(e.payload.get("affordance_id") for e in events if e.event_type == "AffordanceSelectionEvent")
    action_counts = Counter(e.payload.get("action_id") for e in events if e.event_type == "ActionSelectionEvent")
    action_mode_counts = Counter(e.payload.get("action_mode") for e in events if e.event_type == "ActionSelectionEvent")
    expression_counts = Counter(e.payload.get("expression_id") for e in events if e.event_type == "ExpressionSelectionEvent")
    expression_mode_counts = Counter(e.payload.get("expression_mode") for e in events if e.event_type == "ExpressionSelectionEvent")
    recognition_outcome_counts = Counter(e.payload.get("result") for e in events if e.event_type == "RecognitionEvent")
    operative_label_counts = Counter(e.payload.get("label") for e in events if e.event_type == "OperativeClassificationEvent")
    irreversibility_category_counts = Counter(e.payload.get("category") for e in events if e.event_type == "IrreversibilityEvent")
    memory_bias_counts = Counter(
        bias
        for event in events
        if event.event_type == "MemoryReconstructionEvent"
        for bias in event.payload.get("reconstruction_biases", [])
    )
    rpp_counts = Counter(e.payload.get("rpp_id") for e in events if e.event_type == "RPPActivationEvent")
    composition_counts = Counter(e.payload.get("composition_id") for e in events if e.event_type == "RPPCompositionEvent")
    rpp_score_sums: defaultdict[str, float] = defaultdict(float)
    composition_score_sums: defaultdict[str, float] = defaultdict(float)
    for event in events:
        if event.event_type == "RPPActivationEvent":
            rpp_id = event.payload.get("rpp_id")
            if rpp_id:
                rpp_score_sums[str(rpp_id)] += float(event.payload.get("activation_score", 0.0))
        if event.event_type == "RPPCompositionEvent":
            composition_id = event.payload.get("composition_id")
            if composition_id:
                composition_score_sums[str(composition_id)] += float(event.payload.get("composition_score", 0.0))
    return {
        "event_count": len(events),
        "event_type_counts": dict(counts),
        "affordance_counts": {k: v for k, v in affordance_counts.items() if k},
        "action_counts": {k: v for k, v in action_counts.items() if k},
        "action_mode_counts": {k: v for k, v in action_mode_counts.items() if k},
        "expression_counts": {k: v for k, v in expression_counts.items() if k},
        "expression_mode_counts": {k: v for k, v in expression_mode_counts.items() if k},
        "recognition_outcome_counts": {k: v for k, v in recognition_outcome_counts.items() if k},
        "operative_label_counts": {k: v for k, v in operative_label_counts.items() if k},
        "irreversibility_category_counts": {k: v for k, v in irreversibility_category_counts.items() if k},
        "memory_bias_counts": {k: v for k, v in memory_bias_counts.items() if k},
        "rpp_activation_counts": {k: v for k, v in rpp_counts.items() if k},
        "rpp_activation_score_sums": {k: round(v, 4) for k, v in rpp_score_sums.items()},
        "rpp_composition_counts": {k: v for k, v in composition_counts.items() if k},
        "rpp_composition_score_sums": {k: round(v, 4) for k, v in composition_score_sums.items()},
        "operative_classification_count": counts["OperativeClassificationEvent"],
        "irreversibility_count": counts["IrreversibilityEvent"],
        "memory_reconstruction_count": counts["MemoryReconstructionEvent"],
        "action_inhibition_count": counts["ActionInhibitionEvent"],
        "action_substitution_count": counts["ActionSubstitutionEvent"],
    }


