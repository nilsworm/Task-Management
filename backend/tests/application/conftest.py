from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

import pytest

from src.domain.cost.entities import RecurringTransaction, Transaction
from src.domain.cost.repository import ICostRepository
from src.domain.cost.value_objects import TransactionType
from src.domain.entities import KeyResult, LongTermGoal, SprintTask, Task
from src.domain.events import IDomainEvent, IEventHandler, InMemoryEventBus
from src.domain.factory import TaskFactory
from src.domain.repositories.goal_repository import IGoalRepository
from src.domain.repositories.sprint_repository import ISprintRepository
from src.domain.repositories.task_repository import ITaskRepository
from src.domain.sprint import Sprint, SprintStatus
from src.domain.value_objects import TaskStatus


class InMemoryTaskRepository(ITaskRepository):
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, Task] = {}

    async def get_by_id(self, task_id: uuid.UUID) -> Task | None:
        return self._store.get(task_id)

    async def save(self, task: Task) -> None:
        self._store[task.id] = task

    async def delete(self, task_id: uuid.UUID) -> None:
        self._store.pop(task_id, None)

    async def list_all(self) -> list[Task]:
        return list(self._store.values())

    async def list_by_status(self, status: TaskStatus) -> list[Task]:
        return [t for t in self._store.values() if t.status == status]

    async def list_by_sprint(
        self,
        sprint_id: uuid.UUID,
        status_filter: TaskStatus | None = None,
    ) -> list[SprintTask]:
        tasks = [
            t for t in self._store.values()
            if isinstance(t, SprintTask) and t.sprint_id == sprint_id
        ]
        if status_filter is not None:
            tasks = [t for t in tasks if t.status == status_filter]
        return tasks

    async def list_by_sprint_ids(
        self, sprint_ids: list[uuid.UUID]
    ) -> list[SprintTask]:
        return [
            t for t in self._store.values()
            if isinstance(t, SprintTask) and t.sprint_id in sprint_ids
        ]

    async def list_by_search(self, query: str) -> list[Task]:
        q = query.lower()
        return [t for t in self._store.values() if q in t.title.lower()]

    async def list_overdue(self) -> list[Task]:
        today = date.today()
        return [
            t for t in self._store.values()
            if getattr(t, "due_date", None) is not None
            and t.due_date < today
            and t.status not in {TaskStatus.DONE, TaskStatus.CANCELLED}
        ]


class InMemorySprintRepository(ISprintRepository):
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, Sprint] = {}

    async def get_by_id(self, sprint_id: uuid.UUID) -> Sprint | None:
        return self._store.get(sprint_id)

    async def save(self, sprint: Sprint) -> None:
        self._store[sprint.id] = sprint

    async def delete(self, sprint_id: uuid.UUID) -> None:
        self._store.pop(sprint_id, None)

    async def list_all(self) -> list[Sprint]:
        return list(self._store.values())

    async def get_active(self) -> Sprint | None:
        for sprint in self._store.values():
            if sprint.status is SprintStatus.ACTIVE:
                return sprint
        return None


class InMemoryGoalRepository(IGoalRepository):
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, LongTermGoal] = {}
        self._key_results: dict[uuid.UUID, KeyResult] = {}

    async def get_by_id(self, goal_id: uuid.UUID) -> LongTermGoal | None:
        return self._store.get(goal_id)

    async def save(self, goal: LongTermGoal) -> None:
        self._store[goal.id] = goal

    async def delete(self, goal_id: uuid.UUID) -> None:
        self._store.pop(goal_id, None)

    async def list_all(self) -> list[LongTermGoal]:
        return list(self._store.values())

    async def list_key_results(self, goal_id: uuid.UUID) -> list[KeyResult]:
        return [kr for kr in self._key_results.values() if kr.goal_id == goal_id]

    async def list_all_key_results(self) -> list[KeyResult]:
        return list(self._key_results.values())

    async def get_key_result(self, key_result_id: uuid.UUID) -> KeyResult | None:
        return self._key_results.get(key_result_id)

    async def save_key_result(self, key_result: KeyResult) -> None:
        self._key_results[key_result.id] = key_result

    async def delete_key_result(self, key_result_id: uuid.UUID) -> None:
        self._key_results.pop(key_result_id, None)


