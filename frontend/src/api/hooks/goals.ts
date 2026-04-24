import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { apiDelete, apiGet, apiPatch, apiPost } from "@/api/client"
import type { components } from "@/api/types"

export type Goal = components["schemas"]["GoalResponse"]
export type GoalCreate = components["schemas"]["GoalCreateRequest"]
export type GoalUpdate = components["schemas"]["GoalUpdateRequest"]
export type KeyResult = components["schemas"]["KeyResultResponse"]
export type KeyResultCreate = components["schemas"]["KeyResultCreateRequest"]
export type KeyResultUpdate = components["schemas"]["KeyResultUpdateRequest"]

const GOALS_KEY = ["goals"] as const

function krKey(goalId: string) {
  return [...GOALS_KEY, goalId, "key-results"] as const
}

function invalidateDashboard(qc: ReturnType<typeof useQueryClient>) {
  return qc.invalidateQueries({ queryKey: ["dashboard"] })
}

export function useGoals() {
  return useQuery({
    queryKey: GOALS_KEY,
    queryFn: () => apiGet<Goal[]>("/goals"),
  })
}

export function useGoal(id: string) {
  return useQuery({
    queryKey: [...GOALS_KEY, id],
    queryFn: () => apiGet<Goal>(`/goals/${id}`),
    enabled: !!id,
  })
}

export function useGoalKeyResults(goalId: string) {
  return useQuery({
    queryKey: krKey(goalId),
    queryFn: () => apiGet<KeyResult[]>(`/goals/${goalId}/key-results`),
    enabled: !!goalId,
  })
}

export function useCreateGoal() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: GoalCreate) => apiPost<Goal>("/goals", body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: GOALS_KEY })
      invalidateDashboard(qc)
    },
  })
}

export function useUpdateGoal() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...body }: GoalUpdate & { id: string }) =>
      apiPatch<Goal>(`/goals/${id}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: GOALS_KEY }),
  })
}

export function useDeleteGoal() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiDelete(`/goals/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: GOALS_KEY })
      invalidateDashboard(qc)
    },
  })
}

export function useCreateKeyResult(goalId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: KeyResultCreate) =>
      apiPost<KeyResult>(`/goals/${goalId}/key-results`, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: krKey(goalId) })
      invalidateDashboard(qc)
    },
  })
}

export function useUpdateKeyResult(goalId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...body }: KeyResultUpdate & { id: string }) =>
      apiPatch<KeyResult>(`/goals/${goalId}/key-results/${id}`, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: krKey(goalId) })
      invalidateDashboard(qc)
    },
  })
}

export function useDeleteKeyResult(goalId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiDelete(`/goals/${goalId}/key-results/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: krKey(goalId) })
      invalidateDashboard(qc)
    },
  })
}
