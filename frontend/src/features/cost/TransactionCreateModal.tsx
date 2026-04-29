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
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useCreateTransaction, useCostTags } from "@/api/hooks/cost"
import { toast } from "sonner"

interface Props {
  open: boolean
  onClose: () => void
}

interface FormState {
  title: string
  amount: string
  transaction_type: "income" | "expense"
  date: string
  tags: string
  description: string
}

const today = new Date().toISOString().split("T")[0]

const DEFAULT: FormState = {
  title: "",
  amount: "",
  transaction_type: "expense",
  date: today,
  tags: "",
  description: "",
}

export function TransactionCreateModal({ open, onClose }: Props) {
  const [form, setForm] = useState<FormState>(DEFAULT)
  const [error, setError] = useState<string | null>(null)
  const create = useCreateTransaction()
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
    const tags = form.tags
      .split(",")
      .map((t) => t.trim().toLowerCase())
      .filter(Boolean)

    try {
      await create.mutateAsync({
        title: form.title.trim(),
        amount: form.amount,
        transaction_type: form.transaction_type,
        date: form.date,
        tags,
        description: form.description,
      })
      toast.success("Buchung erstellt")
      handleClose()
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Fehler beim Erstellen."
      setError(msg)
      toast.error("Fehler beim Erstellen")
    }
  }

  return (
    <Dialog open={open} onOpenChange={(o) => !o && handleClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Neue Buchung</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="grid gap-1.5">
            <Label htmlFor="tx_type">Typ</Label>
            <Select
              value={form.transaction_type}
              onValueChange={(v) =>
                setForm({ ...form, transaction_type: v as "income" | "expense" })
              }
            >
              <SelectTrigger id="tx_type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="expense">Ausgabe</SelectItem>
                <SelectItem value="income">Einnahme</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-1.5">
            <Label htmlFor="tx_title">Titel *</Label>
            <Input
              id="tx_title"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="z.B. Miete, Gehalt"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="grid gap-1.5">
              <Label htmlFor="tx_amount">Betrag (€) *</Label>
              <Input
                id="tx_amount"
                type="number"
                min="0.01"
                step="0.01"
                placeholder="0.00"
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })}
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="tx_date">Datum *</Label>
              <Input
                id="tx_date"
                type="date"
                value={form.date}
                onChange={(e) => setForm({ ...form, date: e.target.value })}
              />
            </div>
          </div>

          <div className="grid gap-1.5">
            <Label htmlFor="tx_tags">
              Tags{" "}
              <span className="text-xs text-muted-foreground">(kommagetrennt)</span>
            </Label>
            <Input
              id="tx_tags"
              value={form.tags}
              onChange={(e) => setForm({ ...form, tags: e.target.value })}
              placeholder="miete, wohnen"
              list="cost-tags-list"
            />
            <datalist id="cost-tags-list">
              {existingTags.map((t) => (
                <option key={t} value={t} />
              ))}
            </datalist>
          </div>

          <div className="grid gap-1.5">
            <Label htmlFor="tx_desc">Beschreibung</Label>
            <Textarea
              id="tx_desc"
              rows={2}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Optional"
            />
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
