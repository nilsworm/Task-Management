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
import { Skeleton } from "@/components/ui/skeleton"
import { Trash2, Plus } from "lucide-react"
import { useTransactions } from "@/api/hooks/cost"
import type { Transaction, TransactionFilters } from "@/api/hooks/cost"
import { TransactionTypeBadge, formatAmount } from "./TransactionBadge"
import { TransactionCreateModal } from "./TransactionCreateModal"
import { TransactionDeleteDialog } from "./TransactionDeleteDialog"

interface Props {
  filters: TransactionFilters
}

export function TransactionList({ filters }: Props) {
  const [createOpen, setCreateOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<Transaction | null>(null)
  const { data: transactions = [], isLoading, isError } = useTransactions(filters)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {isLoading ? "Lädt…" : `${transactions.length} Buchungen`}
        </p>
        <Button size="sm" onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Neue Buchung
        </Button>
      </div>

      {isError && (
        <p className="text-sm text-destructive">
          Fehler beim Laden. Läuft das Backend?
        </p>
      )}

      {isLoading && (
        <div className="flex flex-col gap-2">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      )}

      {!isLoading && !isError && transactions.length === 0 && (
        <p className="py-8 text-center text-sm text-muted-foreground">
          Keine Buchungen gefunden.
        </p>
      )}

      {!isLoading && !isError && transactions.length > 0 && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Datum</TableHead>
              <TableHead>Titel</TableHead>
              <TableHead>Typ</TableHead>
              <TableHead className="text-right">Betrag</TableHead>
              <TableHead>Tags</TableHead>
              <TableHead className="w-10" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {transactions.map((t) => (
              <TableRow key={t.id}>
                <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
                  {new Date(t.date).toLocaleDateString("de-DE")}
                </TableCell>
                <TableCell className="font-medium">{t.title}</TableCell>
                <TableCell>
                  <TransactionTypeBadge type={t.transaction_type as "income" | "expense"} />
                </TableCell>
                <TableCell
                  className={`text-right font-mono font-medium ${
                    t.transaction_type === "income"
                      ? "text-green-600 dark:text-green-400"
                      : "text-red-600 dark:text-red-400"
                  }`}
                >
                  {t.transaction_type === "income" ? "+" : "-"}
                  {formatAmount(t.amount)}
                </TableCell>
                <TableCell>
                  <div className="flex flex-wrap gap-1">
                    {t.tags.map((tag) => (
                      <Badge key={tag} variant="secondary" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-muted-foreground hover:text-destructive"
                    onClick={() => setDeleteTarget(t)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <TransactionCreateModal open={createOpen} onClose={() => setCreateOpen(false)} />
      <TransactionDeleteDialog
        transaction={deleteTarget}
        onClose={() => setDeleteTarget(null)}
      />
    </div>
  )
}
