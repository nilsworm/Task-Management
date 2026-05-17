"""
Seed script for local development.

⚠️  FOR LOCAL DEVELOPMENT ONLY — never run against production data.
    All existing seed rows are overwritten (upsert via fixed UUIDs).

Usage (run from /backend):
    uv run python -m scripts.seed            # idempotent seed
    uv run python -m scripts.seed --reset    # DELETE all rows first, then seed
"""

from __future__ import annotations

import argparse
import asyncio
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.cost.entities import RecurringTransaction, Transaction
from src.domain.cost.value_objects import RecurrenceInterval, TransactionType
from src.domain.entities import DailyTask, KeyResult, LongTermGoal, Milestone, SprintTask
from src.domain.sprint import Sprint, SprintStatus
from src.domain.value_objects import DateRange, Estimation, Priority, TaskStatus
from src.infrastructure.database import async_session_factory
from src.infrastructure.persistence.repositories.cost_repository import PostgresCostRepository
from src.infrastructure.persistence.repositories.goal_repository import PostgresGoalRepository
from src.infrastructure.persistence.repositories.sprint_repository import PostgresSprintRepository
from src.infrastructure.persistence.repositories.task_repository import PostgresTaskRepository

# ---------------------------------------------------------------------------
# Deterministic UUID helpers — same name always → same UUID
# ---------------------------------------------------------------------------

_SEED_NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def sid(name: str) -> uuid.UUID:
    return uuid.uuid5(_SEED_NS, name)


def _now(days_offset: int = 0) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=days_offset)


def _est(sp: int) -> Estimation:
    return Estimation(story_points=sp)


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------


async def _reset(session: AsyncSession) -> None:
    await session.execute(text("DELETE FROM key_results"))
    await session.execute(text("DELETE FROM tasks"))
    await session.execute(text("DELETE FROM sprints"))
    await session.execute(text("DELETE FROM goals"))
    await session.execute(text("DELETE FROM cost_transactions"))
    await session.execute(text("DELETE FROM cost_recurring"))
    await session.commit()
    print("  DB reset — all seed tables cleared.")


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------


