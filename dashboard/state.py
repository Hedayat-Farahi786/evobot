"""
Dashboard state management
"""
from datetime import datetime
from typing import List, Optional
from fastapi import WebSocket


class BotState:
    """Global bot state"""
    def __init__(self):
        self.is_running = False
        self.is_connected_telegram = False
        self.is_connected_mt5 = False
        self.start_time: Optional[datetime] = None
        self.websocket_clients: List[WebSocket] = []
        self.current_user_id: Optional[str] = None


# Global instance
bot_state = BotState()


async def broadcast_to_clients(message: dict):
    """Broadcast message to all connected WebSocket clients"""
    for client in bot_state.websocket_clients[:]:
        try:
            await client.send_json(message)
        except:
            bot_state.websocket_clients.remove(client)
