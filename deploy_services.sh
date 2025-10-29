#!/bin/bash
# Deploy Muninn Services to Raspberry Pi
# Run this script on the Raspberry Pi after transferring files

set -e

echo "======================================"
echo "  Muninn Services Deployment Script"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Please do not run this script as root${NC}"
    echo "Run it as your regular user. It will prompt for sudo when needed."
    exit 1
fi

# Configuration
MUNINN_DIR="/home/bw/muninn/muninn-v3/muninn-modular"
SYSTEMD_DIR="/etc/systemd/system"
SERVICES=("muninn-assistant.service" "muninn-web-portal.service" "muninn-monitor.service")

echo "Step 1: Checking prerequisites..."
echo "-----------------------------------"

# Check if we're in the right directory
if [ ! -f "$MUNINN_DIR/muninn.py" ]; then
    echo -e "${RED}Error: Cannot find muninn.py in $MUNINN_DIR${NC}"
    echo "Please ensure files are in the correct location"
    exit 1
fi

echo -e "${GREEN}✓ Muninn directory found${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python3 not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python3 found: $(which python3)${NC}"

# Verify Python path in service files
SERVICE_PYTHON_PATH=$(grep "ExecStart=" muninn-assistant.service | awk '{print $1}' | cut -d'=' -f2)
if [ ! -f "$SERVICE_PYTHON_PATH" ]; then
    echo -e "${YELLOW}Warning: Python path in service file may be incorrect${NC}"
    echo "Service file uses: $SERVICE_PYTHON_PATH"
    echo "System Python is at: $(which python3)"
    read -p "Do you want to continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "Step 2: Making scripts executable..."
echo "-------------------------------------"

chmod +x "$MUNINN_DIR/health_check.sh"
chmod +x "$MUNINN_DIR/system_monitor.py"
chmod +x "$MUNINN_DIR/deploy_services.sh"

echo -e "${GREEN}✓ Scripts are now executable${NC}"

echo ""
echo "Step 3: Backing up existing service files..."
echo "---------------------------------------------"

# Stop services if they're running
for service in "${SERVICES[@]}"; do
    if systemctl is-active --quiet "$service" 2>/dev/null; then
        echo "Stopping $service..."
        sudo systemctl stop "$service"
    fi

    # Backup existing service file
    if [ -f "$SYSTEMD_DIR/$service" ]; then
        sudo cp "$SYSTEMD_DIR/$service" "$SYSTEMD_DIR/$service.backup.$(date +%Y%m%d_%H%M%S)"
        echo -e "${GREEN}✓ Backed up $service${NC}"
    fi
done

echo ""
echo "Step 4: Installing service files..."
echo "-------------------------------------"

for service in "${SERVICES[@]}"; do
    if [ -f "$MUNINN_DIR/$service" ]; then
        echo "Installing $service..."
        sudo cp "$MUNINN_DIR/$service" "$SYSTEMD_DIR/"
        echo -e "${GREEN}✓ Installed $service${NC}"
    else
        echo -e "${YELLOW}⚠ Warning: $service not found in $MUNINN_DIR${NC}"
    fi
done

echo ""
echo "Step 5: Reloading systemd..."
echo "-----------------------------"

sudo systemctl daemon-reload
echo -e "${GREEN}✓ Systemd reloaded${NC}"

echo ""
echo "Step 6: Enabling services..."
echo "-----------------------------"

for service in "${SERVICES[@]}"; do
    if [ -f "$SYSTEMD_DIR/$service" ]; then
        echo "Enabling $service..."
        sudo systemctl enable "$service"
        echo -e "${GREEN}✓ Enabled $service${NC}"
    fi
done

echo ""
echo "Step 7: Starting services..."
echo "-----------------------------"

for service in "${SERVICES[@]}"; do
    if [ -f "$SYSTEMD_DIR/$service" ]; then
        echo "Starting $service..."
        if sudo systemctl start "$service"; then
            echo -e "${GREEN}✓ Started $service${NC}"
        else
            echo -e "${RED}✗ Failed to start $service${NC}"
            echo "Check logs with: sudo journalctl -u $service -n 50"
        fi
    fi
done

echo ""
echo "Step 8: Checking service status..."
echo "-----------------------------------"

sleep 3  # Give services time to start

for service in "${SERVICES[@]:0:2}"; do  # Only check main services
    if [ -f "$SYSTEMD_DIR/$service" ]; then
        if systemctl is-active --quiet "$service"; then
            echo -e "${GREEN}✓ $service is running${NC}"
        else
            echo -e "${RED}✗ $service is not running${NC}"
            echo "Run: sudo journalctl -u $service -n 20"
        fi
    fi
done

echo ""
echo "======================================"
echo "  Deployment Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Run health check: ./health_check.sh"
echo "2. View logs: sudo journalctl -u muninn-assistant -f"
echo "3. Access web portal: http://$(hostname -I | awk '{print $1}'):5001"
echo ""
echo "Useful commands:"
echo "  ./health_check.sh                    # Check system health"
echo "  sudo systemctl status muninn-assistant.service"
echo "  sudo journalctl -u muninn-assistant -f"
echo ""

# Offer to run health check
read -p "Run health check now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    "$MUNINN_DIR/health_check.sh"
fi
