from __future__ import annotations

import re
from io import BytesIO
from typing import Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image

from app.schemas.models import (
    FieldSummary,
    FormField,
    SaveFieldValuesRequest,
    SaveFieldValuesResponse,
    SessionSummary,
    UploadFormResponse,
)
from app.services.openai_form_service import get_openai_form_service
from app.services.session_service import session_service, FormField as SessionFormField
from app.services.storage_service import store

router = APIRouter(tags=["forms"])


def _generate_field_id(label: str, index: int) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    return f"{normalized or 'field'}_{index}"


@router.get("/session/{session_id}/summary", response_model=SessionSummary)
def get_session_summary(session_id: str):
    session_payload = store.get_full_response(session_id)
    if not session_payload:
        raise HTTPException(status_code=404, detail="Session not found")

    details = []
    filled_count = 0
    skipped_count = 0

    for field in session_payload["fields"]:
        value = (store.get_field_value(session_id, field["field_id"]) or "").strip()
        if value:
            details.append(FieldSummary(field_label=field["label"], value=value, status="Filled"))
            filled_count += 1
        else:
            details.append(FieldSummary(field_label=field["label"], value="-", status="Skipped"))
            skipped_count += 1

    return SessionSummary(
        total_fields=len(session_payload["fields"]),
        filled_count=filled_count,
        skipped_count=skipped_count,
        details=details,
    )


@router.get("/session/{session_id}")
def get_session(session_id: str):
    response = store.get_full_response(session_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return response


@router.get("/session/{session_id}/image")
def get_session_image(session_id: str):
    payload = store.get_image(session_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Image not found for this session")

    return Response(content=payload["image_data"], media_type=payload["mime_type"])


@router.get("/session/{session_id}/generated-image")
def get_generated_image(session_id: str):
    payload = store.get_generated_image(session_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Generated image not found for this session")

    return Response(content=payload["image_data"], media_type=payload["mime_type"])


@router.put("/session/{session_id}/field-values", response_model=SaveFieldValuesResponse)
def save_field_values(session_id: str, req: SaveFieldValuesRequest) -> SaveFieldValuesResponse:
    session_payload = store.get_full_response(session_id)
    if session_payload is None:
        raise HTTPException(status_code=404, detail="Session not found")

    valid_field_ids = {str(field["field_id"]) for field in session_payload["fields"]}
    unknown_field_ids = sorted(set(req.field_values.keys()) - valid_field_ids)
    if unknown_field_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown field_id values: {', '.join(unknown_field_ids)}",
        )

    saved_values: Dict[str, str] = {}
    for field_id, value in req.field_values.items():
        cleaned = value.strip()
        if not cleaned:
            continue
        store.set_field_value(session_id, field_id, cleaned)
        saved_values[field_id] = cleaned
        if session_service.get_session(session_id):
            session_service.store_value(session_id, field_id, cleaned)

    current_values = {}
    for field in session_payload["fields"]:
        existing = store.get_field_value(session_id, field["field_id"])
        if existing:
            current_values[field["field_id"]] = existing

    return SaveFieldValuesResponse(
        session_id=session_id,
        saved_count=len(saved_values),
        field_values=current_values,
    )


@router.post("/analyze-form", response_model=UploadFormResponse)
async def analyze_form(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
) -> UploadFormResponse:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty upload.")

    try:
        pil = Image.open(BytesIO(image_bytes)).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid image data.") from exc

    image_width, image_height = pil.size

    try:
        form_service = get_openai_form_service()
        fields = form_service.analyze_form_fields(
            image_bytes=image_bytes,
            image_width=image_width,
            image_height=image_height,
            mime_type=file.content_type or "image/png",
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"OpenAI form analysis error: {exc}") from exc

    if not fields:
        raise HTTPException(status_code=400, detail="No fillable fields were detected in the form")

    validated_fields: List[FormField] = []
    for idx, field in enumerate(fields):
        try:
            field["field_id"] = _generate_field_id(str(field.get("label", "field")), idx)
            validated_fields.append(FormField(**field))
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid field structure from OpenAI: {exc}",
            ) from exc

    session_id = store.create_session(
        filename=file.filename or "uploaded_image",
        ocr_items=[],
        fields=validated_fields,
        image_width=image_width,
        image_height=image_height,
        image_data=image_bytes,
        image_mime_type=file.content_type or "image/jpeg",
    )

    session_fields = [
        SessionFormField(
            field_id=field.field_id,
            label=field.label,
            bbox=field.bbox,
            input_mode=field.input_mode,
            write_language=field.write_language,
        )
        for field in validated_fields
    ]

    session_service.create_session(
        session_id=session_id,
        fields=session_fields,
        image_width=image_width,
        image_height=image_height,
        selected_language=language,
    )

    return UploadFormResponse(
        session_id=session_id,
        image_width=image_width,
        image_height=image_height,
        ocr_items=[],
        fields=validated_fields,
    )
