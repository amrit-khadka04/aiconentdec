from pydantic import BaseModel
from typing import Literal


class FrameResult(BaseModel):
    frame_index: int
    timestamp_sec: float
    ai_score: float
    verdict: Literal["human", "uncertain", "ai"]
    signals: dict[str, float]
    reasons: list[str]
    primary_evidence: str
    artifact_categories: list[str]
    confidence: str
    base64_jpeg: str
    width: int
    height: int


class OverallResult(BaseModel):
    overall_score: float
    ml_score: float
    signal_score: float
    overall_verdict: str
    confidence: str
    verdict_reasoning: str
    frame_count: int
    ai_frame_count: int
    uncertain_frame_count: int
    human_frame_count: int
    top_suspicious_frames: list[int]
    score_timeline: list[float]
    mean_signals: dict[str, float]
