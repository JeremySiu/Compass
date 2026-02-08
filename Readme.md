# QHacks2026 - CRM Analytics Platform

A full-stack application for analyzing CRM service request data, featuring automated Python analytics with Supabase backend, Next.js frontend for visualizations, and **AI-powered chat with voice interaction** using Gemini AI and Gradium voice services.

## ✨ New Features

### 🤖 AI Chat Assistant (Gemini)
- Intelligent data analysis and conversational responses
- Two modes: Simple chat and deep data analysis
- Automatic navigation to relevant visualizations
- Real-time streaming responses (SSE)

### 🎙️ Voice Interaction (Gradium)
- **Text-to-Speech**: Professional voice output (Jack - British voice)
- **Speech-to-Text**: Voice input with automatic transcription
- Streaming support for low-latency responses
- Always transcribes in English

## 📚 Documentation

### For Frontend Integration
- **[BACKEND_API_INTEGRATION.md](./BACKEND_API_INTEGRATION.md)** - Complete API reference with examples
- **[BACKEND_CHANGES.md](./BACKEND_CHANGES.md)** - Summary of backend changes and requirements
- **[GEMINI_INTEGRATION_GUIDE.md](./GEMINI_INTEGRATION_GUIDE.md)** - Gemini AI chat integration guide
- **[VOICE_FEATURES.md](./VOICE_FEATURES.md)** - Voice interaction implementation details

### For Backend Development
- **[backend/README.md](./backend/README.md)** - Backend setup and structure
- **[backend/agent/README.md](./backend/agent/README.md)** - Agent implementation details

## 🚀 Quick Start

### Backend API Server

**Prerequisites:**
- Python 3.8+
- Valid `GEMINI_API_KEY` (Google AI Studio)
- Valid `GRADIUM_API_KEY` (Gradium.ai)

**Setup:**
1. Navigate to backend directory:
   ```powershell
   cd backend
   ```

2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

3. Create `.env` file with API keys:
   ```env
   GEMINI_API_KEY=your_gemini_key_here
   GRADIUM_API_KEY=your_gradium_key_here
   ```

4. Start the FastAPI server:
   ```powershell
   python app/main.py
   ```

   Server runs on: `http://localhost:8000`

5. Verify health:
   ```bash
   curl http://localhost:8000/health
   ```

### API Endpoints

The backend provides the following REST API endpoints:

**Chat:**
- `POST /api/chat/stream` - Streaming AI chat with SSE
- `POST /api/chat` - Non-streaming chat (testing)

**Voice (Text-to-Speech):**
- `POST /api/voice/tts` - Convert text to speech (WAV)
- `POST /api/voice/tts/stream` - Streaming TTS

**Voice (Speech-to-Text):**
- `POST /api/voice/stt/stream` - Streaming STT with SSE
- `POST /api/voice/stt` - Non-streaming STT

**Health:**
- `GET /health` - Service health check
- `GET /` - API info

See [BACKEND_API_INTEGRATION.md](./BACKEND_API_INTEGRATION.md) for detailed endpoint documentation and examples.

## Project Structure

```
QHacks2026/
├── backend/                          # Python analytics backend
│   ├── requirements.txt              # Python dependencies
│   ├── .env.example                  # Environment configuration template
│   ├── README.md                     # Backend-specific documentation
│   └── trends/
│       ├── calcs/                    # Analysis calculation scripts
│       │   ├── db_utils.py          # Shared Supabase utilities
│       │   └── *.py                 # Individual analysis scripts
│       └── data/                     # Generated analysis outputs
│
├── frontend/                         # Next.js visualization frontend
│   ├── package.json
│   ├── src/
│   └── ...
│
└── CRMServiceRequests_*.csv         # Legacy local data (for reference)
```

## Data Analytics Scripts

### Running Analysis Scripts

The backend includes Python scripts for generating analytics data:

1. Navigate to backend directory:
   ```powershell
   cd backend
   ```

2. Configure Supabase connection:
   ```powershell
   cp .env.example .env
   ```
   Edit `.env` with your Supabase credentials.

3. Run individual analysis scripts:
   ```powershell
   cd trends/calcs
   python backlog_distribution.py
   python frequency_over_time.py
   # ... etc
   ```

See [backend/README.md](backend/README.md) for detailed documentation.

### Frontend Setup

1. Navigate to frontend directory:
   ```powershell
   cd frontend
   ```

2. Install dependencies:
   ```powershell
   npm install
   ```

3. Run development server:
   ```powershell
   npm run dev
   ```

## Data Source

The application now uses **Supabase as the primary data source**. The local CSV file is kept for reference only. All Python scripts have been updated to:
- Load data directly from Supabase
- Use environment variables for configuration
- Share common database utilities via `db_utils.py`

## Available Analyses

The backend generates the following analytics:

- **Backlog Distribution** - Histogram of unresolved ticket ages
- **Backlog Ranked List** - Unresolved tickets by service type with average age
- **First Call Resolution** - FCR rates by service category
- **Frequency Over Time** - Request volume trends by period
- **Geographic Hot Spots** - Choropleth map data by district
- **Priority Quadrant** - Volume vs. time-to-close scatter plot
- **Seasonality Heatmap** - Monthly patterns by service type
- **Time to Close** - Resolution time distributions
- **Top 10 Rankings** - Multiple top-10 lists (volume, backlog, trending, etc.)

## Technologies

- **Backend**: Python 3.x, Pandas, Supabase
- **Frontend**: Next.js, TypeScript, React
- **Database**: Supabase (PostgreSQL)

## Development Notes

- All Python scripts use relative paths that work with the new `backend/` folder structure
- Output files are saved to `backend/trends/data/`
- The `.env` file is gitignored and must be created from `.env.example`
- Frontend and backend can be developed independently

## Contributing

1. Make sure to test Python scripts from the `backend/trends/calcs/` directory
2. Keep environment variables in `.env` (never commit this file)
3. Follow the existing code structure and naming conventions

