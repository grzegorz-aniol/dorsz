import argparse
import logging
import os
from typing import Optional

import dotenv
from openai.types.responses import EasyInputMessageParam

dotenv.load_dotenv()

from langfuse.openai import AsyncOpenAI
from agents import (
    AgentHooks,
    RunContextWrapper,
    TContext,
    Tool,
    Runner,
    RunResultStreaming,
    ItemHelpers,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled, ModelSettings,
)
from agents.stream_events import (
    AgentUpdatedStreamEvent,
    RawResponsesStreamEvent,
    RunItemStreamEvent,
)
from agents.items import (
    MessageOutputItem,
    ToolCallItem,
    ToolCallOutputItem,
    TResponseInputItem,
    ModelResponse,
)

from agents_why5_ishikawa import (
    create_why5_ishikawa_agent,
    render_why5_ishikawa_summary,
)
from agents_temperature_check import (
    create_temperature_check_agent,
    render_temperature_report,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def setup_logging():
    """Konfiguracja logowania na stdout z prostym formatem."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    # Jeśli brak handlerów, dodaj StreamHandler
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s"
        )
        handler.setFormatter(formatter)
        root.addHandler(handler)
    # Upewnij się, że biblioteka 'agents' i ten moduł emitują na INFO
    logging.getLogger("agents").setLevel(logging.INFO)
    logging.getLogger(__name__).setLevel(logging.INFO)

# Default provider configuration (general runtime)
DEFAULT_PROVIDER = "local"
DEFAULT_LMS_BASE_URL = "http://localhost:1234/v1"
# Local provider settings overridable via env
LOCAL_BASE_URL = os.getenv("LOCAL_BASE_URL", DEFAULT_LMS_BASE_URL)
LOCAL_API_KEY = os.getenv("LOCAL_API_KEY", "EMPTY")

PROVIDER_CONFIGS = {
    "local": {"base_url": LOCAL_BASE_URL, "api_key": LOCAL_API_KEY},
    "openai": {"base_url": None, "api_key": None},  # Uses OpenAI defaults
}

# Agent registry (positional agent ID arg)
AGENT_IDS = ("why5_ishikawa", "temperature_check")

AGENT_FACTORIES = {
    "why5_ishikawa": create_why5_ishikawa_agent,
    "temperature_check": create_temperature_check_agent,
}

AGENT_RENDERERS = {
    "why5_ishikawa": render_why5_ishikawa_summary,
    "temperature_check": render_temperature_report,
}

# Default initial input per agent
AGENT_DEFAULT_INPUTS = {
    "why5_ishikawa": "Zapytaj mnie o problem, który chcę przeanalizować.",
    "temperature_check": "Jaka jest pogoda w Gliwicach?",
}

# Default model (can be overridden via env MODEL)
DEFAULT_MODEL = os.getenv("MODEL", "Bielik-4.5B-v3.0-Instruct.Q8_0.gguf")


def parse_args():
    """Parse command line arguments (general runtime).

    First positional argument is the agent ID.
    """
    parser = argparse.ArgumentParser(
        description="DORSZ - Dokładne Odpytywanie Rozpoznające Sedno Zagadnienia - Runtime"
    )
    parser.add_argument(
        "agent",
        choices=AGENT_IDS,
        help="Identyfikator agenta (wymagany). Dostępne: why5_ishikawa, temperature_check",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=DEFAULT_PROVIDER,
        choices=["local", "openai"],
        help="Provider do użycia (domyślnie: local)",
    )
    parser.add_argument(
        "--model",
        type=str,
        required=False,
        default=None,
        help="Nazwa modelu do użycia (jeśli pominięta, użyje ENV MODEL lub domyślnego).",
    )
    return parser.parse_args()


async def process_stream(result: RunResultStreaming):
    """Przetwarza i wyświetla wydarzenia ze streamu agenta (ogólny runtime)."""
    async for event in result.stream_events():
        # Pomijamy surowe tokeny (zbyt szczegółowe)
        if isinstance(event, RawResponsesStreamEvent):
            continue

        # Agent zmienił się (handoff)
        elif isinstance(event, AgentUpdatedStreamEvent):
            print(f"\n🔄 Przełączono na agenta: {event.new_agent.name}")

        # Zakończony element (wiadomość, narzędzie, itp.)
        elif isinstance(event, RunItemStreamEvent):
            if isinstance(event.item, MessageOutputItem):
                # To jest "myślenie" agenta
                text = ItemHelpers.text_message_output(event.item)
                if text.strip():
                    print(f"\n🤖 Agent: {text}")

            elif isinstance(event.item, ToolCallItem):
                # Agent wywołuje narzędzie
                tool_name = getattr(event.item.raw_item, "name", "unknown")
                arguments = getattr(event.item.raw_item, "arguments", "{}")
                print(f"\n🔧 Wywołanie narzędzia: {tool_name}")
                print(f"   Parametry: {arguments}")

            elif isinstance(event.item, ToolCallOutputItem):
                # Wynik narzędzia
                print(f"✅ Wynik: {event.item.output}")


def create_client(provider: str) -> AsyncOpenAI:
    """Tworzy i ustawia domyślnego klienta OpenAI lub lokalnego endpointu (ogólny runtime)."""
    provider_config = PROVIDER_CONFIGS[provider]
    if provider == "openai":
        # For OpenAI, use default client (requires OPENAI_API_KEY env var)
        client = AsyncOpenAI()
    else:
        # For local provider
        client = AsyncOpenAI(
            base_url=provider_config["base_url"],
            api_key=provider_config["api_key"],
        )

    # Set as default OpenAI client and configure for Bielik
    set_default_openai_client(client=client, use_for_tracing=False)
    set_default_openai_api("chat_completions")  # Force chat completions API
    set_tracing_disabled(True)  # Disable tracing to avoid API key issues

    return client


class CustomAgentHooks(AgentHooks):
    """Przykładowe wspólne hooki agenta (ogólny runtime, wielokrotnego użytku)."""

    async def on_tool_start(
        self,
        context: RunContextWrapper[TContext],
        agent,
        tool: Tool,
    ) -> None:
        logger.info("Tool %s is about to be invoked by agent %s", tool.name, agent.name)

    async def on_tool_end(
        self,
        context: RunContextWrapper[TContext],
        agent,
        tool: Tool,
        result: str,
    ) -> None:
        logger.info("Tool %s execution is done", tool.name)

    async def on_llm_start(
        self,
        context: RunContextWrapper[TContext],
        agent,
        system_prompt: Optional[str],
        input_items: list[TResponseInputItem],
    ) -> None:
        logger.info("%s", input_items)

    async def on_llm_end(
        self,
        context: RunContextWrapper[TContext],
        agent,
        response: ModelResponse,
    ) -> None:
        logger.info("%s", response)


async def main():
    # Konfiguracja logowania
    setup_logging()
    logger.info("Logowanie skonfigurowane — start runtime")

    # Parse command line arguments
    args = parse_args()

    # Configure client based on provider
    create_client(args.provider)

    # Determine model to use with env fallback
    model_to_use = args.model or os.getenv("MODEL", DEFAULT_MODEL)

    # Build the agent using selected factory (agent-specific config resides in dedicated module)
    agent = AGENT_FACTORIES[args.agent](
        model=model_to_use,
        hooks=CustomAgentHooks(),
        temperature=0.1,
    )

    print("DORSZ - Dokładne Odpytywanie Rozpoznające Sedno Zagadnienia")
    print(f"Provider: {args.provider}")
    print(f"Model: {model_to_use}")
    print(f"Agent: {args.agent}")

    # Initial input for agent runtime
    initial_input = AGENT_DEFAULT_INPUTS[args.agent]

    # Run the agent without streaming (streaming support provided by process_stream)
    result = await Runner.run(agent, input=initial_input, max_turns=50)

    # Print the final structured result using agent-specific renderer
    summary = result.final_output
    print("Agent response:", AGENT_RENDERERS[args.agent](summary))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
