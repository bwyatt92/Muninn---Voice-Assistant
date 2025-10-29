# Muninn Memories System

A rich, structured memory system that allows family members to record categorized memories that Muninn can intelligently recall.

## Overview

The Memories system extends Muninn's capabilities beyond simple message playback to include:
- **Structured metadata**: Type, length, tags, and titles
- **Guided recording UI**: Step-by-step wizard for easy recording
- **Smart filtering**: Browse memories by person, type, length, or search terms
- **Voice recall**: Ask Muninn to recall specific memories (coming soon)

## Features

### Memory Creation Wizard

A 5-step guided process:

1. **Who?** - Select the family member creating the memory
2. **What type?** - Choose from:
   - 😄 Joke - Something funny
   - 📖 Story - A tale to tell
   - 💡 Advice - Wisdom to share
   - 🎉 Special Moment - A cherished memory
   - 🎵 Song - Music or singing
   - ✨ Other - Something unique

3. **How long?** - Indicate duration:
   - ⚡ Short (< 1 minute)
   - ⏱️ Medium (1-3 minutes)
   - 📚 Long (3+ minutes)

4. **Details** - Add optional metadata:
   - Title for the memory
   - Tags (comma-separated keywords)

5. **Record** - Capture the audio memory

### Memory Browser

Filter and search memories:
- **By Person**: View memories from specific family members
- **By Type**: Filter jokes, stories, advice, etc.
- **By Length**: Find short, medium, or long memories
- **Search**: Find memories by title or tags
- **Play**: Listen to any memory
- **Delete**: Remove unwanted memories

## Family Members

The system supports these family members:
- Jean, Carrie, Cassie, Scott
- Beau, Lizzie, Allie, Luke
- Charlie, Bea, Lyra, Tui
- Sevro, Nick, Dakota, DeAmber, Caryl

## Technical Details

### Database Schema

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

### API Endpoints

#### Get Memories
```
GET /api/memories?person=Jean&memory_type=joke&length_category=short&search=birthday
```

#### Save Memory
```
POST /api/memories/save
Content-Type: multipart/form-data

Fields:
- audio: Audio file (WAV)
- person: Family member name
- memory_type: joke|story|advice|moment|song|other
- length_category: short|medium|long
- title: Optional title
- tags: Optional comma-separated tags
```

#### Delete Memory
```
POST /api/memories/delete
Content-Type: application/json

{
  "memory_id": "uuid"
}
```

#### Get Random Memory
```
GET /api/memories/random?memory_type=joke
```

#### Get Memory Audio
```
GET /api/memories/audio/<memory_id>
```

## Voice Commands (Coming Soon)

Planned voice interactions:

```
"Muninn, tell me a joke"
→ Plays random joke memory

"Muninn, tell me a story from Mom"
→ Plays random story from Mom

"Muninn, tell me something short and funny"
→ Plays short joke memory

"Muninn, tell me about Christmas"
→ Plays memory tagged with "Christmas"

"Muninn, tell me a special moment from the grandkids"
→ Plays special moment from children

"Muninn, what memories do you have about birthdays?"
→ Lists/plays birthday-tagged memories
```

## Accessing the Memories System

### Web Portal
1. Open the Muninn Web Portal: `http://raspberrypi:5001`
2. Click the **🧠 MEMORIES** button
3. Choose **Create Memory** or **Browse Memories**

### Create a Memory
1. Click "Create Memory"
2. Follow the 5-step wizard:
   - Select who's creating it
   - Choose the type
   - Indicate length
   - Add title/tags (optional)
   - Record the audio
3. Click "Save Memory"

### Browse Memories
1. Click "Browse Memories"
2. Use filters to narrow down:
   - Select a family member
   - Choose a memory type
   - Pick a length category
   - Or search by keywords
3. Click "▶️ Play" to listen
4. Click "🗑️ Delete" to remove

## Integration with Muninn Voice Assistant

The voice assistant integration adds intelligent memory recall through the command processor.

