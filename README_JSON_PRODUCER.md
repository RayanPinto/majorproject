# 🚀 Real-time JSON Producer System

## Overview

This system replaces the old `simulate json` and `simulate event` commands with a real-time JSON ingestion system that continuously processes behavioral data from a producer.

## How It Works

### 1. **Main System (main.py)**

- **Command**: `start json producer` - Starts the JSON receiver
- **Command**: `stop json producer` - Stops the JSON receiver
- The system automatically processes incoming JSON data in real-time

### 2. **JSON Producer (json_producer.py)**

- Runs in a **separate terminal**
- Generates unique behavioral JSON data every 2 seconds
- Connects to the main system via socket (port 12345)
- Each JSON is unique with different behavioral patterns

## Usage Instructions

### Step 1: Start the Main System

```bash
python main.py
```

### Step 2: Start the JSON Receiver

In the main system, type:

```
start json producer
```

### Step 3: Start the Producer (in a new terminal)

```bash
python json_producer.py
```

### Step 4: Monitor Real-time Processing

- The producer will continuously send unique JSON data
- The main system will automatically process each JSON
- You'll see real-time updates of processed data
- Use `stop json producer` to stop receiving data

## JSON Format

The producer generates JSON in the exact format you specified:

- **metadata**: candidate_id, session_id, timestamp, duration
- **video_features**: facial expressions, gaze tracking, head movements, body language
- **audio_features**: speech segments, prosody, pauses, voice tone
- **behavior_profile**: confidence, engagement, stress, emotional valence

## Features

✅ **Real-time Processing**: Continuous JSON ingestion  
✅ **Unique Data**: Each JSON is different  
✅ **Automatic Conversion**: Producer format → System format  
✅ **Socket Communication**: Clean separation between producer and consumer  
✅ **Non-invasive**: No changes to existing system functionality  
✅ **Easy Control**: Start/stop commands integrated into main system

## Technical Details

- **Port**: 12345 (localhost)
- **Protocol**: TCP Socket
- **Data Rate**: 1 JSON every 2 seconds (configurable)
- **Threading**: Non-blocking receiver in background
- **Error Handling**: Graceful connection management

## Troubleshooting

- **Connection Failed**: Make sure to run `start json producer` first
- **Port Already in Use**: The system will automatically handle this
- **JSON Processing Errors**: Check the console for detailed error messages

## Benefits Over Old System

- **Real-time**: Continuous data flow instead of manual commands
- **Scalable**: Easy to add more producers or change data rates
- **Testable**: Perfect for testing system performance with continuous data
- **Realistic**: Simulates actual production environment
