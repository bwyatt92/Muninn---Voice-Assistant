#!/bin/bash

# Setup script for Muninn Voice Assistant service
# Run this on the Raspberry Pi to enable auto-start

echo "🔧 Setting up Muninn Voice Assistant service..."

# Copy service file to systemd directory
sudo cp muninn-assistant.service /etc/systemd/system/

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable muninn-assistant.service

# Start the service now
sudo systemctl start muninn-assistant.service

echo ""
echo "✅ Setup complete!"
echo ""
echo "Useful commands:"
echo "  Start service:   sudo systemctl start muninn-assistant"
echo "  Stop service:    sudo systemctl stop muninn-assistant"
echo "  Restart service: sudo systemctl restart muninn-assistant"
echo "  Check status:    sudo systemctl status muninn-assistant"
echo "  View logs:       sudo journalctl -u muninn-assistant -f"
echo "  Disable auto-start: sudo systemctl disable muninn-assistant"
echo ""
