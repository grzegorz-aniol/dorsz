from typing import Optional
import os
from pydantic import BaseModel, Field

from agents import Agent, ModelSettings, function_tool, AgentHooks


class TemperatureReport(BaseModel):
    """Prosty raport temperatury dla wskazanego miejsca."""
    place: str = Field(description="Miejsce, dla którego sprawdzono temperaturę")
    temperature_c: float = Field(description="Temperatura w stopniach Celsjusza")
    temperature_f: float = Field(description="Temperatura w stopniach Fahrenheita")
    conditions: str = Field(description="Opis warunków pogodowych (np. Słonecznie)")


# Dedykowane narzędzie - zwraca stałą temperaturę (scenariusz testowy)
@function_tool
def get_temperature(place: str) -> str:
    """
    Zwróć stały wynik temperatury dla dowolnego miejsca - na potrzeby prostego scenariusza testowego.
    Użytek: demonstracja wywołania narzędzia z poziomu agenta.
    """
    # Stała odpowiedź - niezależna od wejścia (celowo, do testu)
    print("*** TOOL get_temperature called ***")
    result = {
        "place": place,
        "temperature_c": 21.5,
        "temperature_f": 70.7,
        "conditions": "Słonecznie",
    }
    # Zwracamy tekstową postać (narzędzia mogą zwracać string; agent użyje tego do sformułowania odpowiedzi)
    return f"{result}"


INSTRUCTIONS = """
Jesteś prostym agentem do sprawdzania temperatury w danym miejscu.

Zasady:
- ZAWSZE wywołaj narzędzie get_temperature(place) dokładnie raz, przekazując nazwę miejsca z wejścia użytkownika.

Kroki:
1) Odczytaj nazwę miejsca z wejścia użytkownika (albo użyj domyślnej wartości).
2) Wywołaj get_temperature(place) dokładnie raz.
3) Na podstawie wyniku narzędzia wynik.
"""


DEFAULT_MODEL = os.getenv("MODEL", "Bielik-4.5B-v3.0-Instruct.Q8_0.gguf")

def create_temperature_check_agent(
    model: str | None = None,
    hooks: Optional[AgentHooks] = None,
    temperature: float = 0.1,
) -> Agent:
    """
    Stwórz agenta do testowego sprawdzenia temperatury przy użyciu stałego narzędzia.
    """
    return Agent(
        name="Temperature-Check",
        instructions=INSTRUCTIONS,
        model=model or DEFAULT_MODEL,
        model_settings=ModelSettings(temperature=temperature),
        tools=[get_temperature],
        hooks=hooks,
        # output_type=TemperatureReport,
    )


def render_temperature_report(report: TemperatureReport | str) -> str:
    """Prosty renderer raportu temperatury."""
    return str(report)



__all__ = [
    "TemperatureReport",
    "get_temperature",
    "create_temperature_check_agent",
    "render_temperature_report",
]
