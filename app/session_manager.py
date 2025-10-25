"""
Session Management System for Voice-Based AI Dating Show
Stores session data as JSON files on disk, no database required.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import csv

# Directory for storing session JSON files
SESSIONS_DIR = "sessions"
LOG_FILE = os.path.join(SESSIONS_DIR, "log.csv")

# In-memory cache for quick access
_session_cache: Dict[str, Dict] = {}


def _ensure_sessions_dir():
    """Create sessions directory if it doesn't exist"""
    if not os.path.exists(SESSIONS_DIR):
        os.makedirs(SESSIONS_DIR)


def _get_session_path(session_id: str) -> str:
    """Get file path for a session"""
    return os.path.join(SESSIONS_DIR, f"{session_id}.json")


def _timestamp() -> str:
    """Get current ISO timestamp"""
    return datetime.utcnow().isoformat() + "Z"


# ========== LIFECYCLE FUNCTIONS ==========

def create_session(user_id: str, session_id: Optional[str] = None) -> Dict:
    """
    Create a new session JSON file
    
    Args:
        user_id: First participant's ID
        session_id: Optional custom session ID, otherwise auto-generated
        
    Returns:
        Session data dictionary
    """
    _ensure_sessions_dir()
    
    if session_id is None:
        # Auto-generate session ID using timestamp
        session_id = f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    session_data = {
        "session_id": session_id,
        "participants": {
            "A": user_id,
            "B": None
        },
        "agent": {
            "id": "janitor_01",
            "spiciness": 2
        },
        "phase": "waiting",
        "transcript": [],
        "summary": "",
        "status": "waiting",  # waiting, active, ended
        "created_at": _timestamp(),
        "last_activity": _timestamp()
    }
    
    save_session(session_id, session_data)
    _log_to_csv(session_id, "SYSTEM", f"Session created by {user_id}")
    
    return session_data


def join_session(session_id: str, user_id: str) -> Dict:
    """
    Add participant B to an existing session
    
    Args:
        session_id: Session to join
        user_id: User ID of participant B
        
    Returns:
        Updated session data
    """
    session = load_session(session_id)
    
    if session is None:
        raise ValueError(f"Session {session_id} not found")
    
    if session["participants"]["B"] is not None:
        raise ValueError(f"Session {session_id} is already full")
    
    session["participants"]["B"] = user_id
    session["status"] = "active"
    session["phase"] = "icebreaker"
    session["last_activity"] = _timestamp()
    
    save_session(session_id, session)
    _log_to_csv(session_id, "SYSTEM", f"User {user_id} joined session")
    
    return session


def end_session(session_id: str) -> Dict:
    """
    Mark session as ended
    
    Args:
        session_id: Session to end
        
    Returns:
        Updated session data
    """
    session = load_session(session_id)
    
    if session is None:
        raise ValueError(f"Session {session_id} not found")
    
    session["status"] = "ended"
    session["ended_at"] = _timestamp()
    session["last_activity"] = _timestamp()
    
    save_session(session_id, session)
    _log_to_csv(session_id, "SYSTEM", "Session ended")
    
    # Remove from cache but keep file for archive
    if session_id in _session_cache:
        del _session_cache[session_id]
    
    return session


# ========== UPDATE FUNCTIONS ==========

def update_session_state(session_id: str, field: str, value: Any) -> Dict:
    """
    Update a specific field in session data
    
    Args:
        session_id: Session to update
        field: Field name to update
        value: New value
        
    Returns:
        Updated session data
    """
    session = load_session(session_id)
    
    if session is None:
        raise ValueError(f"Session {session_id} not found")
    
    session[field] = value
    session["last_activity"] = _timestamp()
    
    save_session(session_id, session)
    
    return session


def append_transcript(session_id: str, speaker: str, text: str) -> Dict:
    """
    Add a new line to the transcript
    
    Args:
        session_id: Session to update
        speaker: Speaker identifier ("A", "B", or "AGENT")
        text: Text content
        
    Returns:
        Updated session data
    """
    session = load_session(session_id)
    
    if session is None:
        raise ValueError(f"Session {session_id} not found")
    
    transcript_entry = {
        "speaker": speaker,
        "text": text,
        "timestamp": _timestamp()
    }
    
    session["transcript"].append(transcript_entry)
    session["last_activity"] = _timestamp()
    
    save_session(session_id, session)
    _log_to_csv(session_id, speaker, text)
    
    return session


def update_summary(session_id: str, summary: str) -> Dict:
    """
    Update the session summary
    
    Args:
        session_id: Session to update
        summary: New summary text
        
    Returns:
        Updated session data
    """
    return update_session_state(session_id, "summary", summary)


