"""
WebSocket Server - Real-time Agent Communication
Provides WebSocket-based messaging for agents.
"""

import asyncio
import json
import logging
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types."""
    AGENT_CONNECT = "agent_connect"
    AGENT_DISCONNECT = "agent_disconnect"
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    HEARTBEAT = "heartbeat"
    BROADCAST = "broadcast"


@dataclass
class AgentConnection:
    """Represents a connected agent."""
    agent_id: str
    name: str
    capabilities: List[str]
    connected_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)


@dataclass
class WebSocketMessage:
    """WebSocket message structure."""
    type: MessageType
    sender: str
    receiver: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class WebSocketServer:
    """
    WebSocket server for real-time agent communication.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.server = None
        self.connections: Dict[str, AgentConnection] = {}
        self.message_handlers: Dict[MessageType, List[Callable]] = {
            msg_type: [] for msg_type in MessageType
        }
        self._running = False

    async def start(self):
        """Start the WebSocket server."""
        self.server = await asyncio.start_server(
            self._handle_client,
            self.host,
            self.port
        )
        self._running = True
        logger.info(f"[WebSocket] Server started on {self.host}:{self.port}")

    async def stop(self):
        """Stop the WebSocket server."""
        self._running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        logger.info("[WebSocket] Server stopped")

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle a client connection."""
        addr = writer.get_extra_info('peername')
        client_id = f"{addr[0]}:{addr[1]}"
        logger.info(f"[WebSocket] Client connected: {client_id}")

        try:
            while self._running:
                try:
                    data = await reader.read(4096)
                    if not data:
                        break
                    message = json.loads(data.decode())
                    await self._process_message(client_id, message, writer)
                except json.JSONDecodeError:
                    logger.warning(f"[WebSocket] Invalid JSON from {client_id}")
                except asyncio.CancelledError:
                    break
        except Exception as e:
            logger.error(f"[WebSocket] Error with {client_id}: {e}")
        finally:
            if client_id in self.connections:
                del self.connections[client_id]
            writer.close()
            await writer.wait_closed()
            logger.info(f"[WebSocket] Client disconnected: {client_id}")

    async def _process_message(self, client_id: str, message: Dict, writer: asyncio.StreamWriter):
        """Process incoming message."""
        msg_type = message.get("type")
        try:
            msg_enum = MessageType(msg_type)
        except ValueError:
            logger.warning(f"[WebSocket] Unknown message type: {msg_type}")
            return

        if msg_enum == MessageType.AGENT_CONNECT:
            self.connections[client_id] = AgentConnection(
                agent_id=message.get("agent_id", client_id),
                name=message.get("name", "Unknown"),
                capabilities=message.get("capabilities", [])
            )
            logger.info(f"[WebSocket] Agent registered: {message.get('name')}")
            await self._send_response(writer, {
                "type": "connected",
                "agent_id": client_id
            })

        elif msg_enum == MessageType.HEARTBEAT:
            if client_id in self.connections:
                self.connections[client_id].last_heartbeat = datetime.now()

        elif msg_enum == MessageType.TASK_REQUEST:
            await self._handle_task_request(client_id, message, writer)

        elif msg_enum == MessageType.BROADCAST:
            await self._broadcast_message(client_id, message)

    async def _handle_task_request(self, client_id: str, message: Dict, writer: asyncio.StreamWriter):
        """Handle task request - route to appropriate agent."""
        target = message.get("target")
        task = message.get("task", {})

        if target and target in self.connections:
            await self._send_to_agent(target, {
                "type": "task_request",
                "from": client_id,
                "task": task
            })
        else:
            await self._send_response(writer, {
                "type": "error",
                "message": f"Target agent not found: {target}"
            })

    async def _send_to_agent(self, agent_id: str, message: Dict):
        """Send message to specific agent."""
        for conn_id, conn in self.connections.items():
            if conn.agent_id == agent_id:
                # In a real implementation, would send via the connection
                logger.info(f"[WebSocket] Forwarding to {agent_id}")
                break

    async def _broadcast_message(self, sender_id: str, message: Dict):
        """Broadcast message to all connected agents."""
        broadcast_msg = {
            "type": "broadcast",
            "from": sender_id,
            "payload": message.get("payload", {})
        }
        logger.info(f"[WebSocket] Broadcast from {sender_id}")

    async def _send_response(self, writer: asyncio.StreamWriter, message: Dict):
        """Send response to client."""
        writer.write(json.dumps(message).encode())
        await writer.drain()

    def register_handler(self, msg_type: MessageType, handler: Callable):
        """Register a message handler."""
        self.message_handlers[msg_type].append(handler)

    def get_connected_agents(self) -> List[Dict]:
        """Get list of connected agents."""
        return [
            {
                "agent_id": conn.agent_id,
                "name": conn.name,
                "capabilities": conn.capabilities,
                "connected_at": conn.connected_at.isoformat()
            }
            for conn in self.connections.values()
        ]

    def get_status(self) -> Dict:
        """Get server status."""
        return {
            "running": self._running,
            "host": self.host,
            "port": self.port,
            "connected_agents": len(self.connections),
            "agents": self.get_connected_agents()
        }


async def run_websocket_server(host: str = "127.0.0.1", port: int = 8765):
    """Run the WebSocket server."""
    server = WebSocketServer(host, port)
    await server.start()
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await server.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_websocket_server())