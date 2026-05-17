# AI Financial Advisor — Design Spec

**Datum:** 2026-05-17  
**Branch:** `feature/ai-financial-advisor`  
**Status:** Approved

---

## Überblick

Ein lokaler AI-Finanzberater, der Transaktionsdaten aus den Cost-Tabellen analysiert und dem Nutzer proaktive Insights sowie eine Chat-Schnittstelle zur Verfügung stellt. Keine externen API-Calls — das LLM läuft lokal via Ollama.

---

## Interaktionsmodell

Ein **globaler Floating-Button** (Sparkle-Icon, fixed bottom-right) ist auf jeder Seite sichtbar. Klick öffnet ein **Slide-in Panel** (~420px, von rechts):

- **Oben:** 3 proaktive Insight-Karten (auto-generiert beim Öffnen des Panels)
- **Unten:** Chat-Eingabefeld mit streaming Antwort-Bubble

Jede Chat-Frage ist unabhängig (kein Gesprächs-Gedächtnis). Der Finanz-Kontext wird bei jedem Call frisch aus der DB geladen.

---

## Infrastruktur

### Ollama — lokales Setup (macOS)

Ollama läuft **nativ auf macOS** (nicht in Docker), nutzt Metal-Beschleunigung auf dem M4 Pro.

- **Modell:** `qwen2.5:14b-instruct-q4_K_M` (~9 GB, lässt ~15 GB unified memory frei)
- **Backend (lokal, direkt):** `OLLAMA_BASE_URL=http://localhost:11434`
- **Backend (lokal, in Docker):** `OLLAMA_BASE_URL=http://host.docker.internal:11434`
- **Produktion (Hetzner):** Ollama läuft in `docker-compose.yml` als eigener Service (CPU-Inferenz, kein Metal)

### Startup-Check

FastAPI-Startup pingt `GET {OLLAMA_BASE_URL}/api/tags`. Bei Fehler: Warning-Log, kein Hard-Crash. AI-Endpoints geben `503` zurück wenn Ollama nicht erreichbar.

---

## Backend-Struktur

### Neue Dateien

```
backend/src/
  infrastructure/ai/
    __init__.py
    ollama_client.py          # HTTP-Client: non-streaming + streaming Calls
  application/services/
    ai_advisor.py             # Daten aggregieren, Prompts bauen, Ollama aufrufen
  api/routers/
    ai_router.py              # POST /ai/insights + POST /ai/chat (SSE)
```

Kein neuer Domain-Layer — AI ist ein Application-Service, keine Domain-Entität.

### OllamaClient (`infrastructure/ai/ollama_client.py`)

Thin HTTP-Wrapper um die Ollama REST API:
- `generate(prompt, system) -> str` — synchroner Call, gibt vollständige Antwort zurück
- `generate_stream(prompt, system) -> AsyncIterator[str]` — async Generator, yieldet Tokens

Interface/ABC damit Unit-Tests mocken können.

### AIAdvisorService (`application/services/ai_advisor.py`)

Nutzt `ICostRepository` direkt. Liest:
- Transaktionen der letzten 6 Monate
- Aktuelle Monatszusammenfassung (Einnahmen, Ausgaben, Saldo)
- Aktive Recurring-Einträge
- Top-5 größte Transaktionen des aktuellen Monats

Baut daraus einen strukturierten Kontext-String (kein JSON, plain text für bessere LLM-Verarbeitung).

Zwei öffentliche Methoden:
- `get_insights() -> list[InsightCard]` — ruft Ollama synchron auf, parst JSON-Antwort
- `stream_chat(message: str) -> AsyncIterator[str]` — streamt Tokens

---

## Prompt-Design

### Finanz-Kontext (beide Prompt-Typen)

```
Aktueller Monat (Mai 2026):
- Einnahmen: 3.200 €  Ausgaben: 2.100 €  Saldo: +1.100 €
- Ausgaben nach Tag: lebensmittel 480€, miete 900€, transport 210€

Letzte 6 Monate (Monats-Saldo):
- Nov: +800€  Dez: +1.200€  Jan: +950€  Feb: +600€  Mär: +1.100€  Apr: +900€

Wiederkehrende Einträge (aktiv):
- Netflix 12,99€/mo, Strom 85€/mo, Miete 900€/mo

Top-5 Ausgaben diesen Monat:
- 2026-05-12  Amazon  348€  [shopping]
- ...
```

