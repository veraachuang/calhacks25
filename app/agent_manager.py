"""
Agent Manager for Janitor AI Host
Handles LLM calls, prompt building, and response management
No streaming - waits for complete responses
"""
import time
import json
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Agent configuration
JANITOR_AI_URL = "https://janitorai.com/hackathon/completions"
JANITOR_AI_KEY = "calhacks2047"

# Timing and limits
MAX_TURNS_IN_PROMPT = 12  # Maximum conversation turns to include in prompt
SUMMARY_MAX_TOKENS = 250  # Target summary length
REPLY_MAX_CHARS = 600  # Maximum characters in agent reply
CONNECT_TIMEOUT = 3  # Connection timeout in seconds
READ_TIMEOUT = 20  # Read timeout in seconds
MAX_RETRIES = 2  # Number of retry attempts
BACKOFF_MS = [400, 800]  # Backoff delays in milliseconds
AGENT_COOLDOWN_SEC = 6  # Minimum seconds between agent responses


AGENT_RULES = "You are 'Lana,' a dating show host. Be brief (≤3 sentences) in your responses. Don't use emojis."

# Agent personality and rules
AGENT_PERSONALITY_BASIC = """You are "Lana," a friendly, witty dating-show host.
Be brief (≤3 sentences), nudge toward shared interests or fun topics. 
Either change topic if it gets awkward, OR make a joke or comment if it's going well.
Offer a clear next question or prompt, targeting A OR B OR both users.
Keep it natural, warm, and engaging."""

AGENT_PERSONALITY_SPICY = """You are "Lana," a witty dating-show host.
Be brief (≤3 sentences), keep balance between A and B, no need to avoid sensitive topics,
and nudge toward spicy topics. Offer a clear next question or prompt, targeting A OR B OR both users.
Either change topic if it gets awkward, OR make a joke or comment if it's going well.
Keep it natural, warm, and engaging.
Be spicy and fun."""

AGENT_PERSONALITY_SEXY = """nudge toward sexy topics. 
Do not stick to user background for topics.
Offer ONLY ONE clear next question or prompt.
Either change topic if it gets awkward, OR make a joke or comment if it's going well.
Keep it natural.
Be sexy and fun."""

# Track agent state per session
_agent_state = {}  # session_id -> {'busy': bool, 'last_call': timestamp}

# Fallback responses for errors
FALLBACK_RESPONSES = [
    "Let's keep it simple—A, share one hobby you'd love to try with B.",
    "Interesting! B, what do you think about what A just said?",
    "Great conversation! Let's dig deeper—what do you both value most in friendships?",
    "I love the energy here! A, tell us something that makes you unique.",
    "This is going well! B, what's something you're passionate about?"
]


def _get_timestamp() -> str:
    """Get current ISO 8601 timestamp"""
    return datetime.utcnow().isoformat() + "Z"


def _clean_text(text: str) -> str:
    """
    Clean and normalize text
    - Remove duplicate whitespace
    - Strip leading/trailing space
    - Remove empty lines
    """
    if not text:
        return ""
    
    # Collapse whitespace
    text = " ".join(text.split())
    
    # Remove filler patterns (optional)
    fillers = ["um", "uh", "hmm", "like,"]
    for filler in fillers:
        text = text.replace(f" {filler} ", " ")
    
    return text.strip()


def _is_agent_busy(session_id: str) -> bool:
    """Check if agent is currently processing for this session"""
    state = _agent_state.get(session_id)
    if not state:
        return False
    
    # Check if marked busy
    if state.get('busy', False):
        return True
    
    # Check cooldown period
    last_call = state.get('last_call', 0)
    if time.time() - last_call < AGENT_COOLDOWN_SEC:
        return True
    
    return False


def _set_agent_busy(session_id: str, busy: bool):
    """Set agent busy state"""
    if session_id not in _agent_state:
        _agent_state[session_id] = {}
    
    _agent_state[session_id]['busy'] = busy
    if busy:
        _agent_state[session_id]['last_call'] = time.time()


