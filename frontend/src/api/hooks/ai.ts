import { useQuery } from "@tanstack/react-query"
import { apiPost } from "@/api/client"

// TODO: replace with generated type once AI endpoints are in openapi.json
export interface InsightCard {
  title: string
  body: string
  type: "warning" | "tip" | "forecast"
}

const AI_INSIGHTS_KEY = ["ai", "insights"] as const

export function useAIInsights(enabled: boolean) {
  return useQuery({
    queryKey: AI_INSIGHTS_KEY,
    queryFn: () => apiPost<InsightCard[]>("/ai/insights"),
    enabled,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  })
}
