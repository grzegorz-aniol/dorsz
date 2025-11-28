# DORSZ - Dokładne Odpytywanie Rozpoznające Sedno Zagadnienia

Uniwersalny runtime dla wielu agentów AI (obecnie: Why5-Ishikawa oraz Temperature-Check) korzystających z interfejsu OpenAI-compatible. Projekt jest nastawiony na dewelopera Pythona: używa uv do zarządzania środowiskiem i zależnościami, a uruchamianie odbywa się przez `uv run`.

## Szybki start

1) Wymagania:
- Python >= 3.13
- [uv](https://github.com/astral-sh/uv)
- Uruchomiony provider LLM (co najmniej jeden z): LMS Studio (LM Studio), Ollama lub OpenAI

2) Instalacja uv:
- macOS (Homebrew):
```bash
brew install uv
```
- Skrypt instalacyjny (macOS/Linux):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3) Klon repozytorium i instalacja zależności:
```bash
git clone <repo-url>
cd dorsz
uv sync
```

4) Uruchom pierwszy agent (przykład z LMS Studio i modelem Bielik):
```bash
uv run python main.py why5_ishikawa --provider lms --model bielik-11b-v2.6-instruct
```

Uwaga:
- Dla LMS Studio (LM Studio) włącz endpoint OpenAI-compatible na `http://localhost:1234/v1`.
- Dla Ollama upewnij się, że serwer działa na `http://localhost:11434/v1` i masz pobrany model (`ollama pull ...`).
- Dla OpenAI ustaw `OPENAI_API_KEY` w środowisku lub pliku `.env`.

---

## Uruchamianie — składnia

Ogólny wzorzec:
```bash
uv run python main.py <agent_id> --provider <lms|ollama|openai> --model <nazwa_modelu>
```

Parametry:
- `agent_id` (wymagany): `why5_ishikawa` | `temperature_check`
- `--provider` (opcjonalny): `lms` (domyślny), `ollama`, `openai`
- `--model` (wymagany): nazwa modelu zgodna z wybranym providerem

Przykłady (z użyciem modelu Bielik oraz innych):

- Why5-Ishikawa:
```bash
# LMS Studio + Bielik
uv run python main.py why5_ishikawa --provider lms --model bielik-11b-v2.6-instruct

# Ollama (przykładowy model)
uv run python main.py why5_ishikawa --provider ollama --model llama3.2

# OpenAI (wymaga OPENAI_API_KEY)
uv run python main.py why5_ishikawa --provider openai --model gpt-4o
```

- Temperature-Check:
```bash
# LMS Studio + Bielik
uv run python main.py temperature_check --provider lms --model bielik-11b-v2.6-instruct

# Ollama (przykładowy model)
uv run python main.py temperature_check --provider ollama --model llama3.2

# OpenAI (wymaga OPENAI_API_KEY)
uv run python main.py temperature_check --provider openai --model gpt-4o
```

Wskazówka: domyślne wejście początkowe dla każdego agenta jest ustawione w `main.py` w `AGENT_DEFAULT_INPUTS`.

---

## Agenci

Projekt zawiera kilka agentów. Opis każdego z nich znajduje się w dedykowanym podrozdziale.

### 1) Agent Why5-Ishikawa

Asystent AI do analizy przyczyn źródłowych, łączący:
- Metodę „5 Dlaczego” — iteracyjne zadawanie „dlaczego?”, aby odkryć prawdziwe przyczyny źródłowe (root causes)
- Diagram Ishikawy (5M+E) — klasyfikacja przyczyn według kategorii:
  - Człowiek (Man)
  - Maszyna (Machine)
  - Materiał (Material)
  - Metoda (Method)
  - Zarządzanie (Management)
  - Środowisko (Environment)

Jak działa:
1. Agent rozpoczyna rozmowę, pytając o problem do przeanalizowania (używa narzędzia `ask_human`).
2. Zadaje proste pytania „Dlaczego?”, schodząc coraz głębiej (5–15 iteracji).
3. Eksploruje różne ścieżki przyczynowe — jeśli użytkownik utknie, bada inne aspekty.
4. Generuje strukturalne podsumowanie: sformułowanie problemu, listę przyczyn z kategoriami Ishikawy, działania naprawcze, kluczowe wnioski.

Strukturalny output (Pydantic): zdefiniowany w `agents_why5_ishikawa.py` jako `Why5IshikawaSummary`.

