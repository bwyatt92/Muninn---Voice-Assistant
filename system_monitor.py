#!/usr/bin/env python3
"""
Muninn System Monitor
Continuously monitors system health and logs alerts
Can be run as a standalone script or imported
"""

import psutil
import time
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
log_file = Path.home() / 'muninn' / 'muninn-v3' / 'system_monitor.log'
log_file.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SystemMonitor:
    """Monitor system resources and alert on issues"""

    def __init__(self,
                 cpu_threshold=85.0,
                 memory_threshold=85.0,
                 disk_threshold=90.0,
                 temp_threshold=75.0):
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold
        self.temp_threshold = temp_threshold

        self.alert_cooldown = {}  # Prevent alert spam
        self.cooldown_seconds = 300  # 5 minutes between same alerts

    def check_cpu(self):
        """Check CPU usage"""
        cpu_percent = psutil.cpu_percent(interval=1)

        if cpu_percent > self.cpu_threshold:
            if self._should_alert('cpu'):
                logger.warning(f"High CPU usage: {cpu_percent}%")
                return False

        return True

    def check_memory(self):
        """Check memory usage"""
        memory = psutil.virtual_memory()

        if memory.percent > self.memory_threshold:
            if self._should_alert('memory'):
                logger.warning(
                    f"High memory usage: {memory.percent}% "
                    f"({memory.used / (1024**3):.2f}GB / {memory.total / (1024**3):.2f}GB)"
                )
                return False

        return True

    def check_disk(self):
        """Check disk usage"""
        disk = psutil.disk_usage('/')

        if disk.percent > self.disk_threshold:
            if self._should_alert('disk'):
                logger.warning(
                    f"High disk usage: {disk.percent}% "
                    f"({disk.used / (1024**3):.2f}GB / {disk.total / (1024**3):.2f}GB)"
                )
                return False

        return True

    def check_temperature(self):
        """Check CPU temperature (Raspberry Pi specific)"""
        try:
            # Try to read Raspberry Pi temperature
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read().strip()) / 1000.0

                if temp > self.temp_threshold:
                    if self._should_alert('temperature'):
                        logger.warning(f"High CPU temperature: {temp}°C")
                        return False

                return True
        except FileNotFoundError:
            # Not on Raspberry Pi or thermal zone not available
            return True
        except Exception as e:
            logger.debug(f"Error reading temperature: {e}")
            return True

    def check_processes(self):
        """Check for zombie or problematic processes"""
        try:
            # Check for zombie processes
            zombies = [p for p in psutil.process_iter(['status'])
                      if p.info['status'] == psutil.STATUS_ZOMBIE]

            if zombies:
                if self._should_alert('zombies'):
                    logger.warning(f"Found {len(zombies)} zombie processes")
                    return False

            # Check for processes using excessive memory
            for proc in psutil.process_iter(['name', 'memory_percent']):
                if proc.info['memory_percent'] > 50:
                    logger.info(
                        f"High memory process: {proc.info['name']} "
                        f"using {proc.info['memory_percent']:.1f}% memory"
                    )

            return True
        except Exception as e:
            logger.debug(f"Error checking processes: {e}")
            return True

    def _should_alert(self, alert_type):
        """Check if we should send an alert (cooldown mechanism)"""
        now = time.time()
        last_alert = self.alert_cooldown.get(alert_type, 0)

        if now - last_alert > self.cooldown_seconds:
            self.alert_cooldown[alert_type] = now
            return True

        return False

    def run_checks(self):
        """Run all health checks"""
        results = {
            'cpu': self.check_cpu(),
            'memory': self.check_memory(),
            'disk': self.check_disk(),
            'temperature': self.check_temperature(),
            'processes': self.check_processes()
        }

        all_ok = all(results.values())

        if all_ok:
            logger.info("System health check: OK")
        else:
            failed = [k for k, v in results.items() if not v]
            logger.warning(f"System health check: Issues detected in {', '.join(failed)}")

        return all_ok

    def log_system_stats(self):
        """Log current system statistics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        logger.info(
            f"Stats - CPU: {cpu_percent}%, "
            f"Memory: {memory.percent}%, "
            f"Disk: {disk.percent}%"
        )

def monitor_loop(interval=60):
    """Run monitoring loop continuously"""
    monitor = SystemMonitor()

    logger.info("Starting Muninn system monitor")
    logger.info(f"Monitoring interval: {interval} seconds")

    try:
        while True:
            monitor.run_checks()
            monitor.log_system_stats()
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
    except Exception as e:
        logger.error(f"Monitor error: {e}")
        raise

if __name__ == '__main__':
    import sys

    # Parse command line arguments
    interval = 60  # Default 1 minute
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            print(f"Usage: {sys.argv[0]} [interval_seconds]")
            sys.exit(1)

    monitor_loop(interval)
