# Backend Changes Summary - Gemini AI & Gradium Voice Integration

## What Changed

This branch adds comprehensive AI chat and voice capabilities to the CRM Analytics backend using:
- **Gemini AI** for intelligent data analysis and conversational responses
- **Gradium** for professional text-to-speech and speech-to-text services

## New Backend Features

### 1. AI-Powered Chat with Gemini
- **Two-stage analysis**: Planning → Data retrieval → Answer generation
- **Dual modes**: Simple chat vs. Deep data analysis
- **Automatic navigation**: Agent suggests relevant dashboard pages
- **Streaming responses**: Real-time SSE updates

### 2. Voice Services with Gradium
- **Text-to-Speech (TTS)**: Convert bot responses to natural speech
- **Speech-to-Text (STT)**: Convert user voice input to text
- **Professional voices**: Jack (British) as default
- **Multiple formats**: WAV, PCM, Opus support
- **Streaming support**: Low-latency audio streaming

## New API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Check service initialization |
| `/api/chat/stream` | POST | Stream AI chat responses (SSE) |
| `/api/chat` | POST | Non-streaming chat (for testing) |
| `/api/voice/tts` | POST | Text-to-speech conversion |
| `/api/voice/tts/stream` | POST | Streaming TTS |
| `/api/voice/stt/stream` | POST | Streaming speech-to-text (SSE) |
| `/api/voice/stt` | POST | Non-streaming STT |

## Environment Variables Required

Add to `backend/.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GRADIUM_API_KEY=your_gradium_api_key_here
```

## New Backend Files

### Created
- `backend/agent/gradium_client.py` - Gradium voice services wrapper
- `backend/agent/gemini_client.py` - Gemini AI integration
- `backend/agent/agent.py` - CRM Analytics Agent orchestration

### Modified
- `backend/app/main.py` - Added all voice endpoints and chat streaming

## Frontend Integration Requirements

See [BACKEND_API_INTEGRATION.md](./BACKEND_API_INTEGRATION.md) for detailed integration guide.

### Quick Frontend Checklist

#### For Chat Integration
- [ ] Implement SSE client for `/api/chat/stream`
- [ ] Handle event types: `thought`, `plan`, `navigation`, `answer`, `error`, `complete`
- [ ] Navigate automatically when receiving `navigation` events
- [ ] Support both `chat` and `deep_analysis` modes
- [ ] Show thinking/loading states

#### For Voice Integration (TTS)
- [ ] POST to `/api/voice/tts` with text and voice_id
- [ ] Handle binary audio response (WAV format)
- [ ] Play audio using HTML5 Audio API
- [ ] Show speaking indicator during playback
- [ ] Use voice_id: `m86j6D7UZpGzHsNu` (Jack - British voice)

#### For Voice Integration (STT)
- [ ] Record audio using MediaRecorder API
- [ ] Convert recorded audio to WAV format
- [ ] Base64 encode audio data
- [ ] POST to `/api/voice/stt/stream` with encoded audio
- [ ] Read SSE stream for transcription results
- [ ] Display transcribed text in input field
- [ ] Show recording indicator during capture

## Key Integration Points

### 1. Chat Message Flow
```
User Input → POST /api/chat/stream → SSE Stream → Handle Events → Display
```

### 2. Voice Output Flow
```
Bot Response Text → POST /api/voice/tts → Audio Blob → Play → Animate
```

### 3. Voice Input Flow
```
Mic Button → Record Audio → Convert to WAV → Base64 Encode → 
POST /api/voice/stt/stream → Read Transcript → Display in Input
```

## Language Settings

**Important**: All speech-to-text transcription is hardcoded to **English** (`language="en"`) in both:
- `/api/voice/stt/stream` endpoint
- `/api/voice/stt` endpoint
- `gradium_client.speech_to_text()` method

This ensures consistent English output regardless of input language.

## Voice Configuration

**Default Voice**: Jack (ID: `m86j6D7UZpGzHsNu`)
- Pleasant British male voice
- Professional and clear
- Works well for technical content

**Alternative Voice**: Emma (ID: `YTpq7expH9539ERJ`)
- Pleasant US female voice
- Can be used by passing different `voice_id`

