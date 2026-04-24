import { useQuery } from "@tanstack/react-query"
import { apiGet } from "@/api/client"
import type { components } from "@/api/types"

export type DashboardData = components["schemas"]["DashboardResponse"]
export type MetricsData = components["schemas"]["MetricsResponse"]
export type BurndownData = components["schemas"]["BurndownResponse"]
export type VelocityData = components["schemas"]["VelocityResponse"]
export type GoalProgressData = components["schemas"]["GoalProgressResponse"]
export type GoalProgressItem = components["schemas"]["GoalProgressItem"]
export type SprintVelocity = components["schemas"]["SprintVelocity"]
export type BurndownPoint = components["schemas"]["BurndownPoint"]

const REFETCH = 30_000

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: () => apiGet<DashboardData>("/dashboard"),
    refetchInterval: REFETCH,
  })
}

export function useMetrics() {
  return useQuery({
    queryKey: ["dashboard", "metrics"],
    queryFn: () => apiGet<MetricsData>("/dashboard/metrics"),
    refetchInterval: REFETCH,
  })
}

export function useBurndown(sprintId?: string) {
  return useQuery({
    queryKey: ["dashboard", "burndown", sprintId ?? "active"],
    queryFn: () => {
      const qs = sprintId ? `?sprint_id=${sprintId}` : ""
      return apiGet<BurndownData>(`/dashboard/burndown${qs}`)
    },
    refetchInterval: REFETCH,
  })
}

export function useVelocity(lastN = 5) {
  return useQuery({
    queryKey: ["dashboard", "velocity", lastN],
    queryFn: () => apiGet<VelocityData>(`/dashboard/velocity?last_n=${lastN}`),
    refetchInterval: REFETCH,
  })
}

export function useGoalProgress() {
  return useQuery({
    queryKey: ["dashboard", "goal-progress"],
    queryFn: () => apiGet<GoalProgressData>("/dashboard/goal-progress"),
    refetchInterval: REFETCH,
  })
}
