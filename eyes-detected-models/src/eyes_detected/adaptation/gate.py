def adaptation_gate(
    *, confidence, agreement, consistency, ood, gradable, min_confidence=0.9, min_consistency=0.9
):
    """Decision interface only; no adaptation training performed in starter."""
    if not 0 <= confidence <= 1 or not 0 <= consistency <= 1:
        raise ValueError("Signals must be probabilities")
    if ood or not gradable or not agreement:
        return "QUARANTINE_NO_PSEUDOLABEL"
    if confidence >= min_confidence and consistency >= min_consistency:
        return "HIGH_AGREEMENT_RESEARCH_ONLY"
    return "CONSISTENCY_ONLY"
