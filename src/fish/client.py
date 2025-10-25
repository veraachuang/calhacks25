"""
Fish Audio session manager.

Manages API configuration and session state for Fish Audio services.
"""

import os
import requests
from typing import Optional


class FishSessionManager:
    """
    Singleton manager for Fish Audio API sessions.

    Loads environment configuration and provides access to ASR and TTS sessions.

    Mock mode:
        When FISH_MOCK=true, all API calls return mock responses without network calls.

    Real implementation:
        Will initialize actual HTTP clients with API keys and base URLs for Fish Audio API.
    """

    _instance: Optional['FishSessionManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.api_key = os.getenv('FISH_API_KEY', '570c8155fed341b3a70212f41fc8fc44')
        self.api_base = os.getenv('FISH_API_BASE', 'https://api.fish.audio')
        self.mock_mode = os.getenv('FISH_MOCK', 'false').lower() == 'true'

        self._asr_session = None
        self._tts_session = None
        self._initialized = True

    def get_asr_session(self):
        """
        Get ASR session object.

        Real implementation:
            Returns configured HTTP session for Fish Audio ASR API.
        """
        if self.mock_mode:
            return None

        if self._asr_session is None:
            session = requests.Session()
            session.headers.update({
                'Authorization': f'Bearer {self.api_key}'
                # Content-Type will be set automatically for multipart/form-data
            })
            self._asr_session = session

        return self._asr_session

    def get_tts_session(self):
        """
        Get TTS session object.

        Real implementation:
            Returns configured HTTP session for Fish Audio TTS API.
        """
        if self.mock_mode:
            return None

        if self._tts_session is None:
            session = requests.Session()
            session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
            self._tts_session = session

        return self._tts_session