def update_phase(session_id: str, phase: str) -> Dict:
    """
    Update the conversation phase
    
    Args:
        session_id: Session to update
        phase: New phase (e.g., "icebreaker", "deep_dive", "decision")
        
    Returns:
        Updated session data
    """
    return update_session_state(session_id, "phase", phase)


# ========== UTILITY FUNCTIONS ==========

def load_session(session_id: str) -> Optional[Dict]:
    """
    Load session data from JSON file or cache
    
    Args:
        session_id: Session ID to load
        
    Returns:
        Session data or None if not found
    """
    # Check cache first
    if session_id in _session_cache:
        return _session_cache[session_id]
    
    # Load from file
    session_path = _get_session_path(session_id)
    if not os.path.exists(session_path):
        return None
    
    try:
        with open(session_path, 'r') as f:
            session_data = json.load(f)
            _session_cache[session_id] = session_data
            return session_data
    except Exception as e:
        print(f"Error loading session {session_id}: {e}")
        return None


def save_session(session_id: str, data: Dict):
    """
    Save session data to JSON file and cache
    
    Args:
        session_id: Session ID
        data: Session data dictionary
    """
    _ensure_sessions_dir()
    
    session_path = _get_session_path(session_id)
    
    try:
        with open(session_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Update cache
        _session_cache[session_id] = data
    except Exception as e:
        print(f"Error saving session {session_id}: {e}")
        raise


def list_active_sessions() -> List[Dict]:
    """
    Get all active sessions
    
    Returns:
        List of active session data
    """
    _ensure_sessions_dir()
    
    active_sessions = []
    
    for filename in os.listdir(SESSIONS_DIR):
        if filename.endswith('.json'):
            session_id = filename[:-5]  # Remove .json extension
            session = load_session(session_id)
            
            if session and session.get("status") in ["waiting", "active"]:
                active_sessions.append(session)
    
    return active_sessions


def list_all_sessions() -> List[Dict]:
    """
    Get all sessions (including ended ones)
    
    Returns:
        List of all session data
    """
    _ensure_sessions_dir()
    
    all_sessions = []
    
    for filename in os.listdir(SESSIONS_DIR):
        if filename.endswith('.json'):
            session_id = filename[:-5]
            session = load_session(session_id)
            
            if session:
                all_sessions.append(session)
    
    return all_sessions


def get_waiting_session() -> Optional[Dict]:
    """
    Find a session waiting for participant B
    
    Returns:
        Session data or None
    """
    for session in list_active_sessions():
        if session.get("status") == "waiting" and session["participants"]["B"] is None:
            return session
    return None


def cleanup_idle_sessions(timeout_minutes: int = 30):
    """
    Close sessions that have been idle for too long
    
    Args:
        timeout_minutes: Idle timeout in minutes
    """
    now = datetime.utcnow()
    timeout_delta = timedelta(minutes=timeout_minutes)
    
    for session in list_active_sessions():
        last_activity = datetime.fromisoformat(session["last_activity"].replace("Z", ""))
        
        if now - last_activity > timeout_delta:
            print(f"Cleaning up idle session: {session['session_id']}")
            end_session(session["session_id"])


# ========== CSV LOGGING (OPTIONAL) ==========

def _log_to_csv(session_id: str, speaker: str, text: str):
    """
    Append an entry to the CSV log
    
    Args:
        session_id: Session ID
        speaker: Speaker identifier
        text: Text content
    """
    _ensure_sessions_dir()
    
    # Create CSV with headers if it doesn't exist
    file_exists = os.path.exists(LOG_FILE)
    
    try:
        with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if not file_exists:
                writer.writerow(['timestamp', 'session_id', 'speaker', 'text'])
            
            writer.writerow([_timestamp(), session_id, speaker, text])
    except Exception as e:
        print(f"Error writing to CSV log: {e}")


def get_session_transcript(session_id: str) -> List[Dict]:
    """
    Get full transcript for a session
    
    Args:
        session_id: Session ID
        
    Returns:
        List of transcript entries
    """
    session = load_session(session_id)
    if session:
        return session.get("transcript", [])
    return []


def get_session_stats() -> Dict:
    """
    Get statistics about all sessions
    
    Returns:
        Dictionary with stats
    """
    all_sessions = list_all_sessions()
    active = [s for s in all_sessions if s["status"] in ["waiting", "active"]]
    ended = [s for s in all_sessions if s["status"] == "ended"]
    
    return {
        "total_sessions": len(all_sessions),
        "active_sessions": len(active),
        "ended_sessions": len(ended),
        "waiting_sessions": len([s for s in active if s["status"] == "waiting"])
    }

