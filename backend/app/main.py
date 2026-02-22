import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db, init_db, SessionLocal
from .models import Metric
from .routes import auth, metrics, processes, docker
from .websocket.manager import connection_manager
from .services.metrics_collector import metrics_collector
from .auth import get_current_admin

settings = get_settings()


async def metrics_collection_task():
    """Background task to collect and store metrics every 5 seconds."""
    while True:
        try:
            db = SessionLocal()
            try:
                metrics_collector.collect_and_store_metrics(db)
            finally:
                db.close()
        except Exception as e:
            print(f"Error in metrics collection: {e}")
        
        await asyncio.sleep(settings.metrics_interval)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("Starting InfraSentinel Backend...")
    
    # Initialize database
    init_db()
    print("Database initialized")
    
    # Start background tasks
    metrics_task = asyncio.create_task(metrics_collection_task())
    connection_manager.start_background_tasks()
    print("Background tasks started")
    
    yield
    
    # Shutdown
    print("Shutting down InfraSentinel Backend...")
    metrics_task.cancel()
    try:
        await metrics_task
    except asyncio.CancelledError:
        pass


# Create FastAPI app
app = FastAPI(
    title="InfraSentinel",
    description="Admin-Only Full EC2 Host Monitoring System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware - allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(processes.router, prefix="/api")
app.include_router(docker.router)


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "name": "InfraSentinel",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "websocket_connections": connection_manager.connection_count
    }


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time metrics and process updates.
    
    Requires JWT token as query parameter.
    Broadcasts metrics and process list every 5 seconds.
    """
    # Connect with token verification
    connected = await connection_manager.connect(websocket, token)
    
    if not connected:
        return
    
    try:
        # Send initial data
        await connection_manager.send_personal_message(
            {
                "type": "connected",
                "message": "Successfully connected to InfraSentinel",
                "timestamp": datetime.utcnow().isoformat() + 'Z'
            },
            websocket
        )
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for any message from client (ping/pong handling)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=60.0  # Timeout to check connection health
                )
                
                # Handle ping messages
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_text("ping")
                except Exception:
                    break
                    
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)


@app.get("/api/status")
async def get_system_status(
    _: str = Depends(get_current_admin)
):
    """Get overall system status."""
    current_metrics = metrics_collector.collect_current_metrics()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": {
            "cpu": current_metrics.cpu,
            "memory": current_metrics.memory,
            "disk": current_metrics.disk
        },
        "websocket_connections": connection_manager.connection_count,
        "status": "operational"
    }
