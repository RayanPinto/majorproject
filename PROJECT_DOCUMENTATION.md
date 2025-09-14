# ADK Behavioral Analysis System - Project Documentation

## Project Overview

This is an intelligent behavioral analysis system built using Google's Agent Development Kit (ADK) with real-time audio processing capabilities. The system enables natural voice conversations with an AI agent that can analyze behavioral patterns and adapt responses based on user's emotional state, speech characteristics, and communication preferences.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   FastAPI Server │    │  Google Services│
│                 │    │                  │    │                 │
│  ┌───────────┐  │    │  ┌─────────────┐ │    │  ┌───────────┐  │
│  │Frontend UI│◄─┼────┼─►│WebSocket    │ │    │  │Gemini API │  │
│  └───────────┘  │    │  │Handler      │ │    │  └───────────┘  │
│                 │    │  └─────────────┘ │    │                 │
│  ┌───────────┐  │    │         │        │    │  ┌───────────┐  │
│  │Audio      │  │    │  ┌─────────────┐ │    │  │Calendar   │  │
│  │Processing │  │    │  │ADK Runner   │◄┼────┼─►│API        │  │
│  └───────────┘  │    │  └─────────────┘ │    │  └───────────┘  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Core Components

### 1. Backend Server (`app/main.py`)

**Purpose**: FastAPI server handling WebSocket connections and ADK integration

**Key Functions**:
- `start_agent_session()`: Initializes ADK session with Gemini model
- `agent_to_client_messaging()`: Streams responses from agent to client
- `client_to_agent_messaging()`: Processes client messages to agent

**Audio Configuration**:
```python
speech_config = types.SpeechConfig(
    voice_config=types.VoiceConfig(
        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Puck")
    )
)
```

**WebSocket Flow**:
1. Client connects with session ID and audio mode flag
2. Creates ADK Runner with root_agent
3. Establishes bidirectional communication channels
4. Handles real-time audio/text streaming

### 2. AI Agent (`app/jarvis/agent.py`)

**Purpose**: Core AI agent using Gemini 2.0 Flash Live model

**Configuration**:
- Model: `gemini-2.0-flash-live-001`
- Tools: Calendar operations (create, list, edit, delete events)
- Instructions: Detailed prompts for calendar management

**Key Features**:
- Proactive calendar assistance
- Natural language date/time parsing
- Contextual event management
- Concise response formatting

### 3. Calendar Tools (`app/jarvis/tools/`)

#### Calendar Utilities (`calendar_utils.py`)
- **OAuth2 Authentication**: Manages Google Calendar API access
- **Token Management**: Stores credentials in `~/.credentials/calendar_token.json`
- **Date Parsing**: Supports multiple datetime formats
- **Service Creation**: Builds authenticated Calendar API client

#### Event Operations:
- **`list_events.py`**: Retrieves calendar events with date filtering
- **`create_event.py`**: Creates new calendar events with timezone handling
- **`edit_event.py`**: Modifies existing events (title, time, etc.)
- **`delete_event.py`**: Removes events with confirmation requirement

### 4. Frontend Interface (`app/static/`)

#### HTML Interface (`index.html`)
- Modern, responsive design with Google Material colors
- Chat-style message display
- Audio controls and status indicators
- Real-time typing indicators

#### JavaScript Client (`js/app.js`)
**WebSocket Management**:
- Automatic reconnection on disconnect
- Session ID generation
- Message routing and display

**Audio Integration**:
- Seamless audio/text mode switching
- Real-time audio streaming
- Visual feedback for recording state

#### Audio Processing

##### Audio Recorder (`js/audio-recorder.js`)
```javascript
// Creates 16kHz AudioContext for recording
const audioRecorderContext = new AudioContext({ sampleRate: 16000 });

// Converts Float32 to 16-bit PCM
function convertFloat32ToPCM(inputData) {
    const pcm16 = new Int16Array(inputData.length);
    for (let i = 0; i < inputData.length; i++) {
        pcm16[i] = inputData[i] * 0x7fff;
    }
    return pcm16.buffer;
}
```

##### Audio Player (`js/audio-player.js`)
```javascript
// Creates 24kHz AudioContext for playback
const audioContext = new AudioContext({ sampleRate: 24000 });
```

##### PCM Processors
- **`pcm-recorder-processor.js`**: Captures microphone input as Float32 arrays
- **`pcm-player-processor.js`**: Plays received audio with ring buffer management

## Audio Processing Pipeline

