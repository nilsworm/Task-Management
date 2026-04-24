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

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import DailyTask, KeyResult, LongTermGoal, Milestone, SprintTask
from src.domain.sprint import Sprint, SprintStatus
from src.domain.value_objects import DateRange, Estimation, Priority, TaskStatus
from src.infrastructure.database import async_session_factory
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
    # Sprint 3 tasks — mixed statuses (28 story points total)
    # -----------------------------------------------------------------------

    s3_tasks: list[SprintTask] = [
        SprintTask("Frontend scaffolding & routing",
                   sprint_id=s3_id, id=sid("s3-t1"),
                   status=TaskStatus.DONE, priority=Priority.HIGH,
                   estimation=_est(3), created_at=_now(-10)),
        SprintTask("Tasks view with filters & modals",
                   sprint_id=s3_id, id=sid("s3-t2"),
                   status=TaskStatus.DONE, priority=Priority.HIGH,
                   estimation=_est(5), created_at=_now(-9)),
        SprintTask("Sprint Kanban board with drag & drop",
                   sprint_id=s3_id, id=sid("s3-t3"),
                   status=TaskStatus.IN_PROGRESS, priority=Priority.HIGH,
                   estimation=_est(8), created_at=_now(-8)),
        SprintTask("Goals view with KeyResult progress bars",
                   sprint_id=s3_id, id=sid("s3-t4"),
                   status=TaskStatus.REVIEW, priority=Priority.MEDIUM,
                   estimation=_est(5), created_at=_now(-7)),
        SprintTask("Dashboard charts (Recharts)",
                   sprint_id=s3_id, id=sid("s3-t5"),
                   status=TaskStatus.TODO, priority=Priority.MEDIUM,
                   estimation=_est(5), created_at=_now(-6)),
        SprintTask("Dark mode & theme toggle",
                   sprint_id=s3_id, id=sid("s3-t6"),
                   status=TaskStatus.BACKLOG, priority=Priority.LOW,
                   estimation=_est(2), created_at=_now(-5)),
    ]
    # total: 3+5+8+5+5+2 = 28 pts; done=8, remaining=20

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
        DailyTask("Review open PRs",
                  id=sid("daily-1"), scheduled_date=today,
                  status=TaskStatus.TODO, priority=Priority.HIGH,
                  created_at=_now()),
        DailyTask("Write standup notes",
                  id=sid("daily-2"), scheduled_date=d(-1),
                  status=TaskStatus.DONE, priority=Priority.MEDIUM,
                  created_at=_now(-1)),
        DailyTask("Prep weekly sync agenda",
                  id=sid("daily-3"), scheduled_date=today,
                  status=TaskStatus.IN_PROGRESS, priority=Priority.MEDIUM,
                  created_at=_now()),
        DailyTask("Fix flaky test in CI",
                  id=sid("daily-4"), scheduled_date=d(-3),
                  status=TaskStatus.CANCELLED, priority=Priority.LOW,
                  created_at=_now(-3)),
        DailyTask("Update ticket statuses in backlog",
                  id=sid("daily-5"), scheduled_date=d(-2),
                  status=TaskStatus.DONE, priority=Priority.LOW,
                  created_at=_now(-2)),
    ]
    for t in daily_tasks:
        await task_repo.save(t)

    # -----------------------------------------------------------------------
    # Milestone tasks
    # -----------------------------------------------------------------------

    milestone_tasks: list[Milestone] = [
        Milestone("v1.0 Beta Release",
                  id=sid("milestone-1"), due_date=d(14),
                  status=TaskStatus.TODO, priority=Priority.CRITICAL,
                  created_at=_now(-5)),
        Milestone("v1.0 Public Release",
                  id=sid("milestone-2"), due_date=d(42),
                  status=TaskStatus.BACKLOG, priority=Priority.HIGH,
                  created_at=_now(-5)),
    ]
    for t in milestone_tasks:
        await task_repo.save(t)

    # -----------------------------------------------------------------------
    # LongTermGoal task (task_type="goal", not to confuse with Goal entity)
    # -----------------------------------------------------------------------

    goal_task = LongTermGoal(
        "Define v2.0 scope",
        id=sid("goal-task-1"),
        status=TaskStatus.BACKLOG,
        priority=Priority.MEDIUM,
        date_range=DateRange(d(30), d(90)),
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
