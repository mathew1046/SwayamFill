from __future__ import annotations

import base64
from typing import Dict, List

from fastapi import APIRouter, HTTPException

from app.schemas.models import (
    FilledFieldValue,
    GenerateFormImageRequest,
    GenerateFormImageResponse,
)
from app.services.openai_image_service import get_openai_image_service
from app.services.session_service import session_service
from app.services.storage_service import store

router = APIRouter(tags=["image-generation"])


@router.post("/generate-form-image", response_model=GenerateFormImageResponse)
async def generate_form_image(req: GenerateFormImageRequest) -> GenerateFormImageResponse:
    session_payload = store.get_full_response(req.session_id)
    if session_payload is None:
        raise HTTPException(status_code=404, detail="Session not found")

    image_payload = store.get_image(req.session_id)
    if image_payload is None:
        raise HTTPException(status_code=404, detail="Original form image not found")
    image_bytes = image_payload["image_data"]

    field_lookup: Dict[str, Dict[str, object]] = {
        str(field["field_id"]): field for field in session_payload["fields"]
    }

    unknown_field_ids = sorted(set(req.field_values.keys()) - set(field_lookup.keys()))
    if unknown_field_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown field_id values: {', '.join(unknown_field_ids)}",
        )

    merged_values: Dict[str, str] = {}
    state = session_service.get_session(req.session_id)
    if state:
        for field_id, value in state.collected_values.items():
            cleaned = value.strip()
            if cleaned:
                merged_values[field_id] = cleaned

    for field_id in field_lookup:
        stored_value = store.get_field_value(req.session_id, field_id)
        if stored_value:
            merged_values[field_id] = stored_value.strip()

    for field_id, value in req.field_values.items():
        cleaned = value.strip()
        if cleaned:
            merged_values[field_id] = cleaned

    fields_to_render: List[Dict[str, object]] = []
    fields_used: List[FilledFieldValue] = []

    for field_id, value in merged_values.items():
        field = field_lookup.get(field_id)
        if not field or not value:
            continue

        store.set_field_value(req.session_id, field_id, value)
        if state:
            session_service.store_value(req.session_id, field_id, value)

        fields_to_render.append(
            {
                "field_id": field_id,
                "label": field["label"],
                "bbox": field["bbox"],
                "value": value,
            }
        )
        fields_used.append(
            FilledFieldValue(
                field_id=field_id,
                label=str(field["label"]),
                value=value,
            )
        )

    if not fields_to_render:
        raise HTTPException(
            status_code=400,
            detail="No field values available. Provide field_values or complete the chat flow first.",
        )

    try:
        image_service = get_openai_image_service()
        result = image_service.generate_filled_form(
            image_bytes=image_bytes,
            fields=fields_to_render,
            output_format=req.output_format,
            quality=req.quality,
            background=req.background,
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI image generation failed: {exc}") from exc

    image_base64 = str(result["image_base64"])
    try:
        generated_image_bytes = base64.b64decode(image_base64)
        store.set_generated_image(req.session_id, generated_image_bytes, f"image/{req.output_format}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Generated image could not be stored: {exc}") from exc

    return GenerateFormImageResponse(
        session_id=req.session_id,
        model=str(result["model"]),
        output_format=req.output_format,
        mime_type=f"image/{req.output_format}",
        image_base64=image_base64,
        fields_used=fields_used,
        revised_prompt=result.get("revised_prompt"),
        generated_image_url=f"/session/{req.session_id}/generated-image",
    )
