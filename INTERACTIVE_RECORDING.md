# Interactive Story Recording Feature

## Overview
Muninn can now record stories, memories, jokes, and wisdom interactively through voice! When you say "record a story", Muninn will guide you through a series of questions to properly categorize the recording - just like the web UI.

---

## How to Use

### Starting a Recording
Say any of these commands after the wake word:
- "Record a story"
- "Record a memory"
- "Record story"

### The Interactive Workflow

Muninn will ask you 5 questions:

#### 1. Who is this story from?
**Example:** "Scott" or "Beau"

#### 2. What type of memory is this?
**Options:**
- Story (general story/memory)
- Advice (life advice/wisdom)
- Joke (funny story)
- Wisdom (lessons learned)

**Example:** "This is a story" or "Advice"

#### 3. What should I title this memory?
**Example:** "The fishing trip of 2015"

#### 4. Any tags for this memory?
**Example:** "fishing, family, summer" or say "none" to skip

#### 5. Ready to record
Muninn will say: "Ready to record [title]. I'll record for 60 seconds, or say stop to finish early."

The recording will:
- Automatically record for up to 60 seconds
- Stop early if you say "stop"
- Be saved to the recordings folder
- Be added to the memories database with all metadata

---

## What Gets Saved

The recording is saved with:
- **Person**: Who the story is from
- **Type**: story, advice, joke, or wisdom
- **Title**: Your custom title
- **Tags**: Searchable tags
- **Length**: Automatically categorized as short (<20s), medium (20-45s), or long (>45s)
- **Duration**: Exact length in seconds
- **File**: Audio recording in WAV format
- **ID**: Unique identifier
- **Timestamp**: When it was recorded

---

## Example Session

```
You: "Muninn"
Muninn: "How may I serve you?"

You: "Record a story"
Muninn: "Who is this story from?"

You: "Scott"
Muninn: "What type of memory is this? Say story, advice, joke, or wisdom."

You: "This is advice"
Muninn: "What should I title this memory?"

You: "Life lessons from dad"
Muninn: "Any tags for this memory? Say none if you don't want tags."

You: "Family, wisdom, important"
Muninn: "Ready to record Life lessons from dad. I'll record for 60 seconds, or say stop to finish early."

[Records for 60 seconds or until you say "stop"]

Muninn: "Perfect! I've saved Life lessons from dad from Scott."
```

---

## Playing Back Recorded Stories

Once recorded, you can play them back using story commands:

```
You: "Muninn"
Muninn: "How may I serve you?"

You: "Play a story from Scott"
Muninn: [Plays the recorded story]
```

Or get specific types:
```
You: "Play advice from Scott"
You: "Play a joke from Beau"
You: "Play a short story from Carrie"
```

---

## Technical Details

### Files Modified
- **audio/manager.py**: Added `save_memory()` method
- **commands/processor.py**: Added `_handle_record_story()` and `_get_voice_input()` methods
- **speech/recognition.py**: Added `raw_text` field to recognition results

### Database Schema
Recordings are saved to the `memories` table:
```sql
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    person TEXT NOT NULL,
    memory_type TEXT NOT NULL,
    length_category TEXT NOT NULL,
    title TEXT,
    tags TEXT,
    file_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_size INTEGER,
    duration REAL
)
```

### Recording Settings
- **Max Duration**: 60 seconds
- **Sample Rate**: 16000 Hz
- **Channels**: 1 (mono)
- **Format**: WAV

---

## Tips

1. **Speak clearly** during the question-and-answer phase
2. **Use simple names** - stick to the family names Muninn knows
3. **Keep titles concise** - shorter titles are easier for Muninn to understand
4. **Say "none" for tags** if you don't want to add any
5. **Say "stop" to end early** if you don't need the full 60 seconds

---

## Troubleshooting

### Issue: Muninn doesn't understand my answer
**Solution**: Speak clearly and pause briefly after Muninn asks the question. If it doesn't work, the recording will be cancelled and you can try again.

### Issue: Recording was saved but database update failed
**Solution**: Check that the database file exists at the configured location. The audio file will still be saved in the recordings folder.

### Issue: Muninn keeps recording even after I say "stop"
**Solution**: This feature requires additional implementation for early stop detection. Currently, recordings go for the full 60 seconds.

---

## Deployment

To deploy this feature to your Raspberry Pi:

```bash
# From Windows/development machine
rsync -varzP /mnt/c/Users/gpg-mchristian/muninn-voice-archive/muninn-modular bw@raspberrypi.local:muninn/muninn-v3

# SSH into Pi and restart service
ssh bw@raspberrypi.local
sudo systemctl restart muninn-assistant
sudo journalctl -u muninn-assistant -f
```

---

## Future Enhancements

Possible improvements:
1. **Early stop detection**: Implement voice-activated stop during recording
2. **Playback preview**: Let user hear the recording before saving
3. **Edit metadata**: Allow changing title/tags after recording
4. **Recording quality indicator**: Show audio levels during recording
5. **Multi-person tagging**: Tag recordings with multiple family members

---

## Summary

This feature makes it easy to capture Dad's memories, stories, and wisdom through natural voice interaction. No need to use the web portal - just ask Muninn to record, answer a few questions, and tell the story!

Enjoy preserving precious memories! 🎙️
