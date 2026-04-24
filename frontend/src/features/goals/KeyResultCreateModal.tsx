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
import { useCreateKeyResult } from "@/api/hooks/goals"
import { toast } from "sonner"

interface Props {
  goalId: string
  open: boolean
  onClose: () => void
}

interface Form {
  title: string
  target_value: string
  current_value: string
  unit: string
  description: string
}

const EMPTY: Form = { title: "", target_value: "", current_value: "0", unit: "", description: "" }

export function KeyResultCreateModal({ goalId, open, onClose }: Props) {
  const [form, setForm] = useState<Form>(EMPTY)
  const [error, setError] = useState<string | null>(null)
  const create = useCreateKeyResult(goalId)

  function handleClose() {
    setForm(EMPTY)
    setError(null)
    onClose()
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.title.trim()) return setError("Title is required.")
    const target = Number(form.target_value)
    if (!form.target_value || isNaN(target) || target <= 0)
      return setError("Target value must be a positive number.")
    try {
      await create.mutateAsync({
        title: form.title,
        target_value: target,
        current_value: Number(form.current_value) || 0,
        unit: form.unit,
        description: form.description,
      })
      toast.success("Key result added")
      handleClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create key result.")
      toast.error("Failed to add key result")
    }
  }

  return (
    <Dialog open={open} onOpenChange={(o) => !o && handleClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>New Key Result</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="grid gap-1.5">
            <Label htmlFor="kr-title">Title *</Label>
            <Input
              id="kr-title"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="e.g. Increase test coverage"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="grid gap-1.5">
              <Label htmlFor="kr-target">Target *</Label>
              <Input
                id="kr-target"
                type="number"
                min={0.01}
                step="any"
                value={form.target_value}
                onChange={(e) => setForm({ ...form, target_value: e.target.value })}
                placeholder="100"
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="kr-current">Current</Label>
              <Input
                id="kr-current"
                type="number"
                min={0}
                step="any"
                value={form.current_value}
                onChange={(e) => setForm({ ...form, current_value: e.target.value })}
              />
            </div>
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="kr-unit">Unit</Label>
            <Input
              id="kr-unit"
              value={form.unit}
              onChange={(e) => setForm({ ...form, unit: e.target.value })}
              placeholder="e.g. %, users, PRs"
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>Cancel</Button>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? "Creating…" : "Add"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
