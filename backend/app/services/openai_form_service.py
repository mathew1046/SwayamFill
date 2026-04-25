from __future__ import annotations

import base64
import json
import os
import re
from typing import Dict, List, Optional

from openai import OpenAI


class OpenAIFormService:
    """Analyze uploaded forms directly with OpenAI vision models."""

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")

        self.model_name = os.getenv("OPENAI_FORM_ANALYSIS_MODEL", "gpt-5.4-mini")
        self.client = OpenAI(api_key=self.api_key)

    def analyze_form_fields(
        self,
        *,
        image_bytes: bytes,
        image_width: int,
        image_height: int,
        mime_type: str = "image/png",
    ) -> List[Dict[str, object]]:
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{mime_type};base64,{image_base64}"

        prompt = f"""
Analyze this uploaded form image and identify the user-fillable fields.

Image size: {image_width}x{image_height} pixels.

Rules:
- Return ONLY fields that a user should fill in.
- Exclude headers, printed instructions, office-use-only areas, signatures, stamps, tables, and already-filled values.
- DONOT RETURN FIELDS WHICH DONOT REQUIRED TO BE FILLED BY THE USER, EVEN IF THEY LOOK LIKE FILLABLE BOXES. DOUVKE CHECK TO ENSURE SUCH FIELDS ARE NOT RETURNED.
- For each field, return the bounding box of the writable area, not the label.
- Keep the original top-to-bottom reading order.
- Use short, user-friendly labels like "Full Name", "Date of Birth", "Address", "Phone Number".
- Use "voice" for free-text and numeric fields.
- Use write_language "numeric" for numbers, "date" for date fields, otherwise "en".
- Add a short hint when obvious, such as "DD/MM/YYYY" or "10-digit number".

Return ONLY valid JSON as an array:
[
  {{
    "label": "Full Name",
    "bbox": [120, 80, 420, 120],
    "input_mode": "voice",
    "write_language": "en",
    "hint": null
  }}
]
"""

        response = self.client.responses.create(
            model=self.model_name,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": data_url},
                    ],
                }
            ],
        )

        raw_text = getattr(response, "output_text", "") or self._extract_output_text(response)
        fields = self._parse_json_array(raw_text)

        validated_fields: List[Dict[str, object]] = []
        for field in fields:
            if not isinstance(field, dict):
                continue
            label = str(field.get("label", "")).strip()
            bbox = field.get("bbox")
            if not label or not isinstance(bbox, list) or len(bbox) != 4:
                continue

            try:
                normalized_bbox = [int(v) for v in bbox]
            except Exception:
                continue

            validated_fields.append(
                {
                    "label": label,
                    "bbox": normalized_bbox,
                    "input_mode": str(field.get("input_mode", "voice")),
                    "write_language": str(field.get("write_language", "en")),
                    "hint": self._normalize_hint(field.get("hint")),
                }
            )

        return validated_fields

    def _extract_output_text(self, response: object) -> str:
        output_items = getattr(response, "output", None) or []
        collected: List[str] = []
        for item in output_items:
            contents = getattr(item, "content", None) or []
            for content in contents:
                text = getattr(content, "text", None)
                if text:
                    collected.append(text)
        return "\n".join(collected)

    def _parse_json_array(self, text: str) -> List[Dict[str, object]]:
        cleaned = text.strip()
        fenced = re.search(r"```json\s*(\[.*?\])\s*```", cleaned, re.DOTALL)
        if fenced:
            cleaned = fenced.group(1)
        else:
            raw = re.search(r"(\[.*\])", cleaned, re.DOTALL)
            if raw:
                cleaned = raw.group(1)

        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, list) else []

    def _normalize_hint(self, hint: object) -> Optional[str]:
        if hint is None:
            return None
        text = str(hint).strip()
        return text or None


openai_form_service: Optional[OpenAIFormService] = None


def get_openai_form_service() -> OpenAIFormService:
    global openai_form_service
    if openai_form_service is None:
        openai_form_service = OpenAIFormService()
    return openai_form_service
