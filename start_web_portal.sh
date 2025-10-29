#!/bin/bash

# Muninn Web Portal Startup Script
# Starts the enhanced web dashboard with recording functionality

echo "🌐 Starting Muninn Web Portal..."

# Change to the correct directory
cd /home/bw/muninn/muninn-v3/muninn-modular

# Set environment variables
export FLASK_APP=web_portal.py
export FLASK_ENV=production

# Create necessary directories
mkdir -p /home/bw/muninn/muninn-v3/recordings
mkdir -p templates/static

# Start the web portal
echo "🎯 Web portal will be available at:"
echo "   Local:  http://localhost:5001"
echo "   Network: http://$(hostname -I | awk '{print $1}'):5001"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 web_portal.py