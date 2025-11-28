import os
import pytest
import socket
from urllib.parse import urlparse


def pytest_addoption(parser):
    parser.addoption(
        "--model",
        action="store",
        default=None,
        help="Override model for agent tests (falls back to env AGENT_TEST_MODEL, then default).",
    )


@pytest.fixture(scope="session")
def agent_model(pytestconfig):
    """
    Resolve model in order of priority:
      1) CLI: --model
      2) ENV: AGENT_TEST_MODEL
      3) Default: bielik-4.5b-v3.0-instruct-mlx
    """
    cli_value = pytestconfig.getoption("--model")
    if cli_value:
        return cli_value
    model = os.getenv("AGENT_TEST_MODEL", "bielik-4.5b-v3.0-instruct-mlx")
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

    # Base URL can be overridden via AGENT_TEST_BASE_URL
    base_url = os.getenv("AGENT_TEST_BASE_URL", "http://localhost:1234/v1")
    os.environ.setdefault("OPENAI_API_KEY", "EMPTY")

    # Check connectivity to base URL; skip if not reachable
    parsed = urlparse(base_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=1.5):
            pass
    except OSError:
        pytest.skip(f"LLM endpoint not reachable at {host}:{port} (base_url={base_url}). Set AGENT_TEST_BASE_URL or start the server.")

    client = AsyncOpenAI(
        base_url=base_url,
        api_key="EMPTY",
    )

    # Configure Agents SDK to use this client
    agents_mod.set_default_openai_client(client=client, use_for_tracing=False)
    agents_mod.set_default_openai_api("chat_completions")
    agents_mod.set_tracing_disabled(True)

    return {
        "Agent": agents_mod.Agent,
        "Runner": agents_mod.Runner,
        "function_tool": agents_mod.function_tool,
        "ModelSettings": agents_mod.ModelSettings,
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
    Agent = setup_agents_sdk["Agent"]
    ModelSettings = setup_agents_sdk["ModelSettings"]

    def _make_agent(instructions: str, tools, model: str | None = None, temperature: float = 0.1):
        return Agent(
            name="Temperature-Check",
            instructions=instructions,
            model=model or agent_model,
            model_settings=ModelSettings(temperature=temperature),
            tools=list(tools) if tools else [],
        )

    return _make_agent
