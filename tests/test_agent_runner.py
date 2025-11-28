import pytest
import asyncio


def test_weather_en_usecase(setup_agents_sdk, make_tool, make_agent, capsys):
    """
    English use case:
    - English tool docstring
    - English instructions
    - English prompt
    """
    # Prepare tool with English docstring
    tool = make_tool("Get the current weather for a city.")

    # English instructions
    instructions = "You are a helpful assistant. Use the available tools when needed."

    # Build agent
    agent = make_agent(instructions=instructions, tools=[tool])

    Runner = setup_agents_sdk["Runner"]
    print("Running agent...")
    result = asyncio.run(asyncio.wait_for(Runner.run(agent, "Check weather in Kraków"), timeout=20))
    print(f"Agent final_output: {result.final_output}")
    # Capture stdout and assert tool was executed
    captured = capsys.readouterr()
    assert "*** TOOL get_weather called ***" in captured.out

    # Basic assertions (avoid tying to specific model outputs)
    assert result is not None
    assert hasattr(result, "final_output")
    assert isinstance(result.final_output, str)


def test_weather_pl_en_mix_usecase(setup_agents_sdk, make_tool, make_agent, capsys):
    """
    PL/EN mix use case:
    - English tool docstring
    - Polish instructions
    - Polish prompt
    """
    # Prepare tool with English docstring
    tool = make_tool("Get the current weather for a city.")

    # Polish instructions
    instructions = """
            Jesteś asystentem, który pomaga użytkownikom w sprawdzaniu pogody w różnych miastach. 
            Uruchamiasz narzędzia, aby uzyskać aktualne informacje o pogodzie na podstawie zapytań użytkowników.
            """

    # Build agent
    agent = make_agent(instructions=instructions, tools=[tool])

    Runner = setup_agents_sdk["Runner"]
    print("Running agent...")
    result = asyncio.run(asyncio.wait_for(Runner.run(agent, "Sprawdź pogodę w Krakowie"), timeout=20))
    print(f"Agent final_output: {result.final_output}")
    # Capture stdout and assert tool was executed
    captured = capsys.readouterr()
    assert "*** TOOL get_weather called ***" in captured.out

    # Basic assertions (avoid tying to specific model outputs)
    assert result is not None
    assert hasattr(result, "final_output")
    assert isinstance(result.final_output, str)


def test_weather_pl_usecase(setup_agents_sdk, make_tool, make_agent, capsys):
    """
    Polish use case:
    - Polish tool docstring
    - Polish instructions
    - Polish prompt
    """
    # Prepare tool with Polish docstring
    tool = make_tool("Sprawdzenie aktualnej pogody dla miasta lub miejsca.")

    # Polish instructions
    instructions = """
            Jesteś asystentem, który pomaga użytkownikom w sprawdzaniu pogody w różnych miastach. 
            Uruchamiasz narzędzia, aby uzyskać aktualne informacje o pogodzie na podstawie zapytań użytkowników.
            """

    # Build agent
    agent = make_agent(instructions=instructions, tools=[tool])

    Runner = setup_agents_sdk["Runner"]
    print("Running agent...")
    result = asyncio.run(asyncio.wait_for(Runner.run(agent, "Sprawdź pogodę w Krakowie"), timeout=20))
    print(f"Agent final_output: {result.final_output}")
    # Capture stdout and assert tool was executed
    captured = capsys.readouterr()
    assert "*** TOOL get_weather called ***" in captured.out

    # Basic assertions (avoid tying to specific model outputs)
    assert result is not None
    assert hasattr(result, "final_output")
    assert isinstance(result.final_output, str)
