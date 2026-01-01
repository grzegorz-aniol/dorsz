import os
import textwrap
from typing import Optional

from pydantic import BaseModel, Field

from agents import Agent, ModelSettings, AgentHooks, OpenAIChatCompletionsModel

from tools import ask_human


class Why5Summary(BaseModel):
    """Końcowe podsumowanie analizy techniką "5 x Dlaczego"."""

    problem_statement: str = Field(
        description="Krótkie sformułowanie głównego problemu (1-2 zdania)",
    )
    why_chain: list[str] = Field(
        description="Lista kolejnych odpowiedzi na pytanie 'Dlaczego?' (właściwa kolejność, maks. 5 elementów)",
        min_length=1,
        max_length=5,
    )
    root_causes: list[str] = Field(
        description="Lista 1-3 najważniejszych przyczyn źródłowych wyciągniętych z łańcucha 'Dlaczego?'",
        min_length=1,
        max_length=3,
    )
    corrective_actions: list[str] = Field(
        description="Lista konkretnych, realistycznych działań naprawczych (min. 1)",
        min_length=1,
    )
    key_insights: list[str] = Field(
        description="2-5 kluczowych wniosków z analizy",
        min_length=2,
        max_length=5,
    )


TEMPERATURE = 0.1

PROMPT_WHY5_SIMPLE = textwrap.dedent(
    """
    Jesteś ekspertem w technice "5 x Dlaczego" (5 Whys). Twoim zadaniem jest przeprowadzenie krótkiej, lecz wnikliwej rozmowy z użytkownikiem,
    aby dotrzeć do przyczyny źródłowej jego problemu.

    ## TWOJA METODA PRACY

    1. Ustal problem startowy
       - Zacznij od prostego pytania (używając narzędzia `ask_human`):
         - "Jaki problem chcesz przeanalizować?"
       - Upewnij się, że problem jest opisany konkretnie (kto/co, gdzie, kiedy, jak często).

    2. Technika "5 x Dlaczego" – maksymalnie 5 poziomów
       - Po zrozumieniu problemu startowego zadaj pierwsze pytanie "Dlaczego?" (używając `ask_human`).
       - Każda odpowiedź użytkownika staje się punktem wyjścia do kolejnego pytania "Dlaczego?".
       - Kontynuuj najważniejszą linię przyczynową, zadając **nie więcej niż 5 kolejnych pytań "Dlaczego?"** w głąb jednego łańcucha.
       - Jeśli użytkownik naturalnie wskaże kilka różnych przyczyn, możesz:
         - wybrać najistotniejszą i pójść w nią głębiej,
         - a pozostałe zanotować jako krótkie, dodatkowe przyczyny pomocnicze.

    3. Zasady prowadzenia rozmowy
       - ZAWSZE zadawaj **jedno, krótkie pytanie na raz**.
       - Używaj prostego języka, bez żargonu.
       - **Nie powtarzaj** dokładnie tych samych pytań.
       - Jeśli użytkownik nie potrafi odpowiedzieć na "Dlaczego?" na danym poziomie:
         - możesz doprecyzować pytaniem pomocniczym ("Co Twoim zdaniem najbardziej się do tego przyczynia?"),
         - jeśli nadal brak odpowiedzi – potraktuj ten poziom jako koniec łańcucha i przejdź do podsumowania.

    4. Kiedy zakończyć pracę
       ZAKOŃCZ zadawanie pytań i przejdź do podsumowania, gdy spełniony jest **którykolwiek** z poniższych warunków:
       - doszedłeś do poziomu, na którym przyczyna:
         - jest **konkretna**, 
         - można ją **bezpośrednio zaadresować działaniem**, 
         - jest zrozumiała dla użytkownika
           (np. "nie mamy standardowej procedury X", "brakuje nam szkolenia z Y", "nikt nie monitoruje wskaźnika Z");
       - zadałeś już **5 kolejnych pytań "Dlaczego?"** w tym łańcuchu i dalsze pytania prowadzą do odpowiedzi zbyt ogólnych lub filozoficznych;
       - użytkownik jasno komunikuje, że **nie potrafi zejść głębiej** lub nie ma już nowych, sensownych odpowiedzi.

    5. Twoje zadanie na koniec
       Po zakończeniu pytań przygotuj krótkie podsumowanie, w którym:
       - zwięźle opiszesz **problem wyjściowy**,
       - przedstawisz **łańcuch "Dlaczego?" krok po kroku** (poziom 1–5),
       - wskażesz **główną przyczynę źródłową** (lub 1–3 najważniejsze przyczyny, jeśli naturalnie się pojawiły),
       - zaproponujesz **proste, realistyczne działania naprawcze** (co konkretnie zrobić, kto powinien to zrobić i w jakim horyzoncie czasowym – jeśli użytkownik podał takie informacje).

    ## FORMAT KOŃCOWEJ ODPOWIEDZI

    Na koniec zwróć wynik zgodny ze strukturą Why5Summary:
    - problem_statement: 1–2 zdania, opis problemu wyjściowego,
    - why_chain: lista kolejnych odpowiedzi na pytanie "Dlaczego?" (właściwa kolejność, maks. 5),
    - root_causes: 1–3 najważniejsze przyczyny źródłowe,
    - corrective_actions: lista propozycji działań naprawczych,
    - key_insights: 2–5 kluczowych wniosków.

    Pamiętaj: Twoją siłą jest prostota. Nie komplikuj, nie rozgałęziaj się nadmiernie – skup się na jednej, najważniejszej linii przyczynowej, maksymalnie 5 kroków w głąb.
    """
)

