#!/usr/bin/env python3

"""
Muninn Configuration Settings
"""

import os
from typing import Dict, List

class MuninnConfig:
    """Configuration settings for Muninn voice assistant"""

    # ReSpeaker configuration
    SAMPLE_RATE = 16000
    CHANNELS = 1
    FRAME_LENGTH = 512
    CHUNK_SIZE = 1024

    # Recording settings
    RECORDINGS_DIR = "./recordings"

    # TTS Configuration
    DEFAULT_VOICE = 'expr-voice-4-f'

    # Conversational settings
    CONVERSATION_TIMEOUT = 15  # seconds to stay in conversation mode
    FOLLOW_UP_TIMEOUT = 8      # seconds to wait for follow-up command
    MAX_CONVERSATION_TURNS = 5 # maximum consecutive commands before requiring wake word

    # Command patterns for fuzzy matching
    COMMAND_PATTERNS = {
        'play': ['play', 'played', 'playing', 'plate', 'pale', 'clay', 'way', 'say'],
        'all': ['all', 'old', 'hall', 'owl', 'the', 'call', 'paul', 'wall'],
        'birthday': ['birthday', 'birth day', 'berth day', 'birthday\'s', 'thursday', 'tuesday'],
        'message': ['message', 'messages', 'massage', 'msg', 'passage', 'mess'],
        'record': ['record', 'recorded', 'recording', 'report', 'recall'],
        'stop': ['stop', 'stopped', 'stopping', 'top', 'shop', 'step'],
        'time': ['time', 'clock', 'what time', 'what\'s the time', 'current time'],
        'weather': ['weather', 'temperature', 'forecast', 'how\'s the weather', 'what\'s the weather'],
        'play_last': ['play last', 'play recent', 'play recording', 'last recording', 'recent recording'],
        'list': ['list', 'show', 'what messages', 'who has messages', 'message count'],
        'record_for': ['record for', 'record message for', 'save for'],
        'joke': ['joke', 'tell me a joke', 'tell a joke', 'make me laugh', 'funny', 'humor'],
        'dad_joke': ['dad joke', 'tell me a dad joke', 'father joke', 'cheesy joke']
    }

    # Family members with phonetic variations
    FAMILY_NAMES = {
        'carrie': ['carrie', 'carry', 'carey', 'larry', 'marry', 'fairy', 'mom', 'mommy', 'mother'],
        'cassie': ['cassie', 'cass', 'cassidy', 'sassy', 'lassie'],
        'scott': ['scott', 'scotty', 'lot', 'bot', 'shot', 'cot'],
        'beau': ['beau', 'bo', 'low', 'sew', 'mow', 'snow'],
        'lizzie': ['lizzie', 'liz', 'lizzy', 'elizabeth', 'dizzy', 'whizzy', 'fizzy', 'busy'],
        'jean': ['jean', 'jeanie', 'gene', 'jane', 'dean'],
        'nick': ['nick', 'nicky', 'nicholas', 'nic', 'nik', 'mick', 'pick', 'dick'],
        'dakota': ['dakota', 'de', 'kota', 'lakota', 'tacoma'],
        'bea': ['bea', 'beatrice', 'bee', 'b', 'tea', 'pea'],
        'charlie': ['charlie', 'charles', 'chuck', 'charley', 'harley', 'barley'],
        'allie': ['allie', 'ally', 'allison', 'alley', 'valley', 'sally'],
        'luke': ['luke', 'lucas', 'look', 'luca', 'duke', 'nuke'],
        'lyra': ['lyra', 'lira', 'lira', 'lyric', 'laura', 'lara'],
        'tui': ['tui', 'tooi', 'twi', 'twee', 'too', 'two'],
        'sevro': ['sevro', 'sev', 'servo', 'severe', 'seven']
    }

    @classmethod
    def setup_directories(cls):
        """Ensure required directories exist"""
        os.makedirs(cls.RECORDINGS_DIR, exist_ok=True)