### Insights-Prompt

```
Analysiere die folgenden Finanzdaten und gib exakt 3 Insights als JSON-Array zurück.
Jeder Insight hat die Felder: title (max 60 Zeichen), body (max 120 Zeichen), 
type (einer von: warning, tip, forecast).
Gib ausschließlich das JSON-Array zurück, keine Erklärungen.

[FINANZDATEN]
```

Fehlerfall: Modell antwortet kein valides JSON → Fallback-Karte mit generischem Hinweis.

### Chat-System-Prompt

```
Du bist ein persönlicher Finanzberater. Antworte auf Deutsch, präzise, 
maximal 3 kurze Absätze. Nutze ausschließlich die bereitgestellten Finanzdaten 
als Grundlage. Beantworte nur Fragen zu Finanzen.
```

User-Message: `[Nutzerfrage]\n\n[FINANZDATEN]`

---

## API-Layer

### `POST /ai/insights`

- Keine Request-Parameter
- Response: `[{"title": str, "body": str, "type": "warning"|"tip"|"forecast"}]`
- Fehler: `503` wenn Ollama nicht erreichbar

### `POST /ai/chat`

- Request: `{"message": str}` (max. 500 Zeichen, Pydantic-Validierung)
- Response: `StreamingResponse` mit `Content-Type: text/event-stream`
- Format: SSE — jedes Token als `data: <token>\n\n`, Abschluss: `data: [DONE]\n\n`
- Fehler: `503` wenn Ollama nicht erreichbar, `422` bei Validierungsfehler

---

## Frontend-Struktur

```
frontend/src/
  features/ai/
    AIFloatingButton.tsx      # Fixed bottom-right, Sparkle-Icon, toggle Panel
    AIAdvisorPanel.tsx        # Slide-in Panel (fixed right, ~420px)
    InsightCards.tsx          # 3 Karten (warning/tip/forecast je eigene Farbe)
    AIChat.tsx                # Eingabefeld + streaming Antwort-Bubble
    __tests__/
      AIFloatingButton.test.tsx
      InsightCards.test.tsx
      AIChat.test.tsx
  stores/
    aiPanelStore.ts           # Zustand: isOpen + toggle()
  api/hooks/
    ai.ts                     # useAIInsights (TanStack Query), useAIChat (custom hook)
```

### Verhalten

- Panel öffnet → `useAIInsights` feuert automatisch (`enabled: isOpen`)
- Insights laden: Skeleton-Karten während Ollama antwortet
- Chat: `fetch` mit `ReadableStream` → SSE-Chunks → Token für Token in Bubble appenden
- Panel schließt → Insights bleiben in TanStack Query gecacht, Chat-Input wird geleert

### UI-Design

Bewusst anders als der Rest der App — moderner, AI-nativer Look:
- Dunkles Panel auch im Light Mode
- Glassmorphism-Effekt auf dem Panel
- Gradient-Akzent auf dem FAB (Sparkle-Icon)
- Wird mit dem `frontend-design` Skill im Detail ausgearbeitet

---

## Testing

### Backend

| Was | Wie |
|-----|-----|
| `OllamaClient` | Unit-Tests mit gemocktem HTTP (`httpx.MockTransport`) |
| `AIAdvisorService` | Unit-Tests mit `InMemoryCostRepository` + gemocktem `OllamaClient` |
| `POST /ai/insights` | API-Tests mit gemocktem Service — Status-Codes, Response-Shape |
| `POST /ai/chat` | API-Tests — SSE-Format, `503` wenn Ollama nicht erreichbar |

### Frontend

| Was | Wie |
|-----|-----|
| `AIFloatingButton` | Vitest — Toggle öffnet/schließt Panel |
| `InsightCards` | Vitest — alle drei Karten-Typen (warning/tip/forecast) |
| `AIChat` | Vitest — Eingabe, Sende-Button-Zustand, Streaming-Bubble |

Kein Playwright-E2E für AI (Ollama im CI nicht verfügbar).

---

## Scope — explizit ausgeschlossen

- Anruf-Feature (später, separates Feature)
- Gesprächs-Gedächtnis über Sessions hinweg
- Zugriff auf Task/Sprint/Goal-Tabellen
- Modell-Auswahl in der UI
- Prompt-Tuning UI
