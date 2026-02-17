import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from ..config import get_settings
from ..services.metrics_collector import metrics_collector
from ..services.process_monitor import process_monitor

settings = get_settings()


class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._broadcast_task: asyncio.Task = None
    
    async def connect(self, websocket: WebSocket, token: str) -> bool:
        """
        Accept a new WebSocket connection after verifying the JWT token.
        
        Returns True if connection was accepted, False otherwise.
        """
        # Verify JWT token
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            username = payload.get("sub")
            if username != settings.admin_username:
                await websocket.close(code=4003, reason="Unauthorized")
                return False
        except JWTError:
            await websocket.close(code=4001, reason="Invalid token")
            return False
        
        await websocket.accept()
        self.active_connections.append(websocket)
        return True
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_json(message)
        except Exception:
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_metrics(self):
        """Collect and broadcast current metrics."""
        try:
            metrics = metrics_collector.collect_current_metrics()
            message = {
                "type": "metrics",
                "data": {
                    "cpu": metrics.cpu,
                    "memory": metrics.memory,
                    "disk": metrics.disk
                },
                "timestamp": metrics.timestamp.isoformat()
            }
            await self.broadcast(message)
        except Exception as e:
            print(f"Error broadcasting metrics: {e}")
    
    async def broadcast_processes(self):
        """Collect and broadcast process list."""
        try:
            process_list = process_monitor.get_top_processes(limit=20)
            message = {
                "type": "processes",
                "data": {
                    "processes": [
                        {
                            "pid": p.pid,
                            "name": p.name,
                            "cpu_percent": p.cpu_percent,
                            "memory_percent": p.memory_percent,
                            "status": p.status,
                            "username": p.username
                        }
                        for p in process_list.processes
                    ],
                    "total_count": process_list.total_count
                },
                "timestamp": process_list.timestamp.isoformat()
            }
            await self.broadcast(message)
        except Exception as e:
            print(f"Error broadcasting processes: {e}")
    
    async def start_broadcast_loop(self):
        """Start the background loop that broadcasts updates."""
        while True:
            if self.active_connections:
                await self.broadcast_metrics()
                await self.broadcast_processes()
            await asyncio.sleep(settings.metrics_interval)
    
    def start_background_tasks(self):
        """Start background broadcast tasks."""
        if self._broadcast_task is None or self._broadcast_task.done():
            self._broadcast_task = asyncio.create_task(self.start_broadcast_loop())
    
    @property
    def connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)


# Singleton instance
connection_manager = ConnectionManager()
