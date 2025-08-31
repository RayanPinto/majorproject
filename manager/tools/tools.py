import json
import datetime
from typing import Dict, Any, Optional, List
from google.adk.tools.tool_context import ToolContext

# ===== Deterministic real-time ingestion tools =====

def _now_iso() -> str:
    """UTC ISO timestamp."""
    try:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()
    except Exception:
        return datetime.datetime.utcnow().isoformat()

def _ensure_realtime_state_structures(state: Dict[str, Any]) -> None:
    """Ensure keys required for real-time ingestion exist."""
    if "timeline" not in state:
        state["timeline"] = []
    if "aggregates" not in state:
        state["aggregates"] = {"last_processed_timeline_index": -1}
    if "alerts" not in state:
        state["alerts"] = []
    if "question_windows" not in state:
        state["question_windows"] = {}

def ensure_session_structures(session_service, app_name: str, user_id: str, session_id: str) -> None:
    """Ensure the session has required structures for real-time processing."""
    session = session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
    if not session:
        return
    _ensure_realtime_state_structures(session.state)
    if "last_update" not in session.state:
        session.state["last_update"] = _now_iso()
    session_service.update_session(app_name, user_id, session_id, session.state)

def _get_event_label(event: Dict[str, Any]) -> Optional[str]:
    """Derive a canonical label from features (sentiment first, then face emotion)."""
    try:
        sentiment = (((event.get("features") or {}).get("sentiment") or {}).get("label"))
        if sentiment:
            return str(sentiment).lower()
        face = (((event.get("features") or {}).get("face") or {}).get("emotion"))
        if face:
            return str(face).lower()
    except Exception:
        pass
    return None

def _get_event_score(event: Dict[str, Any]) -> Optional[float]:
    """Get a confidence/score if available."""
    try:
        s_score = (((event.get("features") or {}).get("sentiment") or {}).get("score"))
        if isinstance(s_score, (int, float)):
            return float(s_score)
        f_conf = (((event.get("features") or {}).get("face") or {}).get("confidence"))
        if isinstance(f_conf, (int, float)):
            return float(f_conf)
    except Exception:
        pass
    return None

def ingest_event(session_service, app_name: str, user_id: str, session_id: str, event: Dict[str, Any]) -> bool:
    """
    Ingest a fused multimodal event deterministically.

    - Adds arrival timestamp when JSON reached ADK
    - Ensures idempotency via segment_id (if provided)
    - Updates timeline and last_update
    - Triggers aggregate/alert updates (no textual summaries here)

    Returns True if ingested, False if deduplicated/ignored.
    """
    session = session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
    if not session:
        return False

    _ensure_realtime_state_structures(session.state)

    # Normalize event and set arrival timestamp
    ev: Dict[str, Any] = dict(event) if isinstance(event, dict) else {}
    ev.setdefault("arrival_ts", _now_iso())

    # Require basic timing fields
    t_start = ev.get("t_start")
    t_end = ev.get("t_end")
    if not isinstance(t_start, (int, float)) or not isinstance(t_end, (int, float)):
        # Invalid event, ignore
        return False

    # Idempotency: if segment_id present and already seen, skip
    segment_id = ev.get("segment_id")
    if segment_id:
        if any((e.get("segment_id") == segment_id) for e in session.state["timeline"]):
            return False

    # Append and keep timeline ordered by t_start
    session.state["timeline"].append(ev)
    session.state["timeline"].sort(key=lambda x: (x.get("t_start", 0), x.get("t_end", 0)))

    # Optionally reflect key features into current_state (light merge)
    try:
        label = _get_event_label(ev)
        if label:
            session.state.setdefault("current_state", {})
            session.state["current_state"]["last_label"] = label
        score = _get_event_score(ev)
        if score is not None:
            session.state.setdefault("current_state", {})
            session.state["current_state"]["last_label_score"] = score
    except Exception:
        pass

    now = _now_iso()
    session.state["last_update"] = now
    session.state["last_ingest_at"] = now  # explicit timestamp when JSON reached ADK

    # Update aggregates and alerts
    _update_aggregates_and_alerts(session.state)

    session_service.update_session(app_name, user_id, session_id, session.state)
    return True

def ingest_from_model_output(session_service, app_name: str, user_id: str, session_id: str, payload: Dict[str, Any]) -> bool:
    """
    Convenience wrapper for direct model JSON payloads.
    Accepts already-fused payloads that include t_start/t_end and features.
    Falls back to best-effort extraction if fields are named slightly differently.
    """
    if not isinstance(payload, dict):
        return False
    event = dict(payload)
    # Best-effort normalization
    if "start" in event and "t_start" not in event:
        event["t_start"] = event.get("start")
    if "end" in event and "t_end" not in event:
        event["t_end"] = event.get("end")
    return ingest_event(session_service, app_name, user_id, session_id, event)

