"""Local, project-specific agents built on top of the OpenAI Agents SDK.

This package contains only *your* agents (why5, Ishikawa, etc.).
The official SDK remains available as the top-level ``agents`` package
installed from the ``openai-agents`` dependency.

Usage examples::

    from agents import Agent, ModelSettings  # SDK primitives
    from local_agents.agents_ishikawa import create_ishikawa_agent

This keeps imports simple and avoids any dynamic import tricks.
"""

__all__ = [
    # Re-export local agent factories/renderers here if you ever want
    # ``from local_agents import create_why5_agent`` style imports.
    # For now we keep this empty and import from concrete modules.
]
