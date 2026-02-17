import os
import psutil
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from ..config import get_settings
from ..models import Metric
from ..schemas import CurrentMetrics, MetricCreate

settings = get_settings()


class MetricsCollector:
    """Service for collecting system metrics from host machine."""
    
    def __init__(self):
        """Initialize the metrics collector with host paths."""
        self.host_proc = settings.host_proc
        self.host_root = settings.host_root
        
        # Set psutil to use host /proc if available
        if os.path.exists(self.host_proc):
            os.environ['PSUTIL_HOSTPROC'] = self.host_proc
    
    def get_cpu_percent(self, interval: float = 1.0) -> float:
        """
        Get total CPU usage percentage.
        Uses interval to measure CPU usage over time.
        """
        try:
            return psutil.cpu_percent(interval=interval)
        except Exception as e:
            print(f"Error getting CPU percent: {e}")
            return 0.0
    
    def get_memory_percent(self) -> float:
        """Get total memory usage percentage."""
        try:
            memory = psutil.virtual_memory()
            return memory.percent
        except Exception as e:
            print(f"Error getting memory percent: {e}")
            return 0.0
    
    def get_disk_percent(self, path: str = '/') -> float:
        """
        Get disk usage percentage.
        Uses host root mount point if available.
        """
        try:
            # Try to use host root mount for accurate disk info
            disk_path = self.host_root if os.path.exists(self.host_root) else path
            disk = psutil.disk_usage(disk_path)
            return disk.percent
        except Exception as e:
            print(f"Error getting disk percent: {e}")
            # Fallback to container root
            try:
                disk = psutil.disk_usage('/')
                return disk.percent
            except:
                return 0.0
    
    def collect_current_metrics(self) -> CurrentMetrics:
        """Collect all current metrics."""
        return CurrentMetrics(
            cpu=self.get_cpu_percent(interval=0.5),  # Shorter interval for real-time
            memory=self.get_memory_percent(),
            disk=self.get_disk_percent(),
            timestamp=datetime.utcnow()
        )
    
    def collect_and_store_metrics(self, db: Session) -> Metric:
        """Collect metrics and store them in the database."""
        cpu = self.get_cpu_percent(interval=1.0)
        memory = self.get_memory_percent()
        disk = self.get_disk_percent()
        
        metric = Metric(
            cpu=cpu,
            memory=memory,
            disk=disk
        )
        
        db.add(metric)
        db.commit()
        db.refresh(metric)
        
        return metric
    
    def get_detailed_cpu_info(self) -> dict:
        """Get detailed CPU information."""
        try:
            return {
                "percent_per_cpu": psutil.cpu_percent(percpu=True),
                "count_logical": psutil.cpu_count(logical=True),
                "count_physical": psutil.cpu_count(logical=False),
                "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            }
        except Exception as e:
            print(f"Error getting detailed CPU info: {e}")
            return {}
    
    def get_detailed_memory_info(self) -> dict:
        """Get detailed memory information."""
        try:
            mem = psutil.virtual_memory()
            return {
                "total": mem.total,
                "available": mem.available,
                "used": mem.used,
                "percent": mem.percent,
                "total_gb": round(mem.total / (1024**3), 2),
                "used_gb": round(mem.used / (1024**3), 2)
            }
        except Exception as e:
            print(f"Error getting detailed memory info: {e}")
            return {}
    
    def get_detailed_disk_info(self) -> dict:
        """Get detailed disk information."""
        try:
            disk_path = self.host_root if os.path.exists(self.host_root) else '/'
            disk = psutil.disk_usage(disk_path)
            return {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent,
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2)
            }
        except Exception as e:
            print(f"Error getting detailed disk info: {e}")
            return {}


# Singleton instance
metrics_collector = MetricsCollector()
