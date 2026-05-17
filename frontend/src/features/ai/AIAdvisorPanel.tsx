import { useAIPanelStore } from "@/stores/aiPanelStore"
import { useAIInsights } from "@/api/hooks/ai"
import { InsightCards } from "@/features/ai/InsightCards"
import { AIChat } from "@/features/ai/AIChat"
import { X } from "lucide-react"

export function AIAdvisorPanel() {
  const { isOpen, toggle } = useAIPanelStore()
  const { data: insights, isLoading } = useAIInsights(isOpen)

  if (!isOpen) return null

  return (
    <div
      id="ai-advisor-panel"
      data-testid="ai-advisor-panel"
      className="fixed right-0 top-0 z-50 flex h-screen w-[420px] flex-col overflow-hidden"
      style={{
        background: "linear-gradient(180deg, #0a0812 0%, #080810 50%, #06060e 100%)",
        borderLeft: "1px solid rgba(0, 212, 255, 0.12)",
        boxShadow: "-24px 0 80px rgba(0,0,0,0.9), inset 1px 0 0 rgba(0,212,255,0.06)",
        animation: "ai-panel-in 0.35s cubic-bezier(0.16, 1, 0.3, 1)",
      }}
    >
      {/* Noise texture overlay */}
      <div
        className="pointer-events-none absolute inset-0 z-0 opacity-[0.025]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
          backgroundSize: "256px 256px",
        }}
      />
      {/* Top radial glow */}
      <div
        className="pointer-events-none absolute inset-x-0 top-0 z-0 h-48"
        style={{
          background: "radial-gradient(ellipse at 50% 0%, rgba(0,212,255,0.07) 0%, transparent 70%)",
        }}
      />

      {/* Header */}
      <div
        className="relative z-10 flex h-[52px] shrink-0 items-center justify-between px-5"
        style={{ borderBottom: "1px solid rgba(0,212,255,0.08)" }}
      >
        <div className="flex items-center gap-3">
          {/* Breathing status dot */}
          <div
            className="h-1.5 w-1.5 rounded-full"
            style={{
              background: "#00d4ff",
              boxShadow: "0 0 8px rgba(0,212,255,0.9)",
              animation: "ai-glow-breathe 2s ease-in-out infinite",
            }}
          />
          <span
            className="text-[13px] font-semibold tracking-wide"
            style={{
              background: "linear-gradient(90deg, #c8d8f0, #00d4ff)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            AI Advisor
          </span>
        </div>
        <button
          onClick={toggle}
          aria-label="Close AI Advisor"
          className="flex h-7 w-7 items-center justify-center rounded-md text-zinc-600 transition-all hover:bg-white/5 hover:text-zinc-300"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Content */}
      <div className="relative z-10 flex flex-1 flex-col gap-4 overflow-hidden p-4">
        <div className="shrink-0">
          <p
            className="mb-3 text-[9px] font-bold uppercase tracking-[0.18em]"
            style={{ color: "rgba(0,212,255,0.45)" }}
          >
            Aktuelle Insights
          </p>
          <InsightCards cards={insights ?? []} isLoading={isLoading} />
        </div>
        {/* Gradient divider */}
        <div
          className="shrink-0"
          style={{
            height: "1px",
            background: "linear-gradient(90deg, transparent, rgba(0,212,255,0.15), transparent)",
          }}
        />
        <AIChat />
      </div>
    </div>
  )
}