class InMemoryCostRepository(ICostRepository):
    def __init__(self) -> None:
        self._transactions: dict[uuid.UUID, Transaction] = {}
        self._recurring: dict[uuid.UUID, RecurringTransaction] = {}

    async def save_transaction(self, transaction: Transaction) -> None:
        self._transactions[transaction.id] = transaction

    async def save_transactions_bulk(self, transactions: list[Transaction]) -> None:
        for transaction in transactions:
            self._transactions[transaction.id] = transaction

    async def get_transaction(self, transaction_id: uuid.UUID) -> Transaction | None:
        return self._transactions.get(transaction_id)

    async def list_transactions(
        self,
        year: int | None = None,
        month: int | None = None,
        tags: list[str] | None = None,
        transaction_type: TransactionType | None = None,
    ) -> list[Transaction]:
        result = list(self._transactions.values())
        if year is not None:
            result = [t for t in result if t.date.year == year]
        if month is not None:
            result = [t for t in result if t.date.month == month]
        if transaction_type is not None:
            result = [t for t in result if t.transaction_type == transaction_type]
        if tags:
            result = [t for t in result if any(tag in t.tags for tag in tags)]
        return sorted(result, key=lambda t: t.date, reverse=True)

    async def delete_transaction(self, transaction_id: uuid.UUID) -> None:
        self._transactions.pop(transaction_id, None)

    async def save_recurring(self, recurring: RecurringTransaction) -> None:
        self._recurring[recurring.id] = recurring

    async def get_recurring(self, recurring_id: uuid.UUID) -> RecurringTransaction | None:
        return self._recurring.get(recurring_id)

    async def list_recurring(self, active_only: bool = False) -> list[RecurringTransaction]:
        result = list(self._recurring.values())
        if active_only:
            result = [r for r in result if r.is_active]
        return result

    async def delete_recurring(self, recurring_id: uuid.UUID) -> None:
        self._recurring.pop(recurring_id, None)

    async def list_all_tags(self) -> list[str]:
        tags: set[str] = set()
        for t in self._transactions.values():
            tags.update(t.tags)
        for r in self._recurring.values():
            tags.update(r.tags)
        return sorted(tags)

    async def create_transaction_from_import(
        self,
        parsed_row: dict[str, Any],
        import_source: str,
    ) -> Transaction:
        """Create and persist a Transaction from parsed CSV row."""
        transaction = Transaction.create(
            title=parsed_row["description"],
            amount=parsed_row["amount"],
            transaction_type=TransactionType(parsed_row["type"].lower()),
            transaction_date=parsed_row["date"],
            import_source=import_source,
        )
        await self.save_transaction(transaction)
        return transaction

    async def get_last_import_status(self) -> dict:
        """Get last import date and transaction count from imports."""
        imported = [
            t for t in self._transactions.values() if t.import_source is not None
        ]
        if not imported:
            return {
                "last_import_date": None,
                "transaction_count": 0,
            }
        max_date = max(t.date for t in imported)
        return {
            "last_import_date": max_date.isoformat(),
            "transaction_count": len(imported),
        }

    async def get_opening_balance_transaction(
        self, year: int, month: int
    ) -> Transaction | None:
        """Get opening balance transaction for month (if exists)."""
        for tx in self._transactions.values():
            if (
                tx.is_opening_balance
                and tx.date.year == year
                and tx.date.month == month
            ):
                return tx
        return None

    @property
    def transactions(self) -> list[Transaction]:
        """Expose transactions list for testing."""
        return list(self._transactions.values())


class EventSpy(IEventHandler):
    """Captures all published events for assertion in tests."""

    def __init__(self) -> None:
        self.events: list[IDomainEvent] = []

    def handle(self, event: IDomainEvent) -> None:
        self.events.append(event)


@pytest.fixture
def task_repo() -> InMemoryTaskRepository:
    return InMemoryTaskRepository()


@pytest.fixture
def sprint_repo() -> InMemorySprintRepository:
    return InMemorySprintRepository()


@pytest.fixture
def goal_repo() -> InMemoryGoalRepository:
    return InMemoryGoalRepository()


@pytest.fixture
def cost_repo() -> InMemoryCostRepository:
    return InMemoryCostRepository()


@pytest.fixture
def event_bus() -> InMemoryEventBus:
    return InMemoryEventBus()


@pytest.fixture
def factory() -> TaskFactory:
    return TaskFactory()
