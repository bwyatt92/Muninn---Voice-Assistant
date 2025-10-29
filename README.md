# Muninn Modular Voice Assistant

A refactored, modular version of the Muninn voice assistant with clean separation of concerns and easy maintainability.

## 🏗️ Architecture

```
muninn-modular/
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration and constants
├── speech/
│   ├── __init__.py
│   ├── tts.py              # Text-to-speech engine (KittenTTS)
│   ├── wake_word.py        # Wake word detection (Porcupine)
│   └── recognition.py      # Speech recognition (Vosk + fuzzy matching)
├── commands/
│   ├── __init__.py
│   └── processor.py        # Command processing and intent handling
├── audio/
│   ├── __init__.py
│   └── manager.py          # Audio recording and playback
├── utils/
│   ├── __init__.py
│   └── time_weather.py     # Time and weather utilities
├── muninn.py               # Main application coordinator
├── setup.py                # Setup script
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🚀 Quick Start

### On Raspberry Pi

1. **Clone and setup:**
   ```bash
   cd ~/
   git clone <your-repo> muninn-modular
   cd muninn-modular
   python3 setup.py
   ```

2. **Copy model files:**
   ```bash
   # Copy wake word model
   cp /path/to/munin_en_raspberry-pi_v3_0_0.ppn .

   # Copy Vosk model
   cp -r /path/to/vosk-model-small-en-us-0.15 .
   ```

3. **Run:**
   ```bash
   python3 muninn.py
   ```

### For Development/Testing

Run in mock mode without hardware:
```bash
python3 muninn.py --mock
```

## 🔧 Components

### Speech Module (`speech/`)
- **TTS Engine**: KittenTTS integration with ReSpeaker audio output
- **Wake Word Detector**: Porcupine-based wake word detection
- **Speech Recognizer**: Vosk integration with smart fuzzy matching

### Command Module (`commands/`)
- **Command Processor**: Intent handling and response generation
- Supports: play messages, record audio, time/weather, stop commands

### Audio Module (`audio/`)
- **Audio Manager**: Recording and playback functionality
- WAV file management and ReSpeaker integration

### Utils Module (`utils/`)
- **Time/Weather**: Current time and weather API integration

### Config Module (`config/`)
- **Settings**: Centralized configuration and constants
- Family name patterns and command fuzzy matching rules

## 🎯 Features

- **Modular Design**: Easy to maintain and extend
- **Conversational Flow**: Multi-turn conversations without repeated wake words
- **Mock Mode**: Test without hardware
- **Smart Fuzzy Matching**: Handles speech recognition errors
- **Punctuation Handling**: Ensures complete TTS playback
- **Factory Pattern**: Easy component swapping and testing

### 💬 Conversational Flow

Muninn now supports natural conversations:

1. **Wake Word**: Say "Muninn" to start
2. **First Command**: "What time is it?"
3. **Follow-up**: "What's the weather?" (no wake word needed!)
4. **Continue**: Up to 5 commands in sequence
5. **Auto-timeout**: Returns to sleep after 8 seconds of silence

**Configuration**:
- `CONVERSATION_TIMEOUT`: 15 seconds max conversation duration
- `FOLLOW_UP_TIMEOUT`: 8 seconds for follow-up commands
- `MAX_CONVERSATION_TURNS`: 5 consecutive commands max

## 🛠️ Dependencies

### Core Requirements
- `pyaudio` - Audio I/O
- `vosk` - Speech recognition
- `pvporcupine` - Wake word detection
- `librosa` - Audio processing
- `numpy` - Numerical operations
- `requests` - Weather API

### Optional
- `kittentts` - Text-to-speech (install manually)
- `soundfile` - Audio file handling

## 📝 Usage Examples

### Basic Voice Commands
- **"Muninn, what time is it?"** - Get current time
- **"Muninn, what's the weather?"** - Get weather info
- **"Muninn, record this"** - Start recording (general)
- **"Muninn, record for dad"** - Record message specifically for dad
- **"Muninn, play all messages"** - Play all birthday messages (cycles through all family members)
- **"Muninn, play dad's messages"** - Play all messages from dad
- **"Muninn, list messages"** - Show message counts by family member
- **"Muninn, tell me a joke"** - Random joke from online APIs
- **"Muninn, tell me a dad joke"** - Dad joke (perfect for birthdays!)
- **"Muninn, stop"** - Stop current operation

### 🎁 Enhanced Message System

The birthday message system now supports:

**Recording Messages:**
- General recording: `"record this"`
- Targeted recording: `"record for mom"`, `"record message for carrie"`

**Playing Messages:**
- Play all messages: Cycles through each family member with their messages
- Individual playback: `"play dad's messages"` - plays all of dad's messages
- Smart announcements: "Playing 3 messages from dad", "Messages from carrie"

**Message Management:**
- Automatic organization by family member
- Message counts and durations tracked
- Persistent JSON database storage
- List functionality: `"list messages"` shows counts per person

### 😄 Joke System

Entertainment features perfect for family gatherings:

**Random Jokes:**
- Fetches from https://official-joke-api.appspot.com/jokes/random
- Backup APIs for reliability
- Fallback jokes when offline

**Dad Jokes:**
- Special dad joke API integration
- Perfect for birthday celebrations
- Cheesy jokes that dads love!

**Smart Formatting:**
- Natural pauses between setup and punchline
- Proper punctuation for clear TTS delivery

### Conversational Examples

**Basic Conversation:**
```
User: "Muninn, what time is it?"
Muninn: "It's 3:45 PM on Tuesday, September 29th."
[Waits for follow-up - no wake word needed]

