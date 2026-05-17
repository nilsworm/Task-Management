import { useState, useRef, useEffect } from "react"
import { Send } from "lucide-react"

const BASE_URL = import.meta.env.VITE_API_URL ?? ""

export function AIChat() {
  const [message, setMessage] = useState("")
  const [response, setResponse] = useState("")
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const responseRef = useRef<HTMLDivElement>(null)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => () => { abortRef.current?.abort() }, [])

  useEffect(() => {
    if (responseRef.current) {
      responseRef.current.scrollTop = responseRef.current.scrollHeight
    }
  }, [response])

  const handleSend = async () => {
    if (!message.trim() || isStreaming) return
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    const trimmed = message.trim()
    setIsStreaming(true)
    setResponse("")
    setError(null)
    setMessage("")

    try {
      const res = await fetch(`${BASE_URL}/ai/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmed }),
        signal: controller.signal,
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      if (!res.body) throw new Error("No response body")

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() ?? ""
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue
          const token = line.slice(6)
          if (token.trim() === "[DONE]") return
          if (token.trim()) setResponse((prev) => prev + token)
        }
      }
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") return
      setError("Antwort konnte nicht geladen werden.")
    } finally {
      setIsStreaming(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-1 flex-col gap-3 overflow-hidden">
      {response && (
        <div
          ref={responseRef}
          data-testid="ai-response"
          className="flex-1 overflow-y-auto rounded-lg p-3.5 text-[12px] leading-[1.75] scrollbar-thin"
          style={{
            background: "rgba(0,212,255,0.03)",
            border: "1px solid rgba(0,212,255,0.08)",
            color: "rgba(200,215,240,0.85)",
            boxShadow: "inset 0 1px 0 rgba(0,212,255,0.04)",
          }}
        >
          {response}
          {isStreaming && (
            <span
              className="ml-0.5 inline-block h-[13px] w-[2px] translate-y-[2px] rounded-full"
              style={{
                background: "#00d4ff",
                boxShadow: "0 0 6px rgba(0,212,255,0.8)",
                animation: "ai-cursor 1s step-end infinite",
              }}
            />
          )}
        </div>
      )}

      {error && (
        <p
          data-testid="ai-error"
          className="text-[11px]"
          style={{ color: "rgba(255,77,109,0.8)" }}
        >
          {error}
        </p>
      )}

      <div
        className="flex shrink-0 gap-2 rounded-lg p-1"
        style={{
          background: "rgba(0,212,255,0.03)",
          border: "1px solid rgba(0,212,255,0.1)",
        }}
      >
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Frage stellen..."
          disabled={isStreaming}
          className="flex-1 bg-transparent px-2 py-1.5 text-[12px] focus:outline-none disabled:opacity-40"
          style={{
            color: "rgba(220,230,245,0.9)",
          }}
        />
        <button
          onClick={handleSend}
          disabled={!message.trim() || isStreaming}
          aria-label="Senden"
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md transition-all disabled:cursor-not-allowed disabled:opacity-30"
          style={{
            background: "linear-gradient(135deg, rgba(0,212,255,0.2), rgba(124,58,237,0.2))",
            color: "#00d4ff",
          }}
        >
          <Send className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  )
}
