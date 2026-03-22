import statistics as _stats

# Signal weights reflect discriminative power based on published research.
# Higher weight = more reliable indicator of AI generation.
# Weights updated to include new signals and recalibrated per-signal accuracy.
_SIGNAL_WEIGHTS = {
    "spectral_irregularity": 0.15,         # GAN upsampling fingerprint (Wang et al., 2020)
    "texture_uniformity": 0.14,            # Synthetic smoothness (Farid & Lyu, 2003)
    "regional_noise_inconsistency": 0.13,  # Compositing/blending inconsistency (Rossler et al., 2019)
    "noise_level": 0.11,                   # Absence of sensor noise
    "local_contrast_variance": 0.11,       # Spatial uniformity of contrast (Chai et al., 2020)
    "radial_spectral_slope": 0.11,         # 1/f spectrum deviation (Torralba & Oliva, 2003; Liu et al., 2024)
    "gradient_uniformity": 0.09,           # Unnatural edge uniformity
    "frequency_artifact": 0.08,            # Mid-frequency spectral flatness (fixed)
    "saturation_variance": 0.05,           # Colour-space compression
    "color_uniformity": 0.03,              # Flat colour palette
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
    if not frame_results:
        return {
            "overall_score": 0.0,
            "ml_score": 0.0,
            "signal_score": 0.0,
            "overall_verdict": "uncertain",
            "confidence": "low",
            "verdict_reasoning": "No frames were available for analysis.",
            "frame_count": 0,
            "ai_frame_count": 0,
            "uncertain_frame_count": 0,
            "human_frame_count": 0,
            "top_suspicious_frames": [],
            "score_timeline": [],
            "mean_signals": {},
            "ai_coverage": 0.0,
            "peak_ml_score": 0.0,
            "persistence_score": 0.0,
        }

    # Use raw ML prediction scores for the ML component to avoid double-mixing
    # signals.  Per-frame results store both the raw ML score and the combined
    # score; fall back to ai_score (combined) if raw ml_score is unavailable.
    raw_ml_scores = [f.get("ml_score", f["ai_score"]) for f in frame_results]
    mean_ml = sum(raw_ml_scores) / len(raw_ml_scores)

    # Per-frame signal scores re-computed from raw signal values
    per_frame_sig = [signal_score(f["signals"]) for f in frame_results]
    mean_sig = sum(per_frame_sig) / len(per_frame_sig)

    # Pessimistic component: the top-quartile mean of raw ML scores.
    # AI video often contains a subset of frames with strong AI artifacts while
    # other frames may appear borderline.  Weighting the worst frames more
    # heavily reduces false negatives on partially-AI content.
    if len(raw_ml_scores) >= 4:
        top_k = max(1, len(raw_ml_scores) // 4)
        top_k_mean = sum(sorted(raw_ml_scores, reverse=True)[:top_k]) / top_k
    else:
        top_k_mean = mean_ml

    # Temporal consistency: stdev of per-frame combined scores for reporting.
    combined_scores = [f["ai_score"] for f in frame_results]
    score_stdev = _stats.stdev(combined_scores) if len(combined_scores) > 1 else 0.0

    # Additional video-level evidence:
    # - ai_coverage: proportion of strong-AI frames (handles partially AI videos)
    # - peak_ml_score: strongest frame evidence in the video
    # - persistence_score: longest contiguous AI-like segment as a fraction
    ai_like = [1 if s >= 0.55 else 0 for s in raw_ml_scores]
    ai_coverage = sum(ai_like) / len(ai_like)
    peak_ml_score = max(raw_ml_scores)

    max_streak = 0
    streak = 0
    for flag in ai_like:
        if flag:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    persistence_score = max_streak / len(ai_like)

    # Combined overall score:
    #   55% mean ML score          — primary deepfake classifier
    #   25% mean signal score      — forensic heuristics
    #   10% top-quartile ML score  — pessimistic component
    #   10% temporal/risk evidence — coverage + peak + persistence
    temporal_risk = 0.4 * ai_coverage + 0.4 * peak_ml_score + 0.2 * persistence_score
    combined_score = round(
        0.55 * mean_ml + 0.25 * mean_sig + 0.10 * top_k_mean + 0.10 * temporal_risk, 3
    )

    # Verdict thresholds calibrated for the revised combined score.
    verdict = (
        "ai" if combined_score >= 0.50
        else "uncertain" if combined_score >= 0.30
        else "human"
    )

    # Confidence: how strongly do the evidence streams agree?
    abs_dist = abs(combined_score - 0.5)
    if abs_dist >= 0.20:
        confidence = "high"
    elif abs_dist >= 0.09:
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
        f"(ML={mean_ml:.2f}, signals={mean_sig:.2f}, top-quartile ML={top_k_mean:.2f}, "
        f"coverage={ai_coverage:.2f}, peak={peak_ml_score:.2f}, persistence={persistence_score:.2f}). "
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
        "score_timeline": [round(s, 3) for s in combined_scores],
        "mean_signals": mean_signals,
        "ai_coverage": round(ai_coverage, 3),
        "peak_ml_score": round(peak_ml_score, 3),
        "persistence_score": round(persistence_score, 3),
    }
