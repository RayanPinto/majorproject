#!/usr/bin/env python3
"""
JSON Producer for Real-time Behavioral Analysis Testing
Generates unique JSON data and sends it to the main system
"""

import json
import time
import socket
import random
from datetime import datetime, timezone

class BehavioralJSONProducer:
    """Produces unique behavioral JSON data"""
    
    def __init__(self, host: str = 'localhost', port: int = 12345):
        self.host = host
        self.port = port
        self.socket = None
        self.is_running = False
        self.json_count = 0
        
    def connect_to_system(self):
        """Connect to the main system"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"✅ Connected to main system at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to main system: {e}")
            print("💡 Make sure to run 'start json producer' in the main system first")
            return False
    
    def generate_unique_json(self) -> dict:
        """Generate a unique behavioral JSON"""
        
        # Generate unique timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Generate unique candidate ID
        candidate_id = f"CAND{random.randint(100000, 999999)}"
        
        # Generate unique session ID
        session_id = f"INT{datetime.now().strftime('%Y-%m-%d')}-{random.randint(1, 999):03d}"
        
        # Generate realistic behavioral values with variations
        confidence_level = round(random.uniform(0.1, 1.0), 2)
        engagement_level = round(random.uniform(0.1, 1.0), 2)
        stress_level = round(random.uniform(0.1, 1.0), 2)
        
        # Emotional valence based on confidence
        if confidence_level > 0.7:
            emotional_valence = "positive"
        elif confidence_level > 0.4:
            emotional_valence = "neutral"
        else:
            emotional_valence = "negative"
        
        # Generate facial expressions
        expressions = ["neutral", "smile", "frown", "raised_eyebrows", "squint", "surprised"]
        facial_expressions = []
        for i in range(random.randint(1, 4)):
            facial_expressions.append({
                "time_sec": round(random.uniform(1.0, 30.0), 1),
                "expression": random.choice(expressions),
                "confidence": round(random.uniform(0.7, 0.95), 2)
            })
        
        # Generate gaze tracking
        directions = ["center", "up_left", "up_right", "down_left", "down_right", "left", "right"]
        gaze_tracking = []
        for i in range(random.randint(1, 3)):
            gaze_tracking.append({
                "time_sec": round(random.uniform(1.0, 30.0), 1),
                "direction": random.choice(directions),
                "confidence": round(random.uniform(0.8, 0.95), 2)
            })
        
        # Generate head movements
        movements = ["nod", "shake", "tilt", "turn"]
        intensities = ["low", "medium", "high"]
        head_movements = []
        for i in range(random.randint(1, 3)):
            head_movements.append({
                "time_sec": round(random.uniform(1.0, 30.0), 1),
                "movement": random.choice(movements),
                "intensity": random.choice(intensities)
            })
        
        # Generate body language
        postures = ["upright", "leaning_forward", "leaning_back", "relaxed", "tense"]
        gestures = ["hand_open", "hand_closed", "pointing", "crossed_arms", "hands_on_table"]
        fidgeting_levels = ["none", "low", "medium", "high"]
        
        gestures_detected = []
        if random.random() > 0.3:  # 70% chance of detecting gestures
            for i in range(random.randint(0, 2)):
                gestures_detected.append({
                    "time_sec": round(random.uniform(1.0, 30.0), 1),
                    "gesture": random.choice(gestures),
                    "confidence": round(random.uniform(0.6, 0.9), 2)
                })
        
        # Generate speech segments
        speech_texts = [
            "I'm very confident about my technical skills",
            "My experience with machine learning is extensive",
            "I've led several successful projects in this domain",
            "I believe in continuous learning and improvement",
            "My background includes various technologies",
            "I'm passionate about solving complex problems",
            "I have strong analytical and problem-solving skills",
            "I work well both independently and in teams"
        ]
        
        speech_segments = []
        current_time = 1.0
        for i in range(random.randint(2, 4)):
            text = random.choice(speech_texts)
            duration = random.uniform(3.0, 8.0)
            speech_segments.append({
                "start_sec": round(current_time, 1),
                "end_sec": round(current_time + duration, 1),
                "text": text
            })
            current_time += duration + random.uniform(0.5, 2.0)
        
        # Generate prosody
        prosody = {
            "average_pitch_hz": round(random.uniform(150.0, 200.0), 1),
            "pitch_variability": round(random.uniform(0.1, 0.4), 2),
            "average_volume_db": round(random.uniform(-15.0, -8.0), 1),
            "speaking_rate_wpm": random.randint(140, 180)
        }
        
        # Generate pauses
        pauses = []
        for i in range(random.randint(1, 3)):
            pauses.append({
                "time_sec": round(random.uniform(5.0, 25.0), 1),
                "duration_sec": round(random.uniform(0.5, 2.0), 1)
            })
        
        # Generate voice tone
        voice_tones = ["confident", "neutral", "nervous", "enthusiastic", "calm"]
        voice_tone = random.choice(voice_tones)
        
        # Generate notable observations
        observations = [
            "High confidence throughout the response",
            "Clear and articulate speech",
            "Positive body language with forward lean",
            "No signs of stress or anxiety",
            "Good eye contact maintained",
            "Engaged and responsive to questions",
            "Professional demeanor",
            "Thoughtful responses with examples"
        ]
        
        # Select random observations
        num_observations = random.randint(2, 4)
        notable_observations = random.sample(observations, num_observations)
        
        # Create the JSON structure exactly as specified
        json_data = {
            "metadata": {
                "candidate_id": candidate_id,
                "session_id": session_id,
                "timestamp": timestamp,
                "duration_sec": random.randint(30, 120)
            },
            "video_features": {
                "frame_rate": random.randint(25, 30),
                "facial_expressions": facial_expressions,
                "gaze_tracking": gaze_tracking,
                "head_movements": head_movements,
                "body_language": {
                    "gestures_detected": gestures_detected,
                    "posture": random.choice(postures),
                    "fidgeting_level": random.choice(fidgeting_levels)
                }
            },
            "audio_features": {
                "speech_segments": speech_segments,
                "prosody": prosody,
                "pauses": pauses,
                "voice_tone": voice_tone,
                "disfluencies": []
            },
            "behavior_profile": {
                "confidence_level": confidence_level,
                "engagement_level": engagement_level,
                "stress_level": stress_level,
                "emotional_valence": emotional_valence,
                "notable_observations": notable_observations
            }
        }
        
        return json_data
    
    def start_producing(self, interval_seconds: float = 2.0):
        """Start producing JSON data"""
        
        if not self.connect_to_system():
            return
        
        print(f"🚀 Starting JSON production every {interval_seconds} seconds")
        print("📊 Each JSON will be unique with different behavioral patterns")
        print("⏹️ Press Ctrl+C to stop\n")
        
        self.is_running = True
        
        try:
            while self.is_running:
                # Generate unique JSON
                json_data = self.generate_unique_json()
                self.json_count += 1
                
                # Convert to string and send
                json_str = json.dumps(json_data, indent=2)
                
                try:
                    self.socket.send(json_str.encode('utf-8'))
                    print(f"📤 Sent JSON #{self.json_count}")
                    print(f"   Candidate: {json_data['metadata']['candidate_id']}")
                    print(f"   Confidence: {json_data['behavior_profile']['confidence_level']}")
                    print(f"   Engagement: {json_data['behavior_profile']['engagement_level']}")
                    print(f"   Stress: {json_data['behavior_profile']['stress_level']}")
                    print(f"   Emotional: {json_data['behavior_profile']['emotional_valence']}")
                    print()
                    
                except Exception as e:
                    print(f"❌ Failed to send JSON #{self.json_count}: {e}")
                    break
                
                # Wait for next interval
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping JSON production...")
        except Exception as e:
            print(f"❌ Error during production: {e}")
        finally:
            self.stop_producing()
    
    def stop_producing(self):
        """Stop producing JSON data"""
        self.is_running = False
        if self.socket:
            self.socket.close()
        print("✅ JSON producer stopped")


def main():
    """Main function"""
    
    print("🚀 Behavioral JSON Producer")
    print("=" * 40)
    print("Generates unique behavioral data for testing")
    print("=" * 40)
    
    producer = BehavioralJSONProducer()
    
    try:
        # Start producing JSON every 2 seconds
        producer.start_producing(interval_seconds=2.0)
        
    except KeyboardInterrupt:
        print("\nStopping producer...")
    finally:
        producer.stop_producing()


if __name__ == "__main__":
    main()
