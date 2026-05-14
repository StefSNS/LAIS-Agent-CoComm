"""
YAML-based agent configuration (from Orloj pattern)
Define agents, tools, policies, and permissions in declarative YAML.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class AgentConfig:
    """Agent definition from YAML."""
    id: str
    name: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    policies: List[str] = field(default_factory=list)
    max_retries: int = 3
    timeout: int = 300
    priority: str = "normal"


@dataclass
class ToolConfig:
    """Tool definition from YAML."""
    name: str
    type: str  # function, api, file
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    permissions: List[str] = field(default_factory=list)


@dataclass
class PolicyConfig:
    """Policy definition from YAML."""
    name: str
    rules: List[Dict[str, Any]] = field(default_factory=list)


class AgentConfigLoader:
    """Load agent configurations from YAML files."""

    DEFAULT_CONFIG_PATHS = [
        "config/agents.yaml",
        "config/agents.yml",
        "~/.lais/agents.yaml",
        "/etc/lais/agents.yaml"
    ]

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.agents: Dict[str, AgentConfig] = {}
        self.tools: Dict[str, ToolConfig] = {}
        self.policies: Dict[str, PolicyConfig] = {}

        if config_path:
            self.load(config_path)
        else:
            self._search_default_configs()

    def _search_default_configs(self):
        """Search default paths for config files."""
        for path_str in self.DEFAULT_CONFIG_PATHS:
            path = Path(path_str).expanduser()
            if path.exists():
                self.load(str(path))
                return

    def load(self, path: str):
        """Load configuration from YAML file."""
        path = Path(path)
        if not path.exists():
            print(f"[ConfigLoader] Config file not found: {path}")
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            # Load agents
            for agent_data in data.get("agents", []):
                agent = AgentConfig(**agent_data)
                self.agents[agent.id] = agent

            # Load tools
            for tool_data in data.get("tools", []):
                tool = ToolConfig(**tool_data)
                self.tools[tool.name] = tool

            # Load policies
            for policy_data in data.get("policies", []):
                policy = PolicyConfig(**policy_data)
                self.policies[policy.name] = policy

            print(f"[ConfigLoader] Loaded {len(self.agents)} agents, {len(self.tools)} tools, {len(self.policies)} policies")

        except Exception as e:
            print(f"[ConfigLoader] Error loading config: {e}")

    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent by ID."""
        return self.agents.get(agent_id)

    def get_tool(self, tool_name: str) -> Optional[ToolConfig]:
        """Get tool by name."""
        return self.tools.get(tool_name)

    def get_policy(self, policy_name: str) -> Optional[PolicyConfig]:
        """Get policy by name."""
        return self.policies.get(policy_name)

    def agents_with_capability(self, capability: str) -> List[AgentConfig]:
        """Get all agents with a specific capability."""
        return [a for a in self.agents.values() if capability in a.capabilities]

    def validate_agent(self, agent_id: str) -> bool:
        """Validate an agent configuration."""
        agent = self.get_agent(agent_id)
        if not agent:
            return False

        # Check all tools exist
        for tool in agent.tools:
            if tool not in self.tools:
                print(f"[ConfigLoader] Agent {agent_id} references unknown tool: {tool}")
                return False

        # Check all policies exist
        for policy in agent.policies:
            if policy not in self.policies:
                print(f"[ConfigLoader] Agent {agent_id} references unknown policy: {policy}")
                return False

        return True


def create_sample_config() -> str:
    """Create a sample YAML configuration."""
    return """
# LAIS Agent Configuration
agents:
  - id: coder
    name: Coder Agent
    description: Writes and modifies code
    capabilities:
      - code
      - shell
      - git
    tools:
      - terminal
      - file_editor
    policies:
      - safe_execution
    max_retries: 3
    timeout: 300

  - id: reviewer
    name: Code Reviewer Agent
    description: Reviews code for quality and bugs
    capabilities:
      - code
      - analysis
      - search
    tools:
      - code_analyzer
    policies:
      - thorough_review

  - id: tester
    name: Test Agent
    description: Creates and runs tests
    capabilities:
      - code
      - testing
    tools:
      - test_runner

tools:
  terminal:
    name: terminal
    type: function
    description: Execute shell commands
    parameters:
      command:
        type: string
        required: true

  file_editor:
    name: file_editor
    type: function
    description: Read and write files

  code_analyzer:
    name: code_analyzer
    type: function
    description: Analyze code quality

  test_runner:
    name: test_runner
    type: function
    description: Run test suites

policies:
  safe_execution:
    name: safe_execution
    rules:
      - action: deny
        pattern: "rm -rf /"
      - action: allow
        pattern: ".*"

  thorough_review:
    name: thorough_review
    rules:
      - require: all_files_checked
      - min_comments: 2
"""