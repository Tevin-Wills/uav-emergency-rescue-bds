from target_detection_tracking.detector import PERSON_LABELS, YoloPersonDetector


def test_detector_wrapper_defers_ultralytics_import_until_runtime(tmp_path):
    model_path = tmp_path / "missing.pt"
    detector = YoloPersonDetector(model_path=model_path, confidence=0.4)

    assert detector.model_path == model_path
    assert detector.confidence == 0.4
    assert "person" in PERSON_LABELS
