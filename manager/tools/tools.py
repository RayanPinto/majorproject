import json
import datetime
from typing import Dict, Any, Optional, List

# ===== Enhanced Behavioral Analysis Tools =====

def _now_iso() -> str:
    """UTC ISO timestamp."""
    try:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()
    except Exception:
        return datetime.datetime.utcnow().isoformat()

def _ensure_behavioral_state_structures(state: Dict[str, Any]) -> None:
    """Ensure behavioral analysis state structures exist."""
    if "candidate_info" not in state:
        state["candidate_info"] = {}
    if "behavioral_data" not in state:
        state["behavioral_data"] = []
    if "current_behavior" not in state:
        state["current_behavior"] = {}
    if "behavioral_insights" not in state:
        state["behavioral_insights"] = {}
    if "behavior_timeline" not in state:
        state["behavior_timeline"] = []
    if "alerts" not in state:
        state["alerts"] = []
    if "last_update" not in state:
        state["last_update"] = _now_iso()
    if "last_behavior_ingest" not in state:
        state["last_behavior_ingest"] = None

def ensure_session_structures(session_service, app_name: str, user_id: str, session_id: str) -> None:
    """Ensure the session has required structures for behavioral analysis."""
    session = session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
    if not session:
        return
    _ensure_behavioral_state_structures(session.state)
    session_service.update_session(app_name, user_id, session_id, session.state)

def ingest_from_model_output(session_service, app_name: str, user_id: str, session_id: str, payload: Dict[str, Any]) -> bool:
    """
    Enhanced wrapper for behavioral analysis JSON payloads.
    Handles multimodal behavioral data with timestamp correlation.
    """
    if not isinstance(payload, dict):
        return False

    session = session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
    if not session:
        return False

    # Ensure behavioral state structures exist
    _ensure_behavioral_state_structures(session.state)

    # Process behavioral data
    current_behavior = payload.copy()
    metadata = current_behavior.get("metadata", {})

    # Update candidate info if provided
    if metadata.get("candidate_id"):
        session.state.setdefault("candidate_info", {})
        session.state["candidate_info"]["candidate_id"] = metadata["candidate_id"]
        session.state["candidate_info"]["session_id"] = metadata.get("session_id", "")
        session.state["candidate_info"]["interview_start"] = _now_iso()

    # Store current behavioral data
    session.state["current_behavior"] = current_behavior

    # Add to behavioral timeline with timestamp correlation
    behavior_entry = {
        "timestamp": _now_iso(),
        "behavior_data": current_behavior,
        "ingest_time": _now_iso()
    }

    session.state.setdefault("behavioral_data", [])
    session.state["behavioral_data"].append(behavior_entry)

    # Keep only last 50 entries to prevent memory issues
    if len(session.state["behavioral_data"]) > 50:
        session.state["behavioral_data"] = session.state["behavioral_data"][-50:]

    # Update behavioral insights with pattern recognition
    _update_behavioral_insights(session.state)

    # Update timestamps
    now = _now_iso()
    session.state["last_update"] = now
    session.state["last_behavior_ingest"] = now

    # Force pattern recognition update
    print(f"🔄 **Pattern Recognition**: Analyzing {len(session.state['behavioral_data'])} behavioral data points...")
    
    session_service.update_session(app_name, user_id, session_id, session.state)
    return True

def _analyze_trend(values: List[float]) -> str:
    """Analyze trend in a list of values."""
    if len(values) < 2:
        return "insufficient_data"
    
    # Calculate trend using simple linear regression
    n = len(values)
    x_sum = sum(range(n))
    y_sum = sum(values)
    xy_sum = sum(i * val for i, val in enumerate(values))
    x_sq_sum = sum(i * i for i in range(n))
    
    # Calculate slope
    slope = (n * xy_sum - x_sum * y_sum) / (n * x_sq_sum - x_sum * x_sum)
    
    # Determine trend based on slope
    if slope > 0.05:
        return "increasing"
    elif slope < -0.05:
        return "decreasing"
    else:
        return "stable"

