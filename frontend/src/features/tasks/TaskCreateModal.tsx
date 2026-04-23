import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useCreateTask } from "@/api/hooks/tasks"
import type { TaskCreate } from "@/api/hooks/tasks"

interface Props {
  open: boolean
  onClose: () => void
}

const DEFAULT_FORM: TaskCreate = {
  task_type: "daily",
  title: "",
  priority: "medium",
  estimation: null,
  tags: [],
}

export function TaskCreateModal({ open, onClose }: Props) {
  const [form, setForm] = useState<TaskCreate>(DEFAULT_FORM)
  const [error, setError] = useState<string | null>(null)
  const create = useCreateTask()

  function handleClose() {
    setForm(DEFAULT_FORM)
    setError(null)
    onClose()
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.title.trim()) {
      setError("Title is required.")
      return
    }
    try {
      await create.mutateAsync(form)
      handleClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create task.")
    }
  }

  return (
    <Dialog open={open} onOpenChange={(o) => !o && handleClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>New Task</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="grid gap-1.5">
            <Label htmlFor="task_type">Type</Label>
            <Select
              value={form.task_type}
              onValueChange={(v) =>
                setForm({
                  ...DEFAULT_FORM,
                  task_type: v as TaskCreate["task_type"],
                })
              }
            >
              <SelectTrigger id="task_type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="daily">Daily</SelectItem>
                <SelectItem value="sprint">Sprint</SelectItem>
                <SelectItem value="goal">Goal</SelectItem>
                <SelectItem value="milestone">Milestone</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-1.5">
            <Label htmlFor="title">Title *</Label>
            <Input
              id="title"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="Task title"
            />
          </div>

          <div className="grid gap-1.5">
            <Label htmlFor="priority">Priority</Label>
            <Select
              value={form.priority}
              onValueChange={(v) => setForm({ ...form, priority: v as TaskCreate["priority"] })}
            >
              <SelectTrigger id="priority">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-1.5">
            <Label htmlFor="estimation">Story Points</Label>
            <Input
              id="estimation"
              type="number"
              min={1}
              max={100}
              placeholder="1–100 (optional)"
              value={form.estimation ?? ""}
              onChange={(e) =>
                setForm({
                  ...form,
                  estimation: e.target.value ? Number(e.target.value) : null,
                })
              }
            />
          </div>

          {form.task_type === "daily" && (
            <div className="grid gap-1.5">
              <Label htmlFor="scheduled_date">Scheduled Date</Label>
              <Input
                id="scheduled_date"
                type="date"
                value={form.scheduled_date ?? ""}
                onChange={(e) => setForm({ ...form, scheduled_date: e.target.value || null })}
              />
            </div>
          )}

          {form.task_type === "sprint" && (
            <div className="grid gap-1.5">
              <Label htmlFor="sprint_id">Sprint ID</Label>
              <Input
                id="sprint_id"
                placeholder="Sprint UUID (optional)"
                value={form.sprint_id ?? ""}
                onChange={(e) => setForm({ ...form, sprint_id: e.target.value || null })}
              />
            </div>
          )}

          {(form.task_type === "goal" || form.task_type === "milestone") && (
            <div className="grid grid-cols-2 gap-3">
              <div className="grid gap-1.5">
                <Label htmlFor="date_start">Start Date</Label>
                <Input
                  id="date_start"
                  type="date"
                  value={form.date_range_start ?? ""}
                  onChange={(e) =>
                    setForm({ ...form, date_range_start: e.target.value || null })
                  }
                />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="date_end">End Date</Label>
                <Input
                  id="date_end"
                  type="date"
                  value={form.date_range_end ?? ""}
                  onChange={(e) =>
                    setForm({ ...form, date_range_end: e.target.value || null })
                  }
                />
              </div>
            </div>
          )}

          {error && <p className="text-sm text-destructive">{error}</p>}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? "Creating…" : "Create"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