Przykład uruchomienia z Bielik:
```bash
uv run python main.py why5_ishikawa --provider lms --model bielik-11b-v2.6-instruct
```

Przykładowa sesja (fragment):
```
DORSZ - Dokładne Odpytywanie Rozpoznające Sedno Zagadnienia
Provider: lms
Model: bielik-11b-v2.6-instruct
Agent: why5_ishikawa
Wpisz swój problem lub pytanie, aby rozpocząć analizę.

🤖 Agent: Cześć! Chętnie pomogę Ci przeanalizować jakiś problem metodą "5 Dlaczego"
i diagram Ishikawy. Jaki problem lub sytuację chciałbyś przeanalizować?

🤔 Agent pytanie: Jaki problem chciałbyś przeanalizować?
👤 Twoja odpowiedź: Zespół nie dotrzymuje deadlineów w projektach

[... dalsza interaktywna rozmowa ...]

================================================================================
🦅 PODSUMOWANIE ANALIZY '5 DLACZEGO' + ISHIKAWA
================================================================================
📋 Problem: Zespół regularnie nie dotrzymuje deadlineów w projektach...
🔍 Odkryte przyczyny źródłowe (…)
⚡ Działania naprawcze (…)
💡 Kluczowe wnioski (…)
================================================================================
```

### 2) Agent Temperature-Check

Prosty agent testowy, prezentujący wywołanie narzędzia i zwracanie wyników w strukturze.

Zasady działania:
- Ma dedykowane narzędzie `get_temperature(place)`, które w tym scenariuszu zwraca stałą odpowiedź (do demonstracji integracji tool-call).
- Zawsze wywołuje narzędzie dokładnie raz.
- Zwraca wynik jako strukturę `TemperatureReport` (Pydantic) z polami: miejsce, temperatura (°C/°F), warunki.

Domyślne wejście:
- Jeśli nie podano miejsca, wykorzystywane jest „Warszawa”.
- W aktualnym runtime wejście początkowe jest dostarczane z `AGENT_DEFAULT_INPUTS` (patrz `main.py`). Aby zmienić domyślne miejsce startowe, zaktualizuj `AGENT_DEFAULT_INPUTS["temperature_check"]`.

Przykład uruchomienia z Bielik:
```bash
uv run python main.py temperature_check --provider lms --model bielik-11b-v2.6-instruct
```

---

## Konfiguracja providerów

Domyślne adresy bazowe (zdefiniowane w `main.py`):
- LMS Studio: `http://localhost:1234/v1`
- Ollama: `http://localhost:11434/v1`
- OpenAI: używa domyślnych ustawień biblioteki OpenAI (wymaga `OPENAI_API_KEY`)

Zmienna `--provider` przyjmuje wartości: `lms` (domyślny), `ollama`, `openai`.

---

## Struktura kodu

- `main.py` — ogólny runtime:
  - Rejestr agentów, fabryki (`AGENT_FACTORIES`) i renderery (`AGENT_RENDERERS`)
  - Domyślne wejścia startowe (`AGENT_DEFAULT_INPUTS`)
  - Konfiguracja providerów i klienta OpenAI-compatible
  - Pętla uruchomieniowa i drukowanie wyników
- `agents_why5_ishikawa.py` — definicja agenta Why5-Ishikawa:
  - Instrukcje, narzędzie `ask_human`, modele Pydantic, renderer podsumowania
- `agents_temperature_check.py` — definicja agenta Temperature-Check:
  - Narzędzie `get_temperature`, struktura `TemperatureReport`, renderer

---

## Konfiguracja (.env)

Plik `.env` (opcjonalny), wczytywany automatycznie:
```bash
# Dla OpenAI:
OPENAI_API_KEY=sk-...

# Opcjonalnie: inne ustawienia środowiskowe
```

---

## Temperatura modeli

- Why5-Ishikawa: domyślna temperatura `0.1` (patrz `agents_why5_ishikawa.py`)
- Temperature-Check: domyślna temperatura `0.0` (patrz `agents_temperature_check.py`)

---

## Dodatkowe uwagi

- Wybór modelu (`--model`) jest wymagany dla wszystkich providerów.
- Dla LMS Studio i Ollama wymagane jest uruchomienie lokalnego serwera zgodnego z OpenAI API pod wskazanymi adresami.

