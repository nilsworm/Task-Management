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
            className="h-[60px] rounded-lg"
            style={{
              background: "linear-gradient(90deg, rgba(255,255,255,0.03), rgba(255,255,255,0.06), rgba(255,255,255,0.03))",
              backgroundSize: "200% 100%",
              animation: "ai-glow-breathe 1.5s ease-in-out infinite",
              animationDelay: `${i * 0.15}s`,
            }}
          />
        ))}
      </div>
    )
  }

  if (cards.length === 0) {
    return (
      <p className="text-[11px]" style={{ color: "rgba(255,255,255,0.2)" }}>
        Keine Insights verfügbar.
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {cards.map((card, i) => {
        const typeKey = (card.type in TYPE_CONFIG ? card.type : "tip") as keyof typeof TYPE_CONFIG
        const cfg = TYPE_CONFIG[typeKey]
        return (
          <div
            key={i}
            data-testid={`insight-card-${typeKey}`}
            className="rounded-lg p-3"
            style={{
              borderLeft: `2px solid ${cfg.color}`,
              background: `linear-gradient(135deg, ${cfg.color}0a 0%, rgba(8,8,16,0.6) 100%)`,
              boxShadow: `inset 0 0 20px ${cfg.color}05`,
              animation: "ai-card-appear 0.4s ease-out forwards",
              animationDelay: `${i * 0.08}s`,
              opacity: 0,
            }}
          >
            <div className="mb-1 flex items-center gap-2">
              <span
                className="rounded-sm px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-[0.12em]"
                style={{
                  background: `${cfg.color}18`,
                  color: cfg.color,
                  border: `1px solid ${cfg.color}30`,
                }}
              >
                {cfg.label}
              </span>
              <span className="text-[12px] font-medium" style={{ color: "rgba(220,230,245,0.9)" }}>
                {card.title}
              </span>
            </div>
            <p className="text-[11px] leading-relaxed" style={{ color: "rgba(160,170,200,0.7)" }}>
              {card.body}
            </p>
          </div>
        )
      })}
    </div>
  )
}
