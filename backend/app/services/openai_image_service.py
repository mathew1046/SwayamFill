from __future__ import annotations

import os
from io import BytesIO
from typing import Dict, List, Optional

from openai import OpenAI


class OpenAIImageService:
    """Generate a filled form image using OpenAI's image editing API."""

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")

        self.model_name = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2")
        self.client = OpenAI(api_key=self.api_key)

    def _build_prompt(self, fields: List[Dict[str, object]]) -> str:
        field_lines = []
        for field in fields:
            field_lines.append(
                f"- field_id: {field['field_id']}; label: {field['label']}; "
                f"bbox: {field['bbox']}; value: {field['value']}"
            )

        joined_fields = "\n".join(field_lines)
        return (
            "You are editing a scanned paper form image.\n"
            "Preserve the original form layout, paper texture, printed labels, lines, boxes, borders, logos, and spacing.\n"
            "Only add the requested field values inside the specified bounding boxes.\n"
            "Write the exact value for each field, legibly and aligned to the field area.\n"
            "Do not invent extra text, do not move fields, do not remove any existing printed content, and do not alter areas outside the provided boxes.\n"
            "If a field value is short, keep it within the box without overflowing.\n"
            "Requested form entries:\n"
            f"{joined_fields}"
        )

    def generate_filled_form(
        self,
        *,
        image_bytes: bytes,
        fields: List[Dict[str, object]],
        output_format: str = "png",
        quality: str = "medium",
        background: str = "opaque",
    ) -> Dict[str, Optional[str]]:
        if not fields:
            raise ValueError("At least one field value is required for image generation")

        image_file = BytesIO(image_bytes)
        image_file.name = "form.png"

        result = self.client.images.edit(
            model=self.model_name,
            image=image_file,
            prompt=self._build_prompt(fields),
            output_format=output_format,
            quality=quality,
            background=background,
        )

        if not getattr(result, "data", None):
            raise ValueError("OpenAI image API returned no image data")

        first_image = result.data[0]
        image_base64 = getattr(first_image, "b64_json", None)
        if not image_base64:
            raise ValueError("OpenAI image API response did not include base64 image data")

        return {
            "model": self.model_name,
            "image_base64": image_base64,
            "revised_prompt": getattr(first_image, "revised_prompt", None),
        }


openai_image_service: Optional[OpenAIImageService] = None


def get_openai_image_service() -> OpenAIImageService:
    global openai_image_service
    if openai_image_service is None:
        openai_image_service = OpenAIImageService()
    return openai_image_service
