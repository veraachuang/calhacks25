"""
Fish Audio TTS (Text-to-Speech) module.

Converts text to audio bytes.
"""

import struct
import math
from .client import FishSessionManager


def stream_tts(text: str, reference_id: str = None, emotion: str = None) -> bytes:
    """
    Convert text to audio bytes using Fish Audio TTS.

    Args:
        text: Text string to synthesize into speech.

    Returns:
        Audio data as bytes (WAV format).

    Mock mode:
        Returns a short generated WAV file with a simple 440Hz tone (1 second).

    Real implementation:
        Sends text to Fish Audio TTS API endpoint and returns the audio data.
    """
    manager = FishSessionManager()

    if manager.mock_mode:
        return _generate_mock_wav()

    # Real Fish Audio TTS API call
    session = manager.get_tts_session()
    url = f"{manager.api_base}/v1/tts"

    try:
        # Fish Audio TTS API payload
        payload = {
            'text': text,
            'format': 'wav',
            'reference_id': reference_id or 'b279044ffddf4291b14da6aac86b528e'  # Can be customized for specific voices
        }

        # Add emotion parameter if provided
        if emotion:
            payload['emotion'] = emotion

        response = session.post(url, json=payload, timeout=60, stream=True)
        response.raise_for_status()

        # Aggregate audio chunks from streaming response
        audio_chunks = []
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                audio_chunks.append(chunk)

        raw_audio = b''.join(audio_chunks)
        
        # Fix WAV file if data chunk size is 0 (Fish Audio API bug)
        return _fix_wav_data_chunk(raw_audio)

    except Exception as e:
        raise RuntimeError(f"Fish Audio TTS API call failed: {str(e)}")


def _fix_wav_data_chunk(wav_data: bytes) -> bytes:
    """
    Fix WAV file where data chunk size is incorrectly set to 0.
    
    Fish Audio API sometimes returns WAV files with data chunk size = 0
    but actual audio data after the header. This function corrects the size.
    """
    if not wav_data.startswith(b'RIFF') or b'WAVE' not in wav_data[:20]:
        return wav_data  # Not a WAV file, return as-is
    
    # Find the data chunk
    pos = 12  # Skip RIFF header
    while pos < len(wav_data) - 8:
        chunk_id = wav_data[pos:pos+4]
        chunk_size = struct.unpack('<I', wav_data[pos+4:pos+8])[0]
        
        if chunk_id == b'data':
            # Check if data chunk size is 0 but there's actual data
            if chunk_size == 0 and len(wav_data) > pos + 8:
                # Calculate actual data size
                actual_data_size = len(wav_data) - pos - 8
                
                # Update the data chunk size in the header
                fixed_wav = bytearray(wav_data)
                struct.pack_into('<I', fixed_wav, pos + 4, actual_data_size)
                
                # Also update the RIFF chunk size
                total_size = len(fixed_wav) - 8
                struct.pack_into('<I', fixed_wav, 4, total_size)
                
                return bytes(fixed_wav)
            break
        pos += 8 + chunk_size
    
    return wav_data  # No fix needed


def _generate_mock_wav() -> bytes:
    """
    Generate a simple mock WAV file with a 440Hz tone.

    Returns:
        WAV file bytes (1 second, 440Hz sine wave, 16-bit PCM, mono, 44100Hz sample rate).
    """
    sample_rate = 44100
    duration = 1.0
    frequency = 440.0

    num_samples = int(sample_rate * duration)

    # Generate 440Hz sine wave with proper amplitude
    samples = []
    for i in range(num_samples):
        # Generate sine wave with 0.3 amplitude to avoid clipping
        value = int(32767 * 0.3 * math.sin(2 * math.pi * frequency * i / sample_rate))
        # Ensure value is within 16-bit signed range
        value = max(-32768, min(32767, value))
        samples.append(struct.pack('<h', value))

    audio_data = b''.join(samples)

    # WAV header - fixed to use proper little-endian format
    wav_header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        36 + len(audio_data),
        b'WAVE',
        b'fmt ',
        16,  # fmt chunk size
        1,   # PCM format
        1,   # mono
        sample_rate,
        sample_rate * 2,  # byte rate
        2,   # block align
        16,  # bits per sample
        b'data',
        len(audio_data)
    )

    return wav_header + audio_data
