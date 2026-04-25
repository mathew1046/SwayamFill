from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


@dataclass
class GeminiService:
    """Service for interacting with Google Gemini API."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set in environment")
        # Use gemini-1.5-flash for faster responses, or gemini-1.5-pro for better quality
        self.model_name = "gemini-2.5-flash-lite"
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"

    def analyze_form_fields(
        self, ocr_items: List[Dict[str, Any]], image_width: int, image_height: int, image_base64: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Call Gemini API to identify form fields from OCR data AND image.
        Returns list of field dicts with: label, bbox, input_mode, write_language
        """
        # Build prompt with OCR data
        ocr_text_items = []
        for idx, item in enumerate(ocr_items):
            text = item.get("text", "")
            bbox = item.get("bbox", [0, 0, 0, 0])
            score = item.get("score", 0.0)
            ocr_text_items.append(f"{idx}. '{text}' (confidence: {score:.2f}, bbox: {bbox})")

        ocr_summary = "\n".join(ocr_text_items)

        prompt = f"""You are analyzing a scanned form image. Based on the provided image and OCR text below, identify ONLY the fillable fields that require user input.

Form Dimensions: {image_width}x{image_height} pixels

OCR Data:
{ocr_summary}

CRITICAL FILTERS - EXCLUDE these fields:
1. Office-use-only sections (contains "for office use", "office use only", "stamp", "approval")
2. Pre-printed/pre-filled information (dates, reference numbers already filled)
3. Instructions or informational text (non-data fields)
4. Signature boxes labeled "Office" or "Official"
5. Decorative elements or headers

For EACH user-fillable field, determine:
- label: clear, user-friendly field name (e.g., "Full Name", "Date of Birth", "Mobile Number")
- bbox: [x1, y1, x2, y2] - precise bounding box of the INPUT AREA where user writes (not the label)
- input_mode: "voice" for text/numeric/address, "placeholder" for dates/fixed formats
- write_language: "en" for English, "numeric" for numbers only, "date" for dates

IMPORTANT: Use the image to verify which fields are actually empty/fillable by users (not office fields).

Return ONLY valid JSON array (no markdown, no explanation, no code blocks):
[
  {{
    "label": "Full Name",
    "bbox": [150, 100, 450, 130],
    "input_mode": "voice",
    "write_language": "en"
  }},
  {{
    "label": "Date of Birth",
    "bbox": [150, 150, 350, 180],
    "input_mode": "placeholder",
    "write_language": "date"
  }}
]

JSON array:"""

        try:
            # Prepare request content with image if provided
            parts = []
            
            # Add image if base64 provided
            if image_base64:
                parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": image_base64
                    }
                })
            
            # Add text prompt
            parts.append({"text": prompt})
            
            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": parts}],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 2048,
                    },
                },
                timeout=30,
            )
            response.raise_for_status()

            result = response.json()
            generated_text = result["candidates"][0]["content"]["parts"][0]["text"]

            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r"```json\s*(\[.*?\])\s*```", generated_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                # Try to find raw JSON array
                json_match = re.search(r"(\[.*\])", generated_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1)
                else:
                    json_text = generated_text

            fields = json.loads(json_text)

            # Validate structure
            validated_fields = []
            for field in fields:
                if not isinstance(field, dict):
                    continue
                if "label" not in field or "bbox" not in field:
                    continue
                bbox = field.get("bbox", [])
                if not isinstance(bbox, list) or len(bbox) != 4:
                    continue

                # Set defaults
                field.setdefault("input_mode", "voice")
                field.setdefault("write_language", "en")
                field.setdefault("text", "")

                validated_fields.append(field)

            return validated_fields

        except Exception as e:
            print(f"Gemini API error: {e}")
            return []

    def generate_assistant_text(
        self,
        phase: str,
        field_label: str,
        input_mode: str,
        write_language: str,
        value: str = "",
    ) -> str:
        """Generate contextual assistant instruction for chat flow.
        
        Args:
            phase: "collect_value" | "writing_guide" | "completion"
            field_label: Human-readable field name
            input_mode: "voice" | "placeholder"
            write_language: "en" | "ml" | "numeric"
            value: Collected value (for writing_guide phase)
        
        Returns:
            Assistant text in appropriate language
        """
        # Deterministic templates based on phase
        if phase == "completion":
            return "Great! All fields are completed. Your form is ready."
        
        if phase == "collect_value":
            if input_mode == "voice":
                return f"Please tell me the value for '{field_label}'."
            else:
                # Placeholder fields skip collection
                return f"Moving to '{field_label}'."
        
        if phase == "writing_guide":
            if value:
                return f"Please write '{value}' in the '{field_label}' field. Say 'done' when finished."
            else:
                return f"Please fill the '{field_label}' field. Say 'done' when finished."
        
        return "Please continue."


# Singleton instance
gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get or create Gemini service instance."""
    global gemini_service
    if gemini_service is None:
        gemini_service = GeminiService()
    return gemini_service
