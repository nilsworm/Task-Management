import { useState } from "react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
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

function currentYearMonth() {
  const now = new Date()
  return { year: now.getFullYear(), month: now.getMonth() + 1 }
}

export function CostManagementPage() {
  const [activeTab, setActiveTab] = useState<Tab>("overview")
  const { year, month } = currentYearMonth()
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [generateMsg, setGenerateMsg] = useState<string | null>(null)

  const { data: summary, isLoading: summaryLoading } = useCostSummary(year, month)
  const { data: availableTags = [] } = useCostTags()
  const generateMonthly = useGenerateMonthly()

  const filters = { year, month, tags: selectedTags.length > 0 ? selectedTags : undefined }

  async function handleGenerate() {
    setGenerateMsg(null)
    try {
      const created = await generateMonthly.mutateAsync({ year, month })
      setGenerateMsg(
        created.length === 0
          ? "Keine aktiven Wiederholungseinträge vorhanden."
          : `${created.length} Buchung${created.length !== 1 ? "en" : ""} generiert.`,
      )
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setGenerateMsg("Monat wurde bereits generiert.")
      } else {
        setGenerateMsg("Fehler beim Generieren.")
      }
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Cost Management</h1>
        <p className="text-sm text-muted-foreground">
          Einnahmen und Ausgaben verwalten
        </p>
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
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={handleGenerate}
              disabled={generateMonthly.isPending}
            >
              {generateMonthly.isPending ? "Wird geladen…" : "Monat laden"}
            </Button>
            {generateMsg && (
              <span className="text-xs text-muted-foreground">{generateMsg}</span>
            )}
          </div>
          <TagFilterBar
            availableTags={availableTags}
            selectedTags={selectedTags}
            onChange={setSelectedTags}
          />
          <TransactionList filters={filters} />
        </div>
      )}
      {activeTab === "recurring" && <RecurringList />}
      {activeTab === "analytics" && <AnalyticsTab />}
    </div>
  )
}
