from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


# Authentication schemas
class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""
    username: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request body."""
    username: str
    password: str


# Metrics schemas
class MetricBase(BaseModel):
    """Base metric schema."""
    cpu: float
    memory: float
    disk: float


class MetricCreate(MetricBase):
    """Schema for creating a metric."""
    pass


class MetricResponse(MetricBase):
    """Schema for metric response."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class MetricsHistoryResponse(BaseModel):
    """Schema for metrics history response."""
    metrics: List[MetricResponse]
    total: int


class CurrentMetrics(BaseModel):
    """Current system metrics."""
    cpu: float
    memory: float
    disk: float
    timestamp: datetime


# Process schemas
class ProcessInfo(BaseModel):
    """Individual process information."""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    status: str
    username: Optional[str] = None


class ProcessListResponse(BaseModel):
    """Process list response."""
    processes: List[ProcessInfo]
    total_count: int
    timestamp: datetime


# Alert schemas
class AlertBase(BaseModel):
    """Base alert schema."""
    metric_type: str
    value: float
    threshold: float
    message: Optional[str] = None


class AlertResponse(AlertBase):
    """Alert response schema."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class AlertsListResponse(BaseModel):
    """Alerts list response."""
    alerts: List[AlertResponse]
    total: int


# WebSocket message schemas
class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    type: str  # "metrics" or "processes"
    data: dict
    timestamp: datetime


# Kill process schema
class KillProcessResponse(BaseModel):
    """Response for kill process endpoint."""
    success: bool
    message: str
    pid: int
