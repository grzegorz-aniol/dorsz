from agents import function_tool


@function_tool
def ask_human(question: str) -> str:
    """Zapytaj użytkownika o odpowiedź poprzez stdin.

    Args:
        question: Treść pytania do użytkownika.

    Returns:
        Odpowiedź użytkownika jako string.
    """

    print(f"\n🤔 Agent pytanie: {question}")
    print("👤 Twoja odpowiedź: ", end="", flush=True)
    response = input()
    return response
