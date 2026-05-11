import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Skeleton } from "@/components/ui/skeleton"
import { Trash2, Plus, Pause, Play } from "lucide-react"
import { useRecurring, useDeleteRecurring, useToggleRecurring } from "@/api/hooks/cost"
import type { Recurring } from "@/api/hooks/cost"
import { TransactionTypeBadge, formatAmount } from "./TransactionBadge"
import { RecurringCreateModal } from "./RecurringCreateModal"
import { toast } from "sonner"

const INTERVAL_LABELS: Record<string, string> = {
  weekly: "Wöchentlich",
  monthly: "Monatlich",
  yearly: "Jährlich",
}

function RecurringDeleteDialog({
  recurring,
  onClose,
}: {
  recurring: Recurring | null
  onClose: () => void
}) {
  const del = useDeleteRecurring()
  async function handleConfirm() {
    if (!recurring) return
    try {
      await del.mutateAsync(recurring.id)
      toast.success("Eintrag gelöscht")
      onClose()
    } catch {
      toast.error("Fehler beim Löschen")
    }
  }
  return (
    <AlertDialog open={!!recurring} onOpenChange={(o) => !o && onClose()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Eintrag löschen?</AlertDialogTitle>
          <AlertDialogDescription>
            &ldquo;{recurring?.title}&rdquo; wird dauerhaft gelöscht.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Abbrechen</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleConfirm}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            disabled={del.isPending}
          >
            {del.isPending ? "Löschen…" : "Löschen"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

export function RecurringList() {
  const [createOpen, setCreateOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<Recurring | null>(null)
  const { data: entries = [], isLoading, isError } = useRecurring()
  const toggle = useToggleRecurring()

  async function handleToggle(r: Recurring) {
    try {
      await toggle.mutateAsync({ id: r.id, is_active: !r.is_active })
      toast.success(r.is_active ? "Eintrag pausiert" : "Eintrag aktiviert")
    } catch {
      toast.error("Fehler beim Ändern des Status")
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {isLoading ? "Lädt…" : `${entries.length} Einträge`}
        </p>
        <Button size="sm" onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Neuer Eintrag
        </Button>
      </div>

      {isError && (
        <p className="text-sm text-destructive">Fehler beim Laden.</p>
      )}

      {isLoading && (
        <div className="flex flex-col gap-2">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      )}

      {!isLoading && !isError && entries.length === 0 && (
        <p className="py-8 text-center text-sm text-muted-foreground">
          Noch keine wiederkehrenden Einträge.
        </p>
      )}

      {!isLoading && !isError && entries.length > 0 && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Titel</TableHead>
              <TableHead>Typ</TableHead>
              <TableHead>Intervall</TableHead>
              <TableHead className="text-right">Betrag</TableHead>
              <TableHead>Tags</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-20" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {entries.map((r) => (
              <TableRow key={r.id}>
                <TableCell className="font-medium">
                  {r.title}
                  {r.day_of_month != null && (
                    <span className="ml-2 text-xs text-muted-foreground">
                      (Tag {r.day_of_month})
                    </span>
                  )}
                </TableCell>
                <TableCell>
                  <TransactionTypeBadge type={r.transaction_type as "income" | "expense"} />
                </TableCell>
                <TableCell>
                  <Badge variant="outline">
                    {INTERVAL_LABELS[r.interval] ?? r.interval}
                  </Badge>
                </TableCell>
                <TableCell
                  className={`text-right font-mono font-medium ${
                    r.transaction_type === "income"
                      ? "text-green-600 dark:text-green-400"
                      : "text-red-600 dark:text-red-400"
                  }`}
                >
                  {formatAmount(r.amount)}
                </TableCell>
                <TableCell>
                  <div className="flex flex-wrap gap-1">
                    {r.tags.map((tag) => (
                      <Badge key={tag} variant="secondary" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant={r.is_active ? "default" : "secondary"}>
                    {r.is_active ? "Aktiv" : "Inaktiv"}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-muted-foreground hover:text-foreground"
                      onClick={() => handleToggle(r)}
                      disabled={toggle.isPending}
                      title={r.is_active ? "Pausieren" : "Aktivieren"}
                    >
                      {r.is_active ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-muted-foreground hover:text-destructive"
                      onClick={() => setDeleteTarget(r)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <RecurringCreateModal open={createOpen} onClose={() => setCreateOpen(false)} />
      <RecurringDeleteDialog
        recurring={deleteTarget}
        onClose={() => setDeleteTarget(null)}
      />
    </div>
  )
}
