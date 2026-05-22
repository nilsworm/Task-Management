# Design: AI Auto-Tagging von Transaktionen

**Datum:** 2026-05-22  
**Branch:** `feature/ai-auto-tagging`  
**Status:** Zur Implementierung freigegeben

---

## Ziel

Nach einem CSV-Import werden alle neu importierten Transaktionen automatisch von der KI mit Tags versehen. Die KI wählt aus einer festen Tag-Liste und darf mehrere Tags pro Transaktion vergeben. Kein User-Confirmation-Schritt — vollautomatisch.

---

## Architektur

### Trigger

`POST /cost/import` → `ImportTransactionsUseCase` → nach erfolgreichem Import: FastAPI `BackgroundTask` mit den IDs der neu erstellten Transaktionen.

### Datenfluss

```
POST /cost/import
  └─ ImportTransactionsUseCase
       ├─ Transaktionen parsen + in DB speichern (unverändert)
       ├─ neue_ids = [uuid, uuid, ...]
       └─ BackgroundTask: TagTransactionsUseCase(neue_ids)

BackgroundTask: TagTransactionsUseCase
  1. Transaktionen per neue_ids aus DB laden
  2. Einen AI-Call: generate(prompt, system)
       Prompt enthält: Tag-Liste + alle Transaktionen als JSON-Liste
  3. KI antwortet mit JSON:
       [{"id": "abc", "tags": ["lebensmittel"]},
        {"id": "def", "tags": ["zigaretten", "ungesund", "unnötig"]}]
  4. JSON parsen + validieren (nur Tags aus der erlaubten Liste)
  5. cost_repo.update_tags(id, tags) für jede Transaktion
       → UPDATE cost_transactions SET tags = $1 WHERE id = $2
```

### KI-Provider

Nutzt die bestehende `IAIClient`-Abstraktion (`generate()`, non-streaming). Provider-Wahl via `AI_PROVIDER` env var — kein neues Setup nötig.

---

## Tag-Liste

Lebt als Python-Konstante in einem neuen Modul `src/domain/cost/tags.py`. Zwei Kategorien:

**Thematisch (was):**
`lebensmittel`, `restaurant`, `cafe`, `transport`, `tanken`, `wohnen`, `nebenkosten`, `strom`, `internet`, `versicherung`, `gesundheit`, `apotheke`, `arzt`, `kleidung`, `elektronik`, `haushalt`, `freizeit`, `sport`, `reise`, `bildung`, `bücher`, `software`, `abonnement`, `streaming`, `gehalt`, `freelance`, `erstattung`, `transfer`, `investition`, `sparen`, `steuer`, `geschenk`

**Bewertend (wie):**
`unnötig`, `impuls`, `ungesund`, `tabak`, `alkohol`, `luxury`, `wiederkehrend`, `einmalig`

---

## Neue Komponenten

### Backend

| Datei | Zweck |
|---|---|
| `src/domain/cost/tags.py` | `ALLOWED_TAGS: frozenset[str]` — die kanonische Tag-Liste |
| `src/application/use_cases/tag_transactions.py` | `TagTransactionsUseCase` — Prompt bauen, KI rufen, Tags speichern |
| `src/domain/cost/repository.py` | Interface: `update_tags(id, tags) -> None` |
| `src/infrastructure/persistence/repositories/cost_repository.py` | Implementierung: `UPDATE cost_transactions SET tags = $1 WHERE id = $2` |

### Änderungen an bestehenden Dateien

| Datei | Änderung |
|---|---|
| `src/api/routers/cost_router.py` | `BackgroundTask` nach Import starten |
| `src/api/dependencies.py` | `get_tag_transactions_use_case` Dependency |

---

## AI-Prompt

**System:**
```
Du bist ein Finanz-Kategorisierer. Weise jeder Transaktion passende Tags aus der erlaubten Liste zu.
Antworte ausschließlich mit einem JSON-Array, keine Erklärungen.
```

**Prompt:**
```
Erlaubte Tags: [lebensmittel, restaurant, ...]

Transaktionen:
[
  {"id": "uuid1", "title": "Rewe", "amount": 45.30, "type": "expense", "description": ""},
  {"id": "uuid2", "title": "Marlboro", "amount": 8.50, "type": "expense", "description": ""}
]

Antworte mit:
[{"id": "uuid1", "tags": ["lebensmittel"]}, {"id": "uuid2", "tags": ["tabak", "ungesund", "unnötig"]}]
```

---

## Fehlerbehandlung

- KI nicht verfügbar: BackgroundTask loggt Warning, Transaktionen bleiben ohne Tags (kein Crash, kein Retry)
- JSON-Parse-Fehler: Warning loggen, Transaktionen bleiben ohne Tags
- Unbekannte Tags in KI-Antwort: nur Tags filtern, die in `ALLOWED_TAGS` sind — unbekannte ignorieren
- Leeres `tags`-Array: erlaubt, Transaktion bleibt ungetaggt

---

## Tests

| Test | Art |
|---|---|
| `TagTransactionsUseCase` — happy path (2 Transaktionen, Tags gesetzt) | Unit (Mock-Repo, Mock-AI) |
| `TagTransactionsUseCase` — KI gibt unbekannte Tags zurück → werden gefiltert | Unit |
| `TagTransactionsUseCase` — KI gibt ungültiges JSON zurück → kein Crash | Unit |
| `POST /cost/import` — BackgroundTask wird gestartet | API-Test (BackgroundTask mock) |
| `PostgresCostRepository.update_tags()` | Integration |

---

## Nicht im Scope

- Manueller "Alle neu taggen"-Button im Frontend
- Tag-Liste im Frontend bearbeiten
- Re-Tagging bereits getaggter Transaktionen
- Streaming für Tagging-Response
