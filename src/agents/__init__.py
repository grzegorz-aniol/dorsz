"""Project-facing facade for the OpenAI Agents SDK.

This local `agents` package lives in `src/` and serves two purposes:

* Re-export the core primitives from the real OpenAI Agents SDK installed via
  the `openai-agents` dependency, so code can simply `import agents`.
* Act as an extension point for project-specific modules such as
  `agents_ishikawa`, `agents_why5`, etc.

The test suite prepends `src/` to `sys.path`, which would normally cause this
package to shadow the SDK's own `agents` package. To avoid re‑implementing the
SDK, we dynamically locate and load the external package and delegate to it.
"""

from __future__ import annotations

from pathlib import Path
from types import ModuleType
from typing import Any
import importlib.util
import sys


_THIS_DIR = Path(__file__).resolve().parent


def _load_external_agents() -> ModuleType:
    """Load the real OpenAI Agents SDK package from site-packages.

    We intentionally bypass the normal import-by-name mechanism because this
    local package is also called `agents` and would otherwise shadow the SDK.
    Instead, we scan `sys.path` for another `agents/__init__.py` that does not
    live in `src/agents` and load it under an internal module name.
    """

    for entry in sys.path:
        try:
            base = Path(entry)
        except TypeError:
            # Some entries (like import hooks) are not file-system paths
            continue

        candidate = base / "agents" / "__init__.py"
        if not candidate.is_file():
            continue

        # Skip this very package directory
        if candidate.parent == _THIS_DIR:
            continue

        # Ensure our local `agents` package can see the external SDK's modules
        # when it performs imports like `from agents.model_settings import ...`.
        try:
            current_path = list(__path__)  # type: ignore[name-defined]
        except NameError:  # pragma: no cover - very defensive
            current_path = [str(_THIS_DIR)]
        ext_dir = str(candidate.parent)
        if ext_dir not in current_path:
            __path__ = [*current_path, ext_dir]  # type: ignore[assignment]

        spec = importlib.util.spec_from_file_location(
            "_external_agents_sdk", candidate
        )
        if spec is None or spec.loader is None:  # pragma: no cover - defensive
            continue

        module = importlib.util.module_from_spec(spec)
        # Register under its spec name so relative imports inside the SDK work
        # (e.g. `from . import _config`). In addition, temporarily alias the
        # top-level name `agents` to this module so that any absolute imports
        # inside the SDK like `from agents.model_settings import ModelSettings`
        # resolve against the SDK package rather than this local facade.
        sys.modules[spec.name] = module
        original_agents = sys.modules.get("agents")
        try:
            sys.modules["agents"] = module
            spec.loader.exec_module(module)  # type: ignore[arg-type]
        finally:
            if original_agents is not None:
                sys.modules["agents"] = original_agents
            else:  # pragma: no cover - defensive cleanup
                sys.modules.pop("agents", None)
        return module

    raise ImportError(
        "Could not locate external 'agents' SDK. "
        "Ensure the 'openai-agents' package is installed.",
    )


_external_agents = _load_external_agents()

# Make this package behave like a superset of the external SDK by extending the
# search path so that `import agents.stream_events` and similar imports find the
# modules provided by the real SDK.
if hasattr(_external_agents, "__path__"):
    __path__ = [str(_THIS_DIR), *list(_external_agents.__path__)]  # type: ignore[attr-defined]
else:  # pragma: no cover - highly unlikely for a package
    __path__ = [str(_THIS_DIR)]


# Re-export commonly used SDK symbols for convenience.
Agent: Any = _external_agents.Agent
AgentHooks: Any = getattr(_external_agents, "AgentHooks")
ItemHelpers: Any = getattr(_external_agents, "ItemHelpers")
ModelSettings: Any = _external_agents.ModelSettings
RunContextWrapper: Any = _external_agents.RunContextWrapper
RunResultStreaming: Any = _external_agents.RunResultStreaming
Runner: Any = _external_agents.Runner
Tool: Any = _external_agents.Tool
TContext: Any = _external_agents.TContext
function_tool: Any = _external_agents.function_tool
RunConfig: Any = _external_agents.RunConfig
set_default_openai_api: Any = _external_agents.set_default_openai_api
set_default_openai_client: Any = _external_agents.set_default_openai_client
set_tracing_disabled: Any = _external_agents.set_tracing_disabled


__all__ = [
    "Agent",
    "AgentHooks",
    "ItemHelpers",
    "ModelSettings",
    "RunContextWrapper",
    "RunResultStreaming",
    "Runner",
    "Tool",
    "TContext",
    "function_tool",
    "RunConfig",
    "set_default_openai_api",
    "set_default_openai_client",
    "set_tracing_disabled",
]
