# DORSZ - Dokładne Odpytywanie Rozpoznające Sedno Zagadnienia

<p align="center">
<img src="img/dorsz.png" alt="Alt text" width="500">
</p>

Uniwersalny runtime dla wielu agentów AI (obecnie: Why5, Ishikawa oraz Temperature-Check) korzystających z interfejsu OpenAI-compatible. Projekt jest nastawiony na dewelopera Pythona: używa uv do zarządzania środowiskiem i zależnościami, a uruchamianie odbywa się przez `uv run`.

## Szybki start

1) Wymagania:
- Python >= 3.13
- [uv](https://github.com/astral-sh/uv)
- Uruchomiony provider LLM: lokalny endpoint OpenAI-compatible (np. `llama-server`) lub OpenAI

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

4) Uruchom pierwszego agenta (przykład z lokalnym `llama-server` i modelem Bielik-11B-v3.0-Instruct):
```bash
uv run python main.py why5 --provider local --model Bielik-11B-v3.0-Instruct
```

Uwaga:
- Lokalny endpoint skonfigurowany jest na `http://localhost:1234/v1`.
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
# Lokalny endpoint + Bielik-11B-v3.0-Instruct
uv run python main.py why5 --provider local --model Bielik-11B-v3.0-Instruct


# OpenAI (wymaga OPENAI_API_KEY)
uv run python main.py why5 --provider openai --model gpt-4o
```

- Ishikawa:
```bash
# Lokalny endpoint + Bielik-11B-v3.0-Instruct
uv run python main.py ishikawa --provider local --model Bielik-11B-v3.0-Instruct


# OpenAI (wymaga OPENAI_API_KEY)
uv run python main.py ishikawa --provider openai --model gpt-4o
```

- Temperature-Check:
```bash
# Lokalny endpoint + Bielik-11B-v3.0-Instruct
uv run python main.py temperature_check --provider local --model Bielik-11B-v3.0-Instruct


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

Przykład uruchomienia z Bielik-11B-v3.0-Instruct:
```bash
uv run python main.py why5 --provider local --model Bielik-11B-v3.0-Instruct
```

Przykładowa sesja (fragment):
```
DORSZ - Dokładne Odpytywanie Rozpoznające Sedno Zagadnienia
Provider: local
Model: Bielik-11B-v3.0-Instruct
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

Przykład uruchomienia z Bielik-11B-v3.0-Instruct:
```bash
uv run python main.py ishikawa --provider local --model Bielik-11B-v3.0-Instruct
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

Przykład uruchomienia z Bielik-11B-v3.0-Instruct:
```bash
uv run python main.py temperature_check --provider local --model Bielik-11B-v3.0-Instruct
```

---

## Konfiguracja providerów

Domyślne adresy bazowe (zdefiniowane w `main.py`):
- Lokalny endpoint (np. `llama-server`): `http://localhost:1234/v1`
- OpenAI: używa domyślnych ustawień biblioteki OpenAI (wymaga `OPENAI_API_KEY`)

Parameter `--provider` przyjmuje wartości: `local` (domyślny), `openai`.

---




## Konfiguracja (.env)

Plik `.env` (opcjonalny), wczytywany automatycznie:
```bash
# Default model (used if --model is omitted)
MODEL=Bielik-11B-v3.0-Instruct

# OpenAI (cloud):
OPENAI_API_KEY=...

# Local (OpenAI-compatible) endpoint:
LOCAL_BASE_URL=http://localhost:1234/v1
LOCAL_API_KEY=EMPTY

# Langfuse (optional observability)
LANGFUSE_SECRET_KEY=sk-..
LANGFUSE_PUBLIC_KEY=pk-..
LANGFUSE_BASE_URL=http://localhost:9300
```

Opis kluczowych zmiennych środowiskowych:

