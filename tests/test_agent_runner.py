import textwrap

import asyncio


def test_weather_en_usecase(setup_agents_sdk, make_tool, make_agent, capsys):
    """
    Testing tool calling in a full English language scenario.
    - English tool docstring
    - English instructions
    - English prompt
    """
    # Prepare tool with English docstring
    tool = make_tool("Get the current weather for a city.")

    # English instructions
    instructions = (
        "You are a helpful assistant. "
        "Use the available tool at most once. "
        "If you have already called a tool, produce a final answer without any further tool calls."
    )

    # Build agent
    agent = make_agent(instructions=instructions, tools=[tool])

    runner = setup_agents_sdk["runner"]
    print("Running agent...")
    result = asyncio.run(
        asyncio.wait_for(
            runner.run(agent, "Check weather in Kraków"),
            timeout=60,
        )
    )
    print(f"Agent final_output: {result.final_output}")
    # Capture stdout and assert tool was executed
    captured = capsys.readouterr()
    marker_present = "*** TOOL get_weather called ***" in captured.out
    assert marker_present

    # Basic assertions (avoid tying to specific model outputs)
    assert result is not None
    assert hasattr(result, "final_output")
    assert isinstance(result.final_output, str)




def test_weather_pl_en_mix_usecase(setup_agents_sdk, make_tool, make_agent, capsys):
    """
    Testing tool calling with PL/EN mix use case:
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
            Uruchom narzędzie co najwyżej raz. Jeśli narzędzie zostało już uruchomione,
            zakończ odpowiedzią końcową bez kolejnych wywołań narzędzi.
            """

    # Build agent
    agent = make_agent(instructions=textwrap.dedent(instructions), tools=[tool])

    runner = setup_agents_sdk["runner"]
    print("Running agent...")
    result = asyncio.run(
        asyncio.wait_for(
            runner.run(agent, "Sprawdź pogodę w Krakowie"),
            timeout=60,
        )
    )
    print(f"Agent final_output: {result.final_output}")
    # Capture stdout and assert tool was executed
    captured = capsys.readouterr()
    marker_present = "*** TOOL get_weather called ***" in captured.out
    assert marker_present

    # Basic assertions (avoid tying to specific model outputs)
    assert result is not None
    assert hasattr(result, "final_output")
    assert isinstance(result.final_output, str)


def test_weather_pl_with_param_name_mismatch(setup_agents_sdk, make_tool, make_agent, capsys):
    """
    Testing tool calling in Polish with parameter name mismatch:
    - Polish tool description
    - Polish system instructions referencing get_weather tool
    - Instructions reference 'location' but tool requires 'city'
    - Polish user prompt asking for Warsaw weather
    """
    tool = make_tool("Pobierz aktualną pogodę dla wskazanej lokalizacji")

    instructions = (
        """
        Jesteś pomocnym asystentem, który dostarcza informacji o pogodzie. 
        Używaj narzędzia get_weather, gdy użytkownik pyta o pogodę.        
        Uruchom narzędzie co najwyżej raz. Jeśli narzędzie zostało już uruchomione,
        zakończ odpowiedzią końcową bez kolejnych wywołań narzędzi.
        """
    )

    # Build agent
    agent = make_agent(instructions=textwrap.dedent(instructions), tools=[tool])

    runner = setup_agents_sdk["runner"]
    print("Running agent (OpenAI example PL scenario)...")
    result = asyncio.run(
        asyncio.wait_for(
            runner.run(agent, "Jaka jest pogoda w Warszawie?"),
            timeout=60,
        )
    )
    print(f"Agent final_output: {result.final_output}")

    # Capture stdout and assert tool was executed
    captured = capsys.readouterr()
    marker_present = "*** TOOL get_weather called ***" in captured.out
    assert marker_present

    # Basic assertions
    assert result is not None



def test_weather_pl_usecase(setup_agents_sdk, make_tool, make_agent, capsys):
    """
    Testing tool calling with full Polish use case:
    - Polish tool docstring
    - Polish instructions
    - Polish prompt
    Just function name and parameter names remain in English as per tool definition.
    """
    # Prepare tool with Polish docstring
    tool = make_tool("Sprawdzenie aktualnej pogody dla miasta lub miejsca.")

    # Polish instructions
    instructions = """
        Jesteś asystentem, który pomaga użytkownikom w sprawdzaniu pogody w różnych miastach. 
        Uruchamiasz narzędzia, aby uzyskać aktualne informacje o pogodzie na podstawie zapytań użytkowników.
        Uruchom narzędzie co najwyżej raz. Jeśli narzędzie zostało już uruchomione,
        zakończ odpowiedzią końcową bez kolejnych wywołań narzędzi.
        """

    # Build agent
    agent = make_agent(instructions=textwrap.dedent(instructions), tools=[tool])

    runner = setup_agents_sdk["runner"]
    print("Running agent...")
    result = asyncio.run(
        asyncio.wait_for(
            runner.run(agent, "Sprawdź pogodę w Krakowie"),
            timeout=60,
        )
    )
    print(f"Agent final_output: {result.final_output}")
    # Capture stdout and assert tool was executed
    captured = capsys.readouterr()
    marker_present = "*** TOOL get_weather called ***" in captured.out
    assert marker_present

    # Basic assertions (avoid tying to specific model outputs)
    assert result is not None
    assert hasattr(result, "final_output")
    assert isinstance(result.final_output, str)
