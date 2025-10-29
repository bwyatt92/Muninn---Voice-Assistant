# Muninn Project - Current Status

**Last Updated:** October 22, 2025
**Project:** Muninn Voice Assistant for Dad's 70th Birthday

## Project Overview

Muninn is a custom Raspberry Pi voice assistant that allows family members to:
- Record and playback voice messages
- Create and browse rich, categorized memories
- Use voice commands to interact with the system
- Access a web portal for management

**Target User:** Dad (70th birthday gift)
**Hardware:** Raspberry Pi 5 with Voice Bonnet
**Location:** `/home/bw/muninn/muninn-v3/muninn-modular`

---

## Recent Session Summary (Oct 22, 2025)

### 1. System Reliability Improvements ✅ DEPLOYED

**Problem:** Raspberry Pi was becoming unresponsive due to service restart loops.

**Solutions Implemented:**
- Enhanced systemd service files with:
  - Restart limits (max 5 attempts in 10 minutes)
  - Memory limits (512MB assistant, 256MB web portal)
  - CPU limits (80% assistant, 50% web portal)
  - Graceful shutdown handling

**Files Created:**
- `health_check.sh` - System health monitoring
- `system_monitor.py` - Continuous monitoring service
- `muninn-monitor.service` - Optional monitoring service
- `deploy_services.sh` - Automated deployment
- `DEPLOYMENT.md` - Full documentation
- `RELIABILITY_IMPROVEMENTS.md` - Technical details
- `QUICK_START.md` - Quick deployment guide

**Status:** ✅ DEPLOYED AND TESTED
- Services restarted with new configurations
- Health check script working
- System stable

### 2. Memories System ⚠️ NOT YET DEPLOYED

**Feature:** Rich, structured memory system separate from simple messages.

**What's Built:**
- Database schema for memories table
- Backend API with 6 endpoints:
  - GET `/api/memories` - List/filter
  - POST `/api/memories/save` - Save memory
  - POST `/api/memories/delete` - Delete
  - GET `/api/memories/random` - Random selection
  - GET `/api/memories/audio/<id>` - Serve audio
  - GET `/memories` - Memory UI page

- 5-step creation wizard:
  1. Select person (17 family members)
  2. Choose type (joke, story, advice, moment, song, other)
  3. Pick length (short, medium, long)
  4. Add details (title, tags)
  5. Record audio

- Memory browser with:
  - Filtering by person, type, length
  - Search by title/tags
  - Play/delete controls
  - Responsive design

- Navigation added to main dashboard

**Files Created/Modified:**
- `web_portal.py` - Enhanced with memories backend
- `templates/memories.html` - Full memory interface (NEW)
- `templates/dashboard_enhanced.html` - Added navigation link
- `MEMORIES_SYSTEM.md` - Complete documentation

**Status:** ⚠️ READY TO DEPLOY (NOT YET DEPLOYED)

**Deployment Command:**
```bash
rsync -avz muninn-modular/ bw@raspberrypi:/home/bw/muninn/muninn-v3/muninn-modular/
ssh bw@raspberrypi
cd /home/bw/muninn/muninn-v3/muninn-modular
dos2unix web_portal.py templates/memories.html
sudo systemctl restart muninn-web-portal.service
```

---

## System Components Status

### Deployed & Working ✅

1. **Muninn Voice Assistant** (`muninn.py`)
   - Wake word detection (custom "Muninn" model)
   - Speech recognition (Vosk)
   - TTS (KittenTTS)
   - LED status indicators
   - Command processing
   - Service: `muninn-assistant.service`

2. **Web Portal** (`web_portal.py`)
   - System vitals monitoring
   - Voice message recording/playback
   - Message management
   - System logs viewer
   - Network configuration
   - Service: `muninn-web-portal.service`

3. **Enhanced Service Files**
   - Resource limits
   - Restart protection
   - Graceful shutdown
   - Health monitoring

4. **Health Monitoring**
   - `health_check.sh` script
   - `system_monitor.py` service
   - Real-time vitals

### Built, Ready to Deploy ⚠️

1. **Memories System**
   - Database schema
   - Backend API
   - Creation wizard UI
   - Memory browser
   - Search/filter capabilities

### Not Yet Built 🔴

1. **Voice Commands for Memories**
   - "Muninn, tell me a joke"
   - "Muninn, tell me a story from Mom"
   - "Muninn, tell me about Christmas"
   - Requires command processor updates

---

## Family Members Configuration

All 17 family members configured:
- Jean, Carrie, Cassie, Scott
- Beau, Lizzie, Allie, Luke
- Charlie, Bea, Lyra, Tui
- Sevro, Nick, Dakota, DeAmber, Caryl

---

## File Structure