def mark_question_window(session_service, app_name: str, user_id: str, session_id: str, question_id: str, t_start: Optional[float] = None, t_end: Optional[float] = None) -> None:
    """Update question window timing in state."""
    session = session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
    if not session:
        return
    _ensure_realtime_state_structures(session.state)
    qw = session.state["question_windows"].get(question_id, {})
    if t_start is not None:
        qw["t_start"] = t_start
    if t_end is not None:
        qw["t_end"] = t_end
    session.state["question_windows"][question_id] = qw
    session.state["last_update"] = _now_iso()
    session_service.update_session(app_name, user_id, session_id, session.state)

def _update_aggregates_and_alerts(state: Dict[str, Any]) -> None:
    """
    Compute lightweight aggregates and detect emotion spans for alerts.

    We track contiguous spans by a canonical label (sentiment/face). When a span closes
    and is at least min_span_seconds, append a structured alert for the conversational
    agent to verbalize later. No text is generated here.
    """
    timeline: List[Dict[str, Any]] = state.get("timeline", [])
    aggregates: Dict[str, Any] = state.get("aggregates", {})
    alerts: List[Dict[str, Any]] = state.get("alerts", [])

    state["aggregates"] = aggregates
    state["alerts"] = alerts

    if not timeline:
        return

    last_idx = aggregates.get("last_processed_timeline_index", -1)
    start_idx = max(-1, last_idx)

    # Initialize active span from aggregates
    active = aggregates.get("active_span") or None
    min_span_seconds = 2.0

    # Process newly appended events
    for i in range(start_idx + 1, len(timeline)):
        ev = timeline[i]
        label = _get_event_label(ev)
        score = _get_event_score(ev)
        t_start = ev.get("t_start", 0.0)
        t_end = ev.get("t_end", t_start)

        if label is None:
            # If we have an active span, consider closing on missing label
            if active:
                # Close span at previous event end
                duration = float(active["t_end"] - active["t_start"]) if active["t_end"] is not None else 0.0
                if duration >= min_span_seconds:
                    alerts.append({
                        "kind": "emotion_span",
                        "label": active["label"],
                        "t_start": active["t_start"],
                        "t_end": active["t_end"],
                        "avg_score": (active["score_sum"] / max(1, active["count"])) if active["count"] else None,
                        "closed_at": _now_iso(),
                    })
                active = None
            aggregates["last_processed_timeline_index"] = i
            continue

        if active and label == active.get("label"):
            # Extend current span
            active["t_end"] = t_end
            if isinstance(score, (int, float)):
                active["score_sum"] += float(score)
                active["count"] += 1
        else:
            # Close previous span if any
            if active:
                duration = float(active["t_end"] - active["t_start"]) if active["t_end"] is not None else 0.0
                if duration >= min_span_seconds:
                    alerts.append({
                        "kind": "emotion_span",
                        "label": active["label"],
                        "t_start": active["t_start"],
                        "t_end": active["t_end"],
                        "avg_score": (active["score_sum"] / max(1, active["count"])) if active["count"] else None,
                        "closed_at": _now_iso(),
                    })
            # Start new span
            active = {
                "label": label,
                "t_start": t_start,
                "t_end": t_end,
                "score_sum": float(score) if isinstance(score, (int, float)) else 0.0,
                "count": 1 if isinstance(score, (int, float)) else 0,
            }

        aggregates["last_processed_timeline_index"] = i

    # Persist active span tracker
    aggregates["active_span"] = active

    # Maintain small alert list size
    if len(alerts) > 2000:
        del alerts[: len(alerts) - 2000]

def log_delegation(delegated_to: str, query: str):
    """
    Log delegation events to track routing decisions.
    
    Args:
        delegated_to: The name of the agent being delegated to
        query: The user query that triggered the delegation
    """
    timestamp = datetime.datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "delegated_to": delegated_to,
        "query": query,
        "event_type": "delegation"
    }
    
    # In a real implementation, this would be logged to a file or database
    # For now, we'll just return the log entry
    return f"Delegated to {delegated_to} at {timestamp} for query: {query}"

def transfer_to_state_agent(tool_context: ToolContext) -> None:
    """Transfer to the state agent for direct state operations."""
    tool_context.actions.transfer_to_agent = "state_agent"

def transfer_to_conversational_agent(tool_context: ToolContext) -> None:
    """Transfer to the conversational agent for natural language processing."""
    tool_context.actions.transfer_to_agent = "conversational_agent"
