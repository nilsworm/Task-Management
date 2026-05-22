import { Skeleton } from "@/components/ui/skeleton"
import type { CostSummary } from "@/api/hooks/cost"

function formatEur(value: string | number): string {
  return new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR" }).format(
    Number(value),
  )
}

interface CardProps {
  label: string
  value: string
  colorClass: string
}

function SummaryCard({ label, value, colorClass }: CardProps) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={`mt-1 text-2xl font-semibold tabular-nums ${colorClass}`}>{value}</p>
    </div>
  )
}

function SummaryCardSkeleton() {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <Skeleton className="h-3 w-20" />
      <Skeleton className="mt-2 h-7 w-32" />
    </div>
  )
}

interface Props {
  summary: CostSummary | undefined
  isLoading: boolean
}

export function SummaryCards({ summary, isLoading }: Props) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-5 gap-4">
        <SummaryCardSkeleton />
        <SummaryCardSkeleton />
        <SummaryCardSkeleton />
        <SummaryCardSkeleton />
        <SummaryCardSkeleton />
      </div>
    )
  }

  const balance = Number(summary?.balance ?? 0)

  return (
    <div className="grid grid-cols-5 gap-4">
      <SummaryCard
        label="Einnahmen"
        value={formatEur(summary?.income ?? 0)}
        colorClass="text-green-600 dark:text-green-400"
      />
      <SummaryCard
        label="Ausgaben"
        value={formatEur(summary?.expenses ?? 0)}
        colorClass="text-red-600 dark:text-red-400"
      />
      <SummaryCard
        label="Saldo"
        value={formatEur(balance)}
        colorClass={
          balance >= 0
            ? "text-blue-600 dark:text-blue-400"
            : "text-red-600 dark:text-red-400"
        }
      />
      <SummaryCard
        label="Transfers"
        value={formatEur(summary?.transfers ?? 0)}
        colorClass="text-purple-600 dark:text-purple-400"
      />
      <SummaryCard
        label="Aktieninvestments"
        value={formatEur(summary?.stock_investments ?? 0)}
        colorClass="text-amber-600 dark:text-amber-400"
      />
    </div>
  )
}
