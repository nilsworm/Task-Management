import { Sparkles } from "lucide-react"
import { useAIPanelStore } from "@/stores/aiPanelStore"

export function AIFloatingButton() {
  const { toggle, isOpen } = useAIPanelStore()

  return (
    <button
      onClick={toggle}
      aria-label="AI Advisor"
      aria-expanded={isOpen}
      aria-controls="ai-advisor-panel"
      className="fixed bottom-6 right-6 z-50 flex h-12 w-12 items-center justify-center rounded-full shadow-lg transition-transform hover:scale-105 active:scale-95"
      style={{
        background: "linear-gradient(135deg, #00d4ff, #7c3aed)",
        boxShadow: "0 0 20px rgba(0, 212, 255, 0.4)",
      }}
    >
      <Sparkles className="h-5 w-5 text-white" />
    </button>
  )
}
