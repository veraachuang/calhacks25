"""
Flask application for Fish Audio integration.

Provides REST API endpoints for ASR and TTS services.
"""

import os
import base64
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from fish import stream_asr, stream_tts, FishSessionManager

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Fish session manager
fish_manager = FishSessionManager()


@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint.

    Returns:
        JSON with status and mode information.
    """
    return jsonify({
        'status': 'ok',
        'service': 'fish-audio-api',
        'mock_mode': fish_manager.mock_mode
    })


@app.route('/asr', methods=['POST'])
def asr():
    """
    Automatic Speech Recognition endpoint.

    Accepts audio data as raw bytes or file upload and returns transcript.

    Request:
        - Content-Type: application/octet-stream (raw bytes), OR
        - Content-Type: multipart/form-data with 'audio' file field

    Returns:
        JSON with transcript text.

    Mock mode:
        Returns mock transcript without processing audio.

    Real implementation:
        Will call Fish Audio ASR API with audio data.
    """
    try:
        # Check if raw bytes
        if request.content_type == 'application/octet-stream':
            audio_bytes = request.data
        # Check if file upload
        elif 'audio' in request.files:
            audio_file = request.files['audio']
            audio_bytes = audio_file.read()
        else:
            return jsonify({'error': 'No audio data provided'}), 400

        if not audio_bytes:
            return jsonify({'error': 'Empty audio data'}), 400

        transcript = stream_asr(audio_bytes)

        return jsonify({
            'transcript': transcript,
            'mock': fish_manager.mock_mode
        })

    except NotImplementedError as e:
        return jsonify({'error': str(e)}), 501
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/tts', methods=['POST'])
def tts():
    """
    Text-to-Speech endpoint.

    Accepts text and returns audio data as base64-encoded WAV.

    Request:
        JSON with 'text' field.

    Returns:
        JSON with base64-encoded audio data.

    Mock mode:
        Returns mock WAV tone without calling Fish Audio API.

    Real implementation:
        Will call Fish Audio TTS API with text.
    """
    try:
        data = request.get_json()

        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400

        text = data['text']

        if not text.strip():
            return jsonify({'error': 'Empty text provided'}), 400

        # Optional parameters for voice customization
        reference_id = data.get('reference_id')
        emotion = data.get('emotion')

        audio_bytes = stream_tts(text, reference_id=reference_id, emotion=emotion)
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

        return jsonify({
            'audio': audio_base64,
            'format': 'wav',
            'mock': fish_manager.mock_mode
        })

    except NotImplementedError as e:
        return jsonify({'error': str(e)}), 501
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'

    app.run(host=host, port=port, debug=debug)
