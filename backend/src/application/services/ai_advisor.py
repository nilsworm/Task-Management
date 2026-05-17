from __future__ import annotations

import json
import logging
from calendar import month_abbr, month_name
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import AsyncGenerator, AsyncIterator

from src.domain.ai.client import IAIClient
from src.domain.cost.repository import ICostRepository
from src.domain.cost.value_objects import TransactionType

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
    "Achte besonders auf folgende Muster und priorisiere sie als 'warning':\n"
    "- Zigaretten / Tabak (Tags wie zigaretten, rauchen, tabak)\n"
    "- Unnötige Kleinstausgaben unter 10€ (häufige kleine Beträge)\n"
    "- Impulskäufe und Konsumausgaben (Tags wie shopping, amazon, kleidung, konsum)\n\n"
    "{context}"
)

_CHAT_PROMPT = "{question}\n\nFinanzdaten:\n{context}"

_FOCUS_TAGS = frozenset({
    "zigaretten", "rauchen", "tabak", "tobacco", "iqos", "vape", "nikotin",
    "shopping", "amazon", "konsum", "kleidung", "impulskauf",
})


@dataclass
class InsightCard:
    title: str
    body: str
    type: str  # "warning" | "tip" | "forecast"


class AIAdvisorService:
    def __init__(self, cost_repo: ICostRepository, ollama: IAIClient) -> None:
        self._repo = cost_repo
        self._ollama = ollama

    async def _build_context(self) -> str:
        today = date.today()
        year, month = today.year, today.month

        def signed(v: Decimal) -> str:
            return f"+{v:.2f}€" if v >= 0 else f"{v:.2f}€"

        # --- Letzte 3 Monate: volle Einzeltransaktionen ---
        detailed_sections: list[str] = []
        all_expenses_3m: list = []

        for delta in range(2, -1, -1):
            m = month - delta
            y = year
            while m <= 0:
                m += 12
                y -= 1
            txs = await self._repo.list_transactions(year=y, month=m)

            opening = sum(
                t.amount if t.transaction_type == TransactionType.INCOME else -t.amount
                for t in txs if t.is_opening_balance
            )
            inc = sum(t.amount for t in txs if t.transaction_type == TransactionType.INCOME and not t.is_opening_balance)
            exp = sum(t.amount for t in txs if t.transaction_type == TransactionType.EXPENSE and not t.is_opening_balance)
            net = inc - exp

            exp_list = [t for t in txs if t.transaction_type == TransactionType.EXPENSE and not t.is_opening_balance]
            all_expenses_3m.extend(exp_list)

            tag_totals: dict[str, Decimal] = {}
            for t in exp_list:
                for tag in (t.tags or ["unkategorisiert"]):
                    tag_totals[tag] = tag_totals.get(tag, Decimal("0")) + t.amount
            tag_lines = ", ".join(
                f"{tag} {amt:.2f}€"
                for tag, amt in sorted(tag_totals.items(), key=lambda x: x[1], reverse=True)
            ) or "keine"

            tx_lines = "\n".join(
                f"  {t.date}  {t.title}  {t.amount:.2f}€  [{', '.join(t.tags) or 'unkategorisiert'}]"
                for t in sorted(exp_list, key=lambda t: t.date)
            ) or "  keine"

            label = f"{month_name[m]} {y}" + (" (aktuell)" if delta == 0 else "")
            detailed_sections.append(
                f"{label}:\n"
                f"- Anfangsbestand: {signed(opening)}  Einnahmen: {inc:.2f}€  "
                f"Ausgaben: {exp:.2f}€  Monatssaldo: {signed(net)}  Kontostand: {signed(opening + net)}\n"
                f"- Ausgaben nach Tag: {tag_lines}\n"
                f"- Einzelbuchungen:\n{tx_lines}"
            )

        # --- Ältere Monate (4-6): nur Monatssaldo ---
        trend_lines: list[str] = []
        for delta in range(5, 2, -1):
            m = month - delta
            y = year
            while m <= 0:
                m += 12
                y -= 1
            txs = await self._repo.list_transactions(year=y, month=m)
            inc = sum(t.amount for t in txs if t.transaction_type == TransactionType.INCOME and not t.is_opening_balance)
            exp = sum(t.amount for t in txs if t.transaction_type == TransactionType.EXPENSE and not t.is_opening_balance)
            trend_lines.append(f"  {month_abbr[m]} {y}: {signed(inc - exp)}")

        # --- Wiederkehrend ---
        recurring = await self._repo.list_recurring(active_only=True)
        rec_lines = ", ".join(
            f"{r.title} {r.amount:.2f}€/{r.interval.value}" for r in recurring[:10]
        ) or "keine"

        # --- Focus-Scan über alle 3 Monate ---
        focus_txs = [
            t for t in all_expenses_3m
            if any(tag.lower() in _FOCUS_TAGS for tag in (t.tags or []))
        ]
        small_txs = [t for t in all_expenses_3m if t.amount < Decimal("10")]
        focus_lines: list[str] = []
        if focus_txs:
            focus_lines.append("  Tabak/Konsum/Shopping (letzte 3 Monate):")
            focus_lines += [
                f"    {t.date}  {t.title}  {t.amount:.2f}€  [{', '.join(t.tags)}]"
                for t in sorted(focus_txs, key=lambda t: t.date)
            ]
        if small_txs:
            total_small = sum(t.amount for t in small_txs)
            focus_lines.append(
                f"  Kleinstausgaben <10€ (letzte 3 Monate): {len(small_txs)} Buchungen, gesamt {total_small:.2f}€"
            )
        focus_section = "\n".join(focus_lines) if focus_lines else "  keine"

        return (
            "\n\n".join(detailed_sections) + "\n\n"
            f"Ältere Monatssaldi (Zusammenfassung):\n" + "\n".join(trend_lines) + "\n\n"
            f"Wiederkehrende Einträge (aktiv):\n  {rec_lines}\n\n"
            f"Focus-Ausgaben (Tabak/Konsum/Kleinstbeträge):\n{focus_section}"
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
            cards: list[InsightCard] = []
            for c in cards_data[:3]:
                if isinstance(c, str):
                    try:
                        c = json.loads(c)
                    except (json.JSONDecodeError, ValueError):
                        continue
                if not isinstance(c, dict):
                    continue
                cards.append(InsightCard(
                    title=str(c.get("title", ""))[:60],
                    body=str(c.get("body", ""))[:120],
                    type=c.get("type", "tip") if c.get("type") in valid_types else "tip",
                ))
            return cards
        except (json.JSONDecodeError, TypeError, KeyError, AttributeError, ValueError) as exc:
            logger.warning("Failed to parse AI insights JSON: %s", exc)
            return [
                InsightCard(
                    title="Analyse nicht verfügbar",
                    body="Das Modell konnte keine strukturierten Insights generieren.",
                    type="warning",
                )
            ]

    async def stream_chat(self, message: str) -> AsyncGenerator[str, None]:
        context = await self._build_context()
        prompt = _CHAT_PROMPT.format(question=message, context=context)
        async for token in self._ollama.generate_stream(prompt, _CHAT_SYSTEM):
            yield token
