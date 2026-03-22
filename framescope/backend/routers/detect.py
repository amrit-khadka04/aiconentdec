import asyncio
import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form

from ensemble import compute_overall, signal_score
from job_store import _store, create_job, update_frame, complete_job, fail_job, get_job
from services.frame_extractor import extract_frames, base64_to_pil
from services.groq_explainer import explain_frame
from services.signal_extractor import compute_signals

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm", ".mkv"}


@router.post("/detect")
async def detect(
    request: Request,
    file: UploadFile = File(...),
    sample_rate: int = Form(30),
    max_frames: int = Form(40),
):
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    video_bytes = await file.read()
    job_id = str(uuid4())
    create_job(job_id, 0)

    asyncio.create_task(
        run_job(
            job_id,
            video_bytes,
            sample_rate,
            max_frames,
            request.app.state.detector,
        )
    )

    return {"job_id": job_id, "status": "processing"}


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/health")
async def health():
    return {"status": "ok"}


async def run_job(
    job_id: str,
    video_bytes: bytes,
    sample_rate: int,
    max_frames: int,
    detector,
) -> None:
    try:
        frames = extract_frames(video_bytes, sample_rate, max_frames)
        _store[job_id]["total_frames"] = len(frames)

        ml_sem = asyncio.Semaphore(2)
        groq_sem = asyncio.Semaphore(3)

        async def process(frame_data: dict) -> dict:
            pil = base64_to_pil(frame_data["base64_jpeg"])

            async with ml_sem:
                loop = asyncio.get_event_loop()
                ml_score = await loop.run_in_executor(None, detector.predict, pil)

            signals = compute_signals(pil)

            # Combined per-frame score: 55% ML model + 30% forensic signals + 15% pessimistic.
            # For per-frame scoring we use a simpler 65/35 split (no top-k available
            # at single-frame level) with lowered AI threshold to reduce false negatives.
            combined = 0.65 * ml_score + 0.35 * signal_score(signals)

            verdict = (
                "ai" if combined >= 0.50
                else "uncertain" if combined >= 0.30
                else "human"
            )

            async with groq_sem:
                explanation = await explain_frame(
                    frame_data["base64_jpeg"],
                    ml_score,
                    verdict,
                    signals,
                    frame_data["timestamp_sec"],
                )

            result = {
                "frame_index": frame_data["frame_index"],
                "timestamp_sec": frame_data["timestamp_sec"],
                "ml_score": round(ml_score, 3),
                "ai_score": round(combined, 3),
                "verdict": verdict,
                "signals": signals,
                "reasons": explanation.get("reasons", []),
                "primary_evidence": explanation.get("primary_evidence", ""),
                "artifact_categories": explanation.get("artifact_categories", []),
                "confidence": explanation.get("confidence", "medium"),
                "base64_jpeg": frame_data["base64_jpeg"],
                "width": frame_data["width"],
                "height": frame_data["height"],
            }
            update_frame(job_id, result)
            return result

        await asyncio.gather(*[process(f) for f in frames])
        overall = compute_overall(get_job(job_id)["results"])
        complete_job(job_id, overall)

    except Exception as e:
        import traceback

        traceback.print_exc()
        fail_job(job_id, str(e))
