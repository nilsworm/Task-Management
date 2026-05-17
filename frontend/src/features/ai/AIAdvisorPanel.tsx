import { useAIPanelStore } from "@/stores/aiPanelStore"
import { useAIInsights } from "@/api/hooks/ai"
import { InsightCards } from "@/features/ai/InsightCards"
import { X } from "lucide-react"

export function AIAdvisorPanel() {
  const { isOpen, toggle } = useAIPanelStore()
  const { data: insights, isLoading } = useAIInsights(isOpen)

  if (!isOpen) return null

  return (
    <div
      id="ai-advisor-panel"
      className="fixed right-0 top-0 z-50 flex h-screen w-[420px] flex-col border-l border-border bg-[#0d0d0f] shadow-2xl"
      data-testid="ai-advisor-panel"
    >
      <div className="flex h-12 shrink-0 items-center justify-between border-b border-border/50 px-4">
        <span className="text-sm font-semibold text-white">AI Advisor</span>
        <button
          onClick={toggle}
          aria-label="Close AI Advisor"
          className="rounded p-1 text-zinc-400 hover:bg-white/10 hover:text-white"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="flex flex-1 flex-col gap-4 overflow-hidden p-4">
        <div className="shrink-0">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
            Aktuelle Insights
          </p>
          <InsightCards cards={insights ?? []} isLoading={isLoading} />
        </div>
        <div className="mx-0 h-px bg-border/30" />
        {/* AIChat will be added in Task 8 */}
      </div>
    </div>
  )
}
