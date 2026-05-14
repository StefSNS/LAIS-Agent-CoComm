"""
MCP Bridge - Model Context Protocol Integration
Bridges MCP servers and tools to the LAIS coordination framework.
"""

import json
import subprocess
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class MCPTool:
    """Represents an MCP tool."""
    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    server_id: str = ""


class MCPServerConnection:
    """Connection to an MCP server."""

    def __init__(self, server_id: str, name: str, command: List[str], env: Dict = None):
        self.server_id = server_id
        self.name = name
        self.command = command
        self.env = env or {}
        self.process = None
        self.tools: List[MCPTool] = []
        self.connected = False

    def connect(self) -> bool:
        """Start the MCP server process."""
        try:
            full_env = {**subprocess.os.environ.copy(), **self.env}
            self.process = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=full_env
            )
            self.connected = True
            return True
        except Exception as e:
            print(f"[MCP Bridge] Failed to connect to {self.name}: {e}")
            return False

    def disconnect(self):
        """Stop the MCP server."""
        if self.process:
            self.process.terminate()
            self.process = None
        self.connected = False

    def call_tool(self, tool_name: str, arguments: Dict) -> Any:
        """Call a tool on the MCP server."""
        if not self.connected:
            return {"error": "Not connected"}

        request = {
            "jsonrpc": "2.0",
            "id": f"call_{datetime.now().timestamp()}",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        try:
            self.process.stdin.write(json.dumps(request).encode() + b"\n")
            self.process.stdin.flush()
            response = self.process.stdout.readline()
            return json.loads(response)
        except Exception as e:
            return {"error": str(e)}


class MCPBridge:
    """
    Bridge between MCP servers and the LAIS coordination framework.
    Discovers tools and exposes them to agents.
    """

    def __init__(self):
        self.servers: Dict[str, MCPServerConnection] = {}
        self.tools_by_name: Dict[str, MCPTool] = {}
        self.tools_by_server: Dict[str, List[MCPTool]] = {}

    def add_server(self, server_id: str, name: str, command: List[str], env: Dict = None) -> bool:
        """Add and connect an MCP server."""
        server = MCPServerConnection(server_id, name, command, env)
        if server.connect():
            self.servers[server_id] = server
            self.tools_by_server[server_id] = []
            return True
        return False

    def remove_server(self, server_id: str):
        """Remove an MCP server."""
        if server_id in self.servers:
            self.servers[server_id].disconnect()
            del self.servers[server_id]
            del self.tools_by_server[server_id]

    def register_tools(self, server_id: str, tools: List[MCPTool]):
        """Register tools from an MCP server."""
        for tool in tools:
            tool.server_id = server_id
            self.tools_by_name[tool.name] = tool
            if server_id not in self.tools_by_server:
                self.tools_by_server[server_id] = []
            self.tools_by_server[server_id].append(tool)

    def call_tool(self, tool_name: str, arguments: Dict) -> Any:
        """Call a tool by name."""
        tool = self.tools_by_name.get(tool_name)
        if not tool:
            return {"error": f"Tool not found: {tool_name}"}

        server = self.servers.get(tool.server_id)
        if not server:
            return {"error": f"Server not connected: {tool.server_id}"}

        return server.call_tool(tool_name, arguments)

    def find_tools(self, capability: str) -> List[MCPTool]:
        """Find tools matching a capability/keyword."""
        matches = []
        for tool in self.tools_by_name.values():
            if capability.lower() in tool.name.lower() or capability.lower() in tool.description.lower():
                matches.append(tool)
        return matches

    def get_all_tools(self) -> List[MCPTool]:
        """Get all registered tools."""
        return list(self.tools_by_name.values())

    def get_status(self) -> Dict[str, Any]:
        """Get bridge status."""
        return {
            "servers": len(self.servers),
            "connected": sum(1 for s in self.servers.values() if s.connected),
            "total_tools": len(self.tools_by_name),
            "servers_detail": {
                sid: {
                    "name": s.name,
                    "connected": s.connected,
                    "tools": len(self.tools_by_server.get(sid, []))
                }
                for sid, s in self.servers.items()
            }
        }


# Convenience function
def create_mcp_bridge() -> MCPBridge:
    """Create a new MCP bridge."""
    return MCPBridge()


# Example MCP server configs
MCP_SERVER_CONFIGS = {
    "filesystem": {
        "name": "Filesystem MCP",
        "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"],
        "tools": ["read_file", "write_file", "list_directory"]
    },
    "github": {
        "name": "GitHub MCP",
        "command": ["npx", "-y", "@modelcontextprotocol/server-github"],
        "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"},
        "tools": ["create_issue", "search_code", "get_repo"]
    },
    "slack": {
        "name": "Slack MCP",
        "command": ["npx", "-y", "@modelcontextprotocol/server-slack"],
        "env": {"SLACK_BOT_TOKEN": "${SLACK_BOT_TOKEN}"},
        "tools": ["send_message", "post_message", "list_channels"]
    }
}