### Adding Voice Commands

To enable voice recall, update the command processor to handle memory-related intents:

**Example intents:**
- `play_joke` - Play a random joke memory
- `play_story` - Play a story memory
- `play_memory_from` - Play memory from specific person
- `tell_about` - Play memories matching topic/tags

The backend already supports:
- `GET /api/memories/random?memory_type=joke&person=Jean`
- Filtering by any combination of person, type, length, tags

## File Organization

Memory audio files are stored in:
```
/home/bw/muninn/muninn-v3/recordings/
```

With naming pattern:
```
memory_{person}_{type}_{timestamp}.wav
```

Example:
```
memory_Jean_joke_20251022_153045.wav
```

## Deployment

The memories system is automatically included when you deploy the web portal.

### Quick Deployment
```bash
# Transfer updated files
rsync -avz --delete muninn-modular/ bw@raspberrypi:/home/bw/muninn/muninn-v3/muninn-modular/

# Restart web portal
ssh bw@raspberrypi
sudo systemctl restart muninn-web-portal.service
```

### Verify Deployment
```bash
# Check service status
sudo systemctl status muninn-web-portal.service

# Test memories page
curl http://localhost:5001/memories
```

## Database Migration

When you first restart the web portal after deploying this update, the memories table will be created automatically. Existing messages are not affected.

To verify the table was created:
```bash
sqlite3 /home/bw/muninn/muninn-v3/messages.db "SELECT sql FROM sqlite_master WHERE name='memories';"
```

## UI Design

The memories interface matches the existing retro gaming aesthetic:
- **Press Start 2P font** for authentic retro feel
- **Dark background** with colored gradients
- **Large, accessible buttons** for easy selection
- **Step-by-step wizard** for guided experience
- **Mobile responsive** for recording on phones

## Future Enhancements

Potential additions:
- [ ] Photo/video attachments with memories
- [ ] Memory collections (group related memories)
- [ ] Date context (when did this happen?)
- [ ] Related memories linking
- [ ] Privacy levels (some memories just for Dad)
- [ ] Memory of the day feature
- [ ] Anniversary reminders
- [ ] Multi-language support
- [ ] Export memories as podcast/audio book

## Troubleshooting

### Memories page won't load
```bash
# Check if web portal is running
sudo systemctl status muninn-web-portal.service

# Check logs
sudo journalctl -u muninn-web-portal -n 50
```

### Can't record audio
- Ensure browser has microphone permissions
- Try HTTPS if on remote connection
- Check browser console for errors
- Test with a different browser

### Memories not saving
```bash
# Check database exists
ls -la /home/bw/muninn/muninn-v3/messages.db

# Check recordings directory
ls -la /home/bw/muninn/muninn-v3/recordings/

# Check web portal logs
sudo journalctl -u muninn-web-portal -f
```

### Memory audio won't play
- Check file exists in recordings directory
- Verify file permissions
- Check browser audio codec support
- Try downloading and playing locally

## Examples

### Example Memory: Dad's Joke
```
Person: Jean
Type: Joke
Length: Short
Title: "The One About the Penguin"
Tags: animals, dad-jokes, silly
Audio: 45 seconds of laughter
```

### Example Memory: Birthday Story
```
Person: Carrie
Type: Story
Length: Medium
Title: "Dad's 70th Birthday Surprise"
Tags: birthday, family, celebration, 2025
Audio: 2 minutes of the birthday story
```

### Example Memory: Grandma's Advice
```
Person: DeAmber
Type: Advice
Length: Short
Title: "Always Check the Weather"
Tags: wisdom, practical, funny
Audio: 30 seconds of grandmotherly wisdom
```

## Support

For issues or questions:
1. Check the web portal logs
2. Review this documentation
3. Test with the health check: `./health_check.sh`
4. Check the DEPLOYMENT.md guide

---

**Created:** October 2024
**Version:** 1.0
**Status:** Ready for use (Voice recall coming soon)
