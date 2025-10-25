"""
Fish Audio ASR (Automatic Speech Recognition) module.

Converts audio bytes to text transcription.
"""

from .client import FishSessionManager


def stream_asr(audio_bytes: bytes) -> str:
    """
    Convert audio bytes to text transcript using Fish Audio ASR.

    Args:
        audio_bytes: Raw audio data in supported format (WAV, MP3, etc.)

    Returns:
        Transcribed text string.

    Real implementation:
        Sends audio_bytes to Fish Audio ASR API endpoint and returns the transcription.
    """
    manager = FishSessionManager()

    if manager.mock_mode:
        return "This is a mock transcription of your audio."

    # Real Fish Audio ASR API call
    session = manager.get_asr_session()
    url = f"{manager.api_base}/v1/asr"

    try:
        # Try with multipart/form-data approach
        files = {'audio': ('audio.wav', audio_bytes, 'audio/wav')}
        response = session.post(url, files=files, timeout=30)
        response.raise_for_status()

        result = response.json()

        # Fish Audio ASR API typically returns the transcript in a 'text' field
        if isinstance(result, dict) and 'text' in result:
            return result['text']
        elif isinstance(result, dict) and 'transcript' in result:
            return result['transcript']
        else:
            # If the response structure is different, return the whole result as string
            return str(result)

    except Exception as e:
        raise RuntimeError(f"Fish Audio ASR API call failed: {str(e)}")
