#!/usr/bin/env python3
"""
Simple test/demo script for the session management system
Run this to test session operations without starting the full server
"""

from app import session_manager
import json

def print_separator():
    print("\n" + "="*60 + "\n")

def demo_session_management():
    """Demonstrate session management features"""
    
    print("🎭 SESSION MANAGEMENT DEMO")
    print_separator()
    
    # 1. Create a session
    print("1️⃣ Creating new session with User A...")
    session = session_manager.create_session("user_alice")
    print(f"   ✅ Created session: {session['session_id']}")
    print(f"   Status: {session['status']}")
    print(f"   Participants: {session['participants']}")
    
    print_separator()
    
    # 2. Join session
    print("2️⃣ User B joining session...")
    session_id = session['session_id']
    session = session_manager.join_session(session_id, "user_bob")
    print(f"   ✅ User joined session: {session_id}")
    print(f"   Status: {session['status']}")
    print(f"   Participants: {session['participants']}")
    
    print_separator()
    
    # 3. Add transcript entries
    print("3️⃣ Adding conversation transcript...")
    session_manager.append_transcript(session_id, "A", "Hey! Nice to meet you!")
    session_manager.append_transcript(session_id, "B", "Hi!")
    print("   ✅ Added 5 transcript entries")
    
    print_separator()
    
    # 4. Update phase
    print("4️⃣ Updating conversation phase...")
    session_manager.update_phase(session_id, "deep_dive")
    print("   ✅ Phase updated to: deep_dive")
    
    print_separator()
    
    # 5. Update summary
    print("5️⃣ Adding session summary...")
    summary = "Alice and Bob are connecting over outdoor activities. Both enjoy nature and creative pursuits."
    session_manager.update_summary(session_id, summary)
    print(f"   ✅ Summary: {summary}")
    
    print_separator()
    
    # 6. Show full session data
    print("6️⃣ Full session data:")
    session = session_manager.load_session(session_id)
    print(json.dumps(session, indent=2))
    
    print_separator()
    
    # 7. List active sessions
    print("7️⃣ Active sessions:")
    active = session_manager.list_active_sessions()
    for s in active:
        print(f"   - {s['session_id']}: {s['status']} ({s['phase']})")
    
    print_separator()
    
    # 8. Get stats
    print("8️⃣ Session statistics:")
    stats = session_manager.get_session_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print_separator()
    
    # 9. End session
    print("9️⃣ Ending session...")
    session_manager.end_session(session_id)
    print(f"   ✅ Session {session_id} ended")
    
    print_separator()
    
    print("✨ Demo complete!")
    print(f"\n📂 Check the sessions/ directory for saved JSON files")
    print(f"📊 Check sessions/log.csv for the activity log\n")


def interactive_test():
    """Interactive command-line tool for testing"""
    print("\n🎮 Interactive Session Manager")
    print("Commands: create, join, transcript, phase, summary, list, end, quit")
    print_separator()
    
    current_session_id = None
    
    while True:
        cmd = input("\n> ").strip().lower()
        
        if cmd == "quit":
            break
        
        elif cmd == "create":
            user_id = input("  Enter user ID: ").strip()
            session = session_manager.create_session(user_id)
            current_session_id = session['session_id']
            print(f"  ✅ Created session: {current_session_id}")
        
        elif cmd == "join":
            if not current_session_id:
                print("  ❌ No active session. Create one first.")
                continue
            user_id = input("  Enter user ID: ").strip()
            session_manager.join_session(current_session_id, user_id)
            print(f"  ✅ User joined session: {current_session_id}")
        
        elif cmd == "transcript":
            if not current_session_id:
                print("  ❌ No active session. Create one first.")
                continue
            speaker = input("  Speaker (A/B/AGENT): ").strip()
            text = input("  Text: ").strip()
            session_manager.append_transcript(current_session_id, speaker, text)
            print("  ✅ Transcript added")
        
        elif cmd == "phase":
            if not current_session_id:
                print("  ❌ No active session. Create one first.")
                continue
            phase = input("  Phase: ").strip()
            session_manager.update_phase(current_session_id, phase)
            print(f"  ✅ Phase updated to: {phase}")
        
        elif cmd == "summary":
            if not current_session_id:
                print("  ❌ No active session. Create one first.")
                continue
            summary = input("  Summary: ").strip()
            session_manager.update_summary(current_session_id, summary)
            print("  ✅ Summary updated")
        
        elif cmd == "list":
            sessions = session_manager.list_active_sessions()
            if not sessions:
                print("  No active sessions")
            for s in sessions:
                print(f"  - {s['session_id']}: {s['status']} ({s['phase']})")
        
        elif cmd == "end":
            if not current_session_id:
                print("  ❌ No active session. Create one first.")
                continue
            session_manager.end_session(current_session_id)
            print(f"  ✅ Ended session: {current_session_id}")
            current_session_id = None
        
        else:
            print("  Unknown command")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_test()
    else:
        demo_session_management()

