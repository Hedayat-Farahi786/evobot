"""
WebSocket Connection Manager
Singleton instance for handling WebSocket connections across the application.
"""
import logging
from typing import List, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger("evobot.websocket")

class ConnectionManager:
    """Manages WebSocket connections and broadcasting"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConnectionManager, cls).__new__(cls)
            cls._instance.active_connections = []
        return cls._instance
    
    def __init__(self):
        # Already initialized in __new__, but safe to keep for type hinting or IDEs
        if not hasattr(self, 'active_connections'):
            self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept connection and add to active list"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.debug(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove connection from active list"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.debug(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
            
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

# Global singleton instance
manager = ConnectionManager()
