#!/bin/bash

# Setup script for log viewer permissions
# This allows the web portal to access journalctl logs without password

echo "🔧 Setting up log viewer permissions..."

# Create sudoers file for muninn logs
SUDOERS_FILE="/etc/sudoers.d/muninn-logs"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run with sudo"
    echo "Usage: sudo bash setup_logs_permissions.sh"
    exit 1
fi

# Create the sudoers entry
cat > "$SUDOERS_FILE" << 'EOF'
# Allow user bw to run journalctl for muninn services without password
bw ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u muninn-assistant*
bw ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u muninn-web-portal*
bw ALL=(ALL) NOPASSWD: /usr/bin/journalctl
EOF

# Set correct permissions (must be 0440)
chmod 0440 "$SUDOERS_FILE"

# Validate the sudoers file
if visudo -c -f "$SUDOERS_FILE" > /dev/null 2>&1; then
    echo "✅ Sudoers file created and validated: $SUDOERS_FILE"
    echo ""
    echo "The web portal can now access logs without password."
    echo "You can view real-time logs at: http://your-pi-ip:5001/logs"
else
    echo "❌ Sudoers file validation failed! Removing invalid file."
    rm -f "$SUDOERS_FILE"
    exit 1
fi

echo ""
echo "✅ Log viewer permissions setup complete!"
