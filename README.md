# DORSZ - Dokładne Odpytywanie Rozpoznające Sedno Zagadnienia

<p align="center">
<img src="img/dorsz.png" alt="Alt text" width="500">
</p>

Uniwersalny runtime dla wielu agentów AI (obecnie: Why5, Ishikawa oraz Temperature-Check) korzystających z interfejsu OpenAI-compatible. Projekt jest nastawiony na dewelopera Pythona: używa uv do zarządzania środowiskiem i zależnościami, a uruchamianie odbywa się przez `uv run`.

## Szybki start

1) Wymagania:
- Python >= 3.13
- [uv](https://github.com/astral-sh/uv)
- Uruchomiony provider LLM: lokalny endpoint OpenAI-compatible (np. LMS Studio) lub OpenAI

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
uv run python main.py why5 --provider local --model bielik-11b-v2.6-instruct
```

Uwaga:
- Dla lokalnego endpointu (np. LMS Studio) włącz OpenAI-compatible API na `http://localhost:1234/v1`.
- Dla OpenAI ustaw `OPENAI_API_KEY` w środowisku lub pliku `.env`.

---

## Uruchamianie — składnia

Ogólny wzorzec:
```bash
uv run python main.py <agent_id> --provider <local|openai> [--model <nazwa_modelu>]
```

Parametry:
- `agent_id` (wymagany): `why5` | `ishikawa` | `temperature_check`
- `--provider` (opcjonalny): `local` (domyślny), `openai`
- `--model` (opcjonalny): jeśli pominięty, użyje ENV `MODEL` lub domyślnego; nazwa modelu zgodna z wybranym providerem

Przykłady (z użyciem modelu Bielik oraz innych):

- Why5:
```bash
# Lokalny endpoint + Bielik
uv run python main.py why5 --provider local --model bielik-11b-v2.6-instruct


# OpenAI (wymaga OPENAI_API_KEY)
uv run python main.py why5 --provider openai --model gpt-4o
```

- Ishikawa:
```bash
# Lokalny endpoint + Bielik
uv run python main.py ishikawa --provider local --model bielik-11b-v2.6-instruct


# OpenAI (wymaga OPENAI_API_KEY)
uv run python main.py ishikawa --provider openai --model gpt-4o
```

- Temperature-Check:
```bash
# Lokalny endpoint + Bielik
uv run python main.py temperature_check --provider local --model bielik-11b-v2.6-instruct


# OpenAI (wymaga OPENAI_API_KEY)
uv run python main.py temperature_check --provider openai --model gpt-4o
```

Wskazówka: domyślne wejście początkowe dla każdego agenta jest ustawione w `main.py` w `AGENT_DEFAULT_INPUTS`.

---

## Agenci

Projekt zawiera kilka agentów. Opis każdego z nich znajduje się w dedykowanym podrozdziale.

### 1) Agent Why5

Asystent AI do szybkiej analizy przyczyn źródłowych przy użyciu techniki „5 x Dlaczego” (5 Whys).

Jak działa:
1. Agent rozpoczyna rozmowę, pytając o problem do przeanalizowania (używa narzędzia `ask_human`).
2. Zadaje kolejne pytania „Dlaczego?”, maksymalnie 5 razy w jednym łańcuchu.
3. Kończy, gdy dotrze do przyczyny, którą można bezpośrednio zaadresować działaniem, albo gdy dalsze pytania nie wnoszą nowych informacji.
4. Generuje strukturalne podsumowanie: sformułowanie problemu, łańcuch „Dlaczego?”, główne przyczyny źródłowe, działania naprawcze i wnioski (model `Why5Summary` w `agents_why5.py`).

Przykład uruchomienia z Bielik:
```bash
uv run python main.py why5 --provider local --model bielik-11b-v2.6-instruct
```

Przykładowa sesja (fragment):
```
DORSZ - Dokładne Odpytywanie Rozpoznające Sedno Zagadnienia
Provider: local
Model: bielik-11b-v2.6-instruct
Agent: why5
Wpisz swój problem lub pytanie, aby rozpocząć analizę.

🤖 Agent: Cześć! Chętnie pomogę Ci przeanalizować jakiś problem metodą "5 x Dlaczego".
Jaki problem lub sytuację chciałbyś przeanalizować?

🤔 Agent pytanie: Jaki problem chciałbyś przeanalizować?
👤 Twoja odpowiedź: Zespół nie dotrzymuje deadlineów w projektach

[... dalsza interaktywna rozmowa ...]

================================================================================
🦅 PODSUMOWANIE ANALIZY '5 x DLACZEGO'
================================================================================
📋 Problem: Zespół regularnie nie dotrzymuje deadlineów w projektach...
❓ Łańcuch "Dlaczego?" (...)
🔍 Najważniejsze przyczyny źródłowe (...)
⚡ Działania naprawcze (...)
💡 Kluczowe wnioski (...)
================================================================================
```

### 2) Agent Ishikawa

Asystent AI do analizy przyczyn źródłowych z użyciem diagramu Ishikawy (rybia ość, 5M+E), z poprawnymi kategoriami:
- Człowiek (Man)
- Maszyna (Machine)
- Materiał (Material)
- Metoda (Method)
- Pomiary (Measurement)
- Środowisko (Environment)

Jak działa:
1. Agent rozpoczyna rozmowę, pytając o problem do przeanalizowania (używa narzędzia `ask_human`).
2. Systematycznie przechodzi przez kategorie 5M+E i zbiera przyczyny, opcjonalnie dopytując „Dlaczego?” w ramach kategorii.
3. Korzysta z globalnej listy tematów (`add_topic`, `mark_topic_answered`, `next_unanswered_topic`, `get_topics_summary`), żeby parkować poboczne wątki.
4. Generuje strukturalne podsumowanie: sformułowanie problemu, listę przyczyn z kategoriami Ishikawy, działania naprawcze, kluczowe wnioski (model `IshikawaSummary` w `agents_ishikawa.py`).

Przykład uruchomienia z Bielik:
```bash
uv run python main.py ishikawa --provider local --model bielik-11b-v2.6-instruct
```

### 3) Agent Temperature-Check

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
uv run python main.py temperature_check --provider local --model bielik-11b-v2.6-instruct
```

---

## Konfiguracja providerów

Domyślne adresy bazowe (zdefiniowane w `main.py`):
- Lokalny endpoint (np. LMS Studio): `http://localhost:1234/v1`
- OpenAI: używa domyślnych ustawień biblioteki OpenAI (wymaga `OPENAI_API_KEY`)

Parameter `--provider` przyjmuje wartości: `local` (domyślny), `openai`.

---

## Struktura kodu

- `main.py` — ogólny runtime:
  - Rejestr agentów, fabryki (`AGENT_FACTORIES`) i renderery (`AGENT_RENDERERS`)
  - Domyślne wejścia startowe (`AGENT_DEFAULT_INPUTS`)
  - Konfiguracja providerów i klienta OpenAI-compatible
  - Pętla uruchomieniowa i drukowanie wyników
- `agents_why5.py` — definicja agenta Why5:
  - Instrukcje (prompt), narzędzie `ask_human`, model Pydantic `Why5Summary`, renderer podsumowania
- `agents_ishikawa.py` — definicja agenta Ishikawa:
  - Instrukcje (prompt), narzędzie `ask_human`, narzędzia do zarządzania tematami, modele Pydantic `Ishikawa*`, renderer podsumowania
- `agents_temperature_check.py` — definicja agenta Temperature-Check:
  - Narzędzie `get_temperature`, struktura `TemperatureReport`, renderer

---

## Konfiguracja (.env)

Plik `.env` (opcjonalny), wczytywany automatycznie:
```bash
# Default model (used if --model is omitted)
MODEL=Bielik-4.5B-v3.0-Instruct.Q8_0.gguf

# OpenAI (cloud):
OPENAI_API_KEY=...

# Local (OpenAI-compatible) endpoint:
LOCAL_BASE_URL=http://localhost:1234/v1
LOCAL_API_KEY=EMPTY

# Opcjonalnie: inne ustawienia środowiskowe
```

---

## Testy

Aby uruchomić testy integracyjne:

- Wymagania: uruchomiony lokalny serwer zgodny z OpenAI API pod adresem `http://localhost:1234/v1`. Jeśli serwer nie jest osiągalny, testy zostaną pominięte.
- Model: testy używają modelu w kolejności: 1) parametr `--model`, 2) zmienna środowiskowa `MODEL`, 3) domyślny z `.env.example`.
- Klucze/sekrety: `OPENAI_API_KEY` nie jest wymagany; testy ustawiają go automatycznie na `EMPTY`.