async def _seed(session: AsyncSession) -> None:
    task_repo = PostgresTaskRepository(session)
    sprint_repo = PostgresSprintRepository(session)
    goal_repo = PostgresGoalRepository(session)

    today = date.today()

    def d(offset: int) -> date:
        return today + timedelta(days=offset)

    # -----------------------------------------------------------------------
    # Sprints
    # -----------------------------------------------------------------------

    s1_id = sid("sprint-1-foundation")
    s2_id = sid("sprint-2-api-layer")
    s3_id = sid("sprint-3-frontend")
    s4_id = sid("sprint-4-polish")

    sprint1 = Sprint(
        "Sprint 1: Foundation",
        DateRange(d(-84), d(-71)),
        id=s1_id,
        status=SprintStatus.COMPLETED,
        created_at=_now(-90),
    )
    sprint2 = Sprint(
        "Sprint 2: API Layer",
        DateRange(d(-28), d(-15)),
        id=s2_id,
        status=SprintStatus.COMPLETED,
        created_at=_now(-35),
    )
    sprint3 = Sprint(
        "Sprint 3: Frontend",
        DateRange(d(-7), d(7)),
        id=s3_id,
        status=SprintStatus.ACTIVE,
        created_at=_now(-14),
    )
    sprint4 = Sprint(
        "Sprint 4: Polish",
        DateRange(d(14), d(28)),
        id=s4_id,
        status=SprintStatus.PLANNED,
        created_at=_now(-1),
    )

    for sprint in (sprint1, sprint2, sprint3, sprint4):
        await sprint_repo.save(sprint)

    # -----------------------------------------------------------------------
    # Sprint 1 tasks — all DONE (19 story points total)
    # -----------------------------------------------------------------------

    s1_tasks: list[SprintTask] = [
        SprintTask("Monorepo & Docker Compose setup",
                   sprint_id=s1_id, id=sid("s1-t1"),
                   status=TaskStatus.DONE, priority=Priority.HIGH,
                   estimation=_est(2), created_at=_now(-88)),
        SprintTask("Domain entities & value objects",
                   sprint_id=s1_id, id=sid("s1-t2"),
                   status=TaskStatus.DONE, priority=Priority.HIGH,
                   estimation=_est(5), created_at=_now(-86)),
        SprintTask("SQLAlchemy models & Alembic migrations",
                   sprint_id=s1_id, id=sid("s1-t3"),
                   status=TaskStatus.DONE, priority=Priority.HIGH,
                   estimation=_est(5), created_at=_now(-85)),
        SprintTask("Repository interfaces & implementations",
                   sprint_id=s1_id, id=sid("s1-t4"),
                   status=TaskStatus.DONE, priority=Priority.MEDIUM,
                   estimation=_est(3), created_at=_now(-83)),
        SprintTask("FastAPI skeleton & health endpoint",
                   sprint_id=s1_id, id=sid("s1-t5"),
                   status=TaskStatus.DONE, priority=Priority.MEDIUM,
                   estimation=_est(3), created_at=_now(-82)),
        SprintTask("Domain unit tests (state machine, factory)",
                   sprint_id=s1_id, id=sid("s1-t6"),
                   status=TaskStatus.DONE, priority=Priority.MEDIUM,
                   estimation=_est(1), created_at=_now(-80)),
    ]
    # total: 2+5+5+3+3+1 = 19 pts

    # -----------------------------------------------------------------------
    # Sprint 2 tasks — all DONE (22 story points total)
    # -----------------------------------------------------------------------

    s2_tasks: list[SprintTask] = [
        SprintTask("Task CRUD endpoints & schemas",
                   sprint_id=s2_id, id=sid("s2-t1"),
                   status=TaskStatus.DONE, priority=Priority.HIGH,
                   estimation=_est(5), created_at=_now(-32)),
        SprintTask("Sprint CRUD endpoints & state transitions",
                   sprint_id=s2_id, id=sid("s2-t2"),
                   status=TaskStatus.DONE, priority=Priority.HIGH,
                   estimation=_est(5), created_at=_now(-31)),
        SprintTask("Goal & KeyResult CRUD endpoints",
                   sprint_id=s2_id, id=sid("s2-t3"),
                   status=TaskStatus.DONE, priority=Priority.HIGH,
                   estimation=_est(5), created_at=_now(-30)),
        SprintTask("Dashboard endpoints (metrics, burndown, velocity)",
                   sprint_id=s2_id, id=sid("s2-t4"),
                   status=TaskStatus.DONE, priority=Priority.MEDIUM,
                   estimation=_est(3), created_at=_now(-29)),
        SprintTask("OpenAPI spec export & type generation",
                   sprint_id=s2_id, id=sid("s2-t5"),
                   status=TaskStatus.DONE, priority=Priority.LOW,
                   estimation=_est(1), created_at=_now(-28)),
        SprintTask("API integration tests (300+ assertions)",
                   sprint_id=s2_id, id=sid("s2-t6"),
                   status=TaskStatus.DONE, priority=Priority.HIGH,
                   estimation=_est(3), created_at=_now(-27)),
    ]
    # total: 5+5+5+3+1+3 = 22 pts

    # -----------------------------------------------------------------------
    # Sprint 3 tasks — mixed statuses (26 story points total)
    # -----------------------------------------------------------------------

    s3_tasks: list[SprintTask] = [
        SprintTask("Phase 10.1 — Task Text Search (ILIKE + debounce)",
                   sprint_id=s3_id, id=sid("s3-t1"),
                   status=TaskStatus.DONE, priority=Priority.HIGH,
                   estimation=_est(3), created_at=_now(-10)),
        SprintTask("Phase 10.2 — Overdue Task Highlighting (red indicators)",
                   sprint_id=s3_id, id=sid("s3-t2"),
                   status=TaskStatus.DONE, priority=Priority.HIGH,
                   estimation=_est(5), created_at=_now(-9)),
        SprintTask("Phase 10.3 — Sprint Complete Modal (velocity display)",
                   sprint_id=s3_id, id=sid("s3-t3"),
                   status=TaskStatus.IN_PROGRESS, priority=Priority.HIGH,
                   estimation=_est(8), created_at=_now(-8)),
        SprintTask("Phase 11.5 — CSV Import Endpoint (upload handler)",
                   sprint_id=s3_id, id=sid("s3-t4"),
                   status=TaskStatus.REVIEW, priority=Priority.MEDIUM,
                   estimation=_est(5), created_at=_now(-7)),
        SprintTask("Fix: Cost dashboard month filter edge case",
                   sprint_id=s3_id, id=sid("s3-t5"),
                   status=TaskStatus.TODO, priority=Priority.MEDIUM,
                   estimation=_est(2), created_at=_now(-6)),
        SprintTask("Refactor: Extract useFilterState hook",
                   sprint_id=s3_id, id=sid("s3-t6"),
                   status=TaskStatus.BACKLOG, priority=Priority.LOW,
                   estimation=_est(3), created_at=_now(-5)),
    ]
    # total: 3+5+8+5+2+3 = 26 pts; done=8, remaining=18

    # -----------------------------------------------------------------------
    # Sprint 4 tasks — all BACKLOG (14 story points total)
    # -----------------------------------------------------------------------

    s4_tasks: list[SprintTask] = [
        SprintTask("Playwright E2E test suite",
                   sprint_id=s4_id, id=sid("s4-t1"),
                   status=TaskStatus.BACKLOG, priority=Priority.HIGH,
                   estimation=_est(5), created_at=_now(-1)),
        SprintTask("Seed script for local dev",
                   sprint_id=s4_id, id=sid("s4-t2"),
                   status=TaskStatus.BACKLOG, priority=Priority.MEDIUM,
                   estimation=_est(2), created_at=_now(-1)),
        SprintTask("Docker Compose: backend & frontend services",
                   sprint_id=s4_id, id=sid("s4-t3"),
                   status=TaskStatus.BACKLOG, priority=Priority.HIGH,
                   estimation=_est(3), created_at=_now(-1)),
        SprintTask("README & architecture docs",
                   sprint_id=s4_id, id=sid("s4-t4"),
                   status=TaskStatus.BACKLOG, priority=Priority.MEDIUM,
                   estimation=_est(2), created_at=_now(-1)),
        SprintTask("Makefile / justfile for dev commands",
                   sprint_id=s4_id, id=sid("s4-t5"),
                   status=TaskStatus.BACKLOG, priority=Priority.LOW,
                   estimation=_est(2), created_at=_now(-1)),
    ]
    # total: 5+2+3+2+2 = 14 pts

    all_sprint_tasks = s1_tasks + s2_tasks + s3_tasks + s4_tasks
    for t in all_sprint_tasks:
        await task_repo.save(t)

    # Update sprint task_ids (sprint.add_task → sprint_repo.save)
    for sprint, tasks in [
        (sprint1, s1_tasks),
        (sprint2, s2_tasks),
        (sprint3, s3_tasks),
        (sprint4, s4_tasks),
    ]:
        for t in tasks:
            sprint.add_task(t.id)
        await sprint_repo.save(sprint)

    # -----------------------------------------------------------------------
    # Daily tasks
    # -----------------------------------------------------------------------

    daily_tasks: list[DailyTask] = [
        DailyTask("Review Phase 10.2 test coverage in backend tests",
                  id=sid("daily-1"), scheduled_date=today,
                  status=TaskStatus.TODO, priority=Priority.HIGH,
                  created_at=_now()),
        DailyTask("Update PROGRESS.md with Phase 10.3 completion notes",
                  id=sid("daily-2"), scheduled_date=d(-1),
                  status=TaskStatus.DONE, priority=Priority.MEDIUM,
                  created_at=_now(-1)),
        DailyTask("Debug: Sprint completion modal not rendering on mobile",
                  id=sid("daily-3"), scheduled_date=today,
                  status=TaskStatus.IN_PROGRESS, priority=Priority.HIGH,
                  created_at=_now()),
        DailyTask("Verify all 88 task/sprint tests pass locally",
                  id=sid("daily-4"), scheduled_date=d(-3),
                  status=TaskStatus.DONE, priority=Priority.CRITICAL,
                  created_at=_now(-3)),
        DailyTask("Clean up console errors in TypeScript strict mode",
                  id=sid("daily-5"), scheduled_date=d(-2),
                  status=TaskStatus.DONE, priority=Priority.MEDIUM,
                  created_at=_now(-2)),
        DailyTask("Backup database before migration to Hetzner",
                  id=sid("daily-6"), scheduled_date=d(2),
                  status=TaskStatus.TODO, priority=Priority.CRITICAL,
                  created_at=_now()),
        DailyTask("Test CSV import with real consorsbank file",
                  id=sid("daily-7"), scheduled_date=today,
                  status=TaskStatus.BACKLOG, priority=Priority.MEDIUM,
                  created_at=_now()),
    ]
    for t in daily_tasks:
        await task_repo.save(t)

    # -----------------------------------------------------------------------
    # Milestone tasks
    # -----------------------------------------------------------------------

    milestone_tasks: list[Milestone] = [
        Milestone("v1.0 Beta Release — All Phases 1–10 complete",
                  id=sid("milestone-1"), due_date=d(14),
                  status=TaskStatus.IN_PROGRESS, priority=Priority.CRITICAL,
                  created_at=_now(-30)),
        Milestone("Deploy to Hetzner + Coolify (Production)",
                  id=sid("milestone-2"), due_date=d(30),
                  status=TaskStatus.TODO, priority=Priority.CRITICAL,
                  created_at=_now(-15)),
        Milestone("v1.0 Public Release (GitHub + announcement)",
                  id=sid("milestone-3"), due_date=d(60),
                  status=TaskStatus.BACKLOG, priority=Priority.HIGH,
                  created_at=_now(-5)),
    ]
    for t in milestone_tasks:
        await task_repo.save(t)

    # -----------------------------------------------------------------------
    # LongTermGoal task (task_type="goal", not to confuse with Goal entity)
    # -----------------------------------------------------------------------

    goal_task = LongTermGoal(
        "Evaluate v2.0 Feature Scope (AI-Powered Insights, Mobile App)",
        id=sid("goal-task-1"),
        status=TaskStatus.BACKLOG,
        priority=Priority.MEDIUM,
        date_range=DateRange(d(60), d(120)),
        created_at=_now(),
    )
    await task_repo.save(goal_task)

    # -----------------------------------------------------------------------
    # Goals (OKR objectives)
    # -----------------------------------------------------------------------

    g1_id = sid("goal-ship-v1")
    g2_id = sid("goal-dev-experience")
    g3_id = sid("goal-code-quality")

    goal1 = LongTermGoal(
        "Ship v1.0",
        id=g1_id,
        description="Deliver a working, tested, documented v1.0 release.",
        status=TaskStatus.IN_PROGRESS,
        priority=Priority.HIGH,
        date_range=DateRange(d(-90), d(42)),
        created_at=_now(-90),
    )
    goal2 = LongTermGoal(
        "Developer Experience",
        id=g2_id,
        description="Make the project easy to set up and contribute to.",
        status=TaskStatus.BACKLOG,
        priority=Priority.MEDIUM,
        created_at=_now(-60),
    )
    goal3 = LongTermGoal(
        "Codebase Quality",
        id=g3_id,
        description="Maintain high standards for test coverage and performance.",
        status=TaskStatus.TODO,
        priority=Priority.MEDIUM,
        created_at=_now(-60),
    )

    for g in (goal1, goal2, goal3):
        await goal_repo.save(g)

    # -----------------------------------------------------------------------
    # Key Results
    # -----------------------------------------------------------------------

    key_results: list[KeyResult] = [
        # Goal 1 — Ship v1.0
        KeyResult(id=sid("kr-g1-1"), goal_id=g1_id,
                  title="Backend test coverage",
                  description="pytest --cov target",
                  target_value=90.0, current_value=85.0, unit="%",
                  created_at=_now(-80), updated_at=_now(-1)),
        KeyResult(id=sid("kr-g1-2"), goal_id=g1_id,
                  title="Frontend test coverage",
                  description="vitest coverage target",
                  target_value=80.0, current_value=69.0, unit="%",
                  created_at=_now(-80), updated_at=_now()),
        KeyResult(id=sid("kr-g1-3"), goal_id=g1_id,
                  title="Zero critical open bugs",
                  description="All P0 issues resolved before release",
                  target_value=1.0, current_value=1.0, unit="✓",
                  created_at=_now(-80), updated_at=_now(-2)),

        # Goal 2 — Developer Experience  (avg ~35%)
        KeyResult(id=sid("kr-g2-1"), goal_id=g2_id,
                  title="CI/CD pipeline",
                  description="GitHub Actions: lint + test + build on every PR",
                  target_value=1.0, current_value=0.0, unit="✓",
                  created_at=_now(-55), updated_at=_now(-55)),
        KeyResult(id=sid("kr-g2-2"), goal_id=g2_id,
                  title="Comprehensive README",
                  description="Setup in <10 min for a newcomer",
                  target_value=1.0, current_value=0.7, unit="✓",
                  created_at=_now(-55), updated_at=_now(-1)),

        # Goal 3 — Codebase Quality  (avg ~85%)
        KeyResult(id=sid("kr-g3-1"), goal_id=g3_id,
                  title="Average API response time",
                  description="Measured over 1000 requests against local DB",
                  target_value=50.0, current_value=45.0, unit="ms",
                  created_at=_now(-50), updated_at=_now(-3)),
        KeyResult(id=sid("kr-g3-2"), goal_id=g3_id,
                  title="Code smell refactors completed",
                  description="Tracked via ruff / manual review",
                  target_value=10.0, current_value=8.0, unit="refactors",
                  created_at=_now(-50), updated_at=_now(-5)),
    ]

    for kr in key_results:
        await goal_repo.save_key_result(kr)

    # -----------------------------------------------------------------------
    # Cost data
    # -----------------------------------------------------------------------

    await _seed_cost(session, today)

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------

    n_sprints = 4
    n_sprint_tasks = len(all_sprint_tasks)
    n_daily = len(daily_tasks)
    n_milestones = len(milestone_tasks)
    n_goal_tasks = 1
    n_tasks_total = n_sprint_tasks + n_daily + n_milestones + n_goal_tasks
    n_goals = 3
    n_krs = len(key_results)

    print(f"  Sprints:    {n_sprints}  (2 completed, 1 active, 1 planned)")
    print(f"  Tasks:      {n_tasks_total}  ({n_sprint_tasks} sprint, {n_daily} daily, "
          f"{n_milestones} milestone, {n_goal_tasks} goal-type)")
    print(f"  Goals:      {n_goals}")
    print(f"  KeyResults: {n_krs}")
    print(f"  Velocity:   Sprint 1=19 pts, Sprint 2=22 pts — avg 20.5")
    print(f"  Active sprint burndown: 28 total pts, 8 done (20 remaining)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def _seed_cost(session: AsyncSession, today: date) -> None:
    """Seed cost data with realistic transactions from consorsbank.csv format.

    Maps real bank transaction categories to semantic tags and creates opening
    balance transactions for the current and previous months.
    """
    cost_repo = PostgresCostRepository(session)

    # Recurring entries — mapped to common life expenses
    recurring: list[RecurringTransaction] = [
        RecurringTransaction.create(
            "Gehalt Unity AG",
            Decimal("2212.88"),
            TransactionType.INCOME,
            RecurrenceInterval.MONTHLY,
            id=sid("rec-gehalt-unity"),
            day_of_month=25,
            tags=["salary", "work"],
            start_date=date(2026, 1, 1),
        ),
        RecurringTransaction.create(
            "Krankenversicherung Landeskrankenhilfe",
            Decimal("72.45"),
            TransactionType.EXPENSE,
            RecurrenceInterval.MONTHLY,
            id=sid("rec-krankenkasse"),
            day_of_month=4,
            tags=["insurance", "health"],
            start_date=date(2026, 1, 1),
        ),
        RecurringTransaction.create(
            "Berufsunfähigkeitsversicherung VOLKSWOHL",
            Decimal("21.22"),
            TransactionType.EXPENSE,
            RecurrenceInterval.MONTHLY,
            id=sid("rec-bue"),
            day_of_month=4,
            tags=["insurance", "protection"],
            start_date=date(2026, 1, 1),
        ),
        RecurringTransaction.create(
            "Unfallversicherung prokundo",
            Decimal("13.92"),
            TransactionType.EXPENSE,
            RecurrenceInterval.MONTHLY,
            id=sid("rec-unfall"),
            day_of_month=4,
            tags=["insurance"],
            start_date=date(2026, 1, 1),
        ),
        RecurringTransaction.create(
            "Fitnessstudio EGYM Wellpass",
            Decimal("29.90"),
            TransactionType.EXPENSE,
            RecurrenceInterval.MONTHLY,
            id=sid("rec-gym"),
            day_of_month=7,
            tags=["fitness", "health"],
            start_date=date(2026, 3, 1),
        ),
        RecurringTransaction.create(
            "Claude AI Subscription (Anthropic)",
            Decimal("106.06"),
            TransactionType.EXPENSE,
            RecurrenceInterval.MONTHLY,
            id=sid("rec-claude"),
            day_of_month=27,
            tags=["software", "subscription"],
            start_date=date(2026, 4, 1),
        ),
    ]
    for r in recurring:
        await cost_repo.save_recurring(r)

    # Transactions based on consorsbank.csv (May 2026 actual data)
    def mk_tx(title: str, amount: str, tx_type: TransactionType, day: int,
              tags: list[str], desc: str = "", month_offset: int = 0, suffix: str = "") -> Transaction:
        m = today.month + month_offset
        y = today.year
        if m < 1:
            m += 12
            y -= 1
        elif m > 12:
            m -= 12
            y += 1
        tx_date = date(y, m, day)
        return Transaction.create(
            title, Decimal(amount), tx_type, tx_date,
            id=sid(f"consors-{suffix}"),
            tags=tags,
            description=desc or None,
        )

    # May 2026 transactions (current month) — realistic data from actual consorsbank export
    transactions: list[Transaction] = [
        # Salaries (income)
        mk_tx("Gehalt April 2026 — UNITY AG", "2212.88", TransactionType.INCOME, 30,
              ["salary", "work"], month_offset=-1, suffix="gehalt-apr"),
        mk_tx("Freelance-Projekt Webdesign", "273.20", TransactionType.INCOME, 29,
              ["freelance", "work"], "Siehe Zahlungsavis", month_offset=-1, suffix="freelance-apr"),

        # Current month (May 2026) — daily expenses
        mk_tx("HALL TABAKWAREN — Lebensmittel", "10.00", TransactionType.EXPENSE, 5,
              ["groceries", "daily"], suffix="hall-1"),
        mk_tx("EDEKA BUSCHKUEHLE — Lebensmittel", "14.40", TransactionType.EXPENSE, 12,
              ["groceries", "daily"], suffix="edeka-1"),
        mk_tx("Raiff. Tankstelle — Treibstoff", "75.01", TransactionType.EXPENSE, 11,
              ["fuel", "transport"], suffix="tank-1"),
        mk_tx("HALL TABAKWAREN — Lebensmittel", "10.00", TransactionType.EXPENSE, 11,
              ["groceries", "daily"], suffix="hall-2"),
        mk_tx("Happe Bauzentrum — Unkategorisiert", "567.56", TransactionType.EXPENSE, 8,
              ["shopping", "home"], suffix="happe"),
        mk_tx("HALL TABAKWAREN — Lebensmittel", "10.00", TransactionType.EXPENSE, 8,
              ["groceries", "daily"], suffix="hall-3"),
        mk_tx("EGYM Wellpass — Sport", "29.90", TransactionType.EXPENSE, 7,
              ["fitness", "health"], suffix="egym"),
        mk_tx("Laederach Schweiz — Geschenke", "36.64", TransactionType.EXPENSE, 6,
              ["gifts", "shopping"], suffix="laederach"),
        mk_tx("PayPal — Einnahmen", "75.00", TransactionType.INCOME, 6,
              ["income", "freelance"], "INSTANT TRANSFER", suffix="paypal-in"),
        mk_tx("Aral Station — Treibstoff", "7.58", TransactionType.EXPENSE, 6,
              ["fuel", "transport"], suffix="aral-1"),
        mk_tx("Aral Station — Treibstoff", "71.01", TransactionType.EXPENSE, 6,
              ["fuel", "transport"], suffix="aral-2"),
        mk_tx("Elsner Catering — Elektronik", "6.00", TransactionType.EXPENSE, 6,
              ["food", "work"], suffix="elsner"),
        mk_tx("Starbucks — Restaurants & Cafes", "34.40", TransactionType.EXPENSE, 5,
              ["coffee", "dining"], suffix="starbucks"),
        mk_tx("MCDONALDS — Restaurants & Cafes", "17.98", TransactionType.EXPENSE, 5,
              ["dining", "fast-food"], suffix="mcdonalds-1"),
        mk_tx("Aral Station — Treibstoff", "58.00", TransactionType.EXPENSE, 5,
              ["fuel", "transport"], suffix="aral-3"),
        mk_tx("MCDONALDS — Restaurants & Cafes", "14.28", TransactionType.EXPENSE, 5,
              ["dining", "fast-food"], suffix="mcdonalds-2"),
        mk_tx("Stoosbahnen AG — Bergbahn", "27.67", TransactionType.EXPENSE, 5,
              ["transport", "travel"], suffix="stoos"),
        mk_tx("Autohof Bremgarten — Hobbies", "1.00", TransactionType.EXPENSE, 5,
              ["shopping"], suffix="autohof-1"),
        mk_tx("Berghotel Oeschinensee — Hotels", "5.81", TransactionType.EXPENSE, 5,
              ["travel", "accommodation"], suffix="berg"),
        mk_tx("Stoosbahnen AG — Transport", "9.31", TransactionType.EXPENSE, 5,
              ["transport", "travel"], suffix="stoos-2"),
        mk_tx("AMAZON PAYMENTS — Haushaltsgeräte", "36.98", TransactionType.EXPENSE, 5,
              ["shopping", "amazon"], suffix="amazon-1"),
        mk_tx("SUMUP CUCKOO ICE CREAM — Essen", "11.80", TransactionType.EXPENSE, 5,
              ["dining", "ice-cream"], suffix="cuckoo"),
        mk_tx("PayPal DMC Digital Maut — Transport", "12.80", TransactionType.EXPENSE, 5,
              ["transport", "toll"], suffix="paypal-maut"),
        mk_tx("Cafe Blausee — Restaurants & Cafes", "12.68", TransactionType.EXPENSE, 5,
              ["dining", "cafe"], suffix="blausee"),
        mk_tx("LS AG Sporthotel — Hotels", "27.94", TransactionType.EXPENSE, 5,
              ["travel", "accommodation"], suffix="sporthotel"),
        mk_tx("Stoosbahnen AG — Transport", "25.42", TransactionType.EXPENSE, 5,
              ["transport", "travel"], suffix="stoos-3"),
        mk_tx("TOTAL SERVICE STATION — Treibstoff", "5.00", TransactionType.EXPENSE, 5,
              ["fuel", "transport"], suffix="total"),
        mk_tx("Landeskrankenhilfe — Krankenversicherung", "72.45", TransactionType.EXPENSE, 4,
              ["insurance", "health"], "KV MS-7.730.004", suffix="krankenkasse"),
        mk_tx("VOLKSWOHL BUND — Berufsunfähigkeitsversicherung", "21.22", TransactionType.EXPENSE, 4,
              ["insurance"], suffix="volkswohl"),
        mk_tx("Raiff. Tankstelle — Treibstoff", "61.00", TransactionType.EXPENSE, 4,
              ["fuel", "transport"], suffix="tank-2"),
        mk_tx("prokundo GmbH — Unfallversicherung", "13.92", TransactionType.EXPENSE, 4,
              ["insurance"], suffix="prokundo"),
        mk_tx("Nils Worm TR — Transfer", "1500.00", TransactionType.EXPENSE, 30,
              ["savings", "transfer"], "EURO-Überweisung", month_offset=-1, suffix="transfer-apr"),
        mk_tx("Netto Marken-Discount — Lebensmittel", "24.09", TransactionType.EXPENSE, 28,
              ["groceries", "daily"], month_offset=-1, suffix="netto-apr"),
        mk_tx("HALL TABAKWAREN — Lebensmittel", "10.00", TransactionType.EXPENSE, 27,
              ["groceries", "daily"], month_offset=-1, suffix="hall-apr"),
        mk_tx("Claude AI Subscription — Software", "106.06", TransactionType.EXPENSE, 27,
              ["software", "subscription"], "ANTHROPIC.CO", month_offset=-1, suffix="claude-apr"),
    ]

    for i, t in enumerate(transactions):
        t.id = sid(f"tx-{i:03d}")
        await cost_repo.save_transaction(t)

    # Create opening balance transactions for previous and current months
    # (These are used by CalculateOpeningBalanceUseCase and EnsureOpeningBalanceTransactionUseCase)
    def mk_opening_balance(month_offset: int, balance: Decimal) -> Transaction:
        m = today.month + month_offset
        y = today.year
        if m < 1:
            m += 12
            y -= 1
        month_name = date(y, m, 1).strftime("%B")
        return Transaction.create(
            f"Opening Balance {month_name}",
            balance,
            TransactionType.INCOME if balance >= 0 else TransactionType.EXPENSE,
            date(y, m, 1),
            id=sid(f"opening-{month_offset}"),
            tags=["opening-balance"],
            is_opening_balance=True,
        )

    # Opening balance for April (calculated as closing of March)
    await cost_repo.save_transaction(
        mk_opening_balance(-1, Decimal("2847.56"))
    )

    print(f"  Recurring:    {len(recurring)}")
    print(f"  Transactions: {len(transactions)} (consorsbank-based, realistic May 2026 data)")
    print(f"  Opening Balance: April 2026 (€2,847.56)")


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed local dev database. ⚠️  LOCAL DEVELOPMENT ONLY."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="DELETE all existing rows before seeding (irreversible!)",
    )
    args = parser.parse_args()

    print("🌱 Seeding local development database...")
    if args.reset:
        print("  ⚠️  --reset: wiping existing data first.")

    async with async_session_factory() as session:
        if args.reset:
            await _reset(session)
        await _seed(session)

    print("✅ Done.")


if __name__ == "__main__":
    asyncio.run(main())
