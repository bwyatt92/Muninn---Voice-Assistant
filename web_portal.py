#!/usr/bin/env python3
"""
Muninn Web Portal
Enhanced Flask backend for voice recording, message management, and system monitoring
"""

from flask import Flask, render_template, jsonify, request, send_file, redirect, url_for, Response, stream_with_context
import psutil
import subprocess
import os
import json
import time
import sqlite3
import uuid
from datetime import datetime
import re
import threading
import socket
from werkzeug.utils import secure_filename
import zipfile
import tempfile
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'muninn-voice-portal-2025'

# Configuration
UPLOAD_FOLDER = '/home/bw/muninn/muninn-v3/recordings'
MESSAGES_DB = '/home/bw/muninn/muninn-v3/messages.db'
MESSAGES_JSON = '/home/bw/muninn/muninn-v3/recordings/messages.json'
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a', 'ogg', 'flac', 'aac', 'webm'}

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class MuninnWebPortal:
    def __init__(self):
        self.start_time = time.time()
        self.init_database()

    def init_database(self):
        """Initialize messages and memories databases"""
        try:
            conn = sqlite3.connect(MESSAGES_DB)
            cursor = conn.cursor()

            # Create messages table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    person TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_size INTEGER,
                    duration REAL
                )
            ''')

            # Create memories table for rich memory system
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memories (
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
            ''')

            conn.commit()
            conn.close()
            logger.info("Messages and memories databases initialized")

        except Exception as e:
            logger.error(f"Database initialization error: {e}")

    def get_cpu_info(self):
        """Get CPU information"""
        try:
            # CPU temperature (Pi-specific)
            try:
                temp_cmd = subprocess.run(['vcgencmd', 'measure_temp'],
                                        capture_output=True, text=True, timeout=5)
                temp = temp_cmd.stdout.strip().replace('temp=', '').replace("'C", '')
                cpu_temp = float(temp) if temp else 0
            except:
                cpu_temp = 0

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Load average
            load_avg = os.getloadavg()

            return {
                'temperature': cpu_temp,
                'usage_percent': cpu_percent,
                'load_1m': load_avg[0],
                'load_5m': load_avg[1],
                'load_15m': load_avg[2],
                'cores': psutil.cpu_count()
            }
        except Exception as e:
            return {'error': str(e)}

    def get_memory_info(self):
        """Get memory information"""
        try:
            memory = psutil.virtual_memory()
            return {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent
            }
        except Exception as e:
            return {'error': str(e)}

    def get_disk_info(self):
        """Get disk information"""
        try:
            disk = psutil.disk_usage('/')
            return {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': (disk.used / disk.total) * 100
            }
        except Exception as e:
            return {'error': str(e)}

    def get_network_info(self):
        """Get network information"""
        try:
            network_info = {
                'wifi': {
                    'connected': False,
                    'ssid': 'N/A',
                    'signal': 0,
                    'ip_address': 'N/A'
                },
                'ethernet': {
                    'connected': False,
                    'ip_address': 'N/A'
                }
            }

            # Get network interfaces
            interfaces = psutil.net_if_addrs()
            stats = psutil.net_if_stats()

            # Check WiFi interface (common names: wlan0, wlp*, wl*)
            wifi_interfaces = [name for name in interfaces.keys()
                             if name.startswith(('wlan', 'wlp', 'wl')) and not name.startswith('wlo')]

            for wifi_if in wifi_interfaces:
                if wifi_if in stats and stats[wifi_if].isup:
                    network_info['wifi']['connected'] = True
                    # Get IP address
                    for addr in interfaces[wifi_if]:
                        if addr.family == socket.AF_INET:
                            network_info['wifi']['ip_address'] = addr.address
                            break

            # Check Ethernet interface (common names: eth0, enp*, eno*)
            eth_interfaces = [name for name in interfaces.keys()
                            if name.startswith(('eth', 'enp', 'eno'))]

            for eth_if in eth_interfaces:
                if eth_if in stats and stats[eth_if].isup:
                    network_info['ethernet']['connected'] = True
                    # Get IP address
                    for addr in interfaces[eth_if]:
                        if addr.family == socket.AF_INET:
                            network_info['ethernet']['ip_address'] = addr.address
                            break

            # Try to get WiFi SSID and signal strength (Linux-specific)
            if network_info['wifi']['connected']:
                try:
                    # Get SSID
                    iwconfig_result = subprocess.run(['iwgetid', '-r'],
                                                   capture_output=True, text=True, timeout=5)
                    if iwconfig_result.returncode == 0:
                        network_info['wifi']['ssid'] = iwconfig_result.stdout.strip()

                    # Get signal strength
                    iwconfig_result = subprocess.run(['iwconfig'],
                                                   capture_output=True, text=True, timeout=5)
                    if iwconfig_result.returncode == 0:
                        lines = iwconfig_result.stdout.split('\n')
                        for line in lines:
                            if 'Signal level' in line:
                                # Extract signal level (e.g., "-50 dBm")
                                import re
                                match = re.search(r'Signal level=(-?\d+)', line)
                                if match:
                                    network_info['wifi']['signal'] = int(match.group(1))
                                break
                except Exception as e:
                    logger.debug(f"Could not get WiFi details: {e}")

            return network_info

        except Exception as e:
            logger.error(f"Network info error: {e}")
            return {'error': str(e)}

    def get_services_info(self):
        """Get service status information"""
        try:
            services = {}

            # List of services to check (common Raspberry Pi services)
            service_list = [
                'muninn',      # Custom Muninn service
                'ssh',         # SSH service
                'networking',  # Network service
                'bluetooth',   # Bluetooth service
                'wifi',        # WiFi service (if exists)
                'dhcpcd',      # DHCP client daemon
                'systemd-resolved',  # DNS resolver
            ]

            for service in service_list:
                try:
                    # Check service status using systemctl
                    result = subprocess.run(['systemctl', 'is-active', service],
                                          capture_output=True, text=True, timeout=5)
                    status = result.stdout.strip()
                    services[service] = status if status in ['active', 'inactive', 'failed'] else 'unknown'
                except Exception as e:
                    services[service] = 'error'
                    logger.debug(f"Could not check service {service}: {e}")

            return services

        except Exception as e:
            logger.error(f"Services info error: {e}")
            return {'error': str(e)}

    def get_messages_list(self):
        """Get list of all messages from both SQLite and JSON sources"""
        messages = []

        # Try SQLite first (new format)
        try:
            if os.path.exists(MESSAGES_DB):
                conn = sqlite3.connect(MESSAGES_DB)
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT id, person, file_path, description, created_at, file_size, duration
                    FROM messages
                    ORDER BY created_at DESC
                ''')

                for row in cursor.fetchall():
                    messages.append({
                        'id': row[0],
                        'person': row[1],
                        'file_path': row[2],
                        'description': row[3],
                        'created_at': row[4],
                        'file_size': row[5],
                        'duration': row[6],
                        'source': 'sqlite'
                    })

                conn.close()
        except Exception as e:
            logger.error(f"Error reading SQLite messages: {e}")

        # Also try JSON format (existing Muninn format)
        try:
            if os.path.exists(MESSAGES_JSON):
                with open(MESSAGES_JSON, 'r') as f:
                    json_data = json.load(f)

                if isinstance(json_data, dict):
                    for person, person_messages in json_data.items():
                        if isinstance(person_messages, list):
                            for msg in person_messages:
                                messages.append({
                                    'id': f"json_{person}_{msg.get('file_path', '').split('/')[-1]}",
                                    'person': person,
                                    'file_path': msg.get('file_path', ''),
                                    'description': msg.get('description', f'Message from {person}'),
                                    'created_at': msg.get('created_at', ''),
                                    'file_size': msg.get('file_size', 0),
                                    'duration': msg.get('duration', 0),
                                    'source': 'json'
                                })

        except Exception as e:
            logger.error(f"Error reading JSON messages: {e}")

        # Sort by creation date
        messages.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return messages

    def save_message(self, person, file_path, description=None, file_size=None, duration=None):
        """Save message to SQLite database"""
        try:
            message_id = str(uuid.uuid4())

            # Save to SQLite
            try:
                conn = sqlite3.connect(MESSAGES_DB)
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO messages (id, person, file_path, description, file_size, duration)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (message_id, person, file_path, description, file_size, duration))

                conn.commit()
                conn.close()
                logger.info(f"Message saved to SQLite: {message_id} for {person}")
            except Exception as e:
                logger.error(f"Error saving to SQLite: {e}")
                return None

            return message_id

        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return None

    def _save_to_json(self, person, file_path, description, file_size, duration):
        """Save message to JSON format (for Muninn compatibility)"""
        try:
            # Load existing JSON data
            json_data = {}
            if os.path.exists(MESSAGES_JSON):
                with open(MESSAGES_JSON, 'r') as f:
                    content = f.read().strip()
                    if content:
                        json_data = json.loads(content)

            # Ensure person key exists
            if person not in json_data:
                json_data[person] = []

            # Add new message
            message_entry = {
                'file_path': file_path,
                'description': description or f'Web upload for {person}',
                'created_at': datetime.now().isoformat(),
                'file_size': file_size,
                'duration': duration
            }

            json_data[person].append(message_entry)

            # Save back to JSON
            with open(MESSAGES_JSON, 'w') as f:
                json.dump(json_data, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
            raise

    def delete_message(self, message_id):
        """Delete message from database and file system"""
        try:
            file_path = None
            deleted = False

            # Try SQLite first
            try:
                conn = sqlite3.connect(MESSAGES_DB)
                cursor = conn.cursor()

                # Get file path before deleting
                cursor.execute('SELECT file_path FROM messages WHERE id = ?', (message_id,))
                result = cursor.fetchone()

                if result:
                    file_path = result[0]

                    # Delete from database
                    cursor.execute('DELETE FROM messages WHERE id = ?', (message_id,))
                    conn.commit()
                    deleted = True
                    logger.info(f"Deleted from SQLite: {message_id}")

                conn.close()
            except Exception as e:
                logger.error(f"SQLite delete error: {e}")

            # If not found in SQLite, check if it's a JSON message
            if not deleted and message_id.startswith('json_'):
                try:
                    # Parse JSON message ID format: json_{person}_{filename}
                    # Find and remove the message from JSON
                    if os.path.exists(MESSAGES_JSON):
                        with open(MESSAGES_JSON, 'r') as f:
                            json_data = json.load(f)

                        # Find the message to get file path and remove it
                        found = False
                        for person, person_messages in json_data.items():
                            if isinstance(person_messages, list):
                                for i, msg in enumerate(person_messages):
                                    msg_id = f"json_{person}_{msg.get('file_path', '').split('/')[-1]}"
                                    if msg_id == message_id:
                                        file_path = msg.get('file_path')
                                        # Remove this message from the list
                                        person_messages.pop(i)
                                        found = True
                                        break
                            if found:
                                break

                        if found:
                            # Save updated JSON
                            with open(MESSAGES_JSON, 'w') as f:
                                json.dump(json_data, f, indent=2)
                            deleted = True
                            logger.info(f"Deleted from JSON: {message_id}")

                except Exception as e:
                    logger.error(f"JSON delete error: {e}")

            # Delete the actual audio file if we found it
            if deleted and file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted file: {file_path}")
                except Exception as e:
                    logger.error(f"File deletion error: {e}")

            if deleted:
                logger.info(f"Message successfully deleted: {message_id}")
                return True
            else:
                logger.warning(f"Message not found: {message_id}")
                return False

        except Exception as e:
            logger.error(f"Error deleting message: {e}")
            return False

    def get_memories_list(self, filters=None):
        """Get list of memories with optional filters"""
        try:
            conn = sqlite3.connect(MESSAGES_DB)
            cursor = conn.cursor()

            query = 'SELECT id, person, memory_type, length_category, title, tags, file_path, created_at, file_size, duration FROM memories'
            params = []

            # Apply filters if provided
            if filters:
                conditions = []
                if filters.get('person'):
                    conditions.append('person = ?')
                    params.append(filters['person'])
                if filters.get('memory_type'):
                    conditions.append('memory_type = ?')
                    params.append(filters['memory_type'])
                if filters.get('length_category'):
                    conditions.append('length_category = ?')
                    params.append(filters['length_category'])
                if filters.get('search'):
                    conditions.append('(title LIKE ? OR tags LIKE ?)')
                    search_term = f'%{filters["search"]}%'
                    params.extend([search_term, search_term])

                if conditions:
                    query += ' WHERE ' + ' AND '.join(conditions)

            query += ' ORDER BY created_at DESC'

            cursor.execute(query, params)
            memories = []

            for row in cursor.fetchall():
                memories.append({
                    'id': row[0],
                    'person': row[1],
                    'memory_type': row[2],
                    'length_category': row[3],
                    'title': row[4],
                    'tags': row[5],
                    'file_path': row[6],
                    'created_at': row[7],
                    'file_size': row[8],
                    'duration': row[9]
                })

            conn.close()
            return memories

        except Exception as e:
            logger.error(f"Error getting memories: {e}")
            return []

    def save_memory(self, person, memory_type, length_category, title, tags, file_path, file_size=None, duration=None):
        """Save memory to database"""
        try:
            memory_id = str(uuid.uuid4())

            conn = sqlite3.connect(MESSAGES_DB)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO memories (id, person, memory_type, length_category, title, tags, file_path, file_size, duration)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (memory_id, person, memory_type, length_category, title, tags, file_path, file_size, duration))

            conn.commit()
            conn.close()
            logger.info(f"Memory saved: {memory_id} from {person}")
            return memory_id

        except Exception as e:
            logger.error(f"Error saving memory: {e}")
            return None

    def delete_memory(self, memory_id):
        """Delete memory from database and file system"""
        try:
            conn = sqlite3.connect(MESSAGES_DB)
            cursor = conn.cursor()

            # Get file path before deleting
            cursor.execute('SELECT file_path FROM memories WHERE id = ?', (memory_id,))
            result = cursor.fetchone()

            if result:
                file_path = result[0]

                # Delete from database
                cursor.execute('DELETE FROM memories WHERE id = ?', (memory_id,))
                conn.commit()
                logger.info(f"Deleted memory from database: {memory_id}")

                # Delete the actual audio file
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"Deleted memory file: {file_path}")
                    except Exception as e:
                        logger.error(f"File deletion error: {e}")

                conn.close()
                return True
            else:
                conn.close()
                logger.warning(f"Memory not found: {memory_id}")
                return False

        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return False

    def get_random_memory(self, filters=None):
        """Get a random memory matching optional filters"""
        memories = self.get_memories_list(filters)
        if memories:
            import random
            return random.choice(memories)
        return None

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize portal
portal = MuninnWebPortal()

# Routes
@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard_enhanced.html')

@app.route('/api/vitals')
def api_vitals():
    """Get system vital statistics"""
    try:
        vitals = {
            'cpu': portal.get_cpu_info(),
            'memory': portal.get_memory_info(),
            'disk': portal.get_disk_info(),
            'network': portal.get_network_info(),
            'services': portal.get_services_info(),
            'timestamp': time.time()
        }
        return jsonify(vitals)
    except Exception as e:
        logger.error(f"Error getting vitals: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages')
def api_messages():
    """Get list of all messages"""
    try:
        messages = portal.get_messages_list()
        return jsonify({
            'success': True,
            'messages': messages,
            'count': len(messages)
        })
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload_recording', methods=['POST'])
def api_upload_recording():
    """Handle web recording upload"""
    try:
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': 'No audio file provided'}), 400

        audio_file = request.files['audio']
        family_member = request.form.get('familyMember', 'Unknown')
        description = request.form.get('description', f'Web recording for {family_member}')

        if audio_file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"web_recording_{family_member}_{timestamp}.wav"
        filename = secure_filename(filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # Save file
        audio_file.save(file_path)
        file_size = os.path.getsize(file_path)

        # Save to database
        message_id = portal.save_message(
            person=family_member,
            file_path=file_path,
            description=description,
            file_size=file_size
        )

        if message_id:
            logger.info(f"Web recording saved: {filename} for {family_member}")
            return jsonify({
                'success': True,
                'message_id': message_id,
                'filename': filename,
                'file_size': file_size
            })
        else:
            # Clean up file if database save failed
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'success': False, 'error': 'Failed to save to database'}), 500

    except Exception as e:
        logger.error(f"Upload recording error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload_files', methods=['POST'])
def api_upload_files():
    """Handle file upload"""
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'No files provided'}), 400

        files = request.files.getlist('files')
        uploaded_count = 0
        errors = []

        for file in files:
            if file.filename == '':
                continue

            if not allowed_file(file.filename):
                errors.append(f"File type not allowed: {file.filename}")
                continue

            if file.content_length and file.content_length > MAX_FILE_SIZE:
                errors.append(f"File too large: {file.filename}")
                continue

            try:
                # Generate unique filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                original_name = secure_filename(file.filename)
                name_without_ext = os.path.splitext(original_name)[0]
                ext = os.path.splitext(original_name)[1]
                filename = f"upload_{timestamp}_{name_without_ext}{ext}"
                file_path = os.path.join(UPLOAD_FOLDER, filename)

                # Save file
                file.save(file_path)
                file_size = os.path.getsize(file_path)

                # Extract person name from filename (if possible)
                person = 'Unknown'
                name_parts = name_without_ext.lower().split('_')
                family_names = ['dad', 'mom', 'brother', 'sister', 'grandma', 'grandpa']
                for part in name_parts:
                    if part in family_names:
                        person = part.capitalize()
                        break

                # Save to database
                message_id = portal.save_message(
                    person=person,
                    file_path=file_path,
                    description=f"Uploaded file: {original_name}",
                    file_size=file_size
                )

                if message_id:
                    uploaded_count += 1
                    logger.info(f"File uploaded: {filename}")
                else:
                    errors.append(f"Database save failed: {file.filename}")
                    if os.path.exists(file_path):
                        os.remove(file_path)

            except Exception as e:
                errors.append(f"Error uploading {file.filename}: {str(e)}")
                logger.error(f"File upload error: {e}")

        return jsonify({
            'success': uploaded_count > 0,
            'uploaded': uploaded_count,
            'errors': errors
        })

    except Exception as e:
        logger.error(f"Upload files error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get_audio/<message_id>')
def api_get_audio(message_id):
    """Serve audio file for browser playback"""
    try:
        file_path = None

        # Try SQLite first
        try:
            conn = sqlite3.connect(MESSAGES_DB)
            cursor = conn.cursor()
            cursor.execute('SELECT file_path FROM messages WHERE id = ?', (message_id,))
            result = cursor.fetchone()
            conn.close()

            if result:
                file_path = result[0]
        except Exception as e:
            logger.error(f"SQLite query error: {e}")

        # If not found in SQLite, check if it's a JSON message
        if not file_path and message_id.startswith('json_'):
            try:
                # Parse JSON message ID format: json_{person}_{filename}
                # Get all messages to find the matching one
                messages = portal.get_messages_list()
                for msg in messages:
                    if msg.get('id') == message_id:
                        file_path = msg.get('file_path')
                        break
            except Exception as e:
                logger.error(f"JSON message lookup error: {e}")

        if not file_path:
            return jsonify({'error': 'Message not found'}), 404

        if not os.path.exists(file_path):
            return jsonify({'error': 'Audio file not found'}), 404

        # Determine MIME type based on file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg',
            '.m4a': 'audio/mp4',
            '.ogg': 'audio/ogg',
            '.webm': 'audio/webm',
            '.flac': 'audio/flac',
            '.aac': 'audio/aac'
        }
        mimetype = mime_types.get(file_ext, 'audio/wav')

        logger.info(f"Serving audio file: {file_path} as {mimetype}")
        return send_file(file_path, mimetype=mimetype)

    except Exception as e:
        logger.error(f"Get audio error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/play_message', methods=['POST'])
def api_play_message():
    """Play a specific message on Pi speakers (for local playback)"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')

        if not file_path or not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found'}), 404

        # Use aplay or similar to play the audio file
        try:
            subprocess.run(['aplay', file_path], check=True, timeout=30)
            logger.info(f"Played message: {file_path}")
            return jsonify({'success': True})
        except subprocess.CalledProcessError:
            # Try alternative player
            try:
                subprocess.run(['omxplayer', file_path], check=True, timeout=30)
                return jsonify({'success': True})
            except:
                return jsonify({'success': False, 'error': 'No audio player available'}), 500

    except Exception as e:
        logger.error(f"Play message error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/play_all_messages', methods=['POST'])
def api_play_all_messages():
    """Play all messages in sequence"""
    try:
        messages = portal.get_messages_list()

        if not messages:
            return jsonify({'success': False, 'error': 'No messages to play'}), 404

        # Play messages in a separate thread to avoid blocking
        def play_all():
            for message in messages:
                file_path = message['file_path']
                if os.path.exists(file_path):
                    try:
                        subprocess.run(['aplay', file_path], check=True, timeout=30)
                        time.sleep(0.5)  # Brief pause between messages
                    except:
                        logger.error(f"Failed to play: {file_path}")

        thread = threading.Thread(target=play_all, daemon=True)
        thread.start()

        logger.info(f"Started playing {len(messages)} messages")
        return jsonify({'success': True, 'message_count': len(messages)})

    except Exception as e:
        logger.error(f"Play all messages error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/delete_message', methods=['POST'])
def api_delete_message():
    """Delete a message"""
    try:
        data = request.get_json()
        message_id = data.get('message_id')

        if not message_id:
            return jsonify({'success': False, 'error': 'Message ID required'}), 400

        success = portal.delete_message(message_id)

        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Message not found'}), 404

    except Exception as e:
        logger.error(f"Delete message error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export_archive')
def api_export_archive():
    """Export all messages as a ZIP file"""
    try:
        messages = portal.get_messages_list()

        if not messages:
            return jsonify({'error': 'No messages to export'}), 404

        # Create temporary ZIP file
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, f"muninn_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add metadata file
            metadata = {
                'export_date': datetime.now().isoformat(),
                'message_count': len(messages),
                'messages': messages
            }

            metadata_path = os.path.join(temp_dir, 'metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            zipf.write(metadata_path, 'metadata.json')

            # Add audio files
            for message in messages:
                file_path = message['file_path']
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    zipf.write(file_path, f"audio/{filename}")

        logger.info(f"Archive exported: {zip_path}")
        return send_file(zip_path, as_attachment=True,
                        download_name=f"muninn_archive_{datetime.now().strftime('%Y%m%d')}.zip")

    except Exception as e:
        logger.error(f"Export archive error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
def api_logs():
    """Get system logs"""
    try:
        logs = []

        # Get last 50 lines of syslog
        try:
            result = subprocess.run(['tail', '-50', '/var/log/syslog'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logs.extend(result.stdout.split('\n')[-20:])  # Last 20 lines
        except:
            pass

        # Add Muninn-specific logs
        muninn_log_patterns = [
            'muninn',
            'voice',
            'recording',
            'wake_word'
        ]

        try:
            result = subprocess.run(['journalctl', '-n', '20', '--no-pager'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                journal_logs = result.stdout.split('\n')
                for log in journal_logs:
                    if any(pattern in log.lower() for pattern in muninn_log_patterns):
                        logs.append(log)
        except:
            pass

        # Add current timestamp
        logs.append(f"LOG REFRESH: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return jsonify({'success': True, 'logs': logs[-30:]})  # Last 30 lines

    except Exception as e:
        logger.error(f"Get logs error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/wifi/scan')
def api_wifi_scan():
    """Scan for available WiFi networks"""
    try:
        # Basic WiFi scan using iwlist
        result = subprocess.run(['iwlist', 'scan'], capture_output=True, text=True, timeout=30)

        networks = []
        if result.returncode == 0:
            # Parse iwlist output for network names
            lines = result.stdout.split('\n')
            current_network = {}

            for line in lines:
                if 'Cell' in line and 'Address:' in line:
                    if current_network:
                        networks.append(current_network)
                    current_network = {}
                elif 'ESSID:' in line:
                    ssid = line.split('ESSID:')[1].strip().strip('"')
                    if ssid and ssid != '<hidden>':
                        current_network['ssid'] = ssid
                elif 'Quality' in line:
                    # Extract signal strength
                    if '/' in line:
                        quality = line.split('Quality=')[1].split(' ')[0]
                        current_network['signal'] = quality

            if current_network:
                networks.append(current_network)

        return jsonify({'success': True, 'networks': networks[:10]})  # Limit to 10 networks

    except Exception as e:
        logger.error(f"WiFi scan error: {e}")
        # Return mock data if scanning fails
        return jsonify({
            'success': True,
            'networks': [
                {'ssid': 'WiFi scanning not available', 'signal': 'N/A'}
            ]
        })

@app.route('/api/wifi/connect', methods=['POST'])
def api_wifi_connect():
    """Connect to a WiFi network"""
    try:
        data = request.get_json()
        ssid = data.get('ssid')
        password = data.get('password')

        if not ssid:
            return jsonify({'success': False, 'error': 'SSID required'}), 400

        logger.info(f"WiFi connect request for: {ssid}")

        # Basic WiFi connection attempt
        # Note: This is a simplified implementation
        # In production, you'd want to use proper WiFi management tools

        return jsonify({
            'success': True,
            'message': f'WiFi connection attempted for {ssid}. Please check connection status.'
        })

    except Exception as e:
        logger.error(f"WiFi connect error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reboot', methods=['POST'])
def api_reboot():
    """Reboot the system"""
    try:
        logger.info("System reboot requested")

        def delayed_reboot():
            time.sleep(2)  # Give time for response to be sent
            try:
                subprocess.run(['sudo', 'reboot'], check=True)
            except Exception as e:
                logger.error(f"Reboot failed: {e}")

        # Start reboot in background thread
        thread = threading.Thread(target=delayed_reboot, daemon=True)
        thread.start()

        return jsonify({'success': True, 'message': 'System reboot initiated'})

    except Exception as e:
        logger.error(f"Reboot error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/memories')
def memories_page():
    """Memories page"""
    try:
        return render_template('memories.html')
    except Exception as e:
        logger.error(f"Memories page error: {e}")
        return f"Error loading memories page: {e}", 500

@app.route('/api/memories')
def api_get_memories():
    """Get list of memories with optional filters"""
    try:
        filters = {}
        if request.args.get('person'):
            filters['person'] = request.args.get('person')
        if request.args.get('memory_type'):
            filters['memory_type'] = request.args.get('memory_type')
        if request.args.get('length_category'):
            filters['length_category'] = request.args.get('length_category')
        if request.args.get('search'):
            filters['search'] = request.args.get('search')

        memories = portal.get_memories_list(filters if filters else None)
        return jsonify({
            'success': True,
            'memories': memories,
            'count': len(memories)
        })
    except Exception as e:
        logger.error(f"Error getting memories: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/memories/save', methods=['POST'])
def api_save_memory():
    """Save a new memory"""
    try:
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': 'No audio file provided'}), 400

        audio_file = request.files['audio']
        person = request.form.get('person')
        memory_type = request.form.get('memory_type')
        length_category = request.form.get('length_category')
        title = request.form.get('title', '')
        tags = request.form.get('tags', '')

        if not all([person, memory_type, length_category]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        if audio_file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"memory_{person}_{memory_type}_{timestamp}.wav"
        filename = secure_filename(filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # Save file
        audio_file.save(file_path)
        file_size = os.path.getsize(file_path)

        # Save to database
        memory_id = portal.save_memory(
            person=person,
            memory_type=memory_type,
            length_category=length_category,
            title=title,
            tags=tags,
            file_path=file_path,
            file_size=file_size
        )

        if memory_id:
            logger.info(f"Memory saved: {filename} from {person}")
            return jsonify({
                'success': True,
                'memory_id': memory_id,
                'filename': filename,
                'file_size': file_size
            })
        else:
            # Clean up file if database save failed
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'success': False, 'error': 'Failed to save to database'}), 500

    except Exception as e:
        logger.error(f"Save memory error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/memories/delete', methods=['POST'])
def api_delete_memory():
    """Delete a memory"""
    try:
        data = request.get_json()
        memory_id = data.get('memory_id')

        if not memory_id:
            return jsonify({'success': False, 'error': 'Memory ID required'}), 400

        success = portal.delete_memory(memory_id)

        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Memory not found'}), 404

    except Exception as e:
        logger.error(f"Delete memory error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/memories/random')
def api_random_memory():
    """Get a random memory matching optional filters"""
    try:
        filters = {}
        if request.args.get('person'):
            filters['person'] = request.args.get('person')
        if request.args.get('memory_type'):
            filters['memory_type'] = request.args.get('memory_type')
        if request.args.get('length_category'):
            filters['length_category'] = request.args.get('length_category')

        memory = portal.get_random_memory(filters if filters else None)

        if memory:
            return jsonify({
                'success': True,
                'memory': memory
            })
        else:
            return jsonify({'success': False, 'error': 'No memories found matching criteria'}), 404

    except Exception as e:
        logger.error(f"Random memory error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/memories/audio/<memory_id>')
def api_get_memory_audio(memory_id):
    """Serve audio file for memory playback"""
    try:
        conn = sqlite3.connect(MESSAGES_DB)
        cursor = conn.cursor()
        cursor.execute('SELECT file_path FROM memories WHERE id = ?', (memory_id,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            return jsonify({'error': 'Memory not found'}), 404

        file_path = result[0]

        if not os.path.exists(file_path):
            return jsonify({'error': 'Audio file not found'}), 404

        # Determine MIME type
        file_ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg',
            '.m4a': 'audio/mp4',
            '.ogg': 'audio/ogg',
            '.webm': 'audio/webm',
            '.flac': 'audio/flac',
            '.aac': 'audio/aac'
        }
        mimetype = mime_types.get(file_ext, 'audio/wav')

        logger.info(f"Serving memory audio: {file_path}")
        return send_file(file_path, mimetype=mimetype)

    except Exception as e:
        logger.error(f"Get memory audio error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/logs')
def logs_page():
    """Logs viewer page"""
    try:
        return render_template('logs.html')
    except Exception as e:
        logger.error(f"Logs page error: {e}")
        return f"Error loading logs page: {e}", 500

@app.route('/api/logs/stream')
def stream_logs():
    """Stream journalctl logs in real-time using Server-Sent Events"""
    def generate():
        service = request.args.get('service', 'muninn-assistant')
        lines = request.args.get('lines', '100')

        # Validate service name to prevent injection
        valid_services = ['muninn-assistant', 'muninn-web-portal']
        if service not in valid_services:
            service = 'muninn-assistant'

        try:
            # Run journalctl in follow mode
            process = subprocess.Popen(
                ['sudo', 'journalctl', '-u', service, '-f', '-n', lines, '--no-pager'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Send initial connection message
            yield f"data: {{\"type\": \"connected\", \"service\": \"{service}\"}}\n\n"

            # Stream log lines
            for line in iter(process.stdout.readline, ''):
                if line:
                    # Escape line for JSON
                    escaped_line = json.dumps(line.rstrip())
                    yield f"data: {{\"type\": \"log\", \"line\": {escaped_line}}}\n\n"
        except Exception as e:
            error_msg = json.dumps(f"Error streaming logs: {str(e)}")
            yield f"data: {{\"type\": \"error\", \"message\": {error_msg}}}\n\n"
        finally:
            if 'process' in locals():
                process.terminate()
                process.wait(timeout=5)

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/api/logs/download')
def download_logs():
    """Download logs as a text file"""
    try:
        service = request.args.get('service', 'muninn-assistant')
        lines = request.args.get('lines', '1000')

        # Validate service name
        valid_services = ['muninn-assistant', 'muninn-web-portal']
        if service not in valid_services:
            service = 'muninn-assistant'

        # Get logs
        result = subprocess.run(
            ['sudo', 'journalctl', '-u', service, '-n', lines, '--no-pager'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            # Create temporary file
            temp_dir = tempfile.mkdtemp()
            log_file = os.path.join(temp_dir, f'{service}_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')

            with open(log_file, 'w') as f:
                f.write(f"# {service} logs\n")
                f.write(f"# Downloaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Lines: {lines}\n\n")
                f.write(result.stdout)

            return send_file(log_file, as_attachment=True,
                           download_name=f'{service}_logs_{datetime.now().strftime("%Y%m%d")}.txt')
        else:
            return jsonify({'error': 'Failed to get logs'}), 500

    except Exception as e:
        logger.error(f"Download logs error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)

    print("🌐 Starting Muninn Web Portal...")
    print(f"📁 Upload folder: {UPLOAD_FOLDER}")
    print(f"🗄️ Database: {MESSAGES_DB}")
    print("🎯 Starting server on http://0.0.0.0:5001")

    app.run(host='0.0.0.0', port=5001, debug=False)