## Example Usage

### Chat with AI Agent
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the top service categories?", "mode": "deep_analysis"}'
```

### Text-to-Speech
```bash
curl -X POST http://localhost:8000/api/voice/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, I am Compass CRM Assistant", "voice_id": "m86j6D7UZpGzHsNu"}' \
  --output response.wav
```

## Testing the Backend

### 1. Start Backend Server
```bash
cd backend
python app/main.py
```

### 2. Check Health
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "agent_initialized": true,
  "gradium_initialized": true
}
```

### 3. Test Chat Endpoint
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "mode": "chat"}'
```

### 4. Test Voice Endpoints
See [BACKEND_API_INTEGRATION.md](./BACKEND_API_INTEGRATION.md) for detailed examples.

## Dependencies Added

### Python Packages
```
google-generativeai  # Gemini AI SDK
gradium              # Voice services SDK
```

Install with:
```bash
pip install google-generativeai gradium
```

## Architecture Overview

```
Frontend
   ↓ HTTP/SSE
Backend (FastAPI)
   ├─→ Gemini AI (Chat & Analysis)
   ├─→ Gradium (TTS & STT)
   └─→ CRM Data Loader
```

### Request Flow: Chat with Analysis
1. User asks question via frontend
2. Backend receives POST to `/api/chat/stream`
3. Agent stages:
   - **Planning**: Gemini determines which data to use
   - **Data Retrieval**: Load relevant CRM data products
   - **Analysis**: Gemini generates insights
4. Stream events back to frontend (SSE)
5. Frontend handles navigation and displays results

### Request Flow: Voice Input
1. User clicks microphone button
2. Frontend records audio via MediaRecorder
3. Audio converted to WAV and base64 encoded
4. POST to `/api/voice/stt/stream`
5. Gradium transcribes audio to text
6. Stream transcription back via SSE
7. Frontend displays text in input field

### Request Flow: Voice Output
1. Bot generates text response
2. Frontend sends text to `/api/voice/tts`
3. Gradium converts text to speech (WAV)
4. Backend returns audio binary
5. Frontend plays audio and animates mascot

## CORS Configuration

Backend allows requests from:
- `http://localhost:3000` (Next.js development server)

Update `backend/app/main.py` if deploying to different domain.

## Production Considerations

### Before Deploying
1. **Secure API Keys**: Use proper secret management
2. **Update CORS**: Restrict to production domain
3. **Rate Limiting**: Add rate limiting for voice endpoints
4. **Audio Caching**: Cache TTS responses for repeated phrases
5. **Error Handling**: Add comprehensive error logging
6. **Authentication**: Add user authentication
7. **Usage Monitoring**: Track API usage for cost management

### Scaling Considerations
- Voice endpoints are resource-intensive
- Consider using a queue for STT processing
- Cache common TTS responses
- Monitor Gradium API usage limits
- Set up Gemini AI quota alerts

## Troubleshooting

### Backend Won't Start
- Check `.env` has valid `GEMINI_API_KEY` and `GRADIUM_API_KEY`
- Verify Python packages installed: `pip list | grep -E "gradium|google-generativeai"`

### Voice Endpoints Return 404
- Ensure backend reloaded after code changes
- Check `/health` endpoint shows `gradium_initialized: true`

### STT Not Transcribing
- Verify audio format is WAV, PCM, or Opus
- Check audio is properly base64 encoded
- Ensure audio sample rate is 24kHz (recommended)

### TTS Audio Not Playing
- Check audio format compatibility with browser
- Verify response Content-Type is `audio/wav`
- Test with cURL to save audio file locally

## Next Steps for Frontend Team

1. **Read** [BACKEND_API_INTEGRATION.md](./BACKEND_API_INTEGRATION.md) for detailed API documentation
2. **Implement** SSE client for chat streaming
3. **Add** voice recording with MediaRecorder API
4. **Integrate** TTS playback for bot responses
5. **Test** each endpoint individually before full integration
6. **Handle** all event types and error cases

## Contact

For questions about backend implementation:
- Review backend code in `backend/app/main.py`
- Check agent implementation in `backend/agent/`
- Test endpoints using provided cURL examples
