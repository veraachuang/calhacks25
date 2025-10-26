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
MAX_TURNS_IN_PROMPT = 12  # Maximum conversation turns to include in prompt (captures ~15 seconds of conversation)
SUMMARY_MAX_TOKENS = 250  # Target summary length
REPLY_MAX_CHARS = 300  # Maximum characters in agent reply (shorter for faster, punchier responses)
CONNECT_TIMEOUT = 3  # Connection timeout in seconds
READ_TIMEOUT = 20  # Read timeout in seconds
MAX_RETRIES = 2  # Number of retry attempts
BACKOFF_MS = [400, 800]  # Backoff delays in milliseconds
AGENT_COOLDOWN_SEC = 15  # Minimum seconds between agent responses (increased to reduce frequency)


AGENT_RULES = """You are 'Lana,' a warm, observant, sarcasticdating show host who helps people connect. Be brief (1-2 sentences MAXIMUM). No emojis.

CRITICAL RULES:
1. Your response must ONLY be what Lana says - no labels, no "Lana:", no context
2. You MUST directly reference something specific the users JUST said in the conversation
3. Vary your response style - rotate between these approaches:
   - Direct question to one person about what the other said
   - Observation about shared interests or chemistry
   - Gentle prompt to dig deeper into a topic
   - Light playful comment to ease tension (ONLY if conversation feels awkward)
4. Examples of varied tones:
   - Direct: "So [name], outdoor adventure - yay or nay for you?"
   - Observation: "I'm noticing you both light up when talking about travel."
   - Prompt: "Tell me more about that - what draws you to it?"
   - Playful/sarcastic (ONLY for awkward moments): "Well that's one way to break the ice... Let's try something else - what's something you've always wanted to try?"
5. Use actual names, not "User A" and "User B" - makes it feel more personal"""

# Agent personality and rules
AGENT_PERSONALITY_BASIC = """You are "Lana," a friendly, witty dating-show host.

Your role:
- Listen to what User A and User B are ACTUALLY discussing
- Pick up on interesting topics they mention (hobbies, experiences, stories)
- Ask follow-up questions that connect them to each other
- Example: If they mention travel, ask "Have you two been to the same places?"
- Example: If one mentions a hobby, ask the other "What do you think about that?"

Keep it brief (1-2 sentences), natural, and engaging. Reference their actual conversation."""

AGENT_PERSONALITY_SPICY = """You are "Lana," a witty, flirtatious dating-show host.

Your role:
- React to what User A and User B are ACTUALLY saying
- If they're getting along, playfully tease them about the chemistry
- If conversation lags, ask a provocative but fun question
- Example: "I see sparks flying when you talk about that..."
- Example: "So what would be your ideal date together?"

Be brief (1-2 sentences), spicy, and reference their real conversation."""

AGENT_PERSONALITY_SEXY = """You are "Lana," a warm, perceptive dating-show host who helps people connect.

Your role:
- Listen carefully to what users are saying and help them explore common ground
- VARY your response style each time - don't always use the same format
- Use their actual NAMES, not generic labels
- If the word "awkward" appears, add a touch of playful sarcasm to lighten the mood
- Help deepen the conversation with different approaches

Examples of varied styles:
Style 1 (Direct question): "[Name], outdoor adventures - is that your thing too?"
Style 2 (Observation): "I'm sensing some chemistry when you talk about travel."
Style 3 (Deep dive): "What is it about that hobby that excites you?"
Style 4 (Connection): "You both mentioned loving food - have you been to any great restaurants lately?"
Style 5 (Awkward moment - playful): "Okay, that got quiet fast. Let's shake things up - what's the most spontaneous thing you've ever done?"

1-2 sentences MAX. Reference their ACTUAL words. Rotate between different approaches."""

# Track agent state per session
_agent_state = {}  # session_id -> {'busy': bool, 'last_call': timestamp}

