# Muninn Performance & Feature Improvements

## Date: 2025-01-XX
## Directory: muninn-modular/

---

## Overview
This document summarizes all performance optimizations and new features added to the Muninn Voice Assistant modular version.

---

## ✨ New Features Added

### 1. **Story/Memory Playback System**
Added complete integration with web portal's memories system for playing uploaded stories.

**Files Modified:**
- `audio/manager.py` (lines 584-700)
- `commands/processor.py` (lines 58-63, 401-462)

**New Methods in AudioManager:**
- `get_memories_by_person(person, limit)` - Fetch stories from specific family member
- `get_memories_by_type(memory_type, limit)` - Fetch by type (story, advice, birthday)
- `get_random_memory(person, memory_type, length_category)` - Get random story with filters
- `get_all_memories(limit)` - Fetch all available stories

**Voice Commands:**
- "Get a story" - Plays random story
- "Get a story from [person]" - Plays story from specific family member
- "Get a [short/medium/long] story" - Filter by length
- "Get [advice/birthday/story] from [person]" - Specific type and person

---

## 🚀 Performance Optimizations

### 1. **Reduced Response Delays** (muninn.py)

| Location | Before | After | Improvement |
|----------|--------|-------|-------------|
| Mute button display | 2.0s | 1.0s | 50% faster |
| Wake word response | 0.2s | 0.1s | 50% faster |
| Follow-up listening | 0.3s | 0.1s | 67% faster |
| Conversation loop | 0.2s | 0.1s | 50% faster |

**Impact:** System feels significantly more responsive between commands.

---

### 2. **Optimized Timeout Settings** (config/settings.py)

| Setting | Before | After | Improvement |
|---------|--------|-------|-------------|
| Conversation timeout | 15s | 12s | 20% faster |
| Follow-up timeout | 8s | 6s | 25% faster |

**Impact:** Faster return to wake word mode when no command is detected.

---

### 3. **Audio Playback Already Optimal** (audio/manager.py)

The audio playback system was already well-optimized with:
- ✅ Multiple format support (WAV, MP3, WebM, etc.)
- ✅ Efficient chunk-based playback
- ✅ Fallback strategies for different audio formats
- ✅ Minimal post-playback delays (0.1s)

No changes needed here.

---

## 📊 Expected Performance Improvements

### Before Optimizations:
```
Wake word → Response:     ~0.4-0.5s of delays
Command → Next listen:    ~0.5-0.6s of delays
Follow-up timeout:        8 seconds
Conversation timeout:     15 seconds
```

### After Optimizations:
```
Wake word → Response:     ~0.2s of delays (50% faster)
Command → Next listen:    ~0.2s of delays (60% faster)
Follow-up timeout:        6 seconds (25% faster)
Conversation timeout:     12 seconds (20% faster)
```

### Real-World Impact:
- **Feels snappier:** Commands trigger faster after wake word
- **Quicker recovery:** Empty results return to listening faster
- **Better flow:** Reduced pauses between conversation turns
- **More responsive:** System doesn't feel like it's "thinking" as much

---

## 🔧 Technical Details

### Database Integration
Stories are fetched from the same SQLite database used by the web portal:
- **Location:** `/home/bw/muninn/muninn-v3/messages.db`
- **Table:** `memories`
- **Fields:** id, person, memory_type, length_category, title, tags, file_path, created_at, file_size, duration

### Name Mapping
The system maps common name variations to family members:
```python
'mom' → 'carrie'
'liz' → 'lizzie'
'bo' → 'beau'
'kota' → 'dakota'
... etc
```

This works for both birthday messages and story requests.

---

## 📝 Usage Examples

### Story Playback Commands:
```
User: "Muninn"
Muninn: "How may I serve you?"
User: "Get a story"
Muninn: "Playing [story title] from [person]."
[Plays audio]
```

