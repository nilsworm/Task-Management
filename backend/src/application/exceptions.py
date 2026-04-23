from __future__ import annotations


class EntityNotFoundError(ValueError):
    def __init__(self, entity: str, entity_id: str) -> None:
        super().__init__(f"{entity} {entity_id} not found")
        self.entity = entity
        self.entity_id = entity_id


class InvalidOperationError(ValueError):
    """Raised when a domain operation is not permitted in the current state."""
