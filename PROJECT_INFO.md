# Muninn Project Information

## Active Directory
**muninn-modular/** is the PRIMARY working directory for the Muninn Voice Assistant.

## Deployment Command
Changes are synced to the Raspberry Pi using:
```bash
rsync -varzP /mnt/c/Users/gpg-mchristian/muninn-voice-archive/muninn-modular bw@raspberrypi.local:muninn/muninn-v3
```

## Directory Structure
```
muninn-modular/
├── audio/          # Audio recording/playback management
├── commands/       # Voice command processing
├── config/         # Configuration settings
├── hardware/       # Hardware controllers (ReSpeaker, LEDs)
├── speech/         # Wake word detection, TTS, recognition
├── templates/      # Web portal HTML templates
├── utils/          # Utility functions (time, weather, jokes)
├── muninn.py       # Main application entry point
└── web_portal.py   # Flask web interface
```

## Important Notes
- **DO NOT** edit files in the root `muninn-voice-archive/` directory
- All development should be in `muninn-modular/`
- The web portal uses SQLite database at: `/home/bw/muninn/muninn-v3/messages.db`
- Recordings stored at: `/home/bw/muninn/muninn-v3/recordings/`

## Database Schema
The system uses two tables:
1. **messages** - Birthday messages from family members
2. **memories** - Stories uploaded via web portal (rich categorization)
