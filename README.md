# CalHacks 2025 - Fish Audio Integration

A Flask-based REST API service that integrates Fish Audio's ASR (Automatic Speech Recognition) and TTS (Text-to-Speech) capabilities. Built for CalHacks 2025.

## Features

- **ASR Endpoint**: Convert audio files to text transcriptions
- **TTS Endpoint**: Convert text to synthesized speech audio
- **JanitorAI Integration**: Example script for accessing JanitorAI completions API
- **Mock Mode**: Development mode with mock responses (no API calls)
- **Health Check**: Monitor service status and configuration

## Project Structure

```
calhacks25/
├── src/
│   ├── fish/                  # Fish Audio integration module
│   │   ├── __init__.py
│   │   ├── client.py          # Session manager & API configuration
│   │   ├── asr.py             # Speech-to-text functionality
│   │   └── tts.py             # Text-to-speech functionality
│   └── app.py                 # Flask REST API server
├── app/                       # Web frontend (optional)
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── templates/
│       └── index.html
├── main.py                    # JanitorAI example script
├── requirements.txt
├── .env                       # Environment configuration
└── README.md
```

## Setup Instructions

### 1. Activate Virtual Environment

```bash
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create or edit `.env` file with your Fish Audio API credentials:

```bash
# Fish Audio API Configuration
FISH_API_KEY=your_api_key_here
FISH_API_BASE=https://api.fish.audio
FISH_MOCK=false  # Set to 'true' for mock mode (no API calls)

# Flask Server Configuration
HOST=0.0.0.0
PORT=5000
FLASK_DEBUG=true
```

### 4. Run the Fish Audio API Server

```bash
cd src
python app.py
```

The API will be available at `http://0.0.0.0:5000`

### 5. Run the JanitorAI Example

```bash
python main.py
```

## API Endpoints

### Health Check
```bash
GET /health
```
Returns service status and configuration info.

### Automatic Speech Recognition (ASR)
```bash
POST /asr
Content-Type: application/octet-stream
# OR
Content-Type: multipart/form-data (with 'audio' field)

# Body: audio file bytes (WAV, MP3, etc.)
```
Returns JSON with transcribed text.

**Example:**
```bash
curl -X POST http://localhost:5000/asr \
  -H "Content-Type: application/octet-stream" \
  --data-binary @audio.wav
```

**Response:**
```json
{
  "transcript": "Hello world",
  "mock": false
}
```

### Text-to-Speech (TTS)
```bash
POST /tts
Content-Type: application/json

{
  "text": "Hello world"
}
```
Returns JSON with base64-encoded audio data.

**Example:**
```bash
curl -X POST http://localhost:5000/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}'
```

**Response:**
```json
{
  "audio": "base64_encoded_audio_data...",
  "format": "wav",
  "mock": false
}
```

## Development

### Mock Mode

Set `FISH_MOCK=true` in `.env` to use mock responses without making real API calls:
- ASR returns: "This is a mock transcription of your audio."
- TTS returns: A simple 440Hz tone (1 second WAV file)

### Real API Integration

The project makes actual HTTP calls to Fish Audio API endpoints:
- ASR: `POST {FISH_API_BASE}/v1/asr`
- TTS: `POST {FISH_API_BASE}/v1/tts`

Authentication uses Bearer token from `FISH_API_KEY`.

## Requirements

- Python 3.8+
- Flask 3.0.0
- python-dotenv 1.0.0
- requests 2.31.0

## JanitorAI Integration

The `main.py` script demonstrates how to access the JanitorAI completions API for CalHacks 2025:

- **Endpoint**: `https://janitorai.com/hackathon/completions`
- **API Key**: `calhacks2047`
- **Model**: OpenAI-compatible chat completions format

## Notes

- The `.env` file contains API keys and should not be committed to version control
- Audio files should be in standard formats (WAV, MP3, etc.)
- TTS responses are returned as base64-encoded audio for easy JSON transmission
- The service runs on `0.0.0.0:5000` by default (configurable via environment variables)
