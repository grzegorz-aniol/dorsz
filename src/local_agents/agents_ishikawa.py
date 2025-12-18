import os
import textwrap
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from agents import Agent, ModelSettings, function_tool, AgentHooks
from tools.topics_registry import (
    add_topic,
    mark_topic_answered,
    next_unanswered_topic,
    get_topics_summary,
)

from tools import ask_human


class IshikawaCategory(str, Enum):
    """Kategorie diagramu Ishikawy (5M+E)."""

    MAN = "Człowiek"  # Kompetencje, umiejętności, motywacja, komunikacja, błędy ludzkie
    MACHINE = "Maszyna"  # Urządzenia, narzędzia, sprzęt, oprogramowanie, systemy IT
    MATERIAL = "Materiał"  # Surowce, komponenty, dane wejściowe, informacje
    METHOD = "Metoda"  # Procesy, procedury, instrukcje, standardy pracy, workflow
    MEASUREMENT = "Pomiary"  # Wskaźniki, KPI, sposób mierzenia, narzędzia pomiarowe, raportowanie
    ENVIRONMENT = "Środowisko"  # Warunki otoczenia fizycznego i biznesowego


class IshikawaRootCause(BaseModel):
    """Pojedyncza przyczyna źródłowa odkryta w analizie Ishikawy."""

    description: str = Field(
        description="Opis przyczyny źródłowej - konkretny, jasny i zwięzły",
    )
    category: IshikawaCategory = Field(
        description="Kategoria Ishikawy, do której należy ta przyczyna",
    )
    depth_level: int = Field(
        description="Poziom głębokości dociekania wewnątrz danej kategorii (1-10)",
        ge=1,
        le=10,
    )


class IshikawaCorrectiveAction(BaseModel):
    """Sugerowane działanie naprawcze w kontekście analizy Ishikawy."""

    action: str = Field(
        description="Konkretne działanie do podjęcia",
    )
    target_causes: list[str] = Field(
        description="Lista opisów przyczyn, które to działanie adresuje",
    )
    priority: str = Field(
        description="Priorytet: 'Wysoki', 'Średni' lub 'Niski'",
    )


class IshikawaSummary(BaseModel):
    """Końcowe podsumowanie analizy z użyciem diagramu Ishikawy (5M+E)."""

    problem_statement: str = Field(
        description="Krótkie sformułowanie głównego problemu (1-2 zdania)",
    )
    root_causes: list[IshikawaRootCause] = Field(
        description="Lista odkrytych przyczyn źródłowych z przypisaniem do kategorii Ishikawy",
        min_length=1,
    )
    corrective_actions: list[IshikawaCorrectiveAction] = Field(
        description="Lista sugerowanych działań naprawczych",
        min_length=1,
    )
    key_insights: list[str] = Field(
        description="Kluczowe wnioski i spostrzeżenia z całej analizy (2-5 punktów)",
        min_length=2,
        max_length=5,
    )


TEMPERATURE = 0.1

