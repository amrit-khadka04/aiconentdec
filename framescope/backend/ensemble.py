def compute_overall(frame_results: list) -> dict:
    scores = [f["ai_score"] for f in frame_results]
    overall_score = round(sum(scores) / len(scores), 3)

    verdict = (
        "ai" if overall_score >= 0.65
        else "uncertain" if overall_score >= 0.35
        else "human"
    )

    top3 = sorted(frame_results, key=lambda f: f["ai_score"], reverse=True)[:3]

    signal_keys = [
        "texture_uniformity",
        "noise_level",
        "frequency_artifact",
        "color_uniformity",
    ]
    mean_signals = {
        k: round(
            sum(f["signals"][k] for f in frame_results) / len(frame_results), 3
        )
        for k in signal_keys
    }

    return {
        "overall_score": overall_score,
        "overall_verdict": verdict,
        "frame_count": len(frame_results),
        "ai_frame_count": sum(1 for f in frame_results if f["verdict"] == "ai"),
        "uncertain_frame_count": sum(
            1 for f in frame_results if f["verdict"] == "uncertain"
        ),
        "human_frame_count": sum(
            1 for f in frame_results if f["verdict"] == "human"
        ),
        "top_suspicious_frames": [f["frame_index"] for f in top3],
        "score_timeline": [round(s, 3) for s in scores],
        "mean_signals": mean_signals,
    }
