import { useState } from "react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { TransactionList } from "./TransactionList"
import { RecurringList } from "./RecurringList"
import type { TransactionFilters } from "@/api/hooks/cost"

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
  const [filters] = useState<TransactionFilters>({ year, month })

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
      {activeTab === "overview" && <TransactionList filters={filters} />}
      {activeTab === "recurring" && <RecurringList />}
      {activeTab === "analytics" && (
        <div className="py-16 text-center text-sm text-muted-foreground">
          Analyse-Diagramme folgen in Phase 7.4.
        </div>
      )}
    </div>
  )
}
