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
import { useCreateRecurring, useCostTags } from "@/api/hooks/cost"
import { toast } from "sonner"

interface Props {
  open: boolean
  onClose: () => void
}

interface FormState {
  title: string
  amount: string
  transaction_type: "income" | "expense"
  interval: "weekly" | "monthly" | "yearly"
  day_of_month: string
  tags: string
}

const DEFAULT: FormState = {
  title: "",
  amount: "",
  transaction_type: "expense",
  interval: "monthly",
  day_of_month: "",
  tags: "",
}

export function RecurringCreateModal({ open, onClose }: Props) {
  const [form, setForm] = useState<FormState>(DEFAULT)
  const [error, setError] = useState<string | null>(null)
  const create = useCreateRecurring()
  const { data: existingTags = [] } = useCostTags()

  function handleClose() {
    setForm(DEFAULT)
    setError(null)
    onClose()
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.title.trim()) { setError("Titel ist erforderlich."); return }
    const amount = parseFloat(form.amount)
    if (!form.amount || isNaN(amount) || amount <= 0) {
      setError("Betrag muss größer als 0 sein.")
      return
    }
    const day = form.day_of_month ? parseInt(form.day_of_month) : null
    if (day !== null && (day < 1 || day > 28)) {
      setError("Tag des Monats muss zwischen 1 und 28 liegen.")
      return
    }
    const tags = form.tags
      .split(",")
      .map((t) => t.trim().toLowerCase())
      .filter(Boolean)

    try {
      await create.mutateAsync({
        title: form.title.trim(),
        amount: form.amount,
        transaction_type: form.transaction_type,
        interval: form.interval,
        day_of_month: day,
        tags,
      })
      toast.success("Wiederkehrender Eintrag erstellt")
      handleClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler beim Erstellen.")
      toast.error("Fehler beim Erstellen")
    }
  }

  return (
    <Dialog open={open} onOpenChange={(o) => !o && handleClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Wiederkehrenden Eintrag erstellen</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="grid gap-1.5">
            <Label htmlFor="rec_type">Typ</Label>
            <Select
              value={form.transaction_type}
              onValueChange={(v) =>
                setForm({ ...form, transaction_type: v as "income" | "expense" })
              }
            >
              <SelectTrigger id="rec_type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="expense">Ausgabe</SelectItem>
                <SelectItem value="income">Einnahme</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-1.5">
            <Label htmlFor="rec_title">Titel *</Label>
            <Input
              id="rec_title"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="z.B. Miete, Netflix, Gehalt"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="grid gap-1.5">
              <Label htmlFor="rec_amount">Betrag (€) *</Label>
              <Input
                id="rec_amount"
                type="number"
                min="0.01"
                step="0.01"
                placeholder="0.00"
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })}
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="rec_interval">Intervall</Label>
              <Select
                value={form.interval}
                onValueChange={(v) =>
                  setForm({ ...form, interval: v as FormState["interval"] })
                }
              >
                <SelectTrigger id="rec_interval">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="weekly">Wöchentlich</SelectItem>
                  <SelectItem value="monthly">Monatlich</SelectItem>
                  <SelectItem value="yearly">Jährlich</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {(form.interval === "monthly" || form.interval === "yearly") && (
            <div className="grid gap-1.5">
              <Label htmlFor="rec_day">
                Tag des Monats{" "}
                <span className="text-xs text-muted-foreground">(1–28, optional)</span>
              </Label>
              <Input
                id="rec_day"
                type="number"
                min={1}
                max={28}
                placeholder="z.B. 1"
                value={form.day_of_month}
                onChange={(e) => setForm({ ...form, day_of_month: e.target.value })}
              />
            </div>
          )}

          <div className="grid gap-1.5">
            <Label htmlFor="rec_tags">
              Tags{" "}
              <span className="text-xs text-muted-foreground">(kommagetrennt)</span>
            </Label>
            <Input
              id="rec_tags"
              value={form.tags}
              onChange={(e) => setForm({ ...form, tags: e.target.value })}
              placeholder="miete, wohnen"
              list="rec-tags-list"
            />
            <datalist id="rec-tags-list">
              {existingTags.map((t) => (
                <option key={t} value={t} />
              ))}
            </datalist>
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Abbrechen
            </Button>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? "Speichern…" : "Speichern"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
