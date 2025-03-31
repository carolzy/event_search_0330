import os
import logging
import tempfile
import base64
import shutil
import json
import httpx
from pathlib import Path
from typing import Dict, Any, Optional
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class VoiceProcessor:
    def __init__(self, flow_controller=None):
        self.flow = flow_controller
        self.temp_dir = Path(tempfile.mkdtemp())
        logger.info(f"Initialized VoiceProcessor with temp dir: {self.temp_dir}")

        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
        self.patterns_path = Path("workflows/patterns_v1.json")
        self.workflow_patterns = self._load_workflow_patterns()

    def _load_workflow_patterns(self) -> Dict[str, Any]:
        try:
            if self.patterns_path.exists():
                with open(self.patterns_path) as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load workflow patterns: {e}")
            return {}

    async def transcribe_audio(self, base64_audio: Optional[str]) -> str:
        if not base64_audio or "," not in base64_audio:
            logger.warning("Invalid or missing base64 audio input")
            return ""

        try:
            audio_path = self._save_base64_audio(base64_audio)
            mp3_path = await self._convert_to_mp3(audio_path)
            transcript = await self._transcribe_with_elevenlabs(mp3_path)
            self._cleanup_files(audio_path, mp3_path)
            return transcript
        except Exception as e:
            logger.error(f"Voice processing failed: {e}")
            return ""

    def _save_base64_audio(self, base64_audio: str) -> Path:
        raw_audio = base64.b64decode(base64_audio.split(",")[-1])
        audio_path = self.temp_dir / "input_audio.wav"
        with open(audio_path, "wb") as f:
            f.write(raw_audio)
        return audio_path

    async def _convert_to_mp3(self, audio_path: Path) -> Path:
        mp3_path = self.temp_dir / "converted_audio.mp3"
        audio = AudioSegment.from_file(audio_path)
        audio.export(mp3_path, format="mp3")
        return mp3_path

    async def _transcribe_with_elevenlabs(self, mp3_path: Path) -> str:
        try:
            async with httpx.AsyncClient() as client:
                with open(mp3_path, "rb") as f:
                    form_data = httpx.MultipartData()
                    form_data.add_field("file", f, filename="audio.mp3", content_type="audio/mpeg")
                    form_data.add_field("model_id", "scribe_v1")

                    response = await client.post(
                        "https://api.elevenlabs.io/v1/speech-to-text",
                        headers={"xi-api-key": self.elevenlabs_api_key},
                        data=form_data
                    )
            if response.status_code == 200:
                return response.json().get("text", "")
            logger.error(f"ElevenLabs API error: {response.status_code} {response.text}")
            return ""
        except Exception as e:
            logger.error(f"ElevenLabs transcription failed: {e}")
            return ""

    async def text_to_speech(self, text: str, context: Optional[Dict] = None) -> Optional[str]:
        if not text or not self.elevenlabs_api_key:
            return None
        try:
            enhanced_text = self._enhance_with_workflow_context(text, context)
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}",
                    headers={
                        "xi-api-key": self.elevenlabs_api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "text": enhanced_text,
                        "model_id": "eleven_turbo_v2",
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.75,
                            "style": 0.3,
                            "speaker_boost": True
                        }
                    }
                )
                if response.status_code == 200:
                    return base64.b64encode(response.content).decode("utf-8")
                logger.warning(f"TTS failed: {response.status_code} {response.text}")
                return None
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return None

    def _enhance_with_workflow_context(self, text: str, context: Optional[Dict]) -> str:
        if not context or not self.workflow_patterns:
            return text
        product = context.get("product", "")
        if not product:
            return text
        pattern = self._find_matching_pattern(product)
        if not pattern:
            return text
        enhancements = []
        if "ideal_customer" in pattern:
            industries = ", ".join(pattern["ideal_customer"].get("industries", []))
            if industries:
                enhancements.append(f"Similar products target {industries} companies.")
        return f"{text} {' '.join(enhancements)}" if enhancements else text

    def _find_matching_pattern(self, product: str) -> Optional[Dict[str, Any]]:
        if not product or not self.workflow_patterns.get("targeting_patterns"):
            return None
        product_lower = product.lower()
        for pattern in self.workflow_patterns["targeting_patterns"]:
            keywords = pattern.get("keywords", "").lower().split("|")
            if any(kw.strip() in product_lower for kw in keywords):
                return pattern
        return None

    def _cleanup_files(self, *paths: Path):
        for path in paths:
            try:
                if path.exists():
                    path.unlink()
            except Exception as e:
                logger.warning(f"Failed to remove temp file {path}: {e}")

    async def cleanup(self):
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

    def __del__(self):
        import asyncio
        asyncio.run(self.cleanup())
