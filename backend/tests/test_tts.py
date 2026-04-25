from app.services import sarvam_service


def test_tts_invalid_voice_falls_back_to_bulbul_v3_default(client, monkeypatch):
    captured = {}

    async def fake_tts(self, text, language_code="en-IN", speaker="priya", model="bulbul:v3"):
        captured["text"] = text
        captured["language_code"] = language_code
        captured["speaker"] = speaker
        captured["model"] = model
        return b"fake-audio"

    monkeypatch.setattr(sarvam_service.SarvamService, "text_to_speech", fake_tts)

    response = client.post(
        "/tts",
        json={
            "text": "Hello",
            "language": "en",
            "voice": "anushka",
        },
    )

    assert response.status_code == 200
    assert response.content == b"fake-audio"
    assert captured == {
        "text": "Hello",
        "language_code": "en-IN",
        "speaker": "priya",
        "model": "bulbul:v3",
    }


def test_normalize_tts_speaker_maps_known_aliases_and_unknowns():
    assert sarvam_service.normalize_tts_speaker("default", model="bulbul:v3") == "priya"
    assert sarvam_service.normalize_tts_speaker("male", model="bulbul:v3") == "rahul"
    assert sarvam_service.normalize_tts_speaker("aditya", model="bulbul:v3") == "aditya"
    assert sarvam_service.normalize_tts_speaker("anushka", model="bulbul:v3") == "priya"
