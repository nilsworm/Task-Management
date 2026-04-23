from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone

from src.domain.entities import DailyTask, LongTermGoal, Milestone, SprintTask, Task
from src.domain.sprint import Sprint, SprintStatus
from src.domain.value_objects import (
    DateRange,
    Estimation,
    Priority,
    Tag,
    TaskStatus,
)
from src.infrastructure.persistence.models.goal_model import GoalModel
from src.infrastructure.persistence.models.sprint_model import SprintModel, SprintTaskIdModel
from src.infrastructure.persistence.models.task_model import TaskModel


def _tags_to_json(tags: frozenset[Tag]) -> str:
    return json.dumps([t.name for t in tags])


def _tags_from_json(raw: str) -> frozenset[Tag]:
    return frozenset(Tag(name) for name in json.loads(raw))


def _utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


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
        tags=_tags_to_json(task.tags),
        created_at=task.created_at,
        updated_at=task.updated_at,
    )

    if isinstance(task, DailyTask):
        model.scheduled_date = task.scheduled_date  # type: ignore[assignment]

    elif isinstance(task, SprintTask):
        model.sprint_id = task.sprint_id

    elif isinstance(task, LongTermGoal):
        if task.date_range:
            model.date_range_start = task.date_range.start  # type: ignore[assignment]
            model.date_range_end = task.date_range.end  # type: ignore[assignment]

    elif isinstance(task, Milestone):
        model.due_date = task.due_date  # type: ignore[assignment]
        model.goal_id = task.goal_id

    return model


def task_from_model(model: TaskModel) -> Task:
    estimation = Estimation(model.story_points) if model.story_points else None
    tags = _tags_from_json(model.tags)
    common = dict(
        id=model.id,
        description=model.description,
        status=TaskStatus(model.status),
        priority=Priority(model.priority),
        estimation=estimation,
        tags=tags,
        created_at=_utc(model.created_at),  # type: ignore[arg-type]
        updated_at=_utc(model.updated_at),  # type: ignore[arg-type]
    )

    task_type = model.task_type
    if task_type == "daily":
        return DailyTask(
            model.title,
            scheduled_date=model.scheduled_date,  # type: ignore[arg-type]
            **common,
        )
    if task_type == "sprint":
        return SprintTask(
            model.title,
            sprint_id=model.sprint_id,
            **common,
        )
    if task_type == "goal":
        date_range = None
        if model.date_range_start and model.date_range_end:
            date_range = DateRange(model.date_range_start, model.date_range_end)  # type: ignore[arg-type]
        return LongTermGoal(model.title, date_range=date_range, **common)
    if task_type == "milestone":
        return Milestone(
            model.title,
            due_date=model.due_date,  # type: ignore[arg-type]
            goal_id=model.goal_id,
            **common,
        )
    raise ValueError(f"Unknown task_type: {task_type!r}")


# ---------------------------------------------------------------------------
# Sprint
# ---------------------------------------------------------------------------

def sprint_to_model(sprint: Sprint) -> SprintModel:
    return SprintModel(
        id=sprint.id,
        name=sprint.name,
        status=sprint.status.value,
        start_date=sprint.date_range.start,  # type: ignore[arg-type]
        end_date=sprint.date_range.end,  # type: ignore[arg-type]
        created_at=sprint.created_at,
    )


def sprint_from_model(model: SprintModel, task_ids: list[uuid.UUID]) -> Sprint:
    return Sprint(
        model.name,
        DateRange(model.start_date, model.end_date),  # type: ignore[arg-type]
        id=model.id,
        status=SprintStatus(model.status),
        task_ids=task_ids,
        created_at=_utc(model.created_at),  # type: ignore[arg-type]
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
        tags=_tags_to_json(goal.tags),
        created_at=goal.created_at,
        updated_at=goal.updated_at,
    )
    if goal.date_range:
        model.date_range_start = goal.date_range.start  # type: ignore[assignment]
        model.date_range_end = goal.date_range.end  # type: ignore[assignment]
    return model


def goal_from_model(model: GoalModel) -> LongTermGoal:
    date_range = None
    if model.date_range_start and model.date_range_end:
        date_range = DateRange(model.date_range_start, model.date_range_end)  # type: ignore[arg-type]
    return LongTermGoal(
        model.title,
        id=model.id,
        description=model.description,
        status=TaskStatus(model.status),
        priority=Priority(model.priority),
        tags=_tags_from_json(model.tags),
        date_range=date_range,
        created_at=_utc(model.created_at),  # type: ignore[arg-type]
        updated_at=_utc(model.updated_at),  # type: ignore[arg-type]
    )
