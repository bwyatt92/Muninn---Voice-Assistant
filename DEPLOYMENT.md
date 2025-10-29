# Muninn Deployment and Troubleshooting Guide

This guide covers deploying Muninn services to your Raspberry Pi and troubleshooting common issues.

## Table of Contents
1. [Initial Deployment](#initial-deployment)
2. [Service Management](#service-management)
3. [Health Monitoring](#health-monitoring)
4. [Troubleshooting](#troubleshooting)
5. [Common Issues](#common-issues)

---

## Initial Deployment

### Step 1: Transfer Files to Raspberry Pi

From your development machine:

```bash
# Transfer files to Raspberry Pi
scp -r muninn-modular/* bw@raspberrypi:/home/bw/muninn/muninn-v3/muninn-modular/

# Transfer service files
scp muninn-modular/*.service bw@raspberrypi:/home/bw/muninn/muninn-v3/muninn-modular/
```

### Step 2: Install Service Files

On the Raspberry Pi:

```bash
# Navigate to the directory
cd /home/bw/muninn/muninn-v3/muninn-modular

# Make scripts executable
chmod +x health_check.sh
chmod +x system_monitor.py

# Copy service files to systemd directory
sudo cp muninn-assistant.service /etc/systemd/system/
sudo cp muninn-web-portal.service /etc/systemd/system/
sudo cp muninn-monitor.service /etc/systemd/system/  # Optional

# Reload systemd to recognize new service files
sudo systemctl daemon-reload
```

### Step 3: Enable and Start Services

```bash
# Enable services to start on boot
sudo systemctl enable muninn-assistant.service
sudo systemctl enable muninn-web-portal.service
sudo systemctl enable muninn-monitor.service  # Optional

# Start services
sudo systemctl start muninn-assistant.service
sudo systemctl start muninn-web-portal.service
sudo systemctl start muninn-monitor.service  # Optional
```

### Step 4: Verify Services are Running

```bash
# Check service status
sudo systemctl status muninn-assistant.service
sudo systemctl status muninn-web-portal.service

# Or use the health check script
./health_check.sh
```

---

## Service Management

### Starting Services
```bash
sudo systemctl start muninn-assistant.service
sudo systemctl start muninn-web-portal.service
```

### Stopping Services
```bash
sudo systemctl stop muninn-assistant.service
sudo systemctl stop muninn-web-portal.service
```

### Restarting Services
```bash
sudo systemctl restart muninn-assistant.service
sudo systemctl restart muninn-web-portal.service
```

### Checking Service Status
```bash
# Quick status check
sudo systemctl status muninn-assistant.service

# Detailed health check with system resources
./health_check.sh
```

### Viewing Logs
```bash
# View last 50 lines of logs
sudo journalctl -u muninn-assistant -n 50

# Follow logs in real-time
sudo journalctl -u muninn-assistant -f

# View logs from specific time period
sudo journalctl -u muninn-assistant --since "10 minutes ago"

# View logs for both services
sudo journalctl -u muninn-assistant -u muninn-web-portal -n 100
```

### Disabling Services (if needed)
```bash
sudo systemctl disable muninn-assistant.service
sudo systemctl disable muninn-web-portal.service
```

---

## Health Monitoring

### Automatic Monitoring

The `muninn-monitor.service` continuously monitors system health and logs alerts.

**View monitor logs:**
```bash
sudo journalctl -u muninn-monitor -f
```

### Manual Health Checks

Run the health check script anytime:

```bash
./health_check.sh
```

This will show:
- Service status and restart counts
- CPU temperature and usage
- Memory usage
- Disk usage
- Common issues detected

### Setting Up Periodic Health Checks

Add to crontab for hourly checks:

```bash
# Edit crontab
crontab -e

# Add this line for hourly checks (results logged)
0 * * * * /home/bw/muninn/muninn-v3/muninn-modular/health_check.sh >> /home/bw/muninn/muninn-v3/health_check.log 2>&1
```

---

## Troubleshooting

### Step 1: Check Service Status

```bash
./health_check.sh
```

### Step 2: Check Recent Logs

```bash
# Last 50 log entries
sudo journalctl -u muninn-assistant -n 50

# Look for errors
sudo journalctl -u muninn-assistant -p err -n 20
```

### Step 3: Check System Resources

```bash
# CPU and memory
htop

# Or use the health check script
./health_check.sh
```

### Step 4: Check for Path Issues

The logs showed path errors in the past. Verify Python path:

```bash
# Check if Python exists at the path in service file
ls -la /home/bw/muninn/muninn/bin/python3

# If not found, locate correct Python path
which python3
```

**If path is wrong, update service file:**

```bash
# Edit service file
sudo nano /etc/systemd/system/muninn-assistant.service

# Update ExecStart line with correct Python path
# Then reload
sudo systemctl daemon-reload
sudo systemctl restart muninn-assistant.service
```

### Step 5: Reset Failed Service

If service is in failed state:

```bash
# Reset the failed state
sudo systemctl reset-failed muninn-assistant.service

# Restart
sudo systemctl restart muninn-assistant.service
```

---

## Common Issues

### Issue 1: Service Won't Start - Path Errors

**Symptom:**
```
Failed to locate executable /home/bw/muninn/.../python3: No such file or directory
```

**Solution:**
```bash
# Find correct Python path
which python3

# Update service file
sudo nano /etc/systemd/system/muninn-assistant.service

# Update the ExecStart line with correct path
# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart muninn-assistant.service
```

### Issue 2: Service Keeps Restarting

**Symptom:**
```
restart counter is at 12
restart counter is at 13
...
```

**Solution:**

The new service files limit restarts to 5 attempts in 10 minutes. If service keeps failing:

```bash
# Check logs for the actual error
sudo journalctl -u muninn-assistant -n 100

# Common causes:
# 1. Wrong Python path (see Issue 1)
# 2. Missing dependencies
# 3. Permission issues
# 4. Hardware not available

# To install missing dependencies:
cd /home/bw/muninn/muninn-v3/muninn-modular
pip install -r requirements.txt
```

### Issue 3: System Becomes Unresponsive

**Prevention (already implemented):**
- Resource limits (CPU 80%, Memory 512MB for assistant)
- Restart limits (max 5 restarts in 10 minutes)
- System monitoring with alerts

**If it happens:**

```bash
# 1. SSH into the Pi (if possible)
./health_check.sh

# 2. Check which process is consuming resources
htop

# 3. If needed, stop services
sudo systemctl stop muninn-assistant.service
sudo systemctl stop muninn-web-portal.service

# 4. Review logs
sudo journalctl -n 200 -p err

# 5. Restart services after identifying issue
sudo systemctl start muninn-assistant.service
sudo systemctl start muninn-web-portal.service
```

### Issue 4: Web Portal Can't Connect

**Check if web portal is running:**

```bash
sudo systemctl status muninn-web-portal.service
```

**Check if port is open:**

```bash
sudo netstat -tlnp | grep 5001
```

**Check logs:**

```bash
sudo journalctl -u muninn-web-portal -n 50
```

### Issue 5: Audio Issues

**Check audio hardware:**

```bash
# List audio devices
aplay -l

# Check if ReSpeaker is detected
lsusb | grep -i audio
```

**Check service has audio permissions:**

```bash
# Verify user is in audio group
groups bw

# If not, add user to audio group
sudo usermod -a -G audio bw

# Restart service
sudo systemctl restart muninn-assistant.service
```

### Issue 6: Out of Memory

**Check current memory usage:**

```bash
free -h
```

**Services now have memory limits:**
- Assistant: 512MB max
- Web Portal: 256MB max
- Monitor: 128MB max

**If hitting limits frequently:**

```bash
# Increase memory limits in service file
sudo nano /etc/systemd/system/muninn-assistant.service

# Change MemoryMax=512M to MemoryMax=768M (or higher)
# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart muninn-assistant.service
```

### Issue 7: High CPU Temperature

**Check temperature:**

```bash
vcgencmd measure_temp
```

**If over 70°C:**
- Ensure proper ventilation
- Consider adding heatsinks or fan
- Reduce CPU quota in service files temporarily

---

## Service File Improvements

### What Changed

The new service files include:

1. **Restart Limits**
   - `StartLimitBurst=5` - Only 5 restart attempts
   - `StartLimitIntervalSec=600` - Within 10 minutes
   - `Restart=on-failure` - Only restart on failures, not on clean exits

2. **Resource Limits**
   - `MemoryMax` - Hard memory limit
   - `MemoryHigh` - Soft memory limit (throttles before hard limit)
   - `CPUQuota` - Limit CPU usage

3. **Graceful Shutdown**
   - `TimeoutStopSec=30` - 30 seconds for graceful shutdown
   - `KillMode=mixed` - Try SIGTERM first, then SIGKILL
   - `KillSignal=SIGTERM` - Clean shutdown signal

4. **Better Logging**
   - `SyslogIdentifier` - Easy log filtering
   - `StandardOutput/Error=journal` - Centralized logging

### Adjusting Resource Limits

If services need more resources:

```bash
# Edit service file
sudo nano /etc/systemd/system/muninn-assistant.service

# Adjust these values:
# MemoryMax=512M      -> Increase if needed
# CPUQuota=80%        -> Increase if needed

# Save and reload
sudo systemctl daemon-reload
sudo systemctl restart muninn-assistant.service
```

---

## Maintenance Tasks

### Weekly Maintenance

```bash
# Check system health
./health_check.sh

# Review logs for errors
sudo journalctl -u muninn-assistant --since "7 days ago" -p err

# Check disk space
df -h

# Clean up old logs if needed (keeps last 2 weeks)
sudo journalctl --vacuum-time=2weeks
```

### Monthly Maintenance

```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Check for Python package updates
pip list --outdated

# Backup configuration and messages
tar -czf muninn-backup-$(date +%Y%m%d).tar.gz \
  /home/bw/muninn/muninn-v3/muninn-modular/*.service \
  /home/bw/muninn/muninn-v3/messages.db \
  /home/bw/muninn/muninn-v3/recordings/
```

---

## Quick Reference Commands

```bash
# Service status
sudo systemctl status muninn-assistant.service

# View logs
sudo journalctl -u muninn-assistant -n 50

# Follow logs
sudo journalctl -u muninn-assistant -f

# Restart service
sudo systemctl restart muninn-assistant.service

# Health check
./health_check.sh

# Check temperature
vcgencmd measure_temp

# Check processes
htop

# Check disk space
df -h

# Check memory
free -h
```

---

## Getting Help

If issues persist:

1. **Collect diagnostic information:**
   ```bash
   ./health_check.sh > diagnostic_$(date +%Y%m%d).txt
   sudo journalctl -u muninn-assistant -n 200 >> diagnostic_$(date +%Y%m%d).txt
   sudo journalctl -u muninn-web-portal -n 200 >> diagnostic_$(date +%Y%m%d).txt
   ```

2. **Review the diagnostic file for patterns**

3. **Check system load over time:**
   ```bash
   uptime
   cat /proc/loadavg
   ```

---

## Updates and Rollback

### Deploying Updates

```bash
# On development machine
scp -r muninn-modular/* bw@raspberrypi:/home/bw/muninn/muninn-v3/muninn-modular/

# On Raspberry Pi
sudo systemctl restart muninn-assistant.service
sudo systemctl restart muninn-web-portal.service

# Monitor for issues
sudo journalctl -u muninn-assistant -f
```

### Rolling Back Service Files

```bash
# If new service files cause issues, restore old ones
# (Assuming you kept backups)

sudo cp /home/bw/muninn/muninn-v3/muninn-modular/muninn-assistant.service.backup \
        /etc/systemd/system/muninn-assistant.service

sudo systemctl daemon-reload
sudo systemctl restart muninn-assistant.service
```

---

**Last Updated:** October 2024
