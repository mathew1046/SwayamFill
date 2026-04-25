from fastapi import APIRouter, HTTPException
from fastapi import Body
from fastapi.responses import Response
from app.services.sarvam_service import SarvamService
from app.services.storage_service import store
from app.services.session_service import session_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["tts"])


_BULBUL_V3_SPEAKERS = {
    "aditya", "ritu", "ashutosh", "priya", "neha", "rahul", "pooja", "rohan", "simran", "kavya",
    "amit", "dev", "ishita", "shreya", "ratan", "varun", "manan", "sumit", "roopa", "kabir",
    "aayan", "shubh", "advait", "anand", "tanya", "tarun", "sunny", "mani", "gokul", "vijay",
    "shruti", "suhani", "mohit", "kavitha", "rehan", "soham", "rupali", "niharika",
}


def _lang_to_code(language: str) -> str:
    """Map language code to Sarvam locale code for all 11 supported languages."""
    lang = (language or "en").lower().replace("_", "-")
    if "-" in lang:
        lang = lang.split("-")[0]
    return {
        "hi": "hi-IN",
        "bn": "bn-IN",
        "kn": "kn-IN",
        "ml": "ml-IN",
        "mr": "mr-IN",
        "od": "od-IN",
        "pa": "pa-IN",
        "ta": "ta-IN",
        "te": "te-IN",
        "gu": "gu-IN",
        "en": "en-IN",
    }.get(lang, "en-IN")


def _voice_to_speaker(voice: str) -> str:
    # Map app-level voice to Sarvam Bulbul v3 speakers.
    v = (voice or "default").lower()

    # Friendly aliases used by frontend.
    alias = {
        "default": "priya",
        "female": "priya",
        "male": "rahul",
    }.get(v)
    if alias:
        return alias

    # If caller already passes a valid Sarvam speaker, keep it.
    if v in _BULBUL_V3_SPEAKERS:
        return v

    # Safe default for unknown inputs.
    return "priya"


@router.post("/tts")
async def tts(
    payload: dict = Body(...)
):
    """
    Convert assistant text → speech using Sarvam Bulbul.
    Input JSON:
    - text: text to synthesize
    - language: short code (default ml)
    - voice: 'default' or a specific mapping
    Output: binary audio stream (audio/mpeg)
    """
    text = payload.get("text")
    language = payload.get("language", "en")
    session_id = payload.get("session_id")
    voice = payload.get("voice", "default")
    
    logger.info(f"TTS request received: text='{text}', language={language}, voice={voice}, session_id={session_id}")
    
    if not text:
        logger.error("TTS: No text provided")
        raise HTTPException(status_code=400, detail="text is required")
    
    try:
        sarvam = SarvamService()
        logger.info("TTS: SarvamService initialized")
    except Exception as e:
        logger.error(f"TTS: Sarvam init failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sarvam init failed: {e}")
    
    resolved_language = language
    if session_id:
        state = session_service.get_session(session_id)
        selected_lang = state.selected_language if state else None
        detected_lang = state.detected_language if state else None
        db_lang = store.get_language(session_id)

        # Priority: user-selected language > detected session language > DB language > request language
        resolved_language = selected_lang or detected_lang or db_lang or language

    language_code = _lang_to_code(resolved_language)
    speaker = _voice_to_speaker(voice)
    logger.info(f"TTS: Using language_code={language_code}, speaker={speaker}")

    text_to_speak = text
    normalized_lang = (resolved_language or "en").lower().replace("_", "-")
    if "-" in normalized_lang:
        normalized_lang = normalized_lang.split("-")[0]

    if normalized_lang != "en":
        try:
            text_to_speak = await sarvam.translate_text(text, target_language=normalized_lang)
        except Exception as e:
            logger.error(f"TTS: Translation before synthesis failed for language={normalized_lang}: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"TTS translation failed for selected language '{normalized_lang}'",
            )
    
    try:
        audio_bytes = await sarvam.text_to_speech(
            text=text_to_speak,
            language_code=language_code, 
            speaker=speaker,
            model="bulbul:v3",
        )
        logger.info(f"TTS: Audio generated, size={len(audio_bytes)} bytes")
    except Exception as e:
        logger.error(f"TTS: Sarvam API failed: {e}")
        raise HTTPException(status_code=502, detail=f"TTS failed: {e}")
    
    return Response(content=audio_bytes, media_type="audio/mpeg")