# Fallback responses for errors
FALLBACK_RESPONSES = [
    "Let's keep it simple, A.Share one hobby you'd love to try with B.",
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


def _extract_lana_dialogue(text: str) -> str:
    """
    Extract only Lana's dialogue from the response, removing any context or labels.

    Handles cases where LLM includes:
    - "AI: User A: ... User B: ... Lana: <dialogue>"
    - "Lana: <dialogue>"
    - Context followed by "Lana: <dialogue>"
    """
    if not text:
        return ""

    # Look for "Lana:" or similar labels and extract what comes after
    lana_patterns = [
        r'Lana:\s*(.+)$',
        r'AI:\s*(.+)$',
        r'Host:\s*(.+)$',
    ]

    import re
    for pattern in lana_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            dialogue = match.group(1).strip()
            # Remove any remaining "User A:" or "User B:" prefixes that might be in the dialogue
            dialogue = re.sub(r'^(User [AB]:|[AB]:)\s*', '', dialogue, flags=re.IGNORECASE)
            return dialogue

    # If no label found, check if text starts with participant info pattern
    # Pattern: "AI: User A: ... User B: ... <actual dialogue>"
    # We want to extract only the dialogue after participant info
    lines = text.split('\n')

    # Skip lines that look like participant info (contain "User A:" or "User B:")
    dialogue_lines = []
    for line in lines:
        line = line.strip()
        # Skip empty lines
        if not line:
            continue
        # Skip lines that are just participant labels
        if re.match(r'^(AI:|User [AB]:|[AB]:)', line, re.IGNORECASE):
            # Check if there's content after the label on same line
            content_match = re.search(r'^(?:AI:|User [AB]:|[AB]:)\s*(.+)$', line, re.IGNORECASE)
            if content_match:
                content = content_match.group(1).strip()
                # Only include if it doesn't look like another label
                if not re.match(r'^(User [AB]:|[AB]:)', content, re.IGNORECASE):
                    dialogue_lines.append(content)
        else:
            dialogue_lines.append(line)

    if dialogue_lines:
        return ' '.join(dialogue_lines)

    # If nothing else worked, return the original text
    return text


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
            print(f"❌ Session {session_id} not found")
            print(f"   Available sessions: {list(session_manager.sessions.keys())}")
            return None

        # Check if session is active (both users have joined)
        session_status = session.get('status', 'unknown')
        if session_status != 'active':
            print(f"⚠️ Session {session_id} is not active yet (status: {session_status})")
            print(f"   Session has user_a: {'user_a' in session}, user_b: {'user_b' in session}")
            return None

        print(f"✅ Session {session_id} is active, building prompt...")

        # Load profiles
        profiles = profile_manager.get_both_profiles(session_id)
        profile_a = profiles.get('A')
        profile_b = profiles.get('B')

        if not profile_a or not profile_b:
            print(f"Profiles not found for session {session_id} (session may not be fully initialized)")
            return None
        
        # Build concise profile summary
        profile_summary = f"""About the participants:
- {profile_a.get('name', 'User A')}: Interested in {', '.join(profile_a.get('interests', [])[:2]) or 'conversation'}
- {profile_b.get('name', 'User B')}: Interested in {', '.join(profile_b.get('interests', [])[:2]) or 'conversation'}

Your task: Listen to their recent conversation and ask a relevant follow-up question."""

        # Get transcript
        transcript = session.get('transcript', [])

        # Build conversation context instruction
        context_instruction = """Recent conversation:
The conversation below is what the users JUST said. Pay attention and reference it directly."""
        
        # Build messages array
        messages = [
            {"role": "system", "content": AGENT_RULES},
            {"role": "system", "content": AGENT_PERSONALITY_SEXY},
            {"role": "system", "content": profile_summary},
            {"role": "system", "content": context_instruction}
        ]
        
        # Add recent conversation turns (last MAX_TURNS_IN_PROMPT)
        recent_transcript = transcript[-MAX_TURNS_IN_PROMPT:] if len(transcript) > MAX_TURNS_IN_PROMPT else transcript

        # Build conversation as one coherent block for better context
        conversation_lines = []
        for entry in recent_transcript:
            speaker_role = entry.get('speaker', 'Unknown')
            text = _clean_text(entry.get('text', ''))

            if not text:
                continue

            # Skip previous AI messages (we only want user dialogue)
            if speaker_role.lower() in ['janitor', 'agent', 'ai', 'lana']:
                continue

            # Get actual name instead of just "A" or "B"
            if speaker_role == 'A':
                speaker_name = profile_a.get('name', 'User A')
            elif speaker_role == 'B':
                speaker_name = profile_b.get('name', 'User B')
            else:
                speaker_name = speaker_role

            conversation_lines.append(f"{speaker_name}: {text}")

        # Add the full conversation as ONE user message for clarity
        if conversation_lines:
            full_conversation = "\n".join(conversation_lines)

            # Check if "awkward" appears in conversation
            is_awkward = 'awkward' in full_conversation.lower()

            if is_awkward:
                prompt_instruction = f"Here's what they just said:\n\n{full_conversation}\n\nThe conversation seems a bit awkward. Respond as Lana with a playful, lightly sarcastic comment to break the tension, then redirect to an easier topic. Use their actual names."
            else:
                prompt_instruction = f"Here's what they just said:\n\n{full_conversation}\n\nNow respond as Lana. Vary your style - don't repeat the same format as last time. Use their actual names (not User A/B). Help them connect by referencing what they discussed."

            messages.append({
                "role": "user",
                "content": prompt_instruction
            })

            print(f"📝 Conversation context ({len(conversation_lines)} lines) {'[AWKWARD MODE]' if is_awkward else ''}:")
            for line in conversation_lines[-3:]:  # Show last 3 for debugging
                print(f"   {line}")
        else:
            print("⚠️ No conversation to respond to!")
            return None
        
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
                            # Extract only Lana's dialogue, removing context
                            dialogue = _extract_lana_dialogue(content)
                            return (_clean_text(dialogue), None)
                    
                    # If we got here, couldn't parse response
                    return (None, "Failed to parse LLM response format")
                    
                except json.JSONDecodeError as e:
                    # Try parsing as SSE
                    message = _parse_sse_response(response.text)
                    if message:
                        dialogue = _extract_lana_dialogue(message)
                        return (_clean_text(dialogue), None)
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

        # Extract only dialogue from the SSE response
        if result:
            result = _extract_lana_dialogue(result)

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
            state = _agent_state.get(session_id, {})
            cooldown_remaining = max(0, AGENT_COOLDOWN_SEC - (time.time() - state.get('last_call', 0)))
            print(f"⏳ Agent busy for session {session_id}: cooldown {cooldown_remaining:.1f}s remaining")
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
            return False

        # Check last speaker
        if transcript:
            last_speaker = transcript[-1].get('speaker', '')
            if last_speaker.lower() in ['janitor', 'agent', 'ai']:
                return False

        # Count turns since last agent message
        turns_since_agent = 0
        for entry in reversed(transcript):
            speaker = entry.get('speaker', '').lower()
            if speaker in ['janitor', 'agent', 'ai']:
                break
            turns_since_agent += 1

        # Trigger after 6-8 user turns (increased to reduce frequency)
        if turns_since_agent >= 10:
            print(f"🤖 Agent triggering after {turns_since_agent} user turns")
            return True

        # Check for trigger patterns in recent messages
        recent = transcript[-3:]
        recent_text = " ".join([e.get('text', '').lower() for e in recent])

        trigger_patterns = [
            '?',  # Questions
            'awkward',
            'help',
            'advice',
            'janitor',
            'host'
        ]

        for pattern in trigger_patterns:
            if pattern in recent_text:
                print(f"🤖 Agent triggering due to keyword: '{pattern}'")
                return True

        return False

    except Exception as e:
        print(f"❌ Error checking if should trigger agent: {e}")
        import traceback
        traceback.print_exc()
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