def _detect_spikes(values: List[float], threshold: float = 0.15) -> List[Dict[str, Any]]:
    """Detect spikes in a list of values."""
    spikes = []
    if len(values) < 3:
        return spikes
    
    for i in range(1, len(values) - 1):
        current = values[i]
        prev = values[i - 1]
        next_val = values[i + 1]
        
        # Check for spike (current value is significantly higher than neighbors)
        if current > prev + threshold and current > next_val + threshold:
            spikes.append({
                "index": i,
                "value": current,
                "magnitude": current - max(prev, next_val)
            })
        
        # Check for drop (current value is significantly lower than neighbors)
        elif current < prev - threshold and current < next_val - threshold:
            spikes.append({
                "index": i,
                "value": current,
                "magnitude": min(prev, next_val) - current
            })
    
    return spikes

def _generate_behavioral_timeline(behavioral_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate behavioral timeline with pattern annotations."""
    timeline = []
    
    for i, entry in enumerate(behavioral_data[-10:]):  # Last 10 entries
        behavior_data = entry.get("behavior_data", {})
        behavior_profile = behavior_data.get("behavior_profile", {})
        metadata = behavior_data.get("metadata", {})
        
        timeline_entry = {
            "timestamp": entry.get("timestamp", ""),
            "candidate_id": metadata.get("candidate_id", ""),
            "confidence": behavior_profile.get("confidence_level", 0),
            "engagement": behavior_profile.get("engagement_level", 0),
            "stress": behavior_profile.get("stress_level", 0),
            "emotional_valence": behavior_profile.get("emotional_valence", "neutral"),
            "index": i
        }
        
        # Add pattern annotations
        if i > 0:
            prev_entry = timeline[i - 1]
            timeline_entry["confidence_change"] = timeline_entry["confidence"] - prev_entry["confidence"]
            timeline_entry["engagement_change"] = timeline_entry["engagement"] - prev_entry["engagement"]
            timeline_entry["stress_change"] = timeline_entry["stress"] - prev_entry["stress"]
        
        timeline.append(timeline_entry)
    
    return timeline

def _generate_pattern_summary(insights: Dict[str, Any]) -> str:
    """Generate a human-readable pattern summary."""
    summary_parts = []
    
    # Confidence pattern
    if "confidence_pattern" in insights:
        pattern = insights["confidence_pattern"]
        if pattern == "increasing":
            summary_parts.append("Confidence is trending upward")
        elif pattern == "decreasing":
            summary_parts.append("Confidence is declining")
        else:
            summary_parts.append("Confidence remains stable")
    
    # Stress pattern
    if "stress_pattern" in insights:
        pattern = insights["stress_pattern"]
        if pattern == "increasing":
            summary_parts.append("Stress levels are rising")
        elif pattern == "decreasing":
            summary_parts.append("Stress levels are decreasing")
        else:
            summary_parts.append("Stress levels are stable")
    
    # Engagement pattern
    if "engagement_pattern" in insights:
        pattern = insights["engagement_pattern"]
        if pattern == "increasing":
            summary_parts.append("Engagement is improving")
        elif pattern == "decreasing":
            summary_parts.append("Engagement is declining")
        else:
            summary_parts.append("Engagement remains consistent")
    
    # Emotional transitions
    if "emotional_transitions" in insights and insights["emotional_transitions"]:
        transitions = insights["emotional_transitions"]
        if len(transitions) > 0:
            latest = transitions[-1]
            summary_parts.append(f"Recent emotional shift from {latest['from']} to {latest['to']}")
    
    # Spikes detection
    if "confidence_spikes" in insights and insights["confidence_spikes"]:
        summary_parts.append("Notable confidence fluctuations detected")
    
    if "stress_spikes" in insights and insights["stress_spikes"]:
        summary_parts.append("Stress spikes observed")
    
    return "; ".join(summary_parts) if summary_parts else "No significant patterns detected"

def _update_behavioral_insights(state: Dict[str, Any]) -> None:
    """Update behavioral insights with advanced pattern recognition."""
    behavioral_data = state.get("behavioral_data", [])
    if not behavioral_data:
        return

    insights = state.setdefault("behavioral_insights", {})

    # Enhanced Confidence Pattern Analysis
    confidence_values = []
    confidence_timestamps = []
    for entry in behavioral_data[-15:]:  # Last 15 entries for better pattern detection
        behavior_profile = entry.get("behavior_data", {}).get("behavior_profile", {})
        confidence = behavior_profile.get("confidence_level", 0)
        timestamp = entry.get("timestamp", "")
        if confidence > 0:
            confidence_values.append(confidence)
            confidence_timestamps.append(timestamp)

    if confidence_values:
        avg_confidence = sum(confidence_values) / len(confidence_values)
        insights["confidence_trend"] = confidence_values[-5:]  # Last 5 confidence values
        insights["avg_confidence"] = avg_confidence
        insights["confidence_timestamps"] = confidence_timestamps[-5:]

        # Advanced confidence pattern detection
        if len(confidence_values) >= 3:
            recent_trend = _analyze_trend(confidence_values[-3:])
            overall_trend = _analyze_trend(confidence_values)
            
            insights["confidence_pattern"] = recent_trend
            insights["confidence_overall_trend"] = overall_trend
            
            # Detect confidence spikes and drops
            confidence_spikes = _detect_spikes(confidence_values, threshold=0.15)
            insights["confidence_spikes"] = confidence_spikes

    # Enhanced Stress Pattern Analysis
    stress_values = []
    stress_timestamps = []
    for entry in behavioral_data[-15:]:
        behavior_profile = entry.get("behavior_data", {}).get("behavior_profile", {})
        stress = behavior_profile.get("stress_level", 0)
        timestamp = entry.get("timestamp", "")
        if stress > 0:
            stress_values.append(stress)
            stress_timestamps.append(timestamp)

    if stress_values:
        avg_stress = sum(stress_values) / len(stress_values)
        insights["stress_trend"] = stress_values[-5:]
        insights["avg_stress"] = avg_stress
        insights["stress_timestamps"] = stress_timestamps[-5:]

        # Stress pattern detection
        if len(stress_values) >= 3:
            stress_trend = _analyze_trend(stress_values[-3:])
            insights["stress_pattern"] = stress_trend
            
            # Detect stress spikes
            stress_spikes = _detect_spikes(stress_values, threshold=0.2)
            insights["stress_spikes"] = stress_spikes

    # Enhanced Engagement Pattern Analysis
    engagement_values = []
    engagement_timestamps = []
    for entry in behavioral_data[-15:]:
        behavior_profile = entry.get("behavior_data", {}).get("behavior_profile", {})
        engagement = behavior_profile.get("engagement_level", 0)
        timestamp = entry.get("timestamp", "")
        if engagement > 0:
            engagement_values.append(engagement)
            engagement_timestamps.append(timestamp)

    if engagement_values:
        avg_engagement = sum(engagement_values) / len(engagement_values)
        insights["engagement_trend"] = engagement_values[-5:]
        insights["avg_engagement"] = avg_engagement
        insights["engagement_timestamps"] = engagement_timestamps[-5:]

        # Engagement pattern detection
        if len(engagement_values) >= 3:
            engagement_trend = _analyze_trend(engagement_values[-3:])
            insights["engagement_pattern"] = engagement_trend

    # Enhanced Emotional Pattern Analysis
    valence_counts = {"positive": 0, "negative": 0, "neutral": 0}
    emotional_transitions = []
    previous_valence = None
    
    for entry in behavioral_data[-10:]:
        behavior_profile = entry.get("behavior_data", {}).get("behavior_profile", {})
        valence = behavior_profile.get("emotional_valence", "neutral")
        timestamp = entry.get("timestamp", "")
        
        if valence in valence_counts:
            valence_counts[valence] += 1
            
        # Track emotional transitions
        if previous_valence and previous_valence != valence:
            emotional_transitions.append({
                "from": previous_valence,
                "to": valence,
                "timestamp": timestamp
            })
        previous_valence = valence

    most_common_valence = max(valence_counts, key=valence_counts.get)
    insights["dominant_emotion"] = most_common_valence
    insights["emotional_distribution"] = valence_counts
    insights["emotional_transitions"] = emotional_transitions[-3:]  # Last 3 transitions

    # Enhanced emotional pattern description
    if valence_counts["positive"] > valence_counts["negative"] + 2:
        insights["emotional_pattern"] = "predominantly positive"
    elif valence_counts["negative"] > valence_counts["positive"] + 2:
        insights["emotional_pattern"] = "predominantly negative"
    else:
        insights["emotional_pattern"] = "mixed emotional state"

    # Behavioral Timeline Correlation
    insights["behavioral_timeline"] = _generate_behavioral_timeline(behavioral_data)
    
    # Pattern Summary
    insights["pattern_summary"] = _generate_pattern_summary(insights)
