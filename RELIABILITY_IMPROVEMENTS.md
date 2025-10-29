# Muninn Reliability Improvements Summary

## Problem Analysis

Your Raspberry Pi was becoming unresponsive due to:

1. **Infinite restart loops** - Services failing and restarting continuously (18+ times)
2. **No resource limits** - Services could consume unlimited CPU/memory
3. **Path errors** - Python executable not found, causing constant failures
4. **No monitoring** - No way to detect issues before system becomes unresponsive

## Solutions Implemented

### 1. Improved Service Files

#### muninn-assistant.service
**Changes:**
- ✅ Added restart limits (max 5 attempts in 10 minutes)
- ✅ Changed `Restart=always` to `Restart=on-failure` (won't restart on clean exit)
- ✅ Added memory limits (512MB max, 400MB high threshold)
- ✅ Added CPU quota (80% max)
- ✅ Added graceful shutdown handling (30 second timeout)
- ✅ Added proper logging with `SyslogIdentifier`

**Before:**
```ini
Restart=always
RestartSec=10
```

**After:**
```ini
Restart=on-failure
RestartSec=10
StartLimitBurst=5
StartLimitIntervalSec=600
MemoryMax=512M
CPUQuota=80%
TimeoutStopSec=30
```

#### muninn-web-portal.service
**Changes:**
- ✅ Same restart and resource protections
- ✅ Memory limits (256MB max)
- ✅ CPU quota (50% max)
- ✅ Graceful shutdown (15 second timeout)
- ✅ Starts after assistant service for proper ordering

### 2. Health Monitoring Tools

#### health_check.sh
A comprehensive health check script that shows:
- ✅ Service status and restart counts
- ✅ CPU temperature and usage
- ✅ Memory usage
- ✅ Disk usage
- ✅ Common issues detection
- ✅ Network connectivity

**Usage:**
```bash
./health_check.sh
```

#### system_monitor.py
A continuous monitoring service that:
- ✅ Monitors CPU, memory, disk, temperature
- ✅ Logs alerts when thresholds exceeded
- ✅ Has cooldown to prevent alert spam
- ✅ Checks for zombie processes
- ✅ Can run as a systemd service

**Usage:**
```bash
# Run manually (checks every 60 seconds)
python3 system_monitor.py 60

# Or install as service
sudo systemctl start muninn-monitor.service
```

#### muninn-monitor.service
Optional monitoring service that:
- ✅ Runs system_monitor.py continuously
- ✅ Has its own resource limits (128MB, 10% CPU)
- ✅ Logs to journald for easy viewing

### 3. Deployment Tools

#### deploy_services.sh
Automated deployment script that:
- ✅ Verifies prerequisites
- ✅ Backs up existing service files
- ✅ Installs new service files
- ✅ Enables and starts services
- ✅ Runs health check
- ✅ Provides next steps

**Usage:**
```bash
# On Raspberry Pi, after transferring files
cd /home/bw/muninn/muninn-v3/muninn-modular
./deploy_services.sh
```

### 4. Documentation

#### DEPLOYMENT.md
Comprehensive guide covering:
- ✅ Initial deployment steps
- ✅ Service management commands
- ✅ Health monitoring setup
- ✅ Troubleshooting procedures
- ✅ Common issues and solutions
- ✅ Maintenance tasks
- ✅ Quick reference commands

## Key Protections Added

### Restart Protection
**Problem:** Service restarted 18+ times, consuming resources
**Solution:**
```ini
StartLimitBurst=5              # Max 5 restart attempts
StartLimitIntervalSec=600      # Within 10 minutes
Restart=on-failure             # Only restart on failure
```

### Memory Protection
**Problem:** No limits on memory usage
**Solution:**
```ini
MemoryMax=512M      # Hard limit - process killed if exceeded
MemoryHigh=400M     # Soft limit - throttled if exceeded
```

### CPU Protection
**Problem:** Services could use 100% CPU
**Solution:**
```ini
CPUQuota=80%        # Assistant limited to 80% of one core
CPUQuota=50%        # Web portal limited to 50% of one core
```

### Graceful Shutdown
**Problem:** Services killed immediately on shutdown
**Solution:**
```ini
TimeoutStopSec=30    # 30 seconds for graceful shutdown
KillMode=mixed       # Try SIGTERM first, then SIGKILL
KillSignal=SIGTERM   # Clean shutdown signal
```

## Files Created/Modified

### Modified Files
1. `muninn-assistant.service` - Enhanced service configuration
2. `muninn-web-portal.service` - Enhanced service configuration

### New Files
1. `health_check.sh` - Health check script
2. `system_monitor.py` - Continuous monitoring script
3. `muninn-monitor.service` - Monitoring service
4. `deploy_services.sh` - Automated deployment script
5. `DEPLOYMENT.md` - Comprehensive documentation
6. `RELIABILITY_IMPROVEMENTS.md` - This file

## Deployment Steps

### Quick Deployment (from development machine)

```bash
# 1. Transfer files to Raspberry Pi
scp -r muninn-modular/* bw@raspberrypi:/home/bw/muninn/muninn-v3/muninn-modular/

# 2. SSH to Raspberry Pi
ssh bw@raspberrypi

# 3. Run deployment script
cd /home/bw/muninn/muninn-v3/muninn-modular
chmod +x deploy_services.sh
./deploy_services.sh

# 4. Verify services are running
./health_check.sh
```

### Manual Deployment (on Raspberry Pi)

```bash
cd /home/bw/muninn/muninn-v3/muninn-modular

# Make scripts executable
chmod +x health_check.sh
chmod +x system_monitor.py

# Copy service files
sudo cp muninn-assistant.service /etc/systemd/system/
sudo cp muninn-web-portal.service /etc/systemd/system/
sudo cp muninn-monitor.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable muninn-assistant.service
sudo systemctl enable muninn-web-portal.service

# Start services
sudo systemctl start muninn-assistant.service
sudo systemctl start muninn-web-portal.service

# Check status
./health_check.sh
```

## Monitoring and Maintenance

### Daily Checks
```bash
./health_check.sh
```

### Weekly Checks
```bash
# Check for errors in logs
sudo journalctl -u muninn-assistant --since "7 days ago" -p err

# Check disk space
df -h
```

### Monthly Maintenance
```bash
# Update system
sudo apt update && sudo apt upgrade

# Clean old logs
sudo journalctl --vacuum-time=2weeks

# Backup configuration
tar -czf muninn-backup-$(date +%Y%m%d).tar.gz \
  /home/bw/muninn/muninn-v3/muninn-modular/*.service \
  /home/bw/muninn/muninn-v3/messages.db
```

## Troubleshooting Quick Reference

### Service won't start
```bash
# Check logs
sudo journalctl -u muninn-assistant -n 50

# Look for path errors
sudo journalctl -u muninn-assistant -n 50 | grep "No such file"

# Verify Python path
which python3
grep "ExecStart=" /etc/systemd/system/muninn-assistant.service
```

### Service keeps restarting
```bash
# View restart counter
systemctl show muninn-assistant.service -p NRestarts

# Check recent logs for errors
sudo journalctl -u muninn-assistant -n 100 -p err

# Reset failed state
sudo systemctl reset-failed muninn-assistant.service
sudo systemctl restart muninn-assistant.service
```

### System unresponsive
```bash
# If you can still SSH in:
./health_check.sh

# Check resource usage
htop

# Stop services if needed
sudo systemctl stop muninn-assistant.service
sudo systemctl stop muninn-web-portal.service

# Review logs
sudo journalctl -n 200 -p err
```

### Check service limits
```bash
# View current resource usage
systemctl status muninn-assistant.service

# View detailed properties
systemctl show muninn-assistant.service | grep -E "Memory|CPU|Restart"
```

## Expected Behavior

### Normal Operation
- Services start cleanly with no errors
- CPU usage: 10-30% (depending on activity)
- Memory usage: 200-400MB for assistant, 100-200MB for web portal
- Temperature: Under 60°C idle, under 70°C under load
- No restarts unless manually triggered

### During Issues
- Services will attempt to restart up to 5 times
- After 5 failed attempts in 10 minutes, service stops
- If memory exceeds 512MB (assistant) or 256MB (portal), process is killed
- CPU throttled if exceeding quota
- All issues logged to journald

## Testing the Improvements

### Test 1: Verify Resource Limits
```bash
# Check limits are set
systemctl show muninn-assistant.service | grep -E "Memory|CPU"

# Should show:
# MemoryMax=536870912 (512MB)
# MemoryHigh=419430400 (400MB)
# CPUQuota=0.8 (80%)
```

### Test 2: Verify Restart Limits
```bash
# Check restart policy
systemctl show muninn-assistant.service | grep -E "Restart|StartLimit"

# Should show:
# Restart=on-failure
# StartLimitBurst=5
# StartLimitIntervalSec=600000000 (600 seconds)
```

### Test 3: Test Health Check
```bash
./health_check.sh

# Should show:
# - Service status
# - Resource usage
# - No critical errors
```

## Benefits

1. **Prevents System Hangs**
   - Resource limits prevent runaway processes
   - Restart limits prevent infinite loops

2. **Early Problem Detection**
   - Health monitoring catches issues early
   - Alerts before system becomes unresponsive

3. **Easier Troubleshooting**
   - Comprehensive logs with identifiers
   - Health check script shows system state
   - Documentation covers common issues

4. **Automatic Recovery**
   - Services restart on failure (up to limit)
   - Graceful shutdown prevents data corruption
   - Failed state resets automatically after interval

5. **Maintainability**
   - Automated deployment script
   - Clear documentation
   - Standardized logging

## Next Steps

1. **Deploy the improvements:**
   ```bash
   ./deploy_services.sh
   ```

2. **Monitor for 24-48 hours:**
   ```bash
   # Check every few hours
   ./health_check.sh

   # Review logs
   sudo journalctl -u muninn-assistant --since "1 hour ago"
   ```

3. **Adjust if needed:**
   - If hitting memory limits, increase MemoryMax
   - If CPU throttling is too aggressive, increase CPUQuota
   - If services fail to start, check Python path

4. **Set up periodic monitoring:**
   ```bash
   # Add to crontab for hourly checks
   crontab -e
   # Add: 0 * * * * /home/bw/muninn/muninn-v3/muninn-modular/health_check.sh >> /home/bw/muninn/muninn-v3/health_check.log 2>&1
   ```

## Support

For issues:
1. Run `./health_check.sh` and save output
2. Collect logs: `sudo journalctl -u muninn-assistant -n 200 > logs.txt`
3. Check DEPLOYMENT.md for common issues
4. Review service status: `systemctl status muninn-assistant.service`

---

**Created:** October 2024
**Version:** 1.0
