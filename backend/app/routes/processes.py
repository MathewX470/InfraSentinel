from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from ..auth import get_current_admin
from ..schemas import ProcessListResponse, ProcessInfo, KillProcessResponse
from ..services.process_monitor import process_monitor

router = APIRouter(prefix="/processes", tags=["Processes"])


@router.get("", response_model=ProcessListResponse)
async def get_processes(
    limit: int = Query(default=20, ge=1, le=100, description="Number of processes to return"),
    sort_by: str = Query(default="cpu", regex="^(cpu|memory)$", description="Sort by cpu or memory"),
    _: str = Depends(get_current_admin)
):
    """
    Get top processes from the host machine.
    
    Returns processes sorted by CPU or memory usage.
    This endpoint provides real-time process information.
    """
    return process_monitor.get_top_processes(limit=limit, sort_by=sort_by)


@router.get("/top-cpu", response_model=list[ProcessInfo])
async def get_top_cpu_processes(
    limit: int = Query(default=10, ge=1, le=50, description="Number of processes"),
    _: str = Depends(get_current_admin)
):
    """Get top CPU-consuming processes."""
    return process_monitor.get_top_cpu_consumers(limit=limit)


@router.get("/top-memory", response_model=list[ProcessInfo])
async def get_top_memory_processes(
    limit: int = Query(default=10, ge=1, le=50, description="Number of processes"),
    _: str = Depends(get_current_admin)
):
    """Get top memory-consuming processes."""
    return process_monitor.get_top_memory_consumers(limit=limit)


@router.get("/count")
async def get_process_count(
    _: str = Depends(get_current_admin)
):
    """Get total number of running processes on the host."""
    count = process_monitor.get_process_count()
    return {"count": count}


@router.get("/{pid}", response_model=ProcessInfo)
async def get_process_by_pid(
    pid: int,
    _: str = Depends(get_current_admin)
):
    """Get information about a specific process by PID."""
    process = process_monitor.get_process_by_pid(pid)
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Process with PID {pid} not found"
        )
    return process


@router.post("/kill/{pid}", response_model=KillProcessResponse)
async def kill_process(
    pid: int,
    force: bool = Query(default=False, description="Force kill (SIGKILL) instead of terminate (SIGTERM)"),
    admin: str = Depends(get_current_admin)
):
    """
    Terminate a process by PID.
    
    ADMIN ONLY: This endpoint kills processes on the host machine.
    Use with caution - killing system processes may affect stability.
    
    Args:
        pid: Process ID to terminate
        force: If True, uses SIGKILL (force kill); otherwise uses SIGTERM (graceful)
    """
    # Safety check: Don't allow killing PID 1 (init/systemd)
    if pid == 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot kill init process (PID 1)"
        )
    
    success, message = process_monitor.kill_process(pid, force=force)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return KillProcessResponse(
        success=success,
        message=message,
        pid=pid
    )
