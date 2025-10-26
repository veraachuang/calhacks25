#!/usr/bin/env python3
"""
Test script for Agent Manager (Janitor AI)
"""

from app import agent_manager, session_manager, profile_manager
import json

def print_separator():
    print("\n" + "="*60 + "\n")

def demo_agent():
    """Demonstrate agent manager functionality"""
    
    print("🤖 AGENT MANAGER DEMO")
    print_separator()
    
    # 1. Initialize systems
    print("1️⃣ Initializing profile and session systems...")
    profile_manager.init_profiles()
    print("   ✅ Systems initialized")
    
    print_separator()
    
    # 2. Create a session with profiles
    print("2️⃣ Creating session with conversation...")
    session = session_manager.create_session("socket_alice")
    session_id = session['session_id']
    session_manager.join_session(session_id, "socket_bob")
    profile_manager.attach_profiles_to_session(session_id)
    print(f"   ✅ Session created: {session_id}")
    
    print_separator()
    
    # 3. Add some conversation
    print("3️⃣ Adding conversation transcript...")
    session_manager.append_transcript(session_id, "A", "I'm falling for you.")
    session_manager.append_transcript(session_id, "B", "No your not. ")
    print("   ✅ Added 4 conversation turns")
    
    print_separator()
    
    # 4. Check if agent should trigger
    print("4️⃣ Checking if agent should trigger...")
    should_trigger = agent_manager.should_trigger_agent(session_id)
    print(f"   Should trigger: {should_trigger}")
    
    print_separator()
    
    # 5. Build agent prompt
    print("5️⃣ Building agent prompt...")
    payload = agent_manager.build_agent_prompt(session_id)
    if payload:
        print("   ✅ Prompt built successfully")
        print(f"\n   Messages in prompt:")
        for i, msg in enumerate(payload['messages'], 1):
            role = msg['role']
            content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            print(f"   {i}. {role}: {content}")
    else:
        print("   ❌ Failed to build prompt")
    
    print_separator()
    
    # 6. Get agent stats
    print("6️⃣ Agent statistics (before triggering):")
    stats = agent_manager.get_agent_stats(session_id)
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print_separator()
    
    # 7. Trigger agent (this will make a real API call!)
    print("7️⃣ Triggering agent (making real LLM call)...")
    print("   ⚠️  This will call the actual Janitor AI API")
    
    confirm = input("\n   Continue with real API call? (y/n): ").strip().lower()
    
    if confirm == 'y':
        success, response_text, error = agent_manager.trigger_agent(session_id)
        
        if success:
            print(f"\n   ✅ Agent responded:")
            print(f"   {response_text}")
            if error:
                print(f"\n   ⚠️  Used fallback: {error}")
        else:
            print(f"\n   ❌ Agent failed: {error}")
    else:
        print("   Skipped API call")
    
    print_separator()
    
    # 8. Show updated transcript
    print("8️⃣ Full conversation transcript:")
    session = session_manager.load_session(session_id)
    for entry in session['transcript']:
        speaker = entry['speaker']
        text = entry['text']
        print(f"   {speaker}: {text}")
    
    print_separator()
    
    # 9. Show updated stats
    print("9️⃣ Final agent statistics:")
    stats = agent_manager.get_agent_stats(session_id)
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print_separator()
    
    print("✨ Demo complete!")
    print(f"\n📂 Session saved in: sessions/{session_id}.json\n")


def test_fallback():
    """Test fallback response system"""
    print("\n🛡️  FALLBACK RESPONSE TEST")
    print_separator()
    
    print("Testing fallback responses...")
    for i in range(5):
        fallback = agent_manager.get_fallback_response()
        print(f"{i+1}. {fallback}")
    
    print_separator()


def test_prompt_building():
    """Test prompt building in detail"""
    print("\n📝 PROMPT BUILDING TEST")
    print_separator()
    
    # Create minimal session
    print("Creating test session...")
    profile_manager.init_profiles()
    session = session_manager.create_session("test_user_a")
    session_id = session['session_id']
    session_manager.join_session(session_id, "test_user_b")
    profile_manager.attach_profiles_to_session(session_id)
    
    # Add long conversation
    print("Adding conversation...")
    for i in range(15):
        speaker = "A" if i % 2 == 0 else "B"
        text = f"This is message number {i+1} from speaker {speaker}"
        session_manager.append_transcript(session_id, speaker, text)
    
    # Build prompt
    print("\nBuilding prompt...")
    payload = agent_manager.build_agent_prompt(session_id)
    
    if payload:
        print(f"✅ Built prompt with {len(payload['messages'])} messages")
        print(f"   Max tokens: {payload.get('max_tokens', 'N/A')}")
        
        # Count message types
        system_msgs = [m for m in payload['messages'] if m['role'] == 'system']
        user_msgs = [m for m in payload['messages'] if m['role'] == 'user']
        
        print(f"   System messages: {len(system_msgs)}")
        print(f"   User messages: {len(user_msgs)}")
        print(f"   Total transcript entries: 15")
        print(f"   Messages in prompt: {len(user_msgs)} (trimmed to last {agent_manager.MAX_TURNS_IN_PROMPT})")
    
    # Clean up
    session_manager.end_session(session_id)
    
    print_separator()


def interactive_test():
    """Interactive agent testing"""
    print("\n🎮 Interactive Agent Manager")
    print("Commands: create, add, trigger, stats, payload, fallback, quit")
    print_separator()
    
    current_session_id = None
    
    while True:
        cmd = input("\n> ").strip().lower()
        
        if cmd == "quit":
            break
        
        elif cmd == "create":
            profile_manager.init_profiles()
            session = session_manager.create_session("alice")
            session_id = session['session_id']
            session_manager.join_session(session_id, "bob")
            profile_manager.attach_profiles_to_session(session_id)
            current_session_id = session_id
            print(f"  ✅ Created session: {session_id}")
        
        elif cmd == "add":
            if not current_session_id:
                print("  ❌ No session. Create one first.")
                continue
            speaker = input("  Speaker (A/B): ").strip()
            text = input("  Text: ").strip()
            session_manager.append_transcript(current_session_id, speaker, text)
            print("  ✅ Added to transcript")
        
        elif cmd == "trigger":
            if not current_session_id:
                print("  ❌ No session. Create one first.")
                continue
            print("  Triggering agent (real API call)...")
            success, response, error = agent_manager.trigger_agent(current_session_id)
            if success:
                print(f"  ✅ Agent: {response}")
                if error:
                    print(f"  ⚠️  (Used fallback: {error})")
            else:
                print(f"  ❌ Failed: {error}")
        
        elif cmd == "stats":
            if not current_session_id:
                print("  ❌ No session. Create one first.")
                continue
            stats = agent_manager.get_agent_stats(current_session_id)
            print(json.dumps(stats, indent=2))
        
        elif cmd == "payload":
            if not current_session_id:
                print("  ❌ No session. Create one first.")
                continue
            payload = agent_manager.build_agent_prompt(current_session_id)
            if payload:
                print(json.dumps(payload, indent=2))
            else:
                print("  ❌ Failed to build payload")
        
        elif cmd == "fallback":
            fallback = agent_manager.get_fallback_response()
            print(f"  Janitor: {fallback}")
        
        else:
            print("  Unknown command")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "interactive":
            interactive_test()
        elif sys.argv[1] == "fallback":
            test_fallback()
        elif sys.argv[1] == "prompt":
            test_prompt_building()
    else:
        demo_agent()

