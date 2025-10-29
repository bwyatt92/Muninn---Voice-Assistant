#!/usr/bin/env python3

"""
Time and Weather Utilities for Muninn
"""

import datetime
import requests


def get_current_time():
    """Get current time in a friendly format"""
    try:
        now = datetime.datetime.now()
        # Format: "It's 3:45 PM on Tuesday, December 28th"
        day_suffix = _get_day_suffix(now.day)
        time_str = now.strftime(f"It's %I:%M %p on %A, %B {now.day}{day_suffix}")
        return time_str
    except Exception as e:
        print(f"Error getting time: {e}")
        return "I'm sorry, I can't tell the time right now"


def _get_day_suffix(day):
    """Get suffix for day (1st, 2nd, 3rd, etc.)"""
    if 10 <= day % 100 <= 20:
        return "th"
    else:
        return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")


def get_weather(location=""):
    """Get current weather using wttr.in API"""
    try:
        # Try a simple format first
        url = f"http://wttr.in/?format=%C+%t"
        print(f"🌐 Weather API URL: {url}")

        response = requests.get(url, timeout=10)
        print(f"🌐 Weather API response: {response.status_code} - '{response.text.strip()}'")

        if response.status_code == 200:
            weather_data = response.text.strip()

            # Handle different response formats
            if not weather_data or weather_data == "Unknown location;":
                # Try alternative API
                return _get_weather_fallback()

            # Try to parse the response
            if '+' in weather_data or '-' in weather_data:
                # Format like "Sunny +25°C" or "Cloudy -5°F"
                parts = weather_data.split()
                if len(parts) >= 2:
                    condition = parts[0]
                    temp_part = parts[1]

                    # Clean up temperature - avoid "fahrenheit" which seems to cause issues
                    temp_clean = temp_part.replace('+', '').replace('°C', ' degrees celsius').replace('°F', ' degrees').replace('°', ' degrees')

                    return f"It's {condition.lower()} and {temp_clean}"

            # If we have any weather data, use it as-is
            if weather_data and len(weather_data) > 3:
                return f"The weather is {weather_data.lower()}"

            # Fallback
            return _get_weather_fallback()

        else:
            return "I'm sorry, I can't get the weather right now"

    except Exception as e:
        print(f"Error getting weather: {e}")
        return "I'm sorry, I can't get the weather right now"


def _get_weather_fallback():
    """Fallback weather method using simpler format"""
    try:
        # Try even simpler format
        url = "http://wttr.in/?format=%t"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            temp_data = response.text.strip()
            if temp_data and temp_data != "Unknown location;":
                temp_clean = temp_data.replace('+', '').replace('°C', ' degrees celsius').replace('°F', ' degrees').replace('°', ' degrees')
                return f"The temperature is {temp_clean}"

        # If all else fails, give a generic response
        return "The weather information is not available right now"

    except Exception as e:
        print(f"Fallback weather error: {e}")
        return "I can't get the weather information at the moment"