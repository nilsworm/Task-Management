import { useState } from "react"
import { useUpdateTask, useDeleteTask, useTransitionTask } from "@/api/hooks/tasks"
import type { Task, TaskStatus } from "@/api/hooks/tasks"
import { TRANSITIONS } from "./taskTransitions"
import { toast } from "sonner"

const STATUS_LABELS: Record<TaskStatus, string> = {
  backlog:     "Backlog",
  todo:        "To Do",
  in_progress: "In Progress",
  review:      "Review",
  blocked:     "Blocked",
  done:        "Done",
  cancelled:   "Cancelled",
}

const STATUS_COLORS: Record<TaskStatus, string> = {
  backlog:     "#5a5a7a",
  todo:        "#9090b0",
  in_progress: "#00d4ff",
  review:      "#ffd166",
  blocked:     "#ff4d6d",
  done:        "#06d6a0",
  cancelled:   "#333350",
}

const PRIORITY_COLORS: Record<string, string> = {
  low:      "#9090b0",
  medium:   "#a78bfa",
  high:     "#ffd166",
  critical: "#ff4d6d",
}

const PRIORITIES = ["low", "medium", "high", "critical"] as const
type Priority = typeof PRIORITIES[number]

interface Props {
  task: Task
  onClose: () => void
  onDeleted: () => void
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="mb-1.5 font-mono text-[10px] font-semibold uppercase tracking-[0.6px] text-muted-foreground">
      {children}
    </div>
  )
}

function EditInput({ value, onChange, multiline, placeholder, autoFocus }: {
  value: string
  onChange: (v: string) => void
  multiline?: boolean
  placeholder?: string
  autoFocus?: boolean
}) {
  const base = "w-full rounded-[4px] border border-border bg-surface-1 px-2.5 py-1.5 text-xs text-foreground outline-none transition-colors focus:border-cyan focus:ring-1 focus:ring-cyan/20"
  if (multiline) {
    return (
      <textarea
        className={`${base} min-h-[80px] resize-y leading-relaxed`}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    )
  }
  return (
    <input
      className={base}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      autoFocus={autoFocus}
    />
  )
}

