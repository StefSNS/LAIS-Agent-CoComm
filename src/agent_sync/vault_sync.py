"""
Vault Integration - Obsidian Vault Sync
Provides integration with Obsidian vaults for persistent context.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class VaultIntegration:
    """Integration with Obsidian vault for context and knowledge."""

    def __init__(self, vault_path: str = None):
        if vault_path:
            self.vault_path = Path(vault_path)
        else:
            # Default to LAIS vault location
            self.vault_path = Path(os.environ.get(
                "LAIS_VAULT_PATH",
                "C:/Users/stefa/Desktop/AI projects/Obsidian/Unified Brain"
            ))

        if not self.vault_path.exists():
            print(f"[Vault] Warning: Vault not found at {self.vault_path}")

    def load_context(self) -> Dict[str, Any]:
        """Load session context from vault."""
        context = {"memory": {}, "agents": {}, "projects": []}

        # Load agent registry
        registry_path = self.vault_path / "40_System" / "agent_registry.md"
        if registry_path.exists():
            context["agents"] = self._parse_agent_registry(registry_path)

        # Load crystallized memory
        crystal_path = self.vault_path.parent / "Projects" / "models" / "ai_engine" / "knowledge" / "memory" / "crystallized.json"
        if crystal_path.exists():
            try:
                context["memory"]["crystallized"] = json.loads(crystal_path.read_text())
            except Exception:
                pass

        # Load active projects
        projects_path = self.vault_path / "40_System" / "Project States.md"
        if projects_path.exists():
            context["projects"] = self._parse_project_states(projects_path)

        return context

    def _parse_agent_registry(self, path: Path) -> Dict:
        """Parse agent registry markdown."""
        agents = {}
        content = path.read_text(encoding="utf-8")
        current_agent = None

        for line in content.split("\n"):
            if line.startswith("## "):
                current_agent = line.replace("## ", "").strip()
                agents[current_agent] = {"capabilities": []}
            elif line.startswith("- ID:") and current_agent:
                agents[current_agent]["id"] = line.replace("- ID:", "").strip()
            elif line.startswith("- Capabilities:") and current_agent:
                caps = line.replace("- Capabilities:", "").strip()
                agents[current_agent]["capabilities"] = [c.strip() for c in caps.split(",")]

        return agents

    def _parse_project_states(self, path: Path) -> List[str]:
        """Parse project states from markdown."""
        projects = []
        content = path.read_text(encoding="utf-8")

        for line in content.split("\n"):
            if line.startswith("- ") and ":" in line:
                projects.append(line.strip("- ").split(":")[0])

        return projects

    def search(self, query: str, folder: str = "10_Resources") -> List[Dict]:
        """Search vault notes for matching content."""
        results = []
        search_path = self.vault_path / folder

        if not search_path.exists():
            return results

        for note in search_path.glob("**/*.md"):
            try:
                content = note.read_text(encoding="utf-8")
                if query.lower() in content.lower():
                    results.append({
                        "path": str(note.relative_to(self.vault_path)),
                        "name": note.stem,
                        "preview": content[:200]
                    })
            except Exception:
                pass

        return results[:10]  # Limit results

    def write_note(self, relative_path: str, content: str):
        """Write a note to the vault."""
        note_path = self.vault_path / relative_path
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text(content, encoding="utf-8")

    def log_decision(self, title: str, details: Dict = None):
        """Log a decision to the vault decision log."""
        log_path = self.vault_path / "50_Memory" / "Decision Log.md"

        entry = f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n**{title}**\n"

        if details:
            entry += "```json\n"
            entry += json.dumps(details, indent=2) + "\n"
            entry += "```\n"

        if log_path.exists():
            existing = log_path.read_text(encoding="utf-8")
            log_path.write_text(existing + entry, encoding="utf-8")
        else:
            log_path.write_text(f"# Decision Log\n{entry}", encoding="utf-8")

    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status from registry."""
        registry_path = self.vault_path / "40_System" / "agent_registry.md"
        if not registry_path.exists():
            return {}

        return self._parse_agent_registry(registry_path)


def load_vault_context(vault_path: str = None) -> Dict:
    """Convenience function to load vault context."""
    vault = VaultIntegration(vault_path)
    return vault.load_context()


if __name__ == "__main__":
    vault = VaultIntegration()
    print("=== Vault Integration ===")
    print(f"Vault: {vault.vault_path}")

    context = vault.load_context()
    print(f"Agents: {len(context.get('agents', {}))}")
    print(f"Projects: {len(context.get('projects', []))}")

    # Test search
    results = vault.search("python")
    print(f"Search 'python': {len(results)} results")