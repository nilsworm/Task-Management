import { useState, useRef, useEffect } from "react"
import { Send } from "lucide-react"

const BASE_URL = import.meta.env.VITE_API_URL ?? ""

export function AIChat() {
  const [message, setMessage] = useState("")
  const [response, setResponse] = useState("")
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const responseRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (responseRef.current) {
      responseRef.current.scrollTop = responseRef.current.scrollHeight
    }
  }, [response])

  const handleSend = async () => {
    if (!message.trim() || isStreaming) return
    setIsStreaming(true)
    setResponse("")
    setError(null)

    try {
      const res = await fetch(`${BASE_URL}/ai/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message.trim() }),
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      if (!res.body) throw new Error("No response body")

      const reader = res.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const text = decoder.decode(value, { stream: true })
        for (const line of text.split("\n")) {
          if (!line.startsWith("data: ")) continue
          const token = line.slice(6)
          if (token === "[DONE]") {
            setIsStreaming(false)
            return
          }
          setResponse((prev) => prev + token)
        }
      }
    } catch (e) {
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
          className="flex-1 overflow-y-auto rounded-lg border border-border/30 bg-white/5 p-3 text-[12px] leading-relaxed text-zinc-300"
        >
          {response}
          {isStreaming && (
            <span className="ml-0.5 inline-block h-3 w-0.5 animate-pulse bg-cyan" />
          )}
        </div>
      )}

      {error && (
        <p data-testid="ai-error" className="text-[11px] text-red-400">
          {error}
        </p>
      )}

      <div className="flex shrink-0 gap-2">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Frage stellen..."
          disabled={isStreaming}
          className="flex-1 rounded-lg border border-border/50 bg-white/5 px-3 py-2 text-[12px] text-white placeholder:text-zinc-500 focus:border-cyan/50 focus:outline-none disabled:opacity-50"
        />
        <button
          onClick={handleSend}
          disabled={!message.trim() || isStreaming}
          aria-label="Senden"
          className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan/20 text-cyan transition-colors hover:bg-cyan/30 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Send className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  )
}
