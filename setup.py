#!/usr/bin/env python3

"""
Setup script for Muninn Modular Voice Assistant
"""

import os
import sys
import subprocess


def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False


def setup_directories():
    """Create required directories"""
    directories = [
        "./recordings",
        "./models"
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")


def main():
    """Main setup function"""
    print("🧙‍♂️ Setting up Muninn Modular Voice Assistant")
    print("=" * 50)

    # Create directories
    setup_directories()

    # Install Python dependencies
    if not run_command("pip3 install -r requirements.txt", "Installing Python dependencies"):
        print("❌ Failed to install dependencies")
        return 1

    # Install KittenTTS
    kittentts_url = "https://github.com/KittenML/KittenTTS/releases/download/0.1/kittentts-0.1.0-py3-none-any.whl"
    if not run_command(f"pip3 install {kittentts_url}", "Installing KittenTTS"):
        print("⚠️ KittenTTS installation failed, but continuing...")

    print("\n🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Copy your wake word model (munin_en_raspberry-pi_v3_0_0.ppn) to this directory")
    print("2. Copy your Vosk model to ./vosk-model-small-en-us-0.15")
    print("3. Run: python3 muninn.py")
    print("4. For testing without hardware: python3 muninn.py --mock")

    return 0


if __name__ == "__main__":
    sys.exit(main())