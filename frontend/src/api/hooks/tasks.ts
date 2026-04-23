import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { apiDelete, apiGet, apiPatch, apiPost } from "@/api/client"
import type { components } from "@/api/types"

export type Task = components["schemas"]["TaskResponse"]
export type TaskCreate = components["schemas"]["TaskCreateRequest"]
export type TaskUpdate = components["schemas"]["TaskUpdateRequest"]
export type TaskStatus = components["schemas"]["TaskTransitionRequest"]["status"]

const TASKS_KEY = ["tasks"] as const

interface TaskFilters {
  status?: TaskStatus
  sprint_id?: string
}

function buildQuery(filters: TaskFilters): string {
  const params = new URLSearchParams()
  if (filters.status) params.set("status", filters.status)
  if (filters.sprint_id) params.set("sprint_id", filters.sprint_id)
  const q = params.toString()
  return q ? `?${q}` : ""
}

export function useTasks(filters: TaskFilters = {}) {
  return useQuery({
    queryKey: [...TASKS_KEY, filters],
    queryFn: () => apiGet<Task[]>(`/tasks${buildQuery(filters)}`),
  })
}

export function useTask(id: string) {
  return useQuery({
    queryKey: [...TASKS_KEY, id],
    queryFn: () => apiGet<Task>(`/tasks/${id}`),
  })
}

export function useCreateTask() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: TaskCreate) => apiPost<Task>("/tasks", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: TASKS_KEY }),
  })
}

export function useUpdateTask() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...body }: TaskUpdate & { id: string }) =>
      apiPatch<Task>(`/tasks/${id}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: TASKS_KEY }),
  })
}

export function useDeleteTask() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiDelete(`/tasks/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: TASKS_KEY }),
  })
}

export function useTransitionTask() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: TaskStatus }) =>
      apiPost<Task>(`/tasks/${id}/transition`, { status }),
    onMutate: async ({ id, status }) => {
      await qc.cancelQueries({ queryKey: TASKS_KEY })
      const prev = qc.getQueryData<Task[]>(TASKS_KEY)
      qc.setQueriesData<Task[]>({ queryKey: TASKS_KEY }, (old) =>
        old?.map((t) => (t.id === id ? { ...t, status } : t)),
      )
      return { prev }
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.prev) qc.setQueryData(TASKS_KEY, ctx.prev)
    },
    onSettled: () => qc.invalidateQueries({ queryKey: TASKS_KEY }),
  })
}
