#!/bin/bash

# Setup script for Muninn Web Portal service
# Run this on the Raspberry Pi to enable auto-start

echo "🔧 Setting up Muninn Web Portal service..."

# Copy service file to systemd directory
sudo cp muninn-web-portal.service /etc/systemd/system/

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable muninn-web-portal.service

# Start the service now
sudo systemctl start muninn-web-portal.service

echo ""
echo "✅ Setup complete!"
echo ""
echo "Useful commands:"
echo "  Start service:   sudo systemctl start muninn-web-portal"
echo "  Stop service:    sudo systemctl stop muninn-web-portal"
echo "  Restart service: sudo systemctl restart muninn-web-portal"
echo "  Check status:    sudo systemctl status muninn-web-portal"
echo "  View logs:       sudo journalctl -u muninn-web-portal -f"
echo "  Disable auto-start: sudo systemctl disable muninn-web-portal"
echo ""
