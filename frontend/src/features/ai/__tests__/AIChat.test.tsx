import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { AIChat } from "@/features/ai/AIChat"

function makeStream(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder()
  return new ReadableStream({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk))
      }
      controller.close()
    },
  })
}

describe("AIChat", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  it("renders input and send button", () => {
    render(<AIChat />)
    expect(screen.getByPlaceholderText(/frage stellen/i)).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /senden/i })).toBeInTheDocument()
  })

  it("disables send button when input is empty", () => {
    render(<AIChat />)
    expect(screen.getByRole("button", { name: /senden/i })).toBeDisabled()
  })

  it("enables send button when input has text", () => {
    render(<AIChat />)
    fireEvent.change(screen.getByPlaceholderText(/frage stellen/i), {
      target: { value: "Wie ist mein Saldo?" },
    })
    expect(screen.getByRole("button", { name: /senden/i })).not.toBeDisabled()
  })

  it("streams response tokens into the bubble", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      body: makeStream([
        "data: Dein \n\n",
        "data: Saldo \n\n",
        "data: ist positiv.\n\n",
        "data: [DONE]\n\n",
      ]),
    } as unknown as Response)

    render(<AIChat />)
    fireEvent.change(screen.getByPlaceholderText(/frage stellen/i), {
      target: { value: "Wie ist mein Saldo?" },
    })
    fireEvent.click(screen.getByRole("button", { name: /senden/i }))

    await waitFor(() =>
      expect(screen.getByTestId("ai-response")).toHaveTextContent("Dein Saldo ist positiv.")
    )
  })

  it("shows error message on fetch failure", async () => {
    vi.mocked(fetch).mockRejectedValue(new Error("Network error"))

    render(<AIChat />)
    fireEvent.change(screen.getByPlaceholderText(/frage stellen/i), {
      target: { value: "Test" },
    })
    fireEvent.click(screen.getByRole("button", { name: /senden/i }))

    await waitFor(() =>
      expect(screen.getByTestId("ai-error")).toBeInTheDocument()
    )
  })
})