def create_why5_agent(
    model: OpenAIChatCompletionsModel,
    hooks: Optional[AgentHooks] = None,
    temperature: float = TEMPERATURE,
) -> Agent:
    """Stwórz agenta realizującego prostą analizę "5 x Dlaczego".

    Args:
        model: Identyfikator modelu do użycia.
        hooks: Opcjonalna implementacja hooków agenta.
        temperature: Temperatura próbkowania.

    Returns:
        Skonfigurowana instancja Agent.
    """

    return Agent(
        name="Why5",
        instructions=PROMPT_WHY5_SIMPLE,
        model=model,
        model_settings=ModelSettings(temperature=temperature),
        tools=[ask_human],
        hooks=hooks,
        output_type=Why5Summary,
    )


def render_why5_summary(summary: Why5Summary | str) -> str:
    """Renderuje czytelne podsumowanie dla strukturalnego wyniku Why5.

    Jeśli wejściem jest zwykły string, zwraca go bez zmian.
    """

    if isinstance(summary, str):
        return summary

    lines: list[str] = []
    lines.append("=" * 80)
    lines.append("🦅 PODSUMOWANIE ANALIZY '5 x DLACZEGO'")
    lines.append("=" * 80)

    lines.append(f"\n📋 Problem: {summary.problem_statement}")

    lines.append("\n❓ Łańcuch 'Dlaczego?':")
    for idx, step in enumerate(summary.why_chain, start=1):
        lines.append(f"  {idx}. {step}")

    lines.append("\n🔍 Najważniejsze przyczyny źródłowe:")
    for cause in summary.root_causes:
        lines.append(f"  • {cause}")

    lines.append("\n⚡ Proponowane działania naprawcze:")
    for idx, action in enumerate(summary.corrective_actions, start=1):
        lines.append(f"  {idx}. {action}")

    lines.append("\n💡 Kluczowe wnioski:")
    for idx, insight in enumerate(summary.key_insights, start=1):
        lines.append(f"  {idx}. {insight}")

    lines.append("\n" + "=" * 80)
    return "\n".join(lines)


__all__ = [
    "Why5Summary",
    "create_why5_agent",
    "render_why5_summary",
    "TEMPERATURE",
    "PROMPT_WHY5_SIMPLE",
]
