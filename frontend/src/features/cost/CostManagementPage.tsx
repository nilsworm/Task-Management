import { useState } from "react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { currentYearMonth } from "@/lib/utils"
import { ApiError } from "@/api/client"
import { useCostSummary, useCostTags, useGenerateMonthly } from "@/api/hooks/cost"
import { TransactionList } from "./TransactionList"
import { RecurringList } from "./RecurringList"
import { SummaryCards } from "./SummaryCards"
import { TagFilterBar } from "./TagFilterBar"
import { AnalyticsTab } from "./AnalyticsTab"

type Tab = "overview" | "recurring" | "analytics"

const TABS: { id: Tab; label: string }[] = [
  { id: "overview", label: "Übersicht" },
  { id: "recurring", label: "Regelmäßig" },
  { id: "analytics", label: "Analyse" },
]

const MONTH_NAMES = [
  "Januar", "Februar", "März", "April", "Mai", "Juni",
  "Juli", "August", "September", "Oktober", "November", "Dezember",
]

function clampYearMonth(year: number, month: number): { year: number; month: number } {
  if (month < 1) return { year: year - 1, month: 12 }
  if (month > 12) return { year: year + 1, month: 1 }
  return { year, month }
}

export function CostManagementPage() {
  const [activeTab, setActiveTab] = useState<Tab>("overview")
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [{ year, month }, setYearMonth] = useState(currentYearMonth)

  const { data: summary, isLoading: summaryLoading } = useCostSummary(year, month)
  const { data: availableTags = [] } = useCostTags()
  const generateMonthly = useGenerateMonthly()

  const filters = { year, month, tags: selectedTags.length > 0 ? selectedTags : undefined }

  function navigate(delta: number) {
    setYearMonth(({ year: y, month: m }) => clampYearMonth(y, m + delta))
  }

  async function handleGenerate() {
    try {
      const created = await generateMonthly.mutateAsync({ year, month })
      if (created.length === 0) {
        toast.info("Keine aktiven Wiederholungseinträge vorhanden.")
      } else {
        toast.success(`${created.length} Buchung${created.length !== 1 ? "en" : ""} generiert.`)
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        toast.info("Monat wurde bereits generiert.")
      } else {
        toast.error("Fehler beim Generieren.")
      }
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Cost Management</h1>
          <p className="text-sm text-muted-foreground">Einnahmen und Ausgaben verwalten</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>‹</Button>
          <span className="min-w-[120px] text-center text-sm font-medium tabular-nums">
            {MONTH_NAMES[month - 1]} {year}
          </span>
          <Button variant="ghost" size="sm" onClick={() => navigate(1)}>›</Button>
        </div>
      </div>

      {/* Tab Bar */}
      <div className="flex gap-1 border-b border-border">
        {TABS.map((tab) => (
          <Button
            key={tab.id}
            variant="ghost"
            size="sm"
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "rounded-none border-b-2 border-transparent px-4 pb-2 text-sm font-medium transition-colors",
              activeTab === tab.id
                ? "border-primary text-foreground"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {tab.label}
          </Button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === "overview" && (
        <div className="flex flex-col gap-4">
<SummaryCards summary={summary} isLoading={summaryLoading} />
          <Button
            variant="outline"
            size="sm"
            className="self-start"
            onClick={handleGenerate}
            disabled={generateMonthly.isPending}
          >
            {generateMonthly.isPending ? "Wird geladen…" : "Monat laden"}
          </Button>
          <TagFilterBar
            availableTags={availableTags}
            selectedTags={selectedTags}
            onChange={setSelectedTags}
          />
          <TransactionList filters={filters} />
        </div>
      )}
      {activeTab === "recurring" && <RecurringList />}
      {activeTab === "analytics" && <AnalyticsTab year={year} month={month} />}
    </div>
  )
}
