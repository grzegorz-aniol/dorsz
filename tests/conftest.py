import sys
import pathlib
# Ensure src/ is on sys.path so local packages like 'tools' are importable during test collection
_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SRC_ROOT = _PROJECT_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

import os
import pytest
import socket
from urllib.parse import urlparse


def pytest_addoption(parser):
    parser.addoption(
        "--model",
        action="store",
        default=None,
        help="Override model for agent tests (falls back to env MODEL, then default).",
    )


@pytest.fixture(scope="session")
def agent_model(pytestconfig):
    """
    Resolve model in order of priority:
      1) CLI: --model
      2) ENV: MODEL
      3) Default: Bielik-4.5B-v3.0-Instruct.Q8_0.gguf
    """
    cli_value = pytestconfig.getoption("--model")
    if cli_value:
        return cli_value
    model = os.getenv("MODEL", "Bielik-4.5B-v3.0-Instruct.Q8_0.gguf")
    print("Model: ", model)
    return model


@pytest.fixture(scope="session")
def setup_agents_sdk():
    """
    Configure OpenAI Agents SDK with AsyncOpenAI client.
    Skips tests if required packages are missing or the LLM endpoint is unreachable.
    """
    agents_mod = pytest.importorskip(
        "agents",
        reason="OpenAI Agents SDK not installed",
    )
    lf_mod = pytest.importorskip(
        "openai",
        reason="openai is required",
    )

    AsyncOpenAI = lf_mod.AsyncOpenAI

    # Base URL for local OpenAI-compatible server (fixed for tests)
    base_url = "http://localhost:1234/v1"
    os.environ.setdefault("OPENAI_API_KEY", "EMPTY")

    # Check connectivity to base URL; skip if not reachable
    parsed = urlparse(base_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=1.5):
            pass
    except OSError:
        pytest.skip(f"LLM endpoint not reachable at {host}:{port} (base_url={base_url}). Start the local server at {base_url}.")

    client = AsyncOpenAI(
        base_url=base_url,
        api_key="EMPTY",
    )

    # Configure Agents SDK to use this client
    agents_mod.set_default_openai_client(client=client, use_for_tracing=False)
    agents_mod.set_default_openai_api("chat_completions")
    agents_mod.set_tracing_disabled(True)

    return {
        "agent": agents_mod.Agent,
        "runner": agents_mod.Runner,
        "function_tool": agents_mod.function_tool,
        "model_settings": agents_mod.ModelSettings,
        "RunConfig": agents_mod.RunConfig,
    }


@pytest.fixture
def make_tool(setup_agents_sdk):
    """
    Factory that creates a function_tool with a dynamic docstring.
    The underlying mock tool prints a marker and returns a fixed response.
    """
    function_tool = setup_agents_sdk["function_tool"]

    def _make_tool(docstring: str):
        def get_weather(city: str) -> str:
            """doc will be set dynamically"""
            print("*** TOOL get_weather called ***")
            print("Tool params: city =", city)
            return f"The weather in {city} is sunny with 22°C."

        # Set docstring dynamically so each test can describe the tool differently
        get_weather.__doc__ = docstring
        return function_tool(get_weather)

    return _make_tool


@pytest.fixture
def make_agent(setup_agents_sdk, agent_model):
    """
    Factory that builds an Agent with provided instructions and tools.
    Uses shared model resolved by agent_model fixture.
    """
    Agent = setup_agents_sdk["agent"]
    ModelSettings = setup_agents_sdk["model_settings"]

    def _make_agent(instructions: str, tools, model: str | None = None, temperature: float = 0.1):
        agents_mod_local = pytest.importorskip("agents")

        class SingleToolCallHooks(agents_mod_local.AgentHooks):
            async def on_tool_end(
                self,
                context,
                agent,
                tool,
                result: str,
            ) -> None:
                # Disable further tool usage after first successful call
                agent.tools = []

        return Agent(
            name="Temperature-Check",
            instructions=instructions,
            model=model or agent_model,
            model_settings=ModelSettings(temperature=temperature),
            tools=list(tools) if tools else [],
            hooks=SingleToolCallHooks(),
        )

    return _make_agent
