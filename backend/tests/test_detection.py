"""
Unit tests for the face detection pipeline (detection.py).

These tests do NOT require a running database or Docker — they test
the pure function process_frame() in isolation.
"""
import base64
import io
import pytest
from PIL import Image
from unittest.mock import MagicMock

from detection import process_frame


def _make_blank_frame(width: int = 320, height: int = 240) -> str:
    """Create a plain grey JPEG and return it as a base64 string."""
    img = Image.new("RGB", (width, height), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode()


def test_process_frame_returns_base64_string():
    """process_frame must always return a valid base64 JPEG string."""
    b64_frame = _make_blank_frame()
    annotated, roi = process_frame(b64_frame)

    decoded = base64.b64decode(annotated)
    img = Image.open(io.BytesIO(decoded))
    assert img.format == "JPEG"


def test_no_face_returns_none_roi():
    """A blank frame has no face — roi should be None."""
    b64_frame = _make_blank_frame()
    _, roi = process_frame(b64_frame)
    assert roi is None
def _make_fake_detector(xmin, ymin, width, height, score):
    class FakeBB:
        pass

    bb = FakeBB()
    bb.xmin = xmin
    bb.ymin = ymin
    bb.width = width
    bb.height = height

    class FakeLocationData:
        relative_bounding_box = bb

    _score = score  # capture into local variable before class definition

    class FakeDetection:
        location_data = FakeLocationData()
        score = [_score]  # ← use _score, not score

    class FakeResults:
        detections = [FakeDetection()]

    fake = MagicMock()
    fake.process.return_value = FakeResults()
    return fake
def test_roi_shape_when_face_detected(monkeypatch):
    """
    If mediapipe returns a detection, the roi dict must have the right keys
    and the coordinates must be within image bounds.
    """
    import detection as det_module

    fake_detector = _make_fake_detector(
        xmin=0.1, ymin=0.1, width=0.3, height=0.4, score=0.95
    )
    # patch _get_detector so it returns our fake regardless of thread
    monkeypatch.setattr(det_module, "_get_detector", lambda: fake_detector)

    b64_frame = _make_blank_frame(640, 480)
    _, roi = process_frame(b64_frame)

    assert roi is not None
    assert set(roi.keys()) == {"frame_id", "x", "y", "width", "height", "confidence"}
    assert 0 <= roi["x"] < 640
    assert 0 <= roi["y"] < 480
    assert roi["width"] > 0
    assert roi["height"] > 0
    assert roi["confidence"] == pytest.approx(0.95)


def test_roi_coordinates_clamped(monkeypatch):
    """
    mediapipe can return bounding boxes that extend outside the frame.
    process_frame must clamp them to valid pixel coordinates.
    """
    import detection as det_module

    fake_detector = _make_fake_detector(
        xmin=-0.05, ymin=-0.05, width=1.2, height=1.2, score=0.8
    )
    monkeypatch.setattr(det_module, "_get_detector", lambda: fake_detector)

    b64_frame = _make_blank_frame(320, 240)
    _, roi = process_frame(b64_frame)

    assert roi["x"] >= 0
    assert roi["y"] >= 0
    assert roi["x"] + roi["width"] <= 320
    assert roi["y"] + roi["height"] <= 240