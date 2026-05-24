"""
CoComm Agent Server - Start Script
Starts the cross-agent communication hub for LAIS + OpenCode integration.
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add CoComm to path - use parent (src/) not agent_sync/
COCOMM_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(COCOMM_PATH))

from agent_sync import (
    A2AServer,
    SharedMemory,
    ActiveSessionLog,
    WebSocketServer,
    AgentConfigLoader
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("cocomm")


class CoCommHub:
    """Central hub for all CoComm services."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.a2a_port = 8020
        self.ws_port = 8765
        
        self.a2a_server = None
        self.ws_server = None
        self.shared_memory = None
        self.session_log = None
        self.agent_config = None
        
        self._running = False

    async def start(self):
        """Start all CoComm services."""
        logger.info("=" * 50)
        logger.info("CoComm Agent Hub v0.5.2")
        logger.info("=" * 50)
        
        # Initialize shared memory
        mem_path = self.data_dir / "shared_memory.json"
        self.shared_memory = SharedMemory(mem_path)
        logger.info(f"Shared memory: {mem_path}")
        
        # Initialize session log
        session_path = self.data_dir / "sessions"
        self.session_log = ActiveSessionLog(session_path)
        logger.info(f"Session log: {session_path}")
        
        # Initialize agent config
        self.agent_config = AgentConfigLoader()
        logger.info(f"Agents loaded: {', '.join(a.agent_id for a in self.agent_config.list_agents())}")
        
        # Start A2A server (port 8020)
        self.a2a_server = A2AServer(port=self.a2a_port)
        await self.a2a_server.start()
        logger.info(f"A2A server started on port {self.a2a_port}")
        
        # Start WebSocket server (port 8765)
        self.ws_server = WebSocketServer(port=self.ws_port)
        await self.ws_server.start()
        logger.info(f"WebSocket server started on port {self.ws_port}")
        
        self._running = True
        logger.info("=" * 50)
        logger.info("CoComm Hub running!")
        logger.info(f"A2A:  localhost:{self.a2a_port}")
        logger.info(f"WS:    localhost:{self.ws_port}")
        logger.info("=" * 50)

    async def stop(self):
        """Stop all CoComm services."""
        logger.info("Stopping CoComm Hub...")
        
        if self.a2a_server:
            await self.a2a_server.stop()
        if self.ws_server:
            await self.ws_server.stop()
            
        self._running = False
        logger.info("CoComm Hub stopped.")

    def get_status(self) -> dict:
        """Get hub status."""
        return {
            "running": self._running,
            "a2a_port": self.a2a_port,
            "ws_port": self.ws_port,
            "agents": [a.agent_id for a in self.agent_config.list_agents()] if self.agent_config else [],
            "connected_agents": len(self.ws_server.connections) if self.ws_server else 0
        }


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="CoComm Agent Hub")
    parser.add_argument("--data-dir", default="C:/Users/stefa/Desktop/AI projects/integrations/cocomm/data", help="Data directory")
    parser.add_argument("--a2a-port", type=int, default=8020, help="A2A server port")
    parser.add_argument("--ws-port", type=int, default=8765, help="WebSocket server port")
    args = parser.parse_args()
    
    hub = CoCommHub(Path(args.data_dir))
    hub.a2a_port = args.a2a_port
    hub.ws_port = args.ws_port
    
    try:
        await hub.start()
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await hub.stop()


if __name__ == "__main__":
    asyncio.run(main())