# Speech-to-Speech Integration for Behavioral Analysis System

## Overview

The system now supports **real-time speech-to-speech conversations** using Google ADK Live API with Gemini 2.0 Flash Live model. This enables natural, bidirectional voice communication with your behavioral analysis agent while preserving all existing functionality.

## Key Features

- ✅ **Bidirectional Speech**: Speak naturally and hear responses in real-time
- ✅ **Voice Activity Detection (VAD)**: Automatic speech detection and processing
- ✅ **Interruption Support**: Interrupt the agent while it's speaking
- ✅ **Natural Conversations**: Feels like talking to a real person
- ✅ **Non-Disruptive**: All existing text-based functionality remains unchanged
- ✅ **Behavioral Analysis Integration**: Speech conversations integrate with your behavioral data pipeline

## Architecture

```
Text Input ──┐
             ├─► Existing Agent Pipeline ──► Speech Output (existing)
Speech Input ─┘                            └─► Text Output (existing)
             │
             └─► Live API Session ──► Real-time Audio Response
```

## Installation

### 1. Install New Dependencies

```bash
pip install -r requirements.txt
```

New dependencies added:
- `pyaudio` - For microphone input and speaker output
- `numpy` - For audio processing
- `google-generativeai` - For Live API integration

### 2. System Requirements

**Windows:**
```bash
# Install PyAudio (may require Visual C++ Build Tools)
pip install pyaudio
```

**macOS:**
```bash
# Install PortAudio first
brew install portaudio
pip install pyaudio
```

**Linux:**
```bash
# Install PortAudio development files
sudo apt-get install portaudio19-dev
pip install pyaudio
```

### 3. Microphone Permissions

Ensure your system allows microphone access for Python applications.

## Usage Instructions

### Basic Speech Mode

1. **Start the system** (existing functionality unchanged):
   ```bash
   python main.py
   ```

2. **Enable speech mode**:
   ```
   You: enable speech mode
   ```

3. **Check speech status**:
   ```
   You: speech mode status
   ```

4. **Start speech conversation**:
   ```
   You: start conversation
   ```

5. **Speak naturally** - the agent will respond with voice

6. **Stop conversation**:
   ```
   You: stop conversation
   ```
   Or say: "stop conversation"

7. **Disable speech mode** (return to text-only):
   ```
   You: disable speech mode
   ```

### Available Commands

| Command | Description |
|---------|-------------|
| `enable speech mode` | Enable speech-to-speech functionality |
| `disable speech mode` | Disable speech mode, return to text input |
| `speech mode status` | Show current speech system status |
| `start conversation` | Begin real-time speech conversation |
| `stop conversation` | End speech conversation |

### Natural Speech Examples

Once in speech conversation mode, you can say:

- **"How is the candidate's confidence level?"**
- **"What do you see in the behavioral patterns?"**
- **"Can you analyze the stress indicators?"**
- **"Show me the emotional timeline"**
- **"What insights do you have about this interview?"**

## Technical Implementation

### Core Components

1. **`speech_to_speech_engine.py`** - Main speech engine with Live API integration
2. **`speech_conversation_handler.py`** - Conversation management and async handling
3. **Enhanced `main.py`** - Integration with existing system

### Key Features

#### Voice Activity Detection (VAD)
- **Automatic detection** of when you start/stop speaking
- **Energy-based filtering** to ignore background noise
- **Built-in Google ADK VAD** for optimal performance

#### Interruption Handling
- **Real-time interruption** - speak while agent is talking
- **Automatic cancellation** of ongoing responses
- **Seamless conversation flow**

#### Audio Processing
- **16kHz PCM input** from microphone
- **24kHz PCM output** to speakers
- **Real-time streaming** with minimal latency
- **High-quality audio** using Google's speech synthesis

### Integration with Behavioral Analysis

The speech system integrates seamlessly with your existing behavioral analysis pipeline:

- **Speech input** is processed by the same conversational agent
- **Behavioral insights** are available through voice queries
- **Session data** is maintained across speech and text interactions
- **MongoDB persistence** continues to work normally

