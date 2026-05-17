import { create } from "zustand"

export interface ChatMessage {
  role: "user" | "assistant"
  content: string
  streaming?: boolean
}

interface AIChatState {
  messages: ChatMessage[]
  isStreaming: boolean
  error: string | null
  addUserMessage: (content: string) => void
  startAssistantMessage: () => void
  appendToken: (token: string) => void
  finalizeMessage: () => void
  setError: (error: string | null) => void
  clearError: () => void
}

export const useAIChatStore = create<AIChatState>((set) => ({
  messages: [],
  isStreaming: false,
  error: null,

  addUserMessage: (content) =>
    set((s) => ({ messages: [...s.messages, { role: "user", content }], error: null })),

  startAssistantMessage: () =>
    set((s) => ({
      messages: [...s.messages, { role: "assistant", content: "", streaming: true }],
      isStreaming: true,
    })),

  appendToken: (token) =>
    set((s) => {
      const messages = [...s.messages]
      const last = messages[messages.length - 1]
      if (last?.streaming) {
        messages[messages.length - 1] = { ...last, content: last.content + token }
      }
      return { messages }
    }),

  finalizeMessage: () =>
    set((s) => {
      const messages = s.messages.map((m) =>
        m.streaming ? { ...m, streaming: false } : m
      )
      return { messages, isStreaming: false }
    }),

  setError: (error) => set({ error, isStreaming: false }),
  clearError: () => set({ error: null }),
}))
