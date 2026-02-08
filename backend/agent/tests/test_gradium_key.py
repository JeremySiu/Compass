"""
Test Gradium API key and services (TTS + STT).
Run from backend directory: python -m agent.tests.test_gradium_key
Ensures Gradium is working so the microphone button uses backend STT.
"""
import os
import sys
import ssl
import asyncio
import struct
from pathlib import Path

# Ensure backend root is on path (same as main.py)
_backend_root = Path(__file__).resolve().parent.parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

# Use certifi CA bundle for SSL (fixes CERTIFICATE_VERIFY_FAILED on macOS with Python from python.org)
# Must be set before aiohttp/gradium are imported (they create SSL context at import time).
import certifi
_cert_file = certifi.where()
os.environ["SSL_CERT_FILE"] = _cert_file
os.environ["REQUESTS_CA_BUNDLE"] = _cert_file
_orig_create_default_context = ssl.create_default_context
def _ssl_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=None, capath=None, cadata=None):
    if cafile is None and capath is None and cadata is None:
        return _orig_create_default_context(purpose=purpose, cafile=_cert_file, capath=capath, cadata=cadata)
    return _orig_create_default_context(purpose=purpose, cafile=cafile, capath=capath, cadata=cadata)
ssl.create_default_context = _ssl_default_context
ssl._create_default_https_context = lambda: _ssl_default_context()

from dotenv import load_dotenv

_env_file = _backend_root / ".env"
if _env_file.exists():
    load_dotenv(_env_file)
    print(f"Loaded .env from {_env_file}")
else:
    load_dotenv()
    print("Loaded .env from current directory")

# Import after env is loaded (gradium may be yanked on PyPI; install with pip install gradium --no-deps if needed)
try:
    import gradium
except ImportError:
    gradium = None  # type: ignore[assignment]
import traceback


def _make_minimal_wav_silence(duration_sec: float = 0.3, sample_rate: int = 16000) -> bytes:
    """Create minimal WAV bytes (silence) for STT test. 16-bit mono PCM."""
    num_samples = int(duration_sec * sample_rate)
    raw = struct.pack(f"<{num_samples}h", *([0] * num_samples))
    # WAV header: 44 bytes
    data_len = len(raw)
    header = (
        b"RIFF"
        + struct.pack("<I", 36 + data_len)
        + b"WAVE"
        + b"fmt "
        + struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16)
        + b"data"
        + struct.pack("<I", data_len)
    )
    return header + raw


async def test_stt(client: "gradium.client.GradiumClient") -> bool:
    """Test Speech-to-Text (used when microphone button is pressed)."""
    print("\n🎤 Testing STT (Speech-to-Text, used by microphone)...")
    try:
        from agent.gradium_client import GradiumVoiceClient
        voice_client = GradiumVoiceClient(api_key=os.getenv("GRADIUM_API_KEY"))
        wav_bytes = _make_minimal_wav_silence(duration_sec=0.3)
        # Yield as single chunk (like frontend sends after recording)
        async def audio_gen():
            yield wav_bytes
        text_parts = []
        async for msg in voice_client.speech_to_text(
            audio_generator=audio_gen(),
            input_format="wav",
            language="en",
        ):
            if msg.get("type") == "text" and msg.get("text"):
                text_parts.append(msg["text"])
        # Silence may return empty; we care that the stream completes without error
        print(f"   STT stream completed. Transcript (may be empty for silence): {repr(' '.join(text_parts))}")
        print("✅ STT succeeded (Gradium ready for microphone)")
        return True
    except Exception as e:
        print(f"❌ STT failed: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False


async def test_key():
    if gradium is None:
        print("❌ Gradium SDK not installed or not the voice SDK.")
        print("   The PyPI package 'gradium' (0.0.1) is a placeholder and does not provide the voice API.")
        print("   Get the real Gradium voice SDK from https://gradium.ai and follow their install instructions")
        print("   (e.g. pip from their repo or direct download). Then add GRADIUM_API_KEY to backend/.env")
        return False

    api_key = os.getenv("GRADIUM_API_KEY")
    if not api_key:
        print("❌ GRADIUM_API_KEY not set. Add it to backend/.env")
        print("   Get a key at https://gradium.ai")
        return False

    print(f"API Key: {api_key[:20]}...")
    print(f"API Key length: {len(api_key)}")
    print(f"API Key format valid: {api_key.startswith('gsk_')}")

    if not api_key.startswith("gsk_"):
        print("❌ API key format invalid - should start with 'gsk_'")
        return False

    try:
        client = gradium.client.GradiumClient(api_key=api_key)
        print("✅ Client created successfully")

        # Test 1: Voice list (REST)
        print("\n📋 Testing voice list (REST API)...")
        try:
            voices = await gradium.voices.get(client)
            print(f"✅ Voice list succeeded! Found {len(voices)} voices")
            if voices:
                print(f"   Example voice: {voices[0].get('name', 'Unknown')}")
        except Exception as e:
            print(f"❌ Voice list failed: {type(e).__name__}: {e}")
            traceback.print_exc()

        # Test 2: TTS (WebSocket)
        print("\n🔊 Testing TTS (WebSocket)...")
        setup = {
            "model_name": "default",
            "voice_id": "YTpq7expH9539ERJ",
            "output_format": "wav",
        }
        try:
            result = await client.tts(setup=setup, text="Hello world")
            print(f"✅ TTS succeeded! Audio data size: {len(result.raw_data)} bytes")
        except Exception as e:
            print(f"❌ TTS failed: {type(e).__name__}: {e}")
            traceback.print_exc()
            print("\n🔍 Possible causes: invalid/expired key, firewall blocking websocket, Gradium down")
            return False

        # Test 3: STT (used by microphone button)
        stt_ok = await test_stt(client)
        if not stt_ok:
            return False

        return True

    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_key())
    print("\n" + "=" * 60)
    if success:
        print("✅ All Gradium tests passed. Microphone will use backend STT.")
    else:
        print("❌ Tests failed. Please:")
        print("   1. Install the real Gradium voice SDK (see https://gradium.ai — PyPI 'gradium' is a placeholder)")
        print("   2. Add GRADIUM_API_KEY to backend/.env (get key at https://gradium.ai)")
        print("   3. Ensure no quotes around the key in .env")
        print("   4. Restart backend so voice endpoints are enabled")
    print("=" * 60)
    exit(0 if success else 1)
