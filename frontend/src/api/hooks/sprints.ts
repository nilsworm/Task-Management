import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { apiDelete, apiGet, apiPost } from "@/api/client"
import type { components } from "@/api/types"

export type Sprint = components["schemas"]["SprintResponse"]
export type SprintCreate = components["schemas"]["SprintCreateRequest"]

const SPRINTS_KEY = ["sprints"] as const

export function useSprints() {
  return useQuery({
    queryKey: SPRINTS_KEY,
    queryFn: () => apiGet<Sprint[]>("/sprints"),
  })
}

export function useActiveSprint() {
  return useQuery({
    queryKey: [...SPRINTS_KEY, "active"],
    queryFn: () => apiGet<Sprint | null>("/sprints/active"),
  })
}

export function useSprint(id: string) {
  return useQuery({
    queryKey: [...SPRINTS_KEY, id],
    queryFn: () => apiGet<Sprint>(`/sprints/${id}`),
    enabled: !!id,
  })
}

export function useSprintTasks(sprintId: string) {
  return useQuery({
    queryKey: [...SPRINTS_KEY, sprintId, "tasks"],
    queryFn: () => apiGet<components["schemas"]["TaskResponse"][]>(`/sprints/${sprintId}/tasks`),
    enabled: !!sprintId,
  })
}

export function useCreateSprint() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: SprintCreate) => apiPost<Sprint>("/sprints", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: SPRINTS_KEY }),
  })
}

export function useStartSprint() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiPost<Sprint>(`/sprints/${id}/start`),
    onSuccess: () => qc.invalidateQueries({ queryKey: SPRINTS_KEY }),
  })
}

export function useCompleteSprint() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiPost<Sprint>(`/sprints/${id}/complete`),
    onSuccess: () => qc.invalidateQueries({ queryKey: SPRINTS_KEY }),
  })
}

export function useDeleteSprint() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiDelete(`/sprints/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: SPRINTS_KEY }),
  })
}
