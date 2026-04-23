import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useCreateSprint } from "@/api/hooks/sprints"

interface Props {
  open: boolean
  onClose: () => void
}

interface Form {
  name: string
  start_date: string
  end_date: string
}

const EMPTY: Form = { name: "", start_date: "", end_date: "" }

export function SprintCreateModal({ open, onClose }: Props) {
  const [form, setForm] = useState<Form>(EMPTY)
  const [error, setError] = useState<string | null>(null)
  const create = useCreateSprint()

  function handleClose() {
    setForm(EMPTY)
    setError(null)
    onClose()
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.name.trim()) return setError("Name is required.")
    if (!form.start_date || !form.end_date) return setError("Start and end date are required.")
    if (form.start_date > form.end_date) return setError("Start date must be before end date.")
    try {
      await create.mutateAsync(form)
      handleClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create sprint.")
    }
  }

  return (
    <Dialog open={open} onOpenChange={(o) => !o && handleClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>New Sprint</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="grid gap-1.5">
            <Label htmlFor="sprint-name">Name *</Label>
            <Input
              id="sprint-name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Sprint 1"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="grid gap-1.5">
              <Label htmlFor="sprint-start">Start Date *</Label>
              <Input
                id="sprint-start"
                type="date"
                value={form.start_date}
                onChange={(e) => setForm({ ...form, start_date: e.target.value })}
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="sprint-end">End Date *</Label>
              <Input
                id="sprint-end"
                type="date"
                value={form.end_date}
                onChange={(e) => setForm({ ...form, end_date: e.target.value })}
              />
            </div>
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>Cancel</Button>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? "Creating…" : "Create"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
