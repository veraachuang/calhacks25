"""
Fish Audio integration package.

Provides ASR (Automatic Speech Recognition) and TTS (Text-to-Speech) capabilities
with mock mode support for development.
"""

from .client import FishSessionManager
from .asr import stream_asr
from .tts import stream_tts

__all__ = ['FishSessionManager', 'stream_asr', 'stream_tts']
