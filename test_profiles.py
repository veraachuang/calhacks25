#!/usr/bin/env python3
"""
Test script for profile management system
"""

from app import profile_manager, session_manager
import json

def print_separator():
    print("\n" + "="*60 + "\n")

def demo_profiles():
    """Demonstrate profile management"""
    
    print("👤 PROFILE MANAGEMENT DEMO")
    print_separator()
    
    # 1. Initialize profiles
    print("1️⃣ Initializing profile system...")
    profile_manager.init_profiles()
    print("   ✅ Profile system initialized")
    
    print_separator()
    
    # 2. Load base profiles
    print("2️⃣ Loading base profiles from disk...")
    profile_a = profile_manager.load_profile("user_A")
    profile_b = profile_manager.load_profile("user_B")
    
    print("   User A (base):")
    print(f"   {json.dumps(profile_a, indent=4)}")
    print("\n   User B (base):")
    print(f"   {json.dumps(profile_b, indent=4)}")
    
    print_separator()
    
    # 3. Create a session
    print("3️⃣ Creating a session...")
    session = session_manager.create_session("socket_alice")
    session_id = session['session_id']
    print(f"   ✅ Created session: {session_id}")
    
    # Join session
    session_manager.join_session(session_id, "socket_bob")
    print("   ✅ Bob joined session")
    
    print_separator()
    
    # 4. Attach profiles to session
    print("4️⃣ Attaching profiles to session...")
    profile_manager.attach_profiles_to_session(session_id)
    print("   ✅ Profiles attached")
    
    print_separator()
    
    # 5. Update session profiles (temporary changes)
    print("5️⃣ Updating session profiles (temporary)...")
    
    # Update User A's hobbies
    profile_manager.update_session_profile(
        session_id, 
        "socket_alice", 
        "hobbies", 
        ["art", "music", "gaming"]
    )
    print("   ✅ Updated User A hobbies in session")
    
    # Update User A's personality
    profile_manager.update_session_profile(
        session_id,
        "socket_alice",
        "personality_type",
        "ambivert"
    )
    print("   ✅ Updated User A personality in session")
    
    # Bulk update User B
    profile_manager.update_session_profile_bulk(
        session_id,
        "socket_bob",
        {
            "goal": "find adventure buddy",
            "hobbies": ["rock climbing", "traveling", "photography"],
            "interests": ["fitness", "nature"]
        }
    )
    print("   ✅ Bulk updated User B in session")
    
    print_separator()
    
    # 6. View session profiles
    print("6️⃣ Session profiles (with temporary edits):")
    profiles = profile_manager.get_both_profiles(session_id)
    print("\n   User A (session):")
    print(f"   {json.dumps(profiles['A'], indent=4)}")
    print("\n   User B (session):")
    print(f"   {json.dumps(profiles['B'], indent=4)}")
    
    print_separator()
    
    # 7. Verify base profiles unchanged
    print("7️⃣ Base profiles (unchanged on disk):")
    base_a = profile_manager.load_profile("user_A")
    base_b = profile_manager.load_profile("user_B")
    print("\n   User A (base - still original):")
    print(f"   Hobbies: {base_a['hobbies']}")
    print(f"   Personality: {base_a['personality_type']}")
    print("\n   User B (base - still original):")
    print(f"   Hobbies: {base_b['hobbies']}")
    print(f"   Goal: {base_b['goal']}")
    
    print_separator()
    
    # 8. Reset one profile
    print("8️⃣ Resetting User A profile to base...")
    profile_manager.reset_profile_to_base(session_id, "socket_alice")
    reset_profile = profile_manager.load_session_profile(session_id, "socket_alice")
    print(f"   ✅ Reset profile - hobbies back to: {reset_profile['hobbies']}")
    
    print_separator()
    
    # 9. End session
    print("9️⃣ Ending session...")
    session_manager.end_session(session_id)
    print(f"   ✅ Session ended - all temporary profile changes discarded")
    
    print_separator()
    
    # 10. Show full session JSON
    print("🔟 Full session data with profiles:")
    session_data = session_manager.load_session(session_id)
    print(json.dumps(session_data, indent=2))
    
    print_separator()
    
    print("✨ Demo complete!")
    print(f"\n📂 Base profiles saved in: profiles/")
    print(f"📂 Session data (with temp profiles) in: sessions/")
    print(f"\n💡 Note: Session profile changes don't affect base profiles!\n")


def interactive_test():
    """Interactive profile testing"""
    print("\n🎮 Interactive Profile Manager")
    print("Commands: init, load, create, update, view, reset, list, quit")
    print_separator()
    
    current_session_id = None
    current_user_id = None
    
    while True:
        cmd = input("\n> ").strip().lower()
        
        if cmd == "quit":
            break
        
        elif cmd == "init":
            profile_manager.init_profiles()
            print("  ✅ Profiles initialized")
        
        elif cmd == "load":
            user_id = input("  User ID (user_A/user_B): ").strip()
            profile = profile_manager.load_profile(user_id)
            if profile:
                print(json.dumps(profile, indent=2))
            else:
                print("  ❌ Profile not found")
        
        elif cmd == "create":
            user_id = input("  Enter socket ID for user A: ").strip()
            session = session_manager.create_session(user_id)
            current_session_id = session['session_id']
            current_user_id = user_id
            print(f"  ✅ Created session: {current_session_id}")
            
            # Ask to join
            join = input("  Add user B? (y/n): ").strip().lower()
            if join == 'y':
                user_b_id = input("  Enter socket ID for user B: ").strip()
                session_manager.join_session(current_session_id, user_b_id)
                profile_manager.attach_profiles_to_session(current_session_id)
                print("  ✅ User B joined and profiles attached")
        
        elif cmd == "update":
            if not current_session_id:
                print("  ❌ No active session. Create one first.")
                continue
            user_id = input("  User socket ID: ").strip()
            field = input("  Field to update: ").strip()
            value = input("  New value: ").strip()
            
            # Try to parse as JSON if it looks like a list/dict
            if value.startswith('[') or value.startswith('{'):
                try:
                    value = json.loads(value)
                except:
                    pass
            
            profile_manager.update_session_profile(current_session_id, user_id, field, value)
            print("  ✅ Profile updated")
        
        elif cmd == "view":
            if not current_session_id:
                print("  ❌ No active session. Create one first.")
                continue
            profiles = profile_manager.get_both_profiles(current_session_id)
            print(json.dumps(profiles, indent=2))
        
        elif cmd == "reset":
            if not current_session_id:
                print("  ❌ No active session. Create one first.")
                continue
            user_id = input("  User socket ID: ").strip()
            profile_manager.reset_profile_to_base(current_session_id, user_id)
            print("  ✅ Profile reset to base")
        
        elif cmd == "list":
            profiles = profile_manager.list_all_profiles()
            print(json.dumps(profiles, indent=2))
        
        else:
            print("  Unknown command")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_test()
    else:
        demo_profiles()

