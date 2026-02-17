#!/usr/bin/env python3
"""
InfraSentinel Alert Worker Service

Monitors the latest metrics and creates alerts when thresholds are exceeded.
Runs as a separate container, polling the database every 5 seconds.
"""

import os
import time
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, desc, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+pymysql://monitor_user:monitor_pass@db:3306/monitoring')
CPU_ALERT_THRESHOLD = float(os.getenv('CPU_ALERT_THRESHOLD', '80'))
MEMORY_ALERT_THRESHOLD = float(os.getenv('MEMORY_ALERT_THRESHOLD', '80'))
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', '5'))
ALERT_COOLDOWN = int(os.getenv('ALERT_COOLDOWN', '60'))  # Seconds between same-type alerts

# Database setup
Base = declarative_base()


class Metric(Base):
    """Metrics table model."""
    __tablename__ = 'metrics'
    
    id = Column(Integer, primary_key=True)
    cpu = Column(Float, nullable=False)
    memory = Column(Float, nullable=False)
    disk = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Alert(Base):
    """Alerts table model."""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    metric_type = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    message = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())


class AlertWorker:
    """Worker service for monitoring metrics and creating alerts."""
    
    def __init__(self):
        self.engine = None
        self.Session = None
        self.last_alerts = {}  # Track last alert time per metric type
        self._connect_db()
    
    def _connect_db(self):
        """Establish database connection with retry logic."""
        max_retries = 30
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                self.engine = create_engine(
                    DATABASE_URL,
                    pool_pre_ping=True,
                    pool_recycle=3600
                )
                self.Session = sessionmaker(bind=self.engine)
                
                # Test connection
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                
                logger.info("Successfully connected to database")
                return
            except Exception as e:
                logger.warning(f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise RuntimeError("Could not connect to database after maximum retries")
    
    def get_latest_metric(self):
        """Get the most recent metric from the database."""
        session = self.Session()
        try:
            metric = session.query(Metric).order_by(desc(Metric.created_at)).first()
            return metric
        finally:
            session.close()
    
    def can_create_alert(self, metric_type: str) -> bool:
        """Check if enough time has passed since the last alert of this type."""
        last_alert_time = self.last_alerts.get(metric_type)
        if last_alert_time is None:
            return True
        
        elapsed = datetime.utcnow() - last_alert_time
        return elapsed.total_seconds() >= ALERT_COOLDOWN
    
    def create_alert(self, metric_type: str, value: float, threshold: float):
        """Create a new alert in the database."""
        if not self.can_create_alert(metric_type):
            logger.debug(f"Skipping {metric_type} alert (cooldown active)")
            return
        
        session = self.Session()
        try:
            message = f"{metric_type.upper()} usage at {value:.1f}% exceeded threshold of {threshold:.1f}%"
            
            alert = Alert(
                metric_type=metric_type,
                value=value,
                threshold=threshold,
                message=message
            )
            
            session.add(alert)
            session.commit()
            
            self.last_alerts[metric_type] = datetime.utcnow()
            
            logger.warning(f"ALERT: {message}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create alert: {e}")
        finally:
            session.close()
    
    def check_thresholds(self, metric: Metric):
        """Check if metric values exceed thresholds and create alerts."""
        if metric.cpu > CPU_ALERT_THRESHOLD:
            self.create_alert('cpu', metric.cpu, CPU_ALERT_THRESHOLD)
        
        if metric.memory > MEMORY_ALERT_THRESHOLD:
            self.create_alert('memory', metric.memory, MEMORY_ALERT_THRESHOLD)
    
    def run(self):
        """Main worker loop."""
        logger.info("=" * 60)
        logger.info("InfraSentinel Alert Worker Started")
        logger.info(f"CPU Alert Threshold: {CPU_ALERT_THRESHOLD}%")
        logger.info(f"Memory Alert Threshold: {MEMORY_ALERT_THRESHOLD}%")
        logger.info(f"Poll Interval: {POLL_INTERVAL}s")
        logger.info(f"Alert Cooldown: {ALERT_COOLDOWN}s")
        logger.info("=" * 60)
        
        last_metric_id = None
        
        while True:
            try:
                metric = self.get_latest_metric()
                
                if metric is None:
                    logger.debug("No metrics found in database yet")
                elif metric.id != last_metric_id:
                    # New metric to process
                    last_metric_id = metric.id
                    logger.info(f"Processing metric: CPU={metric.cpu:.1f}%, Memory={metric.memory:.1f}%, Disk={metric.disk:.1f}%")
                    self.check_thresholds(metric)
                
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                # Try to reconnect on database errors
                try:
                    self._connect_db()
                except Exception:
                    pass
            
            time.sleep(POLL_INTERVAL)


def main():
    """Entry point for the worker."""
    try:
        worker = AlertWorker()
        worker.run()
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        raise


if __name__ == '__main__':
    main()