| Zmienna | Wymagane | Opis |
| --- | --- | --- |
| `MODEL` | Nie (domyślnie `Bielik-11B-v3.0-Instruct`) | Nazwa modelu przekazywana do providerów lokalnych; używana także przez testy, jeśli nie podasz `--model`. |
| `OPENAI_API_KEY` | Tak, gdy korzystasz z OpenAI | Klucz API wymagany do połączenia z chmurą OpenAI. |
| `LOCAL_BASE_URL` | Nie (domyślnie `http://localhost:1234/v1`) | Adres endpointu OpenAI-compatible uruchomionego lokalnie, np. `llama-server`. |
| `LOCAL_API_KEY` | Nie | Klucz dla lokalnego endpointu (często `EMPTY`, jeśli serwer nie wymaga autoryzacji). |
| `LANGFUSE_SECRET_KEY` / `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_BASE_URL` | Opcjonalnie | Dane dostępu do Langfuse, jeśli chcesz wysyłać telemetrię/obserwowalność. |

Pełny zestaw zmiennych wraz z komentarzami znajdziesz w `.env.example`.

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
uv run pytest -q --model Bielik-11B-v3.0-Instruct
```

---

## Temperatura modeli

- Why5: domyślna temperatura `0.1` (patrz `agents_why5.py`)
- Ishikawa: domyślna temperatura `0.1` (patrz `agents_ishikawa.py`)
- Temperature-Check: domyślna temperatura `0.0` (patrz `agents_temperature_check.py`)

---

## Dodatkowe uwagi

- Parametr `--model` jest opcjonalny; jeśli pominięty, użyty zostanie `MODEL` z env lub domyślny.
- Dla lokalnego endpointu (np. `llama-server`) wymagane jest uruchomienie serwera zgodnego z OpenAI API pod wskazanym adresem.

---

## Inferencja modelu Bielik (llama.cpp + GGUF)

Wszystkie przykłady wykorzystują model [speakleash/Bielik-11B-v3.0-Instruct](https://huggingface.co/speakleash/Bielik-11B-v3.0-Instruct) oraz jego wariant GGUF [speakleash/Bielik-11B-v3.0-Instruct-GGUF](https://huggingface.co/speakleash/Bielik-11B-v3.0-Instruct-GGUF). Model może wymagać zalogowania w Hugging Face i akceptacji licencji.

### Krok 1: Przygotuj dostęp do Hugging Face

- Zaloguj się w `huggingface-cli login` lub ustaw zmienną `HF_TOKEN` z tokenem mającym dostęp do modelu.
- Zaakceptuj warunki korzystania na karcie modelu (jeśli wymagane).

### Krok 2: Uruchom lokalny serwer llama.cpp

Zapoznaj się ze szczegółami instalacji tutaj: [https://github.com/ggerganov/llama.cpp](https://github.com/ggerganov/llama.cpp). Po instalacji model może zostać pobrany automatycznie przy pierwszym uruchomieniu dzięki flagom `-hf`. Poniższa komenda startuje `llama-server` z kwantyzacją Q8_0 i kontekstem 32768 tokenów:

```bash
llama-server --port 1234 -c 32768 \
    -hf speakleash/Bielik-11B-v3.0-Instruct-GGUF:Bielik-11B-v3.0-Instruct.Q8_0.gguf
```

Serwer OpenAI-compatible będzie dostępny pod `http://localhost:1234/v1`. Jeśli zmienisz port lub kontekst, zaktualizuj odpowiednio parametr `-c` i zmienną `LOCAL_BASE_URL`.

### Krok 3: Integracja z DORSZ

1. Ustaw `LOCAL_BASE_URL=http://localhost:1234/v1` (np. w `.env`).
2. (Opcjonalnie) Ustaw `MODEL=Bielik-11B-v3.0-Instruct`, aby nie podawać go w CLI.
3. Uruchom dowolnego agenta, wskazując model Bielik-11B-v3.0-Instruct:

```bash
uv run python main.py why5 --provider local --model Bielik-11B-v3.0-Instruct
uv run python main.py ishikawa --provider local --model Bielik-11B-v3.0-Instruct
uv run python main.py temperature_check --provider local --model Bielik-11B-v3.0-Instruct
```

To wszystko – jedynym wymaganym komponentem do inferencji jest `llama.cpp` z automatycznym pobieraniem GGUF.
