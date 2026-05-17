import { useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { ArrowLeft, Plus, Search } from "lucide-react"
import { useSprint, useSprintTasks, useStartSprint, useCompleteSprint } from "@/api/hooks/sprints"
import { SprintStatusBadge } from "./SprintStatusBadge"
import { SprintTaskList } from "./SprintTaskList"
import { SprintTaskPicker } from "./SprintTaskPicker"
import { SprintInlineCreate } from "./SprintInlineCreate"
import { SprintCompleteModal } from "./SprintCompleteModal"

export function SprintDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: sprint, isLoading, isError } = useSprint(id!)
  const { data: tasks = [] } = useSprintTasks(id!)
  const start    = useStartSprint()
  const complete = useCompleteSprint()

  const [pickerOpen, setPickerOpen]   = useState(false)
  const [inlineCreate, setInlineCreate] = useState(false)
  const [completeModalOpen, setCompleteModalOpen] = useState(false)

  if (isLoading) return <p className="font-mono text-[11px] text-muted-foreground">Loading sprint…</p>
  if (isError || !sprint) {
    return <p className="font-mono text-[11px] text-destructive">Sprint not found.</p>
  }

  const done  = tasks.filter((t) => t.status === "done").length
  const total = tasks.length
  const pct   = total > 0 ? Math.round((done / total) * 100) : sprint.completion_percent

  return (
    <div className="flex flex-col gap-3">
      {/* Header row */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate("/sprints")}
          className="flex h-7 w-7 items-center justify-center rounded-[5px] border border-border bg-surface-2 text-muted-foreground transition-colors hover:bg-surface-3 hover:text-foreground"
          aria-label="Back to sprints"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
        </button>

        <h1 className="flex-1 text-sm font-semibold text-foreground">{sprint.name}</h1>
        <SprintStatusBadge status={sprint.status} />
        <span className="font-mono text-[10px] text-muted-foreground">
          {sprint.start_date} → {sprint.end_date}
        </span>
      </div>

      {/* Goal + progress row */}
      <div className="flex flex-col gap-2 rounded-[6px] border border-border bg-surface-2 px-4 py-3">
        {sprint.goal && (
          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] text-muted-foreground">Goal</span>
            <span className="text-[11px] text-foreground">{sprint.goal}</span>
          </div>
        )}
        {/* Progress */}
        <div className="flex items-center gap-3">
          <div className="flex-1 h-1.5 rounded-full bg-surface-3 overflow-hidden">
            <div
              className="h-full rounded-full bg-green transition-all"
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="shrink-0 font-mono text-[11px] font-semibold text-foreground">
            {pct}%
          </span>
          <span className="shrink-0 font-mono text-[10px] text-muted-foreground">
            {done}/{total} done
          </span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2">
        {sprint.status === "planned" && (
          <button
            disabled={start.isPending}
            onClick={() => start.mutate(sprint.id)}
            className="h-7 rounded-[5px] border border-border bg-surface-2 px-3 font-mono text-[11px] text-muted-foreground transition-colors hover:bg-surface-3 hover:text-foreground disabled:opacity-50"
          >
            Start sprint
          </button>
        )}
        {sprint.status === "active" && (
          <button
            disabled={complete.isPending}
            onClick={() => setCompleteModalOpen(true)}
            className="h-7 rounded-[5px] border border-border bg-surface-2 px-3 font-mono text-[11px] text-muted-foreground transition-colors hover:bg-surface-3 hover:text-foreground disabled:opacity-50"
          >
            Complete sprint
          </button>
        )}

        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={() => setPickerOpen(true)}
            className="flex h-7 items-center gap-1.5 rounded-[5px] border border-border bg-surface-2 px-3 font-mono text-[11px] text-muted-foreground transition-colors hover:bg-surface-3 hover:text-foreground"
          >
            <Search className="h-3 w-3" />
            Assign existing
          </button>
          <button
            onClick={() => setInlineCreate(true)}
            className="flex h-7 items-center gap-1.5 rounded-[5px] border border-border bg-surface-2 px-3 font-mono text-[11px] text-muted-foreground transition-colors hover:bg-surface-3 hover:text-foreground"
          >
            <Plus className="h-3 w-3" />
            New task
          </button>
        </div>
      </div>

      {/* Inline create form */}
      {inlineCreate && (
        <SprintInlineCreate sprintId={sprint.id} onDone={() => setInlineCreate(false)} />
      )}

      {/* Task list */}
      <SprintTaskList tasks={tasks} sprintId={sprint.id} />

      {/* Task picker modal */}
      {pickerOpen && (
        <SprintTaskPicker
          sprintId={sprint.id}
          assignedTaskIds={sprint.task_ids.map(String)}
          onClose={() => setPickerOpen(false)}
        />
      )}

      {/* Complete sprint modal */}
      {sprint && (
        <SprintCompleteModal
          sprint={sprint}
          isOpen={completeModalOpen}
          doneCount={tasks.filter((t) => t.status === "done").length}
          totalCount={tasks.length}
          onClose={() => setCompleteModalOpen(false)}
          onConfirm={(moveIncomplete) => {
            complete.mutate({ id: sprint.id, moveIncomplete })
            setCompleteModalOpen(false)
          }}
          isPending={complete.isPending}
        />
      )}
    </div>
  )
}
