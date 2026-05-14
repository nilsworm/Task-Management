import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"
import { QueryClientProvider, QueryClient } from "@tanstack/react-query"
import { ImportStatusCard } from "../ImportStatusCard"
import { useImportStatus } from "@/api/hooks/cost"

vi.mock("@/api/hooks/cost")

const mockUseImportStatus = vi.mocked(useImportStatus)

const renderWithQueryClient = (component: React.ReactNode) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  )
}

describe("ImportStatusCard", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("should display last import date and transaction count", () => {
    mockUseImportStatus.mockReturnValue({
      data: {
        last_import_date: "2026-05-14",
        transaction_count: 5,
      },
      isLoading: false,
      error: null,
      isSuccess: true,
      isError: false,
      status: "success",
    } as any)

    renderWithQueryClient(<ImportStatusCard />)

    expect(screen.getByText(/last import/i)).toBeInTheDocument()
    expect(screen.getByText("May 14, 2026")).toBeInTheDocument()
    expect(screen.getByText("5 transactions")).toBeInTheDocument()
    expect(screen.getByText("/imports")).toBeInTheDocument()
  })

  it("should show loading skeleton", () => {
    mockUseImportStatus.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      isSuccess: false,
      isError: false,
      status: "pending",
    } as any)

    const { container } = renderWithQueryClient(<ImportStatusCard />)

    expect(container.querySelector(".animate-pulse")).toBeInTheDocument()
  })

  it("should show empty state if no imports yet", () => {
    mockUseImportStatus.mockReturnValue({
      data: {
        last_import_date: null,
        transaction_count: 0,
      },
      isLoading: false,
      error: null,
      isSuccess: true,
      isError: false,
      status: "success",
    } as any)

    renderWithQueryClient(<ImportStatusCard />)

    expect(screen.getByText(/no imports yet/i)).toBeInTheDocument()
    expect(screen.getByText(/add csv files/i)).toBeInTheDocument()
  })

  it("should display single transaction label", () => {
    mockUseImportStatus.mockReturnValue({
      data: {
        last_import_date: "2026-05-14",
        transaction_count: 1,
      },
      isLoading: false,
      error: null,
      isSuccess: true,
      isError: false,
      status: "success",
    } as any)

    renderWithQueryClient(<ImportStatusCard />)

    expect(screen.getByText("1 transactions")).toBeInTheDocument()
  })
})
