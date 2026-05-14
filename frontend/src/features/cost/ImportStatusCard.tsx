import { useImportStatus } from "@/api/hooks/cost"
import { Skeleton } from "@/components/ui/skeleton"

function formatDateMMDDYYYY(dateStr: string): string {
  const date = new Date(dateStr)
  const formatter = new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
  return formatter.format(date)
}

export function ImportStatusCard() {
  const { data, isLoading } = useImportStatus()

  if (isLoading) {
    return <Skeleton className="h-16 w-full" />
  }

  if (!data || !data.last_import_date) {
    return (
      <div className="rounded-md border border-dashed border-border bg-surface-2 p-4">
        <p className="text-sm text-text-secondary">
          No imports yet. Add CSV files to <code className="text-xs">/imports</code> folder.
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-md border border-border bg-surface-2 p-4">
      <p className="text-sm text-text-secondary">
        Last import: <span className="font-medium text-text-primary">{formatDateMMDDYYYY(data.last_import_date)}</span>
        {" · "}
        <span className="font-medium text-text-primary">{data.transaction_count} transactions</span>
      </p>
      <p className="mt-2 text-xs text-text-tertiary">
        Import folder: <code className="rounded bg-surface-3 px-2 py-1">/imports</code>
      </p>
    </div>
  )
}
