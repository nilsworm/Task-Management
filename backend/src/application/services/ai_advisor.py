from __future__ import annotations

import json
import logging
from calendar import month_abbr, month_name
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import AsyncIterator

from src.domain.cost.repository import ICostRepository
from src.domain.cost.value_objects import TransactionType
from src.infrastructure.ai.ollama_client import IOllamaClient

logger = logging.getLogger(__name__)

_CHAT_SYSTEM = (
    "Du bist ein persönlicher Finanzberater. Antworte auf Deutsch, präzise, "
    "maximal 3 kurze Absätze. Nutze ausschließlich die bereitgestellten Finanzdaten "
    "als Grundlage. Beantworte nur Fragen zu persönlichen Finanzen."
)

_INSIGHTS_SYSTEM = "Du bist ein persönlicher Finanzberater. Antworte ausschließlich mit einem JSON-Array."

_INSIGHTS_PROMPT = (
    "Analysiere die folgenden Finanzdaten und gib exakt 3 Insights als JSON-Array zurück.\n"
    "Jeder Insight hat: title (max 60 Zeichen), body (max 120 Zeichen), "
    "type (warning|tip|forecast).\n"
    "Gib ausschließlich das JSON-Array zurück, keine Erklärungen.\n\n"
    "{context}"
)

_CHAT_PROMPT = "{question}\n\nFinanzdaten:\n{context}"


@dataclass
class InsightCard:
    title: str
    body: str
    type: str  # "warning" | "tip" | "forecast"


class AIAdvisorService:
    def __init__(self, cost_repo: ICostRepository, ollama: IOllamaClient) -> None:
        self._repo = cost_repo
        self._ollama = ollama

    async def _build_context(self) -> str:
        today = date.today()
        year, month = today.year, today.month

        current = await self._repo.list_transactions(year=year, month=month)
        income = sum(
            t.amount for t in current
            if t.transaction_type == TransactionType.INCOME and not t.is_opening_balance
        )
        expenses = sum(
            t.amount for t in current
            if t.transaction_type == TransactionType.EXPENSE and not t.is_opening_balance
        )
        balance = income - expenses

        tag_totals: dict[str, Decimal] = {}
        for t in current:
            if t.transaction_type == TransactionType.EXPENSE and not t.is_opening_balance:
                for tag in (t.tags or ["unkategorisiert"]):
                    tag_totals[tag] = tag_totals.get(tag, Decimal("0")) + t.amount
        tag_lines = ", ".join(
            f"{tag} {amt:.2f}€"
            for tag, amt in sorted(tag_totals.items(), key=lambda x: x[1], reverse=True)[:8]
        )

        trend_lines: list[str] = []
        for delta in range(5, -1, -1):
            m = month - delta
            y = year
            while m <= 0:
                m += 12
                y -= 1
            txs = await self._repo.list_transactions(year=y, month=m)
            inc = sum(t.amount for t in txs if t.transaction_type == TransactionType.INCOME and not t.is_opening_balance)
            exp = sum(t.amount for t in txs if t.transaction_type == TransactionType.EXPENSE and not t.is_opening_balance)
            saldo = inc - exp
            label = f"{month_abbr[m]} {y}"
            sign = "+" if saldo >= 0 else ""
            trend_lines.append(f"  {label}: {sign}{saldo:.2f}€")

        recurring = await self._repo.list_recurring(active_only=True)
        rec_lines = ", ".join(
            f"{r.title} {r.amount:.2f}€/{r.interval.value}" for r in recurring[:10]
        ) or "keine"

        top5 = sorted(
            [t for t in current if t.transaction_type == TransactionType.EXPENSE and not t.is_opening_balance],
            key=lambda t: t.amount,
            reverse=True,
        )[:5]
        top5_lines = "\n".join(
            f"  {t.date}  {t.title}  {t.amount:.2f}€  [{', '.join(t.tags)}]" for t in top5
        ) or "  keine"

        return (
            f"Aktueller Monat ({month_name[month]} {year}):\n"
            f"- Einnahmen: {income:.2f}€  Ausgaben: {expenses:.2f}€  "
            f"Saldo: {'+' if balance >= 0 else ''}{balance:.2f}€\n"
            f"- Ausgaben nach Tag: {tag_lines or 'keine'}\n\n"
            f"Letzte 6 Monate (Monatssaldo):\n{chr(10).join(trend_lines)}\n\n"
            f"Wiederkehrende Einträge (aktiv):\n  {rec_lines}\n\n"
            f"Top-5 Ausgaben diesen Monat:\n{top5_lines}"
        )

    async def get_insights(self) -> list[InsightCard]:
        context = await self._build_context()
        prompt = _INSIGHTS_PROMPT.format(context=context)
        raw = await self._ollama.generate(prompt, _INSIGHTS_SYSTEM)
        try:
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            cards_data = json.loads(clean)
            valid_types = {"warning", "tip", "forecast"}
            return [
                InsightCard(
                    title=str(c.get("title", ""))[:60],
                    body=str(c.get("body", ""))[:120],
                    type=c.get("type", "tip") if c.get("type") in valid_types else "tip",
                )
                for c in cards_data[:3]
            ]
        except (json.JSONDecodeError, TypeError, KeyError) as exc:
            logger.warning("Failed to parse AI insights JSON: %s", exc)
            return [
                InsightCard(
                    title="Analyse nicht verfügbar",
                    body="Das Modell konnte keine strukturierten Insights generieren.",
                    type="warning",
                )
            ]

    async def stream_chat(self, message: str) -> AsyncIterator[str]:
        context = await self._build_context()
        prompt = _CHAT_PROMPT.format(question=message, context=context)
        async for token in self._ollama.generate_stream(prompt, _CHAT_SYSTEM):
            yield token
