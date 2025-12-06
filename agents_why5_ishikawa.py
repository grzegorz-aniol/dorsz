import textwrap
from enum import Enum
from typing import Optional
import os

from pydantic import BaseModel, Field

from agents import Agent, ModelSettings, function_tool, AgentHooks


# Domain models (structured output)
class IshikawaCategory(str, Enum):
    """Kategorie diagramu Ishikawy (5M+E)"""
    MAN = "Człowiek"  # Umiejętności, wiedza, błędy ludzkie, motywacja, komunikacja
    MACHINE = "Maszyna"  # Narzędzia, sprzęt, oprogramowanie, technologia
    MATERIAL = "Materiał"  # Surowce, dane wejściowe, zasoby, informacje
    METHOD = "Metoda"  # Procesy, procedury, sposób pracy, workflow
    MANAGEMENT = "Zarządzanie"  # Decyzje, organizacja, priorytety, kultura
    ENVIRONMENT = "Środowisko"  # Warunki zewnętrzne, kontekst, otoczenie


class RootCause(BaseModel):
    """Pojedyncza przyczyna źródłowa odkryta w analizie"""
    description: str = Field(
        description="Opis przyczyny źródłowej - konkretny, jasny i zwięzły"
    )
    category: IshikawaCategory = Field(
        description="Kategoria Ishikawy, do której należy ta przyczyna"
    )
    depth_level: int = Field(
        description="Poziom głębokości w analizie '5 Dlaczego' (1-15)",
        ge=1,
        le=15
    )


class CorrectiveAction(BaseModel):
    """Sugerowane działanie naprawcze"""
    action: str = Field(
        description="Konkretne działanie do podjęcia"
    )
    target_causes: list[str] = Field(
        description="Lista opisów przyczyn, które to działanie adresuje"
    )
    priority: str = Field(
        description="Priorytet: 'Wysoki', 'Średni' lub 'Niski'"
    )


class Why5IshikawaSummary(BaseModel):
    """Końcowe podsumowanie analizy '5 Dlaczego' + Ishikawa"""
    problem_statement: str = Field(
        description="Krótkie sformułowanie głównego problemu, który był analizowany"
    )
    root_causes: list[RootCause] = Field(
        description="Lista odkrytych przyczyn źródłowych z przypisaniem do kategorii Ishikawy",
        min_length=1
    )
    corrective_actions: list[CorrectiveAction] = Field(
        description="Lista sugerowanych działań naprawczych",
        min_length=1
    )
    key_insights: list[str] = Field(
        description="Kluczowe wnioski i spostrzeżenia z całej analizy (2-5 punktów)",
        min_length=2,
        max_length=5
    )


# Why5-Ishikawa specific configuration
TEMPERATURE = 0.1

PROMPT_WHY5 = textwrap.dedent("""
Jesteś ekspertem w analizie przyczyn źródłowych. Twoim zadaniem jest przeprowadzenie głębokiej rozmowy z użytkownikiem,
aby odkryć prawdziwe, podstawowe przyczyny jego problemu lub sytuacji.

## TWOJA METODA PRACY:

Rozpocznij rozmowę od zapytania użytkownika o problem, który chce przeanalizować.
Ważne!! Musisz użyć narzędzia `ask_human` i to kilkukrotnie, zanim spróbujesz formuować wnioski. 


1. **Technika "5 Dlaczego"**:
   - Zadawaj proste, bezpośrednie pytania typu: "Dlaczego?", "Dlaczego tak robisz?", "Co sprawiło, że to się stało?"
   - Każda odpowiedź użytkownika to punkt wyjścia do kolejnego pytania
   - Schodź głębiej - nie zadowalaj się powierzchownymi odpowiedziami
   - Typowo potrzeba 5-15 iteracji, aby dotrzeć do sedna problemu

2. **Eksploruj różne ścieżki**:
   - Jeśli użytkownik utknął i nie potrafi pójść głębiej w danym kierunku, WRÓĆ do wcześniejszych odpowiedzi
   - Wybierz inny aspekt, który wspomniał i eksploruj go: "Wspomniałeś wcześniej o X. Dlaczego to się dzieje?"
   - Problem rzadko ma jedną przyczynę - szukaj różnych wątków
   - Gdy ścieżka grzęźnie, zaproponuj inną, niebanalną hipotezę lub kąt spojrzenia i zadaj jedno alternatywne pytanie, które może zmienić perspektywę (np. „a próbowałeś zniwelować zapach ryby cytryną?” albo „a dlaczego chcesz jeść ryby?”)

3. **Mapowanie do kategorii Ishikawy (5M+E)**:
   - Podczas rozmowy obserwuj, do których kategorii należą odkrywane przyczyny:
     * **Człowiek (Man)**: umiejętności, wiedza, błędy ludzkie, motywacja, komunikacja
     * **Maszyna (Machine)**: narzędzia, sprzęt, oprogramowanie, technologia
     * **Materiał (Material)**: surowce, dane wejściowe, zasoby, informacje
     * **Metoda (Method)**: procesy, procedury, sposób pracy, workflow
     * **Zarządzanie (Management)**: decyzje, organizacja, priorytety, kultura organizacyjna
     * **Środowisko (Environment)**: warunki zewnętrzne, kontekst, otoczenie fizyczne lub biznesowe

4. **Zasady prowadzenia rozmowy**:
   - Zadawaj ZAWSZE jedno pytanie na raz
   - Pytania powinny być krótkie i proste
   - Nie powtarzaj pytań, które już zadałeś
   - Unikaj żargonu i skomplikowanych sformułowań
   - Bądź empatyczny ale dociekliwy
   - Bądź wytrwały, ale unikaj pytań zbyt fundamentalnych lub nierozstrzygalnych (np. „dlaczego mdli cię, gdy jesz rybę?”); gdy do nich dojdziesz, przerwij ten wątek i zbadaj inną, sprawdzalną ścieżkę przyczynową.
   - Nie zakładaj odpowiedzi - pozwól użytkownikowi myśleć
   - Używaj narzędzia `ask_human` do zadawania pytań

5. **Kiedy zakończyć**:
   - Gdy użytkownik dotarł do przyczyn podstawowych (root causes) - takich, które można bezpośrednio zaadresować
   - Gdy zbadałeś już główne ścieżki przyczynowe
   - Gdy masz wystarczająco dużo materiału do stworzenia diagramu Ishikawy

## TWOJE ZADANIE:

1. Rozpocznij od zrozumienia podstawowego problemu użytkownika
2. Prowadź rozmowę metodą "5 Dlaczego" - zadawaj proste pytania i schodź w głąb
3. Eksploruj różne aspekty i wątki
4. Na koniec przedstaw:
   - Podsumowanie odkrytych przyczyn źródłowych
   - Mapowanie przyczyn do kategorii Ishikawy (5M+E)
   - Sugestie działań naprawczych dla najważniejszych przyczyn

Pamiętaj: Twoja siła leży w prostocie pytań i wytrwałości w dociekaniu. Nie bój się zadać "Dlaczego?" kolejny raz.

## FORMAT ODPOWIEDZI:

Na koniec analizy zwróć strukturalny wynik zawierający:
- **problem_statement**: Krótkie sformułowanie problemu (1-2 zdania)
- **root_causes**: Lista przyczyn źródłowych, każda z:
  - description: opis przyczyny
  - category: jedna z kategorii Ishikawy (Człowiek/Maszyna/Materiał/Metoda/Zarządzanie/Środowisko)
  - depth_level: poziom głębokości w analizie (1-15)
- **corrective_actions**: Lista działań naprawczych, każde z:
  - action: konkretne działanie do podjęcia
  - target_causes: lista opisów przyczyn, które to działanie adresuje
  - priority: "Wysoki", "Średni" lub "Niski"
- **key_insights**: 2-5 kluczowych wniosków z analizy

""")