def build_agent_prompt(session_id: str) -> Optional[Dict]:
    """
    Build complete prompt for Janitor AI from session data and profiles
    
    Args:
        session_id: Session ID
        
    Returns:
        Payload dict ready for LLM API, or None if error
    """
    from app import session_manager, profile_manager
    
    try:
        # Load session
        session = session_manager.load_session(session_id)
        if not session:
            print(f"Session {session_id} not found")
            return None

        # Check if session is active (both users have joined)
        if session.get('status') != 'active':
            print(f"Session {session_id} is not active yet (status: {session.get('status')})")
            return None

        # Load profiles
        profiles = profile_manager.get_both_profiles(session_id)
        profile_a = profiles.get('A')
        profile_b = profiles.get('B')

        if not profile_a or not profile_b:
            print(f"Profiles not found for session {session_id} (session may not be fully initialized)")
            return None
        
        # Build profile summary
        profile_summary = f"""Participants:
A: {profile_a.get('name', 'User A')} - {profile_a.get('personality_type', 'unknown')} personality
   Hobbies: {', '.join(profile_a.get('hobbies', []))}
   Goal: {profile_a.get('goal', 'connect with someone')}
   Interests: {', '.join(profile_a.get('interests', []))}

B: {profile_b.get('name', 'User B')} - {profile_b.get('personality_type', 'unknown')} personality
   Hobbies: {', '.join(profile_b.get('hobbies', []))}
   Goal: {profile_b.get('goal', 'connect with someone')}
   Interests: {', '.join(profile_b.get('interests', []))}"""
        
        # Get transcript
        transcript = session.get('transcript', [])
        
        # Get summary if available
        summary = session.get('summary', '')
        summary_text = f"Summary so far: {summary}" if summary else "Conversation just started."
        
        # Get current phase
        phase = session.get('phase', 'icebreaker')
        phase_context = f"Current phase: {phase}"
        
        # Build messages array
        messages = [
            {"role": "system", "content": AGENT_RULES},
            {"role": "system", "content": AGENT_PERSONALITY_SEXY},
            {"role": "system", "content": profile_summary},
            {"role": "system", "content": f"{summary_text}\n{phase_context}"}
        ]
        
        # Add recent conversation turns (last MAX_TURNS_IN_PROMPT)
        recent_transcript = transcript[-MAX_TURNS_IN_PROMPT:] if len(transcript) > MAX_TURNS_IN_PROMPT else transcript
        
        for entry in recent_transcript:
            speaker = entry.get('speaker', 'Unknown')
            text = _clean_text(entry.get('text', ''))
            
            if not text:
                continue
            
            # Skip previous Janitor messages in prompt (to avoid confusion)
            if speaker.lower() in ['janitor', 'agent', 'ai']:
                continue
            
            # Add as user message with speaker label
            messages.append({
                "role": "user",
                "content": f"{speaker}: {text}"
            })
        
        # Build final payload
        payload = {
            "model": "ignored",
            "messages": messages,
            "max_tokens": 200,  # Keep responses concise
            "stream": False  # Explicitly disable streaming
        }
        
        return payload
        
    except Exception as e:
        print(f"Error building agent prompt: {e}")
        return None


