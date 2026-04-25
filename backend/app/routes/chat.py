"""
Chat endpoint - Deterministic state machine for form filling.
NO Gemini. NO WebSockets.
Uses Sarvam APIs: Saarika (STT), Sarvam-M (LLM), Bulbul (TTS)

State Machine:
- ASK_INPUT: Ask user for field value via voice
- AWAIT_CONFIRMATION: Wait for user to confirm they wrote it

Events:
- USER_SPOKE: User provided voice input (after STT)
- CONFIRM_DONE: User confirmed writing is complete
"""
import re
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
from app.schemas.models import ChatRequest, ChatResponse, DrawGuideAction
from app.services.sarvam_service import SarvamService
from app.services.session_service import session_service, Phase
from app.services.storage_service import store
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


def _normalize_language(lang: Optional[str]) -> str:
    """Normalize various language codes to short form for all 11 Sarvam AI languages."""
    if not lang:
        return "en"
    lower = str(lang).strip().lower().replace("_", "-")
    # Prefer short code before hyphen if present, e.g., hi-IN -> hi
    if "-" in lower:
        lower = lower.split("-")[0]
    allowed = {"hi", "bn", "kn", "ml", "mr", "od", "pa", "ta", "te", "gu", "en"}
    return lower if lower in allowed else "en"