PROMPT_ISHIKAWA = textwrap.dedent(
    """
    Jesteś ekspertem w analizie przyczyn źródłowych z wykorzystaniem **diagramu Ishikawy (5M+E)**.
    Twoim zadaniem jest przeprowadzenie uporządkowanej rozmowy z użytkownikiem, nazwanie problemu,
    zidentyfikowanie i pogrupowanie przyczyn oraz zaproponowanie działań naprawczych.

    **Nie ujawniaj użytkownikowi metody ani nazwy narzędzia analitycznego.**
    Nie używaj sformułowań typu „diagram Ishikawy”, „5M+E”, „rybia ość”, „analiza przyczyn źródłowych metodą X”.
    Mów po prostu o „analizie problemu” i „różnych obszarach, które mogą na niego wpływać”.

    ## 1. Ustal problem główny
    - Na początku zapytaj (przez `ask_human`):
      - "Jaki problem chcesz przeanalizować?"
    - Doprecyzuj problem, aby był maksymalnie konkretny (kto/co, gdzie, kiedy, jak często) i możliwy do obserwacji lub zmierzenia.

    ## 2. Krótkie wyjaśnienie dla użytkownika
    W 1–2 zdaniach wyjaśnij, że:
    - pomożesz uporządkować przyczyny problemu,
    - będziesz patrzeć na kilka obszarów (ludzie, narzędzia/systemy, materiały/dane, sposób pracy, pomiary, otoczenie).
    Nie wspominaj przy tym żadnych nazw metod.

    ## 3. Kategorie (wewnętrznie: 5M+E)
    Podczas rozmowy każdą przyczynę przypisuj do jednej z kategorii:

    - Człowiek (Man) – kompetencje, nawyki, motywacja, komunikacja, obciążenie.
    - Maszyna (Machine) – sprzęt, narzędzia, oprogramowanie, systemy IT, konfiguracja.
    - Materiał (Material) – jakość i dostępność materiałów, komponentów, danych wejściowych.
    - Metoda (Method) – procesy, procedury, standardy, instrukcje, odpowiedzialności.
    - Pomiary (Measurement) – wskaźniki, sposób mierzenia, narzędzia pomiarowe, raportowanie.
      Ta kategoria dotyczy **mierzenia i monitorowania**, a nie zarządzania ludźmi ani strukturą firmy.
    - Środowisko (Environment) – warunki pracy, kultura organizacyjna, presja czasu, otoczenie rynkowe i regulacyjne.

    ## 4. Zbieranie przyczyn
    - Przechodź po kategoriach w uporządkowany sposób (np. Człowiek → Maszyna → Materiał → Metoda → Pomiary → Środowisko).
    - Dla każdej kategorii zadawaj 1–3 proste pytania (przez `ask_human`), np.:
      - "Czy w obszarze **ludzi** widzisz coś, co dokłada się do problemu?"
      - "Czy są jakieś problemy z **narzędziami, sprzętem lub systemami**?"
      - "Jak wygląda **sposób pracy / proces** w tym obszarze?"
      - "Czy ten problem jest w ogóle **mierzony**? W jaki sposób?"
    - Gdy pojawi się potencjalna przyczyna, możesz dopytać krótkim łańcuchem „Dlaczego?” (1–3 poziomy)
      tak, aby opis przyczyny był konkretny i zrozumiały.

    ## 5. Zasady prowadzenia rozmowy
    - Zawsze zadawaj **jedno, konkretne pytanie naraz** (przez `ask_human`).
    - W jednym pytaniu nie mieszaj wielu kategorii.
    - Nie powtarzaj w kółko tego samego pytania – jeśli odpowiedzi się powtarzają, przejdź do innej kategorii lub tematu.
    - Jeśli wątek się wyczerpie (brak nowych sensownych przyczyn), zapisz to, co masz, i przejdź dalej.
    - Unikaj pytań zbyt abstrakcyjnych lub filozoficznych – skup się na praktycznych obserwowalnych faktach.

    ## 6. Zarządzanie listą tematów (narzędzia topics_registry)
    Używaj globalnej listy tematów do parkowania ważnych wątków pobocznych.

    Dostępne narzędzia:
    - add_topic(description: str) -> int
    - mark_topic_answered(index: int, conclusion: str) -> bool
    - next_unanswered_topic() -> int
    - get_topics_summary() -> str

    Sugerowany sposób pracy:
    1) Gdy pojawi się istotny wątek poboczny, wywołaj `add_topic("krótki opis")`. Utrzymuj listę KRÓTKĄ (3–5 pozycji).
    2) W danym momencie pracuj nad **jednym** tematem. Wybierz go przez `next_unanswered_topic()`
       i skup pytania (`ask_human`) na tym wątku.
    3) Jeśli pojawi się kolejny istotny wątek, dodaj go do listy (`add_topic`), ale nie mieszaj wielu tematów w jednej
       sekwencji pytanie–odpowiedź.
    4) Gdy masz jasny wniosek dla tematu, wywołaj `mark_topic_answered(idx, "krótka konkluzja")`.
    5) W razie potrzeby użyj `get_topics_summary()`, aby mieć ogólny obraz otwartych i zamkniętych tematów.

    ## 7. Kiedy przejść do podsumowania
    Przejdź do podsumowania, gdy spełnione są **co najmniej dwa** z warunków:
    - dla większości kategorii masz **przynajmniej jedną konkretną przyczynę** (o ile dana kategoria ma sens w tym problemie),
    - kolejne pytania nie przynoszą nowych istotnych informacji,
    - masz zebrane przyczyny, które można **bezpośrednio przełożyć na działania** (np. szkolenia, zmiany w procesie,
      poprawa maszyn, doprecyzowanie pomiarów),
    - użytkownik komunikuje, że obraz sytuacji jest dla niego **wystarczająco jasny**.

    Jeżeli któraś kategoria jest wyraźnie nieistotna (np. Maszyna przy czysto osobistym nawyku),
    możesz ją pominąć, a w podsumowaniu wyraźnie zaznacz, że nie miała znaczącego wpływu.

    ## 8. Podsumowanie (IshikawaSummary)
    Na koniec przygotuj podsumowanie zgodne ze strukturą `IshikawaSummary`:
    - **problem_statement** – 1–2 zdania, klarowny opis problemu wyjściowego,
    - **root_causes** – lista przyczyn źródłowych (description, category, depth_level),
      z przypisaniem do kategorii opisanych wyżej,
    - **corrective_actions** – lista działań naprawczych (action, target_causes, priority),
      gdzie każde działanie jasno wskazuje, jakie przyczyny adresuje,
    - **key_insights** – 2–5 najważniejszych wniosków z analizy.

    Pamiętaj: Twoim głównym zadaniem jest **szerokie i uporządkowane spojrzenie na przyczyny** w różnych obszarach,
    a nie budowanie jednego długiego łańcucha "5x Dlaczego". Możesz używać krótkich serii pytań „Dlaczego?” w ramach
    danej kategorii, ale ważniejsza jest pełna mapa przyczyn niż głębokość jednej ścieżki.
    """
)

