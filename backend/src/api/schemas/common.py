from typing import Literal

PriorityLiteral = Literal["low", "medium", "high", "critical"]
StatusLiteral = Literal[
    "backlog", "todo", "in_progress", "review", "blocked", "done", "cancelled"
]
