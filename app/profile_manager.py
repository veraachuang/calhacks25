"""
Profile Management System for AI Dating Show
Base profiles stored on disk, session profiles are temporary copies
"""

import json
import os
from typing import Dict, Optional, Any

# Directory for storing profile JSON files
PROFILES_DIR = "profiles"

# Default profile templates
DEFAULT_PROFILES = {
    "user_A": {
        "user_id": "user_A",
        "name": "User A",
        "personality_type": "introvert",
        "hobbies": ["reading", "photography"],
        "goal": "find new friends",
        "age": 25,
        "interests": ["technology", "art"]
    },
    "user_B": {
        "user_id": "user_B",
        "name": "User B",
        "personality_type": "extrovert",
        "hobbies": ["hiking", "cooking"],
        "goal": "find romance",
        "age": 27,
        "interests": ["outdoors", "music"]
    }
}


def _ensure_profiles_dir():
    """Create profiles directory if it doesn't exist"""
    if not os.path.exists(PROFILES_DIR):
        os.makedirs(PROFILES_DIR)


def _get_profile_path(user_id: str) -> str:
    """Get file path for a profile"""
    return os.path.join(PROFILES_DIR, f"{user_id}.json")


# ========== INITIALIZATION ==========

def init_profiles():
    """
    Initialize profile system
    Creates /profiles/ directory and default profile files if they don't exist
    """
    _ensure_profiles_dir()
    
    # Create default profiles if they don't exist
    for user_id, default_profile in DEFAULT_PROFILES.items():
        profile_path = _get_profile_path(user_id)
        
        if not os.path.exists(profile_path):
            with open(profile_path, 'w') as f:
                json.dump(default_profile, f, indent=2)
            print(f"Created default profile: {user_id}")


# ========== RETRIEVAL ==========

