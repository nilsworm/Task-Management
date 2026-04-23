from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.domain.entities import DailyTask, KeyResult, LongTermGoal, Milestone, SprintTask, Task
from src.domain.sprint import Sprint, SprintStatus
from src.domain.value_objects import DateRange, Estimation, Priority, Tag, TaskStatus
from src.infrastructure.persistence.models.goal_model import GoalModel, KeyResultModel
from src.infrastructure.persistence.models.sprint_model import SprintModel
from src.infrastructure.persistence.models.task_model import TaskModel


def _utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def _tags_to_list(tags: frozenset[Tag]) -> list[str]:
    return [t.name for t in tags]


def _tags_from_list(raw: list[str]) -> frozenset[Tag]:
    return frozenset(Tag(name) for name in (raw or []))


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

def task_to_model(task: Task) -> TaskModel:
    model = TaskModel(
        id=task.id,
        task_type=task.task_type,
        title=task.title,
        description=task.description,
        status=task.status.value,
        priority=task.priority.value,
        story_points=task.estimation.story_points if task.estimation else None,
        tags=_tags_to_list(task.tags),
        created_at=task.created_at,
        updated_at=task.updated_at,
    )
    if isinstance(task, DailyTask):
        model.scheduled_date = task.scheduled_date
    elif isinstance(task, SprintTask):
        model.sprint_id = task.sprint_id
    elif isinstance(task, LongTermGoal) and task.date_range:
        model.date_range_start = task.date_range.start
        model.date_range_end = task.date_range.end
    elif isinstance(task, Milestone):
        model.due_date = task.due_date
        model.goal_id = task.goal_id
    return model


def task_from_model(model: TaskModel) -> Task:
    estimation = Estimation(model.story_points) if model.story_points else None
    common = dict(
        id=model.id,
        description=model.description,
        status=TaskStatus(model.status),
        priority=Priority(model.priority),
        estimation=estimation,
        tags=_tags_from_list(model.tags),
        created_at=_utc(model.created_at),
        updated_at=_utc(model.updated_at),
    )
    if model.task_type == "daily":
        return DailyTask(model.title, scheduled_date=model.scheduled_date, **common)
    if model.task_type == "sprint":
        return SprintTask(model.title, sprint_id=model.sprint_id, **common)
    if model.task_type == "goal":
        date_range = (
            DateRange(model.date_range_start, model.date_range_end)
            if model.date_range_start and model.date_range_end
            else None
        )
        return LongTermGoal(model.title, date_range=date_range, **common)
    if model.task_type == "milestone":
        return Milestone(model.title, due_date=model.due_date, goal_id=model.goal_id, **common)
    raise ValueError(f"Unknown task_type: {model.task_type!r}")


# ---------------------------------------------------------------------------
# Sprint
# ---------------------------------------------------------------------------

def sprint_to_model(sprint: Sprint) -> SprintModel:
    return SprintModel(
        id=sprint.id,
        name=sprint.name,
        status=sprint.status.value,
        start_date=sprint.date_range.start,
        end_date=sprint.date_range.end,
        created_at=sprint.created_at,
    )


def sprint_from_model(model: SprintModel, task_ids: list[uuid.UUID]) -> Sprint:
    return Sprint(
        model.name,
        DateRange(model.start_date, model.end_date),
        id=model.id,
        status=SprintStatus(model.status),
        task_ids=task_ids,
        created_at=_utc(model.created_at),
    )


# ---------------------------------------------------------------------------
# Goal (LongTermGoal)
# ---------------------------------------------------------------------------

def goal_to_model(goal: LongTermGoal) -> GoalModel:
    model = GoalModel(
        id=goal.id,
        title=goal.title,
        description=goal.description,
        status=goal.status.value,
        priority=goal.priority.value,
        tags=_tags_to_list(goal.tags),
        created_at=goal.created_at,
        updated_at=goal.updated_at,
    )
    if goal.date_range:
        model.date_range_start = goal.date_range.start
        model.date_range_end = goal.date_range.end
    return model


def key_result_to_model(kr: KeyResult) -> KeyResultModel:
    return KeyResultModel(
        id=kr.id,
        goal_id=kr.goal_id,
        title=kr.title,
        description=kr.description,
        target_value=kr.target_value,
        current_value=kr.current_value,
        unit=kr.unit,
        created_at=kr.created_at,
        updated_at=kr.updated_at,
    )


def key_result_from_model(model: KeyResultModel) -> KeyResult:
    return KeyResult(
        id=model.id,
        goal_id=model.goal_id,
        title=model.title,
        description=model.description,
        target_value=model.target_value,
        current_value=model.current_value,
        unit=model.unit,
        created_at=_utc(model.created_at),
        updated_at=_utc(model.updated_at),
    )


def goal_from_model(model: GoalModel) -> LongTermGoal:
    date_range = (
        DateRange(model.date_range_start, model.date_range_end)
        if model.date_range_start and model.date_range_end
        else None
    )
    return LongTermGoal(
        model.title,
        id=model.id,
        description=model.description,
        status=TaskStatus(model.status),
        priority=Priority(model.priority),
        tags=_tags_from_list(model.tags),
        date_range=date_range,
        created_at=_utc(model.created_at),
        updated_at=_utc(model.updated_at),
    )
