# Muninn Reliability Fix - Quick Start Guide

## What Was Wrong

Your Raspberry Pi was becoming unresponsive because:
- ❌ Services restarted infinitely when failing (18+ times)
- ❌ No memory or CPU limits
- ❌ Python path errors causing constant failures
- ❌ No way to monitor system health

## What's Fixed

- ✅ Services now stop after 5 failed restart attempts
- ✅ Memory limits: 512MB for assistant, 256MB for web portal
- ✅ CPU limits: 80% for assistant, 50% for web portal
- ✅ Health monitoring tools added
- ✅ Comprehensive troubleshooting documentation

## Deploy Now (5 Minutes)

### From Your Computer

```bash
# Transfer files to Raspberry Pi
cd C:\Users\gpg-mchristian\muninn-voice-archive\muninn-modular
scp *.service *.sh *.py *.md bw@raspberrypi:/home/bw/muninn/muninn-v3/muninn-modular/
```

### On Raspberry Pi

```bash
# SSH to your Pi
ssh bw@raspberrypi

# Go to directory
cd /home/bw/muninn/muninn-v3/muninn-modular

# Run deployment script
chmod +x deploy_services.sh
./deploy_services.sh
```

The script will:
1. ✅ Back up old service files
2. ✅ Install new protected service files
3. ✅ Restart services
4. ✅ Run health check

## Verify It's Working

```bash
# Quick health check
./health_check.sh
```

You should see:
- ✅ Both services running
- ✅ Low restart counts (0 or 1)
- ✅ Normal resource usage
- ✅ No errors

## Monitor Over Time

```bash
# Check status anytime
./health_check.sh

# View live logs
sudo journalctl -u muninn-assistant -f

# Check service details
sudo systemctl status muninn-assistant.service
```

## What to Expect

### Before (Problem)
```
restart counter is at 12
restart counter is at 13
restart counter is at 14
...
[System becomes unresponsive]
```

### After (Fixed)
```
Service starts cleanly
If it fails, tries up to 5 times
Then stops and logs the error
System stays responsive
```

## If Something Goes Wrong

### Can't find Python
```bash
# Check Python path
which python3

# Update service file if needed
sudo nano /etc/systemd/system/muninn-assistant.service
# Change ExecStart line to correct path

sudo systemctl daemon-reload
sudo systemctl restart muninn-assistant.service
```

### Service won't start
```bash
# Check logs
sudo journalctl -u muninn-assistant -n 50

# Look for specific error
sudo journalctl -u muninn-assistant -n 50 | grep -i error
```

### Reset and try again
```bash
# Stop everything
sudo systemctl stop muninn-assistant.service
sudo systemctl stop muninn-web-portal.service

# Reset failed states
sudo systemctl reset-failed

# Start again
sudo systemctl start muninn-assistant.service
sudo systemctl start muninn-web-portal.service

# Check status
./health_check.sh
```

## Important Commands

```bash
# Health check (use this often!)
./health_check.sh

# View logs
sudo journalctl -u muninn-assistant -n 50

# Follow logs live
sudo journalctl -u muninn-assistant -f

# Restart services
sudo systemctl restart muninn-assistant.service

# Check restart count
systemctl show muninn-assistant.service -p NRestarts

# Check memory usage
systemctl status muninn-assistant.service
```

## Files Created

1. **muninn-assistant.service** - Protected service config
2. **muninn-web-portal.service** - Protected service config
3. **health_check.sh** - Quick health check script
4. **system_monitor.py** - Continuous monitoring
5. **deploy_services.sh** - Automated deployment
6. **DEPLOYMENT.md** - Full documentation
7. **RELIABILITY_IMPROVEMENTS.md** - Detailed changes

## Next Steps After Deployment

1. **Monitor for 24 hours**
   ```bash
   # Check every few hours
   ./health_check.sh
   ```

2. **Set up automatic monitoring**
   ```bash
   # Optional: Install monitoring service
   sudo systemctl enable muninn-monitor.service
   sudo systemctl start muninn-monitor.service
   ```

3. **Set up periodic checks**
   ```bash
   # Add hourly health check
   crontab -e
   # Add this line:
   # 0 * * * * /home/bw/muninn/muninn-v3/muninn-modular/health_check.sh >> /home/bw/muninn/health_check.log 2>&1
   ```

## Resource Limits Set

| Service | Memory Max | CPU Max | Restarts |
|---------|-----------|---------|----------|
| Assistant | 512MB | 80% | 5 in 10min |
| Web Portal | 256MB | 50% | 5 in 10min |
| Monitor (optional) | 128MB | 10% | 3 in 10min |

## Success Indicators

After deployment, you should see:
- ✅ Services start without errors
- ✅ Restart count stays at 0 or 1
- ✅ CPU usage: 10-30%
- ✅ Memory usage: Under 400MB for assistant
- ✅ Temperature: Under 70°C
- ✅ No "Failed to locate executable" errors
- ✅ System stays responsive

## Need More Help?

See detailed documentation:
- **DEPLOYMENT.md** - Full deployment and troubleshooting guide
- **RELIABILITY_IMPROVEMENTS.md** - Complete list of changes

Check status:
```bash
./health_check.sh
sudo journalctl -u muninn-assistant -n 50
```

---

**Time to deploy:** ~5 minutes
**Impact:** Prevents system hangs and unresponsiveness
**Risk:** Low (old service files backed up automatically)
