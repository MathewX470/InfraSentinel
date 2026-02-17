from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..auth import get_current_admin
from ..database import get_db
from ..models import Metric, Alert
from ..schemas import (
    MetricResponse, 
    MetricsHistoryResponse, 
    CurrentMetrics,
    AlertsListResponse,
    AlertResponse
)
from ..services.metrics_collector import metrics_collector

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/current", response_model=CurrentMetrics)
async def get_current_metrics(
    _: str = Depends(get_current_admin)
):
    """
    Get current system metrics (CPU, memory, disk).
    Real-time snapshot of system state.
    """
    return metrics_collector.collect_current_metrics()


@router.get("/history", response_model=MetricsHistoryResponse)
async def get_metrics_history(
    limit: int = Query(default=100, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    _: str = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get historical metrics from database.
    Returns metrics ordered by timestamp descending (most recent first).
    """
    # Get total count
    total = db.query(Metric).count()
    
    # Get metrics with pagination
    metrics = (
        db.query(Metric)
        .order_by(desc(Metric.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    return MetricsHistoryResponse(
        metrics=[MetricResponse.model_validate(m) for m in metrics],
        total=total
    )


@router.get("/cpu/detailed")
async def get_detailed_cpu(
    _: str = Depends(get_current_admin)
):
    """Get detailed CPU information including per-core usage."""
    return metrics_collector.get_detailed_cpu_info()


@router.get("/memory/detailed")
async def get_detailed_memory(
    _: str = Depends(get_current_admin)
):
    """Get detailed memory information."""
    return metrics_collector.get_detailed_memory_info()


@router.get("/disk/detailed")
async def get_detailed_disk(
    _: str = Depends(get_current_admin)
):
    """Get detailed disk information."""
    return metrics_collector.get_detailed_disk_info()


@router.get("/alerts", response_model=AlertsListResponse)
async def get_alerts(
    limit: int = Query(default=50, ge=1, le=500, description="Number of alerts to return"),
    offset: int = Query(default=0, ge=0, description="Number of alerts to skip"),
    metric_type: Optional[str] = Query(default=None, description="Filter by metric type"),
    _: str = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get system alerts from database.
    Returns alerts ordered by timestamp descending.
    """
    query = db.query(Alert)
    
    if metric_type:
        query = query.filter(Alert.metric_type == metric_type)
    
    total = query.count()
    
    alerts = (
        query
        .order_by(desc(Alert.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    return AlertsListResponse(
        alerts=[AlertResponse.model_validate(a) for a in alerts],
        total=total
    )


@router.delete("/history")
async def clear_metrics_history(
    older_than_hours: int = Query(default=24, ge=1, description="Clear metrics older than X hours"),
    _: str = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Clear old metrics from database.
    Helps manage database size.
    """
    from datetime import timedelta
    cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
    
    deleted_count = (
        db.query(Metric)
        .filter(Metric.created_at < cutoff_time)
        .delete()
    )
    
    db.commit()
    
    return {
        "deleted_count": deleted_count,
        "cutoff_time": cutoff_time.isoformat(),
        "message": f"Deleted {deleted_count} metrics older than {older_than_hours} hours"
    }