## Configuration

### Environment Variables

Ensure your `.env` file contains:
```
GOOGLE_API_KEY=your_google_api_key_here
MONGODB_URI=your_mongodb_connection_string
```

### Audio Settings

Default audio configuration (can be customized in `speech_to_speech_engine.py`):
```python
CHUNK_SIZE = 1024        # Audio buffer size
CHANNELS = 1             # Mono audio
RATE = 16000            # 16kHz input sample rate
OUTPUT_RATE = 24000     # 24kHz output sample rate
```

## Troubleshooting

### Common Issues

#### 1. "Audio initialization failed"
**Solution**: Install PyAudio properly for your system
```bash
# Windows
pip install pyaudio

# macOS
brew install portaudio && pip install pyaudio

# Linux
sudo apt-get install portaudio19-dev && pip install pyaudio
```

#### 2. "GenAI client initialization failed"
**Solution**: Check your Google API key
```bash
# Verify API key in .env file
GOOGLE_API_KEY=your_actual_api_key
```

#### 3. "No microphone detected"
**Solution**: 
- Check microphone permissions
- Verify microphone is working in other applications
- Try different audio devices

#### 4. "Speech mode already enabled"
**Solution**: This is normal - speech mode is already active

#### 5. Audio playback issues
**Solution**:
- Check speaker/headphone connections
- Verify system audio settings
- Try different audio output devices

### Debug Commands

```bash
# Check speech system status
You: speech mode status

# Test existing speech output (TTS only)
You: toggle speech
You: test speech

# Debug session state
You: debug state
```

## Performance Considerations

### Optimal Performance
- **Stable internet connection** for Live API
- **Good quality microphone** for clear speech recognition
- **Minimal background noise** for better VAD performance
- **Adequate system resources** for real-time audio processing

### Latency Optimization
- Uses **Google ADK Live API** for minimal latency
- **Real-time streaming** without buffering delays
- **Efficient audio processing** with PyAudio
- **Asynchronous handling** for responsive interactions

## Integration with Existing Features

### Behavioral Analysis Commands (Voice)
All existing commands work through speech:

- **"Start JSON producer"** - Begin behavioral data ingestion
- **"Show dashboard"** - Display behavioral analysis
- **"Analyze behavior"** - Get comprehensive analysis
- **"Show insights"** - View behavioral insights
- **"Emotional timeline"** - See emotional patterns

### Session Management
- **MongoDB persistence** continues to work
- **Session state** maintained across speech/text modes
- **User queries** logged regardless of input method
- **Behavioral data** processing unaffected

## Security & Privacy

### Data Handling
- **No audio storage** - speech processed in real-time only
- **Google ADK encryption** for all API communications
- **Local audio processing** where possible
- **Existing security measures** remain in place

### API Usage
- Uses **Google ADK Live API** with your existing API key
- **Efficient token usage** through streaming
- **Session-based billing** rather than per-request

## Future Enhancements

### Planned Features
- **Custom wake words** for hands-free activation
- **Multi-language support** for international interviews
- **Voice biometrics** integration with behavioral analysis
- **Advanced VAD tuning** for different environments

### Extensibility
The speech system is designed to be:
- **Modular** - easy to extend with new features
- **Configurable** - customizable for different use cases
- **Compatible** - works with future ADK updates
- **Maintainable** - clean separation of concerns

## Support

### Getting Help
1. **Check this documentation** first
2. **Review console output** for error messages
3. **Test with simple commands** to isolate issues
4. **Verify dependencies** are properly installed

### System Status
Use `speech mode status` to check:
- Speech mode enabled/disabled
- Audio system availability
- Live API client status
- Microphone/speaker detection
- Active session status

---

## Quick Start Summary

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start system
python main.py

# 3. Enable speech mode
You: enable speech mode

# 4. Start conversation
You: start conversation

# 5. Speak naturally!
"How is the candidate performing?"

# 6. Stop when done
"stop conversation"
```

**Enjoy natural, real-time conversations with your behavioral analysis agent!** 🎤🤖
