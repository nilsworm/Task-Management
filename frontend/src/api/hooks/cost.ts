import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { apiDelete, apiGet, apiPatch, apiPost } from "@/api/client"
import type { components } from "@/api/types"

export type Transaction = components["schemas"]["TransactionResponse"]
export type TransactionCreate = components["schemas"]["TransactionCreateRequest"]
export type Recurring = components["schemas"]["RecurringResponse"]
export type RecurringCreate = components["schemas"]["RecurringCreateRequest"]
export type CostSummary = components["schemas"]["CostSummaryResponse"]
export type CostAnalytics = components["schemas"]["CostAnalyticsResponse"]

const TRANSACTIONS_KEY = ["cost", "transactions"] as const
const RECURRING_KEY = ["cost", "recurring"] as const
const TAGS_KEY = ["cost", "tags"] as const
const SUMMARY_KEY = ["cost", "summary"] as const
const ANALYTICS_KEY = ["cost", "analytics"] as const

export interface TransactionFilters {
  year?: number
  month?: number
  tags?: string[]
  transaction_type?: "income" | "expense"
}

function buildQuery(filters: TransactionFilters): string {
  const params = new URLSearchParams()
  if (filters.year) params.set("year", String(filters.year))
  if (filters.month) params.set("month", String(filters.month))
  if (filters.transaction_type) params.set("transaction_type", filters.transaction_type)
  if (filters.tags?.length) filters.tags.forEach((t) => params.append("tags", t))
  const q = params.toString()
  return q ? `?${q}` : ""
}

export function useTransactions(filters: TransactionFilters = {}) {
  return useQuery({
    queryKey: [...TRANSACTIONS_KEY, filters],
    queryFn: () => apiGet<Transaction[]>(`/cost/transactions${buildQuery(filters)}`),
  })
}

export function useCreateTransaction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: TransactionCreate) => apiPost<Transaction>("/cost/transactions", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cost"] }),
  })
}

export function useDeleteTransaction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiDelete(`/cost/transactions/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cost"] }),
  })
}

export function useRecurring(activeOnly = false) {
  return useQuery({
    queryKey: [...RECURRING_KEY, { activeOnly }],
    queryFn: () =>
      apiGet<Recurring[]>(`/cost/recurring${activeOnly ? "?active_only=true" : ""}`),
  })
}

export function useCreateRecurring() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: RecurringCreate) => apiPost<Recurring>("/cost/recurring", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: RECURRING_KEY }),
  })
}

export function useDeleteRecurring() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiDelete(`/cost/recurring/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: RECURRING_KEY }),
  })
}

export function useToggleRecurring() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      apiPatch<Recurring>(`/cost/recurring/${id}`, { is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: RECURRING_KEY }),
  })
}

export function useCostTags() {
  return useQuery({
    queryKey: TAGS_KEY,
    queryFn: () => apiGet<string[]>("/cost/tags"),
  })
}

export function useGenerateMonthly() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ year, month }: { year: number; month: number }) =>
      apiPost<Transaction[]>(`/cost/generate-monthly?year=${year}&month=${month}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cost"] }),
  })
}

export function useCostSummary(year: number, month: number) {
  return useQuery({
    queryKey: [...SUMMARY_KEY, { year, month }],
    queryFn: () => apiGet<CostSummary>(`/cost/summary?year=${year}&month=${month}`),
  })
}

export function useCostAnalytics(year: number, month: number, tags?: string[]) {
  const params = new URLSearchParams({ year: String(year), month: String(month) })
  if (tags?.length) tags.forEach((t) => params.append("tags", t))
  return useQuery({
    queryKey: [...ANALYTICS_KEY, { year, month, tags }],
    queryFn: () => apiGet<CostAnalytics>(`/cost/analytics?${params.toString()}`),
  })
}

