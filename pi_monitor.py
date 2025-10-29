#!/usr/bin/env python3
"""
Raspberry Pi Monitoring Dashboard
Flask backend for system monitoring and basic interactions
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import psutil
import subprocess
import os
import json
import time
from datetime import datetime
import re
import threading
import socket

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

class PiMonitor:
    def __init__(self):
        self.start_time = time.time()
        
    def get_cpu_info(self):
        """Get CPU information"""
        try:
            # CPU temperature
            temp_cmd = subprocess.run(['vcgencmd', 'measure_temp'], 
                                    capture_output=True, text=True)
            temp = temp_cmd.stdout.strip().replace('temp=', '').replace("'C", '')
            cpu_temp = float(temp) if temp else 0
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
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
            swap = psutil.swap_memory()
            
            return {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent,
                'swap_total': swap.total,
                'swap_used': swap.used,
                'swap_percent': swap.percent
            }
        except Exception as e:
            return {'error': str(e)}

    def get_disk_info(self):
        """Get disk information"""
        try:
            disk_usage = psutil.disk_usage('/')
            
            # Get disk I/O stats
            disk_io = psutil.disk_io_counters()
            
            return {
                'total': disk_usage.total,
                'used': disk_usage.used,
                'free': disk_usage.free,
                'percent': (disk_usage.used / disk_usage.total) * 100,
                'read_bytes': disk_io.read_bytes if disk_io else 0,
                'write_bytes': disk_io.write_bytes if disk_io else 0
            }
        except Exception as e:
            return {'error': str(e)}

    def get_network_info(self):
        """Get network information"""
        try:
            # Get network interfaces
            interfaces = {}
            for interface, addrs in psutil.net_if_addrs().items():
                interfaces[interface] = {
                    'addresses': [addr.address for addr in addrs],
                    'is_up': interface in psutil.net_if_stats() and psutil.net_if_stats()[interface].isup
                }
            
            # Get current WiFi connection
            wifi_info = self.get_wifi_status()
            
            # Network I/O stats
            net_io = psutil.net_io_counters()
            
            return {
                'interfaces': interfaces,
                'wifi': wifi_info,
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
        except Exception as e:
            return {'error': str(e)}

    def get_wifi_status(self):
        """Get current WiFi connection status"""
        try:
            # Get current SSID
            iwconfig_cmd = subprocess.run(['iwconfig', 'wlan0'], 
                                        capture_output=True, text=True)
            
            ssid_match = re.search(r'ESSID:"([^"]*)"', iwconfig_cmd.stdout)
            current_ssid = ssid_match.group(1) if ssid_match else "Not connected"
            
            # Get signal strength
            signal_match = re.search(r'Signal level=(-?\d+)', iwconfig_cmd.stdout)
            signal_strength = signal_match.group(1) if signal_match else "Unknown"
            
            return {
                'ssid': current_ssid,
                'signal_strength': signal_strength,
                'connected': current_ssid != "Not connected"
            }
        except Exception as e:
            return {'error': str(e)}

    def get_available_networks(self):
        """Scan for available WiFi networks"""
        try:
            scan_cmd = subprocess.run(['sudo', 'iwlist', 'wlan0', 'scan'], 
                                    capture_output=True, text=True)
            
            networks = []
            cells = scan_cmd.stdout.split('Cell ')
            
            for cell in cells[1:]:  # Skip first empty element
                ssid_match = re.search(r'ESSID:"([^"]*)"', cell)
                quality_match = re.search(r'Quality=(\d+/\d+)', cell)
                encryption_match = re.search(r'Encryption key:(on|off)', cell)
                
                if ssid_match:
                    networks.append({
                        'ssid': ssid_match.group(1),
                        'quality': quality_match.group(1) if quality_match else 'Unknown',
                        'encrypted': encryption_match.group(1) == 'on' if encryption_match else True
                    })
            
            return networks
        except Exception as e:
            return []

    def get_system_info(self):
        """Get general system information"""
        try:
            uptime = time.time() - self.start_time
            
            # Get Pi model
            model_cmd = subprocess.run(['cat', '/proc/device-tree/model'], 
                                     capture_output=True, text=True)
            model = model_cmd.stdout.strip().replace('\x00', '')
            
            return {
                'hostname': socket.gethostname(),
                'model': model,
                'uptime': uptime,
                'os_release': self.get_os_release(),
                'kernel': os.uname().release,
                'architecture': os.uname().machine
            }
        except Exception as e:
            return {'error': str(e)}

    def get_os_release(self):
        """Get OS release information"""
        try:
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if line.startswith('PRETTY_NAME='):
                        return line.split('=')[1].strip().replace('"', '')
            return "Unknown"
        except:
            return "Unknown"

    def get_running_services(self):
        """Get status of important services"""
        services = ['ssh', 'networking', 'bluetooth', 'cron', 'systemd-timesyncd']
        service_status = {}
        
        for service in services:
            try:
                result = subprocess.run(['systemctl', 'is-active', service], 
                                      capture_output=True, text=True)
                service_status[service] = result.stdout.strip()
            except:
                service_status[service] = 'unknown'
        
        return service_status

    def get_recent_logs(self, lines=50):
        """Get recent system logs"""
        try:
            result = subprocess.run(['journalctl', '-n', str(lines), '--no-pager'], 
                                  capture_output=True, text=True)
            return result.stdout.split('\n')
        except Exception as e:
            return [f"Error getting logs: {str(e)}"]

# Initialize monitor
monitor = PiMonitor()

@app.route('/')
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/vitals')
def api_vitals():
    """API endpoint for system vitals"""
    vitals = {
        'cpu': monitor.get_cpu_info(),
        'memory': monitor.get_memory_info(),
        'disk': monitor.get_disk_info(),
        'network': monitor.get_network_info(),
        'system': monitor.get_system_info(),
        'services': monitor.get_running_services(),
        'timestamp': datetime.now().isoformat()
    }
    return jsonify(vitals)

@app.route('/api/logs')
def api_logs():
    """API endpoint for recent logs"""
    lines = request.args.get('lines', 50, type=int)
    logs = monitor.get_recent_logs(lines)
    return jsonify({'logs': logs})

@app.route('/api/wifi/scan')
def api_wifi_scan():
    """API endpoint to scan for WiFi networks"""
    networks = monitor.get_available_networks()
    return jsonify({'networks': networks})

@app.route('/api/wifi/connect', methods=['POST'])
def api_wifi_connect():
    """API endpoint to connect to WiFi network"""
    data = request.get_json()
    ssid = data.get('ssid')
    password = data.get('password')
    
    if not ssid:
        return jsonify({'error': 'SSID required'}), 400
    
    try:
        # Create wpa_supplicant network block
        network_config = f'''
network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
'''
        
        # Append to wpa_supplicant.conf
        with open('/etc/wpa_supplicant/wpa_supplicant.conf', 'a') as f:
            f.write(network_config)
        
        # Restart networking
        subprocess.run(['sudo', 'systemctl', 'restart', 'networking'], check=True)
        
        return jsonify({'message': f'Attempting to connect to {ssid}'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/service/<service>/<action>')
def api_service_control(service, action):
    """API endpoint to control services"""
    valid_services = ['ssh', 'networking', 'bluetooth', 'cron']
    valid_actions = ['start', 'stop', 'restart', 'status']
    
    if service not in valid_services:
        return jsonify({'error': 'Invalid service'}), 400
    
    if action not in valid_actions:
        return jsonify({'error': 'Invalid action'}), 400
    
    try:
        result = subprocess.run(['sudo', 'systemctl', action, service], 
                              capture_output=True, text=True)
        
        return jsonify({
            'service': service,
            'action': action,
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reboot', methods=['POST'])
def api_reboot():
    """API endpoint to reboot system"""
    try:
        # Schedule reboot in 1 minute
        subprocess.run(['sudo', 'shutdown', '-r', '+1'], check=True)
        return jsonify({'message': 'System will reboot in 1 minute'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def format_bytes(bytes_value):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def format_uptime(seconds):
    """Format uptime seconds to human readable format"""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

# Add template filters
app.jinja_env.filters['format_bytes'] = format_bytes
app.jinja_env.filters['format_uptime'] = format_uptime

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)