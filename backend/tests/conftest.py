import io
import sys
import types
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from PIL import Image

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

if "sarvamai" not in sys.modules:
    fake_sarvamai = types.ModuleType("sarvamai")

    class _FakeSarvamAI:
        def __init__(self, *args, **kwargs):
            _ = args, kwargs

    fake_sarvamai.SarvamAI = _FakeSarvamAI
    sys.modules["sarvamai"] = fake_sarvamai


@pytest.fixture()
def app(monkeypatch):
    # Ensure each test run uses an isolated DB file.
    base_dir = BACKEND_ROOT / ".tmp_pytest"
    base_dir.mkdir(exist_ok=True)
    monkeypatch.setenv("swayamfill_DB_PATH", str(base_dir / f"test-{uuid4().hex}.db"))

    from app.main import create_app

    return create_app()


@pytest.fixture()
def client(app):
    return TestClient(app)


@pytest.fixture()
def sample_image_bytes() -> bytes:
    """Generate a tiny in-memory PNG to use for multipart upload tests."""
    img = Image.new("RGB", (300, 120), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture(autouse=True)
def api_keys(monkeypatch):
    """Provide placeholder API keys for tests."""

    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    return True


@pytest.fixture(autouse=True)
def mock_openai_form_analysis(monkeypatch):
    """Stub OpenAI form analysis to avoid network calls during tests."""

    from app.services import openai_form_service

    def _fake_analyze(self, *, image_bytes, image_width, image_height, mime_type="image/png"):
        _ = image_bytes, image_width, image_height, mime_type
        return [
            {
                "label": "Name",
                "bbox": [10, 10, 80, 30],
                "input_mode": "voice",
                "write_language": "en",
                "hint": None,
            }
        ]

    monkeypatch.setattr(openai_form_service.OpenAIFormService, "analyze_form_fields", _fake_analyze)
    return True