def load_profile(user_id: str) -> Optional[Dict]:
    """
    Load the base profile from disk (permanent storage)
    
    Args:
        user_id: User ID (e.g., "user_A", "user_B")
        
    Returns:
        Profile data dictionary or None if not found
    """
    profile_path = _get_profile_path(user_id)
    
    if not os.path.exists(profile_path):
        # Try to initialize if profile is missing
        if user_id in DEFAULT_PROFILES:
            init_profiles()
            return load_profile(user_id)
        return None
    
    try:
        with open(profile_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading profile {user_id}: {e}")
        return None


def load_session_profile(session_id: str, user_id: str) -> Optional[Dict]:
    """
    Load the temporary profile from a session (with any in-session edits)
    
    Args:
        session_id: Session ID
        user_id: User ID (socket ID or "user_A"/"user_B")
        
    Returns:
        Profile data or None if not found
    """
    from app import session_manager
    
    session = session_manager.load_session(session_id)
    if not session:
        return None
    
    # Determine role (A or B) from user_id
    role = None
    if session["participants"]["A"] == user_id:
        role = "A"
    elif session["participants"]["B"] == user_id:
        role = "B"
    
    if not role:
        return None
    
    # Get profile from session data
    participant_data = session.get("participant_profiles", {}).get(role)
    if participant_data:
        return participant_data.get("profile")
    
    return None


def get_effective_profile(session_id: str, user_id: str) -> Optional[Dict]:
    """
    Get the effective profile for a user in a session
    Returns session profile if it exists, otherwise base profile
    
    Args:
        session_id: Session ID
        user_id: User ID
        
    Returns:
        Profile data
    """
    # Try session profile first
    session_profile = load_session_profile(session_id, user_id)
    if session_profile:
        return session_profile
    
    # Fall back to base profile
    # Try to map socket ID to user_A/user_B
    from app import session_manager
    session = session_manager.load_session(session_id)
    if session:
        if session["participants"]["A"] == user_id:
            return load_profile("user_A")
        elif session["participants"]["B"] == user_id:
            return load_profile("user_B")
    
    return None


# ========== SESSION PROFILE MANAGEMENT ==========

def attach_profiles_to_session(session_id: str) -> bool:
    """
    Copy base profiles into session as temporary profiles
    Called when a session becomes active
    
    Args:
        session_id: Session ID
        
    Returns:
        True if successful
    """
    from app import session_manager
    
    session = session_manager.load_session(session_id)
    if not session:
        return False
    
    # Load base profiles
    profile_a = load_profile("user_A")
    profile_b = load_profile("user_B")
    
    if not profile_a or not profile_b:
        print(f"Error: Could not load base profiles")
        return False
    
    # Attach profiles to session
    session["participant_profiles"] = {
        "A": {
            "user_id": session["participants"]["A"],
            "profile": profile_a.copy()  # Copy to avoid mutation
        },
        "B": {
            "user_id": session["participants"]["B"],
            "profile": profile_b.copy() if profile_b else None
        }
    }
    
    session_manager.save_session(session_id, session)
    print(f"Attached profiles to session {session_id}")
    return True


def update_session_profile(session_id: str, user_id: str, field: str, value: Any) -> Optional[Dict]:
    """
    Update a field in the temporary session profile
    Does NOT modify the base profile on disk
    
    Args:
        session_id: Session ID
        user_id: User ID (socket ID)
        field: Field name to update (e.g., "hobbies", "personality_type")
        value: New value
        
    Returns:
        Updated profile or None if error
    """
    from app import session_manager
    
    session = session_manager.load_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")
    
    # Determine role (A or B)
    role = None
    if session["participants"]["A"] == user_id:
        role = "A"
    elif session["participants"]["B"] == user_id:
        role = "B"
    else:
        raise ValueError(f"User {user_id} not in session {session_id}")
    
    # Initialize profiles if not present
    if "participant_profiles" not in session:
        attach_profiles_to_session(session_id)
        session = session_manager.load_session(session_id)
    
    # Update the specific field
    if role in session["participant_profiles"]:
        session["participant_profiles"][role]["profile"][field] = value
        session_manager.save_session(session_id, session)
        
        print(f"Updated {role} profile in session {session_id}: {field} = {value}")
        return session["participant_profiles"][role]["profile"]
    
    return None


def update_session_profile_bulk(session_id: str, user_id: str, updates: Dict[str, Any]) -> Optional[Dict]:
    """
    Update multiple fields in the session profile at once
    
    Args:
        session_id: Session ID
        user_id: User ID
        updates: Dictionary of field: value pairs
        
    Returns:
        Updated profile or None if error
    """
    from app import session_manager
    
    session = session_manager.load_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")
    
    # Determine role
    role = None
    if session["participants"]["A"] == user_id:
        role = "A"
    elif session["participants"]["B"] == user_id:
        role = "B"
    else:
        raise ValueError(f"User {user_id} not in session {session_id}")
    
    # Initialize profiles if not present
    if "participant_profiles" not in session:
        attach_profiles_to_session(session_id)
        session = session_manager.load_session(session_id)
    
    # Update multiple fields
    if role in session["participant_profiles"]:
        for field, value in updates.items():
            session["participant_profiles"][role]["profile"][field] = value
        
        session_manager.save_session(session_id, session)
        print(f"Bulk updated {role} profile in session {session_id}")
        return session["participant_profiles"][role]["profile"]
    
    return None


def get_both_profiles(session_id: str) -> Dict[str, Optional[Dict]]:
    """
    Get both participant profiles from a session
    
    Args:
        session_id: Session ID
        
    Returns:
        Dictionary with keys "A" and "B" containing profiles
    """
    from app import session_manager
    
    session = session_manager.load_session(session_id)
    if not session:
        return {"A": None, "B": None}
    
    profiles = session.get("participant_profiles", {})
    
    return {
        "A": profiles.get("A", {}).get("profile"),
        "B": profiles.get("B", {}).get("profile")
    }


# ========== UTILITY ==========

def reset_profile_to_base(session_id: str, user_id: str) -> Optional[Dict]:
    """
    Reset session profile back to base profile from disk
    
    Args:
        session_id: Session ID
        user_id: User ID
        
    Returns:
        Reset profile
    """
    from app import session_manager
    
    session = session_manager.load_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")
    
    # Determine role
    role = None
    base_profile_id = None
    if session["participants"]["A"] == user_id:
        role = "A"
        base_profile_id = "user_A"
    elif session["participants"]["B"] == user_id:
        role = "B"
        base_profile_id = "user_B"
    else:
        raise ValueError(f"User {user_id} not in session {session_id}")
    
    # Load fresh base profile
    base_profile = load_profile(base_profile_id)
    if not base_profile:
        return None
    
    # Replace session profile with base profile
    if "participant_profiles" not in session:
        session["participant_profiles"] = {}
    
    session["participant_profiles"][role] = {
        "user_id": user_id,
        "profile": base_profile.copy()
    }
    
    session_manager.save_session(session_id, session)
    print(f"Reset {role} profile to base in session {session_id}")
    return base_profile


def list_all_profiles() -> Dict[str, Dict]:
    """
    Get all base profiles from disk
    
    Returns:
        Dictionary mapping user_id to profile data
    """
    _ensure_profiles_dir()
    
    profiles = {}
    for filename in os.listdir(PROFILES_DIR):
        if filename.endswith('.json'):
            user_id = filename[:-5]  # Remove .json
            profile = load_profile(user_id)
            if profile:
                profiles[user_id] = profile
    
    return profiles