Przykłady:
```bash
uv run pytest
uv run pytest -q
uv run pytest -q --model Bielik-4.5B-v3.0-Instruct.Q8_0.gguf
```

---

## Temperatura modeli

- Why5: domyślna temperatura `0.1` (patrz `agents_why5.py`)
- Ishikawa: domyślna temperatura `0.1` (patrz `agents_ishikawa.py`)
- Temperature-Check: domyślna temperatura `0.0` (patrz `agents_temperature_check.py`)

---

## Dodatkowe uwagi

- Parametr `--model` jest opcjonalny; jeśli pominięty, użyty zostanie `MODEL` z env lub domyślny.
- Dla lokalnego endpointu (np. LMS Studio) wymagane jest uruchomienie serwera zgodnego z OpenAI API pod wskazanym adresem.

---

## Inferencja modelu Bielik (lokalnie, GGUF)

Poniżej opisano, jak uruchomić inferencję lokalnego modelu oraz jak wpiąć go do DORSZ jako lokalny provider.

### Krok 1: Pobierz model GGUF

- Przejdź do repozytorium na Hugging Face, np.:
  https://huggingface.co/speakleash/Bielik-4.5B-v3.0-Instruct-GGUF/tree/main
- Pobierz wariant w oczekiwanej kwantyzacji (np. Q8_0) lub model bez kwantyzacji.
- Umieść plik w lokalnym katalogu, np. `./Bielik-4.5B-v3.0-Instruct-GGUF/`.

