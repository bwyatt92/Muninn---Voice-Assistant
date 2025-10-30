# Story Command Reference

## Voice Commands for Stories

### Basic Commands
```
"Get a story"
"Tell me a story"
"Play a story"
"Give me a story"
```

### Filter by Person
```
"Get a story from Carrie"
"Tell me a story from mom"
"Play a story from Lizzie"
"Get a story from Beau"
```

### Filter by Length
```
"Get a short story"
"Tell me a quick story"
"Give me a long story"
"Play a brief story"
```

### Combine Filters
```
"Get a short story from mom"
"Tell me a long story from Carrie"
"Play advice from mom"
"Get a birthday story from Lizzie"
```

## Supported Family Names
The system understands these name variations:
- **Carrie**: carrie, mom, mommy, mother
- **Cassie**: cassie, cass
- **Scott**: scott, scotty
- **Beau**: beau, bo
- **Lizzie**: lizzie, liz, elizabeth
- **Jean**: jean, jeanie
- **Nick**: nick, nicholas, nicky
- **Dakota**: dakota, kota
- **Bea**: bea, beatrice
- **Charlie**: charlie, charles
- **Allie**: allie, ally
- **Luke**: luke, lucas
- **Lyra**: lyra
- **Tui**: tui
- **Sevro**: sevro, sev

## Story Types
- **advice** - Life advice and wisdom
- **birthday** - Birthday messages/stories
- **funny** - Humorous stories
- **wisdom** - Life lessons

## Tips for Best Recognition

1. **Speak clearly** after "How may I serve you?"
2. **Use simple phrases**: "Get a story from mom" works better than "Can you get me a story from mom"
3. **Pause briefly** after the wake word before speaking
4. **If not understood**: Try rephrasing with different words
   - Instead of: "Play a tale from mother"
   - Try: "Get a story from mom"

## Troubleshooting

**Problem:** "I don't have any stories to play"
- **Cause:** No stories uploaded yet
- **Fix:** Upload stories via web portal at `http://raspberrypi.local:5001/memories`

**Problem:** "I don't have any stories from [person]"
- **Cause:** No stories tagged for that person
- **Fix:** Check person name in web portal matches what you're saying

**Problem:** Command not understood
- **Try these variations:**
  - "Get story" (shorter)
  - "Play story from Carrie" (different verb)
  - "Story from mom" (minimal)
  - "Tell me story" (casual)

## Example Conversation Flow

```
You: "Muninn"
Muninn: "How may I serve you?"
You: "Get a story"
Muninn: "Playing [title] from [person]"
[Story plays]
Muninn: [Returns to wake word mode]

You: "Muninn"
Muninn: "How may I serve you?"
You: "Get a story from mom"
Muninn: "Playing [title] from Carrie"
[Story plays]
```

## Birthday Messages vs Stories

**Birthday Messages:** Use these commands:
- "Play birthday message from Carrie"
- "Play mom's message"
- "Play all birthday messages"

**Stories:** Use these commands:
- "Get a story from Carrie"
- "Tell me a story from mom"
- "Play a story"

Both systems work independently and can be used in the same conversation.
