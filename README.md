# 🤖 Behavioral Analysis Assistant

A real-time multimodal behavioral analysis framework for interviews that processes video and audio inputs to provide comprehensive candidate analysis.

## 🎯 Features

- **Real-time Behavioral Analysis**: Processes multimodal data (facial expressions, speech patterns, body language)
- **AI-Powered Insights**: Conversational agent provides behavioral predictions and summaries
- **Interactive Dashboard**: Visual behavioral metrics with confidence levels, engagement, and stress indicators
- **Emotional Timeline**: Track emotional changes throughout the interview
- **MongoDB Persistence**: Session-based data storage with timestamp correlation

## 🚀 Quick Start

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   Create a `.env` file with:

   ```
   MONGODB_URI=your_mongodb_connection_string
   APP_NAME=Behavioral Analysis System
   USER_ID=interviewer_user
   SESSION_ID=session_2025_001
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

## 💬 Test Commands

### Data Ingestion

- `simulate json` - Load sample behavioral data from interview
- `simulate event {"metadata": {...}}` - Ingest custom behavioral JSON

### Behavioral Analysis

- `analyze behavior` - Comprehensive behavioral analysis
- `show insights` - Key behavioral insights and observations
- `emotional pattern` - Analyze emotional patterns over time
- `confidence level` - Assess confidence changes
- `stress analysis` - Evaluate stress indicators

### Visual Dashboards

- `show dashboard` - Behavioral analysis dashboard with metrics
- `emotional timeline` - Timeline of emotional changes
- `give me a summary` - Summary of behavioral state

### Interactive Commands

- `exit` or `quit` - End session

## 📊 Behavioral Metrics Tracked

- **Confidence Level**: Candidate's self-assurance indicators
- **Engagement Level**: Attention and involvement metrics
- **Stress Level**: Anxiety and pressure indicators
- **Emotional Valence**: Positive/negative emotional state
- **Facial Expressions**: Real-time emotion detection
- **Speech Patterns**: Voice tone, prosody, and disfluencies
- **Body Language**: Posture, gestures, and fidgeting

## 🏗️ Architecture

```
Multimodal Input (Video/Audio)
        ↓
    Feature Extraction
    (Whisper + DeepFace)
        ↓
   Structured JSON Output
        ↓
   Real-time ADK Ingestion
        ↓
  Behavioral State Updates
        ↓
Conversational Agent Analysis
        ↓
   Behavioral Insights &
   Predictive Summaries
```

## 📁 Project Structure

```
stateful-agent-system/
├── main.py                      # Main behavioral analysis application
├── utils.py                     # UI and behavioral display functions
├── mongodb_session_service.py   # Session persistence layer
├── sample_json_output.json      # Sample behavioral data structure
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
└── manager/
    ├── tools/tools.py          # JSON ingestion tools
    └── sub_agents/
        └── conversational_agent.py  # Behavioral analysis agent
```
