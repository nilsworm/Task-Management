import { Sparkles } from "lucide-react"
import { useAIPanelStore } from "@/stores/aiPanelStore"

export function AIFloatingButton() {
  const { toggle, isOpen } = useAIPanelStore()

  return (
    <div className="fixed bottom-6 right-6 z-50" style={{ width: 48, height: 48 }}>
      {/* Slowly rotating gradient ring */}
      <div
        className="pointer-events-none absolute -inset-1.5 rounded-full"
        style={{
          background: "conic-gradient(from 0deg, #00d4ff80, #7c3aed60, #00d4ff80, #7c3aed60, #00d4ff80)",
          animation: "ai-ring-spin 8s linear infinite",
        }}
      />
      {/* Dark inset to create ring effect */}
      <div className="pointer-events-none absolute -inset-0.5 rounded-full bg-[#0a0a14]" />
      {/* Button */}
      <button
        onClick={toggle}
        aria-label="AI Advisor"
        aria-expanded={isOpen}
        aria-controls="ai-advisor-panel"
        className="absolute inset-0 flex items-center justify-center rounded-full transition-transform hover:scale-105 active:scale-95"
        style={{
          background: "linear-gradient(135deg, #00d4ff, #7c3aed)",
          boxShadow: "0 0 24px rgba(0, 212, 255, 0.45), 0 0 48px rgba(124, 58, 237, 0.2)",
          animation: "ai-glow-breathe 3s ease-in-out infinite",
        }}
      >
        <Sparkles
          className="h-5 w-5 text-white"
          style={{ filter: "drop-shadow(0 0 6px rgba(255,255,255,0.6))" }}
        />
      </button>
    </div>
  )
}
