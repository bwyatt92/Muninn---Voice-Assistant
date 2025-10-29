#!/usr/bin/env python3

"""
Audio Management Module for Muninn
Handles audio recording and playback
"""

import os
import time
import wave
import subprocess
import pyaudio
import json
import sqlite3
import numpy as np
from typing import List, Optional, Dict

from config.settings import MuninnConfig

# Try to import soundfile for better audio format support
try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False
    print("⚠️  soundfile not available - using fallback audio playback")


class AudioManager:
    """Manages audio recording and playback operations"""

    def __init__(self, audio_device_index: Optional[int] = None, audio: Optional[pyaudio.PyAudio] = None):
        self.audio_device_index = audio_device_index
        self.audio = audio
        self.last_recording = None

        # SQLite database file (used by web portal)
        self.messages_db = "/home/bw/muninn/muninn-v3/messages.db"

        # JSON database file (legacy fallback)
        self.message_db_file = os.path.join(MuninnConfig.RECORDINGS_DIR, "messages.json")

        # Ensure recordings directory exists
        MuninnConfig.setup_directories()

        # Initialize message database
        self._init_message_db()

    def record_audio(self, duration: int = 10) -> Optional[str]:
        """
        Record audio using microphone

        Args:
            duration: Recording duration in seconds

        Returns:
            str: Path to recorded file, or None if failed
        """
        timestamp = int(time.time())
        filename = f"recording_{timestamp}.wav"
        filepath = os.path.join(MuninnConfig.RECORDINGS_DIR, filename)

        try:
            print(f"🎙️ Recording for {duration} seconds...")

            # Open recording stream
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,  # Mono
                rate=16000,  # Sample rate
                input=True,
                input_device_index=self.audio_device_index,
                frames_per_buffer=1024
            )

            frames = []
            start_time = time.time()

            # Record until duration
            while time.time() - start_time < duration:
                try:
                    data = stream.read(1024, exception_on_overflow=False)
                    frames.append(data)

                    # Show recording progress
                    elapsed = time.time() - start_time
                    remaining = duration - elapsed
                    print(f"\r🔴 Recording... {remaining:.1f}s remaining", end='', flush=True)

                except Exception as read_error:
                    print(f"\n❌ Recording read error: {read_error}")
                    break

            print("\n✅ Recording complete!")

            stream.stop_stream()
            stream.close()

            # Save to WAV file
            with wave.open(filepath, 'wb') as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(16000)
                wf.writeframes(b''.join(frames))

            print(f"💾 Saved recording: {filepath}")
            self.last_recording = filepath
            return filepath

        except Exception as e:
            print(f"❌ Recording error: {e}")
            return None

    def play_audio_file(self, filepath: str) -> bool:
        """
        Play audio file through speakers using PyAudio
        Supports multiple audio formats (WAV, WebM, MP3, etc.)

        Args:
            filepath: Path to audio file

        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(filepath):
            print(f"❌ Audio file not found: {filepath}")
            return False

        try:
            print(f"🔊 Playing: {os.path.basename(filepath)}")

            # Detect actual file format
            self._detect_file_format(filepath)

            # Try soundfile first (supports many formats)
            if SOUNDFILE_AVAILABLE:
                try:
                    result = self._play_with_soundfile(filepath)
                    if result:
                        return True
                    print(f"⚠️  Soundfile returned False")
                except Exception as e:
                    print(f"⚠️  Soundfile exception: {e}")

            # Try wave module (only for true WAV files)
            try:
                result = self._play_with_wave(filepath)
                if result:
                    return True
                print(f"⚠️  WAV module returned False")
            except Exception as e:
                print(f"⚠️  WAV module exception: {e}")

            # Try converting with ffmpeg first, then play
            print("🔄 Attempting ffmpeg conversion...")
            result = self._play_with_ffmpeg_conversion(filepath)
            if result:
                return True

            # Last resort - try subprocess playback
            print("🔄 Final attempt with subprocess...")
            return self._play_with_subprocess(filepath)

        except Exception as e:
            print(f"❌ Playback error: {e}")
            return False

    def _detect_file_format(self, filepath: str):
        """Detect and log the actual file format"""
        try:
            # Read first 12 bytes to detect format
            with open(filepath, 'rb') as f:
                header = f.read(12)

            if header.startswith(b'RIFF'):
                print(f"📄 File format: WAV (RIFF)")
            elif header.startswith(b'\x1a\x45\xdf\xa3'):
                print(f"📄 File format: WebM/Matroska")
            elif header.startswith(b'ID3') or header[0:2] == b'\xff\xfb':
                print(f"📄 File format: MP3")
            elif header.startswith(b'fLaC'):
                print(f"📄 File format: FLAC")
            elif header.startswith(b'OggS'):
                print(f"📄 File format: OGG")
            else:
                print(f"📄 File format: Unknown (header: {header[:4].hex()})")
        except Exception as e:
            print(f"⚠️  Could not detect format: {e}")

    def _play_with_soundfile(self, filepath: str) -> bool:
        """Play audio using soundfile library (supports multiple formats)"""
        try:
            # Read audio file
            data, sample_rate = sf.read(filepath, dtype='float32')

            # Convert to mono if stereo
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)

            # Convert to int16 for PyAudio
            audio_int16 = (data * 32767).astype(np.int16)

            # Open PyAudio stream
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                output=True,
                output_device_index=self.audio_device_index
            )

            # Play in chunks
            chunk_size = 1024
            for i in range(0, len(audio_int16), chunk_size):
                chunk = audio_int16[i:i+chunk_size]
                stream.write(chunk.tobytes())

            # Cleanup
            stream.stop_stream()
            stream.close()
            time.sleep(0.1)

            print("✅ Playback complete!")
            return True

        except Exception as e:
            print(f"❌ Soundfile playback error: {e}")
            return False

    def _play_with_wave(self, filepath: str) -> bool:
        """Play audio using wave module (WAV files only)"""
        # Open WAV file
        wf = wave.open(filepath, 'rb')

        # Open PyAudio stream
        stream = self.audio.open(
            format=self.audio.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True,
            output_device_index=self.audio_device_index
        )

        # Read and play audio in chunks
        chunk_size = 1024
        data = wf.readframes(chunk_size)

        while data:
            stream.write(data)
            data = wf.readframes(chunk_size)

        # Cleanup
        stream.stop_stream()
        stream.close()
        wf.close()
        time.sleep(0.1)

        print("✅ Playback complete!")
        return True

    def _play_with_ffmpeg_conversion(self, filepath: str) -> bool:
        """Convert audio to WAV using ffmpeg, then play"""
        import tempfile

        try:
            # Create temporary WAV file
            temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_wav_path = temp_wav.name
            temp_wav.close()

            print(f"🔄 Converting to WAV: {temp_wav_path}")

            # Convert using ffmpeg with explicit format detection
            # -vn: no video
            # -ar 16000: 16kHz sample rate
            # -ac 1: mono
            # -acodec pcm_s16le: standard PCM WAV format
            result = subprocess.run(
                ['ffmpeg', '-v', 'error', '-i', filepath, '-vn', '-ar', '16000', '-ac', '1', '-acodec', 'pcm_s16le', '-y', temp_wav_path],
                capture_output=True,
                timeout=30,
                text=True
            )

            if result.returncode != 0:
                stderr = result.stderr.strip()
                print(f"❌ FFmpeg conversion failed (code {result.returncode}): {stderr}")
                try:
                    os.unlink(temp_wav_path)
                except:
                    pass
                return False

            # Check if output file was created and has content
            if not os.path.exists(temp_wav_path) or os.path.getsize(temp_wav_path) == 0:
                print(f"❌ FFmpeg output file is empty or missing")
                try:
                    os.unlink(temp_wav_path)
                except:
                    pass
                return False

            print(f"✅ Conversion successful ({os.path.getsize(temp_wav_path)} bytes), playing...")

            # Now play the converted WAV file
            success = False
            try:
                success = self._play_with_wave(temp_wav_path)
            except Exception as e:
                print(f"⚠️  Wave playback of converted file failed: {e}")
                # If wave fails, try soundfile on the converted file
                if SOUNDFILE_AVAILABLE:
                    try:
                        success = self._play_with_soundfile(temp_wav_path)
                    except Exception as e2:
                        print(f"⚠️  Soundfile playback of converted file failed: {e2}")

            # Clean up temp file
            try:
                os.unlink(temp_wav_path)
            except:
                pass

            return success

        except subprocess.TimeoutExpired:
            print(f"❌ FFmpeg conversion timed out")
            return False
        except Exception as e:
            print(f"❌ FFmpeg conversion error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _play_with_subprocess(self, filepath: str) -> bool:
        """Fallback: play using aplay/ffplay subprocess"""
        try:
            # Try aplay first
            result = subprocess.run(
                ['aplay', filepath],
                capture_output=True,
                timeout=60
            )

            if result.returncode == 0:
                print("✅ Playback complete!")
                time.sleep(0.1)
                return True

            # Try ffplay as fallback
            result = subprocess.run(
                ['ffplay', '-nodisp', '-autoexit', filepath],
                capture_output=True,
                timeout=60
            )

            if result.returncode == 0:
                print("✅ Playback complete!")
                time.sleep(0.1)
                return True

            return False

        except Exception as e:
            print(f"❌ Subprocess playback error: {e}")
            return False

    def get_recent_recordings(self, count: int = 5) -> List[str]:
        """
        Get list of recent recordings

        Args:
            count: Number of recent recordings to return

        Returns:
            List of file paths
        """
        try:
            recordings = []
            for filename in os.listdir(MuninnConfig.RECORDINGS_DIR):
                if filename.endswith('.wav'):
                    filepath = os.path.join(MuninnConfig.RECORDINGS_DIR, filename)
                    recordings.append(filepath)

            # Sort by modification time (newest first)
            recordings.sort(key=os.path.getmtime, reverse=True)
            return recordings[:count]

        except Exception as e:
            print(f"❌ Error getting recordings: {e}")
            return []

    def get_last_recording(self) -> Optional[str]:
        """Get the path to the last recording"""
        return self.last_recording

    def _init_message_db(self):
        """Initialize the message database"""
        if not os.path.exists(self.message_db_file):
            # Create empty database
            self._save_message_db({})

    def _load_message_db(self) -> Dict:
        """Load the message database"""
        try:
            with open(self.message_db_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_message_db(self, db: Dict):
        """Save the message database"""
        try:
            with open(self.message_db_file, 'w') as f:
                json.dump(db, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving message database: {e}")

    def save_message_for_person(self, person: str, recording_path: str, description: str = "") -> bool:
        """
        Save a message for a specific family member

        Args:
            person: Family member name
            recording_path: Path to the audio file
            description: Optional description of the message

        Returns:
            bool: True if successful
        """
        try:
            db = self._load_message_db()

            if person not in db:
                db[person] = []

            message_entry = {
                "file_path": recording_path,
                "description": description,
                "timestamp": time.time(),
                "duration": self._get_audio_duration(recording_path)
            }

            db[person].append(message_entry)
            self._save_message_db(db)

            print(f"💾 Saved message for {person}: {os.path.basename(recording_path)}")
            return True

        except Exception as e:
            print(f"❌ Error saving message for {person}: {e}")
            return False

    def get_messages_for_person(self, person: str) -> List[Dict]:
        """
        Get all messages for a specific family member

        Args:
            person: Family member name

        Returns:
            List of message dictionaries
        """
        # Try SQLite first (web portal database)
        try:
            if os.path.exists(self.messages_db):
                conn = sqlite3.connect(self.messages_db)
                conn.row_factory = sqlite3.Row  # Enable column access by name
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT id, person, file_path, description, created_at, file_size, duration
                    FROM messages
                    WHERE LOWER(person) = LOWER(?)
                    ORDER BY created_at DESC
                ''', (person,))

                rows = cursor.fetchall()
                conn.close()

                # Convert to list of dicts
                messages = []
                for row in rows:
                    messages.append({
                        'id': row['id'],
                        'person': row['person'],
                        'file_path': row['file_path'],
                        'description': row['description'],
                        'timestamp': row['created_at'],
                        'file_size': row['file_size'],
                        'duration': row['duration'] or 0.0
                    })

                if messages:
                    print(f"Found {len(messages)} messages for {person} in SQLite database")
                    return messages
        except Exception as e:
            print(f"Error reading from SQLite: {e}")

        # Fallback to JSON
        db = self._load_message_db()
        json_messages = db.get(person.lower(), [])
        if json_messages:
            print(f"Found {len(json_messages)} messages for {person} in JSON database")
        return json_messages

    def get_all_family_members_with_messages(self) -> List[str]:
        """
        Get list of all family members who have messages

        Returns:
            List of family member names
        """
        # Try SQLite first
        try:
            if os.path.exists(self.messages_db):
                conn = sqlite3.connect(self.messages_db)
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT DISTINCT LOWER(person) as person
                    FROM messages
                    ORDER BY person
                ''')

                rows = cursor.fetchall()
                conn.close()

                family_members = [row[0] for row in rows]
                if family_members:
                    print(f"Found messages for {len(family_members)} family members in SQLite")
                    return family_members
        except Exception as e:
            print(f"Error reading family members from SQLite: {e}")

        # Fallback to JSON
        db = self._load_message_db()
        return [person for person, messages in db.items() if messages]

    def get_message_count_by_person(self) -> Dict[str, int]:
        """
        Get count of messages for each family member

        Returns:
            Dictionary mapping person to message count
        """
        # Try SQLite first
        try:
            if os.path.exists(self.messages_db):
                conn = sqlite3.connect(self.messages_db)
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT LOWER(person) as person, COUNT(*) as count
                    FROM messages
                    GROUP BY LOWER(person)
                    ORDER BY person
                ''')

                rows = cursor.fetchall()
                conn.close()

                counts = {row[0]: row[1] for row in rows}
                if counts:
                    print(f"Found message counts for {len(counts)} family members in SQLite")
                    return counts
        except Exception as e:
            print(f"Error reading message counts from SQLite: {e}")

        # Fallback to JSON
        db = self._load_message_db()
        return {person: len(messages) for person, messages in db.items()}

    def _get_audio_duration(self, filepath: str) -> float:
        """Get duration of audio file in seconds"""
        try:
            with wave.open(filepath, 'rb') as wf:
                frames = wf.getnframes()
                sample_rate = wf.getframerate()
                return frames / float(sample_rate)
        except Exception:
            return 0.0


class MockAudioManager:
    """Mock audio manager for testing"""

    def __init__(self, audio_device_index: Optional[int] = None, audio: Optional[pyaudio.PyAudio] = None):
        self.last_recording = None
        # Mock message database
        self.mock_messages = {
            "dad": [
                {"file_path": "/tmp/mock_dad_message1.wav", "description": "Birthday message", "timestamp": time.time(), "duration": 10.0},
                {"file_path": "/tmp/mock_dad_message2.wav", "description": "Another message", "timestamp": time.time(), "duration": 8.5}
            ],
            "mom": [
                {"file_path": "/tmp/mock_mom_message1.wav", "description": "Sweet message", "timestamp": time.time(), "duration": 12.0}
            ],
            "carrie": [
                {"file_path": "/tmp/mock_carrie_message1.wav", "description": "Family message", "timestamp": time.time(), "duration": 9.0}
            ]
        }
        print("Mock audio manager initialized")

    def record_audio(self, duration: int = 10) -> Optional[str]:
        """Mock audio recording"""
        print(f"🎙️ [MOCK] Recording for {duration} seconds...")
        time.sleep(2)  # Simulate recording time
        mock_file = "/tmp/mock_recording.wav"
        self.last_recording = mock_file
        print(f"💾 [MOCK] Saved recording: {mock_file}")
        return mock_file

    def play_audio_file(self, filepath: str) -> bool:
        """Mock audio playback"""
        print(f"🔊 [MOCK] Playing: {os.path.basename(filepath)}")
        time.sleep(1)  # Simulate playback time
        print("✅ [MOCK] Playback complete!")
        return True

    def get_recent_recordings(self, count: int = 5) -> List[str]:
        """Mock recent recordings"""
        return ["/tmp/mock_recording1.wav", "/tmp/mock_recording2.wav"]

    def get_last_recording(self) -> Optional[str]:
        """Get mock last recording"""
        return self.last_recording

    def save_message_for_person(self, person: str, recording_path: str, description: str = "") -> bool:
        """Mock save message"""
        print(f"💾 [MOCK] Saved message for {person}: {os.path.basename(recording_path)}")
        return True

    def get_messages_for_person(self, person: str) -> List[Dict]:
        """Mock get messages for person"""
        return self.mock_messages.get(person.lower(), [])

    def get_all_family_members_with_messages(self) -> List[str]:
        """Mock get all family members"""
        return list(self.mock_messages.keys())

    def get_message_count_by_person(self) -> Dict[str, int]:
        """Mock get message counts"""
        return {person: len(messages) for person, messages in self.mock_messages.items()}


def get_audio_manager(audio_device_index: Optional[int] = None, audio: Optional[pyaudio.PyAudio] = None, mock_mode: bool = False) -> AudioManager:
    """
    Factory function to get appropriate audio manager

    Args:
        audio_device_index: Audio device index
        audio: PyAudio instance
        mock_mode: Use mock manager instead of real manager

    Returns:
        AudioManager instance
    """
    if mock_mode:
        return MockAudioManager(audio_device_index, audio)

    return AudioManager(audio_device_index, audio)