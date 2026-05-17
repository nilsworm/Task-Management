import { useAIPanelStore } from "@/stores/aiPanelStore"
import { X } from "lucide-react"

export function AIAdvisorPanel() {
  const { isOpen, toggle } = useAIPanelStore()

  if (!isOpen) return null

  return (
    <div
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
      <div className="flex flex-1 flex-col overflow-hidden p-4">
        {/* InsightCards and AIChat will be added in Tasks 7 and 8 */}
      </div>
    </div>
  )
}
