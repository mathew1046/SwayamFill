import base64


def test_generate_form_image_uses_submitted_values(client, sample_image_bytes, monkeypatch):
    from app.services import openai_image_service

    def _fake_generate(
        self,
        *,
        image_bytes,
        fields,
        output_format="png",
        quality="medium",
        background="opaque",
    ):
        assert image_bytes == sample_image_bytes
        assert output_format == "png"
        assert quality == "medium"
        assert background == "opaque"
        assert fields[0]["field_id"] == "name_0"
        assert fields[0]["value"] == "John Doe"
        return {
            "model": "gpt-image-2",
            "image_base64": base64.b64encode(b"generated-image").decode("utf-8"),
            "revised_prompt": None,
        }

    monkeypatch.setattr(openai_image_service.OpenAIImageService, "generate_filled_form", _fake_generate)

    analyze_resp = client.post(
        "/analyze-form",
        files={"file": ("form.png", sample_image_bytes, "image/png")},
    )
    assert analyze_resp.status_code == 200

    session_id = analyze_resp.json()["session_id"]

    resp = client.post(
        "/generate-form-image",
        json={
            "session_id": session_id,
            "field_values": {
                "name_0": "John Doe",
            },
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"] == session_id
    assert body["model"] == "gpt-image-2"
    assert body["output_format"] == "png"
    assert body["mime_type"] == "image/png"
    assert body["fields_used"] == [
        {
            "field_id": "name_0",
            "label": "Name",
            "value": "John Doe",
        }
    ]
    assert body["generated_image_url"] == f"/session/{session_id}/generated-image"
    assert base64.b64decode(body["image_base64"]) == b"generated-image"


def test_generate_form_image_rejects_unknown_field_ids(client, sample_image_bytes):
    analyze_resp = client.post(
        "/analyze-form",
        files={"file": ("form.png", sample_image_bytes, "image/png")},
    )
    assert analyze_resp.status_code == 200

    session_id = analyze_resp.json()["session_id"]

    resp = client.post(
        "/generate-form-image",
        json={
            "session_id": session_id,
            "field_values": {
                "unknown_field": "John Doe",
            },
        },
    )

    assert resp.status_code == 400
    assert "Unknown field_id" in resp.json()["detail"]
