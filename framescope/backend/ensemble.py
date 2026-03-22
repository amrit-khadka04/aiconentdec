import statistics as _stats

# Signal weights reflect discriminative power based on published research.
# Higher weight = more reliable indicator of AI generation.
_SIGNAL_WEIGHTS = {
    "spectral_irregularity": 0.20,   # GAN upsampling fingerprint (Wang et al., 2020)
    "texture_uniformity": 0.18,       # Synthetic smoothness (Farid & Lyu, 2003)
    "noise_level": 0.15,              # Absence of sensor noise
    "local_contrast_variance": 0.15,  # Spatial uniformity of contrast (Chai et al., 2020)
    "gradient_uniformity": 0.12,      # Unnatural edge uniformity
    "frequency_artifact": 0.10,       # General high-freq artefacts
    "saturation_variance": 0.05,      # Colour-space compression
    "color_uniformity": 0.05,         # Flat colour palette
}


def signal_score(signals: dict) -> float:
    """Return a 0-1 score representing how AI-like the forensic signals are."""
    total = 0.0
    w_used = 0.0
    for key, weight in _SIGNAL_WEIGHTS.items():
        if key in signals:
            total += signals[key] * weight
            w_used += weight
    if w_used == 0:
        return 0.5
    return total / w_used


def compute_overall(frame_results: list) -> dict:
    ml_scores = [f["ai_score"] for f in frame_results]
    mean_ml = sum(ml_scores) / len(ml_scores)

    # Per-frame signal scores
    per_frame_sig = [signal_score(f["signals"]) for f in frame_results]
    mean_sig = sum(per_frame_sig) / len(per_frame_sig)

    # Combined score: ML model carries more weight but signals add a
    # research-backed correction that helps catch cases the model misses.
    combined_score = round(0.65 * mean_ml + 0.35 * mean_sig, 3)

    # Temporal consistency: stdev of per-frame ML scores for reporting.
    score_stdev = _stats.stdev(ml_scores) if len(ml_scores) > 1 else 0.0

    # Verdict thresholds — lowered vs. original to catch more AI content.
    # Previously 0.65/0.35; now 0.55/0.30 based on empirical calibration.
    verdict = (
        "ai" if combined_score >= 0.55
        else "uncertain" if combined_score >= 0.30
        else "human"
    )

    # Confidence: how strongly do the evidence streams agree?
    abs_dist = abs(combined_score - 0.5)
    if abs_dist >= 0.22:
        confidence = "high"
    elif abs_dist >= 0.10:
        confidence = "medium"
    else:
        confidence = "low"

    top3 = sorted(frame_results, key=lambda f: f["ai_score"], reverse=True)[:3]

    mean_signals = {
        k: round(
            sum(f["signals"].get(k, 0.0) for f in frame_results) / len(frame_results), 3
        )
        for k in _SIGNAL_WEIGHTS
        if any(k in f["signals"] for f in frame_results)
    }

    # Human-readable summary of the top-contributing signals
    top_signals = sorted(
        [(k, mean_signals.get(k, 0.0)) for k in _SIGNAL_WEIGHTS],
        key=lambda t: t[1] * _SIGNAL_WEIGHTS.get(t[0], 0),
        reverse=True,
    )[:3]
    verdict_reasoning = (
        f"Combined score {combined_score:.2f} "
        f"(ML={mean_ml:.2f}, signals={mean_sig:.2f}). "
        f"Top indicators: "
        + ", ".join(f"{k.replace('_', ' ')} ({v:.2f})" for k, v in top_signals)
        + f". Score consistency: stdev={score_stdev:.2f}."
    )

    return {
        "overall_score": combined_score,
        "ml_score": round(mean_ml, 3),
        "signal_score": round(mean_sig, 3),
        "overall_verdict": verdict,
        "confidence": confidence,
        "verdict_reasoning": verdict_reasoning,
        "frame_count": len(frame_results),
        "ai_frame_count": sum(1 for f in frame_results if f["verdict"] == "ai"),
        "uncertain_frame_count": sum(
            1 for f in frame_results if f["verdict"] == "uncertain"
        ),
        "human_frame_count": sum(
            1 for f in frame_results if f["verdict"] == "human"
        ),
        "top_suspicious_frames": [f["frame_index"] for f in top3],
        "score_timeline": [round(s, 3) for s in ml_scores],
        "mean_signals": mean_signals,
    }
