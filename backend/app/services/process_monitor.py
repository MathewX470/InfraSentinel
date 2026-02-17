import os
import psutil
from datetime import datetime
from typing import List, Optional
from ..config import get_settings
from ..schemas import ProcessInfo, ProcessListResponse

settings = get_settings()


class ProcessMonitor:
    """Service for monitoring host processes."""
    
    def __init__(self):
        """Initialize the process monitor."""
        self.host_proc = settings.host_proc
        self.process_limit = settings.process_limit
        
        # Set psutil to use host /proc if available
        if os.path.exists(self.host_proc):
            os.environ['PSUTIL_HOSTPROC'] = self.host_proc
    
    def get_all_processes(self) -> List[ProcessInfo]:
        """
        Get list of all running processes on the host.
        Returns process info sorted by CPU usage descending.
        """
        processes = []
        
        # Iterate through all processes
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'username']):
            try:
                info = proc.info
                process = ProcessInfo(
                    pid=info['pid'],
                    name=info['name'] or 'Unknown',
                    cpu_percent=info['cpu_percent'] or 0.0,
                    memory_percent=round(info['memory_percent'] or 0.0, 2),
                    status=info['status'] or 'unknown',
                    username=info.get('username')
                )
                processes.append(process)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Process may have terminated or we don't have access
                continue
            except Exception as e:
                # Log but don't crash on unexpected errors
                continue
        
        # Sort by CPU usage descending
        processes.sort(key=lambda p: p.cpu_percent, reverse=True)
        
        return processes
    
    def get_top_processes(self, limit: Optional[int] = None, sort_by: str = 'cpu') -> ProcessListResponse:
        """
        Get top processes sorted by CPU or memory usage.
        
        Args:
            limit: Maximum number of processes to return (default: settings.process_limit)
            sort_by: Sort criterion - 'cpu' or 'memory'
        
        Returns:
            ProcessListResponse with top processes
        """
        if limit is None:
            limit = self.process_limit
        
        all_processes = self.get_all_processes()
        
        # Sort by the specified criterion
        if sort_by == 'memory':
            all_processes.sort(key=lambda p: p.memory_percent, reverse=True)
        else:
            all_processes.sort(key=lambda p: p.cpu_percent, reverse=True)
        
        top_processes = all_processes[:limit]
        
        return ProcessListResponse(
            processes=top_processes,
            total_count=len(all_processes),
            timestamp=datetime.utcnow()
        )
    
    def get_top_cpu_consumers(self, limit: Optional[int] = None) -> List[ProcessInfo]:
        """Get top CPU-consuming processes."""
        if limit is None:
            limit = self.process_limit
        
        all_processes = self.get_all_processes()
        all_processes.sort(key=lambda p: p.cpu_percent, reverse=True)
        return all_processes[:limit]
    
    def get_top_memory_consumers(self, limit: Optional[int] = None) -> List[ProcessInfo]:
        """Get top memory-consuming processes."""
        if limit is None:
            limit = self.process_limit
        
        all_processes = self.get_all_processes()
        all_processes.sort(key=lambda p: p.memory_percent, reverse=True)
        return all_processes[:limit]
    
    def get_process_by_pid(self, pid: int) -> Optional[ProcessInfo]:
        """Get information about a specific process by PID."""
        try:
            proc = psutil.Process(pid)
            with proc.oneshot():
                return ProcessInfo(
                    pid=proc.pid,
                    name=proc.name(),
                    cpu_percent=proc.cpu_percent(),
                    memory_percent=round(proc.memory_percent(), 2),
                    status=proc.status(),
                    username=proc.username() if hasattr(proc, 'username') else None
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
    
    def kill_process(self, pid: int, force: bool = False) -> tuple[bool, str]:
        """
        Terminate or kill a process by PID.
        
        Args:
            pid: Process ID to terminate
            force: If True, use SIGKILL; otherwise use SIGTERM
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            proc = psutil.Process(pid)
            process_name = proc.name()
            
            if force:
                proc.kill()  # SIGKILL
                return True, f"Process {process_name} (PID: {pid}) was killed"
            else:
                proc.terminate()  # SIGTERM
                return True, f"Process {process_name} (PID: {pid}) was terminated"
                
        except psutil.NoSuchProcess:
            return False, f"Process with PID {pid} does not exist"
        except psutil.AccessDenied:
            return False, f"Access denied: Cannot terminate process {pid}"
        except Exception as e:
            return False, f"Error terminating process {pid}: {str(e)}"
    
    def get_process_count(self) -> int:
        """Get total number of running processes."""
        return len(list(psutil.process_iter()))
    
    def refresh_cpu_percent(self):
        """
        Refresh CPU percent for all processes.
        Should be called before get_all_processes for accurate readings.
        """
        # First call to establish baseline
        for proc in psutil.process_iter(['cpu_percent']):
            try:
                proc.cpu_percent()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue


# Singleton instance
process_monitor = ProcessMonitor()