```
/home/bw/muninn/muninn-v3/muninn-modular/
├── muninn.py                    # Main voice assistant
├── web_portal.py                # Web portal (ENHANCED - not deployed)
├── health_check.sh              # Health monitoring (DEPLOYED)
├── system_monitor.py            # Continuous monitor (DEPLOYED)
├── deploy_services.sh           # Deployment script (DEPLOYED)
├── muninn-assistant.service     # Enhanced service (DEPLOYED)
├── muninn-web-portal.service    # Enhanced service (DEPLOYED)
├── muninn-monitor.service       # Optional monitor (DEPLOYED)
│
├── config/
│   └── settings.py              # Configuration
│
├── speech/
│   ├── tts_engine.py           # Text-to-speech
│   ├── wake_word_detector.py  # Wake word detection
│   └── speech_recognizer.py   # Speech recognition
│
├── commands/
│   └── command_processor.py    # Command handling
│
├── audio/
│   └── audio_manager.py        # Audio management
│
├── hardware/
│   └── hardware_controller.py  # LED control
│
├── templates/
│   ├── dashboard_enhanced.html  # Main dashboard (ENHANCED - not deployed)
│   ├── memories.html            # Memories interface (NEW - not deployed)
│   └── logs.html                # Logs viewer
│
└── Documentation/
    ├── DEPLOYMENT.md
    ├── RELIABILITY_IMPROVEMENTS.md
    ├── QUICK_START.md
    ├── MEMORIES_SYSTEM.md
    └── PROJECT_STATUS.md (this file)
```

---

## Database Schema

### Current (Deployed)

**messages** table:
```sql
id, person, file_path, description,
created_at, file_size, duration
```

### Ready to Deploy

**memories** table:
```sql
id, person, memory_type, length_category,
title, tags, file_path, created_at,
file_size, duration
```

---

## URLs & Access

- **Web Portal:** http://raspberrypi:5001
- **Dashboard:** http://raspberrypi:5001/
- **Memories:** http://raspberrypi:5001/memories (when deployed)
- **Logs:** http://raspberrypi:5001/logs

---

## Services Status

```bash
# Check service status
sudo systemctl status muninn-assistant.service
sudo systemctl status muninn-web-portal.service
sudo systemctl status muninn-monitor.service

# View logs
sudo journalctl -u muninn-assistant -n 50
sudo journalctl -u muninn-web-portal -n 50

# Health check
./health_check.sh
```

---

## Next Steps

### Immediate (When Ready)
1. ⚠️ **Deploy Memories System**
   - Transfer updated files
   - Fix line endings (dos2unix)
   - Restart web portal
   - Test memory creation workflow
   - Test memory browsing/playback

### Future Enhancements
1. 🔴 **Voice Commands for Memory Recall**
   - Update command processor
   - Add memory recall intents
   - Test with wake word + commands
   - Examples:
     - "Muninn, tell me a joke"
     - "Muninn, tell me a story from Mom"
     - "Muninn, tell me about Christmas"

2. 🔴 **Additional Features** (Nice to Have)
   - Photo/video attachments
   - Memory collections
   - Date context tracking
   - Related memories linking
   - Privacy levels
   - Memory of the day
   - Export as podcast

---

## Known Issues & Considerations

### Resolved ✅
- ✅ Service restart loops - Fixed with restart limits
- ✅ Resource exhaustion - Fixed with memory/CPU limits
- ✅ Python path errors - Documented in deployment guide
- ✅ Line ending issues - Fixed with dos2unix

### To Monitor
- Memory usage under load
- CPU temperature during recording
- Disk space (audio files accumulate)
- Service stability over time

### Deployment Notes
- Always use `rsync` for file transfer
- Always run `dos2unix` on scripts after transfer
- Always check health after deployment
- Test recordings from both mobile and desktop

---

## Testing Checklist

### Before Next Deployment
- [ ] Backup current database
- [ ] Test local recording on development machine
- [ ] Verify all family names are correct
- [ ] Review memory type categories

### After Deployment
- [ ] Web portal loads
- [ ] Memories button visible
- [ ] Memories page loads
- [ ] Can select person/type/length
- [ ] Can record audio
- [ ] Memory saves successfully
- [ ] Can browse memories
- [ ] Can filter/search
- [ ] Can play memories
- [ ] Can delete memories
- [ ] Messages system still works
- [ ] No errors in logs

---

## Key Decisions Made

1. **Kept Messages Separate** - Memories are a new system, messages untouched
2. **Guided UI** - Wizard approach vs freeform entry
3. **Large Buttons** - Accessibility for all ages
4. **Retro Aesthetic** - Maintained existing gaming theme
5. **Browser Recording** - No app needed, works on any device
6. **Rich Metadata** - Enables smart filtering and recall
7. **Optional Voice Recall** - Can add later without breaking existing system

---

## Resource Limits (Current)

| Service | Memory Max | CPU Max | Restart Limit |
|---------|-----------|---------|---------------|
| Assistant | 512MB | 80% | 5 in 10min |
| Web Portal | 256MB | 50% | 5 in 10min |
| Monitor | 128MB | 10% | 3 in 10min |

---

## Contact & Support

**System User:** bw
**System Path:** /home/bw/muninn/muninn-v3/muninn-modular
**Database:** /home/bw/muninn/muninn-v3/messages.db
**Recordings:** /home/bw/muninn/muninn-v3/recordings/
**Service Logs:** `sudo journalctl -u <service-name>`

---

## Version History

**v1.0** (Oct 22, 2025)
- Initial deployment with messages system
- Wake word detection
- Voice commands
- Web portal

**v1.1** (Oct 22, 2025)
- Service reliability improvements
- Resource limits added
- Health monitoring tools
- Documentation

**v2.0** (Not yet deployed)
- Memories system
- 5-step wizard
- Memory browser
- Enhanced filtering

**v2.1** (Future)
- Voice memory recall
- Advanced search
- Memory collections

---

**Status:** System is stable and operational. Memories system is ready for deployment when you're ready to test.