### Input Pipeline (Speech to Text)
```
Microphone Input
       ↓
   Float32 Audio (16kHz)
       ↓
   PCM Recorder Processor
       ↓
   16-bit PCM Conversion
       ↓
   Base64 Encoding
       ↓
   WebSocket Transmission
       ↓
   ADK Processing
       ↓
   Gemini Speech Recognition
       ↓
   Text Processing
```

### Output Pipeline (Text to Speech)
```
Agent Text Response
       ↓
   Gemini TTS Processing
       ↓
   PCM Audio Generation
       ↓
   Base64 Encoding
       ↓
   WebSocket Transmission
       ↓
   Base64 Decoding
       ↓
   PCM Player Processor
       ↓
   Float32 Conversion (24kHz)
       ↓
   Speaker Output
```

## Data Flow Diagrams

### WebSocket Communication Flow
```
Client                    Server                    ADK/Gemini
  │                         │                          │
  ├─ Connect WebSocket ────►│                          │
  │                         ├─ Create ADK Session ───►│
  │                         │                          │
  ├─ Send Audio/Text ──────►│                          │
  │                         ├─ Forward to Agent ─────►│
  │                         │                          │
  │                         │◄─ Stream Response ──────┤
  │◄─ Receive Response ─────┤                          │
  │                         │                          │
```

### Calendar Integration Flow
```
Voice Input: "Schedule meeting tomorrow at 2 PM"
       ↓
   Speech Recognition
       ↓
   Intent Analysis (Gemini)
       ↓
   Tool Selection: create_event
       ↓
   Parameter Extraction:
   - summary: "meeting"
   - start_time: "2024-XX-XX 14:00"
   - end_time: "2024-XX-XX 15:00"
       ↓
   Google Calendar API Call
       ↓
   Event Creation
       ↓
   Success Response
       ↓
   Text-to-Speech
       ↓
   Audio Response: "Meeting scheduled for tomorrow at 2 PM"
```

## Configuration Files

### Environment Variables (`.env`)
```
GOOGLE_API_KEY=your_gemini_api_key_here
```

### OAuth Credentials (`credentials.json`)
```json
{
  "installed": {
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token"
  }
}
```

### Dependencies (`requirements.txt`)
Key packages:
- `google-adk==0.5.0`: Google Agent Development Kit
- `google-genai==1.14.0`: Gemini API client
- `fastapi==0.115.12`: Web framework
- `google-api-python-client>=2.169.0`: Calendar API
- `uvicorn==0.34.2`: ASGI server

## Authentication Flow

### Initial Setup
1. Run `setup_calendar_auth.py`
2. OAuth2 flow opens browser
3. User grants calendar permissions
4. Token saved to `~/.credentials/calendar_token.json`

### Runtime Authentication
1. Load saved token from file
2. Check token validity
3. Refresh if expired
4. Create authenticated Calendar service

## Error Handling

### WebSocket Errors
- Automatic reconnection with 5-second delay
- Connection status indicators
- Graceful degradation for network issues

### Audio Errors
- Microphone permission handling
- Audio context state management
- Buffer overflow protection

### Calendar API Errors
- Authentication failure recovery
- Rate limit handling
- Event not found scenarios

## Performance Optimizations

### Audio Processing
- Ring buffer for smooth playback
- Efficient PCM conversion
- Minimal latency audio pipeline

### WebSocket Communication
- JSON message streaming
- Base64 encoding for binary data
- Connection pooling and reuse

### Calendar Operations
- Batch API requests where possible
- Intelligent caching of calendar data
- Timezone-aware event handling

## Security Considerations

### Authentication
- OAuth2 with minimal required scopes
- Secure token storage in user directory
- API key protection via environment variables

### Data Privacy
- No audio data persistence
- Local credential storage
- Encrypted API communications

## Deployment Instructions

### Local Development
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env with your API keys

# 3. Configure Calendar access
python setup_calendar_auth.py

# 4. Start server
cd app
uvicorn main:app --reload
```

### Production Considerations
- Use HTTPS for WebSocket connections
- Implement proper logging
- Set up monitoring for API quotas
- Configure firewall rules

## Troubleshooting Guide

### Common Issues
1. **Audio not working**: Check microphone permissions
2. **Calendar errors**: Re-run OAuth setup
3. **Connection issues**: Verify API keys
4. **Performance problems**: Check network latency

### Debug Tools
- Browser developer console for frontend issues
- FastAPI logs for backend problems
- Google Cloud Console for API monitoring

## Future Enhancements

### Potential Features
- Multi-language support
- Voice activity detection
- Calendar conflict resolution
- Meeting transcription
- Integration with other Google services

### Technical Improvements
- WebRTC for better audio quality
- Caching layer for faster responses
- Load balancing for multiple users
- Advanced error recovery mechanisms
