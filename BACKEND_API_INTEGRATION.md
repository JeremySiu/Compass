# Backend API Integration Guide

## Overview
This guide explains how to integrate your frontend with the backend API that includes Gemini AI chat and Gradium voice services (TTS and STT).

## Base URL
```
http://localhost:8000
```

## Authentication
Currently no authentication required. Ensure these environment variables are set in backend `.env`:
- `GEMINI_API_KEY` - Your Google Gemini AI API key
- `GRADIUM_API_KEY` - Your Gradium voice services API key

---

## Health Check

### `GET /health`
Check if backend services are initialized.

**Response:**
```json
{
  "status": "healthy",
  "agent_initialized": true,
  "gradium_initialized": true
}
```

---

## Chat Endpoints

### `POST /api/chat/stream`
Stream chat responses with real-time updates using Server-Sent Events (SSE).

**Request Body:**
```json
{
  "message": "What are the top service categories?",
  "mode": "auto"  // Options: "auto", "deep_analysis", "chat"
}
```

**Mode Options:**
- `"auto"` - Automatically chooses between deep_analysis and chat based on keyword detection
- `"deep_analysis"` - Full agent analysis with data retrieval and visualization navigation
- `"chat"` - Simple conversational response without data analysis

**Response Stream (SSE):**
```javascript
// Event stream format
data: {"type": "start", "content": "Processing your question..."}

data: {"type": "thought", "content": "🤔 Analyzing your question..."}

data: {"type": "plan", "content": "Selected data products:", "data": {"plan": [...]}}

data: {"type": "navigation", "content": "Navigating to frequency view", "data": {"url": "/dashboard/analytics/frequency"}}

data: {"type": "answer", "content": "Based on the analysis...", "data": {"rationale": [...], "key_metrics": [...]}}

data: {"type": "complete", "content": "Analysis complete"}
```

**Event Types:**
- `start` - Initial acknowledgment
- `thought` - Agent's thinking process
- `plan` - Data products selected for analysis
- `navigation` - Page navigation instruction with URL
- `answer`/`chat` - Final response
- `error` - Error message
- `complete` - Stream end signal

**Frontend Integration Example:**
```typescript
const response = await fetch('http://localhost:8000/api/chat/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    message: userInput,
    mode: 'auto'
  })
});

const reader = response.body?.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      
      switch(data.type) {
        case 'thought':
          // Display agent thinking
          break;
        case 'navigation':
          // Navigate to data.data.url
          router.push(data.data.url);
          break;
        case 'answer':
        case 'chat':
          // Display final answer
          break;
      }
    }
  }
}
```

---

## Voice Endpoints (Gradium)

### Text-to-Speech (TTS)

#### `POST /api/voice/tts`
Convert text to speech and return complete audio file.

**Request Body:**
```json
{
  "text": "Hello, how can I help you today?",
  "voice_id": "m86j6D7UZpGzHsNu",  // Jack (British) - default
  "output_format": "wav"  // Options: "wav", "pcm", "opus"
}
```

**Available Voices:**
- `"m86j6D7UZpGzHsNu"` - Jack (Pleasant British voice) - **DEFAULT**
- `"YTpq7expH9539ERJ"` - Emma (Pleasant US female voice)

**Response:**
- Content-Type: `audio/wav` (or specified format)
- Binary audio data

**Frontend Integration Example:**
```typescript
const response = await fetch('http://localhost:8000/api/voice/tts', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: messageText,
    voice_id: 'm86j6D7UZpGzHsNu',
    output_format: 'wav'
  })
});

const audioBlob = await response.blob();
const audioUrl = URL.createObjectURL(audioBlob);
const audio = new Audio(audioUrl);
await audio.play();
```

#### `POST /api/voice/tts/stream`
Stream audio chunks as they're generated (for lower latency).

**Request Body:** Same as `/api/voice/tts`

**Response:** Streaming audio chunks

---

### Speech-to-Text (STT)

#### `POST /api/voice/stt/stream`
Convert speech to text with real-time transcription (SSE stream).

**Request Body:**
```json
{
  "audio_chunk": "base64_encoded_wav_audio",
  "is_final": false,  // true when recording is complete
  "input_format": "wav"  // Options: "wav", "pcm", "opus"
}
```

**Input Format Notes:**
- Audio should be base64-encoded
- Supported formats: WAV, PCM, Opus
- **Language is always English** (hardcoded to "en")

**Response Stream (SSE):**
```javascript
data: {"type": "transcript", "text": "hello world", "is_final": false}

data: {"type": "transcript", "text": "how are you", "is_final": true}

data: {"type": "complete"}
```