export function TaskExpandedRow({ task, onClose, onDeleted }: Props) {
  const [title, setTitle]         = useState(task.title)
  const [description, setDesc]    = useState(task.description ?? "")
  const [priority, setPriority]   = useState<Priority>(task.priority as Priority)
  const [estimation, setEst]      = useState(task.estimation ?? 0)
  const [dueDate, setDueDate]     = useState(task.due_date ?? "")
  const [tags, setTags]           = useState<string[]>(task.tags ?? [])
  const [tagInput, setTagInput]   = useState("")

  const update    = useUpdateTask()
  const del       = useDeleteTask()
  const transition = useTransitionTask()

  const nextStatuses = TRANSITIONS[task.status as TaskStatus] ?? []

  function handleSave() {
    if (!title.trim()) return
    update.mutate(
      {
        id: task.id,
        title: title.trim(),
        description: description || null,
        priority,
        estimation: estimation > 0 ? estimation : null,
        tags: tags.length > 0 ? tags : null,
        due_date: dueDate || null,
      },
      {
        onSuccess: () => { toast.success("Task saved"); onClose() },
        onError:   () => toast.error("Failed to save task"),
      },
    )
  }

  function handleDelete() {
    del.mutate(task.id, {
      onSuccess: () => { toast.success("Task deleted"); onDeleted() },
      onError:   () => toast.error("Failed to delete task"),
    })
  }

  function handleTransition(status: TaskStatus) {
    transition.mutate(
      { id: task.id, status },
      {
        onSuccess: () => toast.success(`Moved to ${STATUS_LABELS[status]}`),
        onError:   () => toast.error("Failed to update status"),
      },
    )
  }

  function addTag(e: React.KeyboardEvent) {
    if (e.key !== "Enter" && e.key !== ",") return
    e.preventDefault()
    const t = tagInput.trim()
    if (t && !tags.includes(t)) setTags([...tags, t])
    setTagInput("")
  }

  function removeTag(t: string) {
    setTags(tags.filter((x) => x !== t))
  }

  const statusColor = STATUS_COLORS[task.status as TaskStatus] ?? "#5a5a7a"

  return (
    <div
      className="border-b border-border"
      style={{
        background: "linear-gradient(180deg, rgba(0,212,255,0.03) 0%, var(--color-surface-2) 40%)",
      }}
    >
      <div className="mx-3.5 mb-3.5 mt-2.5 overflow-hidden rounded-[6px] border border-border-strong bg-surface-2"
        style={{ borderLeft: `3px solid ${PRIORITY_COLORS[priority] ?? "#9090b0"}` }}
      >
        {/* Card header */}
        <div className="flex items-center justify-between gap-3 border-b border-border bg-surface-1 px-3.5 py-2.5">
          <div className="flex items-center gap-2 min-w-0">
            <span className="shrink-0 rounded-[3px] border border-border bg-surface-3 px-1.5 font-mono text-[10px] text-muted-foreground">
              TASK
            </span>
            <span
              className="shrink-0 rounded-[3px] px-1.5 py-0.5 font-mono text-[10px] font-semibold"
              style={{ background: `${statusColor}22`, color: statusColor }}
            >
              {STATUS_LABELS[task.status as TaskStatus] ?? task.status}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleDelete}
              disabled={del.isPending}
              className="h-6 rounded-[4px] border border-border px-2.5 font-mono text-[10px] text-destructive/60 transition-colors hover:border-destructive/40 hover:bg-destructive/10 hover:text-destructive disabled:opacity-50"
            >
              Delete
            </button>
            <button
              onClick={onClose}
              className="h-6 rounded-[4px] bg-cyan px-3 font-mono text-[10px] font-bold text-black"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={!title.trim() || update.isPending}
              className="h-6 rounded-[4px] bg-cyan px-3 font-mono text-[10px] font-bold text-black disabled:opacity-50"
            >
              {update.isPending ? "Saving…" : "Save"}
            </button>
          </div>
        </div>

        {/* Title */}
        <div className="px-4 pt-3.5 pb-1">
          <FieldLabel>Title</FieldLabel>
          <EditInput value={title} onChange={setTitle} autoFocus placeholder="Task title…" />
        </div>

        {/* Meta grid */}
        <div className="grid grid-cols-4 gap-3 px-4 py-3">
          {/* Status */}
          <div>
            <FieldLabel>Move to</FieldLabel>
            <div className="flex flex-wrap gap-1">
              {nextStatuses.length === 0 ? (
                <span className="font-mono text-[10px] text-muted-foreground">—</span>
              ) : nextStatuses.map((s) => {
                const c = STATUS_COLORS[s]
                return (
                  <button
                    key={s}
                    onClick={() => handleTransition(s)}
                    className="rounded-[3px] px-1.5 py-0.5 font-mono text-[10px] font-semibold transition-colors"
                    style={{ background: `${c}22`, color: c, border: `1px solid ${c}44` }}
                  >
                    {STATUS_LABELS[s]}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Priority */}
          <div>
            <FieldLabel>Priority</FieldLabel>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value as Priority)}
              className="w-full rounded-[4px] border border-border bg-surface-1 px-2 py-1.5 font-mono text-[11px] text-foreground outline-none focus:border-cyan"
              style={{ color: PRIORITY_COLORS[priority] ?? "#9090b0" }}
            >
              {PRIORITIES.map((p) => (
                <option key={p} value={p} style={{ color: PRIORITY_COLORS[p] }}>
                  {p}
                </option>
              ))}
            </select>
          </div>

          {/* Estimation */}
          <div>
            <FieldLabel>Effort (pts)</FieldLabel>
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setEst(Math.max(0, estimation - 1))}
                className="flex h-7 w-7 shrink-0 items-center justify-center rounded-[4px] border border-border bg-surface-1 text-muted-foreground transition-colors hover:text-foreground"
              >−</button>
              <input
                type="number" min="0" max="99"
                value={estimation}
                onChange={(e) => setEst(Math.max(0, parseInt(e.target.value) || 0))}
                className="h-7 w-full rounded-[4px] border border-border bg-surface-1 text-center font-mono text-[12px] font-bold text-cyan outline-none focus:border-cyan"
              />
              <button
                onClick={() => setEst(Math.min(99, estimation + 1))}
                className="flex h-7 w-7 shrink-0 items-center justify-center rounded-[4px] border border-border bg-surface-1 text-cyan transition-colors hover:bg-cyan/10"
              >+</button>
            </div>
          </div>

          {/* Due Date */}
          <div>
            <FieldLabel>Due Date</FieldLabel>
            <input
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              className="w-full rounded-[4px] border border-border bg-surface-1 px-2 py-1.5 font-mono text-[11px] text-foreground outline-none focus:border-cyan"
            />
          </div>
        </div>

        {/* Tags */}
        <div className="px-4 pb-3">
          <FieldLabel>Tags</FieldLabel>
          <div className="flex flex-wrap items-center gap-1.5">
            {tags.map((t) => (
              <span
                key={t}
                className="flex items-center gap-1 rounded-[3px] border border-border bg-surface-3 px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground"
              >
                {t}
                <button onClick={() => removeTag(t)} className="text-muted-foreground hover:text-foreground">×</button>
              </span>
            ))}
            <input
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={addTag}
              placeholder="Add tag…"
              className="h-6 rounded-[3px] border border-dashed border-border bg-transparent px-1.5 font-mono text-[10px] text-muted-foreground outline-none placeholder:text-muted-foreground/50 focus:border-cyan"
            />
          </div>
        </div>

        {/* Description */}
        <div className="px-4 pb-4">
          <FieldLabel>Description</FieldLabel>
          <EditInput
            value={description}
            onChange={setDesc}
            multiline
            placeholder="Add context, acceptance criteria, notes…"
          />
        </div>
      </div>
    </div>
  )
}
