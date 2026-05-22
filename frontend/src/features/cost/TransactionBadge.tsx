import { Badge } from "@/components/ui/badge"

type TransactionType = "income" | "expense" | "transfer" | "stock"

interface Props {
  type: TransactionType
}

const TYPE_CONFIG: Record<TransactionType, { className: string; label: string }> = {
  income:   { className: "border-green-500 text-green-600 dark:text-green-400",   label: "Einnahme"   },
  expense:  { className: "border-red-500 text-red-600 dark:text-red-400",         label: "Ausgabe"    },
  transfer: { className: "border-purple-500 text-purple-600 dark:text-purple-400", label: "Transfer"  },
  stock:    { className: "border-amber-500 text-amber-600 dark:text-amber-400",   label: "Investment" },
}

export function TransactionTypeBadge({ type }: Props) {
  const config = TYPE_CONFIG[type] ?? TYPE_CONFIG.expense
  return (
    <Badge variant="outline" className={config.className}>
      {config.label}
    </Badge>
  )
}

export function formatAmount(amount: number | string, currency = "EUR"): string {
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
  }).format(Number(amount))
}