User: "What's the weather?"
Muninn: "It's sunny and 60 degrees."
[Still listening...]

User: [8 seconds of silence]
Muninn: [Returns to wake word mode]
```

**Birthday Message Examples:**
```
User: "Muninn, list messages"
Muninn: "I have 8 messages from 4 family members. Dad has 3 messages. Mom has 2 messages. Carrie has 2 messages. Scott has 1 message."
[Still listening...]

User: "Play all messages"
Muninn: "Playing all 8 birthday messages from 4 family members. Messages from Dad."
[Plays dad's messages]
Muninn: "Messages from Mom."
[Plays mom's messages]
... [continues through all family members]
Muninn: "All birthday messages have been played."

User: "Play just dad's messages"
Muninn: "Playing 3 messages from dad."
[Plays all of dad's messages]
Muninn: "Those were all 3 messages from dad."
```

**Entertainment Examples:**
```
User: "Muninn, tell me a joke"
Muninn: "Here's a joke for you. What's 50 Cent's name in Zimbabwe?... 200 Dollars."
[Still listening...]

User: "Tell me a dad joke"
Muninn: "Here's a dad joke for you. Why don't scientists trust atoms?... Because they make up everything!"
[Conversation continues...]

User: "What's the weather?"
Muninn: "It's sunny and 60 degrees."
[Perfect mix of practical and entertainment features!]
```

### Development
```python
from speech import get_tts_engine
from config import MuninnConfig

# Get TTS engine in mock mode
tts = get_tts_engine(mock_mode=True)
tts.speak("Hello from modular Muninn!")
```

## 🔄 Migration from Monolithic

The modular version maintains the same functionality as the monolithic version but with:
- Better code organization
- Easier testing and debugging
- Simplified component swapping
- Clean separation of concerns
- Improved maintainability

## 🐛 Troubleshooting

### Audio Issues
- Check ReSpeaker device detection in logs
- Verify audio device permissions
- Test with `--mock` mode first

### TTS Issues
- Ensure KittenTTS is installed
- Check sentence punctuation (periods required)
- Verify audio output device

### Wake Word Issues
- Confirm Porcupine access key is valid
- Check wake word model file path
- Test microphone functionality

## 📚 Development

### Adding New Commands
1. Add command patterns to `config/settings.py`
2. Add intent detection in `speech/recognition.py`
3. Add handler in `commands/processor.py`

### Adding New TTS Voices
1. Update voice options in `speech/tts.py`
2. Modify default in `config/settings.py`

### Testing
```bash
# Run in mock mode for testing
python3 muninn.py --mock

# Test individual components
python3 -c "from speech import get_tts_engine; get_tts_engine(mock_mode=True).speak('Test')"
```