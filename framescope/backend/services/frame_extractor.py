import base64
import os
import tempfile

import cv2
import numpy as np
from PIL import Image


def pil_to_base64(pil_img: Image.Image, quality: int = 85) -> str:
    import io

    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def base64_to_pil(b64_str: str) -> Image.Image:
    import io

    data = base64.b64decode(b64_str)
    return Image.open(io.BytesIO(data)).convert("RGB")


def extract_frames(
    video_bytes: bytes,
    sample_rate: int = 30,
    max_frames: int = 40,
) -> list[dict]:
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name

        cap = cv2.VideoCapture(tmp_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Build list of frame indices to extract
        indices = list(range(0, total_frame_count, sample_rate))

        # Subsample if too many
        if len(indices) > max_frames:
            step = len(indices) / max_frames
            indices = [indices[int(i * step)] for i in range(max_frames)]

        results = []
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret:
                continue

            # BGR → RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Resize: max dimension = 512px, preserve aspect ratio
            h, w = frame_rgb.shape[:2]
            max_dim = 512
            if max(h, w) > max_dim:
                scale = max_dim / max(h, w)
                new_w = int(w * scale)
                new_h = int(h * scale)
                frame_rgb = cv2.resize(
                    frame_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA
                )

            pil_img = Image.fromarray(frame_rgb)
            b64 = pil_to_base64(pil_img, quality=85)

            results.append(
                {
                    "frame_index": idx,
                    "timestamp_sec": round(idx / fps, 2),
                    "base64_jpeg": b64,
                    "width": pil_img.width,
                    "height": pil_img.height,
                }
            )

        cap.release()
        return results

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
