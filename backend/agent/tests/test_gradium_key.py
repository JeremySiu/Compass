"""Test Gradium API key validity."""
import os
import asyncio
from dotenv import load_dotenv
import gradium
import traceback
import aiohttp

async def test_key():
    load_dotenv()
    api_key = os.getenv("GRADIUM_API_KEY")
    
    print(f"API Key: {api_key[:20]}...")
    print(f"API Key length: {len(api_key)}")
    print(f"API Key format valid: {api_key.startswith('gsk_')}")
    
    # Test 1: Check if key format is correct
    if not api_key or not api_key.startswith('gsk_'):
        print("❌ API key format invalid - should start with 'gsk_'")
        return False
    
    try:
        client = gradium.client.GradiumClient(api_key=api_key)
        print("✅ Client created successfully")
        
        # Test 2: Try to get available voices (REST API endpoint)
        print("\n📋 Testing voice list (REST API)...")
        try:
            voices = await gradium.voices.get(client)
            print(f"✅ Voice list succeeded! Found {len(voices)} voices")
            if voices:
                print(f"   Example voice: {voices[0].get('name', 'Unknown')}")
        except Exception as e:
            print(f"❌ Voice list failed: {type(e).__name__}: {e}")
            traceback.print_exc()
        
        # Test 3: Try TTS (uses websocket)
        print("\n🔊 Testing TTS (WebSocket)...")
        setup = {
            "model_name": "default",
            "voice_id": "YTpq7expH9539ERJ",  # Emma
            "output_format": "wav"
        }
        
        try:
            result = await client.tts(setup=setup, text="Hello world")
            print(f"✅ TTS succeeded! Audio data size: {len(result.raw_data)} bytes")
            return True
        except Exception as e:
            print(f"❌ TTS failed: {type(e).__name__}: {e}")
            traceback.print_exc()
            
            # Check if it's a network/websocket issue
            print("\n🔍 Diagnosing issue...")
            print("   Possible causes:")
            print("   1. API key is invalid/expired (regenerate at https://gradium.ai)")
            print("   2. Account may not have API access enabled")
            print("   3. Firewall/proxy blocking websocket connections")
            print("   4. Gradium service might be temporarily down")
            print("   5. API key needs to be activated/verified first")
            
            return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_key())
    print("\n" + "="*60)
    if success:
        print("✅ All tests passed! API key is valid and working.")
    else:
        print("❌ Tests failed. Please:")
        print("   1. Verify your account at https://gradium.ai")
        print("   2. Generate a fresh API key")
        print("   3. Ensure no quotes around the key in .env file")
        print("   4. Check if your network allows websocket connections")
        print("   5. Contact Gradium support: support@gradium.ai")
    print("="*60)
    exit(0 if success else 1)