**Frontend Integration Example:**
```typescript
// 1. Record audio using MediaRecorder
const stream = await navigator.mediaDevices.getUserMedia({ 
  audio: {
    channelCount: 1,
    sampleRate: 24000,
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true
  }
});

const mediaRecorder = new MediaRecorder(stream, {
  mimeType: 'audio/webm;codecs=opus'
});

const audioChunks = [];
mediaRecorder.ondataavailable = (e) => {
  if (e.data.size > 0) audioChunks.push(e.data);
};

mediaRecorder.start(500);

// 2. On stop, convert to WAV and send to backend
mediaRecorder.onstop = async () => {
  const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
  
  // Convert WebM to WAV using Web Audio API
  const arrayBuffer = await audioBlob.arrayBuffer();
  const audioContext = new AudioContext();
  const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
  const wavBlob = audioBufferToWav(audioBuffer); // Helper function
  
  // Convert to base64
  const base64Audio = await blobToBase64(wavBlob);
  
  // Send to backend
  const response = await fetch('http://localhost:8000/api/voice/stt/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      audio_chunk: base64Audio,
      is_final: true,
      input_format: 'wav'
    })
  });
  
  // Read transcription stream
  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  let fullTranscript = '';
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        if (data.type === 'transcript') {
          fullTranscript += (fullTranscript ? ' ' : '') + data.text;
        }
      }
    }
  }
  
  // Use fullTranscript in chat input
  setInput(fullTranscript);
};
```

#### `POST /api/voice/stt`
Non-streaming STT endpoint (simpler but waits for complete transcription).

**Request Body:**
```json
{
  "audio_data": "base64_encoded_audio",
  "input_format": "wav"
}
```

**Response:**
```json
{
  "transcript": "transcribed text here",
  "success": true
}
```

---

## Error Handling

All endpoints return standard HTTP error codes:
- `500` - Server error (check if services are initialized)
- `404` - Endpoint not found

**Error Response Format:**
```json
{
  "detail": "Error message here"
}
```

For streaming endpoints, errors are sent as SSE events:
```javascript
data: {"type": "error", "content": "Error message"}
```

---

## CORS Configuration

Backend allows requests from:
- `http://localhost:3000` (Next.js dev server)

All methods and headers are allowed.

---

## Environment Setup

### Backend `.env` File
```env
GEMINI_API_KEY=your_gemini_api_key_here
GRADIUM_API_KEY=your_gradium_api_key_here
```

### Required Python Packages
```bash
pip install fastapi uvicorn google-generativeai gradium python-dotenv
```

### Starting the Backend
```bash
cd backend
python app/main.py
```

Backend runs on: `http://localhost:8000` with auto-reload enabled.

---

## Best Practices

### Chat Integration
1. **Handle all event types** from the stream gracefully
2. **Navigate automatically** when receiving `navigation` events
3. **Show thinking states** for better UX (display `thought` messages)
4. **Support both modes** (deep_analysis and simple chat)

### Voice Integration
1. **Always use English** - language is hardcoded to "en"
2. **Convert audio to WAV** before sending (most compatible format)
3. **Use Jack voice** for consistent British accent
4. **Handle microphone permissions** appropriately
5. **Show recording indicators** when capturing audio
6. **Clean up audio resources** (stop tracks, revoke object URLs)

### Performance
1. **Use streaming endpoints** for real-time feedback
2. **Buffer audio appropriately** (500ms chunks for recording)
3. **Handle connection issues** gracefully
4. **Display loading states** during processing

---

## Testing Endpoints

### Using cURL

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Chat (non-streaming):**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "mode": "chat"}'
```

**TTS:**
```bash
curl -X POST http://localhost:8000/api/voice/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "voice_id": "m86j6D7UZpGzHsNu"}' \
  --output speech.wav
```

### Using Browser DevTools
Open browser console and test SSE:
```javascript
const eventSource = new EventSource('http://localhost:8000/api/chat/stream');
eventSource.onmessage = (event) => {
  console.log(JSON.parse(event.data));
};
```

---

## Migration Notes

### From Previous Implementation
If migrating from browser-based speech APIs:

1. **Speech Recognition** → Use `/api/voice/stt/stream`
   - More accurate transcription
   - Works in all browsers
   - No browser support issues

2. **Speech Synthesis** → Use `/api/voice/tts`
   - Consistent voice across platforms
   - Better quality audio
   - Controllable voice selection

3. **Chat** → Use streaming endpoint
   - Real-time feedback
   - Navigation automation
   - Richer response types

---

## Support

For issues or questions:
1. Check backend logs for error details
2. Verify `.env` file has valid API keys
3. Ensure backend services initialized (check `/health`)
4. Test endpoints individually before full integration