async def _translate_if_needed(text: str, lang: str, sarvam: SarvamService) -> str:
    if lang == "en":
        return text
    try:
        return await sarvam.translate_text(text, target_language=lang)
    except Exception as e:
        logger.warning(f"Translation failed for lang={lang}: {e}")
        return text


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """
    Deterministic state machine for form filling.
    
    Request Events:
    - USER_SPOKE: User provided voice input (after STT)
    - CONFIRM_DONE: User confirmed writing is complete
    
    Two Phases:
    - ASK_INPUT: Extract value from user speech
    - AWAIT_CONFIRMATION: Wait for user to write and confirm
    """
    
    # ===== STEP 1: Load session state =====
    state = session_service.get_session(req.session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    # Resolve user language: first detected language stored in session or DB, fallback to English.
    stored_lang = state.selected_language or state.detected_language or store.get_language(req.session_id)
    user_lang = _normalize_language(stored_lang)
    
    # ===== STEP 2: Check if form is complete =====
    if not session_service.has_more_fields(req.session_id):
        sarvam = SarvamService()
        completed_text = await _translate_if_needed("You have completed the form. Thank you!", user_lang, sarvam)
        return ChatResponse(
            assistant_text=completed_text,
            action=None,
            is_complete=True
        )
    
    # ===== STEP 3: Get current field =====
    current_field = session_service.get_current_field(req.session_id)
    if not current_field:
        raise HTTPException(status_code=500, detail="No current field")
    
    text = (req.user_text or req.user_message or "").strip()
    event = req.event or "USER_SPOKE"

    confirmation_words = {"done", "finished", "ok", "completed", "yes", "y", "confirmed"}
    if event == "USER_SPOKE" and text:
        if text.lower() in confirmation_words:
            event = "CONFIRM_DONE"

    if event == "SKIP_FIELD":
        session_service.advance_to_next_field(req.session_id)

        if not session_service.has_more_fields(req.session_id):
            sarvam = SarvamService()
            skip_last_text = await _translate_if_needed("You skipped the last field. The form is complete.", user_lang, sarvam)
            return ChatResponse(
                assistant_text=skip_last_text,
                action=None,
                is_complete=True
            )

        next_field = session_service.get_current_field(req.session_id)
        if not next_field:
            raise HTTPException(status_code=500, detail="No next field after skip")

        session_service.set_phase(req.session_id, Phase.ASK_INPUT)
        sarvam = SarvamService()
        skip_text = await _translate_if_needed(
            f"Skipped. Please provide the value for {next_field.label}.",
            user_lang,
            sarvam,
        )
        return ChatResponse(
            assistant_text=skip_text,
            action=None
        )

    if event == "RETRY_FIELD":
        # Reset phase to ASK_INPUT for the current field
        session_service.set_phase(req.session_id, Phase.ASK_INPUT)
        sarvam = SarvamService()
        retry_text = await _translate_if_needed(
            f"Okay, let's try again. Please speak the value for {current_field.label}.",
            user_lang,
            sarvam,
        )
        return ChatResponse(
            assistant_text=retry_text,
            action=None
        )

    sarvam = SarvamService()
    
    # ===== STATE MACHINE LOGIC =====
    
    if state.phase == Phase.ASK_INPUT:
        # ===== PHASE: ASK_INPUT =====
        if event != "USER_SPOKE":
            # Invalid event for this phase
            speak_text = await _translate_if_needed(
                f"Please speak the value for {current_field.label}.", user_lang, sarvam
            )
            return ChatResponse(
                assistant_text=speak_text,
                action=None
            )
        
        if not text:
            raise HTTPException(status_code=400, detail="user_text required for USER_SPOKE event")
        
        # Extract value using Sarvam-M
        extracted_value = await sarvam.extract_field_value(
            field_label=current_field.label,
            user_text=text,
            write_language=current_field.write_language
        )
        
        # Store the value
        session_service.store_value(req.session_id, current_field.field_id, extracted_value)
        
        # Switch to AWAIT_CONFIRMATION phase
        session_service.set_phase(req.session_id, Phase.AWAIT_CONFIRMATION)
        
        # Generate instruction text with placeholder format: "Please write {value} in {field} box"
        field_label = current_field.label
        instruction_text = f"Please write {{{extracted_value}}} in the {field_label} box."
        
        # Translate instruction to user's language (keeping the extracted value in English)
        if user_lang != "en":
            try:
                # Translate only the template, not the value inside braces
                instruction_text = await sarvam.translate_text(instruction_text, target_language=user_lang)
                instruction_text = re.sub(r'\{.*?\}', extracted_value, instruction_text)
            except Exception as e:
                logger.warning(f"Translation failed for instruction lang={user_lang}: {e}")
                # Keep English as fallback
        
        # Return with draw guide action
        return ChatResponse(
            assistant_text=instruction_text,
            action=DrawGuideAction(
                type="DRAW_GUIDE",
                field_id=current_field.field_id,
                    field_label=current_field.label,
                text_to_write=extracted_value,
                bbox=current_field.bbox,
                image_width=state.image_width,
                image_height=state.image_height
            )
        )
    
    elif state.phase == Phase.AWAIT_CONFIRMATION:
        # ===== PHASE: AWAIT_CONFIRMATION =====
        if event != "CONFIRM_DONE":
            # User is speaking when they should be confirming
            return ChatResponse(
                assistant_text=await _translate_if_needed(
                    "Please write it down first, then press the 'Done Writing' button.",
                    user_lang,
                    sarvam,
                ),
                action=DrawGuideAction(
                    type="DRAW_GUIDE",
                    field_id=current_field.field_id,
                    field_label=current_field.label,
                    text_to_write=state.collected_values.get(current_field.field_id, ""),
                    bbox=current_field.bbox,
                    image_width=state.image_width,
                    image_height=state.image_height
                )
            )
        
        # User confirmed - advance to next field
        session_service.advance_to_next_field(req.session_id)
        
        # Check if more fields remain
        if not session_service.has_more_fields(req.session_id):
            done_text = await _translate_if_needed("Great job! The form is complete.", user_lang, sarvam)
            return ChatResponse(
                assistant_t,
                is_complete=True
            )
        
        # Get next field
        next_field = session_service.get_current_field(req.session_id)
        if not next_field:
            fallback_done = await _translate_if_needed("The form is complete.", user_lang, sarvam)
            return ChatResponse(
                assistant_text=fallback_done,
                action=None,
                is_complete=True
            )
        
        # Ask for next field value
        next_instruction = f"Now please say the {next_field.label}."
        if user_lang != "en":
            try:
                next_instruction = await sarvam.translate_text(next_instruction, target_language=user_lang)
            except Exception as e:
                logger.warning(f"Translation failed for next instruction lang={user_lang}: {e}")
        
        return ChatResponse(
            assistant_text=next_instruction,
            action=None
        )

    # Should not reach here
    raise HTTPException(status_code=500, detail="Invalid state")