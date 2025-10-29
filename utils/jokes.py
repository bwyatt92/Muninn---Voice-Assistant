#!/usr/bin/env python3

"""
Joke API Integration for Muninn
Fetches jokes from online APIs and formats them for TTS
"""

import requests
import random
from typing import Optional, Dict, Any


def get_random_joke() -> str:
    """
    Fetch a random joke from the joke API

    Returns:
        str: Formatted joke text for TTS, or fallback joke if API fails
    """
    try:
        # Primary API: Official Joke API
        url = "https://official-joke-api.appspot.com/jokes/random"
        print(f"🌐 Fetching joke from: {url}")

        response = requests.get(url, timeout=10)
        print(f"🌐 Joke API response: {response.status_code}")

        if response.status_code == 200:
            joke_data = response.json()
            print(f"🌐 Joke data: {joke_data}")

            setup = joke_data.get('setup', '').strip()
            punchline = joke_data.get('punchline', '').strip()

            if setup and punchline:
                # Format for natural speech with longer pause for comedic timing
                # Multiple periods create longer pauses in TTS
                formatted_joke = f"{setup}...... {punchline}"
                print(f"😄 Formatted joke: {formatted_joke}")
                return formatted_joke

        # If API fails, try backup API
        return _get_backup_joke()

    except Exception as e:
        print(f"❌ Error fetching joke: {e}")
        return _get_backup_joke()


def _get_backup_joke() -> str:
    """
    Get a backup joke from alternative API or fallback jokes

    Returns:
        str: Backup joke text
    """
    try:
        # Backup API: JokeAPI (SFW jokes only)
        backup_url = "https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,religious,political,racist,sexist,explicit&type=twopart"
        print(f"🌐 Trying backup joke API: {backup_url}")

        response = requests.get(backup_url, timeout=8)

        if response.status_code == 200:
            joke_data = response.json()

            if joke_data.get('type') == 'twopart':
                setup = joke_data.get('setup', '').strip()
                delivery = joke_data.get('delivery', '').strip()

                if setup and delivery:
                    formatted_joke = f"{setup}...... {delivery}"
                    print(f"😄 Backup joke: {formatted_joke}")
                    return formatted_joke

    except Exception as e:
        print(f"❌ Backup API also failed: {e}")

    # Ultimate fallback: built-in jokes
    return _get_fallback_joke()


def _get_fallback_joke() -> str:
    """
    Get a fallback joke when APIs are unavailable

    Returns:
        str: Fallback joke text
    """
    fallback_jokes = [
        "Why don't scientists trust atoms?...... Because they make up everything!",
        "What do you call a bear with no teeth?...... A gummy bear!",
        "Why did the coffee file a police report?...... It got mugged!",
        "What's the best thing about Switzerland?...... I don't know, but the flag is a big plus!",
        "Why don't eggs tell jokes?...... They'd crack each other up!",
        "What do you call a dinosaur that crashes his car?...... Tyrannosaurus Wrecks!",
        "Why did the math book look so sad?...... Because it was full of problems!",
        "What do you call a fake noodle?...... An impasta!",
        "Why don't programmers like nature?...... It has too many bugs!",
        "What's orange and sounds like a parrot?...... A carrot!"
    ]

    joke = random.choice(fallback_jokes)
    print(f"😄 Fallback joke: {joke}")
    return joke


def get_dad_joke() -> str:
    """
    Get a dad joke specifically (perfect for birthday!)

    Returns:
        str: Dad joke text
    """
    try:
        # Dad joke API
        url = "https://icanhazdadjoke.com/"
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Muninn Voice Assistant (https://github.com/yourrepo/muninn)'
        }

        print(f"🌐 Fetching dad joke from: {url}")
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            joke_data = response.json()
            joke_text = joke_data.get('joke', '').strip()

            if joke_text:
                print(f"👨 Dad joke: {joke_text}")
                return joke_text

    except Exception as e:
        print(f"❌ Dad joke API failed: {e}")

    # Fallback dad jokes
    dad_jokes = [
        "I told my wife she was drawing her eyebrows too high...... She looked surprised.",
        "What do you call a fish wearing a crown?...... A king fish!",
        "I used to hate facial hair...... but then it grew on me.",
        "What do you call a bear with no teeth?...... A gummy bear!",
        "Why don't scientists trust atoms?...... Because they make up everything!",
        "I'm reading a book about anti-gravity...... It's impossible to put down!",
        "Did you hear about the mathematician who's afraid of negative numbers?...... He'll stop at nothing to avoid them.",
        "Why do fathers take an extra pair of socks when they go golfing?...... In case they get a hole in one!"
    ]

    joke = random.choice(dad_jokes)
    print(f"👨 Fallback dad joke: {joke}")
    return joke


def test_joke_apis():
    """Test function to verify joke APIs are working"""
    print("🧪 Testing Joke APIs")
    print("=" * 30)

    print("1. Testing random joke API...")
    joke1 = get_random_joke()
    print(f"   Result: {joke1[:50]}...")

    print("\n2. Testing dad joke API...")
    joke2 = get_dad_joke()
    print(f"   Result: {joke2[:50]}...")

    print("\n✅ Joke API testing completed!")


if __name__ == "__main__":
    test_joke_apis()