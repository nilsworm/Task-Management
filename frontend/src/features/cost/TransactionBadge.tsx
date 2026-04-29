import { Badge } from "@/components/ui/badge"

interface Props {
  type: "income" | "expense"
}

export function TransactionTypeBadge({ type }: Props) {
  return (
    <Badge
      variant="outline"
      className={
        type === "income"
          ? "border-green-500 text-green-600 dark:text-green-400"
          : "border-red-500 text-red-600 dark:text-red-400"
      }
    >
      {type === "income" ? "Einnahme" : "Ausgabe"}
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
