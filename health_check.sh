#!/bin/bash
# Muninn Health Check Script
# Run this script periodically to monitor system health and service status

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "===================================="
echo "  Muninn System Health Check"
echo "  $(date)"
echo "===================================="
echo ""

# Function to check service status
check_service() {
    local service=$1
    echo -n "Checking $service... "

    if systemctl is-active --quiet "$service"; then
        echo -e "${GREEN}✓ Running${NC}"

        # Check how many times it has restarted
        restart_count=$(systemctl show "$service" -p NRestarts --value)
        if [ "$restart_count" -gt 0 ]; then
            echo -e "  ${YELLOW}⚠ Warning: Service has restarted $restart_count times${NC}"
        fi

        # Check memory usage
        memory_current=$(systemctl show "$service" -p MemoryCurrent --value)
        if [ "$memory_current" != "[not set]" ] && [ "$memory_current" -gt 0 ]; then
            memory_mb=$((memory_current / 1024 / 1024))
            echo "  Memory usage: ${memory_mb}MB"
        fi

        return 0
    else
        echo -e "${RED}✗ Not Running${NC}"

        # Show recent failure info
        echo -e "${RED}Recent errors:${NC}"
        journalctl -u "$service" -n 5 --no-pager | tail -n 3

        return 1
    fi
}

# Function to check system resources
check_resources() {
    echo ""
    echo "System Resources:"
    echo "-----------------"

    # CPU Temperature (Raspberry Pi specific)
    if command -v vcgencmd &> /dev/null; then
        temp=$(vcgencmd measure_temp | cut -d '=' -f 2 | cut -d "'" -f 1)
        echo "CPU Temperature: ${temp}°C"

        # Warn if temperature is high
        temp_int=${temp%.*}
        if [ "$temp_int" -gt 70 ]; then
            echo -e "${YELLOW}⚠ Warning: High CPU temperature!${NC}"
        fi
    fi

    # CPU Usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    echo "CPU Usage: ${cpu_usage}%"

    # Memory Usage
    mem_info=$(free -m | awk 'NR==2{printf "Memory: %s/%sMB (%.2f%%)", $3,$2,$3*100/$2 }')
    echo "$mem_info"

    # Disk Usage
    disk_info=$(df -h / | awk 'NR==2{printf "Disk: %s/%s (%s)", $3,$2,$5}')
    echo "$disk_info"

    # Check if disk is getting full
    disk_percent=$(df / | awk 'NR==2{print $5}' | sed 's/%//')
    if [ "$disk_percent" -gt 80 ]; then
        echo -e "${YELLOW}⚠ Warning: Disk usage is high!${NC}"
    fi
}

# Function to check for common issues
check_issues() {
    echo ""
    echo "Checking for Common Issues:"
    echo "---------------------------"

    # Check for path issues in logs
    if journalctl -u muninn-assistant -n 50 --no-pager | grep -q "No such file or directory"; then
        echo -e "${RED}✗ Path/File not found errors detected in logs${NC}"
        echo "  Run: journalctl -u muninn-assistant -n 20 to see details"
    else
        echo -e "${GREEN}✓ No path errors detected${NC}"
    fi

    # Check for memory issues
    if journalctl -n 100 --no-pager | grep -i "out of memory\|oom"; then
        echo -e "${RED}✗ Out of memory errors detected${NC}"
    else
        echo -e "${GREEN}✓ No memory errors detected${NC}"
    fi

    # Check network connectivity
    if ping -c 1 8.8.8.8 &> /dev/null; then
        echo -e "${GREEN}✓ Network connectivity OK${NC}"
    else
        echo -e "${RED}✗ Network connectivity issues${NC}"
    fi
}

# Main checks
echo "Service Status:"
echo "---------------"

services_ok=0
check_service "muninn-assistant.service" && ((services_ok++)) || true
check_service "muninn-web-portal.service" && ((services_ok++)) || true

check_resources
check_issues

echo ""
echo "===================================="
if [ $services_ok -eq 2 ]; then
    echo -e "${GREEN}Overall Status: HEALTHY${NC}"
else
    echo -e "${RED}Overall Status: ISSUES DETECTED${NC}"
    echo "Run the following for more details:"
    echo "  journalctl -u muninn-assistant -n 50"
    echo "  journalctl -u muninn-web-portal -n 50"
fi
echo "===================================="
