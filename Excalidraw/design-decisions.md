# Design Decisions

## Use-Case-Regel: Wann entsteht ein Use Case?

**Regel (festgelegt 2026-04-24):**

Repositories machen ausschließlich Datenzugriff. Keine Domain-Regeln,
keine Berechnungen, keine Berechtigungen in Repos. Sobald solche Logik
anfällt, entsteht ein Use Case.

Triviale CRUD-Reads (list_all, get_by_id, get_active) bleiben direkter
Repo-Zugriff aus dem Router — sie enthalten keinerlei Logik und
brauchen keinen Use-Case-Wrapper.

Sobald ein Read Logik enthält (Aggregation, Berechnung, komplexe Filter,
Berechtigungen) wird er ein Use Case. Das gilt insbesondere für
Dashboard-Endpoints (Burndown, Velocity, Goal-Progress, Metrics).

Mutations und Operationen mit Domain-Regeln gehen immer durch Use Cases.

---

## Löschregeln

**Festgelegt 2026-04-24.**

### DeleteSprintUseCase

- Ein **aktiver** Sprint (status = "active") darf **nicht** gelöscht werden.
  Versuch → `InvalidOperationError` → HTTP 409.
- Geplante (planned) und abgeschlossene/abgebrochene Sprints dürfen weg.
- Beim Löschen: `SprintDeletedEvent` feuern.
- Tasks im Sprint bleiben bestehen; die FK `tasks.sprint_id` wird durch
  `ON DELETE SET NULL` automatisch auf NULL gesetzt.

**Begründung:** Ein laufender Sprint repräsentiert laufende Arbeit.
Löschen würde den Kontext der Tasks zerstören, ohne dass der User das
beabsichtigt. "Abschließen zuerst" ist die sichere Operation.

### DeleteTaskUseCase

- Task in **jedem** Zustand löschbar (done, cancelled, in_progress, …).
- Beim Löschen: `TaskDeletedEvent` feuern.

**Begründung:** Der User soll jederzeit aufräumen können.
Der gelöschte Task ist weg — keine Archivierung in dieser Phase.

### DeleteGoalUseCase

- Goal mit aktiven KeyResults darf gelöscht werden.
- KeyResults werden **kaskadierend** mitgelöscht (FK `ON DELETE CASCADE`
  auf `key_results.goal_id`).
- Beim Löschen: `GoalDeletedEvent` feuern.

**Begründung:** Ein Ziel ohne seine Messkriterien zu löschen wäre
inkonsistent. Cascade ist die sauberste Option für ein Single-User-System.

### DeleteKeyResultUseCase

- KeyResult immer löschbar.
- Beim Löschen: `KeyResultDeletedEvent` feuern.

---

## Dependency-Inversion im API-Layer

**Festgelegt 2026-04-24.**

`src/api/dependencies.py` exponiert ausschließlich Interfaces:

```python
TaskRepoDep  = Annotated[ITaskRepository,   Depends(get_task_repo)]
SprintRepoDep = Annotated[ISprintRepository, Depends(get_sprint_repo)]
GoalRepoDep  = Annotated[IGoalRepository,   Depends(get_goal_repo)]
EventBusDep  = Annotated[IEventBus,         Depends(get_event_bus)]
```

Konkrete Klassen (PostgresXxxRepository, InMemoryEventBus) erscheinen
nur in den Factory-Funktionen. So können Router und Use Cases ohne
Änderung gegen InMemory-Implementierungen getestet werden (DI-Override
in TestClient).
