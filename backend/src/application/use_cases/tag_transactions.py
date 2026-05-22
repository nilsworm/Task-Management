from __future__ import annotations

import json
import logging
import uuid

from src.domain.ai.client import IAIClient
from src.domain.cost.repository import ICostRepository
from src.domain.cost.tags import ALLOWED_TAGS

logger = logging.getLogger(__name__)

_SYSTEM = (
    "Du bist ein Finanz-Kategorisierer. "
    "Antworte ausschließlich mit einem JSON-Array, keine Erklärungen."
)

_PROMPT_TEMPLATE = (
    "Erlaubte Tags: {tags}\n\n"
    "Weise jeder Transaktion passende Tags aus der erlaubten Liste zu. "
    "Mehrere Tags pro Transaktion sind erlaubt. "
    "Transaktionen ohne passenden Tag erhalten ein leeres Array.\n\n"
    "Transaktionen:\n{transactions}\n\n"
    "Antworte ausschließlich mit einem JSON-Array in diesem Format:\n"
    '[{{"id": "<uuid>", "tags": ["tag1", "tag2"]}}, ...]'
)


_BATCH_SIZE = 20


class TagTransactionsUseCase:
    def __init__(self, cost_repo: ICostRepository, ai_client: IAIClient) -> None:
        self._repo = cost_repo
        self._ai = ai_client

    async def execute(self, transaction_ids: list[uuid.UUID]) -> None:
        if not transaction_ids:
            return

        transactions = []
        for tid in transaction_ids:
            tx = await self._repo.get_transaction(tid)
            if tx is not None:
                transactions.append(tx)

        if not transactions:
            return

        for i in range(0, len(transactions), _BATCH_SIZE):
            await self._tag_batch(transactions[i : i + _BATCH_SIZE])

    async def _tag_batch(self, transactions: list) -> None:
        tx_json = json.dumps(
            [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "amount": float(t.amount),
                    "type": t.transaction_type.value,
                    "description": t.description or "",
                }
                for t in transactions
            ],
            ensure_ascii=False,
        )

        prompt = _PROMPT_TEMPLATE.format(
            tags=", ".join(sorted(ALLOWED_TAGS)),
            transactions=tx_json,
        )

        try:
            raw = await self._ai.generate(prompt, _SYSTEM)
        except Exception:
            logger.warning("AI tagging failed: AI unavailable", exc_info=True)
            return

        if not raw:
            logger.warning("AI tagging failed: empty response from model")
            return

        try:
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            results = json.loads(clean)
        except (json.JSONDecodeError, ValueError):
            logger.warning("AI tagging failed: could not parse JSON response: %.200s", raw)
            return

        for item in results:
            if not isinstance(item, dict):
                continue
            try:
                tid = uuid.UUID(str(item["id"]))
            except (KeyError, ValueError):
                continue
            raw_tags = item.get("tags", [])
            if not isinstance(raw_tags, list):
                continue
            valid_tags = [
                t.strip().lower()
                for t in raw_tags
                if isinstance(t, str) and t.strip().lower() in ALLOWED_TAGS
            ]
            await self._repo.update_tags(tid, valid_tags)
