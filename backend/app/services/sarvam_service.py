"""
Sarvam AI API Service
Handles STT (Saarika), LLM (Sarvam-M), and TTS (Bulbul)
"""
import io
import os
import base64
from sarvamai import SarvamAI


class SarvamService:
    def __init__(self):
        self.api_key = os.getenv("SARVAM_API_KEY")
        self.stub = False

        if not self.api_key:
            # Allow stubbed behavior in tests when key is absent
            self.stub = True
            self.client = None
        else:
            self.client = SarvamAI(api_subscription_key=self.api_key)
    
    async def speech_to_text(self, audio_data: bytes, language_code: str = "unknown") -> tuple[str, str]:
        """
        Convert speech to text using Sarvam Saarika (NO translation) with auto language detection.
        
        Args:
            audio_data: Audio file bytes (wav, mp3, etc.)
            language_code: Language code (e.g., hi-IN) or "unknown" for auto-detect (per Sarvam docs).
        
        Returns:
            (transcript, detected_language_code)
        """
        import asyncio

        if self.stub:
            # Return echo transcript with detected language as provided/unknown
            return "", language_code

        audio_file = io.BytesIO(audio_data)
        audio_file.name = "audio.wav"  # Add a filename attribute
        
        try:
            response = await asyncio.to_thread(
                self.client.speech_to_text.transcribe,
                file=audio_file,
                model="saarika:v2.5",
                language_code=language_code
            )
            detected_language = getattr(response, "language_code", None) or language_code
            return response.transcript, detected_language
        except Exception as e:
            raise RuntimeError(f"Sarvam STT failed: {e}") from e
    
    async def extract_field_value(
        self, 
        field_label: str, 
        user_text: str, 
        write_language: str
    ) -> str:
        """
        Use Sarvam-M LLM to extract field value from user speech
        
        Args:
            field_label: The form field label
            user_text: What the user said
            write_language: Expected language for the field value
        
        Returns:
            Extracted value only (always in English)
        """
        import asyncio
        
        prompt = f"""You are an expert form filling assistant. Extract the precise value for a form field from user speech.

Field Label: "{field_label}"
User Input (in their language): "{user_text}"

CRITICAL RULE: Always return ONLY the extracted value in ENGLISH. Do NOT translate to user language.

Rules:
1. Extract ONLY the exact value to be written - nothing else
2. If user spoke in a language other than English, convert to English (e.g., മാത്യു → Mathew)
3. For names: Use proper case (John Smith, not john smith)
4. For dates: ALWAYS format as DD/MM/YYYY (e.g., 15/08/1995, not August 15 or 8/15/1995)
5. For numbers: Return digits only (e.g., 9876543210, not nine eight seven...)
6. For addresses: Use sentence case, preserve line breaks
7. Remove conversational filler: "The name is...", "I think it's...", "It should be..."
8. If user self-corrects (says "no wait..."), use the FINAL corrected value
9. For empty/irrelevant input, return empty string
10. Never add units or punctuation unless user said them (e.g., "1000 rupees" → "1000", not "1000 Rs")

Return ONLY the extracted value, nothing else:"""

        messages = [
            {
                "role": "system",
                "content": "You are a precise form field value extractor. Output ONLY the extracted value in English, with no additional text, explanations, or translations."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        if self.stub:
            return user_text

        try:
            response = await asyncio.to_thread(
                self.client.chat.completions,
                messages=messages,
                temperature=0.1
            )
            extracted = response.choices[0].message.content.strip()
            return extracted
        except Exception as e:
            raise RuntimeError(f"Sarvam extract failed: {e}") from e
    
    async def generate_instruction_text(
        self, 
        field_label: str, 
        extracted_value: str,
        target_language: str = "en"
    ) -> str:
        """
        Generate instruction text in user's language
        
        Args:
            field_label: Field label
            extracted_value: The value to write
            target_language: Language code for instruction
        
        Returns:
            Instruction text
        """
        import asyncio
        
        prompt = f"""Generate a short instruction in {target_language} telling the user to write the value in the form field.

Field: {field_label}
Value to write: {extracted_value}

Output format: "Please write [value] in the [field] box."
Keep it brief and natural in {target_language}. keep the language of {extracted_value} english"""

        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Generate brief, natural instructions."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        if self.stub:
            return f"Please write {extracted_value} in the {field_label} box."

        try:
            response = await asyncio.to_thread(
                self.client.chat.completions,
                messages=messages,
                temperature=0.3
            )
            instruction = response.choices[0].message.content.strip()
            return instruction
        except Exception as e:
            raise RuntimeError(f"Sarvam instruction failed: {e}") from e

    async def translate_text(self, text: str, target_language: str = "en") -> str:
        """
        Translate arbitrary assistant text into the target language.

        Args:
            text: English text to translate
            target_language: language code such as en, hi, ml

        Returns:
            Translated text (or original on stub/failure)
        """
        import asyncio

        if self.stub or target_language == "en":
            return text

        # Map codes to full names for better LLM performance
        lang_map = {
            "hi": "Hindi",
            "bn": "Bengali",
            "kn": "Kannada",
            "ml": "Malayalam",
            "mr": "Marathi",
            "od": "Odia",
            "pa": "Punjabi",
            "ta": "Tamil",
            "te": "Telugu",
            "gu": "Gujarati",
            "en": "English"
        }
        
        # Handle both "ml" and "ml-IN" formats
        code = target_language.lower().split("-")[0]
        full_lang = lang_map.get(code, target_language)

        prompt = f"""Translate the following assistant message into {full_lang}.
Preserve meaning and keep it concise.

Message:
{text}
"""

        messages = [
            {
                "role": "system",
                "content": f"You are a precise translator. Translate the text to {full_lang}. Return only the translated text without quotes. Keep the original format of the text, if the text has {{}} do not remove them."
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        try:
            response = await asyncio.to_thread(
                self.client.chat.completions,
                messages=messages,
                temperature=0.2,
            )
            translated = response.choices[0].message.content.strip()
            return translated
        except Exception as e:
            raise RuntimeError(f"Sarvam translation failed: {e}") from e
    
    async def text_to_speech(
        self, 
        text: str, 
        language_code: str = "en-IN",
        speaker: str = "anushka"
    ) -> bytes:
        """
        Convert text to speech using Sarvam Bulbul
        
        Args:
            text: Text to synthesize
            language_code: Language code
            speaker: Voice speaker name
        
        Returns:
            Audio bytes (base64 decoded)
        """
        import asyncio
        
        if self.stub:
            return b""

        try:
            response = await asyncio.to_thread(
                self.client.text_to_speech.convert,
                text=text,
                target_language_code=language_code,
                speaker=speaker,
                enable_preprocessing=True
            )
            # Assuming response.audios is a list of base64 strings
            audio_base64 = response.audios[0]
            audio_bytes = base64.b64decode(audio_base64)
            return audio_bytes
        except Exception as e:
            raise RuntimeError(f"Sarvam TTS failed: {e}") from e