def send_to_llm(payload: Dict) -> Tuple[Optional[str], Optional[str]]:
    """
    Send request to LLM and get complete response (no streaming)
    Includes retry logic with exponential backoff
    
    Args:
        payload: Request payload
        
    Returns:
        Tuple of (response_text, error_message)
        If successful: (text, None)
        If failed: (None, error_message)
    """
    headers = {
        "Authorization": f"Bearer {JANITOR_AI_KEY}",
        "Content-Type": "application/json"
    }
    
    last_error = None
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            # Add delay for retries
            if attempt > 0:
                delay_ms = BACKOFF_MS[min(attempt - 1, len(BACKOFF_MS) - 1)]
                time.sleep(delay_ms / 1000.0)
                print(f"Retry attempt {attempt + 1}/{MAX_RETRIES + 1}")
            
            # Make request
            start_time = time.time()
            response = requests.post(
                JANITOR_AI_URL,
                headers=headers,
                json=payload,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                stream=False  # No streaming
            )
            
            latency = time.time() - start_time
            print(f"LLM request completed in {latency:.2f}s (status: {response.status_code})")
            
            # Handle response codes
            if response.status_code == 200:
                # Success - parse response
                try:
                    response.encoding = 'utf-8'
                    data = response.json()
                    
                    # Handle streaming format (data: prefix on each line)
                    if isinstance(data, str):
                        # Parse SSE format
                        message = _parse_sse_response(data)
                        if message:
                            return (_clean_text(message), None)
                    
                    # Handle standard JSON format
                    if 'choices' in data and len(data['choices']) > 0:
                        content = data['choices'][0].get('message', {}).get('content', '')
                        if not content:
                            # Try delta format
                            content = data['choices'][0].get('delta', {}).get('content', '')
                        
                        if content:
                            return (_clean_text(content), None)
                    
                    # If we got here, couldn't parse response
                    return (None, "Failed to parse LLM response format")
                    
                except json.JSONDecodeError as e:
                    # Try parsing as SSE
                    message = _parse_sse_response(response.text)
                    if message:
                        return (_clean_text(message), None)
                    return (None, f"JSON decode error: {e}")
            
            elif response.status_code == 429:
                # Rate limit - don't retry, use fallback
                last_error = "Rate limit exceeded"
                break
            
            elif 400 <= response.status_code < 500:
                # Client error - don't retry
                last_error = f"Client error {response.status_code}"
                break
            
            elif response.status_code >= 500:
                # Server error - retry
                last_error = f"Server error {response.status_code}"
                continue
            
        except requests.exceptions.Timeout:
            last_error = "Request timeout"
            continue
        
        except requests.exceptions.ConnectionError:
            last_error = "Connection error"
            continue
        
        except Exception as e:
            last_error = f"Unexpected error: {str(e)}"
            continue
    
    # All retries failed
    return (None, last_error)


def _parse_sse_response(response_text: str) -> Optional[str]:
    """
    Parse Server-Sent Events (SSE) streaming response format
    Even though we don't stream, the API might return in SSE format
    """
    try:
        complete_message = []
        lines = response_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith(':'):
                continue
            
            if line.startswith('data: '):
                json_str = line[6:]  # Remove 'data: ' prefix
                
                try:
                    chunk = json.loads(json_str)
                    
                    # Extract content from delta
                    if 'choices' in chunk and len(chunk['choices']) > 0:
                        choice = chunk['choices'][0]
                        
                        # Try delta format
                        content = choice.get('delta', {}).get('content', '')
                        if not content:
                            # Try message format
                            content = choice.get('message', {}).get('content', '')
                        
                        if content:
                            complete_message.append(content)
                
                except json.JSONDecodeError:
                    continue
        
        result = ''.join(complete_message)
        return result if result else None
        
    except Exception as e:
        print(f"Error parsing SSE response: {e}")
        return None


def get_fallback_response() -> str:
    """Get a safe fallback response"""
    import random
    return random.choice(FALLBACK_RESPONSES)


def handle_agent_response(session_id: str, text: str) -> bool:
    """
    Process and save agent response to session
    
    Args:
        session_id: Session ID
        text: Agent response text
        
    Returns:
        True if successful
    """
    from app import session_manager
    
    try:
        # Validate and clean
        text = _clean_text(text)
        if not text:
            return False
        
        # Clamp to max length
        if len(text) > REPLY_MAX_CHARS:
            text = text[:REPLY_MAX_CHARS].rsplit(' ', 1)[0] + "..."
        
        # Append to session transcript
        session_manager.append_transcript(session_id, "Janitor", text)
        
        print(f"Agent response saved to session {session_id}: {text[:100]}...")
        return True
        
    except Exception as e:
        print(f"Error handling agent response: {e}")
        return False


