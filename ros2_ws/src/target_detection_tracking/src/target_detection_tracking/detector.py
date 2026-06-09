"""Detector wrappers used by target detection runtimes."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from target_detection_tracking.core import BoundingBox, Detection


PERSON_LABELS = {"person", "pedestrian", "person_sitting"}


class YoloPersonDetector:
    """Small Ultralytics YOLO wrapper returning ROS-agnostic detections."""

    def __init__(
        self,
        model_path: str | Path,
        confidence: float = 0.25,
        class_names: set[str] | None = None,
    ):
        self.model_path = Path(model_path)
        self.confidence = float(confidence)
        self.class_names = {name.lower() for name in (class_names or PERSON_LABELS)}
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return self._model
        if not self.model_path.exists():
            raise FileNotFoundError(f"YOLO model file does not exist: {self.model_path}")
        from ultralytics import YOLO

        self._model = YOLO(str(self.model_path))
        return self._model

    def detect(self, rgb_image: np.ndarray) -> list[Detection]:
        if rgb_image.ndim != 3 or rgb_image.shape[2] != 3:
            raise ValueError("rgb_image must be HxWx3")
        model = self._load_model()
        results = model.predict(rgb_image, conf=self.confidence, verbose=False)
        if not results:
            return []

        names = results[0].names
        detections: list[Detection] = []
        for box in results[0].boxes:
            cls_id = int(box.cls.item())
            label = str(names.get(cls_id, cls_id))
            if label.lower() not in self.class_names:
                continue
            xyxy = box.xyxy[0].detach().cpu().numpy().astype(float).tolist()
            confidence = float(box.conf.item())
            image_track_id = None
            if getattr(box, "id", None) is not None:
                image_track_id = int(box.id.item())
            detections.append(
                Detection(
                    label=label,
                    confidence=confidence,
                    bbox=BoundingBox.from_xyxy(xyxy),
                    image_track_id=image_track_id,
                )
            )
        return detections
