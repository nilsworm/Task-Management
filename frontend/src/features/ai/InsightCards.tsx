import type { InsightCard } from "@/api/hooks/ai"

const TYPE_CONFIG = {
  warning:  { color: "#f97316", label: "Warnung"  },
  tip:      { color: "#22c55e", label: "Tipp"     },
  forecast: { color: "#00d4ff", label: "Prognose" },
} as const

interface InsightCardsProps {
  cards: InsightCard[]
  isLoading: boolean
}

export function InsightCards({ cards, isLoading }: InsightCardsProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col gap-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div
            key={i}
            data-testid="insight-skeleton"
            className="h-16 animate-pulse rounded-lg bg-white/5"
          />
        ))}
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {cards.map((card, i) => {
        const cfg = TYPE_CONFIG[card.type as keyof typeof TYPE_CONFIG] ?? TYPE_CONFIG.tip
        return (
          <div
            key={i}
            data-testid={`insight-card-${card.type}`}
            className="rounded-lg border p-3"
            style={{
              borderColor: `${cfg.color}33`,
              background: `${cfg.color}0d`,
            }}
          >
            <div className="mb-0.5 flex items-center gap-2">
              <span
                className="rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
                style={{ background: `${cfg.color}22`, color: cfg.color }}
              >
                {cfg.label}
              </span>
              <span className="text-xs font-medium text-white">{card.title}</span>
            </div>
            <p className="text-[11px] leading-relaxed text-zinc-400">{card.body}</p>
          </div>
        )
      })}
    </div>
  )
}
