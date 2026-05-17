import { useRef, useEffect } from "react"
import { Send } from "lucide-react"
import { useAIChatStore } from "@/stores/aiChatStore"
import { useState } from "react"

const BASE_URL = import.meta.env.VITE_API_URL ?? ""

export function AIChat() {
  const [input, setInput] = useState("")
  const { messages, isStreaming, error, addUserMessage, startAssistantMessage, appendToken, finalizeMessage, setError } = useAIChatStore()
  const bottomRef = useRef<HTMLDivElement>(null)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => () => { abortRef.current?.abort() }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    const trimmed = input.trim()

    const history = messages
      .filter((m) => !m.streaming)
      .map((m) => ({ role: m.role, content: m.content }))

    setInput("")
    addUserMessage(trimmed)
    startAssistantMessage()

    try {
      const res = await fetch(`${BASE_URL}/ai/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmed, history }),
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
          if (token.trim() === "[DONE]") {
            finalizeMessage()
            return
          }
          if (token.trim()) appendToken(token)
        }
      }
      finalizeMessage()
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") return
      setError("Antwort konnte nicht geladen werden.")
      finalizeMessage()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-1 flex-col gap-2 overflow-hidden">
      {/* Message list */}
      <div
        data-testid="ai-chat-messages"
        className="flex flex-1 flex-col gap-2 overflow-y-auto pr-1 scrollbar-thin"
      >
        {messages.length === 0 && (
          <p className="text-[11px] text-center mt-4" style={{ color: "rgba(255,255,255,0.2)" }}>
            Stelle eine Frage zu deinen Finanzen.
          </p>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            data-testid={msg.role === "user" ? "ai-chat-user-message" : "ai-chat-assistant-message"}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className="max-w-[85%] rounded-lg px-3 py-2 text-[12px] leading-[1.75]"
              style={
                msg.role === "user"
                  ? {
                      background: "rgba(0,212,255,0.12)",
                      border: "1px solid rgba(0,212,255,0.2)",
                      color: "rgba(220,230,245,0.9)",
                    }
                  : {
                      background: "rgba(255,255,255,0.04)",
                      border: "1px solid rgba(255,255,255,0.07)",
                      color: "rgba(200,215,240,0.85)",
                    }
              }
            >
              {msg.content}
              {msg.streaming && (
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
          </div>
        ))}
        {error && (
          <p
            data-testid="ai-error"
            className="text-[11px] text-center"
            style={{ color: "rgba(255,77,109,0.8)" }}
          >
            {error}
          </p>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div
        className="flex shrink-0 gap-2 rounded-lg p-1"
        style={{
          background: "rgba(0,212,255,0.03)",
          border: "1px solid rgba(0,212,255,0.1)",
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Frage stellen..."
          disabled={isStreaming}
          data-testid="ai-chat-input"
          className="flex-1 bg-transparent px-2 py-1.5 text-[12px] focus:outline-none disabled:opacity-40"
          style={{ color: "rgba(220,230,245,0.9)" }}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || isStreaming}
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