# Dedicated tool(s) used by this agent
@function_tool
def ask_human(question: str) -> str:
    """
    Ask the human user a question and wait for their response via stdin.
    Use this tool when you need clarification or additional information from the user.

    Args:
        question: The question to ask the human user

    Returns:
        The user's response as a string
    """
    print(f"\n🤔 Agent pytanie: {question}")
    print("👤 Twoja odpowiedź: ", end="", flush=True)
    response = input()
    return response


# Default model from environment (fallback)
DEFAULT_MODEL = os.getenv("MODEL", "Bielik-4.5B-v3.0-Instruct.Q8_0.gguf")

# Factory method
def create_why5_ishikawa_agent(
    model: str | None = None,
    hooks: Optional[AgentHooks] = None,
    temperature: float = TEMPERATURE,
) -> Agent:
    """
    Create and configure the Why5-Ishikawa agent.

    Args:
        model: model identifier to use
        hooks: optional AgentHooks implementation
        temperature: sampling temperature (default from module)

    Returns:
        Configured Agent instance
    """
    return Agent(
        name="Why5-Ishikawa",
        instructions=PROMPT_WHY5,
        model=model or DEFAULT_MODEL,
        model_settings=ModelSettings(temperature=temperature),
        tools=[ask_human],
        hooks=hooks,
        output_type=Why5IshikawaSummary,
    )


def render_why5_ishikawa_summary(summary: Why5IshikawaSummary) -> str:
    """
    Render a human-friendly summary for the Why5-Ishikawa structured output.
    """
    from collections import defaultdict

    lines: list[str] = []
    lines.append("=" * 80)
    lines.append("🦅 PODSUMOWANIE ANALIZY '5 DLACZEGO' + ISHIKAWA")
    lines.append("=" * 80)

    lines.append(f"\n📋 Problem: {summary.problem_statement}")

    lines.append(f"\n🔍 Odkryte przyczyny źródłowe ({len(summary.root_causes)}):")
    by_category = defaultdict(list)
    for cause in summary.root_causes:
        by_category[cause.category].append(cause)

    for category in IshikawaCategory:
        causes = by_category.get(category, [])
        if causes:
            lines.append(f"\n  📌 {category.value}:")
            for cause in sorted(causes, key=lambda c: c.depth_level):
                lines.append(f"     • {cause.description} (poziom: {cause.depth_level})")

    lines.append(f"\n⚡ Działania naprawcze ({len(summary.corrective_actions)}):")
    for i, action in enumerate(summary.corrective_actions, 1):
        extra = f" + {len(action.target_causes)-2} więcej" if len(action.target_causes) > 2 else ""
        targets = ", ".join(action.target_causes[:2]) + extra
        lines.append(f"\n  {i}. [{action.priority}] {action.action}")
        lines.append(f"     Adresuje: {targets}")

    lines.append(f"\n💡 Kluczowe wnioski:")
    for i, insight in enumerate(summary.key_insights, 1):
        lines.append(f"  {i}. {insight}")

    lines.append("\n" + "=" * 80)
    return "\n".join(lines)


__all__ = [
    "IshikawaCategory",
    "RootCause",
    "CorrectiveAction",
    "Why5IshikawaSummary",
    "ask_human",
    "create_why5_ishikawa_agent",
    "TEMPERATURE",
    "PROMPT_WHY5",
    "render_why5_ishikawa_summary",
]
