from __future__ import annotations

import base64
import os
from typing import Dict, List, Optional

import requests


class OpenAIImageService:
    """Generate a filled form image using OpenRouter image-capable models."""

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set in environment")

        self.model_name = os.getenv("OPENROUTER_IMAGE_MODEL", "google/gemini-3-pro-image-preview")
        self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.app_referer = os.getenv("OPENROUTER_HTTP_REFERER", "")
        self.app_title = os.getenv("OPENROUTER_APP_TITLE", "swayamfill")

    def _build_prompt(self, fields: List[Dict[str, object]]) -> str:
        field_lines = []
        for field in fields:
            field_lines.append(
                f"- field_id: {field['field_id']}; label: {field['label']}; "
                f"bbox: {field['bbox']}; value: {field['value']}"
            )

        joined_fields = "\n".join(field_lines)
        return (
            "Generate a clean filled-form image from the original scanned form.\n"
            "Preserve the original form layout, paper texture, printed labels, lines, boxes, borders, logos, and spacing.\n"
            "Only add the requested field values inside the specified bounding boxes.\n"
            "Write the exact value for each field, legibly and aligned to the field area.\n the fields should be filled in a way that they look naturally part of the original image, as if they were filled by hand.\n donot use a computer font. use a natural handwriting style that fits well within the field boxes.\n"
            "Do not invent extra text, do not move fields, do not remove any existing printed content, and do not alter areas outside the provided boxes.\n"
            "If a field value is short, keep it within the box without overflowing.\n"
            "Requested form entries:\n"
            f"{joined_fields}"
        )

    def _extract_image_base64(self, result: Dict[str, object]) -> str:
        choices = result.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("OpenRouter response did not include choices")

        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        if not isinstance(message, dict):
            raise ValueError("OpenRouter response did not include assistant message")

        images = message.get("images")
        if not isinstance(images, list) or not images:
            raise ValueError("OpenRouter response did not include generated image")

        first = images[0]
        if not isinstance(first, dict):
            raise ValueError("OpenRouter image payload is invalid")

        image_url = first.get("image_url")
        if not isinstance(image_url, dict):
            raise ValueError("OpenRouter image URL payload is invalid")

        url = image_url.get("url")
        if not isinstance(url, str) or not url:
            raise ValueError("OpenRouter image URL is missing")

        if url.startswith("data:"):
            marker = ","
            if marker not in url:
                raise ValueError("OpenRouter data URL is malformed")
            return url.split(marker, 1)[1]

        # Some providers may return a temporary URL. Fetch and convert to base64.
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        return base64.b64encode(response.content).decode("utf-8")

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

        encoded_input = base64.b64encode(image_bytes).decode("utf-8")
        input_data_url = f"data:image/png;base64,{encoded_input}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.app_referer:
            headers["HTTP-Referer"] = self.app_referer
        if self.app_title:
            headers["X-OpenRouter-Title"] = self.app_title

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self._build_prompt(fields)},
                        {"type": "image_url", "image_url": {"url": input_data_url}},
                    ],
                }
            ],
            "modalities": ["image", "text"],
            "image_config": {
                "output_format": output_format,
                "quality": quality,
                "background": background,
            },
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=180,
        )
        if response.status_code >= 400:
            raise ValueError(f"OpenRouter image API error {response.status_code}: {response.text}")

        result = response.json()
        image_base64 = self._extract_image_base64(result)

        revised_prompt = None
        if isinstance(result, dict):
            choices = result.get("choices")
            if isinstance(choices, list) and choices and isinstance(choices[0], dict):
                message = choices[0].get("message")
                if isinstance(message, dict):
                    revised_prompt = message.get("content")

        return {
            "model": self.model_name,
            "image_base64": image_base64,
            "revised_prompt": revised_prompt if isinstance(revised_prompt, str) else None,
        }


openai_image_service: Optional[OpenAIImageService] = None


def get_openai_image_service() -> OpenAIImageService:
    global openai_image_service
    if openai_image_service is None:
        openai_image_service = OpenAIImageService()
    return openai_image_service
