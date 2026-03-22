import threading

_store: dict = {}
_lock = threading.Lock()


def create_job(job_id: str, total_frames: int) -> None:
    with _lock:
        _store[job_id] = {
            "status": "processing",
            "progress": 0.0,
            "total_frames": total_frames,
            "completed_frames": 0,
            "results": [],
            "overall": None,
            "error": None,
        }


def update_frame(job_id: str, frame_result_dict: dict) -> None:
    with _lock:
        job = _store[job_id]
        job["results"].append(frame_result_dict)
        job["completed_frames"] += 1
        total = job["total_frames"]
        if total > 0:
            job["progress"] = round(job["completed_frames"] / total, 3)


def complete_job(job_id: str, overall_dict: dict) -> None:
    with _lock:
        _store[job_id]["status"] = "complete"
        _store[job_id]["overall"] = overall_dict


def fail_job(job_id: str, error_str: str) -> None:
    with _lock:
        _store[job_id]["status"] = "error"
        _store[job_id]["error"] = error_str


def get_job(job_id: str) -> dict | None:
    return _store.get(job_id)
