import asyncio
import os
import base64
import httpx
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def test_elevenlabs_tts():
    """Test the ElevenLabs text-to-speech API."""
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
    
    if not elevenlabs_api_key:
        logger.error("No ElevenLabs API key found in environment variables.")
        return
    
    logger.info(f"Using ElevenLabs API key: {elevenlabs_api_key[:10]}...")
    logger.info(f"Using voice ID: {voice_id}")
    
    text = "Hello, this is a test of the ElevenLabs text-to-speech API."
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers={
                    "xi-api-key": elevenlabs_api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
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
                logger.info("ElevenLabs TTS API call successful!")
                
                # Save the audio to a file for testing
                with open("test_tts_output.mp3", "wb") as f:
                    f.write(response.content)
                logger.info("Audio saved to test_tts_output.mp3")
                
                # Also test base64 encoding
                base64_audio = base64.b64encode(response.content).decode("utf-8")
                logger.info(f"Base64 encoded audio (first 50 chars): {base64_audio[:50]}...")
                
                return True
            else:
                logger.error(f"ElevenLabs API error: {response.status_code} {response.text}")
                return False
    except Exception as e:
        logger.error(f"Error testing ElevenLabs TTS: {e}")
        return False

async def test_elevenlabs_stt():
    """Test the ElevenLabs speech-to-text API."""
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    
    if not elevenlabs_api_key:
        logger.error("No ElevenLabs API key found in environment variables.")
        return
    
    logger.info(f"Using ElevenLabs API key: {elevenlabs_api_key[:10]}...")
    
    # Check if we have a test audio file from the TTS test
    if not os.path.exists("test_tts_output.mp3"):
        logger.error("No test audio file found. Run the TTS test first.")
        return
    
    try:
        async with httpx.AsyncClient() as client:
            with open("test_tts_output.mp3", "rb") as f:
                form_data = httpx.MultipartData()
                form_data.add_field("file", f, filename="audio.mp3", content_type="audio/mpeg")
                form_data.add_field("model_id", "scribe_v1")
                
                response = await client.post(
                    "https://api.elevenlabs.io/v1/speech-to-text",
                    headers={"xi-api-key": elevenlabs_api_key},
                    data=form_data
                )
                
                if response.status_code == 200:
                    transcript = response.json().get("text", "")
                    logger.info(f"ElevenLabs STT API call successful!")
                    logger.info(f"Transcript: {transcript}")
                    return True
                else:
                    logger.error(f"ElevenLabs API error: {response.status_code} {response.text}")
                    return False
    except Exception as e:
        logger.error(f"Error testing ElevenLabs STT: {e}")
        return False

async def main():
    """Run the ElevenLabs API tests."""
    logger.info("Testing ElevenLabs text-to-speech API...")
    tts_success = await test_elevenlabs_tts()
    
    if tts_success:
        logger.info("\nTesting ElevenLabs speech-to-text API...")
        await test_elevenlabs_stt()

if __name__ == "__main__":
    asyncio.run(main())