```
User: "Muninn"
Muninn: "How may I serve you?"
User: "Get a story from mom"
Muninn: "Playing [story title] from Carrie."
[Plays audio]
```

```
User: "Muninn"
Muninn: "How may I serve you?"
User: "Get a short story"
Muninn: "Playing [title] from [person]."
[Plays audio]
```

---

## 🧪 Testing Recommendations

### 1. **Test Story Fetching:**
```bash
# Upload stories via web portal first
# Then test voice commands:
- "Get a story"
- "Get a story from [family member]"
- "Get a short story"
- "Get advice from mom"
```

### 2. **Test Response Times:**
- Say wake word and time until "How may I serve you?"
  - Target: < 0.3 seconds
- Give command and time until next action
  - Target: < 0.4 seconds
- Test follow-up timeout (should return after 6 seconds of silence)

### 3. **Test Mixed Commands:**
```
Wake word → "Get a story" → [plays] → "Get another story" → [plays]
Wake word → "Play mom's birthday message" → [plays] → "Get a story from mom" → [plays]
```

---

## 🔄 Sync to Raspberry Pi

After making changes, sync to Pi using:
```bash
rsync -varzP /mnt/c/Users/gpg-mchristian/muninn-voice-archive/muninn-modular bw@raspberrypi.local:muninn/muninn-v3
```

Then restart the service:
```bash
ssh bw@raspberrypi.local
sudo systemctl restart muninn-assistant
```

---

## 📌 Important Notes

1. **Database Compatibility:** The story features require the `memories` table to exist in the database. The web portal should have already created this.

2. **No Breaking Changes:** All existing birthday message functionality remains unchanged. This is purely additive.

3. **Graceful Fallbacks:** If no stories are found, Muninn will politely inform the user and return to listening mode.

4. **Mock Mode Support:** Mock versions of all story methods are included for testing without hardware.

---

## 🎯 Future Optimization Opportunities

If you need even more speed:

1. **Reduce Wake Word Timeout:** Change from 30s to 20s in `muninn.py` line 154
2. **Parallel Initialization:** Pre-load audio resources during wake word detection
3. **Cache Story Metadata:** Keep frequently accessed story titles in memory
4. **Reduce TTS Delays:** Adjust the 0.5s pause before story playback (processor.py:453)

---

## 📦 Files Modified Summary

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `audio/manager.py` | +117 lines | Added memory/story database methods |
| `commands/processor.py` | +68 lines | Added story playback handler |
| `muninn.py` | 4 edits | Reduced delay timings |
| `config/settings.py` | 2 edits | Optimized timeout values |

**Total Lines Added:** ~185 lines
**Total Performance Improvements:** 5 optimizations

---

## ✅ Verification Checklist

Before deploying to production:

- [ ] Stories uploaded via web portal
- [ ] Database has `memories` table
- [ ] Test basic story playback: "Get a story"
- [ ] Test filtered requests: "Get a story from [person]"
- [ ] Test empty results: "Get a story from unknown-person"
- [ ] Verify faster response times feel natural
- [ ] Test conversation flow with mix of messages and stories
- [ ] Confirm no regressions in birthday message playback

---

## 🆘 Troubleshooting

**Problem:** "I don't have any stories to play"
- **Solution:** Upload stories via web portal first at `http://raspberrypi.local:5001/memories`

**Problem:** Story files not found
- **Solution:** Check that file paths in database match actual file locations

**Problem:** System feels too fast/abrupt
- **Solution:** Increase delays slightly in `muninn.py` (0.1s → 0.2s)

**Problem:** Follow-up timeout too short
- **Solution:** Increase `FOLLOW_UP_TIMEOUT` in `config/settings.py` from 6 back to 8 seconds

---

## 📞 Support

For issues or questions about these changes:
1. Check this document first
2. Review the code comments in modified files
3. Test with mock mode enabled for debugging
4. Check system logs: `sudo journalctl -u muninn-assistant -f`

---

**End of Document**
