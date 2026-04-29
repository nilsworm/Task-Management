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
import { useDeleteTransaction } from "@/api/hooks/cost"
import type { Transaction } from "@/api/hooks/cost"
import { toast } from "sonner"

interface Props {
  transaction: Transaction | null
  onClose: () => void
}

export function TransactionDeleteDialog({ transaction, onClose }: Props) {
  const del = useDeleteTransaction()

  async function handleConfirm() {
    if (!transaction) return
    try {
      await del.mutateAsync(transaction.id)
      toast.success("Buchung gelöscht")
      onClose()
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Fehler"
      if (msg.includes("past months") || msg.includes("409")) {
        toast.error("Buchungen aus vergangenen Monaten können nicht gelöscht werden.")
      } else {
        toast.error("Fehler beim Löschen")
      }
    }
  }

  return (
    <AlertDialog open={!!transaction} onOpenChange={(o) => !o && onClose()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Buchung löschen?</AlertDialogTitle>
          <AlertDialogDescription>
            &ldquo;{transaction?.title}&rdquo; wird dauerhaft gelöscht. Buchungen aus
            vergangenen Monaten können nicht gelöscht werden.
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
