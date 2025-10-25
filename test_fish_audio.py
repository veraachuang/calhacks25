#!/usr/bin/env python3
"""
Fish Audio Test Script

Tests both TTS (Text-to-Speech) and ASR (Automatic Speech Recognition) functionality.
Supports both mock mode and real API mode.
"""

import os
import sys
import time
from pathlib import Path

# Add src to path so we can import fish modules
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from fish import stream_tts, stream_asr, FishSessionManager


def test_tts(text: str, output_file: str = "test_output.wav"):
    """Test Text-to-Speech functionality."""
    print(f"\n🎤 Testing TTS with text: '{text}'")
    
    try:
        # Generate audio
        start_time = time.time()
        audio_data = stream_tts(text)
        generation_time = time.time() - start_time
        
        # Save to file
        with open(output_file, 'wb') as f:
            f.write(audio_data)
        
        print(f"✅ TTS Success!")
        print(f"   - Generated {len(audio_data)} bytes of audio data")
        print(f"   - Generation time: {generation_time:.2f} seconds")
        print(f"   - Saved to: {output_file}")
        
        return audio_data
        
    except Exception as e:
        print(f"❌ TTS Failed: {e}")
        return None


def test_asr(audio_file: str):
    """Test Automatic Speech Recognition functionality."""
    print(f"\n🎧 Testing ASR with audio file: '{audio_file}'")
    
    try:
        # Read audio file
        with open(audio_file, 'rb') as f:
            audio_data = f.read()
        
        # Transcribe audio
        start_time = time.time()
        transcript = stream_asr(audio_data)
        transcription_time = time.time() - start_time
        
        print(f"✅ ASR Success!")
        print(f"   - Audio file size: {len(audio_data)} bytes")
        print(f"   - Transcription time: {transcription_time:.2f} seconds")
        print(f"   - Transcript: '{transcript}'")
        
        return transcript
        
    except Exception as e:
        print(f"❌ ASR Failed: {e}")
        return None


def test_session_manager():
    """Test Fish Session Manager configuration."""
    print("\n🔧 Testing Fish Session Manager")
    
    manager = FishSessionManager()
    
    print(f"   - API Key: {manager.api_key[:10]}..." if manager.api_key else "   - API Key: None")
    print(f"   - API Base: {manager.api_base}")
    print(f"   - Mock Mode: {manager.mock_mode}")
    
    # Test session creation
    asr_session = manager.get_asr_session()
    tts_session = manager.get_tts_session()
    
    print(f"   - ASR Session: {'Created' if asr_session else 'Mock mode (None)'}")
    print(f"   - TTS Session: {'Created' if tts_session else 'Mock mode (None)'}")


def main():
    """Main test function."""
    print("🐟 Fish Audio Test Suite")
    print("=" * 50)
    
    # Test session manager
    test_session_manager()
    
    # Test TTS
    test_texts = [
        "Hello, this is a test of Fish Audio text-to-speech.",
        "The quick brown fox jumps over the lazy dog.",
        "Testing one, two, three."
    ]
    
    audio_files = []
    for i, text in enumerate(test_texts):
        output_file = f"test_tts_{i+1}.wav"
        audio_data = test_tts(text, output_file)
        if audio_data:
            audio_files.append(output_file)
    
    # Test ASR with generated audio files
    for audio_file in audio_files:
        test_asr(audio_file)
    
    # Test ASR with a sample audio file (if it exists)
    sample_audio = "sample_audio.wav"
    if os.path.exists(sample_audio):
        print(f"\n🎵 Testing ASR with sample audio file: {sample_audio}")
        test_asr(sample_audio)
    else:
        print(f"\n💡 Tip: Place a sample audio file named '{sample_audio}' to test ASR with real audio")
    
    print("\n" + "=" * 50)
    print("🎉 Test suite completed!")
    
    # Cleanup option
    cleanup = input("\n🗑️  Clean up generated test files? (y/n): ").lower().strip()
    if cleanup == 'y':
        for audio_file in audio_files:
            if os.path.exists(audio_file):
                os.remove(audio_file)
                print(f"   - Removed {audio_file}")
        print("✅ Cleanup completed!")


if __name__ == "__main__":
    main()
