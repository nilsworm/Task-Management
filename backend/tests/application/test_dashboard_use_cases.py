"""Unit tests for dashboard use cases."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest

from src.application.exceptions import EntityNotFoundError
from src.application.use_cases.dashboard_use_cases import (
    GetDashboardMetricsUseCase,
    GetDashboardUseCase,
    GetGoalProgressUseCase,
    GetSprintBurndownUseCase,
    GetVelocityUseCase,
)
from src.domain.entities import KeyResult, LongTermGoal
from src.domain.factory import TaskFactory
from src.domain.sprint import Sprint
from src.domain.value_objects import DateRange, Estimation, TaskStatus

from .conftest import InMemoryGoalRepository, InMemorySprintRepository, InMemoryTaskRepository

_factory = TaskFactory()
_dr = DateRange(date(2026, 5, 1), date(2026, 5, 14))


# ---------------------------------------------------------------------------
# GetDashboardUseCase
# ---------------------------------------------------------------------------

async def test_dashboard_empty_state(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
    goal_repo: InMemoryGoalRepository,
) -> None:
    data = await GetDashboardUseCase(task_repo, sprint_repo, goal_repo).execute()

    assert data.total_tasks == 0
    assert data.total_goals == 0
    assert data.active_sprint is None
    assert data.backlog == 0
    assert data.done == 0


async def test_dashboard_counts_tasks_by_status(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
    goal_repo: InMemoryGoalRepository,
) -> None:
    t1 = _factory.create_daily("Task A")
    t2 = _factory.create_daily("Task B")
    t2.transition_to(TaskStatus.TODO)
    t3 = _factory.create_daily("Task C")
    t3.transition_to(TaskStatus.TODO)
    t3.transition_to(TaskStatus.IN_PROGRESS)
    await task_repo.save(t1)
    await task_repo.save(t2)
    await task_repo.save(t3)

    data = await GetDashboardUseCase(task_repo, sprint_repo, goal_repo).execute()

    assert data.total_tasks == 3
    assert data.backlog == 1
    assert data.todo == 1
    assert data.in_progress == 1
    assert data.done == 0


async def test_dashboard_active_sprint_completion(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
    goal_repo: InMemoryGoalRepository,
) -> None:
    sprint = Sprint("Sprint 1", _dr)
    sprint.start()
    await sprint_repo.save(sprint)

    t1 = _factory.create_sprint("Task A", sprint_id=sprint.id)
    t2 = _factory.create_sprint("Task B", sprint_id=sprint.id)
    t2.transition_to(TaskStatus.TODO)
    t2.transition_to(TaskStatus.IN_PROGRESS)
    t2.transition_to(TaskStatus.REVIEW)
    t2.transition_to(TaskStatus.DONE)
    await task_repo.save(t1)
    await task_repo.save(t2)

    data = await GetDashboardUseCase(task_repo, sprint_repo, goal_repo).execute()

    assert data.active_sprint is not None
    assert data.active_sprint.name == "Sprint 1"
    assert data.active_sprint.total_tasks == 2
    assert data.active_sprint.done_tasks == 1
    assert data.active_sprint.completion_percent == 50.0


async def test_dashboard_no_active_sprint_when_planned(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
    goal_repo: InMemoryGoalRepository,
) -> None:
    sprint = Sprint("Planned Sprint", _dr)
    await sprint_repo.save(sprint)

    data = await GetDashboardUseCase(task_repo, sprint_repo, goal_repo).execute()

    assert data.active_sprint is None


async def test_dashboard_sprint_zero_tasks_completion(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
    goal_repo: InMemoryGoalRepository,
) -> None:
    sprint = Sprint("Empty Sprint", _dr)
    sprint.start()
    await sprint_repo.save(sprint)

    data = await GetDashboardUseCase(task_repo, sprint_repo, goal_repo).execute()

    assert data.active_sprint is not None
    assert data.active_sprint.completion_percent == 0.0


# ---------------------------------------------------------------------------
# GetDashboardMetricsUseCase
# ---------------------------------------------------------------------------

async def test_metrics_empty(task_repo: InMemoryTaskRepository) -> None:
    data = await GetDashboardMetricsUseCase(task_repo).execute()
    assert data.completion_rate == 0.0
    assert data.done == 0
    assert data.backlog == 0


async def test_metrics_counts_all_statuses(task_repo: InMemoryTaskRepository) -> None:
    t1 = _factory.create_daily("A")
    t2 = _factory.create_daily("B")
    t2.transition_to(TaskStatus.TODO)
    t3 = _factory.create_daily("C")
    t3.transition_to(TaskStatus.TODO)
    t3.transition_to(TaskStatus.IN_PROGRESS)
    t4 = _factory.create_daily("D")
    t4.transition_to(TaskStatus.TODO)
    t4.transition_to(TaskStatus.IN_PROGRESS)
    t4.transition_to(TaskStatus.REVIEW)
    t4.transition_to(TaskStatus.DONE)
    for t in [t1, t2, t3, t4]:
        await task_repo.save(t)

    data = await GetDashboardMetricsUseCase(task_repo).execute()

    assert data.backlog == 1
    assert data.todo == 1
    assert data.in_progress == 1
    assert data.done == 1
    assert data.completion_rate == 25.0  # 1 done / 4 eligible


async def test_metrics_completion_rate_excludes_cancelled(task_repo: InMemoryTaskRepository) -> None:
    t_done = _factory.create_daily("Done")
    t_done.transition_to(TaskStatus.TODO)
    t_done.transition_to(TaskStatus.IN_PROGRESS)
    t_done.transition_to(TaskStatus.REVIEW)
    t_done.transition_to(TaskStatus.DONE)
    t_cancelled = _factory.create_daily("Cancelled")
    t_cancelled.transition_to(TaskStatus.CANCELLED)
    await task_repo.save(t_done)
    await task_repo.save(t_cancelled)

    data = await GetDashboardMetricsUseCase(task_repo).execute()

    assert data.completion_rate == 100.0  # 1 done / 1 eligible (cancelled excluded)


async def test_metrics_all_cancelled_gives_zero_rate(task_repo: InMemoryTaskRepository) -> None:
    t = _factory.create_daily("Cancelled")
    t.transition_to(TaskStatus.CANCELLED)
    await task_repo.save(t)

    data = await GetDashboardMetricsUseCase(task_repo).execute()

    assert data.completion_rate == 0.0


# ---------------------------------------------------------------------------
# GetSprintBurndownUseCase
# ---------------------------------------------------------------------------

async def test_burndown_uses_active_sprint_when_no_id_given(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
) -> None:
    sprint = Sprint("Active", _dr)
    sprint.start()
    await sprint_repo.save(sprint)

    data = await GetSprintBurndownUseCase(task_repo, sprint_repo).execute()

    assert data.sprint_id == sprint.id
    assert data.sprint_name == "Active"


async def test_burndown_no_active_sprint_raises(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
) -> None:
    with pytest.raises(EntityNotFoundError):
        await GetSprintBurndownUseCase(task_repo, sprint_repo).execute()


async def test_burndown_unknown_sprint_id_raises(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
) -> None:
    with pytest.raises(EntityNotFoundError):
        await GetSprintBurndownUseCase(task_repo, sprint_repo).execute(uuid.uuid4())


async def test_burndown_ideal_line_length_matches_sprint_duration(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
) -> None:
    sprint = Sprint("Sprint", _dr)  # 2026-05-01 to 2026-05-14 = 14 days
    sprint.start()
    await sprint_repo.save(sprint)

    data = await GetSprintBurndownUseCase(task_repo, sprint_repo).execute()

    assert len(data.ideal_line) == 14  # inclusive days
    assert data.ideal_line[0].date == date(2026, 5, 1)
    assert data.ideal_line[-1].date == date(2026, 5, 14)


async def test_burndown_ideal_line_starts_at_total_ends_at_zero(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
) -> None:
    sprint = Sprint("Sprint", _dr)
    sprint.start()
    await sprint_repo.save(sprint)

    t = _factory.create_sprint("Task", sprint_id=sprint.id)
    t.set_estimation(Estimation(story_points=10))
    await task_repo.save(t)

    data = await GetSprintBurndownUseCase(task_repo, sprint_repo).execute()

    assert data.total_points == 10
    assert data.ideal_line[0].remaining_points == 10
    assert data.ideal_line[-1].remaining_points == 0


async def test_burndown_actual_remaining_decreases_with_done_tasks(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
) -> None:
    sprint = Sprint("Sprint", _dr)
    sprint.start()
    await sprint_repo.save(sprint)

    t1 = _factory.create_sprint("Done", sprint_id=sprint.id)
    t1.set_estimation(Estimation(story_points=5))
    t1.transition_to(TaskStatus.TODO)
    t1.transition_to(TaskStatus.IN_PROGRESS)
    t1.transition_to(TaskStatus.REVIEW)
    t1.transition_to(TaskStatus.DONE)

    t2 = _factory.create_sprint("In progress", sprint_id=sprint.id)
    t2.set_estimation(Estimation(story_points=3))
    await task_repo.save(t1)
    await task_repo.save(t2)

    data = await GetSprintBurndownUseCase(task_repo, sprint_repo).execute()

    assert data.total_points == 8
    assert data.actual_remaining == 3  # 8 - 5 (done)


async def test_burndown_no_estimations_gives_zero_points(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
) -> None:
    sprint = Sprint("Sprint", _dr)
    sprint.start()
    await sprint_repo.save(sprint)
    t = _factory.create_sprint("No estimate", sprint_id=sprint.id)
    await task_repo.save(t)

    data = await GetSprintBurndownUseCase(task_repo, sprint_repo).execute()

    assert data.total_points == 0
    assert data.actual_remaining == 0


async def test_burndown_by_explicit_sprint_id(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
) -> None:
    sprint = Sprint("Completed Sprint", _dr)
    sprint.start()
    sprint.complete()
    await sprint_repo.save(sprint)

    data = await GetSprintBurndownUseCase(task_repo, sprint_repo).execute(sprint.id)

    assert data.sprint_id == sprint.id


# ---------------------------------------------------------------------------
# GetVelocityUseCase
# ---------------------------------------------------------------------------

async def test_velocity_empty_no_completed_sprints(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
) -> None:
    data = await GetVelocityUseCase(task_repo, sprint_repo).execute()
    assert data.sprints == []
    assert data.average_velocity == 0.0


async def test_velocity_ignores_planned_and_active_sprints(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
) -> None:
    planned = Sprint("Planned", _dr)
    active = Sprint("Active", _dr)
    active.start()
    await sprint_repo.save(planned)
    await sprint_repo.save(active)

    data = await GetVelocityUseCase(task_repo, sprint_repo).execute()
    assert data.sprints == []


async def test_velocity_sums_done_story_points(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
) -> None:
    sprint = Sprint("Completed", _dr)
    sprint.start()
    sprint.complete()
    await sprint_repo.save(sprint)

    t1 = _factory.create_sprint("Task A", sprint_id=sprint.id)
    t1.set_estimation(Estimation(story_points=5))
    t1.transition_to(TaskStatus.TODO)
    t1.transition_to(TaskStatus.IN_PROGRESS)
    t1.transition_to(TaskStatus.REVIEW)
    t1.transition_to(TaskStatus.DONE)

    t2 = _factory.create_sprint("Task B", sprint_id=sprint.id)
    t2.set_estimation(Estimation(story_points=3))  # not done — excluded
    await task_repo.save(t1)
    await task_repo.save(t2)

    data = await GetVelocityUseCase(task_repo, sprint_repo).execute()

    assert len(data.sprints) == 1
    assert data.sprints[0].completed_points == 5
    assert data.average_velocity == 5.0


async def test_velocity_average_across_multiple_sprints(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
) -> None:
    for points in [4, 6]:
        sprint = Sprint(f"Sprint {points}pts", _dr)
        sprint.start()
        sprint.complete()
        await sprint_repo.save(sprint)
        t = _factory.create_sprint(f"Task {points}", sprint_id=sprint.id)
        t.set_estimation(Estimation(story_points=points))
        t.transition_to(TaskStatus.TODO)
        t.transition_to(TaskStatus.IN_PROGRESS)
        t.transition_to(TaskStatus.REVIEW)
        t.transition_to(TaskStatus.DONE)
        await task_repo.save(t)

    data = await GetVelocityUseCase(task_repo, sprint_repo).execute()

    assert len(data.sprints) == 2
    assert data.average_velocity == 5.0  # (4 + 6) / 2


async def test_velocity_last_n_limits_results(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
) -> None:
    for i in range(4):
        sprint = Sprint(f"Sprint {i}", _dr)
        sprint.start()
        sprint.complete()
        await sprint_repo.save(sprint)

    data = await GetVelocityUseCase(task_repo, sprint_repo).execute(last_n=2)
    assert len(data.sprints) == 2


# ---------------------------------------------------------------------------
# GetGoalProgressUseCase
# ---------------------------------------------------------------------------

def _kr(goal_id: uuid.UUID, current: float, target: float) -> KeyResult:
    now = datetime.now(timezone.utc)
    return KeyResult(
        id=uuid.uuid4(),
        goal_id=goal_id,
        title="KR",
        description="",
        target_value=target,
        current_value=current,
        unit="units",
        created_at=now,
        updated_at=now,
    )


async def test_goal_progress_empty(goal_repo: InMemoryGoalRepository) -> None:
    data = await GetGoalProgressUseCase(goal_repo).execute()
    assert data.goals == []


async def test_goal_progress_no_krs_gives_zero(goal_repo: InMemoryGoalRepository) -> None:
    goal = LongTermGoal("Learn Rust")
    await goal_repo.save(goal)

    data = await GetGoalProgressUseCase(goal_repo).execute()

    assert len(data.goals) == 1
    assert data.goals[0].progress_percent == 0.0
    assert data.goals[0].key_results_count == 0


async def test_goal_progress_averages_krs(goal_repo: InMemoryGoalRepository) -> None:
    goal = LongTermGoal("Master Python")
    await goal_repo.save(goal)
    await goal_repo.save_key_result(_kr(goal.id, current=50.0, target=100.0))  # 50%
    await goal_repo.save_key_result(_kr(goal.id, current=100.0, target=100.0))  # 100%

    data = await GetGoalProgressUseCase(goal_repo).execute()

    assert len(data.goals) == 1
    assert data.goals[0].progress_percent == 75.0
    assert data.goals[0].key_results_count == 2


async def test_goal_progress_caps_at_100(goal_repo: InMemoryGoalRepository) -> None:
    goal = LongTermGoal("Overshoot")
    await goal_repo.save(goal)
    await goal_repo.save_key_result(_kr(goal.id, current=200.0, target=100.0))  # capped at 100%

    data = await GetGoalProgressUseCase(goal_repo).execute()

    assert data.goals[0].progress_percent == 100.0


async def test_goal_progress_multiple_goals(goal_repo: InMemoryGoalRepository) -> None:
    g1 = LongTermGoal("Goal A")
    g2 = LongTermGoal("Goal B")
    await goal_repo.save(g1)
    await goal_repo.save(g2)
    await goal_repo.save_key_result(_kr(g1.id, 25.0, 100.0))  # 25%

    data = await GetGoalProgressUseCase(goal_repo).execute()

    goal_ids = {g.goal_id for g in data.goals}
    assert g1.id in goal_ids
    assert g2.id in goal_ids
    g1_item = next(g for g in data.goals if g.goal_id == g1.id)
    g2_item = next(g for g in data.goals if g.goal_id == g2.id)
    assert g1_item.progress_percent == 25.0
    assert g2_item.progress_percent == 0.0