Przykładowy plik: `Bielik-4.5B-v3.0-Instruct.Q8_0.gguf`

### Opcja A: CLI (llama.cpp)

1) Instalacja llama.cpp:
- macOS (Homebrew):
```bash
brew install llama.cpp
```
- Alternatywnie z kodu źródłowego: https://github.com/ggml-org/llama.cpp

2) Uruchomienie serwera OpenAI-compatible:

Z Bielikiem v2.6
```bash
llama-server --port 1234 -c 32768 -m ./Bielik-11B-v2.6-Instruct-GGUF/Bielik-11B-v2.6-Instruct.Q8_0.gguf
```

Z Bielikiem v3.0
```bash
llama-server --port 1234 -m ./Bielik-4.5B-v3.0-Instruct-GGUF/Bielik-4.5B-v3.0-Instruct.Q8_0.gguf
```

Można również podać parametr `-c` określający rozmiar kontekstu w bajtach (zajrzyj do karty modelu na HF aby sprawdzić dla jakiego rozmiaru kontekstu był trenowany model).
Serwer będzie dostępny pod adresem `http://localhost:1234/v1`.
Server nie wymaga podania nazwy modelu przy wywołaniach API, ale dla spujności możemy go używać. 

3) Integracja z DORSZ:
- Upewnij się, że `LOCAL_BASE_URL=http://localhost:1234/v1` (np. w `.env`).
- Uruchom agenta, wskazując nazwę modelu (tu: nazwę pliku GGUF):
```bash
uv run python main.py why5 --provider local --model Bielik-4.5B-v3.0-Instruct.Q8_0.gguf
```
Analogicznie możesz uruchomić `ishikawa` oraz `temperature_check`.

### Opcja B: UI (Jan)

Jeśli wolisz interfejs graficzny, skorzystaj z projektu Jan:
- Repozytorium: https://github.com/janhq/jan
- Kroki:
  1. Zainstaluj aplikację (patrz „Releases” na GitHub).
  2. Dodaj model, wskazując pobrany plik `.gguf` (Import/Local model).
  3. Rozmawiaj z modelem bezpośrednio w UI.
  4. (Opcjonalnie) Jeśli w Jan dostępne jest lokalne API zgodne z OpenAI, włącz je i wskaż jego adres w `LOCAL_BASE_URL`, aby używać Jana jako providera dla DORSZ.

Uwagi:
- W przypadku ograniczeń pamięci wybierz lżejszą kwantyzację (np. Q6_K, Q5_K_M). Wersja Q8_0 to dobry kompromis jakości/szybkości na CPU.
- Możesz ustawić domyślny model w `.env` (zmienna `MODEL`), a następnie pominąć parametr `--model` przy uruchamianiu.
