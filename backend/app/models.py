from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func
from .database import Base


class Metric(Base):
    """Model for storing system metrics history."""
    
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cpu = Column(Float, nullable=False)
    memory = Column(Float, nullable=False)
    disk = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), index=True)


class Alert(Base):
    """Model for storing system alerts."""
    
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    metric_type = Column(String(50), nullable=False, index=True)
    value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    message = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
