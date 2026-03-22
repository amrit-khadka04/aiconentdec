import logging
import threading

import torch
from PIL import Image
from transformers import pipeline

logger = logging.getLogger(__name__)

_AI_LABELS = {"FAKE", "LABEL_1", "1", "AI"}
_HUMAN_LABELS = {"REAL", "LABEL_0", "0", "HUMAN"}


class DeepfakeDetector:
    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls):
        with cls._instance_lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._loaded = False
                instance._load()
                cls._instance = instance
        return cls._instance

    def _load(self) -> None:
        device = 0 if torch.cuda.is_available() else -1
        # EfficientNet-B4 trained on 190k real/fake images.
        # Source: https://huggingface.co/dima806/deepfake_vs_real_image_detection
        # Downloads ~400 MB on first run; cached in ~/.cache/huggingface thereafter.
        self.pipe = pipeline(
            "image-classification",
            model="dima806/deepfake_vs_real_image_detection",
            device=device,
        )

        # Run dummy prediction to discover label names
        dummy = Image.new("RGB", (224, 224), color=(128, 128, 128))
        dummy_result = self.pipe(dummy)
        logger.info("Model labels discovered: %s", dummy_result)

        self._label_map: dict[str, str] = {}
        for item in dummy_result:
            label_upper = item["label"].upper()
            if label_upper in _AI_LABELS:
                self._label_map[item["label"]] = "ai"
            elif label_upper in _HUMAN_LABELS:
                self._label_map[item["label"]] = "human"
            else:
                logger.warning("Unknown label from model: %s", item["label"])
                self._label_map[item["label"]] = "unknown"

        self._loaded = True

    def predict(self, pil_image: Image.Image) -> float:
        img = pil_image.convert("RGB").resize((224, 224))
        results = self.pipe(img)

        for item in results:
            label_type = self._label_map.get(item["label"])
            if label_type == "ai":
                return float(item["score"])
            if label_type == "human":
                return 1.0 - float(item["score"])

        # All labels unknown — try raw label names as fallback
        for item in results:
            label_upper = item["label"].upper()
            if label_upper in _AI_LABELS:
                return float(item["score"])
            if label_upper in _HUMAN_LABELS:
                return 1.0 - float(item["score"])

        logger.warning(
            "Could not determine AI/human from labels: %s",
            [r["label"] for r in results],
        )
        return 0.5