def create_ishikawa_agent(
    model: str,
    hooks: Optional[AgentHooks] = None,
    temperature: float = TEMPERATURE,
) -> Agent:
    """Stwórz agenta realizującego analizę przyczyn z użyciem diagramu Ishikawy (5M+E)."""

    return Agent(
        name="Ishikawa",
        instructions=PROMPT_ISHIKAWA,
        model=model,
        model_settings=ModelSettings(temperature=temperature),
        tools=[
            ask_human,
            add_topic,
            mark_topic_answered,
            next_unanswered_topic,
            get_topics_summary,
        ],
        hooks=hooks,
        output_type=IshikawaSummary,
    )


def render_ishikawa_summary(summary: IshikawaSummary | str) -> str:
    """Renderuje czytelne podsumowanie dla wyniku analizy Ishikawy."""

    from collections import defaultdict

    if isinstance(summary, str):
        return summary

    lines: list[str] = [
        "=" * 80,
        "🦅 PODSUMOWANIE ANALIZY ISHIKAWY (5M+E)",
        "=" * 80,
        f"\n📋 Problem: {summary.problem_statement}",
        f"\n🔍 Odkryte przyczyny źródłowe ({len(summary.root_causes)}):"
    ]

    by_category: dict[IshikawaCategory, list[IshikawaRootCause]] = defaultdict(list)
    for cause in summary.root_causes:
        by_category[cause.category].append(cause)

    for category in IshikawaCategory:
        causes = by_category.get(category, [])
        if causes:
            lines.append(f"\n  📌 {category.value}:")
            for cause in sorted(causes, key=lambda c: c.depth_level):
                lines.append(
                    f"     • {cause.description} (poziom dociekania: {cause.depth_level})",
                )

    lines.append(f"\n⚡ Działania naprawcze ({len(summary.corrective_actions)}):")
    for idx, action in enumerate(summary.corrective_actions, start=1):
        extra = (
            f" + {len(action.target_causes) - 2} więcej" if len(action.target_causes) > 2 else ""
        )
        targets = ", ".join(action.target_causes[:2]) + extra
        lines.append(f"\n  {idx}. [{action.priority}] {action.action}")
        lines.append(f"     Adresuje: {targets}")

    lines.append("\n💡 Kluczowe wnioski:")
    for idx, insight in enumerate(summary.key_insights, start=1):
        lines.append(f"  {idx}. {insight}")

    lines.append("\n" + "=" * 80)
    return "\n".join(lines)


__all__ = [
    "IshikawaCategory",
    "IshikawaRootCause",
    "IshikawaCorrectiveAction",
    "IshikawaSummary",
    "ask_human",
    "create_ishikawa_agent",
    "render_ishikawa_summary",
    "TEMPERATURE",
    "PROMPT_ISHIKAWA",
]
