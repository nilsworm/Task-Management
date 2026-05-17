import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { apiDelete, apiGet, apiPatch, apiPost } from "@/api/client"
import type { components } from "@/api/types"

export type Task = components["schemas"]["TaskResponse"]
export type TaskCreate = components["schemas"]["TaskCreateRequest"]
export type TaskUpdate = components["schemas"]["TaskUpdateRequest"]
export type TaskStatus = components["schemas"]["TaskTransitionRequest"]["status"]

const TASKS_KEY = ["tasks"] as const

interface TaskFilters {
  overdue?: boolean
  status?: TaskStatus
  sprint_id?: string
  search?: string
}

function buildQuery(filters: TaskFilters): string {
  const params = new URLSearchParams()
  if (filters.overdue) params.set("overdue", "true")
  else if (filters.search) params.set("search", filters.search)
  else if (filters.status) params.set("status", filters.status)
  else if (filters.sprint_id) params.set("sprint_id", filters.sprint_id)
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

function invalidateDashboard(qc: ReturnType<typeof useQueryClient>) {
  return qc.invalidateQueries({ queryKey: ["dashboard"] })
}

export function useCreateTask() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: TaskCreate) => apiPost<Task>("/tasks", body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: TASKS_KEY })
      invalidateDashboard(qc)
    },
  })
}

export function useUpdateTask() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...body }: TaskUpdate & { id: string }) =>
      apiPatch<Task>(`/tasks/${id}`, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: TASKS_KEY })
      invalidateDashboard(qc)
    },
  })
}

export function useDeleteTask() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiDelete(`/tasks/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: TASKS_KEY })
      invalidateDashboard(qc)
    },
  })
}

// matches ["sprints", <id>, "tasks"] — the query key used by useSprintTasks
const sprintTasksFilter = {
  predicate: (q: { queryKey: unknown }) => {
    const key = q.queryKey as unknown[]
    return key[0] === "sprints" && key[2] === "tasks"
  },
}

export function useTransitionTask() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: TaskStatus }) =>
      apiPost<Task>(`/tasks/${id}/transition`, { status }),
    onMutate: async ({ id, status }) => {
      await qc.cancelQueries({ queryKey: TASKS_KEY })

      const updater = (old: Task[] | undefined) =>
        old?.map((t) => (t.id === id ? { ...t, status } : t))

      // snapshot + optimistic update: global task list
      const prevTasks = qc.getQueriesData<Task[]>({ queryKey: TASKS_KEY })
      qc.setQueriesData<Task[]>({ queryKey: TASKS_KEY }, updater)

      // snapshot + optimistic update: sprint task list (used by KanbanBoard)
      const prevSprintTasks = qc.getQueriesData<Task[]>(sprintTasksFilter)
      qc.setQueriesData<Task[]>(sprintTasksFilter, updater)

      return { prevTasks, prevSprintTasks }
    },
    onError: (_err, _vars, ctx) => {
      ctx?.prevTasks?.forEach(([key, data]) => qc.setQueryData(key, data))
      ctx?.prevSprintTasks?.forEach(([key, data]) => qc.setQueryData(key, data))
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: TASKS_KEY })
      qc.invalidateQueries(sprintTasksFilter)
      invalidateDashboard(qc)
    },
  })
}