def trigger_agent(session_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Main orchestrator: trigger agent to respond to conversation
    
    Args:
        session_id: Session ID
        
    Returns:
        Tuple of (success, response_text, error_message)
    """
    try:
        # Check if agent is busy or in cooldown
        if _is_agent_busy(session_id):
            return (False, None, "Agent is busy or in cooldown")
        
        # Mark as busy
        _set_agent_busy(session_id, True)
        
        try:
            # Build prompt
            payload = build_agent_prompt(session_id)
            if not payload:
                return (False, None, "Failed to build prompt")
            
            # Call LLM
            response_text, error = send_to_llm(payload)
            
            # Handle response
            if response_text:
                # Save to session
                success = handle_agent_response(session_id, response_text)
                if success:
                    return (True, response_text, None)
                else:
                    return (False, None, "Failed to save response")
            else:
                # Use fallback
                fallback = get_fallback_response()
                handle_agent_response(session_id, fallback)
                return (True, fallback, f"Used fallback due to: {error}")
        
        finally:
            # Clear busy flag
            _set_agent_busy(session_id, False)
    
    except Exception as e:
        _set_agent_busy(session_id, False)
        return (False, None, f"Exception: {str(e)}")


def should_trigger_agent(session_id: str) -> bool:
    """
    Determine if agent should be triggered based on conversation state
    
    Args:
        session_id: Session ID
        
    Returns:
        True if agent should respond
    """
    from app import session_manager
    
    try:
        # Check if busy
        if _is_agent_busy(session_id):
            return False
        
        # Load session
        session = session_manager.load_session(session_id)
        if not session:
            return False
        
        transcript = session.get('transcript', [])
        if len(transcript) < 3:
            # Too early
            return False
        
        # Check last speaker
        if transcript:
            last_speaker = transcript[-1].get('speaker', '')
            if last_speaker.lower() in ['janitor', 'agent', 'ai']:
                # Agent just spoke, don't trigger again
                return False
        
        # Count turns since last agent message
        turns_since_agent = 0
        for entry in reversed(transcript):
            speaker = entry.get('speaker', '').lower()
            if speaker in ['janitor', 'agent', 'ai']:
                break
            turns_since_agent += 1
        
        # Trigger after 4-6 user turns
        if turns_since_agent >= 4:
            return True
        
        # Check for trigger patterns in recent messages
        recent = transcript[-3:]
        recent_text = " ".join([e.get('text', '').lower() for e in recent])
        
        trigger_patterns = [
            '?',  # Questions
            'what do you think',
            'help',
            'advice',
            'janitor',
            'host'
        ]
        
        for pattern in trigger_patterns:
            if pattern in recent_text:
                return True
        
        return False
        
    except Exception as e:
        print(f"Error checking if should trigger agent: {e}")
        return False


def get_agent_stats(session_id: str) -> Dict:
    """
    Get agent statistics for a session
    
    Args:
        session_id: Session ID
        
    Returns:
        Dictionary with agent stats
    """
    from app import session_manager
    
    try:
        session = session_manager.load_session(session_id)
        if not session:
            return {}
        
        transcript = session.get('transcript', [])
        
        agent_messages = [
            e for e in transcript 
            if e.get('speaker', '').lower() in ['janitor', 'agent', 'ai']
        ]
        
        state = _agent_state.get(session_id, {})
        
        return {
            'total_messages': len(transcript),
            'agent_messages': len(agent_messages),
            'agent_percentage': len(agent_messages) / len(transcript) * 100 if transcript else 0,
            'is_busy': state.get('busy', False),
            'last_call': state.get('last_call', 0),
            'cooldown_remaining': max(0, AGENT_COOLDOWN_SEC - (time.time() - state.get('last_call', 0)))
        }
        
    except Exception as e:
        print(f"Error getting agent stats: {e}")
        return {}

